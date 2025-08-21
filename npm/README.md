# Update NPM Dependencies :package:

This GitHub Action automatically updates NPM dependencies using `npm-check-updates` and creates a pull request with the
changes.

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
        uses: alchemaxinc/update-deps/npm@v1
        with:
          token: ${{ github.token }}
          base-branch: 'main'
          branch-prefix: 'update-npm-deps'
          pr-title: 'Update NPM Dependencies'
          commit-message: 'Update NPM dependencies'
          excluded-packages: 'package1,package2' # Optional
```

## :gear: Inputs

| Input               | Description                                 | Required           | Default                   |
| ------------------- | ------------------------------------------- | ------------------ | ------------------------- |
| `base-branch`       | Base branch for the pull request            | :white_check_mark: | `develop`                 |
| `token`             | GitHub token for authentication             | :x:                | `${{ github.token }}`     |
| `branch-prefix`     | Prefix for the update branch                | :x:                | `update-dependencies`     |
| `pr-title`          | Title for the pull request                  | :x:                | `Update NPM Dependencies` |
| `commit-message`    | Commit message for the update               | :x:                | `Update NPM dependencies` |
| `excluded-packages` | Comma-separated list of packages to exclude | :x:                | -                         |

## :warning: Prerequisites

- Your repository must have a `package.json` file
- Node.js version should be specified in `.nvmrc` file
- The action requires write permissions to create branches and pull requests
