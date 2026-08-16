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

from build_binance_15m_dataset import Bar, iso_from_minute, minute_of  # noqa: E402
from build_binance_hourly_dataset import (  # noqa: E402
    AUDIT_FIELDS,
    FEATURE_FIELDS,
    build_row,
)
from download_binance_klines import FIELDNAMES, sha256_file  # noqa: E402


def make_bars(decision_minute: int) -> dict[int, Bar]:
    bars: dict[int, Bar] = {}
    for minute in range(decision_minute - 65, decision_minute + 60):
        price = 100.0 + (minute - (decision_minute - 65)) * 0.01
        bars[minute] = Bar(
            minute=minute,
            open=price,
            high=price + 0.02,
            low=price - 0.02,
            close=price + 0.01,
            volume=100.0 + (minute % 7),
        )
    return bars


class HistoricalHourlyDatasetTests(unittest.TestCase):
    def test_one_hour_target_does_not_change_features_when_future_changes(self) -> None:
        decision = datetime(2026, 1, 2, 10, tzinfo=timezone.utc)
        decision_minute = minute_of(decision)
        bars = make_bars(decision_minute)
        baseline = build_row(bars, decision)
        self.assertEqual(baseline["feature_row_usable"], "true")
        self.assertEqual(baseline["target_valid"], "true")
        self.assertEqual(baseline["label"], "UP")

        future_changed = dict(bars)
        for minute in range(decision_minute, decision_minute + 60):
            original = future_changed[minute]
            future_changed[minute] = Bar(
                minute=minute,
                open=original.open,
                high=10_000.0,
                low=1.0,
                close=10_000.0,
                volume=1_000_000.0,
            )
        changed = build_row(future_changed, decision)

        for field in FEATURE_FIELDS:
            self.assertEqual(changed[field], baseline[field], field)
        self.assertNotEqual(changed["target_end_price"], baseline["target_end_price"])

    def test_missing_one_hour_target_boundary_is_preserved(self) -> None:
        decision = datetime(2026, 1, 2, 10, tzinfo=timezone.utc)
        bars = make_bars(minute_of(decision))
        bars.pop(minute_of(decision) + 59)

        row = build_row(bars, decision)

        self.assertEqual(row["feature_row_usable"], "true")
        self.assertEqual(row["target_valid"], "false")
        self.assertEqual(row["target_quality_flag"], "missing_end_boundary")
        self.assertEqual(row["eligible_for_model"], "false")

    def test_builder_uses_explicit_date_boundaries_and_hourly_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw_dir = root / "raw"
            raw_dir.mkdir()
            raw_days = [
                datetime(2025, 12, 31, tzinfo=timezone.utc).date(),
                datetime(2026, 1, 1, tzinfo=timezone.utc).date(),
                datetime(2026, 1, 2, tzinfo=timezone.utc).date(),
                datetime(2026, 1, 3, tzinfo=timezone.utc).date(),
            ]
            report_days = []
            global_start = datetime(2025, 12, 31, tzinfo=timezone.utc)
            for day in raw_days:
                path = raw_dir / f"binance_{day.isoformat()}.csv"
                day_start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
                with path.open("w", newline="", encoding="utf-8") as output:
                    writer = csv.DictWriter(output, fieldnames=FIELDNAMES)
                    writer.writeheader()
                    for offset in range(1440):
                        timestamp = day_start + timedelta(minutes=offset)
                        open_ms = int(timestamp.timestamp() * 1000)
                        elapsed_minutes = int((timestamp - global_start).total_seconds() // 60)
                        close = 100.0 + elapsed_minutes / 10_000.0
                        writer.writerow({
                            "open_time_utc": iso_from_minute(open_ms // 60_000),
                            "open": f"{close:.8f}",
                            "high": f"{close + 0.01:.8f}",
                            "low": f"{close - 0.01:.8f}",
                            "close": f"{close:.8f}",
                            "volume": "100.0",
                            "close_time_utc": datetime.fromtimestamp(
                                (open_ms + 59_999) / 1000, tz=timezone.utc
                            ).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                            "quote_volume": "10000.0",
                            "trade_count": "10",
                            "taker_buy_base_volume": "50.0",
                            "taker_buy_quote_volume": "5000.0",
                        })
                report_days.append({
                    "path": str(path),
                    "sha256": sha256_file(path),
                    "rows": 1440,
                })

            download_report = root / "download.json"
            download_report.write_text(json.dumps({
                "status": "completed",
                "config": {"symbol": "BTCUSDT", "interval": "1m"},
                "days": report_days,
            }), encoding="utf-8")
            output_dir = root / "dataset"
            command = [
                sys.executable,
                str(SCRIPTS_DIR / "build_binance_hourly_dataset.py"),
                "--raw-dir", str(raw_dir),
                "--download-report", str(download_report),
                "--target-start", "2026-01-01",
                "--target-end", "2026-01-04",
                "--train-end", "2026-01-02",
                "--validation-end", "2026-01-03",
                "--output-dir", str(output_dir),
                "--checkpoint", str(root / "checkpoint.json"),
                "--report", str(root / "dataset-report.json"),
                "--split-report", str(root / "split-report.json"),
            ]
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads((root / "dataset-report.json").read_text())
            split = json.loads((root / "split-report.json").read_text())
            self.assertEqual(report["config"]["horizon_minutes"], 60)
            self.assertEqual(report["config"]["cadence_minutes"], 60)
            self.assertEqual(report["totals"]["audit_rows"], 72)
            self.assertEqual(report["totals"]["model_rows_usable"], 72)
            self.assertEqual(split["totals"]["train_rows"], 24)
            self.assertEqual(split["totals"]["validation_rows"], 24)
            self.assertEqual(split["totals"]["holdout_rows"], 24)
            self.assertTrue(split["verification"]["chronological_model_keys"])
            with (output_dir / "dataset-audit-v1.csv").open(newline="", encoding="utf-8") as source:
                self.assertEqual(csv.DictReader(source).fieldnames, AUDIT_FIELDS)

            rerun = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(rerun.returncode, 0, rerun.stderr)
            self.assertIn("existing verified output; skipping", rerun.stdout)


if __name__ == "__main__":
    unittest.main()
