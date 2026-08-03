#!/usr/bin/env bash
# Set the local Git author from the token that creates the pull request.

set -euo pipefail

if user_json=$(gh api /user 2>/dev/null); then
  git_user=$(echo "$user_json" | jq -r '.login')
  git_id=$(echo "$user_json" | jq -r '.id')
elif viewer_json=$(gh api graphql -f query='{ viewer { login databaseId } }' 2>/dev/null); then
  git_user=$(echo "$viewer_json" | jq -r '.data.viewer.login')
  git_id=$(echo "$viewer_json" | jq -r '.data.viewer.databaseId')
else
  git_user='github-actions[bot]'
  git_id='41898282'
fi

git config --local user.name "$git_user"
git config --local user.email "${git_id}+${git_user}@users.noreply.github.com"
