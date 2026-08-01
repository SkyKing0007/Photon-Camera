#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
OLD_BUILD="26173"
NEW_BUILD="26174"
STAMP="$(date +%Y%m%d_%H%M%S)"

WORK="/workspaces/Photon-Camera/build_26174_hdrx_ui_compile_fix_${STAMP}"
BACKUP_BRANCH="backup-before-hdrx-ui-compile-fix-26174-${STAMP}"
APK_OUT="$WORK/PhotonCamera-0.9726174-hdrx-fix-apple-liquid-ui-debug.apk"
BUILD_LOG="$WORK/build-26174.log"

VERSION="app/version.properties"
CAMERA_UI="app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java"
CAMERA_CONTROLLER="app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java"
SETTINGS_LAYOUT="app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/settingsbar/SettingsBarLayout.java"
IDS_XML="app/src/main/res/values/ids.xml"

PYRAMID="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts/PyramidMerging.java"
HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
PARAMS="app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java"
NOISE="app/src/main/java/com/particlesdevs/photoncamera/processing/render/NoiseModeler.java"
POST="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
MOTION_SHADER="app/src/main/assets/shaders/merge/motionmerge11.glsl"
INIT_SHADER="app/src/main/assets/shaders/merge/contributioninit.glsl"

mkdir -p "$WORK/before" "$WORK/after"

fail() {
    echo
    echo "============================================================"
    echo " BUILD 26174 STOPPED"
    echo "============================================================"
    echo "Reason: $1"
    exit 1
}

echo "============================================================"
echo " PhotonCamera 0.9726174 — 26173 compile continuation"
echo "============================================================"
echo "Branch required: $EXPECTED_BRANCH"
echo "Base HEAD:       $EXPECTED_HEAD"
echo "Current build:   $OLD_BUILD"
echo "New build:       $NEW_BUILD"
echo

[ "$(git branch --show-current)" = "$EXPECTED_BRANCH" ] \
    || fail "Wrong branch"

[ "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" ] \
    || fail "Unexpected base HEAD"

grep -q "^VERSION_BUILD=${OLD_BUILD}$" "$VERSION" \
    || fail "Expected VERSION_BUILD=${OLD_BUILD}; do not rerun the previous script"

grep -Fq 'int[] modeNameIds = CameraMode.nameIds();' "$CAMERA_UI" \
    || fail "Expected 26173 Integer-array compile fault is not present"

grep -Fq 'R.id.manual_controls_button' "$CAMERA_UI" \
    || fail "Expected manual control reference missing from CameraUIViewImpl"

grep -Fq 'R.id.manual_controls_button' "$CAMERA_CONTROLLER" \
    || fail "Expected manual control reference missing from CameraUIController"

grep -Fq 'R.id.grid_toggle_button' "$CAMERA_CONTROLLER" \
    || fail "Expected grid control reference missing from CameraUIController"

grep -Fq 'manualButton.setId(R.id.manual_controls_button);' "$SETTINGS_LAYOUT" \
    || fail "Expected dynamic manual button source missing"

grep -Fq 'layout(r32f, binding = 4)' "$MOTION_SHADER" \
    || fail "26173 HDRX r32f Motion shader fix is missing"

grep -Fq 'layout(r32f, binding = 0)' "$INIT_SHADER" \
    || fail "26173 HDRX r32f initializer fix is missing"

grep -Fq 'storageFormat=R32F' "$PYRAMID" \
    || fail "26173 R32F contribution marker is missing"

echo "Saving protected processing hashes..."

sha256sum \
    "$PYRAMID" \
    "$HDRX" \
    "$PARAMS" \
    "$NOISE" \
    "$POST" \
    "$MOTION_SHADER" \
    "$INIT_SHADER" \
    > "$WORK/protected-processing-before.sha256"

for file in \
    "$VERSION" \
    "$CAMERA_UI" \
    "$CAMERA_CONTROLLER" \
    "$SETTINGS_LAYOUT"; do
    mkdir -p "$WORK/before/$(dirname "$file")"
    cp "$file" "$WORK/before/$file"
done

if [ -f "$IDS_XML" ]; then
    mkdir -p "$WORK/before/$(dirname "$IDS_XML")"
    cp "$IDS_XML" "$WORK/before/$IDS_XML"
fi

git status --short > "$WORK/status-before.txt"

git branch "$BACKUP_BRANCH" HEAD
git diff --binary > "$WORK/working-tree-before-26174.patch"

echo "Backup branch: $BACKUP_BRANCH"
echo "Backup patch:  $WORK/working-tree-before-26174.patch"
echo

echo "Applying the five Java/resource compile corrections..."

python3 - <<'PY'
from pathlib import Path
import re

camera_ui = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "ui/camera/CameraUIViewImpl.java"
)
text = camera_ui.read_text()

old = "        int[] modeNameIds = CameraMode.nameIds();"
new = "        Integer[] modeNameIds = CameraMode.nameIds();"

if text.count(old) != 1:
    raise SystemExit(
        "CameraUIViewImpl type correction expected one match, found "
        + str(text.count(old))
    )

camera_ui.write_text(text.replace(old, new, 1))

ids_path = Path("app/src/main/res/values/ids.xml")

required_ids = (
    "manual_controls_button",
    "grid_toggle_button",
)

if ids_path.exists():
    ids_text = ids_path.read_text()
    if ids_text.count("</resources>") != 1:
        raise SystemExit("ids.xml must contain exactly one closing resources tag")
else:
    ids_text = '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n</resources>\n'

insertions = []

for name in required_ids:
    item_pattern = re.compile(
        r'<item\s+[^>]*type\s*=\s*["\']id["\'][^>]*'
        r'name\s*=\s*["\']' + re.escape(name) + r'["\'][^>]*/\s*>'
        r'|<item\s+[^>]*name\s*=\s*["\']' + re.escape(name) + r'["\'][^>]*'
        r'type\s*=\s*["\']id["\'][^>]*/\s*>'
    )

    if not item_pattern.search(ids_text):
        insertions.append(f'    <item type="id" name="{name}" />')

if insertions:
    ids_text = ids_text.replace(
        "</resources>",
        "\n".join(insertions) + "\n</resources>",
        1,
    )

ids_path.parent.mkdir(parents=True, exist_ok=True)
ids_path.write_text(ids_text)

version_path = Path("app/version.properties")
version_text = version_path.read_text()

if version_text.count("VERSION_BUILD=26173") != 1:
    raise SystemExit("VERSION_BUILD=26173 context mismatch")

version_path.write_text(
    version_text.replace(
        "VERSION_BUILD=26173",
        "VERSION_BUILD=26174",
        1,
    )
)
PY

grep -Fq 'Integer[] modeNameIds = CameraMode.nameIds();' "$CAMERA_UI" \
    || fail "CameraMode nameIds type was not corrected"

grep -Fq '<item type="id" name="manual_controls_button" />' "$IDS_XML" \
    || fail "manual_controls_button ID declaration missing"

grep -Fq '<item type="id" name="grid_toggle_button" />' "$IDS_XML" \
    || fail "grid_toggle_button ID declaration missing"

grep -q '^VERSION_BUILD=26174$' "$VERSION" \
    || fail "Build version was not incremented to 26174"

if grep -Fq 'int[] modeNameIds = CameraMode.nameIds();' "$CAMERA_UI"; then
    fail "Old incompatible CameraMode nameIds declaration remains"
fi

echo "Verifying protected HDRX and noise-processing files..."

sha256sum -c "$WORK/protected-processing-before.sha256" \
    || fail "A protected processing file changed during the compile correction"

git diff --check \
    || fail "git diff --check failed"

for file in \
    "$VERSION" \
    "$CAMERA_UI" \
    "$CAMERA_CONTROLLER" \
    "$SETTINGS_LAYOUT" \
    "$IDS_XML"; do
    mkdir -p "$WORK/after/$(dirname "$file")"
    cp "$file" "$WORK/after/$file"
done

git diff --binary > "$WORK/working-tree-after-26174.patch"
git status --short > "$WORK/status-after.txt"
git diff --stat > "$WORK/diff-stat.txt"

echo
echo "============================================================"
echo " Building PhotonCamera 0.9726174"
echo "============================================================"

set +e
./gradlew clean assembleDebug 2>&1 | tee "$BUILD_LOG"
GRADLE_STATUS=${PIPESTATUS[0]}
set -e

if [ "$GRADLE_STATUS" -ne 0 ]; then
    grep -nE \
        'error:|FAILURE:|BUILD FAILED|AAPT: error|Android resource linking failed|cannot find symbol|incompatible types' \
        "$BUILD_LOG" \
        > "$WORK/relevant-errors.txt" || true

    fail "Gradle build failed. Upload $WORK/relevant-errors.txt and $BUILD_LOG"
fi

BUILT_APK="$(
    find app/build/outputs/apk/debug \
        -type f \
        -name '*.apk' \
        -printf '%T@ %p\n' \
        | sort -nr \
        | head -n 1 \
        | cut -d' ' -f2-
)"

[ -n "$BUILT_APK" ] \
    || fail "Gradle succeeded but no debug APK was found"

cp "$BUILT_APK" "$APK_OUT"
sha256sum "$APK_OUT" > "$APK_OUT.sha256"

echo
echo "============================================================"
echo " BUILD COMPLETE"
echo "============================================================"
echo "Build:         0.9726174 / VERSION_BUILD=26174"
echo "APK:           $APK_OUT"
echo "SHA-256:       $(cat "$APK_OUT.sha256")"
echo "Backup branch: $BACKUP_BRANCH"
echo "Backup patch:  $WORK/working-tree-before-26174.patch"
echo
echo "Corrections:"
echo "  - CameraMode.nameIds() now uses Integer[]"
echo "  - manual_controls_button is declared as an Android resource ID"
echo "  - grid_toggle_button is declared as an Android resource ID"
echo "  - 26173 R32F HDRX fix remains protected and unchanged"
echo "  - Apple-inspired liquid UI remains included"
echo
echo "Adaptive Noise Model: leave OFF."
