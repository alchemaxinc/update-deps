#  GitHub Actions for Automatic Dependency Updates

A collection of reusable GitHub Actions for automatically updating project dependencies.

- **`actions/workflows/npm.yml`** - Weekly NPM dependency updates (Mondays at 9 AM UTC)
- **`actions/workflows/golang.yml`** - Weekly Go dependency updates (Mondays at 9 AM UTC)

## Usage

### NPM Dependencies

```yaml
- name: Update NPM Dependencies
  uses: ./actions/updates/npm
  with:
    token: ${{ github.token }}
    base-branch: develop
    excluded-packages: "package1,package2"  # optional
```

### Go Dependencies

```yaml
- name: Update Go Dependencies
  uses: snyk/engprod-actions/.github/workflows/golang.yml@v1
  with:
    token: ${{ github.token }}
    base-branch: develop
```

## Permissions Required

```yaml
permissions:
  contents: write
  pull-requests: write
```
