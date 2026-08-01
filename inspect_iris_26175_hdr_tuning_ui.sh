#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="/workspaces/Photon-Camera/iris_26175_hdr_tuning_audit_${STAMP}"
REPORT="$OUT/iris_26175_hdr_tuning_exact_context.txt"
ARCHIVE="/workspaces/Photon-Camera/iris_26175_hdr_tuning_audit_${STAMP}.zip"

mkdir -p "$OUT/files"

echo "============================================================"
echo " Iris Camera 26175 HDR/tone/detail source audit"
echo "============================================================"
echo "No source files will be modified."
echo

{
    echo "=== REPOSITORY STATE ==="
    echo "Branch: $(git branch --show-current)"
    echo "HEAD:   $(git rev-parse HEAD)"
    grep '^VERSION_BUILD=' app/version.properties || true
    grep -nE "applicationId|namespace" app/build.gradle || true
    grep -n 'name="app_name"' app/src/main/res/values/strings.xml || true
    echo
    git status --short
    echo

    echo "=== MOTION MERGE AND EFFECTIVE-STACK PATH ==="
    grep -RIn -B35 -A100 -E \
        'MOTION_26172_LOCAL_CONTRIBUTION|motionNoiseDifferenceRecovery|motionNoiseRecoveryGate|motionEffectiveStackPercentile|effectiveFrame|contributionTexture|motionmerge11|computeStackingNoiseModel' \
        app/src/main/java/com/particlesdevs/photoncamera/processing \
        app/src/main/assets/shaders/merge \
        | head -18000 || true
    echo

    echo "=== TONE, SHADOW AND HIGHLIGHT PIPELINE ==="
    grep -RIn -B45 -A140 -E \
        'shadow|Shadow|highlight|Highlight|tone|Tone|gamma|Gamma|exposure|Exposure|curve|Curve|compress|Compress|blackLevel|whiteLevel|dynamic range|histogram|Hist|equaliz|GainMap|gainMap|local contrast|contrast' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts \
        app/src/main/java/com/particlesdevs/photoncamera/processing/render \
        app/src/main/assets/shaders \
        | head -26000 || true
    echo

    echo "=== DENOISE, DETAIL AND SHARPENING PIPELINE ==="
    grep -RIn -B45 -A140 -E \
        'denoise|Denoise|ESD3D2|luma|Luma|chroma|Chroma|sharpen|Sharpen|detail|Detail|edge|Edge|noise|Noise|radius|sigma|variance|floor|cleanup|stableWeight|shadowNeutral' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts \
        app/src/main/assets/shaders \
        | head -30000 || true
    echo

    echo "=== EXACT POSTPIPELINE AND REGISTERED NODES ==="
    for file in \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java \
        app/src/main/java/com/particlesdevs/photoncamera/settings/TunableRegistry.java; do
        if [ -f "$file" ]; then
            echo
            echo "----- FILE: $file -----"
            nl -ba "$file"
        fi
    done
    echo

    echo "=== CURRENT TUNABLE DEFINITIONS AND DEFAULTS ==="
    grep -RIn -B25 -A80 -E \
        '@Tunable|motion.*shadow|motion.*highlight|motion.*tone|motion.*luma|motion.*chroma|motion.*sharpen|residualVariance|cleanup|max|radius|sigma|floor' \
        app/src/main/java/com/particlesdevs/photoncamera \
        | head -22000 || true
    echo

    echo "=== AUTO EXPOSURE / HDR CAPTURE POLICY ==="
    grep -RIn -B45 -A150 -E \
        'IsoExpoSelector|desiredExposure|exposureEnergy|highlight|clipping|histogram|target|EV|meter|CONTROL_AE|SENSOR_EXPOSURE_TIME|SENSOR_SENSITIVITY|Motion' \
        app/src/main/java/com/particlesdevs/photoncamera/capture \
        app/src/main/java/com/particlesdevs/photoncamera/control \
        app/src/main/java/com/particlesdevs/photoncamera/processing \
        | head -26000 || true
    echo

    echo "=== APPROVED UI IMPLEMENTATION ==="
    for file in \
        app/src/main/res/layout/camera_fragment.xml \
        app/src/main/res/layout/layout_main_bottombar.xml \
        app/src/main/res/layout/layout_bottombuttons.xml \
        app/src/main/res/layout/layout_modeswitcher.xml \
        app/src/main/res/layout/layout_main_topbar.xml \
        app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java \
        app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java \
        app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/modeswitcher/LiquidModePicker.java \
        app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/settingsbar/SettingsBarLayout.java; do
        if [ -f "$file" ]; then
            echo
            echo "----- FILE: $file -----"
            nl -ba "$file"
        fi
    done
    echo

    echo "=== MODE ENUM, ORDER AND MANUAL CONTROL WIRING ==="
    grep -RIn -B35 -A120 -E \
        'enum CameraMode|nameIds|MOTION|VIDEO|PHOTO|NIGHT|UNLIMITED|RAW_VIDEO|manual_controls_button|manual|exposure|shutter|iso|mode_picker_view|setSelectedItem|OnItemSelected' \
        app/src/main/java/com/particlesdevs/photoncamera/ui \
        app/src/main/java/com/particlesdevs/photoncamera/settings \
        app/src/main/res/layout \
        | head -22000 || true
    echo

    echo "=== BRANDING AND LAUNCHER ICON RESOURCES ==="
    grep -RIn -E \
        'PhotonCamera|Iris Camera|com.skyyking.iriscam|applicationId|android:icon|roundIcon|mipmap|adaptive-icon' \
        app/build.gradle \
        app/src/main/AndroidManifest.xml \
        app/src/main/res/values \
        app/src/main/res/mipmap* \
        app/src/main/res/drawable* \
        2>/dev/null | head -12000 || true
    echo

    echo "=== CURRENT DIFF SUMMARY ==="
    git diff --stat
    echo
    git diff --check || true
    echo
    echo "REPORT COMPLETE"
} > "$REPORT"

echo "Collecting exact relevant source files..."

for file in \
    app/version.properties \
    app/build.gradle \
    app/src/main/AndroidManifest.xml \
    app/src/main/res/values/strings.xml \
    app/src/main/res/layout/camera_fragment.xml \
    app/src/main/res/layout/layout_main_bottombar.xml \
    app/src/main/res/layout/layout_bottombuttons.xml \
    app/src/main/res/layout/layout_modeswitcher.xml \
    app/src/main/res/layout/layout_main_topbar.xml \
    app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java \
    app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java \
    app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/modeswitcher/LiquidModePicker.java \
    app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/settingsbar/SettingsBarLayout.java \
    app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java \
    app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java \
    app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java \
    app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java \
    app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java \
    app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts/PyramidMerging.java \
    app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java \
    app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java \
    app/src/main/java/com/particlesdevs/photoncamera/processing/render/NoiseModeler.java \
    app/src/main/java/com/particlesdevs/photoncamera/settings/TunableRegistry.java; do
    if [ -f "$file" ]; then
        mkdir -p "$OUT/files/$(dirname "$file")"
        cp "$file" "$OUT/files/$file"
    fi
done

find app/src/main/assets/shaders -type f \
    \( -iname '*tone*' -o -iname '*equal*' -o -iname '*shadow*' -o -iname '*highlight*' -o -iname '*esd*' -o -iname '*denoise*' -o -iname '*sharpen*' -o -iname '*merge11*' \) \
    -print0 | while IFS= read -r -d '' file; do
        mkdir -p "$OUT/files/$(dirname "$file")"
        cp "$file" "$OUT/files/$file"
    done

find app/src/main/res -type f \
    \( -path '*/mipmap*/*' -o -iname '*launcher*' -o -iname '*iris*' \) \
    -print0 | while IFS= read -r -d '' file; do
        mkdir -p "$OUT/files/$(dirname "$file")"
        cp "$file" "$OUT/files/$file"
    done

(
    cd /workspaces/Photon-Camera
    zip -qr "$ARCHIVE" "$(basename "$OUT")"
)

echo
echo "============================================================"
echo " HDR/TUNING AUDIT COMPLETE"
echo "============================================================"
echo "Report:  $REPORT"
echo "Archive: $ARCHIVE"
echo "No source files were modified."
