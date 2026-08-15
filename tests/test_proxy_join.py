from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from build_binance_feature_view import FIELDNAMES as FEATURE_FIELDNAMES  # noqa: E402
from build_binance_proxy_targets import FIELDNAMES as TARGET_FIELDNAMES  # noqa: E402
from build_proxy_join import MODEL_COLUMNS  # noqa: E402


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def feature_row(window_start: str, usable: str) -> dict[str, str]:
    row = {field: "" for field in FEATURE_FIELDNAMES}
    row.update(
        {
            "window_start_utc": window_start,
            "decision_time_utc": window_start,
            "feature_row_usable": usable,
            "return_1s": "0.0010000000" if usable == "true" else "",
            "return_1m": "0.0020000000" if usable == "true" else "",
            "volatility_1m": "0.0005000000" if usable == "true" else "",
        }
    )
    return row


def target_row(window_start: str) -> dict[str, str]:
    row = {field: "" for field in TARGET_FIELDNAMES}
    row.update(
        {
            "window_start_utc": window_start,
            "decision_time_utc": window_start,
            "label": "UP",
            "label_source": "binance_proxy",
            "label_definition": "end_price_gte_start_price",
            "target_valid": "true",
            "target_quality_flag": "valid_proxy_target",
        }
    )
    return row


class ProxyJoinTests(unittest.TestCase):
    def command(self, root: Path) -> list[str]:
        return [
            sys.executable,
            str(SCRIPTS_DIR / "build_proxy_join.py"),
            "--feature-dir",
            str(root / "features"),
            "--target-dir",
            str(root / "targets"),
            "--audit-output-dir",
            str(root / "audit"),
            "--model-output-dir",
            str(root / "model"),
            "--output-report",
            str(root / "join-report.json"),
        ]

    def test_join_preserves_audit_rows_and_filters_model_view(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "features").mkdir()
            (root / "targets").mkdir()
            target_keys = [
                "2026-07-27T00:00:00.000Z",
                "2026-07-27T00:05:00.000Z",
            ]
            feature_keys = [
                "2026-07-27T00:00:00.000000Z",
                "2026-07-27T00:05:00.000000Z",
            ]
            write_rows(
                root / "features" / "2026-07-27.csv",
                FEATURE_FIELDNAMES,
                [
                    feature_row(feature_keys[0], "true"),
                    feature_row(feature_keys[1], "false"),
                ],
            )
            write_rows(
                root / "targets" / "2026-07-27.csv",
                TARGET_FIELDNAMES,
                [target_row(target_keys[0]), target_row(target_keys[1])],
            )

            first = subprocess.run(
                self.command(root), cwd=ROOT, capture_output=True, text=True
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            second = subprocess.run(
                self.command(root), cwd=ROOT, capture_output=True, text=True
            )
            self.assertEqual(second.returncode, 0, second.stderr)

            with (root / "audit" / "2026-07-27.csv").open(
                newline="", encoding="utf-8"
            ) as source:
                audit_rows = list(csv.DictReader(source))
            with (root / "model" / "2026-07-27.csv").open(
                newline="", encoding="utf-8"
            ) as source:
                model_reader = csv.DictReader(source)
                model_rows = list(model_reader)
            self.assertEqual(len(audit_rows), 2)
            self.assertEqual(len(model_rows), 1)
            self.assertEqual(model_reader.fieldnames, MODEL_COLUMNS)
            self.assertEqual(audit_rows[1]["eligible_for_model"], "false")
            self.assertEqual(audit_rows[1]["eligibility_reason"], "invalid_feature")
            self.assertNotIn("target_proxy_end_price", MODEL_COLUMNS)
            self.assertNotIn("target_target_available_at_utc", MODEL_COLUMNS)
            report = json.loads((root / "join-report.json").read_text())
            self.assertEqual(report["status"], "completed")
            self.assertEqual(report["totals"]["eligible_rows"], 1)

    def test_duplicate_key_stops_join(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "features").mkdir()
            (root / "targets").mkdir()
            key = "2026-07-27T00:00:00.000Z"
            write_rows(
                root / "features" / "2026-07-27.csv",
                FEATURE_FIELDNAMES,
                [feature_row(key, "true"), feature_row(key, "true")],
            )
            write_rows(
                root / "targets" / "2026-07-27.csv",
                TARGET_FIELDNAMES,
                [target_row(key)],
            )
            completed = subprocess.run(
                self.command(root), cwd=ROOT, capture_output=True, text=True
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn("duplicate window_start_utc", completed.stderr)
            report = json.loads((root / "join-report.json").read_text())
            self.assertEqual(report["status"], "review")
            self.assertEqual(list((root / "audit").glob("*.csv")), [])


if __name__ == "__main__":
    unittest.main()
