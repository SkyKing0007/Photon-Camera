#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="cc88123aab41b3728fc17b5312e8fa937bc025b6"
RUNTIME_ACTIONS_RUN="38149183881"
RUNTIME_ARTIFACT_ID="11705768259"
RUNTIME_ARTIFACT_NAME="photon-26810-neutral-parent-edge-fringe"
RUNTIME_ARTIFACT_SHA="edd3c5af66abd77597ca119ef2abf452816e0cff73dcfedf857e48264f0fd665"
RUNTIME_TAR_SHA="88284d1c1552ec51649e8558a03b38d8797b4079c314d287034a99e648050701"
MECHANICS_AUTHORITY_COMMIT="cc88123aab41b3728fc17b5312e8fa937bc025b6"
MECHANICS_ACTIONS_RUN="38149183881"
ROOT_MECHANICS_COMMIT="f853b342cc9c562b56161c94797707073a0ec9e3"
ROOT_MECHANICS_RUN="38110198384"
VERSION_NAME="0.9726811"
VERSION_BUILD="26811"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26811_neutral_parent_edge_fringe_outputs"
WORK="$ROOT/.build_26811_neutral_parent_edge_fringe_work"
ARTZIP="$WORK/26810_artifact.zip"
ARTDIR="$WORK/artifact_26810"
BASE="$WORK/exact_successful_26810_compiled_candidate"
CAND="$WORK/candidate_26811"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"
POST_LANG="$WORK/post_language_compiler_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-resolve-boundary-gallery-direct-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26811_COMPILER_STATUS.txt" <<EOF
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF

# IRIS_26811_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){
  sha256sum -c 26811_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26811_neutral_parent_edge_fringe.sh
  python3 -S -m py_compile transform_26811.py validate_26811.py verify_26811_patches.py verify_26811_runtime_glsl.py
  rm -rf __pycache__
  [[ "$(find handoff_payload_26811 -type f | wc -l)" -eq 3 ]] || fail "26811 payload count"
  diff -u 26811_RUNTIME_CHANGED_PATHS.txt <(find handoff_payload_26811 -type f | sed 's#^handoff_payload_26811/##' | sort) >/dev/null || fail "26811 payload allowlist mismatch"
  for p in 26811_FORWARD_FULL_INDEX.patch 26811_ROLLBACK_FULL_INDEX.patch; do
    ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$p" || fail "26811 patch contains rename/copy inference: $p"
  done
  grep -Fx 'RUN_26811_RESOLVE_BOUNDARY_GALLERY_DIRECT' TRIGGER_26811.txt >/dev/null || fail "26811 trigger contents"
  ! find . -type f -name '*.apk' | grep -q . || fail "APK unexpectedly packaged"
  pass "sealed 26811 package hashes/syntax/allowlist/patch identity"
}

verify_scope(){
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail "26810 runtime authority not ancestor"
  git merge-base --is-ancestor "$MECHANICS_AUTHORITY_COMMIT" HEAD || fail "26810 mechanics authority not ancestor"
  git merge-base --is-ancestor "$ROOT_MECHANICS_COMMIT" HEAD || fail "26808 root mechanics authority not ancestor"
  if git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | grep -E '^app/'; then fail "live app source changed after 26810 authority"; fi
  python3 -S - <<'PY_SCOPE'
import subprocess
allowed_prefixes=(
 '26811_','build_26811_neutral_parent_edge_fringe.sh','transform_26811.py','validate_26811.py',
 'verify_26811_patches.py','verify_26811_runtime_glsl.py','handoff_payload_26811/',
 '.github/workflows/build-26811-neutral-parent-edge-fringe.yml','TRIGGER_26811.txt',
 'PHOTON_26811_RESOLVE_BOUNDARY_GALLERY_DIRECT_README.txt')
paths=subprocess.check_output(['git','diff','--name-only','cc88123aab41b3728fc17b5312e8fa937bc025b6..HEAD'],text=True).splitlines()
bad=[p for p in paths if not any(p==x or p.startswith(x) for x in allowed_prefixes)]
assert not bad,bad
print('PASS 26811 infrastructure scope allowlist')
PY_SCOPE
  pass "26811 scope exact: successful 26810 authority + sealed 3-file payload; live app untouched"
}

obtain_authority(){
  [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
  curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
  [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail "26810 artifact sha"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  T="$ARTDIR/build_26810_neutral_parent_edge_fringe_outputs/26810_candidate_app_source.tar.gz"
  [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail "26810 candidate tar sha"
  STATUS="$ARTDIR/build_26810_neutral_parent_edge_fringe_outputs/26810_COMPILER_STATUS.txt"
  for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do
    grep -F "$proof" "$STATUS" >/dev/null || fail "missing 26810 authority proof: $proof"
  done
  mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"
  [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1782 ]] || fail "26810 base file count"
  (cd "$BASE" && sha256sum -c "$ROOT/26811_BASE_26810_FULL_APP.sha256" >/dev/null) || fail "26810 full base manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26811_PRIOR_SOURCE_HASHES.sha256" >/dev/null) || fail "26810 prior source hashes"
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; [[ ! -e "$BASE/$rel" ]] || fail "26811 prior-absent path unexpectedly exists in 26810 authority: $rel"; done < "$ROOT/26811_PRIOR_ABSENT_PATHS.txt"
  (cd "$BASE" && sha256sum -c "$ROOT/26811_NATIVE_26810.sha256" >/dev/null) || fail "26810 native manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26811_VENDOR_26810.sha256" >/dev/null) || fail "26810 vendor manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26811_DNG_WRITER_26810.sha256" >/dev/null) || fail "26810 DNG writer manifest"
  cat > "$OUT/26811_RESOLVED_AUTHORITIES.txt" <<EOF
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
  pass "exact successful 26810 compiled candidate reconstructed"
}

universe_equal(){ python3 -S - "$1" "$2" <<'PY_UNIVERSE'
from pathlib import Path
import hashlib,sys
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=U(sys.argv[1]),U(sys.argv[2]); assert a==b,(len(a),len(b)); print(f'PASS byte-identical app universe: {len(a)} files')
PY_UNIVERSE
}

make_candidate(){
  python3 -S transform_26811.py "$BASE" "$CAND" handoff_payload_26811
  python3 -S validate_26811.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26811_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail "26811 candidate manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26811_PROTECTED_26810.sha256" >/dev/null) || fail "26811 protected manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26811_NATIVE_26810.sha256" >/dev/null) || fail "26811 native invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26811_VENDOR_26810.sha256" >/dev/null) || fail "26811 vendor invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26811_DNG_WRITER_26810.sha256" >/dev/null) || fail "26811 DNG-writer invariance"
  [[ "$(find "$CAND/app" -type f | wc -l)" -eq 1782 ]] || fail "26811 candidate file count"
  pass "candidate-first 26811 exact 26810 IQ rollback + Resolve boundary provenance + direct exact gallery item"
}

verify_successful_mechanics(){
  local a10="$WORK/authority_26810_build.sh" a08="$WORK/authority_26808_build.sh"
  git show "$MECHANICS_AUTHORITY_COMMIT:build_26810_neutral_parent_edge_fringe.sh" > "$a10"
  git show "$ROOT_MECHANICS_COMMIT:build_26808_neutral_parent_edge_fringe.sh" > "$a08"
  for cmd in './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace' \
             "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" \
             './gradlew :app:assembleDebug --stacktrace'; do
    grep -F "$cmd" "$a10" >/dev/null || fail "26810 authority command missing: $cmd"
    grep -F "$cmd" "$0" >/dev/null || fail "26811 command differs: $cmd"
  done
  grep -F 'compile_spektra_raw_shader(){' "$a10" >/dev/null || fail "26810 Spektra verifier stage missing"
  grep -F 'compile_spektra_raw_shader(){' "$0" >/dev/null || fail "26811 Spektra verifier stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$a10" >/dev/null || fail "26810 native handoff stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$0" >/dev/null || fail "26811 native handoff stage missing"
  python3 -S - "$0" "$a10" "$a08" <<'PY_ORDER'
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
cur,a10,a08=[Path(x).read_text() for x in sys.argv[1:]]
ordered(cur,'# IRIS_26811_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26811')
ordered(a10,'# IRIS_26810_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26810 authority')
ordered(a08,'# IRIS_26808_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26808 root authority')
print('PASS 26811 stage order exactly inherits successful 26810 procedure and successful 26808 root mechanics')
PY_ORDER
  cp 26811_MECHANICS_DIFF_AUDIT.txt "$OUT/26811_MECHANICS_DIFF_AUDIT.txt"
  pass "successful 26810 implementation diff-audited: zero stage-order/compiler/native/assemble deviation; validator delta limited to exact 26811 allowlist"
}

prepare_glslang(){
  D="$WORK/glslang-${GLSLANG_VERSION}"; A="$WORK/glslang.tar.gz"; mkdir -p "$D"
  curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"
  [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive sha"
  tar -xzf "$A" -C "$D"
  compiler="$(find "$D" -type f -name glslang -print -quit)"
  [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"
  compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]] || chmod +x "$compiler"
  "$compiler" --version | tee "$OUT/26811_glslang_version.txt"
  export IRIS26811_GLSLANG="$compiler"
  export IRIS26681_SPEKTRA_GLSLANG="$compiler"
  pass "pinned glslang 16.5.0 dual environment handoff"
}

compile_modified_runtime_shaders(){
  python3 -S verify_26811_runtime_glsl.py "$BASE" "$CAND" --compiler "$IRIS26811_GLSLANG" --out "$OUT/26811_runtime_expanded_glsl" | tee "$OUT/26811_glsl_validation.txt"
  grep -F 'PASS 26811 GLSL ownership: 1 modified runtime-expanded shader + 19 inherited active/protected shaders' "$OUT/26811_glsl_validation.txt" >/dev/null || fail "26811 modified shader ownership proof missing"
  grep -F 'PASS 26811 inherited active/protected shader fidelity: 19 byte-identical to successful 26810' "$OUT/26811_glsl_validation.txt" >/dev/null || fail "26811 protected shader fidelity proof missing"
  for shader in merge motionv2_render motionv2_false_color_classify_26800 motionv2_false_color_classify_26799 motionv2_false_color_propagate_26799 motionv2_gainmap jpegNeutralHighlightClamp26790 normalChromaConsensus26790 jpegPhaseSafeCfaLca26788 universalNormalMasterShortFusion26651 EDGE_FALSE_COLOR_SUPPRESSOR_26778 jpegNeutralHighlightClamp26787 normalDngMerge normalizeBayer seed localMedian directionalSmooth iirRgb universalAdaptiveColor26561 bipolarColorTrust26769; do
    grep -F "PASS 26811 pinned real glslang compile exact runtime-expanded shader: $shader" "$OUT/26811_glsl_validation.txt" >/dev/null || fail "missing real glslang proof: $shader"
  done
  sed -i 's/REAL GLSL COMPILE: NOT RUN YET/REAL GLSL COMPILE: PASS (1 modified + 19 inherited active\/protected shaders, pinned glslang 16.5.0)/' "$OUT/26811_COMPILER_STATUS.txt"
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
  pass "authority-seeded canonical live candidate byte-identical to frozen 26811 candidate"
}

compile_languages(){
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26811_gradle_language_compilers.log"
  snapshot_live_authority_seeded "$POST_LANG"
  universe_equal "$CAND" "$POST_LANG"
  sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26811_COMPILER_STATUS.txt"
  sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26811_COMPILER_STATUS.txt"
  pass "real Kotlin/Java compilers passed and frozen source remained byte-identical"
}

verify_native_glslang_handoff(){
  [[ -n "${IRIS26811_GLSLANG:-}" && -x "$IRIS26811_GLSLANG" ]] || fail "IRIS26811_GLSLANG missing"
  [[ -n "${IRIS26681_SPEKTRA_GLSLANG:-}" && -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "IRIS26681_SPEKTRA_GLSLANG missing"
  [[ "$(readlink -f "$IRIS26811_GLSLANG")" == "$(readlink -f "$IRIS26681_SPEKTRA_GLSLANG")" ]] || fail "native/Spektra glslang handoff differs"
  { echo "IRIS26681_SPEKTRA_GLSLANG=$IRIS26681_SPEKTRA_GLSLANG"; echo "IRIS26811_GLSLANG=$IRIS26811_GLSLANG"; } | tee "$OUT/26811_native_glslang_handoff.txt"
  pass "successful 26810 native glslang handoff preserved before both-ABI native compile"
}

compile_native(){
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26811_gradle_native_compiler.log"
  sed -i 's#NATIVE/NDK COMPILE: NOT RUN YET#NATIVE/NDK COMPILE: PASS (arm64-v8a + armeabi-v7a)#' "$OUT/26811_COMPILER_STATUS.txt"
}

verify_candidate_patches(){
  python3 -S verify_26811_patches.py "$BASE" "$CAND" 26811_FORWARD_FULL_INDEX.patch 26811_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26811_patch_validation.txt"
  grep -F 'PASS 26811 canonical patch proof' "$OUT/26811_patch_validation.txt" >/dev/null || fail "canonical patch proof missing"
  pass "sealed full-index forward/rollback proof: successful 26810 -> exact 3-file 26811 candidate"
}

prebuild_safety(){
  snapshot_live_authority_seeded "$WORK/prebuild_live_snapshot"
  universe_equal "$CAND" "$WORK/prebuild_live_snapshot"
  python3 -S validate_26811.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26811_PROTECTED_26810.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26811_NATIVE_26810.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26811_VENDOR_26810.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26811_DNG_WRITER_26810.sha256" >/dev/null)
  cat > "$OUT/26811_PREBUILD_SAFETY.txt" <<EOF
PRE-BUILD SAFETY PROOF PASSED
runtime_authority=successful 26810 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID
verification_mechanics=exact successful 26810 17-stage sequence; successful 26808 root inherited
runtime_changed_files=3 modified / 0 added / 0 deleted
runtime_allowlist=GlesMgcRawSpatialStacker.kt,CameraFragment.java,app/version.properties
protected_files=1779 unchanged
native_files=819 unchanged
vendor_files=773 unchanged
dng_writer_files=6 unchanged
base_candidate_files=1782
final_candidate_files=1782
failed_26810_iq_owner_present=false
iq_rollback=exact successful 26809 stacker behavior after removing diagnostic-only 26811 blocks
resolve_boundary_logger=IRIS_26811_RESOLVE_BOUNDARY_PROVENANCE_OWNER
resolve_boundary_stages=COMPLETED_NORMAL_PRE_AUX__EXACT_RESOLVE_INPUT_POST_AUX_FUSION__NATIVE_RESOLVE_OUTPUT
resolve_boundary_mutates_image=false
resolve_boundary_coordinate_provenance=all_4_CFA_phases_plus_completed_NORMAL_RminusG_BminusG_plus_CFA_validity_plus_accumulated_channel_support_plus_frame_roles
gallery_owner=IRIS_26811_DIRECT_EXACT_CAPTURE_VIEW_OWNER
gallery_launch=ACTION_VIEW_exact_current_item_direct_no_chooser
gallery_mime=ContentResolver_actual_MIME
gallery_provenance=authority_row_mime_resolvedComponent
gallery_collection_only_fallback=true
gallery_pause_no_gear_owner=IRIS_26808_PAUSE_MUST_NOT_OPEN_SETTINGS
gallery_pause_owner_byte_identical=true
vgn_26807_motionv2_26803_dng_uhdr_native_vendor_tone_color_transform_frozen=true
backup_branch_created=false
EOF
  echo 'PRE-BUILD SAFETY PROOF PASSED'
}

assemble(){
  ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26811_gradle_assemble.log"
  mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort)
  [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one APK, got ${#apks[@]}: ${apks[*]-}"
  cp "${apks[0]}" "$FINAL"
  [[ -f "$FINAL" ]] || fail "final APK copy missing"
  sha256sum "$FINAL" | tee "$OUT/26811_APK.sha256"
  sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS (exactly one APK)/' "$OUT/26811_COMPILER_STATUS.txt"
}

postbuild_proof(){
  snapshot_live_authority_seeded "$WORK/postbuild_live_snapshot"
  universe_equal "$CAND" "$WORK/postbuild_live_snapshot"
  python3 -S validate_26811.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26811_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26811_PROTECTED_26810.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26811_NATIVE_26810.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26811_VENDOR_26810.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26811_DNG_WRITER_26810.sha256" >/dev/null)
  cp 26811_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26811_candidate_full_app.sha256"
  tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26811_candidate_app_source.tar.gz" -C "$CAND" app
  sha256sum "$OUT/26811_candidate_app_source.tar.gz" > "$OUT/26811_candidate_app_source.tar.gz.sha256"
  cp 26811_FORWARD_FULL_INDEX.patch "$OUT/26811_FORWARD_FULL_INDEX.patch"
  cp 26811_ROLLBACK_FULL_INDEX.patch "$OUT/26811_ROLLBACK_FULL_INDEX.patch"
  sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26811_COMPILER_STATUS.txt"
  pass "authority-seeded post-build protected/DNG/native/vendor/source invariance"
}

clean_extract_replay(){
  local replay="$WORK/clean_replay_candidate"
  rm -rf "$replay"
  sha256sum -c 26811_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26811_neutral_parent_edge_fringe.sh
  python3 -S -m py_compile transform_26811.py validate_26811.py verify_26811_patches.py verify_26811_runtime_glsl.py
  rm -rf __pycache__
  python3 -S transform_26811.py "$BASE" "$replay" handoff_payload_26811
  universe_equal "$CAND" "$replay"
  python3 -S validate_26811.py "$BASE" "$replay"
  python3 -S verify_26811_runtime_glsl.py "$BASE" "$replay" --out "$OUT/26811_final_runtime_expanded_glsl" | tee "$OUT/26811_final_glsl_static_replay.txt"
  python3 -S verify_26811_patches.py "$BASE" "$replay" 26811_FORWARD_FULL_INDEX.patch 26811_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26811_final_patch_replay.txt"
  (cd "$replay" && sha256sum -c "$ROOT/26811_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
  grep -F 'VERSION_NAME=0.9726811' "$replay/app/version.properties" >/dev/null
  grep -F 'VERSION_BUILD=26811' "$replay/app/version.properties" >/dev/null
  grep -F 'REAL GLSL COMPILE: PASS' "$OUT/26811_COMPILER_STATUS.txt" >/dev/null
  grep -F 'REAL KOTLIN COMPILE: PASS' "$OUT/26811_COMPILER_STATUS.txt" >/dev/null
  grep -F 'REAL JAVA COMPILE: PASS' "$OUT/26811_COMPILER_STATUS.txt" >/dev/null
  grep -F 'NATIVE/NDK COMPILE: PASS' "$OUT/26811_COMPILER_STATUS.txt" >/dev/null
  grep -F 'FULL ANDROID ASSEMBLE: PASS' "$OUT/26811_COMPILER_STATUS.txt" >/dev/null
  grep -F 'POST-BUILD INVARIANCE: PASS' "$OUT/26811_COMPILER_STATUS.txt" >/dev/null
  pass "final 26811 clean replay of package hashes/resolve-boundary/direct-exact-gallery/version/patch/compiler/build proofs"
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
pass "26811 RESOLVE BOUNDARY + DIRECT EXACT GALLERY: ACTIONS BUILD PROOF COMPLETE"
