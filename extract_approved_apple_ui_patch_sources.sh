#!/usr/bin/env bash
set -euo pipefail

cd /workspaces/Photon-Camera

OUT="approved_apple_ui_patch_sources.txt"

{
  echo "=== APPROVED APPLE UI PATCH SOURCE AUDIT ==="
  echo
  echo "=== 26173 BUILD SCRIPT ==="
  sed -n '1,320p' build_photon_26173_hdrx_fix_apple_liquid_ui.sh 2>/dev/null || true

  echo
  echo "=== 26174 RESUME SCRIPT ==="
  sed -n '1,320p' resume_build_photon_26174_hdrx_ui_compile_fix.sh 2>/dev/null || true

  echo
  echo "=== 26173 BUILD DIRECTORY FILES ==="
  find build_26173_hdrx_fix_apple_liquid_ui_20260731_150139 \
    -maxdepth 3 -type f 2>/dev/null | sort

  echo
  echo "=== 26174 BUILD DIRECTORY FILES ==="
  find build_26174_hdrx_ui_compile_fix_20260731_150812 \
    -maxdepth 3 -type f 2>/dev/null | sort

  echo
  echo "=== PATCH FILES REFERENCING LIQUIDMODEPICKER OR MODE SWITCHER ==="
  find . -maxdepth 3 -type f \( -name '*.patch' -o -name '*.diff' -o -name '*.txt' \) \
    -print0 2>/dev/null |
  xargs -0 grep -IlE 'LiquidModePicker|layout_modeswitcher|liquid_glass|MODE_DISPLAY_ORDER' 2>/dev/null |
  sort

  echo
  echo "=== BACKUP COPIES OF KEY APPROVED UI FILES ==="
  find . -type f \( \
    -path '*/layout_modeswitcher.xml' -o \
    -path '*/layout_bottombuttons.xml' -o \
    -path '*/LiquidModePicker.java' -o \
    -path '*/CameraUIViewImpl.java' \
  \) -not -path './app/*' 2>/dev/null | sort

  echo
  echo "=== END AUDIT ==="
} | tee "$OUT"

echo
echo "Created visible Explorer file:"
echo "/workspaces/Photon-Camera/$OUT"
