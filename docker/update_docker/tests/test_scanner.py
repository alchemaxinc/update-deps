import tempfile
import unittest
from pathlib import Path

from update_docker import scanner


class TestSplitImageRef(unittest.TestCase):
    def test_single_segment_uses_library(self):
        self.assertEqual(
            scanner._split_image_ref("rust:1.94-alpine"),
            ("docker.io", "library/rust", "1.94-alpine"),
        )

    def test_org_image(self):
        self.assertEqual(
            scanner._split_image_ref("getmeili/meilisearch:v1.42.1"),
            ("docker.io", "getmeili/meilisearch", "v1.42.1"),
        )

    def test_third_party_registry(self):
        self.assertEqual(
            scanner._split_image_ref("public.ecr.aws/awsguru/aws-lambda-adapter:1.0.0"),
            ("public.ecr.aws", "awsguru/aws-lambda-adapter", "1.0.0"),
        )

    def test_localhost_registry(self):
        self.assertEqual(
            scanner._split_image_ref("localhost:5000/myimage:1.0"),
            ("localhost:5000", "myimage", "1.0"),
        )

    def test_scratch_skipped(self):
        self.assertIsNone(scanner._split_image_ref("scratch"))

    def test_digest_pinned_skipped(self):
        self.assertIsNone(scanner._split_image_ref("rust:1.94-alpine@sha256:abcd1234"))
        self.assertIsNone(scanner._split_image_ref("rust@sha256:abcd1234"))

    def test_no_tag_skipped(self):
        self.assertIsNone(scanner._split_image_ref("rust"))


class TestScanDockerfile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def _write(self, name: str, body: str) -> Path:
        path = self.root / name
        path.write_text(body, encoding="utf-8")
        return path

    def test_guinea_pig_three_lines(self):
        path = self._write(
            "Dockerfile",
            "FROM rust:1.94-alpine AS builder\n"
            "FROM getmeili/meilisearch:v1.42.1\n"
            "FROM public.ecr.aws/awsguru/aws-lambda-adapter:1.0.0\n",
        )
        refs = scanner.scan_dockerfile(path)
        self.assertEqual(len(refs), 3)
        self.assertEqual(refs[0].repo, "library/rust")
        self.assertEqual(refs[0].tag, "1.94-alpine")
        self.assertEqual(refs[1].repo, "getmeili/meilisearch")
        self.assertEqual(refs[2].registry, "public.ecr.aws")
        self.assertEqual(refs[2].repo, "awsguru/aws-lambda-adapter")

    def test_skips_stage_alias_reference(self):
        path = self._write(
            "Dockerfile",
            "FROM rust:1.94-alpine AS builder\n"
            "FROM alpine:3.20 AS runtime\n"
            "FROM builder\n"
            "FROM runtime AS final\n",
        )
        refs = scanner.scan_dockerfile(path)
        self.assertEqual([r.repo for r in refs], ["library/rust", "library/alpine"])

    def test_skips_scratch_and_digest(self):
        path = self._write(
            "Dockerfile",
            "FROM scratch\n" "FROM rust:1.94-alpine@sha256:abc\n" "FROM alpine:3.20\n",
        )
        refs = scanner.scan_dockerfile(path)
        self.assertEqual([r.repo for r in refs], ["library/alpine"])

    def test_platform_flag(self):
        path = self._write(
            "Dockerfile",
            "FROM --platform=linux/amd64 rust:1.94-alpine AS builder\n",
        )
        refs = scanner.scan_dockerfile(path)
        self.assertEqual(refs[0].repo, "library/rust")
        self.assertEqual(refs[0].tag, "1.94-alpine")

    def test_replace_dockerfile_tag(self):
        path = self._write("Dockerfile", "FROM rust:1.94-alpine AS builder\n")
        refs = scanner.scan_dockerfile(path)
        text = path.read_text(encoding="utf-8")
        updated = scanner.replace_dockerfile_tag(text, refs[0], "1.95-alpine")
        self.assertEqual(updated, "FROM rust:1.95-alpine AS builder\n")


class TestScanCompose(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_basic_compose(self):
        path = self.root / "docker-compose.yml"
        path.write_text(
            "services:\n"
            "  meili:\n"
            "    image: getmeili/meilisearch:v1.42.1\n"
            "  cache:\n"
            "    image: redis:7.2\n",
            encoding="utf-8",
        )
        refs = scanner.scan_compose(path)
        repos = sorted(r.repo for r in refs)
        self.assertEqual(repos, ["getmeili/meilisearch", "library/redis"])

    def test_replace_compose_tag(self):
        path = self.root / "docker-compose.yml"
        path.write_text(
            "services:\n  meili:\n    image: getmeili/meilisearch:v1.42.1\n",
            encoding="utf-8",
        )
        refs = scanner.scan_compose(path)
        text = path.read_text(encoding="utf-8")
        updated = scanner.replace_compose_tag(text, refs[0], "v1.43.0")
        self.assertIn("getmeili/meilisearch:v1.43.0", updated)
        self.assertNotIn("v1.42.1", updated)


class TestMarkdown(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def _ref(self, registry, repo, tag) -> scanner.ImageRef:
        return scanner.ImageRef(
            source_path=self.root / "x",
            line_number=1,
            source_kind="dockerfile",
            registry=registry,
            repo=repo,
            tag=tag,
        )

    def test_word_boundary_rejects_partial(self):
        text = "Use rust:1.94-alpine in CI.\n" "But never my-rust:1.94-alpine.\n"
        ref = self._ref("docker.io", "library/rust", "1.94-alpine")
        updated = scanner.replace_markdown_occurrences(text, ref, "1.95-alpine")
        self.assertIn("Use rust:1.95-alpine", updated)
        self.assertIn("my-rust:1.94-alpine", updated)

    def test_full_form_matches(self):
        text = "See public.ecr.aws/awsguru/aws-lambda-adapter:1.0.0 for details.\n"
        ref = self._ref("public.ecr.aws", "awsguru/aws-lambda-adapter", "1.0.0")
        updated = scanner.replace_markdown_occurrences(text, ref, "1.1.0")
        self.assertIn(":1.1.0", updated)
        self.assertNotIn(":1.0.0", updated)


if __name__ == "__main__":
    unittest.main()
