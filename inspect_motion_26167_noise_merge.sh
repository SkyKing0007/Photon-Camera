#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

REPORT="/workspaces/Photon-Camera/motion_26167_noise_merge_exact_context.txt"

echo "============================================================"
echo " PhotonCamera 26167 Motion noise/merge audit"
echo "============================================================"

{
    echo "=== REPOSITORY STATE ==="
    echo "Branch: $(git branch --show-current)"
    echo "HEAD:   $(git rev-parse HEAD)"
    grep '^VERSION_BUILD=' app/version.properties
    git status --short --untracked-files=no

    echo
    echo "=== HDRX FRAME RETENTION, NOISE MODEL, MERGE AND POST PIPELINE ==="
    sed -n '100,590p' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java

    echo
    echo "=== PYRAMID MERGING COMPLETE SOURCE ==="
    sed -n '1,760p' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts/PyramidMerging.java

    echo
    echo "=== PYRAMID ALIGNMENT COMPLETE SOURCE ==="
    sed -n '1,760p' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts/PyramidAlignment.java

    echo
    echo "=== NOISE MODELER COMPLETE SOURCE ==="
    sed -n '1,620p' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/render/NoiseModeler.java

    echo
    echo "=== POST PIPELINE STAGE ORDER ==="
    sed -n '1,520p' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java

    echo
    echo "=== INITIAL STAGE CURRENT SOURCE ==="
    sed -n '1,620p' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java

    echo
    echo "=== DENOISE / ESD3D2 / SHARPEN / TONE CLASSES ==="
    grep -RIl \
        -E 'ESD3D2|esd3d2|Sharpen|sharpen|denoise|Denoise|tone|Tone|shadow|Shadow|Equalization|ExposureFusion' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts \
        | sort \
        | while IFS= read -r file; do
            echo
            echo "----- FILE: $file -----"
            sed -n '1,520p' "$file"
        done

    echo
    echo "=== MERGE SHADER FILE LIST ==="
    find app/src/main/assets/shaders -type f \
        | grep -E '/merge/|merge[0-9]|align|normalizebl' \
        | sort

    echo
    echo "=== MERGE / ALIGNMENT SHADER CONTENT ==="
    find app/src/main/assets/shaders -type f \
        | grep -E '/merge/|merge[0-9]|align|normalizebl' \
        | sort \
        | while IFS= read -r file; do
            echo
            echo "----- SHADER: $file -----"
            sed -n '1,420p' "$file"
        done

    echo
    echo "=== POST DENOISE / SHARPEN / TONE SHADER CONTENT ==="
    grep -RIl \
        -E 'ESD3D2|esd3d2|sharpen|denoise|noise|tone|shadow|equaliz|exposure' \
        app/src/main/assets/shaders \
        | grep -v '/merge/' \
        | sort \
        | while IFS= read -r file; do
            echo
            echo "----- SHADER: $file -----"
            sed -n '1,420p' "$file"
        done

    echo
    echo "=== CURRENT MOTION/NOISE BUILD MARKERS ==="
    grep -RIn \
        -E 'MOTION_26161_COLOR_RECOVERY|effectiveFrameCount|effectiveStackRatio|subpixelSampleDiversity|retainedFrameCount|computeStackingNoiseModel|enableAdaptiveNoise|noiseMpy|ESD3D2|sharpen|Sharpen|tone|shadow' \
        app/src/main/java/com/particlesdevs/photoncamera/processing \
        | head -5000

    echo
    echo "=== TUNABLE DEFINITIONS RELEVANT TO NOISE AND DETAIL ==="
    grep -RIn -B4 -A8 \
        -E '@Tunable.*(Noise|noise|Denoise|denoise|Sharpen|sharpen|Shadow|shadow|Tone|tone|Merge|merge|Chroma|chroma|Detail|detail)' \
        app/src/main/java/com/particlesdevs/photoncamera/processing \
        | head -5000

    echo
    echo "=== SETTINGS / TUNING PROPERTY LOCATIONS ==="
    find app -type f \
        | grep -E 'properties$|tuning|Tuning|specific|Specific' \
        | sort \
        | head -1000

    echo
    echo "=== DIFF SUMMARY ==="
    git diff --stat
} | tee "$REPORT"

echo
echo "============================================================"
echo " AUDIT COMPLETE"
echo "============================================================"
echo "Report: $REPORT"
echo
echo "Upload motion_26167_noise_merge_exact_context.txt here."
