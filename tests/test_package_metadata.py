from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

import tradingbot_data


ROOT = Path(__file__).resolve().parents[1]


class PackageMetadataTests(unittest.TestCase):
    def test_distribution_and_module_versions_match(self) -> None:
        with (ROOT / "pyproject.toml").open("rb") as source:
            project = tomllib.load(source)["project"]

        self.assertEqual(project["version"], tradingbot_data.__version__)


if __name__ == "__main__":
    unittest.main()
