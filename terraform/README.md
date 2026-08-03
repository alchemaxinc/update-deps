# Terraform provider update actions

Use the split actions to update and validate providers without write
credentials, then create the pull request in a separate job.
`terraform/resolve` has no token input and does not check out code, push, or
create pull requests. Its `terraform init` calls always use `-backend=false`;
backend and Terraform Cloud credentials are not used during unprivileged
resolution or validation.

## Recommended credential-isolated workflow

```yaml
name: Update Terraform Providers

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
        uses: alchemaxinc/update-deps/terraform/resolve@v3
        with:
          working-dir: terraform
      - if: steps.resolve.outputs.has_changes == 'true'
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
        with:
          name: terraform-dependency-update
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
          name: terraform-dependency-update
          path: ${{ runner.temp }}
      - run: git apply --index "$RUNNER_TEMP/terraform-dependency-update.patch"
      - uses: alchemaxinc/update-deps/terraform/create-pr@v3
        with:
          token: ${{ github.token }}
          base-branch: main
          branch-prefix: update-terraform-deps
          pr-title: 'Update Terraform Dependencies'
          commit-message: 'Update Terraform dependencies'
          pr-body: ${{ needs.resolve.outputs.pr_body }}
          files: ${{ needs.resolve.outputs.files }}
```

The artifact is a binary Git patch limited to changed `.tf`, `.tf.json`, and
`.terraform.lock.hcl` files in `working-dir`. The privileged job checks out the
protected base branch, applies that patch, and does not run Terraform. Do not
add untrusted files to this artifact or run untrusted code in the privileged
job.

## Split action inputs

### `terraform/resolve`

| Input         | Description                    | Required |
| ------------- | ------------------------------ | -------- |
| `working-dir` | Directory containing Terraform | yes      |

It outputs `has_changes`, `patch_file`, the newline-separated changed `files`,
and a JSON-encoded `pr_body`.

### `terraform/create-pr`

The PR action must run only after the patch is applied to a checkout of the
base branch. Its required `token` needs `contents: write` and
`pull-requests: write`. It accepts `base-branch`, `branch-prefix`, `pr-title`,
`commit-message`, `pr-body`, `files`, `auto-merge`, `merge-method`, and
`skip-if-pr-exists`.

## Legacy combined action (deprecated)

`alchemaxinc/update-deps/terraform@v2` remains available for compatibility,
but it resolves, validates, and creates a PR in the same job. It is **not**
credential-isolated. Its legacy `backend-config` input can initialize a
backend, unlike `terraform/resolve`. New workflows must use the split actions
above. Existing inputs remain documented in [`action.yml`](./action.yml).
