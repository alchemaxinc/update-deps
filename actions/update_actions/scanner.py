from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

from ruamel.yaml import YAML


def find_uses(obj) -> list[str]:
    """Recursively find all 'uses' values in a YAML structure."""
    found = []

    # Lists appear throughout workflow YAML (jobs, steps, matrices). Recurse
    # into every item rather than assuming only jobs.<job>.steps can contain
    # action references.
    if isinstance(obj, list):
        for item in obj:
            found.extend(find_uses(item))
        return found

    # Guard: Only process dicts from here
    if not isinstance(obj, dict):
        return found

    # Reusable workflows use jobs.<job>.uses, while actions use steps[*].uses.
    # Checking every mapping keeps both shapes covered.
    if isinstance(obj.get("uses"), str):
        found.append(obj["uses"])

    for value in obj.values():
        found.extend(find_uses(value))

    return found


def get_granularity(version: str) -> Literal["major", "minor", "patch"]:
    # A leading "v" stays attached to the first part, but only the number of
    # dot-separated parts matters here.
    parts = version.split(".")
    if len(parts) == 1:
        return "major"

    if len(parts) == 2:
        return "minor"

    return "patch"


def granularize_tag(current_tag: str, latest_tag: str) -> str:
    # Preserve the caller's pinning style: v1 stays major-only, v1.2 stays
    # minor-only, and v1.2.3 stays patch-specific.
    granularity = get_granularity(current_tag)
    if granularity == "major":
        return latest_tag.split(".")[0]

    if granularity == "minor":
        return ".".join(latest_tag.split(".")[:2])

    return ".".join(latest_tag.split(".")[:3])


def update_uses_in_structure(obj, upgrades: dict[tuple[str, str], str]) -> bool:
    """
    Recursively update 'uses' values in a YAML structure.
    Returns True if any updates were made.
    """
    if not isinstance(obj, (dict, list)):
        return False

    updated = False

    # This mirrors find_uses: lists are containers, mappings may be either
    # steps or reusable workflow jobs.
    if isinstance(obj, list):
        for item in obj:
            if update_uses_in_structure(item, upgrades):
                updated = True
        return updated

    # Split on the first "@" only so refs containing "@" later in the string
    # are left intact after the version/tag boundary.
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
        # Multi-document YAML is unusual for workflows, but load_all keeps the
        # scanner safe for action.yml and other YAML files matched by file-glob.
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
    # Do not dump the parsed YAML back out: even ruamel can alter comments,
    # indentation, or multiline run blocks. The parser is used for discovery;
    # the actual write path is intentionally line-based and narrow.
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

        # Guard: Validate prefix is either empty or a dash. That allows both
        # "uses:" and "- uses:" while skipping keys such as "reuses:" or
        # arbitrary text in shell scripts.
        prefix = stripped[:uses_idx].strip()
        if prefix and prefix != "-":
            continue

        # Keep the original indentation and list marker style so the updated
        # line has the smallest possible diff.
        indent = line[: len(line) - len(stripped)]
        rest = stripped[uses_idx + 5 :].strip()

        # Split off inline comments without treating "#" inside quotes as a
        # comment marker, so quoted action refs and comments round-trip cleanly.
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

        # Store and strip quotes for comparison, then add them back around the
        # updated value to avoid unnecessary formatting churn.
        if (
            len(value_part) >= 2
            and value_part[0] in ("'", '"')
            and value_part[-1] == value_part[0]
        ):
            quote = value_part[0]
            value_part = value_part[1:-1]

        # Match the whole uses value exactly. This prevents updating strings
        # that merely contain an action ref as a substring.
        for (repo, current_tag), new_tag in upgrades.items():
            old_value = f"{repo}@{current_tag}"
            if value_part != old_value:
                continue

            new_tag_granularized = granularize_tag(current_tag, new_tag)
            new_value = f"{repo}@{new_tag_granularized}"
            if quote:
                new_value = f"{quote}{new_value}{quote}"

            # Reconstruct line with proper formatting and the original comment.
            prefix_str = "- " if stripped.startswith("- ") else ""
            comment_str = f" {comment}" if comment else ""
            lines[i] = f"{indent}{prefix_str}uses: {new_value}{comment_str}"
            break

    return "\n".join(lines)
