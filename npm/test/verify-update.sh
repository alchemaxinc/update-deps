#!/usr/bin/env bash
set -euo pipefail

if [ "$(node -p 'require("./package.json").dependencies.lodash')" = "^4.17.0" ]; then
  echo "::error::NPM dependency test mode did not update lodash"
  exit 1
fi

test -s package-lock.json
