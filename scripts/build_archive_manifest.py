#!/usr/bin/env python3
"""Create a checksum-bearing manifest for raw archive inputs."""

from __future__ import annotations

import argparse
import json
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


def find_archives(root: Path, recursive: bool) -> list[Path]:
    pattern = "**/*.zip" if recursive else "*.zip"
    return sorted(
        path for path in root.glob(pattern) if path.is_file()
    )


def build_record(path: Path, root: Path, audit_version: str, policy_version: str) -> dict[str, Any]:
    relative_path = path.relative_to(root).as_posix()
    return {
        "archive_name": path.name,
        "archive_relative_path": relative_path,
        "size_bytes": path.stat().st_size,
        "input_sha256": sha256_file(path),
        "audit_version": audit_version,
        "policy_version": policy_version,
        "status": "pending",
        "audit_output_uri": None,
        "audit_output_sha256": None,
        "started_at_utc": None,
        "completed_at_utc": None,
        "last_error": None,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive-dir",
        required=True,
        type=Path,
        help="Directory containing raw .zip archives",
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--audit-version", required=True)
    parser.add_argument("--policy-version", required=True)
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search for archives below --archive-dir",
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

            archives = find_archives(root, args.recursive)
            if not archives:
                raise ValueError(f"no .zip archives found under: {root}")

            records = [
                build_record(path, root, args.audit_version, args.policy_version)
                for path in archives
            ]
            payload: dict[str, Any] = {
                "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
                "created_at_utc": iso_now(),
                "archive_root": str(root),
                "audit_version": args.audit_version,
                "policy_version": args.policy_version,
                "archive_count": len(records),
                "records": records,
            }
            write_manifest_atomically(output, payload)
    except (OSError, ValueError) as error:
        raise SystemExit(f"could not write manifest: {error}") from error

    print(json.dumps({"manifest": str(output), "archive_count": len(records)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
