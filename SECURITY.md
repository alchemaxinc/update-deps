# Security Policy

## Reporting a vulnerability

Report suspected vulnerabilities privately through
[GitHub Security Advisories](https://github.com/alchemaxinc/update-deps/security/advisories/new).
Do not open a public issue for a security vulnerability.

Include a clear description, the affected action or script, reproduction
steps, impact, and a suggested mitigation. Do not include credentials, tokens,
or other secrets in the report.

We review the report and confirm the impact. We coordinate a fix and disclosure
with the reporter when needed.

## Safe use

These actions can modify repositories and create pull requests. Never run them
on an untrusted checkout with write credentials, secrets, or privileged
permissions. This includes code from forked pull requests. For untrusted or
exploratory input, use `dry-run: 'true'` and a read-only token.
