#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
EXPECTED_BUILD="26166"
NEW_BUILD="26167"
NEW_VERSION="0.9726167"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="/workspaces/Photon-Camera/build_${NEW_BUILD}_motion_residual_noise_fix_${STAMP}"
BACKUP_BRANCH="backup-before-motion-residual-noise-${NEW_BUILD}-${STAMP}"

POST="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
ESD_JAVA="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java"
ESD_SHADER="app/src/main/assets/shaders/denoise/esd3d2.glsl"
CAPTURE_SHARP="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java"
FINAL_SHARP="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java"
VERSION="app/version.properties"

# Protected 26166 behavior.
CAPTURE="app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
PARAMS="app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java"
HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
INITIAL="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java"
COLOR_SHADER="app/src/main/assets/shaders/initial.glsl"
EXPOSURE_SELECTOR="app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IsoExpoSelector.java"

fail() {
    echo
    echo "============================================================"
    echo " BUILD FAILED"
    echo " Reason: $1"
    echo " Workspace: $OUT"
    echo "============================================================"
    exit "${2:-1}"
}

trap 'code=$?; if [ "$code" -ne 0 ]; then echo; echo "FAILED: build 26167 v2 (exit $code)"; echo "Workspace: $OUT"; fi' EXIT

echo "============================================================"
echo " PhotonCamera ${NEW_VERSION}"
echo " Motion residual-noise + ESD3D2 correction"
echo "============================================================"

[ "$(git branch --show-current)" = "$EXPECTED_BRANCH" ] \
    || fail "Expected branch $EXPECTED_BRANCH"

[ "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" ] \
    || fail "Expected HEAD $EXPECTED_HEAD"

grep -q "^VERSION_BUILD=${EXPECTED_BUILD}$" "$VERSION" \
    || fail "Expected VERSION_BUILD=${EXPECTED_BUILD}; do not run this after another 26167 script"

EXPECTED_MODIFIED="$CAPTURE
$INITIAL
$HDRX
$PARAMS
$VERSION"

ACTUAL_MODIFIED="$(git status --short --untracked-files=no | awk '{print $2}' | sort)"
EXPECTED_SORTED="$(printf '%s\n' "$EXPECTED_MODIFIED" | sort)"

[ "$ACTUAL_MODIFIED" = "$EXPECTED_SORTED" ] \
    || {
        echo "Expected current 26166 tracked changes:"
        printf '%s\n' "$EXPECTED_SORTED"
        echo
        echo "Actual tracked changes:"
        printf '%s\n' "$ACTUAL_MODIFIED"
        fail "Working tree is not the verified 26166 state"
    }

for file in "$POST" "$ESD_JAVA" "$ESD_SHADER" "$CAPTURE_SHARP" "$FINAL_SHARP"; do
    git diff --quiet HEAD -- "$file" \
        || fail "Unexpected pre-existing modification in $file"
done

grep -Fq 'MOTION_26165_HOMOGENEOUS_RAW_STACK' "$CAPTURE" \
    || fail "26165 homogeneous twenty-frame stack missing"

grep -Fq 'MOTION_26166_BLACK_LEVEL_SELECTED' "$CAPTURE" \
    || fail "26166 validated black-level path missing"

grep -Fq 'MOTION_26166_IMAGE_SAVED_COMPLETE' "$HDRX" \
    || fail "26166 save-completion path missing"

grep -Fq 'processingParameters.effectiveFrameCount =' "$HDRX" \
    || fail "Effective-frame diagnostic field missing"

grep -Fq 'processingParameters.retainedFrameCount' "$HDRX" \
    || fail "Retained-frame diagnostic field missing"

grep -Fq 'float sigY = max(NOISES*noisefactor + NOISES*NOISES * 3.0/8.0 + noiseO' "$ESD_SHADER" \
    || fail "Expected ESD3D2 read-noise defect not found"

grep -Fq 'MOTION_COLOR_REFERENCE_METADATA' "$PARAMS" \
    || fail "Standard Motion color path missing"

grep -Fq 'pRGB = corr*sensorToIntermediate*(pRGB*neutralPoint);' "$COLOR_SHADER" \
    || fail "Original Photon color shader missing"

mkdir -p "$OUT/source_before" "$OUT/source_after"

echo
echo "=== CREATE BACKUP BRANCH AND PATCH ==="

git branch "$BACKUP_BRANCH" HEAD
git diff --binary HEAD > "$OUT/working-tree-before-${NEW_BUILD}.patch"

for file in \
    "$POST" \
    "$ESD_JAVA" \
    "$ESD_SHADER" \
    "$CAPTURE_SHARP" \
    "$FINAL_SHARP" \
    "$VERSION"; do
    cp "$file" "$OUT/source_before/$(basename "$file")"
done

sha256sum \
    "$CAPTURE" \
    "$PARAMS" \
    "$HDRX" \
    "$INITIAL" \
    "$COLOR_SHADER" \
    "$EXPOSURE_SELECTOR" \
    > "$OUT/protected-before.sha256"

echo "Backup branch: $BACKUP_BRANCH"
echo "Backup patch:  $OUT/working-tree-before-${NEW_BUILD}.patch"

echo
echo "=== APPLY CORRECTED 26167 SOURCE CHANGES ==="

python3 - <<'PY'
from pathlib import Path

post_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/opengl/postpipeline/PostPipeline.java"
)
esd_java_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/opengl/postpipeline/ESD3D2.java"
)
esd_shader_path = Path(
    "app/src/main/assets/shaders/denoise/esd3d2.glsl"
)
capture_sharp_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/opengl/postpipeline/CaptureSharpening.java"
)
final_sharp_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/opengl/postpipeline/Sharpen2.java"
)
version_path = Path("app/version.properties")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"ERROR: {label}: expected exactly one match, found {count}"
        )
    return text.replace(old, new, 1)


# -------------------------------------------------------------------------
# PostPipeline:
# Keep retained/effective frame diagnostics untouched. Apply a separately
# named residual-noise variance multiplier after the normal twenty-frame
# stacking model. This does not capture, discard, or re-label any frame.
# -------------------------------------------------------------------------

post = post_path.read_text()

old_post_noise = """        double noisempy = Math.pow(2.0, mSettings.noiseRstr + constShift);
        Log.d("PostPipeline", "noisempy:" + noisempy);
        noiseS *= noisempy;
        noiseO *= noisempy;
        Log.d("PostPipeline", "NoiseS:" + noiseS + "\\n" + "NoiseO:" + noiseO);
"""

new_post_noise = """        double noisempy = Math.pow(2.0, mSettings.noiseRstr + constShift);
        Log.d("PostPipeline", "noisempy:" + noisempy);
        noiseS *= noisempy;
        noiseO *= noisempy;

        /*
         * Build 26167:
         *
         * Motion still captures and merges every retained RAW, and its
         * effective-frame diagnostic remains equal to the retained count.
         *
         * High-ISO temporal rejection can leave more residual variance in
         * moving, dark, or poorly aligned regions than the global stacking
         * model predicts. Represent that uncertainty with a separately
         * named downstream variance multiplier rather than pretending that
         * fewer frames were captured or merged.
         */
        float motionResidualNoiseMpy = 1.0f;

        if (mSettings.selectedMode == CameraMode.MOTION) {
            float motionIso =
                    Math.max(
                            1.0f,
                            mParameters.iso
                    );

            float highIsoBlend =
                    com.particlesdevs.photoncamera.util.Math2.clamp(
                            (motionIso - 400.0f) / 2800.0f,
                            0.0f,
                            1.0f
                    );

            /*
             * Maximum is 1.8x variance at ISO 3200 and above, equivalent to
             * about 1.34x standard deviation. This is deliberately modest.
             */
            motionResidualNoiseMpy =
                    1.0f + 0.80f * highIsoBlend;

            noiseS *= motionResidualNoiseMpy;
            noiseO *= motionResidualNoiseMpy;

            Log.d(
                    "PostPipeline",
                    "MOTION_26167_RESIDUAL_NOISE"
                            + " iso=" + motionIso
                            + " retainedFrames="
                            + mParameters.retainedFrameCount
                            + " effectiveDiagnostic="
                            + mParameters.effectiveFrameCount
                            + " varianceMultiplier="
                            + motionResidualNoiseMpy
                            + " captureFramesChanged=false"
                            + " mergeFramesChanged=false"
                            + " effectiveDiagnosticChanged=false"
                            + " spatialContributionMeasured=false"
                            + " adaptiveNoiseSettingUnchanged=true"
            );
        }

        Log.d(
                "PostPipeline",
                "NoiseS:" + noiseS
                        + "\\nNoiseO:" + noiseO
                        + "\\nMotionResidualNoiseMpy:"
                        + motionResidualNoiseMpy
        );
"""

post = replace_once(
    post,
    old_post_noise,
    new_post_noise,
    "PostPipeline residual-noise model",
)

post_path.write_text(post)


# -------------------------------------------------------------------------
# ESD3D2 shader:
# Java compiles NOISEO, but the shader read an unset lowercase uniform.
# -------------------------------------------------------------------------

esd_shader = esd_shader_path.read_text()

old_sigy = (
    "    float sigY = max(NOISES*noisefactor + "
    "NOISES*NOISES * 3.0/8.0 + noiseO, 0.0000001);"
)

new_sigy = """    /*
     * Build 26167:
     * ESD3D2Run supplies modeled read noise through the NOISEO define.
     * The former lowercase noiseO uniform was unset here, suppressing
     * read-noise protection in deep shadows.
     */
    float sigY = max(
            NOISES*noisefactor
                    + NOISES*NOISES * 3.0/8.0
                    + NOISEO,
            0.0000001
    );"""

esd_shader = replace_once(
    esd_shader,
    old_sigy,
    new_sigy,
    "ESD3D2 read-noise handoff",
)

esd_shader_path.write_text(esd_shader)


# -------------------------------------------------------------------------
# ESD3D2 Java:
# The corrected noise model already drives kernel/scale. Add only a gradual
# Motion high-ISO shadow tolerance so chroma speckle is not protected as an
# edge after aggressive night tone lifting.
# -------------------------------------------------------------------------

esd_java = esd_java_path.read_text()

old_esd_defines = """            glProg.setDefine("MOIRE", moire);
            glProg.setDefine("LUMA", luma);
            glProg.setDefine("CHROMASTRENGTH", chromaStrength);
            glProg.setDefine("SHADOWBOOST", shadowBoost);

            glProg.setDefine("INSIZE", basePipeline.mParameters.rawSize);
"""

new_esd_defines = """            float appliedShadowBoost =
                    shadowBoost;

            if (com.particlesdevs.photoncamera.app.PhotonCamera
                    .getSettings().selectedMode
                    == com.particlesdevs.photoncamera.api.CameraMode.MOTION) {

                float motionIso =
                        Math.max(
                                1.0f,
                                basePipeline.mParameters.iso
                        );

                float highIsoBlend =
                        Math2.clamp(
                                (motionIso - 400.0f) / 2800.0f,
                                0.0f,
                                1.0f
                        );

                appliedShadowBoost =
                        Math.max(
                                shadowBoost,
                                0.50f + 0.65f * highIsoBlend
                        );

                Log.d(
                        Name,
                        "MOTION_26167_ESD3D2_PROFILE"
                                + " iso=" + motionIso
                                + " scale=" + scale
                                + " NoiseS=" + NoiseS
                                + " NoiseO=" + NoiseO
                                + " chromaStrength="
                                + chromaStrength
                                + " shadowBoostConfigured="
                                + shadowBoost
                                + " shadowBoostApplied="
                                + appliedShadowBoost
                                + " readNoiseSource=NOISEO"
                );
            }

            glProg.setDefine("MOIRE", moire);
            glProg.setDefine("LUMA", luma);
            glProg.setDefine("CHROMASTRENGTH", chromaStrength);
            glProg.setDefine(
                    "SHADOWBOOST",
                    appliedShadowBoost
            );

            glProg.setDefine("INSIZE", basePipeline.mParameters.rawSize);
"""

esd_java = replace_once(
    esd_java,
    old_esd_defines,
    new_esd_defines,
    "Motion ESD3D2 shadow profile",
)

esd_java_path.write_text(esd_java)


# -------------------------------------------------------------------------
# CaptureSharpening:
# Reduce amplification of residual high-ISO texture, without disabling the
# sensor-specific sharpening stage or changing other camera modes.
# -------------------------------------------------------------------------

capture_sharp = capture_sharp_path.read_text()

old_capture_strength = """        float size = basePipeline.mParameters.sensorSpecifics.captureSharpeningS;
        float strength = basePipeline.mParameters.sensorSpecifics.captureSharpeningIntense*str;
        glProg.setDefine("SHARPSTR",strength);
"""

new_capture_strength = """        float size = basePipeline.mParameters.sensorSpecifics.captureSharpeningS;
        float strength = basePipeline.mParameters.sensorSpecifics.captureSharpeningIntense*str;

        float motionSharpScale = 1.0f;

        if (com.particlesdevs.photoncamera.app.PhotonCamera
                .getSettings().selectedMode
                == com.particlesdevs.photoncamera.api.CameraMode.MOTION) {

            float motionIso =
                    Math.max(
                            1.0f,
                            basePipeline.mParameters.iso
                    );

            float highIsoBlend =
                    com.particlesdevs.photoncamera.util.Math2.clamp(
                            (motionIso - 400.0f) / 2800.0f,
                            0.0f,
                            1.0f
                    );

            motionSharpScale =
                    1.0f - 0.45f * highIsoBlend;

            strength *= motionSharpScale;

            Log.d(
                    Name,
                    "MOTION_26167_CAPTURE_SHARPEN"
                            + " iso=" + motionIso
                            + " scale=" + motionSharpScale
                            + " appliedStrength=" + strength
            );
        }

        glProg.setDefine("SHARPSTR",strength);
"""

capture_sharp = replace_once(
    capture_sharp,
    old_capture_strength,
    new_capture_strength,
    "Motion CaptureSharpening attenuation",
)

capture_sharp_path.write_text(capture_sharp)


# -------------------------------------------------------------------------
# Sharpen2:
# Apply the same gradual Motion-only ISO attenuation to the final sharpening
# stage, which otherwise turns surviving RGB noise into hard color clumps.
# -------------------------------------------------------------------------

final_sharp = final_sharp_path.read_text()

old_final_strength = """        float sharpness = Math.max(PreferenceKeys.getSharpnessValue(), 0.0f);
        glProg.setVar("strength", sharpness);
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
"""

new_final_strength = """        float sharpness = Math.max(PreferenceKeys.getSharpnessValue(), 0.0f);

        float motionSharpScale = 1.0f;

        if (com.particlesdevs.photoncamera.app.PhotonCamera
                .getSettings().selectedMode
                == com.particlesdevs.photoncamera.api.CameraMode.MOTION) {

            float motionIso =
                    Math.max(
                            1.0f,
                            basePipeline.mParameters.iso
                    );

            float highIsoBlend =
                    com.particlesdevs.photoncamera.util.Math2.clamp(
                            (motionIso - 400.0f) / 2800.0f,
                            0.0f,
                            1.0f
                    );

            motionSharpScale =
                    1.0f - 0.45f * highIsoBlend;

            sharpness *= motionSharpScale;

            Log.d(
                    Name,
                    "MOTION_26167_FINAL_SHARPEN"
                            + " iso=" + motionIso
                            + " scale=" + motionSharpScale
                            + " appliedStrength=" + sharpness
            );
        }

        glProg.setVar("strength", sharpness);
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
"""

final_sharp = replace_once(
    final_sharp,
    old_final_strength,
    new_final_strength,
    "Motion Sharpen2 attenuation",
)

final_sharp_path.write_text(final_sharp)


# -------------------------------------------------------------------------
# Version.
# -------------------------------------------------------------------------

version = version_path.read_text()

if version.count("VERSION_BUILD=26166") != 1:
    raise SystemExit(
        "ERROR: expected exactly one VERSION_BUILD=26166"
    )

version_path.write_text(
    version.replace(
        "VERSION_BUILD=26166",
        "VERSION_BUILD=26167",
        1,
    )
)
PY

echo
echo "=== VERIFY CORRECTED 26167 SOURCE ==="

grep -Fq 'MOTION_26167_RESIDUAL_NOISE' "$POST" \
    || fail "Residual-noise marker missing"

grep -Fq 'effectiveDiagnosticChanged=false' "$POST" \
    || fail "Script does not preserve effective-frame diagnostics"

grep -Fq 'captureFramesChanged=false' "$POST" \
    || fail "Script does not explicitly preserve captured frames"

grep -Fq 'mergeFramesChanged=false' "$POST" \
    || fail "Script does not explicitly preserve merged frames"

grep -Fq 'MOTION_26167_ESD3D2_PROFILE' "$ESD_JAVA" \
    || fail "Motion ESD3D2 profile missing"

grep -Fq '+ NOISEO,' "$ESD_SHADER" \
    || fail "ESD3D2 does not use the compiled read-noise value"

if grep -Fq '+ noiseO, 0.0000001' "$ESD_SHADER"; then
    fail "Old unset ESD3D2 read-noise uniform remains"
fi

grep -Fq 'MOTION_26167_CAPTURE_SHARPEN' "$CAPTURE_SHARP" \
    || fail "Capture sharpening safeguard missing"

grep -Fq 'MOTION_26167_FINAL_SHARPEN' "$FINAL_SHARP" \
    || fail "Final sharpening safeguard missing"

grep -q '^VERSION_BUILD=26167$' "$VERSION" \
    || fail "VERSION_BUILD was not updated"

# The corrected design must not rewrite effective frame count.
if git diff -- "$HDRX" | grep -E \
    '^[+-].*(effectiveFrameCount|effectiveStackRatio|computeStackingNoiseModel)'; then
    fail "Effective-frame or stacking-frame semantics changed unexpectedly"
fi

sha256sum -c "$OUT/protected-before.sha256" \
    || fail "A protected capture, merge-metadata, color, or exposure file changed"

if git diff | grep -E \
    '^[+-].*(mIsRecordingVideo|CameraMode\.RAWVIDEO|TEMPLATE_RECORD|MediaRecorder|CONTROL_AF_MODE_CONTINUOUS_VIDEO|getSelectedFpsRange)'; then
    fail "Video or RAW Video behavior changed unexpectedly"
fi

git diff --check \
    || fail "git diff --check reported a formatting error"

for file in \
    "$POST" \
    "$ESD_JAVA" \
    "$ESD_SHADER" \
    "$CAPTURE_SHARP" \
    "$FINAL_SHARP" \
    "$VERSION"; do
    cp "$file" "$OUT/source_after/$(basename "$file")"
done

git diff --stat | tee "$OUT/change-summary.txt"
git diff --binary HEAD > "$OUT/combined-${NEW_BUILD}-motion-residual-noise-fix.patch"

echo
echo "PASS: all twenty retained RAWs remain in the merge."
echo "PASS: retained/effective frame diagnostics remain unchanged."
echo "PASS: residual-noise uncertainty is a separate variance multiplier."
echo "PASS: ESD3D2 now receives modeled read noise through NOISEO."
echo "PASS: high-ISO Motion shadow chroma receives gradual protection."
echo "PASS: both Motion sharpening stages taper gradually with ISO."
echo "PASS: 26166 color, black level and ImageSaved behavior preserved."
echo "PASS: exposure selection, Video and RAW Video unchanged."
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
        | tail -260 \
        > "$OUT/relevant-errors.txt" || true

    fail "Gradle build failed; inspect $OUT/relevant-errors.txt" \
        "$BUILD_STATUS"
fi

APK="$(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | head -n 1)"

[ -n "$APK" ] && [ -f "$APK" ] \
    || fail "Debug APK was not created"

APK_COPY="$OUT/PhotonCamera-${NEW_VERSION}-motion-residual-noise-fix-debug.apk"

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
echo "Combined patch:$OUT/combined-${NEW_BUILD}-motion-residual-noise-fix.patch"
echo "Build log:     $OUT/build-${NEW_BUILD}.log"
echo
echo "Expected Motion markers:"
echo "  MOTION_26167_RESIDUAL_NOISE"
echo "  MOTION_26167_ESD3D2_PROFILE"
echo "  MOTION_26167_CAPTURE_SHARPEN"
echo "  MOTION_26167_FINAL_SHARPEN"
echo "  MOTION_26166_IMAGE_SAVED_COMPLETE success=true"
echo
echo "Adaptive Noise Model: leave OFF."
echo
git status --short --untracked-files=no
echo
echo "Safe to open another terminal now."

trap - EXIT
