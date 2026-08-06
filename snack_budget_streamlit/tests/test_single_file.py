from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"


class SingleFileDeploymentTests(unittest.TestCase):
    def test_app_compiles(self) -> None:
        compile(APP.read_text(encoding="utf-8"), str(APP), "exec")

    def test_no_local_module_imports(self) -> None:
        tree = ast.parse(APP.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        self.assertNotIn("catalog", imported)
        self.assertNotIn("snack_recommender", imported)
        self.assertNotIn("pandas", imported)

    def test_required_features_exist(self) -> None:
        text = APP.read_text(encoding="utf-8")
        for token in (
            'DAILY_BUDGET = 10_000',
            'SNACKS_PER_PERSON_DAY = 3',
            '"생수 포함"',
            '"커피 포함"',
            '"그 외 음료 포함"',
            'COUPANG_HOME_URL',
            '6 + 2 * education_days',
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
