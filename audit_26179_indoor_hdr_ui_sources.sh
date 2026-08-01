#!/usr/bin/env bash
set -euo pipefail

cd /workspaces/Photon-Camera

OUT="audit_26179_indoor_hdr_ui_sources.txt"

{
  echo "=== PHOTON CAMERA 26179 INDOOR-HDR + APPROVED UI SOURCE AUDIT ==="
  echo
  echo "Branch: $(git branch --show-current)"
  echo "HEAD:   $(git rev-parse HEAD)"
  echo "Build:  $(grep '^VERSION_BUILD=' app/version.properties || true)"
  echo
  echo "=== WORKING TREE ==="
  git status --short
  echo
  echo "=== CURRENT PROCESSING TUNING MARKERS ==="
  grep -RInE \
    'motionChromaCleanupMaximum|motionLumaCleanupMaximum|motionCaptureSharpeningFloor|motionFinalSharpeningFloor|motionShadowNeutralization' \
    app/src/main/java app/src/main/assets 2>/dev/null || true
  echo
  echo "=== TONE / HDR / HIGHLIGHT / SHADOW / MIDTONE IMPLEMENTATION POINTS ==="
  grep -RInE \
    'highlight|Highlight|shadow|Shadow|midtone|Midtone|tone.?map|Tone.?Map|dynamic.?range|HDR|hdr|exposureFusion|compress' \
    app/src/main/java/com/particlesdevs/photoncamera/processing \
    app/src/main/assets/shaders 2>/dev/null | head -n 1200 || true
  echo
  echo "=== LUMA CLEANUP / EDGE SUPPRESSION IMPLEMENTATION POINTS ==="
  grep -RInE \
    'luma|Luma|edge|Edge|denoise|Denoise|cleanup|Cleanup|sharpen|Sharpen' \
    app/src/main/java/com/particlesdevs/photoncamera/processing \
    app/src/main/assets/shaders 2>/dev/null | head -n 1200 || true
  echo
  echo "=== ISO / EXPOSURE / NOISE / SCENE METADATA ACCESS ==="
  grep -RInE \
    'sensitivity|SENSOR_SENSITIVITY|iso|ISO|exposureTime|EXPOSURE_TIME|analogGain|noiseModel|NoiseModel|totalGain|wellExposed|well_exposed' \
    app/src/main/java/com/particlesdevs/photoncamera/processing \
    app/src/main/java/com/particlesdevs/photoncamera/capture \
    2>/dev/null | head -n 1200 || true
  echo
  echo "=== CURRENT APPROVED UI IMPLEMENTATION MARKERS ==="
  grep -RInE \
    'LiquidModePicker|MODE_DISPLAY_ORDER|Motion|Portrait|Video|Exposure|Shutter|ISO|gallery_image_button|flip_camera_button' \
    app/src/main/java/com/particlesdevs/photoncamera/ui/camera \
    app/src/main/res/layout \
    2>/dev/null | head -n 1000 || true
  echo
  echo "=== RELEVANT SOURCE FILE CONTENTS ==="
  for file in \
    app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java \
    app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java \
    app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java \
    app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java \
    app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java \
    app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java \
    app/src/main/java/com/particlesdevs/photoncamera/processing/render/NoiseModeler.java \
    app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java \
    app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java \
    app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/modeswitcher/LiquidModePicker.java \
    app/src/main/res/layout/layout_modeswitcher.xml \
    app/src/main/res/layout/layout_bottombuttons.xml
  do
    if [[ -f "$file" ]]; then
      echo
      echo "----- $file -----"
      sed -n '1,420p' "$file"
    fi
  done
  echo
  echo "=== END AUDIT ==="
} | tee "$OUT"

echo
echo "Created visible Explorer file:"
echo "/workspaces/Photon-Camera/$OUT"
