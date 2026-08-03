# Contributing

Thanks for contributing to Update Dependencies Actions.

## Development and validation

Use a supported Linux environment (`ubuntu-latest` in CI). Install the
repository's JavaScript tooling and run the checks described in the
[local validation section](README.md#local-validation). Run the tests relevant
to the component you change before opening a pull request.

Keep changes focused, update user-facing documentation when behavior changes,
and use [Conventional Commits](https://www.conventionalcommits.org/) commit
messages. CI checks commit messages, formatting, spelling, and Python tests.

## Pull requests

- Describe the problem and the behavior your change provides.
- Include validation commands and their results.
- Do not include unrelated generated files or dependency changes.
- Make sure the pull request can run without credentials from an untrusted
  source.

## Workflow safety

Do not run update actions with write tokens, secrets, or privileged permissions
against untrusted checkouts, including pull requests from forks. Test such
changes with `dry-run: 'true'` and a read-only token. Workflows that create
branches and pull requests need only `contents: write` and
`pull-requests: write`; do not grant broader permissions.
