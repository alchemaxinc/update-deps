from __future__ import annotations

import re
from dataclasses import dataclass

import semver

# A Docker tag we can compare numerically: optional "v" prefix, dotted
# numeric core, optional "-suffix" with letters/digits/dots/dashes
# (e.g. "-alpine", "-slim-bookworm", "-alpine3.20").
TAG_PATTERN = re.compile(
    r"^(?P<prefix>v?)(?P<numeric>\d+(?:\.\d+){0,2})(?P<suffix>(?:-[A-Za-z0-9][A-Za-z0-9.\-]*)?)$"
)


@dataclass(frozen=True)
class TagVariant:
    prefix: str           # "" or "v"
    numeric: tuple[int, ...]
    suffix: str           # "" or e.g. "-alpine"

    @property
    def version(self) -> semver.Version:
        parts = list(self.numeric) + [0] * (3 - len(self.numeric))
        return semver.Version(parts[0], parts[1], parts[2])


def parse_image_tag(tag: str) -> TagVariant | None:
    """Parse an image tag into prefix/numeric/suffix, or None if not numeric.

    Tags such as ``latest``, ``nightly``, or ``edge`` return ``None`` so the
    caller can skip them.
    """
    match = TAG_PATTERN.match(tag)
    if not match:
        return None

    numeric_parts = tuple(int(part) for part in match.group("numeric").split("."))
    return TagVariant(
        prefix=match.group("prefix"),
        numeric=numeric_parts,
        suffix=match.group("suffix"),
    )


def select_latest_matching(tags: list[str], current: TagVariant) -> str | None:
    """Return the highest tag whose prefix and suffix match ``current``.

    Tags that do not parse, or whose prefix/suffix differ from ``current``,
    are ignored. This keeps ``rust:1.94-alpine`` from being bumped across
    variants to ``rust:1.95-slim-bookworm``.
    """
    best_tag: str | None = None
    best_version: semver.Version | None = None

    for tag in tags:
        variant = parse_image_tag(tag)
        if variant is None:
            continue
        if variant.prefix != current.prefix or variant.suffix != current.suffix:
            continue

        version = variant.version
        if best_version is None or version > best_version:
            best_version = version
            best_tag = tag

    return best_tag


def granularize_tag(current_tag: str, latest_tag: str) -> str:
    """Render ``latest_tag`` at the same dot-depth as ``current_tag``.

    ``1`` stays major-only, ``1.94`` stays minor-only, ``v1.42.1`` stays
    patch-specific. The current tag's prefix/suffix are preserved.
    """
    current = parse_image_tag(current_tag)
    latest = parse_image_tag(latest_tag)
    if current is None or latest is None:
        return latest_tag

    depth = len(current.numeric)
    numeric = ".".join(str(part) for part in latest.numeric[:depth])
    return f"{current.prefix}{numeric}{current.suffix}"
