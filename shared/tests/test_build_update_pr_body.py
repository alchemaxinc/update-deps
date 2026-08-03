import json
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
        self.assertEqual(module.categorize_update("1.2.3", "1.2.2"), "other")
        self.assertEqual(module.categorize_update("latest", "next"), "other")

    def test_build_body_renders_sections(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            updates_file = Path(tmpdir) / "updates.json"
            updates_file.write_text(
                json.dumps(
                    [
                        ["major-lib", "1.0.0", "2.0.0"],
                        ["minor-lib", "1.0.0", "1.1.0"],
                        ["patch-lib", "1.0.0", "1.0.1"],
                        ["other-lib", "2.0.0", "1.0.0"],
                    ]
                ),
                encoding="utf-8",
            )

            categories = module.read_updates(updates_file, 3)
            body = module.build_body(
                title="# Updates",
                columns=["Package", "Old", "New"],
                categories=categories,
                source_url="https://github.com/alchemaxinc/update-deps/tree/main/cargo",
                preface="",
                empty_message="",
            )

        self.assertIn("## Major Updates", body)
        self.assertIn(
            "> :warning: **These updates can contain breaking changes. Review them.**\n\n"
            "| Package | Old | New |",
            body,
        )
        self.assertIn("| `major-lib` | `1.0.0` | `2.0.0` |", body)
        self.assertIn("## Minor Updates", body)
        self.assertIn("## Patch Updates", body)
        self.assertIn("## Other Updates", body)
        self.assertIn(
            ":robot: *A bot generated this pull request.*[^update-deps]",
            body,
        )
        self.assertIn(
            "[^update-deps]: [Use this update action in your repository.](https://github.com/alchemaxinc/update-deps/tree/main/cargo)",
            body,
        )

    def test_writes_github_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "github_output"
            value = "# Updates\nENDOFBODY"
            module.write_github_output("pr_body", value, str(output_file))

            output = output_file.read_text(encoding="utf-8")

        name, encoded_value = output.rstrip("\n").split("=", 1)
        self.assertEqual(name, "pr_body")
        self.assertEqual(json.loads(encoded_value), value)

    def test_markdown_row_escapes_table_delimiters_and_newlines(self):
        row = module.markdown_row(["name|with`tick", r"old\value", "new\nvalue"])

        self.assertEqual(
            row,
            "| ``name\\|with`tick`` | `old\\value` | `new value` |",
        )

    def test_read_updates_rejects_non_string_or_incomplete_records(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            updates_file = Path(tmpdir) / "updates.json"
            updates_file.write_text('[["package", "1.0.0"]]', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "expected 3 string fields"):
                module.read_updates(updates_file, 3)

    def test_read_updates_preserves_delimiter_characters_in_json_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            updates_file = Path(tmpdir) / "updates.json"
            record = ["package\tname\nnext line", "1.0.0", "1.0.1"]
            updates_file.write_text(json.dumps([record]), encoding="utf-8")

            categories = module.read_updates(updates_file, 3)

        self.assertEqual(categories["patch"], [record])


if __name__ == "__main__":
    unittest.main()
