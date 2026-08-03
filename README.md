# :arrows_counterclockwise: Update Dependencies Actions

![Logo](docs/logo.png)

This repository provides GitHub Actions that update software dependencies.

## Actions

- :package: **[NPM Dependencies](./npm/README.md)** - Updates NPM dependencies with npm-check-updates.
- :package: **[pnpm Dependencies](./pnpm/README.md)** - Updates pnpm dependencies with pnpm.
- :gear: **[Go Dependencies](./golang/README.md)** - Updates Go module dependencies.
- :arrows_counterclockwise: **[CircleCI Orbs](./circleci-orbs/README.md)** - Updates CircleCI orbs.
- :globe_with_meridians: **[Terraform Dependencies](./terraform/README.md)** - Updates Terraform provider dependencies.
- :crab: **[Cargo Dependencies](./cargo/README.md)** - Updates the Rust toolchain and Cargo dependencies.
- :octocat: **[GitHub Actions](./actions/README.md)** - Updates GitHub Actions in workflow files.
- :whale: **[Docker Dependencies](./docker/README.md)** - Updates Docker image tags in Dockerfiles and docker-compose files.

## Runner platform and permissions

These composite Bash actions run on GitHub-hosted Linux runners
(`ubuntu-latest`). Windows runners are not supported. Run update workflows
only on trusted checkouts.

Actions that create branches and pull requests need `contents: write` and
`pull-requests: write` permissions. For `GITHUB_TOKEN`, declare these
permissions in the calling workflow:

```yaml
permissions:
  contents: write
  pull-requests: write
```

For a test, use a read-only token and `dry-run: 'true'`. Never run these
actions on an untrusted checkout with write credentials, secrets, or other
privileged permissions. This includes code from a forked pull request.

## Local validation

Run the CI checks locally on a supported Linux environment:

```bash
tool_prefix="$HOME/.cache/update-deps-tools"
npm install --global --prefix "$tool_prefix" --ignore-scripts \
  prettier@3.3.3 cspell@8.0.0
"$tool_prefix/bin/prettier" --check .
"$tool_prefix/bin/cspell"

python -m pip install "black==24.10.0" \
  -r actions/requirements.txt -r docker/requirements.txt
black --check .
python -m unittest discover -s actions -p "test_*.py" -v
python -m unittest discover -s terraform -p "test_*.py" -v
python -m unittest discover -s cargo -p "test_*.py" -v
python -m unittest discover -s docker -p "test_*.py" -v
python -m unittest discover -s shared -p "test_*.py" -v
```

## Troubleshooting

- **`Resource not accessible by integration` or PR creation fails:** Give the
  calling workflow or supplied token `contents: write` and
  `pull-requests: write`.
- **No pull request is created:** Make sure that changes exist and `dry-run`
  is `false`. `skip-if-pr-exists` prevents duplicate pull requests.
- **Version lookup or installation fails:** Make sure that the runner can
  reach GitHub, package registries, and the public dependency registry.
  Read the action log for the package or image that the action cannot resolve.

For contribution and security-reporting instructions, see
[CONTRIBUTING.md](./CONTRIBUTING.md) and [SECURITY.md](./SECURITY.md).
