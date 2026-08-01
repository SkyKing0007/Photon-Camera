#!/usr/bin/env bash
set -euo pipefail

ROOT=/workspaces/Photon-Camera
cd "$ROOT"

fail() {
  printf '\nERROR: %s\n' "$*" >&2
  exit 1
}

echo "=== RESUME PHOTON CAMERA 0.9726177 / BUILD 26177 ==="

[[ "$(git branch --show-current)" == "experimental-effective-stack" ]] \
  || fail "Expected branch experimental-effective-stack"

[[ "$(git rev-parse HEAD)" == "cedc3ab3e39ad49d42523cff7e3711f8baa69a13" ]] \
  || fail "Unexpected checkpoint HEAD"

echo "Current version file:"
cat app/version.properties

# Verify the successful UI restoration from the prior run.
grep -q 'android:id="@+id/gallery_image_button"' \
  app/src/main/res/layout/layout_bottombuttons.xml \
  || fail "Gallery thumbnail view is missing"

grep -A4 'android:id="@+id/gallery_image_button"' \
  app/src/main/res/layout/layout_bottombuttons.xml \
  | grep -q 'android:layout_width="30dp"' \
  || fail "Gallery thumbnail is not 30dp"

grep -A4 'android:id="@+id/gallery_image_button"' \
  app/src/main/res/layout/layout_bottombuttons.xml \
  | grep -q 'android:layout_height="30dp"' \
  || fail "Gallery thumbnail height is not 30dp"

grep -A4 'android:id="@+id/flip_camera_button"' \
  app/src/main/res/layout/layout_bottombuttons.xml \
  | grep -q 'android:layout_width="30dp"' \
  || fail "Camera switch icon is not 30dp"

grep -A4 'android:id="@+id/flip_camera_button"' \
  app/src/main/res/layout/layout_bottombuttons.xml \
  | grep -q 'android:layout_height="30dp"' \
  || fail "Camera switch icon height is not 30dp"

[[ -f app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/modeswitcher/LiquidModePicker.java ]] \
  || fail "LiquidModePicker.java is missing"

grep -q 'LiquidModePicker' app/src/main/res/layout/layout_modeswitcher.xml \
  || fail "Approved animated mode selector is missing"

grep -q 'Integer\[\] modeNameIds = CameraMode.nameIds();' \
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java \
  || fail "26174 mode-picker compile correction is missing"

# Verify Motion-processing corrections survived the prior run.
grep -q 'motionChromaCleanupMaximum = 0.45f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java \
  || fail "Motion chroma correction is missing"

grep -q 'motionLumaCleanupMaximum = 0.14f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java \
  || fail "Motion luma correction is missing"

grep -q 'motionCaptureSharpeningFloor = 0.25f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java \
  || fail "Capture sharpening correction is missing"

grep -q 'motionFinalSharpeningFloor = 0.25f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java \
  || fail "Final sharpening correction is missing"

STAMP="$(date +%Y%m%d_%H%M%S)"
WORK="$ROOT/build_26177_resume_${STAMP}"
BACKUP_BRANCH="backup/experimental-effective-stack-before-26177-resume-${STAMP}"

mkdir -p "$WORK"
git branch "$BACKUP_BRANCH"
git status --short > "$WORK/status-before.txt"
git diff --binary HEAD > "$WORK/working-tree-before-resume.patch"
cp -a app/version.properties "$WORK/version.properties.before"

echo "Backup branch: $BACKUP_BRANCH"
echo "Backup directory: $WORK"

# Set the build number directly regardless of whether the restored snapshot
# carried 26173 or 26174.
python3 - <<'PY'
from pathlib import Path
import re

path = Path("app/version.properties")
text = path.read_text()

if not re.search(r"(?m)^VERSION_BUILD=\d+$", text):
    raise SystemExit("VERSION_BUILD entry is missing")

text = re.sub(
    r"(?m)^VERSION_BUILD=\d+$",
    "VERSION_BUILD=26177",
    text,
    count=1,
)

path.write_text(text)
PY

grep -qx 'VERSION_BUILD=26177' app/version.properties \
  || fail "Failed to set VERSION_BUILD=26177"

git diff --check || fail "git diff --check failed"
git diff --binary HEAD > "$WORK/working-tree-after-resume.patch"
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
echo "UI: exact approved animated Apple-liquid UI"
echo "Thumbnail: 30dp"
echo "Camera switch icon: 30dp"
echo "Motion chroma cleanup maximum: 0.45"
echo "Motion luma cleanup maximum: 0.14"
echo "Capture sharpening floor: 0.25"
echo "Final sharpening floor: 0.25"
echo "APK: $OUT"
echo "Backup: $WORK"
