#!/usr/bin/env python3
"""Build and verify a chronological Binance-proxy split manifest/report."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .build_proxy_join import (
        KEY_FIELD,
        MODEL_COLUMNS,
        canonical_window_key,
        sha256_file,
        write_json_atomic,
    )
except ImportError:
    from build_proxy_join import (  # type: ignore
        KEY_FIELD,
        MODEL_COLUMNS,
        canonical_window_key,
        sha256_file,
        write_json_atomic,
    )


REPORT_SCHEMA_VERSION = 1
SPLIT_IMPLEMENTATION_VERSION = "0.7.0"


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    import csv

    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != MODEL_COLUMNS:
            raise ValueError(
                f"unexpected model columns in {path.name}: {reader.fieldnames}"
            )
        return list(reader)


def parse_day(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"model filename is not an ISO UTC day: {value}") from error


def parse_key(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"split key must include a timezone: {value}")
    return parsed.astimezone(timezone.utc)


def read_review_report(path: Path) -> dict[str, Any]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read review report {path}: {error}") from error
    if report.get("status") != "completed":
        raise ValueError(f"review report is not completed: {path}")
    if not isinstance(report.get("totals"), dict):
        raise ValueError(f"review report has no totals: {path}")
    return report


def build_split_report(
    model_dir: Path,
    review_report_path: Path,
    output_report: Path,
    train_day_count: int,
) -> dict[str, Any]:
    model_dir = model_dir.resolve()
    review_report_path = review_report_path.resolve()
    output_report = output_report.resolve()
    if not model_dir.is_dir():
        raise ValueError(f"model directory does not exist: {model_dir}")
    review_report = read_review_report(review_report_path)

    paths = sorted(model_dir.glob("*.csv"), key=lambda path: path.stem)
    if not paths:
        raise ValueError(f"no model CSVs found in {model_dir}")
    days = [path.stem for path in paths]
    if len(set(days)) != len(days):
        raise ValueError("duplicate model-day filenames")
    for day_value in days:
        parse_day(day_value)
    if days != sorted(days):
        raise ValueError("model days are not chronologically ordered")
    if not 0 < train_day_count < len(days):
        raise ValueError(
            f"train day count must be between 1 and {len(days) - 1}: {train_day_count}"
        )

    review_days = {
        item["day"] for item in review_report.get("days", []) if isinstance(item, dict)
    }
    if review_days != set(days):
        raise ValueError(
            "model days differ from review report: "
            f"model-only={sorted(set(days) - review_days)}, "
            f"review-only={sorted(review_days - set(days))}"
        )

    train_days = days[:train_day_count]
    evaluation_days = days[train_day_count:]
    train_keys: list[str] = []
    evaluation_keys: list[str] = []
    day_results: list[dict[str, Any]] = []
    all_keys: list[str] = []

    for index, path in enumerate(paths):
        day = path.stem
        rows = load_csv_rows(path)
        keys: list[str] = []
        for row in rows:
            key = canonical_window_key(row.get(KEY_FIELD, ""))
            if parse_key(key).date() != parse_day(day):
                raise ValueError(
                    f"{path.name} contains {KEY_FIELD} outside its day: {key}"
                )
            keys.append(key)
        if keys != sorted(keys):
            raise ValueError(f"model keys are not chronological in {path.name}")
        if len(keys) != len(set(keys)):
            raise ValueError(f"duplicate {KEY_FIELD} in {path.name}")

        partition = "train" if index < train_day_count else "evaluation"
        if partition == "train":
            train_keys.extend(keys)
        else:
            evaluation_keys.extend(keys)
        all_keys.extend(keys)
        day_results.append(
            {
                "day": day,
                "partition": partition,
                "path": str(path),
                "sha256": sha256_file(path),
                "rows": len(rows),
                "first_window_start_utc": keys[0] if keys else None,
                "last_window_start_utc": keys[-1] if keys else None,
            }
        )

    if all_keys != sorted(all_keys):
        raise ValueError("model keys are not globally chronological")
    if len(all_keys) != len(set(all_keys)):
        raise ValueError("duplicate model keys across day files")

    overlap = sorted(set(train_keys) & set(evaluation_keys))
    if overlap:
        raise ValueError(f"train/evaluation key overlap: {overlap[:5]}")
    train_last = parse_key(train_keys[-1]) if train_keys else None
    evaluation_first = parse_key(evaluation_keys[0]) if evaluation_keys else None
    if train_last is None or evaluation_first is None or train_last >= evaluation_first:
        raise ValueError("training keys do not end before evaluation keys begin")

    model_rows = len(all_keys)
    review_model_rows = review_report["totals"].get("model_rows")
    if review_model_rows != model_rows:
        raise ValueError(
            "model rows do not match review report: "
            f"model={model_rows}, review={review_model_rows}"
        )

    return {
        "split_report_schema_version": REPORT_SCHEMA_VERSION,
        "split_implementation_version": SPLIT_IMPLEMENTATION_VERSION,
        "status": "completed",
        "split_method": "chronological_by_utc_day",
        "model_dir": str(model_dir),
        "review_report": str(review_report_path),
        "review_report_sha256": sha256_file(review_report_path),
        "train_day_count": len(train_days),
        "evaluation_day_count": len(evaluation_days),
        "train_days": train_days,
        "evaluation_days": evaluation_days,
        "days": day_results,
        "verification": {
            "review_status_completed": True,
            "model_rows_match_review": True,
            "keys_unique": True,
            "chronological_keys": True,
            "train_evaluation_overlap_keys": len(overlap),
            "train_end_before_evaluation_start": True,
        },
        "totals": {
            "model_rows": model_rows,
            "train_rows": len(train_keys),
            "evaluation_rows": len(evaluation_keys),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", required=True, type=Path)
    parser.add_argument("--review-report", required=True, type=Path)
    parser.add_argument("--output-report", required=True, type=Path)
    parser.add_argument("--train-day-count", required=True, type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    state: dict[str, Any] = {
        "split_report_schema_version": REPORT_SCHEMA_VERSION,
        "split_implementation_version": SPLIT_IMPLEMENTATION_VERSION,
        "status": "review",
    }
    try:
        report = build_split_report(
            args.model_dir,
            args.review_report,
            args.output_report,
            args.train_day_count,
        )
        write_json_atomic(args.output_report, report)
        print("split report:", args.output_report)
        print(json.dumps(report["totals"], indent=2))
        print("train/evaluation overlap keys:", report["verification"]["train_evaluation_overlap_keys"])
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        state["error"] = str(error)
        try:
            write_json_atomic(args.output_report, state)
        except OSError:
            pass
        raise SystemExit(f"error: {error}") from error


if __name__ == "__main__":
    raise SystemExit(main())
