#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
EXPECTED_BUILD="26172"
VERSION_NAME="0.9726172"

FAILED_OUT="/workspaces/Photon-Camera/build_26172_motion_local_contribution_20260731_123720"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="/workspaces/Photon-Camera/build_26172_motion_local_contribution_resume_${STAMP}"
BACKUP_BRANCH="backup-before-motion-local-contribution-26172-resume-${STAMP}"

PYRAMID="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts/PyramidMerging.java"
HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
PARAMS="app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java"
NOISE="app/src/main/java/com/particlesdevs/photoncamera/processing/render/NoiseModeler.java"
POST="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
MERGE_SHADER="app/src/main/assets/shaders/merge/merge11.glsl"
MOTION_MERGE_SHADER="app/src/main/assets/shaders/merge/motionmerge11.glsl"
CONTRIBUTION_INIT_SHADER="app/src/main/assets/shaders/merge/contributioninit.glsl"
VERSION="app/version.properties"

CAPTURE="app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
AUTO_EXPOSURE="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/AutoExposure.java"
CAPTURE_SHARP="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java"
ESD_JAVA="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java"
ESD_SHADER="app/src/main/assets/shaders/denoise/esd3d2.glsl"
INITIAL="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java"
FINAL_SHARP="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java"
REGISTRY="app/src/main/java/com/particlesdevs/photoncamera/settings/TunableRegistry.java"
LUMA_JAVA="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java"
LUMA_SHADER="app/src/main/assets/shaders/denoise/motionlumadenoise.glsl"
CHROMA_JAVA="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java"
CHROMA_SHADER="app/src/main/assets/shaders/denoise/motionchromadenoise.glsl"

fail() {
    echo
    echo "============================================================"
    echo " RESUMED BUILD FAILED"
    echo " Reason: $1"
    echo " Workspace: $OUT"
    echo "============================================================"
    exit "${2:-1}"
}

trap 'code=$?; if [ "$code" -ne 0 ]; then echo; echo "FAILED: resumed build 26172 (exit $code)"; echo "Workspace: $OUT"; fi' EXIT

check_hash() {
    local expected="$1"
    local file="$2"
    local actual

    [ -f "$file" ] || fail "Missing required file: $file"

    actual="$(sha256sum "$file" | awk '{print $1}')"

    if [ "$actual" != "$expected" ]; then
        echo "File:     $file"
        echo "Expected: $expected"
        echo "Actual:   $actual"
        fail "26172 generated source does not match the failed run"
    fi

    echo "PASS generated hash: $file"
}

echo "============================================================"
echo " PhotonCamera $VERSION_NAME"
echo " Resume verified 26172 build"
echo "============================================================"

[ "$(git branch --show-current)" = "$EXPECTED_BRANCH" ] \
    || fail "Expected branch $EXPECTED_BRANCH"

[ "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" ] \
    || fail "Expected HEAD $EXPECTED_HEAD"

grep -q "^VERSION_BUILD=${EXPECTED_BUILD}$" "$VERSION" \
    || fail "Expected VERSION_BUILD=${EXPECTED_BUILD}; do not rerun the original script"

[ -f "$FAILED_OUT/protected-before.sha256" ] \
    || fail "Original 26172 protection manifest is missing"

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
$NOISE
$REGISTRY
$VERSION"

ACTUAL_MODIFIED="$(git status --short --untracked-files=no | awk '{print $2}' | sort)"
EXPECTED_SORTED="$(printf '%s\n' "$EXPECTED_MODIFIED" | sort)"

if [ "$ACTUAL_MODIFIED" != "$EXPECTED_SORTED" ]; then
    echo "Expected tracked state:"
    printf '%s\n' "$EXPECTED_SORTED"
    echo
    echo "Actual tracked state:"
    printf '%s\n' "$ACTUAL_MODIFIED"
    fail "Workspace changed after the failed 26172 run"
fi

echo
echo "=== VERIFY EXACT GENERATED 26172 SOURCES ==="

check_hash \
    "c9d04e25111921936faddbfa65a6c48ed6b4b295c6941eaad7d25441597ce75e" \
    "$PYRAMID"

check_hash \
    "201a7e3938d36c4a42101374c46051b1d0ad7794e65009a653d9219ba3a1ef39" \
    "$HDRX"

check_hash \
    "1c3f43bcf4733c3fac6fd0dcd88f8e645c9fd122589cdd170cd85ccf8ae1ff1c" \
    "$PARAMS"

check_hash \
    "7a6c9beba00891bdc19f581e194b3cd1271cfa89b4c73ba3c0d8869d0100519e" \
    "$NOISE"

check_hash \
    "99ef221fef9dbf1e1781a2fb0701e4fa8a78dba03c103f39e84bbf5ab5e0f8cc" \
    "$POST"

check_hash \
    "c1bb9bd42df33624a139ac664c71fef9e640fff6064bbb37d2d24f8eb0fc69d8" \
    "$MOTION_MERGE_SHADER"

check_hash \
    "4cf84898efa241ffb1fe60daea554ce23b0f91f1f0ae5a00b785525098cb6123" \
    "$CONTRIBUTION_INIT_SHADER"

echo
echo "=== VERIFY PRESERVED 26171 FILES ==="

sha256sum -c "$FAILED_OUT/protected-before.sha256" \
    || fail "A protected 26171 file changed after the failed run"

echo
echo "=== CREATE RESUME BACKUP BRANCH AND COMPLETE PATCH ==="

mkdir -p "$OUT/source_verified"

git branch "$BACKUP_BRANCH" HEAD

{
    git diff --binary HEAD
    git diff --binary --no-index /dev/null "$LUMA_JAVA" || true
    git diff --binary --no-index /dev/null "$LUMA_SHADER" || true
    git diff --binary --no-index /dev/null "$CHROMA_JAVA" || true
    git diff --binary --no-index /dev/null "$CHROMA_SHADER" || true
    git diff --binary --no-index /dev/null "$MOTION_MERGE_SHADER" || true
    git diff --binary --no-index /dev/null "$CONTRIBUTION_INIT_SHADER" || true
} > "$OUT/working-tree-before-26172-resumed-build.patch"

for file in \
    "$PYRAMID" "$HDRX" "$PARAMS" "$NOISE" "$POST" \
    "$MOTION_MERGE_SHADER" "$CONTRIBUTION_INIT_SHADER" "$VERSION"; do
    cp "$file" "$OUT/source_verified/$(basename "$file")"
done

echo "Backup branch: $BACKUP_BRANCH"
echo "Backup patch:  $OUT/working-tree-before-26172-resumed-build.patch"

echo
echo "=== CORRECTED 26172 VERIFICATION ==="

grep -Fq 'MOTION_26172_CONTRIBUTION_TRACKING' "$PYRAMID" \
    || fail "Contribution tracking marker missing"

grep -Fq 'MOTION_26172_LOCAL_CONTRIBUTION' "$PYRAMID" \
    || fail "Contribution percentile marker missing"

grep -Fq 'merge/motionmerge11' "$PYRAMID" \
    || fail "Motion-isolated merge shader routing missing"

grep -Fq 'merge/merge11' "$PYRAMID" \
    || fail "Original Photo/Night merge routing missing"

grep -Fq 'motionNoiseDifferenceRecovery = 0.75f' "$PYRAMID" \
    || fail "Motion merge recovery default missing"

grep -Fq 'motionEffectiveStackPercentile = 0.25f' "$PYRAMID" \
    || fail "Effective-stack percentile default missing"

grep -Fq 'MOTION_26172_LOCAL_STACK_MODEL' "$HDRX" \
    || fail "Measured model handoff missing"

grep -Fq 'dngNoiseModelSelectedBeforeSave=true' "$HDRX" \
    || fail "DNG pre-save model marker missing"

python3 - <<'PY'
from pathlib import Path

hdrx = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/processor/HdrxProcessor.java"
).read_text()

model = hdrx.find("MOTION_26172_LOCAL_STACK_MODEL")
save = hdrx.find("ImageSaver.Util.saveStackedRaw")

if model < 0 or save < 0 or model > save:
    raise SystemExit(
        "ERROR: measured stack model is not selected before DNG save"
    )

params = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/render/Parameters.java"
).read_text()

required_metadata = [
    '"\\n EffectiveFrameCount="',
    '"\\n EffectiveStackRatio="',
    '"\\n ContributionMeasured="',
    '"\\n ContributionMean="',
    '"\\n ContributionP10="',
    '"\\n ContributionP25="',
    '"\\n ContributionP50="',
    '"\\n ContributionP75="',
    '"\\n ContributionP90="',
    '"\\n ContributionBelow4="',
    '"\\n ContributionBelow8="',
    '"\\n ContributionBelow12="',
    '"\\n ContributionBelow16="',
]

missing = [
    marker for marker in required_metadata
    if marker not in params
]

if missing:
    raise SystemExit(
        "ERROR: missing Parameters metadata: "
        + ", ".join(missing)
    )

print("PASS: effective-frame and contribution metadata present")
PY

grep -Fq 'localContributionMeasured = false' "$PARAMS" \
    || fail "Parameters contribution state missing"

grep -Fq 'computeStackingNoiseModel(float frameCount)' "$NOISE" \
    || fail "Fractional effective-frame noise model missing"

grep -Fq 'MOTION_26172_STACKING_NOISE_MODEL' "$NOISE" \
    || fail "Noise-model marker missing"

grep -Fq 'motionMeasuredResidualVarianceBoost = 0.0f' "$POST" \
    || fail "Measured residual double-count protection missing"

grep -Fq 'MOTION_26172_LOCAL_NOISE_HANDOFF' "$POST" \
    || fail "Post-pipeline measured-noise marker missing"

grep -Fq 'layout(r16f, binding = 4)' "$MOTION_MERGE_SHADER" \
    || fail "Motion contribution image binding missing"

grep -Fq 'preservedIndependentFraction' "$MOTION_MERGE_SHADER" \
    || fail "Independent-contribution measurement missing"

grep -Fq 'motionNoiseRecoveryStrength' "$MOTION_MERGE_SHADER" \
    || fail "Noise-consistent difference recovery missing"

grep -Fq 'layout(r16f, binding = 0)' "$CONTRIBUTION_INIT_SHADER" \
    || fail "Contribution initializer missing"

grep -q '^VERSION_BUILD=26172$' "$VERSION" \
    || fail "VERSION_BUILD changed unexpectedly"

grep -Fq '@Tunable(title = "Enable Adaptive Noise Model"' "$PYRAMID" \
    || fail "Adaptive Noise Model setting was removed"

git diff --check \
    || fail "git diff --check reported a formatting problem"

if git diff | grep -E \
    '^[+-].*(mIsRecordingVideo|CameraMode\.RAWVIDEO|TEMPLATE_RECORD|MediaRecorder|CONTROL_AF_MODE_CONTINUOUS_VIDEO|getSelectedFpsRange)'; then
    fail "Video or RAW Video behavior changed unexpectedly"
fi

{
    git diff --binary HEAD
    git diff --binary --no-index /dev/null "$LUMA_JAVA" || true
    git diff --binary --no-index /dev/null "$LUMA_SHADER" || true
    git diff --binary --no-index /dev/null "$CHROMA_JAVA" || true
    git diff --binary --no-index /dev/null "$CHROMA_SHADER" || true
    git diff --binary --no-index /dev/null "$MOTION_MERGE_SHADER" || true
    git diff --binary --no-index /dev/null "$CONTRIBUTION_INIT_SHADER" || true
} > "$OUT/combined-26172-motion-local-contribution.patch"

git diff --stat | tee "$OUT/change-summary-tracked.txt"

echo
echo "PASS: the prior failure was only an incorrect shell escape check."
echo "PASS: all generated 26172 sources exactly match the intended payloads."
echo "PASS: measured contribution updates the noise model before DNG save."
echo "PASS: the same measured model is supplied to the JPEG pipeline."
echo "PASS: Photo, Night, Video and RAW Video isolation is preserved."
echo "PASS: Adaptive Noise Model remains available and should stay OFF."

echo
echo "=== BUILDING PHOTONCAMERA $VERSION_NAME ==="
echo "Do not open another terminal until BUILD COMPLETE appears."

set +e
./gradlew clean assembleDebug 2>&1 | tee "$OUT/build-26172.log"
BUILD_STATUS=${PIPESTATUS[0]}
set -e

if [ "$BUILD_STATUS" -ne 0 ]; then
    grep -nE \
        'error:|cannot find symbol|FAILURE:|Compilation failed|What went wrong|Error compiling shader' \
        "$OUT/build-26172.log" \
        | tail -600 \
        > "$OUT/relevant-errors.txt" || true

    fail "Gradle build failed; inspect $OUT/relevant-errors.txt" \
        "$BUILD_STATUS"
fi

APK="$(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | head -n 1)"

[ -n "$APK" ] && [ -f "$APK" ] \
    || fail "Debug APK was not created"

APK_COPY="$OUT/PhotonCamera-${VERSION_NAME}-motion-local-contribution-debug.apk"

cp "$APK" "$APK_COPY"
sha256sum "$APK" "$APK_COPY" | tee "$OUT/sha256.txt"

echo
echo "============================================================"
echo " BUILD COMPLETE"
echo "============================================================"
echo "PhotonCamera:   $VERSION_NAME"
echo "VERSION_BUILD: 26172"
echo "APK:           $APK_COPY"
echo "Backup branch: $BACKUP_BRANCH"
echo "Backup patch:  $OUT/working-tree-before-26172-resumed-build.patch"
echo "Combined patch:$OUT/combined-26172-motion-local-contribution.patch"
echo "Build log:     $OUT/build-26172.log"
echo
echo "Expected Motion markers:"
echo "  MOTION_26172_CONTRIBUTION_TRACKING"
echo "  MOTION_26172_LOCAL_CONTRIBUTION"
echo "  MOTION_26172_LOCAL_STACK_MODEL"
echo "  MOTION_26172_STACKING_NOISE_MODEL"
echo "  MOTION_26172_LOCAL_NOISE_HANDOFF"
echo "  MOTION_26172_COLOR_AND_STACK_HANDOFF"
echo "  MOTION_26166_IMAGE_SAVED_COMPLETE success=true"
echo
echo "Adaptive Noise Model: leave OFF."
echo
git status --short --untracked-files=no
echo
echo "Safe to open another terminal now."

trap - EXIT
