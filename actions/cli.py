#!/usr/bin/env python3
import argparse
import os
from pathlib import Path

from update_actions.updater import update_actions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update GitHub Action uses entries to latest releases."
    )
    parser.add_argument(
        "--root",
        default=os.environ.get("GITHUB_WORKSPACE", "."),
        help="Repository root to scan (default: GITHUB_WORKSPACE or .)",
    )
    parser.add_argument(
        "--file-glob",
        default=".github/**/*.yml",
        help="Glob (relative to root) for workflow files.",
    )
    parser.add_argument(
        "--excluded-actions",
        default="",
        help=(
            "Comma-separated list of action owners, repositories, or paths to "
            "exclude. Values are matched literally, not as regex."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned updates without modifying files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    excluded_actions = [
        p.strip() for p in args.excluded_actions.split(",") if p.strip()
    ]
    return update_actions(
        root=root,
        file_glob=args.file_glob,
        excluded_actions=excluded_actions,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())
