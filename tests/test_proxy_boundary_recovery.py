from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from build_binance_proxy_targets import FIELDNAMES, build_targets  # noqa: E402
from apply_proxy_boundary_recovery import patch_rows  # noqa: E402


def make_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    day_start = datetime(2026, 7, 27, tzinfo=timezone.utc)
    for index in range(288):
        window_start = day_start + timedelta(minutes=5 * index)
        window_end = window_start + timedelta(minutes=5)
        start_boundary = window_start - timedelta(seconds=1)
        rows.append(
            {
                "window_start_utc": window_start.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                "decision_time_utc": window_start.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                "window_end_utc": window_end.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                "proxy_start_price": "100.00000000",
                "proxy_start_interval_start_utc": start_boundary.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                "proxy_start_available_at_utc": window_start.isoformat(timespec="microseconds").replace("+00:00", "Z"),
                "proxy_end_price": "",
                "proxy_end_interval_start_utc": "",
                "proxy_end_available_at_utc": "",
                "target_available_at_utc": "",
                "label": "",
                "label_source": "binance_proxy",
                "label_definition": "end_price_gte_start_price",
                "target_valid": "false",
                "target_quality_flag": "",
            }
        )
    final_row = rows[-1]
    final_row["target_quality_flag"] = "missing_end_boundary"
    final_row["proxy_start_available_at_utc"] = "2026-07-27T23:55:01.000000Z"
    return rows


class ProxyBoundaryRecoveryTests(unittest.TestCase):
    def test_target_builder_preserves_valid_start_when_end_is_missing(self) -> None:
        window_start = datetime(2026, 7, 27, 0, 0, tzinfo=timezone.utc)
        start_boundary_ms = int(window_start.timestamp() * 1000) - 1000
        observations = {
            start_boundary_ms: [
                {
                    "start_ms": start_boundary_ms,
                    "close": 100.0,
                    "available_at": window_start,
                }
            ]
        }
        rows, counters = build_targets(
            observations, window_start, window_start + timedelta(minutes=5)
        )
        self.assertEqual(counters["missing_end"], 1)
        self.assertEqual(rows[0]["target_valid"], "false")
        self.assertEqual(rows[0]["proxy_start_price"], "100.00000000")
        self.assertEqual(
            rows[0]["proxy_start_interval_start_utc"],
            "2026-07-26T23:59:59.000Z",
        )

    def test_patch_rows_uses_recovered_end_and_preserves_late_start(self) -> None:
        rows = make_rows()
        boundary = datetime(2026, 7, 27, 23, 59, 59, tzinfo=timezone.utc)
        boundary_ms = int(boundary.timestamp() * 1000)
        patched, details = patch_rows(
            rows,
            {
                boundary_ms: {
                    "boundary_start_ms": boundary_ms,
                    "target_day": "2026-07-27",
                    "close": 101.0,
                    "available_at": datetime(2026, 7, 28, tzinfo=timezone.utc),
                    "source_group": "2026-07-28",
                    "source_file": "binance_raw_events_2026-07-28.jsonl.gz",
                }
            },
        )
        final_row = patched[-1]
        self.assertEqual(details["recovered_rows"], 1)
        self.assertEqual(final_row["proxy_end_price"], "101.00000000")
        self.assertEqual(final_row["label"], "UP")
        self.assertEqual(final_row["target_valid"], "true")
        self.assertEqual(
            final_row["target_quality_flag"],
            "valid_target_recovered_end_boundary_late_start",
        )

    def test_patch_rows_repairs_legacy_missing_start_fields_from_previous_end(self) -> None:
        rows = make_rows()
        previous = rows[-2]
        previous["target_valid"] = "false"
        previous["target_quality_flag"] = "missing_start_boundary"
        previous["proxy_end_price"] = "100.50000000"
        previous["proxy_end_interval_start_utc"] = "2026-07-27T23:54:59.000Z"
        previous["proxy_end_available_at_utc"] = "2026-07-27T23:55:01.000000Z"
        final_row = rows[-1]
        final_row["proxy_start_price"] = ""
        final_row["proxy_start_interval_start_utc"] = ""
        final_row["proxy_start_available_at_utc"] = ""

        boundary = datetime(2026, 7, 27, 23, 59, 59, tzinfo=timezone.utc)
        boundary_ms = int(boundary.timestamp() * 1000)
        patched, details = patch_rows(
            rows,
            {
                boundary_ms: {
                    "boundary_start_ms": boundary_ms,
                    "target_day": "2026-07-27",
                    "close": 101.0,
                    "available_at": datetime(2026, 7, 28, tzinfo=timezone.utc),
                    "source_group": "2026-07-28",
                    "source_file": "binance_raw_events_2026-07-28.jsonl.gz",
                }
            },
        )

        recovered = patched[-1]
        self.assertEqual(details["recovered_rows"], 1)
        self.assertEqual(details["review_rows"], [])
        self.assertEqual(recovered["proxy_start_price"], "100.50000000")
        self.assertEqual(
            recovered["proxy_start_interval_start_utc"],
            "2026-07-27T23:54:59.000Z",
        )
        self.assertEqual(recovered["label"], "UP")
        self.assertEqual(details["recovered_boundaries"][0]["start_source"], "previous_window_end")

    def test_cli_is_resumable_and_does_not_modify_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_dir = root / "input"
            output_dir = root / "output"
            input_dir.mkdir()
            input_path = input_dir / "2026-07-27.csv"
            rows = make_rows()
            previous = rows[-2]
            previous["proxy_end_price"] = "100.50000000"
            previous["proxy_end_interval_start_utc"] = "2026-07-27T23:54:59.000Z"
            previous["proxy_end_available_at_utc"] = "2026-07-27T23:55:01.000000Z"
            final_row = rows[-1]
            final_row["proxy_start_price"] = ""
            final_row["proxy_start_interval_start_utc"] = ""
            final_row["proxy_start_available_at_utc"] = ""
            with input_path.open("w", newline="", encoding="utf-8") as output:
                writer = csv.DictWriter(output, fieldnames=FIELDNAMES)
                writer.writeheader()
                writer.writerows(rows)
            original_bytes = input_path.read_bytes()

            boundary = datetime(2026, 7, 27, 23, 59, 59, tzinfo=timezone.utc)
            report_path = root / "boundary-report.json"
            report_path.write_text(
                json.dumps(
                    [
                        {
                            "target_day": "2026-07-27",
                            "boundary_start_ms": int(boundary.timestamp() * 1000),
                            "sources": [
                                {
                                    "source_group": "2026-07-28",
                                    "source_file": "binance_raw_events_2026-07-28.jsonl.gz",
                                    "close": "101.0",
                                    "received_at_utc": "2026-07-28T00:00:00.000000Z",
                                }
                            ],
                            "recoverable": True,
                        }
                    ]
                ),
                encoding="utf-8",
            )
            output_report = root / "recovery-report.json"
            command = [
                sys.executable,
                str(SCRIPTS_DIR / "apply_proxy_boundary_recovery.py"),
                "--input-dir",
                str(input_dir),
                "--output-dir",
                str(output_dir),
                "--boundary-report",
                str(report_path),
                "--output-report",
                str(output_report),
            ]
            first = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            second = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(input_path.read_bytes(), original_bytes)
            report = json.loads(output_report.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "completed")
            self.assertEqual(report["totals"]["recovered_rows"], 1)
            self.assertEqual(report["totals"]["review_rows"], 0)
            self.assertTrue((output_dir / input_path.name).is_file())


if __name__ == "__main__":
    unittest.main()
