# Update CircleCI Orbs :arrows_counterclockwise:

This GitHub Action automatically updates CircleCI orbs to their latest versions and creates a pull request with the changes.

## :sparkles: Features

- :arrows_counterclockwise: Updates all CircleCI orbs to their latest versions
- :mag: Automatically detects orbs in your CircleCI configuration
- :octocat: Creates a pull request with the changes
- :gear: Configurable CircleCI config file path
- :memo: Customizable commit messages and PR titles

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
        uses: your-org/update-deps/circleci-orbs@v1
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          base-branch: 'main'
          branch-prefix: 'update-circleci-orbs'
          pr-title: 'Update CircleCI Orbs'
          commit-message: 'Update CircleCI orbs'
          circleci-config-file: '.circleci/config.yml'
```

## :gear: Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `token` | GitHub token for authentication | :white_check_mark: | `${{ github.token }}` |
| `base-branch` | Base branch for the pull request | :white_check_mark: | `develop` |
| `branch-prefix` | Prefix for the update branch | :white_check_mark: | `update-orbs` |
| `pr-title` | Title for the pull request | :x: | `Update CircleCI Orbs` |
| `commit-message` | Commit message for the update | :x: | `Update CircleCI orbs` |
| `circleci-config-file` | Path to CircleCI config file | :x: | `.circleci/config.yml` |
| `yq-version` | Version of yq tool to use | :x: | `v4.44.1` |

## :warning: Prerequisites

- Your repository must have a CircleCI configuration file (`.circleci/config.yml` by default)
- The configuration must contain orbs from the CircleCI Public orb registry
- The action requires write permissions to create branches and pull requests

## :memo: What it does

1. :arrow_down: Checks out your repository
2. :wrench: Installs and caches the `yq` YAML processor
3. :mag: Scans your CircleCI config for orb references
4. :arrows_counterclockwise: Fetches latest versions from CircleCI Public orb registry
5. :pencil2: Updates orb versions in the configuration file
6. :mag: Checks for changes in the CircleCI config file
7. :octocat: Creates a pull request if there are updates

## :bulb: Tips

- :calendar: Use scheduled workflows to automatically check for updates
- :shield: Always review the generated pull request before merging
- :test_tube: Test your CircleCI pipeline with the updated orbs
- :books: Check orb changelogs for breaking changes
- :warning: Be cautious with major version updates as they may contain breaking changes

## :information_source: Supported Orbs

This action works with orbs from the CircleCI Public orb registry that follow the standard versioning pattern. It fetches the latest releases from the corresponding GitHub repositories.
