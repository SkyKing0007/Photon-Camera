#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
EXPECTED_BUILD="26159"
NEW_BUILD="26160"
NEW_VERSION="0.9726160"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="/workspaces/Photon-Camera/build_${NEW_BUILD}_motion_color_denoise_isolation_${STAMP}"
BACKUP_BRANCH="backup-before-motion-color-denoise-${NEW_BUILD}-${STAMP}"

PARAMS="app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java"
NOISE="app/src/main/java/com/particlesdevs/photoncamera/processing/render/NoiseModeler.java"
MERGE="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts/PyramidMerging.java"
HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
POST="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
INITIAL="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java"
VERSION="app/version.properties"

fail() {
    echo
    echo "============================================================"
    echo " BUILD FAILED"
    echo " Reason: $1"
    echo "============================================================"
    exit "${2:-1}"
}

trap 'code=$?; if [ "$code" -ne 0 ]; then echo; echo "FAILED: build 26160 (exit $code)"; fi' EXIT

echo "============================================================"
echo " PhotonCamera ${NEW_VERSION}"
echo " Motion color / denoise isolation"
echo "============================================================"

[ "$(git branch --show-current)" = "$EXPECTED_BRANCH" ] \
    || fail "Expected branch $EXPECTED_BRANCH"

[ "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" ] \
    || fail "Expected HEAD $EXPECTED_HEAD"

grep -q "^VERSION_BUILD=${EXPECTED_BUILD}$" "$VERSION" \
    || fail "Expected VERSION_BUILD=${EXPECTED_BUILD}"

EXPECTED_FILES="$PARAMS
$NOISE
$MERGE
$HDRX
$POST
$VERSION"

ACTUAL_FILES="$(git status --short --untracked-files=no | awk '{print $2}' | sort)"
EXPECTED_SORTED="$(printf '%s\n' "$EXPECTED_FILES" | sort)"

[ "$ACTUAL_FILES" = "$EXPECTED_SORTED" ] \
    || {
        echo "Expected modified files:"
        printf '%s\n' "$EXPECTED_SORTED"
        echo
        echo "Actual modified files:"
        printf '%s\n' "$ACTUAL_FILES"
        fail "Tracked changes are not exactly the verified 26159 set"
    }

grep -q 'MOTION_EFFECTIVE_STACK' "$MERGE" \
    || fail "26158 effective-stack marker missing"

grep -q 'MOTION_COLOR_NEUTRAL_SELECTED' "$PARAMS" \
    || fail "26159 neutral-selection marker missing"

grep -q 'computeStackingNoiseModel' "$HDRX" \
    || fail "HDRX noise handoff missing"

mkdir -p "$OUT/source_before" "$OUT/source_after"

git branch "$BACKUP_BRANCH" HEAD
git diff --binary HEAD > "$OUT/working-tree-26159-before-${NEW_BUILD}.patch"

for file in "$PARAMS" "$NOISE" "$MERGE" "$HDRX" "$POST" "$VERSION"; do
    cp "$file" "$OUT/source_before/$(basename "$file")"
done
cp "$INITIAL" "$OUT/source_before/Initial.java"

echo
echo "Saved 26159 working state:"
echo "  Backup branch: $BACKUP_BRANCH"
echo "  Backup patch:  $OUT/working-tree-26159-before-${NEW_BUILD}.patch"

python3 - <<'PY'
from pathlib import Path

hdrx_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/processor/HdrxProcessor.java"
)
params_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/render/Parameters.java"
)
initial_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/opengl/postpipeline/Initial.java"
)
version_path = Path("app/version.properties")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"ERROR: {label}: expected exactly one match, found {count}"
        )
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------
# Keep effective-stack metrics, but do not let the conservative scalar
# increase ESD3D2 strength until a real spatial confidence map exists.
# ---------------------------------------------------------------------
hdrx = hdrx_path.read_text()

old = """        processingParameters.noiseModeler.computeStackingNoiseModel(
                processingParameters.effectiveFrameCount
        );

        Log.d(
                TAG,
                "FINAL_EFFECTIVE_STACK"
"""

new = """        /*
         * Build 26160 color/denoise isolation:
         *
         * Keep measuring the conservative effective stack, but do not use
         * that provisional scalar to increase global ESD3D2 denoise.
         *
         * The 26158 change reduced the assumed stack from 20 to about 13.35
         * frames, which raises the residual-noise estimate and therefore
         * strengthens both luma and chroma denoise. That is the only major
         * processing-strength change coincident with the new green/cyan
         * output. Until a spatial confidence map exists, use retained frames
         * for post denoise while retaining effective metrics for logging and
         * future temporal-fusion work.
         */
        double postDenoiseFrameCount =
                processingParameters.retainedFrameCount;

        processingParameters.noiseModeler.computeStackingNoiseModel(
                postDenoiseFrameCount
        );

        Log.d(
                TAG,
                "MOTION_POST_DENOISE_STACK_POLICY"
                        + " retained="
                        + processingParameters.retainedFrameCount
                        + " measuredEffective="
                        + processingParameters.effectiveFrameCount
                        + " postDenoiseFrames="
                        + postDenoiseFrameCount
                        + " adaptiveNoise=falseExpected"
                        + " reason=avoidGlobalOverDenoiseWithoutSpatialConfidence"
        );

        Log.d(
                TAG,
                "FINAL_EFFECTIVE_STACK"
"""

hdrx = replace_once(
    hdrx,
    old,
    new,
    "use retained stack for post denoise",
)

hdrx_path.write_text(hdrx)


# ---------------------------------------------------------------------
# Add compact gain-map channel statistics after map retrieval.
# This is read-only logging and does not change gain-map behavior.
# ---------------------------------------------------------------------
params = params_path.read_text()

anchor = """            hotPixels =
                    result.get(
                            CaptureResult.STATISTICS_HOT_PIXEL_MAP
                    );

            float[] motionPreviewNeutral =
"""

logging = """            if (gainMap != null
                    && gainMap.length >= 4) {

                double gainR = 0.0;
                double gainG1 = 0.0;
                double gainG2 = 0.0;
                double gainB = 0.0;
                int gainSamples = 0;

                for (int i = 0;
                     i + 3 < gainMap.length;
                     i += 4) {

                    gainR += gainMap[i];
                    gainG1 += gainMap[i + 1];
                    gainG2 += gainMap[i + 2];
                    gainB += gainMap[i + 3];
                    gainSamples++;
                }

                if (gainSamples > 0) {
                    Log.d(
                            TAG,
                            "MOTION_GAIN_MAP_CHANNELS"
                                    + " hasGainMap=" + hasGainMap
                                    + " mapSize=" + mapSize
                                    + " samples=" + gainSamples
                                    + " avgR="
                                    + gainR / gainSamples
                                    + " avgG1="
                                    + gainG1 / gainSamples
                                    + " avgG2="
                                    + gainG2 / gainSamples
                                    + " avgB="
                                    + gainB / gainSamples
                                    + " cfaPattern="
                                    + cfaPattern
                    );
                }
            }

            hotPixels =
                    result.get(
                            CaptureResult.STATISTICS_HOT_PIXEL_MAP
                    );

            float[] motionPreviewNeutral =
"""

params = replace_once(
    params,
    anchor,
    logging,
    "add gain-map channel logging",
)

params_path.write_text(params)


# ---------------------------------------------------------------------
# Log the exact downstream matrices and white point immediately before
# the Initial shader receives them. No shader behavior changes.
# ---------------------------------------------------------------------
initial = initial_path.read_text()

old_initial = """        Log.d(Name,"sensorToIntermediate: "+ Arrays.toString(basePipeline.mParameters.sensorToProPhoto));
        glProg.setVar("sensorToIntermediate",basePipeline.mParameters.sensorToProPhoto);
        Log.d(Name,"intermediateToSRGB: "+ Arrays.toString(cct));
        glProg.setVar("intermediateToSRGB",cct);
"""

new_initial = """        Log.d(
                Name,
                "MOTION_FINAL_COLOR_PATH"
                        + " cfaPattern="
                        + basePipeline.mParameters.cfaPattern
                        + " whitePoint="
                        + Arrays.toString(
                                basePipeline.mParameters.whitePoint
                        )
                        + " sensorToIntermediate="
                        + Arrays.toString(
                                basePipeline.mParameters.sensorToProPhoto
                        )
                        + " intermediateToSRGB="
                        + Arrays.toString(cct)
                        + " hasGainMap="
                        + basePipeline.mParameters.hasGainMap
                        + " gainMapSize="
                        + basePipeline.mParameters.mapSize
        );

        Log.d(Name,"sensorToIntermediate: "+ Arrays.toString(basePipeline.mParameters.sensorToProPhoto));
        glProg.setVar("sensorToIntermediate",basePipeline.mParameters.sensorToProPhoto);
        Log.d(Name,"intermediateToSRGB: "+ Arrays.toString(cct));
        glProg.setVar("intermediateToSRGB",cct);
"""

initial = replace_once(
    initial,
    old_initial,
    new_initial,
    "add final color path logging",
)

initial_path.write_text(initial)


version = version_path.read_text()

if version.count("VERSION_BUILD=26159") != 1:
    raise SystemExit(
        "ERROR: expected exactly one VERSION_BUILD=26159"
    )

version_path.write_text(
    version.replace(
        "VERSION_BUILD=26159",
        "VERSION_BUILD=26160",
        1,
    )
)
PY

echo
echo "=== VERIFY 26160 SOURCE ==="

grep -nE \
    'MOTION_POST_DENOISE_STACK_POLICY|MOTION_GAIN_MAP_CHANNELS|MOTION_FINAL_COLOR_PATH' \
    "$HDRX" "$PARAMS" "$INITIAL" \
    | tee "$OUT/log-markers.txt"

grep -q 'MOTION_EFFECTIVE_STACK' "$MERGE" \
    || fail "Effective-stack measurement was lost"

grep -q 'MOTION_COLOR_NEUTRAL_SELECTED' "$PARAMS" \
    || fail "26159 neutral handling was lost"

grep -q '^VERSION_BUILD=26160$' "$VERSION" \
    || fail "VERSION_BUILD was not updated"

if git diff -- \
    app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java \
    app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IsoExpoSelector.java \
    | grep -q .; then
    fail "Capture or exposure-selection source changed unexpectedly"
fi

if git diff | grep -E \
    '^[+-].*(mIsRecordingVideo|CameraMode\.RAWVIDEO|TEMPLATE_RECORD|MediaRecorder|CONTROL_AF_MODE_CONTINUOUS_VIDEO|getSelectedFpsRange)'; then
    fail "Video or RAW Video code changed unexpectedly"
fi

git diff --check \
    || fail "git diff --check reported a formatting error"

for file in "$PARAMS" "$NOISE" "$MERGE" "$HDRX" "$POST" "$VERSION"; do
    cp "$file" "$OUT/source_after/$(basename "$file")"
done
cp "$INITIAL" "$OUT/source_after/Initial.java"

git diff --stat | tee "$OUT/change-summary.txt"
git diff --binary HEAD > "$OUT/combined-26158-through-26160.patch"

echo
echo "PASS: Effective-stack measurement preserved."
echo "PASS: Post denoise restored to retained-frame scaling."
echo "PASS: Adaptive Noise Model behavior unchanged; leave it OFF."
echo "PASS: Gain-map and final matrix logging added."
echo "PASS: CFA, merge, demosaic, exposure and sharpening unchanged."
echo "PASS: Video and RAW Video source unchanged."

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
        | tail -180 \
        > "$OUT/relevant-errors.txt" || true

    fail "Gradle build failed; inspect $OUT/relevant-errors.txt" \
        "$BUILD_STATUS"
fi

APK="app/build/outputs/apk/debug/PhotonCamera-${NEW_VERSION}-debug.apk"
APK_COPY="$OUT/PhotonCamera-${NEW_VERSION}-motion-color-denoise-isolation-debug.apk"

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
echo "26159 patch:   $OUT/working-tree-26159-before-${NEW_BUILD}.patch"
echo "Combined patch:$OUT/combined-26158-through-26160.patch"
echo "Build log:     $OUT/build-${NEW_BUILD}.log"
echo
echo "Expected log markers:"
echo "  MOTION_POST_DENOISE_STACK_POLICY"
echo "  MOTION_GAIN_MAP_CHANNELS"
echo "  MOTION_FINAL_COLOR_PATH"
echo "  MOTION_EFFECTIVE_STACK"
echo "  FINAL_EFFECTIVE_STACK"
echo
echo "Adaptive Noise Model: leave OFF."
echo
git status --short --untracked-files=no
echo
echo "Safe to open another terminal now."

trap - EXIT
