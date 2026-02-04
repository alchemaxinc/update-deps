from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path

from ruamel.yaml import YAML


def find_uses(obj) -> list[str]:
    """Recursively find all 'uses' values in a YAML structure."""
    found = []
    if isinstance(obj, dict):
        if isinstance(obj.get("steps"), list):
            for step in obj["steps"]:
                if isinstance(step, dict) and isinstance(step.get("uses"), str):
                    found.append(step["uses"])
        for value in obj.values():
            found.extend(find_uses(value))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(find_uses(item))
    return found


def update_uses_in_structure(obj, upgrades: dict[tuple[str, str], str]) -> bool:
    """
    Recursively update 'uses' values in a YAML structure.
    Returns True if any updates were made.
    """
    updated = False
    if isinstance(obj, dict):
        if isinstance(obj.get("steps"), list):
            for step in obj["steps"]:
                if isinstance(step, dict) and isinstance(step.get("uses"), str):
                    use = step["uses"]
                    if "@" in use:
                        repo, tag = use.split("@", 1)
                        new_tag = upgrades.get((repo, tag))
                        if new_tag:
                            step["uses"] = f"{repo}@{new_tag}"
                            updated = True
        for value in obj.values():
            if update_uses_in_structure(value, upgrades):
                updated = True
    elif isinstance(obj, list):
        for item in obj:
            if update_uses_in_structure(item, upgrades):
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
    Apply updates to a YAML workflow file using ruamel.yaml.
    This preserves formatting and comments.
    """
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    yaml.map_indent = 2
    yaml.sequence_indent = 4
    yaml.sequence_dash_offset = 2

    try:
        docs = list(yaml.load_all(text))
    except Exception:
        # If parsing fails, return original text unchanged
        return text

    # Check if any updates are needed
    any_updates = False
    for doc in docs:
        if doc is not None and update_uses_in_structure(doc, upgrades):
            any_updates = True

    if not any_updates:
        return text

    # Write back with preserved formatting
    output = StringIO()
    if len(docs) == 1:
        yaml.dump(docs[0], output)
    else:
        yaml.dump_all(docs, output)

    return output.getvalue()
