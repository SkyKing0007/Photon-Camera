#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

REPORT="/workspaces/Photon-Camera/motion_26166_blacklevel_save_exact_context.txt"

echo "============================================================"
echo " PhotonCamera 26166 black-level + save audit"
echo "============================================================"

{
    echo "=== REPOSITORY STATE ==="
    echo "Branch: $(git branch --show-current)"
    echo "HEAD:   $(git rev-parse HEAD)"
    grep '^VERSION_BUILD=' app/version.properties
    git status --short

    echo
    echo "=== PARAMETERS: DYNAMIC BLACK LEVEL PATH ==="
    grep -nE \
        'useDynamicBlackLevel|SENSOR_DYNAMIC_BLACK_LEVEL|SENSOR_BLACK_LEVEL_PATTERN|usedDynamic|blackLevel|FillDynamicParameters' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java
    echo
    sed -n '230,475p' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java

    echo
    echo "=== IMAGE FRAME DATA MODEL ==="
    sed -n '1,260p' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java

    echo
    echo "=== CAPTURE RESULT / RAW TIMESTAMP PAIRING ==="
    grep -nE -A45 -B30 \
        'onCaptureCompleted|TotalCaptureResult|SENSOR_TIMESTAMP|CONTROLLED_ACTUAL_EXPO_PAIR|mCaptureResult|mCaptureRequest|completedFrames|runRaw|ImageFrame' \
        app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java \
        | head -4200

    echo
    echo "=== DEFAULT SAVER RAW HANDOFF ==="
    sed -n '1,230p' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java

    echo
    echo "=== IMAGE SAVER RAW HANDOFF ==="
    grep -nE -A75 -B40 \
        'runRaw|HdrxProcessor|notifyImageSavedStatus|onFinished|onFailed|ImageSaved' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java \
        | head -1800

    echo
    echo "=== HDRX ENTRY, REFERENCE SELECTION, MERGE AND SAVE ==="
    grep -nE -A90 -B50 \
        'void start|captureResult|captureRequest|selected =|images.set|PyramidMerging|blackLevel|saveBitmapAsJPG|notifyImageSavedStatus|callback.onFinished|onProcessingFinished' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java \
        | head -3600

    echo
    echo "=== PYRAMID ALIGNMENT BLACK-LEVEL USE ==="
    grep -RIn -A90 -B50 \
        -E 'blackLevel|BLACKLEVEL|parameters\.blackLevel' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl \
        app/src/main/assets/shaders \
        | head -4200

    echo
    echo "=== IMAGE-SAVED CALLBACK IMPLEMENTATIONS ==="
    grep -RIn -A90 -B40 \
        -E 'notifyImageSavedStatus|ImageSaved:|onProcessingFinished|ProcessingEventsListener' \
        app/src/main/java/com/particlesdevs/photoncamera \
        | head -3600

    echo
    echo "=== APPLICATION LOG FILE WRITER / EXPORT ==="
    grep -RIn -A100 -B50 \
        -E 'logcat|Logcat|saveLog|writeLog|FileLogger|LogWriter|log-[0-9]|flush|BufferedWriter' \
        app/src/main/java/com/particlesdevs/photoncamera \
        | head -3600

    echo
    echo "=== CURRENT BUILD MARKERS ==="
    grep -RIn \
        -E 'MOTION_26165_HOMOGENEOUS_RAW_STACK|MOTION_COLOR_REFERENCE_METADATA|MOTION_PHOTON_ENERGY_POLICY|CONTROLLED_ACTUAL_EXPO_PAIR' \
        app/src/main/java/com/particlesdevs/photoncamera
} | tee "$REPORT"

echo
echo "============================================================"
echo " AUDIT COMPLETE"
echo "============================================================"
echo "Report: $REPORT"
echo
echo "Upload motion_26166_blacklevel_save_exact_context.txt here."
