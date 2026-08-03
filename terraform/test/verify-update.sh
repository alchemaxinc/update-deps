#!/usr/bin/env bash
set -euo pipefail

if git diff --quiet -- terraform/test; then
  echo "::error::Terraform dependency test mode did not update the fixture"
  exit 1
fi
