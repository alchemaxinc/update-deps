from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

from ruamel.yaml import YAML


def find_uses(obj) -> list[str]:
    """Recursively find all 'uses' values in a YAML structure."""
    found = []

    # Guard: Handle lists
    if isinstance(obj, list):
        for item in obj:
            found.extend(find_uses(item))
        return found

    # Guard: Only process dicts from here
    if not isinstance(obj, dict):
        return found

    # Process steps if present
    if isinstance(obj.get("steps"), list):
        for step in obj["steps"]:
            if not isinstance(step, dict):
                continue
            if isinstance(step.get("uses"), str):
                found.append(step["uses"])

    # Recurse into all dict values
    for value in obj.values():
        found.extend(find_uses(value))

    return found


def get_granularity(version: str) -> Literal["major", "minor", "patch"]:
    parts = version.split(".")
    if len(parts) == 1:
        return "major"

    if len(parts) == 2:
        return "minor"

    if len(parts) >= 3:
        return "patch"

    return "patch"


def update_uses_in_structure(obj, upgrades: dict[tuple[str, str], str]) -> bool:
    """
    Recursively update 'uses' values in a YAML structure.
    Returns True if any updates were made.
    """
    if not isinstance(obj, (dict, list)):
        return False

    updated = False

    if isinstance(obj, list):
        for item in obj:
            if update_uses_in_structure(item, upgrades):
                updated = True
        return updated

    # obj is a dict
    if isinstance(obj.get("steps"), list):
        for step in obj["steps"]:
            if not isinstance(step, dict) or not isinstance(step.get("uses"), str):
                continue

            use = step["uses"]
            if "@" not in use:
                continue

            repo, tag = use.split("@", 1)
            new_tag = upgrades.get((repo, tag))
            if new_tag:
                step["uses"] = f"{repo}@{new_tag}"
                updated = True

    for value in obj.values():
        if update_uses_in_structure(value, upgrades):
            updated = True

    return updated


def find_uses_in_file(path: Path) -> tuple[list[str], str]:
    """Parse a YAML file and find all 'uses' entries."""
    text = path.read_text(encoding="utf-8")
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    yaml.map_indent = 2
    yaml.sequence_indent = 4
    yaml.sequence_dash_offset = 2

    try:
        docs = list(yaml.load_all(text))
    except Exception as exc:
        print(
            f"::warning file={path}::Failed to parse YAML: {exc}",
            file=sys.stderr,
        )
        return [], text

    uses = []
    for doc in docs:
        if doc is None:
            continue
        uses.extend(find_uses(doc))
    return uses, text


def collect_workflow_files(root: Path, file_glob: str) -> list[Path]:
    """Collect all workflow files matching the glob pattern."""
    return sorted(root.glob(file_glob))


def apply_updates(text: str, upgrades: dict[tuple[str, str], str]) -> str:
    """
    Apply updates to a YAML workflow file by doing targeted text replacements.
    This preserves all original formatting and comments, only modifying the 'uses:' lines.
    """
    lines = text.split("\n")

    for i, line in enumerate(lines):
        stripped = line.lstrip()

        # Guard: Skip if no 'uses:' found
        if "uses:" not in stripped:
            continue

        # Guard: Find position of 'uses:'
        uses_idx = stripped.find("uses:")
        if uses_idx == -1:
            continue

        # Guard: Validate prefix is either empty or a dash
        prefix = stripped[:uses_idx].strip()
        if prefix and prefix != "-":
            continue

        # Extract indentation and value parts
        indent = line[: len(line) - len(stripped)]
        rest = stripped[uses_idx + 5 :].strip()

        # Parse value and comment
        comment = ""
        value_part = rest
        if "#" in rest:
            parts = rest.split("#", 1)
            value_part = parts[0].strip()
            comment = "#" + parts[1]

        # Check if this value matches any upgrade
        for (repo, current_tag), new_tag in upgrades.items():
            old_value = f"{repo}@{current_tag}"
            if value_part != old_value:
                continue

            # Granularize new_tag to match current_tag's granularity
            granularity = get_granularity(current_tag)
            if granularity == "major":
                new_tag_granuralized = new_tag.split(".")[0]
            elif granularity == "minor":
                new_tag_granuralized = ".".join(new_tag.split(".")[:2])
            else:
                new_tag_granuralized = ".".join(new_tag.split(".")[:3])

            new_value = f"{repo}@{new_tag_granuralized}"

            # Reconstruct line with proper formatting
            prefix_str = "- " if stripped.startswith("- ") else ""
            comment_str = f" {comment}" if comment else ""
            lines[i] = f"{indent}{prefix_str}uses: {new_value}{comment_str}"
            break

    return "\n".join(lines)
