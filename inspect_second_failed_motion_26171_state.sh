#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

OUT="/workspaces/Photon-Camera/motion_26171_second_failure_exact_state.txt"

{
    echo "=== CURRENT STATE AFTER SECOND 26171 FAILURE ==="
    echo "Branch: $(git branch --show-current)"
    echo "HEAD:   $(git rev-parse HEAD)"
    grep '^VERSION_BUILD=' app/version.properties || true
    echo

    echo "=== TRACKED STATUS ==="
    git status --short --untracked-files=no
    echo

    echo "=== 26171 BACKUP BRANCHES ==="
    git branch --list 'backup-before-motion-noise-tuning-26171*'
    echo

    echo "=== RELEVANT MARKER COUNTS ==="
    markers=(
        MOTION_26171_ESD3D2_TUNABLE
        MOTION_26171_LUMA_TUNABLE
        MOTION_26171_CHROMA_TUNABLE
        MOTION_26171_TONE_TUNABLE
        MOTION_26171_CAPTURE_SHARPEN_TUNABLE
        MOTION_26171_FINAL_SHARPEN_TUNABLE
        MOTION_26170_ESD3D2_STABLE_WEIGHTS
        MOTION_26170_LUMA_WORM_CLEANUP
        MOTION_26170_CHROMA_COARSE
        MOTION_26170_TONE_GAIN_GUARD
        MOTION_26170_CAPTURE_SHARPEN
        MOTION_26170_FINAL_SHARPEN
    )

    for marker in "${markers[@]}"; do
        count="$(
            grep -Roh "$marker" \
                app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline \
                app/src/main/assets/shaders/denoise \
                2>/dev/null \
                | wc -l \
                || true
        )"
        echo "$marker=$count"
    done
    echo

    echo "=== RELEVANT FIELD COUNTS ==="
    fields=(
        motionResidualVarianceBoost
        motionLumaEdgeBlendMaximum
        motionStableWeightBlendMaximum
        motionShadowBoostMaximum
        motionLumaCleanupEnable
        motionLumaCleanupMaximum
        motionLumaNoiseGain
        motionLumaKernelRadius
        motionChromaCleanupEnable
        motionChromaCleanupMaximum
        motionChromaRadiusPixels
        motionChromaGuideSigmaMaximum
        motionShadowNeutralization
        motionHighIsoGainLimit
        motionCaptureSharpeningFloor
        motionFinalSharpeningFloor
    )

    for field in "${fields[@]}"; do
        count="$(
            grep -Roh "$field" \
                app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline \
                2>/dev/null \
                | wc -l \
                || true
        )"
        echo "$field=$count"
    done
    echo

    echo "=== SHARPEN2 EXACT SOURCE ==="
    sed -n '1,280p' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java
    echo

    echo "=== CAPTURE SHARPENING EXACT SOURCE ==="
    sed -n '1,260p' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java
    echo

    echo "=== CURRENT PARTIAL DIFF FOR 26171 TARGET FILES ==="
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

    echo "=== VERSION AND REGISTRY ==="
    grep -n '^VERSION_BUILD=' app/version.properties || true
    grep -n -B6 -A16 \
        -E 'CaptureSharpening.class|MotionLumaDenoise.class|MotionChromaDenoise.class|Sharpen2.class|PostPipeline.class' \
        app/src/main/java/com/particlesdevs/photoncamera/settings/TunableRegistry.java \
        || true
    echo

    echo "=== FAILED RUN SAVED CLEAN COPIES ==="
    find \
        /workspaces/Photon-Camera/build_26171_motion_noise_tuning_resume_20260731_052307/source_before \
        -maxdepth 1 -type f -printf '%f\n' 2>/dev/null | sort || true
    echo

    echo "REPORT COMPLETE"
} | tee "$OUT"

echo
echo "============================================================"
echo " SECOND-FAILURE INSPECTION COMPLETE"
echo "============================================================"
echo "Report: $OUT"
echo "No source files were modified."
