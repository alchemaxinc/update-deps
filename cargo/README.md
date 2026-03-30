# Update Cargo Dependencies :package:

This GitHub Action automatically updates the Rust toolchain version and Cargo dependencies, and creates a pull request with the changes.

> [!IMPORTANT]
> This action requires a `rust-toolchain.toml` file in the repository root. This file serves as the single source of truth for the Rust version used across the project — including CI workflows, Dockerfiles, and any other tooling. The action reads and updates the `channel` field in this file.

> [!NOTE]
> Cargo dependency updates use `cargo update`, which updates `Cargo.lock` to the latest versions allowed by the semver constraints in `Cargo.toml`. This means it will not introduce breaking changes beyond what your version constraints allow. To update to new major versions, you would need to manually bump the constraints in `Cargo.toml`.

## :rocket: Usage

```yaml
name: Update Cargo Dependencies
on:
  schedule:
    - cron: '0 2 * * 1' # Run every Monday at 2 AM
  workflow_dispatch: # Allow manual trigger

jobs:
  update-dependencies:
    runs-on: ubuntu-latest
    steps:
      - name: Update Cargo Dependencies
        uses: alchemaxinc/update-deps/cargo@v1
        with:
          token: ${{ github.token }}
          base-branch: 'main'
```

### Update only the toolchain version

```yaml
- name: Update Rust Toolchain
  uses: alchemaxinc/update-deps/cargo@v1
  with:
    token: ${{ github.token }}
    update-deps: 'false'
```

### Update only Cargo dependencies

```yaml
- name: Update Cargo Dependencies
  uses: alchemaxinc/update-deps/cargo@v1
  with:
    token: ${{ github.token }}
    update-toolchain: 'false'
```

## :gear: Inputs

| Input              | Description                                          | Required           | Default                     |
| ------------------ | ---------------------------------------------------- | ------------------ | --------------------------- |
| `base-branch`      | Base branch for the pull request                     | :white_check_mark: | `main`                      |
| `token`            | GitHub token for authentication                      | :x:                | `${{ github.token }}`       |
| `branch-prefix`    | Prefix for the update branch                         | :x:                | `update-dependencies`       |
| `pr-title`         | Title for the pull request                           | :x:                | `Update Cargo Dependencies` |
| `commit-message`   | Commit message for the update                        | :x:                | `Update Cargo dependencies` |
| `auto-merge`       | Whether automatic merge should be enabled for the PR | :x:                | `false`                     |
| `update-toolchain` | Whether to update the Rust toolchain version         | :x:                | `true`                      |
| `update-deps`      | Whether to update Cargo dependencies                 | :x:                | `true`                      |

## :mag: How It Works

### Toolchain Updates

The action fetches the latest stable Rust release from the GitHub API and compares it against the version specified in `rust-toolchain.toml`. If a newer version is available, it updates the `channel` field in the file.

### Dependency Updates

The action auto-discovers all `Cargo.toml` files in the repository (excluding `target/` directories) and runs `cargo update` for each. This updates `Cargo.lock` files to the latest compatible versions within the existing semver constraints.

## :warning: Prerequisites

- Your repository must have a `rust-toolchain.toml` file with a `channel` field specifying the Rust version
- The action requires write permissions to create branches and pull requests
- All `Cargo.toml` projects in the repository are discovered and updated automatically
