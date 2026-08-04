from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path
from typing import Callable

from update_docker.crane import crane_list
from update_docker.scanner import (
    ImageRef,
    replace_compose_tag,
    replace_dockerfile_tag,
    replace_markdown_occurrences,
    scan_compose_files,
    scan_dockerfiles,
    collect_files,
)
from update_docker.versioning import (
    granularize_tag,
    parse_image_tag,
    select_latest_matching,
)


def _is_excluded(ref: ImageRef, excluded: set[str]) -> bool:
    if not excluded:
        return False
    full = f"{ref.registry}/{ref.repo}:{ref.tag}"
    candidates = {ref.registry, f"{ref.registry}/{ref.repo}", full}
    if ref.registry == "docker.io":
        # Allow exclusions without the implicit registry or library prefix.
        repo_short = (
            ref.repo[len("library/") :] if ref.repo.startswith("library/") else ref.repo
        )
        candidates.add(repo_short)
        candidates.add(f"{repo_short}:{ref.tag}")
    return bool(candidates & excluded)


def update_docker(
    root: Path,
    dockerfile_glob: str,
    compose_glob: str,
    markdown_glob: str,
    excluded_images: list[str],
    dry_run: bool,
    tag_lister: Callable[[str], list[str]] = crane_list,
) -> int:
    excluded = {item for item in excluded_images if item}

    refs: list[ImageRef] = []
    if dockerfile_glob:
        refs.extend(scan_dockerfiles(root, dockerfile_glob))
    if compose_glob:
        refs.extend(scan_compose_files(root, compose_glob))

    refs = [ref for ref in refs if not _is_excluded(ref, excluded)]

    if not refs:
        print("No Docker image references found.")
        return 0

    # Cache crane lookups. Each (registry, repository) pair uses the registry
    # only once per run.
    tag_cache: dict[str, list[str]] = {}
    new_tag_for: dict[tuple[str, str, str], str] = {}
    update_records: list[tuple[ImageRef, str]] = []

    seen_decision: dict[tuple[str, str, str], str | None] = {}

    for ref in refs:
        key = (ref.registry, ref.repo, ref.tag)
        if key in seen_decision:
            new_tag = seen_decision[key]
        else:
            current = parse_image_tag(ref.tag)
            if current is None:
                print(f"::notice::Skip {ref.display}. The tag format is not supported.")
                seen_decision[key] = None
                continue

            if ref.crane_repo not in tag_cache:
                tag_cache[ref.crane_repo] = tag_lister(ref.crane_repo)
            tags = tag_cache[ref.crane_repo]

            latest = select_latest_matching(tags, current)
            if latest is None:
                print(f"::notice::No newer tags found for {ref.display}")
                seen_decision[key] = None
                continue

            new_tag = granularize_tag(ref.tag, latest)
            if new_tag == ref.tag:
                seen_decision[key] = None
                continue

            seen_decision[key] = new_tag
            new_tag_for[key] = new_tag
            print(f"::notice::Updated {ref.display} -> {new_tag}")

        if new_tag is None:
            continue

        update_records.append((ref, new_tag))

    # Group writes by file. Read and write each file at most once when multiple
    # references have the same path.
    by_file: dict[Path, list[tuple[ImageRef, str]]] = defaultdict(list)
    for ref, new_tag in update_records:
        by_file[ref.source_path].append((ref, new_tag))

    changed_files: list[Path] = []
    for path, items in by_file.items():
        original = path.read_text(encoding="utf-8")
        updated = original
        # Replace from the file end. Dockerfile and compose line numbers stay
        # stable across changes.
        for ref, new_tag in sorted(
            items, key=lambda item: item[0].line_number, reverse=True
        ):
            if ref.source_kind == "dockerfile":
                updated = replace_dockerfile_tag(updated, ref, new_tag)
            elif ref.source_kind == "compose":
                updated = replace_compose_tag(updated, ref, new_tag)
        if updated != original:
            changed_files.append(path)
            if dry_run:
                print(f"Planned update in {path}")
            else:
                path.write_text(updated, encoding="utf-8")
                print(f"Updated {path}")

    # Markdown updates require a glob. Markdown receives each unique
    # (reference, new tag) pair so documentation-only updates are kept.
    if markdown_glob:
        unique_updates: dict[tuple[str, str, str], tuple[ImageRef, str]] = {}
        for ref, new_tag in update_records:
            unique_updates.setdefault((ref.registry, ref.repo, ref.tag), (ref, new_tag))

        markdown_files = collect_files(root, markdown_glob)
        for path in markdown_files:
            original = path.read_text(encoding="utf-8")
            updated = original
            md_records: list[tuple[ImageRef, str]] = []
            for (registry, repo, tag), (ref, new_tag) in unique_updates.items():
                before = updated
                updated = replace_markdown_occurrences(updated, ref, new_tag)
                if updated != before:
                    md_record_ref = ImageRef(
                        source_path=path,
                        line_number=0,
                        source_kind="markdown",
                        registry=registry,
                        repo=repo,
                        tag=tag,
                    )
                    md_records.append((md_record_ref, new_tag))
            if updated != original:
                changed_files.append(path)
                update_records.extend(md_records)
                if dry_run:
                    print(f"Planned markdown update in {path}")
                else:
                    path.write_text(updated, encoding="utf-8")
                    print(f"Updated {path}")

    if dry_run:
        print(f"Dry run complete. Files with updates: {len(changed_files)}")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as output:
            output.write("docker_updates<<ENDOFUPDATES\n")
            for ref, new_tag in update_records:
                rel = ref.source_path
                try:
                    rel = ref.source_path.relative_to(root)
                except ValueError:
                    pass
                output.write(f"{ref.display}\t{ref.tag}\t{new_tag}\t{rel}\n")
            output.write("ENDOFUPDATES\n")

    return 0
