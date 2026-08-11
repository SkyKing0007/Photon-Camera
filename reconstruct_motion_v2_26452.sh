#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-mobile-26452-cfa-to-cfa"
BASE_26428_COMMIT="aac8ea5a0f518142b0f8ad60ce34c9a165e4611b"

fail() {
    echo "FAIL: $*" >&2
    exit 1
}

sha_upper() {
    sha256sum "$1" | awk '{print toupper($1)}'
}

echo "======================================================================"
echo "MOTION V2 26452 RECONSTRUCTION"
echo "26428 BASELINE SAFETY PROOF"
echo "======================================================================"

echo
echo "=== GATE 0A: BRANCH SAFETY ==="

CURRENT_BRANCH="$(git branch --show-current)"

if [[ "$CURRENT_BRANCH" != "$EXPECTED_BRANCH" ]]; then
    fail "Wrong branch: expected $EXPECTED_BRANCH, got $CURRENT_BRANCH"
fi

echo "PASS: working branch = $CURRENT_BRANCH"

echo
echo "=== GATE 0B: PROTECTED 26428 ANCESTOR ==="

if ! git merge-base --is-ancestor "$BASE_26428_COMMIT" HEAD; then
    fail "Canonical 26428 commit is not an ancestor of this branch"
fi

echo "PASS: canonical 26428 commit is preserved in branch ancestry"
echo "26428 commit: $BASE_26428_COMMIT"
echo "Current HEAD:  $(git rev-parse HEAD)"

echo
echo "=== GATE 0C: EXACT 26428 APPLICATION SOURCE ==="

declare -A EXPECTED_26428

EXPECTED_26428['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java']='B5CA7F93F1444B7F3C880F97D7E474B072F650273A7E9C4DB51764034C3A1F7D'
EXPECTED_26428['app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl']='A3DC78DC0FFF692D23EEC9909D29A053839DAA16F67E90A4E552B9DF5A8CF7B3'
EXPECTED_26428['app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl']='FE62CA5F04735EB2E2E6D7DB2E725431B2C8CB2D9A0B0482916FAA7569623002'
EXPECTED_26428['app/src/main/assets/shaders/motionv2/color_transform.glsl']='3C0DBE63E08D2E1347294921BED2717902B99390DB8A73E7DB9E88CC5681EF0A'
EXPECTED_26428['app/src/main/assets/shaders/motionv2/denoise.glsl']='5A939C709C181E61534233BECFABDE9C7C9A5A6296F3F362135832D03DC0FC0C'
EXPECTED_26428['app/version.properties']='1D245D59983CD65526C586BFE3A0A7FD12B9EAEDCDE87508A1215C938A6FBC2F'

for SOURCE_PATH in "${!EXPECTED_26428[@]}"; do
    [[ -f "$SOURCE_PATH" ]] || fail "Missing baseline file: $SOURCE_PATH"

    ACTUAL_HASH="$(sha_upper "$SOURCE_PATH")"
    EXPECTED_HASH="${EXPECTED_26428[$SOURCE_PATH]}"

    if [[ "$ACTUAL_HASH" != "$EXPECTED_HASH" ]]; then
        echo "File:     $SOURCE_PATH"
        echo "Expected: $EXPECTED_HASH"
        echo "Actual:   $ACTUAL_HASH"
        fail "26428 application-source hash mismatch"
    fi

    echo "PASS: $SOURCE_PATH"
done

grep -q '^VERSION_NAME=0\.9726428$' app/version.properties \
    || fail "Expected VERSION_NAME=0.9726428"

grep -q '^VERSION_BUILD=26428$' app/version.properties \
    || fail "Expected VERSION_BUILD=26428"

echo
echo "PASS: exact pushed 26428 application baseline proven"

echo
echo "=== GATE 0D: NO EXISTING APPLICATION CHANGES ==="

APP_DIFF="$(git diff "$BASE_26428_COMMIT" -- app || true)"

if [[ -n "$APP_DIFF" ]]; then
    echo "$APP_DIFF"
    fail "Application source differs from canonical 26428 before reconstruction"
fi

echo "PASS: app/ remains byte-identical to canonical 26428"

echo
echo "======================================================================"
echo "26428 BASELINE SAFETY PROOF PASSED"
echo "NO APPLICATION SOURCE MODIFIED"
echo "======================================================================"

echo
echo "=== GATE 1A: CREATE PRE-EDIT SAFETY PACKAGE ==="

SAFETY_DIR="motion_v2_26452_safety"
mkdir -p "$SAFETY_DIR"

PRE_EDIT_PATCH="$SAFETY_DIR/26452_pre_edit_app_vs_26428.patch"
PRE_EDIT_MANIFEST="$SAFETY_DIR/26452_pre_edit_app_sha256.txt"
PRE_EDIT_STATE="$SAFETY_DIR/26452_pre_edit_state.txt"

git diff --binary "$BASE_26428_COMMIT" -- app > "$PRE_EDIT_PATCH"

if [[ -s "$PRE_EDIT_PATCH" ]]; then
    echo "Unexpected application diff:"
    cat "$PRE_EDIT_PATCH"
    fail "Pre-edit application patch is not empty"
fi

echo "PASS: binary pre-edit patch created"
echo "PASS: application source has no pre-existing changes"

{
    echo "Motion V2 26452 pre-edit state"
    echo "================================"
    echo "branch=$(git branch --show-current)"
    echo "head=$(git rev-parse HEAD)"
    echo "base26428=$BASE_26428_COMMIT"
    echo
    echo "version.properties:"
    cat app/version.properties
    echo
    echo "git status:"
    git status --short
} > "$PRE_EDIT_STATE"

echo
echo "=== GATE 1B: HASH COMPLETE APPLICATION TREE ==="

find app \
    -type f \
    ! -path 'app/build/*' \
    ! -path '*/.gradle/*' \
    -print0 \
    | sort -z \
    | xargs -0 sha256sum \
    > "$PRE_EDIT_MANIFEST"

[[ -s "$PRE_EDIT_MANIFEST" ]] \
    || fail "Full pre-edit application hash manifest was not created"

HASHED_FILE_COUNT="$(wc -l < "$PRE_EDIT_MANIFEST" | tr -d ' ')"

if [[ "$HASHED_FILE_COUNT" -lt 100 ]]; then
    fail "Suspiciously small application hash manifest: $HASHED_FILE_COUNT files"
fi

echo "PASS: hashed $HASHED_FILE_COUNT application files"

echo
echo "=== GATE 1C: PROVE SAFETY FILES ARE OUTSIDE APPLICATION SOURCE ==="

for SAFETY_PATH in \
    "$PRE_EDIT_PATCH" \
    "$PRE_EDIT_MANIFEST" \
    "$PRE_EDIT_STATE"
do
    [[ -f "$SAFETY_PATH" ]] || fail "Missing safety file: $SAFETY_PATH"

    case "$SAFETY_PATH" in
        app/*)
            fail "Safety artifact was incorrectly created inside app/: $SAFETY_PATH"
            ;;
    esac

    echo "PASS: $SAFETY_PATH"
done

echo
echo "======================================================================"
echo "PRE-EDIT SAFETY PACKAGE PASSED"
echo "Backup branch already exists remotely:"
echo "  backup/github-26428-before-mobile-26452-20260811"
echo
echo "Binary pre-edit patch:"
echo "  $PRE_EDIT_PATCH"
echo
echo "Full application hash manifest:"
echo "  $PRE_EDIT_MANIFEST"
echo
echo "NO APPLICATION SOURCE MODIFIED"
echo "======================================================================"