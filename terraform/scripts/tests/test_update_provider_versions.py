import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.update_provider_versions as module


class TestUpdateProviderVersions(unittest.TestCase):
    def test_updates_version_constraints(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            versions_path = workdir / "versions.json"
            tf_path = workdir / "main.tf"

            versions_path.write_text(
                json.dumps(
                    {
                        "provider_selections": {
                            "registry.terraform.io/hashicorp/aws": "5.0.0"
                        }
                    }
                ),
                encoding="utf-8",
            )

            tf_path.write_text(
                """
                terraform {
                  required_providers {
                    aws = {
                      source  = "hashicorp/aws"
                      version = "~> 5.0"
                    }
                  }
                }
                """,
                encoding="utf-8",
            )

            mock_result = mock.Mock(returncode=0, stdout='{"version": "5.2.1"}')
            with mock.patch.object(module.subprocess, "run", return_value=mock_result):
                with mock.patch.object(
                    sys, "argv", ["script", str(workdir), str(versions_path)]
                ):
                    module.main()

            updated = tf_path.read_text(encoding="utf-8")
            self.assertIn('version = "~> 5.2"', updated)

    def test_missing_versions_file_exits(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            with mock.patch.object(sys, "argv", ["script", str(workdir)]):
                with self.assertRaises(SystemExit) as ctx:
                    module.main()

            self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
