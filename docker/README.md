# Update Docker Images :whale:

This GitHub Action scans `Dockerfile` and `docker-compose` files. It can also
scan Markdown files. It finds Docker image references and gets the latest
matching tag with [`crane`](https://github.com/google/go-containerregistry).
It opens a pull request with the updated tags.

Tag matching preserves variants. `rust:1.94-alpine` updates to the latest
`<x.y>-alpine`, not `1.95-slim-bookworm` or `latest`. It also preserves pin
depth. `1` stays major-only. `1.94` stays minor-only. `v1.42.1` stays patch-level.

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
        uses: alchemaxinc/update-deps/docker@v2.11.1
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

`crane` must be on `PATH`. The composite action installs its pinned release
with `scripts/install_crane.sh`. For a local run, install it:

```bash
brew install crane           # macOS
# Or install the pinned CI release:
bash scripts/install_crane.sh v0.21.5
```

## :wrench: How tag matching works

The action parses each image reference into `(prefix, numeric, suffix)`:

| Tag                         | prefix                  | numeric      | suffix           |
| --------------------------- | ----------------------- | ------------ | ---------------- |
| `1.42.1`                    | ``                      | `(1, 42, 1)` | ``               |
| `v1.42.1`                   | `v`                     | `(1, 42, 1)` | ``               |
| `1.94-alpine`               | ``                      | `(1, 94)`    | `-alpine`        |
| `1.94-slim-bookworm`        | ``                      | `(1, 94)`    | `-slim-bookworm` |
| `1-alpine`                  | ``                      | `(1,)`       | `-alpine`        |
| `latest`, `nightly`, `edge` | _(malformed — skipped)_ |              |                  |

The action considers only tags with the same prefix and suffix. It writes the
selected tag at the original dot depth.

Version 1 skips references with `@sha256:` digest pins. It also skips
`FROM scratch` and stage aliases in multi-stage Dockerfiles, such as
`FROM builder`.

## :gear: Inputs

| Input               | Description                                                        | Required           | Default                   |
| ------------------- | ------------------------------------------------------------------ | ------------------ | ------------------------- |
| `base-branch`       | Base branch for the pull request                                   | :white_check_mark: | `main`                    |
| `token`             | GitHub token for authentication                                    | :x:                | `${{ github.token }}`     |
| `branch-prefix`     | Prefix for the update branch                                       | :x:                | `update-docker-images`    |
| `pr-title`          | Title of the pull request                                          | :x:                | `Update Docker Images`    |
| `commit-message`    | Commit message for the update                                      | :x:                | `Update Docker images`    |
| `dockerfile-glob`   | Glob for Dockerfiles, relative to the repository root              | :x:                | `**/Dockerfile*`          |
| `compose-glob`      | Glob for docker-compose files                                      | :x:                | `**/docker-compose*.y*ml` |
| `markdown-glob`     | Glob for Markdown files. An empty value disables Markdown updates. | :x:                | -                         |
| `excluded-images`   | Comma-separated registry, repository, or tag values to exclude     | :x:                | -                         |
| `crane-version`     | Pinned `google/go-containerregistry` release for crane             | :x:                | `v0.21.5`                 |
| `check-files`       | Path or glob for changed files in the pull request                 | :x:                | `.`                       |
| `app-slug`          | GitHub App slug for commit attribution                             | :x:                | -                         |
| `auto-merge`        | Enable automatic pull request merge                                | :x:                | `false`                   |
| `merge-method`      | Merge method: `merge`, `squash`, or `rebase`                       | :x:                | `merge`                   |
| `skip-if-pr-exists` | Skip a new pull request when one with the same title exists        | :x:                | `false`                   |
| `dry-run`           | Run without creating a pull request                                | :x:                | `false`                   |

## :warning: Prerequisites

- Give the action write permissions to create branches and pull requests.
- The action installs `crane`. You do not need a setup-crane action.
- Version 1 targets public registries that allow anonymous access, including
  Docker Hub, `public.ecr.aws`, and public `ghcr.io` images. Use
  `excluded-images` to skip private repositories.
