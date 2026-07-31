#!/usr/bin/env bash
set -euo pipefail

cd /workspaces/Photon-Camera

OUT="audit_26179_exact_active_hdr_ui_context.txt"

show_range() {
  local file="$1"
  local start="$2"
  local end="$3"
  echo
  echo "----- $file : $start-$end -----"
  nl -ba "$file" | sed -n "${start},${end}p"
}

{
  echo "=== BUILD 26179 EXACT ACTIVE HDR + APPROVED UI CONTEXT ==="
  echo "Branch: $(git branch --show-current)"
  echo "HEAD:   $(git rev-parse HEAD)"
  grep '^VERSION_BUILD=' app/version.properties
  echo

  show_range \
    app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ExposureFusionBayer2.java \
    190 590

  show_range \
    app/src/main/assets/shaders/ltm/exposebayer2.glsl \
    1 180

  show_range \
    app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java \
    1 390

  show_range \
    app/src/main/assets/shaders/initial.glsl \
    150 610

  show_range \
    app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/AutoExposure.java \
    1 240

  show_range \
    app/src/main/assets/shaders/autoexposure/apply.glsl \
    1 140

  show_range \
    app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java \
    1 285

  show_range \
    app/src/main/assets/shaders/denoise/esd3d2.glsl \
    1 230

  show_range \
    app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java \
    1 230

  show_range \
    app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java \
    110 150

  show_range \
    app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java \
    250 305

  show_range \
    app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java \
    1 180

  show_range \
    app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/modeswitcher/LiquidModePicker.java \
    1 320

  show_range \
    app/src/main/res/layout/layout_modeswitcher.xml \
    1 180

  show_range \
    app/src/main/res/layout/layout_bottombuttons.xml \
    1 180

  echo
  echo "=== SEARCH FOR EXPANSION / COLLAPSE / MANUAL TRAY IMPLEMENTATION ==="
  grep -RIn -B12 -A30 -E \
    'expand|collapse|collapsed|expanded|manual_controls|Exposure|Shutter|ISO|MODE_DISPLAY_ORDER|setValues|setSelectedItem|Motion/Video-first' \
    app/src/main/java/com/particlesdevs/photoncamera/ui/camera \
    app/src/main/res/layout \
    | head -n 3000 || true

  echo
  echo "=== SEARCH FOR AVAILABLE SCENE/HISTOGRAM METRICS ==="
  grep -RIn -B15 -A35 -E \
    'histogram|Histogram|whitePoint|white point|highlightClippedFraction|clipped|overexposure|overExpose|FusionMap|GainMap|targetLuma|target luma' \
    app/src/main/java/com/particlesdevs/photoncamera/processing \
    app/src/main/assets/shaders \
    | head -n 4000 || true

  echo
  echo "=== END EXACT CONTEXT ==="
} | tee "$OUT"

echo
echo "Created visible Explorer file:"
echo "/workspaces/Photon-Camera/$OUT"
