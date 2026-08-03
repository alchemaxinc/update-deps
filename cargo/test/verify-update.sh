#!/usr/bin/env bash
set -euo pipefail

if cmp -s cargo/test/rust-toolchain.toml rust-toolchain.toml; then
  echo "::error::Cargo dependency test mode did not update rust-toolchain.toml"
  exit 1
fi

if cmp -s cargo/test/wrapper/Cargo.toml wrapper/Cargo.toml; then
  echo "::error::Cargo dependency test mode did not update wrapper/Cargo.toml"
  exit 1
fi
