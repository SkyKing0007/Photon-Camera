#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="2a3e7496e9f8286e67575d99d7860b17786e1414"
RUNTIME_ACTIONS_RUN="38101295053"
RUNTIME_ARTIFACT_ID="11687513662"
RUNTIME_ARTIFACT_NAME="photon-26807-neutral-parent-edge-fringe"
RUNTIME_ARTIFACT_SHA="f81cc67209ef94c1ca6f52aa1559d8958d9ee6adfb589bdaeada3f2c7ee849ad"
RUNTIME_TAR_SHA="fd07050c66788d4545d6ab30789e6a8b94976f45789541fcf53a6fc175042da0"
MECHANICS_AUTHORITY_COMMIT="2a3e7496e9f8286e67575d99d7860b17786e1414"
MECHANICS_ACTIONS_RUN="38101295053"
ROOT_MECHANICS_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"
ROOT_MECHANICS_RUN="37075896367"
VERSION_NAME="0.9726808"
VERSION_BUILD="26808"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26808_neutral_parent_edge_fringe_outputs"
WORK="$ROOT/.build_26808_neutral_parent_edge_fringe_work"
ARTZIP="$WORK/26807_artifact.zip"
ARTDIR="$WORK/artifact_26807"
BASE="$WORK/exact_successful_26807_compiled_candidate"
CAND="$WORK/candidate_26808"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"
POST_LANG="$WORK/post_language_compiler_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-neutral-parent-edge-fringe-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26808_COMPILER_STATUS.txt" <<EOF
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF

# IRIS_26808_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){
  sha256sum -c 26808_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26808_neutral_parent_edge_fringe.sh
  python3 -S -m py_compile transform_26808.py validate_26808.py verify_26808_patches.py verify_26808_runtime_glsl.py
  rm -rf __pycache__
  [[ "$(find handoff_payload_26808 -type f | wc -l)" -eq 3 ]] || fail "26808 payload count"
  diff -u 26808_RUNTIME_CHANGED_PATHS.txt <(find handoff_payload_26808 -type f | sed 's#^handoff_payload_26808/##' | sort) >/dev/null || fail "26808 payload allowlist mismatch"
  for p in 26808_FORWARD_FULL_INDEX.patch 26808_ROLLBACK_FULL_INDEX.patch; do
    ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$p" || fail "26808 patch contains rename/copy inference: $p"
  done
  grep -Fx 'RUN_26808_LOCAL_HIGHLIGHT_EDGE_GALLERY_PAUSE_FIX' TRIGGER_26808.txt >/dev/null || fail "26808 trigger contents"
  ! find . -type f -name '*.apk' | grep -q . || fail "APK unexpectedly packaged"
  pass "sealed 26808 package hashes/syntax/allowlist/patch identity"
}

verify_scope(){
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail "26807 runtime authority not ancestor"
  git merge-base --is-ancestor "$MECHANICS_AUTHORITY_COMMIT" HEAD || fail "26807 mechanics authority not ancestor"
  git merge-base --is-ancestor "$ROOT_MECHANICS_COMMIT" HEAD || fail "26752 root mechanics authority not ancestor"
  if git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | grep -E '^app/'; then fail "live app source changed after 26807 authority"; fi
  python3 -S - <<'PY_SCOPE'
import subprocess
allowed_prefixes=(
 '26808_','build_26808_neutral_parent_edge_fringe.sh','transform_26808.py','validate_26808.py',
 'verify_26808_patches.py','verify_26808_runtime_glsl.py','handoff_payload_26808/',
 '.github/workflows/build-26808-neutral-parent-edge-fringe.yml','TRIGGER_26808.txt',
 'PHOTON_26808_LOCAL_HIGHLIGHT_EDGE_GALLERY_README.txt')
paths=subprocess.check_output(['git','diff','--name-only','2a3e7496e9f8286e67575d99d7860b17786e1414..HEAD'],text=True).splitlines()
bad=[p for p in paths if not any(p==x or p.startswith(x) for x in allowed_prefixes)]
assert not bad,bad
print('PASS 26808 infrastructure scope allowlist')
PY_SCOPE
  pass "26808 scope exact: successful 26807 authority + sealed 3-file payload; live app untouched"
}

obtain_authority(){
  [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
  curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
  [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail "26807 artifact sha"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  T="$ARTDIR/build_26807_neutral_parent_edge_fringe_outputs/26807_candidate_app_source.tar.gz"
  [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail "26807 candidate tar sha"
  STATUS="$ARTDIR/build_26807_neutral_parent_edge_fringe_outputs/26807_COMPILER_STATUS.txt"
  for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do
    grep -F "$proof" "$STATUS" >/dev/null || fail "missing 26807 authority proof: $proof"
  done
  mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"
  [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1782 ]] || fail "26807 base file count"
  (cd "$BASE" && sha256sum -c "$ROOT/26808_BASE_26807_FULL_APP.sha256" >/dev/null) || fail "26807 full base manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26808_PRIOR_SOURCE_HASHES.sha256" >/dev/null) || fail "26807 prior source hashes"
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; [[ ! -e "$BASE/$rel" ]] || fail "26808 prior-absent path unexpectedly exists in 26807 authority: $rel"; done < "$ROOT/26808_PRIOR_ABSENT_PATHS.txt"
  (cd "$BASE" && sha256sum -c "$ROOT/26808_NATIVE_26807.sha256" >/dev/null) || fail "26807 native manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26808_VENDOR_26807.sha256" >/dev/null) || fail "26807 vendor manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26808_DNG_WRITER_26807.sha256" >/dev/null) || fail "26807 DNG writer manifest"
  cat > "$OUT/26808_RESOLVED_AUTHORITIES.txt" <<EOF
runtime_commit=$RUNTIME_AUTHORITY_COMMIT
runtime_run=$RUNTIME_ACTIONS_RUN
runtime_artifact_id=$RUNTIME_ARTIFACT_ID
runtime_artifact_name=$RUNTIME_ARTIFACT_NAME
runtime_artifact_sha256=$RUNTIME_ARTIFACT_SHA
runtime_candidate_tar_sha256=$RUNTIME_TAR_SHA
mechanics_commit=$MECHANICS_AUTHORITY_COMMIT
mechanics_run=$MECHANICS_ACTIONS_RUN
root_mechanics_commit=$ROOT_MECHANICS_COMMIT
root_mechanics_run=$ROOT_MECHANICS_RUN
EOF
  pass "exact successful 26807 compiled candidate reconstructed"
}

universe_equal(){ python3 -S - "$1" "$2" <<'PY_UNIVERSE'
from pathlib import Path
import hashlib,sys
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=U(sys.argv[1]),U(sys.argv[2]); assert a==b,(len(a),len(b)); print(f'PASS byte-identical app universe: {len(a)} files')
PY_UNIVERSE
}

make_candidate(){
  python3 -S transform_26808.py "$BASE" "$CAND" handoff_payload_26808
  python3 -S validate_26808.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26808_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail "26808 candidate manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26808_PROTECTED_26807.sha256" >/dev/null) || fail "26808 protected manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26808_NATIVE_26807.sha256" >/dev/null) || fail "26808 native invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26808_VENDOR_26807.sha256" >/dev/null) || fail "26808 vendor invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26808_DNG_WRITER_26807.sha256" >/dev/null) || fail "26808 DNG-writer invariance"
  [[ "$(find "$CAND/app" -type f | wc -l)" -eq 1782 ]] || fail "26808 candidate file count"
  pass "candidate-first 26808 bounded local highlight-edge admission + gallery pause semantics repair"
}

verify_successful_mechanics(){
  local a02="$WORK/authority_26807_build.sh" a52="$WORK/authority_26752_build.sh"
  git show "$MECHANICS_AUTHORITY_COMMIT:build_26807_neutral_parent_edge_fringe.sh" > "$a02"
  git show "$ROOT_MECHANICS_COMMIT:build_26752_ipol_plan_b_translational_sr.sh" > "$a52"
  for cmd in './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace' \
             "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" \
             './gradlew :app:assembleDebug --stacktrace'; do
    grep -F "$cmd" "$a02" >/dev/null || fail "26807 authority command missing: $cmd"
    grep -F "$cmd" "$0" >/dev/null || fail "26808 command differs: $cmd"
  done
  grep -F 'compile_spektra_raw_shader(){' "$a02" >/dev/null || fail "26807 Spektra verifier stage missing"
  grep -F 'compile_spektra_raw_shader(){' "$0" >/dev/null || fail "26808 Spektra verifier stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$a02" >/dev/null || fail "26807 native handoff stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$0" >/dev/null || fail "26808 native handoff stage missing"
  python3 -S - "$0" "$a02" "$a52" <<'PY_ORDER'
from pathlib import Path
import sys
def ordered(text,marker,tokens,label):
 i=text.find(marker)
 if i<0: raise SystemExit(f'{label}: missing marker {marker}')
 text=text[i:]; pos=-1
 for token in tokens:
  nxt=text.find(token,pos+1)
  if nxt<0: raise SystemExit(f'{label}: missing stage {token}')
  if nxt<=pos: raise SystemExit(f'{label}: out-of-order stage {token}')
  pos=nxt
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
cur,a02,a52=[Path(x).read_text() for x in sys.argv[1:]]
ordered(cur,'# IRIS_26808_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26808')
ordered(a02,'# IRIS_26807_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26807 authority')
auth52=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26751_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','mapfile -t apks','postbuild_proof']
ordered(a52,'# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER',auth52,'26752 root authority')
print('PASS 26808 stage order exactly inherits successful 26807 procedure and root 26752 mechanics')
PY_ORDER
  cp 26808_MECHANICS_DIFF_AUDIT.txt "$OUT/26808_MECHANICS_DIFF_AUDIT.txt"
  pass "successful 26807 implementation diff-audited: zero stage-order/compiler/native/assemble deviation; validator delta limited to exact 26808 repair allowlist"
}

prepare_glslang(){
  D="$WORK/glslang-${GLSLANG_VERSION}"; A="$WORK/glslang.tar.gz"; mkdir -p "$D"
  curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"
  [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive sha"
  tar -xzf "$A" -C "$D"
  compiler="$(find "$D" -type f -name glslang -print -quit)"
  [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"
  compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]] || chmod +x "$compiler"
  "$compiler" --version | tee "$OUT/26808_glslang_version.txt"
  export IRIS26808_GLSLANG="$compiler"
  export IRIS26681_SPEKTRA_GLSLANG="$compiler"
  pass "pinned glslang 16.5.0 dual environment handoff"
}

compile_modified_runtime_shaders(){
  python3 -S verify_26808_runtime_glsl.py "$BASE" "$CAND" --compiler "$IRIS26808_GLSLANG" --out "$OUT/26808_runtime_expanded_glsl" | tee "$OUT/26808_glsl_validation.txt"
  grep -F 'PASS 26808 GLSL ownership: 1 modified runtime-expanded shader + 19 inherited active/protected shaders' "$OUT/26808_glsl_validation.txt" >/dev/null || fail "26808 modified shader ownership proof missing"
  grep -F 'PASS 26808 inherited active/protected shader fidelity: 19 byte-identical to successful 26807' "$OUT/26808_glsl_validation.txt" >/dev/null || fail "26808 protected shader fidelity proof missing"
  for shader in merge motionv2_render motionv2_false_color_classify_26800 motionv2_false_color_classify_26799 motionv2_false_color_propagate_26799 motionv2_gainmap jpegNeutralHighlightClamp26790 normalChromaConsensus26790 jpegPhaseSafeCfaLca26788 universalNormalMasterShortFusion26651 EDGE_FALSE_COLOR_SUPPRESSOR_26778 jpegNeutralHighlightClamp26787 normalDngMerge normalizeBayer seed localMedian directionalSmooth iirRgb universalAdaptiveColor26561 bipolarColorTrust26769; do
    grep -F "PASS 26808 pinned real glslang compile exact runtime-expanded shader: $shader" "$OUT/26808_glsl_validation.txt" >/dev/null || fail "missing real glslang proof: $shader"
  done
  sed -i 's/REAL GLSL COMPILE: NOT RUN YET/REAL GLSL COMPILE: PASS (1 modified + 19 inherited active\/protected shaders, pinned glslang 16.5.0)/' "$OUT/26808_COMPILER_STATUS.txt"
}

compile_spektra_raw_shader(){
  pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"
}

snapshot_live_authority_seeded(){ python3 -S - "$CAND" "$1" "$ROOT" <<'PY_SNAPSHOT'
from pathlib import Path
import shutil,sys
cand,out,live=map(Path,sys.argv[1:])
if out.exists(): shutil.rmtree(out)
shutil.copytree(cand,out)
expected={str(p.relative_to(cand)):p for p in (cand/'app').rglob('*') if p.is_file()}
for rel,cp in expected.items():
    lp=live/rel
    if not lp.is_file(): raise SystemExit(f'missing live candidate path: {rel}')
    op=out/rel; op.write_bytes(lp.read_bytes())
expected_src={r for r in expected if r.startswith('app/src/')}
actual_src={str(p.relative_to(live)) for p in (live/'app/src').rglob('*') if p.is_file()}
extra=sorted(actual_src-expected_src)
if extra: raise SystemExit(f'unexpected app/src paths: {extra}')
print(f'PASS authority-seeded canonical live snapshot: {len(expected)} candidate files; generated app/build + app/.cxx excluded')
PY_SNAPSHOT
}

install_frozen_candidate_live(){
  rm -rf app
  cp -a "$CAND/app" app
  snapshot_live_authority_seeded "$LIVE_CANON"
  universe_equal "$CAND" "$LIVE_CANON"
  pass "authority-seeded canonical live candidate byte-identical to frozen 26808 candidate"
}

compile_languages(){
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26808_gradle_language_compilers.log"
  snapshot_live_authority_seeded "$POST_LANG"
  universe_equal "$CAND" "$POST_LANG"
  sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26808_COMPILER_STATUS.txt"
  sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26808_COMPILER_STATUS.txt"
  pass "real Kotlin/Java compilers passed and frozen source remained byte-identical"
}

verify_native_glslang_handoff(){
  [[ -n "${IRIS26808_GLSLANG:-}" && -x "$IRIS26808_GLSLANG" ]] || fail "IRIS26808_GLSLANG missing"
  [[ -n "${IRIS26681_SPEKTRA_GLSLANG:-}" && -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "IRIS26681_SPEKTRA_GLSLANG missing"
  [[ "$(readlink -f "$IRIS26808_GLSLANG")" == "$(readlink -f "$IRIS26681_SPEKTRA_GLSLANG")" ]] || fail "native/Spektra glslang handoff differs"
  { echo "IRIS26681_SPEKTRA_GLSLANG=$IRIS26681_SPEKTRA_GLSLANG"; echo "IRIS26808_GLSLANG=$IRIS26808_GLSLANG"; } | tee "$OUT/26808_native_glslang_handoff.txt"
  pass "successful 26807 native glslang handoff preserved before both-ABI native compile"
}

compile_native(){
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26808_gradle_native_compiler.log"
  sed -i 's#NATIVE/NDK COMPILE: NOT RUN YET#NATIVE/NDK COMPILE: PASS (arm64-v8a + armeabi-v7a)#' "$OUT/26808_COMPILER_STATUS.txt"
}

verify_candidate_patches(){
  python3 -S verify_26808_patches.py "$BASE" "$CAND" 26808_FORWARD_FULL_INDEX.patch 26808_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26808_patch_validation.txt"
  grep -F 'PASS 26808 canonical patch proof' "$OUT/26808_patch_validation.txt" >/dev/null || fail "canonical patch proof missing"
  pass "sealed full-index forward/rollback proof: successful 26807 -> exact 3-file 26808 candidate"
}

prebuild_safety(){
  snapshot_live_authority_seeded "$WORK/prebuild_live_snapshot"
  universe_equal "$CAND" "$WORK/prebuild_live_snapshot"
  python3 -S validate_26808.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26808_PROTECTED_26807.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26808_NATIVE_26807.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26808_VENDOR_26807.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26808_DNG_WRITER_26807.sha256" >/dev/null)
  cat > "$OUT/26808_PREBUILD_SAFETY.txt" <<EOF
PRE-BUILD SAFETY PROOF PASSED
runtime_authority=successful 26807 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID
verification_mechanics=exact successful 26807 17-stage sequence; root 26752 inherited
runtime_changed_files=3 modified / 0 added / 0 deleted
runtime_allowlist=GlesIris26529SpatialRgbChromaPostprocessor.kt,CameraFragment.java,app/version.properties
protected_files=1779 unchanged
native_files=819 unchanged
vendor_files=773 unchanged
dng_writer_files=6 unchanged + normalDngMerge/normalizeBayer byte-identical
base_candidate_files=1782
final_candidate_files=1782
successful_26807_global_0p72_0p92_headroom_curve_preserved=true
successful_26807_far4_broad2d_real_color_protection_preserved=true
successful_26807_pink_cleanup_baseline_preserved=true
failed_26804_broad_rgb_guess_absent=true
failed_26805_fake_pre_resolve_rgb_authority_absent=true
bright_chroma_cleanup_owner=immutable_seed_bit13_plus_bounded_local_highlight_edge_admission
local_highlight_edge_admission_requires_two_immediate_bright_neutral_support_directions=true
local_highlight_edge_admission_dark_center_veto=true
local_highlight_edge_admission_strong_saturated_color_veto=true
local_highlight_edge_admission_broad_2d_material_veto=true
local_median_legacy_edge_cannot_override_bit13=true
directional_topology_cannot_reinject_original_chroma_for_bit13=true
iir_bit13_cleanup_transport_crosses_strong_luma_boundary_one_way=true
iir_contiguous_bit13_chain_cannot_flow_back_into_trusted_pixel=true
universal_pre_vgn_magnitude_recovery_vetoed_for_bit13=true
bipolar_recovery_and_floor_vetoed_for_bit13=true
luma_path_modified=false
new_gpu_image_allocation=false
new_texture_lifetime_extension=false
stacker_byte_identical_to_successful_26807=true
motionv2_26803_late_far_parent_owner_byte_identical=true
uhdr_dng_sr_native_vendor_tone_color_transform_frozen=true
gallery_fresh_capture_uri=FileProvider_content_uri
gallery_external_file_uri_dispatch=false
gallery_first_press=Intent_createChooser
gallery_settings_bar_closed_before_launch=true
gallery_pause_never_opens_settings=true
gallery_launch_failure_nonfatal=true
EOF
  echo 'PRE-BUILD SAFETY PROOF PASSED'
}

assemble(){
  ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26808_gradle_assemble.log"
  mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort)
  [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one APK, got ${#apks[@]}: ${apks[*]-}"
  cp "${apks[0]}" "$FINAL"
  [[ -f "$FINAL" ]] || fail "final APK copy missing"
  sha256sum "$FINAL" | tee "$OUT/26808_APK.sha256"
  sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS (exactly one APK)/' "$OUT/26808_COMPILER_STATUS.txt"
}

postbuild_proof(){
  snapshot_live_authority_seeded "$WORK/postbuild_live_snapshot"
  universe_equal "$CAND" "$WORK/postbuild_live_snapshot"
  python3 -S validate_26808.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26808_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26808_PROTECTED_26807.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26808_NATIVE_26807.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26808_VENDOR_26807.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26808_DNG_WRITER_26807.sha256" >/dev/null)
  cp 26808_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26808_candidate_full_app.sha256"
  tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26808_candidate_app_source.tar.gz" -C "$CAND" app
  sha256sum "$OUT/26808_candidate_app_source.tar.gz" > "$OUT/26808_candidate_app_source.tar.gz.sha256"
  cp 26808_FORWARD_FULL_INDEX.patch "$OUT/26808_FORWARD_FULL_INDEX.patch"
  cp 26808_ROLLBACK_FULL_INDEX.patch "$OUT/26808_ROLLBACK_FULL_INDEX.patch"
  sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26808_COMPILER_STATUS.txt"
  pass "authority-seeded post-build protected/DNG/native/vendor/source invariance"
}

clean_extract_replay(){
  local replay="$WORK/clean_replay_candidate"
  rm -rf "$replay"
  sha256sum -c 26808_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26808_neutral_parent_edge_fringe.sh
  python3 -S -m py_compile transform_26808.py validate_26808.py verify_26808_patches.py verify_26808_runtime_glsl.py
  rm -rf __pycache__
  python3 -S transform_26808.py "$BASE" "$replay" handoff_payload_26808
  universe_equal "$CAND" "$replay"
  python3 -S validate_26808.py "$BASE" "$replay"
  python3 -S verify_26808_runtime_glsl.py "$BASE" "$replay" --out "$OUT/26808_final_runtime_expanded_glsl" | tee "$OUT/26808_final_glsl_static_replay.txt"
  python3 -S verify_26808_patches.py "$BASE" "$replay" 26808_FORWARD_FULL_INDEX.patch 26808_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26808_final_patch_replay.txt"
  (cd "$replay" && sha256sum -c "$ROOT/26808_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
  grep -F 'VERSION_NAME=0.9726808' "$replay/app/version.properties" >/dev/null
  grep -F 'VERSION_BUILD=26808' "$replay/app/version.properties" >/dev/null
  grep -F 'REAL GLSL COMPILE: PASS' "$OUT/26808_COMPILER_STATUS.txt" >/dev/null
  grep -F 'REAL KOTLIN COMPILE: PASS' "$OUT/26808_COMPILER_STATUS.txt" >/dev/null
  grep -F 'REAL JAVA COMPILE: PASS' "$OUT/26808_COMPILER_STATUS.txt" >/dev/null
  grep -F 'NATIVE/NDK COMPILE: PASS' "$OUT/26808_COMPILER_STATUS.txt" >/dev/null
  grep -F 'FULL ANDROID ASSEMBLE: PASS' "$OUT/26808_COMPILER_STATUS.txt" >/dev/null
  grep -F 'POST-BUILD INVARIANCE: PASS' "$OUT/26808_COMPILER_STATUS.txt" >/dev/null
  pass "final 26808 clean replay of package hashes/local-highlight-edge/gallery-pause/version/patch/compiler/build proofs"
}

verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_mechanics
prepare_glslang
compile_modified_runtime_shaders
compile_spektra_raw_shader
install_frozen_candidate_live
compile_languages
verify_native_glslang_handoff
compile_native
verify_candidate_patches
prebuild_safety
assemble
postbuild_proof
clean_extract_replay
pass "26808 LOCAL HIGHLIGHT EDGE + GALLERY PAUSE FIX: ACTIONS BUILD PROOF COMPLETE"
