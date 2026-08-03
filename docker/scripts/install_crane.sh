#!/usr/bin/env bash
#
# Install a pinned `crane` binary from google/go-containerregistry.
#
# Usage: install_crane.sh <version>
#
# - Downloads the release tarball from the GitHub release.
# - Extracts to "$RUNNER_TEMP/crane/bin" and appends that dir to $GITHUB_PATH.
#
set -euo pipefail

version="${1:-}"
if [[ -z "$version" ]]; then
  echo "::error::install_crane.sh requires a version argument (e.g. v0.21.5)"
  exit 1
fi

# Map uname -> go-containerregistry asset naming.
os_raw="$(uname -s)"
arch_raw="$(uname -m)"

case "$os_raw" in
  Linux)  os="Linux" ;;
  Darwin) os="Darwin" ;;
  *)
    echo "::error::Unsupported OS for crane install: $os_raw"
    exit 1
    ;;
esac

case "$arch_raw" in
  x86_64|amd64) arch="x86_64" ;;
  arm64|aarch64) arch="arm64" ;;
  *)
    echo "::error::Unsupported architecture for crane install: $arch_raw"
    exit 1
    ;;
esac

asset="go-containerregistry_${os}_${arch}.tar.gz"
base_url="https://github.com/google/go-containerregistry/releases/download/${version}"

work_dir="${RUNNER_TEMP:-/tmp}/crane"
bin_dir="$work_dir/bin"
mkdir -p "$bin_dir"

# Fast path: if a previous step (e.g. actions/cache) already restored the
# requested crane binary, skip the download and just expose it on PATH.
if [[ -x "$bin_dir/crane" ]]; then
  installed_version="$("$bin_dir/crane" version 2>/dev/null || true)"
  if [[ "$installed_version" == *"${version#v}"* ]]; then
    echo "::notice::Reusing cached crane $version at $bin_dir/crane"
    if [[ -n "${GITHUB_PATH:-}" ]]; then
      echo "$bin_dir" >> "$GITHUB_PATH"
    fi
    exit 0
  fi
  echo "::notice::Cached crane reports version '$installed_version' (want '${version#v}'); reinstalling"
  rm -f "$bin_dir/crane"
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

echo "::notice::Downloading crane $version ($asset)"
curl --fail --location --silent --show-error --retry 3 --retry-all-errors \
  --connect-timeout 10 --max-time 60 -o "$tmp_dir/$asset" "$base_url/$asset"
tar -xzf "$tmp_dir/$asset" -C "$bin_dir" crane
chmod +x "$bin_dir/crane"

# Persist for subsequent steps in the same job.
if [[ -n "${GITHUB_PATH:-}" ]]; then
  echo "$bin_dir" >> "$GITHUB_PATH"
fi

echo "::notice::Installed crane to $bin_dir/crane"
"$bin_dir/crane" version
