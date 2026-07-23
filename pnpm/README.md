# Update pnpm Dependencies :package:

This GitHub Action automatically updates pnpm dependencies using `npm-check-updates` and creates a pull request with the
changes.

## :rocket: Usage

```yaml
name: Update pnpm Dependencies
on:
  schedule:
    - cron: '0 2 * * 1' # Run every Monday at 2 AM
  workflow_dispatch: # Allow manual trigger

jobs:
  update-dependencies:
    runs-on: ubuntu-latest
    steps:
      - name: Update pnpm Dependencies
        uses: alchemaxinc/update-deps/pnpm@v2.6.0
        with:
          token: ${{ github.token }}
          base-branch: 'main'
          branch-prefix: 'update-pnpm-deps'
          pr-title: 'Update pnpm Dependencies'
          commit-message: 'Update pnpm dependencies'
          excluded-packages: 'package1,package2'
          relock: false
```

## :gear: Inputs

| Input               | Description                                                                                | Required           | Default                    |
| ------------------- | ------------------------------------------------------------------------------------------ | ------------------ | -------------------------- |
| `base-branch`       | Base branch for the pull request                                                           | :white_check_mark: | `main`                     |
| `token`             | GitHub token for authentication                                                            | :x:                | `${{ github.token }}`      |
| `branch-prefix`     | Prefix for the update branch                                                               | :x:                | `update-dependencies`      |
| `pr-title`          | Title for the pull request                                                                 | :x:                | `Update pnpm Dependencies` |
| `commit-message`    | Commit message for the update                                                              | :x:                | `Update pnpm dependencies` |
| `excluded-packages` | Comma-separated list of packages to exclude                                                | :x:                | -                          |
| `relock`            | Whether `pnpm-lock.yaml` should be regenerated                                             | :x:                | `false`                    |
| `app-slug`          | GitHub App slug for commit attribution                                                     | :x:                | -                          |
| `auto-merge`        | Whether automatic merge should be enabled for the PR                                       | :x:                | `false`                    |
| `merge-method`      | Merge method when auto-merging (`merge`, `squash`, `rebase`)                               | :x:                | `merge`                    |
| `skip-if-pr-exists` | Skip creating a new PR if an open PR with the same title already exists on the base branch | :x:                | `false`                    |
| `dry-run`           | Run without creating a PR                                                                  | :x:                | `false`                    |

## :warning: Prerequisites

- Your repository must have a `package.json` file and a `pnpm-lock.yaml` lockfile
- Node.js version should be specified in `.nvmrc` file
- The pnpm version can be pinned via the `packageManager` field in `package.json` (read by `pnpm/action-setup`)
- The action requires write permissions to create branches and pull requests
