#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
EXPECTED_BUILD="26164"
NEW_BUILD="26165"
NEW_VERSION="0.9726165"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="/workspaces/Photon-Camera/build_${NEW_BUILD}_motion_post_only_color_stability_${STAMP}"
BACKUP_BRANCH="backup-before-motion-post-only-${NEW_BUILD}-${STAMP}"

CAPTURE="app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
PARAMS="app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java"
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

trap 'code=$?; if [ "$code" -ne 0 ]; then echo; echo "FAILED: build 26165 (exit $code)"; echo "Workspace: $OUT"; fi' EXIT

echo "============================================================"
echo " PhotonCamera ${NEW_VERSION}"
echo " Motion homogeneous RAW color-stability checkpoint"
echo "============================================================"

[ "$(git branch --show-current)" = "$EXPECTED_BRANCH" ] \
    || fail "Expected branch $EXPECTED_BRANCH"

[ "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" ] \
    || fail "Expected HEAD $EXPECTED_HEAD"

grep -q "^VERSION_BUILD=${EXPECTED_BUILD}$" "$VERSION" \
    || fail "Expected VERSION_BUILD=${EXPECTED_BUILD}"

grep -Fq 'MOTION_COLOR_REFERENCE_METADATA' "$PARAMS" \
    || fail "Expected 26164 result-based color path missing"

grep -Fq \
    'pRGB = corr*sensorToIntermediate*(pRGB*neutralPoint);' \
    "$SHADER" \
    || fail "Expected original Photon shader path missing"

grep -Fq 'PREBUFFER_TOP_UP' "$CAPTURE" \
    || fail "Motion hybrid top-up code missing"

grep -Fq \
    'completedFrames =' \
    "$CAPTURE" \
    || fail "Motion finalized-frame handoff missing"

mkdir -p "$OUT/source_before" "$OUT/source_after"

git branch "$BACKUP_BRANCH" HEAD
git diff --binary HEAD > "$OUT/working-tree-before-${NEW_BUILD}.patch"

cp "$CAPTURE" "$OUT/source_before/CaptureController.java"
cp "$VERSION" "$OUT/source_before/version.properties"

python3 - <<'PY'
from pathlib import Path

capture_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "capture/CaptureController.java"
)
version_path = Path("app/version.properties")

capture = capture_path.read_text()

old_preselection = """        final int preFramesToUse =
                Math.min(
                        maximumPreFrames,
                        candidates.size()
                );
"""

new_preselection = """        /*
         * Build 26165 color-stability checkpoint:
         *
         * The rolling RAW candidates are produced by the live
         * TEMPLATE_PREVIEW request with preview + RAW targets, while the
         * controlled post-shutter RAWs use TEMPLATE_STILL_CAPTURE with a RAW
         * target. Mixing those two HAL paths has produced intermittent
         * green/cyan output even when exposure and AWB metadata appear close.
         *
         * Keep collecting and validating the rolling ring, but do not feed
         * its frames into HDRX until every RAW carries its own complete
         * CaptureResult/CaptureRequest and both paths are proven compatible.
         * The requested stack is therefore filled with homogeneous
         * post-shutter still-capture RAWs.
         */
        final int preFramesToUse = 0;
"""

if capture.count(old_preselection) != 1:
    raise SystemExit(
        "ERROR: expected exactly one Motion preFramesToUse block, found "
        + str(capture.count(old_preselection))
    )

capture = capture.replace(
    old_preselection,
    new_preselection,
    1,
)

old_log_tail = """                        + " maxPre="
                        + maximumPreFrames
        );
"""

new_log_tail = """                        + " maxPre="
                        + maximumPreFrames
                        + " colorStabilityPostOnly=true"
                        + " rollingCandidatesStillCollected="
                        + candidates.size()
        );

        Log.d(
                MOTION_LOG_TAG,
                "MOTION_26165_HOMOGENEOUS_RAW_STACK"
                        + " preframesContributing=0"
                        + " postframesRequested="
                        + mMotionPostShutterFrameOverride
                        + " previewTemplateRawExcluded=true"
                        + " stillTemplateRawOnly=true"
                        + " shutterPolicyUnchanged=true"
        );
"""

if capture.count(old_log_tail) != 1:
    raise SystemExit(
        "ERROR: expected exactly one PREBUFFER_TOP_UP log tail, found "
        + str(capture.count(old_log_tail))
    )

capture = capture.replace(
    old_log_tail,
    new_log_tail,
    1,
)

capture_path.write_text(capture)

version = version_path.read_text()

if version.count("VERSION_BUILD=26164") != 1:
    raise SystemExit(
        "ERROR: expected exactly one VERSION_BUILD=26164"
    )

version_path.write_text(
    version.replace(
        "VERSION_BUILD=26164",
        "VERSION_BUILD=26165",
        1,
    )
)
PY

echo
echo "=== VERIFY 26165 SOURCE ==="

grep -Fq 'final int preFramesToUse = 0;' "$CAPTURE" \
    || fail "Post-only contribution policy missing"

grep -Fq 'MOTION_26165_HOMOGENEOUS_RAW_STACK' "$CAPTURE" \
    || fail "26165 diagnostic marker missing"

grep -Fq 'colorStabilityPostOnly=true' "$CAPTURE" \
    || fail "26165 top-up diagnostic missing"

grep -Fq 'MOTION_PHOTON_ENERGY_POLICY' "$CAPTURE" \
    || fail "Motion shutter/energy policy was lost"

grep -Fq 'CONTROLLED_ACTUAL_EXPO_PAIR' "$CAPTURE" \
    || fail "Actual exposure metadata path was lost"

grep -Fq 'MOTION_COLOR_REFERENCE_METADATA' "$PARAMS" \
    || fail "26164 standard color path was lost"

grep -Fq \
    'pRGB = corr*sensorToIntermediate*(pRGB*neutralPoint);' \
    "$SHADER" \
    || fail "Original Photon shader path was lost"

grep -q '^VERSION_BUILD=26165$' "$VERSION" \
    || fail "VERSION_BUILD was not updated"

# This build must not alter exposure selection or video paths.
if git diff -- \
    app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IsoExpoSelector.java \
    | grep -q .; then
    fail "IsoExpoSelector changed unexpectedly"
fi

if git diff | grep -E \
    '^[+-].*(mIsRecordingVideo|CameraMode\.RAWVIDEO|TEMPLATE_RECORD|MediaRecorder|CONTROL_AF_MODE_CONTINUOUS_VIDEO|getSelectedFpsRange)'; then
    fail "Video or RAW Video source changed unexpectedly"
fi

git diff --check \
    || fail "git diff --check reported a formatting error"

cp "$CAPTURE" "$OUT/source_after/CaptureController.java"
cp "$VERSION" "$OUT/source_after/version.properties"

git diff --stat | tee "$OUT/change-summary.txt"
git diff --binary HEAD > "$OUT/combined-${NEW_BUILD}-post-only-color-stability.patch"

echo
echo "PASS: Rolling RAW candidates are still collected and logged."
echo "PASS: Preview-template RAWs no longer contribute to the HDR merge."
echo "PASS: Motion now requests all 20 frames through the controlled still path."
echo "PASS: Shutter and exposure-energy policy preserved."
echo "PASS: 26164 standard color calculation and original shader preserved."
echo "PASS: Video and RAW Video unchanged."
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

    fail "Gradle build failed; inspect $OUT/relevant-errors.txt" \
        "$BUILD_STATUS"
fi

APK="$(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | head -n 1)"

[ -n "$APK" ] && [ -f "$APK" ] \
    || fail "Debug APK was not created"

APK_COPY="$OUT/PhotonCamera-${NEW_VERSION}-motion-post-only-color-stability-debug.apk"

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
echo "Combined patch:$OUT/combined-${NEW_BUILD}-post-only-color-stability.patch"
echo "Build log:     $OUT/build-${NEW_BUILD}.log"
echo
echo "Expected capture log:"
echo "  MOTION_26165_HOMOGENEOUS_RAW_STACK preframesContributing=0 postframesRequested=20"
echo
echo "Adaptive Noise Model: leave OFF."
echo
git status --short --untracked-files=no
echo
echo "Safe to open another terminal now."

trap - EXIT
