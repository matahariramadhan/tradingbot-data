#!/usr/bin/env python3
"""Run independent archive audits from a manifest and explicit coverage map."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from .archive_manifest import load_manifest, manifest_lock
    from .audit_binance_klines import parse_utc
    from .run_archive_audit import run_one
except ImportError:
    from archive_manifest import load_manifest, manifest_lock
    from audit_binance_klines import parse_utc
    from run_archive_audit import run_one


def load_coverage_map(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8") as source:
        mapping = json.load(source)
    if not isinstance(mapping, dict):
        raise ValueError("coverage map must be a JSON object")
    if not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in mapping.items()
    ):
        raise ValueError("coverage map keys and values must be strings")
    for key, value in mapping.items():
        parsed = parse_utc(value)
        if any(
            (
                parsed.hour,
                parsed.minute,
                parsed.second,
                parsed.microsecond,
            )
        ):
            raise ValueError(
                f"coverage start must be aligned to UTC midnight: {key}={value}"
            )
    return mapping


def get_records(manifest_path: Path) -> list[dict[str, Any]]:
    with manifest_lock(manifest_path):
        payload = load_manifest(manifest_path)
        return [dict(record) for record in payload["records"]]


def coverage_for(record: dict[str, Any], mapping: dict[str, str]) -> str | None:
    relative_path = record["archive_relative_path"]
    if relative_path in mapping:
        return mapping[relative_path]
    archive_name = record["archive_name"]
    if archive_name in mapping:
        return mapping[archive_name]
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--coverage-map", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--archive-root", type=Path)
    parser.add_argument("--member")
    parser.add_argument("--duration-seconds", type=int, default=86400)
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry records currently marked failed or interrupted",
    )
    parser.add_argument(
        "--reprocess-completed",
        action="store_true",
        help="Create a new output for completed records instead of verifying/skipping",
    )
    parser.add_argument(
        "--recover-running",
        action="store_true",
        help="Recover stale running records after confirming no runner is active",
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop after the first archive failure",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.duration_seconds < 1:
        raise SystemExit("--duration-seconds must be at least 1")

    manifest_path = args.manifest.resolve()
    try:
        coverage_map = load_coverage_map(args.coverage_map.resolve())
        records = get_records(manifest_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(f"error: {error}") from error
    selected: list[tuple[dict[str, Any], str]] = []
    missing_coverage: list[str] = []
    blocked_running: list[str] = []
    unknown_statuses: list[str] = []

    for record in records:
        status = record.get("status")
        if status == "running":
            if args.recover_running:
                should_process = True
            else:
                blocked_running.append(record["archive_relative_path"])
                should_process = False
        elif status in {"pending", "completed"}:
            should_process = True
        elif status in {"failed", "interrupted"}:
            should_process = args.retry_failed
        else:
            unknown_statuses.append(
                f"{record.get('archive_relative_path')}: {status}"
            )
            should_process = False
        if not should_process:
            continue
        day_start = coverage_for(record, coverage_map)
        if day_start is None:
            missing_coverage.append(record["archive_relative_path"])
            continue
        selected.append((record, day_start))

    if blocked_running:
        joined = ", ".join(blocked_running)
        raise SystemExit(
            "archives are marked running; confirm no runner is active and "
            f"rerun with --recover-running: {joined}"
        )
    if unknown_statuses:
        raise SystemExit(
            "unsupported manifest statuses: " + ", ".join(unknown_statuses)
        )
    if missing_coverage:
        joined = ", ".join(missing_coverage)
        raise SystemExit(
            "coverage map has no day start for: "
            f"{joined}; refusing to guess timestamps"
        )

    failures = 0
    for record, day_start in selected:
        identifier = record["archive_relative_path"]
        try:
            message = run_one(
                manifest_path,
                identifier,
                day_start,
                args.output_dir.resolve(),
                None if args.archive_root is None else args.archive_root.resolve(),
                args.member,
                args.duration_seconds,
                args.reprocess_completed,
                args.recover_running,
            )
            print(message)
        except Exception as error:
            failures += 1
            print(f"failed {identifier}: {error}")
            if args.stop_on_error:
                break

    print(f"processed={len(selected)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
