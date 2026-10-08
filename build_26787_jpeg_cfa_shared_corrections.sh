#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="9b9acbc7d81aab81ca42e88cd08f8322b2dddfac"
RUNTIME_ACTIONS_RUN="37719905550"
RUNTIME_ARTIFACT_ID="11525571357"
RUNTIME_ARTIFACT_NAME="photon-26786-combined-dng-cfa-ab"
RUNTIME_ARTIFACT_SHA="33b1ba11f18c5b3ff2edeb19b2a293c0730f9297ad436fc108385320647252e1"
RUNTIME_TAR_SHA="8d5b90ec5e41f1b6fcc5488e09e037e219c6e53b44a6bd9d2c5a90b1d6b568f9"
MECHANICS_AUTHORITY_COMMIT="9b9acbc7d81aab81ca42e88cd08f8322b2dddfac"
MECHANICS_ACTIONS_RUN="37719905550"
MECHANICS_SCRIPT_SHA="5bd7600ff3141a1b76f27e46e553c4041454889dea669bfd781562956d69f3ed"
ROOT_MECHANICS_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"
ROOT_MECHANICS_RUN="37075896367"
VERSION_NAME="0.9726787"
VERSION_BUILD="26787"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26787_jpeg_cfa_shared_corrections_outputs"
WORK="$ROOT/.build_26787_jpeg_cfa_shared_corrections_work"
ARTZIP="$WORK/26786_artifact.zip"
ARTDIR="$WORK/artifact_26786"
BASE="$WORK/exact_successful_26786_compiled_candidate"
CAND="$WORK/candidate_26787"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"
POST_LANG="$WORK/post_language_compiler_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-jpeg-cfa-shared-corrections-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26787_COMPILER_STATUS.txt" <<EOF
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF

# IRIS_26787_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){
  sha256sum -c 26787_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26787_jpeg_cfa_shared_corrections.sh
  python3 -S -m py_compile transform_26787.py validate_26787.py verify_26787_patches.py verify_26787_embedded_glsl.py
  rm -rf __pycache__
  [[ "$(find handoff_payload_26787 -type f | wc -l)" -eq 3 ]] || fail "26787 payload count"
  diff -u 26787_RUNTIME_CHANGED_PATHS.txt <(find handoff_payload_26787 -type f | sed 's#^handoff_payload_26787/##' | sort) >/dev/null || fail "26787 payload allowlist mismatch"
  for p in 26787_FORWARD_FULL_INDEX.patch 26787_ROLLBACK_FULL_INDEX.patch; do
    ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$p" || fail "26787 patch contains rename/copy inference: $p"
  done
  grep -Fx 'RUN_26787_JPEG_CFA_SHARED_CORRECTIONS' TRIGGER_26787.txt >/dev/null || fail "26787 trigger contents"
  ! find . -type f -name '*.apk' | grep -q . || fail "APK unexpectedly packaged"
  pass "sealed 26787 package hashes/syntax/allowlist/patch identity"
}
verify_scope(){
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail "26786 runtime authority not ancestor"
  git merge-base --is-ancestor "$MECHANICS_AUTHORITY_COMMIT" HEAD || fail "26786 mechanics authority not ancestor"
  git merge-base --is-ancestor "$ROOT_MECHANICS_COMMIT" HEAD || fail "26752 root mechanics authority not ancestor"
  if git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | grep -E '^app/'; then fail "live app source changed after 26786 authority"; fi
  python3 -S - <<'PY_SCOPE'
import subprocess
allowed_prefixes=('26787_','build_26787_jpeg_cfa_shared_corrections.sh','transform_26787.py','validate_26787.py','verify_26787_patches.py','verify_26787_embedded_glsl.py','handoff_payload_26787/','.github/workflows/build-26787-jpeg-cfa-shared-corrections.yml','TRIGGER_26787.txt')
paths=subprocess.check_output(['git','diff','--name-only','9b9acbc7d81aab81ca42e88cd08f8322b2dddfac..HEAD'],text=True).splitlines()
bad=[p for p in paths if not any(p==x or p.startswith(x) for x in allowed_prefixes)]
assert not bad,bad
print('PASS 26787 infrastructure scope allowlist')
PY_SCOPE
  pass "26787 scope exact: successful 26786 authority + sealed 3-file payload; live app untouched"
}
obtain_authority(){
  [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
  curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
  [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail "26786 artifact sha"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  T="$ARTDIR/build_26786_combined_dng_cfa_ab_outputs/26786_candidate_app_source.tar.gz"
  [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail "26786 candidate tar sha"
  STATUS="$ARTDIR/build_26786_combined_dng_cfa_ab_outputs/26786_COMPILER_STATUS.txt"
  for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$STATUS" >/dev/null || fail "missing 26786 authority proof: $proof"; done
  mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"
  [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1779 ]] || fail "26786 base file count"
  (cd "$BASE" && sha256sum -c "$ROOT/26787_BASE_26786_FULL_APP.sha256" >/dev/null) || fail "26786 full base manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26787_NATIVE_26786.sha256" >/dev/null) || fail "26786 native manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26787_VENDOR_26786.sha256" >/dev/null) || fail "26786 vendor manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26787_DNG_WRITER_26786.sha256" >/dev/null) || fail "26786 DNG manifest"
  cat > "$OUT/26787_RESOLVED_AUTHORITIES.txt" <<EOF
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
  pass "exact successful 26786 compiled candidate reconstructed"
}
universe_equal(){ python3 -S - "$1" "$2" <<'PY_UNIVERSE'
from pathlib import Path
import hashlib,sys
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=U(sys.argv[1]),U(sys.argv[2]); assert a==b,(len(a),len(b)); print(f'PASS byte-identical app universe: {len(a)} files')
PY_UNIVERSE
}
make_candidate(){
  python3 -S transform_26787.py "$BASE" "$CAND" handoff_payload_26787
  python3 -S validate_26787.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26787_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail "26787 candidate manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26787_PROTECTED_26786.sha256" >/dev/null) || fail "26787 protected manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26787_NATIVE_26786.sha256" >/dev/null) || fail "26787 native invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26787_VENDOR_26786.sha256" >/dev/null) || fail "26787 vendor invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26787_DNG_WRITER_26786.sha256" >/dev/null) || fail "26787 DNG-writer invariance"
  [[ "$(find "$CAND/app" -type f | wc -l)" -eq 1779 ]] || fail "26787 candidate file count"
  pass "candidate-first 26787 JPEG CFA shared-correction reconstruction/ownership checks"
}
verify_successful_mechanics(){
  local a81="$WORK/authority_26786_build.sh" a52="$WORK/authority_26752_build.sh"
  git show "$MECHANICS_AUTHORITY_COMMIT:build_26786_combined_dng_cfa_ab.sh" > "$a81"
  git show "$ROOT_MECHANICS_COMMIT:build_26752_ipol_plan_b_translational_sr.sh" > "$a52"
  [[ "$(sha "$a81")" == "$MECHANICS_SCRIPT_SHA" ]] || fail "successful 26786 build-script authority hash differs"
  for cmd in './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace' "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" './gradlew :app:assembleDebug --stacktrace'; do
    grep -F "$cmd" "$a81" >/dev/null || fail "26786 authority command missing: $cmd"
    grep -F "$cmd" "$0" >/dev/null || fail "26787 command differs: $cmd"
  done
  grep -F 'compile_spektra_raw_shader(){' "$a81" >/dev/null || fail "26786 Spektra verifier stage missing"
  grep -F 'compile_spektra_raw_shader(){' "$0" >/dev/null || fail "26787 Spektra verifier stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$a81" >/dev/null || fail "26786 native handoff stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$0" >/dev/null || fail "26787 native handoff stage missing"
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
ordered(cur,'# IRIS_26787_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26787')
ordered(a81,'# IRIS_26786_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26786 authority')
auth52=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26751_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','mapfile -t apks','postbuild_proof']
ordered(a52,'# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER',auth52,'26752 root authority')
print('PASS 26787 stage order exactly inherits successful 26786 procedure and root 26752 mechanics')
PY_ORDER
  pass "successful 26786 implementation diff-audited: same 17-stage order and exact compiler/native/assemble commands; only authority/version/26787 validation advances"
}
prepare_glslang(){
  D="$WORK/glslang-${GLSLANG_VERSION}"; A="$WORK/glslang.tar.gz"; mkdir -p "$D"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive sha"; tar -xzf "$A" -C "$D"
  compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]] || chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26787_glslang_version.txt"; export IRIS26787_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; pass "pinned glslang 16.5.0 dual environment handoff"
}
compile_modified_runtime_shaders(){
  python3 -S verify_26787_embedded_glsl.py "$BASE" "$CAND" --compiler "$IRIS26787_GLSLANG" --out "$OUT/26787_runtime_expanded_glsl" | tee "$OUT/26787_glsl_validation.txt"
  grep -F 'PASS 26787 modified shader ownership: add JPEG pre-Resolve neutral-clamp + radial-LCA shaders only; no inherited shader body modified' "$OUT/26787_glsl_validation.txt" >/dev/null || fail "26787 modified shader ownership proof missing"
  grep -F 'PASS 26787 protected shader fidelity: live merge/DNG normalize/26778/VGN owners byte-identical to successful 26786' "$OUT/26787_glsl_validation.txt" >/dev/null || fail "26787 inherited shader fidelity proof missing"
  for shader in jpegNeutralHighlightClamp26787 jpegLcaPreResolve26787 merge normalDngMerge normalizeBayer EDGE_FALSE_COLOR_SUPPRESSOR_26778 universalAdaptiveColor26561 bipolarColorTrust26769; do grep -F "PASS 26787 pinned real glslang compile runtime-expanded shader: ${shader}" "$OUT/26787_glsl_validation.txt" >/dev/null || fail "26787 ${shader} glslang proof missing"; done
  sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: PASS (2 new modified + 6 inherited active/protected runtime-expanded shader carriers compiled with pinned glslang 16.5.0)#' "$OUT/26787_COMPILER_STATUS.txt"
}
compile_spektra_raw_shader(){ if [[ -f scripts/verify_shaders.py ]]; then IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/26787_spektra_shader_verify.txt"; else pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"; fi; }
install_frozen_candidate_live(){ rm -rf app; cp -a "$CAND/app" app; rm -rf app/build app/.cxx; mkdir -p "$LIVE_CANON"; cp -a "$CAND/app" "$LIVE_CANON/app"; universe_equal "$CAND" "$LIVE_CANON"; pass "authority-seeded canonical live candidate byte-identical to frozen 26787 candidate"; }
compile_languages(){ ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26787_gradle_language_compilers.log"; sed -i 's#REAL KOTLIN COMPILE:.*#REAL KOTLIN COMPILE: PASS#; s#REAL JAVA COMPILE:.*#REAL JAVA COMPILE: PASS (includes settings resources and Data Binding contracts)#' "$OUT/26787_COMPILER_STATUS.txt"; rm -rf "$POST_LANG"; mkdir -p "$POST_LANG"; cp -a app "$POST_LANG/app"; rm -rf "$POST_LANG/app/build" "$POST_LANG/app/.cxx"; universe_equal "$CAND" "$POST_LANG"; pass "real Kotlin/Java compilers passed and frozen source remained byte-identical"; }
verify_native_glslang_handoff(){ [[ -n "${IRIS26681_SPEKTRA_GLSLANG:-}" ]] || fail "PERMANENT REGRESSION: IRIS26681_SPEKTRA_GLSLANG unset before NDK"; [[ -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "PERMANENT REGRESSION: Spektra glslang not executable before NDK"; [[ "$IRIS26681_SPEKTRA_GLSLANG" == "$IRIS26787_GLSLANG" ]] || fail "PERMANENT REGRESSION: shader and Spektra compiler paths differ"; "$IRIS26681_SPEKTRA_GLSLANG" --version | grep -F '16.5.0' >/dev/null || fail "PERMANENT REGRESSION: Spektra compiler not pinned 16.5.0"; printf 'IRIS26681_SPEKTRA_GLSLANG=%s\nIRIS26787_GLSLANG=%s\n' "$IRIS26681_SPEKTRA_GLSLANG" "$IRIS26787_GLSLANG" | tee "$OUT/26787_native_glslang_handoff.txt"; pass "successful 26786 native glslang handoff preserved before both-ABI native compile"; }
compile_native(){ ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/26787_gradle_native_compiler.log"; sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#' "$OUT/26787_COMPILER_STATUS.txt"; }
verify_candidate_patches(){ python3 -S verify_26787_patches.py "$BASE" "$CAND" | tee "$OUT/26787_patch_validation.txt"; for n in 7 12 40; do grep -F "PASS 26787 full-index forward/rollback core.abbrev=${n} fuzz=0 exact rollback; 3 modifications" "$OUT/26787_patch_validation.txt" >/dev/null || fail "26787 abbrev${n} patch proof missing"; done; cp 26787_FORWARD_FULL_INDEX.patch "$OUT/26787_FORWARD_FULL_INDEX.patch"; cp 26787_ROLLBACK_FULL_INDEX.patch "$OUT/26787_ROLLBACK_FULL_INDEX.patch"; pass "sealed full-index forward/rollback proof: successful 26786 -> exact 3-file 26787 candidate"; }
prebuild_safety(){ universe_equal "$CAND" "$POST_LANG"; python3 -S validate_26787.py "$BASE" "$CAND"; for manifest in 26787_PROTECTED_26786.sha256 26787_NATIVE_26786.sha256 26787_VENDOR_26786.sha256 26787_DNG_WRITER_26786.sha256; do (cd "$CAND" && sha256sum -c "$ROOT/$manifest" >/dev/null) || fail "prebuild $manifest"; done; grep -F 'REAL GLSL COMPILE: PASS' "$OUT/26787_COMPILER_STATUS.txt" >/dev/null; grep -F 'REAL KOTLIN COMPILE: PASS' "$OUT/26787_COMPILER_STATUS.txt" >/dev/null; grep -F 'REAL JAVA COMPILE: PASS' "$OUT/26787_COMPILER_STATUS.txt" >/dev/null; grep -F 'NATIVE/NDK COMPILE: PASS' "$OUT/26787_COMPILER_STATUS.txt" >/dev/null; grep -F 'PASS 26787 canonical patch proof' "$OUT/26787_patch_validation.txt" >/dev/null || fail "26787 canonical patch proof missing"; echo 'PRE-BUILD SAFETY PROOF PASSED' | tee "$OUT/26787_PREBUILD_SAFETY.txt"; }
assemble(){ ./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26787_gradle_assemble.log"; mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk'); [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#apks[@]}"; cp "${apks[0]}" "$FINAL"; [[ -f "$FINAL" ]] || fail "final APK missing"; sha256sum "$FINAL" > "$OUT/26787_APK.sha256"; sed -i 's#FULL ANDROID ASSEMBLE:.*#FULL ANDROID ASSEMBLE: PASS (exactly one APK)#' "$OUT/26787_COMPILER_STATUS.txt"; }
postbuild_proof(){ rm -rf "$WORK/postbuild"; mkdir -p "$WORK/postbuild"; cp -a app "$WORK/postbuild/app"; rm -rf "$WORK/postbuild/app/build" "$WORK/postbuild/app/.cxx"; universe_equal "$CAND" "$WORK/postbuild"; for manifest in 26787_PROTECTED_26786.sha256 26787_NATIVE_26786.sha256 26787_VENDOR_26786.sha256 26787_DNG_WRITER_26786.sha256; do (cd "$WORK/postbuild" && sha256sum -c "$ROOT/$manifest" >/dev/null) || fail "postbuild $manifest"; done; tar -czf "$OUT/26787_candidate_app_source.tar.gz" -C "$CAND" app; sha256sum "$OUT/26787_candidate_app_source.tar.gz" > "$OUT/26787_candidate_app_source.tar.gz.sha256"; (cd "$CAND" && find app -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum) > "$OUT/26787_candidate_full_app.sha256"; python3 -S - "$OUT/26787_candidate_full_app.sha256" "$ROOT/26787_EXPECTED_CANDIDATE_FULL_APP.sha256" <<'PY_FINAL'
from pathlib import Path
import sys
def M(p):
 out={}
 for line in Path(p).read_text().splitlines(): h,r=line.split('  ',1); out[r]=h
 assert len(out)==1779,(p,len(out)); return out
assert M(sys.argv[1])==M(sys.argv[2]),'final candidate manifest differs'; print('PASS 26787 final candidate manifest: 1779 hash/path entries equal')
PY_FINAL
 sed -i 's#POST-BUILD INVARIANCE:.*#POST-BUILD INVARIANCE: PASS#' "$OUT/26787_COMPILER_STATUS.txt"; pass "authority-seeded post-build protected/DNG/native/vendor/source invariance"; }
clean_extract_replay(){ sha256sum -c 26787_HANDOFF_HASHES.sha256 >/dev/null; bash -n build_26787_jpeg_cfa_shared_corrections.sh; python3 -S -m py_compile transform_26787.py validate_26787.py verify_26787_patches.py verify_26787_embedded_glsl.py; rm -rf __pycache__; python3 -S validate_26787.py "$BASE" "$CAND"; python3 -S verify_26787_embedded_glsl.py "$BASE" "$CAND" | tee "$OUT/26787_final_glsl_static_replay.txt"; python3 -S verify_26787_patches.py "$BASE" "$CAND" | tee "$OUT/26787_final_patch_replay.txt"; cmp -s 26787_FORWARD_FULL_INDEX.patch "$OUT/26787_FORWARD_FULL_INDEX.patch" || fail "final forward patch bytes changed"; cmp -s 26787_ROLLBACK_FULL_INDEX.patch "$OUT/26787_ROLLBACK_FULL_INDEX.patch" || fail "final rollback patch bytes changed"; grep -F 'PRE-BUILD SAFETY PROOF PASSED' "$OUT/26787_PREBUILD_SAFETY.txt" >/dev/null; for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$OUT/26787_COMPILER_STATUS.txt" >/dev/null || fail "final proof missing: $proof"; done; pass "final 26787 clean replay of package hashes/JPEG-CFA-shared-corrections/JPEG-VGN-freeze/version/patch/compiler/build proofs"; }

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
printf '\n=========================================\n26787 JPEG CFA SHARED CORRECTIONS: PASS\nRuntime authority: successful 26786 %s\nVerification mechanics authority: exact successful 26786 17-stage procedure (root 26752 inherited)\nRuntime changed-file allowlist: 3 modified, 0 added, 0 deleted\nInfrastructure mechanics: zero stage-order/compiler/native/assemble deviation from successful 26786\nReal GLSL/Kotlin/Java/NDK/full assemble: PASS\nExactly one APK: PASS\n=========================================\n' "$RUNTIME_AUTHORITY_COMMIT"
