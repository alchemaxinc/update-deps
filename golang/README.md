# Update Go Dependencies :package:

This GitHub Action updates Go module dependencies. It creates a pull request
with the changes.

> [!IMPORTANT]  
> By default, this action uses `go get -u`. It does not update to new major
> versions. Use the `strategy` input to change this behavior.

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
        uses: alchemaxinc/update-deps/golang@v2.11.0
        with:
          token: ${{ github.token }}
          base-branch: 'main'
          branch-prefix: 'update-go-deps'
          strategy: 'controlled' # or 'direct', 'everything'
```

## :gear: Inputs

| Input               | Description                                                 | Required           | Default                      |
| ------------------- | ----------------------------------------------------------- | ------------------ | ---------------------------- |
| `base-branch`       | Base branch for the pull request                            | :white_check_mark: | `main`                       |
| `token`             | GitHub token for authentication                             | :x:                | `${{ github.token }}`        |
| `branch-prefix`     | Prefix for the update branch                                | :x:                | `update-dependencies`        |
| `pr-title`          | Title of the pull request                                   | :x:                | `Update Golang Dependencies` |
| `commit-message`    | Commit message for the update                               | :x:                | `Update Golang dependencies` |
| `app-slug`          | GitHub App slug for commit attribution                      | :x:                | -                            |
| `auto-merge`        | Enable automatic pull request merge                         | :x:                | `false`                      |
| `merge-method`      | Merge method: `merge`, `squash`, or `rebase`                | :x:                | `merge`                      |
| `skip-if-pr-exists` | Skip a new pull request when one with the same title exists | :x:                | `false`                      |
| `strategy`          | Dependency update strategy                                  | :x:                | `controlled`                 |
| `dry-run`           | Run without creating a pull request                         | :x:                | `false`                      |

## 📋 Update Strategies

The `strategy` input controls dependency updates:

### `controlled` (default)

Updates direct and transitive dependencies within version constraints. It uses
`go get -t -u ./...`.

**Use this strategy for:** Updates that need stability and compatibility.

### `direct`

Updates only direct dependencies listed in `go.mod`. It ignores indirect
dependencies.

```bash
while IFS= read -r module; do
  [ -z "$module" ] && continue
  go get -u "$module"
done < <(go list -m -f '{{if and (not .Indirect) (not .Main)}}{{.Path}}{{end}}' all)
```

**Use this strategy for:** Updates to only direct dependencies.

### `everything`

Updates direct and indirect dependencies to their latest versions. This is the
most aggressive strategy. It can introduce breaking changes.

```bash
while IFS= read -r module; do
  [ -z "$module" ] && continue
  go get "$module"
done < <(go list -m -u all \
  | awk '$NF ~ /^\[v/ { print $1 "@" substr($NF, 2, length($NF) - 2) }')
```

**Use this strategy for:** Updates that need the latest versions and can accept
breaking changes.

## :warning: Prerequisites

- Add a `go.mod` file to the repository.
- Specify the Go version in `go.mod`.
- Give the action write permissions to create branches and pull requests.
