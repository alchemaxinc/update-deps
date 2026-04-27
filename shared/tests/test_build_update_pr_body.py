import tempfile
import unittest
from pathlib import Path

import build_update_pr_body as module


class TestBuildUpdatePrBody(unittest.TestCase):
    def test_categorizes_updates(self):
        self.assertEqual(module.categorize_update("1.2.3", "2.0.0"), "major")
        self.assertEqual(module.categorize_update("1.2.3", "1.3.0"), "minor")
        self.assertEqual(module.categorize_update("1.2.3", "1.2.4"), "patch")
        self.assertEqual(module.categorize_update("~> 6.0", "~> 6.35"), "minor")
        self.assertEqual(module.categorize_update("v3", "v4"), "major")

    def test_build_body_renders_sections(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            updates_file = Path(tmpdir) / "updates.tsv"
            updates_file.write_text(
                "major-lib\t1.0.0\t2.0.0\n"
                "minor-lib\t1.0.0\t1.1.0\n"
                "patch-lib\t1.0.0\t1.0.1\n",
                encoding="utf-8",
            )

            categories = module.read_updates(updates_file, 3)
            body = module.build_body(
                title="# Updates",
                columns=["Package", "Old", "New"],
                categories=categories,
                footer="Generated",
                preface="",
                empty_message="",
            )

        self.assertIn("## Major Updates", body)
        self.assertIn("| `major-lib` | `1.0.0` | `2.0.0` |", body)
        self.assertIn("## Minor Updates", body)
        self.assertIn("## Patch Updates", body)
        self.assertIn("Generated", body)

    def test_writes_github_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "github_output"
            module.write_github_output("pr_body", "# Updates", str(output_file))

            output = output_file.read_text(encoding="utf-8")

        self.assertIn("pr_body<<ENDOFBODY", output)
        self.assertIn("# Updates", output)


if __name__ == "__main__":
    unittest.main()
