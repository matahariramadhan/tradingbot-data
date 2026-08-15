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

from build_binance_15m_dataset import (  # noqa: E402
    AUDIT_FIELDS,
    FEATURE_FIELDS,
    Bar,
    build_row,
    iso_from_minute,
    minute_of,
)
from download_binance_klines import (  # noqa: E402
    FIELDNAMES,
    normalize_payload,
    sha256_file,
)


def make_bars(decision_minute: int) -> dict[int, Bar]:
    bars: dict[int, Bar] = {}
    for minute in range(decision_minute - 65, decision_minute + 15):
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


class HistoricalBinance15mTests(unittest.TestCase):
    def test_normalize_payload_preserves_binance_ohlcv_fields(self) -> None:
        day = datetime(2026, 1, 1, tzinfo=timezone.utc).date()
        start_ms = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        payload = [[
            start_ms,
            "100.0",
            "101.0",
            "99.0",
            "100.5",
            "12.0",
            start_ms + 59_999,
            "1200.0",
            42,
            "6.0",
            "600.0",
            "0",
        ]]

        rows = normalize_payload(payload, day)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["open_time_utc"], "2026-01-01T00:00:00.000Z")
        self.assertEqual(rows[0]["close"], "100.5")
        self.assertEqual(set(rows[0]), set(FIELDNAMES))

    def test_features_do_not_use_future_bars(self) -> None:
        decision = datetime(2026, 1, 2, 10, 15, tzinfo=timezone.utc)
        decision_minute = minute_of(decision)
        bars = make_bars(decision_minute)
        baseline = build_row(bars, decision)
        self.assertEqual(baseline["feature_row_usable"], "true")
        self.assertEqual(baseline["target_valid"], "true")
        self.assertEqual(baseline["label"], "UP")

        future_changed = dict(bars)
        for minute in range(decision_minute, decision_minute + 15):
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

    def test_missing_target_boundary_is_preserved_and_ineligible(self) -> None:
        decision = datetime(2026, 1, 2, 10, 15, tzinfo=timezone.utc)
        bars = make_bars(minute_of(decision))
        bars.pop(minute_of(decision) + 14)

        row = build_row(bars, decision)

        self.assertEqual(row["feature_row_usable"], "true")
        self.assertEqual(row["target_valid"], "false")
        self.assertEqual(row["target_quality_flag"], "missing_end_boundary")
        self.assertEqual(row["eligible_for_model"], "false")

    def test_builder_writes_audited_rows_and_disjoint_chronological_split(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw_dir = root / "raw"
            raw_dir.mkdir()
            raw_days = [
                datetime(2026, 1, day, tzinfo=timezone.utc).date()
                for day in range(1, 5)
            ]
            report_days = []
            for day in raw_days:
                path = raw_dir / f"binance_{day.isoformat()}.csv"
                day_start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
                with path.open("w", newline="", encoding="utf-8") as output:
                    writer = csv.DictWriter(output, fieldnames=FIELDNAMES)
                    writer.writeheader()
                    for offset in range(1440):
                        open_ms = int((day_start + timedelta(minutes=offset)).timestamp() * 1000)
                        close = 100.0 + (offset / 10_000.0)
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
                str(SCRIPTS_DIR / "build_binance_15m_dataset.py"),
                "--raw-dir", str(raw_dir),
                "--download-report", str(download_report),
                "--target-start", "2026-01-02",
                "--target-end", "2026-01-05",
                "--output-dir", str(output_dir),
                "--checkpoint", str(root / "checkpoint.json"),
                "--report", str(root / "dataset-report.json"),
                "--split-report", str(root / "split-report.json"),
                "--train-day-count", "1",
                "--validation-day-count", "1",
            ]
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads((root / "dataset-report.json").read_text())
            split = json.loads((root / "split-report.json").read_text())
            self.assertEqual(report["totals"]["audit_rows"], 288)
            self.assertEqual(report["totals"]["model_rows_usable"], 288)
            self.assertEqual(split["totals"]["train_rows"], 96)
            self.assertEqual(split["totals"]["validation_rows"], 96)
            self.assertEqual(split["totals"]["holdout_rows"], 96)
            self.assertTrue(split["verification"]["model_keys_unique"])
            self.assertTrue(split["verification"]["chronological_model_keys"])
            with (output_dir / "dataset-audit-v1.csv").open(newline="", encoding="utf-8") as source:
                self.assertEqual(csv.DictReader(source).fieldnames, AUDIT_FIELDS)

            rerun = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(rerun.returncode, 0, rerun.stderr)
            self.assertIn("existing verified output; skipping", rerun.stdout)


if __name__ == "__main__":
    unittest.main()
