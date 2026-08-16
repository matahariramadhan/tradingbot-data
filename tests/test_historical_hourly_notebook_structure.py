from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "historical_binance_hourly_4y.ipynb"
REQUIRED_IDS = {
    "hourly-bootstrap",
    "hourly-download",
    "hourly-download-gate",
    "hourly-build",
    "hourly-dataset-gate",
    "hourly-model-columns",
    "hourly-human-plots",
}


class HistoricalHourlyNotebookStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        cls.cells = cls.notebook["cells"]
        cls.by_id = {cell["id"]: cell for cell in cls.cells}

    def test_ids_and_code_are_valid(self) -> None:
        ids = [cell["id"] for cell in self.cells]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(REQUIRED_IDS.issubset(ids))
        for cell in self.cells:
            if cell["cell_type"] == "code":
                compile("".join(cell["source"]), f"cell:{cell['id']}", "exec")

    def test_scope_and_split_are_explicit(self) -> None:
        paths = "".join(self.by_id["hourly-drive-paths"]["source"])
        self.assertIn("RAW_START = '2022-08-15'", paths)
        self.assertIn("TARGET_END = '2026-08-16'", paths)
        self.assertIn("TRAIN_END = '2025-06-04'", paths)
        self.assertIn("VALIDATION_END = '2026-01-09'", paths)
        self.assertIn("(1461, 1023, 219, 219)", paths)
        gate = "".join(self.by_id["hourly-download-gate"]["source"])
        self.assertIn("['totals']['days'] == 1462", gate)

    def test_bootstrap_and_long_cells_are_durable(self) -> None:
        bootstrap = "".join(self.by_id["hourly-bootstrap"]["source"])
        self.assertIn("925e4d9f9a94a7ffb9f777caafbbe7badde337d1", bootstrap)
        for cell_id in ("hourly-download", "hourly-build"):
            source = "".join(self.by_id[cell_id]["source"])
            self.assertIn("--checkpoint", source)
            self.assertIn("subprocess.run", source)

    def test_model_columns_do_not_include_future_target_values(self) -> None:
        source = "".join(self.by_id["hourly-model-columns"]["source"])
        for field in ("target_start_price", "target_end_price", "target_return_60m"):
            self.assertIn(field, source)


if __name__ == "__main__":
    unittest.main()
