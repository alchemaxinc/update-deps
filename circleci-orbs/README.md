# Update CircleCI Orbs :arrows_counterclockwise:

This GitHub Action updates CircleCI orbs and creates a pull request.

> [!IMPORTANT]  
> This action supports orbs from the CircleCI Public orb registry with the
> standard version pattern. It gets the latest published version from that registry.

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
        uses: alchemaxinc/update-deps/circleci-orbs@v2.11.2
        with:
          token: ${{ github.token }}
          base-branch: 'main'
          branch-prefix: 'update-circleci-orbs'
          pr-title: 'Update CircleCI Orbs'
          commit-message: 'Update CircleCI orbs'
          circleci-config-file: '.circleci/config.yml'
```

## :gear: Inputs

| Input                  | Description                                                 | Required           | Default                |
| ---------------------- | ----------------------------------------------------------- | ------------------ | ---------------------- |
| `base-branch`          | Base branch for the pull request                            | :white_check_mark: | `main`                 |
| `token`                | GitHub token for authentication                             | :x:                | `${{ github.token }}`  |
| `branch-prefix`        | Prefix for the update branch                                | :x:                | `update-orbs`          |
| `pr-title`             | Title of the pull request                                   | :x:                | `Update CircleCI Orbs` |
| `commit-message`       | Commit message for the update                               | :x:                | `Update CircleCI orbs` |
| `circleci-config-file` | Path to the CircleCI configuration file                     | :x:                | `.circleci/config.yml` |
| `yq-version`           | Version of yq                                               | :x:                | `v4.44.1`              |
| `app-slug`             | GitHub App slug for commit attribution                      | :x:                | -                      |
| `auto-merge`           | Enable automatic pull request merge                         | :x:                | `false`                |
| `merge-method`         | Merge method: `merge`, `squash`, or `rebase`                | :x:                | `merge`                |
| `skip-if-pr-exists`    | Skip a new pull request when one with the same title exists | :x:                | `false`                |
| `dry-run`              | Run without creating a pull request                         | :x:                | `false`                |

## :warning: Prerequisites

- Add a CircleCI configuration file. The default is `.circleci/config.yml`.
- The configuration must contain orbs from the CircleCI Public orb registry.
- Give the action write permissions to create branches and pull requests.
- Linux and macOS runners with x86_64 or arm64 CPUs are supported.
