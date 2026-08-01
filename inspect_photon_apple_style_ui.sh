#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="/workspaces/Photon-Camera/photon_ui_apple_reference_audit_${STAMP}"
REPORT="$OUT/photon_ui_apple_reference_exact_context.txt"
ARCHIVE="/workspaces/Photon-Camera/photon_ui_apple_reference_audit_${STAMP}.zip"

mkdir -p "$OUT/files"

echo "============================================================"
echo " Photon UI Apple-reference source audit"
echo "============================================================"
echo "No source files will be modified."
echo

{
    echo "=== REPOSITORY STATE ==="
    echo "Branch: $(git branch --show-current)"
    echo "HEAD:   $(git rev-parse HEAD)"
    grep '^VERSION_BUILD=' app/version.properties || true
    echo
    git status --short
    echo

    echo "=== CAMERA UI SOURCE CANDIDATES ==="
    find app/src/main \
        -type f \
        \( \
            -iname '*camera*' -o \
            -iname '*viewfinder*' -o \
            -iname '*preview*' -o \
            -iname '*shutter*' -o \
            -iname '*mode*' -o \
            -iname '*zoom*' -o \
            -iname '*lens*' \
        \) \
        | sort
    echo

    echo "=== LAYOUTS AND IDS USED BY CAMERA SCREEN ==="
    grep -RIn -E \
        'TextureView|SurfaceView|PreviewView|camera_preview|viewfinder|shutter|captureButton|camera_switch|switch_camera|mode_selector|camera_mode|zoom|lens|flash|timer|settings|gallery|thumbnail|hdr|motion|night' \
        app/src/main/res/layout \
        app/src/main/res/xml \
        app/src/main/res/values \
        2>/dev/null \
        | head -12000 || true
    echo

    echo "=== CAMERA UI JAVA/KOTLIN REFERENCES ==="
    grep -RIn -E \
        'CameraUIViewImpl|CameraFragment|CameraActivity|TextureView|SurfaceView|PreviewView|shutter|captureButton|switchCamera|cameraSwitch|modeSelector|selectedMode|CameraMode|zoom|lens|flash|timer|settings|thumbnail|gallery|onTouch|GestureDetector|WindowInsets|systemUiVisibility' \
        app/src/main/java \
        2>/dev/null \
        | head -18000 || true
    echo

    echo "=== CAMERA VIEW IMPLEMENTATION ==="
    for file in \
        app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java \
        app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIView.java \
        app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIEvents.java \
        app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java \
        app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraActivity.java; do
        if [ -f "$file" ]; then
            echo
            echo "----- FILE: $file -----"
            nl -ba "$file"
        fi
    done
    echo

    echo "=== CAMERA LAYOUT FILES ==="
    for file in \
        app/src/main/res/layout/fragment_camera.xml \
        app/src/main/res/layout/camera_fragment.xml \
        app/src/main/res/layout/activity_camera.xml \
        app/src/main/res/layout/camera_ui.xml \
        app/src/main/res/layout/view_camera.xml \
        app/src/main/res/layout/camera_controls.xml; do
        if [ -f "$file" ]; then
            echo
            echo "----- FILE: $file -----"
            nl -ba "$file"
        fi
    done
    echo

    echo "=== ALL LAYOUT FILES REFERENCING CORE CAMERA CONTROLS ==="
    while IFS= read -r file; do
        echo
        echo "----- FILE: $file -----"
        nl -ba "$file"
    done < <(
        grep -RIl -E \
            'shutter|captureButton|camera_switch|switch_camera|TextureView|SurfaceView|PreviewView|mode_selector|zoom|lens' \
            app/src/main/res/layout \
            2>/dev/null \
            | sort -u
    )
    echo

    echo "=== DRAWABLES USED BY CAMERA CONTROLS ==="
    grep -RIn -E \
        '@drawable/|setImageResource|setBackgroundResource|R\.drawable\.' \
        app/src/main/res/layout \
        app/src/main/java/com/particlesdevs/photoncamera/ui \
        2>/dev/null \
        | grep -E \
            'camera|shutter|capture|switch|flash|timer|settings|gallery|thumbnail|zoom|lens|mode|hdr|motion|night' \
        | head -12000 || true
    echo

    echo "=== THEMES, COLORS, DIMENSIONS AND STYLES ==="
    for file in \
        app/src/main/res/values/colors.xml \
        app/src/main/res/values/dimens.xml \
        app/src/main/res/values/styles.xml \
        app/src/main/res/values/themes.xml \
        app/src/main/res/values-night/colors.xml \
        app/src/main/res/values-night/themes.xml; do
        if [ -f "$file" ]; then
            echo
            echo "----- FILE: $file -----"
            nl -ba "$file"
        fi
    done
    echo

    echo "=== MODE AND LENS CONTROL IMPLEMENTATIONS ==="
    grep -RIl -E \
        'CameraMode|selectedMode|mode_selector|setMode|zoom|lens|cameraId|mCameraID|switchCamera|cameraSwitch' \
        app/src/main/java/com/particlesdevs/photoncamera/ui \
        app/src/main/java/com/particlesdevs/photoncamera/control \
        2>/dev/null \
        | sort -u \
        | while IFS= read -r file; do
            echo
            echo "----- FILE: $file -----"
            nl -ba "$file"
        done
    echo

    echo "=== ORIENTATION, INSETS AND FULLSCREEN HANDLING ==="
    grep -RIn -B20 -A60 -E \
        'WindowInsets|SYSTEM_UI_FLAG|FLAG_LAYOUT_NO_LIMITS|setDecorFitsSystemWindows|statusBarColor|navigationBarColor|rotation|orientation|displayCutout|fitsSystemWindows' \
        app/src/main/java \
        app/src/main/res \
        2>/dev/null \
        | head -14000 || true
    echo

    echo "=== CURRENT CAMERA UI TUNABLES ==="
    grep -RIn -B15 -A30 -E \
        '@Tunable|Camera UI|CameraUIViewImpl|Viewfinder|Shutter|Mode selector|Zoom|Lens' \
        app/src/main/java/com/particlesdevs/photoncamera/ui \
        app/src/main/java/com/particlesdevs/photoncamera/settings/TunableRegistry.java \
        2>/dev/null \
        | head -10000 || true
    echo

    echo "=== BUILD SYSTEM / VIEW BINDING ==="
    grep -RIn -E \
        'viewBinding|dataBinding|compose|androidx\.compose|material|constraintlayout' \
        app/build.gradle* \
        build.gradle* \
        gradle/libs.versions.toml \
        2>/dev/null || true
    echo

    echo "=== CURRENT DIFF SUMMARY ==="
    git diff --stat
    echo
    git diff --check || true
    echo

    echo "REPORT COMPLETE"
} > "$REPORT"

echo "Collecting directly relevant source files..."

find app/src/main \
    -type f \
    \( \
        -path '*/ui/camera/*' -o \
        -path '*/res/layout/*camera*' -o \
        -path '*/res/layout/*capture*' -o \
        -path '*/res/layout/*viewfinder*' -o \
        -path '*/res/drawable/*camera*' -o \
        -path '*/res/drawable/*shutter*' -o \
        -path '*/res/drawable/*capture*' -o \
        -path '*/res/drawable/*switch*' -o \
        -path '*/res/drawable/*flash*' -o \
        -path '*/res/drawable/*timer*' -o \
        -path '*/res/drawable/*zoom*' -o \
        -path '*/res/drawable/*lens*' -o \
        -path '*/res/values/colors.xml' -o \
        -path '*/res/values/dimens.xml' -o \
        -path '*/res/values/styles.xml' -o \
        -path '*/res/values/themes.xml' \
    \) \
    -print0 \
    | while IFS= read -r -d '' file; do
        mkdir -p "$OUT/files/$(dirname "$file")"
        cp "$file" "$OUT/files/$file"
    done

cp app/version.properties "$OUT/files/app/version.properties"

(
    cd /workspaces/Photon-Camera
    zip -qr "$ARCHIVE" "$(basename "$OUT")"
)

echo
echo "============================================================"
echo " UI AUDIT COMPLETE"
echo "============================================================"
echo "Report:  $REPORT"
echo "Archive: $ARCHIVE"
echo "No source files were modified."
