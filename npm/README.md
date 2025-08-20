# Update NPM Dependencies :package:

This GitHub Action automatically updates NPM dependencies using `npm-check-updates` and creates a pull request with the changes.

## :sparkles: Features

- :arrows_counterclockwise: Updates all NPM dependencies to their latest versions
- :package: Uses `npm-check-updates` for reliable dependency updates
- :octocat: Automatically creates a pull request with the changes
- :no_entry_sign: Support for excluding specific packages from updates
- :memo: Customizable commit messages and PR titles

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
        uses: your-org/update-deps/npm@v1
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          base-branch: 'main'
          branch-prefix: 'update-npm-deps'
          pr-title: 'Update NPM Dependencies'
          commit-message: 'Update NPM dependencies'
          excluded-packages: 'package1,package2' # Optional
```

## :gear: Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `token` | GitHub token for authentication | :white_check_mark: | `${{ github.token }}` |
| `base-branch` | Base branch for the pull request | :white_check_mark: | `develop` |
| `branch-prefix` | Prefix for the update branch | :white_check_mark: | `update-dependencies` |
| `pr-title` | Title for the pull request | :x: | `Update NPM Dependencies` |
| `commit-message` | Commit message for the update | :x: | `Update NPM dependencies` |
| `excluded-packages` | Comma-separated list of packages to exclude | :x: | - |

## :warning: Prerequisites

- Your repository must have a `package.json` file
- Node.js version should be specified in `.nvmrc` file
- The action requires write permissions to create branches and pull requests

## :memo: What it does

1. :arrow_down: Checks out your repository
2. :wrench: Sets up Node.js environment with npm caching
3. :inbox_tray: Installs and caches `npm-check-updates`
4. :arrows_counterclockwise: Updates dependencies (excluding specified packages if any)
5. :package: Runs `npm install` to update the lockfile
6. :mag: Checks for changes in `package.json` and `package-lock.json`
7. :octocat: Creates a pull request if there are updates

## :bulb: Tips

- :calendar: Use scheduled workflows to automatically check for updates
- :shield: Always review the generated pull request before merging
- :test_tube: Ensure your CI/CD pipeline runs tests on the update branch
- :books: Check release notes for major version updates
