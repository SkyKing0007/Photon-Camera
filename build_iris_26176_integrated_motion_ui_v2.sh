#!/usr/bin/env bash
set -euo pipefail

ROOT=/workspaces/Photon-Camera
cd "$ROOT"

EXPECTED_BRANCH=experimental-effective-stack
EXPECTED_HEAD=cedc3ab3e39ad49d42523cff7e3711f8baa69a13
EXPECTED_BUILD=26175
NEW_BUILD=26176
TS=$(date +%Y%m%d_%H%M%S)
BACKUP_BRANCH="backup/iris-26175-before-26176-$TS"
BACKUP_DIR="$ROOT/build_26176_integrated_motion_ui_$TS"
mkdir -p "$BACKUP_DIR"

fail() { echo "ERROR: $*" >&2; exit 1; }

[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "Wrong branch"
[[ "$(git rev-parse HEAD)" == "$EXPECTED_HEAD" ]] || fail "Unexpected HEAD"
grep -qx "VERSION_BUILD=$EXPECTED_BUILD" app/version.properties || fail "Expected VERSION_BUILD=$EXPECTED_BUILD"
grep -q "applicationId 'com.skyyking.iriscam'" app/build.gradle || fail "Iris package ID missing"
grep -q '>Iris Camera<' app/src/main/res/values/strings.xml || fail "Iris Camera branding missing"
[[ -f app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/modeswitcher/LiquidModePicker.java ]] || fail "Approved LiquidModePicker missing"

# Preserve the complete 26175 state before editing, including untracked Iris/Motion source files.
git branch "$BACKUP_BRANCH"
git status --short > "$BACKUP_DIR/status_before.txt"
git diff --binary HEAD > "$BACKUP_DIR/iris_26175_to_pre26176.patch"
mapfile -t BACKUP_FILES < <(git ls-files -m -d -o --exclude-standard app)
printf '%s\n' "${BACKUP_FILES[@]}" > "$BACKUP_DIR/changed_app_paths_including_deletions.txt"
EXISTING_BACKUP_FILES=()
for f in "${BACKUP_FILES[@]}"; do
  [[ -e "$f" || -L "$f" ]] && EXISTING_BACKUP_FILES+=("$f")
done
if ((${#EXISTING_BACKUP_FILES[@]})); then
  tar -czf "$BACKUP_DIR/iris_26175_existing_changed_app_files.tar.gz" "${EXISTING_BACKUP_FILES[@]}"
fi

UI_FILES=(
  app/build.gradle
  app/src/main/AndroidManifest.xml
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/binding/CustomBinding.java
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/AuxButtonsViewModel.java
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/SettingsBarEntryProvider.java
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/AuxButtonsLayout.java
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/modeswitcher/LiquidModePicker.java
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/settingsbar/SettingsBarEntryView.java
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/settingsbar/SettingsBarLayout.java
  app/src/main/res/color/iris_lens_text.xml
  app/src/main/res/layout/camera_fragment.xml
  app/src/main/res/layout/layout_bottombuttons.xml
  app/src/main/res/layout/layout_main_bottombar.xml
  app/src/main/res/layout/layout_main_topbar.xml
  app/src/main/res/layout/layout_modeswitcher.xml
  app/src/main/res/values/ids.xml
  app/src/main/res/values/strings.xml
  app/src/main/res/values/styles.xml
)
for f in "${UI_FILES[@]}"; do [[ -f "$f" ]] || fail "Protected UI file missing: $f"; done
sha256sum "${UI_FILES[@]}" > "$BACKUP_DIR/ui_hashes_before.sha256"

python3 - <<'PY'
from pathlib import Path

def replace_exact(path, old, new):
    p = Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one guarded block, found {count}")
    p.write_text(text.replace(old, new, 1))

replace_exact(
    "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java",
    '''            description = "Maximum broad chroma cleanup at ISO 3200. 26170 used 0.90; the safer default is 0.30.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 1.0f,
            defaultValue = 0.30f,
            step = 0.01f
    )
    float motionChromaCleanupMaximum = 0.30f;''',
    '''            description = "Maximum broad chroma cleanup at ISO 3200. 26176 raises cleanup moderately to suppress the remaining broad color clouds without using shadow desaturation.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 1.0f,
            defaultValue = 0.45f,
            step = 0.01f
    )
    float motionChromaCleanupMaximum = 0.45f;''')

replace_exact(
    "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java",
    '''            description = "Maximum cleanup strength at ISO 3200. Keep low to avoid losing foliage and fine texture.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 0.60f,
            defaultValue = 0.08f,
            step = 0.01f
    )
    float motionLumaCleanupMaximum = 0.08f;''',
    '''            description = "Maximum cleanup strength at ISO 3200. 26176 increases flat-area cleanup while retaining the existing noise gate and detail protection.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 0.60f,
            defaultValue = 0.14f,
            step = 0.01f
    )
    float motionLumaCleanupMaximum = 0.14f;''')

replace_exact(
    "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java",
    '''            description = "Fraction of normal capture sharpening retained at ISO 3200. 26170 used 0.10; the detail-recovery default is 0.40.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 1.0f,
            defaultValue = 0.40f,
            step = 0.05f
    )
    float motionCaptureSharpeningFloor = 0.40f;''',
    '''            description = "Fraction of normal capture sharpening retained at ISO 3200. 26176 reduces high-ISO sharpening so residual noise is not enlarged into clumps.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 1.0f,
            defaultValue = 0.25f,
            step = 0.05f
    )
    float motionCaptureSharpeningFloor = 0.25f;''')

replace_exact(
    "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java",
    '''            title = "Motion final sharpening floor",
            description = "Fraction of the selected final sharpening retained at ISO 3200.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 1.0f,
            defaultValue = 0.40f,
            step = 0.05f
    )
    float motionFinalSharpeningFloor = 0.40f;''',
    '''            title = "Motion final sharpening floor",
            description = "Fraction of the selected final sharpening retained at ISO 3200. 26176 lowers the floor to avoid re-amplifying residual luma and chroma noise.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 1.0f,
            defaultValue = 0.25f,
            step = 0.05f
    )
    float motionFinalSharpeningFloor = 0.25f;''')

vp = Path("app/version.properties")
text = vp.read_text()
old = "VERSION_BUILD=26175"
if text.count(old) != 1:
    raise SystemExit("version.properties: guarded VERSION_BUILD=26175 not found exactly once")
vp.write_text(text.replace(old, "VERSION_BUILD=26176", 1))
PY

# The approved 26175 UI must be byte-for-byte unchanged.
sha256sum "${UI_FILES[@]}" > "$BACKUP_DIR/ui_hashes_after.sha256"
diff -u "$BACKUP_DIR/ui_hashes_before.sha256" "$BACKUP_DIR/ui_hashes_after.sha256" > "$BACKUP_DIR/ui_hash_check.diff" || fail "Protected Iris UI changed"

grep -qx "VERSION_BUILD=$NEW_BUILD" app/version.properties || fail "Build number did not update"
grep -q 'motionChromaCleanupMaximum = 0.45f' app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java || fail "Chroma tuning missing"
grep -q 'motionLumaCleanupMaximum = 0.14f' app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java || fail "Luma tuning missing"
grep -q 'motionCaptureSharpeningFloor = 0.25f' app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java || fail "Capture sharpening tuning missing"
grep -q 'motionFinalSharpeningFloor = 0.25f' app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java || fail "Final sharpening tuning missing"
grep -q 'motionShadowNeutralization = 0.0f' app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java || fail "Shadow neutralization must remain zero"

git diff --binary HEAD > "$BACKUP_DIR/iris_26175_to_26176.patch"
git status --short > "$BACKUP_DIR/status_after_edit.txt"

# Version increment and APK build occur in this same guarded command script.
./gradlew --no-daemon clean assemblePlaystoreRelease 2>&1 | tee "$BACKUP_DIR/build_26176.log"

mapfile -t APKS < <(find app/build/outputs/apk -type f -name '*.apk' -printf '%T@ %p\n' | sort -nr | awk '{print $2}')
((${#APKS[@]})) || fail "Build completed but no APK was found"
APK="${APKS[0]}"
OUT="$ROOT/IrisCamera-0.9726176-build26176.apk"
cp -f "$APK" "$OUT"
sha256sum "$OUT" | tee "$BACKUP_DIR/IrisCamera-0.9726176-build26176.sha256"

printf '\n=== IRIS CAMERA 26176 COMPLETE ===\n'
printf 'Branch: %s\n' "$(git branch --show-current)"
printf 'Backup branch: %s\n' "$BACKUP_BRANCH"
printf 'Backup and patch: %s\n' "$BACKUP_DIR"
printf 'Protected UI: unchanged\n'
printf 'APK: %s\n' "$OUT"
printf 'Build: 0.9726176 / 26176\n'
