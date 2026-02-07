#!/bin/bash
set -e

# Ensure we are running from the project root (parent of scripts/)
cd "$(dirname "$0")/.."

# Configuration
WORKTREE_DIR="build_temp"
OUTPUT_DIR="local_preview"
GH_PAGES_BRANCH="gh-pages"

# Ensure tools are available
export PATH=$PATH:$HOME/.cargo/bin

# Capture the configured Python environment
PYTHON_CMD=$(uv python find)
echo "Using Python: $PYTHON_CMD"

echo "=== Setup ==="
rm -rf "$OUTPUT_DIR"

# Save current config and assets to inject into historical builds
# We want all versions to use the MODERN configuration (nav, consent, theme)
cp mkdocs-spec.yml /tmp/ucp-mkdocs-spec.yml
cp docs/javascripts/consent-patch.js /tmp/ucp-consent-patch.js

echo "=== Syncing Release Branches ==="
git fetch origin
RELEASE_BRANCHES=$(git branch -r | grep "origin/release/[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}" | sed 's/ *origin\///')

echo "Found branches: $RELEASE_BRANCHES"

for branch in $RELEASE_BRANCHES; do
    version=$(echo "$branch" | sed 's/release\///')
    echo ">>> Rebuilding Version: $version (from $branch) using CURRENT config"
    
    rm -rf "$WORKTREE_DIR"
    git worktree prune
    git worktree add -f "$WORKTREE_DIR" "origin/$branch"
    
    pushd "$WORKTREE_DIR" > /dev/null
    
    # 1. Install Modern Assets
    mkdir -p docs/javascripts
    cp /tmp/ucp-consent-patch.js docs/javascripts/consent-patch.js
    
    # 2. Use Modern Config
    # We copy the current mkdocs-spec.yml over the old mkdocs.yml (or just use it via -F)
    cp /tmp/ucp-mkdocs-spec.yml mkdocs-spec.yml
    
    # 3. Deploy
    "$PYTHON_CMD" -m mike deploy -F mkdocs-spec.yml "$version"
    
    popd > /dev/null
    git worktree remove -f "$WORKTREE_DIR"
done

echo ">>> Building Current Version (Draft & Latest)"
uv run mike deploy -F mkdocs-spec.yml draft

LATEST_VERSION=$(echo "$RELEASE_BRANCHES" | sed 's/release\///' | sort -r | head -n 1)

if [ -n "$LATEST_VERSION" ]; then
    echo "Aliasing 'latest' to $LATEST_VERSION"
    uv run mike alias "$LATEST_VERSION" latest --update-aliases
else
    echo "No release found, aliasing latest to draft"
    uv run mike alias draft latest --update-aliases
fi

echo ">>> Building Root Site"
uv run mkdocs build -f mkdocs.yml -d "$OUTPUT_DIR"
rm -rf "$OUTPUT_DIR/specification"

echo ">>> Merging All Versions"
git archive "$GH_PAGES_BRANCH" | tar -x -C "$OUTPUT_DIR"

echo "=== Build Complete! ==="
echo "Run this command to serve:"
echo "python3 -m http.server 8000 -d $OUTPUT_DIR"
