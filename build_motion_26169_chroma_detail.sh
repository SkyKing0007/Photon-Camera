#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
EXPECTED_BUILD="26168"
NEW_BUILD="26169"
NEW_VERSION="0.9726169"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="/workspaces/Photon-Camera/build_${NEW_BUILD}_motion_chroma_detail_${STAMP}"
BACKUP_BRANCH="backup-before-motion-chroma-detail-${NEW_BUILD}-${STAMP}"

POST="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
ESD_JAVA="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java"
ESD_SHADER="app/src/main/assets/shaders/denoise/esd3d2.glsl"
NEW_JAVA="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java"
NEW_SHADER="app/src/main/assets/shaders/denoise/motionchromadenoise.glsl"
VERSION="app/version.properties"

CAPTURE="app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
PARAMS="app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java"
HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
INITIAL="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java"
COLOR_SHADER="app/src/main/assets/shaders/initial.glsl"
PYRAMID="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts/PyramidMerging.java"
MERGE_SHADER="app/src/main/assets/shaders/merge/merge11.glsl"
AUTO_EXPOSURE="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/AutoExposure.java"
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

trap 'code=$?; if [ "$code" -ne 0 ]; then echo; echo "FAILED: build 26169 (exit $code)"; echo "Workspace: $OUT"; fi' EXIT

echo "============================================================"
echo " PhotonCamera ${NEW_VERSION}"
echo " Motion chroma-blotch cleanup with luma-detail preservation"
echo "============================================================"

[ "$(git branch --show-current)" = "$EXPECTED_BRANCH" ] \
    || fail "Expected branch $EXPECTED_BRANCH"

[ "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" ] \
    || fail "Expected HEAD $EXPECTED_HEAD"

grep -q "^VERSION_BUILD=${EXPECTED_BUILD}$" "$VERSION" \
    || fail "Expected VERSION_BUILD=${EXPECTED_BUILD}"

[ ! -e "$NEW_JAVA" ] \
    || fail "Unexpected existing file: $NEW_JAVA"

[ ! -e "$NEW_SHADER" ] \
    || fail "Unexpected existing file: $NEW_SHADER"

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
        echo "Expected current 26168 tracked changes:"
        printf '%s\n' "$EXPECTED_SORTED"
        echo
        echo "Actual tracked changes:"
        printf '%s\n' "$ACTUAL_MODIFIED"
        fail "Working tree is not the verified 26168 state"
    }

grep -Fq 'MOTION_26168_MERGE_NOISE_AWARE' "$PYRAMID" \
    || fail "26168 temporal merge correction missing"

grep -Fq 'predictedNoiseCap' "$MERGE_SHADER" \
    || fail "26168 temporal merge shader correction missing"

grep -Fq 'MOTION_26168_RESIDUAL_NOISE_EFFECTIVE' "$POST" \
    || fail "26168 post-floor residual-noise path missing"

grep -Fq 'MOTION_26168_TONE_GAIN_GUARD' "$AUTO_EXPOSURE" \
    || fail "26168 tone-gain guard missing"

grep -Fq 'MOTION_26168_ESD3D2_PROFILE' "$ESD_JAVA" \
    || fail "26168 ESD3D2 profile missing"

grep -Fq 'MOTIONNOISEBLEND' "$ESD_SHADER" \
    || fail "26168 ESD3D2 shader blend missing"

grep -Fq 'MOTION_26165_HOMOGENEOUS_RAW_STACK' "$CAPTURE" \
    || fail "Homogeneous twenty-frame stack missing"

grep -Fq 'MOTION_26166_BLACK_LEVEL_SELECTED' "$CAPTURE" \
    || fail "Validated black-level path missing"

grep -Fq 'MOTION_26166_IMAGE_SAVED_COMPLETE' "$HDRX" \
    || fail "Post-save completion path missing"

grep -Fq 'pRGB = corr*sensorToIntermediate*(pRGB*neutralPoint);' "$COLOR_SHADER" \
    || fail "Original Photon color path missing"

mkdir -p "$OUT/source_before" "$OUT/source_after"

echo
echo "=== CREATE BACKUP BRANCH AND PATCH ==="

git branch "$BACKUP_BRANCH" HEAD
git diff --binary HEAD > "$OUT/working-tree-before-${NEW_BUILD}.patch"

for file in "$POST" "$ESD_JAVA" "$ESD_SHADER" "$VERSION"; do
    cp "$file" "$OUT/source_before/$(basename "$file")"
done

printf '%s\n' \
    "ABSENT BEFORE 26169: $NEW_JAVA" \
    "ABSENT BEFORE 26169: $NEW_SHADER" \
    > "$OUT/source_before/new-files-status.txt"

sha256sum \
    "$CAPTURE" \
    "$PARAMS" \
    "$HDRX" \
    "$INITIAL" \
    "$COLOR_SHADER" \
    "$PYRAMID" \
    "$MERGE_SHADER" \
    "$AUTO_EXPOSURE" \
    "$CAPTURE_SHARP" \
    "$FINAL_SHARP" \
    "$EXPOSURE_SELECTOR" \
    > "$OUT/protected-before.sha256"

echo "Backup branch: $BACKUP_BRANCH"
echo "Backup patch:  $OUT/working-tree-before-${NEW_BUILD}.patch"

echo
echo "=== APPLY 26169 TRACKED-FILE CHANGES ==="

python3 - <<'PY'
from pathlib import Path

post_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/opengl/postpipeline/PostPipeline.java"
)
esd_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/opengl/postpipeline/ESD3D2.java"
)
version_path = Path("app/version.properties")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"ERROR: {label}: expected exactly one match, found {count}"
        )
    return text.replace(old, new, 1)


esd = esd_path.read_text()

old_blend = """                motionNoiseBlend =
                        highIsoBlend;

                appliedShadowBoost =
                        Math.max(
                                shadowBoost,
                                0.50f + 0.65f * highIsoBlend
                        );

                Log.d(
                        Name,
                        "MOTION_26168_ESD3D2_PROFILE"
"""

new_blend = """                /*
                 * Build 26169:
                 * Keep ESD3D2 primarily RGB-edge aware. The dedicated
                 * MotionChromaDenoise node handles broad chroma blotches
                 * without widening the luma-detail filter globally.
                 */
                motionNoiseBlend =
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

esd = replace_once(
    esd,
    old_blend,
    new_blend,
    "ESD3D2 detail-preserving Motion profile",
)

old_log_tail = """                                + " motionNoiseBlend="
                                + motionNoiseBlend
                                + " edgeMetric="
                                + "rgbToLumaWithIso"
                                + " readNoiseSource=NOISEO"
"""

new_log_tail = """                                + " motionNoiseBlend="
                                + motionNoiseBlend
                                + " motionNoiseBlendMaximum=0.30"
                                + " edgeMetric="
                                + "mostlyRgbWithLimitedLumaAssist"
                                + " dedicatedChromaStage=true"
                                + " readNoiseSource=NOISEO"
"""

esd = replace_once(
    esd,
    old_log_tail,
    new_log_tail,
    "ESD3D2 profile log",
)

esd_path.write_text(esd)

post = post_path.read_text()

old_order = """        add(new Initial());

        add(new AutoExposure());
"""

new_order = """        add(new Initial());

        if (mSettings.selectedMode == CameraMode.MOTION
                && mSettings.hdrxNR) {
            add(new MotionChromaDenoise());
        }

        add(new AutoExposure());
"""

post = replace_once(
    post,
    old_order,
    new_order,
    "Motion chroma stage placement",
)

post_path.write_text(post)

version = version_path.read_text()

if version.count("VERSION_BUILD=26168") != 1:
    raise SystemExit(
        "ERROR: expected exactly one VERSION_BUILD=26168"
    )

version_path.write_text(
    version.replace(
        "VERSION_BUILD=26168",
        "VERSION_BUILD=26169",
        1,
    )
)
PY

echo
echo "=== CREATE 26169 VISIBLE SOURCE FILES ==="

cat > "$NEW_JAVA" <<'JAVA'
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
            float guideSigma,
            float chromaSigma
    ) {
        glProg.setDefine("DIRECTION", direction);
        glProg.setDefine("KSIZE", 4);
        glProg.setDefine("SAMPLESTEP", 3);
        glProg.setDefine("CHROMASTRENGTH", strength);
        glProg.setDefine("GUIDESIGMA", guideSigma);
        glProg.setDefine("CHROMASIGMA", chromaSigma);
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
                0.72f * highIsoBlend;

        if (strength <= 0.001f) {
            Log.d(
                    Name,
                    "MOTION_26169_CHROMA_DETAIL_STAGE"
                            + " iso=" + motionIso
                            + " enabled=false"
                            + " reason=belowIso800"
                            + " lumaPreserved=true"
            );

            WorkingTexture = previousNode.WorkingTexture;
            return;
        }

        float guideSigma =
                0.025f + 0.035f * highIsoBlend;

        float chromaSigma =
                0.055f + 0.075f * highIsoBlend;

        configurePass(
                0,
                strength,
                guideSigma,
                chromaSigma
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
                guideSigma,
                chromaSigma
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
                "MOTION_26169_CHROMA_DETAIL_STAGE"
                        + " iso=" + motionIso
                        + " enabled=true"
                        + " highIsoBlend=" + highIsoBlend
                        + " strength=" + strength
                        + " guideSigma=" + guideSigma
                        + " chromaSigma=" + chromaSigma
                        + " passes=2"
                        + " kernelRadiusSamples=4"
                        + " sampleStepPixels=3"
                        + " fullRadiusPixels=12"
                        + " representation=Y_RminusG_BminusG"
                        + " lumaPreserved=true"
                        + " darkFlatMask=true"
                        + " saturatedColorProtection=true"
                        + " placement=afterInitialBeforeAutoExposure"
        );
    }
}
JAVA

cat > "$NEW_SHADER" <<'GLSL'
precision highp float;
precision highp sampler2D;

uniform sampler2D InputBuffer;
uniform sampler2D GuideBuffer;
uniform int yOffset;

out vec4 Output;

#define DIRECTION 0
#define KSIZE 4
#define SAMPLESTEP 3
#define CHROMASTRENGTH 0.0
#define GUIDESIGMA 0.04
#define CHROMASIGMA 0.10

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

    float flatMask =
            1.0
                    - smoothstep(
                            0.018,
                            0.085,
                            localGradient
                    );

    float darkMask =
            1.0
                    - smoothstep(
                            0.48,
                            0.78,
                            centerLuma
                    );

    float centerSaturation =
            length(
                    opponentChroma(
                            guideCenter
                    )
            );

    float saturatedColorProtection =
            1.0
                    - smoothstep(
                            0.30,
                            0.58,
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
                        2.25
                );

        float lumaGuideWeight =
                gaussianWeight(
                        sampleLuma - centerLuma,
                        GUIDESIGMA
                );

        float chromaDistance =
                length(
                        sampleChroma - centerChroma
                );

        float chromaRatio =
                chromaDistance
                        / max(
                                CHROMASIGMA,
                                0.0001
                        );

        float chromaWeight =
                1.0
                        / (
                                1.0
                                        + chromaRatio
                                        * chromaRatio
                          );

        float sampleWeight =
                spatialWeight
                        * lumaGuideWeight
                        * chromaWeight;

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
                            * saturatedColorProtection,
                    0.0,
                    1.0
            );

    vec2 outputChroma =
            mix(
                    centerChroma,
                    filteredChroma,
                    blend
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
echo "=== VERIFY 26169 SOURCE ==="

grep -Fq 'MOTION_26169_ESD3D2_DETAIL_PROFILE' "$ESD_JAVA" \
    || fail "26169 ESD3D2 detail profile missing"

grep -Fq 'motionNoiseBlendMaximum=0.30' "$ESD_JAVA" \
    || fail "ESD3D2 global luma blend is not capped"

grep -Fq 'MOTION_26169_CHROMA_DETAIL_STAGE' "$NEW_JAVA" \
    || fail "Dedicated chroma-stage marker missing"

grep -Fq 'placement=afterInitialBeforeAutoExposure' "$NEW_JAVA" \
    || fail "Chroma-stage placement marker missing"

grep -Fq 'reconstructFromLumaChroma' "$NEW_SHADER" \
    || fail "Luma-preserving reconstruction missing"

grep -Fq 'opponentChroma' "$NEW_SHADER" \
    || fail "Opponent-chroma representation missing"

grep -Fq 'flatMask' "$NEW_SHADER" \
    || fail "Flat-region mask missing"

grep -Fq 'saturatedColorProtection' "$NEW_SHADER" \
    || fail "Saturated-color protection missing"

grep -Fq 'add(new MotionChromaDenoise());' "$POST" \
    || fail "New Motion chroma node was not inserted"

python3 - <<'PY'
from pathlib import Path

post = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/opengl/postpipeline/PostPipeline.java"
).read_text()

initial = post.find("add(new Initial());")
chroma = post.find("add(new MotionChromaDenoise());")
auto = post.find("add(new AutoExposure());")

if not (
        initial >= 0
        and chroma > initial
        and auto > chroma
):
    raise SystemExit(
        "ERROR: expected Initial -> MotionChromaDenoise -> AutoExposure"
    )

print(
    "PASS: pipeline order is "
    "Initial -> MotionChromaDenoise -> AutoExposure"
)
PY

grep -Fq 'MOTION_26168_MERGE_NOISE_AWARE' "$PYRAMID" \
    || fail "26168 temporal merge correction was lost"

grep -Fq 'predictedNoiseCap' "$MERGE_SHADER" \
    || fail "26168 temporal merge shader was lost"

grep -Fq 'MOTION_26168_RESIDUAL_NOISE_EFFECTIVE' "$POST" \
    || fail "26168 residual-noise path was lost"

grep -Fq 'MOTION_26168_TONE_GAIN_GUARD' "$AUTO_EXPOSURE" \
    || fail "26168 tone-gain guard was lost"

grep -Fq 'MOTION_26167_CAPTURE_SHARPEN' "$CAPTURE_SHARP" \
    || fail "26167 capture-sharpening safeguard was lost"

grep -Fq 'MOTION_26167_FINAL_SHARPEN' "$FINAL_SHARP" \
    || fail "26167 final-sharpening safeguard was lost"

grep -Fq 'MOTION_26166_IMAGE_SAVED_COMPLETE' "$HDRX" \
    || fail "26166 save-completion path was lost"

grep -q '^VERSION_BUILD=26169$' "$VERSION" \
    || fail "VERSION_BUILD was not updated"

sha256sum -c "$OUT/protected-before.sha256" \
    || fail "A protected capture, merge, tone, color, sharpening, or Video file changed"

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
    "$NEW_JAVA" \
    "$NEW_SHADER" \
    "$VERSION"; do
    cp "$file" "$OUT/source_after/$(basename "$file")"
done

git diff --stat | tee "$OUT/change-summary-tracked.txt"

{
    git diff --binary HEAD
    git diff --binary --no-index /dev/null "$NEW_JAVA" || true
    git diff --binary --no-index /dev/null "$NEW_SHADER" || true
} > "$OUT/combined-${NEW_BUILD}-motion-chroma-detail.patch"

echo
echo "PASS: 26168 temporal merge and residual-noise fixes preserved."
echo "PASS: 26168 high-ISO tone-gain guard preserved."
echo "PASS: ESD3D2 global luma-guided softness reduced."
echo "PASS: new stage filters only opponent chroma in dark flat regions."
echo "PASS: original full-resolution luma is reconstructed unchanged."
echo "PASS: saturated colors and luma edges receive protection."
echo "PASS: Photo, Night, Video and RAW Video unchanged."
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
        | tail -320 \
        > "$OUT/relevant-errors.txt" || true

    fail "Gradle build failed; inspect $OUT/relevant-errors.txt" \
        "$BUILD_STATUS"
fi

APK="$(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | head -n 1)"

[ -n "$APK" ] && [ -f "$APK" ] \
    || fail "Debug APK was not created"

APK_COPY="$OUT/PhotonCamera-${NEW_VERSION}-motion-chroma-detail-debug.apk"

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
echo "Combined patch:$OUT/combined-${NEW_BUILD}-motion-chroma-detail.patch"
echo "Build log:     $OUT/build-${NEW_BUILD}.log"
echo
echo "Expected Motion markers:"
echo "  MOTION_26169_ESD3D2_DETAIL_PROFILE"
echo "  MOTION_26169_CHROMA_DETAIL_STAGE"
echo "  MOTION_26168_MERGE_NOISE_AWARE"
echo "  MOTION_26168_RESIDUAL_NOISE_EFFECTIVE"
echo "  MOTION_26168_TONE_GAIN_GUARD"
echo "  MOTION_26166_IMAGE_SAVED_COMPLETE success=true"
echo
echo "Adaptive Noise Model: leave OFF."
echo
git status --short --untracked-files=no
echo
echo "New visible source files:"
echo "  $NEW_JAVA"
echo "  $NEW_SHADER"
echo
echo "Safe to open another terminal now."

trap - EXIT
