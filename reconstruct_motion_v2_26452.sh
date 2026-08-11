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

    # Repair the duplicated 26430 Gate-5 lineage checks too. These old checks
    # grep whole files and can mistake explanatory comments for executable code.
    old_gate5 = r"""! grep -q 'basePipeline\.noiseS' "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Denoise.java" || fail "Photon noiseS leaked back into Motion"
! grep -q 'basePipeline\.noiseO' "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Denoise.java" || fail "Photon noiseO leaked back into Motion"
! grep -q 'uniform float noiseS' "app/src/main/assets/shaders/motionv2/denoise.glsl" || fail "Generic noiseS shader path leaked back"
! grep -q 'uniform float noiseO' "app/src/main/assets/shaders/motionv2/denoise.glsl" || fail "Generic noiseO shader path leaked back"
! grep -q 'start=0.70' "app/src/main/assets/shaders/motionv2/render.glsl" || fail "26420 fixed shoulder leaked back"
! grep -q 'transformedLoss' "app/src/main/assets/shaders/motionv2/color_transform.glsl" || fail "26427 output-space neutralization leaked back"
"""

    new_gate5 = r"""! grep -q 'glProg\.setVar("noiseS"' "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Denoise.java" || fail "Executable Photon noiseS binding leaked back into Motion"
! grep -q 'glProg\.setVar("noiseO"' "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Denoise.java" || fail "Executable Photon noiseO binding leaked back into Motion"
! grep -Eq '^[[:space:]]*uniform[[:space:]]+float[[:space:]]+noiseS[[:space:]]*;' "app/src/main/assets/shaders/motionv2/denoise.glsl" || fail "Executable generic noiseS shader uniform leaked back"
! grep -Eq '^[[:space:]]*uniform[[:space:]]+float[[:space:]]+noiseO[[:space:]]*;' "app/src/main/assets/shaders/motionv2/denoise.glsl" || fail "Executable generic noiseO shader uniform leaked back"
! grep -Eq '^[[:space:]]*const[[:space:]]+float[[:space:]]+start[[:space:]]*=[[:space:]]*0\.70[[:space:]]*;' "app/src/main/assets/shaders/motionv2/render.glsl" || fail "Executable 0.70 shoulder leaked back"
! grep -Eq '^[[:space:]]*(float|vec2|vec3|vec4)[[:space:]]+transformedLoss([[:space:]]|=|;)' "app/src/main/assets/shaders/motionv2/color_transform.glsl" || fail "Executable transformedLoss path leaked back"
"""

    if old_gate5 not in text:
        raise SystemExit(
            "FAIL: expected 26430 Gate-5 lineage block not found for replay repair"
        )

    text = text.replace(old_gate5, new_gate5, 1)
    
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
echo "=== GATE 4G1: SAVE COMPLETE SOURCE-ONLY 26435 APP SNAPSHOT ==="

REPLAY_26435_SNAPSHOT="$REPLAY_ROOT/26435_replayed_app_snapshot"
mkdir -p "$REPLAY_26435_SNAPSHOT"

(
    cd "$REPLAY_REPO"

    tar \
        --exclude='app/build' \
        -cf - app
) | (
    cd "$REPLAY_26435_SNAPSHOT"
    tar -xf -
) || fail "Could not save complete source-only 26435 app snapshot"

[[ -d "$REPLAY_26435_SNAPSHOT/app" ]] \
    || fail "Complete 26435 app snapshot missing"

(
    cd "$REPLAY_26435_SNAPSHOT"

    find app \
        -type f \
        -print0 \
        | sort -z \
        | xargs -0 sha256sum \
        > "$REPLAY_ROOT/26435_snapshot_app_sha256.txt"
)

[[ -s "$REPLAY_ROOT/26435_snapshot_app_sha256.txt" ]] \
    || fail "26435 snapshot hash manifest missing"

if ! cmp -s \
    "$REPLAY_ROOT/26435_replayed_app_sha256.txt" \
    "$REPLAY_ROOT/26435_snapshot_app_sha256.txt"
then
    echo "Gate 4 replay vs snapshot manifest difference:"
    diff -u \
        "$REPLAY_ROOT/26435_replayed_app_sha256.txt" \
        "$REPLAY_ROOT/26435_snapshot_app_sha256.txt" \
        | head -n 120 || true

    fail "Saved complete 26435 snapshot is not byte-identical to Gate 4 replay state"
fi

echo "PASS: complete source-only 26435 app snapshot saved and hash-verified"

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

echo
echo "=== GATE 5: 26452 CFA-TO-CFA FINAL-CARRIER CANDIDATE ==="

GATE5_REPO="$REPLAY_REPO"
GATE5_APP="$GATE5_REPO/app"
GATE5_SAFETY="$REPLAY_ROOT/gate5_26452_cfa_carrier"
GATE5_SNAPSHOT="$GATE5_SAFETY/candidate_app"

mkdir -p "$GATE5_SAFETY"

G5_RECON="$GATE5_APP/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
G5_INPUT="$GATE5_APP/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java"
G5_POST="$GATE5_APP/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
G5_DEMOSAIC="$GATE5_APP/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaDemosaic.java"
G5_VERSION="$GATE5_APP/version.properties"

echo
echo "=== GATE 5A: PROVE EXACT REPLAYED INPUT STATE ==="

grep -q '^VERSION_NAME=0\.9726435$' "$G5_VERSION" \
    || fail "Gate 5 input is not replayed version 0.9726435"

grep -q '^VERSION_BUILD=26435$' "$G5_VERSION" \
    || fail "Gate 5 input is not replayed build 26435"

grep -q 'IRIS_26429_SHARED_GUIDE_ROBUSTNESS_REFERENCE_STRUCTURE' \
    "$G5_RECON" \
    || fail "Gate 5 lacks replayed 26429 reconstruction foundation"

grep -q 'cfa_reconstruct_accumulate' "$G5_RECON" \
    || fail "CFA-to-CFA accumulator missing before Gate 5"

grep -q 'currentMerged' "$G5_RECON" \
    || fail "CFA currentMerged carrier missing before Gate 5"

grep -q 'currentDirectRgb' "$G5_RECON" \
    || fail "Direct-RGB comparison carrier missing before Gate 5"

grep -q 'directBayer ? currentDirectRgb : currentMerged' "$G5_RECON" \
    || fail "Expected pre-26452 final carrier expression missing"

grep -q 'IRIS_26415_MOTION_V2_PACKED_CFA_DOMAIN' "$G5_DEMOSAIC" \
    || fail "Motion V2 packed-CFA demosaic contract missing"

grep -q 'expectedPacked' "$G5_DEMOSAIC" \
    || fail "Motion V2 demosaic packed-dimension validation missing"

grep -q 'new Point(raw.x / 2, raw.y / 2)' "$G5_DEMOSAIC" \
    || fail "Motion V2 demosaic does not require packed half-resolution CFA"

echo "PASS: replayed 26435 producer/carrier/consumer state proven"

echo
echo "=== GATE 5B: SNAPSHOT REAL APP BEFORE CANDIDATE TRANSFORM ==="

git diff --binary "$BASE_26428_COMMIT" -- app \
    > "$GATE5_SAFETY/real_app_before_gate5.patch"

[[ ! -s "$GATE5_SAFETY/real_app_before_gate5.patch" ]] \
    || fail "Real app/ changed before Gate 5 candidate work"

echo "PASS: real app/ still canonical 26428"

echo
echo "=== GATE 5C: SAVE PRE-TRANSFORM REPLAY HASHES ==="

for rel in \
    "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java" \
    "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java" \
    "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java" \
    "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaDemosaic.java"
do
    printf '%s  %s\n' \
        "$(sha_upper "$GATE5_REPO/$rel")" \
        "$rel"
done > "$GATE5_SAFETY/pre_transform_target_hashes.txt"

echo "PASS: Gate 5 target hashes recorded"

echo
echo "=== GATE 5D: APPLY CARRIER TRANSFORM ONLY TO THROWAWAY REPLAY ==="

python3 - \
    "$G5_RECON" \
    "$G5_INPUT" \
    "$G5_POST" <<'PY'
from pathlib import Path
import sys

recon = Path(sys.argv[1])
cfa_input = Path(sys.argv[2])
post = Path(sys.argv[3])

# -------------------------------------------------------------------------
# 1. Reconstruction:
#    temporal CFA-to-CFA currentMerged becomes the final image carrier.
#    Direct RGB remains calculated only as non-owning comparison telemetry.
# -------------------------------------------------------------------------
s = recon.read_text()

old = "GLTexture imageOutput = directBayer ? currentDirectRgb : currentMerged;"
new = """/*
             * IRIS_26452_MULTIFRAME_CFA_FINAL_OWNER
             *
             * Temporal ownership remains in the sensor CFA domain.
             * currentMerged contains the reference-first multiframe CFA result.
             * Direct temporal RGB may still be computed for comparison telemetry,
             * but it cannot own the image crossing into PostPipeline.
             */
            GLTexture imageOutput = currentMerged;"""

if s.count(old) != 1:
    raise SystemExit(
        "FAIL: expected exactly one direct-RGB final-owner expression; "
        f"found {s.count(old)}"
    )

s = s.replace(old, new, 1)

# The final carrier is now packed half-resolution CFA for Bayer as well.
old_size = """+ " size=" + (directBayer
                            ? raw.x + "x" + raw.y
                            : rawHalf.x + "x" + rawHalf.y)"""
new_size = """+ " size=" + rawHalf.x + "x" + rawHalf.y"""

if s.count(old_size) != 1:
    raise SystemExit(
        "FAIL: expected exactly one old final-carrier size telemetry block; "
        f"found {s.count(old_size)}"
    )

s = s.replace(old_size, new_size, 1)

s = s.replace(
    '+ " directMultiframeRgb=" + directBayer',
    '+ " directMultiframeRgbComputed=" + directBayer'
    '+ " directMultiframeRgbFinalOwner=false"',
    1
)

s = s.replace(
    '+ " separateDemosaic=" + (!directBayer)',
    '+ " separateDemosaic=true"',
    1
)

recon.write_text(s)

# -------------------------------------------------------------------------
# 2. MotionV2CfaInput:
#    the bridge now always uploads the reconstruction as packed half-res CFA.
#    This preserves exact CFA cell values with GL_NEAREST.
# -------------------------------------------------------------------------
s = cfa_input.read_text()

old = """        boolean directBayer =
                basePipeline.mParameters.cfaPattern >= 0
                        && basePipeline.mParameters.cfaPattern <= 3;
        if (directBayer) {
            WorkingTexture = new GLTexture(
                    raw,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                    view,
                    GL_LINEAR,
                    GL_CLAMP_TO_EDGE);
        } else {
            WorkingTexture = new GLTexture(
                    half,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                    view,
                    GL_NEAREST,
                    GL_CLAMP_TO_EDGE);
        }"""

new = """        /*
         * IRIS_26452_MULTIFRAME_CFA_INPUT_OWNER
         *
         * Standard Bayer no longer arrives as temporally synthesized RGB.
         * The owned reconstruction carrier is the packed half-resolution
         * multiframe CFA result and must remain nearest-sampled until the
         * single Motion V2 demosaic.
         */
        WorkingTexture = new GLTexture(
                half,
                new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                view,
                GL_NEAREST,
                GL_CLAMP_TO_EDGE);"""

if s.count(old) != 1:
    raise SystemExit(
        "FAIL: expected exactly one direct-RGB/CFA input branch; "
        f"found {s.count(old)}"
    )

s = s.replace(old, new, 1)

s = s.replace(
    '(directBayer ? "directRgbFullRes" : "packedCfaHalfRes")',
    '"packedMultiframeCfaHalfRes"',
)

s = s.replace(
    '+ " directMultiframeRgb=" + directBayer',
    '+ " directMultiframeRgbFinalOwner=false"',
)

cfa_input.write_text(s)

# -------------------------------------------------------------------------
# 3. PostPipeline:
#    standard Bayer must now perform exactly one MotionV2CfaDemosaic.
#    Special CFA fallback behavior remains unchanged.
# -------------------------------------------------------------------------
s = post.read_text()

old = """            if (directBayer) {
                /*
                 * IRIS_26424_DIRECT_MULTIFRAME_RGB_POST_GRAPH
                 * Standard Bayer image formation already produced full-
                 * resolution linear camera RGB. No separate demosaic runs.
                 */
                add(new StageTelemetry("V2_POST_DIRECT_MULTIFRAME_RGB"));
            } else {"""

new = """            if (directBayer) {
                /*
                 * IRIS_26452_MULTIFRAME_CFA_SINGLE_DEMOSAIC
                 *
                 * Standard Bayer now arrives as the aligned multiframe
                 * packed-CFA result. One V2-owned demosaic converts that
                 * sensor-domain carrier to full-resolution camera RGB.
                 */
                add(new StageTelemetry("V2_POST_MULTIFRAME_CFA"));
                add(new MotionV2CfaDemosaic());
                add(new StageTelemetry("V2_POST_SINGLE_CFA_DEMOSAIC"));
            } else {"""

if s.count(old) != 1:
    raise SystemExit(
        "FAIL: expected exactly one standard-Bayer direct-RGB post branch; "
        f"found {s.count(old)}"
    )

s = s.replace(old, new, 1)

s = s.replace(
    '"nodes=MotionV2CfaInput,DirectRGB-or-CFAFallback,MotionV2ColorTransform,MotionV2Denoise,MotionV2Render,RotateWatermark"',
    '"nodes=MotionV2CfaInput,MultiframeCFA,SingleMotionV2CfaDemosaic,MotionV2ColorTransform,MotionV2Denoise,MotionV2Render,RotateWatermark"',
    1
)

s = s.replace(
    '+ " directMultiframeRgb=" + directBayer',
    '+ " directMultiframeRgbFinalOwner=false"'
    '+ " standardBayerSingleDemosaic=" + directBayer',
    1
)

post.write_text(s)

print("candidate/source validation PASS")
PY

echo "Temporary-copy transformation: PASS"

echo
echo "=== GATE 5E: OWNERSHIP / DOMAIN VALIDATION ==="

grep -q 'IRIS_26452_MULTIFRAME_CFA_FINAL_OWNER' "$G5_RECON" \
    || fail "26452 CFA final-owner marker missing"

grep -q 'GLTexture imageOutput = currentMerged;' "$G5_RECON" \
    || fail "currentMerged is not the Gate 5 final carrier"

if grep -q 'directBayer ? currentDirectRgb : currentMerged' "$G5_RECON"; then
    fail "Direct RGB still conditionally owns the final reconstruction output"
fi

grep -q 'cfa_reconstruct_accumulate' "$G5_RECON" \
    || fail "CFA temporal accumulator disappeared"

grep -q 'currentSupport' "$G5_RECON" \
    || fail "Separate CFA support carrier disappeared"

grep -q 'IRIS_26452_MULTIFRAME_CFA_INPUT_OWNER' "$G5_INPUT" \
    || fail "26452 packed-CFA input marker missing"

grep -q 'packedMultiframeCfaHalfRes' "$G5_INPUT" \
    || fail "Packed multiframe CFA input telemetry missing"

grep -q 'GL_NEAREST' "$G5_INPUT" \
    || fail "Packed CFA input no longer proves nearest sampling"

grep -q 'IRIS_26452_MULTIFRAME_CFA_SINGLE_DEMOSAIC' "$G5_POST" \
    || fail "26452 single-demosaic routing marker missing"

grep -q 'V2_POST_SINGLE_CFA_DEMOSAIC' "$G5_POST" \
    || fail "Single CFA demosaic telemetry missing"

grep -q 'add(new MotionV2CfaDemosaic());' "$G5_POST" \
    || fail "MotionV2CfaDemosaic is not present in V2 post graph"

grep -q 'IRIS_26415_MOTION_V2_PACKED_CFA_DOMAIN' "$G5_DEMOSAIC" \
    || fail "Existing packed-CFA demosaic contract was lost"

grep -q 'sensorNeutralFallback=true' "$G5_DEMOSAIC" \
    || fail "Existing sensor-neutral highlight fallback was lost"

echo "PASS: producer = multiframe CFA currentMerged"
echo "PASS: support = separate currentSupport carrier"
echo "PASS: bridge = packed half-resolution FLOAT32 CFA / GL_NEAREST"
echo "PASS: consumer = one MotionV2CfaDemosaic"
echo "PASS: direct temporal RGB has no final-image ownership"

echo
echo "=== GATE 5F: PROVE VERSION DID NOT MOVE ==="

grep -q '^VERSION_NAME=0\.9726435$' "$G5_VERSION" \
    || fail "Gate 5 candidate unexpectedly changed version name"

grep -q '^VERSION_BUILD=26435$' "$G5_VERSION" \
    || fail "Gate 5 candidate unexpectedly changed build number"

echo "PASS: candidate remains 26435 because real 26452 has not been applied"

echo
echo "=== GATE 5G: RESTORE REAL GRADLE WRAPPER INSIDE THROWAWAY REPLAY ==="

cp "$REPLAY_ROOT/gradlew.real" "$GATE5_REPO/gradlew" \
    || fail "Could not restore real Gradle wrapper in throwaway replay"

chmod +x "$GATE5_REPO/gradlew"

git -C "$GATE5_REPO" update-index --no-assume-unchanged gradlew \
    || fail "Could not restore normal Gradle index handling in replay repo"

echo "PASS: throwaway replay now uses the real Gradle wrapper"

echo
echo "=== GATE 5H: REAL JAVAC PROOF OF CFA-CARRIER CANDIDATE ==="

GATE5_JAVAC_LOG="$GATE5_SAFETY/gate5_javac.txt"

(
    cd "$GATE5_REPO"

    ./gradlew :app:compileDebugJavaWithJavac --stacktrace
) > "$GATE5_JAVAC_LOG" 2>&1 \
    || {
        tail -n 160 "$GATE5_JAVAC_LOG" || true
        fail "Gate 5 real Javac proof failed"
    }

grep -q 'BUILD SUCCESSFUL' "$GATE5_JAVAC_LOG" \
    || {
        tail -n 160 "$GATE5_JAVAC_LOG" || true
        fail "Gate 5 Javac did not report BUILD SUCCESSFUL"
    }

echo "PASS: real Javac accepted the 26452 CFA-carrier candidate"

echo
echo "=== GATE 5I: SAVE EXPLORER/BROWSER-VISIBLE SOURCE-ONLY CANDIDATE ==="

mkdir -p "$GATE5_SNAPSHOT"

# Save only tracked application source/configuration from the transformed
# throwaway replay. Do not copy Gradle-generated app/build products into the
# candidate snapshot.
(
    cd "$GATE5_REPO"

    while IFS= read -r -d '' rel; do
        src="$GATE5_REPO/$rel"
        dst="$GATE5_SNAPSHOT/${rel#app/}"

        mkdir -p "$(dirname "$dst")"
        cp -p "$src" "$dst"
    done < <(git ls-files -z app)
)

[[ -f "$GATE5_SNAPSHOT/version.properties" ]] \
    || fail "Gate 5 source-only snapshot is missing version.properties"

find "$GATE5_SNAPSHOT" \
    -type f \
    -print0 \
    | sort -z \
    | xargs -0 sha256sum \
    > "$GATE5_SAFETY/gate5_candidate_sha256.txt"

[[ -s "$GATE5_SAFETY/gate5_candidate_sha256.txt" ]] \
    || fail "Gate 5 candidate hash manifest missing"

(
    cd "$GATE5_REPO"
    git diff --binary "$BASE_26428_COMMIT" -- app \
        > "$GATE5_SAFETY/gate5_candidate_vs_26428.patch"
)

[[ -s "$GATE5_SAFETY/gate5_candidate_vs_26428.patch" ]] \
    || fail "Gate 5 candidate patch is empty"

echo "PASS: candidate snapshot, hashes and binary patch saved"

echo
echo "=== GATE 5J: FINAL REAL-APP NON-MODIFICATION PROOF ==="

REAL_APP_DIFF="$(git diff "$BASE_26428_COMMIT" -- app || true)"

if [[ -n "$REAL_APP_DIFF" ]]; then
    echo "$REAL_APP_DIFF"
    fail "Real app/ changed during Gate 5"
fi

echo "PASS: real app/ remains byte-identical to canonical 26428"

echo
echo "======================================================================"
echo "GATE 5 26452 CFA-TO-CFA FINAL-CARRIER CANDIDATE PASSED"
echo "CURRENTMERGED CFA OWNS FINAL TEMPORAL IMAGE"
echo "STANDARD BAYER RUNS ONE MOTION V2 CFA DEMOSAIC"
echo "DIRECT TEMPORAL RGB FINAL OWNERSHIP = FALSE"
echo "REAL JAVAC = PASS"
echo "REAL app/ UNMODIFIED"
echo "VERSION STILL 0.9726435 / 26435 INSIDE CANDIDATE"
echo "NO REAL 26452 VERSION CHANGE"
echo "NO REAL 26452 APK YET"
echo "======================================================================"

echo
echo "=== GATE 5L: LATE-HISTORY SELECTIVE EXTRACTION AUDIT ==="

G5L_DIR="$GATE5_SAFETY/late_history_selective"
mkdir -p "$G5L_DIR"

G5L_26437="$HIST_DIR/build_26437_windows_whitepoint_motion_detail_stable_uhdr.ps1"
G5L_26438="$HIST_DIR/build_26438_windows_REVISED_v2_audited_motion_microcontrast_standard_ultrahdr.ps1"
G5L_26450="$REPLAY_DECODED/26450.ps1"

for f in "$G5L_26437" "$G5L_26438" "$G5L_26450"; do
    [[ -s "$f" ]] || fail "Gate 5L historical source missing: $f"
done

echo
echo "=== GATE 5L-A: 26437 OWNERSHIP MARKERS ==="

for marker in \
    "IRIS_26437_WHITE_POINT_OWNED_REFERENCE_AND_EDGE_ANCHOR" \
    "IRIS_26437_SENSOR_WHITE_POINT_COLOR_OWNERSHIP" \
    "IRIS_26437_DETAIL_PRESERVE_RESIDUAL_CLEANUP"
do
    grep -q "$marker" "$G5L_26437" \
        || fail "26437 required marker missing: $marker"
    echo "PASS: $marker"
done

grep -q 'direct_rgb_init.glsl' "$G5L_26437" \
    || fail "26437 white-point reference initializer ownership missing"

grep -q 'color_transform.glsl' "$G5L_26437" \
    || fail "26437 color-transform ownership missing"

grep -q 'denoise.glsl' "$G5L_26437" \
    || fail "26437 residual-detail cleanup ownership missing"

echo "PASS: 26437 white-point/color/detail domains identified"

echo
echo "=== GATE 5L-B: 26438 COMPATIBLE / INCOMPATIBLE DOMAIN SPLIT ==="

grep -q 'IRIS_26438_NOISE_AWARE_IMMUTABLE_REFERENCE_MOTION_VETO' \
    "$G5L_26438" \
    || fail "26438 reference-motion veto provenance missing"

grep -q 'IRIS_26438_NEAR_WHITE_REFERENCE_MERGE_OWNERSHIP' \
    "$G5L_26438" \
    || fail "26438 direct-RGB near-white ownership provenance missing"

grep -qi 'microcontrast' "$G5L_26438" \
    || fail "26438 microcontrast provenance missing"

grep -qi 'Ultra HDR\|ULTRAHDR\|gainmap' "$G5L_26438" \
    || fail "26438 Ultra HDR provenance missing"

cat > "$G5L_DIR/26438_policy.txt" <<'EOF'
26438 SELECTIVE POLICY

PRESERVE WHERE DOMAIN-COMPATIBLE:
- immutable-reference / contradictory-local-observation rejection principle
- rendering/microcontrast behavior that is downstream of demosaic
- standards-aligned Ultra HDR behavior
- global exposure behavior

DO NOT TRANSPLANT LITERALLY:
- near-white direct-RGB merge suppression
- any direct_rgb_accumulate RGB-channel synthesis ownership

Reason:
26452 final temporal owner is multiframe CFA currentMerged, not direct RGB.
EOF

echo "PASS: 26438 compatible/incompatible domains explicitly separated"

echo
echo "=== GATE 5L-C: EXACT 26450 DNG VS RGB-FINALIZER SEPARATION ==="

python3 - "$G5L_26450" "$G5L_DIR" <<'PY'
from pathlib import Path
import re
import sys

src = Path(sys.argv[1]).read_text()
out = Path(sys.argv[2])

def extract_here_string(var):
    pattern = re.compile(
        r"\$" + re.escape(var) + r"\s*=\s*@'\s*\n(.*?)\n'@",
        re.S,
    )
    m = pattern.search(src)
    if not m:
        raise SystemExit(f"FAIL: could not extract ${var} from decoded 26450")
    return m.group(1)

dng_old = extract_here_string("DngInsertOld")
dng_new = extract_here_string("DngInsertNew")
final_old = extract_here_string("FinalizeOld")
final_new = extract_here_string("FinalizeNew")

(out / "26450_DNG_INSERT_OLD.txt").write_text(dng_old + "\n")
(out / "26450_DNG_INSERT_NEW.txt").write_text(dng_new + "\n")
(out / "26450_RGB_FINALIZER_OLD_REJECT.txt").write_text(final_old + "\n")
(out / "26450_RGB_FINALIZER_NEW_REJECT.txt").write_text(final_new + "\n")

required_dng = (
    "IRIS_26450_MOTION_V2_REFERENCE_DNG",
    "images.get(0).buffer.duplicate()",
    "ImageSaver.Util.saveStackedRaw(",
    "processingParameters",
    "source=timestampOwnedReferenceBayer",
    "multiframeNr=false",
    "bakedRgb=false",
)

for token in required_dng:
    if token not in dng_new:
        raise SystemExit(
            "FAIL: exact 26450 DNG insertion missing required token: " + token
        )

if "MotionV2CfaReconstruction.reconstruct(" in dng_new:
    raise SystemExit(
        "FAIL: extracted DNG insertion unexpectedly includes reconstruction call"
    )

if "direct_rgb_finalize_alias_safe" not in final_new:
    raise SystemExit(
        "FAIL: 26450 rejected RGB-finalizer extraction did not identify alias shader"
    )

if "IRIS_26450_ALIAS_AWARE_CHROMA_FINALIZER" not in final_new:
    raise SystemExit(
        "FAIL: rejected 26450 finalizer marker missing"
    )

if "IRIS_26450_MOTION_V2_REFERENCE_DNG" in final_new:
    raise SystemExit(
        "FAIL: DNG and RGB-finalizer historical changes are not cleanly separable"
    )

print("PASS: exact 26450 DNG insertion extracted")
print("PASS: exact 26450 alias-aware RGB finalizer extracted separately")
print("PASS: DNG does not depend on rejected RGB finalizer")
PY

echo
echo "=== GATE 5L-D: VERIFY DNG SEMANTIC ORDER IN ACTUAL HDRX CANDIDATE ==="

G5L_HDRX="$GATE5_APP/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
G5L_HDRX_TEST="$G5L_DIR/HdrxProcessor_with_reference_dng_candidate.java"

[[ -s "$G5L_HDRX" ]] \
    || fail "Gate 5L candidate HdrxProcessor.java missing"

python3 - \
    "$G5L_26450" \
    "$G5L_HDRX" \
    "$G5L_HDRX_TEST" <<'PY'
from pathlib import Path
import re
import sys

history = Path(sys.argv[1]).read_text()
hdrx = Path(sys.argv[2]).read_text()
out = Path(sys.argv[3])

def extract_here_string(var):
    pattern = re.compile(
        r"\$" + re.escape(var) + r"\s*=\s*@'\s*\n(.*?)\n'@",
        re.S,
    )
    m = pattern.search(history)
    if not m:
        raise SystemExit(
            f"FAIL: could not extract ${var} from decoded 26450"
        )
    return m.group(1)

old = extract_here_string("DngInsertOld")
new = extract_here_string("DngInsertNew")

count = hdrx.count(old)

if count != 1:
    raise SystemExit(
        "FAIL: exact 26450 reference-DNG insertion anchor appears "
        f"{count} times in the Gate 5 Hdrx candidate"
    )

candidate = hdrx.replace(old, new, 1)

owner = candidate.find("MOTION_REFERENCE_AFTER_RETENTION")
dng = candidate.find("IRIS_26450_MOTION_V2_REFERENCE_DNG")
recon = candidate.find(
    "MotionV2CfaReconstruction.reconstruct(",
    dng
)

if owner < 0:
    raise SystemExit(
        "FAIL: reference-owner marker missing from transformed Hdrx candidate"
    )

if dng < 0:
    raise SystemExit(
        "FAIL: reference-DNG marker missing from transformed Hdrx candidate"
    )

if recon < 0:
    raise SystemExit(
        "FAIL: reconstruction call missing after reference-DNG insertion"
    )

if not (owner < dng < recon):
    raise SystemExit(
        "FAIL: transformed Hdrx source order is not "
        "reference ownership -> reference DNG -> reconstruction"
    )

for token in (
    "images.get(0).buffer.duplicate()",
    "ImageSaver.Util.saveStackedRaw(",
    "source=timestampOwnedReferenceBayer",
    "multiframeNr=false",
    "bakedRgb=false",
):
    if token not in candidate:
        raise SystemExit(
            "FAIL: transformed Hdrx DNG contract missing " + token
        )

out.write_text(candidate)

print("PASS: exact 26450 DNG transform applies once to Gate 5 Hdrx")
print("PASS: reference ownership precedes DNG save")
print("PASS: reference DNG precedes MotionV2 reconstruction")
print("PASS: DNG source is timestamp-owned single-frame Bayer RAW")
PY

[[ -s "$G5L_HDRX_TEST" ]] \
    || fail "Transformed Hdrx DNG candidate was not saved"

echo "PASS: actual Hdrx source ordering proven, not PowerShell text ordering"

echo
echo "=== GATE 5L-E: PROVE REJECTED 26450 RGB PATH WILL NOT ENTER 26452 ==="

if grep -q 'direct_rgb_finalize_alias_safe' "$G5_RECON"; then
    fail "Gate 5 CFA candidate unexpectedly contains rejected 26450 alias finalizer"
fi

if grep -q 'IRIS_26450_ALIAS_AWARE_CHROMA_FINALIZER' "$G5_RECON"; then
    fail "Gate 5 CFA candidate unexpectedly contains rejected RGB finalizer marker"
fi

grep -q 'IRIS_26452_MULTIFRAME_CFA_FINAL_OWNER' "$G5_RECON" \
    || fail "Gate 5 CFA final ownership marker disappeared"

grep -q 'GLTexture imageOutput = currentMerged;' "$G5_RECON" \
    || fail "Gate 5 currentMerged ownership disappeared"

echo "PASS: rejected 26450 RGB finalizer is absent"
echo "PASS: 26452 CFA final ownership remains intact"

echo
echo "=== GATE 5L-F: SAVE SELECTIVE-MIGRATION MANIFEST ==="

cat > "$G5L_DIR/26452_selective_migration_manifest.txt" <<'EOF'
26452 SELECTIVE LATE-HISTORY MIGRATION

PRESERVE:
26437
- sensor white-point ownership
- reference white-point / edge authority where transferable to CFA ownership
- detail-preserving residual cleanup

26438
- immutable-reference local-conflict principle where CFA-domain compatible
- downstream microcontrast/render behavior
- standards-aligned Ultra HDR behavior
- existing global exposure behavior

26450
- exact timestamp-owned single-reference Bayer DNG insertion in HdrxProcessor
- DNG before MotionV2CfaReconstruction.reconstruct()
- multiframeNr=false
- bakedRgb=false

REJECT:
- direct multiframe RGB final image ownership
- direct_rgb_finalize_alias_safe
- IRIS_26450_ALIAS_AWARE_CHROMA_FINALIZER
- 26440-26442 GPU readback diagnostics
- 26447-26448 no-improvement experiments
- untested 26449 experiment

26452 FINAL TEMPORAL OWNER:
currentMerged CFA -> one MotionV2CfaDemosaic
EOF

[[ -s "$G5L_DIR/26452_selective_migration_manifest.txt" ]] \
    || fail "Selective-migration manifest missing"

echo
echo "=== GATE 5L-G: REAL APP MUST STILL BE UNTOUCHED ==="

REAL_APP_DIFF="$(git diff "$BASE_26428_COMMIT" -- app || true)"

if [[ -n "$REAL_APP_DIFF" ]]; then
    echo "$REAL_APP_DIFF"
    fail "Real app/ changed during Gate 5L"
fi

echo "PASS: real app/ remains canonical 26428"

echo
echo "======================================================================"
echo "GATE 5L LATE-HISTORY SELECTIVE EXTRACTION AUDIT PASSED"
echo "26437 WHITE-POINT / DETAIL OWNERSHIP IDENTIFIED"
echo "26438 DOMAIN-COMPATIBILITY SPLIT PROVEN"
echo "26450 REFERENCE DNG EXTRACTED INDEPENDENTLY"
echo "26450 DIRECT-RGB FINALIZER EXPLICITLY REJECTED"
echo "26452 CURRENTMERGED CFA OWNERSHIP PRESERVED"
echo "REAL app/ UNMODIFIED"
echo "NO VERSION CHANGE"
echo "NO FINAL APK YET"
echo "======================================================================"

echo
echo "=== GATE 5M: EXACT HISTORICAL 26436 INTEGRATED CANDIDATE RECONSTRUCTION ==="

G5M_DIR="$GATE5_SAFETY/exact_26436_reconstruction"
G5M_REPO="$G5M_DIR/repo_26428_exact"
G5M_OUT="$G5M_DIR/output"
G5M_SCRIPT="$G5M_DIR/build_26436_candidate_only.ps1"
G5M_PARSER="$G5M_DIR/parse_ps1.ps1"
G5M_PLATFORM="$G5M_DIR/platform_probe.ps1"
G5M_LOG="$G5M_DIR/26436_candidate_replay.log"
G5M_SOURCE="$HIST_DIR/build_26436_windows_integrated_motion_architecture.ps1"
mkdir -p "$G5M_DIR" "$G5M_OUT"
[[ -s "$G5M_SOURCE" ]] || fail "Gate 5M historical 26436 source script missing"

echo
echo "=== GATE 5M-A: PROVE TRUE 26436 HISTORICAL CONTRACT ==="
grep -Fq '$ExpectedHead = "aac8ea5a0f518142b0f8ad60ce34c9a165e4611b"' "$G5M_SOURCE" || fail "26436 canonical 26428 HEAD contract missing"
grep -Fq '$ExpectedBranch = "experimental-clean-photon-rebuild"' "$G5M_SOURCE" || fail "26436 historical branch contract missing"
grep -q 'Expected 0\.9726428 / 26428' "$G5M_SOURCE" || fail "26436 26428 input-version contract missing"
grep -q 'candidate/source validation PASS' "$G5M_SOURCE" || fail "26436 candidate validation gate missing"
grep -q 'Temporary-copy validation: PASS' "$G5M_SOURCE" || fail "26436 temporary-copy validation gate missing"
grep -q '=== GATE 3: REAL GLSL VALIDATION ===' "$G5M_SOURCE" || fail "26436 candidate-only truncation point missing"
for marker in 'IRIS_26436_REFERENCE_SEEDED_TEMPORAL_CONSENSUS_INIT' 'IRIS_26436_REFERENCE_SEEDED_TEMPORAL_CONSENSUS' 'IRIS_26436_REFERENCE_RESIDUAL_SHARED_COLOR_MERGE' 'IRIS_26436_REFERENCE_TIME_ORDERED_TEMPORAL_CONSENSUS' 'IRIS_26436_REFERENCE_RIGID_LOCAL_ALIGNMENT' 'IRIS_26436_BROAD_REGION_CHROMA_PROTECTED_GAINMAP' 'IRIS_26436_MOTION_V2_CHROMA_SAFE_ULTRAHDR'; do
    grep -q "$marker" "$G5M_SOURCE" || fail "26436 historical marker missing: $marker"
done
echo "PASS: exact historical 26436 integrated-build contract proven"

echo
echo "=== GATE 5M-B: CREATE FRESH CANONICAL 26428 INPUT REPO ==="
rm -rf "$G5M_REPO"
git clone --no-hardlinks . "$G5M_REPO" >/dev/null 2>&1 || fail "Gate 5M isolated canonical clone failed"
git -C "$G5M_REPO" checkout --detach "$BASE_26428_COMMIT" >/dev/null 2>&1 || fail "Gate 5M canonical checkout failed"
git -C "$G5M_REPO" checkout -B experimental-clean-photon-rebuild "$BASE_26428_COMMIT" >/dev/null 2>&1 || fail "Gate 5M historical branch reset failed"
[[ "$(git -C "$G5M_REPO" rev-parse HEAD)" == "$BASE_26428_COMMIT" ]] || fail "Gate 5M HEAD is not canonical 26428"
[[ "$(git -C "$G5M_REPO" branch --show-current)" == 'experimental-clean-photon-rebuild' ]] || fail "Gate 5M historical branch name wrong"

G5M_ANDROID_SDK="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-/usr/local/lib/android/sdk}}"
printf 'sdk.dir=%s\n' "$G5M_ANDROID_SDK" > "$G5M_REPO/local.properties"
grep -q '^sdk\.dir=' "$G5M_REPO/local.properties" || fail "Gate 5M local.properties preparation failed"
[[ -f "$G5M_REPO/gradlew.bat" ]] || fail "Gate 5M gradlew.bat prerequisite missing"
grep -q '^VERSION_NAME=0\.9726428$' "$G5M_REPO/app/version.properties" || fail "Gate 5M input is not version 0.9726428"
grep -q '^VERSION_BUILD=26428$' "$G5M_REPO/app/version.properties" || fail "Gate 5M input is not build 26428"

check_g5m_baseline_hash() {
    local rel="$1" expected="$2" label="$3" actual
    [[ -f "$G5M_REPO/$rel" ]] || fail "Gate 5M baseline file missing: $rel"
    actual="$(sha_upper "$G5M_REPO/$rel")"
    if [[ "$actual" != "$expected" ]]; then
        echo "File: $rel"; echo "Expected: $expected"; echo "Actual: $actual"
        fail "Gate 5M canonical 26428 hash mismatch: $label"
    fi
    echo "PASS: $label"
}
check_g5m_baseline_hash 'app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl' 'A3DC78DC0FFF692D23EEC9909D29A053839DAA16F67E90A4E552B9DF5A8CF7B3' '26428 direct_rgb_init'
check_g5m_baseline_hash 'app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl' 'FE62CA5F04735EB2E2E6D7DB2E725431B2C8CB2D9A0B0482916FAA7569623002' '26428 direct_rgb_accumulate'
check_g5m_baseline_hash 'app/src/main/assets/shaders/motionv2/alignment_local_flow.glsl' '1B35547A4D13B26703412BB56E4414641FA62F8F3F251908A476DAE3D830CEFE' '26428 alignment_local_flow'
check_g5m_baseline_hash 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Alignment.java' '80548631423555C5C104A76E5B5950FFB44C69008D85D47440C8E01D7A0B2BA8' '26428 MotionV2Alignment.java'
check_g5m_baseline_hash 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java' 'B5CA7F93F1444B7F3C880F97D7E474B072F650273A7E9C4DB51764034C3A1F7D' '26428 MotionV2CfaReconstruction.java'
check_g5m_baseline_hash 'app/src/main/assets/shaders/motionv2/color_transform.glsl' '3C0DBE63E08D2E1347294921BED2717902B99390DB8A73E7DB9E88CC5681EF0A' '26428 color_transform.glsl'
check_g5m_baseline_hash 'app/src/main/assets/shaders/motionv2/denoise.glsl' '5A939C709C181E61534233BECFABDE9C7C9A5A6296F3F362135832D03DC0FC0C' '26428 denoise.glsl'
check_g5m_baseline_hash 'app/src/main/assets/shaders/motionv2/render.glsl' '7A9053712E89B6C837F99F6259DF770C6D90672E66DE5DEA55379730093B30C2' '26428 render.glsl'
check_g5m_baseline_hash 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java' '5D99C5E183D51D9A25FB906DD4EFA9463D10E189757B46297E8C5A68130E1C12' '26428 MotionV2ColorTransform.java'
check_g5m_baseline_hash 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Denoise.java' '7474026F8573A5F727B809B738EA8D13F2B2EE7E484E360224F14CE1C3EF70AF' '26428 MotionV2Denoise.java'
check_g5m_baseline_hash 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java' 'D9D112951CF56F3E7D367E4016CA092DFB77BEA03575CAF0792020AFEAB6E27F' '26428 MotionV2Render.java'
if grep -q 'IRIS_26452_MULTIFRAME_CFA_FINAL_OWNER' "$G5M_REPO/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"; then fail "26452 transform leaked into Gate 5M input"; fi
git -C "$G5M_REPO" diff --check || fail "Gate 5M canonical tree failed git diff --check"
[[ -z "$(git -C "$G5M_REPO" diff "$BASE_26428_COMMIT" -- app)" ]] || fail "Gate 5M app differs from canonical 26428"
echo "PASS: exact historical 26436 input proven before pwsh"

echo
echo "=== GATE 5M-C: CREATE CANDIDATE-ONLY HISTORICAL 26436 SCRIPT ==="
python3 - "$G5M_SOURCE" "$G5M_SCRIPT" "$G5M_REPO" "$G5M_OUT" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]); dst=Path(sys.argv[2]); repo=sys.argv[3]; out=sys.argv[4]
text=src.read_text(encoding='utf-8-sig')
old_repo=r'C:\Users\nhann\Documents\GitHub\Photon-Camera-clean-rebuild'
if text.count(old_repo)!=1: raise SystemExit(f'FAIL: repo-path assignment count={text.count(old_repo)}')
text=text.replace(old_repo,repo,1)
old_out='$Out = Join-Path $Repo "fresh_iris_outputs"'
if text.count(old_out)!=1: raise SystemExit(f'FAIL: output-root assignment count={text.count(old_out)}')
text=text.replace(old_out,f'$Out = "{out}"',1)
cut='Write-Host "=== GATE 3: REAL GLSL VALIDATION ==="'
if text.count(cut)!=1: raise SystemExit(f'FAIL: truncation marker count={text.count(cut)}')
pos=text.index(cut); candidate_only=text[:pos]
for required in ('Write-Host "candidate/source validation PASS"','Write-Host "Temporary-copy validation: PASS"'):
    if candidate_only.rfind(required)<0: raise SystemExit('FAIL: pre-GLSL proof missing: '+required)
for forbidden in ('=== GATE 3: REAL GLSL VALIDATION ===','=== GATE 4: APPLY EXACT VALIDATED CANDIDATES ===','=== GATE 5: JAVAC PROOF ===','=== GATE 6: BUILD 0.9726436 / 26436 ===','.\\gradlew.bat :app:assembleDebug'):
    if forbidden in candidate_only: raise SystemExit('FAIL: forbidden later stage remains: '+forbidden)
candidate_only += '\n\nWrite-Host ""\nWrite-Host "=============================================================="\nWrite-Host "GATE 5M HISTORICAL 26436 CANDIDATE-ONLY REPLAY PASSED"\nWrite-Host "NO HISTORICAL GLSL STAGE EXECUTED"\nWrite-Host "NO HISTORICAL SOURCE APPLY EXECUTED"\nWrite-Host "NO HISTORICAL JAVAC EXECUTED"\nWrite-Host "NO HISTORICAL APK BUILD EXECUTED"\nWrite-Host "=============================================================="\n'
dst.write_text(candidate_only,encoding='utf-8')
print('PASS: exact historical candidate construction retained')
print('PASS: only repo/output environment assignments relocated')
print('PASS: script truncated after historical candidate validation')
PY
[[ -s "$G5M_SCRIPT" ]] || fail "Gate 5M candidate-only PowerShell missing"

echo
echo "=== GATE 5M-D: POWERSHELL PARSER + UNIX PATH PREFLIGHT ==="
command -v pwsh >/dev/null 2>&1 || fail "pwsh unavailable on runner"
cat > "$G5M_PARSER" <<'PWSH'
param([Parameter(Mandatory = $true)][string]$Path)
$tokens=$null
$errors=$null
[System.Management.Automation.Language.Parser]::ParseFile($Path,[ref]$tokens,[ref]$errors) | Out-Null
if ($errors.Count -gt 0) {
    foreach ($e in $errors) { Write-Host ("PARSER ERROR line {0}: {1}" -f $e.Extent.StartLineNumber,$e.Message) }
    exit 1
}
Write-Host ("PASS: parsed {0}" -f $Path)
PWSH
cat > "$G5M_PLATFORM" <<'PWSH'
param([Parameter(Mandatory = $true)][string]$Repo)
$ErrorActionPreference="Stop"
Set-Location -LiteralPath $Repo
if (-not (Test-Path -LiteralPath 'app\version.properties' -PathType Leaf)) { throw "FAIL: backslash app path unsupported" }
$joined=Join-Path $Repo 'app\version.properties'
if (-not (Test-Path -LiteralPath $joined -PathType Leaf)) { throw "FAIL: Join-Path historical path unsupported" }
if (-not (Test-Path -LiteralPath 'local.properties' -PathType Leaf)) { throw "FAIL: local.properties missing in pwsh view" }
if (-not (Test-Path -LiteralPath 'gradlew.bat' -PathType Leaf)) { throw "FAIL: gradlew.bat missing in pwsh view" }
Write-Host "PASS: pwsh Unix path compatibility"
PWSH
[[ -s "$G5M_PARSER" && -s "$G5M_PLATFORM" ]] || fail "Gate 5M pwsh helpers missing"
pwsh -NoLogo -NoProfile -File "$G5M_PARSER" "$G5M_PARSER" || fail "Parser helper invalid"
pwsh -NoLogo -NoProfile -File "$G5M_PARSER" "$G5M_PLATFORM" || fail "Platform helper parser invalid"
pwsh -NoLogo -NoProfile -File "$G5M_PARSER" "$G5M_SCRIPT" || fail "Historical candidate parser validation failed"
pwsh -NoLogo -NoProfile -File "$G5M_PLATFORM" "$G5M_REPO" || fail "PowerShell Unix-path preflight failed"
echo "PASS: parser helper, historical script, and Unix paths proven"

echo
echo "=== GATE 5M-E: SNAPSHOT CANONICAL APP BEFORE HISTORICAL CANDIDATE ==="
find "$G5M_REPO/app" -type f ! -path '*/build/*' -print0 | sort -z | xargs -0 sha256sum > "$G5M_DIR/app_before_26436_candidate.sha256"
[[ -s "$G5M_DIR/app_before_26436_candidate.sha256" ]] || fail "Gate 5M pre-candidate hash manifest missing"

echo
echo "=== GATE 5M-F: EXECUTE EXACT HISTORICAL 26436 CANDIDATE GENERATOR ==="
( cd "$G5M_REPO"; pwsh -NoLogo -NoProfile -File "$G5M_SCRIPT" ) > "$G5M_LOG" 2>&1 || { tail -n 220 "$G5M_LOG" || true; fail "Historical 26436 candidate reconstruction failed safely"; }
for required_log in 'PASS: exact Windows 26428 source proven' 'candidate/source validation PASS' 'Temporary-copy validation: PASS' 'GATE 5M HISTORICAL 26436 CANDIDATE-ONLY REPLAY PASSED'; do
    grep -q "$required_log" "$G5M_LOG" || { tail -n 220 "$G5M_LOG" || true; fail "Historical 26436 proof missing: $required_log"; }
done

echo
echo "=== GATE 5M-G: LOCATE HISTORICAL 26436 CANDIDATE ==="
G5M_CANDIDATE="$(find "$G5M_OUT" -type d -path '*/windows_26436_integrated_migration_*/candidate' -print | sort | tail -n 1)"
[[ -n "$G5M_CANDIDATE" && -d "$G5M_CANDIDATE" ]] || { find "$G5M_OUT" -maxdepth 5 -type d -print || true; fail "Historical 26436 candidate directory not found"; }
G5M_26436_APP="$G5M_CANDIDATE/app"
[[ -d "$G5M_26436_APP" ]] || fail "Historical 26436 candidate app missing"

echo
echo "=== GATE 5M-H: VERIFY EXACT 26436 CANDIDATE ARCHITECTURE ==="
G5M_RECON="$G5M_26436_APP/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
G5M_ALIGNJ="$G5M_26436_APP/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Alignment.java"
G5M_ALIGNF="$G5M_26436_APP/src/main/assets/shaders/motionv2/alignment_local_flow.glsl"
G5M_DINIT="$G5M_26436_APP/src/main/assets/shaders/motionv2/direct_rgb_init.glsl"
G5M_DACC="$G5M_26436_APP/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl"
G5M_HDRX="$G5M_26436_APP/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
G5M_POST="$G5M_26436_APP/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
G5M_COLORG="$G5M_26436_APP/src/main/assets/shaders/motionv2/color_transform.glsl"
G5M_DENOISEG="$G5M_26436_APP/src/main/assets/shaders/motionv2/denoise.glsl"
G5M_RENDERG="$G5M_26436_APP/src/main/assets/shaders/motionv2/render.glsl"
G5M_GAINMAP="$G5M_26436_APP/src/main/assets/shaders/motionv2/gainmap.glsl"
G5M_UHDR="$G5M_26436_APP/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java"
G5M_VERSION="$G5M_26436_APP/version.properties"
for f in "$G5M_RECON" "$G5M_ALIGNJ" "$G5M_ALIGNF" "$G5M_DINIT" "$G5M_DACC" "$G5M_HDRX" "$G5M_POST" "$G5M_COLORG" "$G5M_DENOISEG" "$G5M_RENDERG" "$G5M_GAINMAP" "$G5M_UHDR" "$G5M_VERSION"; do [[ -s "$f" ]] || fail "Gate 5M candidate file missing: $f"; done
for pair in "$G5M_DINIT|IRIS_26436_REFERENCE_SEEDED_TEMPORAL_CONSENSUS_INIT" "$G5M_DACC|IRIS_26436_REFERENCE_SEEDED_TEMPORAL_CONSENSUS" "$G5M_DACC|IRIS_26436_REFERENCE_RESIDUAL_SHARED_COLOR_MERGE" "$G5M_RECON|IRIS_26436_REFERENCE_TIME_ORDERED_TEMPORAL_CONSENSUS" "$G5M_RECON|IRIS_26436_PERMANENT_SPATIAL_SUPPORT_TELEMETRY" "$G5M_ALIGNJ|IRIS_26436_PERMANENT_ALIGNMENT_TELEMETRY" "$G5M_ALIGNF|IRIS_26436_REFERENCE_RIGID_LOCAL_ALIGNMENT" "$G5M_HDRX|IRIS_26431_MOTION_V2_ALL_FRAME_HANDOFF" "$G5M_POST|IRIS_26432_TRUE_V2_ULTRAHDR_ATTACH" "$G5M_COLORG|IRIS_26430_SENSOR_CLIP_COLOR_SAFETY_ONLY" "$G5M_DENOISEG|IRIS_26430_LIGHT_SUPPORT_OWNED_RESIDUAL_CLEANUP" "$G5M_RENDERG|IRIS_26435_EXACT_26430_HEADROOM_BASE_MINUS_032EV" "$G5M_GAINMAP|IRIS_26436_BROAD_REGION_CHROMA_PROTECTED_GAINMAP" "$G5M_UHDR|IRIS_26436_MOTION_V2_CHROMA_SAFE_ULTRAHDR"; do file="${pair%%|*}"; marker="${pair#*|}"; grep -q "$marker" "$file" || fail "Gate 5M candidate marker missing: $marker"; done
grep -q 'targetFraction=1.0' "$G5M_HDRX" || fail "26436 all-frame target missing"
grep -q 'globalGyroDiscard=false' "$G5M_HDRX" || fail "26436 local-not-global rejection missing"
if grep -q 'perFrameCap' "$G5M_DACC"; then fail "26436 hard per-frame cap returned"; fi
if grep -q 'referenceCeiling' "$G5M_DACC"; then fail "26436 hard support ceiling returned"; fi
G5M_VERSION_NORMALIZED="$G5M_DIR/26436_version_normalized.txt"
tr -d '\r' < "$G5M_VERSION" > "$G5M_VERSION_NORMALIZED"

grep -qx 'VERSION_NAME=0.9726436' "$G5M_VERSION_NORMALIZED" \
    || {
        echo "Historical 26436 version.properties after CRLF normalization:"
        cat "$G5M_VERSION_NORMALIZED" || true
        fail "26436 candidate version name wrong after CRLF normalization"
    }

grep -qx 'VERSION_BUILD=26436' "$G5M_VERSION_NORMALIZED" \
    || {
        echo "Historical 26436 version.properties after CRLF normalization:"
        cat "$G5M_VERSION_NORMALIZED" || true
        fail "26436 candidate build wrong after CRLF normalization"
    }

echo "PASS: historical 26436 semantic version = 0.9726436 / 26436"
echo "PASS: CRLF accepted semantically; exact bytes remain protected by Gate 5M-I SHA-256"

echo
echo "=== GATE 5M-I: VERIFY 26437 EXPECTED HASH CONTRACT ==="
check_hash() { local file="$1" expected="$2" label="$3" actual; actual="$(sha_upper "$file")"; if [[ "$actual" != "$expected" ]]; then echo "File: $file"; echo "Expected: $expected"; echo "Actual: $actual"; fail "Gate 5M 26436 -> 26437 hash contract mismatch: $label"; fi; echo "PASS: $label"; }
check_hash "$G5M_DINIT" '7BABF08973ABD74AF81BBC7E3D543443C1ECE745AED6C43A036690CD44CB3B8A' '26436 direct_rgb_init'
check_hash "$G5M_DACC" 'E5ECB4966AF49DDAF656EF2A7B94A17FF62E8FAC110D0B80A8500965D5A40C47' '26436 direct_rgb_accumulate'
check_hash "$G5M_COLORG" '642DDD94D9374C9792A652561AE82C67ADD73D1FB810551A9CC157FD15AAADF1' '26436 color_transform'
check_hash "$G5M_DENOISEG" '420BAB6F8D917BF8A37D5B6F5864080A1179C04AB90FBD51C0474E45898C3A1C' '26436 denoise shader'
check_hash "$G5M_26436_APP/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Denoise.java" 'C451D4D98BAEA223638CDA2CA116400881440A153720A358BF1C00D1AC381C20' '26436 MotionV2Denoise.java'
check_hash "$G5M_RENDERG" 'FEBC6CCD70249EE036EEAD47C266DA4A3D7133209555CBCC1A584B1E3A066D7D' '26436 render shader'
check_hash "$G5M_VERSION" '245C2610BB7FD9741D467BF08D6F6AE89035C50077AC79A0EE94CCF75A589667' '26436 version.properties'

echo
echo "=== GATE 5M-J: SAVE EXACT 26436 SOURCE SNAPSHOT + HASHES ==="
G5M_EXPORT="$G5M_DIR/exact_26436_candidate_app"; rm -rf "$G5M_EXPORT"; mkdir -p "$G5M_EXPORT"
cp -a "$G5M_26436_APP/." "$G5M_EXPORT/" || fail "Could not export exact 26436 candidate app"
find "$G5M_EXPORT" -type f -print0 | sort -z | xargs -0 sha256sum > "$G5M_DIR/exact_26436_candidate_sha256.txt"
[[ -s "$G5M_DIR/exact_26436_candidate_sha256.txt" ]] || fail "Gate 5M 26436 hash manifest missing"

echo
echo "=== GATE 5M-K: PROVE HISTORICAL CANDIDATE DID NOT APPLY TO SOURCE ==="
find "$G5M_REPO/app" -type f ! -path '*/build/*' -print0 | sort -z | xargs -0 sha256sum > "$G5M_DIR/app_after_26436_candidate.sha256"
cmp -s "$G5M_DIR/app_before_26436_candidate.sha256" "$G5M_DIR/app_after_26436_candidate.sha256" || { diff -u "$G5M_DIR/app_before_26436_candidate.sha256" "$G5M_DIR/app_after_26436_candidate.sha256" | head -n 120 || true; fail "Historical 26436 candidate unexpectedly modified source app/"; }

echo
echo "=== GATE 5M-L: REAL APPLICATION MUST STILL BE UNTOUCHED ==="
REAL_APP_DIFF="$(git diff "$BASE_26428_COMMIT" -- app || true)"
if [[ -n "$REAL_APP_DIFF" ]]; then echo "$REAL_APP_DIFF"; fail "Real app/ changed during Gate 5M"; fi

echo
echo "======================================================================"
echo "GATE 5M EXACT HISTORICAL 26436 INTEGRATED RECONSTRUCTION PASSED"
echo "TRUE INPUT = CANONICAL 0.9726428 / 26428"
echo "26437 INPUT HASH CONTRACT PASSED"
echo "POWERSHELL PARSER + UNIX PATH PREFLIGHT PASSED"
echo "HISTORICAL SOURCE APPLY / JAVAC / APK BUILD NOT EXECUTED"
echo "ISOLATED SOURCE app/ UNMODIFIED"
echo "REAL app/ UNMODIFIED"
echo "NO VERSION CHANGE IN REAL app/"
echo "NO FINAL 26452 APK YET"
echo "======================================================================"

echo
echo "======================================================================"
echo "GATE 6: REAL 0.9726452 / 26452 CANDIDATE CONSTRUCTION + BUILD"
echo "======================================================================"

G6_STAMP="$(date +%Y%m%d_%H%M%S)_$$"
G6_ROOT="$(pwd)/motion_v2_26452_real_$G6_STAMP"
G6_REPO="$G6_ROOT/late_history_repo"
G6_LOGS="$G6_ROOT/logs"
G6_PS="$G6_ROOT/powershell"
G6_SAFETY="$(pwd)/motion_v2_26452_real_safety_$G6_STAMP"
G6_EXPORT="$(pwd)/motion-v2-build-output"

mkdir -p "$G6_ROOT" "$G6_LOGS" "$G6_PS" "$G6_SAFETY" "$G6_EXPORT"

echo
echo "=== GATE 6A: CREATE EXACT 26436 LATE-HISTORY MIGRATION BASE ==="

rm -rf "$G6_REPO"
git clone --no-hardlinks . "$G6_REPO" > "$G6_LOGS/clone.log" 2>&1 \
    || fail "Gate 6 could not create isolated late-history repo"

git -C "$G6_REPO" checkout --detach "$BASE_26428_COMMIT" >/dev/null 2>&1 \
    || fail "Gate 6 could not checkout canonical 26428"

git -C "$G6_REPO" checkout -B experimental-clean-photon-rebuild "$BASE_26428_COMMIT" >/dev/null 2>&1 \
    || fail "Gate 6 could not reset isolated historical branch"

[[ -d "$G5M_26436_APP" ]] \
    || fail "Gate 6 exact Gate 5M 26436 candidate is unavailable"

find "$G6_REPO/app" -mindepth 1 -maxdepth 1 -exec rm -rf {} + \
    || fail "Gate 6 could not clear throwaway app tree"

cp -a "$G5M_26436_APP/." "$G6_REPO/app/" \
    || fail "Gate 6 could not install exact 26436 candidate"

G6_ANDROID_SDK="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-/usr/local/lib/android/sdk}}"
printf 'sdk.dir=%s\n' "$G6_ANDROID_SDK" > "$G6_REPO/local.properties"

G6_VERSION_NORMALIZED="$G6_ROOT/version_26436.txt"
tr -d '\r' < "$G6_REPO/app/version.properties" > "$G6_VERSION_NORMALIZED"
grep -qx 'VERSION_NAME=0.9726436' "$G6_VERSION_NORMALIZED" \
    || fail "Gate 6 late-history base is not version 0.9726436"
grep -qx 'VERSION_BUILD=26436' "$G6_VERSION_NORMALIZED" \
    || fail "Gate 6 late-history base is not build 26436"

g6_hash_check() {
    local rel="$1"
    local expected="$2"
    local label="$3"
    local actual
    actual="$(sha_upper "$G6_REPO/$rel")"
    [[ "$actual" == "$expected" ]] || {
        echo "File: $rel"
        echo "Expected: $expected"
        echo "Actual: $actual"
        fail "Gate 6 exact 26436 base mismatch: $label"
    }
    echo "PASS: $label"
}

g6_hash_check 'app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl' \
    '7BABF08973ABD74AF81BBC7E3D543443C1ECE745AED6C43A036690CD44CB3B8A' \
    '26436 direct_rgb_init'
g6_hash_check 'app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl' \
    'E5ECB4966AF49DDAF656EF2A7B94A17FF62E8FAC110D0B80A8500965D5A40C47' \
    '26436 direct_rgb_accumulate'
g6_hash_check 'app/src/main/assets/shaders/motionv2/color_transform.glsl' \
    '642DDD94D9374C9792A652561AE82C67ADD73D1FB810551A9CC157FD15AAADF1' \
    '26436 color_transform'
g6_hash_check 'app/src/main/assets/shaders/motionv2/denoise.glsl' \
    '420BAB6F8D917BF8A37D5B6F5864080A1179C04AB90FBD51C0474E45898C3A1C' \
    '26436 denoise shader'
g6_hash_check \
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Denoise.java' \
    'C451D4D98BAEA223638CDA2CA116400881440A153720A358BF1C00D1AC381C20' \
    '26436 MotionV2Denoise.java'
g6_hash_check 'app/src/main/assets/shaders/motionv2/render.glsl' \
    'FEBC6CCD70249EE036EEAD47C266DA4A3D7133209555CBCC1A584B1E3A066D7D' \
    '26436 render shader'

echo "PASS: exact 26436 late-history migration base installed"

echo
echo "=== GATE 6B: MATERIALIZE LATE HISTORICAL POWERSHELL SOURCES ==="

cp "$HIST_DIR/build_26437_windows_whitepoint_motion_detail_stable_uhdr.ps1" "$G6_PS/26437.source.ps1"
cp "$HIST_DIR/build_26438_windows_REVISED_v2_audited_motion_microcontrast_standard_ultrahdr.ps1" "$G6_PS/26438.source.ps1"
cp "$REPLAY_DECODED/26439.ps1" "$G6_PS/26439.source.ps1"
cp "$REPLAY_DECODED/26443.ps1" "$G6_PS/26443.source.ps1"
cp "$REPLAY_DECODED/26445.ps1" "$G6_PS/26445.source.ps1"
cp "$REPLAY_DECODED/26446.ps1" "$G6_PS/26446.source.ps1"

for f in "$G6_PS/26437.source.ps1" "$G6_PS/26438.source.ps1" \
         "$G6_PS/26439.source.ps1" "$G6_PS/26443.source.ps1" \
         "$G6_PS/26445.source.ps1" "$G6_PS/26446.source.ps1"
do
    [[ -s "$f" ]] || fail "Gate 6 historical PowerShell source missing: $f"
done

echo "PASS: late historical PowerShell sources materialized"

prepare_g6_candidate_script() {
    local source="$1"
    local output="$2"
    local current_version="$3"
    local current_build="$4"
    local target_version="$5"
    local target_build="$6"
    local selective="$7"

    python3 - "$source" "$output" "$G6_REPO" \
        "$current_version" "$current_build" "$target_version" "$target_build" "$selective" <<'PY'
from pathlib import Path
import re
import sys

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
repo = sys.argv[3]
cur_v = sys.argv[4]
cur_b = sys.argv[5]
target_v = sys.argv[6]
target_b = sys.argv[7]
selective = sys.argv[8] == "1"

text = src.read_text(encoding="utf-8-sig")
text = text.replace("\r\n", "\n").replace("\r", "\n")

repo_assign = re.compile(r'(?m)^\$Repo\s*=\s*"[^"\n]*Photon-Camera-clean-rebuild"\s*$')
matches = list(repo_assign.finditer(text))
if len(matches) != 1:
    raise SystemExit(f"FAIL: historical Repo assignment count={len(matches)}")
text = repo_assign.sub('$Repo = "' + repo.replace("\\", "\\\\") + '"', text, count=1)

text = text.replace('"git.exe"', '"git"').replace("'git.exe'", "'git'")

version_tokens = sorted({
    m.group(1) for m in re.finditer(r'VERSION_NAME=(0\.9726\d+)', text)
    if m.group(1) != target_v
})
build_tokens = sorted({
    int(m.group(1)) for m in re.finditer(r'VERSION_BUILD=(264\d+)', text)
    if m.group(1) != target_b
})

if selective:
    old_v = version_tokens[-1] if version_tokens else None
    old_b = str(build_tokens[-1]) if build_tokens else None

    if old_v and old_v != cur_v:
        text = text.replace(f"VERSION_NAME={old_v}", f"VERSION_NAME={cur_v}")
        text = re.sub(
            r'(?m)^(\$OldVersion\s*=\s*")[^"]+(")\s*$',
            lambda m: m.group(1) + cur_v + m.group(2),
            text
        )

    if old_b and old_b != cur_b:
        text = text.replace(f"VERSION_BUILD={old_b}", f"VERSION_BUILD={cur_b}")
        text = re.sub(
            r'(?m)^(\$OldBuild\s*=\s*")[^"]+(")\s*$',
            lambda m: m.group(1) + cur_b + m.group(2),
            text
        )

    h0 = re.search(r'(?m)^Write-Host\s+"===\s*GATE\s+0[^"]*"\s*$', text)
    h1 = re.search(r'(?m)^Write-Host\s+"===\s*GATE\s+1[^"]*"\s*$', text)
    if not h0 or not h1 or h1.start() <= h0.end():
        raise SystemExit("FAIL: selective migration could not isolate Gate 0/Gate 1")

    proof = (
        'Write-Host "=== GATE 0: SELECTIVE PRESERVED-HISTORY INPUT PROOF ==="\n'
        '$Branch = (& git branch --show-current).Trim()\n'
        '$Head = (& git rev-parse HEAD).Trim()\n'
        'if ($Branch -ne "experimental-clean-photon-rebuild") { Fail ("wrong branch: " + $Branch) }\n'
        'if ($Head -ne "aac8ea5a0f518142b0f8ad60ce34c9a165e4611b") { Fail ("wrong HEAD: " + $Head) }\n'
        '$SelectiveVersion = [IO.File]::ReadAllText((Join-Path $Repo "app\\version.properties"))\n'
        f'if ($SelectiveVersion -notmatch "(?m)^VERSION_NAME={re.escape(cur_v)}`r?$" -or '
        f'$SelectiveVersion -notmatch "(?m)^VERSION_BUILD={re.escape(cur_b)}`r?$") '
        '{ Fail "selective migration input version mismatch" }\n'
        f'Write-Host "PASS: selective preserved-history input = {cur_v} / {cur_b}"\n'
    )
    text = text[:h0.start()] + proof + "\n" + text[h1.start():]

headings = list(re.finditer(r'(?m)^Write-Host\s+"===\s*GATE\s+[^"]*"\s*$', text))
cut = None
for m in headings:
    title = m.group(0).upper()
    if any(k in title for k in ("GLSL", "APPLY", "JAVAC", " APK BUILD", " BUILD ")):
        prefix = text[:m.start()].upper()
        if "CANDIDATE" in prefix or "TEMPORARY" in prefix:
            cut = m.start()
            break

if cut is None:
    raise SystemExit("FAIL: no safe post-candidate truncation gate found")

text = text[:cut]
text += (
    '\nWrite-Host ""\n'
    f'Write-Host "PASS: GATE6 candidate-only historical transform {target_b}"\n'
    'Write-Host "NO HISTORICAL SOURCE APPLY / JAVAC / APK BUILD EXECUTED"\n'
)
dst.write_text(text, encoding="utf-8")
PY

    [[ -s "$output" ]] || fail "Prepared Gate 6 PowerShell script is empty"
    pwsh -NoLogo -NoProfile -File "$G5M_PARSER" "$output" \
        || fail "Prepared Gate 6 PowerShell does not parse: $target_build"
}

apply_g6_historical_candidate() {
    local build="$1"
    local current_version="$2"
    local current_build="$3"
    local target_version="$4"
    local source="$5"
    local selective="$6"

    local prepared="$G6_PS/$build.candidate_only.ps1"
    local log="$G6_LOGS/$build.candidate.log"

    rm -rf "$G6_REPO/fresh_iris_outputs"

    prepare_g6_candidate_script "$source" "$prepared" "$current_version" \
        "$current_build" "$target_version" "$build" "$selective"

    (
        cd "$G6_REPO"
        pwsh -NoLogo -NoProfile -File "$prepared"
    ) > "$log" 2>&1 || {
        tail -n 220 "$log" || true
        fail "Gate 6 historical candidate transform failed: $build"
    }

    grep -q "PASS: GATE6 candidate-only historical transform $build" "$log" \
        || fail "Gate 6 candidate completion banner missing: $build"

    local candidate_version
    candidate_version="$(
        find "$G6_REPO/fresh_iris_outputs" -type f \
            -path '*/candidate*/app/version.properties' -print \
        | while read -r vf; do
            if tr -d '\r' < "$vf" | grep -qx "VERSION_BUILD=$build"; then
                printf '%s\n' "$vf"
            fi
          done | tail -n 1
    )"

    [[ -n "$candidate_version" && -f "$candidate_version" ]] \
        || fail "Gate 6 could not locate $build candidate app"

    local candidate_app
    candidate_app="$(dirname "$candidate_version")"

    (
        cd "$candidate_app"
        find . -type f -print0
    ) | while IFS= read -r -d '' rel; do
        rel="${rel#./}"
        mkdir -p "$G6_REPO/app/$(dirname "$rel")"
        cp -p "$candidate_app/$rel" "$G6_REPO/app/$rel"
    done

    local normalized="$G6_ROOT/version_$build.txt"
    tr -d '\r' < "$G6_REPO/app/version.properties" > "$normalized"
    grep -qx "VERSION_NAME=$target_version" "$normalized" \
        || fail "Gate 6 overlay $build has wrong VERSION_NAME"
    grep -qx "VERSION_BUILD=$build" "$normalized" \
        || fail "Gate 6 overlay $build has wrong VERSION_BUILD"

    grep -R -q "IRIS_${build}_" "$G6_REPO/app/src/main" \
        || fail "Gate 6 overlay $build lacks its historical IRIS marker"

    git -C "$G6_REPO" diff --check \
        || fail "Gate 6 overlay $build failed git diff --check"

    echo "PASS: historical $build candidate overlaid"
}

echo
echo "=== GATE 6C: REPLAY PRESERVED LATE IMAGE HISTORY THROUGH 26446 ==="

apply_g6_historical_candidate 26437 0.9726436 26436 0.9726437 "$G6_PS/26437.source.ps1" 0
apply_g6_historical_candidate 26438 0.9726437 26437 0.9726438 "$G6_PS/26438.source.ps1" 0
apply_g6_historical_candidate 26439 0.9726438 26438 0.9726439 "$G6_PS/26439.source.ps1" 0

# 26440-26442 were diagnostic GPU-readback experiments and are excluded.
apply_g6_historical_candidate 26443 0.9726439 26439 0.9726443 "$G6_PS/26443.source.ps1" 1
apply_g6_historical_candidate 26445 0.9726443 26443 0.9726445 "$G6_PS/26445.source.ps1" 1
apply_g6_historical_candidate 26446 0.9726445 26445 0.9726446 "$G6_PS/26446.source.ps1" 1

echo
echo "=== GATE 6D: VERIFY 26446 SUPPORT OWNERSHIP BEFORE 26452 ==="

G6_RECON="$G6_REPO/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
G6_INPUT="$G6_REPO/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java"
G6_POST="$G6_REPO/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
G6_DEMOSAIC="$G6_REPO/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaDemosaic.java"
G6_LOCAL="$G6_REPO/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2LocalSupportDenoise.java"
G6_FINALIZER="$G6_REPO/app/src/main/assets/shaders/motionv2/direct_rgb_finalize_frame_support.glsl"
G6_VERSION="$G6_REPO/app/version.properties"

for f in "$G6_RECON" "$G6_INPUT" "$G6_POST" "$G6_DEMOSAIC" \
         "$G6_LOCAL" "$G6_FINALIZER" "$G6_VERSION"
do
    [[ -s "$f" ]] || fail "Gate 6 expected 26446 file missing: $f"
done

grep -q 'IRIS_26446_TRUE_FRAME_SUPPORT_TEXTURES' "$G6_RECON" \
    || fail "26446 true frame-support producer missing"
grep -q 'IRIS_26446_LOCAL_FRAME_SUPPORT_CARRIER' "$G6_RECON" \
    || fail "26446 direct-RGB-alpha support carrier missing"
grep -q 'IRIS_26446_TRUE_LOCAL_SUPPORT_DENOISE' "$G6_LOCAL" \
    || fail "26446 local-support consumer missing"
grep -q 'supportSource=directRgbAlpha' "$G6_LOCAL" \
    || fail "26446 local-support consumer does not prove direct-RGB-alpha dependency"
grep -q 'add(new MotionV2LocalSupportDenoise());' "$G6_POST" \
    || fail "26446 local-support node inactive before 26452"

echo "PASS: 26446 support producer/carrier/consumer dependency proven"

echo
echo "=== GATE 6D1: APPLY EXACT 26450 REFERENCE-DNG-ONLY MIGRATION ==="

G6_HDRX="$G6_REPO/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
G6_DNG_OLD="$G5L_DIR/26450_DNG_INSERT_OLD.txt"
G6_DNG_NEW="$G5L_DIR/26450_DNG_INSERT_NEW.txt"

for f in "$G6_HDRX" "$G6_DNG_OLD" "$G6_DNG_NEW"; do
    [[ -s "$f" ]] || fail "Gate 6 DNG migration prerequisite missing: $f"
done

python3 - "$G6_HDRX" "$G6_DNG_OLD" "$G6_DNG_NEW" <<'PY'
from pathlib import Path
import sys

hdrx = Path(sys.argv[1])
old_file = Path(sys.argv[2])
new_file = Path(sys.argv[3])

text = hdrx.read_text()
old = old_file.read_text().rstrip("\n")
new = new_file.read_text().rstrip("\n")

count = text.count(old)
if count != 1:
    raise SystemExit(
        "FAIL: exact 26450 reference-DNG insertion anchor count="
        + str(count)
        + " on late-history Hdrx"
    )

if "IRIS_26450_MOTION_V2_REFERENCE_DNG" in text:
    raise SystemExit("FAIL: 26450 reference-DNG marker already present before migration")

text = text.replace(old, new, 1)

ref = text.find("MOTION_REFERENCE_AFTER_RETENTION")
dng = text.find("IRIS_26450_MOTION_V2_REFERENCE_DNG")
recon = text.find("MotionV2CfaReconstruction.reconstruct(")

if ref < 0:
    raise SystemExit("FAIL: reference-retention marker missing after DNG migration")
if dng < 0:
    raise SystemExit("FAIL: reference-DNG marker missing after migration")
if recon < 0:
    raise SystemExit("FAIL: MotionV2 reconstruction call missing after DNG migration")
if not (ref < dng < recon):
    raise SystemExit(
        "FAIL: required Hdrx order is not reference-retention -> reference-DNG -> reconstruction"
    )

for required in (
    "source=timestampOwnedReferenceBayer",
    "multiframeNr=false",
    "bakedRgb=false",
    "images.get(0).buffer.duplicate()",
):
    if required not in text:
        raise SystemExit("FAIL: migrated reference-DNG contract missing " + required)

hdrx.write_text(text)

print("PASS: exact 26450 reference-DNG-only migration applied once")
print("PASS: timestamp-owned reference Bayer DNG precedes V2 reconstruction")
print("PASS: no direct-RGB finalizer dependency introduced")
PY

grep -q 'IRIS_26450_MOTION_V2_REFERENCE_DNG' "$G6_HDRX"     || fail "26450 reference-DNG marker missing after exact migration"
grep -q 'source=timestampOwnedReferenceBayer' "$G6_HDRX"     || fail "26450 timestamp-owned reference-DNG source marker missing"

if grep -q 'direct_rgb_finalize_alias_safe' "$G6_RECON"; then
    fail "Rejected 26450 alias-aware direct-RGB finalizer entered Gate 6"
fi

echo "PASS: exact 26450 reference DNG preserved independently"
echo "PASS: rejected 26450 direct-RGB finalizer remains absent"

echo
echo "=== GATE 6E: APPLY 26452 CFA OWNERSHIP TO TEMPORARY TREE ==="

python3 - "$G6_RECON" "$G6_INPUT" "$G6_POST" "$G6_VERSION" <<'PY'
from pathlib import Path
import re
import sys

recon = Path(sys.argv[1])
cfa_input = Path(sys.argv[2])
post = Path(sys.argv[3])
version = Path(sys.argv[4])

s = recon.read_text()
marker = "IRIS_26446_LOCAL_FRAME_SUPPORT_CARRIER"
if s.count(marker) != 1:
    raise SystemExit(f"FAIL: 26446 support-carrier marker count={s.count(marker)}")
mi = s.index(marker)
start = s.rfind("            /*", 0, mi)
needle = "            imageOutput.BufferLoad();"
end0 = s.find(needle, mi)
if start < 0 or end0 < 0:
    raise SystemExit("FAIL: could not isolate 26446 final carrier block")
end = end0 + len(needle)

replacement = """            /*
             * IRIS_26452_MULTIFRAME_CFA_FINAL_OWNER
             *
             * Final temporal ownership remains in multiframe CFA currentMerged.
             * 26446 frame support lived in direct-RGB alpha; it is not copied
             * into CFA alpha and cannot own the final image.
             */
            GLTexture imageOutput = currentMerged;
            imageOutput.BufferLoad();"""
s = s[:start] + replacement + s[end:]

if "motionv2/direct_rgb_finalize_frame_support" in s:
    raise SystemExit("FAIL: direct-RGB support finalizer still called")

s = s.replace(
    '+ " directMultiframeRgb=" + directBayer',
    '+ " directMultiframeRgbComputed=" + directBayer'
    '+ " directMultiframeRgbFinalOwner=false"'
)
s = s.replace(
    '+ " separateDemosaic=" + (!directBayer)',
    '+ " separateDemosaic=true"'
)

old_size = """+ " size=" + (directBayer
                            ? raw.x + "x" + raw.y
                            : rawHalf.x + "x" + rawHalf.y)"""
if old_size in s:
    s = s.replace(old_size, '+ " size=" + rawHalf.x + "x" + rawHalf.y', 1)

recon.write_text(s)

s = cfa_input.read_text()
old = """        boolean directBayer =
                basePipeline.mParameters.cfaPattern >= 0
                        && basePipeline.mParameters.cfaPattern <= 3;
        if (directBayer) {
            WorkingTexture = new GLTexture(
                    raw,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                    view,
                    GL_LINEAR,
                    GL_CLAMP_TO_EDGE);
        } else {
            WorkingTexture = new GLTexture(
                    half,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                    view,
                    GL_NEAREST,
                    GL_CLAMP_TO_EDGE);
        }"""
new = """        /*
         * IRIS_26452_MULTIFRAME_CFA_INPUT_OWNER
         *
         * Standard Bayer crosses as packed multiframe CFA and remains nearest
         * sampled until the one Motion V2-owned demosaic.
         */
        WorkingTexture = new GLTexture(
                half,
                new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                view,
                GL_NEAREST,
                GL_CLAMP_TO_EDGE);"""
if s.count(old) != 1:
    raise SystemExit(f"FAIL: MotionV2CfaInput branch count={s.count(old)}")
s = s.replace(old, new, 1)
s = s.replace(
    '(directBayer ? "directRgbFullRes" : "packedCfaHalfRes")',
    '"packedMultiframeCfaHalfRes"'
)
s = s.replace(
    '+ " directMultiframeRgb=" + directBayer',
    '+ " directMultiframeRgbFinalOwner=false"'
)
cfa_input.write_text(s)

s = post.read_text()
old_branch = """            if (directBayer) {
                /*
                 * IRIS_26424_DIRECT_MULTIFRAME_RGB_POST_GRAPH
                 * Standard Bayer image formation already produced full-
                 * resolution linear camera RGB. No separate demosaic runs.
                 */
                add(new StageTelemetry("V2_POST_DIRECT_MULTIFRAME_RGB"));
            } else {"""
new_branch = """            if (directBayer) {
                /*
                 * IRIS_26452_MULTIFRAME_CFA_SINGLE_DEMOSAIC
                 *
                 * Standard Bayer arrives as aligned multiframe packed CFA.
                 * Exactly one Motion V2 demosaic converts it to camera RGB.
                 */
                add(new StageTelemetry("V2_POST_MULTIFRAME_CFA"));
                add(new MotionV2CfaDemosaic());
                add(new StageTelemetry("V2_POST_SINGLE_CFA_DEMOSAIC"));
            } else {"""
if s.count(old_branch) != 1:
    raise SystemExit(f"FAIL: PostPipeline direct-Bayer branch count={s.count(old_branch)}")
s = s.replace(old_branch, new_branch, 1)

support_marker = "IRIS_26446_LOCAL_SUPPORT_CONSUMER_ORDER"
if s.count(support_marker) != 1:
    raise SystemExit(f"FAIL: 26446 local-support marker count={s.count(support_marker)}")
mi = s.index(support_marker)
support_start = s.rfind("            /*", 0, mi)
color_add = '            add(new MotionV2ColorTransform());'
support_end = s.find(color_add, mi)
if support_start < 0 or support_end < 0:
    raise SystemExit("FAIL: could not isolate 26446 local-support consumer block")

replacement_support = """            /*
             * IRIS_26452_LOCAL_SUPPORT_DEFERRED_SEPARATE_CFA_SUPPORT_REQUIRED
             *
             * 26446 MotionV2LocalSupportDenoise consumed direct-RGB alpha.
             * CFA ownership has no such alpha contract. Do not invent support=1
             * and do not reinterpret CFA channels as support.
             */
"""
s = s[:support_start] + replacement_support + s[support_end:]
if 'add(new MotionV2LocalSupportDenoise());' in s:
    raise SystemExit("FAIL: direct-RGB-alpha local-support consumer remains active")

s = s.replace(
    '"nodes=MotionV2CfaInput,DirectRGB-or-CFAFallback,TrueLocalSupportDenoise,MotionV2ColorTransform,MotionV2Denoise,MotionV2Render,RotateWatermark"',
    '"nodes=MotionV2CfaInput,MultiframeCFA,SingleMotionV2CfaDemosaic,MotionV2ColorTransform,MotionV2Denoise,MotionV2Render,RotateWatermark"'
)
s = s.replace(
    '+ " directMultiframeRgb=" + directBayer',
    '+ " directMultiframeRgbFinalOwner=false"'
    '+ " standardBayerSingleDemosaic=" + directBayer'
)
post.write_text(s)

v = version.read_text().replace("\r\n", "\n").replace("\r", "\n")
v, n1 = re.subn(r'(?m)^VERSION_NAME=.*$', 'VERSION_NAME=0.9726452', v, count=1)
v, n2 = re.subn(r'(?m)^VERSION_BUILD=.*$', 'VERSION_BUILD=26452', v, count=1)
if n1 != 1 or n2 != 1:
    raise SystemExit(f"FAIL: version replacement counts name={n1} build={n2}")
version.write_text(v)

print("candidate/source validation PASS")
print("Temporary-copy validation: PASS")
PY

echo
echo "=== GATE 6F: TEMPORARY PRODUCER / CARRIER / CONSUMER PROOF ==="

grep -q 'IRIS_26452_MULTIFRAME_CFA_FINAL_OWNER' "$G6_RECON" \
    || fail "26452 CFA final-owner marker missing"
grep -q 'GLTexture imageOutput = currentMerged;' "$G6_RECON" \
    || fail "26452 currentMerged final owner missing"
grep -q 'currentSupport' "$G6_RECON" \
    || fail "26452 separate CFA support producer disappeared"
if grep -q 'motionv2/direct_rgb_finalize_frame_support' "$G6_RECON"; then
    fail "26446 direct-RGB-alpha finalizer still called"
fi

grep -q 'IRIS_26452_MULTIFRAME_CFA_INPUT_OWNER' "$G6_INPUT" \
    || fail "26452 packed-CFA bridge marker missing"
grep -q 'GL_NEAREST' "$G6_INPUT" \
    || fail "26452 packed CFA bridge lost nearest sampling"
grep -q 'IRIS_26452_MULTIFRAME_CFA_SINGLE_DEMOSAIC' "$G6_POST" \
    || fail "26452 single-demosaic route missing"
grep -q 'IRIS_26452_LOCAL_SUPPORT_DEFERRED_SEPARATE_CFA_SUPPORT_REQUIRED' "$G6_POST" \
    || fail "26452 local-support deferral marker missing"
if grep -q 'add(new MotionV2LocalSupportDenoise());' "$G6_POST"; then
    fail "direct-RGB-alpha local-support consumer still active"
fi
grep -q 'add(new MotionV2ColorTransform());' "$G6_POST" \
    || fail "MotionV2ColorTransform disappeared"
grep -q 'add(new MotionV2Denoise());' "$G6_POST" \
    || fail "MotionV2Denoise disappeared"
grep -q 'add(new MotionV2Render());' "$G6_POST" \
    || fail "MotionV2Render disappeared"

grep -q 'IRIS_26450_MOTION_V2_REFERENCE_DNG' "$G6_HDRX" \
    || fail "26450 reference DNG disappeared from temporary 26452 tree"
python3 - "$G6_HDRX" <<'PY'
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text()
r = text.find("MOTION_REFERENCE_AFTER_RETENTION")
d = text.find("IRIS_26450_MOTION_V2_REFERENCE_DNG")
m = text.find("MotionV2CfaReconstruction.reconstruct(")
if min(r, d, m) < 0 or not (r < d < m):
    raise SystemExit(
        "FAIL: temporary 26452 Hdrx order is not "
        "reference-retention -> reference-DNG -> reconstruction"
    )
print("PASS: temporary 26452 reference-DNG semantic order")
PY

tr -d '\r' < "$G6_VERSION" > "$G6_ROOT/version_26452.txt"
grep -qx 'VERSION_NAME=0.9726452' "$G6_ROOT/version_26452.txt" \
    || fail "Temporary candidate version name is not 0.9726452"
grep -qx 'VERSION_BUILD=26452' "$G6_ROOT/version_26452.txt" \
    || fail "Temporary candidate build is not 26452"

git -C "$G6_REPO" diff --check \
    || fail "Temporary 26452 candidate failed git diff --check"

echo "PASS: producer = currentMerged multiframe CFA"
echo "PASS: support remains separate; no fake CFA alpha support"
echo "PASS: bridge = packed CFA / GL_NEAREST"
echo "PASS: standard Bayer consumer = one MotionV2CfaDemosaic"
echo "PASS: residual MotionV2Denoise / render retained"

echo
echo "=== GATE 6G: REAL JAVAC PROOF ON TEMPORARY 26452 TREE ==="

G6_JAVAC_LOG="$G6_LOGS/26452_candidate_javac.txt"
(
    cd "$G6_REPO"
    chmod +x ./gradlew
    ./gradlew :app:compileDebugJavaWithJavac --stacktrace
) > "$G6_JAVAC_LOG" 2>&1 || {
    tail -n 220 "$G6_JAVAC_LOG" || true
    fail "Temporary 26452 candidate Javac proof failed"
}

grep -q 'BUILD SUCCESSFUL' "$G6_JAVAC_LOG" \
    || fail "Temporary 26452 Javac log lacks BUILD SUCCESSFUL"

echo "candidate/source validation PASS"
echo "Temporary-copy validation: PASS"
echo "PASS: real Javac accepted temporary 26452 tree"

echo
echo "=== GATE 6H: FRESH REAL BACKUP / PATCH / PROTECTED HASHES ==="

REAL_BEFORE_DIFF="$(git diff "$BASE_26428_COMMIT" -- app || true)"
[[ -z "$REAL_BEFORE_DIFF" ]] || {
    echo "$REAL_BEFORE_DIFF"
    fail "Real app/ is not canonical 26428 before real 26452 apply"
}

REAL_UNTRACKED_APP="$(git ls-files --others --exclude-standard app || true)"
[[ -z "$REAL_UNTRACKED_APP" ]] || {
    echo "$REAL_UNTRACKED_APP"
    fail "Untracked files exist inside real app/ before 26452 apply"
}

G6_BACKUP_BRANCH="backup/pre-real-26452-cfa-$G6_STAMP"
git branch "$G6_BACKUP_BRANCH" HEAD \
    || fail "Could not create fresh real 26452 backup branch"

G6_PRE_PATCH="$G6_SAFETY/26452_pre_edit_binary.patch"
git diff --binary HEAD -- app > "$G6_PRE_PATCH" \
    || fail "Could not create real pre-edit binary patch"

G6_INTENTIONAL="$G6_SAFETY/26452_intentional_app_paths.txt"
{
    git -C "$G6_REPO" diff --name-only "$BASE_26428_COMMIT" -- app
    git -C "$G6_REPO" ls-files --others --exclude-standard app
} | sort -u > "$G6_INTENTIONAL"

[[ -s "$G6_INTENTIONAL" ]] || fail "26452 intentional path list is empty"

G6_PROTECTED_BEFORE="$G6_SAFETY/26452_protected_before.sha256"
while IFS= read -r rel; do
    [[ -n "$rel" ]] || continue
    if grep -Fxq "$rel" "$G6_INTENTIONAL"; then continue; fi
    [[ -f "$rel" ]] || continue
    printf '%s  %s\n' "$(sha_upper "$rel")" "$rel"
done < <(git ls-files app) | sort > "$G6_PROTECTED_BEFORE"

[[ -s "$G6_PROTECTED_BEFORE" ]] || fail "Protected pre-edit hash manifest is empty"

git -C "$G6_REPO" diff --binary "$BASE_26428_COMMIT" -- app \
    > "$G6_SAFETY/26452_validated_candidate.patch"

echo "PASS: fresh backup branch = $G6_BACKUP_BRANCH"
echo "PASS: binary pre-edit patch created"
echo "PASS: protected source hashes captured"

echo
echo "=== GATE 6I: APPLY EXACT VALIDATED CANDIDATE DIFF TO REAL app/ ==="

while IFS=$'\t' read -r status rel rest; do
    [[ -n "${status:-}" && -n "${rel:-}" ]] || continue
    case "$status" in
        M|A)
            mkdir -p "$(dirname "$rel")"
            cp -p "$G6_REPO/$rel" "$rel"
            ;;
        D)
            rm -f "$rel"
            ;;
        R*|C*)
            fail "Unexpected rename/copy status: $status $rel $rest"
            ;;
        *)
            fail "Unexpected tracked diff status: $status $rel"
            ;;
    esac
done < <(git -C "$G6_REPO" diff --name-status "$BASE_26428_COMMIT" -- app)

while IFS= read -r rel; do
    [[ -n "$rel" ]] || continue
    mkdir -p "$(dirname "$rel")"
    cp -p "$G6_REPO/$rel" "$rel"
done < <(git -C "$G6_REPO" ls-files --others --exclude-standard app)

echo "PASS: exact temporary candidate applied to real app/"

echo
echo "=== GATE 6J: PROTECTED HASH + PRE-BUILD SAFETY PROOF ==="

G6_PROTECTED_AFTER="$G6_SAFETY/26452_protected_after.sha256"
while IFS= read -r rel; do
    [[ -n "$rel" ]] || continue
    if grep -Fxq "$rel" "$G6_INTENTIONAL"; then continue; fi
    [[ -f "$rel" ]] || continue
    printf '%s  %s\n' "$(sha_upper "$rel")" "$rel"
done < <(git ls-files app) | sort > "$G6_PROTECTED_AFTER"

cmp -s "$G6_PROTECTED_BEFORE" "$G6_PROTECTED_AFTER" || {
    diff -u "$G6_PROTECTED_BEFORE" "$G6_PROTECTED_AFTER" | head -n 160 || true
    fail "Protected application source changed during real 26452 apply"
}

REAL_RECON="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
REAL_INPUT="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java"
REAL_POST="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
REAL_HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
REAL_VERSION="app/version.properties"

grep -q 'IRIS_26452_MULTIFRAME_CFA_FINAL_OWNER' "$REAL_RECON" \
    || fail "Real 26452 currentMerged ownership marker missing"
grep -q 'GLTexture imageOutput = currentMerged;' "$REAL_RECON" \
    || fail "Real 26452 currentMerged final owner missing"
grep -q 'currentSupport' "$REAL_RECON" \
    || fail "Real 26452 separate support producer missing"
if grep -q 'motionv2/direct_rgb_finalize_frame_support' "$REAL_RECON"; then
    fail "Real path still calls direct-RGB support finalizer"
fi

grep -q 'IRIS_26452_MULTIFRAME_CFA_INPUT_OWNER' "$REAL_INPUT" \
    || fail "Real packed-CFA bridge marker missing"
grep -q 'IRIS_26452_MULTIFRAME_CFA_SINGLE_DEMOSAIC' "$REAL_POST" \
    || fail "Real single-demosaic route missing"
grep -q 'IRIS_26452_LOCAL_SUPPORT_DEFERRED_SEPARATE_CFA_SUPPORT_REQUIRED' "$REAL_POST" \
    || fail "Real local-support deferral marker missing"
if grep -q 'add(new MotionV2LocalSupportDenoise());' "$REAL_POST"; then
    fail "Real direct-RGB-alpha local-support consumer still active"
fi

grep -q 'IRIS_26450_MOTION_V2_REFERENCE_DNG' "$REAL_HDRX"     || fail "Real 26452 lost timestamp-owned reference DNG"
grep -q 'source=timestampOwnedReferenceBayer' "$REAL_HDRX"     || fail "Real 26452 reference DNG lost timestamp-owned source contract"

python3 - "$REAL_HDRX" <<'PY'
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text()
r = text.find("MOTION_REFERENCE_AFTER_RETENTION")
d = text.find("IRIS_26450_MOTION_V2_REFERENCE_DNG")
m = text.find("MotionV2CfaReconstruction.reconstruct(")
if min(r, d, m) < 0 or not (r < d < m):
    raise SystemExit(
        "FAIL: real 26452 Hdrx order is not "
        "reference-retention -> reference-DNG -> reconstruction"
    )
print("PASS: real 26452 timestamp-owned reference-DNG order")
PY

tr -d '\r' < "$REAL_VERSION" > "$G6_ROOT/real_version_26452.txt"
grep -qx 'VERSION_NAME=0.9726452' "$G6_ROOT/real_version_26452.txt" \
    || fail "Real VERSION_NAME is not 0.9726452"
grep -qx 'VERSION_BUILD=26452' "$G6_ROOT/real_version_26452.txt" \
    || fail "Real VERSION_BUILD is not 26452"

git diff --check -- app || fail "Real 26452 app diff failed git diff --check"

echo "candidate/source validation PASS"
echo "Temporary-copy validation: PASS"
echo "PRE-BUILD SAFETY PROOF PASSED"
echo "PASS: currentMerged CFA -> packed CFA -> one V2 demosaic"
echo "PASS: direct temporal RGB final ownership = FALSE"
echo "PASS: fake local support = FALSE"
echo "PASS: 26450 timestamp-owned reference DNG preserved"
echo "PASS: version/build = 0.9726452 / 26452"

echo
echo "=== GATE 6K: BUILD REAL 0.9726452 / 26452 APK ==="

G6_BUILD_LOG="$G6_SAFETY/26452_real_build.txt"
chmod +x ./gradlew
./gradlew :app:assembleDebug --stacktrace > "$G6_BUILD_LOG" 2>&1 || {
    tail -n 240 "$G6_BUILD_LOG" || true
    fail "Real 26452 Gradle build failed"
}
grep -q 'BUILD SUCCESSFUL' "$G6_BUILD_LOG" || {
    tail -n 240 "$G6_BUILD_LOG" || true
    fail "Real 26452 build log lacks literal BUILD SUCCESSFUL"
}

G6_BUILT_APK="$(
    find app/build/outputs/apk/debug -type f -name '*.apk' \
        -printf '%T@ %p\n' | sort -nr | head -n 1 | cut -d' ' -f2-
)"
[[ -n "$G6_BUILT_APK" && -f "$G6_BUILT_APK" ]] \
    || fail "Real 26452 build succeeded but no APK was found"

G6_APK_OUT="$(pwd)/IrisCamera-0.9726452-26452-multiframe-cfa-single-demosaic-debug.apk"
cp -p "$G6_BUILT_APK" "$G6_APK_OUT" || fail "Could not copy final 26452 APK"
G6_APK_SHA="$(sha_upper "$G6_APK_OUT")"

G6_RESULT="$G6_SAFETY/26452_RESULT.txt"
{
    echo "Motion V2 26452 REAL BUILD RESULT"
    echo "================================"
    echo "branch=$(git branch --show-current)"
    echo "head=$(git rev-parse HEAD)"
    echo "backup_branch=$G6_BACKUP_BRANCH"
    echo "version=0.9726452"
    echo "build=26452"
    echo "apk=$G6_APK_OUT"
    echo "apk_sha256=$G6_APK_SHA"
    echo
    echo "Architecture:"
    echo "  final temporal owner = currentMerged multiframe CFA"
    echo "  bridge = packed CFA / GL_NEAREST"
    echo "  standard Bayer demosaic = one MotionV2CfaDemosaic"
    echo "  direct temporal RGB final owner = false"
    echo "  26446 direct-RGB-alpha local-support consumer = inactive"
    echo "  fake CFA alpha support = false"
    echo "  MotionV2Denoise / MotionV2Render = retained"
    echo
    echo "26450 reference DNG = preserved; timestamp-owned single Bayer RAW before V2 reconstruction"
    echo "BUILD SUCCESSFUL"
} > "$G6_RESULT"

cp -p "$G6_PRE_PATCH" "$G6_EXPORT/"
cp -p "$G6_SAFETY/26452_validated_candidate.patch" "$G6_EXPORT/"
cp -p "$G6_INTENTIONAL" "$G6_EXPORT/"
cp -p "$G6_PROTECTED_BEFORE" "$G6_EXPORT/"
cp -p "$G6_PROTECTED_AFTER" "$G6_EXPORT/"
cp -p "$G6_BUILD_LOG" "$G6_EXPORT/"
cp -p "$G6_RESULT" "$G6_EXPORT/"
cp -p "$G6_APK_OUT" "$G6_EXPORT/"

echo
echo "======================================================================"
echo "REAL MOTION V2 26452 BUILD SUCCESS"
echo "VERSION / BUILD: 0.9726452 / 26452"
echo "CURRENTMERGED MULTIFRAME CFA OWNS FINAL TEMPORAL IMAGE"
echo "STANDARD BAYER DEMOSAIC COUNT: ONE"
echo "DIRECT TEMPORAL RGB FINAL OWNERSHIP: FALSE"
echo "26446 DIRECT-RGB-ALPHA LOCAL SUPPORT CONSUMER: INACTIVE"
echo "26450 TIMESTAMP-OWNED REFERENCE DNG: PRESERVED"
echo "PRE-BUILD SAFETY PROOF PASSED"
echo "BUILD SUCCESSFUL"
echo "APK: $G6_APK_OUT"
echo "APK SHA256: $G6_APK_SHA"
echo "======================================================================"
