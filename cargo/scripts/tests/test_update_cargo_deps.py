import json
import os
import sys
import unittest
from unittest import mock

import scripts.update_cargo_deps as module


class TestProcessManifest(unittest.TestCase):
    @staticmethod
    def _metadata(dependencies):
        return {
            "packages": [
                {
                    "id": "path+file:///workspace/test#test@0.1.0",
                    "dependencies": dependencies,
                }
            ]
        }

    def _mock_cargo(self, before, after):
        metadata = iter((before, after))

        def run(command, **kwargs):
            if command[1] == "metadata":
                return mock.Mock(stdout=json.dumps(next(metadata)))
            self.assertEqual(
                command,
                [
                    "cargo",
                    "upgrade",
                    "--manifest-path",
                    "Cargo.toml",
                    "--incompatible",
                    "--pinned",
                ],
            )
            self.assertTrue(kwargs["check"])
            return mock.Mock()

        return mock.patch.object(module.subprocess, "run", side_effect=run)

    def test_uses_cargo_upgrade_for_complex_constraints(self):
        old_requirement = ">=1.2.3, <2.0.0, !=1.5.0"
        new_requirement = ">=2.1.0, <3.0.0, !=2.5.0"
        dependency = {
            "name": "example",
            "rename": None,
            "kind": None,
            "target": None,
            "req": old_requirement,
        }
        updated_dependency = {**dependency, "req": new_requirement}

        with self._mock_cargo(
            self._metadata([dependency]), self._metadata([updated_dependency])
        ):
            updates = module.process_manifest("Cargo.toml")

        self.assertEqual(updates, [("example", old_requirement, new_requirement)])

    def test_tracks_renamed_dependencies_by_their_cargo_metadata_identity(self):
        dependency = {
            "name": "serde",
            "rename": "serde_for_api",
            "kind": None,
            "target": None,
            "req": "^1.0.0",
        }
        updated_dependency = {**dependency, "req": "^1.0.228"}

        with self._mock_cargo(
            self._metadata([dependency]), self._metadata([updated_dependency])
        ):
            updates = module.process_manifest("Cargo.toml")

        self.assertEqual(updates, [("serde", "^1.0.0", "^1.0.228")])

    def test_skips_unchanged_requirements(self):
        dependency = {
            "name": "serde",
            "rename": None,
            "kind": None,
            "target": None,
            "req": "^1.0.228",
        }

        with self._mock_cargo(
            self._metadata([dependency]), self._metadata([dependency])
        ):
            updates = module.process_manifest("Cargo.toml")

        self.assertEqual(updates, [])

    def test_preserves_build_metadata_when_requested(self):
        old_requirement = "^1.0.0"
        new_requirement = "^1.0.228"
        dependency = {
            "name": "serde",
            "rename": None,
            "kind": None,
            "target": None,
            "req": old_requirement,
        }
        updated_dependency = {**dependency, "req": new_requirement}

        with self._mock_cargo(
            self._metadata([dependency]), self._metadata([updated_dependency])
        ):
            with mock.patch.object(
                module.Path,
                "read_text",
                side_effect=[
                    '[dependencies]\nserde = "^1.0.0+important"\n',
                    '[dependencies]\nserde = "^1.0.228"\n',
                ],
            ):
                with mock.patch.object(module.Path, "write_text") as write_text:
                    updates = module.process_manifest(
                        "Cargo.toml", keep_build_metadata=True
                    )

        self.assertEqual(updates, [("serde", "^1.0.0", "^1.0.228+important")])
        self.assertIn("^1.0.228+important", write_text.call_args.args[0])


class TestMain(unittest.TestCase):
    def test_writes_dep_updates_to_github_output(self):
        with mock.patch.object(
            module, "process_manifest", return_value=[("serde", "^1.0.0", "^1.0.228")]
        ):
            with mock.patch.dict(os.environ, {"GITHUB_OUTPUT": "github_output"}):
                with mock.patch("builtins.open", mock.mock_open()) as open_file:
                    with mock.patch.object(sys, "argv", ["script", "Cargo.toml"]):
                        module.main()

        open_file.assert_called_once_with("github_output", "a")
        self.assertIn("dep_updates", open_file().write.call_args.args[0])
        self.assertIn(
            "serde\t^1.0.0\t^1.0.228\tCargo.toml", open_file().write.call_args.args[0]
        )

    def test_no_output_when_no_updates(self):
        with mock.patch.object(module, "process_manifest", return_value=[]):
            with mock.patch.dict(os.environ, {"GITHUB_OUTPUT": "github_output"}):
                with mock.patch("builtins.open", mock.mock_open()) as open_file:
                    with mock.patch.object(sys, "argv", ["script", "Cargo.toml"]):
                        module.main()

        open_file.assert_not_called()


if __name__ == "__main__":
    unittest.main()
