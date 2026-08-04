# Contributing

Thank you for contributing to Update Dependencies Actions.

## Development and validation

Use a supported Linux environment (`ubuntu-latest` in CI). Install the
repository JavaScript tools. Run the checks in the
[local validation section](README.md#local-validation). Before you open a pull
request, run the tests for the component that you change.

Keep each change focused. Update user documentation when behavior changes. Use
[Conventional Commits](https://www.conventionalcommits.org/) commit messages.
CI checks commit messages, formatting, spelling, and Python tests.

## Pull requests

- Describe the problem and the new behavior.
- Include the validation commands and results.
- Do not include unrelated generated files or dependency changes.
- Make sure that the pull request runs without credentials from an untrusted
  source.

## Workflow safety

Never run update actions on untrusted checkouts with write tokens, secrets, or
privileged permissions. This includes pull requests from forks. Test these
changes with `dry-run: 'true'` and a read-only token. Workflows that create
branches and pull requests need only `contents: write` and
`pull-requests: write`. Do not grant more permissions.
