#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
EXPECTED_BUILD="26170"
NEW_BUILD="26171"
NEW_VERSION="0.9726171"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="/workspaces/Photon-Camera/build_${NEW_BUILD}_motion_noise_tuning_linefix_${STAMP}"
BACKUP_BRANCH="backup-before-motion-noise-tuning-${NEW_BUILD}-linefix-${STAMP}"

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

trap 'code=$?; if [ "$code" -ne 0 ]; then echo; echo "FAILED: 26171 line-safe finalization (exit $code)"; echo "Workspace: $OUT"; fi' EXIT

echo "============================================================"
echo " PhotonCamera ${NEW_VERSION}"
echo " Line-safe Motion tuning finalization"
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
        echo "Expected tracked state:"
        printf '%s\n' "$EXPECTED_SORTED"
        echo
        echo "Actual tracked state:"
        printf '%s\n' "$ACTUAL_MODIFIED"
        fail "Workspace does not match the audited second-failure state"
    }

for file in "$LUMA_JAVA" "$LUMA_SHADER" "$CHROMA_JAVA" "$CHROMA_SHADER"; do
    [ -f "$file" ] || fail "Required Motion source missing: $file"
done

count_marker() {
    grep -Roh "$1" \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline \
        app/src/main/assets/shaders/denoise \
        2>/dev/null | wc -l | tr -d ' '
}

[ "$(count_marker MOTION_26171_ESD3D2_TUNABLE)" = "1" ] \
    || fail "Expected one 26171 ESD marker"

[ "$(count_marker MOTION_26171_LUMA_TUNABLE)" = "2" ] \
    || fail "Expected two 26171 luma markers"

[ "$(count_marker MOTION_26171_CHROMA_TUNABLE)" = "2" ] \
    || fail "Expected two 26171 chroma markers"

[ "$(count_marker MOTION_26171_TONE_TUNABLE)" = "1" ] \
    || fail "Expected one 26171 tone marker"

[ "$(count_marker MOTION_26171_CAPTURE_SHARPEN_TUNABLE)" = "1" ] \
    || fail "Expected one 26171 capture-sharpen marker"

[ "$(count_marker MOTION_26171_FINAL_SHARPEN_TUNABLE)" = "0" ] \
    || fail "Final sharpening is already modified"

[ "$(count_marker MOTION_26170_FINAL_SHARPEN)" = "1" ] \
    || fail "Expected one remaining 26170 final-sharpen marker"

grep -Fq 'float denoiseActivity;' "$FINAL_SHARP" \
    || fail "Sharpen2 denoiseActivity field missing"

grep -Fq '1.0f - 0.90f * highIsoBlend;' "$FINAL_SHARP" \
    || fail "Sharpen2 26170 scale formula missing"

grep -Fq '"MOTION_26170_FINAL_SHARPEN"' "$FINAL_SHARP" \
    || fail "Sharpen2 26170 marker missing"

! grep -Fq 'motionFinalSharpeningFloor' "$FINAL_SHARP" \
    || fail "Sharpen2 floor already exists"

! grep -Fq 'CaptureSharpening.class' "$REGISTRY" \
    || fail "CaptureSharpening is already registered"

! grep -Fq 'MotionLumaDenoise.class' "$REGISTRY" \
    || fail "MotionLumaDenoise is already registered"

! grep -Fq 'MotionChromaDenoise.class' "$REGISTRY" \
    || fail "MotionChromaDenoise is already registered"

grep -Fq '#define KSIZE 6' "$CHROMA_SHADER" \
    || fail "Expected 26170 chroma KSIZE missing"

grep -Fq '#define SAMPLESTEP 8' "$CHROMA_SHADER" \
    || fail "Expected 26170 chroma SAMPLESTEP missing"

! grep -Fq 'SHADOWNEUTRALIZATION' "$CHROMA_SHADER" \
    || fail "Chroma shader is already finalized"

grep -Fq 'showPreciseValueDialog' "$SEEK_PREF" \
    || fail "Precise numeric-entry UI missing"

grep -Fq 'setNeutralButton("Reset"' "$SEEK_PREF" \
    || fail "Per-setting Reset control missing"

grep -Fq 'MOTION_26168_MERGE_NOISE_AWARE' "$PYRAMID" \
    || fail "Twenty-frame merge correction missing"

grep -Fq 'MOTION_26166_BLACK_LEVEL_SELECTED' "$CAPTURE" \
    || fail "Validated black-level path missing"

grep -Fq 'MOTION_26166_IMAGE_SAVED_COMPLETE' "$HDRX" \
    || fail "Image save-completion path missing"

grep -Fq 'pRGB = corr*sensorToIntermediate*(pRGB*neutralPoint);' "$COLOR_SHADER" \
    || fail "Original Photon color path missing"

mkdir -p "$OUT/source_before" "$OUT/source_after"

echo
echo "=== CREATE BACKUP BRANCH AND PATCH ==="

git branch "$BACKUP_BRANCH" HEAD

{
    git diff --binary HEAD
    git diff --binary --no-index /dev/null "$LUMA_JAVA" || true
    git diff --binary --no-index /dev/null "$LUMA_SHADER" || true
    git diff --binary --no-index /dev/null "$CHROMA_JAVA" || true
    git diff --binary --no-index /dev/null "$CHROMA_SHADER" || true
} > "$OUT/working-tree-before-${NEW_BUILD}-linefix.patch"

for file in "$FINAL_SHARP" "$REGISTRY" "$CHROMA_SHADER" "$VERSION"; do
    cp "$file" "$OUT/source_before/$(basename "$file")"
done

sha256sum \
    "$POST" "$ESD_JAVA" "$ESD_SHADER" \
    "$LUMA_JAVA" "$LUMA_SHADER" "$CHROMA_JAVA" \
    "$AUTO_EXPOSURE" "$CAPTURE_SHARP" \
    "$CAPTURE" "$PARAMS" "$HDRX" "$INITIAL" "$COLOR_SHADER" \
    "$PYRAMID" "$MERGE_SHADER" "$EXPOSURE_SELECTOR" \
    "$GENERATOR" "$INJECTOR" "$ANNOTATION" "$SEEK_PREF" \
    > "$OUT/protected-before.sha256"

echo "Backup branch: $BACKUP_BRANCH"
echo "Backup patch:  $OUT/working-tree-before-${NEW_BUILD}-linefix.patch"

echo
echo "=== APPLY FOUR LINE-SAFE FINAL CHANGES ==="

python3 - <<'PY'
from pathlib import Path

sharp_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/opengl/postpipeline/Sharpen2.java"
)
registry_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "settings/TunableRegistry.java"
)
shader_path = Path(
    "app/src/main/assets/shaders/denoise/"
    "motionchromadenoise.glsl"
)
version_path = Path("app/version.properties")


def find_unique_line(lines, stripped_value, label):
    matches = [
        index
        for index, line in enumerate(lines)
        if line.strip() == stripped_value
    ]
    if len(matches) != 1:
        raise SystemExit(
            f"ERROR: {label}: expected one line, found {len(matches)}"
        )
    return matches[0]


def replace_unique_text(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"ERROR: {label}: expected one match, found {count}"
        )
    return text.replace(old, new, 1)


# --------------------------------------------------------------
# Sharpen2: line-based field insertion, then exact formula edits.
# --------------------------------------------------------------
sharp_text = sharp_path.read_text()
sharp_lines = sharp_text.splitlines(keepends=True)

field_index = find_unique_line(
    sharp_lines,
    "float denoiseActivity;",
    "Sharpen2 denoiseActivity field",
)

override_indices = [
    index
    for index in range(field_index + 1, len(sharp_lines))
    if sharp_lines[index].strip() == "@Override"
]

if not override_indices:
    raise SystemExit(
        "ERROR: Sharpen2: no @Override found after denoiseActivity"
    )

override_index = override_indices[0]

between = sharp_lines[field_index + 1:override_index]
if any(line.strip() for line in between):
    raise SystemExit(
        "ERROR: Sharpen2: unexpected code between denoiseActivity and @Override"
    )

insertion = [
    "\n",
    "    @Tunable(\n",
    '            title = "Motion final sharpening floor",\n',
    '            description = "Fraction of the selected final sharpening retained at ISO 3200.",\n',
    '            category = "Motion Noise Tuning",\n',
    "            min = 0.0f,\n",
    "            max = 1.0f,\n",
    "            defaultValue = 0.40f,\n",
    "            step = 0.05f\n",
    "    )\n",
    "    float motionFinalSharpeningFloor = 0.40f;\n",
]

sharp_lines[field_index + 1:override_index] = insertion
sharp_text = "".join(sharp_lines)

sharp_text = replace_unique_text(
    sharp_text,
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
    "Sharpen2 high-ISO formula",
)

sharp_text = replace_unique_text(
    sharp_text,
    '"MOTION_26170_FINAL_SHARPEN"',
    '"MOTION_26171_FINAL_SHARPEN_TUNABLE"',
    "Sharpen2 marker",
)

sharp_text = replace_unique_text(
    sharp_text,
    """                            + " scale=" + motionSharpScale
                            + " appliedStrength=" + sharpness
""",
    """                            + " scale=" + motionSharpScale
                            + " configuredFloor="
                            + motionFinalSharpeningFloor
                            + " appliedStrength=" + sharpness
""",
    "Sharpen2 log",
)

sharp_path.write_text(sharp_text)


# --------------------------------------------------------------
# TunableRegistry: insert directly after the unique Sharpen2 line.
# --------------------------------------------------------------
registry_text = registry_path.read_text()
registry_lines = registry_text.splitlines(keepends=True)

sharpen_registry_index = find_unique_line(
    registry_lines,
    "com.particlesdevs.photoncamera.processing.opengl.postpipeline.Sharpen2.class,",
    "TunableRegistry Sharpen2 line",
)

registry_insertion = [
    "        com.particlesdevs.photoncamera.processing.opengl.postpipeline.CaptureSharpening.class,\n",
    "        com.particlesdevs.photoncamera.processing.opengl.postpipeline.MotionLumaDenoise.class,\n",
    "        com.particlesdevs.photoncamera.processing.opengl.postpipeline.MotionChromaDenoise.class,\n",
]

registry_lines[
    sharpen_registry_index + 1:
    sharpen_registry_index + 1
] = registry_insertion

registry_path.write_text("".join(registry_lines))


# --------------------------------------------------------------
# Chroma shader: replace define lines and neutrality constants
# without depending on surrounding whitespace.
# --------------------------------------------------------------
shader_text = shader_path.read_text()
shader_lines = shader_text.splitlines(keepends=True)

define_updates = {
    "#define KSIZE 6": "#define KSIZE 4\n",
    "#define SAMPLESTEP 8": "#define SAMPLESTEP 6\n",
    "#define GUIDESIGMA 0.10": "#define GUIDESIGMA 0.08\n",
}

for old_line, new_line in define_updates.items():
    index = find_unique_line(
        shader_lines,
        old_line,
        f"Shader {old_line}",
    )
    shader_lines[index] = new_line

noiseo_index = find_unique_line(
    shader_lines,
    "#define NOISEO 0.0",
    "Shader NOISEO define",
)

shader_lines.insert(
    noiseo_index,
    "#define SHADOWNEUTRALIZATION 0.0\n",
)

shader_text = "".join(shader_lines)

shader_text = replace_unique_text(
    shader_text,
    """    float neutralityStrength =
            0.18
                    * CHROMASTRENGTH
""",
    """    float neutralityStrength =
            SHADOWNEUTRALIZATION
                    * CHROMASTRENGTH
""",
    "Shader neutrality strength",
)

shader_text = replace_unique_text(
    shader_text,
    """                            0.0,
                            0.18
""",
    """                            0.0,
                            SHADOWNEUTRALIZATION
""",
    "Shader neutrality clamp",
)

shader_path.write_text(shader_text)


# --------------------------------------------------------------
# Version bump, line-based and last.
# --------------------------------------------------------------
version_lines = version_path.read_text().splitlines(keepends=True)
version_index = find_unique_line(
    version_lines,
    "VERSION_BUILD=26170",
    "VERSION_BUILD",
)
version_lines[version_index] = "VERSION_BUILD=26171\n"
version_path.write_text("".join(version_lines))
PY

echo
echo "=== VERIFY COMPLETE 26171 STATE ==="

grep -Fq 'motionFinalSharpeningFloor = 0.40f' "$FINAL_SHARP" \
    || fail "Sharpen2 tuning floor missing"

grep -Fq 'MOTION_26171_FINAL_SHARPEN_TUNABLE' "$FINAL_SHARP" \
    || fail "Sharpen2 26171 marker missing"

! grep -Fq 'MOTION_26170_FINAL_SHARPEN' "$FINAL_SHARP" \
    || fail "Old Sharpen2 marker remains"

grep -Fq 'CaptureSharpening.class' "$REGISTRY" \
    || fail "CaptureSharpening not registered"

grep -Fq 'MotionLumaDenoise.class' "$REGISTRY" \
    || fail "MotionLumaDenoise not registered"

grep -Fq 'MotionChromaDenoise.class' "$REGISTRY" \
    || fail "MotionChromaDenoise not registered"

grep -Fq '#define KSIZE 4' "$CHROMA_SHADER" \
    || fail "Conservative chroma kernel missing"

grep -Fq '#define SAMPLESTEP 6' "$CHROMA_SHADER" \
    || fail "Conservative chroma step missing"

grep -Fq '#define GUIDESIGMA 0.08' "$CHROMA_SHADER" \
    || fail "Conservative chroma guide default missing"

grep -Fq '#define SHADOWNEUTRALIZATION 0.0' "$CHROMA_SHADER" \
    || fail "Zero-default shadow neutralization missing"

grep -q '^VERSION_BUILD=26171$' "$VERSION" \
    || fail "VERSION_BUILD was not updated"

[ "$(count_marker MOTION_26171_ESD3D2_TUNABLE)" = "1" ] \
    || fail "26171 ESD marker count changed"

[ "$(count_marker MOTION_26171_LUMA_TUNABLE)" = "2" ] \
    || fail "26171 luma marker count changed"

[ "$(count_marker MOTION_26171_CHROMA_TUNABLE)" = "2" ] \
    || fail "26171 chroma marker count changed"

[ "$(count_marker MOTION_26171_TONE_TUNABLE)" = "1" ] \
    || fail "26171 tone marker count changed"

[ "$(count_marker MOTION_26171_CAPTURE_SHARPEN_TUNABLE)" = "1" ] \
    || fail "26171 capture-sharpen marker count changed"

[ "$(count_marker MOTION_26171_FINAL_SHARPEN_TUNABLE)" = "1" ] \
    || fail "Expected one 26171 final-sharpen marker"

grep -Fq 'category = "Motion Noise Tuning"' "$POST" \
    || fail "Motion tuning category missing"

grep -Fq 'motionStableWeightBlendMaximum = 0.10f' "$ESD_JAVA" \
    || fail "Conservative ESD default missing"

grep -Fq 'motionLumaCleanupMaximum = 0.08f' "$LUMA_JAVA" \
    || fail "Conservative luma default missing"

grep -Fq 'motionChromaCleanupMaximum = 0.30f' "$CHROMA_JAVA" \
    || fail "Conservative chroma default missing"

grep -Fq 'motionChromaRadiusPixels = 24' "$CHROMA_JAVA" \
    || fail "24-pixel chroma-radius default missing"

grep -Fq 'motionShadowNeutralization = 0.0f' "$CHROMA_JAVA" \
    || fail "Zero shadow-neutralization Java default missing"

grep -Fq 'motionHighIsoGainLimit = 4.0f' "$AUTO_EXPOSURE" \
    || fail "4.0 tone-gain default missing"

grep -Fq 'motionCaptureSharpeningFloor = 0.40f' "$CAPTURE_SHARP" \
    || fail "Capture sharpening floor missing"

grep -Fq 'showPreciseValueDialog' "$SEEK_PREF" \
    || fail "Precise numeric-entry UI disappeared"

grep -Fq 'setPositiveButton("Set"' "$SEEK_PREF" \
    || fail "Numeric-entry Set control disappeared"

grep -Fq 'setNeutralButton("Reset"' "$SEEK_PREF" \
    || fail "Numeric-entry Reset control disappeared"

grep -Fq 'setNegativeButton("Cancel"' "$SEEK_PREF" \
    || fail "Numeric-entry Cancel control disappeared"

sha256sum -c "$OUT/protected-before.sha256" \
    || fail "A protected file changed"

git diff --check \
    || fail "git diff --check reported a formatting problem"

for file in "$FINAL_SHARP" "$REGISTRY" "$CHROMA_SHADER" "$VERSION"; do
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
echo "PASS: four unfinished 26171 files finalized."
echo "PASS: Motion Noise Tuning sliders and numeric entry registered."
echo "PASS: luma cleanup default 0.08."
echo "PASS: chroma cleanup default 0.30."
echo "PASS: chroma radius default 24 pixels."
echo "PASS: shadow neutralization default 0.00."
echo "PASS: ESD stable-weight blend default 0.10."
echo "PASS: capture and final sharpening floors 0.40."
echo "PASS: high-ISO tone limit 4.0."
echo "PASS: twenty-frame merge, black level and color paths preserved."
echo "PASS: Photo, Night, Video and RAW Video unchanged."
echo "PASS: Adaptive Noise Model unchanged; leave OFF."

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
echo "Backup patch:  $OUT/working-tree-before-${NEW_BUILD}-linefix.patch"
echo "Combined patch:$OUT/combined-${NEW_BUILD}-motion-noise-tuning.patch"
echo "Build log:     $OUT/build-${NEW_BUILD}.log"
echo
echo "Open:"
echo "  Settings -> Tunable Settings -> Tunable - Motion Noise Tuning"
echo
echo "Tap the displayed value for precise numeric entry."
echo "Use Reset to restore the 26171 default."
echo
echo "Adaptive Noise Model: leave OFF."
echo
git status --short --untracked-files=no
echo
echo "Safe to open another terminal now."

trap - EXIT
