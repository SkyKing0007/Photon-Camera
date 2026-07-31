#!/usr/bin/env bash
set -euo pipefail

cd /workspaces/Photon-Camera

echo "=== LOCATE APPROVED 26174 UI SOURCE ==="

echo
echo "=== 26174 BUILD DIRECTORY CONTENTS ==="
find build_26174_hdrx_ui_compile_fix_20260731_150812 -maxdepth 4 -type f 2>/dev/null | sort | head -300

echo
echo "=== ALL SAVED layout_bottombuttons.xml COPIES ==="
find . -type f -path '*/app/src/main/res/layout/layout_bottombuttons.xml' \
  -not -path './app/src/main/res/layout/layout_bottombuttons.xml' \
  2>/dev/null | sort

echo
echo "=== ALL SAVED layout_modeswitcher.xml COPIES ==="
find . -type f -path '*/app/src/main/res/layout/layout_modeswitcher.xml' \
  -not -path './app/src/main/res/layout/layout_modeswitcher.xml' \
  2>/dev/null | sort

echo
echo "=== ALL SAVED CameraUIViewImpl.java COPIES ==="
find . -type f -path '*/app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java' \
  -not -path './app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java' \
  2>/dev/null | sort

echo
echo "=== 26173 / 26174 UI SCRIPT REFERENCES ==="
for f in \
  build_photon_26173_hdrx_fix_apple_liquid_ui.sh \
  resume_build_photon_26174_hdrx_ui_compile_fix.sh \
  inspect_photon_apple_style_ui.sh
do
  if [[ -f "$f" ]]; then
    echo
    echo "--- $f ---"
    grep -nE 'backup|cp |layout_bottombuttons|layout_modeswitcher|CameraUIViewImpl|LiquidModePicker|tar|zip|rsync' "$f" | head -240 || true
  fi
done

echo
echo "=== APPLE UI AUDIT CONTENTS ==="
find photon_ui_apple_reference_audit_20260731_134042 -maxdepth 5 -type f 2>/dev/null | sort | head -300

echo
echo "=== END LOCATOR ==="
