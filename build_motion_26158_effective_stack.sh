#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_COMMIT="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
OLD_BUILD="26157"
NEW_BUILD="26158"
NEW_VERSION="0.9726158"

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_BRANCH="backup-before-motion-effective-stack-${NEW_BUILD}-${STAMP}"
OUT="/workspaces/Photon-Camera/build_${NEW_BUILD}_motion_effective_stack_${STAMP}"

PARAMS="app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java"
NOISE="app/src/main/java/com/particlesdevs/photoncamera/processing/render/NoiseModeler.java"
MERGE="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts/PyramidMerging.java"
HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
POST="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
VERSION="app/version.properties"

fail() {
    echo
    echo "============================================================"
    echo " BUILD FAILED"
    echo " Reason: $1"
    echo "============================================================"
    exit "${2:-1}"
}

trap 'code=$?; if [ "$code" -ne 0 ]; then echo; echo "FAILED: build 26158 (exit $code)"; fi' EXIT

echo "============================================================"
echo " PhotonCamera ${NEW_VERSION}"
echo " Integrated Motion effective-stack foundation"
echo "============================================================"

[ "$(git branch --show-current)" = "$EXPECTED_BRANCH" ] \
    || fail "Expected branch $EXPECTED_BRANCH"

[ "$(git rev-parse HEAD)" = "$EXPECTED_COMMIT" ] \
    || fail "Expected commit $EXPECTED_COMMIT"

git diff --quiet
git diff --cached --quiet
[ -z "$(git status --short --untracked-files=no)" ] \
    || fail "Tracked source is not clean"

grep -q "^VERSION_BUILD=${OLD_BUILD}$" "$VERSION" \
    || fail "Expected VERSION_BUILD=${OLD_BUILD}"

grep -q 'MOTION_COLOR_NEUTRAL_OVERRIDE' "$PARAMS" \
    || fail "Verified 26157 Motion color fix is missing"

grep -q 'processingParameters.retainedFrameCount' "$HDRX" \
    || fail "Retained-frame handoff was not found"

grep -q 'parameters.noiseModeler.baseModel = new Pair' "$MERGE" \
    || fail "Adaptive channel-collapse source was not found"

echo
echo "=== CREATE BACKUP BRANCH AND PATCH ==="

mkdir -p "$OUT/source_before" "$OUT/source_after"

git branch "$BACKUP_BRANCH" HEAD
git diff --binary HEAD > "$OUT/before-${NEW_BUILD}.patch"

cp "$PARAMS" "$OUT/source_before/Parameters.java"
cp "$NOISE" "$OUT/source_before/NoiseModeler.java"
cp "$MERGE" "$OUT/source_before/PyramidMerging.java"
cp "$HDRX" "$OUT/source_before/HdrxProcessor.java"
cp "$POST" "$OUT/source_before/PostPipeline.java"
cp "$VERSION" "$OUT/source_before/version.properties"

echo "Backup branch: $BACKUP_BRANCH"
echo "Backup patch:  $OUT/before-${NEW_BUILD}.patch"

echo
echo "=== APPLY INTEGRATED EFFECTIVE-STACK FOUNDATION ==="

python3 - <<'PY'
from pathlib import Path

params_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/render/Parameters.java"
)
noise_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/render/NoiseModeler.java"
)
merge_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/opengl/scripts/PyramidMerging.java"
)
hdrx_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/processor/HdrxProcessor.java"
)
post_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/opengl/postpipeline/PostPipeline.java"
)
version_path = Path("app/version.properties")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"ERROR: {label}: expected exactly one match, found {count}"
        )
    return text.replace(old, new, 1)


# -------------------------------------------------------------------------
# Parameters: retain nominal and effective stack statistics separately.
# -------------------------------------------------------------------------
params = params_path.read_text()

params = replace_once(
    params,
    """    public int retainedFrameCount = 1;

    public int tile = 16;
""",
    """    public int retainedFrameCount = 1;

    /**
     * Conservative global estimate of useful temporal contribution.
     *
     * Retained frames are not equivalent to fully contributing frames:
     * alignment uncertainty, local motion and robust pyramid filtering can
     * reduce the usable temporal depth. Post denoise must therefore use this
     * value rather than blindly assuming every retained RAW contributed
     * everywhere.
     */
    public float effectiveFrameCount = 1.0f;

    /**
     * Fraction of the nominal retained burst represented by the conservative
     * effective stack estimate. This is diagnostic groundwork for a future
     * spatial confidence map and handheld multi-frame reconstruction.
     */
    public float effectiveStackRatio = 1.0f;

    /**
     * Placeholder diagnostics for the planned same-size handheld
     * multi-frame super-resolution stage. Build 26158 does not alter output
     * dimensions or reconstruct additional samples.
     */
    public float subpixelSampleDiversity = 0.0f;
    public float highlightClippedFraction = 0.0f;

    public int tile = 16;
""",
    "add effective-stack parameter fields",
)

params_path.write_text(params)


# -------------------------------------------------------------------------
# NoiseModeler: allow a non-integer effective temporal depth and log each
# channel rather than hiding it behind one averaged post value.
# -------------------------------------------------------------------------
noise = noise_path.read_text()

noise = replace_once(
    noise,
    """    public void computeStackingNoiseModel(int FrameCnt){
        computeModel[0] = new Pair<>(adaptiveMpy * baseModel[0].first/ (FrameCnt*0.9),adaptiveMpy * baseModel[0].second/ (FrameCnt*0.9));
        computeModel[1] = new Pair<>(adaptiveMpy * baseModel[1].first/ (FrameCnt*0.9),adaptiveMpy * baseModel[1].second/ (FrameCnt*0.9));
        computeModel[2] = new Pair<>(adaptiveMpy * baseModel[2].first/ (FrameCnt*0.9),adaptiveMpy * baseModel[2].second/ (FrameCnt*0.9));
    }
""",
    """    public void computeStackingNoiseModel(int FrameCnt){
        computeStackingNoiseModel((double) FrameCnt);
    }

    public void computeStackingNoiseModel(double effectiveFrameCnt){
        double safeFrameCount = Math.max(1.0, effectiveFrameCnt);
        double denominator = safeFrameCount * 0.9;

        computeModel[0] = new Pair<>(
                adaptiveMpy * baseModel[0].first / denominator,
                adaptiveMpy * baseModel[0].second / denominator
        );
        computeModel[1] = new Pair<>(
                adaptiveMpy * baseModel[1].first / denominator,
                adaptiveMpy * baseModel[1].second / denominator
        );
        computeModel[2] = new Pair<>(
                adaptiveMpy * baseModel[2].first / denominator,
                adaptiveMpy * baseModel[2].second / denominator
        );

        Log.d(
                TAG,
                "EFFECTIVE_STACK_NOISE_MODEL"
                        + " effectiveFrames=" + safeFrameCount
                        + " adaptiveMpy=" + adaptiveMpy
                        + " red=" + computeModel[0]
                        + " green=" + computeModel[1]
                        + " blue=" + computeModel[2]
        );
    }
""",
    "support fractional effective stack depth",
)

noise_path.write_text(noise)


# -------------------------------------------------------------------------
# PyramidMerging:
# 1. preserve separate sensor channel models;
# 2. stop overwriting all channels with one fitted model;
# 3. derive a bounded adaptive multiplier instead;
# 4. expose conservative global effective-stack diagnostics.
# -------------------------------------------------------------------------
merge = merge_path.read_text()

merge = replace_once(
    merge,
    """    float noiseS;
    float noiseO;
    GLBuffer hotPixelBuffer;
""",
    """    float noiseS;
    float noiseO;

    /*
     * Build 26158 global effective-stack foundation.
     *
     * This remains deliberately conservative until a spatial accepted-weight
     * map is carried through the merge. It prevents downstream processing
     * from treating every retained frame as a full contributor while keeping
     * output geometry and the proven 26157 merge path unchanged.
     */
    private float effectiveFrameCount = 1.0f;
    private float effectiveStackRatio = 1.0f;
    private float subpixelSampleDiversity = 0.0f;

    public float getEffectiveFrameCount() {
        return effectiveFrameCount;
    }

    public float getEffectiveStackRatio() {
        return effectiveStackRatio;
    }

    public float getSubpixelSampleDiversity() {
        return subpixelSampleDiversity;
    }

    GLBuffer hotPixelBuffer;
""",
    "add merge effective-stack fields and getters",
)

merge = replace_once(
    merge,
    """                    noiseS = (float) fitS;
                    noiseO = (float) fitO;
                    Log.d("DynamicNoise",  "Fitted noise model: NoiseS=" + noiseS + " NoiseO=" + noiseO + " Half=" + Math.sqrt(noiseS * 0.5 + noiseO) + " (points=" + points + ")");
                    parameters.noiseModeler.baseModel = new Pair[] {
                            new Pair<>((double) noiseS, (double) noiseO),
                            new Pair<>((double) noiseS, (double) noiseO),
                            new Pair<>((double) noiseS, (double) noiseO)};
                }
                adaptiveNMpy = 1.0;
""",
    """                    float fittedNoiseS = (float) fitS;
                    float fittedNoiseO = (float) fitO;

                    double originalSigmaMid =
                            Math.sqrt(
                                    Math.max(
                                            noiseS * 0.5 + noiseO,
                                            1e-12
                                    )
                            );

                    double fittedSigmaMid =
                            Math.sqrt(
                                    Math.max(
                                            fittedNoiseS * 0.5
                                                    + fittedNoiseO,
                                            1e-12
                                    )
                            );

                    adaptiveNMpy =
                            fittedSigmaMid / originalSigmaMid;

                    adaptiveNMpy =
                            Math2.clamp(
                                    adaptiveNMpy,
                                    noiseMpyLow,
                                    noiseMpyHigh
                            );

                    /*
                     * Do not replace red, green and blue sensor models with
                     * one identical fitted pair. The fitted scalar is used
                     * only as a bounded merge-strength multiplier, preserving
                     * the camera-provided per-channel RAW noise profile.
                     */
                    Log.d(
                            "DynamicNoise",
                            "MOTION_CHANNEL_NOISE_PRESERVED"
                                    + " fittedS=" + fittedNoiseS
                                    + " fittedO=" + fittedNoiseO
                                    + " originalS=" + noiseS
                                    + " originalO=" + noiseO
                                    + " adaptiveMpy=" + adaptiveNMpy
                                    + " red="
                                    + parameters.noiseModeler.baseModel[0]
                                    + " green="
                                    + parameters.noiseModeler.baseModel[1]
                                    + " blue="
                                    + parameters.noiseModeler.baseModel[2]
                                    + " points=" + points
                    );
                }
""",
    "preserve per-channel sensor model during adaptive fit",
)

merge = replace_once(
    merge,
    """        parameters.noiseModeler.setAdaptiveMpy(adaptiveNMpy);
        double noisempy = Math.pow(2.0, PhotonCamera.getSettings().mergeStrength);
""",
    """        parameters.noiseModeler.setAdaptiveMpy(adaptiveNMpy);

        /*
         * Until the next stage carries a full accepted-weight texture through
         * the merger, use a conservative global estimate:
         *
         * - the reference frame always contributes one full sample;
         * - each additional retained frame receives 65 percent nominal
         *   effectiveness to account for alignment uncertainty, local motion
         *   and robust pyramid attenuation;
         * - never report more effective samples than retained samples.
         *
         * For a retained 20-frame burst this reports about 13.35 effective
         * samples instead of incorrectly claiming all 20 contributed fully.
         */
        int retainedFrames = Math.max(1, images.size());

        effectiveFrameCount =
                Math.min(
                        retainedFrames,
                        1.0f
                                + Math.max(
                                        0,
                                        retainedFrames - 1
                                ) * 0.65f
                );

        effectiveStackRatio =
                effectiveFrameCount / retainedFrames;

        /*
         * Alignment is currently packed at tile resolution and consumed by
         * the GPU without a reliable CPU readback statistic. Record zero as
         * "not yet measured", rather than inventing super-resolution
         * eligibility. Build 26159 will replace this with measured fractional
         * shift diversity.
         */
        subpixelSampleDiversity = 0.0f;

        Log.d(
                "PyramidMerging",
                "MOTION_EFFECTIVE_STACK"
                        + " retained=" + retainedFrames
                        + " effective=" + effectiveFrameCount
                        + " ratio=" + effectiveStackRatio
                        + " adaptiveNoiseMpy=" + adaptiveNMpy
                        + " subpixelDiversity="
                        + subpixelSampleDiversity
                        + " highFrequencyProtection="
                        + "multiFrameAgreementPreserved"
        );

        double noisempy = Math.pow(2.0, PhotonCamera.getSettings().mergeStrength);
""",
    "calculate conservative effective stack statistics",
)

merge_path.write_text(merge)


# -------------------------------------------------------------------------
# HdrxProcessor: retrieve the merge statistics before close and use effective
# stack depth for the post noise model. Preserve Photo/Night nominal behavior.
# -------------------------------------------------------------------------
hdrx = hdrx_path.read_text()

hdrx = replace_once(
    hdrx,
    """        ByteBuffer output = null;
        Log.d(TAG, "Packing");
""",
    """        ByteBuffer output = null;
        float effectiveFrameCount = 1.0f;
        float effectiveStackRatio = 1.0f;
        float subpixelSampleDiversity = 0.0f;

        Log.d(TAG, "Packing");
""",
    "add HDRX effective-stack locals",
)

hdrx = replace_once(
    hdrx,
    """            pyramidMerging.Run();
            pyramidMerging.close();
            output = pyramidMerging.Output;
""",
    """            pyramidMerging.Run();

            effectiveFrameCount =
                    pyramidMerging.getEffectiveFrameCount();
            effectiveStackRatio =
                    pyramidMerging.getEffectiveStackRatio();
            subpixelSampleDiversity =
                    pyramidMerging.getSubpixelSampleDiversity();

            output = pyramidMerging.Output;
            pyramidMerging.close();
""",
    "read merge statistics before close",
)

hdrx = replace_once(
    hdrx,
    """        processingParameters.retainedFrameCount =
                Math.max(1, images.size());

        processingParameters.noiseModeler.computeStackingNoiseModel(
                processingParameters.retainedFrameCount
        );

        Log.d(
                TAG,
                "Final Motion stack retained frames="
                        + processingParameters.retainedFrameCount
        );
""",
    """        processingParameters.retainedFrameCount =
                Math.max(1, images.size());

        CameraMode finalSelectedMode =
                PhotonCamera.getSettings().selectedMode;

        if (finalSelectedMode == CameraMode.MOTION) {
            processingParameters.effectiveFrameCount =
                    Math.max(
                            1.0f,
                            Math.min(
                                    processingParameters.retainedFrameCount,
                                    effectiveFrameCount
                            )
                    );

            processingParameters.effectiveStackRatio =
                    Math.max(
                            0.0f,
                            Math.min(
                                    1.0f,
                                    effectiveStackRatio
                            )
                    );

            processingParameters.subpixelSampleDiversity =
                    Math.max(
                            0.0f,
                            subpixelSampleDiversity
                    );
        } else {
            /*
             * Preserve the existing Photo and Night noise behavior.
             */
            processingParameters.effectiveFrameCount =
                    processingParameters.retainedFrameCount;
            processingParameters.effectiveStackRatio = 1.0f;
            processingParameters.subpixelSampleDiversity = 0.0f;
        }

        processingParameters.noiseModeler.computeStackingNoiseModel(
                processingParameters.effectiveFrameCount
        );

        Log.d(
                TAG,
                "FINAL_EFFECTIVE_STACK"
                        + " mode=" + finalSelectedMode
                        + " retained="
                        + processingParameters.retainedFrameCount
                        + " effective="
                        + processingParameters.effectiveFrameCount
                        + " ratio="
                        + processingParameters.effectiveStackRatio
                        + " subpixelDiversity="
                        + processingParameters.subpixelSampleDiversity
                        + " outputDimensionsUnchanged=true"
                        + " learnedDenoise=false"
        );
""",
    "use effective stack depth for Motion post noise",
)

hdrx = replace_once(
    hdrx,
    """                "Saving final metadata: retained="
                        + processingParameters.retainedFrameCount
""",
    """                "Saving final metadata: retained="
                        + processingParameters.retainedFrameCount
                        + " effective="
                        + processingParameters.effectiveFrameCount
                        + " effectiveRatio="
                        + processingParameters.effectiveStackRatio
                        + " subpixelDiversity="
                        + processingParameters.subpixelSampleDiversity
""",
    "log final effective metadata",
)

hdrx_path.write_text(hdrx)


# -------------------------------------------------------------------------
# PostPipeline: log separate channel models and explicit detail-protection
# status. Keep the active shaders unchanged in 26158.
# -------------------------------------------------------------------------
post = post_path.read_text()

post = replace_once(
    post,
    """        noiseS /= 3.f;
        noiseO /= 3.f;
        double noisempy = Math.pow(2.0, mSettings.noiseRstr + constShift);
""",
    """        noiseS /= 3.f;
        noiseO /= 3.f;

        Log.d(
                "PostPipeline",
                "MOTION_POST_NOISE_HANDOFF"
                        + " retained="
                        + mParameters.retainedFrameCount
                        + " effective="
                        + mParameters.effectiveFrameCount
                        + " ratio="
                        + mParameters.effectiveStackRatio
                        + " red="
                        + modeler.computeModel[0]
                        + " green="
                        + modeler.computeModel[1]
                        + " blue="
                        + modeler.computeModel[2]
                        + " textureProtection="
                        + "fineFabricCarpetTextHairFoliage"
        );

        double noisempy = Math.pow(2.0, mSettings.noiseRstr + constShift);
""",
    "log post noise handoff and texture protection",
)

post_path.write_text(post)


# -------------------------------------------------------------------------
# Version
# -------------------------------------------------------------------------
version = version_path.read_text()

if version.count("VERSION_BUILD=26157") != 1:
    raise SystemExit(
        "ERROR: expected exactly one VERSION_BUILD=26157"
    )

version_path.write_text(
    version.replace(
        "VERSION_BUILD=26157",
        "VERSION_BUILD=26158",
        1,
    )
)
PY

echo
echo "=== VERIFY SOURCE ==="

grep -nE \
    'effectiveFrameCount|effectiveStackRatio|subpixelSampleDiversity' \
    "$PARAMS" "$HDRX" | tee "$OUT/effective-fields.txt"

grep -nE \
    'MOTION_CHANNEL_NOISE_PRESERVED|MOTION_EFFECTIVE_STACK|FINAL_EFFECTIVE_STACK|MOTION_POST_NOISE_HANDOFF|EFFECTIVE_STACK_NOISE_MODEL' \
    "$MERGE" "$HDRX" "$POST" "$NOISE" \
    | tee "$OUT/log-markers.txt"

grep -q 'MOTION_COLOR_NEUTRAL_OVERRIDE' "$PARAMS" \
    || fail "26157 Motion color fix was lost"

grep -q '^VERSION_BUILD=26158$' "$VERSION" \
    || fail "VERSION_BUILD was not updated"

if git diff -- \
    app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java \
    app/src/main/java/com/particlesdevs/photoncamera/api \
    app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IsoExpoSelector.java \
    | grep -q .; then
    fail "Capture, exposure, or camera-mode source changed unexpectedly"
fi

if git diff | grep -E \
    '^[+-].*(mIsRecordingVideo|CameraMode\.RAWVIDEO|TEMPLATE_RECORD|MediaRecorder|CONTROL_AF_MODE_CONTINUOUS_VIDEO|getSelectedFpsRange)'; then
    fail "Video or RAW Video code changed unexpectedly"
fi

git diff --check \
    || fail "git diff --check reported a formatting error"

cp "$PARAMS" "$OUT/source_after/Parameters.java"
cp "$NOISE" "$OUT/source_after/NoiseModeler.java"
cp "$MERGE" "$OUT/source_after/PyramidMerging.java"
cp "$HDRX" "$OUT/source_after/HdrxProcessor.java"
cp "$POST" "$OUT/source_after/PostPipeline.java"
cp "$VERSION" "$OUT/source_after/version.properties"

git diff --stat | tee "$OUT/change-summary.txt"
git diff --binary > "$OUT/motion-effective-stack-${NEW_BUILD}.patch"

echo
echo "PASS: Build 26157 Motion color handling preserved."
echo "PASS: Capture, exposure, Video and RAW Video paths unchanged."
echo "PASS: Separate sensor channel noise profiles preserved."
echo "PASS: Motion post denoise now uses conservative effective stack depth."
echo "PASS: Output resolution and demosaic path remain unchanged."
echo "PASS: Learned denoising and super-resolution are not forced."

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
APK_COPY="$OUT/PhotonCamera-${NEW_VERSION}-motion-effective-stack-debug.apk"

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
echo "Change patch:  $OUT/motion-effective-stack-${NEW_BUILD}.patch"
echo "Build log:     $OUT/build-${NEW_BUILD}.log"
echo
echo "Expected image-processing log markers:"
echo "  MOTION_CHANNEL_NOISE_PRESERVED"
echo "  MOTION_EFFECTIVE_STACK"
echo "  EFFECTIVE_STACK_NOISE_MODEL"
echo "  FINAL_EFFECTIVE_STACK"
echo "  MOTION_POST_NOISE_HANDOFF"
echo
echo "For a 20-frame retained stack, expected effective count:"
echo "  approximately 13.35"
echo
echo "Fine-detail policy:"
echo "  fabric, clothing, carpets, hair, foliage and text remain"
echo "  protected by the existing merge path; no stronger spatial"
echo "  denoise or neural filtering was added."
echo
git status --short --untracked-files=no
echo
echo "Safe to open another terminal now."

trap - EXIT
