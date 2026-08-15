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

from build_proxy_join import AUDIT_FIELDNAMES, MODEL_COLUMNS  # noqa: E402


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def audit_row(key: str, eligible: str, reason: str) -> dict[str, str]:
    row = {field: "" for field in AUDIT_FIELDNAMES}
    row.update(
        {
            "window_start_utc": key,
            "feature_row_present": "true",
            "target_row_present": "true",
            "feature_row_usable": "true" if eligible == "true" else "false",
            "target_valid": "true",
            "eligible_for_model": eligible,
            "eligibility_reason": reason,
            "feature_feature_quality_flag": "valid_consecutive_kline",
            "target_target_quality_flag": "valid_proxy_target",
            "target_label_source": "binance_proxy",
        }
    )
    return row


def model_row(key: str, label: str = "UP") -> dict[str, str]:
    return {
        "window_start_utc": key,
        "decision_time_utc": key,
        "return_1s": "0.0010000000",
        "return_1m": "0.0020000000",
        "volatility_1m": "0.0005000000",
        "label": label,
        "label_source": "binance_proxy",
        "label_definition": "end_price_gte_start_price",
    }


class ProxyModelReviewTests(unittest.TestCase):
    def command(self, root: Path) -> list[str]:
        return [
            sys.executable,
            str(SCRIPTS_DIR / "review_proxy_model_view.py"),
            "--audit-dir",
            str(root / "audit"),
            "--model-dir",
            str(root / "model"),
            "--output-report",
            str(root / "review.json"),
            "--excluded-output",
            str(root / "excluded.csv"),
        ]

    def test_review_reports_balance_stats_and_exclusions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "audit").mkdir()
            (root / "model").mkdir()
            keys = [
                "2026-07-27T00:00:00.000Z",
                "2026-07-27T00:05:00.000Z",
            ]
            write_rows(
                root / "audit" / "2026-07-27.csv",
                AUDIT_FIELDNAMES,
                [
                    audit_row(keys[0], "true", "eligible"),
                    audit_row(keys[1], "false", "invalid_feature"),
                ],
            )
            write_rows(
                root / "model" / "2026-07-27.csv",
                MODEL_COLUMNS,
                [model_row(keys[0], "UP")],
            )
            completed = subprocess.run(
                self.command(root), cwd=ROOT, capture_output=True, text=True
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads((root / "review.json").read_text())
            self.assertEqual(report["status"], "completed")
            self.assertEqual(report["totals"]["model_rows"], 1)
            self.assertEqual(report["totals"]["excluded_rows"], 1)
            self.assertEqual(report["totals"]["label_counts"], {"UP": 1})
            with (root / "excluded.csv").open(newline="") as source:
                excluded = list(csv.DictReader(source))
            self.assertEqual(excluded[0]["eligibility_reason"], "invalid_feature")

    def test_review_rejects_duplicate_model_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "audit").mkdir()
            (root / "model").mkdir()
            key = "2026-07-27T00:00:00.000Z"
            write_rows(
                root / "audit" / "2026-07-27.csv",
                AUDIT_FIELDNAMES,
                [audit_row(key, "true", "eligible")],
            )
            write_rows(
                root / "model" / "2026-07-27.csv",
                MODEL_COLUMNS,
                [model_row(key), model_row(key)],
            )
            completed = subprocess.run(
                self.command(root), cwd=ROOT, capture_output=True, text=True
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn("duplicate window_start_utc", completed.stderr)
            report = json.loads((root / "review.json").read_text())
            self.assertEqual(report["status"], "review")


if __name__ == "__main__":
    unittest.main()
