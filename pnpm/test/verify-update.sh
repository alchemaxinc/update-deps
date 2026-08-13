#!/usr/bin/env bash
set -euo pipefail

if [ "$(node -p 'require("./package.json").dependencies.lodash')" = "^4.17.0" ]; then
  echo "::error::pnpm dependency test mode did not update lodash"
  exit 1
fi

if [ "$(node -p 'require("./package.json").dependencies["is-odd"]')" != "2.0.0" ]; then
  echo "::error::pnpm dependency test mode updated excluded package is-odd"
  exit 1
fi

if [ "$(node -p 'require("./package.json").dependencies.semver')" != "7.0.0" ]; then
  echo "::error::pnpm dependency test mode updated excluded package semver"
  exit 1
fi

test -s pnpm-lock.yaml
