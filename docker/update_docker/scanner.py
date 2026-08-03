from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal

from ruamel.yaml import YAML

SourceKind = Literal["dockerfile", "compose", "markdown"]


@dataclass(frozen=True)
class ImageRef:
    source_path: Path
    line_number: int
    source_kind: SourceKind
    registry: str
    repo: str
    tag: str

    @property
    def display(self) -> str:
        # Render the canonical "registry/repo:tag" form for logs and pull request rows.
        if self.registry == "docker.io" and self.repo.startswith("library/"):
            return f"{self.repo[len('library/'):]}:{self.tag}"

        if self.registry == "docker.io":
            return f"{self.repo}:{self.tag}"

        return f"{self.registry}/{self.repo}:{self.tag}"

    @property
    def crane_repo(self) -> str:
        if self.registry == "docker.io":
            return self.repo

        return f"{self.registry}/{self.repo}"

    @property
    def full_ref(self) -> str:
        return f"{self.registry}/{self.repo}:{self.tag}"


# Match `FROM [--platform=...] <ref> [AS <alias>]`. The final optional group
# captures the stage alias. The scanner skips later references to this alias.
_FROM_RE = re.compile(
    r"^\s*FROM\s+(?:--platform=\S+\s+)?(?P<ref>\S+)(?:\s+AS\s+(?P<alias>\S+))?\s*$",
    re.IGNORECASE,
)


def _split_image_ref(ref: str) -> tuple[str, str, str] | None:
    """Split an image reference into (registry, repository, tag).

    Return None for ``scratch``, digest-only references, or references without
    a tag.
    """
    if ref == "scratch":
        return None

    # Version 1 skips digest-pinned references with or without a tag.
    if "@sha256:" in ref or "@" in ref:
        return None

    if ":" not in ref.rsplit("/", 1)[-1]:
        # A reference without a tag cannot be updated.
        return None

    name_part, tag = ref.rsplit(":", 1)

    # Treat the leading path segment as a registry only when it resembles a
    # hostname. It contains ".", ":", or equals "localhost". Otherwise it is a
    # Docker Hub organization name.
    segments = name_part.split("/")
    if len(segments) == 1:
        registry = "docker.io"
        repo = f"library/{segments[0]}"
    elif "." in segments[0] or ":" in segments[0] or segments[0] == "localhost":
        registry = segments[0]
        repo = "/".join(segments[1:])
    else:
        registry = "docker.io"
        repo = name_part

    return registry, repo, tag


def scan_dockerfile(path: Path) -> list[ImageRef]:
    """Return image references from a Dockerfile without stage aliases.

    First collect each ``AS <alias>`` token. Then skip a later ``FROM <token>``
    when the token matches an alias in the same file.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # First, collect stage aliases in declaration order.
    aliases: list[str] = []
    parsed: list[tuple[int, str, str | None]] = []
    for idx, line in enumerate(lines, start=1):
        match = _FROM_RE.match(line)
        if not match:
            continue

        parsed.append((idx, match.group("ref"), match.group("alias")))
        if match.group("alias"):
            aliases.append(match.group("alias"))

    refs: list[ImageRef] = []
    seen_aliases: set[str] = set()
    for line_no, ref, alias in parsed:
        # This stage reference, for example FROM builder, is not an image.
        if ref in seen_aliases:
            if alias:
                seen_aliases.add(alias)
            continue

        split = _split_image_ref(ref)
        if split is None:
            if alias:
                seen_aliases.add(alias)
            continue

        registry, repo, tag = split
        refs.append(
            ImageRef(
                source_path=path,
                line_number=line_no,
                source_kind="dockerfile",
                registry=registry,
                repo=repo,
                tag=tag,
            )
        )

        if alias:
            seen_aliases.add(alias)

    return refs


def _walk_compose(node, callback) -> None:
    """Visit each ``image:`` key in a compose mapping."""
    if isinstance(node, list):
        for item in node:
            _walk_compose(item, callback)
        return

    if not isinstance(node, dict):
        return

    # ``dict.get`` includes values inherited through YAML merges. These values
    # have no source location in the service. Update the explicit anchor instead.
    if "image" in node and isinstance(node["image"], str):
        key_position = node.lc.key("image")
        if key_position is not None:
            callback(node["image"], key_position[0] + 1)

    for value in node.values():
        _walk_compose(value, callback)


def scan_compose(path: Path) -> list[ImageRef]:
    """Return image references from a docker-compose file."""
    text = path.read_text(encoding="utf-8")
    yaml = YAML()
    yaml.preserve_quotes = True
    try:
        doc = yaml.load(text)
    except Exception as exc:
        print(
            f"::warning file={path}::Failed to parse compose YAML: {exc}",
            file=sys.stderr,
        )
        return []

    if not isinstance(doc, dict):
        return []

    refs: list[ImageRef] = []

    def collect(image: str, line_no: int) -> None:
        split = _split_image_ref(image)
        if split is None:
            return

        registry, repo, tag = split
        refs.append(
            ImageRef(
                source_path=path,
                line_number=line_no,
                source_kind="compose",
                registry=registry,
                repo=repo,
                tag=tag,
            )
        )

    _walk_compose(doc, collect)
    return refs


def collect_files(root: Path, glob: str) -> list[Path]:
    if not glob:
        return []

    return sorted(p for p in root.glob(glob) if p.is_file())


def scan_dockerfiles(root: Path, glob: str) -> list[ImageRef]:
    refs: list[ImageRef] = []
    for path in collect_files(root, glob):
        refs.extend(scan_dockerfile(path))
    return refs


def scan_compose_files(root: Path, glob: str) -> list[ImageRef]:
    refs: list[ImageRef] = []
    for path in collect_files(root, glob):
        refs.extend(scan_compose(path))
    return refs


def _markdown_pattern(needle: str) -> re.Pattern[str]:
    # Leading lookbehind rejects partial matches, such as ``my-rust:1.94-alpine``
    # when the action updates ``rust:1.94-alpine``.
    # Trailing lookahead rejects only text that can extend the tag, such as
    # word characters or dashes. Punctuation, such as ``.``, ``,``, and ``)``,
    # does not block a replacement.
    return re.compile(rf"(?<![\w./-]){re.escape(needle)}(?![\w-])")


def _ref_needles(ref: ImageRef) -> list[str]:
    """Return search forms that match ``ref`` in Markdown text."""
    needles = [ref.display]
    if ref.full_ref not in needles:
        needles.append(ref.full_ref)

    return needles


def find_markdown_occurrences(
    path: Path, candidates: list[ImageRef]
) -> Iterator[tuple[ImageRef, int]]:
    """Yield (reference, line_number) for each known Markdown reference.

    Match ``registry/repo:tag`` and bare ``repo:tag`` forms for Docker Hub
    library images. Use word-style boundaries.
    """
    text = path.read_text(encoding="utf-8")
    for ref in candidates:
        for needle in _ref_needles(ref):
            for match in _markdown_pattern(needle).finditer(text):
                yield ref, text.count("\n", 0, match.start()) + 1


def replace_dockerfile_tag(text: str, ref: ImageRef, new_tag: str) -> str:
    """Replace the tag on the matching ``FROM`` line."""
    lines = text.splitlines(keepends=True)
    target = ref.line_number - 1
    if target < 0 or target >= len(lines):
        return text

    line = lines[target]
    match = _FROM_RE.match(line)
    if not match:
        return text

    old_ref = match.group("ref")
    if not old_ref.endswith(f":{ref.tag}"):
        return text

    new_ref = old_ref[: -len(ref.tag)] + new_tag
    lines[target] = line.replace(old_ref, new_ref, 1)
    return "".join(lines)


def replace_compose_tag(text: str, ref: ImageRef, new_tag: str) -> str:
    """Replace the image scalar on the parser-identified ``image:`` line."""
    lines = text.splitlines(keepends=True)
    target = ref.line_number - 1
    if target < 0 or target >= len(lines):
        return text

    line = lines[target]
    image_forms = sorted({ref.display, ref.full_ref}, key=len, reverse=True)
    match = re.match(
        rf"^(?P<prefix>\s*image\s*:\s*)(?P<quote>['\"]?)(?P<image>{'|'.join(re.escape(image) for image in image_forms)})(?P=quote)(?P<suffix>\s*(?:#.*)?(?:\r?\n)?)$",
        line,
    )
    if match is None:
        return text

    new_image = match.group("image")[: -len(ref.tag)] + new_tag
    lines[target] = (
        f"{match.group('prefix')}{match.group('quote')}{new_image}"
        f"{match.group('quote')}{match.group('suffix')}"
    )
    return "".join(lines)


def replace_markdown_occurrences(text: str, ref: ImageRef, new_tag: str) -> str:
    """Replace each word-bounded occurrence of the reference display form."""
    for needle in _ref_needles(ref):
        replacement = needle[: -len(ref.tag)] + new_tag
        text = _markdown_pattern(needle).sub(replacement, text)

    return text
