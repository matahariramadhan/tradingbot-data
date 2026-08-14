#!/usr/bin/env python3
"""Create a checksum-bearing manifest for raw data inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    from .archive_manifest import (
        MANIFEST_SCHEMA_VERSION,
        iso_now,
        manifest_lock,
        sha256_file,
        write_manifest_atomically,
    )
except ImportError:
    from archive_manifest import (
        MANIFEST_SCHEMA_VERSION,
        iso_now,
        manifest_lock,
        sha256_file,
        write_manifest_atomically,
    )


RAW_PATTERNS = {
    "binance_raw": re.compile(
        r"^binance_raw_events_(20\d{2}-\d{2}-\d{2})\.jsonl\.gz$"
    ),
    "polymarket_raw": re.compile(
        r"^polymarket_raw_events_(20\d{2}-\d{2}-\d{2})\.jsonl\.gz$"
    ),
    "recorder_log": re.compile(
        r"^recorder\.log\.(20\d{2}-\d{2}-\d{2})\.gz$"
    ),
}
EXPECTED_GROUP_ROLES = tuple(RAW_PATTERNS)


def find_files(root: Path, pattern: str, recursive: bool) -> list[Path]:
    glob_pattern = f"**/{pattern}" if recursive else pattern
    return sorted(path for path in root.glob(glob_pattern) if path.is_file())


def input_descriptor(path: Path, root: Path) -> dict[str, Any]:
    return {
        "name": path.name,
        "relative_path": path.relative_to(root).as_posix(),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def group_sha256(inputs: dict[str, dict[str, Any]]) -> str:
    identity = {
        role: {
            "relative_path": descriptor["relative_path"],
            "size_bytes": descriptor["size_bytes"],
            "sha256": descriptor["sha256"],
        }
        for role, descriptor in sorted(inputs.items())
    }
    encoded = json.dumps(
        identity, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def processing_fields(audit_version: str, policy_version: str) -> dict[str, Any]:
    return {
        "audit_version": audit_version,
        "policy_version": policy_version,
        "status": "pending",
        "audit_output_uri": None,
        "audit_output_sha256": None,
        "started_at_utc": None,
        "completed_at_utc": None,
        "last_error": None,
    }


def build_zip_records(
    root: Path,
    recursive: bool,
    audit_version: str,
    policy_version: str,
) -> list[dict[str, Any]]:
    archives = find_files(root, "*.zip", recursive)
    records = []
    for path in archives:
        descriptor = input_descriptor(path, root)
        inputs = {"zip_archive": descriptor}
        records.append(
            {
                "group_id": descriptor["relative_path"],
                "candidate_date": None,
                "input_layout": "zip",
                "inputs": inputs,
                "missing_input_roles": [],
                "input_complete": True,
                "group_sha256": group_sha256(inputs),
                **processing_fields(audit_version, policy_version),
            }
        )
    return records


def classify_raw_gzip(name: str) -> tuple[str, str] | None:
    for role, pattern in RAW_PATTERNS.items():
        match = pattern.fullmatch(name)
        if match:
            return role, match.group(1)
    return None


def build_grouped_gzip_records(
    root: Path,
    recursive: bool,
    audit_version: str,
    policy_version: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups: dict[str, dict[str, Path]] = {}
    ignored: list[dict[str, Any]] = []
    for path in find_files(root, "*.gz", recursive):
        classification = classify_raw_gzip(path.name)
        if classification is None:
            ignored.append(
                {
                    "relative_path": path.relative_to(root).as_posix(),
                    "size_bytes": path.stat().st_size,
                    "reason": "not_an_authoritative_raw_group_member",
                }
            )
            continue
        role, candidate_date = classification
        members = groups.setdefault(candidate_date, {})
        if role in members:
            raise ValueError(
                f"duplicate {role} input for candidate date {candidate_date}: "
                f"{members[role]} and {path}"
            )
        members[role] = path

    records = []
    for candidate_date, paths in sorted(groups.items()):
        inputs = {
            role: input_descriptor(path, root)
            for role, path in sorted(paths.items())
        }
        missing = sorted(set(EXPECTED_GROUP_ROLES) - set(inputs))
        records.append(
            {
                "group_id": candidate_date,
                "candidate_date": candidate_date,
                "input_layout": "direct_gzip_group",
                "inputs": inputs,
                "missing_input_roles": missing,
                "input_complete": not missing,
                "group_sha256": group_sha256(inputs),
                **processing_fields(audit_version, policy_version),
            }
        )
    return records, ignored


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive-dir",
        required=True,
        type=Path,
        help="Directory containing direct GZIP inputs or legacy ZIP archives",
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--audit-version", required=True)
    parser.add_argument("--policy-version", required=True)
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search for inputs below --archive-dir",
    )
    parser.add_argument(
        "--layout",
        choices=("auto", "grouped-gzip", "zip"),
        default="auto",
        help="Physical input layout; auto refuses mixed recognized layouts",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.archive_dir.resolve()
    output = args.output.resolve()

    if not root.is_dir():
        raise SystemExit(f"archive directory not found: {root}")
    try:
        with manifest_lock(output):
            if output.exists():
                raise FileExistsError(
                    f"refusing to overwrite existing manifest: {output}; "
                    "choose a new output path"
                )

            raw_gzip_files = [
                path
                for path in find_files(root, "*.gz", args.recursive)
                if classify_raw_gzip(path.name) is not None
            ]
            zip_files = find_files(root, "*.zip", args.recursive)
            layout = args.layout
            if layout == "auto":
                if raw_gzip_files and zip_files:
                    raise ValueError(
                        "recognized both grouped GZIP inputs and ZIP archives; "
                        "pass --layout explicitly"
                    )
                layout = "grouped-gzip" if raw_gzip_files else "zip"

            ignored: list[dict[str, Any]] = []
            if layout == "grouped-gzip":
                records, ignored = build_grouped_gzip_records(
                    root,
                    args.recursive,
                    args.audit_version,
                    args.policy_version,
                )
            else:
                records = build_zip_records(
                    root,
                    args.recursive,
                    args.audit_version,
                    args.policy_version,
                )
            if not records:
                raise ValueError(
                    f"no recognized inputs for layout {layout} under: {root}"
                )

            payload: dict[str, Any] = {
                "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
                "created_at_utc": iso_now(),
                "input_root": str(root),
                "archive_root": str(root),
                "input_layout": layout,
                "audit_scope": "binance_day_coverage",
                "audit_version": args.audit_version,
                "policy_version": args.policy_version,
                "archive_count": len(records),
                "group_count": len(records),
                "ignored_files": ignored,
                "records": records,
            }
            write_manifest_atomically(output, payload)
    except (OSError, ValueError) as error:
        raise SystemExit(f"could not write manifest: {error}") from error

    print(json.dumps({"manifest": str(output), "archive_count": len(records)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
