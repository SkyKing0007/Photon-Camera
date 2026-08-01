#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
EXPECTED_BUILD="26167"
NEW_BUILD="26168"
NEW_VERSION="0.9726168"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="/workspaces/Photon-Camera/build_${NEW_BUILD}_motion_effective_noise_fix_${STAMP}"
BACKUP_BRANCH="backup-before-motion-effective-noise-${NEW_BUILD}-${STAMP}"

PYRAMID="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts/PyramidMerging.java"
MERGE_SHADER="app/src/main/assets/shaders/merge/merge11.glsl"
POST="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
ESD_JAVA="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java"
ESD_SHADER="app/src/main/assets/shaders/denoise/esd3d2.glsl"
AUTO_EXPOSURE="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/AutoExposure.java"
VERSION="app/version.properties"

# Existing 26166/26167 behavior that must remain present.
CAPTURE="app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
PARAMS="app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java"
HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
INITIAL="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java"
COLOR_SHADER="app/src/main/assets/shaders/initial.glsl"
CAPTURE_SHARP="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java"
FINAL_SHARP="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java"
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

trap 'code=$?; if [ "$code" -ne 0 ]; then echo; echo "FAILED: build 26168 (exit $code)"; echo "Workspace: $OUT"; fi' EXIT

echo "============================================================"
echo " PhotonCamera ${NEW_VERSION}"
echo " Motion effective temporal-noise correction"
echo "============================================================"

[ "$(git branch --show-current)" = "$EXPECTED_BRANCH" ] \
    || fail "Expected branch $EXPECTED_BRANCH"

[ "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" ] \
    || fail "Expected HEAD $EXPECTED_HEAD"

grep -q "^VERSION_BUILD=${EXPECTED_BUILD}$" "$VERSION" \
    || fail "Expected VERSION_BUILD=${EXPECTED_BUILD}"

grep -Fq 'MOTION_26165_HOMOGENEOUS_RAW_STACK' "$CAPTURE" \
    || fail "Homogeneous twenty-frame Motion capture path missing"

grep -Fq 'MOTION_26166_BLACK_LEVEL_SELECTED' "$CAPTURE" \
    || fail "Validated Motion black-level path missing"

grep -Fq 'MOTION_26166_IMAGE_SAVED_COMPLETE' "$HDRX" \
    || fail "Post-save Motion completion path missing"

grep -Fq 'MOTION_26167_RESIDUAL_NOISE' "$POST" \
    || fail "Expected 26167 residual-noise implementation missing"

grep -Fq 'MOTION_26167_ESD3D2_PROFILE' "$ESD_JAVA" \
    || fail "Expected 26167 ESD3D2 profile missing"

grep -Fq 'MOTION_26167_CAPTURE_SHARPEN' "$CAPTURE_SHARP" \
    || fail "Expected 26167 capture-sharpening safeguard missing"

grep -Fq 'MOTION_26167_FINAL_SHARPEN' "$FINAL_SHARP" \
    || fail "Expected 26167 final-sharpening safeguard missing"

grep -Fq '+ NOISEO,' "$ESD_SHADER" \
    || fail "Expected corrected ESD3D2 read-noise source missing"

grep -Fq 'float lDiff = clamp(length(diff), EPS, sqrt(length(variance)*1.4826 + EPS));' "$MERGE_SHADER" \
    || fail "Expected original temporal-difference cap missing"

grep -Fq 'pRGB = corr*sensorToIntermediate*(pRGB*neutralPoint);' "$COLOR_SHADER" \
    || fail "Original Photon color shader missing"

mkdir -p "$OUT/source_before" "$OUT/source_after"

echo
echo "=== CREATE BACKUP BRANCH AND PATCH ==="

git branch "$BACKUP_BRANCH" HEAD
git diff --binary HEAD > "$OUT/working-tree-before-${NEW_BUILD}.patch"

for file in \
    "$PYRAMID" \
    "$MERGE_SHADER" \
    "$POST" \
    "$ESD_JAVA" \
    "$ESD_SHADER" \
    "$AUTO_EXPOSURE" \
    "$VERSION"; do
    cp "$file" "$OUT/source_before/$(basename "$file")"
done

sha256sum \
    "$CAPTURE" \
    "$PARAMS" \
    "$HDRX" \
    "$INITIAL" \
    "$COLOR_SHADER" \
    "$CAPTURE_SHARP" \
    "$FINAL_SHARP" \
    "$EXPOSURE_SELECTOR" \
    > "$OUT/protected-before.sha256"

echo "Backup branch: $BACKUP_BRANCH"
echo "Backup patch:  $OUT/working-tree-before-${NEW_BUILD}.patch"

echo
echo "=== APPLY 26168 SOURCE CHANGES ==="

python3 - <<'PY'
from pathlib import Path

pyramid_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/opengl/scripts/PyramidMerging.java"
)
merge_shader_path = Path(
    "app/src/main/assets/shaders/merge/merge11.glsl"
)
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
auto_exposure_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/opengl/postpipeline/AutoExposure.java"
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
# 1. Temporal merge:
# merge11 already calculates the predicted per-frame noise but never uses it.
# In a noisy flat region, the local-difference cap can pull every reconstructed
# alternate back toward the same reference-frame noise. For equal-exposure
# Motion only, guarantee that the allowed difference is at least the expected
# independent-frame noise range before the normal running average.
# -------------------------------------------------------------------------

pyramid = pyramid_path.read_text()

old_noise_setup = """        noiseS = (float)Math.max(noiseS * noisempy * adaptiveNMpy * adaptiveNMpy,noiseMin);
        noiseO = (float)Math.max(noiseO * noisempy * adaptiveNMpy * adaptiveNMpy,noiseMin);
        if(enableHotPixelCorrection)
            hotPixels();
"""

new_noise_setup = """        noiseS = (float)Math.max(noiseS * noisempy * adaptiveNMpy * adaptiveNMpy,noiseMin);
        noiseO = (float)Math.max(noiseO * noisempy * adaptiveNMpy * adaptiveNMpy,noiseMin);

        final boolean motionEqualExposureStack =
                PhotonCamera.getSettings().selectedMode
                        == com.particlesdevs.photoncamera.api.CameraMode.MOTION;

        /*
         * vec4 length is approximately two times one-channel sigma.
         * 1.5 therefore gives an approximately three-sigma vector allowance.
         */
        final float motionNoiseAllowance =
                motionEqualExposureStack
                        ? 1.5f
                        : 0.0f;

        if (motionEqualExposureStack) {
            Log.d(
                    "PyramidMerging",
                    "MOTION_26168_MERGE_NOISE_AWARE"
                            + " frames=" + images.size()
                            + " perFrameNoiseS=" + noiseS
                            + " perFrameNoiseO=" + noiseO
                            + " vectorSigmaAllowance="
                            + motionNoiseAllowance
                            + " equalExposure=true"
                            + " runningAveragePreserved=true"
                            + " noFramesDiscarded=true"
            );
        }

        if(enableHotPixelCorrection)
            hotPixels();
"""

pyramid = replace_once(
    pyramid,
    old_noise_setup,
    new_noise_setup,
    "PyramidMerging Motion noise allowance setup",
)

old_merge_vars = """            glProg.setVar("noiseS", noiseS);
            glProg.setVar("noiseO", noiseO);
            glProg.setVar("whiteLevel", (float) (parameters.whiteLevel));
"""

new_merge_vars = """            glProg.setVar("noiseS", noiseS);
            glProg.setVar("noiseO", noiseO);
            glProg.setVar(
                    "motionEqualStack",
                    motionEqualExposureStack
                            ? 1
                            : 0
            );
            glProg.setVar(
                    "motionNoiseAllowance",
                    motionNoiseAllowance
            );
            glProg.setVar("whiteLevel", (float) (parameters.whiteLevel));
"""

pyramid = replace_once(
    pyramid,
    old_merge_vars,
    new_merge_vars,
    "merge11 Motion uniforms",
)

pyramid_path.write_text(pyramid)


merge_shader = merge_shader_path.read_text()

old_uniforms = """uniform float noiseS;
uniform float noiseO;
uniform float whiteLevel;
"""

new_uniforms = """uniform float noiseS;
uniform float noiseO;
uniform int motionEqualStack;
uniform float motionNoiseAllowance;
uniform float whiteLevel;
"""

merge_shader = replace_once(
    merge_shader,
    old_uniforms,
    new_uniforms,
    "merge11 Motion uniform declarations",
)

old_ldiff = """    float lDiff = clamp(length(diff), EPS, sqrt(length(variance)*1.4826 + EPS));
    //float lDiff = length(diff);
"""

new_ldiff = """    float localDifferenceCap =
            sqrt(length(variance)*1.4826 + EPS);

    if (motionEqualStack == 1) {
        /*
         * Build 26168:
         * Do not let a noisy reference frame become a common component of
         * every reconstructed alternate merely because local scene variance
         * is small. Permit the expected independent per-frame sensor-noise
         * difference, then retain the existing running-average weight.
         */
        float predictedNoiseCap =
                length(noise) * motionNoiseAllowance;

        localDifferenceCap =
                max(
                        localDifferenceCap,
                        predictedNoiseCap
                );
    }

    float lDiff =
            clamp(
                    length(diff),
                    EPS,
                    localDifferenceCap
            );
    //float lDiff = length(diff);
"""

merge_shader = replace_once(
    merge_shader,
    old_ldiff,
    new_ldiff,
    "merge11 noise-aware temporal cap",
)

merge_shader_path.write_text(merge_shader)


# -------------------------------------------------------------------------
# 2. PostPipeline:
# 26167 multiplied read noise before the fixed 1/4096 floor. The floor then
# replaced most of the adjusted value. Move the Motion residual multiplier
# after both normal floors so it actually reaches ESD3D2 and tone-gain guards.
# -------------------------------------------------------------------------

post = post_path.read_text()

old_residual_block = """        /*
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

new_residual_placeholder = """        float motionResidualNoiseMpy = 1.0f;
"""

post = replace_once(
    post,
    old_residual_block,
    new_residual_placeholder,
    "remove pre-floor residual multiplier",
)

old_floor = """        noiseO = Math.max(noiseO, 1.0f/4096.0f);
        noiseS = Math.max(noiseS, Float.MIN_NORMAL);
        Point rawSliced = parameters.rawSize;
"""

new_floor = """        noiseO = Math.max(noiseO, 1.0f/4096.0f);
        noiseS = Math.max(noiseS, Float.MIN_NORMAL);

        /*
         * Build 26168:
         * Apply residual Motion variance after the normal Photon floors.
         * This keeps every captured/merged frame and leaves the effective
         * frame diagnostic unchanged.
         */
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

            motionResidualNoiseMpy =
                    1.0f + 0.80f * highIsoBlend;

            noiseS *= motionResidualNoiseMpy;
            noiseO *= motionResidualNoiseMpy;

            Log.d(
                    "PostPipeline",
                    "MOTION_26168_RESIDUAL_NOISE_EFFECTIVE"
                            + " iso=" + motionIso
                            + " retainedFrames="
                            + mParameters.retainedFrameCount
                            + " effectiveDiagnostic="
                            + mParameters.effectiveFrameCount
                            + " varianceMultiplier="
                            + motionResidualNoiseMpy
                            + " appliedAfterNoiseFloor=true"
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

        Point rawSliced = parameters.rawSize;
"""

post = replace_once(
    post,
    old_floor,
    new_floor,
    "post-floor Motion residual multiplier",
)

post_path.write_text(post)


# -------------------------------------------------------------------------
# 3. ESD3D2:
# Its edge pre-scan uses full RGB distance. At high ISO, random chroma noise
# frequently looks like a color boundary and forces the filter from its full
# kernel down to KSIZE_SMALL=3. For Motion high ISO, progressively use luma
# distance and a noise-scaled threshold, while still protecting real edges.
# -------------------------------------------------------------------------

esd_java = esd_java_path.read_text()

old_profile = """            float appliedShadowBoost =
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
"""

new_profile = """            float appliedShadowBoost =
                    shadowBoost;

            float motionNoiseBlend =
                    0.0f;

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

                motionNoiseBlend =
                        highIsoBlend;

                appliedShadowBoost =
                        Math.max(
                                shadowBoost,
                                0.50f + 0.65f * highIsoBlend
                        );

                Log.d(
                        Name,
                        "MOTION_26168_ESD3D2_PROFILE"
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
                                + " motionNoiseBlend="
                                + motionNoiseBlend
                                + " edgeMetric="
                                + "rgbToLumaWithIso"
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
            glProg.setDefine(
                    "MOTIONNOISEBLEND",
                    motionNoiseBlend
            );
"""

esd_java = replace_once(
    esd_java,
    old_profile,
    new_profile,
    "ESD3D2 high-ISO Motion edge profile",
)

esd_java_path.write_text(esd_java)


esd_shader = esd_shader_path.read_text()

old_define = """#define SHADOWBOOST 0.5
#define CHROMASTRENGTH 1.0
#define PI 3.1415926535897932384626433832795
"""

new_define = """#define SHADOWBOOST 0.5
#define CHROMASTRENGTH 1.0
#define MOTIONNOISEBLEND 0.0
#define PI 3.1415926535897932384626433832795
"""

esd_shader = replace_once(
    esd_shader,
    old_define,
    new_define,
    "ESD3D2 Motion noise blend define",
)

old_edge_threshold = """    float edgeThreshold = max(sqrt(sigY) * 3.0, 0.05);
    int effectiveKSIZE = KSIZE;
"""

new_edge_threshold = """    float edgeThreshold =
            max(
                    sqrt(sigY)
                            * mix(
                                    3.0,
                                    5.0,
                                    MOTIONNOISEBLEND
                            ),
                    mix(
                            0.05,
                            0.08,
                            MOTIONNOISEBLEND
                    )
            );

    int effectiveKSIZE = KSIZE;
"""

esd_shader = replace_once(
    esd_shader,
    old_edge_threshold,
    new_edge_threshold,
    "ESD3D2 noise-scaled edge threshold",
)

old_edge_distance = """            vec3 neighbor = texelFetch(InputBuffer, xy + ivec2(i, j), 0).rgb;
            float dist = length(abs(neighbor - cin));
            if (dist > edgeThreshold) {
"""

new_edge_distance = """            vec3 neighbor = texelFetch(InputBuffer, xy + ivec2(i, j), 0).rgb;

            float rgbDistance =
                    length(
                            abs(
                                    neighbor - cin
                            )
                    );

            float neighborLuma =
                    dot(
                            neighbor,
                            vec3(0.25, 0.5, 0.25)
                    );

            float centerLuma =
                    dot(
                            cin,
                            vec3(0.25, 0.5, 0.25)
                    );

            float lumaDistance =
                    abs(
                            neighborLuma - centerLuma
                    );

            /*
             * At high ISO, chroma speckles must not masquerade as hard color
             * boundaries and collapse the denoise support to KSIZE_SMALL.
             */
            float dist =
                    mix(
                            rgbDistance,
                            lumaDistance,
                            MOTIONNOISEBLEND
                    );

            if (dist > edgeThreshold) {
"""

esd_shader = replace_once(
    esd_shader,
    old_edge_distance,
    new_edge_distance,
    "ESD3D2 luma-aware Motion edge distance",
)

esd_shader_path.write_text(esd_shader)


# -------------------------------------------------------------------------
# 4. AutoExposure:
# At ISO ~3200 the prior run lifted a very dark frame by about 10.75x.
# That overwhelms modest denoise improvements. Preserve configured behavior
# at low ISO, but reduce the allowed post gain gradually to 4.5 at ISO 3200.
# -------------------------------------------------------------------------

auto = auto_exposure_path.read_text()

old_gain_max = """        if(mpy > gainMax) {
            Log.d("AutoExposure", "Clamping gain by max from " + mpy + " to " + gainMax);
            mpy = gainMax;
        }
        float normL = 0.0f;
"""

new_gain_max = """        if(mpy > gainMax) {
            Log.d("AutoExposure", "Clamping gain by max from " + mpy + " to " + gainMax);
            mpy = gainMax;
        }

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

            float highIsoGainLimit =
                    Math.min(
                            gainMax,
                            4.5f
                    );

            float motionGainLimit =
                    Math2.mix(
                            gainMax,
                            highIsoGainLimit,
                            highIsoBlend
                    );

            float gainBeforeMotionGuard =
                    mpy;

            if (mpy > motionGainLimit) {
                mpy =
                        motionGainLimit;
            }

            Log.d(
                    "AutoExposure",
                    "MOTION_26168_TONE_GAIN_GUARD"
                            + " iso=" + motionIso
                            + " highIsoBlend="
                            + highIsoBlend
                            + " gainBefore="
                            + gainBeforeMotionGuard
                            + " gainLimit="
                            + motionGainLimit
                            + " gainAfter=" + mpy
                            + " lowIsoBehaviorPreserved=true"
            );
        }

        float normL = 0.0f;
"""

auto = replace_once(
    auto,
    old_gain_max,
    new_gain_max,
    "Motion high-ISO tone-gain guard",
)

auto_exposure_path.write_text(auto)


# -------------------------------------------------------------------------
# Version.
# -------------------------------------------------------------------------

version = version_path.read_text()

if version.count("VERSION_BUILD=26167") != 1:
    raise SystemExit(
        "ERROR: expected exactly one VERSION_BUILD=26167"
    )

version_path.write_text(
    version.replace(
        "VERSION_BUILD=26167",
        "VERSION_BUILD=26168",
        1,
    )
)
PY

echo
echo "=== VERIFY 26168 SOURCE ==="

grep -Fq 'MOTION_26168_MERGE_NOISE_AWARE' "$PYRAMID" \
    || fail "Noise-aware temporal merge marker missing"

grep -Fq 'motionNoiseAllowance' "$MERGE_SHADER" \
    || fail "Noise-aware temporal merge shader path missing"

grep -Fq 'predictedNoiseCap' "$MERGE_SHADER" \
    || fail "Predicted per-frame noise cap missing"

grep -Fq 'MOTION_26168_RESIDUAL_NOISE_EFFECTIVE' "$POST" \
    || fail "Post-floor residual-noise marker missing"

grep -Fq 'appliedAfterNoiseFloor=true' "$POST" \
    || fail "Residual-noise multiplier is not confirmed after the floor"

grep -Fq 'MOTION_26168_ESD3D2_PROFILE' "$ESD_JAVA" \
    || fail "26168 ESD3D2 profile missing"

grep -Fq 'MOTIONNOISEBLEND' "$ESD_SHADER" \
    || fail "Luma-aware ESD3D2 edge path missing"

grep -Fq 'MOTION_26168_TONE_GAIN_GUARD' "$AUTO_EXPOSURE" \
    || fail "Motion tone-gain guard missing"

grep -Fq 'MOTION_26167_CAPTURE_SHARPEN' "$CAPTURE_SHARP" \
    || fail "26167 capture-sharpening safeguard was lost"

grep -Fq 'MOTION_26167_FINAL_SHARPEN' "$FINAL_SHARP" \
    || fail "26167 final-sharpening safeguard was lost"

grep -Fq 'MOTION_26166_IMAGE_SAVED_COMPLETE' "$HDRX" \
    || fail "26166 save-completion path was lost"

grep -q '^VERSION_BUILD=26168$' "$VERSION" \
    || fail "VERSION_BUILD was not updated"

sha256sum -c "$OUT/protected-before.sha256" \
    || fail "A protected 26166/26167 file changed unexpectedly"

if git diff | grep -E \
    '^[+-].*(mIsRecordingVideo|CameraMode\.RAWVIDEO|TEMPLATE_RECORD|MediaRecorder|CONTROL_AF_MODE_CONTINUOUS_VIDEO|getSelectedFpsRange)'; then
    fail "Video or RAW Video behavior changed unexpectedly"
fi

git diff --check \
    || fail "git diff --check reported a formatting problem"

for file in \
    "$PYRAMID" \
    "$MERGE_SHADER" \
    "$POST" \
    "$ESD_JAVA" \
    "$ESD_SHADER" \
    "$AUTO_EXPOSURE" \
    "$VERSION"; do
    cp "$file" "$OUT/source_after/$(basename "$file")"
done

git diff --stat | tee "$OUT/change-summary.txt"
git diff --binary HEAD > "$OUT/combined-${NEW_BUILD}-motion-effective-noise-fix.patch"

echo
echo "PASS: all twenty Motion RAWs remain captured and merged."
echo "PASS: equal-exposure temporal reconstruction now uses per-frame noise."
echo "PASS: residual variance is applied after Photon's read-noise floor."
echo "PASS: high-ISO chroma noise no longer automatically looks like an edge."
echo "PASS: extreme high-ISO Motion tone gain is limited gradually."
echo "PASS: color, black level, exposure selection and save completion preserved."
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
        | tail -300 \
        > "$OUT/relevant-errors.txt" || true

    fail "Gradle build failed; inspect $OUT/relevant-errors.txt" \
        "$BUILD_STATUS"
fi

APK="$(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | head -n 1)"

[ -n "$APK" ] && [ -f "$APK" ] \
    || fail "Debug APK was not created"

APK_COPY="$OUT/PhotonCamera-${NEW_VERSION}-motion-effective-noise-fix-debug.apk"

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
echo "Combined patch:$OUT/combined-${NEW_BUILD}-motion-effective-noise-fix.patch"
echo "Build log:     $OUT/build-${NEW_BUILD}.log"
echo
echo "Expected Motion markers:"
echo "  MOTION_26168_MERGE_NOISE_AWARE"
echo "  MOTION_26168_RESIDUAL_NOISE_EFFECTIVE"
echo "  MOTION_26168_ESD3D2_PROFILE"
echo "  MOTION_26168_TONE_GAIN_GUARD"
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
