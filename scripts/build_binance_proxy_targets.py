#!/usr/bin/env python3
"""Build clean five-minute Binance proxy targets from closed one-second klines."""

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


FIELDNAMES = [
    "window_start_utc",
    "decision_time_utc",
    "window_end_utc",
    "proxy_start_price",
    "proxy_start_interval_start_utc",
    "proxy_start_available_at_utc",
    "proxy_end_price",
    "proxy_end_interval_start_utc",
    "proxy_end_available_at_utc",
    "target_available_at_utc",
    "label",
    "label_source",
    "label_definition",
    "target_valid",
    "target_quality_flag",
]


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def iso_from_ms(value: int) -> str:
    return (
        datetime.fromtimestamp(value / 1000, tz=timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


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
) -> Iterator[dict[str, Any] | None]:
    with archive.open(member_name, "r") as compressed_member:
        with gzip.GzipFile(fileobj=compressed_member) as gzip_stream:
            with io.TextIOWrapper(gzip_stream, encoding="utf-8") as text_stream:
                for line in text_stream:
                    if not line.strip():
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        yield None


def collect_closed_klines(
    archive_path: Path, member_name: str | None
) -> tuple[dict[int, list[dict[str, Any]]], str, dict[str, int]]:
    observations: dict[int, list[dict[str, Any]]] = {}
    counters = {
        "records_scanned": 0,
        "malformed_json": 0,
        "closed_klines": 0,
        "duplicate_closed_kline_starts": 0,
    }

    with zipfile.ZipFile(archive_path) as archive:
        selected_member = find_binance_member(archive, member_name)
        for record in iter_json_records(archive, selected_member):
            if record is None:
                counters["malformed_json"] += 1
                continue
            counters["records_scanned"] += 1
            if record.get("stream") != "btcusdt@kline_1s":
                continue

            kline = record.get("raw_event", {}).get("k", {})
            if kline.get("x") is not True:
                continue
            counters["closed_klines"] += 1

            start_ms = int(kline["t"])
            row = {
                "start_ms": start_ms,
                "close": float(kline["c"]),
                "available_at": parse_utc(record["received_at_utc"]),
            }
            previous = observations.setdefault(start_ms, [])
            if previous:
                counters["duplicate_closed_kline_starts"] += 1
            previous.append(row)

    return observations, selected_member, counters


def build_targets(
    observations: dict[int, list[dict[str, Any]]],
    window_start: datetime,
    window_end: datetime,
) -> tuple[list[dict[str, str]], dict[str, int]]:
    start_ms = int(window_start.timestamp() * 1000)
    end_ms = int(window_end.timestamp() * 1000)
    window_ms = 5 * 60 * 1000
    rows: list[dict[str, str]] = []
    counters = {
        "windows_requested": 0,
        "valid_targets": 0,
        "missing_start": 0,
        "missing_end": 0,
        "late_start": 0,
        "duplicate_boundary": 0,
    }

    for current_ms in range(start_ms, end_ms, window_ms):
        counters["windows_requested"] += 1
        target_end_ms = current_ms + window_ms
        start_observations = observations.get(current_ms - 1000, [])
        end_observations = observations.get(target_end_ms - 1000, [])
        row = {
            "window_start_utc": iso_from_ms(current_ms),
            "decision_time_utc": iso_from_ms(current_ms),
            "window_end_utc": iso_from_ms(target_end_ms),
            "proxy_start_price": "",
            "proxy_start_interval_start_utc": "",
            "proxy_start_available_at_utc": "",
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

        if len(start_observations) != 1 or len(end_observations) != 1:
            if len(start_observations) > 1 or len(end_observations) > 1:
                counters["duplicate_boundary"] += 1
                row["target_quality_flag"] = "duplicate_boundary_observation"
            elif not start_observations:
                counters["missing_start"] += 1
                row["target_quality_flag"] = "missing_start_boundary"
            else:
                counters["missing_end"] += 1
                row["target_quality_flag"] = "missing_end_boundary"
            rows.append(row)
            continue

        start_observation = start_observations[0]
        end_observation = end_observations[0]
        row["proxy_start_price"] = f'{start_observation["close"]:.8f}'
        row["proxy_start_interval_start_utc"] = iso_from_ms(
            start_observation["start_ms"]
        )
        row["proxy_start_available_at_utc"] = start_observation[
            "available_at"
        ].isoformat(timespec="microseconds").replace("+00:00", "Z")
        row["proxy_end_price"] = f'{end_observation["close"]:.8f}'
        row["proxy_end_interval_start_utc"] = iso_from_ms(
            end_observation["start_ms"]
        )
        row["proxy_end_available_at_utc"] = end_observation[
            "available_at"
        ].isoformat(timespec="microseconds").replace("+00:00", "Z")
        target_available_at = max(
            start_observation["available_at"], end_observation["available_at"]
        )
        row["target_available_at_utc"] = (
            target_available_at.isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )

        if start_observation["available_at"] > window_start:
            counters["late_start"] += 1
            row["target_quality_flag"] = "valid_target_late_start_boundary"
        else:
            row["target_quality_flag"] = "valid_proxy_target"
        row["label"] = (
            "UP"
            if end_observation["close"] >= start_observation["close"]
            else "DOWN"
        )
        row["target_valid"] = "true"
        counters["valid_targets"] += 1
        rows.append(row)

    return rows, counters


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--window-start", required=True)
    parser.add_argument("--window-end", required=True)
    parser.add_argument("--member", help="ZIP member; auto-detected when omitted")
    parser.add_argument("--output", type=Path, help="CSV output; stdout by default")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        window_start = parse_utc(args.window_start)
        window_end = parse_utc(args.window_end)
        if window_start >= window_end:
            raise ValueError("--window-start must be before --window-end")
        if any(
            (
                window_start.second,
                window_start.microsecond,
                window_start.minute % 5,
                window_end.second,
                window_end.microsecond,
                window_end.minute % 5,
            )
        ):
            raise ValueError("window boundaries must be aligned to five minutes")

        observations, member, scan_counters = collect_closed_klines(
            args.archive, args.member
        )
        rows, target_counters = build_targets(
            observations, window_start, window_end
        )
        output = args.output.open("w", newline="", encoding="utf-8") if args.output else sys.stdout
        try:
            writer = csv.DictWriter(output, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
        finally:
            if args.output:
                output.close()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        raise SystemExit(f"error: {error}") from error

    print(
        json.dumps(
            {
                "member": member,
                "scan_counters": scan_counters,
                "target_counters": target_counters,
            },
            indent=2,
        ),
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
