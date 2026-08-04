# Update GitHub Actions :arrows_counterclockwise:

This GitHub Action scans `.github` workflow files for external `uses:` entries.
It compares each entry with the latest GitHub release. It updates entries that
have newer versions.

## :rocket: Usage

```yaml
name: Update GitHub Actions
on:
  schedule:
    - cron: '0 2 * * 1'
  workflow_dispatch:

jobs:
  update-actions:
    runs-on: ubuntu-latest
    steps:
      - name: Update GitHub Actions
        uses: alchemaxinc/update-deps/actions@v2.11.1
        with:
          token: ${{ github.token }}
          base-branch: 'main'
          branch-prefix: 'update-actions'
          pr-title: 'Update GitHub Actions'
          commit-message: 'Update GitHub Actions'
          file-glob: '.github/**/*.yml'
          excluded-actions: 'docker,owner/legacy-action'
```

## :computer: Local CLI

```bash
python cli.py --root /path/to/repo --file-glob '.github/**/*.yml' --excluded-actions 'docker,owner/legacy-action'
```

By default, the action updates external GitHub Actions with semver-like tags.
Use `excluded-actions` to skip an action. Exclusions are comma-separated
literal values, not regular expressions or glob patterns. Each value can be an
owner (`actions`), repository (`actions/checkout`), or action path
(`owner/repo/path/to/action`).

## :gear: Inputs

| Input               | Description                                                      | Required           | Default                 |
| ------------------- | ---------------------------------------------------------------- | ------------------ | ----------------------- |
| `base-branch`       | Base branch for the pull request                                 | :white_check_mark: | `main`                  |
| `token`             | GitHub token for authentication                                  | :x:                | `${{ github.token }}`   |
| `branch-prefix`     | Prefix for the update branch                                     | :x:                | `update-actions`        |
| `pr-title`          | Title of the pull request                                        | :x:                | `Update GitHub Actions` |
| `commit-message`    | Commit message for the update                                    | :x:                | `Update GitHub Actions` |
| `file-glob`         | Glob for workflow files, relative to the repository root         | :x:                | `.github/**/*.yml`      |
| `check-files`       | Path or glob for changed files in the pull request               | :x:                | `.github`               |
| `excluded-actions`  | Comma-separated action owners, repositories, or paths to exclude | :x:                | -                       |
| `app-slug`          | GitHub App slug for commit attribution                           | :x:                | -                       |
| `auto-merge`        | Enable automatic pull request merge                              | :x:                | `false`                 |
| `merge-method`      | Merge method: `merge`, `squash`, or `rebase`                     | :x:                | `merge`                 |
| `skip-if-pr-exists` | Skip a new pull request when one with the same title exists      | :x:                | `false`                 |
| `dry-run`           | Run without creating a pull request                              | :x:                | `false`                 |

## :warning: Prerequisites

- Put workflow files under `.github` and match the configured `file-glob`.
- Give the action write permissions to create branches and pull requests.
- Make sure that GitHub CLI is available on the runner.
