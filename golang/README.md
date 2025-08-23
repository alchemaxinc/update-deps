# Update Go Dependencies :package:

This GitHub Action automatically updates Go module dependencies and creates a pull request with the changes.

> [!IMPORTANT]  
> This action updates dependencies using `go get -u` and thus does not update to new major versions.

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
        uses: alchemaxinc/update-deps/golang@v1
        with:
          token: ${{ github.token }}
          base-branch: 'main'
          branch-prefix: 'update-go-deps'
```

## :gear: Inputs

| Input           | Description                      | Required           | Default               |
| --------------- | -------------------------------- | ------------------ | --------------------- |
| `base-branch`   | Base branch for the pull request | :white_check_mark: | `main`                |
| `token`         | GitHub token for authentication  | :x:                | `${{ github.token }}` |
| `branch-prefix` | Prefix for the update branch     | :x:                | `update-dependencies` |

## :warning: Prerequisites

- Your repository must have a `go.mod` file
- Go version should be specified in the `go.mod` file
- The action requires write permissions to create branches and pull requests
