#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

OUT="/workspaces/Photon-Camera/motion_26172_local_contribution_exact_context.txt"

{
    echo "=== REPOSITORY STATE ==="
    echo "Branch: $(git branch --show-current)"
    echo "HEAD:   $(git rev-parse HEAD)"
    grep '^VERSION_BUILD=' app/version.properties || true
    git status --short
    echo

    echo "=== REQUIRED CHECKPOINTS ==="
    grep -RIn \
        -E 'MOTION_26171_|MOTION_26168_MERGE_NOISE_AWARE|MOTION_26166_BLACK_LEVEL_SELECTED|MOTION_26166_IMAGE_SAVED_COMPLETE|MOTION_26165_HOMOGENEOUS_RAW_STACK' \
        app/src/main/java \
        app/src/main/assets/shaders \
        | head -6000
    echo

    echo "=== PYRAMID MERGING JAVA ==="
    sed -n '1,1400p' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts/PyramidMerging.java
    echo

    echo "=== MERGE SHADER ==="
    sed -n '1,1400p' \
        app/src/main/assets/shaders/merge/merge11.glsl
    echo

    echo "=== HDRX PROCESSOR ==="
    sed -n '1,1800p' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java
    echo

    echo "=== PARAMETERS ==="
    sed -n '1,1800p' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java
    echo

    echo "=== NOISE MODELER ==="
    sed -n '1,1800p' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/render/NoiseModeler.java
    echo

    echo "=== POST PIPELINE NOISE HANDOFF ==="
    sed -n '1,900p' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java
    echo

    echo "=== GL BASE PIPELINE / TEXTURES / IMAGE UTILITIES ==="
    for file in \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLBasePipeline.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLTexture.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLImage.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLUtils.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLProg.java; do
        echo
        echo "----- FILE: $file -----"
        sed -n '1,1800p' "$file"
    done
    echo

    echo "=== RAW SAVE AND JPEG INPUT ROUTING ==="
    grep -RIn -B35 -A90 \
        -E 'saveStackedRaw|saveSingleRaw|PostPipeline\.Run|pyramidMerging\.Output|PyramidMerging\.Output|output[[:space:]]*=|merged.*output|stacked.*raw' \
        app/src/main/java/com/particlesdevs/photoncamera \
        | head -12000
    echo

    echo "=== EFFECTIVE / RETAINED FRAME COUNT ROUTING ==="
    grep -RIn -B40 -A100 \
        -E 'effectiveFrameCount|retainedFrameCount|computeStackingNoiseModel|images\.size\(\)|frameCount|FrameCount|RetainedFrameCount' \
        app/src/main/java/com/particlesdevs/photoncamera \
        | head -14000
    echo

    echo "=== MERGE WEIGHTS / REJECTION / ALIGNMENT ROUTING ==="
    grep -RIn -B45 -A140 \
        -E 'weight|WEIGHT|running|average|reject|threshold|Wiener|wiener|baseFrame|base frame|FrameNumber|frameNumber|align|Alignment|difference|diff|confidence|contribution' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts/PyramidMerging.java \
        app/src/main/assets/shaders/merge/merge11.glsl \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts \
        | head -18000
    echo

    echo "=== EXISTING DEBUG IMAGE / BUFFER EXPORT PATHS ==="
    grep -RIn -B35 -A120 \
        -E 'SaveProgResult|save.*PNG|save.*png|Bitmap\.compress|GLImage|debugData|DebugData|diagnostic|confidence|heatmap|histogram|percentile' \
        app/src/main/java/com/particlesdevs/photoncamera \
        | head -16000
    echo

    echo "=== SHADER OUTPUT FORMATS AND AUXILIARY TARGETS ==="
    grep -RIn -B35 -A100 \
        -E 'drawBlocks|setTexture|setTextureCompute|Output|out vec|layout.*location|GLFormat|main1|main2|main3|main4|FusionMap|GainMap' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts/PyramidMerging.java \
        app/src/main/assets/shaders/merge/merge11.glsl \
        | head -14000
    echo

    echo "=== 26171 TUNABLE REGISTRY AND UI ==="
    sed -n '1,360p' \
        app/src/main/java/com/particlesdevs/photoncamera/settings/TunableRegistry.java
    echo

    grep -RIn -B12 -A24 \
        -E 'Motion Noise Tuning|motionResidualVarianceBoost|motionStableWeightBlendMaximum|motionLumaCleanupMaximum|motionChromaCleanupMaximum|motionHighIsoGainLimit' \
        app/src/main/java/com/particlesdevs/photoncamera \
        | head -6000
    echo

    echo "=== CURRENT DIFF SUMMARY ==="
    git diff --stat
    echo
    git diff --check || true
    echo

    echo "REPORT COMPLETE"
} | tee "$OUT"

echo
echo "============================================================"
echo " 26172 MERGE AUDIT COMPLETE"
echo "============================================================"
echo "Report: $OUT"
echo "No source files were modified."
