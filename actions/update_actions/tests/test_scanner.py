import tempfile
import unittest
from pathlib import Path

from update_actions import scanner


class TestScanner(unittest.TestCase):
    def test_find_uses_nested(self):
        data = {
            "jobs": {
                "build": {
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {"run": "echo hi"},
                    ],
                    "other": [{"steps": [{"uses": "actions/cache@v3"}]}],
                }
            }
        }
        self.assertEqual(
            scanner.find_uses(data),
            ["actions/checkout@v4", "actions/cache@v3"],
        )

    def test_find_uses_in_file_invalid_yaml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.yml"
            path.write_text(":::not yaml", encoding="utf-8")
            uses, text = scanner.find_uses_in_file(path)
            self.assertEqual(uses, [])
            self.assertEqual(text, ":::not yaml")

    def test_apply_updates(self):
        text = """
        steps:
          - uses: actions/checkout@v3
          - uses: org/tool@1.2.3 # comment
        """
        upgrades = {("actions/checkout", "v3"): "v4"}
        updated = scanner.apply_updates(text, upgrades)
        self.assertIn("actions/checkout@v4", updated)
        self.assertIn("org/tool@1.2.3", updated)

    def test_collect_workflow_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / ".github/workflows").mkdir(parents=True)

            target = root / ".github/workflows" / "ci.yml"
            target.write_text("name: ci", encoding="utf-8")
            files = scanner.collect_workflow_files(root, ".github/**/*.yml")
            self.assertEqual(files, [target])


if __name__ == "__main__":
    unittest.main()
