#!/usr/bin/env python3
"""Run one archive audit and update its manifest safely."""

from __future__ import annotations

import argparse
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .archive_manifest import (
        find_record_index,
        iso_now,
        load_manifest,
        manifest_lock,
        sha256_file,
        update_manifest,
        write_manifest_atomically,
    )
    from .audit_binance_klines import audit, parse_utc
except ImportError:
    from archive_manifest import (
        find_record_index,
        iso_now,
        load_manifest,
        manifest_lock,
        sha256_file,
        update_manifest,
        write_manifest_atomically,
    )
    from audit_binance_klines import audit, parse_utc


AUDIT_RESULT_SCHEMA_VERSION = 2
RETRYABLE_STATUSES = {"pending", "interrupted", "failed"}


def safe_token(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._") or "value"


def get_record_snapshot(
    manifest_path: Path, identifier: str
) -> tuple[dict[str, Any], dict[str, Any], int]:
    with manifest_lock(manifest_path):
        payload = load_manifest(manifest_path)
        index = find_record_index(payload, identifier)
        return payload, dict(payload["records"][index]), index


def update_record(
    manifest_path: Path,
    identifier: str,
    values: dict[str, Any],
) -> None:
    def updater(payload: dict[str, Any]) -> None:
        index = find_record_index(payload, identifier)
        payload["records"][index].update(values)

    update_manifest(manifest_path, updater)


def resolve_archive_path(
    manifest_payload: dict[str, Any],
    record: dict[str, Any],
    archive_root: Path | None,
) -> Path:
    root = archive_root or Path(manifest_payload["archive_root"])
    return root / record["archive_relative_path"]


def resolve_audit_input(
    manifest_payload: dict[str, Any],
    record: dict[str, Any],
    input_root: Path | None,
) -> tuple[Path, str, dict[str, Any]]:
    """Resolve the physical Binance source for schema-v1 or schema-v2 records."""

    if manifest_payload.get("manifest_schema_version") == 1:
        path = resolve_archive_path(manifest_payload, record, input_root)
        descriptor = {
            "name": record["archive_name"],
            "relative_path": record["archive_relative_path"],
            "size_bytes": record["size_bytes"],
            "sha256": record["input_sha256"],
        }
        return path, "zip_archive", descriptor

    inputs = record.get("inputs")
    if not isinstance(inputs, dict):
        raise ValueError("schema-v2 record has no inputs object")
    if "binance_raw" in inputs:
        role = "binance_raw"
    elif "zip_archive" in inputs:
        role = "zip_archive"
    else:
        raise ValueError(
            f"group has no Binance raw input: {record.get('group_id')}"
        )
    descriptor = inputs[role]
    if not isinstance(descriptor, dict):
        raise ValueError(f"invalid input descriptor for role: {role}")
    root = input_root or Path(
        manifest_payload.get("input_root")
        or manifest_payload.get("archive_root")
    )
    return root / descriptor["relative_path"], role, descriptor


def resolve_output_path(manifest_path: Path, uri: str) -> Path:
    path = Path(uri)
    return path if path.is_absolute() else manifest_path.parent / path


def verify_completed_output(
    manifest_path: Path, record: dict[str, Any]
) -> tuple[bool, str]:
    uri = record.get("audit_output_uri")
    expected_hash = record.get("audit_output_sha256")
    if not uri or not expected_hash:
        return False, "completed record has no output URI and checksum"
    output_path = resolve_output_path(manifest_path, uri)
    if not output_path.is_file():
        return False, f"audit output is missing: {output_path}"
    actual_hash = sha256_file(output_path)
    if actual_hash != expected_hash:
        return False, (
            f"audit output checksum mismatch: expected {expected_hash}, "
            f"found {actual_hash}"
        )
    return True, "verified"


def make_output_path(
    output_dir: Path,
    archive_path: Path,
    input_sha256: str,
    audit_version: str,
    policy_version: str,
) -> Path:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{run_id}-{os.getpid()}"
    filename = "--".join(
        (
            safe_token(archive_path.stem),
            input_sha256[:12],
            safe_token(audit_version),
            safe_token(policy_version),
            run_id,
        )
    )
    return output_dir / f"{filename}.json"


def run_one(
    manifest_path: Path,
    identifier: str,
    day_start: str,
    output_dir: Path,
    archive_root: Path | None = None,
    member: str | None = None,
    duration_seconds: int = 86400,
    reprocess: bool = False,
    recover_running: bool = False,
) -> str:
    manifest_payload, record, _ = get_record_snapshot(manifest_path, identifier)
    status = record.get("status")
    if status == "completed":
        verified, reason = verify_completed_output(manifest_path, record)
        if verified and not reprocess:
            return f"skipped {identifier}: completed output verified"
        if not reprocess:
            raise RuntimeError(
                f"completed entry is inconsistent ({reason}); "
                "use --reprocess after investigation"
            )
    elif status == "running":
        if not recover_running:
            raise RuntimeError(
                f"archive is already marked running: {identifier}; "
                "use --recover-running only after confirming no other runner"
            )
        update_record(
            manifest_path,
            identifier,
            {
                "status": "interrupted",
                "last_error": "Prior running state was explicitly recovered.",
            },
        )
    elif status not in RETRYABLE_STATUSES:
        raise RuntimeError(f"unsupported archive status: {status}")

    source_path, input_role, input_descriptor = resolve_audit_input(
        manifest_payload, record, archive_root
    )
    if not source_path.is_file():
        message = f"audit input is missing: {source_path}"
        update_record(
            manifest_path,
            identifier,
            {"status": "failed", "last_error": message},
        )
        raise FileNotFoundError(message)

    actual_size = source_path.stat().st_size
    expected_size = input_descriptor.get("size_bytes")
    actual_hash = sha256_file(source_path)
    expected_hash = input_descriptor.get("sha256")
    if actual_size != expected_size or actual_hash != expected_hash:
        message = (
            "audit-input identity mismatch: "
            f"expected size/hash {expected_size}/{expected_hash}, "
            f"found {actual_size}/{actual_hash}"
        )
        update_record(
            manifest_path,
            identifier,
            {"status": "failed", "last_error": message},
        )
        raise ValueError(message)

    started_at = iso_now()
    update_record(
        manifest_path,
        identifier,
        {
            "status": "running",
            "started_at_utc": started_at,
            "completed_at_utc": None,
            "last_error": None,
        },
    )
    running = True

    try:
        summary, selected_member = audit(
            source_path,
            member,
            parse_utc(day_start),
            duration_seconds,
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = make_output_path(
            output_dir,
            source_path,
            record.get("group_sha256", actual_hash),
            record["audit_version"],
            record["policy_version"],
        )
        if output_path.exists():
            raise FileExistsError(f"refusing to overwrite audit output: {output_path}")

        result = {
            "audit_result_schema_version": AUDIT_RESULT_SCHEMA_VERSION,
            "generated_at_utc": iso_now(),
            "audit_version": record["audit_version"],
            "policy_version": record["policy_version"],
            "group_id": record.get(
                "group_id", record.get("archive_relative_path")
            ),
            "candidate_date": record.get("candidate_date"),
            "input_layout": record.get("input_layout", "legacy_zip"),
            "input_complete": record.get("input_complete", True),
            "missing_input_roles": record.get("missing_input_roles", []),
            "audit_input_role": input_role,
            "audit_input_relative_path": input_descriptor["relative_path"],
            "audit_input_sha256": actual_hash,
            "group_sha256": record.get("group_sha256", actual_hash),
            "archive_relative_path": record.get("archive_relative_path"),
            "input_sha256": actual_hash,
            "day_start_utc": parse_utc(day_start).isoformat().replace("+00:00", "Z"),
            "duration_seconds": duration_seconds,
            "member": selected_member,
            "summary": summary,
        }
        write_manifest_atomically(output_path, result)
        output_hash = sha256_file(output_path)
        output_uri = str(output_path)

        update_record(
            manifest_path,
            identifier,
            {
                "status": "completed",
                "audit_output_uri": output_uri,
                "audit_output_sha256": output_hash,
                "completed_at_utc": iso_now(),
                "last_error": None,
            },
        )
        running = False
        return f"completed {identifier}: {output_uri}"
    except KeyboardInterrupt:
        if running:
            update_record(
                manifest_path,
                identifier,
                {
                    "status": "interrupted",
                    "last_error": "Runner interrupted by operator.",
                },
            )
        raise
    except Exception as error:
        if running:
            update_record(
                manifest_path,
                identifier,
                {"status": "failed", "last_error": str(error)},
            )
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument(
        "--archive",
        required=True,
        help="Group ID or unique input path/name from the manifest",
    )
    parser.add_argument("--day-start", required=True, help="UTC audit-day start")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--archive-root",
        type=Path,
        help="Override the manifest input root (legacy option name)",
    )
    parser.add_argument("--member")
    parser.add_argument("--duration-seconds", type=int, default=86400)
    parser.add_argument(
        "--reprocess",
        action="store_true",
        help="Create a new output for an inconsistent or completed entry",
    )
    parser.add_argument(
        "--recover-running",
        action="store_true",
        help="Recover a stale running state after confirming no runner is active",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.duration_seconds < 1:
        raise SystemExit("--duration-seconds must be at least 1")
    try:
        print(
            run_one(
                args.manifest.resolve(),
                args.archive,
                args.day_start,
                args.output_dir.resolve(),
                None if args.archive_root is None else args.archive_root.resolve(),
                args.member,
                args.duration_seconds,
                args.reprocess,
                args.recover_running,
            )
        )
    except (OSError, ValueError, RuntimeError) as error:
        raise SystemExit(f"error: {error}") from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
