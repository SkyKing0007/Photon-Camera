#!/usr/bin/env bash
set -euo pipefail

ROOT=/workspaces/Photon-Camera
cd "$ROOT"

fail() {
  printf '\nERROR: %s\n' "$*" >&2
  exit 1
}

echo "=== PHOTON CAMERA 0.9726177 / BUILD 26177 ==="

[[ "$(git branch --show-current)" == "experimental-effective-stack" ]] \
  || fail "Expected branch experimental-effective-stack"

[[ "$(git rev-parse HEAD)" == "cedc3ab3e39ad49d42523cff7e3711f8baa69a13" ]] \
  || fail "Unexpected checkpoint HEAD; stopping to avoid patching the wrong source"

grep -qx 'VERSION_BUILD=26176' app/version.properties \
  || fail "Expected current VERSION_BUILD=26176"

# Verify the already-applied 26176 Motion processing corrections.
grep -q 'motionChromaCleanupMaximum = 0.45f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java \
  || fail "26176 Motion chroma correction is missing"

grep -q 'motionLumaCleanupMaximum = 0.14f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java \
  || fail "26176 Motion luma correction is missing"

grep -q 'motionCaptureSharpeningFloor = 0.25f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java \
  || fail "26176 capture-sharpening correction is missing"

grep -q 'motionFinalSharpeningFloor = 0.25f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java \
  || fail "26176 final-sharpening correction is missing"

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_BRANCH="backup/experimental-effective-stack-before-26177-${STAMP}"
BACKUP_DIR="$ROOT/build_26177_approved_ui_motion_${STAMP}"

mkdir -p "$BACKUP_DIR"
git branch "$BACKUP_BRANCH"
git diff --binary HEAD > "$BACKUP_DIR/before_26177.patch"
git status --short > "$BACKUP_DIR/status_before_26177.txt"
cp -a app/version.properties "$BACKUP_DIR/version.properties.before"

echo "Backup branch: $BACKUP_BRANCH"
echo "Backup directory: $BACKUP_DIR"

# Locate the actual saved 26174 approved Apple-liquid UI source tree.
APPROVED_BUILD="$ROOT/build_26174_hdrx_ui_compile_fix_20260731_150812"
[[ -d "$APPROVED_BUILD" ]] || fail "Approved 26174 build directory is missing"

mapfile -t APPROVED_LAYOUTS < <(
  find "$APPROVED_BUILD" -type f \
    -path '*/app/src/main/res/layout/layout_bottombuttons.xml' | sort
)

((${#APPROVED_LAYOUTS[@]} > 0)) \
  || fail "Could not locate the saved approved layout_bottombuttons.xml inside the 26174 build directory"

# Prefer a complete saved source tree containing both the mode picker and CameraUIViewImpl.
APPROVED_ROOT=""
for layout in "${APPROVED_LAYOUTS[@]}"; do
  candidate="${layout%/app/src/main/res/layout/layout_bottombuttons.xml}"
  if [[ -f "$candidate/app/src/main/res/layout/layout_modeswitcher.xml" ]] &&
     [[ -f "$candidate/app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java" ]]; then
    APPROVED_ROOT="$candidate"
    break
  fi
done

[[ -n "$APPROVED_ROOT" ]] \
  || fail "The 26174 folder does not contain a complete approved UI source snapshot"

echo "Approved UI source: $APPROVED_ROOT"

# Restore only the approved UI/branding surface. Processing source remains untouched.
restore_file() {
  local rel="$1"
  [[ -f "$APPROVED_ROOT/$rel" ]] || fail "Approved UI source is missing $rel"
  mkdir -p "$(dirname "$ROOT/$rel")"
  cp -a "$APPROVED_ROOT/$rel" "$ROOT/$rel"
}

UI_FILES=(
  "app/build.gradle"
  "app/src/main/AndroidManifest.xml"
  "app/src/main/res/layout/camera_fragment.xml"
  "app/src/main/res/layout/layout_bottombuttons.xml"
  "app/src/main/res/layout/layout_main_bottombar.xml"
  "app/src/main/res/layout/layout_main_topbar.xml"
  "app/src/main/res/layout/layout_modeswitcher.xml"
  "app/src/main/res/values/ids.xml"
  "app/src/main/res/values/strings.xml"
  "app/src/main/res/values/styles.xml"
  "app/src/main/res/values-ko-rKR/strings.xml"
  "app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java"
  "app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java"
  "app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java"
  "app/src/main/java/com/particlesdevs/photoncamera/ui/camera/binding/CustomBinding.java"
  "app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/AuxButtonsViewModel.java"
  "app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/SettingsBarEntryProvider.java"
  "app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/AuxButtonsLayout.java"
  "app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/settingsbar/SettingsBarEntryView.java"
  "app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/settingsbar/SettingsBarLayout.java"
)

for rel in "${UI_FILES[@]}"; do
  restore_file "$rel"
done

# Restore the exact approved mode-picker class and liquid UI drawables when present.
while IFS= read -r -d '' src; do
  rel="${src#"$APPROVED_ROOT/"}"
  mkdir -p "$(dirname "$ROOT/$rel")"
  cp -a "$src" "$ROOT/$rel"
done < <(
  find "$APPROVED_ROOT/app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/modeswitcher" \
       "$APPROVED_ROOT/app/src/main/res/drawable" \
       -type f \( \
         -name 'LiquidModePicker.java' -o \
         -name 'liquid_*.xml' -o \
         -name 'ic_quad_status.xml' \
       \) -print0 2>/dev/null
)

# Remove later Iris-only UI resources so they cannot override the approved design.
rm -f \
  app/src/main/res/color/iris_lens_text.xml \
  app/src/main/res/drawable/iris_lens_button_background.xml \
  app/src/main/res/drawable/iris_outline_circle.xml \
  app/src/main/res/drawable/iris_outline_pill.xml

# Restore approved launcher XML if it exists in the saved UI.
if [[ -f "$APPROVED_ROOT/app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml" ]]; then
  mkdir -p app/src/main/res/mipmap-anydpi-v26
  cp -a "$APPROVED_ROOT/app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml" \
        app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml
fi

# Shrink only the visible thumbnail and camera-switch icon to exactly 50%.
python3 - <<'PY'
from pathlib import Path
import re
import sys

path = Path("app/src/main/res/layout/layout_bottombuttons.xml")
text = path.read_text()

def halve_view(text: str, view_id: str) -> str:
    # Match the complete start tag containing the requested android:id.
    pattern = re.compile(
        r'(<[^>]+\bandroid:id="@\+id/' + re.escape(view_id) + r'"[^>]*>)',
        re.S,
    )
    match = pattern.search(text)
    if not match:
        raise SystemExit(f"Missing approved view id: {view_id}")

    tag = match.group(1)

    def halve_dimension(tag_text: str, attr: str) -> str:
        dim_pattern = re.compile(
            rf'({re.escape(attr)}=")(\d+(?:\.\d+)?)(dp|dip|sp)(")'
        )
        dim_match = dim_pattern.search(tag_text)
        if not dim_match:
            raise SystemExit(
                f"{view_id} does not have a numeric {attr}; source needs inspection"
            )
        old = float(dim_match.group(2))
        new = old / 2.0
        value = str(int(new)) if new.is_integer() else f"{new:g}"
        return (
            tag_text[:dim_match.start()]
            + dim_match.group(1)
            + value
            + dim_match.group(3)
            + dim_match.group(4)
            + tag_text[dim_match.end():]
        )

    tag = halve_dimension(tag, "android:layout_width")
    tag = halve_dimension(tag, "android:layout_height")
    return text[:match.start()] + tag + text[match.end():]

text = halve_view(text, "gallery_image_button")
text = halve_view(text, "flip_camera_button")
path.write_text(text)
PY

# Confirm only the requested controls were scaled.
grep -n -A14 -B4 'android:id="@+id/gallery_image_button"' \
  app/src/main/res/layout/layout_bottombuttons.xml \
  | tee "$BACKUP_DIR/gallery_thumbnail_50_percent.txt"

grep -n -A14 -B4 'android:id="@+id/flip_camera_button"' \
  app/src/main/res/layout/layout_bottombuttons.xml \
  | tee "$BACKUP_DIR/camera_switch_50_percent.txt"

# Increment build after UI restoration.
sed -i 's/^VERSION_BUILD=26176$/VERSION_BUILD=26177/' app/version.properties
grep -qx 'VERSION_BUILD=26177' app/version.properties \
  || fail "Failed to increment VERSION_BUILD to 26177"

# Reconfirm processing corrections survived the UI restoration.
grep -q 'motionChromaCleanupMaximum = 0.45f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java \
  || fail "Motion chroma correction was lost"

grep -q 'motionLumaCleanupMaximum = 0.14f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java \
  || fail "Motion luma correction was lost"

grep -q 'motionCaptureSharpeningFloor = 0.25f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java \
  || fail "Capture sharpening correction was lost"

grep -q 'motionFinalSharpeningFloor = 0.25f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java \
  || fail "Final sharpening correction was lost"

git diff --binary HEAD > "$BACKUP_DIR/after_26177.patch"
git status --short > "$BACKUP_DIR/status_after_26177.txt"

echo
echo "Building signed debug APK..."
./gradlew --no-daemon clean assembleDebug 2>&1 | tee "$BACKUP_DIR/build_26177.log"

APK="$(find app/build/outputs/apk -type f -name '*debug*.apk' -printf '%T@ %p\n' \
  | sort -nr | head -1 | cut -d' ' -f2-)"

[[ -n "$APK" && -f "$APK" ]] || fail "Debug build completed but no APK was found"

OUT="$ROOT/PhotonCamera-0.9726177-build26177-approved-apple-ui-motion-debug.apk"
cp -f "$APK" "$OUT"

APKSIGNER=""
for candidate in \
  "$ANDROID_HOME"/build-tools/*/apksigner \
  "$ANDROID_SDK_ROOT"/build-tools/*/apksigner
do
  [[ -x "$candidate" ]] && APKSIGNER="$candidate"
done

[[ -n "$APKSIGNER" ]] || fail "apksigner was not found"
"$APKSIGNER" verify --verbose --print-certs "$OUT" \
  | tee "$BACKUP_DIR/apk_signing_verification.txt"

sha256sum "$OUT" | tee "$BACKUP_DIR/PhotonCamera-0.9726177-build26177.sha256"

echo
echo "=== BUILD 26177 COMPLETE ==="
echo "Branch: $(git branch --show-current)"
echo "Build: 0.9726177 / 26177"
echo "Approved UI source: $APPROVED_ROOT"
echo "UI change: thumbnail and camera-switch icon scaled to 50%"
echo "Motion chroma cleanup maximum: 0.45"
echo "Motion luma cleanup maximum: 0.14"
echo "High-ISO capture sharpening floor: 0.25"
echo "High-ISO final sharpening floor: 0.25"
echo "APK: $OUT"
echo "Backup: $BACKUP_DIR"
