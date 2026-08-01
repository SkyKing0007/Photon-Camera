#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
EXPECTED_BUILD="26170"
NEW_BUILD="26171"
NEW_VERSION="0.9726171"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="/workspaces/Photon-Camera/build_${NEW_BUILD}_motion_noise_tuning_resume_${STAMP}"
BACKUP_BRANCH="backup-before-motion-noise-tuning-${NEW_BUILD}-resume-${STAMP}"
FAILED_OUT="/workspaces/Photon-Camera/build_26171_motion_noise_tuning_20260731_051604"

POST="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
ESD_JAVA="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java"
ESD_SHADER="app/src/main/assets/shaders/denoise/esd3d2.glsl"
LUMA_JAVA="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java"
LUMA_SHADER="app/src/main/assets/shaders/denoise/motionlumadenoise.glsl"
CHROMA_JAVA="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java"
CHROMA_SHADER="app/src/main/assets/shaders/denoise/motionchromadenoise.glsl"
AUTO_EXPOSURE="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/AutoExposure.java"
CAPTURE_SHARP="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java"
FINAL_SHARP="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java"
REGISTRY="app/src/main/java/com/particlesdevs/photoncamera/settings/TunableRegistry.java"
VERSION="app/version.properties"

GENERATOR="app/src/main/java/com/particlesdevs/photoncamera/settings/TunablePreferenceGenerator.java"
INJECTOR="app/src/main/java/com/particlesdevs/photoncamera/settings/TunableInjector.java"
ANNOTATION="app/src/main/java/com/particlesdevs/photoncamera/settings/annotations/Tunable.java"
SEEK_PREF="app/src/main/java/com/particlesdevs/photoncamera/ui/settings/custompreferences/TunableSeekBarPreference.java"

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

trap 'code=$?; if [ "$code" -ne 0 ]; then echo; echo "FAILED: resumed build 26171 (exit $code)"; echo "Workspace: $OUT"; fi' EXIT

echo "============================================================"
echo " PhotonCamera ${NEW_VERSION}"
echo " Motion noise tuning UI continuation and detail recovery"
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
        echo "Expected current 26170 tracked changes:"
        printf '%s\n' "$EXPECTED_SORTED"
        echo
        echo "Actual tracked changes:"
        printf '%s\n' "$ACTUAL_MODIFIED"
        fail "Working tree is not the audited 26170 state"
    }

for file in "$LUMA_JAVA" "$LUMA_SHADER" "$CHROMA_JAVA" "$CHROMA_SHADER"; do
    [ -f "$file" ] || fail "Required 26170 source is missing: $file"
done

grep -Fq 'MOTION_26171_ESD3D2_TUNABLE' "$ESD_JAVA" \
    || fail "Expected partial 26171 ESD3D2 edit is missing"

grep -Fq 'motionResidualVarianceBoost' "$POST" \
    || fail "Expected partial 26171 PostPipeline edit is missing"

grep -Fq 'motionStableWeightBlendMaximum' "$ESD_JAVA" \
    || fail "Expected partial 26171 ESD tunable fields are missing"

[ -f "$FAILED_OUT/source_before/PostPipeline.java" ] \
    || fail "Failed-run PostPipeline backup copy is missing"

[ -f "$FAILED_OUT/source_before/ESD3D2.java" ] \
    || fail "Failed-run ESD3D2 backup copy is missing"

grep -Fq 'MOTION_26170_LUMA_WORM_CLEANUP' "$LUMA_JAVA" \
    || fail "26170 luma stage missing"

grep -Fq 'MOTION_26170_CHROMA_COARSE' "$CHROMA_JAVA" \
    || fail "26170 chroma stage missing"

grep -Fq 'MOTION_26170_TONE_GAIN_GUARD' "$AUTO_EXPOSURE" \
    || fail "26170 tone guard missing"

grep -Fq 'MOTION_26170_CAPTURE_SHARPEN' "$CAPTURE_SHARP" \
    || fail "26170 capture sharpening guard missing"

grep -Fq 'MOTION_26170_FINAL_SHARPEN' "$FINAL_SHARP" \
    || fail "26170 final sharpening guard missing"

grep -Fq 'showPreciseValueDialog' "$SEEK_PREF" \
    || fail "Existing precise numeric-entry dialog missing"

grep -Fq 'setNeutralButton("Reset"' "$SEEK_PREF" \
    || fail "Existing per-setting Reset control missing"

grep -Fq 'TunableSeekBarPreference' "$GENERATOR" \
    || fail "Existing tunable slider generator missing"

grep -Fq 'MOTION_26168_MERGE_NOISE_AWARE' "$PYRAMID" \
    || fail "Twenty-frame merge correction missing"

grep -Fq 'MOTION_26166_BLACK_LEVEL_SELECTED' "$CAPTURE" \
    || fail "Validated black-level path missing"

grep -Fq 'MOTION_26166_IMAGE_SAVED_COMPLETE' "$HDRX" \
    || fail "Save-completion path missing"

grep -Fq 'pRGB = corr*sensorToIntermediate*(pRGB*neutralPoint);' "$COLOR_SHADER" \
    || fail "Original Photon color path missing"

# The failed script wrote PostPipeline and ESD3D2, then stopped before
# writing the luma file. Confirm every later target still exactly matches
# the pre-run 26170 backup before repairing anything.
for pair in \
    "$LUMA_JAVA:MotionLumaDenoise.java" \
    "$LUMA_SHADER:motionlumadenoise.glsl" \
    "$CHROMA_JAVA:MotionChromaDenoise.java" \
    "$CHROMA_SHADER:motionchromadenoise.glsl" \
    "$AUTO_EXPOSURE:AutoExposure.java" \
    "$CAPTURE_SHARP:CaptureSharpening.java" \
    "$FINAL_SHARP:Sharpen2.java" \
    "$REGISTRY:TunableRegistry.java" \
    "$VERSION:version.properties"; do
    current="${pair%%:*}"
    saved="${pair##*:}"
    [ -f "$FAILED_OUT/source_before/$saved" ] \
        || fail "Failed-run source backup missing: $saved"
    cmp -s "$current" "$FAILED_OUT/source_before/$saved" \
        || fail "Unexpected partial modification outside PostPipeline/ESD3D2: $current"
done

mkdir -p "$OUT/source_before" "$OUT/source_after"

echo
echo "=== CREATE BACKUP BRANCH AND COMPLETE PATCH ==="

git branch "$BACKUP_BRANCH" HEAD

{
    git diff --binary HEAD
    git diff --binary --no-index /dev/null "$LUMA_JAVA" || true
    git diff --binary --no-index /dev/null "$LUMA_SHADER" || true
    git diff --binary --no-index /dev/null "$CHROMA_JAVA" || true
    git diff --binary --no-index /dev/null "$CHROMA_SHADER" || true
} > "$OUT/working-tree-before-${NEW_BUILD}.patch"

for file in \
    "$POST" "$ESD_JAVA" "$ESD_SHADER" \
    "$LUMA_JAVA" "$LUMA_SHADER" \
    "$CHROMA_JAVA" "$CHROMA_SHADER" \
    "$AUTO_EXPOSURE" "$CAPTURE_SHARP" "$FINAL_SHARP" \
    "$REGISTRY" "$VERSION"; do
    cp "$file" "$OUT/source_before/$(basename "$file")"
done

sha256sum \
    "$CAPTURE" "$PARAMS" "$HDRX" "$INITIAL" "$COLOR_SHADER" \
    "$PYRAMID" "$MERGE_SHADER" "$EXPOSURE_SELECTOR" \
    "$GENERATOR" "$INJECTOR" "$ANNOTATION" "$SEEK_PREF" \
    > "$OUT/protected-before.sha256"

echo "Backup branch: $BACKUP_BRANCH"
echo "Backup patch:  $OUT/working-tree-before-${NEW_BUILD}.patch"

echo
echo "=== RESTORE CLEAN 26170 SOURCES FROM FAILED-RUN BACKUP ==="

cp "$FAILED_OUT/source_before/PostPipeline.java" "$POST"
cp "$FAILED_OUT/source_before/ESD3D2.java" "$ESD_JAVA"

grep -Fq 'MOTION_26170_ESD3D2_STABLE_WEIGHTS' "$ESD_JAVA" \
    || fail "ESD3D2 did not restore to 26170"

grep -Fq '1.0f + 0.80f * highIsoBlend' "$POST" \
    || fail "PostPipeline did not restore to 26170"

! grep -Fq 'MOTION_26171_ESD3D2_TUNABLE' "$ESD_JAVA" \
    || fail "Partial ESD3D2 edit remains after restore"

! grep -Fq 'motionResidualVarianceBoost' "$POST" \
    || fail "Partial PostPipeline edit remains after restore"

echo "PASS: exact 26170 PostPipeline and ESD3D2 restored."

echo
echo "=== APPLY CORRECTED 26171 MOTION TUNABLES ==="

python3 - <<'PY'
from pathlib import Path

post_path = Path("app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java")
esd_path = Path("app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java")
luma_path = Path("app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java")
chroma_path = Path("app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java")
auto_path = Path("app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/AutoExposure.java")
capture_sharp_path = Path("app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java")
final_sharp_path = Path("app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java")
registry_path = Path("app/src/main/java/com/particlesdevs/photoncamera/settings/TunableRegistry.java")
version_path = Path("app/version.properties")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"ERROR: {label}: expected exactly one match, found {count}"
        )
    return text.replace(old, new, 1)


# ------------------------------------------------------------------
# PostPipeline residual-noise confidence.
# ------------------------------------------------------------------
post = post_path.read_text()

anchor = """    int demosaicingMethod = 1;

    public Bitmap Run(ByteBuffer inBuffer, Parameters parameters) {
"""

addition = """    int demosaicingMethod = 1;

    @Tunable(
            title = "Motion residual variance boost",
            description = "Maximum extra downstream noise variance at ISO 3200. 0 disables the extra boost; 0.80 gives a 1.80x model.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 2.0f,
            defaultValue = 0.80f,
            step = 0.05f
    )
    float motionResidualVarianceBoost = 0.80f;

    public Bitmap Run(ByteBuffer inBuffer, Parameters parameters) {
"""

post = replace_once(
    post,
    anchor,
    addition,
    "PostPipeline Motion residual tunable",
)

post = replace_once(
    post,
    """            motionResidualNoiseMpy =
                    1.0f + 0.80f * highIsoBlend;
""",
    """            motionResidualNoiseMpy =
                    1.0f
                            + motionResidualVarianceBoost
                            * highIsoBlend;
""",
    "PostPipeline residual boost usage",
)

post = replace_once(
    post,
    """                            + " varianceMultiplier="
                            + motionResidualNoiseMpy
                            + " appliedAfterNoiseFloor=true"
""",
    """                            + " varianceMultiplier="
                            + motionResidualNoiseMpy
                            + " configuredMaximumBoost="
                            + motionResidualVarianceBoost
                            + " appliedAfterNoiseFloor=true"
""",
    "PostPipeline residual log",
)

post_path.write_text(post)


# ------------------------------------------------------------------
# ESD3D2 conservative high-ISO controls.
# ------------------------------------------------------------------
esd = esd_path.read_text()

anchor = """    float shadowBoost = 0.5f;

    boolean needClose = false;
"""

addition = """    float shadowBoost = 0.5f;

    @Tunable(
            title = "Motion ESD luma-edge blend",
            description = "Maximum high-ISO use of luma instead of RGB for ESD edge detection. Lower preserves colored fine detail.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 0.30f,
            defaultValue = 0.05f,
            step = 0.01f
    )
    float motionLumaEdgeBlendMaximum = 0.05f;

    @Tunable(
            title = "Motion ESD stable-weight blend",
            description = "Maximum high-ISO blend toward dense bilateral weights. High values can make foliage and grass mushy.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 0.65f,
            defaultValue = 0.10f,
            step = 0.01f
    )
    float motionStableWeightBlendMaximum = 0.10f;

    @Tunable(
            title = "Motion ESD shadow boost maximum",
            description = "Maximum ESD shadow-noise tolerance reached at ISO 3200.",
            category = "Motion Noise Tuning",
            min = 0.50f,
            max = 1.20f,
            defaultValue = 0.55f,
            step = 0.01f
    )
    float motionShadowBoostMaximum = 0.55f;

    boolean needClose = false;
"""

esd = replace_once(
    esd,
    anchor,
    addition,
    "ESD3D2 Motion tunables",
)

esd = replace_once(
    esd,
    """                motionNoiseBlend =
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
""",
    """                motionNoiseBlend =
                        motionLumaEdgeBlendMaximum
                                * highIsoBlend;

                motionStableWeights =
                        motionStableWeightBlendMaximum
                                * highIsoBlend;

                appliedShadowBoost =
                        Math.max(
                                shadowBoost,
                                Math2.mix(
                                        shadowBoost,
                                        motionShadowBoostMaximum,
                                        highIsoBlend
                                )
                        );

                Log.d(
                        Name,
                        "MOTION_26171_ESD3D2_TUNABLE"
""",
    "ESD3D2 tunable calculations",
)

esd = replace_once(
    esd,
    """                                + " motionNoiseBlendMaximum=0.10"
                                + " stableWeightBlend="
                                + motionStableWeights
                                + " stableWeightBlendMaximum=0.65"
                                + " chromaMinimumIndependent=true"
""",
    """                                + " motionNoiseBlendMaximum="
                                + motionLumaEdgeBlendMaximum
                                + " stableWeightBlend="
                                + motionStableWeights
                                + " stableWeightBlendMaximum="
                                + motionStableWeightBlendMaximum
                                + " motionShadowBoostMaximum="
                                + motionShadowBoostMaximum
                                + " chromaMinimumIndependent=true"
""",
    "ESD3D2 tunable log",
)

esd_path.write_text(esd)


# ------------------------------------------------------------------
# Motion luma cleanup: conservative defaults and UI controls.
# ------------------------------------------------------------------
luma = luma_path.read_text()

luma = replace_once(
    luma,
    """import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;
""",
    """import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.settings.annotations.Tunable;
import com.particlesdevs.photoncamera.util.Log;
""",
    "MotionLumaDenoise Tunable import",
)

anchor = """public class MotionLumaDenoise extends Node {
    public MotionLumaDenoise() {
"""

addition = """public class MotionLumaDenoise extends Node {
    @Tunable(
            title = "Motion luma cleanup enable",
            description = "Enable the additional dark flat-area luma residual cleanup.",
            category = "Motion Noise Tuning",
            min = 0,
            max = 1,
            defaultValue = 1,
            step = 1
    )
    boolean motionLumaCleanupEnable = true;

    @Tunable(
            title = "Motion luma cleanup strength",
            description = "Maximum cleanup strength at ISO 3200. Keep low to avoid losing foliage and fine texture.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 0.60f,
            defaultValue = 0.08f,
            step = 0.01f
    )
    float motionLumaCleanupMaximum = 0.08f;

    @Tunable(
            title = "Motion luma noise threshold",
            description = "Multiplier applied to the modeled noise threshold. Higher values classify more texture as noise.",
            category = "Motion Noise Tuning",
            min = 0.50f,
            max = 2.00f,
            defaultValue = 1.00f,
            step = 0.05f
    )
    float motionLumaNoiseGain = 1.00f;

    @Tunable(
            title = "Motion luma kernel radius",
            description = "Radius of each separable luma pass in pixels.",
            category = "Motion Noise Tuning",
            min = 1,
            max = 3,
            defaultValue = 2,
            step = 1
    )
    int motionLumaKernelRadius = 2;

    public MotionLumaDenoise() {
"""

luma = replace_once(
    luma,
    anchor,
    addition,
    "MotionLumaDenoise tunables",
)

luma = replace_once(
    luma,
    """        glProg.setDefine("KSIZE", 3);
""",
    """        glProg.setDefine(
                "KSIZE",
                motionLumaKernelRadius
        );
""",
    "Motion luma kernel usage",
)

luma = replace_once(
    luma,
    """        if (PhotonCamera.getSettings().selectedMode
                != CameraMode.MOTION) {
""",
    """        if (PhotonCamera.getSettings().selectedMode
                != CameraMode.MOTION
                || !motionLumaCleanupEnable) {
""",
    "Motion luma enable check",
)

luma = replace_once(
    luma,
    """        float strength =
                0.55f * highIsoBlend;
""",
    """        float strength =
                motionLumaCleanupMaximum
                        * highIsoBlend;
""",
    "Motion luma strength usage",
)

luma = replace_once(
    luma,
    """        float noiseGain =
                1.35f;
""",
    """        float noiseGain =
                motionLumaNoiseGain;
""",
    "Motion luma noise threshold usage",
)

luma_marker = '"MOTION_26170_LUMA_WORM_CLEANUP"'
if luma.count(luma_marker) != 2:
    raise SystemExit(
        "ERROR: Motion luma marker: expected exactly two "
        f"enabled/disabled log markers, found {luma.count(luma_marker)}"
    )
luma = luma.replace(
    luma_marker,
    '"MOTION_26171_LUMA_TUNABLE"',
)

luma = luma.replace(
    '+ " kernelRadiusPixels=3"',
    '+ " kernelRadiusPixels=" + motionLumaKernelRadius',
)

luma_path.write_text(luma)


# ------------------------------------------------------------------
# Motion chroma cleanup: restore color and expose controls.
# ------------------------------------------------------------------
chroma = chroma_path.read_text()

chroma = replace_once(
    chroma,
    """import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;
""",
    """import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.settings.annotations.Tunable;
import com.particlesdevs.photoncamera.util.Log;
""",
    "MotionChromaDenoise Tunable import",
)

anchor = """public class MotionChromaDenoise extends Node {
    public MotionChromaDenoise() {
"""

addition = """public class MotionChromaDenoise extends Node {
    @Tunable(
            title = "Motion chroma cleanup enable",
            description = "Enable broad dark-area chroma-cloud cleanup.",
            category = "Motion Noise Tuning",
            min = 0,
            max = 1,
            defaultValue = 1,
            step = 1
    )
    boolean motionChromaCleanupEnable = true;

    @Tunable(
            title = "Motion chroma cleanup strength",
            description = "Maximum broad chroma cleanup at ISO 3200. 26170 used 0.90; the safer default is 0.30.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 1.0f,
            defaultValue = 0.30f,
            step = 0.01f
    )
    float motionChromaCleanupMaximum = 0.30f;

    @Tunable(
            title = "Motion chroma radius",
            description = "Requested full-resolution chroma radius in pixels. Internally rounded to the nearest four-pixel step.",
            category = "Motion Noise Tuning",
            min = 4,
            max = 48,
            defaultValue = 24,
            step = 1
    )
    int motionChromaRadiusPixels = 24;

    @Tunable(
            title = "Motion chroma guide tolerance",
            description = "Luma difference allowed across the broad chroma filter. Lower values protect object boundaries and color separation.",
            category = "Motion Noise Tuning",
            min = 0.02f,
            max = 0.15f,
            defaultValue = 0.08f,
            step = 0.01f
    )
    float motionChromaGuideSigmaMaximum = 0.08f;

    @Tunable(
            title = "Motion shadow color neutralization",
            description = "Additional deepest-shadow desaturation. Default is zero because 26170 removed legitimate color.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 0.20f,
            defaultValue = 0.0f,
            step = 0.01f
    )
    float motionShadowNeutralization = 0.0f;

    public MotionChromaDenoise() {
"""

chroma = replace_once(
    chroma,
    anchor,
    addition,
    "MotionChromaDenoise tunables",
)

chroma = replace_once(
    chroma,
    """    private void configurePass(
            int direction,
            float strength,
            float guideSigma
    ) {
        glProg.setDefine("DIRECTION", direction);
        glProg.setDefine("KSIZE", 6);
        glProg.setDefine("SAMPLESTEP", 8);
        glProg.setDefine("CHROMASTRENGTH", strength);
        glProg.setDefine("GUIDESIGMA", guideSigma);
""",
    """    private void configurePass(
            int direction,
            int sampleStep,
            float strength,
            float guideSigma
    ) {
        glProg.setDefine("DIRECTION", direction);
        glProg.setDefine("KSIZE", 4);
        glProg.setDefine("SAMPLESTEP", sampleStep);
        glProg.setDefine("CHROMASTRENGTH", strength);
        glProg.setDefine("GUIDESIGMA", guideSigma);
        glProg.setDefine(
                "SHADOWNEUTRALIZATION",
                motionShadowNeutralization
        );
""",
    "Motion chroma pass configuration",
)

chroma = replace_once(
    chroma,
    """        if (PhotonCamera.getSettings().selectedMode
                != CameraMode.MOTION) {
""",
    """        if (PhotonCamera.getSettings().selectedMode
                != CameraMode.MOTION
                || !motionChromaCleanupEnable) {
""",
    "Motion chroma enable check",
)

chroma = replace_once(
    chroma,
    """        float strength =
                0.90f * highIsoBlend;
""",
    """        float strength =
                motionChromaCleanupMaximum
                        * highIsoBlend;
""",
    "Motion chroma strength usage",
)

chroma = replace_once(
    chroma,
    """        float guideSigma =
                0.060f
                        + 0.060f * highIsoBlend;

        configurePass(
                0,
                strength,
                guideSigma
        );
""",
    """        float guideSigma =
                Math2.mix(
                        0.040f,
                        motionChromaGuideSigmaMaximum,
                        highIsoBlend
                );

        int sampleStep =
                Math.max(
                        1,
                        Math.round(
                                motionChromaRadiusPixels
                                        / 4.0f
                        )
                );

        int actualRadiusPixels =
                sampleStep * 4;

        configurePass(
                0,
                sampleStep,
                strength,
                guideSigma
        );
""",
    "Motion chroma conservative profile",
)

chroma = replace_once(
    chroma,
    """        configurePass(
                1,
                strength,
                guideSigma
        );
""",
    """        configurePass(
                1,
                sampleStep,
                strength,
                guideSigma
        );
""",
    "Motion chroma second pass",
)

chroma_marker = '"MOTION_26170_CHROMA_COARSE"'
if chroma.count(chroma_marker) != 2:
    raise SystemExit(
        "ERROR: Motion chroma marker: expected exactly two "
        f"enabled/disabled log markers, found {chroma.count(chroma_marker)}"
    )
chroma = chroma.replace(
    chroma_marker,
    '"MOTION_26171_CHROMA_TUNABLE"',
)

chroma = replace_once(
    chroma,
    """                        + " kernelRadiusSamples=6"
                        + " sampleStepPixels=8"
                        + " fullRadiusPixels=48"
                        + " fullDiameterPixels=96"
""",
    """                        + " kernelRadiusSamples=4"
                        + " sampleStepPixels=" + sampleStep
                        + " requestedRadiusPixels="
                        + motionChromaRadiusPixels
                        + " actualRadiusPixels="
                        + actualRadiusPixels
                        + " actualDiameterPixels="
                        + actualRadiusPixels * 2
""",
    "Motion chroma radius log",
)

chroma = replace_once(
    chroma,
    """                        + " deepestShadowNeutralityGuard=0.18"
""",
    """                        + " deepestShadowNeutralityGuard="
                        + motionShadowNeutralization
""",
    "Motion chroma neutralization log",
)

chroma_path.write_text(chroma)


# ------------------------------------------------------------------
# AutoExposure Motion tone limit.
# ------------------------------------------------------------------
auto = auto_path.read_text()

anchor = """    @Tunable(title = "Apply gamma mix", category = "Auto Exposure", min = 0.0f, max = 1.0f, step = 0.01f, defaultValue = 0.1f, description = "Blend between AE color space sRGB-linear")
    float applyGammaMix;


    public AutoExposure() {
"""

addition = """    @Tunable(title = "Apply gamma mix", category = "Auto Exposure", min = 0.0f, max = 1.0f, step = 0.01f, defaultValue = 0.1f, description = "Blend between AE color space sRGB-linear")
    float applyGammaMix;

    @Tunable(
            title = "Motion high-ISO tone gain limit",
            description = "Maximum post-exposure gain at ISO 3200. The 4.0 default matched the GCam reference brightness better.",
            category = "Motion Noise Tuning",
            min = 3.0f,
            max = 9.0f,
            defaultValue = 4.0f,
            step = 0.1f
    )
    float motionHighIsoGainLimit = 4.0f;


    public AutoExposure() {
"""

auto = replace_once(
    auto,
    anchor,
    addition,
    "AutoExposure Motion tone tunable",
)

auto = replace_once(
    auto,
    """            float highIsoGainLimit =
                    Math.min(
                            gainMax,
                            4.0f
                    );
""",
    """            float highIsoGainLimit =
                    Math.min(
                            gainMax,
                            motionHighIsoGainLimit
                    );
""",
    "AutoExposure tone tunable usage",
)

auto = replace_once(
    auto,
    '"MOTION_26170_TONE_GAIN_GUARD"',
    '"MOTION_26171_TONE_TUNABLE"',
    "AutoExposure marker",
)

auto = replace_once(
    auto,
    """                            + " gainLimit="
                            + motionGainLimit
""",
    """                            + " configuredHighIsoLimit="
                            + motionHighIsoGainLimit
                            + " gainLimit="
                            + motionGainLimit
""",
    "AutoExposure tunable log",
)

auto_path.write_text(auto)


# ------------------------------------------------------------------
# Sharpening floors.
# ------------------------------------------------------------------
capture_sharp = capture_sharp_path.read_text()

capture_sharp = replace_once(
    capture_sharp,
    """import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;
""",
    """import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;
import com.particlesdevs.photoncamera.settings.annotations.Tunable;
""",
    "CaptureSharpening Tunable import",
)

anchor = """public class CaptureSharpening extends Node {
    public CaptureSharpening() {
"""

addition = """public class CaptureSharpening extends Node {
    @Tunable(
            title = "Motion capture sharpening floor",
            description = "Fraction of normal capture sharpening retained at ISO 3200. 26170 used 0.10; the detail-recovery default is 0.40.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 1.0f,
            defaultValue = 0.40f,
            step = 0.05f
    )
    float motionCaptureSharpeningFloor = 0.40f;

    public CaptureSharpening() {
"""

capture_sharp = replace_once(
    capture_sharp,
    anchor,
    addition,
    "CaptureSharpening Motion tunable",
)

capture_sharp = replace_once(
    capture_sharp,
    """            motionSharpScale =
                    1.0f - 0.90f * highIsoBlend;
""",
    """            motionSharpScale =
                    1.0f
                            - (
                                    1.0f
                                            - motionCaptureSharpeningFloor
                              )
                            * highIsoBlend;
""",
    "CaptureSharpening floor usage",
)

capture_sharp = replace_once(
    capture_sharp,
    '"MOTION_26170_CAPTURE_SHARPEN"',
    '"MOTION_26171_CAPTURE_SHARPEN_TUNABLE"',
    "CaptureSharpening marker",
)

capture_sharp = replace_once(
    capture_sharp,
    """                            + " scale=" + motionSharpScale
                            + " appliedStrength=" + strength
""",
    """                            + " scale=" + motionSharpScale
                            + " configuredFloor="
                            + motionCaptureSharpeningFloor
                            + " appliedStrength=" + strength
""",
    "CaptureSharpening tunable log",
)

capture_sharp_path.write_text(capture_sharp)


final_sharp = final_sharp_path.read_text()

anchor = """    float denoiseActivity;

    @Override
"""

addition = """    float denoiseActivity;

    @Tunable(
            title = "Motion final sharpening floor",
            description = "Fraction of the selected final sharpening retained at ISO 3200.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 1.0f,
            defaultValue = 0.40f,
            step = 0.05f
    )
    float motionFinalSharpeningFloor = 0.40f;

    @Override
"""

final_sharp = replace_once(
    final_sharp,
    anchor,
    addition,
    "Sharpen2 Motion tunable",
)

final_sharp = replace_once(
    final_sharp,
    """            motionSharpScale =
                    1.0f - 0.90f * highIsoBlend;
""",
    """            motionSharpScale =
                    1.0f
                            - (
                                    1.0f
                                            - motionFinalSharpeningFloor
                              )
                            * highIsoBlend;
""",
    "Sharpen2 floor usage",
)

final_sharp = replace_once(
    final_sharp,
    '"MOTION_26170_FINAL_SHARPEN"',
    '"MOTION_26171_FINAL_SHARPEN_TUNABLE"',
    "Sharpen2 marker",
)

final_sharp = replace_once(
    final_sharp,
    """                            + " scale=" + motionSharpScale
                            + " appliedStrength=" + sharpness
""",
    """                            + " scale=" + motionSharpScale
                            + " configuredFloor="
                            + motionFinalSharpeningFloor
                            + " appliedStrength=" + sharpness
""",
    "Sharpen2 tunable log",
)

final_sharp_path.write_text(final_sharp)


# ------------------------------------------------------------------
# Register the new tunable classes with the existing generated UI.
# ------------------------------------------------------------------
registry = registry_path.read_text()

anchor = """        com.particlesdevs.photoncamera.processing.opengl.postpipeline.Sharpen2.class,
        com.particlesdevs.photoncamera.processing.opengl.postpipeline.PostPipeline.class,
"""

addition = """        com.particlesdevs.photoncamera.processing.opengl.postpipeline.Sharpen2.class,
        com.particlesdevs.photoncamera.processing.opengl.postpipeline.CaptureSharpening.class,
        com.particlesdevs.photoncamera.processing.opengl.postpipeline.MotionLumaDenoise.class,
        com.particlesdevs.photoncamera.processing.opengl.postpipeline.MotionChromaDenoise.class,
        com.particlesdevs.photoncamera.processing.opengl.postpipeline.PostPipeline.class,
"""

registry = replace_once(
    registry,
    anchor,
    addition,
    "TunableRegistry Motion classes",
)

registry_path.write_text(registry)


version = version_path.read_text()

if version.count("VERSION_BUILD=26170") != 1:
    raise SystemExit(
        "ERROR: expected exactly one VERSION_BUILD=26170"
    )

version_path.write_text(
    version.replace(
        "VERSION_BUILD=26170",
        "VERSION_BUILD=26171",
        1,
    )
)
PY

echo
echo "=== UPDATE CHROMA SHADER TUNABLE ==="

python3 - <<'PY'
from pathlib import Path

path = Path(
    "app/src/main/assets/shaders/denoise/"
    "motionchromadenoise.glsl"
)
text = path.read_text()


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"ERROR: {label}: expected exactly one match, found {count}"
        )
    return text.replace(old, new, 1)


text = replace_once(
    text,
    """#define DIRECTION 0
#define KSIZE 6
#define SAMPLESTEP 8
#define CHROMASTRENGTH 0.0
#define GUIDESIGMA 0.10
#define NOISES 0.0
#define NOISEO 0.0
""",
    """#define DIRECTION 0
#define KSIZE 4
#define SAMPLESTEP 6
#define CHROMASTRENGTH 0.0
#define GUIDESIGMA 0.08
#define SHADOWNEUTRALIZATION 0.0
#define NOISES 0.0
#define NOISEO 0.0
""",
    "Motion chroma shader defaults",
)

text = replace_once(
    text,
    """    float neutralityStrength =
            0.18
                    * CHROMASTRENGTH
""",
    """    float neutralityStrength =
            SHADOWNEUTRALIZATION
                    * CHROMASTRENGTH
""",
    "Motion shadow neutralization tunable",
)

text = replace_once(
    text,
    """                            0.0,
                            0.18
""",
    """                            0.0,
                            SHADOWNEUTRALIZATION
""",
    "Motion shadow neutralization clamp",
)

path.write_text(text)
PY

echo
echo "=== VERIFY 26171 IMPLEMENTATION ==="

grep -Fq 'category = "Motion Noise Tuning"' "$POST" \
    || fail "Motion tuning category missing from PostPipeline"

grep -Fq 'MOTION_26171_ESD3D2_TUNABLE' "$ESD_JAVA" \
    || fail "ESD3D2 tunable marker missing"

grep -Fq 'defaultValue = 0.10f' "$ESD_JAVA" \
    || fail "Conservative stable-weight default missing"

grep -Fq 'MOTION_26171_LUMA_TUNABLE' "$LUMA_JAVA" \
    || fail "Luma tunable marker missing"

grep -Fq 'defaultValue = 0.08f' "$LUMA_JAVA" \
    || fail "Conservative luma default missing"

grep -Fq 'motionLumaKernelRadius' "$LUMA_JAVA" \
    || fail "Luma radius control missing"

grep -Fq 'MOTION_26171_CHROMA_TUNABLE' "$CHROMA_JAVA" \
    || fail "Chroma tunable marker missing"

grep -Fq 'defaultValue = 0.30f' "$CHROMA_JAVA" \
    || fail "Conservative chroma default missing"

grep -Fq 'defaultValue = 24' "$CHROMA_JAVA" \
    || fail "24-pixel chroma radius default missing"

grep -Fq 'defaultValue = 0.0f' "$CHROMA_JAVA" \
    || fail "Zero shadow-neutralization default missing"

grep -Fq 'SHADOWNEUTRALIZATION' "$CHROMA_SHADER" \
    || fail "Shader shadow-neutralization control missing"

grep -Fq 'MOTION_26171_TONE_TUNABLE' "$AUTO_EXPOSURE" \
    || fail "Tone-gain tunable marker missing"

grep -Fq 'motionHighIsoGainLimit = 4.0f' "$AUTO_EXPOSURE" \
    || fail "GCam-like 4.0 tone default missing"

grep -Fq 'MOTION_26171_CAPTURE_SHARPEN_TUNABLE' "$CAPTURE_SHARP" \
    || fail "Capture sharpening tunable marker missing"

grep -Fq 'motionCaptureSharpeningFloor = 0.40f' "$CAPTURE_SHARP" \
    || fail "Capture detail-recovery default missing"

grep -Fq 'MOTION_26171_FINAL_SHARPEN_TUNABLE' "$FINAL_SHARP" \
    || fail "Final sharpening tunable marker missing"

grep -Fq 'motionFinalSharpeningFloor = 0.40f' "$FINAL_SHARP" \
    || fail "Final detail-recovery default missing"

grep -Fq 'MotionLumaDenoise.class' "$REGISTRY" \
    || fail "Motion luma class not registered"

grep -Fq 'MotionChromaDenoise.class' "$REGISTRY" \
    || fail "Motion chroma class not registered"

grep -Fq 'CaptureSharpening.class' "$REGISTRY" \
    || fail "Capture sharpening class not registered"

grep -q '^VERSION_BUILD=26171$' "$VERSION" \
    || fail "VERSION_BUILD was not updated"

# Existing value-entry UI must remain untouched and functional.
grep -Fq 'showPreciseValueDialog' "$SEEK_PREF" \
    || fail "Precise value dialog disappeared"

grep -Fq 'setPositiveButton("Set"' "$SEEK_PREF" \
    || fail "Precise value Set control disappeared"

grep -Fq 'setNeutralButton("Reset"' "$SEEK_PREF" \
    || fail "Precise value Reset control disappeared"

grep -Fq 'setNegativeButton("Cancel"' "$SEEK_PREF" \
    || fail "Precise value Cancel control disappeared"

sha256sum -c "$OUT/protected-before.sha256" \
    || fail "Protected capture, merge, metadata, color, exposure selection, or tuning UI engine changed"

if git diff | grep -E \
    '^[+-].*(mIsRecordingVideo|CameraMode\.RAWVIDEO|TEMPLATE_RECORD|MediaRecorder|CONTROL_AF_MODE_CONTINUOUS_VIDEO|getSelectedFpsRange)'; then
    fail "Video or RAW Video behavior changed unexpectedly"
fi

git diff --check \
    || fail "git diff --check reported a formatting problem"

for file in \
    "$POST" "$ESD_JAVA" "$ESD_SHADER" \
    "$LUMA_JAVA" "$LUMA_SHADER" \
    "$CHROMA_JAVA" "$CHROMA_SHADER" \
    "$AUTO_EXPOSURE" "$CAPTURE_SHARP" "$FINAL_SHARP" \
    "$REGISTRY" "$VERSION"; do
    cp "$file" "$OUT/source_after/$(basename "$file")"
done

git diff --stat | tee "$OUT/change-summary-tracked.txt"

{
    git diff --binary HEAD
    git diff --binary --no-index /dev/null "$LUMA_JAVA" || true
    git diff --binary --no-index /dev/null "$LUMA_SHADER" || true
    git diff --binary --no-index /dev/null "$CHROMA_JAVA" || true
    git diff --binary --no-index /dev/null "$CHROMA_SHADER" || true
} > "$OUT/combined-${NEW_BUILD}-motion-noise-tuning.patch"

echo
echo "PASS: existing generated slider UI is reused."
echo "PASS: tapping the displayed value opens precise numeric entry."
echo "PASS: every numeric control shows min, max, default and Reset."
echo "PASS: 26170 luma cleanup default reduced from 0.55 to 0.08."
echo "PASS: 26170 chroma cleanup default reduced from 0.90 to 0.30."
echo "PASS: chroma radius default reduced from 48 to 24 pixels."
echo "PASS: forced shadow neutralization default reduced from 0.18 to 0.00."
echo "PASS: ESD dense-weight blend default reduced from 0.65 to 0.10."
echo "PASS: high-ISO sharpening floor restored from 0.10 to 0.40."
echo "PASS: 4.0x high-ISO tone limit retained as a slider."
echo "PASS: twenty-frame merge, black level and color paths preserved."
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
        | tail -400 \
        > "$OUT/relevant-errors.txt" || true

    fail "Gradle build failed; inspect $OUT/relevant-errors.txt" \
        "$BUILD_STATUS"
fi

APK="$(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | head -n 1)"

[ -n "$APK" ] && [ -f "$APK" ] \
    || fail "Debug APK was not created"

APK_COPY="$OUT/PhotonCamera-${NEW_VERSION}-motion-noise-tuning-debug.apk"

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
echo "Original backup: backup-before-motion-noise-tuning-26171-20260731_051604"
echo "Combined patch:$OUT/combined-${NEW_BUILD}-motion-noise-tuning.patch"
echo "Build log:     $OUT/build-${NEW_BUILD}.log"
echo
echo "Open:"
echo "  Settings -> Tunable Settings -> Tunable - Motion Noise Tuning"
echo
echo "Tap a displayed value for precise numeric entry."
echo "Use Reset in that dialog to restore the 26171 default."
echo
echo "Expected Motion markers:"
echo "  MOTION_26171_ESD3D2_TUNABLE"
echo "  MOTION_26171_LUMA_TUNABLE"
echo "  MOTION_26171_CHROMA_TUNABLE"
echo "  MOTION_26171_TONE_TUNABLE"
echo "  MOTION_26171_CAPTURE_SHARPEN_TUNABLE"
echo "  MOTION_26171_FINAL_SHARPEN_TUNABLE"
echo "  MOTION_26168_MERGE_NOISE_AWARE"
echo "  MOTION_26166_IMAGE_SAVED_COMPLETE success=true"
echo
echo "Adaptive Noise Model: leave OFF."
echo
git status --short --untracked-files=no
echo
echo "Safe to open another terminal now."

trap - EXIT
