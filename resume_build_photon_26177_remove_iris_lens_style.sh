#!/usr/bin/env bash
set -euo pipefail

ROOT=/workspaces/Photon-Camera
cd "$ROOT"

fail() {
  printf '\nERROR: %s\n' "$*" >&2
  exit 1
}

echo "=== RESUME BUILD 26177 — REMOVE IRIS-ONLY LENS STYLING ==="

[[ "$(git branch --show-current)" == "experimental-effective-stack" ]]   || fail "Expected branch experimental-effective-stack"

[[ "$(git rev-parse HEAD)" == "cedc3ab3e39ad49d42523cff7e3711f8baa69a13" ]]   || fail "Unexpected checkpoint HEAD"

grep -qx 'VERSION_BUILD=26177' app/version.properties   || fail "Expected VERSION_BUILD=26177"

AUX="app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/AuxButtonsLayout.java"

grep -q 'R.color.iris_lens_text' "$AUX"   || fail "Expected Iris lens text reference is missing"

grep -q 'iris_lens_button_background' "$AUX"   || fail "Expected Iris lens background reference is missing"

STAMP="$(date +%Y%m%d_%H%M%S)"
WORK="$ROOT/build_26177_remove_iris_lens_style_${STAMP}"
BACKUP_BRANCH="backup/experimental-effective-stack-before-26177-lens-style-fix-${STAMP}"

mkdir -p "$WORK/before" "$WORK/after"
git branch "$BACKUP_BRANCH"
git status --short > "$WORK/status-before.txt"
git diff --binary HEAD > "$WORK/working-tree-before.patch"
cp -a "$AUX" "$WORK/before/AuxButtonsLayout.java"

echo "Backup branch: $BACKUP_BRANCH"
echo "Backup directory: $WORK"

python3 - <<'PY'
from pathlib import Path

path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "ui/camera/views/AuxButtonsLayout.java"
)
text = path.read_text()

text_color_block = '''        button.setTextColor(
                getResources().getColorStateList(
                        R.color.iris_lens_text,
                        getContext().getTheme()
                )
        );

'''

background_block = '''        button.setBackgroundResource(
                R.drawable
                        .iris_lens_button_background
        );

'''

if text.count(text_color_block) != 1:
    raise SystemExit(
        "Expected exactly one Iris text-color block, found "
        + str(text.count(text_color_block))
    )

if text.count(background_block) != 1:
    raise SystemExit(
        "Expected exactly one Iris background block, found "
        + str(text.count(background_block))
    )

text = text.replace(text_color_block, "", 1)
text = text.replace(background_block, "", 1)
path.write_text(text)
PY

if grep -qE 'iris_lens_text|iris_lens_button_background' "$AUX"; then
  fail "Iris-only lens resource references remain"
fi

grep -q 'button.setTextAppearance(' "$AUX"   || fail "Approved AuxButtonText styling hook is missing"

cp -a "$AUX" "$WORK/after/AuxButtonsLayout.java"

grep -q 'LiquidModePicker' app/src/main/res/layout/layout_modeswitcher.xml   || fail "Approved animated mode selector is missing"

grep -A4 'android:id="@+id/gallery_image_button"'   app/src/main/res/layout/layout_bottombuttons.xml   | grep -q 'android:layout_width="30dp"'   || fail "Gallery thumbnail is no longer 30dp"

grep -A4 'android:id="@+id/flip_camera_button"'   app/src/main/res/layout/layout_bottombuttons.xml   | grep -q 'android:layout_width="30dp"'   || fail "Camera switch icon is no longer 30dp"

grep -q 'motionChromaCleanupMaximum = 0.45f'   app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java   || fail "Motion chroma correction is missing"

grep -q 'motionLumaCleanupMaximum = 0.14f'   app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java   || fail "Motion luma correction is missing"

grep -q 'motionCaptureSharpeningFloor = 0.25f'   app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java   || fail "Capture sharpening correction is missing"

grep -q 'motionFinalSharpeningFloor = 0.25f'   app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java   || fail "Final sharpening correction is missing"

git diff --check || fail "git diff --check failed"
git diff --binary HEAD > "$WORK/working-tree-after.patch"
git status --short > "$WORK/status-after.txt"

echo
echo "Building signed debug APK..."
./gradlew --no-daemon assembleDebug 2>&1 | tee "$WORK/build-26177.log"

APK="$(find app/build/outputs/apk/debug -type f -name '*.apk' -printf '%T@ %p\n'   | sort -nr | head -1 | cut -d' ' -f2-)"

[[ -n "$APK" && -f "$APK" ]] || fail "No debug APK found"

OUT="$ROOT/PhotonCamera-0.9726177-build26177-approved-animated-ui-motion-debug.apk"
cp -f "$APK" "$OUT"

APKSIGNER=""
for candidate in   "$ANDROID_HOME"/build-tools/*/apksigner   "$ANDROID_SDK_ROOT"/build-tools/*/apksigner
do
  [[ -x "$candidate" ]] && APKSIGNER="$candidate"
done

[[ -n "$APKSIGNER" ]] || fail "apksigner not found"

"$APKSIGNER" verify --verbose --print-certs "$OUT"   | tee "$WORK/apk-signing.txt"

sha256sum "$OUT" | tee "$WORK/PhotonCamera-0.9726177-build26177.sha256"

echo
echo "=== BUILD 26177 COMPLETE ==="
echo "Build: 0.9726177 / 26177"
echo "Fix: removed only Iris-only lens text/background overrides"
echo "Lens buttons: approved AuxButtonText style retained"
echo "UI: exact approved animated Apple-liquid UI"
echo "Thumbnail: 30dp"
echo "Camera switch icon: 30dp"
echo "APK: $OUT"
echo "Backup: $WORK"
