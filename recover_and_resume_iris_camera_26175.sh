#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
FAILED_WORK="/workspaces/Photon-Camera/build_26175_iris_camera_brand_ui_20260731_175737"
RESUME_SCRIPT="/workspaces/Photon-Camera/resume_build_iris_camera_26175.sh"
STAMP="$(date +%Y%m%d_%H%M%S)"

RECOVERY_WORK="/workspaces/Photon-Camera/recover_failed_iris_26175_${STAMP}"
BACKUP_BRANCH="backup-before-recovering-failed-iris-26175-${STAMP}"

fail() {
    echo
    echo "============================================================"
    echo " IRIS 26175 RECOVERY STOPPED"
    echo "============================================================"
    echo "Reason: $1"
    exit 1
}

echo "============================================================"
echo " Iris Camera 26175 failed-state recovery and build continuation"
echo "============================================================"
echo

[ "$(git branch --show-current)" = "$EXPECTED_BRANCH" ] \
    || fail "Wrong branch"

[ "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" ] \
    || fail "Unexpected base HEAD"

grep -q '^VERSION_BUILD=26175$' app/version.properties \
    || fail "Expected the partial failed state with VERSION_BUILD=26175"

[ -d "$FAILED_WORK/before" ] \
    || fail "Missing original pre-26175 source backup: $FAILED_WORK/before"

[ -f "$FAILED_WORK/working-tree-before-26175.patch" ] \
    || fail "Missing original pre-26175 patch"

[ -f "$RESUME_SCRIPT" ] \
    || fail "Missing resume_build_iris_camera_26175.sh in the repository root"

bash -n "$RESUME_SCRIPT" \
    || fail "The corrected continuation script has invalid shell syntax"

mkdir -p "$RECOVERY_WORK"

echo "Protecting the current partial state before restoration..."

git branch "$BACKUP_BRANCH" HEAD
git diff --binary > "$RECOVERY_WORK/partial-working-tree-before-recovery.patch"
git diff --cached --binary > "$RECOVERY_WORK/partial-index-before-recovery.patch"
git status --short > "$RECOVERY_WORK/partial-status-before-recovery.txt"

cp app/version.properties "$RECOVERY_WORK/version-before-recovery.properties"

echo "Backup branch: $BACKUP_BRANCH"
echo "Partial patch: $RECOVERY_WORK/partial-working-tree-before-recovery.patch"
echo

echo "Restoring only the files saved before the failed Iris 26175 edit..."

cp -a "$FAILED_WORK/before/." /workspaces/Photon-Camera/

# Remove only resources introduced by the failed Iris branding/UI attempt.
rm -f \
    app/src/main/res/drawable/iris_outline_pill.xml \
    app/src/main/res/drawable/iris_outline_circle.xml \
    app/src/main/res/drawable/iris_lens_button_background.xml \
    app/src/main/res/color/iris_lens_text.xml

# Restore the previous launcher resources exactly when the original archive exists.
if [ -f "$FAILED_WORK/launcher-resources-before.tar.gz" ]; then
    tar -xzf "$FAILED_WORK/launcher-resources-before.tar.gz" -C /workspaces/Photon-Camera
fi

grep -q '^VERSION_BUILD=26174$' app/version.properties \
    || fail "Pre-failure VERSION_BUILD=26174 was not restored"

grep -Fq "applicationId 'com.particlesdevs.photoncamera'" app/build.gradle \
    || fail "Original applicationId was not restored"

grep -Fq '<string name="app_name" translatable="false">PhotonCamera</string>' \
    app/src/main/res/values/strings.xml \
    || fail "Original PhotonCamera label was not restored"

grep -Fq 'layout(r32f, binding = 4)' \
    app/src/main/assets/shaders/merge/motionmerge11.glsl \
    || fail "Protected HDRX R32F shader state was not preserved"

grep -Fq 'storageFormat=R32F' \
    app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts/PyramidMerging.java \
    || fail "Protected HDRX R32F Java state was not preserved"

git diff --check \
    || fail "Restored working tree failed git diff --check"

git diff --binary > "$RECOVERY_WORK/restored-pre-26175-working-tree.patch"
git status --short > "$RECOVERY_WORK/restored-pre-26175-status.txt"

echo
echo "Pre-failure 26174 state restored safely."
echo "Starting the corrected integrated Iris Camera 26175 build..."
echo

chmod +x "$RESUME_SCRIPT"
bash "$RESUME_SCRIPT"
