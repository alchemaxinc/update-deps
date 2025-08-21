# Update CircleCI Orbs :arrows_counterclockwise:

This GitHub Action automatically updates CircleCI orbs to their latest versions and creates a pull request with the
changes.

> [!IMPORTANT]  
> This action works with orbs from the CircleCI Public orb registry that follow the standard versioning pattern. It
> fetches the latest releases from the corresponding GitHub repositories.

## :rocket: Usage

```yaml
name: Update CircleCI Orbs
on:
  schedule:
    - cron: '0 2 * * 1' # Run every Monday at 2 AM
  workflow_dispatch: # Allow manual trigger

jobs:
  update-orbs:
    runs-on: ubuntu-latest
    steps:
      - name: Update CircleCI Orbs
        uses: alchemaxinc/update-deps/circleci-orbs@v21
        with:
          token: ${{ github.token }}
          base-branch: 'main'
          branch-prefix: 'update-circleci-orbs'
          pr-title: 'Update CircleCI Orbs'
          commit-message: 'Update CircleCI orbs'
          circleci-config-file: '.circleci/config.yml'
```

## :gear: Inputs

| Input                  | Description                      | Required           | Default                |
| ---------------------- | -------------------------------- | ------------------ | ---------------------- |
| `base-branch`          | Base branch for the pull request | :white_check_mark: | `develop`              |
| `token`                | GitHub token for authentication  | :x:                | `${{ github.token }}`  |
| `branch-prefix`        | Prefix for the update branch     | :x:                | `update-orbs`          |
| `pr-title`             | Title for the pull request       | :x:                | `Update CircleCI Orbs` |
| `commit-message`       | Commit message for the update    | :x:                | `Update CircleCI orbs` |
| `circleci-config-file` | Path to CircleCI config file     | :x:                | `.circleci/config.yml` |
| `yq-version`           | Version of yq tool to use        | :x:                | `v4.44.1`              |

## :warning: Prerequisites

- Your repository must have a CircleCI configuration file (`.circleci/config.yml` by default)
- The configuration must contain orbs from the CircleCI Public orb registry
- The action requires write permissions to create branches and pull requests
