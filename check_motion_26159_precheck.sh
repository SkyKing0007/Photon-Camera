#!/usr/bin/env bash
set -u

cd /workspaces/Photon-Camera

echo "=== PHOTON 26159 PRECHECK ==="
echo "Branch: $(git branch --show-current)"
echo "Commit: $(git rev-parse HEAD)"
grep '^VERSION_BUILD=' app/version.properties || true
echo
echo "=== TRACKED STATUS ==="
git status --short --untracked-files=no
echo
echo "=== DIFF SUMMARY ==="
git diff --stat
echo
echo "=== BACKUP BRANCHES FOR 26158/26159 ==="
git branch --list '*26158*' '*26159*'
echo
echo "=== PRECHECK COMPLETE ==="
