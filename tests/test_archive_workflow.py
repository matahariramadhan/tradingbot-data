from __future__ import annotations

import hashlib
import gzip
import io
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from archive_manifest import (  # noqa: E402
    MANIFEST_SCHEMA_VERSION,
    find_record_index,
    load_manifest,
    sha256_file,
    write_manifest_atomically,
)
from audit_binance_klines import audit  # noqa: E402
from build_archive_manifest import build_grouped_gzip_records  # noqa: E402
from build_binance_feature_view import build_feature_view  # noqa: E402
from run_archive_audit import run_one, verify_completed_output  # noqa: E402
from run_archive_batch import coverage_for, load_coverage_map  # noqa: E402


class ArchiveWorkflowTests(unittest.TestCase):
    @staticmethod
    def _binance_record(start_ms: int, receipt: str) -> dict[str, object]:
        return {
            "received_at_utc": receipt,
            "stream": "btcusdt@kline_1s",
            "raw_event": {
                "k": {
                    "t": start_ms,
                    "T": start_ms + 999,
                    "c": "100.0",
                    "x": True,
                }
            },
        }

    @staticmethod
    def _jsonl_bytes(records: list[dict[str, object]]) -> bytes:
        return b"".join(
            (json.dumps(record) + "\n").encode("utf-8")
            for record in records
        )

    def test_sha256_file_matches_standard_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.bin"
            path.write_bytes(b"archive test data")
            expected = hashlib.sha256(b"archive test data").hexdigest()
            self.assertEqual(sha256_file(path), expected)

    def test_manifest_write_and_record_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            payload = {
                "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
                "records": [
                    {
                        "archive_name": "day.zip",
                        "archive_relative_path": "nested/day.zip",
                    }
                ],
            }
            write_manifest_atomically(path, payload)
            loaded = load_manifest(path)
            self.assertEqual(find_record_index(loaded, "nested/day.zip"), 0)
            self.assertEqual(json.loads(path.read_text())["records"][0]["archive_name"], "day.zip")

    def test_schema_v1_manifest_remains_readable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            payload = {
                "manifest_schema_version": 1,
                "records": [
                    {
                        "archive_name": "legacy.zip",
                        "archive_relative_path": "legacy.zip",
                    }
                ],
            }
            path.write_text(json.dumps(payload), encoding="utf-8")
            loaded = load_manifest(path)
            self.assertEqual(find_record_index(loaded, "legacy.zip"), 0)

    def test_reader_scripts_remain_directly_invokable(self) -> None:
        for name in (
            "audit_binance_klines.py",
            "inspect_binance_klines.py",
            "build_decision_snapshot.py",
            "build_binance_proxy_targets.py",
            "apply_proxy_boundary_recovery.py",
            "build_binance_feature_view.py",
            "build_proxy_join.py",
            "review_proxy_model_view.py",
        ):
            completed = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / name), "--help"],
                cwd=SCRIPTS_DIR.parent,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                completed.returncode,
                0,
                msg=f"{name}: {completed.stderr}",
            )

    def test_grouped_gzip_manifest_preserves_missing_roles(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            names = (
                "binance_raw_events_2026-06-29.jsonl.gz",
                "recorder.log.2026-06-29.gz",
                "binance_raw_events_2026-06-30.jsonl.gz",
                "polymarket_raw_events_2026-06-30.jsonl.gz",
                "recorder.log.2026-06-30.gz",
                "binance_kline_1s_2026-06-30.csv.gz",
            )
            for name in names:
                with gzip.open(root / name, "wb") as destination:
                    destination.write(b"fixture\n")

            records, ignored = build_grouped_gzip_records(
                root, False, "audit-v2", "policy-v1"
            )
            by_id = {record["group_id"]: record for record in records}
            self.assertEqual(len(records), 2)
            self.assertFalse(by_id["2026-06-29"]["input_complete"])
            self.assertEqual(
                by_id["2026-06-29"]["missing_input_roles"],
                ["polymarket_raw"],
            )
            self.assertTrue(by_id["2026-06-30"]["input_complete"])
            self.assertEqual(len(ignored), 1)
            self.assertEqual(
                ignored[0]["relative_path"],
                "binance_kline_1s_2026-06-30.csv.gz",
            )

    def test_day_audit_supports_direct_gzip_and_legacy_zip(self) -> None:
        start = 1782691200000  # 2026-06-29T00:00:00Z
        records = [
            self._binance_record(
                start, "2026-06-29T00:00:01.100000Z"
            ),
            self._binance_record(
                start + 1000, "2026-06-29T00:00:02.100000Z"
            ),
        ]
        raw = self._jsonl_bytes(records)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            direct = root / "binance_raw_events_2026-06-29.jsonl.gz"
            with gzip.open(direct, "wb") as destination:
                destination.write(raw)

            compressed = io.BytesIO()
            with gzip.GzipFile(fileobj=compressed, mode="wb") as destination:
                destination.write(raw)
            legacy = root / "legacy.zip"
            member = "binance_raw_events_2026-06-29.jsonl.gz"
            with zipfile.ZipFile(legacy, "w") as archive:
                archive.writestr(member, compressed.getvalue())

            day_start = datetime(2026, 6, 29, tzinfo=timezone.utc)
            direct_summary, direct_member = audit(
                direct, None, day_start, 2
            )
            zip_summary, zip_member = audit(legacy, None, day_start, 2)

            self.assertEqual(direct_summary["records_scanned"], 2)
            self.assertEqual(direct_summary["missing_starts_in_window"], 0)
            self.assertEqual(zip_summary["records_scanned"], 2)
            self.assertEqual(direct_member, direct.name)
            self.assertEqual(zip_member, member)

    def test_feature_view_requires_complete_as_of_lookback(self) -> None:
        decision = datetime(2026, 6, 29, 0, 5, tzinfo=timezone.utc)
        decision_ms = int(decision.timestamp() * 1000)
        records = []
        for offset in range(61, 0, -1):
            start_ms = decision_ms - offset * 1000
            receipt = datetime.fromtimestamp(
                (start_ms + 999) / 1000, tz=timezone.utc
            ).isoformat().replace("+00:00", "Z")
            records.append(
                self._binance_record(start_ms, receipt)
            )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            direct = root / "binance_raw_events_2026-06-29.jsonl.gz"
            with gzip.open(direct, "wb") as destination:
                destination.write(self._jsonl_bytes(records))

            rows, _, counters = build_feature_view(
                direct,
                None,
                datetime(2026, 6, 29, tzinfo=timezone.utc),
                duration_seconds=600,
            )

            self.assertEqual(len(rows), 2)
            self.assertEqual(counters["windows_requested"], 2)
            self.assertEqual(counters["feature_rows_usable"], 1)
            self.assertEqual(rows[0]["feature_row_usable"], "false")
            self.assertEqual(rows[1]["feature_row_usable"], "true")
            self.assertEqual(rows[1]["return_1m_valid"], "true")
            self.assertEqual(rows[1]["volatility_1m_valid"], "true")

    def test_feature_view_rejects_missing_lookback_inputs(self) -> None:
        decision = datetime(2026, 6, 29, 0, 5, tzinfo=timezone.utc)
        decision_ms = int(decision.timestamp() * 1000)
        records = []
        for offset in range(61, 0, -1):
            start_ms = decision_ms - offset * 1000
            receipt = datetime.fromtimestamp(
                (start_ms + 999) / 1000, tz=timezone.utc
            ).isoformat().replace("+00:00", "Z")
            if offset == 30:
                continue
            records.append(self._binance_record(start_ms, receipt))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            direct = root / "binance_raw_events_2026-06-29.jsonl.gz"
            with gzip.open(direct, "wb") as destination:
                destination.write(self._jsonl_bytes(records))

            rows, _, counters = build_feature_view(
                direct,
                None,
                datetime(2026, 6, 29, tzinfo=timezone.utc),
                duration_seconds=600,
            )

            self.assertEqual(counters["feature_rows_usable"], 0)
            row = rows[1]
            self.assertEqual(row["return_1s_valid"], "true")
            self.assertEqual(row["return_1m_valid"], "false")
            self.assertIn("missing_kline", row["return_1m_quality_flag"])

    def test_feature_view_uses_latest_eligible_kline_when_latest_is_late(self) -> None:
        decision = datetime(2026, 6, 29, 0, 5, tzinfo=timezone.utc)
        decision_ms = int(decision.timestamp() * 1000)
        records = []
        for offset in range(62, 0, -1):
            start_ms = decision_ms - offset * 1000
            receipt = datetime.fromtimestamp(
                (start_ms + 999) / 1000, tz=timezone.utc
            ).isoformat().replace("+00:00", "Z")
            if offset == 1:
                receipt = "2026-06-29T00:05:00.100000Z"
            records.append(self._binance_record(start_ms, receipt))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            direct = root / "binance_raw_events_2026-06-29.jsonl.gz"
            with gzip.open(direct, "wb") as destination:
                destination.write(self._jsonl_bytes(records))

            rows, _, counters = build_feature_view(
                direct,
                None,
                datetime(2026, 6, 29, tzinfo=timezone.utc),
                duration_seconds=600,
            )

            self.assertEqual(counters["feature_rows_usable"], 1)
            self.assertEqual(rows[1]["feature_row_usable"], "true")
            self.assertEqual(
                rows[1]["latest_interval_start_utc"],
                "2026-06-29T00:04:58.000Z",
            )

    def test_feature_view_return_1m_is_net_lookback_return(self) -> None:
        decision = datetime(2026, 6, 29, 0, 5, tzinfo=timezone.utc)
        decision_ms = int(decision.timestamp() * 1000)
        records = []
        for index, offset in enumerate(range(61, 0, -1)):
            start_ms = decision_ms - offset * 1000
            if index < 59:
                close = 100.0
            elif index == 59:
                close = 109.0
            else:
                close = 110.0
            record = self._binance_record(
                start_ms,
                datetime.fromtimestamp(
                    (start_ms + 999) / 1000, tz=timezone.utc
                ).isoformat().replace("+00:00", "Z"),
            )
            record["raw_event"]["k"]["c"] = str(close)
            records.append(record)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            direct = root / "binance_raw_events_2026-06-29.jsonl.gz"
            with gzip.open(direct, "wb") as destination:
                destination.write(self._jsonl_bytes(records))

            rows, _, counters = build_feature_view(
                direct,
                None,
                datetime(2026, 6, 29, tzinfo=timezone.utc),
                duration_seconds=600,
            )

            self.assertEqual(counters["feature_rows_usable"], 1)
            row = rows[1]
            self.assertEqual(row["return_1s"], f"{1 / 109:.10f}")
            self.assertEqual(row["return_1m"], "0.1000000000")
            self.assertNotEqual(row["return_1s"], row["return_1m"])

    def test_grouped_gzip_runner_completes_binance_scope_only(self) -> None:
        start = 1782691200000
        records = [
            self._binance_record(
                start, "2026-06-29T00:00:01.100000Z"
            ),
            self._binance_record(
                start + 1000, "2026-06-29T00:00:02.100000Z"
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            direct = root / "binance_raw_events_2026-06-29.jsonl.gz"
            with gzip.open(direct, "wb") as destination:
                destination.write(self._jsonl_bytes(records))

            grouped, ignored = build_grouped_gzip_records(
                root, False, "audit-v2", "policy-v1"
            )
            self.assertEqual(ignored, [])
            manifest = root / "manifest.json"
            write_manifest_atomically(
                manifest,
                {
                    "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
                    "input_root": str(root),
                    "archive_root": str(root),
                    "records": grouped,
                },
            )
            output_dir = root / "outputs"

            message = run_one(
                manifest,
                "2026-06-29",
                "2026-06-29T00:00:00Z",
                output_dir,
                duration_seconds=2,
            )
            self.assertIn("completed 2026-06-29", message)
            loaded = load_manifest(manifest)
            record = loaded["records"][0]
            self.assertEqual(record["status"], "completed")
            self.assertFalse(record["input_complete"])
            result_path = Path(record["audit_output_uri"])
            result = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(result["audit_input_role"], "binance_raw")
            self.assertFalse(result["input_complete"])
            self.assertEqual(result["summary"]["records_scanned"], 2)

    def test_completed_output_requires_matching_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "audit.json"
            output.write_text('{"ok": true}\n', encoding="utf-8")
            record = {
                "audit_output_uri": str(output),
                "audit_output_sha256": sha256_file(output),
            }
            manifest = root / "manifest.json"
            self.assertEqual(verify_completed_output(manifest, record), (True, "verified"))

            output.write_text('{"ok": false}\n', encoding="utf-8")
            verified, reason = verify_completed_output(manifest, record)
            self.assertFalse(verified)
            self.assertIn("checksum mismatch", reason)

    def test_coverage_map_requires_utc_midnight(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            valid = Path(directory) / "valid.json"
            valid.write_text(
                json.dumps({"day.zip": "2026-07-27T00:00:00Z"}),
                encoding="utf-8",
            )
            self.assertEqual(
                load_coverage_map(valid), {"day.zip": "2026-07-27T00:00:00Z"}
            )

            invalid = Path(directory) / "invalid.json"
            invalid.write_text(
                json.dumps({"day.zip": "2026-07-27T00:05:00Z"}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "UTC midnight"):
                load_coverage_map(invalid)

    def test_coverage_map_accepts_group_id(self) -> None:
        record = {
            "group_id": "2026-06-29",
            "inputs": {
                "binance_raw": {
                    "name": "binance_raw_events_2026-06-29.jsonl.gz",
                    "relative_path": "raw/binance_raw_events_2026-06-29.jsonl.gz",
                }
            },
        }
        mapping = {"2026-06-29": "2026-06-29T00:00:00Z"}
        self.assertEqual(
            coverage_for(record, mapping), "2026-06-29T00:00:00Z"
        )


if __name__ == "__main__":
    unittest.main()
