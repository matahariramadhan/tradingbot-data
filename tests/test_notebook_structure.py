from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "tradingbot_data.ipynb"
VISUAL_CELL_IDS = {
    "human-data-overview",
    "human-split-timeline",
    "human-baseline-dashboard",
}


class NotebookStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        cls.cells = cls.notebook["cells"]

    def test_cell_ids_are_unique_and_visual_checkpoints_exist(self) -> None:
        cell_ids = [cell["id"] for cell in self.cells]
        self.assertEqual(len(cell_ids), len(set(cell_ids)))
        self.assertTrue(VISUAL_CELL_IDS.issubset(cell_ids))

    def test_all_code_cells_compile(self) -> None:
        for cell in self.cells:
            if cell["cell_type"] != "code":
                continue
            compile("".join(cell["source"]), f"cell:{cell['id']}", "exec")

    def test_visual_cells_reload_durable_drive_artifacts(self) -> None:
        by_id = {cell["id"]: cell for cell in self.cells}
        for cell_id in VISUAL_CELL_IDS:
            source = "".join(by_id[cell_id]["source"])
            self.assertIn("/content/drive/MyDrive/tradingbot-data-audit", source)
            self.assertIn("matplotlib", source)
            self.assertNotIn("subprocess.run", source)


if __name__ == "__main__":
    unittest.main()
