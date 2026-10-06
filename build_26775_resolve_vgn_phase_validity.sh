#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="36a02d20b0e187b920d26e68ba238924d9415275"
RUNTIME_ACTIONS_RUN="37505517708"
RUNTIME_ARTIFACT_ID="11432360941"
RUNTIME_ARTIFACT_NAME="photon-26774-histogram-downward-hinge"
RUNTIME_ARTIFACT_SHA="57546b133b3279f9f4b7c620d46e2f6b2db4a531b30a0d208498bfb4b57f1666"
RUNTIME_TAR_SHA="f76019ed6e6de5e6f1257c70006c24fa0957445fc30b3ed1312a46afe291edfe"
MECHANICS_AUTHORITY_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"
MECHANICS_ACTIONS_RUN="37075896367"
VERSION_NAME="0.9726775"
VERSION_BUILD="26775"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26775_resolve_vgn_phase_validity_outputs"
WORK="$ROOT/.build_26775_resolve_vgn_phase_validity_work"
ARTZIP="$WORK/26774_artifact.zip"
ARTDIR="$WORK/artifact_26774"
BASE="$WORK/exact_successful_26774_compiled_candidate"
CAND="$WORK/candidate_26775"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"
POST_LANG="$WORK/post_language_compiler_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-resolve-vgn-phase-validity-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26775_COMPILER_STATUS.txt" <<EOF
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF

# IRIS_26775_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){
  sha256sum -c 26775_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26775_resolve_vgn_phase_validity.sh
  python3 -S -m py_compile transform_26775.py validate_26775.py verify_26775_patches.py verify_26775_embedded_glsl.py
  rm -rf __pycache__
  [[ "$(find handoff_payload_26775 -type f | wc -l)" -eq 2 ]] || fail "26775 payload count"
  diff -u 26775_RUNTIME_CHANGED_PATHS.txt <(find handoff_payload_26775 -type f | sed 's#^handoff_payload_26775/##' | sort) >/dev/null || fail "26775 payload allowlist mismatch"
  for p in 26775_FORWARD_FULL_INDEX.patch 26775_ROLLBACK_FULL_INDEX.patch; do
    ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$p" || fail "26775 patch contains rename/copy inference: $p"
  done
  grep -Fx 'RUN_26775_RESOLVE_VGN_PHASE_VALIDITY' TRIGGER_26775.txt >/dev/null || fail "26775 trigger contents"
  ! find . -type f -name '*.apk' | grep -q . || fail "APK unexpectedly packaged"
  pass "sealed 26775 package hashes/syntax/allowlist/patch identity"
}
verify_scope(){
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail "26774 runtime authority not ancestor"
  git merge-base --is-ancestor "$MECHANICS_AUTHORITY_COMMIT" HEAD || fail "26752 mechanics authority not ancestor"
  # No live runtime source is uploaded. Candidate source exists only in the sealed payload and is
  # reconstructed from the exact successful artifact.
  if git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | grep -E '^app/'; then
    fail "live app source changed after 26774 authority"
  fi
  python3 -S - <<'PY'
import subprocess
allowed_prefixes=(
 '26775_', 'build_26775_resolve_vgn_phase_validity.sh', 'transform_26775.py',
 'validate_26775.py', 'verify_26775_patches.py', 'verify_26775_embedded_glsl.py', 'handoff_payload_26775/',
 '.github/workflows/build-26775-resolve-vgn-phase-validity.yml', 'TRIGGER_26775.txt')
paths=subprocess.check_output(['git','diff','--name-only','36a02d20b0e187b920d26e68ba238924d9415275..HEAD'],text=True).splitlines()
bad=[p for p in paths if not any(p==x or p.startswith(x) for x in allowed_prefixes)]
assert not bad,bad
print('PASS 26775 infrastructure scope allowlist')
PY
  pass "26775 scope exact: successful 26774 authority + sealed 2-file payload; live app untouched"
}
obtain_authority(){
  [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
  curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
  [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail "26774 artifact sha"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  T="$ARTDIR/build_26774_histogram_downward_hinge_outputs/26774_candidate_app_source.tar.gz"
  [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail "26774 candidate tar sha"
  STATUS="$ARTDIR/build_26774_histogram_downward_hinge_outputs/26774_COMPILER_STATUS.txt"
  for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do
    grep -F "$proof" "$STATUS" >/dev/null || fail "missing 26774 authority proof: $proof"
  done
  mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"
  [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1779 ]] || fail "26774 base file count"
  (cd "$BASE" && sha256sum -c "$ROOT/26775_BASE_26774_FULL_APP.sha256" >/dev/null) || fail "26774 full base manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26775_NATIVE_26774.sha256" >/dev/null) || fail "26774 native manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26775_VENDOR_26774.sha256" >/dev/null) || fail "26774 vendor manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26775_DNG_26774.sha256" >/dev/null) || fail "26774 DNG manifest"
  cat > "$OUT/26775_RESOLVED_AUTHORITIES.txt" <<EOF
runtime_commit=$RUNTIME_AUTHORITY_COMMIT
runtime_run=$RUNTIME_ACTIONS_RUN
runtime_artifact_id=$RUNTIME_ARTIFACT_ID
runtime_artifact_name=$RUNTIME_ARTIFACT_NAME
runtime_artifact_sha256=$RUNTIME_ARTIFACT_SHA
runtime_candidate_tar_sha256=$RUNTIME_TAR_SHA
mechanics_commit=$MECHANICS_AUTHORITY_COMMIT
mechanics_run=$MECHANICS_ACTIONS_RUN
EOF
  pass "exact successful 26774 compiled candidate reconstructed"
}
universe_equal(){
  python3 -S - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=U(sys.argv[1]),U(sys.argv[2]); assert a==b,(len(a),len(b)); print(f'PASS byte-identical app universe: {len(a)} files')
PY
}
make_candidate(){
  python3 -S transform_26775.py "$BASE" "$CAND" handoff_payload_26775
  python3 -S validate_26775.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26775_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail "26775 candidate manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26775_PROTECTED_26774.sha256" >/dev/null) || fail "26775 protected manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26775_NATIVE_26774.sha256" >/dev/null) || fail "26775 native invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26775_VENDOR_26774.sha256" >/dev/null) || fail "26775 vendor invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26775_DNG_26774.sha256" >/dev/null) || fail "26775 DNG invariance"
  [[ "$(find "$CAND/app" -type f | wc -l)" -eq 1779 ]] || fail "26775 candidate file count"
  pass "candidate-first 26775 reconstruction/domain/ownership checks"
}
verify_successful_mechanics(){
  local a74="$WORK/authority_26774_build.sh" a52="$WORK/authority_26752_build.sh"
  git show "$RUNTIME_AUTHORITY_COMMIT:build_26774_histogram_downward_hinge.sh" > "$a74"
  git show "$MECHANICS_AUTHORITY_COMMIT:build_26752_ipol_plan_b_translational_sr.sh" > "$a52"
  grep -F 'export IRIS26774_GLSLANG="$compiler"' "$a74" >/dev/null || fail "26774 primary glslang handoff missing"
  grep -F 'export IRIS26681_SPEKTRA_GLSLANG="$compiler"' "$a74" >/dev/null || fail "26774 Spektra glslang handoff missing"
  grep -F 'compile_spektra_raw_shader(){' "$a74" >/dev/null || fail "26774 Spektra verifier stage missing"
  grep -F "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" "$a74" >/dev/null || fail "26774 both-ABI native stage missing"
  grep -F './gradlew :app:assembleDebug --stacktrace' "$a74" >/dev/null || fail "26774 assemble stage missing"
  grep -F 'export IRIS26681_SPEKTRA_GLSLANG="$compiler"' "$0" >/dev/null || fail "26775 dual glslang handoff missing"
  grep -F 'compile_spektra_raw_shader(){' "$0" >/dev/null || fail "26775 Spektra verifier stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$0" >/dev/null || fail "26775 native handoff regression missing"
  grep -F "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" "$0" >/dev/null || fail "26775 both-ABI native command differs"
  grep -F './gradlew :app:assembleDebug --stacktrace' "$0" >/dev/null || fail "26775 assemble command differs"
  python3 -S - "$0" "$a74" "$a52" <<'PY_ORDER'
from pathlib import Path
import sys
def ordered(text, marker, tokens, label):
    i=text.find(marker)
    if i < 0: raise SystemExit(f'{label}: missing marker {marker}')
    text=text[i:]; pos=-1
    for token in tokens:
        nxt=text.find(token,pos+1)
        if nxt < 0: raise SystemExit(f'{label}: missing stage {token}')
        if nxt <= pos: raise SystemExit(f'{label}: out-of-order stage {token}')
        pos=nxt
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
cur=Path(sys.argv[1]).read_text(); a74=Path(sys.argv[2]).read_text(); a52=Path(sys.argv[3]).read_text()
ordered(cur,'# IRIS_26775_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26775')
ordered(a74,'# IRIS_26774_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26774 authority')
auth52=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26751_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','mapfile -t apks','postbuild_proof']
ordered(a52,'# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER',auth52,'26752 authority')
print('PASS 26775 stage order exactly inherits successful 26774 and 26752 mechanics')
PY_ORDER
  pass "successful 26774 procedure audited: same stage order, dual glslang/Spektra, language compilers, both ABIs, assemble"
}
prepare_glslang(){
  D="$WORK/glslang-${GLSLANG_VERSION}"; A="$WORK/glslang.tar.gz"; mkdir -p "$D"
  curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"
  [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive sha"
  tar -xzf "$A" -C "$D"
  compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"
  compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]] || chmod +x "$compiler"
  "$compiler" --version | tee "$OUT/26775_glslang_version.txt"
  export IRIS26775_GLSLANG="$compiler"
  export IRIS26681_SPEKTRA_GLSLANG="$compiler"
  pass "pinned glslang 16.5.0 dual environment handoff"
}
compile_modified_runtime_shaders(){
  # 26775 modifies embedded runtime compute shaders inside the VGN Kotlin owner. Asset shader
  # bytes remain inherited, but the exact runtime-expanded modified shader strings must pass the
  # complete reserved-identifier scan and pinned real glslang 16.5.0 before language compilation.
  python3 -S - "$BASE" "$CAND" <<'PY'
from pathlib import Path
import hashlib,sys
def S(r):
 r=Path(r); return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
a,b=S(sys.argv[1]),S(sys.argv[2]); assert a==b,(len(a),len(b)); print(f'PASS inherited asset shader universe byte-identical: {len(a)} files')
PY
  python3 -S verify_26775_embedded_glsl.py "$CAND" --compiler "$IRIS26775_GLSLANG" --out "$OUT/26775_runtime_expanded_glsl" | tee "$OUT/26775_embedded_glsl_validation.txt"
  grep -F 'PASS 26775 reserved-identifier scan seed' "$OUT/26775_embedded_glsl_validation.txt" >/dev/null || fail "26775 seed reserved scan proof missing"
  grep -F 'PASS 26775 reserved-identifier scan bipolarColorTrust26769' "$OUT/26775_embedded_glsl_validation.txt" >/dev/null || fail "26775 bipolar reserved scan proof missing"
  grep -F 'PASS 26775 pinned real glslang compile: seed' "$OUT/26775_embedded_glsl_validation.txt" >/dev/null || fail "26775 seed real GLSL proof missing"
  grep -F 'PASS 26775 pinned real glslang compile: bipolarColorTrust26769' "$OUT/26775_embedded_glsl_validation.txt" >/dev/null || fail "26775 bipolar real GLSL proof missing"
  sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: PASS (modified embedded VGN seed + bipolar runtime-expanded shaders; reserved scan + pinned glslang 16.5.0)#' "$OUT/26775_COMPILER_STATUS.txt"
}

compile_spektra_raw_shader(){
  if [[ -f scripts/verify_shaders.py ]]; then
    IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/26775_spektra_shader_verify.txt"
  else
    pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"
  fi
}
verify_native_glslang_handoff(){
  [[ -n "${IRIS26681_SPEKTRA_GLSLANG:-}" ]] || fail "PERMANENT REGRESSION: IRIS26681_SPEKTRA_GLSLANG unset before NDK"
  [[ -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "PERMANENT REGRESSION: Spektra glslang not executable before NDK"
  [[ "$IRIS26681_SPEKTRA_GLSLANG" == "$IRIS26775_GLSLANG" ]] || fail "PERMANENT REGRESSION: shader and Spektra compiler paths differ"
  "$IRIS26681_SPEKTRA_GLSLANG" --version | grep -F '16.5.0' >/dev/null || fail "PERMANENT REGRESSION: Spektra compiler not pinned 16.5.0"
  printf 'IRIS26681_SPEKTRA_GLSLANG=%s\nIRIS26775_GLSLANG=%s\n' "$IRIS26681_SPEKTRA_GLSLANG" "$IRIS26775_GLSLANG" | tee "$OUT/26775_native_glslang_handoff.txt"
  pass "successful 26774 native glslang handoff preserved before both-ABI native compile"
}
install_frozen_candidate_live(){
  rm -rf app
  cp -a "$CAND/app" app
  rm -rf app/build app/.cxx
  mkdir -p "$LIVE_CANON"; cp -a "$CAND/app" "$LIVE_CANON/app"
  universe_equal "$CAND" "$LIVE_CANON"
  pass "authority-seeded canonical live candidate byte-identical to frozen 26775 candidate"
}
compile_languages(){
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26775_gradle_language_compilers.log"
  sed -i 's#REAL KOTLIN COMPILE:.*#REAL KOTLIN COMPILE: PASS#; s#REAL JAVA COMPILE:.*#REAL JAVA COMPILE: PASS (includes Data Binding orientation-property contract)#' "$OUT/26775_COMPILER_STATUS.txt"
  rm -rf "$POST_LANG"; mkdir -p "$POST_LANG"; cp -a app "$POST_LANG/app"; rm -rf "$POST_LANG/app/build" "$POST_LANG/app/.cxx"
  universe_equal "$CAND" "$POST_LANG"
  pass "real Kotlin/Java compilers passed and frozen source remained byte-identical"
}
compile_native(){
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/26775_gradle_native_compiler.log"
  sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#' "$OUT/26775_COMPILER_STATUS.txt"
}
verify_candidate_patches(){
  python3 -S verify_26775_patches.py "$BASE" "$CAND" | tee "$OUT/26775_patch_validation.txt"
  for n in 7 12 40; do
    grep -F "PASS 26775 full-index forward/rollback core.abbrev=${n} fuzz=0 exact rollback; 2 modifications" "$OUT/26775_patch_validation.txt" >/dev/null || fail "26775 abbrev${n} patch proof missing"
  done
  cp 26775_FORWARD_FULL_INDEX.patch "$OUT/26775_FORWARD_FULL_INDEX.patch"
  cp 26775_ROLLBACK_FULL_INDEX.patch "$OUT/26775_ROLLBACK_FULL_INDEX.patch"
  pass "sealed full-index forward/rollback proof: successful 26774 -> exact 2-file 26775 candidate"
}
prebuild_safety(){
  universe_equal "$CAND" "$POST_LANG"
  python3 -S validate_26775.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26775_PROTECTED_26774.sha256" >/dev/null) || fail "prebuild protected manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26775_NATIVE_26774.sha256" >/dev/null) || fail "prebuild native manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26775_VENDOR_26774.sha256" >/dev/null) || fail "prebuild vendor manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26775_DNG_26774.sha256" >/dev/null) || fail "prebuild DNG manifest"
  grep -F 'REAL GLSL COMPILE: PASS' "$OUT/26775_COMPILER_STATUS.txt" >/dev/null
  grep -F 'REAL KOTLIN COMPILE: PASS' "$OUT/26775_COMPILER_STATUS.txt" >/dev/null
  grep -F 'REAL JAVA COMPILE: PASS' "$OUT/26775_COMPILER_STATUS.txt" >/dev/null
  grep -F 'NATIVE/NDK COMPILE: PASS' "$OUT/26775_COMPILER_STATUS.txt" >/dev/null
  grep -F 'PASS 26775 canonical patch proof' "$OUT/26775_patch_validation.txt" >/dev/null || fail "26775 canonical patch proof missing"
  echo 'PRE-BUILD SAFETY PROOF PASSED' | tee "$OUT/26775_PREBUILD_SAFETY.txt"
}
assemble(){
  ./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26775_gradle_assemble.log"
  mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk')
  [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#apks[@]}"
  cp "${apks[0]}" "$FINAL"
  [[ -f "$FINAL" ]] || fail "final APK missing"
  sha256sum "$FINAL" > "$OUT/26775_APK.sha256"
  sed -i 's#FULL ANDROID ASSEMBLE:.*#FULL ANDROID ASSEMBLE: PASS (exactly one APK)#' "$OUT/26775_COMPILER_STATUS.txt"
}
postbuild_proof(){
  rm -rf "$WORK/postbuild"; mkdir -p "$WORK/postbuild"; cp -a app "$WORK/postbuild/app"; rm -rf "$WORK/postbuild/app/build" "$WORK/postbuild/app/.cxx"
  universe_equal "$CAND" "$WORK/postbuild"
  for manifest in 26775_PROTECTED_26774.sha256 26775_NATIVE_26774.sha256 26775_VENDOR_26774.sha256 26775_DNG_26774.sha256; do
    (cd "$WORK/postbuild" && sha256sum -c "$ROOT/$manifest" >/dev/null) || fail "postbuild $manifest"
  done
  tar -czf "$OUT/26775_candidate_app_source.tar.gz" -C "$CAND" app
  sha256sum "$OUT/26775_candidate_app_source.tar.gz" > "$OUT/26775_candidate_app_source.tar.gz.sha256"
  (cd "$CAND" && find app -type f -print0 | sort -z | xargs -0 sha256sum) > "$OUT/26775_candidate_full_app.sha256"
  cmp -s "$OUT/26775_candidate_full_app.sha256" "$ROOT/26775_EXPECTED_CANDIDATE_FULL_APP.sha256" || fail "final candidate manifest differs from frozen candidate"
  sed -i 's#POST-BUILD INVARIANCE:.*#POST-BUILD INVARIANCE: PASS#' "$OUT/26775_COMPILER_STATUS.txt"
  pass "authority-seeded post-build protected/DNG/native/vendor/source invariance"
}
clean_extract_replay(){
  sha256sum -c 26775_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26775_resolve_vgn_phase_validity.sh
  python3 -S -m py_compile transform_26775.py validate_26775.py verify_26775_patches.py verify_26775_embedded_glsl.py
  rm -rf __pycache__
  python3 -S validate_26775.py "$BASE" "$CAND"
  python3 -S verify_26775_embedded_glsl.py "$CAND" | tee "$OUT/26775_final_embedded_glsl_static_replay.txt"
  grep -F 'PASS 26775 pinned real glslang compile: seed' "$OUT/26775_embedded_glsl_validation.txt" >/dev/null || fail "final seed real GLSL proof missing"
  grep -F 'PASS 26775 pinned real glslang compile: bipolarColorTrust26769' "$OUT/26775_embedded_glsl_validation.txt" >/dev/null || fail "final bipolar real GLSL proof missing"
  python3 -S verify_26775_patches.py "$BASE" "$CAND" | tee "$OUT/26775_final_patch_replay.txt"
  cmp -s 26775_FORWARD_FULL_INDEX.patch "$OUT/26775_FORWARD_FULL_INDEX.patch" || fail "final forward patch bytes changed"
  cmp -s 26775_ROLLBACK_FULL_INDEX.patch "$OUT/26775_ROLLBACK_FULL_INDEX.patch" || fail "final rollback patch bytes changed"
  grep -F 'PRE-BUILD SAFETY PROOF PASSED' "$OUT/26775_PREBUILD_SAFETY.txt" >/dev/null
  for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do
    grep -F "$proof" "$OUT/26775_COMPILER_STATUS.txt" >/dev/null || fail "final proof missing: $proof"
  done
  pass "final 26775 clean replay of package hashes/ownership/version/patch/compiler/build proofs"
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
printf '\n=========================================\n26775 RESOLVE VGN PHASE VALIDITY: PASS\nRuntime authority: successful 26774 %s\nVerification mechanics authority: 26752 %s\nRuntime changed-file allowlist: 2 modified, 0 added, 0 deleted\nInfrastructure mechanics: inherited successful 26774 stage/compiler/native/assemble procedure\nReal Kotlin/Java/NDK/full assemble: PASS\nExactly one APK: PASS\n=========================================\n' "$RUNTIME_AUTHORITY_COMMIT" "$MECHANICS_AUTHORITY_COMMIT"
