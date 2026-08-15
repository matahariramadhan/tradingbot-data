#!/usr/bin/env python3
"""Train and evaluate the first leakage-safe Binance-proxy baseline."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .build_proxy_join import MODEL_COLUMNS, MODEL_FEATURE_COLUMNS, canonical_window_key
except ImportError:
    from build_proxy_join import MODEL_COLUMNS, MODEL_FEATURE_COLUMNS, canonical_window_key


REPORT_SCHEMA_VERSION = 1
BASELINE_IMPLEMENTATION_VERSION = "0.8.0"
MODEL_NAME = "standardized_logistic_regression"
PREDICTION_FIELDS = [
    "window_start_utc",
    "decision_time_utc",
    "label",
    "predicted_label",
    "p_up",
    "correct",
]


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


def write_csv_atomic(path: Path, rows: list[dict[str, str]]) -> None:
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
        writer = csv.DictWriter(temporary, fieldnames=PREDICTION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON artifact {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"JSON artifact is not an object: {path}")
    return value


def parse_key(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp must include a timezone: {value}")
    return parsed.astimezone(timezone.utc)


def load_model_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != MODEL_COLUMNS:
            raise ValueError(f"unexpected model columns in {path.name}: {reader.fieldnames}")
        rows = list(reader)
    keys = [canonical_window_key(row["window_start_utc"]) for row in rows]
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        raise ValueError(f"model rows are not unique and chronological in {path.name}")
    for row, key in zip(rows, keys):
        row["window_start_utc"] = key
        if parse_key(key).date().isoformat() != path.stem:
            raise ValueError(f"{path.name} contains a key outside its day: {key}")
        if row["label_source"] != "binance_proxy":
            raise ValueError(f"{path.name} contains a non-proxy label")
        if row["label"] not in {"UP", "DOWN"}:
            raise ValueError(f"{path.name} contains an unsupported label")
        for field in MODEL_FEATURE_COLUMNS:
            try:
                value = float(row[field])
            except (TypeError, ValueError) as error:
                raise ValueError(f"{path.name} has a non-numeric {field}") from error
            if not math.isfinite(value):
                raise ValueError(f"{path.name} has a non-finite {field}")
    return rows


def verify_inputs(
    model_dir: Path, split_report_path: Path, review_report_path: Path
) -> tuple[dict[str, Any], list[dict[str, str]], list[dict[str, str]]]:
    split_report = load_json(split_report_path)
    if split_report.get("status") != "completed":
        raise ValueError(f"split report is not completed: {split_report_path}")
    if split_report.get("verification", {}).get("train_evaluation_overlap_keys") != 0:
        raise ValueError("split report does not verify zero train/evaluation overlap")
    if split_report.get("verification", {}).get("train_end_before_evaluation_start") is not True:
        raise ValueError("split report does not verify chronological partition order")

    review_report = load_json(review_report_path)
    if review_report.get("status") != "completed":
        raise ValueError(f"review report is not completed: {review_report_path}")
    expected_review_hash = split_report.get("review_report_sha256")
    if expected_review_hash != sha256_file(review_report_path):
        raise ValueError("review report hash does not match the split report")

    train_days = split_report.get("train_days", [])
    evaluation_days = split_report.get("evaluation_days", [])
    if not train_days or not evaluation_days:
        raise ValueError("split report must contain both training and evaluation days")
    expected_days = train_days + evaluation_days
    day_metadata = {item["day"]: item for item in split_report.get("days", [])}
    if set(day_metadata) != set(expected_days):
        raise ValueError("split report day metadata does not match its partitions")

    train_rows: list[dict[str, str]] = []
    evaluation_rows: list[dict[str, str]] = []
    all_keys: list[str] = []
    for day in expected_days:
        path = model_dir / f"{day}.csv"
        if not path.is_file():
            raise ValueError(f"missing model-day CSV: {path}")
        metadata = day_metadata[day]
        if sha256_file(path) != metadata.get("sha256"):
            raise ValueError(f"model-day CSV hash differs from split report: {path.name}")
        rows = load_model_rows(path)
        if len(rows) != metadata.get("rows"):
            raise ValueError(f"model-day row count differs from split report: {path.name}")
        all_keys.extend(row["window_start_utc"] for row in rows)
        if day in train_days:
            train_rows.extend(rows)
        else:
            evaluation_rows.extend(rows)

    if all_keys != sorted(all_keys) or len(all_keys) != len(set(all_keys)):
        raise ValueError("model keys are not globally unique and chronological")
    totals = split_report.get("totals", {})
    if len(all_keys) != totals.get("model_rows"):
        raise ValueError("model row total differs from split report")
    if len(train_rows) != totals.get("train_rows"):
        raise ValueError("training row total differs from split report")
    if len(evaluation_rows) != totals.get("evaluation_rows"):
        raise ValueError("evaluation row total differs from split report")
    if review_report.get("totals", {}).get("model_rows") != len(all_keys):
        raise ValueError("model row total differs from review report")
    return split_report, train_rows, evaluation_rows


def metrics(y_true: list[int], predicted: list[int], probabilities: list[float]) -> dict[str, Any]:
    from sklearn.metrics import (
        accuracy_score,
        balanced_accuracy_score,
        brier_score_loss,
        confusion_matrix,
        log_loss,
        roc_auc_score,
    )

    return {
        "accuracy": float(accuracy_score(y_true, predicted)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, predicted)),
        "roc_auc": float(roc_auc_score(y_true, probabilities)),
        "log_loss": float(log_loss(y_true, probabilities, labels=[0, 1])),
        "brier_score": float(brier_score_loss(y_true, probabilities)),
        "confusion_matrix_labels": ["DOWN", "UP"],
        "confusion_matrix": confusion_matrix(y_true, predicted, labels=[0, 1]).tolist(),
    }


def class_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    return dict(sorted(Counter(row["label"] for row in rows).items()))


def completed_outputs_are_reusable(
    report_path: Path, split_report_path: Path, artifact_path: Path, prediction_path: Path
) -> bool:
    if not all(path.is_file() for path in (report_path, artifact_path, prediction_path)):
        return False
    try:
        report = load_json(report_path)
        return (
            report.get("status") == "completed"
            and report.get("baseline_implementation_version") == BASELINE_IMPLEMENTATION_VERSION
            and report.get("split_report_sha256") == sha256_file(split_report_path)
            and report.get("outputs", {}).get("model_sha256") == sha256_file(artifact_path)
            and report.get("outputs", {}).get("evaluation_predictions_sha256") == sha256_file(prediction_path)
        )
    except (OSError, ValueError, KeyError, TypeError):
        return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", required=True, type=Path)
    parser.add_argument("--split-report", required=True, type=Path)
    parser.add_argument("--review-report", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    model_dir = args.model_dir.resolve()
    split_report_path = args.split_report.resolve()
    review_report_path = args.review_report.resolve()
    output_dir = args.output_dir.resolve()
    report_path = output_dir / "proxy-baseline-v1.json"
    artifact_path = output_dir / "proxy-baseline-v1.joblib"
    prediction_path = output_dir / "proxy-baseline-evaluation-v1.csv"

    if completed_outputs_are_reusable(
        report_path, split_report_path, artifact_path, prediction_path
    ):
        print("existing verified baseline; skipping training:", report_path)
        return 0

    try:
        from joblib import dump
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError as error:
        raise SystemExit(
            "error: baseline training requires scikit-learn and joblib; "
            "install the package with `pip install '.[training]'`"
        ) from error

    try:
        split_report, train_rows, evaluation_rows = verify_inputs(
            model_dir, split_report_path, review_report_path
        )
        x_train = [[float(row[field]) for field in MODEL_FEATURE_COLUMNS] for row in train_rows]
        y_train = [1 if row["label"] == "UP" else 0 for row in train_rows]
        x_evaluation = [
            [float(row[field]) for field in MODEL_FEATURE_COLUMNS] for row in evaluation_rows
        ]
        y_evaluation = [1 if row["label"] == "UP" else 0 for row in evaluation_rows]

        pipeline = Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    LogisticRegression(
                        solver="liblinear", max_iter=1000, random_state=0
                    ),
                ),
            ]
        )
        pipeline.fit(x_train, y_train)
        train_probabilities = pipeline.predict_proba(x_train)[:, 1].tolist()
        train_predictions = pipeline.predict(x_train).tolist()
        evaluation_probabilities = pipeline.predict_proba(x_evaluation)[:, 1].tolist()
        evaluation_predictions = pipeline.predict(x_evaluation).tolist()

        train_prior = sum(y_train) / len(y_train)
        majority_label = 1 if train_prior >= 0.5 else 0
        majority_probabilities = [train_prior] * len(y_evaluation)
        majority_predictions = [majority_label] * len(y_evaluation)

        prediction_rows = []
        for row, predicted, probability in zip(
            evaluation_rows, evaluation_predictions, evaluation_probabilities
        ):
            prediction_rows.append(
                {
                    "window_start_utc": row["window_start_utc"],
                    "decision_time_utc": row["decision_time_utc"],
                    "label": row["label"],
                    "predicted_label": "UP" if predicted == 1 else "DOWN",
                    "p_up": f"{probability:.12g}",
                    "correct": str(predicted == (1 if row["label"] == "UP" else 0)).lower(),
                }
            )

        output_dir.mkdir(parents=True, exist_ok=True)
        model_metadata = {
            "model_name": MODEL_NAME,
            "baseline_implementation_version": BASELINE_IMPLEMENTATION_VERSION,
            "feature_columns": MODEL_FEATURE_COLUMNS,
            "label_mapping": {"DOWN": 0, "UP": 1},
            "split_report_sha256": sha256_file(split_report_path),
            "training_rows": len(train_rows),
        }
        model_payload = {"model": pipeline, "metadata": model_metadata}
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=output_dir, prefix=".proxy-baseline-model-", suffix=".tmp", delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
        dump(model_payload, temporary_path)
        os.replace(temporary_path, artifact_path)
        write_csv_atomic(prediction_path, prediction_rows)

        classifier = pipeline.named_steps["classifier"]
        report = {
            "report_schema_version": REPORT_SCHEMA_VERSION,
            "baseline_implementation_version": BASELINE_IMPLEMENTATION_VERSION,
            "status": "completed",
            "model_name": MODEL_NAME,
            "model_features": MODEL_FEATURE_COLUMNS,
            "label_source": "binance_proxy",
            "label_definition": "end_price_gte_start_price",
            "split_report": str(split_report_path),
            "split_report_sha256": sha256_file(split_report_path),
            "review_report": str(review_report_path),
            "review_report_sha256": sha256_file(review_report_path),
            "training": {
                "days": split_report["train_days"],
                "rows": len(train_rows),
                "label_counts": class_counts(train_rows),
                "metrics": metrics(y_train, train_predictions, train_probabilities),
            },
            "evaluation": {
                "days": split_report["evaluation_days"],
                "rows": len(evaluation_rows),
                "label_counts": class_counts(evaluation_rows),
                "metrics": metrics(y_evaluation, evaluation_predictions, evaluation_probabilities),
                "majority_baseline": {
                    "training_prior_p_up": train_prior,
                    "predicted_label": "UP" if majority_label == 1 else "DOWN",
                    "metrics": metrics(y_evaluation, majority_predictions, majority_probabilities),
                },
            },
            "model_parameters": {
                "scaler_fit_scope": "training_rows_only",
                "classifier": "LogisticRegression",
                "solver": "liblinear",
                "max_iter": 1000,
                "random_state": 0,
                "classes": ["DOWN", "UP"],
                "coefficients": classifier.coef_.tolist(),
                "intercept": classifier.intercept_.tolist(),
            },
            "outputs": {
                "model": str(artifact_path),
                "model_sha256": sha256_file(artifact_path),
                "evaluation_predictions": str(prediction_path),
                "evaluation_predictions_sha256": sha256_file(prediction_path),
            },
        }
        write_json_atomic(report_path, report)
        print("baseline report:", report_path)
        print(json.dumps({
            "training_rows": len(train_rows),
            "evaluation_rows": len(evaluation_rows),
            "evaluation_metrics": report["evaluation"]["metrics"],
            "majority_baseline": report["evaluation"]["majority_baseline"]["metrics"],
        }, indent=2))
        return 0
    except (OSError, ValueError, csv.Error, KeyError, TypeError) as error:
        state = {
            "report_schema_version": REPORT_SCHEMA_VERSION,
            "baseline_implementation_version": BASELINE_IMPLEMENTATION_VERSION,
            "status": "review",
            "error": str(error),
        }
        write_json_atomic(report_path, state)
        raise SystemExit(f"error: {error}") from error


if __name__ == "__main__":
    raise SystemExit(main())
