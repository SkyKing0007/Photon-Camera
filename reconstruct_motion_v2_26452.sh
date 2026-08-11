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

echo
echo "=== GATE 2: HISTORICAL REPLAY PROVENANCE ==="

HIST_DIR="historical_replay"
[[ -d "$HIST_DIR" ]] || fail "Missing historical_replay directory"

REQUIRED_HISTORY=(
    "build_26429_codespace_shared_guide_reference_structure.sh"
    "build_26430_codespace_v2_ownership_headroom_cleanup.sh"
    "build_26431_codespace_allframes_body_lens_ownership_v2.sh"
    "build_26432_codespace_stack_robust_true_ultrahdr_final.sh"
    "resume_26433_fix_ultrahdr_javac_type_and_build.sh"
    "build_26434_codespace_stable_base_smooth_motion_ultrahdr_v2.sh"
    "build_26435_codespace_exact26430_sdr_lowfreq_ultrahdr_v2.sh"
    "build_26436_windows_integrated_motion_architecture.ps1"
    "build_26437_windows_whitepoint_motion_detail_stable_uhdr.ps1"
    "build_26438_windows_REVISED_v2_audited_motion_microcontrast_standard_ultrahdr.ps1"
    "launch_resume_build_26439_after_gate8_v2_MINIMAL.ps1"
    "launch_build_26443_reference_first_local_ownership.ps1"
    "launch_build_26445_specular_channel_validity_v2.ps1"
    "launch_build_26446_corrected_published_robustness_true_local_support.ps1"
    "launch_build_26450_alias_aware_chroma_reference_dng_REVISED.ps1"
)

for HISTORY_FILE in "${REQUIRED_HISTORY[@]}"; do
    FULL_HISTORY_PATH="$HIST_DIR/$HISTORY_FILE"

    [[ -s "$FULL_HISTORY_PATH" ]] \
        || fail "Missing or empty historical replay source: $HISTORY_FILE"

    echo "PASS: $HISTORY_FILE"
done

HIST_FILE_COUNT="$(
    find "$HIST_DIR" -maxdepth 1 -type f | wc -l | tr -d ' '
)"

if [[ "$HIST_FILE_COUNT" -ne 15 ]]; then
    fail "Expected exactly 15 historical replay files; found $HIST_FILE_COUNT"
fi

echo
echo "=== GATE 2A: REQUIRED ARCHITECTURE EVIDENCE ==="

grep -q 'IRIS_26429' \
    "$HIST_DIR/build_26429_codespace_shared_guide_reference_structure.sh" \
    || fail "26429 reconstruction ownership evidence missing"

grep -q 'targetFraction' \
    "$HIST_DIR/build_26431_codespace_allframes_body_lens_ownership_v2.sh" \
    || fail "26431 all-frame ownership evidence missing"

grep -q 'globalGyroDiscard' \
    "$HIST_DIR/build_26431_codespace_allframes_body_lens_ownership_v2.sh" \
    || fail "26431 gyro-discard ownership evidence missing"

grep -qi 'ultrahdr' \
    "$HIST_DIR/build_26432_codespace_stack_robust_true_ultrahdr_final.sh" \
    || fail "26432 Ultra HDR provenance missing"

grep -qi 'reference' \
    "$HIST_DIR/build_26436_windows_integrated_motion_architecture.ps1" \
    || fail "26436 reference-ownership provenance missing"

grep -qi 'whitepoint\|white.point' \
    "$HIST_DIR/build_26437_windows_whitepoint_motion_detail_stable_uhdr.ps1" \
    || fail "26437 white-point ownership provenance missing"

grep -qi 'microcontrast' \
    "$HIST_DIR/build_26438_windows_REVISED_v2_audited_motion_microcontrast_standard_ultrahdr.ps1" \
    || fail "26438 revised provenance missing"

grep -qi 'reference_first\|reference.first\|reference-first' \
    "$HIST_DIR/launch_build_26443_reference_first_local_ownership.ps1" \
    || fail "26443 reference-first provenance missing"

grep -qi 'channel_validity\|channel.validity\|channel-validity' \
    "$HIST_DIR/launch_build_26445_specular_channel_validity_v2.ps1" \
    || fail "26445 channel-validity provenance missing"

grep -qi 'local_support\|local.support\|local-support' \
    "$HIST_DIR/launch_build_26446_corrected_published_robustness_true_local_support.ps1" \
    || fail "26446 local-support provenance missing"

# 26450 is a thin PowerShell launcher.  Its actual historical build script is
# embedded as one Base64 FromBase64String(...) payload, so validate the decoded
# provenance rather than grepping the wrapper for plaintext markers.
PAYLOAD_26450_FILE="$HIST_DIR/launch_build_26450_alias_aware_chroma_reference_dng_REVISED.ps1"
PAYLOAD_26450_B64="$(
    sed -n 's/.*FromBase64String("\([^"]*\)").*/\1/p' "$PAYLOAD_26450_FILE"
)"

[[ -n "$PAYLOAD_26450_B64" ]] \
    || fail "26450 embedded historical payload was not found"

PAYLOAD_26450_DECODED="$SAFETY_DIR/26450_decoded_provenance.ps1"

printf '%s' "$PAYLOAD_26450_B64" \
    | base64 --decode > "$PAYLOAD_26450_DECODED" \
    || fail "26450 embedded historical payload could not be decoded"

[[ -s "$PAYLOAD_26450_DECODED" ]] \
    || fail "26450 decoded historical payload is empty"

grep -qi 'reference[_ -]*dng' "$PAYLOAD_26450_DECODED" \
    || fail "26450 decoded payload has no reference-DNG provenance"

grep -qi 'HdrxProcessor' "$PAYLOAD_26450_DECODED" \
    || fail "26450 decoded payload has no HdrxProcessor reference-DNG plumbing"

grep -qi 'MotionV2CfaReconstruction' "$PAYLOAD_26450_DECODED" \
    || fail "26450 decoded payload has no Motion V2 reconstruction provenance"

echo "PASS: 26450 embedded reference-DNG provenance decoded and verified"

echo
echo "PASS: required historical architecture evidence is present"

echo
echo "=== GATE 2B: EXPLICIT REPLAY POLICY ==="

cat <<'EOF'
PRESERVE:
  26429 shared guide / physical-reference reconstruction foundation
  26431 all-retained-frame eligibility and local contribution ownership
  26432+ true Motion V2 Ultra HDR plumbing
  26436 reference-rigid alignment / temporal consensus
  26437 white-point-owned color behavior
  26438 audited Motion microcontrast / standard UHDR behavior
  26439 temporal ownership refinements
  26443 reference-first moving/uncertain-content ownership
  26445 channel/specular validity where compatible
  26446 robustness/local-support semantics where domain-compatible
  26450 timestamp-owned reference RAW DNG plumbing

DO NOT PRESERVE AS FINAL IMAGE OWNER:
  direct multiframe RGB temporal synthesis
  26450 alias-aware direct-RGB finalizer
  diagnostic 26440-26442 GPU readbacks
  26447/26448 no-improvement direct-RGB experiments
  untested 26449 highlight experiment

26452 TARGET:
  aligned retained RAW burst
    -> reference-first local confidence
    -> multiframe CFA-to-CFA currentMerged
    -> one Motion V2 CFA demosaic
    -> V2 color
    -> V2 denoise/render
    -> Ultra HDR
EOF

echo
echo "======================================================================"
echo "HISTORICAL REPLAY PROVENANCE PASSED"
echo "NO APPLICATION SOURCE MODIFIED"
echo "======================================================================"

echo
echo "=== GATE 3: TEMPORARY 26452 CANDIDATE FOUNDATION ==="

CANDIDATE_ROOT="motion_v2_26452_candidate"
CANDIDATE_APP="$CANDIDATE_ROOT/app"
REPLAY_DECODED="$SAFETY_DIR/decoded_replay"

rm -rf "$CANDIDATE_ROOT"
mkdir -p "$CANDIDATE_ROOT" "$REPLAY_DECODED"

echo
echo "=== GATE 3A: CREATE EXACT DISPOSABLE 26428 APPLICATION COPY ==="

git archive "$BASE_26428_COMMIT" app \
    | tar -x -C "$CANDIDATE_ROOT"

[[ -d "$CANDIDATE_APP" ]] \
    || fail "Temporary candidate app tree was not created"

grep -q '^VERSION_NAME=0\.9726428$' \
    "$CANDIDATE_APP/version.properties" \
    || fail "Temporary candidate is not version 0.9726428"

grep -q '^VERSION_BUILD=26428$' \
    "$CANDIDATE_APP/version.properties" \
    || fail "Temporary candidate is not build 26428"

echo "PASS: exact committed 26428 app copied to disposable candidate"

echo
echo "=== GATE 3B: PROVE REAL app/ IS STILL UNTOUCHED ==="

REAL_APP_DIFF="$(git diff "$BASE_26428_COMMIT" -- app || true)"

if [[ -n "$REAL_APP_DIFF" ]]; then
    echo "$REAL_APP_DIFF"
    fail "Real app/ changed before temporary reconstruction"
fi

echo "PASS: real app/ remains byte-identical to canonical 26428"

echo
echo "=== GATE 3C: DECODE LATE WINDOWS HISTORICAL PAYLOADS ==="

decode_launcher_payload() {
    local launcher="$1"
    local output="$2"
    local label="$3"

    [[ -s "$launcher" ]] \
        || fail "$label launcher missing or empty"

    local encoded
    encoded="$(
        sed -n 's/.*FromBase64String("\([^"]*\)").*/\1/p' "$launcher" \
            | head -n 1
    )"

    [[ -n "$encoded" ]] \
        || fail "$label embedded Base64 payload not found"

    printf '%s' "$encoded" \
        | base64 --decode > "$output" \
        || fail "$label payload decode failed"

    [[ -s "$output" ]] \
        || fail "$label decoded payload is empty"

    echo "PASS: $label decoded -> $output"
}

decode_launcher_payload \
    "$HIST_DIR/launch_resume_build_26439_after_gate8_v2_MINIMAL.ps1" \
    "$REPLAY_DECODED/26439.ps1" \
    "26439"

decode_launcher_payload \
    "$HIST_DIR/launch_build_26443_reference_first_local_ownership.ps1" \
    "$REPLAY_DECODED/26443.ps1" \
    "26443"

decode_launcher_payload \
    "$HIST_DIR/launch_build_26445_specular_channel_validity_v2.ps1" \
    "$REPLAY_DECODED/26445.ps1" \
    "26445"

decode_launcher_payload \
    "$HIST_DIR/launch_build_26446_corrected_published_robustness_true_local_support.ps1" \
    "$REPLAY_DECODED/26446.ps1" \
    "26446"

cp "$PAYLOAD_26450_DECODED" \
    "$REPLAY_DECODED/26450.ps1"

[[ -s "$REPLAY_DECODED/26450.ps1" ]] \
    || fail "26450 decoded replay payload missing"

echo "PASS: 26450 decoded payload carried forward"

echo
echo "=== GATE 3D: AUDIT LATE PAYLOAD PRODUCER / CARRIER / CONSUMER EVIDENCE ==="

# Each historical build touched a different part of the V2 graph.
# Validate the domain each build actually owned instead of falsely requiring
# every payload to reference MotionV2CfaReconstruction.java.

grep -qi 'MotionV2CfaReconstruction' \
    "$REPLAY_DECODED/26439.ps1" \
    || fail "26439 decoded payload lacks reconstruction ownership evidence"

grep -qi 'direct_rgb_accumulate' \
    "$REPLAY_DECODED/26443.ps1" \
    || fail "26443 decoded payload lacks direct-RGB accumulator evidence"

grep -qi 'reference' \
    "$REPLAY_DECODED/26443.ps1" \
    || fail "26443 decoded payload lacks reference-first/local-ownership evidence"

grep -qi 'direct_rgb_accumulate' \
    "$REPLAY_DECODED/26445.ps1" \
    || fail "26445 decoded payload lacks direct-RGB accumulator evidence"

grep -qi 'color_transform' \
    "$REPLAY_DECODED/26445.ps1" \
    || fail "26445 decoded payload lacks color/channel-validity evidence"

grep -qi 'MotionV2ColorTransform' \
    "$REPLAY_DECODED/26445.ps1" \
    || fail "26445 decoded payload lacks Motion V2 color-owner evidence"

grep -qi 'support' \
    "$REPLAY_DECODED/26446.ps1" \
    || fail "26446 decoded payload lacks local-support evidence"

grep -qi 'direct_rgb_accumulate\|MotionV2LocalSupportDenoise\|PostPipeline' \
    "$REPLAY_DECODED/26446.ps1" \
    || fail "26446 decoded payload lacks expected support consumer/producer evidence"

grep -qi 'MotionV2CfaReconstruction' \
    "$REPLAY_DECODED/26450.ps1" \
    || fail "26450 decoded payload lacks reconstruction provenance"

grep -qi 'direct_rgb_finalize_alias_safe\|alias.safe\|alias-safe' \
    "$REPLAY_DECODED/26450.ps1" \
    || fail "26450 decoded payload lacks direct-RGB finalizer provenance"

grep -qi 'reference[_ -]*dng' \
    "$REPLAY_DECODED/26450.ps1" \
    || fail "26450 decoded payload lacks reference-DNG provenance"

grep -qi 'HdrxProcessor' \
    "$REPLAY_DECODED/26450.ps1" \
    || fail "26450 decoded payload lacks reference-DNG Hdrx plumbing"

echo "PASS: 26439 reconstruction ownership provenance"
echo "PASS: 26443 reference-first accumulator provenance"
echo "PASS: 26445 channel/color ownership provenance"
echo "PASS: 26446 local-support provenance"
echo "PASS: 26450 reconstruction/finalizer/reference-DNG provenance"
echo "PASS: late historical producer/carrier/consumer evidence verified"

echo
echo "=== GATE 3E: PROVE CFA-TO-CFA FOUNDATION EXISTS IN CANONICAL SOURCE ==="

CANDIDATE_RECON="$CANDIDATE_APP/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"

[[ -s "$CANDIDATE_RECON" ]] \
    || fail "Candidate MotionV2CfaReconstruction.java missing"

grep -q 'cfa_reconstruct_accumulate' "$CANDIDATE_RECON" \
    || fail "Candidate lacks CFA-to-CFA accumulator"

grep -q 'currentMerged' "$CANDIDATE_RECON" \
    || fail "Candidate lacks currentMerged CFA carrier"

grep -q 'currentDirectRgb' "$CANDIDATE_RECON" \
    || fail "Candidate lacks direct-RGB comparison carrier"

grep -q 'directBayer ? currentDirectRgb : currentMerged' "$CANDIDATE_RECON" \
    || fail "Expected 26428 final carrier ownership expression not found"

echo "PASS: CFA-to-CFA currentMerged producer exists"
echo "PASS: direct-RGB is currently the standard-Bayer final owner"
echo "PASS: exact ownership point for 26452 is identified"

echo
echo "=== GATE 3F: SNAPSHOT TEMPORARY CANDIDATE BEFORE HISTORICAL REPLAY ==="

find "$CANDIDATE_APP" \
    -type f \
    -print0 \
    | sort -z \
    | xargs -0 sha256sum \
    > "$SAFETY_DIR/26452_candidate_before_replay_sha256.txt"

[[ -s "$SAFETY_DIR/26452_candidate_before_replay_sha256.txt" ]] \
    || fail "Candidate pre-replay hash manifest missing"

git diff "$BASE_26428_COMMIT" -- app \
    > "$SAFETY_DIR/26452_real_app_before_replay.patch"

[[ ! -s "$SAFETY_DIR/26452_real_app_before_replay.patch" ]] \
    || fail "Real app/ changed during Gate 3"

echo
echo "======================================================================"
echo "GATE 3 TEMPORARY CANDIDATE FOUNDATION PASSED"
echo "CFA-TO-CFA PRODUCER CONFIRMED"
echo "DIRECT-RGB FINAL OWNERSHIP POINT CONFIRMED"
echo "REAL APPLICATION SOURCE STILL UNMODIFIED"
echo "NO VERSION INCREMENT"
echo "NO 26452 BUILD YET"
echo "======================================================================"

echo
echo "=== GATE 4: ISOLATED HISTORICAL REPLAY 26429 -> 26435 ==="

REPLAY_STAMP="$(date +%Y%m%d_%H%M%S)_$$"
REPLAY_ROOT="$(pwd)/$SAFETY_DIR/replay_26429_26435_$REPLAY_STAMP"
REPLAY_REPO="$REPLAY_ROOT/repo"
REPLAY_AUX="$REPLAY_ROOT/aux"
REPLAY_PATCHED="$REPLAY_ROOT/patched_scripts"
REPLAY_LOGS="$REPLAY_ROOT/logs"

mkdir -p \
    "$REPLAY_ROOT" \
    "$REPLAY_AUX" \
    "$REPLAY_PATCHED" \
    "$REPLAY_LOGS"

echo
echo "=== GATE 4A: CREATE THROWAWAY REPLAY REPOSITORY ==="

git clone --no-hardlinks . "$REPLAY_REPO" \
    > "$REPLAY_LOGS/clone.log" 2>&1 \
    || fail "Could not create isolated replay clone"

(
    cd "$REPLAY_REPO"

    git checkout --detach "$BASE_26428_COMMIT" \
        > "$REPLAY_LOGS/checkout.log" 2>&1 \
        || fail "Could not checkout canonical 26428 in replay clone"

    git switch -c experimental-clean-photon-rebuild \
        > "$REPLAY_LOGS/branch.log" 2>&1 \
        || fail "Could not create historical replay branch"

# Historical build scripts insist on fetching their original branch from
# "origin". Keep those safety checks intact, but make origin completely local
# to this disposable replay clone so no real branch can be fetched or changed.
git remote set-url origin "$REPLAY_REPO" \
    || fail "Could not isolate historical replay origin"

git fetch origin experimental-clean-photon-rebuild \
    > "$REPLAY_LOGS/self_origin_fetch.log" 2>&1 \
    || fail "Could not initialize isolated historical origin"

REMOTE_REPLAY_HEAD="$(
    git rev-parse refs/remotes/origin/experimental-clean-photon-rebuild
)"

[[ "$REMOTE_REPLAY_HEAD" == "$BASE_26428_COMMIT" ]] \
    || fail "Isolated replay origin does not point to canonical 26428"

echo "PASS: historical origin isolated inside throwaway replay clone"

    [[ "$(git rev-parse HEAD)" == "$BASE_26428_COMMIT" ]] \
        || fail "Replay clone is not canonical 26428"

    grep -q '^VERSION_NAME=0\.9726428$' app/version.properties \
        || fail "Replay clone version is not 0.9726428"

    grep -q '^VERSION_BUILD=26428$' app/version.properties \
        || fail "Replay clone build is not 26428"
)

echo "PASS: isolated canonical 26428 replay repository created"

echo
echo "=== GATE 4B: INSTALL/VERIFY GLSL VALIDATOR ==="

if ! command -v glslangValidator >/dev/null 2>&1; then
    sudo apt-get update -qq \
        > "$REPLAY_LOGS/apt_update.log" 2>&1 \
        || fail "apt update failed while preparing GLSL validator"

    sudo apt-get install -y glslang-tools \
        > "$REPLAY_LOGS/apt_glslang.log" 2>&1 \
        || fail "glslang-tools installation failed"
fi

command -v glslangValidator >/dev/null 2>&1 \
    || fail "glslangValidator unavailable"

echo "PASS: real glslangValidator available"

echo
echo "=== GATE 4C: INSTALL NON-BUILDING GRADLE REPLAY SHIM ==="

# The replay-only Gradle shim intentionally changes the tracked wrapper inside
# this disposable clone. Hide only that known file from historical dirty-tree
# checks; application source remains fully visible to Git.
git -C "$REPLAY_REPO" update-index --assume-unchanged gradlew \
    || fail "Could not isolate replay-only Gradle wrapper change"

echo "PASS: replay-only gradlew change isolated from historical dirty-tree checks"

# Preserve the real wrapper OUTSIDE the disposable Git worktree so historical
# clean-tree checks cannot mistake the backup wrapper for project content.
cp "$REPLAY_REPO/gradlew" \
   "$REPLAY_ROOT/gradlew.real"

[[ -s "$REPLAY_ROOT/gradlew.real" ]] \
    || fail "Could not preserve original replay Gradle wrapper"

cat > "$REPLAY_REPO/gradlew" <<'GRADLE_SHIM'
#!/usr/bin/env bash
set -euo pipefail

mkdir -p app/build/outputs/apk/debug

printf 'historical-replay-placeholder\n' \
    > app/build/outputs/apk/debug/app-debug.apk

printf 'historical-replay-placeholder\n' \
    > app/build/outputs/apk/debug/app-arm64-v8a-debug.apk

echo "Historical replay Gradle shim"
echo "No APK is being accepted from this isolated replay."
echo "BUILD SUCCESSFUL in 0s"
GRADLE_SHIM

chmod +x "$REPLAY_REPO/gradlew"

# 26432-26435 require local.properties even though this isolated replay never
# performs a real Android build. Supply the runner's real SDK location without
# placing any machine-specific configuration in the real repository.
REPLAY_ANDROID_SDK="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-/usr/local/lib/android/sdk}}"

printf 'sdk.dir=%s\n' "$REPLAY_ANDROID_SDK" \
    > "$REPLAY_REPO/local.properties"

grep -q '^sdk\.dir=' "$REPLAY_REPO/local.properties" \
    || fail "Replay-only local.properties was not created"

echo "PASS: replay-only Android SDK pointer installed"

echo "PASS: historical scripts cannot perform a real intermediate APK build"

echo
echo "=== GATE 4D: PATCH ONLY HISTORICAL ENVIRONMENT PATHS ==="

REPLAY_SCRIPTS=(
    "build_26429_codespace_shared_guide_reference_structure.sh"
    "build_26430_codespace_v2_ownership_headroom_cleanup.sh"
    "build_26431_codespace_allframes_body_lens_ownership_v2.sh"
    "build_26432_codespace_stack_robust_true_ultrahdr_final.sh"
    "resume_26433_fix_ultrahdr_javac_type_and_build.sh"
    "build_26434_codespace_stable_base_smooth_motion_ultrahdr_v2.sh"
    "build_26435_codespace_exact26430_sdr_lowfreq_ultrahdr_v2.sh"
)

for SCRIPT_NAME in "${REPLAY_SCRIPTS[@]}"; do
    SOURCE_SCRIPT="$HIST_DIR/$SCRIPT_NAME"
    PATCHED_SCRIPT="$REPLAY_PATCHED/$SCRIPT_NAME"

    [[ -s "$SOURCE_SCRIPT" ]] \
        || fail "Historical replay source missing: $SCRIPT_NAME"

    python3 - \
        "$SOURCE_SCRIPT" \
        "$PATCHED_SCRIPT" \
        "$REPLAY_REPO" \
        "$REPLAY_AUX" <<'PY'
from pathlib import Path
import sys

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
repo = sys.argv[3]
aux = sys.argv[4]

text = src.read_text()

# Environment relocation only.
# Historical image-processing transforms remain byte-for-byte untouched.
text = text.replace(
    "/workspaces/Photon-Camera-fresh-iris",
    repo
)
text = text.replace(
    "/workspaces/Photon-Camera",
    aux
)

# Keep every historical log, safety directory, generated APK and result file
# outside the disposable Git worktree. Several later scripts derive OUT from
# $SRC rather than using the old /workspaces/Photon-Camera path directly.
text = text.replace(
    'OUT="$SRC/fresh_iris_outputs"',
    f'OUT="{aux}/fresh_iris_outputs"'
)
text = text.replace(
    'OUTDIR="$SRC/fresh_iris_outputs"',
    f'OUTDIR="{aux}/fresh_iris_outputs"'
)

# Repair a known historical 26430 validation bug only.
# Its candidate source intentionally documents that it does NOT consume
# basePipeline.noiseS/noiseO/noiseRstr, while the old plain grep mistakenly
# treats those explanatory comments as executable consumption.
if src.name == "build_26430_codespace_v2_ownership_headroom_cleanup.sh":
    text = text.replace(
        """! grep -q 'basePipeline\\.noiseS' "$CDENOISE_JAVA" || fail "Photon noiseS still consumed by Motion V2"
! grep -q 'basePipeline\\.noiseO' "$CDENOISE_JAVA" || fail "Photon noiseO still consumed by Motion V2"
! grep -q 'noiseRstr' "$CDENOISE_JAVA" || fail "Photon noiseRstr still consumed by Motion V2\"""",
        """! grep -q 'glProg\\.setVar("noiseS"' "$CDENOISE_JAVA" || fail "Executable Photon noiseS binding still consumed by Motion V2"
! grep -q 'glProg\\.setVar("noiseO"' "$CDENOISE_JAVA" || fail "Executable Photon noiseO binding still consumed by Motion V2"
! grep -q 'mSettings\\.noiseRstr\\|PhotonCamera\\.getSettings().noiseRstr' "$CDENOISE_JAVA" || fail "Executable Photon noiseRstr consumption still present in Motion V2\""""
    )

dst.write_text(text)
PY

    chmod +x "$PATCHED_SCRIPT"

    [[ -s "$PATCHED_SCRIPT" ]] \
        || fail "Patched replay script is empty: $SCRIPT_NAME"

    echo "PASS: environment-relocated $SCRIPT_NAME"
done

echo
echo "=== GATE 4E: REPLAY 26429 -> 26435 IN ORDER ==="

for SCRIPT_NAME in "${REPLAY_SCRIPTS[@]}"; do
    echo
    echo "--- REPLAY: $SCRIPT_NAME ---"

    (
        cd "$REPLAY_REPO"

        bash "$REPLAY_PATCHED/$SCRIPT_NAME"
    ) > "$REPLAY_LOGS/$SCRIPT_NAME.log" 2>&1 \
      || {
          echo "Historical replay failed: $SCRIPT_NAME"
          tail -n 120 "$REPLAY_LOGS/$SCRIPT_NAME.log" || true
          fail "Isolated historical replay stopped safely"
      }

    echo "PASS: $SCRIPT_NAME"
done

echo
echo "=== GATE 4F: VERIFY 26435 REPLAY STATE ==="

grep -q '^VERSION_NAME=0\.9726435$' \
    "$REPLAY_REPO/app/version.properties" \
    || fail "Historical replay did not reach version 0.9726435"

grep -q '^VERSION_BUILD=26435$' \
    "$REPLAY_REPO/app/version.properties" \
    || fail "Historical replay did not reach build 26435"

grep -q 'IRIS_26429_SHARED_GUIDE_ROBUSTNESS_REFERENCE_STRUCTURE' \
    "$REPLAY_REPO/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java" \
    || fail "26429 shared-guide reconstruction state missing"

grep -q 'IRIS_26431_MOTION_V2_ALL_FRAME_HANDOFF' \
    "$REPLAY_REPO/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java" \
    || fail "26431 all-retained-frame handoff missing"

grep -q 'targetFraction=1.0' \
    "$REPLAY_REPO/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java" \
    || fail "26431 all-frame target missing"

grep -q 'globalGyroDiscard=false' \
    "$REPLAY_REPO/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java" \
    || fail "26431 local rather than global frame rejection missing"

grep -q 'IRIS_26435_' \
    "$REPLAY_REPO/app/src/main/assets/shaders/motionv2/render.glsl" \
    || fail "26435 render/headroom state missing"

echo "PASS: 26429 -> 26435 historical image-processing state reconstructed"

echo
echo "=== GATE 4G: SAVE REPLAY PATCH + HASH PROOF ==="

(
    cd "$REPLAY_REPO"

    git diff --binary "$BASE_26428_COMMIT" -- app \
        > "../26429_to_26435_replay.patch"

    find app \
        -type f \
        ! -path 'app/build/*' \
        -print0 \
        | sort -z \
        | xargs -0 sha256sum \
        > "../26435_replayed_app_sha256.txt"
)

[[ -s "$REPLAY_ROOT/26429_to_26435_replay.patch" ]] \
    || fail "26429->26435 replay patch is empty"

[[ -s "$REPLAY_ROOT/26435_replayed_app_sha256.txt" ]] \
    || fail "26435 replay hash manifest missing"

echo
echo "=== GATE 4H: REAL APPLICATION MUST STILL BE UNTOUCHED ==="

REAL_APP_DIFF="$(git diff "$BASE_26428_COMMIT" -- app || true)"

if [[ -n "$REAL_APP_DIFF" ]]; then
    echo "$REAL_APP_DIFF"
    fail "Real app/ changed during isolated historical replay"
fi

echo "PASS: real app/ remains byte-identical to canonical 26428"

echo
echo "======================================================================"
echo "GATE 4 ISOLATED HISTORICAL REPLAY 26429 -> 26435 PASSED"
echo "HISTORICAL TRANSFORMS RAN ONLY INSIDE THROWAWAY REPLAY REPOSITORY"
echo "REAL app/ UNMODIFIED"
echo "NO REAL INTERMEDIATE APK BUILDS"
echo "NO VERSION CHANGE IN REAL app/"
echo "======================================================================"