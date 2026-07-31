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
  || fail "Unexpected checkpoint HEAD"

grep -qx 'VERSION_BUILD=26176' app/version.properties \
  || fail "Expected VERSION_BUILD=26176"

# Confirm the intended 26176 Motion-processing corrections are present.
grep -q 'motionChromaCleanupMaximum = 0.45f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java \
  || fail "26176 Motion chroma correction is missing"

grep -q 'motionLumaCleanupMaximum = 0.14f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java \
  || fail "26176 Motion luma correction is missing"

grep -q 'motionCaptureSharpeningFloor = 0.25f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java \
  || fail "26176 capture sharpening correction is missing"

grep -q 'motionFinalSharpeningFloor = 0.25f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java \
  || fail "26176 final sharpening correction is missing"

STAMP="$(date +%Y%m%d_%H%M%S)"
WORK="$ROOT/build_26177_exact_approved_ui_motion_${STAMP}"
BACKUP_BRANCH="backup/experimental-effective-stack-before-26177-final-${STAMP}"

mkdir -p "$WORK"
git branch "$BACKUP_BRANCH"
git status --short > "$WORK/status-before.txt"
git diff --binary HEAD > "$WORK/working-tree-before-26177.patch"

echo "Backup branch: $BACKUP_BRANCH"
echo "Backup directory: $WORK"

UI26173="$ROOT/build_26173_hdrx_fix_apple_liquid_ui_20260731_150139/after"
UI26174="$ROOT/build_26174_hdrx_ui_compile_fix_20260731_150812/after"

[[ -d "$UI26173/app/src/main" ]] \
  || fail "26173 approved UI after-snapshot is missing"

[[ -f "$UI26174/app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java" ]] \
  || fail "26174 compile-corrected CameraUIViewImpl.java is missing"

# Restore the exact approved animated Apple-liquid UI files from 26173.
mapfile -t APPROVED_FILES < <(
  find "$UI26173/app" -type f | sort
)

((${#APPROVED_FILES[@]} > 0)) \
  || fail "No files found in the 26173 approved UI snapshot"

for src in "${APPROVED_FILES[@]}"; do
  rel="${src#"$UI26173/"}"
  mkdir -p "$(dirname "$ROOT/$rel")"
  cp -a "$src" "$ROOT/$rel"
done

# Apply the 26174 compile-corrected UI Java/resource files.
for rel in \
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java \
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java \
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/settingsbar/SettingsBarLayout.java \
  app/src/main/res/values/ids.xml
do
  if [[ -f "$UI26174/$rel" ]]; then
    mkdir -p "$(dirname "$ROOT/$rel")"
    cp -a "$UI26174/$rel" "$ROOT/$rel"
  fi
done

# Remove later Iris-only overrides/resources.
rm -f \
  app/src/main/res/color/iris_lens_text.xml \
  app/src/main/res/drawable/iris_lens_button_background.xml \
  app/src/main/res/drawable/iris_outline_circle.xml \
  app/src/main/res/drawable/iris_outline_pill.xml

# Restore Photon branding/package from the approved pre-Iris build state.
python3 - <<'PY'
from pathlib import Path
import re

build_gradle = Path("app/build.gradle")
text = build_gradle.read_text()
text = text.replace("applicationId 'com.skyyking.iriscam'",
                    "applicationId 'com.particlesdevs.photoncamera'")
build_gradle.write_text(text)

for path_str in (
    "app/src/main/res/values/strings.xml",
    "app/src/main/res/values-ko-rKR/strings.xml",
):
    path = Path(path_str)
    if not path.exists():
        continue
    t = path.read_text()
    t = t.replace(">Iris Camera<", ">PhotonCamera<")
    t = t.replace(">Iris Camera Pro<", ">PhotonCamera Pro<")
    path.write_text(t)
PY

# Set only the requested visual size change:
# gallery thumbnail and camera-switch icon from 60dp to 30dp.
python3 - <<'PY'
from pathlib import Path
import re

path = Path("app/src/main/res/layout/layout_bottombuttons.xml")
text = path.read_text()

def set_size(view_id: str, size: str) -> None:
    global text
    pattern = re.compile(
        r'(<[^>]+\bandroid:id="@\+id/' + re.escape(view_id) + r'"[^>]*>)',
        re.S,
    )
    match = pattern.search(text)
    if not match:
        raise SystemExit(f"Missing view id: {view_id}")

    tag = match.group(1)

    def replace_attr(tag_text: str, attr: str) -> str:
        attr_pattern = re.compile(rf'{re.escape(attr)}="[^"]+"')
        if not attr_pattern.search(tag_text):
            raise SystemExit(f"{view_id} missing {attr}")
        return attr_pattern.sub(f'{attr}="{size}"', tag_text, count=1)

    tag = replace_attr(tag, "android:layout_width")
    tag = replace_attr(tag, "android:layout_height")
    text = text[:match.start()] + tag + text[match.end():]

set_size("gallery_image_button", "30dp")
set_size("flip_camera_button", "30dp")
path.write_text(text)
PY

grep -n -A12 -B4 'android:id="@+id/gallery_image_button"' \
  app/src/main/res/layout/layout_bottombuttons.xml \
  | tee "$WORK/gallery_thumbnail_30dp.txt"

grep -n -A12 -B4 'android:id="@+id/flip_camera_button"' \
  app/src/main/res/layout/layout_bottombuttons.xml \
  | tee "$WORK/camera_switch_30dp.txt"

# Confirm approved animated mode picker is restored.
[[ -f app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/modeswitcher/LiquidModePicker.java ]] \
  || fail "LiquidModePicker.java was not restored"

grep -q 'LiquidModePicker' app/src/main/res/layout/layout_modeswitcher.xml \
  || fail "Approved animated mode picker layout is missing"

grep -q 'Integer\[\] modeNameIds = CameraMode.nameIds();' \
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java \
  || fail "26174 CameraMode compile correction is missing"

# Increment build.
sed -i 's/^VERSION_BUILD=26176$/VERSION_BUILD=26177/' app/version.properties
grep -qx 'VERSION_BUILD=26177' app/version.properties \
  || fail "Failed to set VERSION_BUILD=26177"

# Reconfirm Motion-processing corrections survived UI restoration.
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

git diff --check || fail "git diff --check failed"
git diff --binary HEAD > "$WORK/working-tree-after-26177.patch"
git status --short > "$WORK/status-after.txt"

echo
echo "Building signed debug APK..."
./gradlew --no-daemon clean assembleDebug 2>&1 | tee "$WORK/build-26177.log"

APK="$(find app/build/outputs/apk/debug -type f -name '*.apk' -printf '%T@ %p\n' \
  | sort -nr | head -1 | cut -d' ' -f2-)"

[[ -n "$APK" && -f "$APK" ]] || fail "No debug APK found"

OUT="$ROOT/PhotonCamera-0.9726177-build26177-approved-animated-ui-motion-debug.apk"
cp -f "$APK" "$OUT"

APKSIGNER=""
for candidate in \
  "$ANDROID_HOME"/build-tools/*/apksigner \
  "$ANDROID_SDK_ROOT"/build-tools/*/apksigner
do
  [[ -x "$candidate" ]] && APKSIGNER="$candidate"
done

[[ -n "$APKSIGNER" ]] || fail "apksigner not found"
"$APKSIGNER" verify --verbose --print-certs "$OUT" \
  | tee "$WORK/apk-signing.txt"

sha256sum "$OUT" | tee "$WORK/PhotonCamera-0.9726177-build26177.sha256"

echo
echo "=== BUILD 26177 COMPLETE ==="
echo "Build: 0.9726177 / 26177"
echo "UI: exact approved 26173 animated Apple-liquid UI + 26174 compile fix"
echo "Thumbnail: 30dp"
echo "Camera switch icon: 30dp"
echo "Motion chroma cleanup maximum: 0.45"
echo "Motion luma cleanup maximum: 0.14"
echo "Capture sharpening floor: 0.25"
echo "Final sharpening floor: 0.25"
echo "APK: $OUT"
echo "Backup: $WORK"
