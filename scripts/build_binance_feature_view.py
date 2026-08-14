#!/usr/bin/env python3
"""Build a gap-aware Binance feature view at five-minute decision times."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from bisect import bisect_left
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import pstdev
from typing import Any

try:
    from .binance_source import describe_binance_source, iter_json_records
except ImportError:
    from binance_source import describe_binance_source, iter_json_records


FIELDNAMES = [
    "window_start_utc",
    "decision_time_utc",
    "window_end_utc",
    "latest_interval_start_utc",
    "latest_interval_end_utc",
    "latest_close",
    "latest_available_at_utc",
    "return_1s",
    "return_1s_valid",
    "return_1s_quality_flag",
    "return_1m",
    "return_1m_valid",
    "return_1m_quality_flag",
    "volatility_1m",
    "volatility_1m_valid",
    "volatility_1m_quality_flag",
    "feature_row_usable",
    "feature_quality_flag",
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


def iso_from_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(
        timespec="microseconds"
    ).replace("+00:00", "Z")


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

    selected_member = describe_binance_source(archive_path, member_name)
    for record in iter_json_records(archive_path, member_name):
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
        observation = {
            "start_ms": start_ms,
            "end_ms": int(kline["T"]),
            "close": float(kline["c"]),
            "available_at": parse_utc(record["received_at_utc"]),
        }
        bucket = observations.setdefault(start_ms, [])
        if bucket:
            counters["duplicate_closed_kline_starts"] += 1
        bucket.append(observation)

    return observations, selected_member, counters


def eligible_observation(
    observations: dict[int, list[dict[str, Any]]],
    start_ms: int,
    decision_ms: int,
) -> tuple[dict[str, Any] | None, str | None]:
    candidates = observations.get(start_ms, [])
    if not candidates:
        return None, "missing_kline"
    if len(candidates) != 1:
        return None, "duplicate_kline"

    observation = candidates[0]
    if observation["end_ms"] > decision_ms:
        return None, "incomplete_at_cutoff"
    if int(observation["available_at"].timestamp() * 1000) > decision_ms:
        return None, "received_after_cutoff"
    return observation, None


def make_row(
    window_start: datetime,
    window_end: datetime,
    observations: dict[int, list[dict[str, Any]]],
    sorted_starts: list[int],
    lookback_seconds: int,
) -> dict[str, str]:
    decision_ms = int(window_start.timestamp() * 1000)
    latest = None
    latest_reason = None
    index = bisect_left(sorted_starts, decision_ms) - 1
    while index >= 0:
        candidate_start_ms = sorted_starts[index]
        candidate, reason = eligible_observation(
            observations, candidate_start_ms, decision_ms
        )
        if candidate is not None:
            latest = candidate
            break
        latest_reason = reason
        index -= 1

    row = {
        "window_start_utc": window_start.isoformat().replace("+00:00", "Z"),
        "decision_time_utc": window_start.isoformat().replace("+00:00", "Z"),
        "window_end_utc": window_end.isoformat().replace("+00:00", "Z"),
        "latest_interval_start_utc": "",
        "latest_interval_end_utc": "",
        "latest_close": "",
        "latest_available_at_utc": "",
        "return_1s": "",
        "return_1s_valid": "false",
        "return_1s_quality_flag": "",
        "return_1m": "",
        "return_1m_valid": "false",
        "return_1m_quality_flag": "",
        "volatility_1m": "",
        "volatility_1m_valid": "false",
        "volatility_1m_quality_flag": "",
        "feature_row_usable": "false",
        "feature_quality_flag": "",
    }

    if latest is None:
        latest_flag = latest_reason or "missing_latest_kline"
        row["return_1s_quality_flag"] = latest_flag
        row["return_1m_quality_flag"] = latest_flag
        row["volatility_1m_quality_flag"] = latest_flag
        row["feature_quality_flag"] = latest_flag
        return row

    row["latest_interval_start_utc"] = iso_from_ms(latest["start_ms"])
    row["latest_interval_end_utc"] = iso_from_ms(latest["end_ms"])
    row["latest_close"] = f'{latest["close"]:.8f}'
    row["latest_available_at_utc"] = iso_from_datetime(
        latest["available_at"]
    )

    previous, previous_reason = eligible_observation(
        observations, latest["start_ms"] - 1000, decision_ms
    )
    if previous is None:
        row["return_1s_quality_flag"] = (
            previous_reason or "missing_previous_kline"
        )
    else:
        return_1s = (latest["close"] - previous["close"]) / previous["close"]
        row["return_1s"] = f"{return_1s:.10f}"
        row["return_1s_valid"] = "true"
        row["return_1s_quality_flag"] = "valid_consecutive_kline"

    history: list[dict[str, Any]] = []
    lookback_reasons: set[str] = set()
    first_start_ms = latest["start_ms"] - lookback_seconds * 1000
    for start_ms in range(first_start_ms, latest["start_ms"] + 1, 1000):
        observation, reason = eligible_observation(
            observations, start_ms, decision_ms
        )
        if observation is None:
            lookback_reasons.add(reason or "invalid_lookback_kline")
        else:
            history.append(observation)

    if len(history) != lookback_seconds + 1:
        lookback_flag = ";".join(sorted(lookback_reasons))
        if not lookback_flag:
            lookback_flag = "insufficient_eligible_history"
        row["return_1m_quality_flag"] = lookback_flag
        row["volatility_1m_quality_flag"] = lookback_flag
    else:
        returns = [
            (current["close"] - previous["close"]) / previous["close"]
            for previous, current in zip(history, history[1:])
        ]
        return_1m = returns[-1]
        row["return_1m"] = f"{return_1m:.10f}"
        row["return_1m_valid"] = "true"
        row["return_1m_quality_flag"] = "valid_consecutive_lookback"
        row["volatility_1m"] = f"{pstdev(returns):.10f}"
        row["volatility_1m_valid"] = "true"
        row["volatility_1m_quality_flag"] = (
            "valid_consecutive_lookback"
        )

    usable = all(
        row[field] == "true"
        for field in (
            "return_1s_valid",
            "return_1m_valid",
            "volatility_1m_valid",
        )
    )
    row["feature_row_usable"] = str(usable).lower()
    invalid_flags = [
        row[field]
        for field in (
            "return_1s_quality_flag",
            "return_1m_quality_flag",
            "volatility_1m_quality_flag",
        )
        if not row[field].startswith("valid_")
    ]
    row["feature_quality_flag"] = (
        "valid_all_initial_features"
        if usable
        else ";".join(dict.fromkeys(invalid_flags))
    )
    return row


def build_feature_view(
    archive_path: Path,
    member_name: str | None,
    day_start: datetime,
    duration_seconds: int = 86400,
    window_seconds: int = 300,
    lookback_seconds: int = 60,
) -> tuple[list[dict[str, str]], str, dict[str, int]]:
    if duration_seconds < 1:
        raise ValueError("duration_seconds must be at least 1")
    if window_seconds < 1:
        raise ValueError("window_seconds must be at least 1")
    if lookback_seconds < 1:
        raise ValueError("lookback_seconds must be at least 1")
    if duration_seconds % window_seconds:
        raise ValueError("duration_seconds must be divisible by window_seconds")

    observations, selected_member, counters = collect_closed_klines(
        archive_path, member_name
    )
    sorted_starts = sorted(observations)
    rows = []
    window_count = duration_seconds // window_seconds
    for index in range(window_count):
        window_start = day_start + timedelta(seconds=index * window_seconds)
        window_end = window_start + timedelta(seconds=window_seconds)
        rows.append(
            make_row(
                window_start,
                window_end,
                observations,
                sorted_starts,
                lookback_seconds,
            )
        )

    counters.update(
        {
            "windows_requested": len(rows),
            "feature_rows_usable": sum(
                row["feature_row_usable"] == "true" for row in rows
            ),
            "return_1s_valid": sum(
                row["return_1s_valid"] == "true" for row in rows
            ),
            "return_1m_valid": sum(
                row["return_1m_valid"] == "true" for row in rows
            ),
            "volatility_1m_valid": sum(
                row["volatility_1m_valid"] == "true" for row in rows
            ),
        }
    )
    return rows, selected_member, counters


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--day-start", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--member")
    parser.add_argument("--duration-seconds", type=int, default=86400)
    parser.add_argument("--window-seconds", type=int, default=300)
    parser.add_argument("--lookback-seconds", type=int, default=60)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        rows, member, counters = build_feature_view(
            args.archive,
            args.member,
            parse_utc(args.day_start),
            args.duration_seconds,
            args.window_seconds,
            args.lookback_seconds,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        raise SystemExit(f"error: {error}") from error

    print(
        json.dumps(
            {"member": member, "counters": counters},
            indent=2,
        ),
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
