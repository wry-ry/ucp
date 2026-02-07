#!/bin/bash
set -e

# Ensure we are running from the project root (parent of scripts/)
cd "$(dirname "$0")/.."

# Configuration
ROOT_CONFIG="mkdocs.yml"
SPEC_CONFIG="mkdocs-spec.yml"
OUTPUT_DIR="local_preview"
GH_PAGES_BRANCH="gh-pages"

# Ensure tools are available
export PATH=$PATH:$HOME/.cargo/bin

echo "=== Cleaning Output Directory ==="
rm -rf "$OUTPUT_DIR"

echo "=== Building Root Site (Unversioned) ==="
uv run mkdocs build -f "$ROOT_CONFIG" -d "$OUTPUT_DIR"

echo "=== Removing Unversioned Specification Files ==="
rm -rf "$OUTPUT_DIR/specification"

echo "=== Syncing gh-pages from Remote ==="
git fetch origin gh-pages
git update-ref refs/heads/$GH_PAGES_BRANCH refs/remotes/origin/$GH_PAGES_BRANCH

echo "=== Deploying Current Changes to 'draft' ==="
uv run mike deploy -F "$SPEC_CONFIG" draft

echo "=== Identifying All Version Folders ==="
ALL_VERSIONS=$(git ls-tree -d --name-only $GH_PAGES_BRANCH | grep -E '^(draft|[0-9]{4}-[0-9]{2}-[0-9]{2})$' | tr '\n' ' ')
LATEST_VERSION=$(git ls-tree -d --name-only $GH_PAGES_BRANCH | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' | sort -r | head -n 1)

echo "Found versions: $ALL_VERSIONS"
echo "Latest stable: $LATEST_VERSION"

echo "=== Extracting All Spec Versions from $GH_PAGES_BRANCH ==="
git archive "$GH_PAGES_BRANCH" $ALL_VERSIONS versions.json | tar -x -C "$OUTPUT_DIR"

echo "=== Creating 'latest' alias ==="
if [ -n "$LATEST_VERSION" ]; then
    rm -rf "$OUTPUT_DIR/latest"
    cp -r "$OUTPUT_DIR/$LATEST_VERSION" "$OUTPUT_DIR/latest"
    echo "Created 'latest' directory from $LATEST_VERSION"
else
    echo "Warning: No dated version found to alias as 'latest'."
fi

echo "=== Injecting Consent Patch into Historical Versions ==="
# Inject the consent-patch.js script into all HTML files of extracted versions.
# This allows old versions to participate in shared consent during local preview.
# We skip 'draft' and 'latest' if they are new builds that already include it via mkdocs.yml,
# but injecting it twice is harmless (just redundant) or we can check.
# Since historical versions (e.g. 2026-01-11) DEFINITELY lack it, we target everything in ALL_VERSIONS.

INJECTION_SCRIPT='<script src="/latest/javascripts/consent-patch.js"></script>'

for ver in $ALL_VERSIONS; do
    if [ -d "$OUTPUT_DIR/$ver" ]; then
        echo "Injecting consent patch into $ver..."
        # Using python to append before </body> tag for cross-platform compatibility
        # We walk all HTML files
        find "$OUTPUT_DIR/$ver" -name "*.html" -print0 | xargs -0 python3 -c "
import sys
import os

script_tag = '$INJECTION_SCRIPT'
for filepath in sys.argv[1:]:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Avoid double injection if already present
    if 'consent-patch.js' in content:
        continue
        
    if '</body>' in content:
        new_content = content.replace('</body>', script_tag + '\n</body>')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
"
    fi
done

echo "=== Build Complete! ==="
echo "You can now view the site at: http://localhost:8000/"
echo "Run this command to serve:"
echo "python3 -m http.server 8000 -d $OUTPUT_DIR"
