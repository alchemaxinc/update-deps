# Update Cargo Dependencies :package:

This GitHub Action updates the Rust toolchain and Cargo dependencies. It creates
a pull request with the changes.

> [!IMPORTANT]
> Add `rust-toolchain.toml` to the repository root. This file defines the Rust
> version for the project, including CI workflows, Dockerfiles, and tools. The
> action reads and updates its `channel` field.

> [!NOTE]
> Cargo dependency updates change direct dependency requirements in `Cargo.toml`
> to the latest stable crates.io versions. Then they run `cargo update` for each
> matching `Cargo.lock`. Review these changes because they can include new major
> versions.

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
        uses: alchemaxinc/update-deps/cargo@v2.10.5
        with:
          token: ${{ github.token }}
          base-branch: 'main'
```

### Update only the toolchain version

```yaml
- name: Update Rust Toolchain
  uses: alchemaxinc/update-deps/cargo@v2.10.5
  with:
    token: ${{ github.token }}
    update-deps: 'false'
```

### Update only Cargo dependencies

```yaml
- name: Update Cargo Dependencies
  uses: alchemaxinc/update-deps/cargo@v2.10.5
  with:
    token: ${{ github.token }}
    update-toolchain: 'false'
```

## :gear: Inputs

| Input | Description | Required | Default |
| --- | --- | --- | --- |
| `base-branch` | Base branch for the pull request | :white_check_mark: | `main` |
| `token` | GitHub token for authentication | :x: | `${{ github.token }}` |
| `branch-prefix` | Prefix for the update branch | :x: | `update-dependencies` |
| `pr-title` | Title of the pull request | :x: | `Update Cargo Dependencies` |
| `commit-message` | Commit message for the update | :x: | `Update Cargo dependencies` |
| `app-slug` | GitHub App slug for commit attribution | :x: | - |
| `auto-merge` | Enable automatic pull request merge | :x: | `false` |
| `merge-method` | Merge method: `merge`, `squash`, or `rebase` | :x: | `merge` |
| `skip-if-pr-exists` | Skip a new pull request when one with the same title exists | :x: | `false` |
| `update-toolchain` | Update the Rust toolchain version | :x: | `true` |
| `update-deps` | Update Cargo dependencies | :x: | `true` |
| `dry-run` | Run without creating a pull request | :x: | `false` |

## :mag: How It Works

### Toolchain Updates

The action gets the latest stable Rust release from the GitHub API. It compares
this release with the version in `rust-toolchain.toml`. If a newer version
exists, it updates the `channel` field.

### Dependency Updates

The action finds `Cargo.toml` files outside `target/` directories. It runs
`cargo upgrade` for direct dependencies. Then it runs `cargo update` for each
manifest. This refreshes matching `Cargo.lock` files. Cargo preserves version
syntax, renamed dependencies, and file formatting. Older toolchains install
`cargo-edit` for the same command.

## :warning: Prerequisites

- Add `rust-toolchain.toml` with a `channel` field for the Rust version.
- Give the action write permissions to create branches and pull requests.
- The action finds and updates all `Cargo.toml` projects in the repository.
