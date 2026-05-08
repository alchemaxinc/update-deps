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
        # Re-render in canonical "registry/repo:tag" form for logs and PR rows.
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


# Matches `FROM [--platform=...] <ref> [AS <alias>]`. The optional final group
# captures the stage alias so we can skip later refs that point to it.
_FROM_RE = re.compile(
    r"^\s*FROM\s+(?:--platform=\S+\s+)?(?P<ref>\S+)(?:\s+AS\s+(?P<alias>\S+))?\s*$",
    re.IGNORECASE,
)


def _split_image_ref(ref: str) -> tuple[str, str, str] | None:
    """Split an image ref into (registry, repo, tag).

    Returns None for refs we cannot or should not handle: ``scratch``,
    digest-only refs, or refs that lack a tag.
    """
    if ref == "scratch":
        return None

    # Skip any digest-pinned ref (with or without tag) per design v1.
    if "@sha256:" in ref or "@" in ref:
        return None

    if ":" not in ref.rsplit("/", 1)[-1]:
        # No tag → can't bump it.
        return None

    name_part, tag = ref.rsplit(":", 1)

    # A leading path segment is treated as a registry only when it looks like
    # a hostname (contains ".", ":", or equals "localhost"). Otherwise it's a
    # Docker Hub org name.
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
    """Return image refs from a Dockerfile, skipping stage aliases.

    Two-pass: first collect every ``AS <alias>`` token, then skip any later
    ``FROM <token>`` whose token matches a previously-declared alias in the
    same file.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # First pass: collect stage aliases in declaration order.
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
        if ref in seen_aliases:
            # Stage reference (e.g. FROM builder), not an image — skip.
            if alias:
                seen_aliases.add(alias)
            continue

        split = _split_image_ref(ref)
        if split is not None:
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
    """Recursively visit every ``image:`` key in a compose mapping."""
    if isinstance(node, list):
        for item in node:
            _walk_compose(item, callback)
        return
    if not isinstance(node, dict):
        return
    if isinstance(node.get("image"), str):
        callback(node["image"], node.lc.data["image"][0] + 1 if hasattr(node, "lc") else 0)
    for value in node.values():
        _walk_compose(value, callback)


def scan_compose(path: Path) -> list[ImageRef]:
    """Return image refs from a docker-compose file."""
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
    # Leading lookbehind rejects partial-word collisions like
    # ``my-rust:1.94-alpine`` when updating ``rust:1.94-alpine``.
    # Trailing lookahead rejects only continuations that could extend the
    # tag itself (word chars or dashes); punctuation like ``.``, ``,``, or
    # ``)`` is fine — the period at the end of a sentence must not block
    # replacement.
    return re.compile(rf"(?<![\w./-]){re.escape(needle)}(?![\w-])")


def find_markdown_occurrences(
    path: Path, candidates: list[ImageRef]
) -> Iterator[tuple[ImageRef, int]]:
    """Yield (ref, line_number) for each markdown match of a known ref.

    Both ``registry/repo:tag`` and the bare ``repo:tag`` form (for Docker Hub
    library images) are matched, with word-style boundaries.
    """
    text = path.read_text(encoding="utf-8")
    for ref in candidates:
        needles = [ref.display]
        full = f"{ref.registry}/{ref.repo}:{ref.tag}"
        if full not in needles:
            needles.append(full)
        for needle in needles:
            pattern = _markdown_pattern(needle)
            for match in pattern.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                yield ref, line_no


def replace_dockerfile_tag(text: str, ref: ImageRef, new_tag: str) -> str:
    """Replace the tag on the matching ``FROM`` line, leaving the rest alone."""
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
    """Replace the tag on the compose ``image:`` line."""
    lines = text.splitlines(keepends=True)
    target = ref.line_number - 1
    if target < 0 or target >= len(lines):
        return text
    line = lines[target]
    if f":{ref.tag}" not in line:
        return text
    # Replace the last colon-tag occurrence on the line so registry ports
    # (e.g. ``localhost:5000/...``) aren't rewritten by accident.
    suffix = f":{ref.tag}"
    idx = line.rfind(suffix)
    lines[target] = line[:idx] + f":{new_tag}" + line[idx + len(suffix) :]
    return "".join(lines)


def replace_markdown_occurrences(
    text: str, ref: ImageRef, new_tag: str
) -> str:
    """Replace every word-bounded occurrence of the ref's display form."""
    needles = [ref.display]
    full = f"{ref.registry}/{ref.repo}:{ref.tag}"
    if full not in needles:
        needles.append(full)
    for needle in needles:
        pattern = _markdown_pattern(needle)
        replacement = needle[: -len(ref.tag)] + new_tag
        text = pattern.sub(replacement, text)
    return text
