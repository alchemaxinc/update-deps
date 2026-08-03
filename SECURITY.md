# Security Policy

## Reporting a vulnerability

Please report suspected vulnerabilities privately through
[GitHub Security Advisories](https://github.com/alchemaxinc/update-deps/security/advisories/new).
Do not open a public issue for a security vulnerability.

Include a clear description, affected action or script, reproduction steps,
impact, and any suggested mitigation. Do not include credentials, tokens, or
other secrets in the report.

We will review the report, confirm the impact, and coordinate a fix and
disclosure with the reporter where appropriate.

## Safe use

These actions can modify repositories and create pull requests. Never run them
with write credentials, secrets, or privileged permissions on an untrusted
checkout, including code from forked pull requests. Use `dry-run: 'true'` and
a read-only token for untrusted or exploratory inputs.
