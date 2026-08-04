# Update Terraform Dependencies :package:

This GitHub Action updates Terraform provider dependencies. It creates a pull
request with the changes.

> [!IMPORTANT]
> This action finds provider updates:
>
> 1. It gets current provider versions.
> 2. It gets the latest versions from the Terraform Registry.
> 3. It updates provider version constraints in `.tf` files.
> 4. It runs `terraform init -upgrade` to update `.terraform.lock.hcl`.
> 5. It creates a pull request when files change in the Terraform working directory.

## :rocket: Usage

```yaml
name: Update Terraform Dependencies
on:
  schedule:
    - cron: '0 2 * * 1' # Run every Monday at 2 AM
  workflow_dispatch: # Allow manual trigger

jobs:
  update-dependencies:
    runs-on: ubuntu-latest
    steps:
      - name: Update Terraform Dependencies
        uses: alchemaxinc/update-deps/terraform@v2.11.1
        with:
          token: ${{ github.token }}
          base-branch: 'main'
          branch-prefix: 'update-terraform-deps'
          working-dir: './terraform'
```

## :gear: Inputs

| Input               | Description                                                                  | Required           | Default                         |
| ------------------- | ---------------------------------------------------------------------------- | ------------------ | ------------------------------- |
| `base-branch`       | Base branch for the pull request                                             | :white_check_mark: | `main`                          |
| `token`             | GitHub token for authentication                                              | :x:                | `${{ github.token }}`           |
| `branch-prefix`     | Prefix for the update branch                                                 | :x:                | `update-dependencies`           |
| `pr-title`          | Title of the pull request                                                    | :x:                | `Update Terraform Dependencies` |
| `commit-message`    | Commit message for the update                                                | :x:                | `Update Terraform dependencies` |
| `working-dir`       | Working directory for Terraform                                              | :white_check_mark: | -                               |
| `var-file-path`     | Deprecated input. Terraform `init` and `validate` do not use variable files. | :x:                | -                               |
| `backend-config`    | Backend configuration value for `terraform init -backend-config=`            | :x:                | -                               |
| `app-slug`          | GitHub App slug for commit attribution                                       | :x:                | -                               |
| `auto-merge`        | Enable automatic pull request merge                                          | :x:                | `false`                         |
| `merge-method`      | Merge method: `merge`, `squash`, or `rebase`                                 | :x:                | `merge`                         |
| `skip-if-pr-exists` | Skip a new pull request when one with the same title exists                  | :x:                | `false`                         |
| `dry-run`           | Run without creating a pull request                                          | :x:                | `false`                         |

## :gear: How It Works

The action does these steps:

1. **Checkout and setup:** Checks out the repository and sets up Terraform.
2. **Baseline initialization:** Runs `terraform init` with an optional backend configuration.
3. **Get current versions:** Runs `terraform version -json`.
4. **Get latest versions:** Queries the Terraform Registry API for each provider.
5. **Update provider constraints:** Updates `.tf` files in the `required_providers` block.
6. **Run Terraform init with upgrade:** Runs `terraform init -upgrade` to update `.terraform.lock.hcl`.
7. **Validate Terraform:** Validates the Terraform configuration.
8. **Format Terraform:** Formats `.tf` files with `terraform fmt`.
9. **Find changes:** Detects changes in the configured Terraform working directory.
10. **Create pull request:** Creates a pull request only when files change.

## :warning: Prerequisites

- Add Terraform configuration files (`.tf` files) to the repository.
- Add `.terraform.lock.hcl`, or let the action create it.
- Define provider requirements in a `required_providers` block in `.tf` files.
- Give the action write permissions to create branches and pull requests.

## :bulb: Tips

- Use `backend-config` for remote state backends that need more configuration.
- The action creates a pull request only when it finds version changes.
- Use `working-dir` to specify the subdirectory with Terraform configuration.
- The action uses conservative provider version constraints (`~> X.Y`).
- The action validates and formats Terraform files before it creates the pull request.
