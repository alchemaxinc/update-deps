from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

USES_PATTERN = re.compile(r"(^\s*-?\s*uses:\s*)([^@\s]+)@([^\s#]+)", re.MULTILINE)


def find_uses(obj) -> list[str]:
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


def find_uses_in_file(path: Path) -> tuple[list[str], str]:
    text = path.read_text(encoding="utf-8")
    try:
        docs = list(yaml.safe_load_all(text))
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
    return sorted(root.glob(file_glob))


def apply_updates(text: str, upgrades: dict[tuple[str, str], str]) -> str:
    def replace_match(match):
        repo = match.group(2)
        tag = match.group(3)

        new_tag = upgrades.get((repo, tag))
        if new_tag:
            return f"{match.group(1)}{repo}@{new_tag}"
        return match.group(0)

    return USES_PATTERN.sub(replace_match, text)
