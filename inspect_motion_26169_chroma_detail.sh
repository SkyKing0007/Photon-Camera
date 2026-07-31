#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

OUT="/workspaces/Photon-Camera/motion_26169_chroma_detail_exact_context.txt"

{
    echo "=== REPOSITORY STATE ==="
    echo "Branch: $(git branch --show-current)"
    echo "HEAD:   $(git rev-parse HEAD)"
    grep '^VERSION_BUILD=' app/version.properties || true
    git status --short --untracked-files=no
    echo

    echo "=== REQUIRED 26168 MARKERS ==="
    grep -RIn \
        'MOTION_26168_MERGE_NOISE_AWARE\|MOTION_26168_RESIDUAL_NOISE_EFFECTIVE\|MOTION_26168_ESD3D2_PROFILE\|MOTION_26168_TONE_GAIN_GUARD\|MOTIONNOISEBLEND\|predictedNoiseCap' \
        app/src/main/java \
        app/src/main/assets/shaders \
        || true
    echo

    echo "=== CURRENT POST PIPELINE ORDER ==="
    sed -n '1,280p' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java
    echo

    echo "=== CURRENT ESD3D2 JAVA ==="
    cat \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java
    echo

    echo "=== CURRENT ESD3D2 SHADER ==="
    cat app/src/main/assets/shaders/denoise/esd3d2.glsl
    echo

    echo "=== GUIDED UPSAMPLE SHADER ==="
    if [ -f app/src/main/assets/shaders/denoise/guidedupsample.glsl ]; then
        cat app/src/main/assets/shaders/denoise/guidedupsample.glsl
    else
        find app/src/main/assets/shaders -type f \
            -iname '*guided*' -o -iname '*upsample*' | sort
    fi
    echo

    echo "=== DEMOSAIC3 JAVA AND SHADERS ==="
    cat \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Demosaic3.java \
        2>/dev/null || true
    find app/src/main/assets/shaders -type f \
        \( -iname '*demosaic3*' -o -path '*/demosaic/*' \) \
        -print -exec sh -c 'echo "--- $1"; sed -n "1,260p" "$1"' _ {} \;
    echo

    echo "=== EXISTING CHROMA / COLOR DENOISE JAVA ==="
    find \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline \
        -maxdepth 1 -type f \
        \( -iname '*chroma*' -o -iname '*bilateral*' -o -iname '*denoise*' \) \
        -print -exec sh -c 'echo "--- $1"; cat "$1"' _ {} \;
    echo

    echo "=== EXISTING CHROMA / COLOR DENOISE SHADERS ==="
    find app/src/main/assets/shaders -type f \
        \( -iname '*chroma*' -o -iname '*bilateral*' -o -iname '*color*denoise*' \) \
        -print -exec sh -c 'echo "--- $1"; sed -n "1,320p" "$1"' _ {} \;
    echo

    echo "=== CHROMATIC FLOW SOURCE AND SHADERS ==="
    find \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline \
        app/src/main/assets/shaders \
        -type f \
        \( -iname '*chromatic*' -o -iname '*colorflow*' \) \
        -print -exec sh -c 'echo "--- $1"; sed -n "1,340p" "$1"' _ {} \;
    echo

    echo "=== NODE / PIPELINE TEXTURE OWNERSHIP ==="
    sed -n '1,360p' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/nodes/Node.java
    echo
    grep -RIn \
        'GLTexture getMain\|swap3\|main1\|main2\|main3\|main4\|runAll' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl \
        | sed -n '1,420p'
    echo

    echo "=== GLUTILS DOWNSAMPLE / BLUR / UPSAMPLE METHODS ==="
    grep -nE \
        'gaussdown|medianDown|interpolate|guided|blur|ConvDiff|convertVec4' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLUtils.java \
        | sed -n '1,260p'
    sed -n '1,520p' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLUtils.java
    echo

    echo "=== INITIAL / AUTOEXPOSURE CURRENT CONTEXT ==="
    sed -n '1,420p' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java
    echo
    cat \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/AutoExposure.java
    echo

    echo "=== CURRENT 26168 DIFF FOR RELEVANT FILES ==="
    git diff HEAD -- \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java \
        app/src/main/assets/shaders/denoise/esd3d2.glsl \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts/PyramidMerging.java \
        app/src/main/assets/shaders/merge/merge11.glsl \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/AutoExposure.java \
        app/version.properties
    echo

    echo "=== VIDEO / RAW VIDEO ISOLATION REFERENCES ==="
    grep -RIn \
        'CameraMode.RAWVIDEO\|TEMPLATE_RECORD\|mIsRecordingVideo\|MediaRecorder' \
        app/src/main/java/com/particlesdevs/photoncamera \
        | sed -n '1,260p'
} > "$OUT"

echo "AUDIT COMPLETE"
echo "$OUT"
echo "No source files were modified."
