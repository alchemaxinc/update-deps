import os
import tempfile
import unittest
from pathlib import Path

from update_docker.updater import update_docker

# Stand-in tag listings keyed by crane repo (registry/repo, with implicit
# docker.io stripped) so tests don't shell out.
FAKE_TAGS = {
    "library/rust": ["1.94-alpine", "1.95-alpine", "1.95-slim-bookworm", "latest"],
    "getmeili/meilisearch": ["v1.42.1", "v1.43.0", "v2.0.0"],
    "public.ecr.aws/awsguru/aws-lambda-adapter": ["1.0.0", "1.1.0"],
    "library/redis": ["7.2", "7.4"],
}


def fake_lister(repo: str) -> list[str]:
    return FAKE_TAGS.get(repo, [])


class TestUpdater(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

        # Mirror the guinea-pig repo layout.
        (self.root / "Dockerfile").write_text(
            "FROM rust:1.94-alpine AS builder\n"
            "FROM getmeili/meilisearch:v1.42.1\n"
            "FROM public.ecr.aws/awsguru/aws-lambda-adapter:1.0.0\n",
            encoding="utf-8",
        )
        (self.root / "docker-compose.yml").write_text(
            "services:\n" "  cache:\n" "    image: redis:7.2\n",
            encoding="utf-8",
        )

    def _run(self, **overrides):
        kwargs = dict(
            root=self.root,
            dockerfile_glob="**/Dockerfile*",
            compose_glob="**/docker-compose*.y*ml",
            markdown_glob="",
            excluded_images=[],
            dry_run=False,
            tag_lister=fake_lister,
        )
        kwargs.update(overrides)
        return update_docker(**kwargs)

    def test_updates_dockerfile_and_compose(self):
        self.assertEqual(self._run(), 0)
        dockerfile = (self.root / "Dockerfile").read_text(encoding="utf-8")
        compose = (self.root / "docker-compose.yml").read_text(encoding="utf-8")

        # Variant suffix preserved.
        self.assertIn("rust:1.95-alpine", dockerfile)
        self.assertNotIn("rust:1.95-slim-bookworm", dockerfile)
        # Patch-level granularity preserved (we don't bump v1.42.1 → v2.0.0,
        # we bump to v2.0.0 verbatim because granularize keeps three parts).
        self.assertIn("getmeili/meilisearch:v2.0.0", dockerfile)
        self.assertIn("public.ecr.aws/awsguru/aws-lambda-adapter:1.1.0", dockerfile)
        # Stage alias not rewritten.
        self.assertIn("AS builder", dockerfile)
        # Compose updated.
        self.assertIn("redis:7.4", compose)

    def test_dry_run_does_not_write(self):
        self.assertEqual(self._run(dry_run=True), 0)
        dockerfile = (self.root / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("rust:1.94-alpine", dockerfile)
        self.assertIn("getmeili/meilisearch:v1.42.1", dockerfile)

    def test_excluded_images(self):
        self.assertEqual(self._run(excluded_images=["rust", "redis"]), 0)
        dockerfile = (self.root / "Dockerfile").read_text(encoding="utf-8")
        compose = (self.root / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("rust:1.94-alpine", dockerfile)
        self.assertIn("redis:7.2", compose)
        self.assertIn("getmeili/meilisearch:v2.0.0", dockerfile)

    def test_diff_minimality(self):
        self._run()
        dockerfile = (self.root / "Dockerfile").read_text(encoding="utf-8")
        # Stage alias, --platform-less FROM lines, and the trailing newline
        # all survive a single-line tag swap.
        self.assertEqual(dockerfile.count("\n"), 3)
        self.assertTrue(dockerfile.endswith("\n"))

    def test_markdown_opt_in(self):
        readme = self.root / "README.md"
        readme.write_text(
            "We pin rust:1.94-alpine and getmeili/meilisearch:v1.42.1.\n",
            encoding="utf-8",
        )
        self.assertEqual(self._run(markdown_glob="**/*.md"), 0)
        text = readme.read_text(encoding="utf-8")
        self.assertIn("rust:1.95-alpine", text)
        self.assertIn("getmeili/meilisearch:v2.0.0", text)

    def test_emits_github_output(self):
        with tempfile.NamedTemporaryFile("w+", delete=False) as out:
            out_path = out.name
        self.addCleanup(os.unlink, out_path)
        env = os.environ.copy()
        os.environ["GITHUB_OUTPUT"] = out_path
        try:
            self._run()
        finally:
            if "GITHUB_OUTPUT" in env:
                os.environ["GITHUB_OUTPUT"] = env["GITHUB_OUTPUT"]
            else:
                del os.environ["GITHUB_OUTPUT"]

        contents = Path(out_path).read_text(encoding="utf-8")
        self.assertIn("docker_updates<<ENDOFUPDATES", contents)
        self.assertIn("ENDOFUPDATES", contents)
        self.assertIn("rust:1.94-alpine\t1.94-alpine\t1.95-alpine", contents)


if __name__ == "__main__":
    unittest.main()
