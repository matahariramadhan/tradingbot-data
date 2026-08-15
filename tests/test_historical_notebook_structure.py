from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "historical_binance_15m.ipynb"
REQUIRED_IDS = {
    "historical-bootstrap",
    "historical-download",
    "historical-download-gate",
    "historical-build",
    "historical-dataset-gate",
    "historical-model-columns",
    "historical-human-plots",
}


class HistoricalNotebookStructureTests(unittest.TestCase):
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

    def test_bootstrap_is_pinned_and_long_cells_are_resumable(self) -> None:
        bootstrap = "".join(self.by_id["historical-bootstrap"]["source"])
        self.assertIn("91507cf3303bc0a88977091c3601175b3acd21e4", bootstrap)
        for cell_id in ("historical-download", "historical-build"):
            source = "".join(self.by_id[cell_id]["source"])
            self.assertIn("--checkpoint", source)
            self.assertIn("subprocess.run", source)

    def test_model_gate_excludes_future_target_fields(self) -> None:
        source = "".join(self.by_id["historical-model-columns"]["source"])
        self.assertIn("target_start_price", source)
        self.assertIn("target_end_price", source)
        self.assertIn("target_return_15m", source)


if __name__ == "__main__":
    unittest.main()
