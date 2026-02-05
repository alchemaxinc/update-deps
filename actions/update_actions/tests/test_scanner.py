import tempfile
import unittest
from pathlib import Path

from update_actions import scanner


class TestScanner(unittest.TestCase):
    def test_get_granularity(self):
        """Test granularity detection for various version formats."""
        test_cases = [
            # (version, expected_granularity)
            ("1", "major"),
            ("2", "major"),
            ("v1", "major"),
            ("v10", "major"),
            ("1.2", "minor"),
            ("2.5", "minor"),
            ("v1.2", "minor"),
            ("v3.14", "minor"),
            ("1.2.3", "patch"),
            ("2.5.8", "patch"),
            ("v1.2.3", "patch"),
            ("v3.14.159", "patch"),
            ("1.2.3.4", "patch"),  # More than 3 parts
            ("v1.2.3.4", "patch"),
        ]

        for version, expected in test_cases:
            with self.subTest(version=version):
                result = scanner.get_granularity(version)
                self.assertEqual(result, expected)

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

    def test_apply_updates_preserves_non_uses_variables(self):
        """
        Regression test: Ensure that non-'uses' variables and multi-line env vars
        are not modified when updating action versions.

        This tests the issue where LOCAL_VERSION and LATEST_VERSION environment
        variables were being incorrectly split across multiple lines.
        """
        text = """name: Automatic Version Synchronization

on:
  workflow_dispatch:
  schedule:
    - cron: "0 0 * * *"

env:
  PYTHON_VERSION: "3.14"

jobs:
  update-version:
    runs-on: ubuntu-latest
    env:
      LOCAL_VERSION: ${{ needs.get-current-local-version.outputs.local_version }}
      LATEST_VERSION: ${{ needs.get-newest-version.outputs.latest_version }}
    needs:
      - get-newest-version
      - get-current-local-version

    steps:
      - name: Create temporary GitHub App Token
        id: app
        uses: actions/create-github-app-token@v1
        with:
          owner: ${{ github.repository_owner }}
          app-id: ${{ vars.BOT_APP_ID }}
          private-key: ${{ secrets.BOT_PRIVATE_KEY }}

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          cache: "pip"
          python-version: "${{ env.PYTHON_VERSION }}"

      - name: Print and verify versions
        id: print-versions
        run: |
          echo "Local version: $LOCAL_VERSION"
          echo "Latest version: $LATEST_VERSION"
"""

        # Upgrade specific actions to new versions
        upgrades = {
            ("actions/create-github-app-token", "v1"): "v2.2.1",
            ("actions/setup-python", "v5"): "v6.2.0",
        }

        updated = scanner.apply_updates(text, upgrades)

        # Verify that the uses entries were updated
        self.assertIn("actions/create-github-app-token@v2", updated)
        self.assertIn("actions/setup-python@v6", updated)

        # Verify that non-uses variables are preserved exactly as-is
        self.assertIn('PYTHON_VERSION: "3.14"', updated)
        self.assertIn(
            "LOCAL_VERSION: ${{ needs.get-current-local-version.outputs.local_version }}",
            updated,
        )
        self.assertIn(
            "LATEST_VERSION: ${{ needs.get-newest-version.outputs.latest_version }}",
            updated,
        )

        # Verify that the run command is not split across lines
        self.assertIn('run: |\n          echo "Local version: $LOCAL_VERSION"', updated)
        self.assertIn('echo "Latest version: $LATEST_VERSION"', updated)

        # Verify that other comments and structure are preserved
        self.assertIn('cron: "0 0 * * *"', updated)


if __name__ == "__main__":
    unittest.main()
