# Update GitHub Actions :arrows_counterclockwise:

This GitHub Action scans `.github` workflows, finds external `uses:` entries, compares them to the latest GitHub
releases, and updates them when newer versions exist.

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
        uses: alchemaxinc/update-deps/actions@v2.0.0
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

By default, the action updates all external GitHub Actions with semver-like tags. Use `excluded-actions` to skip specific
actions. Exclusions are comma-separated literal values, not regex or glob patterns. Each value can be an owner
(`actions`), repository (`actions/checkout`), or action path (`owner/repo/path/to/action`).

## :gear: Inputs

| Input               | Description                                                                                | Required           | Default                 |
| ------------------- | ------------------------------------------------------------------------------------------ | ------------------ | ----------------------- |
| `base-branch`       | Base branch for the pull request                                                           | :white_check_mark: | `main`                  |
| `token`             | GitHub token for authentication                                                            | :x:                | `${{ github.token }}`   |
| `branch-prefix`     | Prefix for the update branch                                                               | :x:                | `update-actions`        |
| `pr-title`          | Title for the pull request                                                                 | :x:                | `Update GitHub Actions` |
| `commit-message`    | Commit message for the update                                                              | :x:                | `Update GitHub Actions` |
| `file-glob`         | Glob for workflow files (relative to repo root)                                            | :x:                | `.github/**/*.yml`      |
| `check-files`       | Path/glob used to detect and include changed files in the PR                               | :x:                | `.github`               |
| `excluded-actions`  | Comma-separated literal action owners, repositories, or paths to exclude                   | :x:                | -                       |
| `app-slug`          | GitHub App slug for commit attribution                                                     | :x:                | -                       |
| `auto-merge`        | Whether automatic merge should be enabled for the PR                                       | :x:                | `false`                 |
| `skip-if-pr-exists` | Skip creating a new PR if an open PR with the same title already exists on the base branch | :x:                | `false`                 |
| `dry-run`           | Run without creating a PR                                                                  | :x:                | `false`                 |

## :warning: Prerequisites

- Workflow files must be under `.github` and match the configured `file-glob`
- The action requires write permissions to create branches and pull requests
- GitHub CLI must be available in the runner environment
