from __future__ import annotations

from pathlib import Path

from update_actions.github_api import fetch_release_tags
from update_actions.scanner import (
    apply_updates,
    collect_workflow_files,
    find_uses_in_file,
)
from update_actions.versioning import parse_version, select_latest_tag


def update_actions(
    root: Path,
    file_glob: str,
    excluded_actions: list[str],
    dry_run: bool,
) -> int:
    workflow_files = collect_workflow_files(root, file_glob)
    if not workflow_files:
        print("No workflow files found.")
        return 0

    uses_set = set()
    file_cache = {}
    for path in workflow_files:
        uses, text = find_uses_in_file(path)
        file_cache[path] = text
        uses_set.update(uses)

    excluded_actions_set = set(excluded_actions)
    filtered_uses: list[tuple[str, str, str]] = []
    for use in sorted(uses_set):
        if "@" not in use:
            continue
        action_ref, current_tag = use.split("@", 1)
        action_parts = action_ref.split("/")
        if len(action_parts) < 2 or action_ref.startswith(("./", "../", "docker://")):
            continue

        release_repo = "/".join(action_parts[:2])
        action_owner = action_parts[0]
        if excluded_actions_set.intersection({action_owner, release_repo, action_ref}):
            continue

        filtered_uses.append((action_ref, release_repo, current_tag))

    if not filtered_uses:
        print("No matching action uses entries found.")
        return 0

    upgrades: dict[tuple[str, str], str] = {}
    release_tags_cache: dict[str, list[str]] = {}
    for action_ref, release_repo, current_tag in filtered_uses:
        current_version = parse_version(current_tag)
        if current_version is None:
            print(f"Skipping {action_ref}@{current_tag} (unsupported tag format)")
            continue

        if release_repo not in release_tags_cache:
            release_tags_cache[release_repo] = fetch_release_tags(release_repo)
        tags = release_tags_cache[release_repo]
        latest_tag = select_latest_tag(tags)
        if latest_tag is None:
            print(f"Skipping {action_ref}@{current_tag} (no valid release tags found)")
            continue

        latest_version = parse_version(latest_tag)
        if latest_version and latest_version > current_version:
            upgrade_key = (action_ref, current_tag)
            if upgrade_key not in upgrades:
                upgrades[upgrade_key] = latest_tag
                print(f"::notice::Updated {action_ref} from {current_tag} to {latest_tag}")

    if not upgrades:
        print("All matching actions are up to date.")
        return 0

    changes = 0
    for path, text in file_cache.items():
        updated = apply_updates(text, upgrades)

        if updated != text:
            changes += 1

            if dry_run:
                print(f"Planned update in {path}")
                continue

            path.write_text(updated, encoding="utf-8")
            print(f"Updated {path}")

    if dry_run:
        print(f"Dry run complete. Files with updates: {changes}")

    return 0
