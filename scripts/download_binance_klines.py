#!/usr/bin/env python3
"""Download historical Binance 1-minute klines with Drive-friendly checkpoints."""

from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
import time
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


INTERVAL = "1m"
INTERVAL_MS = 60_000
API_LIMIT = 1000
FIELDNAMES = [
    "open_time_utc",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time_utc",
    "quote_volume",
    "trade_count",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
]
CHECKPOINT_SCHEMA_VERSION = 1
REPORT_SCHEMA_VERSION = 1
IMPLEMENTATION_VERSION = "historical-binance-download-2026-08-15-v1"
DEFAULT_BASE_URL = "https://data-api.binance.vision/api/v3/klines"


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as temporary:
        json.dump(payload, temporary, indent=2)
        temporary.write("\n")
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)


def atomic_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        newline="",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as temporary:
        writer = csv.DictWriter(temporary, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_day(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"not an ISO UTC date: {value}") from error


def iso_from_ms(value: int) -> str:
    return (
        datetime.fromtimestamp(value / 1000, tz=timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def day_bounds(day_value: date) -> tuple[int, int]:
    start = datetime(day_value.year, day_value.month, day_value.day, tzinfo=timezone.utc)
    start_ms = int(start.timestamp() * 1000)
    return start_ms, start_ms + 86_400_000


def normalize_payload(payload: list[list[Any]], day_value: date) -> list[dict[str, str]]:
    day_start, day_end = day_bounds(day_value)
    rows: list[dict[str, str]] = []
    for item in payload:
        if len(item) != 12:
            raise ValueError(f"unexpected Binance kline length: {len(item)}")
        open_ms = int(item[0])
        if not day_start <= open_ms < day_end:
            raise ValueError(f"API returned kline outside requested day: {open_ms}")
        rows.append(
            {
                "open_time_utc": iso_from_ms(open_ms),
                "open": str(item[1]),
                "high": str(item[2]),
                "low": str(item[3]),
                "close": str(item[4]),
                "volume": str(item[5]),
                "close_time_utc": iso_from_ms(int(item[6])),
                "quote_volume": str(item[7]),
                "trade_count": str(item[8]),
                "taker_buy_base_volume": str(item[9]),
                "taker_buy_quote_volume": str(item[10]),
            }
        )
    rows.sort(key=lambda row: row["open_time_utc"])
    keys = [row["open_time_utc"] for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError(f"duplicate kline open times for {day_value}")
    if keys != sorted(keys):
        raise ValueError(f"kline open times are not chronological for {day_value}")
    return rows


def fetch_page(
    base_url: str,
    symbol: str,
    start_ms: int,
    end_ms: int,
    opener=urlopen,
) -> list[list[Any]]:
    query = urlencode(
        {
            "symbol": symbol,
            "interval": INTERVAL,
            "startTime": start_ms,
            "endTime": end_ms - 1,
            "limit": API_LIMIT,
        }
    )
    request = Request(f"{base_url}?{query}", headers={"User-Agent": "tradingbot-data/0.9"})
    with opener(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if isinstance(payload, dict):
        raise ValueError(f"Binance API error: {payload}")
    if not isinstance(payload, list):
        raise ValueError("Binance API response is not a list")
    return payload


def fetch_day(
    day_value: date,
    symbol: str,
    base_url: str,
    request_delay_seconds: float,
) -> list[dict[str, str]]:
    day_start, day_end = day_bounds(day_value)
    cursor = day_start
    raw_items: list[list[Any]] = []
    while cursor < day_end:
        payload = fetch_page(base_url, symbol, cursor, day_end)
        if not payload:
            break
        raw_items.extend(payload)
        last_start = int(payload[-1][0])
        next_cursor = last_start + INTERVAL_MS
        if next_cursor <= cursor:
            raise ValueError(f"Binance cursor did not advance for {day_value}")
        cursor = next_cursor
        if request_delay_seconds:
            time.sleep(request_delay_seconds)
    return normalize_payload(raw_items, day_value)


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != FIELDNAMES:
            raise ValueError(f"unexpected fields in {path.name}: {reader.fieldnames}")
        return list(reader)


def verified_output(path: Path, expected_sha256: str | None) -> bool:
    if not path.is_file() or not expected_sha256:
        return False
    try:
        rows = load_rows(path)
        return bool(rows) and sha256_file(path) == expected_sha256
    except (OSError, csv.Error, ValueError):
        return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--start-date", required=True, help="inclusive UTC date")
    parser.add_argument("--end-date", required=True, help="exclusive UTC date")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--request-delay-seconds", default=0.1, type=float)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start_day = parse_day(args.start_date)
    end_day = parse_day(args.end_date)
    if end_day <= start_day:
        raise SystemExit("error: end date must be after start date")
    output_dir = args.output_dir.resolve()
    checkpoint_path = args.checkpoint.resolve()
    report_path = args.report.resolve()
    days = [
        start_day + timedelta(days=offset)
        for offset in range((end_day - start_day).days)
    ]
    config = {
        "implementation_version": IMPLEMENTATION_VERSION,
        "symbol": args.symbol,
        "interval": INTERVAL,
        "start_date": start_day.isoformat(),
        "end_date_exclusive": end_day.isoformat(),
        "base_url": args.base_url,
    }
    state: dict[str, Any] = {
        "checkpoint_schema_version": CHECKPOINT_SCHEMA_VERSION,
        "config": config,
        "completed_days": {},
    }
    if checkpoint_path.is_file():
        try:
            candidate = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            if (
                candidate.get("checkpoint_schema_version") == CHECKPOINT_SCHEMA_VERSION
                and candidate.get("config") == config
                and isinstance(candidate.get("completed_days"), dict)
            ):
                state = candidate
                print("resuming checkpoint:", checkpoint_path)
        except (OSError, json.JSONDecodeError):
            pass

    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        for day_value in days:
            day = day_value.isoformat()
            output_path = output_dir / f"{day}.csv"
            previous = state["completed_days"].get(day, {})
            if verified_output(output_path, previous.get("sha256")):
                print(f"{day}: existing verified output; skipping")
                continue
            print(f"{day}: downloading")
            rows = fetch_day(
                day_value,
                args.symbol,
                args.base_url,
                args.request_delay_seconds,
            )
            atomic_csv(output_path, rows)
            result = {
                "status": "completed",
                "path": str(output_path),
                "sha256": sha256_file(output_path),
                "rows": len(rows),
                "first_open_time_utc": rows[0]["open_time_utc"] if rows else None,
                "last_open_time_utc": rows[-1]["open_time_utc"] if rows else None,
            }
            state["completed_days"][day] = result
            atomic_json(checkpoint_path, state)
            print(f"{day}: checkpoint saved; rows: {len(rows)}")
    except KeyboardInterrupt:
        atomic_json(checkpoint_path, state)
        print("interrupted safely; rerun to resume from the checkpoint")
        return 2
    except (OSError, ValueError, csv.Error) as error:
        atomic_json(checkpoint_path, state)
        raise SystemExit(f"error: {error}") from error

    missing = [day.isoformat() for day in days if day.isoformat() not in state["completed_days"]]
    if missing:
        atomic_json(checkpoint_path, state)
        raise SystemExit(f"error: incomplete download; missing days: {missing[:5]}")
    report = {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "implementation_version": IMPLEMENTATION_VERSION,
        "status": "completed",
        "config": config,
        "output_dir": str(output_dir),
        "checkpoint": str(checkpoint_path),
        "days": [state["completed_days"][day.isoformat()] for day in days],
        "totals": {
            "days": len(days),
            "rows": sum(state["completed_days"][day.isoformat()]["rows"] for day in days),
        },
        "availability_policy": "interval_complete_assumption",
        "receipt_time_available": False,
    }
    atomic_json(report_path, report)
    print("download report:", report_path)
    print(json.dumps(report["totals"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
