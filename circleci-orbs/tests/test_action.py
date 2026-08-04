import unittest
from pathlib import Path


ACTION = Path(__file__).parents[1] / "action.yml"


class TestCircleCIOrbAction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.action = ACTION.read_text(encoding="utf-8")

    def test_yq_binaries_are_platform_specific(self):
        for asset in (
            "yq_linux_amd64",
            "yq_linux_arm64",
            "yq_darwin_amd64",
            "yq_darwin_arm64",
        ):
            self.assertIn(f"yq_asset='{asset}'", self.action)

        self.assertIn(
            "key: yq-${{ inputs.yq-version }}-${{ runner.os }}-${{ runner.arch }}",
            self.action,
        )

    def test_dry_run_does_not_edit_configuration(self):
        self.assertIn("DRY_RUN: ${{ inputs.dry-run }}", self.action)
        self.assertIn('if [ "$DRY_RUN" = "true" ]; then', self.action)

    def test_latest_versions_come_from_the_circleci_orb_registry(self):
        self.assertIn("https://app.circleci.com/api/v2/orbs", self.action)
        self.assertIn('--data-urlencode "ns=${orb_namespace}"', self.action)
        self.assertIn('--data-urlencode "name=${orb_name}"', self.action)
        self.assertIn("version=volatile", self.action)
        self.assertNotIn("CircleCI-Public/${orb_repo_name}-orb", self.action)


if __name__ == "__main__":
    unittest.main()
