# Update GitHub Actions :arrows_counterclockwise:

This GitHub Action scans `.github` workflows, finds `uses:` entries that match configured prefixes, compares them to the
latest GitHub releases, and updates them when newer versions exist.

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
        uses: alchemaxinc/update-deps/actions@v1
        with:
          token: ${{ github.token }}
          base-branch: 'main'
          branch-prefix: 'update-actions'
          pr-title: 'Update GitHub Actions'
          commit-message: 'Update GitHub Actions'
          file-glob: '.github/**/*.yml'
          prefixes: 'actions'
```

## :computer: Local CLI

```bash
python cli.py --root /path/to/repo --file-glob '.github/**/*.yml' --prefixes 'actions'
```

## :gear: Inputs

| Input            | Description                                         | Required           | Default                 |
| ---------------- | --------------------------------------------------- | ------------------ | ----------------------- |
| `base-branch`    | Base branch for the pull request                    | :white_check_mark: | `main`                  |
| `token`          | GitHub token for authentication                     | :x:                | `${{ github.token }}`   |
| `branch-prefix`  | Prefix for the update branch                        | :x:                | `update-actions`        |
| `pr-title`       | Title for the pull request                          | :x:                | `Update GitHub Actions` |
| `commit-message` | Commit message for the update                       | :x:                | `Update GitHub Actions` |
| `file-glob`      | Glob for workflow files (relative to repo root)     | :x:                | `.github/**/*.yml`      |
| `prefixes`       | Comma-separated list of action prefixes to include  | :x:                | `actions`               |
| `auto-merge`     | Wether automatic merge should be enabled for the PR | :x:                | `false`                 |

## :warning: Prerequisites

- Workflow files must be under `.github` and match the configured `file-glob`
- The action requires write permissions to create branches and pull requests
- GitHub CLI must be available in the runner environment
