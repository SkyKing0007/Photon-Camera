#!/usr/bin/env bash
set -euo pipefail

ROOT=/workspaces/Photon-Camera
cd "$ROOT"

echo "=== PHOTON / IRIS 26177 PRECHECK ==="
echo
echo "=== BRANCH ==="
git branch --show-current
echo
echo "=== HEAD ==="
git rev-parse HEAD
echo
echo "=== BUILD ==="
grep '^VERSION_' app/version.properties || true
echo
echo "=== STATUS ==="
git status --short
echo
echo "=== POSSIBLE APPROVED APPLE-STYLE UI ARTIFACTS ==="
find . -maxdepth 2 \( \
  -iname '*26175*apple*ui*' -o \
  -iname '*apple*reference*audit*' -o \
  -iname '*26174*ui*' -o \
  -iname '*26173*ui*' -o \
  -iname '*compact*apple*' \
\) | sort
echo
echo "=== UI LAYOUT HITS (THUMBNAIL / SWITCH / MODE PICKER) ==="
grep -RInE 'gallery|thumbnail|switch|flip|mode|LiquidModePicker|HorizontalPicker' \
  app/src/main/res/layout \
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera \
  2>/dev/null | head -220
echo
echo "=== BOTTOM BUTTON LAYOUT CONTEXT ==="
sed -n '1,240p' app/src/main/res/layout/layout_bottombuttons.xml || true
echo
echo "=== MAIN BOTTOM BAR CONTEXT ==="
sed -n '1,260p' app/src/main/res/layout/layout_main_bottombar.xml || true
echo
echo "=== MODE SWITCHER CONTEXT ==="
sed -n '1,220p' app/src/main/res/layout/layout_modeswitcher.xml || true
echo
echo "=== 26176 MOTION TUNING MARKERS ==="
for f in \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java
do
  echo
  echo "--- $f ---"
  if [[ -f "$f" ]]; then
    grep -nE 'motionChromaCleanupMaximum|motionLumaCleanupMaximum|motionCaptureSharpeningFloor|motionFinalSharpeningFloor' "$f" || true
  else
    echo "MISSING"
  fi
done
echo
echo "=== END PRECHECK ==="
