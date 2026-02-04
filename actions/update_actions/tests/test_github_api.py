import unittest
from unittest import mock

from update_actions import github_api


class TestGithubApi(unittest.TestCase):
    def test_fetch_release_tags_filters_prerelease(self):
        completed = mock.Mock()
        completed.returncode = 0
        completed.stdout = "v1\tfalse\nv2\ttrue\n1.2.3\tfalse\n"
        completed.stderr = ""
        with mock.patch("subprocess.run", return_value=completed) as run:
            tags = github_api.fetch_release_tags("actions/checkout")
        run.assert_called_once()
        self.assertEqual(tags, ["v1", "1.2.3"])

    def test_fetch_release_tags_handles_error(self):
        completed = mock.Mock()
        completed.returncode = 1
        completed.stdout = ""
        completed.stderr = "boom"
        with mock.patch("subprocess.run", return_value=completed):
            self.assertEqual(github_api.fetch_release_tags("actions/checkout"), [])


if __name__ == "__main__":
    unittest.main()
