import subprocess
import sys


def fetch_release_tags(repo: str) -> list[str]:
    cmd = [
        "gh",
        "api",
        f"/repos/{repo}/releases",
        "--paginate",
        "--jq",
        ".[] | [.tag_name, .prerelease] | @tsv",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(
            f"::warning::Failed to fetch releases for {repo}: {result.stderr.strip()}",
            file=sys.stderr,
        )
        return []
    tags = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        tag, prerelease = line.split("\t", 1)
        if prerelease.strip().lower() == "true":
            continue
        tags.append(tag.strip())
    return tags
