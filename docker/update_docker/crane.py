from __future__ import annotations

import subprocess
import sys
import time


def crane_list(repo: str) -> list[str]:
    """Return all tags for a fully-qualified repo via ``crane ls``.

    On non-zero exit (network error, rate limit, missing repo) we log a
    GitHub-Actions warning annotation and return an empty list, matching the
    pattern used by ``actions/update_actions/github_api.py::fetch_release_tags``.
    Crane must be on ``PATH``; the composite action installs it via
    ``scripts/install_crane.sh``.
    """
    cmd = ["crane", "ls", repo]
    for attempt in range(3):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=30
            )
        except FileNotFoundError:
            print(
                "::warning::crane binary not found on PATH; skipping tag lookup",
                file=sys.stderr,
            )
            return []
        except subprocess.TimeoutExpired:
            result = None

        if result is not None and result.returncode == 0:
            break
        if attempt < 2:
            time.sleep(2**attempt)
    else:
        detail = result.stderr.strip() if result is not None else "request timed out"
        print(
            f"::warning::Failed to list tags for {repo}: {detail}",
            file=sys.stderr,
        )
        return []

    tags: list[str] = []
    for line in result.stdout.splitlines():
        tag = line.strip()
        if tag:
            tags.append(tag)
    return tags
