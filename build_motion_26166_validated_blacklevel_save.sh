#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
EXPECTED_BUILD="26165"
NEW_BUILD="26166"
NEW_VERSION="0.9726166"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="/workspaces/Photon-Camera/build_${NEW_BUILD}_validated_blacklevel_save_completion_${STAMP}"
BACKUP_BRANCH="backup-before-motion-blacklevel-${NEW_BUILD}-${STAMP}"

CAPTURE="app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
PARAMS="app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java"
HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
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

trap 'code=$?; if [ "$code" -ne 0 ]; then echo; echo "FAILED: build 26166 (exit $code)"; echo "Workspace: $OUT"; fi' EXIT

echo "============================================================"
echo " PhotonCamera ${NEW_VERSION}"
echo " Validated Motion black level + save completion"
echo "============================================================"

[ "$(git branch --show-current)" = "$EXPECTED_BRANCH" ] \
    || fail "Expected branch $EXPECTED_BRANCH"

[ "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" ] \
    || fail "Expected HEAD $EXPECTED_HEAD"

grep -q "^VERSION_BUILD=${EXPECTED_BUILD}$" "$VERSION" \
    || fail "Expected VERSION_BUILD=${EXPECTED_BUILD}"

grep -Fq 'MOTION_26165_HOMOGENEOUS_RAW_STACK' "$CAPTURE" \
    || fail "Expected 26165 homogeneous Motion stack missing"

grep -Fq 'MOTION_COLOR_REFERENCE_METADATA' "$PARAMS" \
    || fail "Expected 26164 standard color path missing"

grep -Fq \
    'pRGB = corr*sensorToIntermediate*(pRGB*neutralPoint);' \
    "$SHADER" \
    || fail "Expected original Photon color shader missing"

grep -Fq \
    'processingEventsListener.onProcessingFinished("HdrX JPG Processing Finished");' \
    "$HDRX" \
    || fail "Expected HDRX completion callback missing"

mkdir -p "$OUT/source_before" "$OUT/source_after"

echo
echo "=== CREATE BACKUP BRANCH AND PATCH ==="

git branch "$BACKUP_BRANCH" HEAD
git diff --binary HEAD > "$OUT/working-tree-before-${NEW_BUILD}.patch"

for file in "$CAPTURE" "$PARAMS" "$HDRX" "$SHADER" "$VERSION"; do
    cp "$file" "$OUT/source_before/$(basename "$file")"
done

echo "Backup branch: $BACKUP_BRANCH"
echo "Backup patch:  $OUT/working-tree-before-${NEW_BUILD}.patch"

echo
echo "=== APPLY 26166 SOURCE CHANGES ==="

python3 - <<'PY'
from pathlib import Path

capture_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "capture/CaptureController.java"
)
params_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/render/Parameters.java"
)
hdrx_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/processor/HdrxProcessor.java"
)
version_path = Path("app/version.properties")

capture = capture_path.read_text()
params = params_path.read_text()
hdrx = hdrx_path.read_text()
version = version_path.read_text()


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"ERROR: {label}: expected exactly one match, found {count}"
        )
    return text.replace(old, new, 1)


old_fields = """    private final HashMap<Long, Integer> mMotionBurstSensitivity =
            new HashMap<>();

    /*
     * Controlled Motion pre-buffer. The visible preview remains under Xiaomi
"""

new_fields = """    private final HashMap<Long, Integer> mMotionBurstSensitivity =
            new HashMap<>();

    /*
     * Build 26166:
     *
     * Keep the four-channel dynamic black level belonging to every
     * controlled RAW timestamp. Processing uses a validated burst median,
     * never an arbitrary last-frame value.
     */
    private final HashMap<Long, float[]> mMotionBurstDynamicBlackLevel =
            new HashMap<>();

    private static volatile float[] mMotionValidatedBlackLevel = null;
    private static volatile String mMotionValidatedBlackLevelSource =
            "unavailable";

    public static float[] getMotionValidatedBlackLevel() {
        float[] selected = mMotionValidatedBlackLevel;
        return selected != null ? selected.clone() : null;
    }

    public static String getMotionValidatedBlackLevelSource() {
        return mMotionValidatedBlackLevelSource;
    }

    /*
     * Controlled Motion pre-buffer. The visible preview remains under Xiaomi
"""

capture = replace_once(
    capture,
    old_fields,
    new_fields,
    "Motion black-level metadata fields",
)

helper_anchor = """    private void tryMatchControlledMotionFrameLocked(
            long timestamp
    ) {
"""

helper_code = r"""    private float[] getMotionStaticBlackLevel() {
        int[] staticValues = new int[]{64, 64, 64, 64};

        CameraCharacteristics characteristics =
                getActiveCameraCharacteristics();

        if (characteristics != null) {
            android.hardware.camera2.params.BlackLevelPattern pattern =
                    characteristics.get(
                            CameraCharacteristics
                                    .SENSOR_BLACK_LEVEL_PATTERN
                    );

            if (pattern != null) {
                pattern.copyTo(staticValues, 0);
            }
        }

        return new float[]{
                staticValues[0],
                staticValues[1],
                staticValues[2],
                staticValues[3]
        };
    }

    private int getMotionStaticWhiteLevel() {
        CameraCharacteristics characteristics =
                getActiveCameraCharacteristics();

        if (characteristics != null) {
            Integer whiteLevel =
                    characteristics.get(
                            CameraCharacteristics
                                    .SENSOR_INFO_WHITE_LEVEL
                    );

            if (whiteLevel != null && whiteLevel > 0) {
                return whiteLevel;
            }
        }

        return 1023;
    }

    private boolean isValidMotionDynamicBlackLevel(
            float[] candidate,
            int whiteLevel
    ) {
        if (candidate == null || candidate.length < 4) {
            return false;
        }

        float maximumAllowed =
                Math.max(
                        256.0f,
                        Math.max(1, whiteLevel) * 0.25f
                );

        float minimum = Float.POSITIVE_INFINITY;
        float maximum = Float.NEGATIVE_INFINITY;

        for (int i = 0; i < 4; i++) {
            float value = candidate[i];

            if (!Float.isFinite(value)
                    || value < 0.0f
                    || value >= maximumAllowed) {
                return false;
            }

            minimum = Math.min(minimum, value);
            maximum = Math.max(maximum, value);
        }

        float maximumChannelSpread =
                Math.max(
                        64.0f,
                        Math.max(1, whiteLevel) * 0.08f
                );

        return maximum - minimum <= maximumChannelSpread;
    }

    private float medianMotionValue(
            ArrayList<Float> values
    ) {
        Collections.sort(values);

        int size = values.size();
        int middle = size / 2;

        if ((size & 1) == 1) {
            return values.get(middle);
        }

        return (
                values.get(middle - 1)
                        + values.get(middle)
        ) * 0.5f;
    }

    private void selectMotionValidatedBlackLevelLocked(
            ArrayList<ImageFrame> completedFrames
    ) {
        float[] staticBlackLevel = getMotionStaticBlackLevel();
        int whiteLevel = getMotionStaticWhiteLevel();

        ArrayList<float[]> samples = new ArrayList<>();

        for (ImageFrame frame : completedFrames) {
            if (frame == null) {
                continue;
            }

            float[] sample =
                    mMotionBurstDynamicBlackLevel.get(
                            frame.timestamp
                    );

            if (isValidMotionDynamicBlackLevel(
                    sample,
                    whiteLevel
            )) {
                samples.add(sample.clone());
            }
        }

        int requiredSamples =
                Math.max(
                        3,
                        (int) Math.ceil(
                                completedFrames.size() * 0.75
                        )
                );

        float[] selected = staticBlackLevel.clone();
        String source = "staticFallback";
        String reason = "insufficientSamples";

        float maximumObservedRange =
                Float.POSITIVE_INFINITY;

        if (samples.size() >= requiredSamples) {
            float[] median = new float[4];
            maximumObservedRange = 0.0f;

            for (int channel = 0; channel < 4; channel++) {
                ArrayList<Float> channelValues =
                        new ArrayList<>();

                float channelMinimum =
                        Float.POSITIVE_INFINITY;
                float channelMaximum =
                        Float.NEGATIVE_INFINITY;

                for (float[] sample : samples) {
                    float value = sample[channel];

                    channelValues.add(value);
                    channelMinimum =
                            Math.min(channelMinimum, value);
                    channelMaximum =
                            Math.max(channelMaximum, value);
                }

                median[channel] =
                        medianMotionValue(channelValues);

                maximumObservedRange =
                        Math.max(
                                maximumObservedRange,
                                channelMaximum - channelMinimum
                        );
            }

            float medianMinimum =
                    Math.min(
                            Math.min(median[0], median[1]),
                            Math.min(median[2], median[3])
                    );

            float medianMaximum =
                    Math.max(
                            Math.max(median[0], median[1]),
                            Math.max(median[2], median[3])
                    );

            float stabilityLimit =
                    Math.max(
                            8.0f,
                            whiteLevel * 0.02f
                    );

            float channelSpreadLimit =
                    Math.max(
                            64.0f,
                            whiteLevel * 0.08f
                    );

            boolean stable =
                    maximumObservedRange <= stabilityLimit;

            boolean plausible =
                    isValidMotionDynamicBlackLevel(
                            median,
                            whiteLevel
                    )
                            && medianMaximum - medianMinimum
                                    <= channelSpreadLimit;

            if (stable && plausible) {
                selected = median;
                source = "dynamicMedian";
                reason = "validated";
            } else if (!stable) {
                reason = "burstVariation";
            } else {
                reason = "implausibleMedian";
            }
        }

        mMotionValidatedBlackLevel = selected.clone();
        mMotionValidatedBlackLevelSource = source;

        Log.d(
                MOTION_LOG_TAG,
                "MOTION_26166_BLACK_LEVEL_SELECTED"
                        + " source=" + source
                        + " reason=" + reason
                        + " samples="
                        + samples.size()
                        + "/"
                        + completedFrames.size()
                        + " required="
                        + requiredSamples
                        + " selected="
                        + Arrays.toString(selected)
                        + " static="
                        + Arrays.toString(staticBlackLevel)
                        + " maxObservedRange="
                        + maximumObservedRange
                        + " whiteLevel="
                        + whiteLevel
                        + " cfaOrder=R_G1_G2_B"
        );
    }

"""

capture = replace_once(
    capture,
    helper_anchor,
    helper_code + helper_anchor,
    "Motion black-level helper insertion",
)

old_callback = """                                    mMotionBurstSensitivity.put(
                                            (long) time, iso);

                                    tryMatchControlledMotionFrameLocked(
                                            (long) time
                                    );
"""

new_callback = """                                    mMotionBurstSensitivity.put(
                                            (long) time, iso);

                                    float[] dynamicBlackLevel =
                                            result.get(
                                                    CaptureResult
                                                            .SENSOR_DYNAMIC_BLACK_LEVEL
                                            );

                                    Integer dynamicWhiteLevel =
                                            result.get(
                                                    CaptureResult
                                                            .SENSOR_DYNAMIC_WHITE_LEVEL
                                            );

                                    int validationWhiteLevel =
                                            dynamicWhiteLevel != null
                                                    && dynamicWhiteLevel > 0
                                                    ? dynamicWhiteLevel
                                                    : getMotionStaticWhiteLevel();

                                    boolean dynamicBlackLevelValid =
                                            isValidMotionDynamicBlackLevel(
                                                    dynamicBlackLevel,
                                                    validationWhiteLevel
                                            );

                                    if (dynamicBlackLevelValid) {
                                        mMotionBurstDynamicBlackLevel.put(
                                                (long) time,
                                                dynamicBlackLevel.clone()
                                        );
                                    } else {
                                        mMotionBurstDynamicBlackLevel.remove(
                                                (long) time
                                        );
                                    }

                                    Log.d(
                                            MOTION_LOG_TAG,
                                            "CONTROLLED_BLACK_LEVEL"
                                                    + " timestamp=" + time
                                                    + " dynamic="
                                                    + Arrays.toString(
                                                            dynamicBlackLevel
                                                    )
                                                    + " valid="
                                                    + dynamicBlackLevelValid
                                                    + " static="
                                                    + Arrays.toString(
                                                            getMotionStaticBlackLevel()
                                                    )
                                                    + " whiteLevel="
                                                    + validationWhiteLevel
                                                    + " cfaOrder=R_G1_G2_B"
                                    );

                                    tryMatchControlledMotionFrameLocked(
                                            (long) time
                                    );
"""

capture = replace_once(
    capture,
    old_callback,
    new_callback,
    "controlled result black-level collection",
)

old_finalize = """                completedFrames.addAll(
                        mMotionBurstFrames
                );

                mMotionPreselectedFrames.clear();
"""

new_finalize = """                completedFrames.addAll(
                        mMotionBurstFrames
                );

                selectMotionValidatedBlackLevelLocked(
                        completedFrames
                );

                mMotionPreselectedFrames.clear();
"""

capture = replace_once(
    capture,
    old_finalize,
    new_finalize,
    "validated black-level finalization",
)

old_new_burst = """                    mMotionBurstExposureTimeNs.clear();
                    mMotionBurstSensitivity.clear();
                    mMotionBurstFinalized.set(false);
"""

new_new_burst = """                    mMotionBurstExposureTimeNs.clear();
                    mMotionBurstSensitivity.clear();
                    mMotionBurstDynamicBlackLevel.clear();
                    mMotionValidatedBlackLevel = null;
                    mMotionValidatedBlackLevelSource =
                            "collecting";
                    mMotionBurstFinalized.set(false);
"""

capture = replace_once(
    capture,
    old_new_burst,
    new_new_burst,
    "new Motion burst black-level reset",
)

old_recovery = """            mMotionBurstExposureTimeNs.clear();
            mMotionBurstSensitivity.clear();
            mMotionPreselectedExposureTimeNs.clear();
"""

new_recovery = """            mMotionBurstExposureTimeNs.clear();
            mMotionBurstSensitivity.clear();
            mMotionBurstDynamicBlackLevel.clear();
            mMotionValidatedBlackLevel = null;
            mMotionValidatedBlackLevelSource =
                    "recoveryCleared";
            mMotionPreselectedExposureTimeNs.clear();
"""

capture = replace_once(
    capture,
    old_recovery,
    new_recovery,
    "Motion recovery black-level reset",
)

old_finally = """                mMotionPostShutterFrameOverride = 0;
                mMotionCombinedRequestedFrames = 0;

                /*
"""

new_finally = """                mMotionPostShutterFrameOverride = 0;
                mMotionCombinedRequestedFrames = 0;

                synchronized (mMotionBurstLock) {
                    mMotionBurstDynamicBlackLevel.clear();
                }

                mMotionValidatedBlackLevel = null;
                mMotionValidatedBlackLevelSource =
                        "processingComplete";

                /*
"""

capture = replace_once(
    capture,
    old_finally,
    new_finally,
    "post-processing black-level cleanup",
)

capture_path.write_text(capture)


old_dynamic = """            if(useDynamicBlackLevel) {
                float[] dynbl = result.get(CaptureResult.SENSOR_DYNAMIC_BLACK_LEVEL);
                if (dynbl != null) {
                    System.arraycopy(dynbl, 0, blackLevel, 0, 4);
                    usedDynamic = true;
                }
            }
"""

new_dynamic = """            /*
             * Build 26166:
             *
             * Motion uses a validated median collected from the timestamp-
             * matched controlled burst. The global user setting remains
             * unchanged for Photo, Night, Video and RAW Video.
             */
            float[] motionValidatedBlackLevel =
                    CaptureController
                            .getMotionValidatedBlackLevel();

            boolean motionBlackLevelValid =
                    motionValidatedBlackLevel != null
                            && motionValidatedBlackLevel.length >= 4;

            if (motionBlackLevelValid) {
                float maximumAllowed =
                        Math.max(
                                256.0f,
                                Math.max(1, whiteLevel) * 0.25f
                        );

                for (int i = 0; i < 4; i++) {
                    float value =
                            motionValidatedBlackLevel[i];

                    if (!Float.isFinite(value)
                            || value < 0.0f
                            || value >= maximumAllowed) {
                        motionBlackLevelValid = false;
                        break;
                    }
                }
            }

            if (PhotonCamera.getSettings().selectedMode
                    == com.particlesdevs.photoncamera.api.CameraMode.MOTION
                    && motionBlackLevelValid) {

                System.arraycopy(
                        motionValidatedBlackLevel,
                        0,
                        blackLevel,
                        0,
                        4
                );

                usedDynamic = true;

                Log.d(
                        TAG,
                        "MOTION_26166_BLACK_LEVEL_APPLIED"
                                + " source="
                                + CaptureController
                                        .getMotionValidatedBlackLevelSource()
                                + " selected="
                                + Arrays.toString(blackLevel)
                                + " userDynamicSetting="
                                + useDynamicBlackLevel
                                + " appliedBeforeAlignment=true"
                );
            } else if (useDynamicBlackLevel) {
                float[] dynbl =
                        result.get(
                                CaptureResult
                                        .SENSOR_DYNAMIC_BLACK_LEVEL
                        );

                boolean validDynamic =
                        dynbl != null && dynbl.length >= 4;

                if (validDynamic) {
                    float maximumAllowed =
                            Math.max(
                                    256.0f,
                                    Math.max(1, whiteLevel) * 0.25f
                            );

                    for (int i = 0; i < 4; i++) {
                        float value = dynbl[i];

                        if (!Float.isFinite(value)
                                || value < 0.0f
                                || value >= maximumAllowed) {
                            validDynamic = false;
                            break;
                        }
                    }
                }

                if (validDynamic) {
                    System.arraycopy(
                            dynbl,
                            0,
                            blackLevel,
                            0,
                            4
                    );
                    usedDynamic = true;
                }
            }
"""

params = replace_once(
    params,
    old_dynamic,
    new_dynamic,
    "Parameters validated Motion black level",
)

old_override = """        if(blackLevelOverride >= 0) {
            for (int i = 0; i < 4; i++) blackLevel[i] = blackLevelOverride;
        }
        Float aperture = result.get(CaptureResult.LENS_APERTURE);
"""

new_override = """        if(blackLevelOverride >= 0) {
            for (int i = 0; i < 4; i++) blackLevel[i] = blackLevelOverride;
        }

        if (PhotonCamera.getSettings().selectedMode
                == com.particlesdevs.photoncamera.api.CameraMode.MOTION) {
            Log.d(
                    TAG,
                    "MOTION_26166_BLACK_LEVEL_FINAL"
                            + " selected="
                            + Arrays.toString(blackLevel)
                            + " usedValidatedOrDynamic="
                            + usedDynamic
                            + " override="
                            + blackLevelOverride
                            + " whiteLevel="
                            + whiteLevel
                            + " cfaPattern="
                            + cfaPattern
            );
        }

        Float aperture = result.get(CaptureResult.LENS_APERTURE);
"""

params = replace_once(
    params,
    old_override,
    new_override,
    "final Motion black-level diagnostic",
)

params_path.write_text(params)


old_pre_save_finished = """        img = overlay(img, pipeline.debugData.toArray(new Bitmap[0]));
        try {
            processingEventsListener.onProcessingFinished("HdrX JPG Processing Finished");
        }
        catch (Exception e){
            Log.d(TAG,"Error in processingEventsListener.onProcessingFinished:"+Log.getStackTraceString(e));
        }
        imageFile = Paths.get(imageFile.toAbsolutePath() + ".jpg");
"""

new_pre_save_finished = """        img = overlay(img, pipeline.debugData.toArray(new Bitmap[0]));

        /*
         * Preserve Photo/Night UI timing. Motion completion is delayed until
         * after the JPEG is written and the ImageSaved callback is delivered.
         */
        if (cameraMode != CameraMode.MOTION) {
            try {
                processingEventsListener.onProcessingFinished(
                        "HdrX JPG Processing Finished"
                );
            }
            catch (Exception e){
                Log.d(
                        TAG,
                        "Error in processingEventsListener.onProcessingFinished:"
                                + Log.getStackTraceString(e)
                );
            }
        }

        imageFile = Paths.get(imageFile.toAbsolutePath() + ".jpg");
"""

hdrx = replace_once(
    hdrx,
    old_pre_save_finished,
    new_pre_save_finished,
    "Motion save-completion ordering",
)

old_notify = """        try {
            processingEventsListener.notifyImageSavedStatus(imageSaved, imageFile);
        }
        catch (Exception e){
            Log.d(TAG,"Error in processingEventsListener.notifyImageSavedStatus:"+Log.getStackTraceString(e));
        }

        pipeline.close();
"""

new_notify = """        boolean saveCallbackDelivered = false;

        try {
            processingEventsListener.notifyImageSavedStatus(
                    imageSaved,
                    imageFile
            );
            saveCallbackDelivered = true;
        }
        catch (Exception e){
            Log.d(
                    TAG,
                    "Error in processingEventsListener.notifyImageSavedStatus:"
                            + Log.getStackTraceString(e)
            );
        }

        if (cameraMode == CameraMode.MOTION) {
            boolean fileExists =
                    imageFile != null
                            && imageFile.toFile().exists();

            long fileBytes =
                    fileExists
                            ? imageFile.toFile().length()
                            : 0L;

            Log.d(
                    TAG,
                    "MOTION_26166_IMAGE_SAVED_COMPLETE"
                            + " success=" + imageSaved
                            + " callbackDelivered="
                            + saveCallbackDelivered
                            + " exists=" + fileExists
                            + " bytes=" + fileBytes
                            + " path=" + imageFile
            );

            try {
                processingEventsListener.onProcessingFinished(
                        imageSaved
                                ? "HdrX JPG Saved"
                                : "HdrX JPG Save Failed"
                );
            }
            catch (Exception e){
                Log.d(
                        TAG,
                        "Error in Motion post-save onProcessingFinished:"
                                + Log.getStackTraceString(e)
                );
            }
        }

        pipeline.close();
"""

hdrx = replace_once(
    hdrx,
    old_notify,
    new_notify,
    "durable Motion ImageSaved completion marker",
)

hdrx_path.write_text(hdrx)


if version.count("VERSION_BUILD=26165") != 1:
    raise SystemExit(
        "ERROR: expected exactly one VERSION_BUILD=26165"
    )

version_path.write_text(
    version.replace(
        "VERSION_BUILD=26165",
        "VERSION_BUILD=26166",
        1,
    )
)
PY

echo
echo "=== VERIFY 26166 SOURCE ==="

grep -Fq 'mMotionBurstDynamicBlackLevel' "$CAPTURE" \
    || fail "Per-frame Motion black-level map missing"

grep -Fq 'CONTROLLED_BLACK_LEVEL' "$CAPTURE" \
    || fail "Per-frame black-level diagnostic missing"

grep -Fq 'MOTION_26166_BLACK_LEVEL_SELECTED' "$CAPTURE" \
    || fail "Validated median selection marker missing"

grep -Fq 'MOTION_26166_BLACK_LEVEL_APPLIED' "$PARAMS" \
    || fail "Validated black level is not applied in Parameters"

grep -Fq 'MOTION_26166_BLACK_LEVEL_FINAL' "$PARAMS" \
    || fail "Final black-level marker missing"

grep -Fq 'MOTION_26166_IMAGE_SAVED_COMPLETE' "$HDRX" \
    || fail "Post-save completion marker missing"

grep -Fq 'MOTION_26165_HOMOGENEOUS_RAW_STACK' "$CAPTURE" \
    || fail "26165 post-only stack isolation was lost"

grep -Fq 'MOTION_PHOTON_ENERGY_POLICY' "$CAPTURE" \
    || fail "Motion shutter/exposure-energy policy was lost"

grep -Fq 'MOTION_COLOR_REFERENCE_METADATA' "$PARAMS" \
    || fail "Standard result-based color path was lost"

grep -Fq \
    'pRGB = corr*sensorToIntermediate*(pRGB*neutralPoint);' \
    "$SHADER" \
    || fail "Original Photon shader path was lost"

grep -q '^VERSION_BUILD=26166$' "$VERSION" \
    || fail "VERSION_BUILD was not updated"

if git diff -- \
    app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IsoExpoSelector.java \
    | grep -q .; then
    fail "IsoExpoSelector changed unexpectedly"
fi

if git diff | grep -E \
    '^[+-].*(mIsRecordingVideo|CameraMode\.RAWVIDEO|TEMPLATE_RECORD|MediaRecorder|CONTROL_AF_MODE_CONTINUOUS_VIDEO|getSelectedFpsRange)'; then
    fail "Video or RAW Video behavior changed unexpectedly"
fi

git diff --check \
    || fail "git diff --check reported a formatting error"

for file in "$CAPTURE" "$PARAMS" "$HDRX" "$SHADER" "$VERSION"; do
    cp "$file" "$OUT/source_after/$(basename "$file")"
done

git diff --stat | tee "$OUT/change-summary.txt"
git diff --binary HEAD > "$OUT/combined-${NEW_BUILD}-validated-blacklevel-save.patch"

echo
echo "PASS: 20 controlled still-capture RAWs remain isolated."
echo "PASS: Every controlled result logs its dynamic black level."
echo "PASS: A stable per-channel median is selected with static fallback."
echo "PASS: Selected black level is applied before alignment and merge."
echo "PASS: Motion UI completion now occurs after JPEG save notification."
echo "PASS: Shutter, exposure energy, color matrix and shader preserved."
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
        | tail -240 \
        > "$OUT/relevant-errors.txt" || true

    fail "Gradle build failed; inspect $OUT/relevant-errors.txt" \
        "$BUILD_STATUS"
fi

APK="$(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | head -n 1)"

[ -n "$APK" ] && [ -f "$APK" ] \
    || fail "Debug APK was not created"

APK_COPY="$OUT/PhotonCamera-${NEW_VERSION}-validated-blacklevel-save-debug.apk"

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
echo "Combined patch:$OUT/combined-${NEW_BUILD}-validated-blacklevel-save.patch"
echo "Build log:     $OUT/build-${NEW_BUILD}.log"
echo
echo "Expected capture markers:"
echo "  CONTROLLED_BLACK_LEVEL ... dynamic=[R,G1,G2,B]"
echo "  MOTION_26166_BLACK_LEVEL_SELECTED source=dynamicMedian"
echo "  MOTION_26166_BLACK_LEVEL_APPLIED appliedBeforeAlignment=true"
echo "  MOTION_26166_IMAGE_SAVED_COMPLETE success=true callbackDelivered=true"
echo
echo "Adaptive Noise Model: leave OFF."
echo
git status --short --untracked-files=no
echo
echo "Safe to open another terminal now."

trap - EXIT
