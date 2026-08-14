#!/usr/bin/env python3
"""Inspect closed Binance one-second klines without extracting the archive."""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


CSV_FIELDS = (
    "interval_start_utc",
    "interval_end_utc",
    "close",
    "previous_close",
    "return_1s",
    "available_at_utc",
    "consecutive_with_previous",
    "feature_valid",
    "quality_flag",
)


def iso_from_ms(value: int) -> str:
    """Convert a Unix timestamp in milliseconds to an ISO-8601 UTC string."""

    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")


def find_binance_member(archive: zipfile.ZipFile, requested: str | None) -> str:
    names = archive.namelist()
    if requested is not None:
        if requested not in names:
            raise ValueError(f"Archive member not found: {requested}")
        return requested

    candidates = [
        name
        for name in names
        if name.startswith("binance_raw_events_") and name.endswith(".jsonl.gz")
    ]
    if len(candidates) != 1:
        raise ValueError(
            "Could not select one Binance member automatically; "
            "pass --member explicitly."
        )
    return candidates[0]


def iter_json_records(
    archive: zipfile.ZipFile, member_name: str
) -> Iterator[dict[str, Any]]:
    with archive.open(member_name, "r") as compressed_member:
        with gzip.GzipFile(fileobj=compressed_member) as gzip_stream:
            with io.TextIOWrapper(gzip_stream, encoding="utf-8") as text_stream:
                for line in text_stream:
                    if line.strip():
                        yield json.loads(line)


def inspect_klines(
    archive_path: Path, member_name: str | None, limit: int, model_only: bool
) -> tuple[list[dict[str, Any]], dict[str, int], str]:
    rows: list[dict[str, Any]] = []
    counters = {
        "records_scanned": 0,
        "malformed_json": 0,
        "kline_records": 0,
        "closed_klines": 0,
        "gaps_or_nonconsecutive": 0,
        "invalid_rows_seen": 0,
        "invalid_rows_excluded": 0,
        "model_rows_emitted": 0,
    }
    previous: tuple[int, float] | None = None

    with zipfile.ZipFile(archive_path) as archive:
        selected_member = find_binance_member(archive, member_name)
        records = iter_json_records(archive, selected_member)

        while len(rows) < limit:
            try:
                record = next(records)
            except StopIteration:
                break
            except json.JSONDecodeError:
                counters["malformed_json"] += 1
                continue

            counters["records_scanned"] += 1
            if record.get("stream") != "btcusdt@kline_1s":
                continue
            counters["kline_records"] += 1

            raw_event = record.get("raw_event", {})
            kline = raw_event.get("k", {})
            if kline.get("x") is not True:
                continue
            counters["closed_klines"] += 1

            start_ms = int(kline["t"])
            end_ms = int(kline["T"])
            close = float(kline["c"])
            available_at = record["received_at_utc"]

            consecutive = previous is not None and start_ms == previous[0] + 1000
            if previous is not None and not consecutive:
                counters["gaps_or_nonconsecutive"] += 1

            return_1s = None
            previous_close = None
            if previous is not None:
                previous_close = previous[1]
                if consecutive:
                    return_1s = (close - previous_close) / previous_close

            if previous is None:
                quality_flag = "no_previous_kline"
            elif not consecutive:
                quality_flag = "nonconsecutive_previous_kline"
            else:
                quality_flag = "valid_consecutive_kline"

            row = {
                "interval_start_utc": iso_from_ms(start_ms),
                "interval_end_utc": iso_from_ms(end_ms),
                "close": f"{close:.8f}",
                "previous_close": "" if previous_close is None else f"{previous_close:.8f}",
                "return_1s": "" if return_1s is None else f"{return_1s:.10f}",
                "available_at_utc": available_at,
                "consecutive_with_previous": str(consecutive).lower(),
                "feature_valid": str(consecutive).lower(),
                "quality_flag": quality_flag,
            }
            if consecutive:
                rows.append(row)
                counters["model_rows_emitted"] += 1
            else:
                counters["invalid_rows_seen"] += 1
                if model_only:
                    counters["invalid_rows_excluded"] += 1
                else:
                    rows.append(row)
            previous = (start_ms, close)

    return rows, counters, selected_member


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--member", help="ZIP member; auto-detected when omitted")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument(
        "--model-only",
        action="store_true",
        help="exclude rows whose required return feature is invalid",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit < 1:
        raise SystemExit("--limit must be at least 1")

    try:
        rows, counters, selected_member = inspect_klines(
            args.archive, args.member, args.limit, args.model_only
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        raise SystemExit(f"error: {error}") from error

    writer = csv.DictWriter(sys.stdout, fieldnames=CSV_FIELDS)
    writer.writeheader()
    writer.writerows(rows)

    print(f"member: {selected_member}", file=sys.stderr)
    for name, value in counters.items():
        print(f"{name}: {value}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
