from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from archive_manifest import (  # noqa: E402
    MANIFEST_SCHEMA_VERSION,
    find_record_index,
    load_manifest,
    sha256_file,
    write_manifest_atomically,
)
from run_archive_audit import verify_completed_output  # noqa: E402
from run_archive_batch import load_coverage_map  # noqa: E402


class ArchiveWorkflowTests(unittest.TestCase):
    def test_sha256_file_matches_standard_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.bin"
            path.write_bytes(b"archive test data")
            expected = hashlib.sha256(b"archive test data").hexdigest()
            self.assertEqual(sha256_file(path), expected)

    def test_manifest_write_and_record_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            payload = {
                "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
                "records": [
                    {
                        "archive_name": "day.zip",
                        "archive_relative_path": "nested/day.zip",
                    }
                ],
            }
            write_manifest_atomically(path, payload)
            loaded = load_manifest(path)
            self.assertEqual(find_record_index(loaded, "nested/day.zip"), 0)
            self.assertEqual(json.loads(path.read_text())["records"][0]["archive_name"], "day.zip")

    def test_completed_output_requires_matching_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "audit.json"
            output.write_text('{"ok": true}\n', encoding="utf-8")
            record = {
                "audit_output_uri": str(output),
                "audit_output_sha256": sha256_file(output),
            }
            manifest = root / "manifest.json"
            self.assertEqual(verify_completed_output(manifest, record), (True, "verified"))

            output.write_text('{"ok": false}\n', encoding="utf-8")
            verified, reason = verify_completed_output(manifest, record)
            self.assertFalse(verified)
            self.assertIn("checksum mismatch", reason)

    def test_coverage_map_requires_utc_midnight(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            valid = Path(directory) / "valid.json"
            valid.write_text(
                json.dumps({"day.zip": "2026-07-27T00:00:00Z"}),
                encoding="utf-8",
            )
            self.assertEqual(
                load_coverage_map(valid), {"day.zip": "2026-07-27T00:00:00Z"}
            )

            invalid = Path(directory) / "invalid.json"
            invalid.write_text(
                json.dumps({"day.zip": "2026-07-27T00:05:00Z"}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "UTC midnight"):
                load_coverage_map(invalid)


if __name__ == "__main__":
    unittest.main()
