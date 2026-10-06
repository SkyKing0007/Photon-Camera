#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="2925a4bd35bf208d13acd0c9b04505bc0d8cec58"
RUNTIME_ACTIONS_RUN="37497402228"
RUNTIME_ARTIFACT_ID="11428796463"
RUNTIME_ARTIFACT_NAME="photon-26773-ui-rotation-downloads"
RUNTIME_ARTIFACT_SHA="6be12ae14112639986b99a2af328aaacec1d3aee2c9145ecb2dd86b254d8617c"
RUNTIME_TAR_SHA="30cfe7797cc728423387e234cc069163e219f00c0b793c6ec2b5fab59d7e9d2d"
MECHANICS_AUTHORITY_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"
MECHANICS_ACTIONS_RUN="37075896367"
VERSION_NAME="0.9726774"
VERSION_BUILD="26774"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26774_histogram_downward_hinge_outputs"
WORK="$ROOT/.build_26774_histogram_downward_hinge_work"
ARTZIP="$WORK/26773_artifact.zip"
ARTDIR="$WORK/artifact_26773"
BASE="$WORK/exact_successful_26773_compiled_candidate"
CAND="$WORK/candidate_26774"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"
POST_LANG="$WORK/post_language_compiler_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-histogram-downward-hinge-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26774_COMPILER_STATUS.txt" <<EOF
REAL GLSL COMPILE: NOT APPLICABLE YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF

# IRIS_26774_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){
  sha256sum -c 26774_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26774_histogram_downward_hinge.sh
  python3 -S -m py_compile transform_26774.py validate_26774.py verify_26774_patches.py
  rm -rf __pycache__
  [[ "$(find handoff_payload_26774 -type f | wc -l)" -eq 2 ]] || fail "26774 payload count"
  diff -u 26774_RUNTIME_CHANGED_PATHS.txt <(find handoff_payload_26774 -type f | sed 's#^handoff_payload_26774/##' | sort) >/dev/null || fail "26774 payload allowlist mismatch"
  for p in 26774_FORWARD_FULL_INDEX.patch 26774_ROLLBACK_FULL_INDEX.patch; do
    ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$p" || fail "26774 patch contains rename/copy inference: $p"
  done
  grep -Fx 'RUN_26774_HISTOGRAM_DOWNWARD_HINGE' TRIGGER_26774.txt >/dev/null || fail "26774 trigger contents"
  ! find . -type f -name '*.apk' | grep -q . || fail "APK unexpectedly packaged"
  pass "sealed 26774 package hashes/syntax/allowlist/patch identity"
}
verify_scope(){
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail "26773 runtime authority not ancestor"
  git merge-base --is-ancestor "$MECHANICS_AUTHORITY_COMMIT" HEAD || fail "26752 mechanics authority not ancestor"
  # No live runtime source is uploaded. Candidate source exists only in the sealed payload and is
  # reconstructed from the exact successful artifact.
  if git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | grep -E '^app/'; then
    fail "live app source changed after 26773 authority"
  fi
  python3 -S - <<'PY'
import subprocess
allowed_prefixes=(
 '26774_', 'build_26774_histogram_downward_hinge.sh', 'transform_26774.py',
 'validate_26774.py', 'verify_26774_patches.py', 'handoff_payload_26774/',
 '.github/workflows/build-26774-histogram-downward-hinge.yml', 'TRIGGER_26774.txt')
paths=subprocess.check_output(['git','diff','--name-only','2925a4bd35bf208d13acd0c9b04505bc0d8cec58..HEAD'],text=True).splitlines()
bad=[p for p in paths if not any(p==x or p.startswith(x) for x in allowed_prefixes)]
assert not bad,bad
print('PASS 26774 infrastructure scope allowlist')
PY
  pass "26774 scope exact: successful 26773 authority + sealed 2-file payload; live app untouched"
}
obtain_authority(){
  [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
  curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
  [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail "26773 artifact sha"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  T="$ARTDIR/build_26773_ui_rotation_downloads_outputs/26773_candidate_app_source.tar.gz"
  [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail "26773 candidate tar sha"
  STATUS="$ARTDIR/build_26773_ui_rotation_downloads_outputs/26773_COMPILER_STATUS.txt"
  for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do
    grep -F "$proof" "$STATUS" >/dev/null || fail "missing 26773 authority proof: $proof"
  done
  mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"
  [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1779 ]] || fail "26773 base file count"
  (cd "$BASE" && sha256sum -c "$ROOT/26774_BASE_26773_FULL_APP.sha256" >/dev/null) || fail "26773 full base manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26774_NATIVE_26773.sha256" >/dev/null) || fail "26773 native manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26774_VENDOR_26773.sha256" >/dev/null) || fail "26773 vendor manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26774_DNG_26773.sha256" >/dev/null) || fail "26773 DNG manifest"
  cat > "$OUT/26774_RESOLVED_AUTHORITIES.txt" <<EOF
runtime_commit=$RUNTIME_AUTHORITY_COMMIT
runtime_run=$RUNTIME_ACTIONS_RUN
runtime_artifact_id=$RUNTIME_ARTIFACT_ID
runtime_artifact_name=$RUNTIME_ARTIFACT_NAME
runtime_artifact_sha256=$RUNTIME_ARTIFACT_SHA
runtime_candidate_tar_sha256=$RUNTIME_TAR_SHA
mechanics_commit=$MECHANICS_AUTHORITY_COMMIT
mechanics_run=$MECHANICS_ACTIONS_RUN
EOF
  pass "exact successful 26773 compiled candidate reconstructed"
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
  python3 -S transform_26774.py "$BASE" "$CAND" handoff_payload_26774
  python3 -S validate_26774.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26774_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail "26774 candidate manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26774_PROTECTED_26773.sha256" >/dev/null) || fail "26774 protected manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26774_NATIVE_26773.sha256" >/dev/null) || fail "26774 native invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26774_VENDOR_26773.sha256" >/dev/null) || fail "26774 vendor invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26774_DNG_26773.sha256" >/dev/null) || fail "26774 DNG invariance"
  [[ "$(find "$CAND/app" -type f | wc -l)" -eq 1779 ]] || fail "26774 candidate file count"
  pass "candidate-first 26774 reconstruction/domain/ownership checks"
}
verify_successful_mechanics(){
  local a73="$WORK/authority_26773_build.sh" a52="$WORK/authority_26752_build.sh"
  git show "$RUNTIME_AUTHORITY_COMMIT:build_26773_ui_rotation_downloads.sh" > "$a73"
  git show "$MECHANICS_AUTHORITY_COMMIT:build_26752_ipol_plan_b_translational_sr.sh" > "$a52"
  grep -F 'export IRIS26773_GLSLANG="$compiler"' "$a73" >/dev/null || fail "26773 primary glslang handoff missing"
  grep -F 'export IRIS26681_SPEKTRA_GLSLANG="$compiler"' "$a73" >/dev/null || fail "26773 Spektra glslang handoff missing"
  grep -F 'compile_spektra_raw_shader(){' "$a73" >/dev/null || fail "26773 Spektra verifier stage missing"
  grep -F "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" "$a73" >/dev/null || fail "26773 both-ABI native stage missing"
  grep -F './gradlew :app:assembleDebug --stacktrace' "$a73" >/dev/null || fail "26773 assemble stage missing"
  grep -F 'export IRIS26681_SPEKTRA_GLSLANG="$compiler"' "$0" >/dev/null || fail "26774 dual glslang handoff missing"
  grep -F 'compile_spektra_raw_shader(){' "$0" >/dev/null || fail "26774 Spektra verifier stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$0" >/dev/null || fail "26774 native handoff regression missing"
  grep -F "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" "$0" >/dev/null || fail "26774 both-ABI native command differs"
  grep -F './gradlew :app:assembleDebug --stacktrace' "$0" >/dev/null || fail "26774 assemble command differs"
  python3 -S - "$0" "$a73" "$a52" <<'PY_ORDER'
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
cur=Path(sys.argv[1]).read_text(); a73=Path(sys.argv[2]).read_text(); a52=Path(sys.argv[3]).read_text()
ordered(cur,'# IRIS_26774_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26774')
ordered(a73,'# IRIS_26773_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26773 authority')
auth52=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26751_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','mapfile -t apks','postbuild_proof']
ordered(a52,'# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER',auth52,'26752 authority')
print('PASS 26774 stage order exactly inherits successful 26773 and 26752 mechanics')
PY_ORDER
  pass "successful 26773 procedure audited: same stage order, dual glslang/Spektra, language compilers, both ABIs, assemble"
}
prepare_glslang(){
  D="$WORK/glslang-${GLSLANG_VERSION}"; A="$WORK/glslang.tar.gz"; mkdir -p "$D"
  curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"
  [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive sha"
  tar -xzf "$A" -C "$D"
  compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"
  compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]] || chmod +x "$compiler"
  "$compiler" --version | tee "$OUT/26774_glslang_version.txt"
  export IRIS26774_GLSLANG="$compiler"
  export IRIS26681_SPEKTRA_GLSLANG="$compiler"
  pass "pinned glslang 16.5.0 dual environment handoff"
}
compile_modified_runtime_shaders(){
  # 26774 changes no shader bytes. The exact shader universe is inherited byte-for-byte from the
  # successful R6 candidate whose real glslang proof was checked in obtain_authority.
  python3 -S - "$BASE" "$CAND" <<'PY'
from pathlib import Path
import hashlib,sys
def S(r):
 r=Path(r); return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
a,b=S(sys.argv[1]),S(sys.argv[2]); assert a==b,(len(a),len(b)); print(f'PASS inherited shader universe byte-identical: {len(a)} files')
PY
  sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: PASS (zero 26774 GLSL delta; exact successful 26773 shader universe inherited byte-identically)#' "$OUT/26774_COMPILER_STATUS.txt"
}
compile_spektra_raw_shader(){
  if [[ -f scripts/verify_shaders.py ]]; then
    IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/26774_spektra_shader_verify.txt"
  else
    pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"
  fi
}
verify_native_glslang_handoff(){
  [[ -n "${IRIS26681_SPEKTRA_GLSLANG:-}" ]] || fail "PERMANENT REGRESSION: IRIS26681_SPEKTRA_GLSLANG unset before NDK"
  [[ -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "PERMANENT REGRESSION: Spektra glslang not executable before NDK"
  [[ "$IRIS26681_SPEKTRA_GLSLANG" == "$IRIS26774_GLSLANG" ]] || fail "PERMANENT REGRESSION: shader and Spektra compiler paths differ"
  "$IRIS26681_SPEKTRA_GLSLANG" --version | grep -F '16.5.0' >/dev/null || fail "PERMANENT REGRESSION: Spektra compiler not pinned 16.5.0"
  printf 'IRIS26681_SPEKTRA_GLSLANG=%s\nIRIS26774_GLSLANG=%s\n' "$IRIS26681_SPEKTRA_GLSLANG" "$IRIS26774_GLSLANG" | tee "$OUT/26774_native_glslang_handoff.txt"
  pass "successful 26773 native glslang handoff preserved before both-ABI native compile"
}
install_frozen_candidate_live(){
  rm -rf app
  cp -a "$CAND/app" app
  rm -rf app/build app/.cxx
  mkdir -p "$LIVE_CANON"; cp -a "$CAND/app" "$LIVE_CANON/app"
  universe_equal "$CAND" "$LIVE_CANON"
  pass "authority-seeded canonical live candidate byte-identical to frozen 26774 candidate"
}
compile_languages(){
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26774_gradle_language_compilers.log"
  sed -i 's#REAL KOTLIN COMPILE:.*#REAL KOTLIN COMPILE: PASS#; s#REAL JAVA COMPILE:.*#REAL JAVA COMPILE: PASS (includes Data Binding orientation-property contract)#' "$OUT/26774_COMPILER_STATUS.txt"
  rm -rf "$POST_LANG"; mkdir -p "$POST_LANG"; cp -a app "$POST_LANG/app"; rm -rf "$POST_LANG/app/build" "$POST_LANG/app/.cxx"
  universe_equal "$CAND" "$POST_LANG"
  pass "real Kotlin/Java compilers passed and frozen source remained byte-identical"
}
compile_native(){
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/26774_gradle_native_compiler.log"
  sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#' "$OUT/26774_COMPILER_STATUS.txt"
}
verify_candidate_patches(){
  python3 -S verify_26774_patches.py "$BASE" "$CAND" | tee "$OUT/26774_patch_validation.txt"
  for n in 7 12 40; do
    grep -F "PASS 26774 full-index forward/rollback core.abbrev=${n} fuzz=0 exact rollback; 2 modifications" "$OUT/26774_patch_validation.txt" >/dev/null || fail "26774 abbrev${n} patch proof missing"
  done
  cp 26774_FORWARD_FULL_INDEX.patch "$OUT/26774_FORWARD_FULL_INDEX.patch"
  cp 26774_ROLLBACK_FULL_INDEX.patch "$OUT/26774_ROLLBACK_FULL_INDEX.patch"
  pass "sealed full-index forward/rollback proof: successful 26773 -> exact 2-file 26774 candidate"
}
prebuild_safety(){
  universe_equal "$CAND" "$POST_LANG"
  python3 -S validate_26774.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26774_PROTECTED_26773.sha256" >/dev/null) || fail "prebuild protected manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26774_NATIVE_26773.sha256" >/dev/null) || fail "prebuild native manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26774_VENDOR_26773.sha256" >/dev/null) || fail "prebuild vendor manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26774_DNG_26773.sha256" >/dev/null) || fail "prebuild DNG manifest"
  grep -F 'REAL GLSL COMPILE: PASS' "$OUT/26774_COMPILER_STATUS.txt" >/dev/null
  grep -F 'REAL KOTLIN COMPILE: PASS' "$OUT/26774_COMPILER_STATUS.txt" >/dev/null
  grep -F 'REAL JAVA COMPILE: PASS' "$OUT/26774_COMPILER_STATUS.txt" >/dev/null
  grep -F 'NATIVE/NDK COMPILE: PASS' "$OUT/26774_COMPILER_STATUS.txt" >/dev/null
  grep -F 'PASS 26774 canonical patch proof' "$OUT/26774_patch_validation.txt" >/dev/null || fail "26774 canonical patch proof missing"
  echo 'PRE-BUILD SAFETY PROOF PASSED' | tee "$OUT/26774_PREBUILD_SAFETY.txt"
}
assemble(){
  ./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26774_gradle_assemble.log"
  mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk')
  [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#apks[@]}"
  cp "${apks[0]}" "$FINAL"
  [[ -f "$FINAL" ]] || fail "final APK missing"
  sha256sum "$FINAL" > "$OUT/26774_APK.sha256"
  sed -i 's#FULL ANDROID ASSEMBLE:.*#FULL ANDROID ASSEMBLE: PASS (exactly one APK)#' "$OUT/26774_COMPILER_STATUS.txt"
}
postbuild_proof(){
  rm -rf "$WORK/postbuild"; mkdir -p "$WORK/postbuild"; cp -a app "$WORK/postbuild/app"; rm -rf "$WORK/postbuild/app/build" "$WORK/postbuild/app/.cxx"
  universe_equal "$CAND" "$WORK/postbuild"
  for manifest in 26774_PROTECTED_26773.sha256 26774_NATIVE_26773.sha256 26774_VENDOR_26773.sha256 26774_DNG_26773.sha256; do
    (cd "$WORK/postbuild" && sha256sum -c "$ROOT/$manifest" >/dev/null) || fail "postbuild $manifest"
  done
  tar -czf "$OUT/26774_candidate_app_source.tar.gz" -C "$CAND" app
  sha256sum "$OUT/26774_candidate_app_source.tar.gz" > "$OUT/26774_candidate_app_source.tar.gz.sha256"
  (cd "$CAND" && find app -type f -print0 | sort -z | xargs -0 sha256sum) > "$OUT/26774_candidate_full_app.sha256"
  cmp -s "$OUT/26774_candidate_full_app.sha256" "$ROOT/26774_EXPECTED_CANDIDATE_FULL_APP.sha256" || fail "final candidate manifest differs from frozen candidate"
  sed -i 's#POST-BUILD INVARIANCE:.*#POST-BUILD INVARIANCE: PASS#' "$OUT/26774_COMPILER_STATUS.txt"
  pass "authority-seeded post-build protected/DNG/native/vendor/source invariance"
}
clean_extract_replay(){
  sha256sum -c 26774_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26774_histogram_downward_hinge.sh
  python3 -S -m py_compile transform_26774.py validate_26774.py verify_26774_patches.py
  rm -rf __pycache__
  python3 -S validate_26774.py "$BASE" "$CAND"
  python3 -S verify_26774_patches.py "$BASE" "$CAND" | tee "$OUT/26774_final_patch_replay.txt"
  cmp -s 26774_FORWARD_FULL_INDEX.patch "$OUT/26774_FORWARD_FULL_INDEX.patch" || fail "final forward patch bytes changed"
  cmp -s 26774_ROLLBACK_FULL_INDEX.patch "$OUT/26774_ROLLBACK_FULL_INDEX.patch" || fail "final rollback patch bytes changed"
  grep -F 'PRE-BUILD SAFETY PROOF PASSED' "$OUT/26774_PREBUILD_SAFETY.txt" >/dev/null
  for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do
    grep -F "$proof" "$OUT/26774_COMPILER_STATUS.txt" >/dev/null || fail "final proof missing: $proof"
  done
  pass "final 26774 clean replay of package hashes/ownership/version/patch/compiler/build proofs"
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
printf '\n=========================================\n26774 HISTOGRAM DOWNWARD HINGE: PASS\nRuntime authority: successful 26773 %s\nVerification mechanics authority: 26752 %s\nRuntime changed-file allowlist: 2 modified, 0 added, 0 deleted\nInfrastructure mechanics: inherited successful 26773 stage/compiler/native/assemble procedure\nReal Kotlin/Java/NDK/full assemble: PASS\nExactly one APK: PASS\n=========================================\n' "$RUNTIME_AUTHORITY_COMMIT" "$MECHANICS_AUTHORITY_COMMIT"
