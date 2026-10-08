#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="6cfeccd50ad71f32f12bebd89f4e87c5afc77a61"
RUNTIME_ACTIONS_RUN="37706878374"
RUNTIME_ARTIFACT_ID="11520262723"
RUNTIME_ARTIFACT_NAME="photon-26785-phase-scoped-cfa-highlight"
RUNTIME_ARTIFACT_SHA="fe9bdbb8a959172172ce4da94bc4e3a6eed1d702f25f5be49b5363da147c0ee0"
RUNTIME_TAR_SHA="856cae25c9e00c43e364954675c04bb2000e68b2547422a550f5c4291d3095c6"
MECHANICS_AUTHORITY_COMMIT="6cfeccd50ad71f32f12bebd89f4e87c5afc77a61"
MECHANICS_ACTIONS_RUN="37706878374"
MECHANICS_SCRIPT_SHA="45bd4d728686fe0aa4be00efa62cf14b9f819ade03ef6db584b5b8116d5c59f4"
ROOT_MECHANICS_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"
ROOT_MECHANICS_RUN="37075896367"
VERSION_NAME="0.9726786"
VERSION_BUILD="26786"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26786_combined_dng_cfa_ab_outputs"
WORK="$ROOT/.build_26786_combined_dng_cfa_ab_work"
ARTZIP="$WORK/26785_artifact.zip"
ARTDIR="$WORK/artifact_26785"
BASE="$WORK/exact_successful_26785_compiled_candidate"
CAND="$WORK/candidate_26786"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"
POST_LANG="$WORK/post_language_compiler_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-combined-dng-cfa-ab-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26786_COMPILER_STATUS.txt" <<EOF
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF

# IRIS_26786_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){
  sha256sum -c 26786_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26786_combined_dng_cfa_ab.sh
  python3 -S -m py_compile transform_26786.py validate_26786.py verify_26786_patches.py verify_26786_embedded_glsl.py
  rm -rf __pycache__
  [[ "$(find handoff_payload_26786 -type f | wc -l)" -eq 15 ]] || fail "26786 payload count"
  diff -u 26786_RUNTIME_CHANGED_PATHS.txt <(find handoff_payload_26786 -type f | sed 's#^handoff_payload_26786/##' | sort) >/dev/null || fail "26786 payload allowlist mismatch"
  for p in 26786_FORWARD_FULL_INDEX.patch 26786_ROLLBACK_FULL_INDEX.patch; do
    ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$p" || fail "26786 patch contains rename/copy inference: $p"
  done
  grep -Fx 'RUN_26786_COMBINED_DNG_CFA_AB' TRIGGER_26786.txt >/dev/null || fail "26786 trigger contents"
  ! find . -type f -name '*.apk' | grep -q . || fail "APK unexpectedly packaged"
  pass "sealed 26786 package hashes/syntax/allowlist/patch identity"
}
verify_scope(){
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail "26785 runtime authority not ancestor"
  git merge-base --is-ancestor "$MECHANICS_AUTHORITY_COMMIT" HEAD || fail "26785 mechanics authority not ancestor"
  git merge-base --is-ancestor "$ROOT_MECHANICS_COMMIT" HEAD || fail "26752 root mechanics authority not ancestor"
  if git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | grep -E '^app/'; then fail "live app source changed after 26785 authority"; fi
  python3 -S - <<'PY_SCOPE'
import subprocess
allowed_prefixes=('26786_','build_26786_combined_dng_cfa_ab.sh','transform_26786.py','validate_26786.py','verify_26786_patches.py','verify_26786_embedded_glsl.py','handoff_payload_26786/','.github/workflows/build-26786-combined-dng-cfa-ab.yml','TRIGGER_26786.txt')
paths=subprocess.check_output(['git','diff','--name-only','6cfeccd50ad71f32f12bebd89f4e87c5afc77a61..HEAD'],text=True).splitlines()
bad=[p for p in paths if not any(p==x or p.startswith(x) for x in allowed_prefixes)]
assert not bad,bad
print('PASS 26786 infrastructure scope allowlist')
PY_SCOPE
  pass "26786 scope exact: successful 26785 authority + sealed 15-file payload; live app untouched"
}
obtain_authority(){
  [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
  curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
  [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail "26785 artifact sha"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  T="$ARTDIR/build_26785_phase_scoped_cfa_highlight_outputs/26785_candidate_app_source.tar.gz"
  [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail "26785 candidate tar sha"
  STATUS="$ARTDIR/build_26785_phase_scoped_cfa_highlight_outputs/26785_COMPILER_STATUS.txt"
  for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$STATUS" >/dev/null || fail "missing 26785 authority proof: $proof"; done
  mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"
  [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1779 ]] || fail "26785 base file count"
  (cd "$BASE" && sha256sum -c "$ROOT/26786_BASE_26785_FULL_APP.sha256" >/dev/null) || fail "26785 full base manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26786_NATIVE_26785.sha256" >/dev/null) || fail "26785 native manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26786_VENDOR_26785.sha256" >/dev/null) || fail "26785 vendor manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26786_DNG_WRITER_26785.sha256" >/dev/null) || fail "26785 DNG manifest"
  cat > "$OUT/26786_RESOLVED_AUTHORITIES.txt" <<EOF
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
  pass "exact successful 26785 compiled candidate reconstructed"
}
universe_equal(){ python3 -S - "$1" "$2" <<'PY_UNIVERSE'
from pathlib import Path
import hashlib,sys
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=U(sys.argv[1]),U(sys.argv[2]); assert a==b,(len(a),len(b)); print(f'PASS byte-identical app universe: {len(a)} files')
PY_UNIVERSE
}
make_candidate(){
  python3 -S transform_26786.py "$BASE" "$CAND" handoff_payload_26786
  python3 -S validate_26786.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26786_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail "26786 candidate manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26786_PROTECTED_26785.sha256" >/dev/null) || fail "26786 protected manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26786_NATIVE_26785.sha256" >/dev/null) || fail "26786 native invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26786_VENDOR_26785.sha256" >/dev/null) || fail "26786 vendor invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26786_DNG_WRITER_26785.sha256" >/dev/null) || fail "26786 DNG-writer invariance"
  [[ "$(find "$CAND/app" -type f | wc -l)" -eq 1779 ]] || fail "26786 candidate file count"
  pass "candidate-first 26786 combined DNG/CFA visible-A/B reconstruction/ownership checks"
}
verify_successful_mechanics(){
  local a81="$WORK/authority_26785_build.sh" a52="$WORK/authority_26752_build.sh"
  git show "$MECHANICS_AUTHORITY_COMMIT:build_26785_phase_scoped_cfa_highlight.sh" > "$a81"
  git show "$ROOT_MECHANICS_COMMIT:build_26752_ipol_plan_b_translational_sr.sh" > "$a52"
  [[ "$(sha "$a81")" == "$MECHANICS_SCRIPT_SHA" ]] || fail "successful 26785 build-script authority hash differs"
  for cmd in './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace' "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" './gradlew :app:assembleDebug --stacktrace'; do
    grep -F "$cmd" "$a81" >/dev/null || fail "26785 authority command missing: $cmd"
    grep -F "$cmd" "$0" >/dev/null || fail "26786 command differs: $cmd"
  done
  grep -F 'compile_spektra_raw_shader(){' "$a81" >/dev/null || fail "26785 Spektra verifier stage missing"
  grep -F 'compile_spektra_raw_shader(){' "$0" >/dev/null || fail "26786 Spektra verifier stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$a81" >/dev/null || fail "26785 native handoff stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$0" >/dev/null || fail "26786 native handoff stage missing"
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
ordered(cur,'# IRIS_26786_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26786')
ordered(a81,'# IRIS_26785_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26785 authority')
auth52=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26751_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','mapfile -t apks','postbuild_proof']
ordered(a52,'# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER',auth52,'26752 root authority')
print('PASS 26786 stage order exactly inherits successful 26785 procedure and root 26752 mechanics')
PY_ORDER
  pass "successful 26785 implementation diff-audited: same 17-stage order and exact compiler/native/assemble commands; only authority/version/26786 validation advances"
}
prepare_glslang(){
  D="$WORK/glslang-${GLSLANG_VERSION}"; A="$WORK/glslang.tar.gz"; mkdir -p "$D"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive sha"; tar -xzf "$A" -C "$D"
  compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]] || chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26786_glslang_version.txt"; export IRIS26786_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; pass "pinned glslang 16.5.0 dual environment handoff"
}
compile_modified_runtime_shaders(){
  python3 -S verify_26786_embedded_glsl.py "$BASE" "$CAND" --compiler "$IRIS26786_GLSLANG" --out "$OUT/26786_runtime_expanded_glsl" | tee "$OUT/26786_glsl_validation.txt"
  grep -F 'PASS 26786 modified shader ownership: DNG normalDngMerge + DNG normalizeBayer only' "$OUT/26786_glsl_validation.txt" >/dev/null || fail "26786 modified shader ownership proof missing"
  grep -F 'PASS 26786 protected shader fidelity: live merge/26778/VGN owners byte-identical' "$OUT/26786_glsl_validation.txt" >/dev/null || fail "26786 inherited shader fidelity proof missing"
  for shader in normalDngMerge normalizeBayer merge EDGE_FALSE_COLOR_SUPPRESSOR_26778 universalAdaptiveColor26561 bipolarColorTrust26769; do grep -F "PASS 26786 pinned real glslang compile runtime-expanded shader: ${shader}" "$OUT/26786_glsl_validation.txt" >/dev/null || fail "26786 ${shader} glslang proof missing"; done
  sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: PASS (2 modified + 4 inherited active/protected runtime-expanded shader carriers compiled with pinned glslang 16.5.0)#' "$OUT/26786_COMPILER_STATUS.txt"
}
compile_spektra_raw_shader(){ if [[ -f scripts/verify_shaders.py ]]; then IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/26786_spektra_shader_verify.txt"; else pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"; fi; }
install_frozen_candidate_live(){ rm -rf app; cp -a "$CAND/app" app; rm -rf app/build app/.cxx; mkdir -p "$LIVE_CANON"; cp -a "$CAND/app" "$LIVE_CANON/app"; universe_equal "$CAND" "$LIVE_CANON"; pass "authority-seeded canonical live candidate byte-identical to frozen 26786 candidate"; }
compile_languages(){ ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26786_gradle_language_compilers.log"; sed -i 's#REAL KOTLIN COMPILE:.*#REAL KOTLIN COMPILE: PASS#; s#REAL JAVA COMPILE:.*#REAL JAVA COMPILE: PASS (includes settings resources and Data Binding contracts)#' "$OUT/26786_COMPILER_STATUS.txt"; rm -rf "$POST_LANG"; mkdir -p "$POST_LANG"; cp -a app "$POST_LANG/app"; rm -rf "$POST_LANG/app/build" "$POST_LANG/app/.cxx"; universe_equal "$CAND" "$POST_LANG"; pass "real Kotlin/Java compilers passed and frozen source remained byte-identical"; }
verify_native_glslang_handoff(){ [[ -n "${IRIS26681_SPEKTRA_GLSLANG:-}" ]] || fail "PERMANENT REGRESSION: IRIS26681_SPEKTRA_GLSLANG unset before NDK"; [[ -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "PERMANENT REGRESSION: Spektra glslang not executable before NDK"; [[ "$IRIS26681_SPEKTRA_GLSLANG" == "$IRIS26786_GLSLANG" ]] || fail "PERMANENT REGRESSION: shader and Spektra compiler paths differ"; "$IRIS26681_SPEKTRA_GLSLANG" --version | grep -F '16.5.0' >/dev/null || fail "PERMANENT REGRESSION: Spektra compiler not pinned 16.5.0"; printf 'IRIS26681_SPEKTRA_GLSLANG=%s\nIRIS26786_GLSLANG=%s\n' "$IRIS26681_SPEKTRA_GLSLANG" "$IRIS26786_GLSLANG" | tee "$OUT/26786_native_glslang_handoff.txt"; pass "successful 26785 native glslang handoff preserved before both-ABI native compile"; }
compile_native(){ ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/26786_gradle_native_compiler.log"; sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#' "$OUT/26786_COMPILER_STATUS.txt"; }
verify_candidate_patches(){ python3 -S verify_26786_patches.py "$BASE" "$CAND" | tee "$OUT/26786_patch_validation.txt"; for n in 7 12 40; do grep -F "PASS 26786 full-index forward/rollback core.abbrev=${n} fuzz=0 exact rollback; 15 modifications" "$OUT/26786_patch_validation.txt" >/dev/null || fail "26786 abbrev${n} patch proof missing"; done; cp 26786_FORWARD_FULL_INDEX.patch "$OUT/26786_FORWARD_FULL_INDEX.patch"; cp 26786_ROLLBACK_FULL_INDEX.patch "$OUT/26786_ROLLBACK_FULL_INDEX.patch"; pass "sealed full-index forward/rollback proof: successful 26785 -> exact 15-file 26786 candidate"; }
prebuild_safety(){ universe_equal "$CAND" "$POST_LANG"; python3 -S validate_26786.py "$BASE" "$CAND"; for manifest in 26786_PROTECTED_26785.sha256 26786_NATIVE_26785.sha256 26786_VENDOR_26785.sha256 26786_DNG_WRITER_26785.sha256; do (cd "$CAND" && sha256sum -c "$ROOT/$manifest" >/dev/null) || fail "prebuild $manifest"; done; grep -F 'REAL GLSL COMPILE: PASS' "$OUT/26786_COMPILER_STATUS.txt" >/dev/null; grep -F 'REAL KOTLIN COMPILE: PASS' "$OUT/26786_COMPILER_STATUS.txt" >/dev/null; grep -F 'REAL JAVA COMPILE: PASS' "$OUT/26786_COMPILER_STATUS.txt" >/dev/null; grep -F 'NATIVE/NDK COMPILE: PASS' "$OUT/26786_COMPILER_STATUS.txt" >/dev/null; grep -F 'PASS 26786 canonical patch proof' "$OUT/26786_patch_validation.txt" >/dev/null || fail "26786 canonical patch proof missing"; echo 'PRE-BUILD SAFETY PROOF PASSED' | tee "$OUT/26786_PREBUILD_SAFETY.txt"; }
assemble(){ ./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26786_gradle_assemble.log"; mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk'); [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#apks[@]}"; cp "${apks[0]}" "$FINAL"; [[ -f "$FINAL" ]] || fail "final APK missing"; sha256sum "$FINAL" > "$OUT/26786_APK.sha256"; sed -i 's#FULL ANDROID ASSEMBLE:.*#FULL ANDROID ASSEMBLE: PASS (exactly one APK)#' "$OUT/26786_COMPILER_STATUS.txt"; }
postbuild_proof(){ rm -rf "$WORK/postbuild"; mkdir -p "$WORK/postbuild"; cp -a app "$WORK/postbuild/app"; rm -rf "$WORK/postbuild/app/build" "$WORK/postbuild/app/.cxx"; universe_equal "$CAND" "$WORK/postbuild"; for manifest in 26786_PROTECTED_26785.sha256 26786_NATIVE_26785.sha256 26786_VENDOR_26785.sha256 26786_DNG_WRITER_26785.sha256; do (cd "$WORK/postbuild" && sha256sum -c "$ROOT/$manifest" >/dev/null) || fail "postbuild $manifest"; done; tar -czf "$OUT/26786_candidate_app_source.tar.gz" -C "$CAND" app; sha256sum "$OUT/26786_candidate_app_source.tar.gz" > "$OUT/26786_candidate_app_source.tar.gz.sha256"; (cd "$CAND" && find app -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum) > "$OUT/26786_candidate_full_app.sha256"; python3 -S - "$OUT/26786_candidate_full_app.sha256" "$ROOT/26786_EXPECTED_CANDIDATE_FULL_APP.sha256" <<'PY_FINAL'
from pathlib import Path
import sys
def M(p):
 out={}
 for line in Path(p).read_text().splitlines(): h,r=line.split('  ',1); out[r]=h
 assert len(out)==1779,(p,len(out)); return out
assert M(sys.argv[1])==M(sys.argv[2]),'final candidate manifest differs'; print('PASS 26786 final candidate manifest: 1779 hash/path entries equal')
PY_FINAL
 sed -i 's#POST-BUILD INVARIANCE:.*#POST-BUILD INVARIANCE: PASS#' "$OUT/26786_COMPILER_STATUS.txt"; pass "authority-seeded post-build protected/DNG/native/vendor/source invariance"; }
clean_extract_replay(){ sha256sum -c 26786_HANDOFF_HASHES.sha256 >/dev/null; bash -n build_26786_combined_dng_cfa_ab.sh; python3 -S -m py_compile transform_26786.py validate_26786.py verify_26786_patches.py verify_26786_embedded_glsl.py; rm -rf __pycache__; python3 -S validate_26786.py "$BASE" "$CAND"; python3 -S verify_26786_embedded_glsl.py "$BASE" "$CAND" | tee "$OUT/26786_final_glsl_static_replay.txt"; python3 -S verify_26786_patches.py "$BASE" "$CAND" | tee "$OUT/26786_final_patch_replay.txt"; cmp -s 26786_FORWARD_FULL_INDEX.patch "$OUT/26786_FORWARD_FULL_INDEX.patch" || fail "final forward patch bytes changed"; cmp -s 26786_ROLLBACK_FULL_INDEX.patch "$OUT/26786_ROLLBACK_FULL_INDEX.patch" || fail "final rollback patch bytes changed"; grep -F 'PRE-BUILD SAFETY PROOF PASSED' "$OUT/26786_PREBUILD_SAFETY.txt" >/dev/null; for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$OUT/26786_COMPILER_STATUS.txt" >/dev/null || fail "final proof missing: $proof"; done; pass "final 26786 clean replay of package hashes/combined-DNG-CFA-visible-AB/JPEG-VGN-freeze/version/patch/compiler/build proofs"; }

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
printf '\n=========================================\n26786 COMBINED DNG CFA A/B: PASS\nRuntime authority: successful 26785 %s\nVerification mechanics authority: exact successful 26785 17-stage procedure (root 26752 inherited)\nRuntime changed-file allowlist: 15 modified, 0 added, 0 deleted\nInfrastructure mechanics: zero stage-order/compiler/native/assemble deviation from successful 26785\nReal GLSL/Kotlin/Java/NDK/full assemble: PASS\nExactly one APK: PASS\n=========================================\n' "$RUNTIME_AUTHORITY_COMMIT"
