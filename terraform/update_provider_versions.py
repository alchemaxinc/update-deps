#!/usr/bin/env python3
import json
import subprocess
import re
import os
import sys
import logging


def main():
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname)s: %(message)s',
        stream=sys.stderr
    )

    working_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    versions_file = sys.argv[2] if len(sys.argv) > 2 else None

    # Check that working_dir exists and is a directory
    if not os.path.isdir(working_dir):
        logging.error(f"Working directory '{working_dir}' does not exist or is not a directory.")
        sys.exit(1)

    # Check that versions_file is provided
    if not versions_file:
        logging.error("Versions file path must be provided as the second argument.")
        sys.exit(1)

    # Check that versions_file exists
    if not os.path.isfile(versions_file):
        logging.error(f"Versions file '{versions_file}' does not exist or is not a file.")
        sys.exit(1)

    # Read current versions
    try:
        with open(versions_file, "r") as f:
            current_data = json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Versions file '{versions_file}' is not valid JSON: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading versions file '{versions_file}': {e}")
        sys.exit(1)

    # Extract providers from current versions
    providers = {}
    if "provider_selections" not in current_data:
        logging.error("No providers found in current versions")
        sys.exit(1)

    for namespace, version in current_data["provider_selections"].items():
        logging.debug(f"Processing provider '{namespace}/{version}'")

        registry, name = namespace.split("/", 1)
        providers[namespace] = {
            "registry": registry,
            "name": name,
            "current": version,
            "latest": None
        }

    # Get latest versions from Terraform registry
    logging.info("Fetching latest provider versions...")
    for namespace, provider_info in providers.items():
        try:
            registry = provider_info["registry"]
            name = provider_info["name"]
            url = f"https://{registry}/v1/providers/{name}"

            logging.debug(f"Fetching version info from {url}")

            result = subprocess.run(
                ["curl", "-s", url],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                logging.warning(f"Failed to fetch {namespace}: curl returned {result.returncode}")
                continue

            data = json.loads(result.stdout)
            if "version" not in data:
                logging.warning(f"No version field found for {namespace}")
                continue

            provider_info["latest"] = data["version"]
            logging.info(
                f"{namespace}: current={provider_info['current']}, latest={provider_info['latest']}")
        except Exception as e:
            logging.error(f"Error fetching {namespace}: {e}")

    # Update .tf files with new versions
    tf_files = []
    for root, dirs, files in os.walk(working_dir):
        for file in files:
            if file.endswith(".tf"):
                tf_files.append(os.path.join(root, file))

    logging.info(f"Found {len(tf_files)} .tf files")

    for tf_file in tf_files:
        # Initialize content to satisfy static analyzers in all code paths
        content = ""
        with open(tf_file, "r") as rf:
            content = rf.read()

        # Skip files that don't have required_providers block
        if "required_providers" not in content:
            logging.debug(f"Skipping {tf_file} - no required_providers block found")
            continue

        original_content = content

        for namespace, provider_info in providers.items():
            if not provider_info["latest"]:
                continue

            if provider_info["latest"] == provider_info["current"]:
                continue

            # Extract major.minor version from latest version (ignore patch)
            latest_version = provider_info["latest"]
            version_parts = latest_version.split('.')
            if len(version_parts) >= 2:
                new_version_constraint = f"~> {version_parts[0]}.{version_parts[1]}"
            else:
                # Fallback if version format is unexpected
                logging.warning(f"Unexpected version format for {namespace}: {latest_version}")
                new_version_constraint = f"~> {version_parts[0]}.0"

            # The source in .tf files looks like "hashicorp/aws" (namespace/name)
            # not the full path like "registry.terraform.io/hashicorp/aws"
            # We need to extract just the last two parts
            name = provider_info["name"]

            # Pattern matches: source = "hashicorp/aws" followed by version = "..."
            # We need to find the provider block and update its version
            # Match the provider with its source, then update the version line within that block
            pattern = (
                    rf'(\b\w+\s*=\s*\{{\s*'  # provider_name = {
                    rf'[^}}]*source\s*=\s*["\']' + re.escape(name) + r'["\']'  # source = "registry/name"
                                                                     rf'[^}}]*version\s*=\s*["\'])[^"\']+(["\'])'
                # version = "..."
            )

            replacement = f'\\g<1>{new_version_constraint}\\g<2>'
            new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

            if new_content == content:
                logging.debug(f"No match found for {name} in {tf_file}")
                continue

            content = new_content
            logging.info(f"Updated {name} to {new_version_constraint} in {tf_file}")

        if content != original_content:
            with open(tf_file, "w") as wf:
                wf.write(content)

    logging.info("Provider updates complete")


if __name__ == "__main__":
    main()
