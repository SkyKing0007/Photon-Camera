#!/usr/bin/env bash
set -euo pipefail

ROOT=/workspaces/Photon-Camera
cd "$ROOT"

fail() {
  printf '\nERROR: %s\n' "$*" >&2
  exit 1
}

printf '=== IRIS CAMERA 26176 BUILD RESUME ===\n'

[[ "$(git branch --show-current)" == "experimental-effective-stack" ]] \
  || fail "Expected branch experimental-effective-stack"

grep -qx 'VERSION_BUILD=26176' app/version.properties \
  || fail "VERSION_BUILD is not 26176; do not reapply the tuning script"

grep -q 'motionChromaCleanupMaximum = 0.45f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java \
  || fail "26176 chroma tuning is missing"

grep -q 'motionLumaCleanupMaximum = 0.14f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java \
  || fail "26176 luma tuning is missing"

grep -q 'motionCaptureSharpeningFloor = 0.25f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java \
  || fail "26176 capture sharpening tuning is missing"

grep -q 'motionFinalSharpeningFloor = 0.25f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java \
  || fail "26176 final sharpening tuning is missing"

grep -q "applicationId 'com.skyyking.iriscam'" app/build.gradle \
  || fail "Approved Iris package ID is missing"

grep -q '<string name="app_name" translatable="false">Iris Camera</string>' \
  app/src/main/res/values/strings.xml \
  || fail "Approved Iris branding is missing"

[[ -f app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/modeswitcher/LiquidModePicker.java ]] \
  || fail "Approved LiquidModePicker UI is missing"

STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_DIR="$ROOT/build_26176_release_resume_${STAMP}"
mkdir -p "$LOG_DIR"

git status --short > "$LOG_DIR/status_before_build.txt"
git diff --binary HEAD > "$LOG_DIR/iris_26176_prebuild.patch"

printf '\nBuilding the actual unflavored release variant: assembleRelease\n'
./gradlew --no-daemon clean assembleRelease 2>&1 | tee "$LOG_DIR/build_26176.log"

mapfile -t APKS < <(
  find app/build/outputs/apk -type f -name '*release*.apk' -printf '%T@ %p\n' \
    | sort -nr | awk '{print $2}'
)
((${#APKS[@]})) || fail "Gradle completed but no release APK was found"

APK="${APKS[0]}"
OUT="$ROOT/IrisCamera-0.9726176-build26176.apk"
cp -f "$APK" "$OUT"
sha256sum "$OUT" | tee "$LOG_DIR/IrisCamera-0.9726176-build26176.sha256"

printf '\n=== IRIS CAMERA 26176 COMPLETE ===\n'
printf 'Branch: %s\n' "$(git branch --show-current)"
printf 'Build: 0.9726176 / 26176\n'
printf 'APK: %s\n' "$OUT"
printf 'Build log: %s\n' "$LOG_DIR/build_26176.log"
