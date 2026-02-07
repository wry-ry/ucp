#!/bin/bash
set -e

# Ensure we are running from the project root (parent of scripts/)
cd "$(dirname "$0")/.."

# Configuration
TEMP_PATCH="/tmp/ucp-consent-patch.js"
WORKTREE_DIR="build_temp"
OUTPUT_DIR="local_preview"
GH_PAGES_BRANCH="gh-pages"

# Ensure tools are available
export PATH=$PATH:$HOME/.cargo/bin

echo "=== Setup ==="
# Save the consent patch from the current branch
cp docs/javascripts/consent-patch.js "$TEMP_PATCH"

# Clean output
rm -rf "$OUTPUT_DIR"
# Reset local gh-pages to start fresh (optional, but ensures we don't keep junk)
# If you want to keep existing versions that aren't being rebuilt, skip this.
# But "rebuild historical" implies we want a clean state matching the release branches.
# git branch -D $GH_PAGES_BRANCH || true
# git checkout --orphan $GH_PAGES_BRANCH
# rm -rf ./*
# ... initializing fresh gh-pages is complex in script. 
# Better: Just let mike add to existing, we overwrite versions.

echo "=== Syncing Release Branches ==="
git fetch origin

# Find all release branches (format: release/YYYY-MM-DD)
# We strip 'origin/' to get the remote branch name
RELEASE_BRANCHES=$(git branch -r | grep "origin/release/[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}" | sed 's/ *origin\///')

echo "Found branches: $RELEASE_BRANCHES"

for branch in $RELEASE_BRANCHES; do
    version=$(echo "$branch" | sed 's/release\///')
    echo ">>> Rebuilding Version: $version (from $branch)"
    
    # Clean up previous worktree if any
    rm -rf "$WORKTREE_DIR"
    git worktree prune
    
    # Create worktree
    git worktree add -f "$WORKTREE_DIR" "origin/$branch"
    
    pushd "$WORKTREE_DIR" > /dev/null
    
    # 1. Install Consent Patch File
    mkdir -p docs/javascripts
    cp "$TEMP_PATCH" docs/javascripts/consent-patch.js
    
    # 2. Patch mkdocs.yml to include the script
    # We use python to safely modify YAML without breaking structure
    python3 -c "
import yaml
import sys

try:
    with open('mkdocs.yml', 'r') as f:
        config = yaml.safe_load(f) or {}
    
    extra_js = config.get('extra_javascript', [])
    if 'javascripts/consent-patch.js' not in extra_js:
        extra_js.append('javascripts/consent-patch.js')
        config['extra_javascript'] = extra_js
        
        with open('mkdocs.yml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        print('Patched mkdocs.yml with consent script.')
    else:
        print('mkdocs.yml already has consent script.')
except Exception as e:
    print(f'Error patching mkdocs.yml: {e}')
    sys.exit(1)
"
    
    # 3. Deploy with Mike
    # Note: We use the local mkdocs.yml of that version
    uv run mike deploy "$version"
    
    popd > /dev/null
    git worktree remove -f "$WORKTREE_DIR"
done

echo ">>> Building Current Version (Draft & Latest)"
# Deploy current code
uv run mike deploy -F mkdocs-spec.yml draft
# Deploy as latest (copy of draft, or date? User asked for 'latest' to be latest version)
# Actually, if we rebuilt releases, one of them IS the latest date.
# We should alias 'latest' to the newest release, NOT draft.
# Let's find the newest release version again.
LATEST_VERSION=$(echo "$RELEASE_BRANCHES" | sed 's/release\///' | sort -r | head -n 1)

if [ -n "$LATEST_VERSION" ]; then
    echo "Aliasing 'latest' to $LATEST_VERSION"
    # We don't need to rebuild it, just alias it.
    uv run mike alias "$LATEST_VERSION" latest --update-aliases
else
    echo "No release found, aliasing latest to draft"
    uv run mike alias draft latest --update-aliases
fi

echo ">>> Building Root Site"
uv run mkdocs build -f mkdocs.yml -d "$OUTPUT_DIR"
rm -rf "$OUTPUT_DIR/specification"

echo ">>> Merging All Versions"
# Extract everything from gh-pages
git archive "$GH_PAGES_BRANCH" | tar -x -C "$OUTPUT_DIR"

echo "=== Build Complete! ==="
echo "Run this command to serve:"
echo "python3 -m http.server 8000 -d $OUTPUT_DIR"
