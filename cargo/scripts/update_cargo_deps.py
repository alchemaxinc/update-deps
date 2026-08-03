#!/usr/bin/env python3
"""Update Cargo.toml dependencies with Cargo's formatting-preserving upgrader."""

import argparse
import json
import os
import subprocess
from pathlib import Path


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


def process_manifest(manifest_path):
    """Upgrade a manifest with Cargo and return its changed requirements."""
    manifest = Path(manifest_path)
    before = get_direct_dependencies(str(manifest))

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

    after = get_direct_dependencies(str(manifest))
    updates = []
    for identity, old_requirement in before.items():
        new_requirement = after.get(identity)
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
        description="Update Cargo.toml dependencies to their latest crates.io versions."
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
