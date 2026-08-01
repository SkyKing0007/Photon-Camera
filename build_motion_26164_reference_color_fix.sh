#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
EXPECTED_BUILD="26163"
NEW_BUILD="26164"
NEW_VERSION="0.9726164"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="/workspaces/Photon-Camera/build_${NEW_BUILD}_motion_reference_color_fix_${STAMP}"
BACKUP_BRANCH="backup-before-motion-reference-color-${NEW_BUILD}-${STAMP}"

PARAMS="app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java"
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

trap 'code=$?; if [ "$code" -ne 0 ]; then echo; echo "FAILED: build 26164 (exit $code)"; echo "Workspace: $OUT"; fi' EXIT

echo "============================================================"
echo " PhotonCamera ${NEW_VERSION}"
echo " Motion reference-metadata color correction"
echo "============================================================"

[ "$(git branch --show-current)" = "$EXPECTED_BRANCH" ] \
    || fail "Expected branch $EXPECTED_BRANCH"

[ "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" ] \
    || fail "Expected HEAD $EXPECTED_HEAD"

grep -q "^VERSION_BUILD=${EXPECTED_BUILD}$" "$VERSION" \
    || fail "Expected VERSION_BUILD=${EXPECTED_BUILD}"

grep -Fq 'pRGB = corr*sensorToIntermediate*pRGB;' "$SHADER" \
    || fail "Expected 26163 shader line missing"

grep -Fq 'ReCalcColor(true, result);' "$PARAMS" \
    || fail "Expected Motion custom-neutral override missing"

mkdir -p "$OUT/source_before" "$OUT/source_after"

git branch "$BACKUP_BRANCH" HEAD
git diff --binary HEAD > "$OUT/working-tree-before-${NEW_BUILD}.patch"

cp "$PARAMS" "$OUT/source_before/Parameters.java"
cp "$SHADER" "$OUT/source_before/initial.glsl"
cp "$VERSION" "$OUT/source_before/version.properties"

python3 - <<'PY'
from pathlib import Path

params_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/render/Parameters.java"
)
shader_path = Path("app/src/main/assets/shaders/initial.glsl")
version_path = Path("app/version.properties")

params = params_path.read_text()

start_marker = """            /*
             * Build 26159:
"""

end_marker = """        }
        if (!usedDynamic)
"""

start = params.find(start_marker)
end = params.find(end_marker, start)

if start < 0 or end < 0:
    raise SystemExit(
        "ERROR: exact Motion custom-neutral block was not found"
    )

old_block = params[start:end]

required_terms = [
    "customNeutral",
    "ReCalcColor(true, result);",
    "MOTION_COLOR_NEUTRAL_SELECTED",
    "source=burst",
    "source=previewFallback",
    "source=resultFallback",
]

for term in required_terms:
    if term not in old_block:
        raise SystemExit(
            "ERROR: unexpected Motion color block; missing " + term
        )

new_block = """            /*
             * Build 26164:
             *
             * Use the standard Photon color path with the same CaptureResult
             * already supplied to FillDynamicParameters. This keeps the
             * neutral point, color transforms, calibration transforms and
             * forward matrices tied to one metadata source.
             *
             * Preview and burst neutral values remain diagnostics only.
             * They must not override the standard result-based calculation.
             */
            ReCalcColor(false, result);

            Log.d(
                    TAG,
                    "MOTION_COLOR_REFERENCE_METADATA"
                            + " source=captureResult"
                            + " burstNeutral="
                            + Arrays.toString(
                                    burstNeutral
                            )
                            + " previewNeutral="
                            + Arrays.toString(
                                    motionPreviewNeutral
                            )
                            + " burstNeutralValid="
                            + burstNeutralValid
                            + " previewNeutralValid="
                            + previewNeutralValid
                            + " neutralDistance="
                            + neutralDistance(
                                    burstNeutral,
                                    motionPreviewNeutral
                            )
                            + " selectedWhitePoint="
                            + Arrays.toString(
                                    whitePoint
                            )
                            + " controlledIso="
                            + iso
                            + " controlledExposureTime="
                            + exposureTime
            );
"""

params = params[:start] + new_block + params[end:]
params_path.write_text(params)

shader = shader_path.read_text()

comment_start = """    /*
     * Build 26163:
"""
shader_line = "    pRGB = corr*sensorToIntermediate*pRGB;"
original_line = "    pRGB = corr*sensorToIntermediate*(pRGB*neutralPoint);"

comment_pos = shader.find(comment_start)
line_pos = shader.find(shader_line, comment_pos)

if comment_pos < 0 or line_pos < 0:
    raise SystemExit(
        "ERROR: 26163 shader modification block was not found"
    )

line_end = line_pos + len(shader_line)

shader = (
    shader[:comment_pos]
    + original_line
    + shader[line_end:]
)

if shader.count(original_line) != 1:
    raise SystemExit(
        "ERROR: restored shader expression count is not exactly one"
    )

shader_path.write_text(shader)

version = version_path.read_text()

if version.count("VERSION_BUILD=26163") != 1:
    raise SystemExit(
        "ERROR: expected exactly one VERSION_BUILD=26163"
    )

version_path.write_text(
    version.replace(
        "VERSION_BUILD=26163",
        "VERSION_BUILD=26164",
        1,
    )
)
PY

echo
echo "=== VERIFY 26164 SOURCE ==="

grep -Fq \
    'pRGB = corr*sensorToIntermediate*(pRGB*neutralPoint);' \
    "$SHADER" \
    || fail "Original Photon shader expression was not restored"

if grep -Fq 'pRGB = corr*sensorToIntermediate*pRGB;' "$SHADER"; then
    fail "26163 pink-producing shader expression remains"
fi

grep -Fq 'MOTION_COLOR_REFERENCE_METADATA' "$PARAMS" \
    || fail "26164 reference-metadata diagnostic missing"

grep -Fq 'ReCalcColor(false, result);' "$PARAMS" \
    || fail "Standard result-based color call missing"

if sed -n '330,465p' "$PARAMS" | grep -Fq 'ReCalcColor(true, result);'; then
    fail "Motion custom-neutral color override remains"
fi

if sed -n '330,465p' "$PARAMS" | grep -Fq 'customNeutral ='; then
    fail "Motion custom-neutral assignment remains"
fi

grep -q '^VERSION_BUILD=26164$' "$VERSION" \
    || fail "VERSION_BUILD was not updated"

# Guard the capture and exposure code against accidental changes.
if git diff -- \
    app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java \
    app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IsoExpoSelector.java \
    | grep -q .; then
    fail "Capture or shutter-policy source changed unexpectedly"
fi

if git diff | grep -E \
    '^[+-].*(mIsRecordingVideo|CameraMode\.RAWVIDEO|TEMPLATE_RECORD|MediaRecorder|CONTROL_AF_MODE_CONTINUOUS_VIDEO|getSelectedFpsRange)'; then
    fail "Video or RAW Video source changed unexpectedly"
fi

git diff --check \
    || fail "git diff --check reported a formatting error"

cp "$PARAMS" "$OUT/source_after/Parameters.java"
cp "$SHADER" "$OUT/source_after/initial.glsl"
cp "$VERSION" "$OUT/source_after/version.properties"

git diff --stat | tee "$OUT/change-summary.txt"
git diff --binary HEAD > "$OUT/combined-${NEW_BUILD}-motion-reference-color-fix.patch"

echo
echo "PASS: Original Photon neutral shader path restored."
echo "PASS: Motion custom-neutral override removed."
echo "PASS: CaptureResult now drives the standard color calculation."
echo "PASS: Burst and preview neutral values remain logging only."
echo "PASS: Existing shutter policy and rolling prebuffer preserved."
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
        | tail -220 \
        > "$OUT/relevant-errors.txt" || true

    fail "Gradle build failed; inspect $OUT/relevant-errors.txt" \
        "$BUILD_STATUS"
fi

APK="$(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | head -n 1)"

[ -n "$APK" ] && [ -f "$APK" ] \
    || fail "Debug APK was not created"

APK_COPY="$OUT/PhotonCamera-${NEW_VERSION}-motion-reference-color-fix-debug.apk"

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
echo "Combined patch:$OUT/combined-${NEW_BUILD}-motion-reference-color-fix.patch"
echo "Build log:     $OUT/build-${NEW_BUILD}.log"
echo
echo "Adaptive Noise Model: leave OFF."
echo
git status --short --untracked-files=no
echo
echo "Safe to open another terminal now."

trap - EXIT
