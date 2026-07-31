#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

REPORT="/workspaces/Photon-Camera/motion_26160_color_path_exact_context.txt"

{
  echo "=== CHECKPOINT ==="
  echo "Branch: $(git branch --show-current)"
  echo "Commit: $(git rev-parse HEAD)"
  grep '^VERSION_BUILD=' app/version.properties
  echo

  echo "=== TRACKED STATUS ==="
  git status --short --untracked-files=no
  echo

  echo "=== PARAMETERS COLOR PATH ==="
  nl -ba app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java |
    sed -n '200,620p'
  echo

  echo "=== COLOR CORRECTION TRANSFORM ==="
  nl -ba app/src/main/java/com/particlesdevs/photoncamera/processing/render/ColorCorrectionTransform.java
  echo

  echo "=== BAYER TO FLOAT ==="
  nl -ba app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Bayer2Float.java
  echo

  echo "=== EXPOSURE FUSION BAYER ==="
  nl -ba app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ExposureFusionBayer2.java
  echo

  echo "=== DEMOSAIC3 JAVA ==="
  nl -ba app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Demosaic3.java
  echo

  echo "=== INITIAL COLOR NODE ==="
  nl -ba app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java
  echo

  echo "=== RELEVANT COLOR SHADERS ==="
  for file in \
    app/src/main/assets/shaders/merge/merge00.glsl \
    app/src/main/assets/shaders/merge/merge2o.glsl \
    app/src/main/assets/shaders/bayer2float.glsl \
    app/src/main/assets/shaders/demosaic/demosaic3.glsl \
    app/src/main/assets/shaders/initial.glsl \
    app/src/main/assets/shaders/initial2.glsl \
    app/src/main/assets/shaders/exposurefusionbayer2.glsl; do
    if [ -f "$file" ]; then
      echo
      echo "----- $file -----"
      nl -ba "$file"
    fi
  done
  echo

  echo "=== CFA / ANALOG BALANCE / GAIN MAP REFERENCES ==="
  grep -RIn -A20 -B20 -E \
    'cfaPattern|CFAPATTERN|analogBalance|whitePoint|gainMap|GainMap|sensorToProPhoto|ColorMatrix|ForwardTransform|calibrationTransform' \
    app/src/main/java/com/particlesdevs/photoncamera/processing \
    app/src/main/assets/shaders \
    | head -5000
  echo

  echo "=== COLOR PATH CONTEXT COMPLETE ==="
} | tee "$REPORT"
