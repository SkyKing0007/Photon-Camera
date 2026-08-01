#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
EXPECTED_BUILD="26169"
NEW_BUILD="26170"
NEW_VERSION="0.9726170"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="/workspaces/Photon-Camera/build_${NEW_BUILD}_motion_gcam_noise_balance_${STAMP}"
BACKUP_BRANCH="backup-before-motion-gcam-noise-${NEW_BUILD}-${STAMP}"

POST="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
ESD_JAVA="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java"
ESD_SHADER="app/src/main/assets/shaders/denoise/esd3d2.glsl"
CHROMA_JAVA="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java"
CHROMA_SHADER="app/src/main/assets/shaders/denoise/motionchromadenoise.glsl"
LUMA_JAVA="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java"
LUMA_SHADER="app/src/main/assets/shaders/denoise/motionlumadenoise.glsl"
AUTO_EXPOSURE="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/AutoExposure.java"
CAPTURE_SHARP="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java"
FINAL_SHARP="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java"
VERSION="app/version.properties"

# Protected established behavior.
CAPTURE="app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
PARAMS="app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java"
HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
INITIAL="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java"
COLOR_SHADER="app/src/main/assets/shaders/initial.glsl"
PYRAMID="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts/PyramidMerging.java"
MERGE_SHADER="app/src/main/assets/shaders/merge/merge11.glsl"
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

trap 'code=$?; if [ "$code" -ne 0 ]; then echo; echo "FAILED: build 26170 (exit $code)"; echo "Workspace: $OUT"; fi' EXIT

echo "============================================================"
echo " PhotonCamera ${NEW_VERSION}"
echo " Motion GCam-reference noise balance"
echo "============================================================"

[ "$(git branch --show-current)" = "$EXPECTED_BRANCH" ] \
    || fail "Expected branch $EXPECTED_BRANCH"

[ "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" ] \
    || fail "Expected HEAD $EXPECTED_HEAD"

grep -q "^VERSION_BUILD=${EXPECTED_BUILD}$" "$VERSION" \
    || fail "Expected VERSION_BUILD=${EXPECTED_BUILD}"

EXPECTED_MODIFIED="$ESD_SHADER
$MERGE_SHADER
$CAPTURE
$AUTO_EXPOSURE
$CAPTURE_SHARP
$ESD_JAVA
$INITIAL
$POST
$FINAL_SHARP
$PYRAMID
$HDRX
$PARAMS
$VERSION"

ACTUAL_MODIFIED="$(git status --short --untracked-files=no | awk '{print $2}' | sort)"
EXPECTED_SORTED="$(printf '%s\n' "$EXPECTED_MODIFIED" | sort)"

[ "$ACTUAL_MODIFIED" = "$EXPECTED_SORTED" ] \
    || {
        echo "Expected current 26169 tracked changes:"
        printf '%s\n' "$EXPECTED_SORTED"
        echo
        echo "Actual tracked changes:"
        printf '%s\n' "$ACTUAL_MODIFIED"
        fail "Working tree is not the verified 26169 state"
    }

[ -f "$CHROMA_JAVA" ] \
    || fail "26169 MotionChromaDenoise.java is missing"

[ -f "$CHROMA_SHADER" ] \
    || fail "26169 motionchromadenoise.glsl is missing"

[ ! -e "$LUMA_JAVA" ] \
    || fail "Unexpected existing file: $LUMA_JAVA"

[ ! -e "$LUMA_SHADER" ] \
    || fail "Unexpected existing file: $LUMA_SHADER"

grep -Fq 'MOTION_26169_CHROMA_DETAIL_STAGE' "$CHROMA_JAVA" \
    || fail "26169 chroma stage marker missing"

grep -Fq 'MOTION_26169_ESD3D2_DETAIL_PROFILE' "$ESD_JAVA" \
    || fail "26169 ESD3D2 profile missing"

grep -Fq 'MOTION_26168_MERGE_NOISE_AWARE' "$PYRAMID" \
    || fail "26168 temporal merge correction missing"

grep -Fq 'predictedNoiseCap' "$MERGE_SHADER" \
    || fail "26168 temporal merge shader correction missing"

grep -Fq 'MOTION_26168_RESIDUAL_NOISE_EFFECTIVE' "$POST" \
    || fail "26168 post-floor residual-noise path missing"

grep -Fq 'MOTION_26168_TONE_GAIN_GUARD' "$AUTO_EXPOSURE" \
    || fail "26168 tone-gain guard missing"

grep -Fq 'MOTION_26167_CAPTURE_SHARPEN' "$CAPTURE_SHARP" \
    || fail "26167 capture-sharpening guard missing"

grep -Fq 'MOTION_26167_FINAL_SHARPEN' "$FINAL_SHARP" \
    || fail "26167 final-sharpening guard missing"

grep -Fq 'MOTION_26165_HOMOGENEOUS_RAW_STACK' "$CAPTURE" \
    || fail "Homogeneous twenty-frame Motion stack missing"

grep -Fq 'MOTION_26166_BLACK_LEVEL_SELECTED' "$CAPTURE" \
    || fail "Validated Motion black-level path missing"

grep -Fq 'MOTION_26166_IMAGE_SAVED_COMPLETE' "$HDRX" \
    || fail "Post-save Motion completion path missing"

grep -Fq 'pRGB = corr*sensorToIntermediate*(pRGB*neutralPoint);' "$COLOR_SHADER" \
    || fail "Original Photon color shader missing"

mkdir -p "$OUT/source_before" "$OUT/source_after"

echo
echo "=== CREATE BACKUP BRANCH AND COMPLETE PATCH ==="

git branch "$BACKUP_BRANCH" HEAD

{
    git diff --binary HEAD
    git diff --binary --no-index /dev/null "$CHROMA_JAVA" || true
    git diff --binary --no-index /dev/null "$CHROMA_SHADER" || true
} > "$OUT/working-tree-before-${NEW_BUILD}.patch"

for file in \
    "$POST" \
    "$ESD_JAVA" \
    "$ESD_SHADER" \
    "$CHROMA_JAVA" \
    "$CHROMA_SHADER" \
    "$AUTO_EXPOSURE" \
    "$CAPTURE_SHARP" \
    "$FINAL_SHARP" \
    "$VERSION"; do
    cp "$file" "$OUT/source_before/$(basename "$file")"
done

printf '%s\n' \
    "ABSENT BEFORE 26170: $LUMA_JAVA" \
    "ABSENT BEFORE 26170: $LUMA_SHADER" \
    > "$OUT/source_before/new-files-status.txt"

sha256sum \
    "$CAPTURE" \
    "$PARAMS" \
    "$HDRX" \
    "$INITIAL" \
    "$COLOR_SHADER" \
    "$PYRAMID" \
    "$MERGE_SHADER" \
    "$EXPOSURE_SELECTOR" \
    > "$OUT/protected-before.sha256"

echo "Backup branch: $BACKUP_BRANCH"
echo "Backup patch:  $OUT/working-tree-before-${NEW_BUILD}.patch"

echo
echo "=== APPLY 26170 TRACKED-FILE CHANGES ==="

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
auto_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/opengl/postpipeline/AutoExposure.java"
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
# ESD3D2:
# - retain mostly RGB edge detection;
# - use stable bilateral weights at high ISO instead of the sparse
#   subtract-minimum SNN pattern that creates connected worm structures;
# - use an independent minimum for the chroma weights.
# -------------------------------------------------------------------------

esd_java = esd_java_path.read_text()

old_declaration = """            float motionNoiseBlend =
                    0.0f;

            if (com.particlesdevs.photoncamera.app.PhotonCamera
"""

new_declaration = """            float motionNoiseBlend =
                    0.0f;

            float motionStableWeights =
                    0.0f;

            if (com.particlesdevs.photoncamera.app.PhotonCamera
"""

esd_java = replace_once(
    esd_java,
    old_declaration,
    new_declaration,
    "ESD3D2 stable-weight declaration",
)

old_profile = """                motionNoiseBlend =
                        0.30f * highIsoBlend;

                appliedShadowBoost =
                        Math.max(
                                shadowBoost,
                                0.50f + 0.30f * highIsoBlend
                        );

                Log.d(
                        Name,
                        "MOTION_26169_ESD3D2_DETAIL_PROFILE"
"""

new_profile = """                /*
                 * Build 26170:
                 * Stable bilateral weights suppress connected noise worms
                 * without restoring the broad luma softness from 26168.
                 */
                motionNoiseBlend =
                        0.10f * highIsoBlend;

                motionStableWeights =
                        0.65f * highIsoBlend;

                appliedShadowBoost =
                        Math.max(
                                shadowBoost,
                                0.50f + 0.20f * highIsoBlend
                        );

                Log.d(
                        Name,
                        "MOTION_26170_ESD3D2_STABLE_WEIGHTS"
"""

esd_java = replace_once(
    esd_java,
    old_profile,
    new_profile,
    "ESD3D2 26170 Motion profile",
)

old_log = """                                + " motionNoiseBlend="
                                + motionNoiseBlend
                                + " motionNoiseBlendMaximum=0.30"
                                + " edgeMetric="
                                + "mostlyRgbWithLimitedLumaAssist"
                                + " dedicatedChromaStage=true"
                                + " readNoiseSource=NOISEO"
"""

new_log = """                                + " motionNoiseBlend="
                                + motionNoiseBlend
                                + " motionNoiseBlendMaximum=0.10"
                                + " stableWeightBlend="
                                + motionStableWeights
                                + " stableWeightBlendMaximum=0.65"
                                + " chromaMinimumIndependent=true"
                                + " edgeMetric="
                                + "rgbDominant"
                                + " dedicatedLumaStage=true"
                                + " dedicatedCoarseChromaStage=true"
                                + " readNoiseSource=NOISEO"
"""

esd_java = replace_once(
    esd_java,
    old_log,
    new_log,
    "ESD3D2 26170 log",
)

old_define_set = """            glProg.setDefine(
                    "MOTIONNOISEBLEND",
                    motionNoiseBlend
            );

            glProg.setDefine("INSIZE", basePipeline.mParameters.rawSize);
"""

new_define_set = """            glProg.setDefine(
                    "MOTIONNOISEBLEND",
                    motionNoiseBlend
            );
            glProg.setDefine(
                    "MOTIONSTABLEWEIGHTS",
                    motionStableWeights
            );

            glProg.setDefine("INSIZE", basePipeline.mParameters.rawSize);
"""

esd_java = replace_once(
    esd_java,
    old_define_set,
    new_define_set,
    "ESD3D2 stable-weight shader define",
)

esd_java_path.write_text(esd_java)


esd_shader = esd_shader_path.read_text()

old_shader_define = """#define CHROMASTRENGTH 1.0
#define MOTIONNOISEBLEND 0.0
#define PI 3.1415926535897932384626433832795
"""

new_shader_define = """#define CHROMASTRENGTH 1.0
#define MOTIONNOISEBLEND 0.0
#define MOTIONSTABLEWEIGHTS 0.0
#define PI 3.1415926535897932384626433832795
"""

esd_shader = replace_once(
    esd_shader,
    old_shader_define,
    new_shader_define,
    "ESD3D2 stable-weight define",
)

old_weight_block = """            vec4 w = (1.0-d*d/(d*d + sigY));
            vec4 w2 = (1.0-d*d/(d*d + sigZ));
            float wm = min(min(min(w[0],w[1]),w[2]),w[3])*1.0;
            vec4 ws = w - wm;
            ws /= length(ws) + 0.000001;
            vec4 w2s = w2 - wm;
            w2s /= length(w2s) + 0.000001;
            w *= ws;
            w2 *= w2s;
            float f1 = normpdf(float(i),KERNELSIZE)*normpdf(float(j),KERNELSIZE);
"""

new_weight_block = """            vec4 w = (1.0-d*d/(d*d + sigY));
            vec4 w2 = (1.0-d*d/(d*d + sigZ));

            vec4 stableW =
                    max(
                            w,
                            vec4(0.0)
                    );

            vec4 stableW2 =
                    max(
                            w2,
                            vec4(0.0)
                    );

            float wm =
                    min(
                            min(
                                    min(w[0], w[1]),
                                    w[2]
                            ),
                            w[3]
                    );

            float wm2 =
                    min(
                            min(
                                    min(w2[0], w2[1]),
                                    w2[2]
                            ),
                            w2[3]
                    );

            vec4 ws =
                    w - wm;

            ws /=
                    length(ws)
                            + 0.000001;

            vec4 w2s =
                    w2 - wm2;

            w2s /=
                    length(w2s)
                            + 0.000001;

            vec4 sparseW =
                    w * ws;

            vec4 sparseW2 =
                    w2 * w2s;

            /*
             * The original sparse SNN weights can connect random residual
             * noise into worms. Blend toward ordinary bilateral weights only
             * for noisy Motion captures.
             */
            w =
                    mix(
                            sparseW,
                            stableW,
                            MOTIONSTABLEWEIGHTS
                    );

            w2 =
                    mix(
                            sparseW2,
                            stableW2,
                            MOTIONSTABLEWEIGHTS
                    );

            float f1 = normpdf(float(i),KERNELSIZE)*normpdf(float(j),KERNELSIZE);
"""

esd_shader = replace_once(
    esd_shader,
    old_weight_block,
    new_weight_block,
    "ESD3D2 stable bilateral weighting",
)

esd_shader_path.write_text(esd_shader)


# -------------------------------------------------------------------------
# Pipeline:
# luma-worm cleanup first, then coarse chroma-cloud cleanup, then tone lift.
# -------------------------------------------------------------------------

post = post_path.read_text()

old_order = """        if (mSettings.selectedMode == CameraMode.MOTION
                && mSettings.hdrxNR) {
            add(new MotionChromaDenoise());
        }

        add(new AutoExposure());
"""

new_order = """        if (mSettings.selectedMode == CameraMode.MOTION
                && mSettings.hdrxNR) {
            add(new MotionLumaDenoise());
            add(new MotionChromaDenoise());
        }

        add(new AutoExposure());
"""

post = replace_once(
    post,
    old_order,
    new_order,
    "26170 Motion luma/chroma pipeline order",
)

post_path.write_text(post)


# -------------------------------------------------------------------------
# Tone:
# GCam reference preserves darker shadows. Reduce only the maximum high-ISO
# Motion post gain from 4.5x to 4.0x.
# -------------------------------------------------------------------------

auto = auto_path.read_text()

auto = replace_once(
    auto,
    '                            4.5f\n',
    '                            4.0f\n',
    "Motion high-ISO gain limit",
)

auto = replace_once(
    auto,
    '"MOTION_26168_TONE_GAIN_GUARD"',
    '"MOTION_26170_TONE_GAIN_GUARD"',
    "Motion tone marker",
)

auto_path.write_text(auto)


# -------------------------------------------------------------------------
# Sharpening:
# At ISO 3200, scale falls from 0.55 to 0.10. This prevents surviving
# residual noise from being converted back into hard worms and colored grit.
# -------------------------------------------------------------------------

capture_sharp = capture_sharp_path.read_text()

capture_sharp = replace_once(
    capture_sharp,
    '                    1.0f - 0.45f * highIsoBlend;',
    '                    1.0f - 0.90f * highIsoBlend;',
    "CaptureSharpening ISO attenuation",
)

capture_sharp = replace_once(
    capture_sharp,
    '"MOTION_26167_CAPTURE_SHARPEN"',
    '"MOTION_26170_CAPTURE_SHARPEN"',
    "CaptureSharpening marker",
)

capture_sharp_path.write_text(capture_sharp)


final_sharp = final_sharp_path.read_text()

final_sharp = replace_once(
    final_sharp,
    '                    1.0f - 0.45f * highIsoBlend;',
    '                    1.0f - 0.90f * highIsoBlend;',
    "Sharpen2 ISO attenuation",
)

final_sharp = replace_once(
    final_sharp,
    '"MOTION_26167_FINAL_SHARPEN"',
    '"MOTION_26170_FINAL_SHARPEN"',
    "Sharpen2 marker",
)

final_sharp_path.write_text(final_sharp)


version = version_path.read_text()

if version.count("VERSION_BUILD=26169") != 1:
    raise SystemExit(
        "ERROR: expected exactly one VERSION_BUILD=26169"
    )

version_path.write_text(
    version.replace(
        "VERSION_BUILD=26169",
        "VERSION_BUILD=26170",
        1,
    )
)
PY

echo
echo "=== REPLACE MOTION CHROMA STAGE ==="

cat > "$CHROMA_JAVA" <<'JAVA'
package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.api.CameraMode;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;
import com.particlesdevs.photoncamera.util.Math2;

public class MotionChromaDenoise extends Node {
    public MotionChromaDenoise() {
        super("", "MotionChromaDenoise");
    }

    @Override
    public void Compile() {
    }

    private void configurePass(
            int direction,
            float strength,
            float guideSigma
    ) {
        glProg.setDefine("DIRECTION", direction);
        glProg.setDefine("KSIZE", 6);
        glProg.setDefine("SAMPLESTEP", 8);
        glProg.setDefine("CHROMASTRENGTH", strength);
        glProg.setDefine("GUIDESIGMA", guideSigma);
        glProg.setDefine("NOISES", basePipeline.noiseS);
        glProg.setDefine("NOISEO", basePipeline.noiseO);
    }

    @Override
    public void Run() {
        if (PhotonCamera.getSettings().selectedMode
                != CameraMode.MOTION) {
            WorkingTexture = previousNode.WorkingTexture;
            return;
        }

        float motionIso =
                Math.max(
                        1.0f,
                        basePipeline.mParameters.iso
                );

        float highIsoBlend =
                Math2.clamp(
                        (motionIso - 600.0f) / 2600.0f,
                        0.0f,
                        1.0f
                );

        float strength =
                0.90f * highIsoBlend;

        if (strength <= 0.001f) {
            Log.d(
                    Name,
                    "MOTION_26170_CHROMA_COARSE"
                            + " iso=" + motionIso
                            + " enabled=false"
                            + " reason=belowIso600"
                            + " lumaPreserved=true"
            );

            WorkingTexture = previousNode.WorkingTexture;
            return;
        }

        float guideSigma =
                0.060f
                        + 0.060f * highIsoBlend;

        configurePass(
                0,
                strength,
                guideSigma
        );

        glProg.useAssetProgram(
                "denoise/motionchromadenoise"
        );

        glProg.setTexture(
                "InputBuffer",
                previousNode.WorkingTexture
        );

        glProg.setTexture(
                "GuideBuffer",
                previousNode.WorkingTexture
        );

        glProg.drawBlocks(
                basePipeline.main3
        );

        glProg.closed = true;

        configurePass(
                1,
                strength,
                guideSigma
        );

        glProg.useAssetProgram(
                "denoise/motionchromadenoise"
        );

        glProg.setTexture(
                "InputBuffer",
                basePipeline.main3
        );

        glProg.setTexture(
                "GuideBuffer",
                previousNode.WorkingTexture
        );

        WorkingTexture =
                basePipeline.getMain();

        glProg.drawBlocks(
                WorkingTexture
        );

        glProg.closed = true;

        Log.d(
                Name,
                "MOTION_26170_CHROMA_COARSE"
                        + " iso=" + motionIso
                        + " enabled=true"
                        + " highIsoBlend=" + highIsoBlend
                        + " strength=" + strength
                        + " guideSigma=" + guideSigma
                        + " passes=2"
                        + " kernelRadiusSamples=6"
                        + " sampleStepPixels=8"
                        + " fullRadiusPixels=48"
                        + " fullDiameterPixels=96"
                        + " centerChromaSimilarityUsed=false"
                        + " sampleSaturationProtected=true"
                        + " deepestShadowNeutralityGuard=0.18"
                        + " representation=Y_RminusG_BminusG"
                        + " lumaPreserved=true"
                        + " noiseAwareFlatMask=true"
                        + " placement=afterLumaBeforeAutoExposure"
        );
    }
}
JAVA

cat > "$CHROMA_SHADER" <<'GLSL'
precision highp float;
precision highp sampler2D;

uniform sampler2D InputBuffer;
uniform sampler2D GuideBuffer;
uniform int yOffset;

out vec4 Output;

#define DIRECTION 0
#define KSIZE 6
#define SAMPLESTEP 8
#define CHROMASTRENGTH 0.0
#define GUIDESIGMA 0.10
#define NOISES 0.0
#define NOISEO 0.0

float lumaValue(vec3 rgb) {
    return dot(
            rgb,
            vec3(0.25, 0.50, 0.25)
    );
}

vec2 opponentChroma(vec3 rgb) {
    return vec2(
            rgb.r - rgb.g,
            rgb.b - rgb.g
    );
}

vec3 reconstructFromLumaChroma(
        float y,
        vec2 uv
) {
    float r =
            y + 0.75 * uv.x - 0.25 * uv.y;

    float g =
            y - 0.25 * uv.x - 0.25 * uv.y;

    float b =
            y - 0.25 * uv.x + 0.75 * uv.y;

    return vec3(r, g, b);
}

float gaussianWeight(
        float value,
        float sigma
) {
    float safeSigma =
            max(
                    sigma,
                    0.0001
            );

    float normalized =
            value / safeSigma;

    return exp(
            -0.5 * normalized * normalized
    );
}

void main() {
    ivec2 xy =
            ivec2(gl_FragCoord.xy)
                    + ivec2(0, yOffset);

    ivec2 imageSize =
            textureSize(
                    GuideBuffer,
                    0
            );

    ivec2 maximumCoordinate =
            imageSize - ivec2(1);

    vec3 guideCenter =
            texelFetch(
                    GuideBuffer,
                    xy,
                    0
            ).rgb;

    vec3 inputCenter =
            texelFetch(
                    InputBuffer,
                    xy,
                    0
            ).rgb;

    float centerLuma =
            lumaValue(
                    guideCenter
            );

    vec2 centerChroma =
            opponentChroma(
                    inputCenter
            );

    float noiseSigma =
            sqrt(
                    max(
                            NOISES
                                    * max(centerLuma, 0.0)
                                    + NOISEO,
                            0.000001
                    )
            );

    float localGradient =
            0.0;

    const ivec2 localOffsets[4] =
            ivec2[4](
                    ivec2(-1, 0),
                    ivec2(1, 0),
                    ivec2(0, -1),
                    ivec2(0, 1)
            );

    for (int index = 0; index < 4; index++) {
        ivec2 localCoordinate =
                clamp(
                        xy + localOffsets[index],
                        ivec2(0),
                        maximumCoordinate
                );

        float localLuma =
                lumaValue(
                        texelFetch(
                                GuideBuffer,
                                localCoordinate,
                                0
                        ).rgb
                );

        localGradient =
                max(
                        localGradient,
                        abs(
                                localLuma - centerLuma
                        )
                );
    }

    float flatThresholdLow =
            max(
                    0.025,
                    noiseSigma * 1.5
            );

    float flatThresholdHigh =
            max(
                    0.100,
                    noiseSigma * 5.0
            );

    float flatMask =
            1.0
                    - smoothstep(
                            flatThresholdLow,
                            flatThresholdHigh,
                            localGradient
                    );

    float darkMask =
            1.0
                    - smoothstep(
                            0.58,
                            0.92,
                            centerLuma
                    );

    float centerSaturation =
            length(
                    opponentChroma(
                            guideCenter
                    )
            );

    float saturatedCenterProtection =
            1.0
                    - smoothstep(
                            0.45,
                            0.75,
                            centerSaturation
                    );

    vec2 accumulatedChroma =
            vec2(0.0);

    float accumulatedWeight =
            0.0;

    ivec2 direction =
            DIRECTION == 0
                    ? ivec2(1, 0)
                    : ivec2(0, 1);

    for (int offsetIndex = -KSIZE;
         offsetIndex <= KSIZE;
         offsetIndex++) {

        ivec2 sampleCoordinate =
                clamp(
                        xy
                                + direction
                                * offsetIndex
                                * SAMPLESTEP,
                        ivec2(0),
                        maximumCoordinate
                );

        vec3 sampleGuide =
                texelFetch(
                        GuideBuffer,
                        sampleCoordinate,
                        0
                ).rgb;

        vec3 sampleInput =
                texelFetch(
                        InputBuffer,
                        sampleCoordinate,
                        0
                ).rgb;

        float sampleLuma =
                lumaValue(
                        sampleGuide
                );

        vec2 sampleChroma =
                opponentChroma(
                        sampleInput
                );

        float spatialWeight =
                gaussianWeight(
                        float(offsetIndex),
                        3.5
                );

        float lumaGuideWeight =
                gaussianWeight(
                        sampleLuma - centerLuma,
                        GUIDESIGMA
                );

        /*
         * Do not compare sample chroma with the center chroma. The 26169
         * comparison caused pixels inside a colored cloud to reinforce that
         * same cloud. Only strongly saturated real colors are downweighted.
         */
        float sampleSaturation =
                length(
                        opponentChroma(
                                sampleGuide
                        )
                );

        float sampleColorProtection =
                1.0
                        - smoothstep(
                                0.45,
                                0.85,
                                sampleSaturation
                        );

        float sampleWeight =
                spatialWeight
                        * lumaGuideWeight
                        * mix(
                                0.15,
                                1.0,
                                sampleColorProtection
                          );

        accumulatedChroma +=
                sampleChroma
                        * sampleWeight;

        accumulatedWeight +=
                sampleWeight;
    }

    vec2 filteredChroma =
            accumulatedWeight > 0.000001
                    ? accumulatedChroma
                            / accumulatedWeight
                    : centerChroma;

    float blend =
            clamp(
                    CHROMASTRENGTH
                            * flatMask
                            * darkMask
                            * saturatedCenterProtection,
                    0.0,
                    1.0
            );

    vec2 outputChroma =
            mix(
                    centerChroma,
                    filteredChroma,
                    blend
            );

    /*
     * Equal per-channel black levels were validated in the supplied session.
     * Instead of inventing a black offset, gently reduce only residual
     * chroma in the deepest, flat, high-ISO shadows.
     */
    float deepestShadowMask =
            1.0
                    - smoothstep(
                            0.10,
                            0.32,
                            centerLuma
                    );

    float neutralityStrength =
            0.18
                    * CHROMASTRENGTH
                    * flatMask
                    * deepestShadowMask
                    * saturatedCenterProtection;

    outputChroma *=
            1.0
                    - clamp(
                            neutralityStrength,
                            0.0,
                            0.18
                    );

    vec3 outputRgb =
            reconstructFromLumaChroma(
                    centerLuma,
                    outputChroma
            );

    Output =
            vec4(
                    clamp(
                            outputRgb,
                            0.0,
                            1.0
                    ),
                    1.0
            );
}
GLSL

echo
echo "=== CREATE MOTION LUMA-WORM STAGE ==="

cat > "$LUMA_JAVA" <<'JAVA'
package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.api.CameraMode;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;
import com.particlesdevs.photoncamera.util.Math2;

public class MotionLumaDenoise extends Node {
    public MotionLumaDenoise() {
        super("", "MotionLumaDenoise");
    }

    @Override
    public void Compile() {
    }

    private void configurePass(
            int direction,
            float strength,
            float noiseGain
    ) {
        glProg.setDefine("DIRECTION", direction);
        glProg.setDefine("KSIZE", 3);
        glProg.setDefine("STRENGTH", strength);
        glProg.setDefine("NOISEGAIN", noiseGain);
        glProg.setDefine("NOISES", basePipeline.noiseS);
        glProg.setDefine("NOISEO", basePipeline.noiseO);
    }

    @Override
    public void Run() {
        if (PhotonCamera.getSettings().selectedMode
                != CameraMode.MOTION) {
            WorkingTexture = previousNode.WorkingTexture;
            return;
        }

        float motionIso =
                Math.max(
                        1.0f,
                        basePipeline.mParameters.iso
                );

        float highIsoBlend =
                Math2.clamp(
                        (motionIso - 800.0f) / 2400.0f,
                        0.0f,
                        1.0f
                );

        float strength =
                0.55f * highIsoBlend;

        if (strength <= 0.001f) {
            Log.d(
                    Name,
                    "MOTION_26170_LUMA_WORM_CLEANUP"
                            + " iso=" + motionIso
                            + " enabled=false"
                            + " reason=belowIso800"
                            + " chromaPreserved=true"
            );

            WorkingTexture = previousNode.WorkingTexture;
            return;
        }

        float noiseGain =
                1.35f;

        configurePass(
                0,
                strength,
                noiseGain
        );

        glProg.useAssetProgram(
                "denoise/motionlumadenoise"
        );

        glProg.setTexture(
                "InputBuffer",
                previousNode.WorkingTexture
        );

        glProg.setTexture(
                "GuideBuffer",
                previousNode.WorkingTexture
        );

        glProg.drawBlocks(
                basePipeline.main3
        );

        glProg.closed = true;

        configurePass(
                1,
                strength,
                noiseGain
        );

        glProg.useAssetProgram(
                "denoise/motionlumadenoise"
        );

        glProg.setTexture(
                "InputBuffer",
                basePipeline.main3
        );

        glProg.setTexture(
                "GuideBuffer",
                previousNode.WorkingTexture
        );

        WorkingTexture =
                basePipeline.getMain();

        glProg.drawBlocks(
                WorkingTexture
        );

        glProg.closed = true;

        Log.d(
                Name,
                "MOTION_26170_LUMA_WORM_CLEANUP"
                        + " iso=" + motionIso
                        + " enabled=true"
                        + " highIsoBlend=" + highIsoBlend
                        + " strength=" + strength
                        + " noiseGain=" + noiseGain
                        + " passes=2"
                        + " kernelRadiusPixels=3"
                        + " policy=noiseThresholdedFlatDarkOnly"
                        + " chromaPreserved=true"
                        + " strongEdgesPreserved=true"
                        + " placement=afterInitialBeforeCoarseChroma"
        );
    }
}
JAVA

cat > "$LUMA_SHADER" <<'GLSL'
precision highp float;
precision highp sampler2D;

uniform sampler2D InputBuffer;
uniform sampler2D GuideBuffer;
uniform int yOffset;

out vec4 Output;

#define DIRECTION 0
#define KSIZE 3
#define STRENGTH 0.0
#define NOISEGAIN 1.35
#define NOISES 0.0
#define NOISEO 0.0

float lumaValue(vec3 rgb) {
    return dot(
            rgb,
            vec3(0.25, 0.50, 0.25)
    );
}

vec2 opponentChroma(vec3 rgb) {
    return vec2(
            rgb.r - rgb.g,
            rgb.b - rgb.g
    );
}

vec3 reconstructFromLumaChroma(
        float y,
        vec2 uv
) {
    float r =
            y + 0.75 * uv.x - 0.25 * uv.y;

    float g =
            y - 0.25 * uv.x - 0.25 * uv.y;

    float b =
            y - 0.25 * uv.x + 0.75 * uv.y;

    return vec3(r, g, b);
}

float gaussianWeight(
        float value,
        float sigma
) {
    float safeSigma =
            max(
                    sigma,
                    0.0001
            );

    float normalized =
            value / safeSigma;

    return exp(
            -0.5 * normalized * normalized
    );
}

void main() {
    ivec2 xy =
            ivec2(gl_FragCoord.xy)
                    + ivec2(0, yOffset);

    ivec2 imageSize =
            textureSize(
                    GuideBuffer,
                    0
            );

    ivec2 maximumCoordinate =
            imageSize - ivec2(1);

    vec3 guideCenter =
            texelFetch(
                    GuideBuffer,
                    xy,
                    0
            ).rgb;

    vec3 inputCenter =
            texelFetch(
                    InputBuffer,
                    xy,
                    0
            ).rgb;

    float guideLuma =
            lumaValue(
                    guideCenter
            );

    float inputLuma =
            lumaValue(
                    inputCenter
            );

    vec2 originalChroma =
            opponentChroma(
                    guideCenter
            );

    float noiseSigma =
            sqrt(
                    max(
                            NOISES
                                    * max(guideLuma, 0.0)
                                    + NOISEO,
                            0.000001
                    )
            )
                    * NOISEGAIN;

    float localGradient =
            0.0;

    const ivec2 localOffsets[4] =
            ivec2[4](
                    ivec2(-1, 0),
                    ivec2(1, 0),
                    ivec2(0, -1),
                    ivec2(0, 1)
            );

    for (int index = 0; index < 4; index++) {
        ivec2 localCoordinate =
                clamp(
                        xy + localOffsets[index],
                        ivec2(0),
                        maximumCoordinate
                );

        float localLuma =
                lumaValue(
                        texelFetch(
                                GuideBuffer,
                                localCoordinate,
                                0
                        ).rgb
                );

        localGradient =
                max(
                        localGradient,
                        abs(
                                localLuma - guideLuma
                        )
                );
    }

    ivec2 direction =
            DIRECTION == 0
                    ? ivec2(1, 0)
                    : ivec2(0, 1);

    float accumulatedLuma =
            0.0;

    float accumulatedWeight =
            0.0;

    float guideSigma =
            max(
                    0.025,
                    noiseSigma * 4.0
            );

    for (int offsetIndex = -KSIZE;
         offsetIndex <= KSIZE;
         offsetIndex++) {

        ivec2 sampleCoordinate =
                clamp(
                        xy
                                + direction
                                * offsetIndex,
                        ivec2(0),
                        maximumCoordinate
                );

        float sampleGuideLuma =
                lumaValue(
                        texelFetch(
                                GuideBuffer,
                                sampleCoordinate,
                                0
                        ).rgb
                );

        float sampleInputLuma =
                lumaValue(
                        texelFetch(
                                InputBuffer,
                                sampleCoordinate,
                                0
                        ).rgb
                );

        float spatialWeight =
                gaussianWeight(
                        float(offsetIndex),
                        1.65
                );

        float guideWeight =
                gaussianWeight(
                        sampleGuideLuma - guideLuma,
                        guideSigma
                );

        float sampleWeight =
                spatialWeight
                        * guideWeight;

        accumulatedLuma +=
                sampleInputLuma
                        * sampleWeight;

        accumulatedWeight +=
                sampleWeight;
    }

    float filteredLuma =
            accumulatedWeight > 0.000001
                    ? accumulatedLuma
                            / accumulatedWeight
                    : inputLuma;

    float residual =
            abs(
                    inputLuma - filteredLuma
            );

    /*
     * Residuals inside the modeled-noise range are cleaned. Larger residuals
     * are treated as genuine structure, preventing general softness.
     */
    float noiseResidualMask =
            1.0
                    - smoothstep(
                            noiseSigma * 1.25,
                            noiseSigma * 4.50,
                            residual
                    );

    float flatMask =
            1.0
                    - smoothstep(
                            max(
                                    0.020,
                                    noiseSigma * 1.20
                            ),
                            max(
                                    0.085,
                                    noiseSigma * 4.50
                            ),
                            localGradient
                    );

    float darkMask =
            1.0
                    - smoothstep(
                            0.50,
                            0.90,
                            guideLuma
                    );

    float blend =
            clamp(
                    STRENGTH
                            * noiseResidualMask
                            * flatMask
                            * darkMask,
                    0.0,
                    1.0
            );

    float outputLuma =
            mix(
                    inputLuma,
                    filteredLuma,
                    blend
            );

    vec3 outputRgb =
            reconstructFromLumaChroma(
                    outputLuma,
                    originalChroma
            );

    Output =
            vec4(
                    clamp(
                            outputRgb,
                            0.0,
                            1.0
                    ),
                    1.0
            );
}
GLSL

echo
echo "=== VERIFY 26170 SOURCE ==="

grep -Fq 'MOTION_26170_ESD3D2_STABLE_WEIGHTS' "$ESD_JAVA" \
    || fail "Stable ESD3D2 marker missing"

grep -Fq 'MOTIONSTABLEWEIGHTS' "$ESD_SHADER" \
    || fail "Stable ESD3D2 shader path missing"

grep -Fq 'float wm2' "$ESD_SHADER" \
    || fail "Independent chroma-weight minimum missing"

grep -Fq 'MOTION_26170_LUMA_WORM_CLEANUP' "$LUMA_JAVA" \
    || fail "Luma-worm cleanup marker missing"

grep -Fq 'noiseResidualMask' "$LUMA_SHADER" \
    || fail "Noise-thresholded luma policy missing"

grep -Fq 'originalChroma' "$LUMA_SHADER" \
    || fail "Luma stage does not preserve original chroma"

grep -Fq 'MOTION_26170_CHROMA_COARSE' "$CHROMA_JAVA" \
    || fail "Coarse chroma marker missing"

grep -Fq 'fullRadiusPixels=48' "$CHROMA_JAVA" \
    || fail "Coarse chroma radius marker missing"

grep -Fq 'centerChromaSimilarityUsed=false' "$CHROMA_JAVA" \
    || fail "Old center-chroma reinforcement was not removed"

grep -Fq 'deepestShadowNeutralityGuard=0.18' "$CHROMA_JAVA" \
    || fail "Deep-shadow chroma guard missing"

grep -Fq 'add(new MotionLumaDenoise());' "$POST" \
    || fail "Motion luma node not inserted"

grep -Fq 'add(new MotionChromaDenoise());' "$POST" \
    || fail "Motion chroma node missing"

python3 - <<'PY'
from pathlib import Path

post = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/opengl/postpipeline/PostPipeline.java"
).read_text()

initial = post.find("add(new Initial());")
luma = post.find("add(new MotionLumaDenoise());")
chroma = post.find("add(new MotionChromaDenoise());")
auto = post.find("add(new AutoExposure());")

if not (
        initial >= 0
        and luma > initial
        and chroma > luma
        and auto > chroma
):
    raise SystemExit(
        "ERROR: expected Initial -> MotionLumaDenoise "
        "-> MotionChromaDenoise -> AutoExposure"
    )

print(
    "PASS: pipeline order is Initial -> MotionLumaDenoise "
    "-> MotionChromaDenoise -> AutoExposure"
)
PY

grep -Fq 'MOTION_26170_TONE_GAIN_GUARD' "$AUTO_EXPOSURE" \
    || fail "26170 tone-gain marker missing"

grep -Fq '                            4.0f' "$AUTO_EXPOSURE" \
    || fail "High-ISO Motion tone limit was not changed to 4.0"

grep -Fq 'MOTION_26170_CAPTURE_SHARPEN' "$CAPTURE_SHARP" \
    || fail "26170 capture-sharpening marker missing"

grep -Fq '1.0f - 0.90f * highIsoBlend' "$CAPTURE_SHARP" \
    || fail "Capture sharpening is not reduced to 10 percent at ISO 3200"

grep -Fq 'MOTION_26170_FINAL_SHARPEN' "$FINAL_SHARP" \
    || fail "26170 final-sharpening marker missing"

grep -Fq '1.0f - 0.90f * highIsoBlend' "$FINAL_SHARP" \
    || fail "Final sharpening is not reduced to 10 percent at ISO 3200"

grep -Fq 'MOTION_26168_MERGE_NOISE_AWARE' "$PYRAMID" \
    || fail "26168 temporal merge correction was lost"

grep -Fq 'predictedNoiseCap' "$MERGE_SHADER" \
    || fail "26168 temporal merge shader was lost"

grep -Fq 'MOTION_26168_RESIDUAL_NOISE_EFFECTIVE' "$POST" \
    || fail "26168 residual-noise path was lost"

grep -Fq 'MOTION_26166_IMAGE_SAVED_COMPLETE' "$HDRX" \
    || fail "26166 save-completion path was lost"

grep -q '^VERSION_BUILD=26170$' "$VERSION" \
    || fail "VERSION_BUILD was not updated"

sha256sum -c "$OUT/protected-before.sha256" \
    || fail "A protected capture, merge, metadata, color, exposure-selection, or Video file changed"

if git diff | grep -E \
    '^[+-].*(mIsRecordingVideo|CameraMode\.RAWVIDEO|TEMPLATE_RECORD|MediaRecorder|CONTROL_AF_MODE_CONTINUOUS_VIDEO|getSelectedFpsRange)'; then
    fail "Video or RAW Video behavior changed unexpectedly"
fi

git diff --check \
    || fail "git diff --check reported a formatting problem"

for file in \
    "$POST" \
    "$ESD_JAVA" \
    "$ESD_SHADER" \
    "$CHROMA_JAVA" \
    "$CHROMA_SHADER" \
    "$LUMA_JAVA" \
    "$LUMA_SHADER" \
    "$AUTO_EXPOSURE" \
    "$CAPTURE_SHARP" \
    "$FINAL_SHARP" \
    "$VERSION"; do
    cp "$file" "$OUT/source_after/$(basename "$file")"
done

git diff --stat | tee "$OUT/change-summary-tracked.txt"

{
    git diff --binary HEAD
    git diff --binary --no-index /dev/null "$CHROMA_JAVA" || true
    git diff --binary --no-index /dev/null "$CHROMA_SHADER" || true
    git diff --binary --no-index /dev/null "$LUMA_JAVA" || true
    git diff --binary --no-index /dev/null "$LUMA_SHADER" || true
} > "$OUT/combined-${NEW_BUILD}-motion-gcam-noise-balance.patch"

echo
echo "PASS: all twenty Motion RAWs remain captured and merged."
echo "PASS: validated black-level and standard color paths remain unchanged."
echo "PASS: ESD3D2 worm-forming sparse weights are stabilized at high ISO."
echo "PASS: luma cleanup acts only inside modeled noise in dark flat regions."
echo "PASS: coarse chroma radius expands from 12 to 48 pixels."
echo "PASS: coarse chroma no longer reinforces the center blotch."
echo "PASS: deepest flat shadows receive a conservative chroma-neutrality guard."
echo "PASS: high-ISO Motion tone lift is limited to 4.0x."
echo "PASS: high-ISO Motion sharpening falls to 10 percent at ISO 3200."
echo "PASS: Photo, Night, Video and RAW Video remain unchanged."
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
        | tail -360 \
        > "$OUT/relevant-errors.txt" || true

    fail "Gradle build failed; inspect $OUT/relevant-errors.txt" \
        "$BUILD_STATUS"
fi

APK="$(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | head -n 1)"

[ -n "$APK" ] && [ -f "$APK" ] \
    || fail "Debug APK was not created"

APK_COPY="$OUT/PhotonCamera-${NEW_VERSION}-motion-gcam-noise-balance-debug.apk"

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
echo "Combined patch:$OUT/combined-${NEW_BUILD}-motion-gcam-noise-balance.patch"
echo "Build log:     $OUT/build-${NEW_BUILD}.log"
echo
echo "Expected Motion markers:"
echo "  MOTION_26170_ESD3D2_STABLE_WEIGHTS"
echo "  MOTION_26170_LUMA_WORM_CLEANUP"
echo "  MOTION_26170_CHROMA_COARSE"
echo "  MOTION_26170_TONE_GAIN_GUARD"
echo "  MOTION_26170_CAPTURE_SHARPEN"
echo "  MOTION_26170_FINAL_SHARPEN"
echo "  MOTION_26168_MERGE_NOISE_AWARE"
echo "  MOTION_26168_RESIDUAL_NOISE_EFFECTIVE"
echo "  MOTION_26166_IMAGE_SAVED_COMPLETE success=true"
echo
echo "Adaptive Noise Model: leave OFF."
echo
git status --short --untracked-files=no
echo
echo "New visible source files:"
echo "  $LUMA_JAVA"
echo "  $LUMA_SHADER"
echo
echo "Safe to open another terminal now."

trap - EXIT
