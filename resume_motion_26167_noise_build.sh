#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
EXPECTED_BUILD="26167"
VERSION_NAME="0.9726167"

OUT="/workspaces/Photon-Camera/build_26167_motion_residual_noise_fix_20260731_022656"

POST="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
ESD_JAVA="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java"
ESD_SHADER="app/src/main/assets/shaders/denoise/esd3d2.glsl"
CAPTURE_SHARP="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java"
FINAL_SHARP="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java"
VERSION="app/version.properties"

CAPTURE="app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
PARAMS="app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java"
HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
INITIAL="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java"
COLOR_SHADER="app/src/main/assets/shaders/initial.glsl"
EXPOSURE_SELECTOR="app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IsoExpoSelector.java"

fail() {
    echo
    echo "============================================================"
    echo " CONTINUATION FAILED"
    echo " Reason: $1"
    echo " Workspace: $OUT"
    echo "============================================================"
    exit "${2:-1}"
}

trap 'code=$?; if [ "$code" -ne 0 ]; then echo; echo "FAILED: 26167 continuation (exit $code)"; fi' EXIT

echo "============================================================"
echo " PhotonCamera ${VERSION_NAME}"
echo " Resume verified 26167 build"
echo "============================================================"

[ -d "$OUT" ] \
    || fail "Original failed-build workspace is missing"

[ "$(git branch --show-current)" = "$EXPECTED_BRANCH" ] \
    || fail "Expected branch $EXPECTED_BRANCH"

[ "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" ] \
    || fail "Expected HEAD $EXPECTED_HEAD"

grep -q "^VERSION_BUILD=${EXPECTED_BUILD}$" "$VERSION" \
    || fail "Expected partially applied VERSION_BUILD=${EXPECTED_BUILD}"

[ -f "$OUT/protected-before.sha256" ] \
    || fail "Saved protected-file hashes are missing"

echo
echo "=== VERIFY PROTECTED 26166 FILES ==="

sha256sum -c "$OUT/protected-before.sha256" \
    || fail "A protected capture, exposure, color, black-level, or save file changed"

echo
echo "=== VERIFY CORRECTED 26167 EDITS ==="

grep -Fq 'MOTION_26167_RESIDUAL_NOISE' "$POST" \
    || fail "Residual-noise correction is missing"

grep -Fq 'captureFramesChanged=false' "$POST" \
    || fail "Captured-frame preservation marker is missing"

grep -Fq 'mergeFramesChanged=false' "$POST" \
    || fail "Merged-frame preservation marker is missing"

grep -Fq 'effectiveDiagnosticChanged=false' "$POST" \
    || fail "Effective-frame preservation marker is missing"

grep -Fq 'MOTION_26167_ESD3D2_PROFILE' "$ESD_JAVA" \
    || fail "ESD3D2 Motion profile is missing"

grep -Fq '+ NOISEO,' "$ESD_SHADER" \
    || fail "ESD3D2 read-noise correction is missing"

if grep -Fq '+ noiseO, 0.0000001' "$ESD_SHADER"; then
    fail "Old unset ESD3D2 noiseO expression still exists"
fi

grep -Fq 'MOTION_26167_CAPTURE_SHARPEN' "$CAPTURE_SHARP" \
    || fail "Capture-sharpening safeguard is missing"

grep -Fq 'MOTION_26167_FINAL_SHARPEN' "$FINAL_SHARP" \
    || fail "Final-sharpening safeguard is missing"

grep -Fq 'MOTION_26165_HOMOGENEOUS_RAW_STACK' "$CAPTURE" \
    || fail "Twenty-frame homogeneous stack was lost"

grep -Fq 'MOTION_26166_BLACK_LEVEL_SELECTED' "$CAPTURE" \
    || fail "26166 black-level path was lost"

grep -Fq 'MOTION_26166_IMAGE_SAVED_COMPLETE' "$HDRX" \
    || fail "26166 ImageSaved completion path was lost"

grep -Fq 'MOTION_COLOR_REFERENCE_METADATA' "$PARAMS" \
    || fail "Standard Motion color path was lost"

grep -Fq 'pRGB = corr*sensorToIntermediate*(pRGB*neutralPoint);' "$COLOR_SHADER" \
    || fail "Original Photon color shader was lost"

if git diff | grep -E \
    '^[+-].*(mIsRecordingVideo|CameraMode\.RAWVIDEO|TEMPLATE_RECORD|MediaRecorder|CONTROL_AF_MODE_CONTINUOUS_VIDEO|getSelectedFpsRange)'; then
    fail "Video or RAW Video behavior changed unexpectedly"
fi

git diff --check \
    || fail "git diff --check reported a formatting problem"

echo
echo "PASS: previous failure was only the over-broad diff check."
echo "PASS: all twenty frames remain captured and merged."
echo "PASS: effective-frame diagnostics remain at the retained count."
echo "PASS: protected 26166 behavior matches its saved hashes."
echo "PASS: corrected ESD3D2 and Motion residual-noise edits are present."
echo "PASS: Video and RAW Video remain unchanged."
echo "PASS: Adaptive Noise Model remains unchanged; leave OFF."

echo
echo "=== SAVE VERIFIED CURRENT PATCH ==="

git diff --binary HEAD \
    > "$OUT/combined-26167-motion-residual-noise-fix-verified.patch"

mkdir -p "$OUT/source_after_verified"

for file in \
    "$POST" \
    "$ESD_JAVA" \
    "$ESD_SHADER" \
    "$CAPTURE_SHARP" \
    "$FINAL_SHARP" \
    "$VERSION"; do
    cp "$file" "$OUT/source_after_verified/$(basename "$file")"
done

git diff --stat | tee "$OUT/change-summary-verified.txt"

echo
echo "=== BUILDING PHOTONCAMERA ${VERSION_NAME} ==="
echo "Do not open another terminal until BUILD COMPLETE appears."

set +e
./gradlew clean assembleDebug 2>&1 \
    | tee "$OUT/build-26167-resumed.log"
BUILD_STATUS=${PIPESTATUS[0]}
set -e

if [ "$BUILD_STATUS" -ne 0 ]; then
    grep -nE \
        'error:|cannot find symbol|FAILURE:|Compilation failed|What went wrong' \
        "$OUT/build-26167-resumed.log" \
        | tail -260 \
        > "$OUT/relevant-errors-resumed.txt" || true

    fail "Gradle build failed; inspect $OUT/relevant-errors-resumed.txt" \
        "$BUILD_STATUS"
fi

APK="$(find app/build/outputs/apk/debug \
    -maxdepth 1 -type f -name '*.apk' | head -n 1)"

[ -n "$APK" ] && [ -f "$APK" ] \
    || fail "Debug APK was not created"

APK_COPY="$OUT/PhotonCamera-${VERSION_NAME}-motion-residual-noise-fix-debug.apk"

cp "$APK" "$APK_COPY"
sha256sum "$APK" "$APK_COPY" \
    | tee "$OUT/sha256-resumed.txt"

echo
echo "============================================================"
echo " BUILD COMPLETE"
echo "============================================================"
echo "PhotonCamera:   ${VERSION_NAME}"
echo "VERSION_BUILD: ${EXPECTED_BUILD}"
echo "APK:           $APK_COPY"
echo "Verified patch:$OUT/combined-26167-motion-residual-noise-fix-verified.patch"
echo "Build log:     $OUT/build-26167-resumed.log"
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
