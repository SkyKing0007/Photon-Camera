#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_COMMIT="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
EXPECTED_BUILD="26157"

REPORT="/workspaces/Photon-Camera/motion_temporal_noise_exact_context.txt"

fail() {
    echo
    echo "REPORT FAILED"
    echo "Reason: $1"
    exit 1
}

echo "============================================================"
echo " PhotonCamera Motion temporal/noise source audit"
echo "============================================================"

CURRENT_BRANCH="$(git branch --show-current)"
CURRENT_COMMIT="$(git rev-parse HEAD)"

[ "$CURRENT_BRANCH" = "$EXPECTED_BRANCH" ] \
    || fail "Expected branch $EXPECTED_BRANCH, found $CURRENT_BRANCH"

[ "$CURRENT_COMMIT" = "$EXPECTED_COMMIT" ] \
    || fail "Expected commit $EXPECTED_COMMIT, found $CURRENT_COMMIT"

grep -q "^VERSION_BUILD=${EXPECTED_BUILD}$" app/version.properties \
    || fail "Expected VERSION_BUILD=${EXPECTED_BUILD}"

{
    echo "=== VERSION ==="
    git branch --show-current
    git rev-parse HEAD
    grep '^VERSION_BUILD=' app/version.properties

    echo
    echo "=== HDRX PROCESSOR ENTRY AND FRAME RETENTION ==="
    grep -RIn -A180 -B80 -E \
        'class HdrxProcessor|retainedFrameCount|IMAGE_BUFFER|slicedBuffer|frameCount|start\(' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/processor \
        app/src/main/java/com/particlesdevs/photoncamera/processing \
        | head -2600

    echo
    echo "=== ALIGNMENT AND WHOLE-FRAME REJECTION ==="
    grep -RIn -A220 -B100 -E \
        'align|Alignment|reject|rejected|remove|prune|sharpness|motion|gyro|homography|optical|confidence|robust' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/processor \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl \
        app/src/main/java/com/particlesdevs/photoncamera/processing/render \
        | head -4200

    echo
    echo "=== PYRAMID MERGE / TEMPORAL WEIGHTING JAVA ==="
    grep -RIn -A260 -B120 -E \
        'PyramidMerging|Merge|merge|weight|weights|temporal|robust|reference|baseFrame|layerMpy|exposure' \
        app/src/main/java/com/particlesdevs/photoncamera/processing \
        | head -5200

    echo
    echo "=== PYRAMID MERGE / TEMPORAL WEIGHTING SHADERS ==="
    grep -RIn -A220 -B100 -E \
        'weight|weights|robust|merge|temporal|reference|noise|sigma|variance|motion|alignment|exposure' \
        app/src/main/assets/shaders \
        app/src/main/res/raw \
        2>/dev/null \
        | head -6200

    echo
    echo "=== NOISE MODEL CONSTRUCTION AND USE ==="
    grep -RIn -A240 -B120 -E \
        'NoiseModeler|noiseModeler|SENSOR_NOISE_PROFILE|noiseS|noiseO|NOISES|NOISEO|analogIso|retainedFrameCount|frameCount' \
        app/src/main/java/com/particlesdevs/photoncamera \
        | head -5200

    echo
    echo "=== ACTIVE DENOISE STAGES ==="
    grep -RIn -A260 -B120 -E \
        'esd3d2|guidedupsample|KERNELSIZE|MSIZE|SCALE|LUMA|MOIRE|noiseS|noiseO' \
        app/src/main/java/com/particlesdevs/photoncamera \
        app/src/main/assets/shaders \
        2>/dev/null \
        | head -5200

    echo
    echo "=== TONE, AUTO EXPOSURE, HIGHLIGHT LIFT ==="
    grep -RIn -A260 -B120 -E \
        'AutoExposure|Histogram already full|base Mpy|Average brightness multiplier|exposureFusion|tonemap|highlight|whitePoint|whiteLevel|clip|clipped|histogram' \
        app/src/main/java/com/particlesdevs/photoncamera \
        app/src/main/assets/shaders \
        2>/dev/null \
        | head -5200

    echo
    echo "=== MOTION ACTUAL METADATA HANDOFF ==="
    grep -n -A340 -B160 -E \
        'CONTROLLED_ACTUAL_EXPO_PAIR|COMBINED_EXPOSURE_MAP_READY|runRaw\(|mCaptureResult|mMotionBurstExposureTimeNs|mMotionBurstSensitivity' \
        app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java \
        | head -3200

    echo
    echo "=== CURRENT TUNABLE VALUES / DEFAULTS ==="
    grep -RIn -A140 -B60 -E \
        '@Tunable|ESD3D2|Guided|Denoise|Sharpen|Noise|Temporal|Merge|Robust|Highlight|Tone' \
        app/src/main/java/com/particlesdevs/photoncamera \
        | head -5200

    echo
    echo "REPORT COMPLETE"
} | tee "$REPORT"

echo
echo "============================================================"
echo " REPORT COMPLETE"
echo "============================================================"
echo "Report: $REPORT"
echo "No source files were modified."
