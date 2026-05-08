import unittest

from update_docker import versioning


class TestParseImageTag(unittest.TestCase):
    def test_plain_semver(self):
        v = versioning.parse_image_tag("1.42.1")
        self.assertEqual(v.prefix, "")
        self.assertEqual(v.numeric, (1, 42, 1))
        self.assertEqual(v.suffix, "")

    def test_v_prefix(self):
        v = versioning.parse_image_tag("v1.42.1")
        self.assertEqual(v.prefix, "v")
        self.assertEqual(v.numeric, (1, 42, 1))
        self.assertEqual(v.suffix, "")

    def test_alpine_suffix(self):
        v = versioning.parse_image_tag("1.94-alpine")
        self.assertEqual(v.prefix, "")
        self.assertEqual(v.numeric, (1, 94))
        self.assertEqual(v.suffix, "-alpine")

    def test_compound_suffix(self):
        v = versioning.parse_image_tag("1.94-slim-bookworm")
        self.assertEqual(v.numeric, (1, 94))
        self.assertEqual(v.suffix, "-slim-bookworm")

    def test_alpine_with_dot(self):
        v = versioning.parse_image_tag("1.94-alpine3.20")
        self.assertEqual(v.numeric, (1, 94))
        self.assertEqual(v.suffix, "-alpine3.20")

    def test_major_only(self):
        v = versioning.parse_image_tag("1-alpine")
        self.assertEqual(v.numeric, (1,))
        self.assertEqual(v.suffix, "-alpine")

    def test_non_semver_returns_none(self):
        self.assertIsNone(versioning.parse_image_tag("latest"))
        self.assertIsNone(versioning.parse_image_tag("nightly"))
        self.assertIsNone(versioning.parse_image_tag("edge"))
        self.assertIsNone(versioning.parse_image_tag(""))

    def test_more_than_three_parts_rejected(self):
        self.assertIsNone(versioning.parse_image_tag("1.2.3.4"))


class TestSelectLatestMatching(unittest.TestCase):
    def test_preserves_prefix_and_suffix(self):
        current = versioning.parse_image_tag("1.94-alpine")
        tags = [
            "1.94-alpine",
            "1.95-alpine",
            "1.95-slim-bookworm",
            "v1.95-alpine",
            "1.95",
            "latest",
        ]
        self.assertEqual(
            versioning.select_latest_matching(tags, current), "1.95-alpine"
        )

    def test_picks_highest(self):
        current = versioning.parse_image_tag("v1.42.1")
        tags = ["v1.42.0", "v1.42.1", "v1.43.0", "v2.0.0", "1.43.0"]
        self.assertEqual(versioning.select_latest_matching(tags, current), "v2.0.0")

    def test_returns_none_when_no_match(self):
        current = versioning.parse_image_tag("1.94-alpine")
        self.assertIsNone(
            versioning.select_latest_matching(["latest", "nightly"], current)
        )


class TestGranularizeTag(unittest.TestCase):
    def test_major_only(self):
        self.assertEqual(
            versioning.granularize_tag("1-alpine", "1.95.0-alpine"), "1-alpine"
        )

    def test_minor_only(self):
        self.assertEqual(
            versioning.granularize_tag("1.94-alpine", "1.95.0-alpine"), "1.95-alpine"
        )

    def test_patch(self):
        self.assertEqual(versioning.granularize_tag("v1.42.1", "v1.43.2"), "v1.43.2")

    def test_preserves_prefix_when_latest_lacks_it(self):
        self.assertEqual(versioning.granularize_tag("v1.42.1", "1.43.2"), "v1.43.2")

    def test_unparseable_returns_latest_verbatim(self):
        self.assertEqual(versioning.granularize_tag("latest", "1.43.2"), "1.43.2")


if __name__ == "__main__":
    unittest.main()
