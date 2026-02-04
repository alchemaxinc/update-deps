import unittest

from update_actions import versioning


class TestVersioning(unittest.TestCase):
    def test_parse_version_accepts_simple_semver(self):
        self.assertEqual(str(versioning.parse_version("v1")), "1.0.0")
        self.assertEqual(str(versioning.parse_version("1.2")), "1.2.0")
        self.assertEqual(str(versioning.parse_version("1.2.3")), "1.2.3")

    def test_parse_version_rejects_invalid(self):
        self.assertIsNone(versioning.parse_version("1.2.3-beta"))
        self.assertIsNone(versioning.parse_version("1.2.3.4"))
        self.assertIsNone(versioning.parse_version("foo"))

    def test_select_latest_tag_ignores_invalid(self):
        tags = ["v1", "v2", "1.2.3", "not-a-tag"]
        self.assertEqual(versioning.select_latest_tag(tags), "v2")


if __name__ == "__main__":
    unittest.main()
