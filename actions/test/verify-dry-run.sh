#!/usr/bin/env bash
set -euo pipefail

git diff --exit-code -- actions/test/.github
