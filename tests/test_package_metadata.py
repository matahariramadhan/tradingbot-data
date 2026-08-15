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

    def test_training_extra_contains_visualization_dependency(self) -> None:
        with (ROOT / "pyproject.toml").open("rb") as source:
            project = tomllib.load(source)["project"]

        training = project["optional-dependencies"]["training"]
        self.assertTrue(
            any(requirement.startswith("matplotlib") for requirement in training)
        )


if __name__ == "__main__":
    unittest.main()
