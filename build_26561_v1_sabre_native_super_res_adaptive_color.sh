#!/usr/bin/env bash
set -euo pipefail

fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
manifest_audited(){ local root="$1" out="$2"; (cd "$root" && { find app/src/main -type f ! -path 'app/src/main/cpp/third_party_26507/*' ! -path 'app/src/main/cpp/deps/*' -print; [[ -f app/src/main/cpp/deps/.gitignore ]] && echo app/src/main/cpp/deps/.gitignore; echo app/version.properties; echo app/build.gradle; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done) > "$out"; }
vendor_manifest(){ local root="$1" out="$2"; (cd "$root" && { [[ -d app/src/main/cpp/third_party_26507 ]] && find app/src/main/cpp/third_party_26507 -type f -print; [[ -d app/src/main/cpp/deps ]] && find app/src/main/cpp/deps -type f -print; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done) > "$out"; }
exact_tree_equal(){ python3 - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def tree(root):
    root=Path(root)
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}
a,b=tree(sys.argv[1]),tree(sys.argv[2])
if a!=b:
    bad=[k for k in sorted(set(a)|set(b)) if a.get(k)!=b.get(k)]
    raise SystemExit('tree mismatch: '+repr(bad[:40]))
PY
}

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_SUCCESS_COMMIT="40714fc8077b66b8a9f04adaff6cff212c02f644"
BASE_RUN_ID="33257466556"
BASE_ARTIFACT_ID="9716289696"
BASE_ARTIFACT_NAME="photon-26560-v1-sabre-only-spatial-rgb-cleanup"
BASE_ARTIFACT_SHA="f9c3329820270c686b401e62752b364b89e04f0d19aabff2e4a3fea810c641a8"
BASE_TAR_SHA="932dd616e6f1dde527afe9e909783c869e62940572f56eb6a5dba625616fcb22"
BASE_MANIFEST_SHA="a8249154bdf98d6661f2ca05a8ec2ff47fc76d86dd4475967cbfc5c4e13b0a39"
CAND_MANIFEST_SHA="1cda4a00406f83e42c1d6d66e6b1a7067514c645402dc4859bf21f0b7bd13f64"
VENDOR_MANIFEST_SHA="7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8"
PROTECTED_CORE_SHA="8994db8abed508bb020f098d426c6ccc63ef2c5607aef64a17438bcc3f32aa48"
PREWRITE_MANIFEST_SHA="baa0c22dfdc748a13e8795848d8d9d17c290c66279282ec7a9914a82c4bf8704"
CAND_CHANGED_MANIFEST_SHA="80610f15addf2b0d892cb1eb700862e8d008942175b56ee0c327f70ccf89eafd"
RUNTIME_GLSL_MANIFEST_SHA="934e7f897d09fc824304b3dfe622c50c24bfad79722ea4703e0a887c3ba6f57a"
GLSLANG_PKG_VERSION="15.1.0-2~ubuntu0.24.04.2"
BACKUP_BRANCH="backup-26559-v1-before-sabre-only-spatial-rgb-sr-transition"
BACKUP_SHA_EXPECTED="77aee0b9abd18f22cb3f9872d53e3ea1869824fe"
VERSION_NAME="0.9726561"
VERSION_BUILD="26561"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"

BASE_PIN="$ROOT/V1_26561_BASE_26560_V1_AUDITED_RUNTIME.sha256"
BASE_TAR_PIN="$ROOT/V1_26561_BASE_26560_V1_CANDIDATE_TAR.sha256"
CAND_PIN="$ROOT/V1_26561_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
VENDOR_PIN="$ROOT/V1_26561_NATIVE_VENDOR_DEPENDENCIES.sha256"
RUNTIME_LIST="$ROOT/V1_26561_RUNTIME_FILES.txt"
PREWRITE="$ROOT/V1_26561_PREWRITE_SOURCE_HASHES.sha256"
CAND_CHANGED="$ROOT/V1_26561_CANDIDATE_CHANGED_HASHES.sha256"
PROTECTED_CORE="$ROOT/V1_26561_PROTECTED_UNCHANGED_CORE.sha256"
RUNTIME_GLSL_PIN="$ROOT/V1_26561_RUNTIME_EXPANDED_GLSL.sha256"
FORWARD="$ROOT/V1_26561_RUNTIME_DELTA_FROM_26560.patch"
ROLLBACK="$ROOT/V1_26561_RUNTIME_ROLLBACK_TO_26560.patch"
TRANSFORM="$ROOT/transform_26561_v1_sabre_native_super_res_adaptive_color.py"
VALIDATE="$ROOT/validate_26561_v1_sabre_native_super_res_adaptive_color.py"
EXTRACT="$ROOT/extract_26561_runtime_glsl.py"
RESERVED="$ROOT/scan_glsl_reserved_identifiers_26561.py"
HANDOFF_HASHES="$ROOT/V1_26561_HANDOFF_HASHES.sha256"
OUT="$ROOT/build_26561_v1_sabre_native_super_res_adaptive_color_outputs"
WORK="$ROOT/.build_26561_v1_sabre_native_super_res_adaptive_color_work"
ARTZIP="$WORK/26560_v1_artifact.zip"
ARTDIR="$WORK/artifact"
BASE="$WORK/exact_26560_compiled_candidate"
AFTER="$WORK/candidate_26561"
GLSLOUT="$WORK/runtime_glsl"
PATCHREPO="$WORK/patchrepo"
ROLLREPO="$WORK/rollbackrepo"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-sabre-native-super-res-adaptive-color-debug.apk"
LOCAL_REPLAY_ARTIFACT=""
if [[ "${1:-}" == "--local-prebuild" ]]; then
    [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact 26560 artifact ZIP"
    LOCAL_REPLAY_ARTIFACT="$2"
fi

mapfile -t RUNTIME_FILES < "$RUNTIME_LIST"
[[ "${#RUNTIME_FILES[@]}" -eq 10 ]] || fail "runtime inventory must contain exactly 10 files"

rm -rf "$OUT" "$WORK"
rm -f "$FINAL"
mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$GLSLOUT"

cat > "$OUT/26561_V1_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET (covered by full assemble)
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
cat > "$OUT/26561_V1_STRICT_HANDOFF_REPORT.txt" <<'EOF'
RUNTIME OWNERSHIP: NOT RUN
DORMANT-OWNER REJECTION: NOT RUN
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
BACKUP STATUS: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
SABRE/VGN EXISTING GLSL INVARIANCE: NOT RUN
NIGHT SHADOW_LONG NATIVE OWNERSHIP: NOT RUN
NIGHT SHADOW_LONG SR-DETAIL EXCLUSION: NOT RUN
SUPER RES 2X DETAIL ABI: NOT RUN
NATIVE 1X DNG OWNERSHIP: NOT RUN
UNIVERSAL ADAPTIVE COLOR OWNERSHIP: NOT RUN
PROTECTED CAPTURE/NIGHT/DNG/UHDR INVARIANCE: NOT RUN
GLSL RESERVED-IDENTIFIER SCAN: NOT RUN
EXACT RUNTIME-EXPANDED GLSL: NOT RUN
REAL GLSL COMPILE: NOT RUN
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
NATIVE/NDK COMPILE: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
POST-BUILD INVARIANCE: NOT RUN
CLEAN ARTIFACT SOURCE EXPORT: NOT RUN
TARGET VERSION/BUILD: 0.9726561 / 26561 V1
EOF
set_report(){ python3 - "$OUT/26561_V1_STRICT_HANDOFF_REPORT.txt" "$1" "$2" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); key=sys.argv[2]; value=sys.argv[3]
lines=p.read_text().splitlines(); pref=key+':'
for i,line in enumerate(lines):
    if line.startswith(pref): lines[i]=pref+' '+value; break
else: raise SystemExit('report key missing '+key)
p.write_text('\n'.join(lines)+'\n')
PY
}

verify_package_and_pins(){
    sha256sum -c "$HANDOFF_HASHES"
    python3 -m py_compile "$TRANSFORM" "$VALIDATE" "$EXTRACT" "$RESERVED"
    python3 "$VALIDATE" --self-test
    python3 "$EXTRACT" --self-test
    python3 "$RESERVED" --self-test
    bash -n "$0"
    [[ "$(wc -l < "$BASE_PIN")" -eq 925 ]] || fail "base manifest count"
    [[ "$(sha "$BASE_PIN")" == "$BASE_MANIFEST_SHA" ]] || fail "base manifest SHA"
    [[ "$(wc -l < "$CAND_PIN")" -eq 927 ]] || fail "candidate manifest count"
    [[ "$(sha "$CAND_PIN")" == "$CAND_MANIFEST_SHA" ]] || fail "candidate manifest SHA"
    [[ "$(wc -l < "$VENDOR_PIN")" -eq 778 ]] || fail "vendor manifest count"
    [[ "$(sha "$VENDOR_PIN")" == "$VENDOR_MANIFEST_SHA" ]] || fail "vendor manifest SHA"
    [[ "$(wc -l < "$PROTECTED_CORE")" -eq 13 ]] || fail "protected core count"
    [[ "$(sha "$PROTECTED_CORE")" == "$PROTECTED_CORE_SHA" ]] || fail "protected core manifest SHA"
    [[ "$(wc -l < "$PREWRITE")" -eq 8 ]] || fail "prewrite count"
    [[ "$(sha "$PREWRITE")" == "$PREWRITE_MANIFEST_SHA" ]] || fail "prewrite manifest SHA"
    [[ "$(wc -l < "$CAND_CHANGED")" -eq 10 ]] || fail "candidate changed count"
    [[ "$(sha "$CAND_CHANGED")" == "$CAND_CHANGED_MANIFEST_SHA" ]] || fail "candidate changed SHA"
    [[ "$(wc -l < "$RUNTIME_GLSL_PIN")" -eq 5 ]] || fail "runtime GLSL manifest count"
    [[ "$(sha "$RUNTIME_GLSL_PIN")" == "$RUNTIME_GLSL_MANIFEST_SHA" ]] || fail "runtime GLSL manifest SHA"
    grep -F "$BASE_TAR_SHA" "$BASE_TAR_PIN" >/dev/null || fail "base TAR pin drift"
}

verify_base_artifact_and_reconstruct(){
    local zip="$1"
    [[ "$(sha "$zip")" == "$BASE_ARTIFACT_SHA" ]] || fail "26560 artifact ZIP SHA mismatch"
    unzip -q "$zip" -d "$ARTDIR"
    local base_out="$ARTDIR/build_26560_v1_sabre_only_spatial_rgb_cleanup_outputs"
    local base_tar="$base_out/26560_V1_candidate_app_source.tar.gz"
    local base_audited="$base_out/26560_V1_candidate_source.sha256"
    local base_compiler="$base_out/26560_V1_COMPILER_STATUS.txt"
    local base_vendor="$base_out/26560_vendor_postbuild.sha256"
    local base_apk_hash="$base_out/26560_V1_APK.sha256"
    for f in "$base_tar" "$base_audited" "$base_compiler" "$base_vendor" "$base_apk_hash"; do
        [[ -f "$f" ]] || fail "base artifact missing $f"
    done
    [[ "$(sha "$base_tar")" == "$BASE_TAR_SHA" ]] || fail "26560 candidate TAR SHA mismatch"
    [[ "$(sha "$base_audited")" == "$BASE_MANIFEST_SHA" ]] || fail "26560 audited manifest SHA mismatch"
    cmp "$base_audited" "$BASE_PIN" >/dev/null || fail "packaged base pin differs from successful 26560 artifact"
    cmp "$base_vendor" "$VENDOR_PIN" >/dev/null || fail "successful 26560 vendor proof differs from pin"
    for status in 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do
        grep -F "$status" "$base_compiler" >/dev/null || fail "26560 compiler proof missing: $status"
    done
    tar -xzf "$base_tar" -C "$BASE"
    manifest_audited "$BASE" "$WORK/base_reconstructed.sha256"
    cmp "$WORK/base_reconstructed.sha256" "$BASE_PIN" >/dev/null || fail "reconstructed 26560 runtime manifest mismatch"
    vendor_manifest "$BASE" "$WORK/base_vendor_reconstructed.sha256"
    cmp "$WORK/base_vendor_reconstructed.sha256" "$VENDOR_PIN" >/dev/null || fail "reconstructed 26560 vendor mismatch"
    set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (run ${BASE_RUN_ID} artifact ${BASE_ARTIFACT_ID})"
    pass "exact successful compiled 26560 authority"
}

build_candidate_and_precompile_proof(){
    cp -a "$BASE/." "$AFTER/"
    (cd "$AFTER" && sha256sum -c "$PREWRITE")
    python3 "$TRANSFORM" "$AFTER"
    manifest_audited "$AFTER" "$WORK/candidate_manifest.sha256"
    cmp "$WORK/candidate_manifest.sha256" "$CAND_PIN" >/dev/null || fail "candidate manifest differs from pin"
    (cd "$AFTER" && sha256sum -c "$CAND_CHANGED")
    python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER"
    set_report "RUNTIME OWNERSHIP" "PASS (Sabre native 1x structural/color authority; SR detail sidecar only)"
    set_report "DORMANT-OWNER REJECTION" "PASS (deleted Spatial/Wronski reconstruction owners remain absent)"
    set_report "CHANGED RUNTIME SCOPE" "PASS (exact 10-file allowlist; 7 existing source + 2 icons + version)"
    set_report "SABRE/VGN EXISTING GLSL INVARIANCE" "PASS (15/15 Sabre + 11/11 current-MGC VGN literals byte-identical)"
    set_report "NIGHT SHADOW_LONG NATIVE OWNERSHIP" "PASS (native Sabre long merge/source clipping preserved)"
    set_report "NIGHT SHADOW_LONG SR-DETAIL EXCLUSION" "PASS (fine SR carrier admits NORMAL only)"
    set_report "SUPER RES 2X DETAIL ABI" "PASS (RG16F luma/support accumulator -> R8/Q8 streamed detail; existing JPEG ABI)"
    set_report "NATIVE 1X DNG OWNERSHIP" "PASS"
    set_report "UNIVERSAL ADAPTIVE COLOR OWNERSHIP" "PASS (post-VGN local unsupported-chroma correction; center luma preserved)"
    set_report "PROTECTED CAPTURE/NIGHT/DNG/UHDR INVARIANCE" "PASS (13 files byte-identical)"

    rm -rf "$GLSLOUT"; mkdir -p "$GLSLOUT"
    python3 "$EXTRACT" --root "$AFTER" --out "$GLSLOUT" | tee "$OUT/26561_runtime_glsl_extraction.txt"
    (cd "$GLSLOUT" && sha256sum -c "$RUNTIME_GLSL_PIN")
    python3 "$RESERVED" "$GLSLOUT"/* | tee "$OUT/26561_reserved_identifier_scan.txt"
    set_report "GLSL RESERVED-IDENTIFIER SCAN" "PASS (all 5 exact runtime-expanded files; coherent regression retained)"
    set_report "EXACT RUNTIME-EXPANDED GLSL" "PASS (5-file hash pin)"

    rm -rf "$PATCHREPO" "$ROLLREPO"; mkdir -p "$PATCHREPO" "$ROLLREPO"
    # Patch determinism/proof is intentionally scoped to the exact 10-file runtime delta.
    # Full 925/927-file runtime manifests and the 778-file native/vendor manifest independently
    # prove every unchanged byte, so indexing multi-hundred-MB vendor trees here adds no proof.
    seed_changed_scope(){
        local source_root="$1" dest_root="$2" include_added="$3"
        mkdir -p "$dest_root"
        while IFS= read -r rel; do
            if [[ -f "$source_root/$rel" ]]; then
                mkdir -p "$dest_root/$(dirname "$rel")"
                cp -a "$source_root/$rel" "$dest_root/$rel"
            elif [[ "$include_added" == "yes" ]]; then
                fail "candidate changed file missing while seeding patch scope: $rel"
            fi
        done < "$RUNTIME_LIST"
    }
    seed_changed_scope "$BASE" "$PATCHREPO" no
    (
      cd "$PATCHREPO"
      git init -q; git config user.name Photon; git config user.email photon@example.invalid
      git add app; git commit -qm base
    )
    while IFS= read -r rel; do
        mkdir -p "$PATCHREPO/$(dirname "$rel")"
        cp -a "$AFTER/$rel" "$PATCHREPO/$rel"
    done < "$RUNTIME_LIST"
    (
      cd "$PATCHREPO"
      git add -N app/src/main/res/drawable/ic_super_res_off.xml app/src/main/res/drawable/ic_super_res_on.xml
      for ab in 7 12 40; do git -c core.abbrev="$ab" diff --binary --full-index --no-ext-diff > "$WORK/forward.$ab.patch"; done
      cmp "$WORK/forward.7.patch" "$WORK/forward.12.patch"; cmp "$WORK/forward.7.patch" "$WORK/forward.40.patch"
      cmp "$WORK/forward.7.patch" "$FORWARD"
    )
    seed_changed_scope "$AFTER" "$ROLLREPO" yes
    (
      cd "$ROLLREPO"
      git init -q; git config user.name Photon; git config user.email photon@example.invalid
      git add app; git commit -qm candidate
    )
    while IFS= read -r rel; do
        if [[ -f "$BASE/$rel" ]]; then
            cp -a "$BASE/$rel" "$ROLLREPO/$rel"
        else
            rm -f "$ROLLREPO/$rel"
        fi
    done < "$RUNTIME_LIST"
    (
      cd "$ROLLREPO"
      for ab in 7 12 40; do git -c core.abbrev="$ab" diff --binary --full-index --no-ext-diff > "$WORK/rollback.$ab.patch"; done
      cmp "$WORK/rollback.7.patch" "$WORK/rollback.12.patch"; cmp "$WORK/rollback.7.patch" "$WORK/rollback.40.patch"
      cmp "$WORK/rollback.7.patch" "$ROLLBACK"
    )

    rm -rf "$WORK/forwardproof" "$WORK/rollbackproof"
    mkdir -p "$WORK/forwardproof" "$WORK/rollbackproof"
    seed_changed_scope "$BASE" "$WORK/forwardproof" no
    (
      cd "$WORK/forwardproof"
      git init -q; git config user.name Photon; git config user.email photon@example.invalid
      git add app; git commit -qm base
      git apply --check "$FORWARD"
      git apply "$FORWARD"
      sha256sum -c "$CAND_CHANGED"
      mapfile -t got < <({ git diff --name-only HEAD; git ls-files --others --exclude-standard; } | LC_ALL=C sort -u)
      mapfile -t want < <(LC_ALL=C sort "$RUNTIME_LIST")
      [[ "${got[*]}" == "${want[*]}" ]] || fail "forward patch changed-file scope drift"
    )
    seed_changed_scope "$AFTER" "$WORK/rollbackproof" yes
    (
      cd "$WORK/rollbackproof"
      git init -q; git config user.name Photon; git config user.email photon@example.invalid
      git add app; git commit -qm candidate
      git apply --check "$ROLLBACK"
      git apply "$ROLLBACK"
      sha256sum -c "$PREWRITE"
      [[ ! -e app/src/main/res/drawable/ic_super_res_off.xml && ! -e app/src/main/res/drawable/ic_super_res_on.xml ]] || fail "rollback did not delete added SR icons"
      mapfile -t got < <(git diff --name-only HEAD | LC_ALL=C sort)
      mapfile -t want < <(LC_ALL=C sort "$RUNTIME_LIST")
      [[ "${got[*]}" == "${want[*]}" ]] || fail "rollback patch changed-file scope drift"
    )
    set_report "FORWARD PATCH FUZZ=0" "PASS"
    set_report "ROLLBACK PATCH FUZZ=0" "PASS"
    pass "candidate semantics / exact GLSL / deterministic patch proof"
}

run_real_glsl(){
    if ! command -v glslangValidator >/dev/null 2>&1 || [[ "$(dpkg-query -W -f='${Version}' glslang-tools 2>/dev/null || true)" != "$GLSLANG_PKG_VERSION" ]]; then
        sudo apt-get update -qq
        sudo apt-get install -y "glslang-tools=${GLSLANG_PKG_VERSION}"
    fi
    [[ "$(dpkg-query -W -f='${Version}' glslang-tools)" == "$GLSLANG_PKG_VERSION" ]] || fail "wrong glslang-tools package version"
    glslangValidator --version | tee "$OUT/26561_glslang_version.txt"
    grep -F 'Khronos. 15.1.0' "$OUT/26561_glslang_version.txt" >/dev/null || fail "glslangValidator version is not pinned 15.1.0"
    glslangValidator -S vert "$GLSLOUT/sabre_super_res_detail_merge_26561.vert"
    glslangValidator -S frag "$GLSLOUT/sabre_super_res_detail_merge_26561.frag"
    glslangValidator -l "$GLSLOUT/sabre_super_res_detail_merge_26561.vert" "$GLSLOUT/sabre_super_res_detail_merge_26561.frag"
    glslangValidator -S vert "$GLSLOUT/sabre_super_res_detail_resolve_26561.vert"
    glslangValidator -S frag "$GLSLOUT/sabre_super_res_detail_resolve_26561.frag"
    glslangValidator -l "$GLSLOUT/sabre_super_res_detail_resolve_26561.vert" "$GLSLOUT/sabre_super_res_detail_resolve_26561.frag"
    glslangValidator -S comp "$GLSLOUT/universal_adaptive_color_26561.comp"
    python3 - "$OUT/26561_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]);p.write_text(p.read_text().replace('REAL GLSL COMPILE: NOT RUN YET','REAL GLSL COMPILE: PASS'))
PY
    set_report "REAL GLSL COMPILE" "PASS (pinned Khronos glslangValidator 15.1.0; exact runtime-expanded files)"
    pass "real GLSL compile"
}

if [[ -n "$LOCAL_REPLAY_ARTIFACT" ]]; then
    echo "=== 26561 LOCAL PREBUILD REPLAY: package/pins ==="
    verify_package_and_pins
    echo "=== 26561 LOCAL PREBUILD REPLAY: exact 26560 artifact ==="
    verify_base_artifact_and_reconstruct "$LOCAL_REPLAY_ARTIFACT"
    echo "=== 26561 LOCAL PREBUILD REPLAY: transform/ownership/GLSL/patches ==="
    build_candidate_and_precompile_proof
    if command -v glslangValidator >/dev/null 2>&1 && command -v dpkg-query >/dev/null 2>&1 && [[ "$(dpkg-query -W -f='${Version}' glslang-tools 2>/dev/null || true)" == "$GLSLANG_PKG_VERSION" ]]; then
        run_real_glsl
    else
        echo "LOCAL REAL GLSL COMPILE: NOT RUN (pinned package unavailable locally)" | tee "$OUT/26561_LOCAL_COMPILER_LIMIT.txt"
    fi
    echo "LOCAL REAL KOTLIN/JAVA/ASSEMBLE: NOT RUN (Actions-only Android SDK/toolchain in this environment)" | tee -a "$OUT/26561_LOCAL_COMPILER_LIMIT.txt"
    pass "26561 local prebuild replay complete; authoritative compiler/build gates remain Actions-only"
    exit 0
fi

echo "=== 26561 GATE 0: sealed handoff / branch / lineage / architectural backup ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
[[ "$(git rev-parse HEAD^)" == "$BASE_SUCCESS_COMMIT" ]] || fail "handoff commit must be direct child of successful 26560"
[[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
verify_package_and_pins
BACKUP_SHA="$(git ls-remote origin "refs/heads/${BACKUP_BRANCH}" | awk '{print $1}')"
[[ "$BACKUP_SHA" == "$BACKUP_SHA_EXPECTED" ]] || fail "architectural backup missing/wrong: $BACKUP_SHA"
set_report "BACKUP STATUS" "PASS (${BACKUP_BRANCH} @ ${BACKUP_SHA_EXPECTED}; covers Sabre-only/SR transition; exact 26560 rollback also packaged)"
python3 - "$BASE_SUCCESS_COMMIT" <<'PY'
import subprocess,sys
base=sys.argv[1]
allowed={
'.github/workflows/build-26561-v1-sabre-native-super-res-adaptive-color.yml',
'V1_26561_BASE_26560_V1_AUDITED_RUNTIME.sha256','V1_26561_BASE_26560_V1_CANDIDATE_TAR.sha256',
'V1_26561_BASE_PROVENANCE.txt','V1_26561_CANDIDATE_CHANGED_HASHES.sha256',
'V1_26561_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256','V1_26561_HANDOFF_HASHES.sha256',
'V1_26561_LOCAL_VALIDATION.txt','V1_26561_NATIVE_VENDOR_DEPENDENCIES.sha256',
'V1_26561_PREWRITE_SOURCE_HASHES.sha256','V1_26561_PROTECTED_UNCHANGED_CORE.sha256',
'V1_26561_RUNTIME_DELTA_FROM_26560.patch','V1_26561_RUNTIME_EXPANDED_GLSL.sha256',
'V1_26561_RUNTIME_FILES.txt','V1_26561_RUNTIME_ROLLBACK_TO_26560.patch',
'V1_26561_UPLOAD_INSTRUCTIONS.md','build_26561_v1_sabre_native_super_res_adaptive_color.sh',
'extract_26561_runtime_glsl.py','scan_glsl_reserved_identifiers_26561.py',
'transform_26561_v1_sabre_native_super_res_adaptive_color.py','validate_26561_v1_sabre_native_super_res_adaptive_color.py'}
actual=set(subprocess.check_output(['git','diff','--name-only',base+'..HEAD'],text=True).splitlines())
if actual!=allowed: raise SystemExit('handoff scope mismatch extra=%r missing=%r'%(sorted(actual-allowed),sorted(allowed-actual)))
if any(x.startswith('app/') for x in actual): raise SystemExit('handoff directly modified repository app source')
print('PASS exact 21-file handoff scope; repository app source untouched')
PY
pass "sealed 26561 package / lineage / backup"

echo "=== 26561 GATE 1: exact successful compiled 26560 runtime authority ==="
REPO_API="https://api.github.com/repos/${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/runs/${BASE_RUN_ID}" -o "$WORK/base_run.json"
python3 - "$WORK/base_run.json" "$BASE_RUN_ID" "$BASE_SUCCESS_COMMIT" "$EXPECTED_BRANCH" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2]; assert d.get('conclusion')=='success'; assert d.get('head_sha')==sys.argv[3]; assert d.get('head_branch')==sys.argv[4]
print('PASS exact successful 26560 Actions run')
PY
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}" -o "$WORK/base_artifact.json"
python3 - "$WORK/base_artifact.json" "$BASE_ARTIFACT_ID" "$BASE_ARTIFACT_NAME" "$BASE_ARTIFACT_SHA" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2]; assert d.get('name')==sys.argv[3]; assert not d.get('expired'); assert d.get('digest')=='sha256:'+sys.argv[4]
print('PASS exact 26560 artifact metadata/digest')
PY
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
verify_base_artifact_and_reconstruct "$ARTZIP"

echo "=== 26561 GATE 2: candidate-first transform / ownership / exact runtime GLSL / patches ==="
build_candidate_and_precompile_proof

echo "=== 26561 GATE 3: pinned real glslangValidator on exact runtime-expanded GLSL ==="
run_real_glsl

echo "=== 26561 GATE 4: controlled live install / real Kotlin+Java / full assemble ==="
LIVE_PRE="$WORK/live_preinstall.sha256"
manifest_audited "$ROOT" "$LIVE_PRE"
VENDOR_PRE="$WORK/vendor_preinstall.sha256"; vendor_manifest "$ROOT" "$VENDOR_PRE"
cmp "$VENDOR_PRE" "$VENDOR_PIN" >/dev/null || fail "repository native/vendor drift before install"
rm -rf "$ROOT/app/src/main" "$ROOT/app/version.properties" "$ROOT/app/build.gradle"
cp -a "$AFTER/app/src/main" "$ROOT/app/src/"
cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"
cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"
manifest_audited "$ROOT" "$WORK/live_installed.sha256"
cmp "$WORK/live_installed.sha256" "$CAND_PIN" >/dev/null || fail "live source differs from frozen candidate"
python3 "$VALIDATE" --base "$BASE" --candidate "$ROOT"
rm -rf "$ROOT/app/build/outputs/apk/debug"
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
python3 - "$OUT/26561_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]);s=p.read_text().replace('REAL KOTLIN COMPILE: NOT RUN YET','REAL KOTLIN COMPILE: PASS').replace('REAL JAVA COMPILE: NOT RUN YET','REAL JAVA COMPILE: PASS');p.write_text(s)
PY
set_report "REAL KOTLIN COMPILE" "PASS"
set_report "REAL JAVA COMPILE" "PASS"
./gradlew :app:assembleDebug --stacktrace
python3 - "$OUT/26561_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]);s=p.read_text().replace('NATIVE/NDK COMPILE: NOT RUN YET (covered by full assemble)','NATIVE/NDK COMPILE: PASS (full assemble)').replace('FULL ANDROID ASSEMBLE: NOT RUN YET','FULL ANDROID ASSEMBLE: PASS');p.write_text(s)
PY
set_report "NATIVE/NDK COMPILE" "PASS (full assemble)"
set_report "FULL ANDROID ASSEMBLE" "PASS"
mapfile -t APKS < <(find "$ROOT/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' -print)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#APKS[@]}"
mv "${APKS[0]}" "$FINAL"
[[ -s "$FINAL" ]] || fail "final APK missing/empty"
[[ "$(find "$ROOT/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' | wc -l)" -eq 0 ]] || fail "duplicate APK remained in Gradle output"
sha256sum "$FINAL" > "$OUT/26561_V1_APK.sha256"
pass "real Kotlin/Java/NDK compilers + full assemble + exactly one intended APK"

echo "=== 26561 GATE 5: post-build frozen candidate / protected / native / vendor invariance ==="
manifest_audited "$ROOT" "$OUT/26561_postbuild_runtime.sha256"
cmp "$OUT/26561_postbuild_runtime.sha256" "$CAND_PIN" >/dev/null || fail "post-build runtime source changed"
manifest_audited "$AFTER" "$OUT/26561_frozen_candidate_postbuild.sha256"
cmp "$OUT/26561_frozen_candidate_postbuild.sha256" "$CAND_PIN" >/dev/null || fail "frozen candidate changed"
vendor_manifest "$ROOT" "$OUT/26561_vendor_postbuild.sha256"
cmp "$OUT/26561_vendor_postbuild.sha256" "$VENDOR_PIN" >/dev/null || fail "native/vendor changed during build"
(cd "$ROOT" && sha256sum -c "$PROTECTED_CORE")
rm -rf "$WORK/runtime_glsl_post"; mkdir -p "$WORK/runtime_glsl_post"
python3 "$EXTRACT" --root "$ROOT" --out "$WORK/runtime_glsl_post" >/dev/null
(cd "$WORK/runtime_glsl_post" && sha256sum -c "$RUNTIME_GLSL_PIN")
python3 - "$OUT/26561_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]);p.write_text(p.read_text().replace('POST-BUILD INVARIANCE: NOT RUN YET','POST-BUILD INVARIANCE: PASS'))
PY
set_report "POST-BUILD INVARIANCE" "PASS"
pass "post-build invariance"

echo "=== 26561 GATE 6: clean candidate source export ==="
tar --sort=name --mtime='UTC 2020-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26561_V1_candidate_app_source.tar.gz" -C "$AFTER" app
sha256sum "$OUT/26561_V1_candidate_app_source.tar.gz" > "$OUT/26561_V1_candidate_app_source.tar.gz.sha256"
cp "$CAND_PIN" "$OUT/26561_V1_candidate_source.sha256"
set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS"
pass "26561 V1 BUILD-PROVEN Actions output"
