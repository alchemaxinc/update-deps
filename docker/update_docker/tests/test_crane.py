import subprocess
import unittest
from unittest import mock

from update_docker import crane


class TestCraneList(unittest.TestCase):
    def test_returns_tag_list(self):
        completed = mock.Mock()
        completed.returncode = 0
        completed.stdout = "1.0\n1.1\n\nlatest\n"
        completed.stderr = ""
        with mock.patch("subprocess.run", return_value=completed) as run:
            tags = crane.crane_list("library/rust")
        run.assert_called_once_with(
            ["crane", "ls", "library/rust"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(tags, ["1.0", "1.1", "latest"])

    def test_returns_empty_on_error(self):
        completed = mock.Mock()
        completed.returncode = 1
        completed.stdout = ""
        completed.stderr = "boom"
        with mock.patch("subprocess.run", return_value=completed):
            with mock.patch("update_docker.crane.time.sleep"):
                self.assertEqual(crane.crane_list("library/rust"), [])

    def test_retries_timeout(self):
        completed = mock.Mock(returncode=0, stdout="1.0\n", stderr="")
        with mock.patch(
            "subprocess.run",
            side_effect=[subprocess.TimeoutExpired(["crane"], 30), completed],
        ) as run:
            with mock.patch("update_docker.crane.time.sleep") as sleep:
                self.assertEqual(crane.crane_list("library/rust"), ["1.0"])
        self.assertEqual(run.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_returns_empty_when_crane_missing(self):
        with mock.patch("subprocess.run", side_effect=FileNotFoundError()):
            self.assertEqual(crane.crane_list("library/rust"), [])


if __name__ == "__main__":
    unittest.main()
