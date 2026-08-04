#!/usr/bin/env python3
"""Update Cargo.toml dependencies with the Cargo format-preserving upgrader."""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

BUILD_METADATA_PATTERN = re.compile(
    r'"(?P<requirement>[~^=<>!,\s]*\d+(?:\.\d+){0,2}(?:-[0-9A-Za-z.-]+)?)\+(?P<metadata>[0-9A-Za-z.-]+)"'
)


def get_direct_dependencies(manifest_path):
    """Get direct dependency requirements, including renamed dependencies."""
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

    deps = {}
    for package in metadata["packages"]:
        for dep in package.get("dependencies", []):
            identity = (
                package["id"],
                dep["name"],
                dep.get("rename"),
                dep.get("kind"),
                json.dumps(dep.get("target"), sort_keys=True),
            )
            deps[identity] = dep["req"]
    return deps


def find_build_metadata(content):
    """Map normalized requirements to unique requested build metadata."""
    metadata = {}
    for match in BUILD_METADATA_PATTERN.finditer(content):
        requirement = match.group("requirement")
        suffix = match.group("metadata")
        if requirement in metadata:
            metadata[requirement] = None
        else:
            metadata[requirement] = suffix
    return metadata


def restore_build_metadata(content, before, after, metadata):
    """Restore build metadata only when the updated requirement is unambiguous."""
    restored = {}
    for identity, old_requirement in before.items():
        new_requirement = after.get(identity)
        suffix = metadata.get(old_requirement)
        if (
            new_requirement is None
            or new_requirement == old_requirement
            or not suffix
            or "+" in new_requirement
        ):
            continue

        old_value = f'"{new_requirement}"'
        new_value = f'"{new_requirement}+{suffix}"'
        if content.count(old_value) != 1:
            print(
                f"::warning::Cannot preserve build metadata for {identity[1]} "
                f"in Cargo.toml because the requirement is ambiguous."
            )
            continue
        content = content.replace(old_value, new_value, 1)
        restored[identity] = f"{new_requirement}+{suffix}"
    return content, restored


def process_manifest(manifest_path, keep_build_metadata=False):
    """Update a manifest with Cargo and return changed requirements."""
    manifest = Path(manifest_path)
    before = get_direct_dependencies(str(manifest))
    metadata = find_build_metadata(manifest.read_text()) if keep_build_metadata else {}

    try:
        subprocess.run(
            [
                "cargo",
                "upgrade",
                "--manifest-path",
                str(manifest),
                "--incompatible",
                "--pinned",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as error:
        print(f"::warning::Failed to upgrade dependencies in {manifest_path}: {error}")
        return []

    after = get_direct_dependencies(str(manifest))
    restored = {}
    if metadata:
        content, restored = restore_build_metadata(
            manifest.read_text(), before, after, metadata
        )
        if restored:
            manifest.write_text(content)

    updates = []
    for identity, old_requirement in before.items():
        new_requirement = after.get(identity)
        new_requirement = restored.get(identity, new_requirement)
        if new_requirement is not None and new_requirement != old_requirement:
            dependency_name = identity[1]
            updates.append((dependency_name, old_requirement, new_requirement))
            print(
                f"::notice::Updated {dependency_name} from {old_requirement} "
                f"to {new_requirement} in {manifest_path}"
            )
    return updates


def main():
    parser = argparse.ArgumentParser(
        description="Update Cargo.toml dependencies to the latest crates.io versions."
    )
    parser.add_argument(
        "manifests",
        nargs="*",
        help="Paths to Cargo.toml files to update",
    )
    parser.add_argument(
        "--manifests-file",
        type=argparse.FileType("rb"),
        help="NUL-delimited file containing paths to Cargo.toml files to update",
    )
    parser.add_argument(
        "--keep-build-metadata",
        action="store_true",
        help="Preserve SemVer build metadata in upgraded version requirements",
    )
    args = parser.parse_args()

    manifests = args.manifests
    if args.manifests_file:
        manifests.extend(
            path.decode() for path in args.manifests_file.read().split(b"\0") if path
        )
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
