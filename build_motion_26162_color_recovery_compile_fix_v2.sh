#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
EXPECTED_BUILD="26161"
NEW_BUILD="26162"
NEW_VERSION="0.9726162"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="/workspaces/Photon-Camera/build_${NEW_BUILD}_motion_color_recovery_compile_fix_${STAMP}"
BACKUP_BRANCH="backup-before-motion-color-recovery-${NEW_BUILD}-${STAMP}"

HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
MERGE="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts/PyramidMerging.java"
NOISE="app/src/main/java/com/particlesdevs/photoncamera/processing/render/NoiseModeler.java"
POST="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
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

trap 'code=$?; if [ "$code" -ne 0 ]; then echo; echo "FAILED: build 26162 (exit $code)"; echo "Workspace: $OUT"; fi' EXIT

echo "============================================================"
echo " PhotonCamera ${NEW_VERSION}"
echo " Motion color recovery compile repair"
echo "============================================================"

[ "$(git branch --show-current)" = "$EXPECTED_BRANCH" ] \
    || fail "Expected branch $EXPECTED_BRANCH"

[ "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" ] \
    || fail "Expected HEAD $EXPECTED_HEAD"

grep -q "^VERSION_BUILD=${EXPECTED_BUILD}$" "$VERSION" \
    || fail "Expected VERSION_BUILD=${EXPECTED_BUILD}"

grep -q 'MOTION_26161_COLOR_RECOVERY' "$HDRX" \
    || fail "26161 recovery block missing"

grep -q 'pyramidMerging.getEffectiveFrameCount();' "$HDRX" \
    || fail "Expected stale effective-frame getter missing"

grep -q 'pyramidMerging.getEffectiveStackRatio();' "$HDRX" \
    || fail "Expected stale effective-ratio getter missing"

grep -q 'pyramidMerging.getSubpixelSampleDiversity();' "$HDRX" \
    || fail "Expected stale subpixel getter missing"

if grep -q 'MOTION_EFFECTIVE_STACK' "$MERGE"; then
    fail "PyramidMerging was not restored to 26157"
fi

mkdir -p "$OUT/source_before" "$OUT/source_after"

git branch "$BACKUP_BRANCH" HEAD
git diff --binary HEAD > "$OUT/working-tree-failed-26161-before-${NEW_BUILD}.patch"

for file in "$HDRX" "$MERGE" "$NOISE" "$POST" "$PARAMS" "$INITIAL" "$VERSION"; do
    cp "$file" "$OUT/source_before/$(basename "$file")"
done

python3 - <<'PY'
from pathlib import Path

hdrx_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/processor/HdrxProcessor.java"
)
version_path = Path("app/version.properties")

hdrx = hdrx_path.read_text()

old_locals = """        float effectiveFrameCount = 1.0f;
        float effectiveStackRatio = 1.0f;
        float subpixelSampleDiversity = 0.0f;

"""

if hdrx.count(old_locals) != 1:
    raise SystemExit(
        "ERROR: expected one obsolete local declaration block, found "
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

start = hdrx.find(start_marker)
if start < 0:
    raise SystemExit("ERROR: finalSelectedMode block start not found")

end_marker = """        /*
         * Build 26161:
"""

end = hdrx.find(end_marker, start)
if end < 0:
    raise SystemExit("ERROR: Build 26161 block not found")

obsolete_mode_block = hdrx[start:end]

required_terms = [
    "effectiveFrameCount",
    "effectiveStackRatio",
    "subpixelSampleDiversity",
]

for term in required_terms:
    if term not in obsolete_mode_block:
        raise SystemExit(
            "ERROR: obsolete mode block missing expected term " + term
        )

hdrx = hdrx[:start] + hdrx[end:]
hdrx_path.write_text(hdrx)

version = version_path.read_text()

if version.count("VERSION_BUILD=26161") != 1:
    raise SystemExit(
        "ERROR: expected exactly one VERSION_BUILD=26161"
    )

version_path.write_text(
    version.replace(
        "VERSION_BUILD=26161",
        "VERSION_BUILD=26162",
        1,
    )
)
PY

echo
echo "=== VERIFY 26162 SOURCE ==="

if grep -qE \
    'getEffectiveFrameCount|getEffectiveStackRatio|getSubpixelSampleDiversity' \
    "$HDRX"; then
    fail "A stale PyramidMerging getter remains"
fi

grep -q 'MOTION_26161_COLOR_RECOVERY' "$HDRX" \
    || fail "26161 recovery policy was lost"

grep -q 'processingParameters.effectiveFrameCount =' "$HDRX" \
    || fail "Diagnostic effective-frame assignment missing"

grep -q 'processingParameters.effectiveStackRatio =' "$HDRX" \
    || fail "Diagnostic effective-ratio assignment missing"

grep -q 'processingParameters.subpixelSampleDiversity =' "$HDRX" \
    || fail "Diagnostic subpixel assignment missing"

grep -q '^VERSION_BUILD=26162$' "$VERSION" \
    || fail "VERSION_BUILD was not updated"

for file in "$MERGE" "$NOISE" "$POST"; do
    if ! git diff --quiet HEAD -- "$file"; then
        fail "$file no longer exactly matches the 26157 checkpoint"
    fi
done

grep -q 'MOTION_COLOR_NEUTRAL_SELECTED' "$PARAMS" \
    || fail "26159 burst-neutral validation was lost"

grep -q 'MOTION_GAIN_MAP_CHANNELS' "$PARAMS" \
    || fail "26160 gain-map diagnostics were lost"

grep -q 'MOTION_26161_FINAL_COLOR_PATH' "$INITIAL" \
    || fail "26161 final-color diagnostics were lost"

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

for file in "$HDRX" "$MERGE" "$NOISE" "$POST" "$PARAMS" "$INITIAL" "$VERSION"; do
    cp "$file" "$OUT/source_after/$(basename "$file")"
done

git diff --stat | tee "$OUT/change-summary.txt"
git diff --binary HEAD > "$OUT/combined-26157-metadata-and-26162-recovery.patch"

echo
echo "PASS: Obsolete 26158 local metrics removed from HdrxProcessor."
echo "PASS: All stale PyramidMerging getter calls removed."
echo "PASS: 26157 merge, noise model and post pipeline remain restored."
echo "PASS: 26159 burst-neutral validation preserved."
echo "PASS: 26160/26161 color diagnostics preserved."
echo "PASS: Adaptive Noise Model remains user-controlled; leave OFF."
echo "PASS: Capture, exposure, Video and RAW Video unchanged."

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
APK_COPY="$OUT/PhotonCamera-${NEW_VERSION}-motion-color-recovery-debug.apk"

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
echo "Failed 26161 patch: $OUT/working-tree-failed-26161-before-${NEW_BUILD}.patch"
echo "Combined patch:    $OUT/combined-26157-metadata-and-26162-recovery.patch"
echo "Build log:         $OUT/build-${NEW_BUILD}.log"
echo
echo "Expected markers:"
echo "  MOTION_26161_COLOR_RECOVERY"
echo "  MOTION_26161_FINAL_COLOR_PATH"
echo "  MOTION_COLOR_NEUTRAL_SELECTED"
echo "  MOTION_GAIN_MAP_CHANNELS"
echo
echo "Adaptive Noise Model: leave OFF."
echo
git status --short --untracked-files=no
echo
echo "Safe to open another terminal now."

trap - EXIT
