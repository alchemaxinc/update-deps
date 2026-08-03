#!/usr/bin/env bash
set -euo pipefail

git diff --exit-code -- circleci-orbs/test/.circleci/config.yml
