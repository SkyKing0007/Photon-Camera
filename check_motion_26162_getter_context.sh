#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

REPORT="/workspaces/Photon-Camera/motion_26162_getter_exact_context.txt"
HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"

{
  echo "=== CHECKPOINT ==="
  echo "Branch: $(git branch --show-current)"
  echo "Commit: $(git rev-parse HEAD)"
  grep '^VERSION_BUILD=' app/version.properties
  echo

  echo "=== TRACKED STATUS ==="
  git status --short --untracked-files=no
  echo

  echo "=== STALE GETTER MATCHES ==="
  grep -n -A12 -B12 -E \
    'getEffectiveFrameCount|getEffectiveStackRatio|getSubpixelSampleDiversity|effectiveFrameCount|effectiveStackRatio|subpixelSampleDiversity' \
    "$HDRX"
  echo

  echo "=== EXACT LINES 420-475 ==="
  nl -ba "$HDRX" | sed -n '420,475p'
  echo

  echo "=== CONTEXT COMPLETE ==="
} | tee "$REPORT"
