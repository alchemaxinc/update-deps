# pnpm dependency update actions

Use the split actions to resolve dependency updates without write credentials,
then create the pull request in a separate job. `pnpm/resolve` has no token
input and does not check out code, push, or create pull requests. Every pnpm
update and install command uses `--ignore-scripts`.

## Recommended credential-isolated workflow

```yaml
name: Update pnpm Dependencies

on:
  schedule:
    - cron: '0 2 * * 1'
  workflow_dispatch:

jobs:
  resolve:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    outputs:
      has_changes: ${{ steps.resolve.outputs.has_changes }}
      patch_file: ${{ steps.resolve.outputs.patch_file }}
      files: ${{ steps.resolve.outputs.files }}
      pr_body: ${{ steps.resolve.outputs.pr_body }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
        with:
          persist-credentials: false
      - id: resolve
        uses: alchemaxinc/update-deps/pnpm/resolve@v3
      - if: steps.resolve.outputs.has_changes == 'true'
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
        with:
          name: pnpm-dependency-update
          path: ${{ steps.resolve.outputs.patch_file }}
          if-no-files-found: error

  create-pr:
    needs: resolve
    if: needs.resolve.outputs.has_changes == 'true'
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
        with:
          ref: main
          persist-credentials: false
      - uses: actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093
        with:
          name: pnpm-dependency-update
          path: ${{ runner.temp }}
      - run: git apply --index "$RUNNER_TEMP/pnpm-dependency-update.patch"
      - uses: alchemaxinc/update-deps/pnpm/create-pr@v3
        with:
          token: ${{ github.token }}
          base-branch: main
          branch-prefix: update-pnpm-deps
          pr-title: 'Update pnpm Dependencies'
          commit-message: 'Update pnpm dependencies'
          pr-body: ${{ needs.resolve.outputs.pr_body }}
          files: ${{ needs.resolve.outputs.files }}
```

The artifact is a binary Git patch containing only `package.json`,
`pnpm-lock.yaml`, and `pnpm-workspace.yaml` changes. The privileged job checks
out the protected base branch, applies that patch, and does not execute
package-management commands. Do not add untrusted files to this artifact or
run untrusted code in the privileged job.

## Split action inputs

### `pnpm/resolve`

| Input               | Description                                                         | Default |
| ------------------- | ------------------------------------------------------------------- | ------- |
| `excluded-packages` | Comma-separated packages to exclude; pnpm glob patterns are allowed | -       |
| `relock`            | Refresh `pnpm-lock.yaml` without version changes when true          | `false` |

It outputs `has_changes`, `patch_file`, newline-separated changed `files`, and
a JSON-encoded `pr_body`.

### `pnpm/create-pr`

The PR action must run only after the patch is applied to a checkout of the
base branch. Its required `token` needs `contents: write` and
`pull-requests: write`. It accepts `base-branch`, `branch-prefix`, `pr-title`,
`commit-message`, `pr-body`, `files`, `auto-merge`, `merge-method`, and
`skip-if-pr-exists`.

## Legacy combined action (deprecated)

`alchemaxinc/update-deps/pnpm@v2` remains available for compatibility, but it
resolves dependencies and creates a PR in the same job. It is **not**
credential-isolated and its `token` defaults to `${{ github.token }}`. New
workflows must use the split actions above. Existing inputs remain documented
in [`action.yml`](./action.yml).
