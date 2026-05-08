from __future__ import annotations

from dataclasses import dataclass

import semver


_SUFFIX_ALLOWED = set(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-"
)


@dataclass(frozen=True)
class TagVariant:
    prefix: str  # "" or "v"
    numeric: tuple[int, ...]
    suffix: str  # "" or e.g. "-alpine"

    @property
    def version(self) -> semver.Version:
        parts = list(self.numeric) + [0] * (3 - len(self.numeric))
        return semver.Version(parts[0], parts[1], parts[2])


def parse_image_tag(tag: str) -> TagVariant | None:
    """Parse an image tag into prefix/numeric/suffix, or None if not numeric.

    Tags such as ``latest``, ``nightly``, or ``edge`` return ``None`` so the
    caller can skip them. The accepted shape is::

        [v]<num>(.<num>){0,2}[-<alnum>[<alnum.->...]]

    e.g. ``1.94``, ``v1.42.1``, ``1.94-alpine``, ``1.94-slim-bookworm``.
    """
    if not tag:
        return None

    # A leading "v" is only a prefix when it precedes a digit. Otherwise it's
    # part of a non-numeric tag like "vault" and the whole tag is rejected.
    if tag[0] == "v" and len(tag) > 1 and tag[1].isdigit():
        prefix, rest = "v", tag[1:]
    else:
        prefix, rest = "", tag

    # Split numeric core from optional "-suffix" on the first dash.
    numeric_part, sep, suffix_body = rest.partition("-")
    suffix = f"-{suffix_body}" if sep else ""

    parts = numeric_part.split(".")
    if not 1 <= len(parts) <= 3:
        return None

    if not all(part.isdigit() for part in parts):
        return None

    # Suffix body must start with an alphanumeric and only contain
    # alphanumerics, "." or "-" (matches Docker tag conventions like
    # "-alpine3.20" or "-slim-bookworm").
    if suffix:
        if not suffix_body or not suffix_body[0].isalnum():
            return None

        if any(ch not in _SUFFIX_ALLOWED for ch in suffix_body):
            return None

    return TagVariant(
        prefix=prefix,
        numeric=tuple(int(part) for part in parts),
        suffix=suffix,
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
