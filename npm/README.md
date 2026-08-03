# Update NPM Dependencies :package:

This GitHub Action updates NPM dependencies with `npm-check-updates`. It creates
a pull request with the changes.

## :rocket: Usage

```yaml
name: Update NPM Dependencies
on:
  schedule:
    - cron: '0 2 * * 1' # Run every Monday at 2 AM
  workflow_dispatch: # Allow manual trigger

jobs:
  update-dependencies:
    runs-on: ubuntu-latest
    steps:
      - name: Update NPM Dependencies
        uses: alchemaxinc/update-deps/npm@v2.10.5
        with:
          token: ${{ github.token }}
          base-branch: 'main'
          branch-prefix: 'update-npm-deps'
          pr-title: 'Update NPM Dependencies'
          commit-message: 'Update NPM dependencies'
          excluded-packages: 'package1,package2'
          relock: false
```

## :gear: Inputs

| Input | Description | Required | Default |
| --- | --- | --- | --- |
| `base-branch` | Base branch for the pull request | :white_check_mark: | `main` |
| `token` | GitHub token for authentication | :x: | `${{ github.token }}` |
| `branch-prefix` | Prefix for the update branch | :x: | `update-dependencies` |
| `pr-title` | Title of the pull request | :x: | `Update NPM Dependencies` |
| `commit-message` | Commit message for the update | :x: | `Update NPM dependencies` |
| `excluded-packages` | Comma-separated packages to exclude | :x: | - |
| `relock` | Regenerate `package-lock.json` | :x: | `false` |
| `app-slug` | GitHub App slug for commit attribution | :x: | - |
| `auto-merge` | Enable automatic pull request merge | :x: | `false` |
| `merge-method` | Merge method: `merge`, `squash`, or `rebase` | :x: | `merge` |
| `skip-if-pr-exists` | Skip a new pull request when one with the same title exists | :x: | `false` |
| `dry-run` | Run without creating a pull request | :x: | `false` |

## :warning: Prerequisites

- Add a `package.json` file to the repository.
- Specify the Node.js version in `.nvmrc`.
- Give the action write permissions to create branches and pull requests.
