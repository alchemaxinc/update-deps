import tempfile
import unittest
from pathlib import Path
from unittest import mock

from update_actions import updater


class TestUpdater(unittest.TestCase):
    def test_update_actions_writes_updates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workflow_dir = root / ".github/workflows"
            workflow_dir.mkdir(parents=True)
            workflow = workflow_dir / "ci.yml"
            workflow.write_text(
                """
                jobs:
                  build:
                    steps:
                      - uses: actions/checkout@v3
                """,
                encoding="utf-8",
            )

            with mock.patch(
                "update_actions.updater.fetch_release_tags",
                return_value=["v2", "v4"],
            ):
                updater.update_actions(
                    root=root,
                    file_glob=".github/**/*.yml",
                    prefixes=["actions"],
                    dry_run=False,
                )

            updated = workflow.read_text(encoding="utf-8")
            self.assertIn("actions/checkout@v4", updated)

    def test_update_actions_dry_run_no_write(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workflow_dir = root / ".github/workflows"
            workflow_dir.mkdir(parents=True)
            workflow = workflow_dir / "ci.yml"
            original = """
            jobs:
              build:
                steps:
                  - uses: actions/checkout@v3
            """
            workflow.write_text(original, encoding="utf-8")

            with mock.patch(
                "update_actions.updater.fetch_release_tags",
                return_value=["v4"],
            ):
                updater.update_actions(
                    root=root,
                    file_glob=".github/**/*.yml",
                    prefixes=["actions"],
                    dry_run=True,
                )

            self.assertEqual(workflow.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
