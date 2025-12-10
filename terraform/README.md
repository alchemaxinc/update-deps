````markdown
# Update Terraform Dependencies :package:

This GitHub Action automatically updates Terraform provider dependencies and creates a pull request with the changes.

> [!IMPORTANT]  
> This action intelligently detects provider updates by:
>
> 1. Capturing current provider versions
> 2. Fetching the latest versions from the Terraform Registry
> 3. Updating provider version constraints in `.tf` files
> 4. Running `terraform init -upgrade` to update the `.terraform.lock.hcl`
> 5. Comparing versions before and after to ensure changes were made

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
        uses: alchemaxinc/update-deps/terraform@v1
        with:
          token: ${{ github.token }}
          base-branch: 'main'
          branch-prefix: 'update-terraform-deps'
          working-dir: './terraform'
          var-file-path: './terraform/terraform.tfvars'
```

## :gear: Inputs

| Input            | Description                                                       | Required           | Default                         |
| ---------------- | ----------------------------------------------------------------- | ------------------ | ------------------------------- |
| `base-branch`    | Base branch for the pull request                                  | :white_check_mark: | `main`                          |
| `token`          | GitHub token for authentication                                   | :x:                | `${{ github.token }}`           |
| `branch-prefix`  | Prefix for the update branch                                      | :x:                | `update-dependencies`           |
| `pr-title`       | Title for the pull request                                        | :x:                | `Update Terraform Dependencies` |
| `commit-message` | Commit message for the update                                     | :x:                | `Update Terraform dependencies` |
| `working-dir`    | Working directory for Terraform                                   | :white_check_mark: | -                               |
| `var-file-path`  | Path to Terraform variables file                                  | :white_check_mark: | -                               |
| `backend-config` | Backend configuration value for `terraform init -backend-config=` | :x:                | -                               |

## :gear: How It Works

This action performs the following steps:

1. **Checkout and Setup** - Checks out the repository and sets up Terraform
2. **Baseline Initialization** - Runs `terraform init` with optional backend configuration to establish baseline
3. **Capture Current Versions** - Runs `terraform version -json` to get current provider versions
4. **Fetch Latest Versions** - Queries the Terraform Registry API for each provider to find the latest available versions
5. **Update Provider Constraints** - Updates all `.tf` files with new provider version constraints in the `required_providers` block
6. **Run Terraform Init with Upgrade** - Executes `terraform init -upgrade` to update the `.terraform.lock.hcl` file
7. **Capture Updated Versions** - Runs `terraform version -json` again to get the updated provider versions
8. **Terraform Validate** - Validates the Terraform configuration to ensure it's still valid
9. **Terraform Format** - Formats all `.tf` files using `terraform fmt`
10. **Check for Changes** - Compares the version snapshots before and after to verify changes were made
11. **Create Pull Request** - Only creates a PR if version changes were detected

## :warning: Prerequisites

- Your repository must have Terraform configuration files (`.tf` files)
- A `.terraform.lock.hcl` file must be present or will be created
- Provider requirements must be defined in a `required_providers` block in your `.tf` files
- A valid Terraform variables file must be provided via `var-file-path`
- The action requires write permissions to create branches and pull requests

## :bulb: Tips

- The `var-file-path` is required when your Terraform configuration needs variables to initialize successfully
- The `backend-config` is optional and useful for remote state backends that require additional configuration
- The action only creates a PR if it detects actual version changes, preventing unnecessary PRs
- Use `working-dir` to specify the subdirectory containing your Terraform configuration
- The action uses conservative version constraints (`~> X.Y.Z`) when updating providers
- The action automatically validates and formats your Terraform code before creating the PR
````
