#!/usr/bin/env python3
"""Build one as-of BTC feature snapshot without using late observations."""

from __future__ import annotations

import argparse
import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from statistics import pstdev
from typing import Any

try:
    from .binance_source import describe_binance_source, iter_json_records
except ImportError:
    from binance_source import describe_binance_source, iter_json_records


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def iso_from_ms(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")


def build_snapshot(
    archive_path: Path,
    member_name: str | None,
    decision_time: datetime,
    lookback_seconds: int,
) -> tuple[dict[str, Any], str]:
    decision_ms = int(decision_time.timestamp() * 1000)
    counters = {
        "records_scanned": 0,
        "malformed_json": 0,
        "closed_klines": 0,
        "started_by_cutoff": 0,
        "completed_by_cutoff": 0,
        "received_by_cutoff": 0,
        "eligible_klines": 0,
    }
    last_closed_start: int | None = None
    last_eligible_start: int | None = None
    last_eligible_close: float | None = None
    latest_row: dict[str, Any] | None = None
    eligible_history: deque[tuple[int, float]] = deque(
        maxlen=lookback_seconds + 1
    )

    selected_member = describe_binance_source(archive_path, member_name)
    for record in iter_json_records(archive_path, member_name):
        if record is None:
            counters["malformed_json"] += 1
            continue
        counters["records_scanned"] += 1
        if record.get("stream") != "btcusdt@kline_1s":
            continue

        raw_event = record.get("raw_event", {})
        kline = raw_event.get("k", {})
        if kline.get("x") is not True:
            continue
        counters["closed_klines"] += 1

        start_ms = int(kline["t"])
        end_ms = int(kline["T"])
        close = float(kline["c"])
        receipt_ms = int(
            parse_utc(record["received_at_utc"]).timestamp() * 1000
        )

        if start_ms > decision_ms:
            continue
        counters["started_by_cutoff"] += 1

        completed = end_ms <= decision_ms
        received = receipt_ms <= decision_ms
        if completed:
            counters["completed_by_cutoff"] += 1
        if received:
            counters["received_by_cutoff"] += 1

        eligible = completed and received
        if eligible:
            counters["eligible_klines"] += 1
            consecutive = (
                last_eligible_start is not None
                and start_ms == last_eligible_start + 1000
                and last_closed_start == start_ms - 1000
            )
            if last_eligible_start is None:
                quality_flag = "no_previous_eligible_kline"
            elif not consecutive:
                quality_flag = "nonconsecutive_eligible_kline"
            else:
                quality_flag = "valid_consecutive_kline"

            return_1s = None
            previous_close = None
            if consecutive and last_eligible_close is not None:
                previous_close = last_eligible_close
                return_1s = (close - previous_close) / previous_close

            latest_row = {
                    "interval_start_utc": iso_from_ms(start_ms),
                    "interval_end_utc": iso_from_ms(end_ms),
                    "close": f"{close:.8f}",
                    "previous_close": (
                        "" if previous_close is None else f"{previous_close:.8f}"
                    ),
                    "return_1s": (
                        "" if return_1s is None else f"{return_1s:.10f}"
                    ),
                    "available_at_utc": record["received_at_utc"],
                    "feature_valid": str(consecutive).lower(),
                    "quality_flag": quality_flag,
            }
            last_eligible_start = start_ms
            last_eligible_close = close
            eligible_history.append((start_ms, close))

        if last_closed_start is None or start_ms > last_closed_start:
            last_closed_start = start_ms

    return_1m = None
    return_1m_valid = False
    return_1m_quality = "no_latest_eligible_kline"
    volatility_1m = None
    volatility_1m_valid = False
    volatility_1m_quality = "no_latest_eligible_kline"
    if latest_row is not None:
        history = list(eligible_history)
        if len(history) < lookback_seconds + 1:
            return_1m_quality = "insufficient_eligible_history"
            volatility_1m_quality = "insufficient_eligible_history"
        elif all(
            current_start == previous_start + 1000
            for (previous_start, _), (current_start, _) in zip(
                history, history[1:]
            )
        ):
            first_close = history[0][1]
            last_close = history[-1][1]
            return_1m = (last_close - first_close) / first_close
            return_1m_valid = True
            return_1m_quality = "valid_consecutive_lookback"
            returns = [
                (current_close - previous_close) / previous_close
                for (_, previous_close), (_, current_close) in zip(
                    history, history[1:]
                )
            ]
            volatility_1m = pstdev(returns)
            volatility_1m_valid = True
            volatility_1m_quality = "valid_consecutive_lookback"
        else:
            return_1m_quality = "nonconsecutive_lookback"
            volatility_1m_quality = "nonconsecutive_lookback"
        latest_row["return_1m"] = (
            "" if return_1m is None else f"{return_1m:.10f}"
        )
        latest_row["return_1m_valid"] = str(return_1m_valid).lower()
        latest_row["return_1m_quality_flag"] = return_1m_quality
        latest_row["volatility_1m"] = (
            "" if volatility_1m is None else f"{volatility_1m:.10f}"
        )
        latest_row["volatility_1m_valid"] = str(volatility_1m_valid).lower()
        latest_row["volatility_1m_quality_flag"] = volatility_1m_quality

    result = {
        "decision_time_utc": decision_time.isoformat().replace("+00:00", "Z"),
        "lookback_seconds": lookback_seconds,
        "feature_row": latest_row,
        "snapshot_usable": bool(
            latest_row
            and latest_row["feature_valid"] == "true"
            and latest_row["return_1m_valid"] == "true"
            and latest_row["volatility_1m_valid"] == "true"
        ),
        "counters": counters,
    }
    return result, selected_member


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--decision-time", required=True)
    parser.add_argument("--member", help="ZIP member; auto-detected when omitted")
    parser.add_argument("--lookback-seconds", type=int, default=60)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.lookback_seconds < 1:
        raise SystemExit("--lookback-seconds must be at least 1")
    try:
        result, member = build_snapshot(
            args.archive,
            args.member,
            parse_utc(args.decision_time),
            args.lookback_seconds,
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        raise SystemExit(f"error: {error}") from error

    result["member"] = member
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
