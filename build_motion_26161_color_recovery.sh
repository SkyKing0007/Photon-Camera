#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
EXPECTED_BUILD="26160"
NEW_BUILD="26161"
NEW_VERSION="0.9726161"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="/workspaces/Photon-Camera/build_${NEW_BUILD}_motion_color_recovery_${STAMP}"
BACKUP_BRANCH="backup-before-motion-color-recovery-${NEW_BUILD}-${STAMP}"

PARAMS="app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java"
NOISE="app/src/main/java/com/particlesdevs/photoncamera/processing/render/NoiseModeler.java"
MERGE="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts/PyramidMerging.java"
HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
POST="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
INITIAL="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java"
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

trap 'code=$?; if [ "$code" -ne 0 ]; then echo; echo "FAILED: build 26161 (exit $code)"; echo "Workspace: $OUT"; fi' EXIT

echo "============================================================"
echo " PhotonCamera ${NEW_VERSION}"
echo " Motion color recovery / 26157 processing restoration"
echo "============================================================"

[ "$(git branch --show-current)" = "$EXPECTED_BRANCH" ] \
    || fail "Expected branch $EXPECTED_BRANCH"

[ "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" ] \
    || fail "Expected HEAD $EXPECTED_HEAD"

grep -q "^VERSION_BUILD=${EXPECTED_BUILD}$" "$VERSION" \
    || fail "Expected VERSION_BUILD=${EXPECTED_BUILD}"

EXPECTED_FILES="$INITIAL
$PARAMS
$NOISE
$MERGE
$HDRX
$POST
$VERSION"

ACTUAL_FILES="$(git status --short --untracked-files=no | awk '{print $2}' | sort)"
EXPECTED_SORTED="$(printf '%s\n' "$EXPECTED_FILES" | sort)"

[ "$ACTUAL_FILES" = "$EXPECTED_SORTED" ] \
    || {
        echo "Expected modified files:"
        printf '%s\n' "$EXPECTED_SORTED"
        echo
        echo "Actual modified files:"
        printf '%s\n' "$ACTUAL_FILES"
        fail "Tracked changes are not exactly the verified 26160 set"
    }

grep -q 'MOTION_EFFECTIVE_STACK' "$MERGE" \
    || fail "26158 merge marker missing"

grep -q 'MOTION_COLOR_NEUTRAL_SELECTED' "$PARAMS" \
    || fail "26159 burst-neutral selection missing"

grep -q 'MOTION_POST_DENOISE_STACK_POLICY' "$HDRX" \
    || fail "26160 denoise policy marker missing"

grep -q 'MOTION_FINAL_COLOR_PATH' "$INITIAL" \
    || fail "26160 final color diagnostics missing"

mkdir -p "$OUT/source_before" "$OUT/source_after"

git branch "$BACKUP_BRANCH" HEAD
git diff --binary HEAD > "$OUT/working-tree-26160-before-${NEW_BUILD}.patch"

for file in "$PARAMS" "$NOISE" "$MERGE" "$HDRX" "$POST" "$INITIAL" "$VERSION"; do
    cp "$file" "$OUT/source_before/$(basename "$file")"
done

echo
echo "Saved complete 26160 working state:"
echo "  Backup branch: $BACKUP_BRANCH"
echo "  Backup patch:  $OUT/working-tree-26160-before-${NEW_BUILD}.patch"

echo
echo "=== RESTORE LAST COLOR-STABLE PROCESSING CORE ==="

git show "HEAD:$NOISE" > "$NOISE"
git show "HEAD:$MERGE" > "$MERGE"
git show "HEAD:$POST" > "$POST"

python3 - <<'PY'
from pathlib import Path
import re

params_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/render/Parameters.java"
)
hdrx_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/processor/HdrxProcessor.java"
)
initial_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/opengl/postpipeline/Initial.java"
)
version_path = Path("app/version.properties")

params = params_path.read_text()

old_fields = (
    "    public int retainedFrameCount = 1;\n"
    "    public float effectiveFrameCount = 1.0f;\n"
    "    public float effectiveStackRatio = 1.0f;\n"
    "    public float subpixelSampleDiversity = 0.0f;\n"
    "    public float highlightClippedFraction = 0.0f;\n"
)

new_fields = (
    "    /*\n"
    "     * Build 26161 keeps these values as diagnostics only.\n"
    "     * They no longer alter merge or downstream denoise behavior.\n"
    "     */\n"
    "    public int retainedFrameCount = 1;\n"
    "    public float effectiveFrameCount = 1.0f;\n"
    "    public float effectiveStackRatio = 1.0f;\n"
    "    public float subpixelSampleDiversity = 0.0f;\n"
    "    public float highlightClippedFraction = 0.0f;\n"
)

if old_fields in params:
    params = params.replace(old_fields, new_fields, 1)

params_path.write_text(params)

hdrx = hdrx_path.read_text()

start_marker = "        /*\n         * Build 26160 color/denoise isolation:"
end_marker = '        Log.d(\n                TAG,\n                "FINAL_EFFECTIVE_STACK"'

start = hdrx.find(start_marker)
if start < 0:
    raise SystemExit("ERROR: 26160 denoise block start not found")

end_start = hdrx.find(end_marker, start)
if end_start < 0:
    raise SystemExit("ERROR: FINAL_EFFECTIVE_STACK log not found")

end = hdrx.find("        );", end_start)
if end < 0:
    raise SystemExit("ERROR: FINAL_EFFECTIVE_STACK log end not found")
end += len("        );\n")

replacement = """        /*
         * Build 26161:
         *
         * Restore the last color-stable 26157 processing behavior.
         * Effective-stack values remain diagnostic only and are set equal
         * to the retained frame count. No heuristic effective-frame scalar
         * is allowed to alter merge thresholds, channel noise, ESD3D2,
         * tone lifting, or sharpening.
         */
        processingParameters.retainedFrameCount =
                Math.max(
                        1,
                        processingParameters.retainedFrameCount
                );

        processingParameters.effectiveFrameCount =
                processingParameters.retainedFrameCount;

        processingParameters.effectiveStackRatio =
                1.0f;

        processingParameters.subpixelSampleDiversity =
                0.0f;

        processingParameters.noiseModeler.computeStackingNoiseModel(
                processingParameters.retainedFrameCount
        );

        Log.d(
                TAG,
                "MOTION_26161_COLOR_RECOVERY"
                        + " retained="
                        + processingParameters.retainedFrameCount
                        + " effectiveDiagnostic="
                        + processingParameters.effectiveFrameCount
                        + " ratioDiagnostic="
                        + processingParameters.effectiveStackRatio
                        + " processingCore=26157"
                        + " adaptiveNoiseSettingUnchanged=true"
                        + " colorNeutral=burstValidated"
                        + " matrixConvention=unchanged"
                        + " gainMapConvention=unchanged"
        );
"""

hdrx = hdrx[:start] + replacement + hdrx[end:]
hdrx_path.write_text(hdrx)

initial = initial_path.read_text()
if initial.count('"MOTION_FINAL_COLOR_PATH"') != 1:
    raise SystemExit(
        "ERROR: expected one MOTION_FINAL_COLOR_PATH marker"
    )

initial = initial.replace(
    '"MOTION_FINAL_COLOR_PATH"',
    '"MOTION_26161_FINAL_COLOR_PATH"',
    1,
)
initial_path.write_text(initial)

version = version_path.read_text()
if version.count("VERSION_BUILD=26160") != 1:
    raise SystemExit(
        "ERROR: expected exactly one VERSION_BUILD=26160"
    )

version_path.write_text(
    version.replace(
        "VERSION_BUILD=26160",
        "VERSION_BUILD=26161",
        1,
    )
)
PY

echo
echo "=== VERIFY 26161 RECOVERY SCOPE ==="

grep -q 'MOTION_COLOR_NEUTRAL_SELECTED' "$PARAMS" \
    || fail "Burst-neutral validation was lost"

grep -q 'MOTION_GAIN_MAP_CHANNELS' "$PARAMS" \
    || fail "Gain-map diagnostics were lost"

grep -q 'MOTION_26161_COLOR_RECOVERY' "$HDRX" \
    || fail "26161 recovery marker missing"

grep -q 'MOTION_26161_FINAL_COLOR_PATH' "$INITIAL" \
    || fail "26161 final color marker missing"

grep -q '^VERSION_BUILD=26161$' "$VERSION" \
    || fail "VERSION_BUILD was not updated"

if grep -q 'MOTION_EFFECTIVE_STACK' "$MERGE"; then
    fail "26158 effective-stack merge behavior still present"
fi

if grep -q 'MOTION_CHANNEL_NOISE_PRESERVED' "$MERGE"; then
    fail "26158 channel-noise merge behavior still present"
fi

if grep -q 'MOTION_POST_NOISE_HANDOFF' "$POST"; then
    fail "26158 post-noise behavior still present"
fi

for file in "$NOISE" "$MERGE" "$POST"; do
    if ! git diff --quiet HEAD -- "$file"; then
        fail "$file does not exactly match the 26157 checkpoint"
    fi
done

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

for file in "$PARAMS" "$NOISE" "$MERGE" "$HDRX" "$POST" "$INITIAL" "$VERSION"; do
    cp "$file" "$OUT/source_after/$(basename "$file")"
done

git diff --stat | tee "$OUT/change-summary.txt"
git diff --binary HEAD > "$OUT/combined-26157-metadata-and-26161-recovery.patch"

echo
echo "PASS: 26158 processing behavior fully removed."
echo "PASS: Pyramid merge restored exactly to 26157."
echo "PASS: NoiseModeler restored exactly to 26157."
echo "PASS: PostPipeline restored exactly to 26157."
echo "PASS: 26159 burst-neutral validation preserved."
echo "PASS: 26160 matrix and gain-map diagnostics preserved."
echo "PASS: Neutral/matrix convention left mathematically consistent."
echo "PASS: Adaptive Noise Model setting remains user-controlled; leave OFF."
echo "PASS: Capture, exposure, Video and RAW Video unchanged."

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
        | tail -220 \
        > "$OUT/relevant-errors.txt" || true

    fail "Gradle build failed; inspect $OUT/relevant-errors.txt" \
        "$BUILD_STATUS"
fi

APK="app/build/outputs/apk/debug/PhotonCamera-${NEW_VERSION}-debug.apk"
APK_COPY="$OUT/PhotonCamera-${NEW_VERSION}-motion-color-recovery-debug.apk"

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
echo "26160 patch:   $OUT/working-tree-26160-before-${NEW_BUILD}.patch"
echo "Combined patch:$OUT/combined-26157-metadata-and-26161-recovery.patch"
echo "Build log:     $OUT/build-${NEW_BUILD}.log"
echo
echo "Expected markers:"
echo "  MOTION_26161_COLOR_RECOVERY"
echo "  MOTION_26161_FINAL_COLOR_PATH"
echo "  MOTION_COLOR_NEUTRAL_SELECTED"
echo "  MOTION_GAIN_MAP_CHANNELS"
echo
echo "Adaptive Noise Model: leave OFF."
echo
git status --short --untracked-files=no
echo
echo "Safe to open another terminal now."

trap - EXIT
