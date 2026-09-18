#!/usr/bin/env bash
# Helper to publish repository to GitHub. Prefers GitHub CLI (gh) if available.
# Usage: ./scripts/publish.sh [repo-name] [--private]

set -euo pipefail
REPO_NAME=${1:-whispering-wilds}
PRIVATE_FLAG=""
if [[ "${2:-}" == "--private" ]]; then PRIVATE_FLAG="--private"; fi

if ! command -v git >/dev/null 2>&1; then
  echo "git is required. Install it and try again." >&2
  exit 1
fi

# init and commit if necessary
if [[ ! -d .git ]]; then
  echo "Initializing git repository..."
  git init
  git add -A
  git commit -m "Initial commit: LifeHub dashboard"
else
  echo "Existing git repository detected. Will commit staged changes if any."
  if ! git diff --quiet || ! git diff --cached --quiet; then
    git add -A
    git commit -m "chore: update before publish" || true
  fi
fi

# If gh is available use it
if command -v gh >/dev/null 2>&1; then
  echo "Using GitHub CLI to create repo and push..."
  gh repo create "$REPO_NAME" $PRIVATE_FLAG --source=. --push
  echo "Repository created and pushed via gh.";
  exit 0
fi

# Otherwise prompt user to create repo on GitHub and add remote
read -p "gh CLI not found. Please create a repo on GitHub (https://github.com/new) and enter the remote URL (HTTPS or SSH): " REMOTE_URL
if [[ -z "$REMOTE_URL" ]]; then
  echo "No remote supplied — aborting." >&2
  exit 1
fi

git remote add origin "$REMOTE_URL"
git branch -M main
git push -u origin main

echo "Pushed to $REMOTE_URL"