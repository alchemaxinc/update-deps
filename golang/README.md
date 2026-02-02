# Update Go Dependencies :package:

This GitHub Action automatically updates Go module dependencies and creates a pull request with the changes.

> [!IMPORTANT]  
> This action updates dependencies using `go get -u` (by default) and thus does not update to new major versions. You can customize this behavior using the `strategy` input parameter.

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
          strategy: 'controlled' # or 'direct', 'everything'
```

## :gear: Inputs

| Input            | Description                                         | Required           | Default                      |
| ---------------- | --------------------------------------------------- | ------------------ | ---------------------------- |
| `base-branch`    | Base branch for the pull request                    | :white_check_mark: | `main`                       |
| `token`          | GitHub token for authentication                     | :x:                | `${{ github.token }}`        |
| `branch-prefix`  | Prefix for the update branch                        | :x:                | `update-dependencies`        |
| `pr-title`       | Title for the pull request                          | :x:                | `Update Golang Dependencies` |
| `commit-message` | Commit message for the update                       | :x:                | `Update Golang dependencies` |
| `auto-merge`     | Wether automatic merge should be enabled for the PR | :x:                | `false`                      |
| `strategy`       | Dependency update strategy                          | :x:                | `controlled`                 |

## 📋 Update Strategies

The `strategy` parameter controls how dependencies are updated:

### `controlled` (default)

Updates direct dependencies and their transitive dependencies while respecting version constraints. Uses `go get -t -u ./...` for a safe, tested update approach.

**Best for:** Most use cases where stability and compatibility are important.

### `direct`

Updates only direct dependencies (those explicitly listed in `go.mod`) to their latest versions, ignoring indirect dependencies.

```bash
go list -m -f '{{if not .Indirect}}{{.Path}}{{end}}' all \
  | xargs -n1 go get -u
```

**Best for:** When you want to update only the dependencies you directly control.

### `everything`

Updates all dependencies, including indirect ones, to their latest available versions. This is the most aggressive strategy and may introduce breaking changes.

```bash
go list -m -u all \
  | awk '/\[/ { print $1 "@" substr($2,2,length($2)-2) }' \
  | xargs -n1 go get
```

**Best for:** When you want the absolute latest versions and are willing to handle breaking changes.

## :warning: Prerequisites

- Your repository must have a `go.mod` file
- Go version should be specified in the `go.mod` file
- The action requires write permissions to create branches and pull requests
