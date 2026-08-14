#!/usr/bin/env python3
"""Audit one day's Binance streams and closed one-second kline coverage."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from .binance_source import describe_binance_source, iter_json_records
except ImportError:
    from binance_source import describe_binance_source, iter_json_records


def parse_utc(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def iso_from_ms(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")


def audit(
    archive_path: Path,
    member_name: str | None,
    day_start: datetime,
    duration_seconds: int,
) -> tuple[dict[str, Any], str]:
    day_end = day_start + timedelta(seconds=duration_seconds)
    day_start_ms = int(day_start.timestamp() * 1000)
    day_end_ms = int(day_end.timestamp() * 1000)
    stream_counts: Counter[str] = Counter()
    counters = Counter()
    starts_in_window: set[int] = set()
    first_closed_start: int | None = None
    last_closed_start: int | None = None
    previous_start: int | None = None
    first_receipt: str | None = None
    last_receipt: str | None = None
    max_gap_ms = 0
    gap_events = 0

    selected_member = describe_binance_source(archive_path, member_name)
    for record in iter_json_records(archive_path, member_name):
        if record is None:
            counters["malformed_json"] += 1
            continue
        counters["records_scanned"] += 1
        stream = record.get("stream", "<missing>")
        stream_counts[stream] += 1
        receipt = record.get("received_at_utc")
        if isinstance(receipt, str):
            if first_receipt is None:
                first_receipt = receipt
            last_receipt = receipt

        if stream != "btcusdt@kline_1s":
            continue
        counters["kline_records"] += 1

        raw_event = record.get("raw_event", {})
        kline = raw_event.get("k", {})
        if kline.get("x") is not True:
            continue
        counters["closed_klines"] += 1

        start_ms = int(kline["t"])
        if not day_start_ms <= start_ms < day_end_ms:
            continue
        counters["closed_klines_in_window"] += 1

        if start_ms in starts_in_window:
            counters["duplicate_starts"] += 1
            continue
        starts_in_window.add(start_ms)

        if first_closed_start is None:
            first_closed_start = start_ms
        if previous_start is not None:
            delta_ms = start_ms - previous_start
            if delta_ms < 0:
                counters["backward_starts"] += 1
            elif delta_ms > 1000:
                gap_events += 1
                max_gap_ms = max(max_gap_ms, delta_ms - 1000)
        if previous_start is None or start_ms > previous_start:
            previous_start = start_ms
            last_closed_start = start_ms

    expected = duration_seconds
    unique_count = len(starts_in_window)
    summary = {
        "archive": str(archive_path),
        "member": selected_member,
        "receipt_coverage": {"first": first_receipt, "last": last_receipt},
        "stream_counts": dict(sorted(stream_counts.items())),
        "records_scanned": counters["records_scanned"],
        "malformed_json": counters["malformed_json"],
        "kline_records": counters["kline_records"],
        "closed_klines_total": counters["closed_klines"],
        "closed_klines_in_window": counters["closed_klines_in_window"],
        "unique_closed_starts_in_window": unique_count,
        "expected_closed_starts_in_window": expected,
        "missing_starts_in_window": expected - unique_count,
        "duplicate_starts_in_window": counters["duplicate_starts"],
        "backward_starts_in_window": counters["backward_starts"],
        "gap_events_in_window": gap_events,
        "largest_missing_gap_seconds": max_gap_ms / 1000,
        "first_closed_start_in_window": (
            None if first_closed_start is None else iso_from_ms(first_closed_start)
        ),
        "last_closed_start_in_window": (
            None if last_closed_start is None else iso_from_ms(last_closed_start)
        ),
    }
    return summary, selected_member


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--day-start", required=True, help="ISO-8601 UTC day start")
    parser.add_argument("--member", help="ZIP member; auto-detected when omitted")
    parser.add_argument("--duration-seconds", type=int, default=86400)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.duration_seconds < 1:
        raise SystemExit("--duration-seconds must be at least 1")

    try:
        summary, _ = audit(
            args.archive,
            args.member,
            parse_utc(args.day_start),
            args.duration_seconds,
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        raise SystemExit(f"error: {error}") from error

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
