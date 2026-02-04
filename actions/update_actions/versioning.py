from __future__ import annotations

import re

import semver

SEMVER_PATTERN = re.compile(r"^v?(\d+(?:\.\d+)*)$")


def parse_version(tag: str) -> semver.VersionInfo | None:
    match = SEMVER_PATTERN.match(tag)
    if not match:
        return None
    parts = [int(part) for part in match.group(1).split(".")]
    if len(parts) > 3:
        return None
    while len(parts) < 3:
        parts.append(0)
    return semver.VersionInfo(parts[0], parts[1], parts[2])


def select_latest_tag(tags: list[str]) -> str | None:
    best_tag = None
    best_version = None
    for tag in tags:
        version = parse_version(tag)
        if version is None:
            continue
        if best_version is None or version > best_version:
            best_version = version
            best_tag = tag
    return best_tag
