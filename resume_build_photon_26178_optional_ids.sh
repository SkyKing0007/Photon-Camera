#!/usr/bin/env bash
set -euo pipefail

ROOT=/workspaces/Photon-Camera
cd "$ROOT"

fail() {
  printf '\nERROR: %s\n' "$*" >&2
  exit 1
}

echo "=== RESUME PHOTON CAMERA 0.9726178 / BUILD 26178 ==="

[[ "$(git branch --show-current)" == "experimental-effective-stack" ]]   || fail "Expected branch experimental-effective-stack"

[[ "$(git rev-parse HEAD)" == "cedc3ab3e39ad49d42523cff7e3711f8baa69a13" ]]   || fail "Unexpected checkpoint HEAD"

grep -qx 'VERSION_BUILD=26177' app/version.properties   || grep -qx 'VERSION_BUILD=26178' app/version.properties   || fail "Expected VERSION_BUILD=26177 or 26178"

UIROOT="$ROOT/build_26175_iris_camera_brand_ui_resume_20260731_181003/after"
[[ -d "$UIROOT/app/src/main" ]]   || fail "Final 26175 UI snapshot is missing: $UIROOT"

# Verify protected processing corrections first.
grep -q 'motionChromaCleanupMaximum = 0.45f'   app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java   || fail "Motion chroma correction is missing"

grep -q 'motionLumaCleanupMaximum = 0.14f'   app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java   || fail "Motion luma correction is missing"

grep -q 'motionCaptureSharpeningFloor = 0.25f'   app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java   || fail "Capture sharpening correction is missing"

grep -q 'motionFinalSharpeningFloor = 0.25f'   app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java   || fail "Final sharpening correction is missing"

STAMP="$(date +%Y%m%d_%H%M%S)"
WORK="$ROOT/build_26178_resume_exact_ui_${STAMP}"
BACKUP_BRANCH="backup/experimental-effective-stack-before-26178-resume-${STAMP}"

mkdir -p "$WORK"
git branch "$BACKUP_BRANCH"
git status --short > "$WORK/status-before.txt"
git diff --binary HEAD > "$WORK/working-tree-before.patch"

echo "Backup branch: $BACKUP_BRANCH"
echo "Backup directory: $WORK"

copy_if_present() {
  local rel="$1"
  if [[ -f "$UIROOT/$rel" ]]; then
    mkdir -p "$(dirname "$ROOT/$rel")"
    cp -a "$UIROOT/$rel" "$ROOT/$rel"
    echo "Restored: $rel"
  else
    echo "Skipped absent snapshot file: $rel"
  fi
}

# Exact final 26175 UI files. ids.xml is intentionally optional because
# it was not captured in the preserved final snapshot.
for rel in   app/build.gradle   app/src/main/AndroidManifest.xml   app/src/main/res/layout/camera_fragment.xml   app/src/main/res/layout/layout_bottombuttons.xml   app/src/main/res/layout/layout_main_bottombar.xml   app/src/main/res/layout/layout_main_topbar.xml   app/src/main/res/layout/layout_modeswitcher.xml   app/src/main/res/values/strings.xml   app/src/main/res/values/styles.xml   app/src/main/res/values-ko-rKR/strings.xml   app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java   app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java   app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java   app/src/main/java/com/particlesdevs/photoncamera/ui/camera/binding/CustomBinding.java   app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/AuxButtonsViewModel.java   app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/SettingsBarEntryProvider.java   app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/AuxButtonsLayout.java   app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/settingsbar/SettingsBarEntryView.java   app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/settingsbar/SettingsBarLayout.java
do
  copy_if_present "$rel"
done

# Restore complete preserved mode-picker and visual resource directories.
for dir in   app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/modeswitcher   app/src/main/res/color   app/src/main/res/drawable
do
  if [[ -d "$UIROOT/$dir" ]]; then
    while IFS= read -r -d '' src; do
      rel="${src#"$UIROOT/"}"
      mkdir -p "$(dirname "$ROOT/$rel")"
      cp -a "$src" "$ROOT/$rel"
    done < <(find "$UIROOT/$dir" -type f -print0)
  fi
done

# Keep the current valid ids.xml if the snapshot does not contain one.
[[ -f app/src/main/res/values/ids.xml ]]   || fail "Current ids.xml is missing and no snapshot replacement exists"

# Apply only the requested 50% visible icon sizes.
python3 - <<'PY'
from pathlib import Path
import re

path = Path("app/src/main/res/layout/layout_bottombuttons.xml")
text = path.read_text()

def set_size(view_id: str, size: str) -> None:
    global text
    pattern = re.compile(
        r'(<[^>]+android:id="@\+id/' + re.escape(view_id) + r'"[^>]*>)',
        re.S,
    )
    match = pattern.search(text)
    if not match:
        raise SystemExit(f"Missing view id: {view_id}")

    tag = match.group(1)
    for attr in ("android:layout_width", "android:layout_height"):
        attr_pattern = re.compile(rf'{re.escape(attr)}="[^"]+"')
        if not attr_pattern.search(tag):
            raise SystemExit(f"{view_id} missing {attr}")
        tag = attr_pattern.sub(f'{attr}="{size}"', tag, count=1)

    text = text[:match.start()] + tag + text[match.end():]

set_size("gallery_image_button", "30dp")
set_size("flip_camera_button", "30dp")
path.write_text(text)
PY

# Verify the preserved approved UI markers.
grep -q 'LiquidModePicker' app/src/main/res/layout/layout_modeswitcher.xml   || fail "Approved animated mode picker is missing"

grep -q 'MODE_DISPLAY_ORDER'   app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java   || fail "Approved mode display ordering is missing"

grep -A4 'android:id="@+id/gallery_image_button"'   app/src/main/res/layout/layout_bottombuttons.xml   | grep -q 'android:layout_width="30dp"'   || fail "Thumbnail is not 30dp"

grep -A4 'android:id="@+id/flip_camera_button"'   app/src/main/res/layout/layout_bottombuttons.xml   | grep -q 'android:layout_width="30dp"'   || fail "Camera switch icon is not 30dp"

# Set the new build number directly.
python3 - <<'PY'
from pathlib import Path
import re

path = Path("app/version.properties")
text = path.read_text()
if not re.search(r"(?m)^VERSION_BUILD=\d+$", text):
    raise SystemExit("VERSION_BUILD entry missing")
path.write_text(
    re.sub(r"(?m)^VERSION_BUILD=\d+$", "VERSION_BUILD=26178", text, count=1)
)
PY

grep -qx 'VERSION_BUILD=26178' app/version.properties   || fail "Failed to set VERSION_BUILD=26178"

# Final protected processing verification after UI restore.
grep -q 'motionChromaCleanupMaximum = 0.45f'   app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java   || fail "Motion chroma correction was lost"

grep -q 'motionLumaCleanupMaximum = 0.14f'   app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java   || fail "Motion luma correction was lost"

grep -q 'motionCaptureSharpeningFloor = 0.25f'   app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java   || fail "Capture sharpening correction was lost"

grep -q 'motionFinalSharpeningFloor = 0.25f'   app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java   || fail "Final sharpening correction was lost"

git diff --check || fail "git diff --check failed"
git diff --binary HEAD > "$WORK/working-tree-after.patch"
git status --short > "$WORK/status-after.txt"

echo
echo "Building signed debug APK..."
./gradlew --no-daemon clean assembleDebug 2>&1 | tee "$WORK/build-26178.log"

APK="$(find app/build/outputs/apk/debug -type f -name '*.apk' -printf '%T@ %p\n'   | sort -nr | head -1 | cut -d' ' -f2-)"

[[ -n "$APK" && -f "$APK" ]] || fail "No debug APK found"

OUT="$ROOT/PhotonCamera-0.9726178-build26178-exact-approved-ui-motion-debug.apk"
cp -f "$APK" "$OUT"

APKSIGNER=""
for candidate in   "$ANDROID_HOME"/build-tools/*/apksigner   "$ANDROID_SDK_ROOT"/build-tools/*/apksigner
do
  [[ -x "$candidate" ]] && APKSIGNER="$candidate"
done

[[ -n "$APKSIGNER" ]] || fail "apksigner not found"

"$APKSIGNER" verify --verbose --print-certs "$OUT"   | tee "$WORK/apk-signing.txt"

sha256sum "$OUT" | tee "$WORK/PhotonCamera-0.9726178-build26178.sha256"

echo
echo "=== BUILD 26178 COMPLETE ==="
echo "Build: 0.9726178 / 26178"
echo "UI source: preserved final 26175 snapshot"
echo "Current ids.xml retained because snapshot did not contain one"
echo "Thumbnail: 30dp"
echo "Camera switch icon: 30dp"
echo "Motion chroma cleanup maximum: 0.45"
echo "Motion luma cleanup maximum: 0.14"
echo "Capture sharpening floor: 0.25"
echo "Final sharpening floor: 0.25"
echo "APK: $OUT"
echo "Backup: $WORK"
