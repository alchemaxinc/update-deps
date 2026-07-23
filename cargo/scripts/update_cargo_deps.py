#!/usr/bin/env python3
"""Update Cargo.toml dependencies to their latest crates.io versions."""

import argparse
import json
import os
import re
import subprocess
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


def strip_build_metadata(version):
    """Drop SemVer build metadata (everything after a '+').

    Build metadata is ignored when Cargo resolves version requirements, so it
    is meaningless (and unidiomatic) inside a Cargo.toml constraint. Keeping it
    would also make the string comparison in find_and_replace_version report a
    phantom update on every run (e.g. "0.9.34" != "0.9.34+deprecated").
    Pre-release identifiers (after a '-') are preserved as they affect
    precedence.
    """
    return version.split("+", 1)[0]


def get_latest_stable_version(crate_name, keep_build_metadata=False):
    """Fetch the latest stable version from crates.io.

    By default SemVer build metadata (the "+..." suffix) is stripped, since it
    is ignored by Cargo when resolving requirements and only adds noise to the
    manifest. Pass keep_build_metadata=True to preserve it verbatim.
    """
    url = f"https://crates.io/api/v1/crates/{crate_name}"
    req = Request(
        url,
        headers={
            "User-Agent": "update-deps-action (github.com/alchemaxinc/update-deps)"
        },
    )
    with urlopen(req) as resp:
        data = json.loads(resp.read())
    version = data["crate"]["max_stable_version"]
    if keep_build_metadata:
        return version
    return strip_build_metadata(version)


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


def process_manifest(manifest_path, keep_build_metadata=False):
    """Process a single Cargo.toml, updating all dependencies to latest versions."""
    manifest = Path(manifest_path)
    content = manifest.read_text()

    deps = get_direct_dependencies(str(manifest_path))
    updates = []

    for dep_name in deps:
        try:
            latest = get_latest_stable_version(dep_name, keep_build_metadata)
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
    parser = argparse.ArgumentParser(
        description="Update Cargo.toml dependencies to their latest crates.io versions."
    )
    parser.add_argument(
        "manifests",
        nargs="*",
        help="Paths to Cargo.toml files to update",
    )
    parser.add_argument(
        "--keep-build-metadata",
        action="store_true",
        help=(
            "Preserve SemVer build metadata (the '+...' suffix, e.g. "
            "'0.9.34+deprecated') in written version requirements. Off by "
            "default because Cargo ignores build metadata when resolving."
        ),
    )
    args = parser.parse_args()

    manifests = args.manifests
    if not manifests:
        print("::warning::No Cargo.toml files provided")
        return

    all_updates = []
    for manifest_path in manifests:
        updates = process_manifest(manifest_path, args.keep_build_metadata)
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
