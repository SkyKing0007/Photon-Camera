#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="38d2f4e18ecd8b418e4f999b424412536cd0a67e"
RUNTIME_ACTIONS_RUN="37639098496"
RUNTIME_ARTIFACT_ID="11491284890"
RUNTIME_ARTIFACT_NAME="photon-26781-quad-coherent-cfa"
RUNTIME_ARTIFACT_SHA="b77eb5daf5a6cf7818e36ac25e325cdcfe44774e015536f26578e5df8753d495"
RUNTIME_TAR_SHA="04d52bafd1ee9d85ca2f893e7e94624e82700989d47feedd383c25c018e8ab13"
MECHANICS_AUTHORITY_COMMIT="38d2f4e18ecd8b418e4f999b424412536cd0a67e"
MECHANICS_ACTIONS_RUN="37639098496"
MECHANICS_SCRIPT_SHA="35c37940ec48f4f2177a0d9b1c185b4fc0f53d7d3f3683e7396cf6fef7c6dcb9"
ROOT_MECHANICS_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"
ROOT_MECHANICS_RUN="37075896367"
VERSION_NAME="0.9726782"
VERSION_BUILD="26782"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26782_edge_safe_cfa_highlight_outputs"
WORK="$ROOT/.build_26782_edge_safe_cfa_highlight_work"
ARTZIP="$WORK/26781_artifact.zip"
ARTDIR="$WORK/artifact_26781"
BASE="$WORK/exact_successful_26781_compiled_candidate"
CAND="$WORK/candidate_26782"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"
POST_LANG="$WORK/post_language_compiler_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-edge-safe-cfa-highlight-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26782_COMPILER_STATUS.txt" <<EOF
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF

# IRIS_26782_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){
  sha256sum -c 26782_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26782_edge_safe_cfa_highlight.sh
  python3 -S -m py_compile transform_26782.py validate_26782.py verify_26782_patches.py verify_26782_embedded_glsl.py
  rm -rf __pycache__
  [[ "$(find handoff_payload_26782 -type f | wc -l)" -eq 3 ]] || fail "26782 payload count"
  diff -u 26782_RUNTIME_CHANGED_PATHS.txt <(find handoff_payload_26782 -type f | sed 's#^handoff_payload_26782/##' | sort) >/dev/null || fail "26782 payload allowlist mismatch"
  for p in 26782_FORWARD_FULL_INDEX.patch 26782_ROLLBACK_FULL_INDEX.patch; do
    ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$p" || fail "26782 patch contains rename/copy inference: $p"
  done
  grep -Fx 'RUN_26782_EDGE_SAFE_CFA_HIGHLIGHT' TRIGGER_26782.txt >/dev/null || fail "26782 trigger contents"
  ! find . -type f -name '*.apk' | grep -q . || fail "APK unexpectedly packaged"
  pass "sealed 26782 package hashes/syntax/allowlist/patch identity"
}
verify_scope(){
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail "26781 runtime authority not ancestor"
  git merge-base --is-ancestor "$MECHANICS_AUTHORITY_COMMIT" HEAD || fail "26781 mechanics authority not ancestor"
  git merge-base --is-ancestor "$ROOT_MECHANICS_COMMIT" HEAD || fail "26752 root mechanics authority not ancestor"
  if git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | grep -E '^app/'; then fail "live app source changed after 26781 authority"; fi
  python3 -S - <<'PY_SCOPE'
import subprocess
allowed_prefixes=('26782_','build_26782_edge_safe_cfa_highlight.sh','transform_26782.py','validate_26782.py','verify_26782_patches.py','verify_26782_embedded_glsl.py','handoff_payload_26782/','.github/workflows/build-26782-edge-safe-cfa-highlight.yml','TRIGGER_26782.txt')
paths=subprocess.check_output(['git','diff','--name-only','38d2f4e18ecd8b418e4f999b424412536cd0a67e..HEAD'],text=True).splitlines()
bad=[p for p in paths if not any(p==x or p.startswith(x) for x in allowed_prefixes)]
assert not bad,bad
print('PASS 26782 infrastructure scope allowlist')
PY_SCOPE
  pass "26782 scope exact: successful 26781 authority + sealed 3-file payload; live app untouched"
}
obtain_authority(){
  [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
  curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
  [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail "26781 artifact sha"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  T="$ARTDIR/build_26781_quad_coherent_cfa_outputs/26781_candidate_app_source.tar.gz"
  [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail "26781 candidate tar sha"
  STATUS="$ARTDIR/build_26781_quad_coherent_cfa_outputs/26781_COMPILER_STATUS.txt"
  for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$STATUS" >/dev/null || fail "missing 26781 authority proof: $proof"; done
  mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"
  [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1779 ]] || fail "26781 base file count"
  (cd "$BASE" && sha256sum -c "$ROOT/26782_BASE_26781_FULL_APP.sha256" >/dev/null) || fail "26781 full base manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26782_NATIVE_26781.sha256" >/dev/null) || fail "26781 native manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26782_VENDOR_26781.sha256" >/dev/null) || fail "26781 vendor manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26782_DNG_26781.sha256" >/dev/null) || fail "26781 DNG manifest"
  cat > "$OUT/26782_RESOLVED_AUTHORITIES.txt" <<EOF
runtime_commit=$RUNTIME_AUTHORITY_COMMIT
runtime_run=$RUNTIME_ACTIONS_RUN
runtime_artifact_id=$RUNTIME_ARTIFACT_ID
runtime_artifact_name=$RUNTIME_ARTIFACT_NAME
runtime_artifact_sha256=$RUNTIME_ARTIFACT_SHA
runtime_candidate_tar_sha256=$RUNTIME_TAR_SHA
mechanics_commit=$MECHANICS_AUTHORITY_COMMIT
mechanics_run=$MECHANICS_ACTIONS_RUN
mechanics_script_sha256=$MECHANICS_SCRIPT_SHA
root_mechanics_commit=$ROOT_MECHANICS_COMMIT
root_mechanics_run=$ROOT_MECHANICS_RUN
EOF
  pass "exact successful 26781 compiled candidate reconstructed"
}
universe_equal(){ python3 -S - "$1" "$2" <<'PY_UNIVERSE'
from pathlib import Path
import hashlib,sys
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=U(sys.argv[1]),U(sys.argv[2]); assert a==b,(len(a),len(b)); print(f'PASS byte-identical app universe: {len(a)} files')
PY_UNIVERSE
}
make_candidate(){
  python3 -S transform_26782.py "$BASE" "$CAND" handoff_payload_26782
  python3 -S validate_26782.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26782_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail "26782 candidate manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26782_PROTECTED_26781.sha256" >/dev/null) || fail "26782 protected manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26782_NATIVE_26781.sha256" >/dev/null) || fail "26782 native invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26782_VENDOR_26781.sha256" >/dev/null) || fail "26782 vendor invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26782_DNG_26781.sha256" >/dev/null) || fail "26782 DNG-writer invariance"
  [[ "$(find "$CAND/app" -type f | wc -l)" -eq 1779 ]] || fail "26782 candidate file count"
  pass "candidate-first 26782 edge-safe CFA/highlight reconstruction/ownership checks"
}
verify_successful_mechanics(){
  local a81="$WORK/authority_26781_build.sh" a52="$WORK/authority_26752_build.sh"
  git show "$MECHANICS_AUTHORITY_COMMIT:build_26781_quad_coherent_cfa.sh" > "$a81"
  git show "$ROOT_MECHANICS_COMMIT:build_26752_ipol_plan_b_translational_sr.sh" > "$a52"
  [[ "$(sha "$a81")" == "$MECHANICS_SCRIPT_SHA" ]] || fail "successful 26781 build-script authority hash differs"
  for cmd in './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace' "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" './gradlew :app:assembleDebug --stacktrace'; do
    grep -F "$cmd" "$a81" >/dev/null || fail "26781 authority command missing: $cmd"
    grep -F "$cmd" "$0" >/dev/null || fail "26782 command differs: $cmd"
  done
  grep -F 'compile_spektra_raw_shader(){' "$a81" >/dev/null || fail "26781 Spektra verifier stage missing"
  grep -F 'compile_spektra_raw_shader(){' "$0" >/dev/null || fail "26782 Spektra verifier stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$a81" >/dev/null || fail "26781 native handoff stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$0" >/dev/null || fail "26782 native handoff stage missing"
  python3 -S - "$0" "$a81" "$a52" <<'PY_ORDER'
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
cur,a81,a52=[Path(x).read_text() for x in sys.argv[1:]]
ordered(cur,'# IRIS_26782_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26782')
ordered(a81,'# IRIS_26781_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26781 authority')
auth52=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26751_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','mapfile -t apks','postbuild_proof']
ordered(a52,'# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER',auth52,'26752 root authority')
print('PASS 26782 stage order exactly inherits successful 26781 procedure and root 26752 mechanics')
PY_ORDER
  pass "successful 26781 implementation diff-audited: same 17-stage order and exact compiler/native/assemble commands; only authority/version/26782 validation advances"
}
prepare_glslang(){
  D="$WORK/glslang-${GLSLANG_VERSION}"; A="$WORK/glslang.tar.gz"; mkdir -p "$D"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive sha"; tar -xzf "$A" -C "$D"
  compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]] || chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26782_glslang_version.txt"; export IRIS26782_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; pass "pinned glslang 16.5.0 dual environment handoff"
}
compile_modified_runtime_shaders(){
  python3 -S verify_26782_embedded_glsl.py "$BASE" "$CAND" --compiler "$IRIS26782_GLSLANG" --out "$OUT/26782_runtime_expanded_glsl" | tee "$OUT/26782_glsl_validation.txt"
  grep -F 'PASS 26782 modified shader ownership: normalDngMerge + existing 26778 suppressor extension are the only runtime-expanded shader deltas' "$OUT/26782_glsl_validation.txt" >/dev/null || fail "26782 modified shader ownership proof missing"
  grep -F 'PASS 26782 inherited shader fidelity: live merge + bipolarColorTrust26769 + seed preserved byte-identical before expansion; 26780 matched-bandwidth stage remains absent' "$OUT/26782_glsl_validation.txt" >/dev/null || fail "26782 inherited shader fidelity proof missing"
  for shader in normalDngMerge merge EDGE_FALSE_COLOR_SUPPRESSOR_26778 bipolarColorTrust26769 seed; do grep -F "PASS 26782 pinned real glslang compile runtime-expanded shader: ${shader}" "$OUT/26782_glsl_validation.txt" >/dev/null || fail "26782 ${shader} glslang proof missing"; done
  sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: PASS (2 modified + 3 inherited active/protected runtime-expanded shader carriers compiled with pinned glslang 16.5.0)#' "$OUT/26782_COMPILER_STATUS.txt"
}
compile_spektra_raw_shader(){ if [[ -f scripts/verify_shaders.py ]]; then IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/26782_spektra_shader_verify.txt"; else pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"; fi; }
install_frozen_candidate_live(){ rm -rf app; cp -a "$CAND/app" app; rm -rf app/build app/.cxx; mkdir -p "$LIVE_CANON"; cp -a "$CAND/app" "$LIVE_CANON/app"; universe_equal "$CAND" "$LIVE_CANON"; pass "authority-seeded canonical live candidate byte-identical to frozen 26782 candidate"; }
compile_languages(){ ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26782_gradle_language_compilers.log"; sed -i 's#REAL KOTLIN COMPILE:.*#REAL KOTLIN COMPILE: PASS#; s#REAL JAVA COMPILE:.*#REAL JAVA COMPILE: PASS (includes settings resources and Data Binding contracts)#' "$OUT/26782_COMPILER_STATUS.txt"; rm -rf "$POST_LANG"; mkdir -p "$POST_LANG"; cp -a app "$POST_LANG/app"; rm -rf "$POST_LANG/app/build" "$POST_LANG/app/.cxx"; universe_equal "$CAND" "$POST_LANG"; pass "real Kotlin/Java compilers passed and frozen source remained byte-identical"; }
verify_native_glslang_handoff(){ [[ -n "${IRIS26681_SPEKTRA_GLSLANG:-}" ]] || fail "PERMANENT REGRESSION: IRIS26681_SPEKTRA_GLSLANG unset before NDK"; [[ -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "PERMANENT REGRESSION: Spektra glslang not executable before NDK"; [[ "$IRIS26681_SPEKTRA_GLSLANG" == "$IRIS26782_GLSLANG" ]] || fail "PERMANENT REGRESSION: shader and Spektra compiler paths differ"; "$IRIS26681_SPEKTRA_GLSLANG" --version | grep -F '16.5.0' >/dev/null || fail "PERMANENT REGRESSION: Spektra compiler not pinned 16.5.0"; printf 'IRIS26681_SPEKTRA_GLSLANG=%s\nIRIS26782_GLSLANG=%s\n' "$IRIS26681_SPEKTRA_GLSLANG" "$IRIS26782_GLSLANG" | tee "$OUT/26782_native_glslang_handoff.txt"; pass "successful 26781 native glslang handoff preserved before both-ABI native compile"; }
compile_native(){ ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/26782_gradle_native_compiler.log"; sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#' "$OUT/26782_COMPILER_STATUS.txt"; }
verify_candidate_patches(){ python3 -S verify_26782_patches.py "$BASE" "$CAND" | tee "$OUT/26782_patch_validation.txt"; for n in 7 12 40; do grep -F "PASS 26782 full-index forward/rollback core.abbrev=${n} fuzz=0 exact rollback; 3 modifications" "$OUT/26782_patch_validation.txt" >/dev/null || fail "26782 abbrev${n} patch proof missing"; done; cp 26782_FORWARD_FULL_INDEX.patch "$OUT/26782_FORWARD_FULL_INDEX.patch"; cp 26782_ROLLBACK_FULL_INDEX.patch "$OUT/26782_ROLLBACK_FULL_INDEX.patch"; pass "sealed full-index forward/rollback proof: successful 26781 -> exact 3-file 26782 candidate"; }
prebuild_safety(){ universe_equal "$CAND" "$POST_LANG"; python3 -S validate_26782.py "$BASE" "$CAND"; for manifest in 26782_PROTECTED_26781.sha256 26782_NATIVE_26781.sha256 26782_VENDOR_26781.sha256 26782_DNG_26781.sha256; do (cd "$CAND" && sha256sum -c "$ROOT/$manifest" >/dev/null) || fail "prebuild $manifest"; done; grep -F 'REAL GLSL COMPILE: PASS' "$OUT/26782_COMPILER_STATUS.txt" >/dev/null; grep -F 'REAL KOTLIN COMPILE: PASS' "$OUT/26782_COMPILER_STATUS.txt" >/dev/null; grep -F 'REAL JAVA COMPILE: PASS' "$OUT/26782_COMPILER_STATUS.txt" >/dev/null; grep -F 'NATIVE/NDK COMPILE: PASS' "$OUT/26782_COMPILER_STATUS.txt" >/dev/null; grep -F 'PASS 26782 canonical patch proof' "$OUT/26782_patch_validation.txt" >/dev/null || fail "26782 canonical patch proof missing"; echo 'PRE-BUILD SAFETY PROOF PASSED' | tee "$OUT/26782_PREBUILD_SAFETY.txt"; }
assemble(){ ./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26782_gradle_assemble.log"; mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk'); [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#apks[@]}"; cp "${apks[0]}" "$FINAL"; [[ -f "$FINAL" ]] || fail "final APK missing"; sha256sum "$FINAL" > "$OUT/26782_APK.sha256"; sed -i 's#FULL ANDROID ASSEMBLE:.*#FULL ANDROID ASSEMBLE: PASS (exactly one APK)#' "$OUT/26782_COMPILER_STATUS.txt"; }
postbuild_proof(){ rm -rf "$WORK/postbuild"; mkdir -p "$WORK/postbuild"; cp -a app "$WORK/postbuild/app"; rm -rf "$WORK/postbuild/app/build" "$WORK/postbuild/app/.cxx"; universe_equal "$CAND" "$WORK/postbuild"; for manifest in 26782_PROTECTED_26781.sha256 26782_NATIVE_26781.sha256 26782_VENDOR_26781.sha256 26782_DNG_26781.sha256; do (cd "$WORK/postbuild" && sha256sum -c "$ROOT/$manifest" >/dev/null) || fail "postbuild $manifest"; done; tar -czf "$OUT/26782_candidate_app_source.tar.gz" -C "$CAND" app; sha256sum "$OUT/26782_candidate_app_source.tar.gz" > "$OUT/26782_candidate_app_source.tar.gz.sha256"; (cd "$CAND" && find app -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum) > "$OUT/26782_candidate_full_app.sha256"; python3 -S - "$OUT/26782_candidate_full_app.sha256" "$ROOT/26782_EXPECTED_CANDIDATE_FULL_APP.sha256" <<'PY_FINAL'
from pathlib import Path
import sys
def M(p):
 out={}
 for line in Path(p).read_text().splitlines(): h,r=line.split('  ',1); out[r]=h
 assert len(out)==1779,(p,len(out)); return out
assert M(sys.argv[1])==M(sys.argv[2]),'final candidate manifest differs'; print('PASS 26782 final candidate manifest: 1779 hash/path entries equal')
PY_FINAL
 sed -i 's#POST-BUILD INVARIANCE:.*#POST-BUILD INVARIANCE: PASS#' "$OUT/26782_COMPILER_STATUS.txt"; pass "authority-seeded post-build protected/DNG/native/vendor/source invariance"; }
clean_extract_replay(){ sha256sum -c 26782_HANDOFF_HASHES.sha256 >/dev/null; bash -n build_26782_edge_safe_cfa_highlight.sh; python3 -S -m py_compile transform_26782.py validate_26782.py verify_26782_patches.py verify_26782_embedded_glsl.py; rm -rf __pycache__; python3 -S validate_26782.py "$BASE" "$CAND"; python3 -S verify_26782_embedded_glsl.py "$BASE" "$CAND" | tee "$OUT/26782_final_glsl_static_replay.txt"; python3 -S verify_26782_patches.py "$BASE" "$CAND" | tee "$OUT/26782_final_patch_replay.txt"; cmp -s 26782_FORWARD_FULL_INDEX.patch "$OUT/26782_FORWARD_FULL_INDEX.patch" || fail "final forward patch bytes changed"; cmp -s 26782_ROLLBACK_FULL_INDEX.patch "$OUT/26782_ROLLBACK_FULL_INDEX.patch" || fail "final rollback patch bytes changed"; grep -F 'PRE-BUILD SAFETY PROOF PASSED' "$OUT/26782_PREBUILD_SAFETY.txt" >/dev/null; for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$OUT/26782_COMPILER_STATUS.txt" >/dev/null || fail "final proof missing: $proof"; done; pass "final 26782 clean replay of package hashes/edge-safe CFA/highlight ownership/version/patch/compiler/build proofs"; }

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
printf '\n=========================================\n26782 EDGE-SAFE CFA HIGHLIGHT: PASS\nRuntime authority: successful 26781 %s\nVerification mechanics authority: exact successful 26781 17-stage procedure (root 26752 inherited)\nRuntime changed-file allowlist: 3 modified, 0 added, 0 deleted\nInfrastructure mechanics: zero stage-order/compiler/native/assemble deviation from successful 26781\nReal GLSL/Kotlin/Java/NDK/full assemble: PASS\nExactly one APK: PASS\n=========================================\n' "$RUNTIME_AUTHORITY_COMMIT"
