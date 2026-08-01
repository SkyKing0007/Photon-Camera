#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
EXPECTED_BUILD="26161"
NEW_BUILD="26163"
NEW_VERSION="0.9726163"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="/workspaces/Photon-Camera/build_${NEW_BUILD}_double_neutral_color_fix_${STAMP}"
BACKUP_BRANCH="backup-before-double-neutral-${NEW_BUILD}-${STAMP}"

HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
SHADER="app/src/main/assets/shaders/initial.glsl"
PARAMS="app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java"
INITIAL="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java"
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
echo " Motion double-neutral color correction"
echo "============================================================"

[ "$(git branch --show-current)" = "$EXPECTED_BRANCH" ] \
    || fail "Expected branch $EXPECTED_BRANCH"

[ "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" ] \
    || fail "Expected HEAD $EXPECTED_HEAD"

grep -q "^VERSION_BUILD=${EXPECTED_BUILD}$" "$VERSION" \
    || fail "Expected VERSION_BUILD=${EXPECTED_BUILD}"

grep -q 'MOTION_26161_COLOR_RECOVERY' "$HDRX" \
    || fail "Expected 26161 recovery state missing"

grep -Fq 'pRGB = corr*sensorToIntermediate*(pRGB*neutralPoint);' "$SHADER" \
    || fail "Expected double-neutral shader expression missing"

mkdir -p "$OUT/source_before" "$OUT/source_after"

git branch "$BACKUP_BRANCH" HEAD
git diff --binary HEAD > "$OUT/working-tree-before-${NEW_BUILD}.patch"

for file in "$HDRX" "$SHADER" "$PARAMS" "$INITIAL" "$VERSION"; do
    cp "$file" "$OUT/source_before/$(basename "$file")"
done

python3 - <<'PY'
from pathlib import Path

hdrx_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/processor/HdrxProcessor.java"
)
shader_path = Path("app/src/main/assets/shaders/initial.glsl")
version_path = Path("app/version.properties")

hdrx = hdrx_path.read_text()

old_locals = """        float effectiveFrameCount = 1.0f;
        float effectiveStackRatio = 1.0f;
        float subpixelSampleDiversity = 0.0f;

"""

if hdrx.count(old_locals) != 1:
    raise SystemExit(
        "ERROR: expected one obsolete local metric block, found "
        + str(hdrx.count(old_locals))
    )

hdrx = hdrx.replace(old_locals, "", 1)

old_getters = """            effectiveFrameCount =
                    pyramidMerging.getEffectiveFrameCount();
            effectiveStackRatio =
                    pyramidMerging.getEffectiveStackRatio();
            subpixelSampleDiversity =
                    pyramidMerging.getSubpixelSampleDiversity();

"""

if hdrx.count(old_getters) != 1:
    raise SystemExit(
        "ERROR: expected one obsolete getter block, found "
        + str(hdrx.count(old_getters))
    )

hdrx = hdrx.replace(old_getters, "", 1)

start_marker = """        CameraMode finalSelectedMode =
                PhotonCamera.getSettings().selectedMode;
"""

end_marker = """        /*
         * Build 26161:
"""

start = hdrx.find(start_marker)
end = hdrx.find(end_marker, start)

if start < 0 or end < 0:
    raise SystemExit(
        "ERROR: obsolete effective-stack mode block not found"
    )

obsolete = hdrx[start:end]

for term in (
    "effectiveFrameCount",
    "effectiveStackRatio",
    "subpixelSampleDiversity",
):
    if term not in obsolete:
        raise SystemExit(
            "ERROR: unexpected obsolete mode block; missing " + term
        )

hdrx = hdrx[:start] + hdrx[end:]
hdrx_path.write_text(hdrx)

shader = shader_path.read_text()

old_shader = "    pRGB = corr*sensorToIntermediate*(pRGB*neutralPoint);"

new_shader = """    /*
     * Build 26163:
     *
     * sensorToIntermediate is already calculated using the camera neutral
     * and maps the captured neutral to D50 white. Multiplying the RGB by
     * neutralPoint here applies white balance a second time and suppresses
     * red and blue relative to green, especially after HDR tone lifting.
     */
    pRGB = corr*sensorToIntermediate*pRGB;"""

if shader.count(old_shader) != 1:
    raise SystemExit(
        "ERROR: expected exactly one double-neutral expression, found "
        + str(shader.count(old_shader))
    )

shader_path.write_text(
    shader.replace(
        old_shader,
        new_shader,
        1,
    )
)

version = version_path.read_text()

if version.count("VERSION_BUILD=26161") != 1:
    raise SystemExit(
        "ERROR: expected exactly one VERSION_BUILD=26161"
    )

version_path.write_text(
    version.replace(
        "VERSION_BUILD=26161",
        "VERSION_BUILD=26163",
        1,
    )
)
PY

echo
echo "=== VERIFY 26163 SOURCE ==="

if grep -qE \
    'getEffectiveFrameCount|getEffectiveStackRatio|getSubpixelSampleDiversity' \
    "$HDRX"; then
    fail "A stale PyramidMerging getter remains"
fi

grep -Fq 'pRGB = corr*sensorToIntermediate*pRGB;' "$SHADER" \
    || fail "Corrected shader expression missing"

if grep -Fq \
    'pRGB = corr*sensorToIntermediate*(pRGB*neutralPoint);' \
    "$SHADER"; then
    fail "Old double-neutral shader expression remains"
fi

grep -q 'MOTION_COLOR_NEUTRAL_SELECTED' "$PARAMS" \
    || fail "Burst-neutral validation was lost"

grep -q 'MOTION_26161_FINAL_COLOR_PATH' "$INITIAL" \
    || fail "Final color diagnostics were lost"

grep -q '^VERSION_BUILD=26163$' "$VERSION" \
    || fail "VERSION_BUILD was not updated"

if git diff -- \
    app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java \
    app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IsoExpoSelector.java \
    | grep -q .; then
    fail "Capture or exposure-selection source changed unexpectedly"
fi

if git diff | grep -E \
    '^[+-].*(mIsRecordingVideo|CameraMode\.RAWVIDEO|TEMPLATE_RECORD|MediaRecorder|CONTROL_AF_MODE_CONTINUOUS_VIDEO|getSelectedFpsRange)'; then
    fail "Video or RAW Video source changed unexpectedly"
fi

git diff --check \
    || fail "git diff --check reported a formatting error"

for file in "$HDRX" "$SHADER" "$PARAMS" "$INITIAL" "$VERSION"; do
    cp "$file" "$OUT/source_after/$(basename "$file")"
done

git diff --stat | tee "$OUT/change-summary.txt"
git diff --binary HEAD > "$OUT/combined-${NEW_BUILD}-double-neutral-fix.patch"

echo
echo "PASS: Stale effective-stack compile references removed."
echo "PASS: Duplicate neutral multiplication removed from final color shader."
echo "PASS: Burst-neutral metadata selection preserved."
echo "PASS: Capture, exposure, Video and RAW Video unchanged."
echo "PASS: Adaptive Noise Model remains user-controlled; leave OFF."

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

    fail "Gradle build failed; inspect $OUT/relevant-errors.txt" \
        "$BUILD_STATUS"
fi

APK="app/build/outputs/apk/debug/PhotonCamera-${NEW_VERSION}-debug.apk"
APK_COPY="$OUT/PhotonCamera-${NEW_VERSION}-double-neutral-color-fix-debug.apk"

[ -f "$APK" ] \
    || fail "Expected APK was not created: $APK"

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
