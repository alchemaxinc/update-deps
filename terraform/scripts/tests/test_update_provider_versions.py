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
            output_file = workdir / "github_output"

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
                with mock.patch.dict("os.environ", {"GITHUB_OUTPUT": str(output_file)}):
                    with mock.patch.object(
                        sys, "argv", ["script", str(workdir), str(versions_path)]
                    ):
                        module.main()

            updated = tf_path.read_text(encoding="utf-8")
            output = output_file.read_text(encoding="utf-8")
            self.assertIn('version = "~> 5.2"', updated)
            self.assertIn("provider_updates<<ENDOFUPDATES", output)
            self.assertIn("hashicorp/aws\t~> 5.0\t~> 5.2\tmain.tf", output)

    def test_updates_version_constraints_without_github_output(self):
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

    def test_updates_when_current_equals_latest(self):
        """Covers the real-world case: terraform init already installed the
        latest version within the constraint, so current == latest, but the
        constraint in the .tf file is still stale (e.g. ~> 6.0 vs 6.35.1)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            versions_path = workdir / "versions.json"
            tf_path = workdir / "main.tf"

            versions_path.write_text(
                json.dumps(
                    {
                        "provider_selections": {
                            "registry.terraform.io/hashicorp/aws": "6.35.1",
                            "registry.terraform.io/lukasaron/stripe": "3.4.1",
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
                      version = "~> 6.0"
                    }
                    stripe = {
                      source  = "lukasaron/stripe"
                      version = "~> 3.3"
                    }
                  }
                }
                """,
                encoding="utf-8",
            )

            def fake_curl(*args, **kwargs):
                cmd = args[0]
                url = cmd[-1]
                if "hashicorp/aws" in url:
                    return mock.Mock(returncode=0, stdout='{"version": "6.35.1"}')
                elif "lukasaron/stripe" in url:
                    return mock.Mock(returncode=0, stdout='{"version": "3.4.1"}')
                return mock.Mock(returncode=1, stdout="")

            with mock.patch.object(module.subprocess, "run", side_effect=fake_curl):
                with mock.patch.object(
                    sys, "argv", ["script", str(workdir), str(versions_path)]
                ):
                    module.main()

            updated = tf_path.read_text(encoding="utf-8")
            self.assertIn('version = "~> 6.35"', updated)
            self.assertIn('version = "~> 3.4"', updated)

    def test_missing_versions_file_exits(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            with mock.patch.object(sys, "argv", ["script", str(workdir)]):
                with self.assertRaises(SystemExit) as ctx:
                    module.main()

            self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
