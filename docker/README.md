# Update Docker Images :whale:

This GitHub Action scans `Dockerfile`s and `docker-compose` files (and, optionally,
markdown documentation), discovers Docker image references, looks up the latest
matching tag for each image via [`crane`](https://github.com/google/go-containerregistry),
and opens a pull request bumping every image to the latest **matching** tag.

The match is variant-aware: `rust:1.94-alpine` is bumped to the latest
`<x.y>-alpine`, never to `1.95-slim-bookworm` or to `latest`. Pinning depth is
preserved too — `1` stays major-only, `1.94` stays minor-only, `v1.42.1` stays
patch.

## :rocket: Usage

```yaml
name: Update Docker Images
on:
  schedule:
    - cron: '0 2 * * 1'
  workflow_dispatch:

jobs:
  update-docker:
    runs-on: ubuntu-latest
    steps:
      - name: Update Docker images
        uses: alchemaxinc/update-deps/docker@v2.3.0
        with:
          token: ${{ github.token }}
          base-branch: 'main'
          branch-prefix: 'update-docker-images'
          pr-title: 'Update Docker Images'
          commit-message: 'Update Docker images'
          markdown-glob: '**/*.md'
          excluded-images: 'public.ecr.aws/awsguru/aws-lambda-adapter'
```

## :computer: Local CLI

```bash
python cli.py \
  --root /path/to/repo \
  --dockerfile-glob '**/Dockerfile*' \
  --compose-glob '**/docker-compose*.y*ml' \
  --markdown-glob '**/*.md' \
  --excluded-images 'public.ecr.aws/awsguru/aws-lambda-adapter' \
  --dry-run
```

`crane` must be on `PATH`. The composite action installs it via
`scripts/install_crane.sh` (pinned release, SHA256-verified). For local runs
install it yourself with:

```bash
brew install crane           # macOS
# or download the pinned release used in CI:
bash scripts/install_crane.sh v0.21.5
```

## :wrench: How tag matching works

Each image reference is parsed into `(prefix, numeric, suffix)`:

| Tag                         | prefix                  | numeric      | suffix           |
| --------------------------- | ----------------------- | ------------ | ---------------- |
| `1.42.1`                    | ``                      | `(1, 42, 1)` | ``               |
| `v1.42.1`                   | `v`                     | `(1, 42, 1)` | ``               |
| `1.94-alpine`               | ``                      | `(1, 94)`    | `-alpine`        |
| `1.94-slim-bookworm`        | ``                      | `(1, 94)`    | `-slim-bookworm` |
| `1-alpine`                  | ``                      | `(1,)`       | `-alpine`        |
| `latest`, `nightly`, `edge` | _(malformed — skipped)_ |              |                  |

Only tags with the **same prefix and same suffix** are considered when picking
the latest. The selected tag is then re-rendered at the same dot-depth as the
original.

Refs containing `@sha256:` (digest pins, with or without a tag) are skipped in
v1. `FROM scratch` and stage-alias references in multi-stage Dockerfiles
(`FROM builder`) are also skipped.

## :gear: Inputs

| Input               | Description                                                                                | Required           | Default                   |
| ------------------- | ------------------------------------------------------------------------------------------ | ------------------ | ------------------------- |
| `base-branch`       | Base branch for the pull request                                                           | :white_check_mark: | `main`                    |
| `token`             | GitHub token for authentication                                                            | :x:                | `${{ github.token }}`     |
| `branch-prefix`     | Prefix for the update branch                                                               | :x:                | `update-docker-images`    |
| `pr-title`          | Title for the pull request                                                                 | :x:                | `Update Docker Images`    |
| `commit-message`    | Commit message for the update                                                              | :x:                | `Update Docker images`    |
| `dockerfile-glob`   | Glob for Dockerfiles to scan (relative to repo root)                                       | :x:                | `**/Dockerfile*`          |
| `compose-glob`      | Glob for docker-compose files                                                              | :x:                | `**/docker-compose*.y*ml` |
| `markdown-glob`     | Optional glob for markdown files. Empty disables markdown updates.                         | :x:                | -                         |
| `excluded-images`   | Comma-separated literal registry, registry/repo, or registry/repo:tag values to exclude    | :x:                | -                         |
| `crane-version`     | Pinned `google/go-containerregistry` release used to install crane                         | :x:                | `v0.21.5`                 |
| `check-files`       | Path/glob used to detect and include changed files in the PR                               | :x:                | `.`                       |
| `app-slug`          | GitHub App slug for commit attribution                                                     | :x:                | -                         |
| `auto-merge`        | Whether automatic merge should be enabled for the PR                                       | :x:                | `false`                   |
| `skip-if-pr-exists` | Skip creating a new PR if an open PR with the same title already exists on the base branch | :x:                | `false`                   |
| `dry-run`           | Run without creating a PR                                                                  | :x:                | `false`                   |

## :warning: Prerequisites

- The action requires write permissions to create branches and pull requests
- `crane` is installed by the action itself; no setup-crane action is required
- v1 only targets public registries reachable anonymously (Docker Hub,
  `public.ecr.aws`, `ghcr.io` public images, etc.). Use `excluded-images` to
  skip private repos.
