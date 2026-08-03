#!/usr/bin/env bash
set -euo pipefail

cmp docker/test/Dockerfile Dockerfile
cmp docker/test/docker-compose.yml docker-compose.yml
