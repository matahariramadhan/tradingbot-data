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

from build_proxy_join import MODEL_COLUMNS  # noqa: E402


def write_model_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=MODEL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def model_row(key: str) -> dict[str, str]:
    return {
        "window_start_utc": key,
        "decision_time_utc": key,
        "return_1s": "0.0010000000",
        "return_1m": "0.0020000000",
        "volatility_1m": "0.0005000000",
        "label": "UP",
        "label_source": "binance_proxy",
        "label_definition": "end_price_gte_start_price",
    }


class ChronologicalProxySplitTests(unittest.TestCase):
    def command(self, root: Path, train_day_count: int = 2) -> list[str]:
        return [
            sys.executable,
            str(SCRIPTS_DIR / "build_chronological_proxy_split.py"),
            "--model-dir",
            str(root / "model"),
            "--review-report",
            str(root / "review.json"),
            "--output-report",
            str(root / "split.json"),
            "--train-day-count",
            str(train_day_count),
        ]

    def write_fixture(self, root: Path) -> None:
        (root / "model").mkdir()
        days = ["2026-07-01", "2026-07-02", "2026-07-03"]
        for day in days:
            write_model_rows(
                root / "model" / f"{day}.csv",
                [model_row(f"{day}T00:00:00.000Z")],
            )
        (root / "review.json").write_text(
            json.dumps(
                {
                    "status": "completed",
                    "days": [{"day": day} for day in days],
                    "totals": {"model_rows": 3},
                }
            ),
            encoding="utf-8",
        )

    def test_builds_split_and_verifies_zero_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            completed = subprocess.run(
                self.command(root), cwd=ROOT, capture_output=True, text=True
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads((root / "split.json").read_text())
            self.assertEqual(report["status"], "completed")
            self.assertEqual(report["train_days"], ["2026-07-01", "2026-07-02"])
            self.assertEqual(report["evaluation_days"], ["2026-07-03"])
            self.assertEqual(report["totals"], {
                "model_rows": 3,
                "train_rows": 2,
                "evaluation_rows": 1,
            })
            self.assertEqual(
                report["verification"]["train_evaluation_overlap_keys"], 0
            )
            self.assertTrue(
                report["verification"]["train_end_before_evaluation_start"]
            )

    def test_rejects_key_outside_declared_day(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            write_model_rows(
                root / "model" / "2026-07-02.csv",
                [model_row("2026-07-03T00:00:00.000Z")],
            )
            completed = subprocess.run(
                self.command(root), cwd=ROOT, capture_output=True, text=True
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn("outside its day", completed.stderr)
            report = json.loads((root / "split.json").read_text())
            self.assertEqual(report["status"], "review")


if __name__ == "__main__":
    unittest.main()
