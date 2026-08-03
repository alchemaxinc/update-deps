import unittest
from pathlib import Path


ACTION = Path(__file__).parents[1] / "action.yml"


class TestCircleCIOrbAction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.action = ACTION.read_text(encoding="utf-8")

    def test_yq_binaries_are_platform_specific_and_sha256_pinned(self):
        expected_assets = {
            "yq_linux_amd64": "6dc2d0cd4e0caca5aeffd0d784a48263591080e4a0895abe69f3a76eb50d1ba3",
            "yq_linux_arm64": "8c12fcc10e14774ca6624cc282f092a526568b036fe1192258c3aecbad56d063",
            "yq_darwin_amd64": "114d0fab983929a76b39d792dea339b07631e0fb2f195d9e43815f907308e309",
            "yq_darwin_arm64": "638ea9b4e7a89e12159e5077556f0d10559b49df3ec67504dd2a567fec2bb47e",
        }

        for asset, checksum in expected_assets.items():
            self.assertIn(f"yq_asset='{asset}'", self.action)
            self.assertIn(f"yq_checksum='{checksum}'", self.action)

        self.assertIn("sha256sum --check --status", self.action)
        self.assertIn("shasum -a 256", self.action)
        self.assertIn(
            "key: yq-${{ inputs.yq-version }}-${{ runner.os }}-${{ runner.arch }}",
            self.action,
        )

    def test_latest_versions_come_from_the_circleci_orb_registry(self):
        self.assertIn("https://app.circleci.com/api/v2/orbs", self.action)
        self.assertIn('--data-urlencode "ns=${orb_namespace}"', self.action)
        self.assertIn('--data-urlencode "name=${orb_name}"', self.action)
        self.assertIn("version=volatile", self.action)
        self.assertNotIn("CircleCI-Public/${orb_repo_name}-orb", self.action)


if __name__ == "__main__":
    unittest.main()
