#!/usr/bin/env python3
"""Build a categorized dependency update pull request body."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path


VERSION_PATTERN = re.compile(r"(\d+(?:\.\d+)*)")
CATEGORY_LABELS = {
    "major": "## Major Updates (Breaking Changes)",
    "minor": "## Minor Updates",
    "patch": "## Patch Updates",
}


def parse_version_parts(value: str) -> tuple[int, int, int] | None:
    match = VERSION_PATTERN.search(value)
    if not match:
        return None

    parts = [int(part) for part in match.group(1).split(".")[:3]]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def categorize_update(old: str, new: str) -> str:
    old_parts = parse_version_parts(old)
    new_parts = parse_version_parts(new)
    if old_parts is None or new_parts is None:
        return "patch"

    if new_parts[0] > old_parts[0]:
        return "major"
    if new_parts[0] == old_parts[0] and new_parts[1] > old_parts[1]:
        return "minor"
    return "patch"


def markdown_cell(value: str) -> str:
    return value.replace("|", "\\|")


def markdown_row(values: list[str]) -> str:
    return "| " + " | ".join(f"`{markdown_cell(value)}`" for value in values) + " |"


def read_updates(path: Path, column_count: int) -> dict[str, list[list[str]]]:
    categories = {"major": [], "minor": [], "patch": []}
    if not path.exists():
        return categories

    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip():
            continue

        fields = line.split("\t")
        if len(fields) != column_count:
            raise ValueError(
                f"{path}:{line_number}: expected {column_count} tab-separated fields, got {len(fields)}"
            )

        category = categorize_update(fields[1], fields[2])
        categories[category].append(fields)

    return categories


def read_optional_text(path: str | None) -> str:
    if not path:
        return ""
    return Path(path).read_text(encoding="utf-8").strip()


def build_body(
    title: str,
    columns: list[str],
    categories: dict[str, list[list[str]]],
    footer: str,
    preface: str,
    empty_message: str,
) -> str:
    parts = [title]

    if preface:
        parts.append(preface)

    if not any(categories.values()) and empty_message:
        parts.append(empty_message)

    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    for category in ("major", "minor", "patch"):
        rows = categories[category]
        if not rows:
            continue

        section = [CATEGORY_LABELS[category]]
        if category == "major":
            section.extend(
                [
                    "> :warning: **These updates may contain breaking changes. Please review carefully!**",
                ]
            )
        section.extend([header, separator])
        section.extend(markdown_row(row) for row in rows)
        parts.append("\n".join(section))

    parts.append("---")
    parts.append(footer)
    return "\n\n".join(parts)


def write_github_output(name: str, value: str, output_path: str) -> None:
    with open(output_path, "a", encoding="utf-8") as output:
        output.write(f"{name}<<ENDOFBODY\n{value}\nENDOFBODY\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True)
    parser.add_argument(
        "--columns", required=True, help="Comma-separated table columns"
    )
    parser.add_argument("--updates-file", required=True)
    parser.add_argument("--footer", required=True)
    parser.add_argument("--preface-file")
    parser.add_argument("--empty-message", default="")
    parser.add_argument("--output-name", default="pr_body")
    parser.add_argument("--output-file", default=os.environ.get("GITHUB_OUTPUT"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.output_file:
        raise SystemExit("GITHUB_OUTPUT is not set and --output-file was not provided")

    columns = [column.strip() for column in args.columns.split(",") if column.strip()]
    if len(columns) < 3:
        raise SystemExit("--columns must include at least name, old, and new columns")

    categories = read_updates(Path(args.updates_file), len(columns))
    body = build_body(
        title=args.title,
        columns=columns,
        categories=categories,
        footer=args.footer,
        preface=read_optional_text(args.preface_file),
        empty_message=args.empty_message,
    )
    write_github_output(args.output_name, body, args.output_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
