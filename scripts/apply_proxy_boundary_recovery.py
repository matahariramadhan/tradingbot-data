#!/usr/bin/env python3
"""Apply verified cross-archive proxy-target boundary observations."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

try:
    from .build_binance_proxy_targets import FIELDNAMES, iso_from_ms, parse_utc
except ImportError:
    from build_binance_proxy_targets import FIELDNAMES, iso_from_ms, parse_utc


REPORT_SCHEMA_VERSION = 1
RECOVERED_FLAG = "valid_target_recovered_end_boundary"
RECOVERED_LATE_START_FLAG = "valid_target_recovered_end_boundary_late_start"


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
        writer = csv.DictWriter(temporary, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)


def load_boundary_overrides(
    path: Path,
) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    with path.open("r", encoding="utf-8") as source:
        payload = json.load(source)
    if not isinstance(payload, list):
        raise ValueError("boundary report must be a JSON array")

    overrides: dict[int, dict[str, Any]] = {}
    seen_boundaries: set[int] = set()
    ambiguous: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("boundary report entries must be objects")
        try:
            boundary_ms = int(item["boundary_start_ms"])
            target_day = str(item["target_day"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("boundary report entry has invalid identity") from error
        if boundary_ms in seen_boundaries:
            raise ValueError(f"duplicate boundary in report: {boundary_ms}")
        seen_boundaries.add(boundary_ms)
        if not item.get("recoverable"):
            continue

        sources = item.get("sources")
        if not isinstance(sources, list) or len(sources) != 1:
            ambiguous.append(
                {
                    "boundary_start_ms": boundary_ms,
                    "target_day": target_day,
                    "reason": "expected exactly one source provenance entry",
                }
            )
            continue
        source = sources[0]
        if not isinstance(source, dict):
            raise ValueError(f"source entry is not an object: {boundary_ms}")
        try:
            close = Decimal(str(source["close"]))
            available_at = parse_utc(str(source["received_at_utc"]))
            source_group = str(source["source_group"])
            source_file = str(source["source_file"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"recoverable boundary lacks valid source provenance: {boundary_ms}"
            ) from error
        overrides[boundary_ms] = {
            "boundary_start_ms": boundary_ms,
            "target_day": target_day,
            "close": close,
            "available_at": available_at,
            "source_group": source_group,
            "source_file": source_file,
        }

    metadata = {
        "requested_boundaries": len(payload),
        "recoverable_boundaries": len(overrides),
        "ambiguous_boundaries": ambiguous,
        "unrecoverable_boundaries": sum(
            not bool(item.get("recoverable")) for item in payload
        ),
    }
    return overrides, metadata


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != FIELDNAMES:
            raise ValueError(
                f"unexpected target columns in {path.name}: {reader.fieldnames}"
            )
        rows = list(reader)
    if len(rows) != 288:
        raise ValueError(f"expected 288 target rows in {path.name}, found {len(rows)}")
    return rows


def resolve_start_boundary(
    rows: list[dict[str, str]], row_index: int, boundary_ms: int
) -> tuple[Decimal, datetime, str] | None:
    """Return a verified start boundary, including legacy-output repair.

    Early proxy-target outputs discarded the valid start boundary when only
    the end boundary was missing.  The end of the immediately preceding
    five-minute row is the same one-second observation as this row's start.
    Reuse it only when the interval identity and provenance fields match
    exactly; never synthesize a price from a neighboring value.
    """

    expected_interval = iso_from_ms(boundary_ms)
    row = rows[row_index]
    if (
        row.get("proxy_start_interval_start_utc") == expected_interval
        and row.get("proxy_start_price")
        and row.get("proxy_start_available_at_utc")
    ):
        return (
            Decimal(row["proxy_start_price"]),
            parse_utc(row["proxy_start_available_at_utc"]),
            "target_row_start",
        )

    if row_index == 0:
        return None
    previous = rows[row_index - 1]
    if (
        previous.get("window_end_utc") != row.get("window_start_utc")
        or previous.get("proxy_end_interval_start_utc") != expected_interval
        or not previous.get("proxy_end_price")
        or not previous.get("proxy_end_available_at_utc")
    ):
        return None
    return (
        Decimal(previous["proxy_end_price"]),
        parse_utc(previous["proxy_end_available_at_utc"]),
        "previous_window_end",
    )


def patch_rows(
    rows: list[dict[str, str]],
    overrides: dict[int, dict[str, Any]],
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    recovered: list[dict[str, Any]] = []
    review_rows: list[dict[str, Any]] = []
    used_boundaries: set[int] = set()
    for row_index, row in enumerate(rows):
        if row["target_valid"] == "true":
            continue
        if row["target_quality_flag"] != "missing_end_boundary":
            continue
        try:
            window_start = parse_utc(row["window_start_utc"])
            window_end = parse_utc(row["window_end_utc"])
            start_boundary_ms = int(window_start.timestamp() * 1000) - 1000
            boundary_ms = int(window_end.timestamp() * 1000) - 1000
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"invalid target row timestamp: {row.get('window_start_utc')}"
            ) from error
        override = overrides.get(boundary_ms)
        if override is None:
            continue
        if override["target_day"] != row["window_start_utc"][:10]:
            raise ValueError(
                f"boundary day mismatch for {row['window_start_utc']}: "
                f"{override['target_day']}"
            )
        start_boundary = resolve_start_boundary(rows, row_index, start_boundary_ms)
        if start_boundary is None:
            review_rows.append(
                {
                    "window_start_utc": row["window_start_utc"],
                    "boundary_start_ms": boundary_ms,
                    "reason": "missing_valid_start_boundary",
                }
            )
            continue

        start_close, start_available_at, start_source = start_boundary
        end_close = override["close"]
        end_available_at = override["available_at"]
        decision_time = parse_utc(row["decision_time_utc"])
        target_available_at = max(start_available_at, end_available_at)

        if start_source == "previous_window_end":
            row["proxy_start_price"] = f"{start_close:.8f}"
            row["proxy_start_interval_start_utc"] = iso_from_ms(start_boundary_ms)
            row["proxy_start_available_at_utc"] = (
                start_available_at.isoformat(timespec="microseconds").replace(
                    "+00:00", "Z"
                )
            )

        row["proxy_end_price"] = f"{end_close:.8f}"
        row["proxy_end_interval_start_utc"] = iso_from_ms(boundary_ms)
        row["proxy_end_available_at_utc"] = (
            end_available_at.isoformat(timespec="microseconds").replace(
                "+00:00", "Z"
            )
        )
        row["target_available_at_utc"] = (
            target_available_at.isoformat(timespec="microseconds").replace(
                "+00:00", "Z"
            )
        )
        row["label"] = "UP" if end_close >= start_close else "DOWN"
        row["target_valid"] = "true"
        row["target_quality_flag"] = (
            RECOVERED_LATE_START_FLAG
            if start_available_at > decision_time
            else RECOVERED_FLAG
        )
        used_boundaries.add(boundary_ms)
        recovered.append(
            {
                "window_start_utc": row["window_start_utc"],
                "boundary_start_ms": boundary_ms,
                "target_day": override["target_day"],
                "source_group": override["source_group"],
                "source_file": override["source_file"],
                "close": f"{end_close:.8f}",
                "received_at_utc": row["proxy_end_available_at_utc"],
                "quality_flag": row["target_quality_flag"],
                "start_source": start_source,
            }
        )

    return rows, {
        "rows": len(rows),
        "recovered_rows": len(recovered),
        "recovered_boundaries": recovered,
        "review_rows": review_rows,
        "used_boundary_starts_ms": sorted(used_boundaries),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--boundary-report", required=True, type=Path)
    parser.add_argument("--output-report", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    boundary_report = args.boundary_report.resolve()
    output_report = args.output_report.resolve()

    try:
        overrides, boundary_metadata = load_boundary_overrides(boundary_report)
        input_files = sorted(input_dir.glob("*.csv"))
        if not input_files:
            raise ValueError(f"no target CSVs found in {input_dir}")
        boundary_digest = sha256_file(boundary_report)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(f"error: {error}") from error

    state: dict[str, Any] = {
        "recovery_report_schema_version": REPORT_SCHEMA_VERSION,
        "status": "running",
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "boundary_report": str(boundary_report),
        "boundary_report_sha256": boundary_digest,
        "boundary_metadata": boundary_metadata,
        "days": {},
    }
    if output_report.is_file():
        try:
            previous = json.loads(output_report.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            previous = None
        if (
            isinstance(previous, dict)
            and previous.get("recovery_report_schema_version")
            == REPORT_SCHEMA_VERSION
            and previous.get("boundary_report_sha256") == boundary_digest
            and previous.get("input_dir") == str(input_dir)
            and previous.get("output_dir") == str(output_dir)
            and isinstance(previous.get("days"), dict)
        ):
            state["days"] = previous["days"]
            print("resuming recovery report:", output_report)

    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        for input_path in input_files:
            day = input_path.stem
            output_path = output_dir / input_path.name
            prior = state["days"].get(day)
            if (
                isinstance(prior, dict)
                and prior.get("status") == "completed"
                and output_path.is_file()
                and prior.get("output_sha256") == sha256_file(output_path)
            ):
                print(f"{day}: existing verified recovery; skipping")
                continue

            print(f"{day}: recovering")
            rows = load_rows(input_path)
            recovered_rows, details = patch_rows(rows, overrides)
            write_csv_atomic(output_path, recovered_rows)
            output_sha256 = sha256_file(output_path)
            state["days"][day] = {
                "status": "completed",
                "input": str(input_path),
                "output": str(output_path),
                "output_sha256": output_sha256,
                **details,
            }
            write_json_atomic(output_report, state)
            print(
                f"{day}: checkpoint saved; recovered rows: "
                f"{details['recovered_rows']}"
            )
    except KeyboardInterrupt:
        state["status"] = "interrupted"
        write_json_atomic(output_report, state)
        print("interrupted safely; rerun to resume from the recovery report")
        return 130
    except (OSError, ValueError, csv.Error) as error:
        state["status"] = "review"
        write_json_atomic(output_report, state)
        raise SystemExit(f"error: {error}") from error

    used_boundaries = {
        boundary_ms
        for day_result in state["days"].values()
        for boundary_ms in day_result.get("used_boundary_starts_ms", [])
    }
    unused_boundaries = sorted(set(overrides) - used_boundaries)
    incomplete_days = sorted(
        day for day, result in state["days"].items()
        if result.get("status") != "completed"
    )
    state["totals"] = {
        "input_days": len(input_files),
        "completed_days": len(input_files) - len(incomplete_days),
        "recovered_rows": sum(
            result.get("recovered_rows", 0)
            for result in state["days"].values()
        ),
        "review_rows": sum(
            len(result.get("review_rows", []))
            for result in state["days"].values()
        ),
        "used_recovered_boundaries": len(used_boundaries),
        "unused_recovered_boundaries": len(unused_boundaries),
        "unused_boundary_starts_ms": unused_boundaries,
    }
    state["status"] = (
        "completed"
        if not incomplete_days and not boundary_metadata["ambiguous_boundaries"]
        and not unused_boundaries and state["totals"]["review_rows"] == 0
        else "review"
    )
    write_json_atomic(output_report, state)
    print("recovery report:", output_report)
    print(json.dumps(state["totals"], indent=2))
    if state["status"] != "completed":
        print("recovery requires review")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
