# Update Go Dependencies :package:

This GitHub Action automatically updates Go module dependencies and creates a pull request with the changes.

## :sparkles: Features

- :arrows_counterclockwise: Updates all Go module dependencies to their latest versions
- :wrench: Uses `go get -u` and `go mod tidy` for clean updates
- :octocat: Automatically creates a pull request with the changes
- :memo: Customizable base branch and branch prefix

## :rocket: Usage

```yaml
name: Update Go Dependencies
on:
  schedule:
    - cron: '0 2 * * 1' # Run every Monday at 2 AM
  workflow_dispatch: # Allow manual trigger

jobs:
  update-dependencies:
    runs-on: ubuntu-latest
    steps:
      - name: Update Go Dependencies
        uses: your-org/update-deps/golang@v1
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          base-branch: 'main'
          branch-prefix: 'update-go-deps'
```

## :gear: Inputs

| Input           | Description                      | Required           | Default               |
| --------------- | -------------------------------- | ------------------ | --------------------- |
| `token`         | GitHub token for authentication  | :white_check_mark: | `${{ github.token }}` |
| `base-branch`   | Base branch for the pull request | :white_check_mark: | `develop`             |
| `branch-prefix` | Prefix for the update branch     | :white_check_mark: | `update-dependencies` |

## :warning: Prerequisites

- Your repository must have a `go.mod` file
- Go version should be specified in the `go.mod` file
- The action requires write permissions to create branches and pull requests

## :memo: What it does

1. :arrow_down: Checks out your repository
2. :wrench: Sets up Go environment with module caching
3. :arrows_counterclockwise: Runs `go get -t -u ./...` to update all dependencies
4. :broom: Runs `go mod tidy` to clean up the module files
5. :mag: Checks for changes in `go.mod` and `go.sum`
6. :octocat: Creates a pull request if there are updates

## :bulb: Tips

- :calendar: Use scheduled workflows to automatically check for updates
- :shield: Always review the generated pull request before merging
- :test_tube: Ensure your CI/CD pipeline runs tests on the update branch
- :books: Check for breaking changes in major version updates
- :warning: Be cautious with major version updates as they may contain breaking changes
