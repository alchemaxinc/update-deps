# Update Cargo Dependencies :package:

This GitHub Action automatically updates the Rust toolchain version and Cargo dependencies, and creates a pull request with the changes.

> [!IMPORTANT]
> This action requires a `rust-toolchain.toml` file in the repository root. This file serves as the single source of truth for the Rust version used across the project — including CI workflows, Dockerfiles, and any other tooling. The action reads and updates the `channel` field in this file.

> [!NOTE]
> Cargo dependency updates bump direct dependency version requirements in `Cargo.toml` to the latest stable crates.io versions, then run `cargo update` to refresh each matching `Cargo.lock`. Review these changes carefully because version requirement bumps can include new major versions.

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
        uses: alchemaxinc/update-deps/cargo@v2.1.0
        with:
          token: ${{ github.token }}
          base-branch: 'main'
```

### Update only the toolchain version

```yaml
- name: Update Rust Toolchain
  uses: alchemaxinc/update-deps/cargo@v2.1.0
  with:
    token: ${{ github.token }}
    update-deps: 'false'
```

### Update only Cargo dependencies

```yaml
- name: Update Cargo Dependencies
  uses: alchemaxinc/update-deps/cargo@v2.1.0
  with:
    token: ${{ github.token }}
    update-toolchain: 'false'
```

## :gear: Inputs

| Input               | Description                                                                                | Required           | Default                     |
| ------------------- | ------------------------------------------------------------------------------------------ | ------------------ | --------------------------- |
| `base-branch`       | Base branch for the pull request                                                           | :white_check_mark: | `main`                      |
| `token`             | GitHub token for authentication                                                            | :x:                | `${{ github.token }}`       |
| `branch-prefix`     | Prefix for the update branch                                                               | :x:                | `update-dependencies`       |
| `pr-title`          | Title for the pull request                                                                 | :x:                | `Update Cargo Dependencies` |
| `commit-message`    | Commit message for the update                                                              | :x:                | `Update Cargo dependencies` |
| `app-slug`          | GitHub App slug for commit attribution                                                     | :x:                | -                           |
| `auto-merge`        | Whether automatic merge should be enabled for the PR                                       | :x:                | `false`                     |
| `skip-if-pr-exists` | Skip creating a new PR if an open PR with the same title already exists on the base branch | :x:                | `false`                     |
| `update-toolchain`  | Whether to update the Rust toolchain version                                               | :x:                | `true`                      |
| `update-deps`       | Whether to update Cargo dependencies                                                       | :x:                | `true`                      |
| `dry-run`           | Run without creating a PR                                                                  | :x:                | `false`                     |

## :mag: How It Works

### Toolchain Updates

The action fetches the latest stable Rust release from the GitHub API and compares it against the version specified in `rust-toolchain.toml`. If a newer version is available, it updates the `channel` field in the file.

### Dependency Updates

The action auto-discovers all `Cargo.toml` files in the repository (excluding `target/` directories), updates direct dependency version requirements to the latest stable crates.io versions, and runs `cargo update` for each manifest. This refreshes matching `Cargo.lock` files after the manifest changes.

## :warning: Prerequisites

- Your repository must have a `rust-toolchain.toml` file with a `channel` field specifying the Rust version
- The action requires write permissions to create branches and pull requests
- All `Cargo.toml` projects in the repository are discovered and updated automatically
