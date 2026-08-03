#!/usr/bin/env bash
set -euo pipefail

manifest_path="${CARGO_MANIFEST_PATH:-wrapper/Cargo.toml}"
cargo metadata --manifest-path "$manifest_path" --no-deps --format-version 1 \
  > /dev/null
