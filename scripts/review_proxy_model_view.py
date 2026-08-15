#!/usr/bin/env python3
"""Review a persisted Binance proxy model view before any model training."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import tempfile
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

try:
    from .build_proxy_join import (
        AUDIT_FIELDNAMES,
        KEY_FIELD,
        MODEL_COLUMNS,
        MODEL_FEATURE_COLUMNS,
        canonical_window_key,
    )
except ImportError:
    from build_proxy_join import (
        AUDIT_FIELDNAMES,
        KEY_FIELD,
        MODEL_COLUMNS,
        MODEL_FEATURE_COLUMNS,
        canonical_window_key,
    )


REPORT_SCHEMA_VERSION = 1
REVIEW_IMPLEMENTATION_VERSION = "0.6.0"
EXCLUDED_FIELDNAMES = [
    "day",
    KEY_FIELD,
    "eligibility_reason",
    "feature_row_usable",
    "target_valid",
    "feature_feature_quality_flag",
    "target_target_quality_flag",
    "target_label_source",
]


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
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


def write_csv_atomic(
    path: Path, fieldnames: list[str], rows: list[dict[str, str]]
) -> None:
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


def load_rows(path: Path, expected_fields: list[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != expected_fields:
            raise ValueError(
                f"unexpected columns in {path.name}: {reader.fieldnames}"
            )
        return list(reader)


def index_unique(rows: list[dict[str, str]], path: Path) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        raw_key = row.get(KEY_FIELD, "")
        if not raw_key:
            raise ValueError(f"blank {KEY_FIELD} in {path.name}")
        key = canonical_window_key(raw_key)
        if key in indexed:
            raise ValueError(f"duplicate {KEY_FIELD} in {path.name}: {key}")
        normalized = dict(row)
        normalized[KEY_FIELD] = key
        indexed[key] = normalized
    return indexed


def numeric_stats(rows: list[dict[str, str]], field: str) -> dict[str, Any]:
    values: list[float] = []
    for row in rows:
        value = row.get(field, "")
        try:
            number = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"model field {field} is not numeric at {row.get(KEY_FIELD)}"
            ) from error
        if not math.isfinite(number):
            raise ValueError(
                f"model field {field} is not finite at {row.get(KEY_FIELD)}"
            )
        values.append(number)
    if not values:
        raise ValueError(f"model field {field} has no values")
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": mean(values),
    }


def review_day(
    day: str, audit_path: Path, model_path: Path
) -> tuple[dict[str, Any], list[dict[str, str]], list[str]]:
    audit_rows = load_rows(audit_path, AUDIT_FIELDNAMES)
    model_rows = load_rows(model_path, MODEL_COLUMNS)
    audit_index = index_unique(audit_rows, audit_path)
    model_index = index_unique(model_rows, model_path)

    audit_eligible = {
        key
        for key, row in audit_index.items()
        if row["eligible_for_model"] == "true"
    }
    model_keys = set(model_index)
    if audit_eligible != model_keys:
        missing = sorted(audit_eligible - model_keys)
        extra = sorted(model_keys - audit_eligible)
        raise ValueError(
            f"{day}: audit/model eligibility mismatch; "
            f"missing model keys={missing[:3]}, extra model keys={extra[:3]}"
        )

    labels = Counter(row["label"] for row in model_rows)
    if set(labels) - {"UP", "DOWN"}:
        raise ValueError(f"{day}: unsupported labels: {sorted(set(labels) - {'UP', 'DOWN'})}")
    if any(row["label_source"] != "binance_proxy" for row in model_rows):
        raise ValueError(f"{day}: model rows contain a non-proxy label source")
    for row in model_rows:
        if row["label_definition"] != "end_price_gte_start_price":
            raise ValueError(f"{day}: unsupported proxy label definition")

    excluded = []
    for row in audit_rows:
        if row["eligible_for_model"] == "true":
            continue
        excluded.append(
            {
                "day": day,
                KEY_FIELD: canonical_window_key(row[KEY_FIELD]),
                "eligibility_reason": row["eligibility_reason"],
                "feature_row_usable": row["feature_row_usable"],
                "target_valid": row["target_valid"],
                "feature_feature_quality_flag": row[
                    "feature_feature_quality_flag"
                ],
                "target_target_quality_flag": row[
                    "target_target_quality_flag"
                ],
                "target_label_source": row["target_label_source"],
            }
        )

    feature_stats = {
        field: numeric_stats(model_rows, field) for field in MODEL_FEATURE_COLUMNS
    }
    keys = sorted(model_index)
    return (
        {
            "day": day,
            "audit_rows": len(audit_rows),
            "model_rows": len(model_rows),
            "excluded_rows": len(excluded),
            "label_counts": dict(sorted(labels.items())),
            "feature_stats": feature_stats,
            "first_model_key": keys[0] if keys else None,
            "last_model_key": keys[-1] if keys else None,
        },
        excluded,
        keys,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", required=True, type=Path)
    parser.add_argument("--model-dir", required=True, type=Path)
    parser.add_argument("--output-report", required=True, type=Path)
    parser.add_argument("--excluded-output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audit_dir = args.audit_dir.resolve()
    model_dir = args.model_dir.resolve()
    output_report = args.output_report.resolve()
    excluded_output = args.excluded_output.resolve()
    audit_paths = {path.stem: path for path in audit_dir.glob("*.csv")}
    model_paths = {path.stem: path for path in model_dir.glob("*.csv")}
    days = sorted(set(audit_paths) | set(model_paths))
    if not days:
        raise SystemExit("error: no audit or model CSVs found")
    if set(audit_paths) != set(model_paths):
        raise SystemExit(
            "error: audit/model day sets differ: "
            f"audit-only={sorted(set(audit_paths) - set(model_paths))}, "
            f"model-only={sorted(set(model_paths) - set(audit_paths))}"
        )

    state: dict[str, Any] = {
        "review_report_schema_version": REPORT_SCHEMA_VERSION,
        "review_implementation_version": REVIEW_IMPLEMENTATION_VERSION,
        "status": "running",
        "audit_dir": str(audit_dir),
        "model_dir": str(model_dir),
        "model_feature_columns": MODEL_FEATURE_COLUMNS,
        "excluded_output": str(excluded_output),
    }
    try:
        day_results = []
        excluded_rows: list[dict[str, str]] = []
        all_model_keys: list[str] = []
        for day in days:
            result, excluded, model_keys = review_day(
                day, audit_paths[day], model_paths[day]
            )
            day_results.append(result)
            excluded_rows.extend(excluded)
            all_model_keys.extend(model_keys)

        if all_model_keys != sorted(all_model_keys):
            raise ValueError("model keys are not in chronological order")
        if len(all_model_keys) != len(set(all_model_keys)):
            raise ValueError("duplicate model keys across day files")

        label_counts = Counter()
        feature_stats: dict[str, dict[str, Any]] = {}
        for result in day_results:
            label_counts.update(result["label_counts"])
            for field in MODEL_FEATURE_COLUMNS:
                stats = result["feature_stats"][field]
                current = feature_stats.setdefault(
                    field,
                    {"count": 0, "min": stats["min"], "max": stats["max"]},
                )
                current["count"] += stats["count"]
                current["min"] = min(current["min"], stats["min"])
                current["max"] = max(current["max"], stats["max"])

        report = {
            **state,
            "status": "completed",
            "days": day_results,
            "totals": {
                "days": len(days),
                "audit_rows": sum(item["audit_rows"] for item in day_results),
                "model_rows": sum(item["model_rows"] for item in day_results),
                "excluded_rows": len(excluded_rows),
                "label_counts": dict(sorted(label_counts.items())),
                "chronological_model_keys": True,
            },
            "feature_stats": feature_stats,
        }
        write_csv_atomic(excluded_output, EXCLUDED_FIELDNAMES, excluded_rows)
        write_json_atomic(output_report, report)
        print("review report:", output_report)
        print(json.dumps(report["totals"], indent=2))
        print("excluded rows:", excluded_output)
        return 0
    except (OSError, ValueError, csv.Error) as error:
        state["status"] = "review"
        state["error"] = str(error)
        write_json_atomic(output_report, state)
        raise SystemExit(f"error: {error}") from error


if __name__ == "__main__":
    raise SystemExit(main())
