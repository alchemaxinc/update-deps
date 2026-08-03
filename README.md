# :arrows_counterclockwise: Update Dependencies Actions

![Logo](docs/logo.png)

A collection of convenient GitHub Actions for automatically updating your software dependencies.

## Actions

- :package: **[NPM Dependencies](./npm/README.md)** - Updates NPM package dependencies using npm-check-updates
- :package: **[pnpm Dependencies](./pnpm/README.md)** - Updates pnpm package dependencies using pnpm update
- :gear: **[Go Dependencies](./golang/README.md)** - Updates Go module dependencies
- :arrows_counterclockwise: **[CircleCI Orbs](./circleci-orbs/README.md)** - Updates CircleCI orbs to their latest versions
- :globe_with_meridians: **[Terraform Dependencies](./terraform/README.md)** - Updates Terraform provider dependencies
- :crab: **[Cargo Dependencies](./cargo/README.md)** - Updates Rust toolchain version and Cargo dependencies
- :octocat: **[GitHub Actions](./actions/README.md)** - Updates GitHub Actions in workflow files to their latest versions
- :whale: **[Docker Dependencies](./docker/README.md)** - Updates Docker image tags in Dockerfiles and docker-compose files

## Runner platform and permissions

The actions are composite Bash actions supported on GitHub-hosted Linux runners
(`ubuntu-latest`). Windows runners are not supported. Run update workflows on a
trusted checkout only.

Actions that create branches and pull requests require a token with
`contents: write` and `pull-requests: write` permissions. For
`GITHUB_TOKEN`, declare the permissions in the calling workflow:

```yaml
permissions:
  contents: write
  pull-requests: write
```

Use a read-only token and `dry-run: 'true'` when testing. Never run these
actions with write credentials, secrets, or other privileged permissions on an
untrusted checkout, including code from a forked pull request.

## Local validation

The CI checks can be run locally on a supported Linux environment:

```bash
npm ci --ignore-scripts
npx --no-install prettier --check .
npm exec --package=cspell@8.0.0 -- cspell

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

- **`Resource not accessible by integration` or PR creation fails:** grant the
  calling workflow or supplied token `contents: write` and
  `pull-requests: write`.
- **No pull request is created:** confirm that changes are available and that
  `dry-run` is `false`; `skip-if-pr-exists` also avoids duplicate PRs.
- **Version lookup or install failures:** ensure the runner can reach GitHub,
  package registries, and the relevant public dependency registry. Review the
  action log for the package or image that could not be resolved.

For contribution and security-reporting guidance, see
[CONTRIBUTING.md](./CONTRIBUTING.md) and [SECURITY.md](./SECURITY.md).
