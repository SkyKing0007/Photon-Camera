#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
EXPECTED_BUILD="26162"
NEW_BUILD="26163"
NEW_VERSION="0.9726163"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="/workspaces/Photon-Camera/build_${NEW_BUILD}_double_neutral_color_fix_${STAMP}"
BACKUP_BRANCH="backup-before-double-neutral-${NEW_BUILD}-${STAMP}"

SHADER="app/src/main/assets/shaders/initial.glsl"
VERSION="app/version.properties"

fail() {
    echo
    echo "============================================================"
    echo " BUILD FAILED"
    echo " Reason: $1"
    echo " Workspace: $OUT"
    echo "============================================================"
    exit "${2:-1}"
}

trap 'code=$?; if [ "$code" -ne 0 ]; then echo; echo "FAILED: build 26163 (exit $code)"; echo "Workspace: $OUT"; fi' EXIT

echo "============================================================"
echo " PhotonCamera ${NEW_VERSION}"
echo " Double-neutral color correction from 26162"
echo "============================================================"

[ "$(git branch --show-current)" = "$EXPECTED_BRANCH" ] \
    || fail "Expected branch $EXPECTED_BRANCH"

[ "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" ] \
    || fail "Expected HEAD $EXPECTED_HEAD"

grep -q "^VERSION_BUILD=${EXPECTED_BUILD}$" "$VERSION" \
    || fail "Expected VERSION_BUILD=${EXPECTED_BUILD}"

grep -Fq 'pRGB = corr*sensorToIntermediate*(pRGB*neutralPoint);' "$SHADER" \
    || fail "Expected double-neutral shader expression missing"

mkdir -p "$OUT/source_before" "$OUT/source_after"

git branch "$BACKUP_BRANCH" HEAD
git diff --binary HEAD > "$OUT/working-tree-before-${NEW_BUILD}.patch"

cp "$SHADER" "$OUT/source_before/initial.glsl"
cp "$VERSION" "$OUT/source_before/version.properties"

python3 - <<'PY'
from pathlib import Path

shader_path = Path("app/src/main/assets/shaders/initial.glsl")
version_path = Path("app/version.properties")

shader = shader_path.read_text()
old_shader = "    pRGB = corr*sensorToIntermediate*(pRGB*neutralPoint);"
new_shader = """    /*
     * Build 26163:
     * sensorToIntermediate already includes the camera-neutral white-balance
     * transform. Applying neutralPoint again here suppresses red and blue
     * relative to green, especially after HDR tone lifting.
     */
    pRGB = corr*sensorToIntermediate*pRGB;"""

if shader.count(old_shader) != 1:
    raise SystemExit(
        f"ERROR: expected one double-neutral expression, found {shader.count(old_shader)}"
    )

shader_path.write_text(shader.replace(old_shader, new_shader, 1))

version = version_path.read_text()
if version.count("VERSION_BUILD=26162") != 1:
    raise SystemExit("ERROR: expected exactly one VERSION_BUILD=26162")

version_path.write_text(
    version.replace("VERSION_BUILD=26162", "VERSION_BUILD=26163", 1)
)
PY

echo
echo "=== VERIFY 26163 SOURCE ==="

grep -Fq 'pRGB = corr*sensorToIntermediate*pRGB;' "$SHADER" \
    || fail "Corrected shader expression missing"

if grep -Fq 'pRGB = corr*sensorToIntermediate*(pRGB*neutralPoint);' "$SHADER"; then
    fail "Old double-neutral expression remains"
fi

grep -q '^VERSION_BUILD=26163$' "$VERSION" \
    || fail "VERSION_BUILD was not updated"

# Ensure this build changes only the shader and version relative to the existing 26162 working tree.
git diff --check || fail "git diff --check reported an error"

cp "$SHADER" "$OUT/source_after/initial.glsl"
cp "$VERSION" "$OUT/source_after/version.properties"

git diff --stat | tee "$OUT/change-summary.txt"
git diff --binary HEAD > "$OUT/combined-${NEW_BUILD}-double-neutral-fix.patch"

echo
echo "PASS: Existing 26162 Motion/shutter/prebuffer state preserved."
echo "PASS: Existing color-recovery and metadata changes preserved."
echo "PASS: Duplicate neutral multiplication removed."
echo "PASS: Adaptive Noise Model remains unchanged; leave OFF."

echo
echo "=== BUILDING PHOTONCAMERA ${NEW_VERSION} ==="
echo "Do not open another terminal until BUILD COMPLETE appears."

set +e
./gradlew clean assembleDebug 2>&1 | tee "$OUT/build-${NEW_BUILD}.log"
BUILD_STATUS=${PIPESTATUS[0]}
set -e

if [ "$BUILD_STATUS" -ne 0 ]; then
    grep -nE \
        'error:|cannot find symbol|FAILURE:|Compilation failed|What went wrong' \
        "$OUT/build-${NEW_BUILD}.log" \
        | tail -220 \
        > "$OUT/relevant-errors.txt" || true

    fail "Gradle build failed; inspect $OUT/relevant-errors.txt" "$BUILD_STATUS"
fi

APK="$(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | head -n 1)"
[ -n "$APK" ] && [ -f "$APK" ] \
    || fail "Debug APK was not created"

APK_COPY="$OUT/PhotonCamera-${NEW_VERSION}-double-neutral-color-fix-debug.apk"
cp "$APK" "$APK_COPY"
sha256sum "$APK" "$APK_COPY" | tee "$OUT/sha256.txt"

echo
echo "============================================================"
echo " BUILD COMPLETE"
echo "============================================================"
echo "PhotonCamera:   ${NEW_VERSION}"
echo "VERSION_BUILD: ${NEW_BUILD}"
echo "APK:           $APK_COPY"
echo "Backup branch: $BACKUP_BRANCH"
echo "Backup patch:  $OUT/working-tree-before-${NEW_BUILD}.patch"
echo "Combined patch:$OUT/combined-${NEW_BUILD}-double-neutral-fix.patch"
echo "Build log:     $OUT/build-${NEW_BUILD}.log"
echo
echo "Adaptive Noise Model: leave OFF."
echo
git status --short --untracked-files=no
echo
echo "Safe to open another terminal now."

trap - EXIT
