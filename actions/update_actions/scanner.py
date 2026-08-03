from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

from ruamel.yaml import YAML


def find_uses(obj) -> list[str]:
    """Find all 'uses' values in a YAML structure."""
    found = []

    # Lists can occur in jobs, steps, and matrices. Search each item because
    # action references are not limited to jobs.<job>.steps.
    if isinstance(obj, list):
        for item in obj:
            found.extend(find_uses(item))
        return found

    # Process only dictionaries from this point.
    if not isinstance(obj, dict):
        return found

    # Reusable workflows use jobs.<job>.uses. Actions use steps[*].uses.
    # Search each mapping to support both forms.
    if isinstance(obj.get("uses"), str):
        found.append(obj["uses"])

    for value in obj.values():
        found.extend(find_uses(value))

    return found


def get_granularity(version: str) -> Literal["major", "minor", "patch"]:
    # Keep a leading "v" with the first part. Only the number of dot-separated
    # parts matters here.
    parts = version.split(".")
    if len(parts) == 1:
        return "major"

    if len(parts) == 2:
        return "minor"

    return "patch"


def granularize_tag(current_tag: str, latest_tag: str) -> str:
    # Keep the caller pinning style. v1 stays major-only. v1.2 stays minor-only.
    # v1.2.3 stays patch-specific.
    granularity = get_granularity(current_tag)
    if granularity == "major":
        return latest_tag.split(".")[0]

    if granularity == "minor":
        return ".".join(latest_tag.split(".")[:2])

    return ".".join(latest_tag.split(".")[:3])


def update_uses_in_structure(obj, upgrades: dict[tuple[str, str], str]) -> bool:
    """
    Update 'uses' values in a YAML structure.
    Return True when an update occurs.
    """
    if not isinstance(obj, (dict, list)):
        return False

    updated = False

    # Match find_uses behavior. Lists are containers. Mappings can be steps or
    # reusable workflow jobs.
    if isinstance(obj, list):
        for item in obj:
            if update_uses_in_structure(item, upgrades):
                updated = True
        return updated

    # Split only at the first "@". Keep references that contain a later "@"
    # unchanged after the version or tag boundary.
    use = obj.get("uses")
    if isinstance(use, str) and "@" in use:
        repo, tag = use.split("@", 1)
        new_tag = upgrades.get((repo, tag))
        if new_tag:
            obj["uses"] = f"{repo}@{new_tag}"
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
        # Workflow files rarely use multiple documents. load_all supports them
        # and other YAML files that match file-glob.
        uses.extend(find_uses(doc))
    return uses, text


def collect_workflow_files(root: Path, file_glob: str) -> list[Path]:
    """Collect workflow files that match the glob pattern."""
    return sorted(root.glob(file_glob))


def find_uses_line_numbers(obj) -> set[int]:
    """Return zero-based source lines for YAML mapping keys named ``uses``."""
    lines = set()
    if isinstance(obj, list):
        for item in obj:
            lines.update(find_uses_line_numbers(item))
        return lines

    if not isinstance(obj, dict):
        return lines

    if isinstance(obj.get("uses"), str):
        key_position = obj.lc.key("uses")
        if key_position is not None:
            lines.add(key_position[0])

    for value in obj.values():
        lines.update(find_uses_line_numbers(value))
    return lines


def apply_updates(text: str, upgrades: dict[tuple[str, str], str]) -> str:
    """
    Apply targeted text replacements to a YAML workflow file.
    Preserve formatting and comments. Modify only 'uses:' lines.
    """
    # Do not write the parsed YAML. ruamel can change comments, indentation, and
    # multiline run blocks. Source locations allow a line-level rewrite without
    # changing scalar block content.
    yaml = YAML()
    try:
        allowed_lines = set()
        for doc in yaml.load_all(text):
            if doc is not None:
                allowed_lines.update(find_uses_line_numbers(doc))
    except Exception:
        return text

    lines = text.split("\n")

    for i, line in enumerate(lines):
        if i not in allowed_lines:
            continue

        stripped = line.lstrip()

        # Skip lines without 'uses:'.
        if "uses:" not in stripped:
            continue

        # Find the 'uses:' position.
        uses_idx = stripped.find("uses:")
        if uses_idx == -1:
            continue

        # The prefix must be empty or a dash. This permits "uses:" and
        # "- uses:". It skips "reuses:" keys and shell script text.
        prefix = stripped[:uses_idx].strip()
        if prefix and prefix != "-":
            continue

        # Keep the original indentation and list marker style. This produces
        # the smallest possible change.
        indent = line[: len(line) - len(stripped)]
        rest = stripped[uses_idx + 5 :].strip()

        # Separate inline comments. Do not treat "#" in quotes as a comment
        # marker. This preserves quoted action references and comments.
        comment = ""
        value_part = rest
        quote = ""
        in_quote = None
        for char_index, char in enumerate(rest):
            if char in ("'", '"'):
                if in_quote is None:
                    in_quote = char
                elif in_quote == char:
                    in_quote = None
            elif char == "#" and in_quote is None:
                value_part = rest[:char_index].strip()
                comment = rest[char_index:]
                break

        # Store and remove quotes for comparison. Add them to the updated value
        # to preserve file formatting.
        if (
            len(value_part) >= 2
            and value_part[0] in ("'", '"')
            and value_part[-1] == value_part[0]
        ):
            quote = value_part[0]
            value_part = value_part[1:-1]

        # Match the complete uses value. This prevents updates to strings that
        # contain an action reference only as a substring.
        for (repo, current_tag), new_tag in upgrades.items():
            old_value = f"{repo}@{current_tag}"
            if value_part != old_value:
                continue

            new_tag_granularized = granularize_tag(current_tag, new_tag)
            new_value = f"{repo}@{new_tag_granularized}"
            if quote:
                new_value = f"{quote}{new_value}{quote}"

            # Rebuild the line with the original format and comment.
            prefix_str = "- " if stripped.startswith("- ") else ""
            comment_str = f" {comment}" if comment else ""
            lines[i] = f"{indent}{prefix_str}uses: {new_value}{comment_str}"
            break

    return "\n".join(lines)
