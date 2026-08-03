#!/usr/bin/env bash
set -euo pipefail

if cmp -s golang/test/go.mod go.mod; then
  echo "::error::Go dependency test mode did not update go.mod"
  exit 1
fi
