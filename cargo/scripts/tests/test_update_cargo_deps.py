import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.update_cargo_deps as module


class TestFindAndReplaceVersion(unittest.TestCase):
    def test_simple_dependency(self):
        content = '[dependencies]\nserde = "1.0.0"\n'
        new_content, old = module.find_and_replace_version(content, "serde", "1.0.228")
        self.assertEqual(old, "1.0.0")
        self.assertIn('serde = "1.0.228"', new_content)

    def test_table_dependency(self):
        content = (
            '[dependencies]\nserde = { version = "1.0.0", features = ["derive"] }\n'
        )
        new_content, old = module.find_and_replace_version(content, "serde", "1.0.228")
        self.assertEqual(old, "1.0.0")
        self.assertIn('version = "1.0.228"', new_content)
        self.assertIn('features = ["derive"]', new_content)

    def test_preserves_caret_prefix(self):
        content = '[dependencies]\ntokio = "^1.0.0"\n'
        new_content, old = module.find_and_replace_version(content, "tokio", "1.40.0")
        self.assertEqual(old, "^1.0.0")
        self.assertIn('tokio = "^1.40.0"', new_content)

    def test_preserves_tilde_prefix(self):
        content = '[dependencies]\naxum = "~0.7.0"\n'
        new_content, old = module.find_and_replace_version(content, "axum", "0.7.9")
        self.assertEqual(old, "~0.7.0")
        self.assertIn('axum = "~0.7.9"', new_content)

    def test_preserves_exact_prefix(self):
        content = '[dependencies]\nfoo = "=1.2.3"\n'
        new_content, old = module.find_and_replace_version(content, "foo", "1.2.5")
        self.assertEqual(old, "=1.2.3")
        self.assertIn('foo = "=1.2.5"', new_content)

    def test_no_change_when_already_latest(self):
        content = '[dependencies]\nserde = "1.0.228"\n'
        new_content, old = module.find_and_replace_version(content, "serde", "1.0.228")
        self.assertIsNone(old)
        self.assertEqual(content, new_content)

    def test_hyphen_underscore_interchangeable(self):
        content = '[dependencies]\nserde-json = "1.0.0"\n'
        new_content, old = module.find_and_replace_version(
            content, "serde_json", "1.0.140"
        )
        self.assertEqual(old, "1.0.0")
        self.assertIn('serde-json = "1.0.140"', new_content)

    def test_underscore_in_toml_hyphen_in_metadata(self):
        content = '[dependencies]\nserde_json = "1.0.0"\n'
        new_content, old = module.find_and_replace_version(
            content, "serde-json", "1.0.140"
        )
        self.assertEqual(old, "1.0.0")
        self.assertIn('serde_json = "1.0.140"', new_content)

    def test_updates_both_deps_and_dev_deps(self):
        content = (
            "[dependencies]\n"
            'reqwest = { version = "0.11.0", features = ["json"] }\n'
            "\n"
            "[dev-dependencies]\n"
            'reqwest = { version = "0.11.0", features = ["blocking"] }\n'
        )
        new_content, old = module.find_and_replace_version(content, "reqwest", "0.13.2")
        self.assertEqual(old, "0.11.0")
        self.assertEqual(new_content.count('"0.13.2"'), 2)
        self.assertNotIn("0.11.0", new_content)

    def test_does_not_touch_unrelated_crates(self):
        content = "[dependencies]\n" 'serde = "1.0.0"\n' 'tokio = "1.0.0"\n'
        new_content, _ = module.find_and_replace_version(content, "serde", "1.0.228")
        self.assertIn('tokio = "1.0.0"', new_content)


class TestProcessManifest(unittest.TestCase):
    def test_updates_cargo_toml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Path(tmpdir) / "Cargo.toml"
            manifest.write_text(
                "[package]\n"
                'name = "test"\n'
                'edition = "2021"\n'
                "\n"
                "[dependencies]\n"
                'serde = "1.0.0"\n',
                encoding="utf-8",
            )

            fake_metadata = {
                "packages": [
                    {"dependencies": [{"name": "serde", "req": "^1.0.0", "kind": None}]}
                ]
            }
            mock_result = mock.Mock(returncode=0, stdout=json.dumps(fake_metadata))

            with mock.patch.object(module.subprocess, "run", return_value=mock_result):
                with mock.patch.object(
                    module, "get_latest_stable_version", return_value="1.0.228"
                ):
                    updates = module.process_manifest(str(manifest))

            self.assertEqual(len(updates), 1)
            self.assertEqual(updates[0], ("serde", "1.0.0", "1.0.228"))

            updated = manifest.read_text(encoding="utf-8")
            self.assertIn('serde = "1.0.228"', updated)

    def test_skips_up_to_date_deps(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Path(tmpdir) / "Cargo.toml"
            manifest.write_text(
                "[package]\n"
                'name = "test"\n'
                'edition = "2021"\n'
                "\n"
                "[dependencies]\n"
                'serde = "1.0.228"\n',
                encoding="utf-8",
            )

            fake_metadata = {
                "packages": [
                    {
                        "dependencies": [
                            {"name": "serde", "req": "^1.0.228", "kind": None}
                        ]
                    }
                ]
            }
            mock_result = mock.Mock(returncode=0, stdout=json.dumps(fake_metadata))

            with mock.patch.object(module.subprocess, "run", return_value=mock_result):
                with mock.patch.object(
                    module, "get_latest_stable_version", return_value="1.0.228"
                ):
                    updates = module.process_manifest(str(manifest))

            self.assertEqual(len(updates), 0)

    def test_warns_on_failed_crate_lookup(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Path(tmpdir) / "Cargo.toml"
            manifest.write_text(
                "[package]\n"
                'name = "test"\n'
                'edition = "2021"\n'
                "\n"
                "[dependencies]\n"
                'nonexistent-crate = "0.1.0"\n',
                encoding="utf-8",
            )

            fake_metadata = {
                "packages": [
                    {
                        "dependencies": [
                            {
                                "name": "nonexistent-crate",
                                "req": "^0.1.0",
                                "kind": None,
                            }
                        ]
                    }
                ]
            }
            mock_result = mock.Mock(returncode=0, stdout=json.dumps(fake_metadata))

            with mock.patch.object(module.subprocess, "run", return_value=mock_result):
                with mock.patch.object(
                    module,
                    "get_latest_stable_version",
                    side_effect=Exception("404 Not Found"),
                ):
                    updates = module.process_manifest(str(manifest))

            self.assertEqual(len(updates), 0)
            # Cargo.toml should be unchanged
            content = manifest.read_text(encoding="utf-8")
            self.assertIn('nonexistent-crate = "0.1.0"', content)


class TestMain(unittest.TestCase):
    def test_writes_dep_updates_to_github_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Path(tmpdir) / "Cargo.toml"
            manifest.write_text(
                "[package]\n"
                'name = "test"\n'
                'edition = "2021"\n'
                "\n"
                "[dependencies]\n"
                'serde = "1.0.0"\n',
                encoding="utf-8",
            )

            output_file = Path(tmpdir) / "github_output"
            output_file.write_text("", encoding="utf-8")

            fake_metadata = {
                "packages": [
                    {"dependencies": [{"name": "serde", "req": "^1.0.0", "kind": None}]}
                ]
            }
            mock_result = mock.Mock(returncode=0, stdout=json.dumps(fake_metadata))

            with mock.patch.object(module.subprocess, "run", return_value=mock_result):
                with mock.patch.object(
                    module, "get_latest_stable_version", return_value="1.0.228"
                ):
                    with mock.patch.dict(
                        os.environ, {"GITHUB_OUTPUT": str(output_file)}
                    ):
                        with mock.patch.object(sys, "argv", ["script", str(manifest)]):
                            module.main()

            output = output_file.read_text(encoding="utf-8")
            self.assertIn("dep_updates", output)
            self.assertIn("serde", output)
            self.assertIn("1.0.0", output)
            self.assertIn("1.0.228", output)

    def test_no_output_when_no_updates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Path(tmpdir) / "Cargo.toml"
            manifest.write_text(
                "[package]\n"
                'name = "test"\n'
                'edition = "2021"\n'
                "\n"
                "[dependencies]\n"
                'serde = "1.0.228"\n',
                encoding="utf-8",
            )

            output_file = Path(tmpdir) / "github_output"
            output_file.write_text("", encoding="utf-8")

            fake_metadata = {
                "packages": [
                    {
                        "dependencies": [
                            {"name": "serde", "req": "^1.0.228", "kind": None}
                        ]
                    }
                ]
            }
            mock_result = mock.Mock(returncode=0, stdout=json.dumps(fake_metadata))

            with mock.patch.object(module.subprocess, "run", return_value=mock_result):
                with mock.patch.object(
                    module, "get_latest_stable_version", return_value="1.0.228"
                ):
                    with mock.patch.dict(
                        os.environ, {"GITHUB_OUTPUT": str(output_file)}
                    ):
                        with mock.patch.object(sys, "argv", ["script", str(manifest)]):
                            module.main()

            output = output_file.read_text(encoding="utf-8")
            self.assertEqual(output, "")


if __name__ == "__main__":
    unittest.main()
