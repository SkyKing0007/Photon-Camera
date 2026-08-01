#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

OUT="/workspaces/Photon-Camera/motion_26171_failed_build_exact_state.txt"

{
    echo "=== CURRENT STATE AFTER FAILED 26171 SCRIPT ==="
    echo "Branch: $(git branch --show-current)"
    echo "HEAD:   $(git rev-parse HEAD)"
    grep '^VERSION_BUILD=' app/version.properties || true
    echo

    echo "=== TRACKED STATUS ==="
    git status --short --untracked-files=no
    echo

    echo "=== BACKUP BRANCH ==="
    git branch --list 'backup-before-motion-noise-tuning-26171-*'
    echo

    echo "=== 26171 MARKER COUNTS ==="
    for marker in \
        MOTION_26171_ESD3D2_TUNABLE \
        MOTION_26171_LUMA_TUNABLE \
        MOTION_26171_CHROMA_TUNABLE \
        MOTION_26171_TONE_TUNABLE \
        MOTION_26171_CAPTURE_SHARPEN_TUNABLE \
        MOTION_26171_FINAL_SHARPEN_TUNABLE \
        MOTION_26170_ESD3D2_STABLE_WEIGHTS \
        MOTION_26170_LUMA_WORM_CLEANUP \
        MOTION_26170_CHROMA_COARSE \
        MOTION_26170_TONE_GAIN_GUARD \
        MOTION_26170_CAPTURE_SHARPEN \
        MOTION_26170_FINAL_SHARPEN; do
        count="$(grep -Roh "$marker" \
            app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline \
            app/src/main/assets/shaders/denoise \
            2>/dev/null | wc -l)"
        echo "$marker=$count"
    done
    echo

    echo "=== RELEVANT FIELD COUNTS ==="
    for token in \
        motionResidualVarianceBoost \
        motionLumaEdgeBlendMaximum \
        motionStableWeightBlendMaximum \
        motionShadowBoostMaximum \
        motionLumaCleanupMaximum \
        motionChromaCleanupMaximum \
        motionHighIsoGainLimit \
        motionCaptureSharpeningFloor \
        motionFinalSharpeningFloor; do
        count="$(grep -Roh "$token" \
            app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline \
            2>/dev/null | wc -l)"
        echo "$token=$count"
    done
    echo

    echo "=== EXACT PARTIAL DIFF ==="
    git diff -- \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/AutoExposure.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java \
        app/src/main/java/com/particlesdevs/photoncamera/settings/TunableRegistry.java \
        app/src/main/assets/shaders/denoise/motionchromadenoise.glsl \
        app/version.properties
    echo

    echo "=== LUMA MARKER LOCATIONS ==="
    grep -n -B4 -A8 'MOTION_26170_LUMA_WORM_CLEANUP' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java \
        || true
    echo

    echo "=== POSTPIPELINE 26171 CONTEXT ==="
    grep -n -B15 -A35 \
        -E 'motionResidualVarianceBoost|MOTION_26168_RESIDUAL_NOISE_EFFECTIVE' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java \
        || true
    echo

    echo "=== ESD3D2 26171 CONTEXT ==="
    grep -n -B15 -A55 \
        -E 'motionLumaEdgeBlendMaximum|motionStableWeightBlendMaximum|motionShadowBoostMaximum|MOTION_26171_ESD3D2_TUNABLE|MOTION_26170_ESD3D2_STABLE_WEIGHTS' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java \
        || true
    echo

    echo "=== VERSION AND REGISTRY CONTEXT ==="
    grep -n '^VERSION_BUILD=' app/version.properties || true
    grep -n -B4 -A10 \
        -E 'MotionLumaDenoise.class|MotionChromaDenoise.class|CaptureSharpening.class' \
        app/src/main/java/com/particlesdevs/photoncamera/settings/TunableRegistry.java \
        || true
    echo

    echo "REPORT COMPLETE"
} | tee "$OUT"

echo
echo "============================================================"
echo " FAILED-BUILD INSPECTION COMPLETE"
echo "============================================================"
echo "Report: $OUT"
echo "No source files were modified."
