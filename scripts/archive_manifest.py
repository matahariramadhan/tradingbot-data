"""Shared safe operations for the archive manifest scripts."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator


MANIFEST_SCHEMA_VERSION = 1
HASH_CHUNK_BYTES = 1024 * 1024


def iso_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(HASH_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


@contextmanager
def manifest_lock(path: Path) -> Iterator[None]:
    """Serialize manifest readers/writers within a host."""

    lock_path = Path(f"{path}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as source:
        payload = json.load(source)
    if not isinstance(payload, dict):
        raise ValueError("manifest root must be a JSON object")
    if payload.get("manifest_schema_version") != MANIFEST_SCHEMA_VERSION:
        raise ValueError(
            "unsupported manifest_schema_version: "
            f"{payload.get('manifest_schema_version')}"
        )
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("manifest records must be a JSON array")
    return payload


def write_manifest_atomically(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(payload, temporary, indent=2)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def update_manifest(
    path: Path, updater: Callable[[dict[str, Any]], None]
) -> dict[str, Any]:
    with manifest_lock(path):
        payload = load_manifest(path)
        updater(payload)
        write_manifest_atomically(path, payload)
        return payload


def find_record_index(payload: dict[str, Any], identifier: str) -> int:
    records = payload["records"]
    matches = [
        index
        for index, record in enumerate(records)
        if record.get("archive_relative_path") == identifier
        or record.get("archive_name") == identifier
    ]
    if not matches:
        raise ValueError(f"archive not found in manifest: {identifier}")
    if len(matches) > 1:
        raise ValueError(
            f"archive identifier is ambiguous; use relative path: {identifier}"
        )
    return matches[0]
