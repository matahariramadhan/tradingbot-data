#!/usr/bin/env python3
"""Build a leakage-safe, non-overlapping historical Binance 15-minute dataset."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics
import tempfile
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

try:
    from .download_binance_klines import FIELDNAMES as RAW_FIELDNAMES
except ImportError:
    from download_binance_klines import FIELDNAMES as RAW_FIELDNAMES


FEATURE_FIELDS = [
    "return_1m",
    "return_5m",
    "return_15m",
    "return_30m",
    "volatility_5m",
    "volatility_15m",
    "volume_ratio_5m",
    "candle_body_5m",
    "high_low_range_5m",
    "distance_ma_15",
    "ma_slope_15",
    "rsi_14",
]
AUDIT_FIELDS = [
    "window_start_utc",
    "decision_time_utc",
    "feature_row_usable",
    "feature_quality_flag",
    *FEATURE_FIELDS,
    "target_valid",
    "target_quality_flag",
    "target_start_price",
    "target_end_price",
    "target_return_15m",
    "label",
    "label_source",
    "label_definition",
    "availability_policy",
    "eligible_for_model",
]
MODEL_FIELDS = [
    "window_start_utc",
    "decision_time_utc",
    *FEATURE_FIELDS,
    "label",
    "label_source",
    "label_definition",
]

IMPLEMENTATION_VERSION = "historical-binance-15m-dataset-2026-08-15-v1"
CHECKPOINT_SCHEMA_VERSION = 1
REPORT_SCHEMA_VERSION = 1
LABEL_SOURCE = "binance_historical"
LABEL_DEFINITION = "end_price_gte_start_price"
AVAILABILITY_POLICY = "interval_complete_assumption"


@dataclass(frozen=True)
class Bar:
    minute: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Block:
    open: float
    high: float
    low: float
    close: float
    volume: float


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def atomic_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
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
        writer = csv.DictWriter(temporary, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)


def parse_day(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"not an ISO UTC date: {value}") from error


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp has no timezone: {value}")
    return parsed.astimezone(timezone.utc)


def iso_from_minute(minute: int) -> str:
    return (
        datetime.fromtimestamp(minute * 60, tz=timezone.utc)
        .isoformat(timespec="minutes")
        .replace("+00:00", "Z")
    )


def minute_of(value: datetime) -> int:
    return int(value.timestamp() // 60)


def format_number(value: float | None) -> str:
    return "" if value is None else f"{value:.12g}"


def load_raw_bars(
    raw_dir: Path, download_report_path: Path
) -> tuple[dict[int, Bar], dict[str, str]]:
    with download_report_path.open(encoding="utf-8") as source:
        download_report = json.load(source)
    if download_report.get("status") != "completed":
        raise ValueError("download report is not completed")
    if download_report.get("config", {}).get("interval") != "1m":
        raise ValueError("download report is not for 1-minute klines")
    expected_files = {
        Path(item["path"]).name: item for item in download_report.get("days", [])
    }
    if not expected_files:
        raise ValueError("download report contains no day outputs")

    bars: dict[int, Bar] = {}
    source_hashes: dict[str, str] = {}
    for filename, metadata in sorted(expected_files.items()):
        path = raw_dir / filename
        if not path.is_file():
            raise ValueError(f"missing downloaded kline file: {path}")
        digest = sha256_file(path)
        if digest != metadata.get("sha256"):
            raise ValueError(f"downloaded file hash differs from report: {filename}")
        source_hashes[filename] = digest
        with path.open(newline="", encoding="utf-8") as source:
            reader = csv.DictReader(source)
            if reader.fieldnames != RAW_FIELDNAMES:
                raise ValueError(f"unexpected raw fields in {filename}")
            previous_minute: int | None = None
            for row in reader:
                timestamp = parse_utc(row["open_time_utc"])
                minute = minute_of(timestamp)
                if timestamp.second or timestamp.microsecond:
                    raise ValueError(f"non-minute kline timestamp in {filename}")
                if previous_minute is not None and minute <= previous_minute:
                    raise ValueError(f"raw rows are not chronological in {filename}")
                previous_minute = minute
                if minute in bars:
                    raise ValueError(f"duplicate raw kline across files: {row['open_time_utc']}")
                values = {
                    name: float(row[name])
                    for name in ("open", "high", "low", "close", "volume")
                }
                if not all(math.isfinite(value) for value in values.values()):
                    raise ValueError(f"non-finite raw kline in {filename}")
                bars[minute] = Bar(minute=minute, **values)
    if not bars:
        raise ValueError("downloaded kline files contain no rows")
    return bars, source_hashes


def aggregate_block(bars: dict[int, Bar], start_minute: int, length: int) -> Block | None:
    members = [bars.get(start_minute + offset) for offset in range(length)]
    if any(member is None for member in members):
        return None
    complete = [member for member in members if member is not None]
    return Block(
        open=complete[0].open,
        high=max(member.high for member in complete),
        low=min(member.low for member in complete),
        close=complete[-1].close,
        volume=sum(member.volume for member in complete),
    )


def population_std(values: list[float]) -> float:
    average = statistics.fmean(values)
    return math.sqrt(statistics.fmean((value - average) ** 2 for value in values))


def rsi(values: list[float]) -> float:
    gains = [max(value, 0.0) for value in values]
    losses = [max(-value, 0.0) for value in values]
    average_gain = statistics.fmean(gains)
    average_loss = statistics.fmean(losses)
    if average_loss == 0:
        return 100.0 if average_gain > 0 else 50.0
    relative_strength = average_gain / average_loss
    return 100.0 - (100.0 / (1.0 + relative_strength))


def build_row(bars: dict[int, Bar], decision: datetime) -> dict[str, str]:
    decision_minute = minute_of(decision)
    row = {
        "window_start_utc": decision.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "decision_time_utc": decision.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "feature_row_usable": "false",
        "feature_quality_flag": "",
        **{field: "" for field in FEATURE_FIELDS},
        "target_valid": "false",
        "target_quality_flag": "",
        "target_start_price": "",
        "target_end_price": "",
        "target_return_15m": "",
        "label": "",
        "label_source": LABEL_SOURCE,
        "label_definition": LABEL_DEFINITION,
        "availability_policy": AVAILABILITY_POLICY,
        "eligible_for_model": "false",
    }
    feature_errors: list[str] = []
    closes: dict[int, float] = {}
    for offset in range(-65, 0):
        bar = bars.get(decision_minute + offset)
        if bar is not None:
            closes[decision_minute + offset] = bar.close
    if any(decision_minute + offset not in closes for offset in range(-31, 0)):
        feature_errors.append("missing_minute_lookback")
    else:
        latest_close = closes[decision_minute - 1]
        row["return_1m"] = format_number(latest_close / closes[decision_minute - 2] - 1.0)
        row["return_5m"] = format_number(latest_close / closes[decision_minute - 6] - 1.0)
        row["return_15m"] = format_number(latest_close / closes[decision_minute - 16] - 1.0)
        row["return_30m"] = format_number(latest_close / closes[decision_minute - 31] - 1.0)
        recent_returns = [
            closes[decision_minute - offset] / closes[decision_minute - offset - 1] - 1.0
            for offset in range(1, 16)
        ]
        row["volatility_5m"] = format_number(population_std(recent_returns[:5]))
        row["volatility_15m"] = format_number(population_std(recent_returns))
        current_ma = statistics.fmean(
            closes[decision_minute - offset] for offset in range(1, 16)
        )
        earlier_ma = statistics.fmean(
            closes[decision_minute - offset] for offset in range(6, 21)
        )
        row["distance_ma_15"] = format_number(latest_close / current_ma - 1.0)
        row["ma_slope_15"] = format_number(current_ma / earlier_ma - 1.0)
        row["rsi_14"] = format_number(rsi(recent_returns[:14]))

    latest_block = aggregate_block(bars, decision_minute - 5, 5)
    if latest_block is None:
        feature_errors.append("missing_5m_candle")
    else:
        row["candle_body_5m"] = format_number(
            latest_block.close / latest_block.open - 1.0
        )
        row["high_low_range_5m"] = format_number(
            (latest_block.high - latest_block.low) / latest_block.close
        )

    baseline_blocks = [
        aggregate_block(bars, decision_minute - 5 * (index + 2), 5)
        for index in range(12)
    ]
    if latest_block is None or any(block is None for block in baseline_blocks):
        feature_errors.append("missing_volume_history")
    else:
        baseline_volumes = [block.volume for block in baseline_blocks if block is not None]
        baseline_median = statistics.median(baseline_volumes)
        if baseline_median <= 0:
            feature_errors.append("zero_volume_baseline")
        else:
            row["volume_ratio_5m"] = format_number(
                latest_block.volume / baseline_median
            )

    target_start = bars.get(decision_minute - 1)
    target_end = bars.get(decision_minute + 14)
    if target_start is None:
        row["target_quality_flag"] = "missing_start_boundary"
    elif target_end is None:
        row["target_quality_flag"] = "missing_end_boundary"
    else:
        target_return = target_end.close / target_start.close - 1.0
        row["target_valid"] = "true"
        row["target_quality_flag"] = "valid_target"
        row["target_start_price"] = format_number(target_start.close)
        row["target_end_price"] = format_number(target_end.close)
        row["target_return_15m"] = format_number(target_return)
        row["label"] = "UP" if target_end.close >= target_start.close else "DOWN"

    missing_features = [field for field in FEATURE_FIELDS if not row[field]]
    if not missing_features:
        row["feature_row_usable"] = "true"
        row["feature_quality_flag"] = "valid_all_features"
    else:
        feature_errors.append("missing_feature_values")
        row["feature_quality_flag"] = ";".join(dict.fromkeys(feature_errors))
    if row["feature_row_usable"] == "true" and row["target_valid"] == "true":
        row["eligible_for_model"] = "true"
    return row


def load_dataset_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != AUDIT_FIELDS:
            raise ValueError(f"unexpected dataset fields in {path.name}")
        return list(reader)


def verify_model_output(path: Path, expected_rows: int) -> None:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != MODEL_FIELDS:
            raise ValueError(f"unexpected model fields in {path.name}")
        rows = list(reader)
    if len(rows) != expected_rows:
        raise ValueError(
            f"model output row count differs from audit: {len(rows)} != {expected_rows}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", required=True, type=Path)
    parser.add_argument("--download-report", required=True, type=Path)
    parser.add_argument("--target-start", required=True, help="inclusive UTC date")
    parser.add_argument("--target-end", required=True, help="exclusive UTC date")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--split-report", required=True, type=Path)
    parser.add_argument("--train-day-count", required=True, type=int)
    parser.add_argument("--validation-day-count", required=True, type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target_start = parse_day(args.target_start)
    target_end = parse_day(args.target_end)
    if target_end <= target_start:
        raise SystemExit("error: target end must be after target start")
    days = [
        target_start + timedelta(days=offset)
        for offset in range((target_end - target_start).days)
    ]
    if not 0 < args.train_day_count < len(days):
        raise SystemExit("error: train-day-count must leave validation and holdout days")
    if not 0 < args.validation_day_count < len(days) - args.train_day_count:
        raise SystemExit("error: validation-day-count must leave holdout days")
    output_dir = args.output_dir.resolve()
    day_dir = output_dir / "days"
    checkpoint_path = args.checkpoint.resolve()
    report_path = args.report.resolve()
    split_report_path = args.split_report.resolve()
    config = {
        "implementation_version": IMPLEMENTATION_VERSION,
        "target_start": target_start.isoformat(),
        "target_end_exclusive": target_end.isoformat(),
        "train_day_count": args.train_day_count,
        "validation_day_count": args.validation_day_count,
        "feature_fields": FEATURE_FIELDS,
        "availability_policy": AVAILABILITY_POLICY,
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

    try:
        bars, source_hashes = load_raw_bars(args.raw_dir.resolve(), args.download_report.resolve())
        for day_value in days:
            day = day_value.isoformat()
            output_path = day_dir / f"{day}.csv"
            previous = state["completed_days"].get(day, {})
            if (
                output_path.is_file()
                and previous.get("sha256") == sha256_file(output_path)
                and previous.get("rows") == 96
            ):
                print(f"{day}: existing verified output; skipping")
                continue
            print(f"{day}: building")
            day_start = datetime(day_value.year, day_value.month, day_value.day, tzinfo=timezone.utc)
            rows = [build_row(bars, day_start + timedelta(minutes=15 * index)) for index in range(96)]
            atomic_csv(output_path, AUDIT_FIELDS, rows)
            state["completed_days"][day] = {
                "status": "completed",
                "path": str(output_path),
                "sha256": sha256_file(output_path),
                "rows": len(rows),
                "feature_rows_usable": sum(row["feature_row_usable"] == "true" for row in rows),
                "target_rows_valid": sum(row["target_valid"] == "true" for row in rows),
                "model_rows_usable": sum(row["eligible_for_model"] == "true" for row in rows),
            }
            atomic_json(checkpoint_path, state)
            print(f"{day}: checkpoint saved; model rows: {state['completed_days'][day]['model_rows_usable']}")
    except KeyboardInterrupt:
        atomic_json(checkpoint_path, state)
        print("interrupted safely; rerun to resume from the checkpoint")
        return 2
    except (OSError, ValueError, csv.Error, KeyError, TypeError) as error:
        atomic_json(checkpoint_path, state)
        raise SystemExit(f"error: {error}") from error

    if set(state["completed_days"]) != {day.isoformat() for day in days}:
        atomic_json(checkpoint_path, state)
        raise SystemExit("error: dataset build is incomplete")

    all_rows: list[dict[str, str]] = []
    day_results: list[dict[str, Any]] = []
    for day_value in days:
        day = day_value.isoformat()
        rows = load_dataset_rows(day_dir / f"{day}.csv")
        all_rows.extend(rows)
        result = state["completed_days"][day]
        day_results.append({"day": day, **result})
    audit_output = output_dir / "dataset-audit-v1.csv"
    model_output = output_dir / "model-ready-v1.csv"
    model_rows = [row for row in all_rows if row["eligible_for_model"] == "true"]
    atomic_csv(audit_output, AUDIT_FIELDS, all_rows)
    atomic_csv(model_output, MODEL_FIELDS, [
        {field: row[field] for field in MODEL_FIELDS} for row in model_rows
    ])
    if len(load_dataset_rows(audit_output)) != len(all_rows):
        raise ValueError("audit output verification failed")
    verify_model_output(model_output, len(model_rows))

    train_days = [day.isoformat() for day in days[: args.train_day_count]]
    validation_end = args.train_day_count + args.validation_day_count
    validation_days = [day.isoformat() for day in days[args.train_day_count:validation_end]]
    holdout_days = [day.isoformat() for day in days[validation_end:]]
    partition_by_day = {
        **{day: "train" for day in train_days},
        **{day: "validation" for day in validation_days},
        **{day: "holdout" for day in holdout_days},
    }
    keys_by_partition: dict[str, list[str]] = {"train": [], "validation": [], "holdout": []}
    rows_by_partition = Counter()
    model_rows_by_partition = Counter()
    for row in all_rows:
        day = parse_utc(row["window_start_utc"]).date().isoformat()
        partition = partition_by_day[day]
        rows_by_partition[partition] += 1
        if row["eligible_for_model"] == "true":
            model_rows_by_partition[partition] += 1
            keys_by_partition[partition].append(row["window_start_utc"])
    model_keys = [key for partition in ("train", "validation", "holdout") for key in keys_by_partition[partition]]
    if len(model_keys) != len(set(model_keys)):
        raise SystemExit("error: duplicate model window keys")
    if model_keys != sorted(model_keys):
        raise SystemExit("error: model window keys are not chronological")
    overlap = set(keys_by_partition["train"]) & set(keys_by_partition["validation"])
    overlap |= set(keys_by_partition["train"]) & set(keys_by_partition["holdout"])
    overlap |= set(keys_by_partition["validation"]) & set(keys_by_partition["holdout"])
    if overlap:
        raise SystemExit(f"error: split key overlap: {sorted(overlap)[:3]}")
    split_report = {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "implementation_version": IMPLEMENTATION_VERSION,
        "status": "completed",
        "split_method": "chronological_by_utc_day",
        "dataset_report": str(report_path),
        "train_days": train_days,
        "validation_days": validation_days,
        "holdout_days": holdout_days,
        "verification": {
            "partitions_are_disjoint": True,
            "chronological_partitions": True,
            "train_validation_holdout_overlap_keys": 0,
            "model_keys_unique": True,
            "chronological_model_keys": True,
        },
        "totals": {
            "audit_rows": len(all_rows),
            "model_rows": len(model_rows),
            "train_rows": model_rows_by_partition["train"],
            "validation_rows": model_rows_by_partition["validation"],
            "holdout_rows": model_rows_by_partition["holdout"],
        },
        "rows_by_partition": dict(rows_by_partition),
    }
    report = {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "implementation_version": IMPLEMENTATION_VERSION,
        "status": "completed",
        "config": config,
        "download_report": str(args.download_report.resolve()),
        "download_report_sha256": sha256_file(args.download_report.resolve()),
        "availability_policy": AVAILABILITY_POLICY,
        "receipt_time_available": False,
        "raw_source_hashes": source_hashes,
        "days": day_results,
        "totals": {
            "days": len(days),
            "audit_rows": len(all_rows),
            "feature_rows_usable": sum(row["feature_row_usable"] == "true" for row in all_rows),
            "target_rows_valid": sum(row["target_valid"] == "true" for row in all_rows),
            "model_rows_usable": len(model_rows),
            "label_counts": dict(sorted(Counter(row["label"] for row in model_rows).items())),
        },
        "outputs": {
            "audit": str(audit_output),
            "audit_sha256": sha256_file(audit_output),
            "model": str(model_output),
            "model_sha256": sha256_file(model_output),
            "split_report": str(split_report_path),
        },
    }
    atomic_json(report_path, report)
    atomic_json(split_report_path, split_report)
    print("dataset report:", report_path)
    print(json.dumps(report["totals"], indent=2))
    print("split report:", split_report_path)
    print(json.dumps(split_report["totals"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
