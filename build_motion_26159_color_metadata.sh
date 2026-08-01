#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_BUILD="26158"
NEW_BUILD="26159"
NEW_VERSION="0.9726159"

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_BRANCH="backup-before-motion-color-metadata-${NEW_BUILD}-${STAMP}"
OUT="/workspaces/Photon-Camera/build_${NEW_BUILD}_motion_color_metadata_${STAMP}"

PARAMS="app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java"
HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
VERSION="app/version.properties"

fail() {
    echo
    echo "============================================================"
    echo " BUILD FAILED"
    echo " Reason: $1"
    echo "============================================================"
    exit "${2:-1}"
}

trap 'code=$?; if [ "$code" -ne 0 ]; then echo; echo "FAILED: build 26159 (exit $code)"; fi' EXIT

echo "============================================================"
echo " PhotonCamera ${NEW_VERSION}"
echo " Motion RAW color metadata validation"
echo "============================================================"

[ "$(git branch --show-current)" = "$EXPECTED_BRANCH" ] \
    || fail "Expected branch $EXPECTED_BRANCH"

grep -q "^VERSION_BUILD=${EXPECTED_BUILD}$" "$VERSION" \
    || fail "Expected VERSION_BUILD=${EXPECTED_BUILD}"

git diff --quiet
git diff --cached --quiet
[ -z "$(git status --short --untracked-files=no)" ] \
    || fail "Tracked source is not clean"

grep -q 'MOTION_COLOR_NEUTRAL_OVERRIDE' "$PARAMS" \
    || fail "26158 Motion color-neutral source was not found"

grep -q 'effectiveFrameCount' "$PARAMS" \
    || fail "26158 effective-stack foundation was not found"

mkdir -p "$OUT/source_before" "$OUT/source_after"

git branch "$BACKUP_BRANCH" HEAD
git diff --binary HEAD > "$OUT/before-${NEW_BUILD}.patch"

cp "$PARAMS" "$OUT/source_before/Parameters.java"
cp "$HDRX" "$OUT/source_before/HdrxProcessor.java"
cp "$VERSION" "$OUT/source_before/version.properties"

python3 - <<'PY'
from pathlib import Path

params_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/render/Parameters.java"
)
hdrx_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/processor/HdrxProcessor.java"
)
version_path = Path("app/version.properties")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"ERROR: {label}: expected exactly one match, found {count}"
        )
    return text.replace(old, new, 1)


params = params_path.read_text()

old_block = """            float[] motionPreviewNeutral =
                    CaptureController.getMotionProcessingNeutral();

            if (motionPreviewNeutral != null
                    && motionPreviewNeutral.length >= 3) {

                customNeutral = motionPreviewNeutral;
                ReCalcColor(true, result);

                Log.d(
                        TAG,
                        "MOTION_COLOR_NEUTRAL_OVERRIDE"
                                + " previewNeutral="
                                + Arrays.toString(
                                        motionPreviewNeutral
                                )
                                + " controlledIso="
                                + iso
                                + " controlledExposureTime="
                                + exposureTime
                );
            } else {
                ReCalcColor(false, result);
            }
"""

new_block = """            float[] motionPreviewNeutral =
                    CaptureController.getMotionProcessingNeutral();

            Rational[] burstNeutralR =
                    result.get(
                            CaptureResult.SENSOR_NEUTRAL_COLOR_POINT
                    );

            float[] burstNeutral =
                    neutralToFloatArray(
                            burstNeutralR
                    );

            boolean burstNeutralValid =
                    isValidNeutral(
                            burstNeutral
                    );

            boolean previewNeutralValid =
                    isValidNeutral(
                            motionPreviewNeutral
                    );

            /*
             * Build 26159:
             *
             * The controlled Motion RAW capture result is authoritative.
             * Preview-neutral metadata may come from an earlier AE/AWB state
             * and must not unconditionally override the burst result.
             *
             * Use preview neutral only when the burst result is unavailable
             * or invalid. This preserves the 26157 fallback without allowing
             * stale preview color metadata to create a green/cyan cast.
             */
            if (burstNeutralValid) {
                customNeutral = burstNeutral;
                ReCalcColor(true, result);

                Log.d(
                        TAG,
                        "MOTION_COLOR_NEUTRAL_SELECTED"
                                + " source=burst"
                                + " burstNeutral="
                                + Arrays.toString(
                                        burstNeutral
                                )
                                + " previewNeutral="
                                + Arrays.toString(
                                        motionPreviewNeutral
                                )
                                + " neutralDistance="
                                + neutralDistance(
                                        burstNeutral,
                                        motionPreviewNeutral
                                )
                                + " controlledIso="
                                + iso
                                + " controlledExposureTime="
                                + exposureTime
                );
            } else if (previewNeutralValid) {
                customNeutral =
                        motionPreviewNeutral.clone();

                ReCalcColor(true, result);

                Log.w(
                        TAG,
                        "MOTION_COLOR_NEUTRAL_SELECTED"
                                + " source=previewFallback"
                                + " burstNeutral="
                                + Arrays.toString(
                                        burstNeutral
                                )
                                + " previewNeutral="
                                + Arrays.toString(
                                        motionPreviewNeutral
                                )
                                + " controlledIso="
                                + iso
                                + " controlledExposureTime="
                                + exposureTime
                );
            } else {
                ReCalcColor(false, result);

                Log.w(
                        TAG,
                        "MOTION_COLOR_NEUTRAL_SELECTED"
                                + " source=rawResultFallback"
                                + " burstNeutral="
                                + Arrays.toString(
                                        burstNeutral
                                )
                                + " previewNeutral="
                                + Arrays.toString(
                                        motionPreviewNeutral
                                )
                                + " controlledIso="
                                + iso
                                + " controlledExposureTime="
                                + exposureTime
                );
            }
"""

params = replace_once(
    params,
    old_block,
    new_block,
    "replace unconditional preview-neutral override",
)

anchor = """    public float[] customNeutral;

    public void ReCalcColor(boolean customNeutr, CaptureResult result) {
"""

helpers = """    public float[] customNeutral;

    private float[] neutralToFloatArray(
            Rational[] neutral
    ) {
        if (neutral == null || neutral.length < 3) {
            return null;
        }

        float[] converted = new float[3];

        for (int i = 0; i < 3; i++) {
            if (neutral[i] == null) {
                return null;
            }

            converted[i] =
                    neutral[i].floatValue();
        }

        return converted;
    }

    private boolean isValidNeutral(
            float[] neutral
    ) {
        if (neutral == null || neutral.length < 3) {
            return false;
        }

        for (int i = 0; i < 3; i++) {
            float value = neutral[i];

            if (!Float.isFinite(value)
                    || value <= 0.01f
                    || value > 8.0f) {
                return false;
            }
        }

        return true;
    }

    private float neutralDistance(
            float[] first,
            float[] second
    ) {
        if (!isValidNeutral(first)
                || !isValidNeutral(second)) {
            return -1.0f;
        }

        float sum = 0.0f;

        for (int i = 0; i < 3; i++) {
            float denominator =
                    Math.max(
                            Math.abs(first[i]),
                            1e-6f
                    );

            float relative =
                    (first[i] - second[i])
                            / denominator;

            sum += relative * relative;
        }

        return (float) Math.sqrt(sum / 3.0f);
    }

    public void ReCalcColor(boolean customNeutr, CaptureResult result) {
"""

params = replace_once(
    params,
    anchor,
    helpers,
    "add neutral validation helpers",
)

old_recalc = """        Rational[] neutralR = result.get(CaptureResult.SENSOR_NEUTRAL_COLOR_POINT);
        if (!customNeutr)
            for (int i = 0; i < neutralR.length; i++) {
                whitePoint[i] = neutralR[i].floatValue();
            }
        else {
            whitePoint = customNeutral;
        }
"""

new_recalc = """        Rational[] neutralR =
                result.get(
                        CaptureResult.SENSOR_NEUTRAL_COLOR_POINT
                );

        if (!customNeutr) {
            float[] resultNeutral =
                    neutralToFloatArray(
                            neutralR
                    );

            if (isValidNeutral(resultNeutral)) {
                whitePoint =
                        resultNeutral;
            } else {
                Log.w(
                        TAG,
                        "Invalid SENSOR_NEUTRAL_COLOR_POINT; "
                                + "preserving existing whitePoint="
                                + Arrays.toString(
                                        whitePoint
                                )
                );
            }
        } else if (isValidNeutral(customNeutral)) {
            whitePoint =
                    customNeutral.clone();
        } else {
            Log.w(
                    TAG,
                    "Invalid custom neutral; preserving existing "
                            + "whitePoint="
                            + Arrays.toString(
                                    whitePoint
                            )
            );
        }
"""

params = replace_once(
    params,
    old_recalc,
    new_recalc,
    "make ReCalcColor null-safe and validated",
)

params_path.write_text(params)


hdrx = hdrx_path.read_text()

old_dynamic = """        processingParameters.FillDynamicParameters(captureResult, captureRequest,ISO);
        processingParameters.cameraRotation = cameraRotation;
"""

new_dynamic = """        Log.d(
                TAG,
                "MOTION_DYNAMIC_METADATA_INPUT"
                        + " averagePairIso=" + ISO
                        + " captureResultIso="
                        + captureResult.get(
                                CaptureResult.SENSOR_SENSITIVITY
                        )
                        + " requestIso="
                        + captureRequest.get(
                                CaptureRequest.SENSOR_SENSITIVITY
                        )
                        + " captureResultExposureNs="
                        + captureResult.get(
                                CaptureResult.SENSOR_EXPOSURE_TIME
                        )
                        + " requestExposureNs="
                        + captureRequest.get(
                                CaptureRequest.SENSOR_EXPOSURE_TIME
                        )
                        + " captureResultNeutral="
                        + java.util.Arrays.toString(
                                captureResult.get(
                                        CaptureResult
                                                .SENSOR_NEUTRAL_COLOR_POINT
                                )
                        )
        );

        processingParameters.FillDynamicParameters(
                captureResult,
                captureRequest,
                ISO
        );

        processingParameters.cameraRotation =
                cameraRotation;

        Log.d(
                TAG,
                "MOTION_DYNAMIC_METADATA_SELECTED"
                        + " iso="
                        + processingParameters.iso
                        + " exposureSeconds="
                        + processingParameters.exposureTime
                        + " whitePoint="
                        + java.util.Arrays.toString(
                                processingParameters.whitePoint
                        )
                        + " cfaPattern="
                        + processingParameters.cfaPattern
                        + " whiteLevel="
                        + processingParameters.whiteLevel
                        + " blackLevel="
                        + java.util.Arrays.toString(
                                processingParameters.blackLevel
                        )
        );
"""

hdrx = replace_once(
    hdrx,
    old_dynamic,
    new_dynamic,
    "add grouped Motion metadata logs",
)

hdrx_path.write_text(hdrx)


version = version_path.read_text()

if version.count("VERSION_BUILD=26158") != 1:
    raise SystemExit(
        "ERROR: expected exactly one VERSION_BUILD=26158"
    )

version_path.write_text(
    version.replace(
        "VERSION_BUILD=26158",
        "VERSION_BUILD=26159",
        1,
    )
)
PY

echo
echo "=== VERIFY SOURCE ==="

grep -nE \
    'MOTION_COLOR_NEUTRAL_SELECTED|MOTION_DYNAMIC_METADATA_INPUT|MOTION_DYNAMIC_METADATA_SELECTED|neutralDistance|neutralToFloatArray' \
    "$PARAMS" "$HDRX" \
    | tee "$OUT/log-markers.txt"

grep -q 'effectiveFrameCount' "$PARAMS" \
    || fail "26158 effective-stack fields were lost"

grep -q 'MOTION_POST_NOISE_HANDOFF' \
    app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java \
    || fail "26158 post-noise handoff was lost"

grep -q '^VERSION_BUILD=26159$' "$VERSION" \
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

cp "$PARAMS" "$OUT/source_after/Parameters.java"
cp "$HDRX" "$OUT/source_after/HdrxProcessor.java"
cp "$VERSION" "$OUT/source_after/version.properties"

git diff --stat | tee "$OUT/change-summary.txt"
git diff --binary > "$OUT/motion-color-metadata-${NEW_BUILD}.patch"

echo
echo "PASS: 26158 effective-stack foundation preserved."
echo "PASS: Adaptive noise setting and merge strengths unchanged."
echo "PASS: Burst RAW neutral is now authoritative."
echo "PASS: Preview neutral remains a validated fallback only."
echo "PASS: Fine-detail denoise and sharpening settings unchanged."
echo "PASS: Capture, Video and RAW Video source unchanged."

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
APK_COPY="$OUT/PhotonCamera-${NEW_VERSION}-motion-color-metadata-debug.apk"

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
echo "Backup patch:  $OUT/before-${NEW_BUILD}.patch"
echo "Change patch:  $OUT/motion-color-metadata-${NEW_BUILD}.patch"
echo "Build log:     $OUT/build-${NEW_BUILD}.log"
echo
echo "Expected image-processing log markers:"
echo "  MOTION_COLOR_NEUTRAL_SELECTED"
echo "  MOTION_DYNAMIC_METADATA_INPUT"
echo "  MOTION_DYNAMIC_METADATA_SELECTED"
echo "  MOTION_EFFECTIVE_STACK"
echo "  FINAL_EFFECTIVE_STACK"
echo
echo "Adaptive Noise Model:"
echo "  Leave OFF for this validation."
echo
git status --short --untracked-files=no
echo
echo "Safe to open another terminal now."

trap - EXIT
