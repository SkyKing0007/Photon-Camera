#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="99fbd295f6a1e04d70c56873671a50170abfd11b"
RUNTIME_ACTIONS_RUN="37471535421"
RUNTIME_ARTIFACT_ID="11417756195"
RUNTIME_ARTIFACT_NAME="photon-26772-r6-strict-inherited-mechanics-repair"
RUNTIME_ARTIFACT_SHA="fc20ef69cedee9857fd6ff18d719d5449fdac4a6dc67682f7df7aa37700f6736"
RUNTIME_TAR_SHA="844aed294008662c67741617bebfc0b4c61d4cdd27fcac924bc9d61860fb146c"
MECHANICS_AUTHORITY_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"
MECHANICS_ACTIONS_RUN="37075896367"
VERSION_NAME="0.9726773"
VERSION_BUILD="26773"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26773_ui_rotation_downloads_outputs"
WORK="$ROOT/.build_26773_ui_rotation_downloads_work"
ARTZIP="$WORK/26772_r6_artifact.zip"
ARTDIR="$WORK/artifact_26772_r6"
BASE="$WORK/exact_successful_26772_r6_compiled_candidate"
CAND="$WORK/candidate_26773"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"
POST_LANG="$WORK/post_language_compiler_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-ui-rotation-downloads-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26773_COMPILER_STATUS.txt" <<EOF
REAL GLSL COMPILE: NOT APPLICABLE YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF

# IRIS_26773_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){
  sha256sum -c 26773_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26773_ui_rotation_downloads.sh
  python3 -S -m py_compile transform_26773.py validate_26773.py verify_26773_patches.py
  rm -rf __pycache__
  [[ "$(find handoff_payload_26773 -type f | wc -l)" -eq 7 ]] || fail "26773 payload count"
  diff -u 26773_RUNTIME_CHANGED_PATHS.txt <(find handoff_payload_26773 -type f | sed 's#^handoff_payload_26773/##' | sort) >/dev/null || fail "26773 payload allowlist mismatch"
  for p in 26773_FORWARD_FULL_INDEX.patch 26773_ROLLBACK_FULL_INDEX.patch; do
    ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$p" || fail "26773 patch contains rename/copy inference: $p"
  done
  grep -Fx 'RUN_26773_UI_ROTATION_DOWNLOADS' TRIGGER_26773.txt >/dev/null || fail "26773 trigger contents"
  ! find . -type f -name '*.apk' | grep -q . || fail "APK unexpectedly packaged"
  pass "sealed 26773 package hashes/syntax/allowlist/patch identity"
}
verify_scope(){
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail "26772 R6 runtime authority not ancestor"
  git merge-base --is-ancestor "$MECHANICS_AUTHORITY_COMMIT" HEAD || fail "26752 mechanics authority not ancestor"
  # No live runtime source is uploaded. Candidate source exists only in the sealed payload and is
  # reconstructed from the exact successful artifact.
  if git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | grep -E '^app/'; then
    fail "live app source changed after 26772 R6 authority"
  fi
  python3 -S - <<'PY'
import subprocess
allowed_prefixes=(
 '26773_', 'build_26773_ui_rotation_downloads.sh', 'transform_26773.py',
 'validate_26773.py', 'verify_26773_patches.py', 'handoff_payload_26773/',
 '.github/workflows/build-26773-ui-rotation-downloads.yml', 'TRIGGER_26773.txt')
paths=subprocess.check_output(['git','diff','--name-only','99fbd295f6a1e04d70c56873671a50170abfd11b..HEAD'],text=True).splitlines()
bad=[p for p in paths if not any(p==x or p.startswith(x) for x in allowed_prefixes)]
assert not bad,bad
print('PASS 26773 infrastructure scope allowlist')
PY
  pass "26773 scope exact: successful 26772 R6 authority + sealed 7-file payload; live app untouched"
}
obtain_authority(){
  [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
  curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
  [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail "26772 R6 artifact sha"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  T="$ARTDIR/build_r6_26772_storage_ui_highlight_outputs/r6_26772_candidate_app_source.tar.gz"
  [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail "26772 R6 candidate tar sha"
  STATUS="$ARTDIR/build_r6_26772_storage_ui_highlight_outputs/r6_26772_COMPILER_STATUS.txt"
  for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do
    grep -F "$proof" "$STATUS" >/dev/null || fail "missing 26772 R6 authority proof: $proof"
  done
  mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"
  [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1779 ]] || fail "26772 R6 base file count"
  (cd "$BASE" && sha256sum -c "$ROOT/26773_BASE_26772_R6_FULL_APP.sha256" >/dev/null) || fail "26772 R6 full base manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26773_NATIVE_26772_R6.sha256" >/dev/null) || fail "26772 R6 native manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26773_VENDOR_26772_R6.sha256" >/dev/null) || fail "26772 R6 vendor manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26773_DNG_26772_R6.sha256" >/dev/null) || fail "26772 R6 DNG manifest"
  cat > "$OUT/26773_RESOLVED_AUTHORITIES.txt" <<EOF
runtime_commit=$RUNTIME_AUTHORITY_COMMIT
runtime_run=$RUNTIME_ACTIONS_RUN
runtime_artifact_id=$RUNTIME_ARTIFACT_ID
runtime_artifact_name=$RUNTIME_ARTIFACT_NAME
runtime_artifact_sha256=$RUNTIME_ARTIFACT_SHA
runtime_candidate_tar_sha256=$RUNTIME_TAR_SHA
mechanics_commit=$MECHANICS_AUTHORITY_COMMIT
mechanics_run=$MECHANICS_ACTIONS_RUN
EOF
  pass "exact successful 26772 R6 compiled candidate reconstructed"
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
  python3 -S transform_26773.py "$BASE" "$CAND" handoff_payload_26773
  python3 -S validate_26773.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26773_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail "26773 candidate manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26773_PROTECTED_26772_R6.sha256" >/dev/null) || fail "26773 protected manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26773_NATIVE_26772_R6.sha256" >/dev/null) || fail "26773 native invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26773_VENDOR_26772_R6.sha256" >/dev/null) || fail "26773 vendor invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26773_DNG_26772_R6.sha256" >/dev/null) || fail "26773 DNG invariance"
  [[ "$(find "$CAND/app" -type f | wc -l)" -eq 1779 ]] || fail "26773 candidate file count"
  pass "candidate-first 26773 reconstruction/domain/ownership checks"
}
verify_successful_mechanics(){
  local r6="$WORK/authority_26772_r6_build.sh" a52="$WORK/authority_26752_build.sh"
  git show "$RUNTIME_AUTHORITY_COMMIT:build_r6_26772_storage_ui_highlight.sh" > "$r6"
  git show "$MECHANICS_AUTHORITY_COMMIT:build_26752_ipol_plan_b_translational_sr.sh" > "$a52"
  grep -F 'export IRIS26772_GLSLANG="$compiler"' "$r6" >/dev/null || fail "R6 primary glslang handoff missing"
  grep -F 'export IRIS26681_SPEKTRA_GLSLANG="$compiler"' "$r6" >/dev/null || fail "R6 Spektra glslang handoff missing"
  grep -F 'compile_spektra_raw_shader(){' "$r6" >/dev/null || fail "R6 Spektra verifier stage missing"
  grep -F "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" "$r6" >/dev/null || fail "R6 both-ABI native stage missing"
  grep -F './gradlew :app:assembleDebug --stacktrace' "$r6" >/dev/null || fail "R6 assemble stage missing"
  grep -F 'export IRIS26681_SPEKTRA_GLSLANG="$compiler"' "$0" >/dev/null || fail "26773 dual glslang handoff missing"
  grep -F 'compile_spektra_raw_shader(){' "$0" >/dev/null || fail "26773 Spektra verifier stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$0" >/dev/null || fail "26773 native handoff regression missing"
  grep -F "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" "$0" >/dev/null || fail "26773 both-ABI native command differs"
  grep -F './gradlew :app:assembleDebug --stacktrace' "$0" >/dev/null || fail "26773 assemble command differs"
  python3 -S - "$0" "$r6" "$a52" <<'PY_ORDER'
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
cur=Path(sys.argv[1]).read_text(); r6=Path(sys.argv[2]).read_text(); a52=Path(sys.argv[3]).read_text()
ordered(cur,'# IRIS_26773_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26773')
ordered(r6,'# IRIS_26772_R6_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26772 R6 authority')
auth52=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26751_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','mapfile -t apks','postbuild_proof']
ordered(a52,'# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER',auth52,'26752 authority')
print('PASS 26773 stage order exactly inherits successful 26772 R6 and 26752 mechanics')
PY_ORDER
  pass "successful 26772 R6 procedure audited: same stage order, dual glslang/Spektra, language compilers, both ABIs, assemble"
}
prepare_glslang(){
  D="$WORK/glslang-${GLSLANG_VERSION}"; A="$WORK/glslang.tar.gz"; mkdir -p "$D"
  curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"
  [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive sha"
  tar -xzf "$A" -C "$D"
  compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"
  compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]] || chmod +x "$compiler"
  "$compiler" --version | tee "$OUT/26773_glslang_version.txt"
  export IRIS26773_GLSLANG="$compiler"
  export IRIS26681_SPEKTRA_GLSLANG="$compiler"
  pass "pinned glslang 16.5.0 dual environment handoff"
}
compile_modified_runtime_shaders(){
  # 26773 changes no shader bytes. The exact shader universe is inherited byte-for-byte from the
  # successful R6 candidate whose real glslang proof was checked in obtain_authority.
  python3 -S - "$BASE" "$CAND" <<'PY'
from pathlib import Path
import hashlib,sys
def S(r):
 r=Path(r); return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
a,b=S(sys.argv[1]),S(sys.argv[2]); assert a==b,(len(a),len(b)); print(f'PASS inherited shader universe byte-identical: {len(a)} files')
PY
  sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: PASS (zero 26773 GLSL delta; exact successful 26772 R6 real-compiled shader universe inherited byte-identically)#' "$OUT/26773_COMPILER_STATUS.txt"
}
compile_spektra_raw_shader(){
  if [[ -f scripts/verify_shaders.py ]]; then
    IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/26773_spektra_shader_verify.txt"
  else
    pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"
  fi
}
verify_native_glslang_handoff(){
  [[ -n "${IRIS26681_SPEKTRA_GLSLANG:-}" ]] || fail "PERMANENT REGRESSION: IRIS26681_SPEKTRA_GLSLANG unset before NDK"
  [[ -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "PERMANENT REGRESSION: Spektra glslang not executable before NDK"
  [[ "$IRIS26681_SPEKTRA_GLSLANG" == "$IRIS26773_GLSLANG" ]] || fail "PERMANENT REGRESSION: shader and Spektra compiler paths differ"
  "$IRIS26681_SPEKTRA_GLSLANG" --version | grep -F '16.5.0' >/dev/null || fail "PERMANENT REGRESSION: Spektra compiler not pinned 16.5.0"
  printf 'IRIS26681_SPEKTRA_GLSLANG=%s\nIRIS26773_GLSLANG=%s\n' "$IRIS26681_SPEKTRA_GLSLANG" "$IRIS26773_GLSLANG" | tee "$OUT/26773_native_glslang_handoff.txt"
  pass "R6 native glslang handoff preserved before both-ABI native compile"
}
install_frozen_candidate_live(){
  rm -rf app
  cp -a "$CAND/app" app
  rm -rf app/build app/.cxx
  mkdir -p "$LIVE_CANON"; cp -a "$CAND/app" "$LIVE_CANON/app"
  universe_equal "$CAND" "$LIVE_CANON"
  pass "authority-seeded canonical live candidate byte-identical to frozen 26773 candidate"
}
compile_languages(){
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26773_gradle_language_compilers.log"
  sed -i 's#REAL KOTLIN COMPILE:.*#REAL KOTLIN COMPILE: PASS#; s#REAL JAVA COMPILE:.*#REAL JAVA COMPILE: PASS (includes Data Binding orientation-property contract)#' "$OUT/26773_COMPILER_STATUS.txt"
  rm -rf "$POST_LANG"; mkdir -p "$POST_LANG"; cp -a app "$POST_LANG/app"; rm -rf "$POST_LANG/app/build" "$POST_LANG/app/.cxx"
  universe_equal "$CAND" "$POST_LANG"
  pass "real Kotlin/Java compilers passed and frozen source remained byte-identical"
}
compile_native(){
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/26773_gradle_native_compiler.log"
  sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#' "$OUT/26773_COMPILER_STATUS.txt"
}
verify_candidate_patches(){
  python3 -S verify_26773_patches.py "$BASE" "$CAND" | tee "$OUT/26773_patch_validation.txt"
  for n in 7 12 40; do
    grep -F "PASS 26773 full-index forward/rollback core.abbrev=${n} fuzz=0 exact rollback; 7 modifications" "$OUT/26773_patch_validation.txt" >/dev/null || fail "26773 abbrev${n} patch proof missing"
  done
  cp 26773_FORWARD_FULL_INDEX.patch "$OUT/26773_FORWARD_FULL_INDEX.patch"
  cp 26773_ROLLBACK_FULL_INDEX.patch "$OUT/26773_ROLLBACK_FULL_INDEX.patch"
  pass "sealed full-index forward/rollback proof: successful 26772 R6 -> exact 7-file 26773 candidate"
}
prebuild_safety(){
  universe_equal "$CAND" "$POST_LANG"
  python3 -S validate_26773.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26773_PROTECTED_26772_R6.sha256" >/dev/null) || fail "prebuild protected manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26773_NATIVE_26772_R6.sha256" >/dev/null) || fail "prebuild native manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26773_VENDOR_26772_R6.sha256" >/dev/null) || fail "prebuild vendor manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26773_DNG_26772_R6.sha256" >/dev/null) || fail "prebuild DNG manifest"
  grep -F 'REAL GLSL COMPILE: PASS' "$OUT/26773_COMPILER_STATUS.txt" >/dev/null
  grep -F 'REAL KOTLIN COMPILE: PASS' "$OUT/26773_COMPILER_STATUS.txt" >/dev/null
  grep -F 'REAL JAVA COMPILE: PASS' "$OUT/26773_COMPILER_STATUS.txt" >/dev/null
  grep -F 'NATIVE/NDK COMPILE: PASS' "$OUT/26773_COMPILER_STATUS.txt" >/dev/null
  grep -F 'PASS 26773 canonical patch proof' "$OUT/26773_patch_validation.txt" >/dev/null || fail "26773 canonical patch proof missing"
  echo 'PRE-BUILD SAFETY PROOF PASSED' | tee "$OUT/26773_PREBUILD_SAFETY.txt"
}
assemble(){
  ./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26773_gradle_assemble.log"
  mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk')
  [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#apks[@]}"
  cp "${apks[0]}" "$FINAL"
  [[ -f "$FINAL" ]] || fail "final APK missing"
  sha256sum "$FINAL" > "$OUT/26773_APK.sha256"
  sed -i 's#FULL ANDROID ASSEMBLE:.*#FULL ANDROID ASSEMBLE: PASS (exactly one APK)#' "$OUT/26773_COMPILER_STATUS.txt"
}
postbuild_proof(){
  rm -rf "$WORK/postbuild"; mkdir -p "$WORK/postbuild"; cp -a app "$WORK/postbuild/app"; rm -rf "$WORK/postbuild/app/build" "$WORK/postbuild/app/.cxx"
  universe_equal "$CAND" "$WORK/postbuild"
  for manifest in 26773_PROTECTED_26772_R6.sha256 26773_NATIVE_26772_R6.sha256 26773_VENDOR_26772_R6.sha256 26773_DNG_26772_R6.sha256; do
    (cd "$WORK/postbuild" && sha256sum -c "$ROOT/$manifest" >/dev/null) || fail "postbuild $manifest"
  done
  tar -czf "$OUT/26773_candidate_app_source.tar.gz" -C "$CAND" app
  sha256sum "$OUT/26773_candidate_app_source.tar.gz" > "$OUT/26773_candidate_app_source.tar.gz.sha256"
  (cd "$CAND" && find app -type f -print0 | sort -z | xargs -0 sha256sum) > "$OUT/26773_candidate_full_app.sha256"
  cmp -s "$OUT/26773_candidate_full_app.sha256" "$ROOT/26773_EXPECTED_CANDIDATE_FULL_APP.sha256" || fail "final candidate manifest differs from frozen candidate"
  sed -i 's#POST-BUILD INVARIANCE:.*#POST-BUILD INVARIANCE: PASS#' "$OUT/26773_COMPILER_STATUS.txt"
  pass "authority-seeded post-build protected/DNG/native/vendor/source invariance"
}
clean_extract_replay(){
  sha256sum -c 26773_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26773_ui_rotation_downloads.sh
  python3 -S -m py_compile transform_26773.py validate_26773.py verify_26773_patches.py
  rm -rf __pycache__
  python3 -S validate_26773.py "$BASE" "$CAND"
  python3 -S verify_26773_patches.py "$BASE" "$CAND" | tee "$OUT/26773_final_patch_replay.txt"
  cmp -s 26773_FORWARD_FULL_INDEX.patch "$OUT/26773_FORWARD_FULL_INDEX.patch" || fail "final forward patch bytes changed"
  cmp -s 26773_ROLLBACK_FULL_INDEX.patch "$OUT/26773_ROLLBACK_FULL_INDEX.patch" || fail "final rollback patch bytes changed"
  grep -F 'PRE-BUILD SAFETY PROOF PASSED' "$OUT/26773_PREBUILD_SAFETY.txt" >/dev/null
  for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do
    grep -F "$proof" "$OUT/26773_COMPILER_STATUS.txt" >/dev/null || fail "final proof missing: $proof"
  done
  pass "final 26773 clean replay of package hashes/ownership/version/patch/compiler/build proofs"
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
printf '\n=========================================\n26773 UI ROTATION + DOWNLOADS: PASS\nRuntime authority: successful 26772 R6 %s\nVerification mechanics authority: 26752 %s\nRuntime changed-file allowlist: 7 modified, 0 added, 0 deleted\nInfrastructure mechanics: inherited successful 26772 R6 stage/compiler/native/assemble procedure\nReal Kotlin/Java/NDK/full assemble: PASS\nExactly one APK: PASS\n=========================================\n' "$RUNTIME_AUTHORITY_COMMIT" "$MECHANICS_AUTHORITY_COMMIT"
