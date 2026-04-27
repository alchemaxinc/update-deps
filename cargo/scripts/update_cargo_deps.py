#!/usr/bin/env python3
"""Update Cargo.toml dependencies to their latest crates.io versions."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen


def get_direct_dependencies(manifest_path):
    """Get direct dependency names using cargo metadata."""
    result = subprocess.run(
        [
            "cargo",
            "metadata",
            "--no-deps",
            "--format-version",
            "1",
            "--manifest-path",
            manifest_path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    metadata = json.loads(result.stdout)

    deps = set()
    for package in metadata["packages"]:
        for dep in package.get("dependencies", []):
            deps.add(dep["name"])
    return sorted(deps)


def get_latest_stable_version(crate_name):
    """Fetch the latest stable version from crates.io."""
    url = f"https://crates.io/api/v1/crates/{crate_name}"
    req = Request(
        url,
        headers={
            "User-Agent": "update-deps-action (github.com/alchemaxinc/update-deps)"
        },
    )
    with urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["crate"]["max_stable_version"]


def find_and_replace_version(content, crate_name, new_version):
    """Update a crate's version in Cargo.toml content.

    Handles both dependency formats:
      name = "version"
      name = { version = "version", ... }

    Matches both hyphens and underscores in crate names, and updates all
    occurrences (e.g. same crate in [dependencies] and [dev-dependencies]).

    Preserves constraint prefixes (^, ~, =, etc.).
    Returns (new_content, old_version) or (content, None) if no change.
    """
    name_pattern = re.escape(crate_name.replace("-", "_")).replace("_", "[-_]")
    pattern = rf'({name_pattern}\s*=\s*(?:\{{[^}}]*version\s*=\s*"|"))([^"]+)'

    old_version = None

    def replacer(match):
        nonlocal old_version
        prefix = match.group(1)
        old_ver = match.group(2)

        constraint_match = re.match(r"^([~^=><!\s]*)([\d][\d.]*)", old_ver)
        if not constraint_match:
            return match.group(0)

        constraint = constraint_match.group(1)
        current = constraint_match.group(2)

        if current == new_version:
            return match.group(0)

        old_version = old_ver
        return f"{prefix}{constraint}{new_version}"

    new_content = re.sub(pattern, replacer, content)
    return new_content, old_version


def process_manifest(manifest_path):
    """Process a single Cargo.toml, updating all dependencies to latest versions."""
    manifest = Path(manifest_path)
    content = manifest.read_text()

    deps = get_direct_dependencies(str(manifest_path))
    updates = []

    for dep_name in deps:
        try:
            latest = get_latest_stable_version(dep_name)
        except Exception as e:
            print(f"::warning::Failed to fetch latest version for {dep_name}: {e}")
            continue

        new_content, old_version = find_and_replace_version(content, dep_name, latest)
        if old_version is not None:
            updates.append((dep_name, old_version, latest))
            content = new_content
            print(
                f"::notice::Updated {dep_name} from {old_version} to {latest} in {manifest_path}"
            )

    if updates:
        manifest.write_text(content)

    return updates


def main():
    manifests = sys.argv[1:]
    if not manifests:
        print("::warning::No Cargo.toml files provided")
        return

    all_updates = []
    for manifest_path in manifests:
        updates = process_manifest(manifest_path)
        for name, old, new in updates:
            all_updates.append(
                {
                    "manifest": manifest_path,
                    "name": name,
                    "old": old,
                    "new": new,
                }
            )

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output and all_updates:
        records = ""
        for u in all_updates:
            records += f"{u['name']}\t{u['old']}\t{u['new']}\t{u['manifest']}\n"

        with open(github_output, "a") as f:
            f.write(f"dep_updates<<ENDOFUPDATES\n{records}ENDOFUPDATES\n")

    if not all_updates:
        print("::notice::All Cargo dependencies are up to date")


if __name__ == "__main__":
    main()
