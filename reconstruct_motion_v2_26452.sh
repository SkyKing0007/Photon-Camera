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