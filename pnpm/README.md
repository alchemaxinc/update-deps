# Update pnpm Dependencies :package:

This GitHub Action updates pnpm dependencies with `pnpm update --latest`. It
creates a pull request with the changes.

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
        uses: alchemaxinc/update-deps/pnpm@v2.11.1
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

| Input               | Description                                                 | Required           | Default                    |
| ------------------- | ----------------------------------------------------------- | ------------------ | -------------------------- |
| `base-branch`       | Base branch for the pull request                            | :white_check_mark: | `main`                     |
| `token`             | GitHub token for authentication                             | :x:                | `${{ github.token }}`      |
| `branch-prefix`     | Prefix for the update branch                                | :x:                | `update-dependencies`      |
| `pr-title`          | Title of the pull request                                   | :x:                | `Update pnpm Dependencies` |
| `commit-message`    | Commit message for the update                               | :x:                | `Update pnpm dependencies` |
| `excluded-packages` | Comma-separated packages to exclude                         | :x:                | -                          |
| `relock`            | Regenerate `pnpm-lock.yaml`                                 | :x:                | `false`                    |
| `app-slug`          | GitHub App slug for commit attribution                      | :x:                | -                          |
| `auto-merge`        | Enable automatic pull request merge                         | :x:                | `false`                    |
| `merge-method`      | Merge method: `merge`, `squash`, or `rebase`                | :x:                | `merge`                    |
| `skip-if-pr-exists` | Skip a new pull request when one with the same title exists | :x:                | `false`                    |
| `dry-run`           | Run without creating a pull request                         | :x:                | `false`                    |

## :warning: Prerequisites

- Add `package.json` and a `pnpm-lock.yaml` lockfile to the repository.
- Specify the Node.js version in `.nvmrc`.
- You can pin the pnpm version in the `packageManager` field of `package.json`.
  `pnpm/action-setup` reads this field.
- Give the action write permissions to create branches and pull requests.

## :information_source: Behavior Notes

pnpm applies these updates. Note these effects:

- The action updates `catalog:` entries in `pnpm-workspace.yaml`. It includes
  this file in the pull request when the file exists.
- On the first run, pnpm sorts the dependency keys in `package.json`.
- pnpm replaces a `"*"` range with a caret range, for example `^1.3.0`.
- The action passes `excluded-packages` entries to pnpm as negation patterns
  (`!<package>`). Plain package names work. pnpm also supports glob patterns
  such as `@scope/*`.
