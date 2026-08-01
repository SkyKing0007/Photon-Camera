#!/usr/bin/env bash
set -euo pipefail

cd /workspaces/Photon-Camera

fail() {
  printf '\nERROR: %s\n' "$*" >&2
  exit 1
}

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_BRANCH="backup/codespace-migration-before-local-${STAMP}"
PATCH="/workspaces/Photon-Camera-codespace-migration-${STAMP}.patch"
BUNDLE="/workspaces/Photon-Camera-codespace-migration-${STAMP}.bundle"

[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] \
  || fail "Expected branch $EXPECTED_BRANCH"

[[ "$(git rev-parse HEAD)" == "$EXPECTED_HEAD" ]] \
  || fail "Unexpected starting HEAD"

grep -qx 'VERSION_BUILD=26179' app/version.properties \
  || fail "Expected VERSION_BUILD=26179"

echo "Creating backup branch..."
git branch "$BACKUP_BRANCH"

echo "Saving complete tracked-file patch..."
git diff --binary HEAD > "$PATCH"

echo "Staging source, resources, and visible workflow scripts..."
git add app ./*.sh

git status --short

if git diff --cached --quiet; then
  fail "Nothing was staged"
fi

echo "Committing exact local development state..."
git commit -m "Checkpoint Photon Motion HDR and UI work at build 26179"

NEW_HEAD="$(git rev-parse HEAD)"

echo "Pushing experimental branch only..."
git push -u origin "$EXPECTED_BRANCH"

echo "Pushing backup pointer..."
git push origin "$BACKUP_BRANCH"

echo "Creating offline Git bundle..."
git bundle create "$BUNDLE" \
  "$EXPECTED_BRANCH" \
  "$BACKUP_BRANCH"

git bundle verify "$BUNDLE"

echo
echo "=== CODESPACE MIGRATION CHECKPOINT COMPLETE ==="
echo "Branch: $EXPECTED_BRANCH"
echo "Commit: $NEW_HEAD"
echo "Build:  26179"
echo "Remote: origin/$EXPECTED_BRANCH"
echo "Backup branch: $BACKUP_BRANCH"
echo "Patch:  $PATCH"
echo "Bundle: $BUNDLE"
echo
echo "Do not delete the Codespace yet."
