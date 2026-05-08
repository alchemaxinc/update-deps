#!/usr/bin/env bash
#
# Install a pinned `crane` binary from google/go-containerregistry.
#
# Usage: install_crane.sh <version>
#
# - Downloads the release tarball + checksums.txt from the GitHub release.
# - Verifies the tarball against the canonical SHA256 in checksums.txt.
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

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

echo "::notice::Downloading crane $version ($asset)"
curl -fsSL -o "$tmp_dir/$asset" "$base_url/$asset"
curl -fsSL -o "$tmp_dir/checksums.txt" "$base_url/checksums.txt"

# checksums.txt contains "<sha256>  <asset>" lines for every asset; pick the
# one matching our tarball and feed it to sha256sum -c.
expected_line="$(grep " ${asset}\$" "$tmp_dir/checksums.txt" || true)"
if [[ -z "$expected_line" ]]; then
  echo "::error::No checksum entry for $asset in checksums.txt"
  exit 1
fi

(
  cd "$tmp_dir"
  echo "$expected_line" | sha256sum -c -
)

tar -xzf "$tmp_dir/$asset" -C "$bin_dir" crane
chmod +x "$bin_dir/crane"

# Persist for subsequent steps in the same job.
if [[ -n "${GITHUB_PATH:-}" ]]; then
  echo "$bin_dir" >> "$GITHUB_PATH"
fi

echo "::notice::Installed crane to $bin_dir/crane"
"$bin_dir/crane" version
