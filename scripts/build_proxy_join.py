#!/usr/bin/env python3
"""Join Binance features to a Binance proxy target without target leakage."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    from .build_binance_feature_view import FIELDNAMES as FEATURE_FIELDNAMES
    from .build_binance_proxy_targets import FIELDNAMES as TARGET_FIELDNAMES
except ImportError:
    from build_binance_feature_view import FIELDNAMES as FEATURE_FIELDNAMES
    from build_binance_proxy_targets import FIELDNAMES as TARGET_FIELDNAMES


REPORT_SCHEMA_VERSION = 1
KEY_FIELD = "window_start_utc"
MODEL_FEATURE_COLUMNS = ["return_1s", "return_1m", "volatility_1m"]
MODEL_COLUMNS = [
    KEY_FIELD,
    "decision_time_utc",
    *MODEL_FEATURE_COLUMNS,
    "label",
    "label_source",
    "label_definition",
]


class DuplicateKeyError(ValueError):
    """Raised when a source contains more than one row for a join key."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def load_rows(path: Path, fieldnames: list[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        actual = reader.fieldnames or []
        missing = sorted(set(fieldnames) - set(actual))
        if missing:
            raise ValueError(f"{path.name} is missing columns: {missing}")
        return list(reader)


def index_unique_rows(
    rows: list[dict[str, str]], path: Path
) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    duplicates: list[str] = []
    for row in rows:
        key = row.get(KEY_FIELD, "")
        if not key:
            raise ValueError(f"{path.name} contains a blank {KEY_FIELD}")
        if key in indexed:
            duplicates.append(key)
        else:
            indexed[key] = row
    if duplicates:
        unique_duplicates = sorted(set(duplicates))
        raise DuplicateKeyError(
            f"duplicate {KEY_FIELD} in {path.name}: {unique_duplicates[:5]}"
        )
    return indexed


def prefixed_row(
    prefix: str, row: dict[str, str] | None, fieldnames: list[str]
) -> dict[str, str]:
    if row is None:
        return {f"{prefix}_{field}": "" for field in fieldnames if field != KEY_FIELD}
    return {
        f"{prefix}_{field}": value
        for field, value in row.items()
        if field != KEY_FIELD
    }


def audit_fieldnames() -> list[str]:
    return [
        KEY_FIELD,
        "feature_row_present",
        "target_row_present",
        "feature_row_usable",
        "target_valid",
        "eligible_for_model",
        "eligibility_reason",
        *(
            f"feature_{field}"
            for field in FEATURE_FIELDNAMES
            if field != KEY_FIELD
        ),
        *(
            f"target_{field}"
            for field in TARGET_FIELDNAMES
            if field != KEY_FIELD
        ),
    ]


AUDIT_FIELDNAMES = audit_fieldnames()


def eligibility_reason(
    feature: dict[str, str] | None, target: dict[str, str] | None
) -> tuple[bool, str]:
    if feature is None and target is None:
        return False, "missing_feature_and_target_row"
    if feature is None:
        return False, "missing_feature_row"
    if target is None:
        return False, "missing_target_row"
    feature_valid = feature.get("feature_row_usable") == "true"
    target_valid = target.get("target_valid") == "true"
    if feature_valid and target_valid:
        return True, "eligible"
    if not feature_valid and not target_valid:
        return False, "invalid_feature_and_target"
    if not feature_valid:
        return False, "invalid_feature"
    return False, "invalid_target"


def build_join_rows(
    feature_rows: dict[str, dict[str, str]],
    target_rows: dict[str, dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, int]]:
    audit_rows: list[dict[str, str]] = []
    model_rows: list[dict[str, str]] = []
    counters = {
        "audit_rows": 0,
        "eligible_rows": 0,
        "invalid_feature_rows": 0,
        "invalid_target_rows": 0,
        "missing_feature_rows": 0,
        "missing_target_rows": 0,
    }

    for key in sorted(set(feature_rows) | set(target_rows)):
        feature = feature_rows.get(key)
        target = target_rows.get(key)
        eligible, reason = eligibility_reason(feature, target)
        audit_row = {
            KEY_FIELD: key,
            "feature_row_present": str(feature is not None).lower(),
            "target_row_present": str(target is not None).lower(),
            "feature_row_usable": (
                "false" if feature is None else feature.get("feature_row_usable", "false")
            ),
            "target_valid": (
                "false" if target is None else target.get("target_valid", "false")
            ),
            "eligible_for_model": str(eligible).lower(),
            "eligibility_reason": reason,
        }
        audit_row.update(prefixed_row("feature", feature, FEATURE_FIELDNAMES))
        audit_row.update(prefixed_row("target", target, TARGET_FIELDNAMES))
        audit_rows.append(audit_row)
        counters["audit_rows"] += 1

        if feature is None:
            counters["missing_feature_rows"] += 1
        if target is None:
            counters["missing_target_rows"] += 1
        if feature is not None and feature.get("feature_row_usable") != "true":
            counters["invalid_feature_rows"] += 1
        if target is not None and target.get("target_valid") != "true":
            counters["invalid_target_rows"] += 1

        if not eligible:
            continue
        missing_features = [
            field for field in MODEL_FEATURE_COLUMNS if not feature.get(field)
        ]
        if missing_features or not target.get("label"):
            raise ValueError(
                f"eligible row {key} has blank model/target values: "
                f"{missing_features or ['label']}"
            )
        if target.get("label_source") != "binance_proxy":
            raise ValueError(
                f"eligible row {key} has unsupported label_source: "
                f"{target.get('label_source', '')}"
            )
        model_rows.append(
            {
                KEY_FIELD: key,
                "decision_time_utc": feature["decision_time_utc"],
                **{field: feature[field] for field in MODEL_FEATURE_COLUMNS},
                "label": target["label"],
                "label_source": target["label_source"],
                "label_definition": target["label_definition"],
            }
        )
        counters["eligible_rows"] += 1

    return audit_rows, model_rows, counters


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature-dir", required=True, type=Path)
    parser.add_argument("--target-dir", required=True, type=Path)
    parser.add_argument("--audit-output-dir", required=True, type=Path)
    parser.add_argument("--model-output-dir", required=True, type=Path)
    parser.add_argument("--output-report", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    feature_dir = args.feature_dir.resolve()
    target_dir = args.target_dir.resolve()
    audit_output_dir = args.audit_output_dir.resolve()
    model_output_dir = args.model_output_dir.resolve()
    output_report = args.output_report.resolve()

    input_paths = {
        "feature": {path.stem: path for path in feature_dir.glob("*.csv")},
        "target": {path.stem: path for path in target_dir.glob("*.csv")},
    }
    days = sorted(set(input_paths["feature"]) | set(input_paths["target"]))
    if not days:
        raise SystemExit("error: no feature or target CSVs found")

    state: dict[str, Any] = {
        "join_report_schema_version": REPORT_SCHEMA_VERSION,
        "status": "running",
        "feature_dir": str(feature_dir),
        "target_dir": str(target_dir),
        "audit_output_dir": str(audit_output_dir),
        "model_output_dir": str(model_output_dir),
        "key_field": KEY_FIELD,
        "model_feature_columns": MODEL_FEATURE_COLUMNS,
        "model_columns": MODEL_COLUMNS,
        "days": {},
    }
    if output_report.is_file():
        try:
            previous = json.loads(output_report.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            previous = None
        if (
            isinstance(previous, dict)
            and previous.get("join_report_schema_version") == REPORT_SCHEMA_VERSION
            and previous.get("feature_dir") == str(feature_dir)
            and previous.get("target_dir") == str(target_dir)
            and previous.get("audit_output_dir") == str(audit_output_dir)
            and previous.get("model_output_dir") == str(model_output_dir)
            and previous.get("key_field") == KEY_FIELD
            and previous.get("model_feature_columns") == MODEL_FEATURE_COLUMNS
            and isinstance(previous.get("days"), dict)
        ):
            state["days"] = previous["days"]
            print("resuming join report:", output_report)

    audit_output_dir.mkdir(parents=True, exist_ok=True)
    model_output_dir.mkdir(parents=True, exist_ok=True)
    try:
        for day in days:
            feature_path = input_paths["feature"].get(day)
            target_path = input_paths["target"].get(day)
            audit_path = audit_output_dir / f"{day}.csv"
            model_path = model_output_dir / f"{day}.csv"
            feature_digest = sha256_file(feature_path) if feature_path else None
            target_digest = sha256_file(target_path) if target_path else None
            prior = state["days"].get(day)
            if (
                isinstance(prior, dict)
                and prior.get("status") == "completed"
                and prior.get("feature_sha256") == feature_digest
                and prior.get("target_sha256") == target_digest
                and audit_path.is_file()
                and model_path.is_file()
                and prior.get("audit_sha256") == sha256_file(audit_path)
                and prior.get("model_sha256") == sha256_file(model_path)
            ):
                print(f"{day}: existing verified join; skipping")
                continue

            print(f"{day}: joining")
            feature_rows = (
                index_unique_rows(
                    load_rows(feature_path, FEATURE_FIELDNAMES), feature_path
                )
                if feature_path
                else {}
            )
            target_rows = (
                index_unique_rows(
                    load_rows(target_path, TARGET_FIELDNAMES), target_path
                )
                if target_path
                else {}
            )
            audit_rows, model_rows, counters = build_join_rows(
                feature_rows, target_rows
            )
            write_csv_atomic(audit_path, AUDIT_FIELDNAMES, audit_rows)
            write_csv_atomic(model_path, MODEL_COLUMNS, model_rows)
            state["days"][day] = {
                "status": "completed" if feature_path and target_path else "review",
                "feature": str(feature_path) if feature_path else None,
                "target": str(target_path) if target_path else None,
                "feature_sha256": feature_digest,
                "target_sha256": target_digest,
                "audit": str(audit_path),
                "audit_sha256": sha256_file(audit_path),
                "model": str(model_path),
                "model_sha256": sha256_file(model_path),
                **counters,
            }
            write_json_atomic(output_report, state)
            print(
                f"{day}: checkpoint saved; audit rows: {counters['audit_rows']}; "
                f"model rows: {counters['eligible_rows']}"
            )
    except KeyboardInterrupt:
        state["status"] = "interrupted"
        write_json_atomic(output_report, state)
        print("interrupted safely; rerun to resume from the join report")
        return 130
    except (OSError, ValueError, csv.Error) as error:
        state["status"] = "review"
        state["error"] = str(error)
        write_json_atomic(output_report, state)
        raise SystemExit(f"error: {error}") from error

    incomplete_days = sorted(
        day
        for day, result in state["days"].items()
        if result.get("status") != "completed"
    )
    totals = {
        "input_days": len(days),
        "completed_days": len(days) - len(incomplete_days),
        "audit_rows": sum(
            result.get("audit_rows", 0) for result in state["days"].values()
        ),
        "eligible_rows": sum(
            result.get("eligible_rows", 0) for result in state["days"].values()
        ),
        "invalid_feature_rows": sum(
            result.get("invalid_feature_rows", 0)
            for result in state["days"].values()
        ),
        "invalid_target_rows": sum(
            result.get("invalid_target_rows", 0)
            for result in state["days"].values()
        ),
        "missing_feature_rows": sum(
            result.get("missing_feature_rows", 0)
            for result in state["days"].values()
        ),
        "missing_target_rows": sum(
            result.get("missing_target_rows", 0)
            for result in state["days"].values()
        ),
    }
    state["totals"] = totals
    state["status"] = "completed" if not incomplete_days else "review"
    write_json_atomic(output_report, state)
    print("join report:", output_report)
    print(json.dumps(totals, indent=2))
    if state["status"] != "completed":
        print("join requires review")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
