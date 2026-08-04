#!/usr/bin/env python3
import argparse
import os
from pathlib import Path

from update_docker.updater import update_docker


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update Docker image references to the latest matching tag."
    )
    parser.add_argument(
        "--root",
        default=os.environ.get("GITHUB_WORKSPACE", "."),
        help="Repository root to scan. The default is GITHUB_WORKSPACE or .",
    )
    parser.add_argument(
        "--dockerfile-glob",
        default="**/Dockerfile*",
        help="Glob for Dockerfiles, relative to the root.",
    )
    parser.add_argument(
        "--compose-glob",
        default="**/docker-compose*.y*ml",
        help="Glob for docker-compose files, relative to the root.",
    )
    parser.add_argument(
        "--markdown-glob",
        default="",
        help=(
            "Optional glob for Markdown files with discovered image references. "
            "An empty value disables Markdown scanning."
        ),
    )
    parser.add_argument(
        "--excluded-images",
        default="",
        help=(
            "Comma-separated registries, repositories, or complete image "
            "references to exclude. Values match literally."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned updates. Do not modify files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    excluded = [
        item.strip() for item in args.excluded_images.split(",") if item.strip()
    ]
    return update_docker(
        root=root,
        dockerfile_glob=args.dockerfile_glob,
        compose_glob=args.compose_glob,
        markdown_glob=args.markdown_glob,
        excluded_images=excluded,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())
