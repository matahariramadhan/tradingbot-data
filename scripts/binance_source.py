"""Shared streaming readers for Binance JSONL stored directly or inside ZIP."""

from __future__ import annotations

import gzip
import io
import json
import zipfile
from pathlib import Path
from typing import Any, Iterator


def find_binance_member(
    archive: zipfile.ZipFile, requested: str | None
) -> str:
    names = archive.namelist()
    if requested is not None:
        if requested not in names:
            raise ValueError(f"Archive member not found: {requested}")
        return requested

    candidates = [
        name
        for name in names
        if name.startswith("binance_raw_events_")
        and name.endswith(".jsonl.gz")
    ]
    if len(candidates) != 1:
        raise ValueError(
            "Could not select one Binance member automatically; "
            "pass --member explicitly."
        )
    return candidates[0]


def describe_binance_source(
    source_path: Path, requested_member: str | None
) -> str:
    if zipfile.is_zipfile(source_path):
        with zipfile.ZipFile(source_path) as archive:
            return find_binance_member(archive, requested_member)
    if source_path.name.endswith(".jsonl.gz"):
        if requested_member is not None:
            raise ValueError("--member is only valid for a ZIP input")
        return source_path.name
    raise ValueError(
        "Binance input must be a ZIP containing one raw JSONL GZIP member "
        "or a direct .jsonl.gz file"
    )


def _iter_text_stream(
    text_stream: io.TextIOBase,
) -> Iterator[dict[str, Any] | None]:
    for line in text_stream:
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            yield None
            continue
        if isinstance(payload, dict):
            yield payload
        else:
            yield None


def iter_json_records(
    source_path: Path, requested_member: str | None = None
) -> Iterator[dict[str, Any] | None]:
    """Stream records without extracting or modifying the source input."""

    if zipfile.is_zipfile(source_path):
        with zipfile.ZipFile(source_path) as archive:
            member_name = find_binance_member(archive, requested_member)
            with archive.open(member_name, "r") as compressed_member:
                with gzip.GzipFile(fileobj=compressed_member) as gzip_stream:
                    with io.TextIOWrapper(
                        gzip_stream, encoding="utf-8"
                    ) as text_stream:
                        yield from _iter_text_stream(text_stream)
        return

    if source_path.name.endswith(".jsonl.gz"):
        if requested_member is not None:
            raise ValueError("--member is only valid for a ZIP input")
        with gzip.open(source_path, "rt", encoding="utf-8") as text_stream:
            yield from _iter_text_stream(text_stream)
        return

    raise ValueError(
        "Binance input must be a ZIP containing one raw JSONL GZIP member "
        "or a direct .jsonl.gz file"
    )

