#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="bb6e72a86a22ddf0aad335056525a69b09828b97"
RUNTIME_ACTIONS_RUN="37401145164"
RUNTIME_ARTIFACT_ID="11384889292"
RUNTIME_ARTIFACT_NAME="photon-26771-ui-storage-ownership"
RUNTIME_ARTIFACT_SHA="1742c0643ec58cdeda995a01df47f6b53e5624d30a8ed38a47c86c95388a4683"
RUNTIME_TAR_SHA="9144d09ff0a0317e2307f4d332d3985c85cecb226f7eaedaf8021231d16be58b"
MECHANICS_AUTHORITY_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"
MECHANICS_ACTIONS_RUN="37075896367"
FAILED_26772_COMMIT="6c8b8c96a18373a822cf54185cec97d6bb9124c0"
VERSION_NAME="0.9726772"
VERSION_BUILD="26772"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_r5_26772_storage_ui_highlight_outputs"
WORK="$ROOT/.build_r5_26772_storage_ui_highlight_work"
ARTZIP="$WORK/26771_artifact.zip"
ARTDIR="$WORK/artifact_26771"
BASE="$WORK/exact_successful_26771_compiled_candidate"
FAILED="$WORK/intended_failed_26772_candidate"
CAND="$WORK/candidate_26772_r5"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"
POST_LANG="$WORK/post_language_compiler_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-R5-storage-ui-highlight-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/r5_26772_COMPILER_STATUS.txt" <<EOF
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF

# IRIS_26772_R5_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){
  sha256sum -c r5_26772_HANDOFF_HASHES.sha256 >/dev/null
  sha256sum -c r3_26772_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_r5_26772_storage_ui_highlight.sh
  python3 -S -m py_compile r3_26772_validate.py r5_26772_make_patches.py
  rm -rf __pycache__
  [[ "$(find handoff_payload_r3_26772 -type f | wc -l)" -eq 1 ]] || fail "R3 payload count"
  ! find . -type f -name '*.apk' | grep -q . || fail "APK unexpectedly packaged"
  pass "sealed R5 infrastructure + inherited sealed R3 package hashes/syntax"
}
verify_scope(){
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail "26771 runtime authority not ancestor"
  git merge-base --is-ancestor "$MECHANICS_AUTHORITY_COMMIT" HEAD || fail "26752 mechanics authority not ancestor"
  git merge-base --is-ancestor "$FAILED_26772_COMMIT" HEAD || fail "failed 26772 package commit not ancestor"
  # R3 must not alter any previously sealed 26772 input nor live app source in Git history.
  if git diff --name-only "$FAILED_26772_COMMIT"..HEAD | grep -E '^(26772_|build_26772_storage_ui_highlight\.sh$|transform_26772\.py$|validate_26772\.py$|verify_26772_.*\.py$|handoff_payload_26772/|\.github/workflows/build-26772-storage-ui-highlight\.yml$|app/)'; then
    fail "R3 changed sealed 26772 package or live app source"
  fi
  sha256sum -c 26772_HANDOFF_HASHES.sha256 >/dev/null
  pass "R5 scope exact: successful 26771 authority + untouched sealed 26772/R3 runtime package + R5 infrastructure-only correction"
}
obtain_authority(){
  [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
  curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
  [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail "26771 artifact sha"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  T="$ARTDIR/build_26771_ui_storage_ownership_outputs/26771_candidate_app_source.tar.gz"
  [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail "26771 candidate tar sha"
  for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do
    grep -F "$proof" "$ARTDIR/build_26771_ui_storage_ownership_outputs/26771_COMPILER_STATUS.txt" >/dev/null || fail "missing 26771 authority proof: $proof"
  done
  mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"
  [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1824 ]] || fail "26771 base file count"
  (cd "$BASE" && sha256sum -c "$ROOT/26772_BASE_26771_FULL_APP.sha256" >/dev/null) || fail "26771 base manifest"
  cat > "$OUT/r5_26772_RESOLVED_AUTHORITIES.txt" <<EOF
runtime_commit=$RUNTIME_AUTHORITY_COMMIT
runtime_run=$RUNTIME_ACTIONS_RUN
runtime_artifact_id=$RUNTIME_ARTIFACT_ID
runtime_artifact_name=$RUNTIME_ARTIFACT_NAME
runtime_artifact_sha256=$RUNTIME_ARTIFACT_SHA
runtime_candidate_tar_sha256=$RUNTIME_TAR_SHA
mechanics_commit=$MECHANICS_AUTHORITY_COMMIT
mechanics_run=$MECHANICS_ACTIONS_RUN
failed_26772_commit_reference=$FAILED_26772_COMMIT
EOF
  pass "exact successful 26771 R2 compiled candidate reconstructed"
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
  # First reproduce the exact failed 26772 candidate from successful 26771 authority and its sealed payload.
  python3 -S transform_26772.py "$BASE" "$FAILED" handoff_payload_26772
  python3 -S validate_26772.py "$BASE" "$FAILED"
  (cd "$FAILED" && sha256sum -c "$ROOT/26772_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail "sealed failed-26772 candidate mismatch"
  # R3 correction is candidate-first and changes exactly the already-in-scope camera CustomBinding file.
  cp -a "$FAILED" "$CAND"
  cp handoff_payload_r3_26772/app/src/main/java/com/particlesdevs/photoncamera/ui/camera/binding/CustomBinding.java \
     "$CAND/app/src/main/java/com/particlesdevs/photoncamera/ui/camera/binding/CustomBinding.java"
  python3 -S r3_26772_validate.py "$BASE" "$FAILED" "$CAND"
  [[ "$(sha "$CAND/app/src/main/java/com/particlesdevs/photoncamera/ui/camera/binding/CustomBinding.java")" == "$(cat r3_26772_CORRECTED_CUSTOMBINDING.sha256)" ]] || fail "corrected source hash"
  # All candidate files except the repaired owner must remain byte-identical to intended 26772.
  python3 -S - "$FAILED" "$CAND" <<'PY'
from pathlib import Path
import hashlib,sys
rel='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/binding/CustomBinding.java'
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=U(sys.argv[1]),U(sys.argv[2]); d=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k)); assert d==[rel],d; print('PASS intended 26772 -> R3 delta exactly one file')
PY
  # Existing domain/protected proofs still apply because the repaired file was already a 26772 modified path.
  for manifest in 26772_PROTECTED_AUTHORITY.sha256 26772_NATIVE_AUTHORITY.sha256 26772_VENDOR_AUTHORITY.sha256 26772_DNG_AUTHORITY.sha256 26772_EXPECTED_ASSET_SHADER_UNIVERSE.sha256 26772_PROTECTED_ASSET_SHADERS.sha256; do
    (cd "$CAND" && sha256sum -c "$ROOT/$manifest" >/dev/null) || fail "$manifest"
  done
  python3 -S verify_26772_shaders.py "$BASE" "$FAILED"
  pass "candidate-first R5 reconstruction/domain/ownership checks"
}
verify_successful_mechanics(){
  local a71="$WORK/authority_26771_build.sh" a52="$WORK/authority_26752_build.sh"
  git show "$RUNTIME_AUTHORITY_COMMIT:build_26771_ui_storage_ownership.sh" > "$a71"
  git show "$MECHANICS_AUTHORITY_COMMIT:build_26752_ipol_plan_b_translational_sr.sh" > "$a52"
  grep -F 'export IRIS26771_GLSLANG="$compiler"' "$a71" >/dev/null || fail "26771 primary glslang handoff missing"
  grep -F 'export IRIS26681_SPEKTRA_GLSLANG="$compiler"' "$a71" >/dev/null || fail "26771 Spektra glslang handoff missing"
  grep -F 'compile_spektra_raw_shader(){' "$a71" >/dev/null || fail "26771 Spektra verifier stage missing"
  grep -F "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" "$a71" >/dev/null || fail "26771 both-ABI native stage missing"
  grep -F './gradlew :app:assembleDebug --stacktrace' "$a71" >/dev/null || fail "26771 assemble stage missing"
  grep -F "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'" "$a52" >/dev/null || fail "26752 both-ABI mechanics missing"
  grep -F './gradlew :app:assembleDebug' "$a52" >/dev/null || fail "26752 assemble mechanics missing"
  grep -F 'export IRIS26681_SPEKTRA_GLSLANG="$compiler"' "$0" >/dev/null || fail "R5 dual glslang handoff missing"
  grep -F 'compile_spektra_raw_shader(){' "$0" >/dev/null || fail "R5 Spektra verifier stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$0" >/dev/null || fail "R5 permanent native handoff regression missing"
  python3 -S - "$0" "$a71" "$a52" <<'PY_ORDER'
from pathlib import Path
import sys
def ordered(text, marker, tokens, label):
    i=text.find(marker)
    if i < 0: raise SystemExit(f'{label}: missing marker {marker}')
    text=text[i:]
    pos=-1
    for token in tokens:
        nxt=text.find(token,pos+1)
        if nxt < 0: raise SystemExit(f'{label}: missing stage {token}')
        if nxt <= pos: raise SystemExit(f'{label}: out-of-order stage {token}')
        pos=nxt
common=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
cur=Path(sys.argv[1]).read_text()
a71=Path(sys.argv[2]).read_text()
a52=Path(sys.argv[3]).read_text()
ordered(cur,'# IRIS_26772_R5_AUTHORITATIVE_ACTIONS_STAGE_ORDER',common,'R5')
auth71=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','mapfile -t apks','postbuild_proof']
ordered(a71,'# IRIS_26771_AUTHORITATIVE_ACTIONS_STAGE_ORDER',auth71,'26771 authority')
auth52=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26751_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','mapfile -t apks','postbuild_proof']
ordered(a52,'# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER',auth52,'26752 authority')
print('PASS R5 stage order is explicitly frozen to successful 26771/26752 mechanics')
PY_ORDER
  pass "exact successful 26771 dual-glslang/Spektra/native mechanics and successful 26752 stage/native/assemble mechanics audited"
}
prepare_glslang(){
  D="$WORK/glslang-${GLSLANG_VERSION}"; A="$WORK/glslang.tar.gz"; mkdir -p "$D"
  curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"
  [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive sha"
  tar -xzf "$A" -C "$D"
  compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"
  compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]] || chmod +x "$compiler"
  "$compiler" --version | tee "$OUT/r5_26772_glslang_version.txt"
  export IRIS26772_GLSLANG="$compiler"
  export IRIS26681_SPEKTRA_GLSLANG="$compiler"
  pass "pinned glslang 16.5.0 dual environment handoff"
}
compile_modified_runtime_shaders(){
  # R3 changes no GLSL versus intended 26772. Compile the exact intended runtime-expanded shaders with the same pinned compiler.
  python3 -S verify_26772_shaders.py "$BASE" "$FAILED" --compiler "$IRIS26772_GLSLANG" | tee "$OUT/r5_26772_shader_compiler_validation.txt"
  sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: PASS (exact intended 26772 runtime-expanded shader set recompiled with pinned glslang 16.5.0; R5 infrastructure-only correction adds no shader delta)#' "$OUT/r5_26772_COMPILER_STATUS.txt"
}
compile_spektra_raw_shader(){
  if [[ -f scripts/verify_shaders.py ]]; then
    IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/r5_26772_spektra_shader_verify.txt"
  else
    pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"
  fi
}
verify_native_glslang_handoff(){
  [[ -n "${IRIS26681_SPEKTRA_GLSLANG:-}" ]] || fail "PERMANENT REGRESSION: IRIS26681_SPEKTRA_GLSLANG unset before NDK"
  [[ -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "PERMANENT REGRESSION: Spektra glslang not executable before NDK"
  [[ "$IRIS26681_SPEKTRA_GLSLANG" == "$IRIS26772_GLSLANG" ]] || fail "PERMANENT REGRESSION: shader and Spektra compiler paths differ"
  "$IRIS26681_SPEKTRA_GLSLANG" --version | grep -F '16.5.0' >/dev/null || fail "PERMANENT REGRESSION: Spektra compiler not pinned 16.5.0"
  printf 'IRIS26681_SPEKTRA_GLSLANG=%s\nIRIS26772_GLSLANG=%s\n' "$IRIS26681_SPEKTRA_GLSLANG" "$IRIS26772_GLSLANG" | tee "$OUT/r5_26772_native_glslang_handoff.txt"
  pass "permanent R3 CMake failure condition proven absent before both-ABI native compile"
}
install_frozen_candidate_live(){
  rm -rf app
  cp -a "$CAND/app" app
  rm -rf app/build app/.cxx
  mkdir -p "$LIVE_CANON"; cp -a "$CAND/app" "$LIVE_CANON/app"
  universe_equal "$CAND" "$LIVE_CANON"
  pass "authority-seeded canonical live candidate byte-identical to frozen R5 candidate"
}
compile_languages(){
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/r5_26772_gradle_language_compilers.log"
  sed -i 's#REAL KOTLIN COMPILE:.*#REAL KOTLIN COMPILE: PASS#; s#REAL JAVA COMPILE:.*#REAL JAVA COMPILE: PASS (includes Android Data Binding imageFromBitmap contract)#' "$OUT/r5_26772_COMPILER_STATUS.txt"
  rm -rf "$POST_LANG"; mkdir -p "$POST_LANG"; cp -a app "$POST_LANG/app"; rm -rf "$POST_LANG/app/build" "$POST_LANG/app/.cxx"
  universe_equal "$CAND" "$POST_LANG"
  pass "real Kotlin/Java compilers passed and frozen source remained byte-identical"
}
compile_native(){
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/r5_26772_gradle_native_compiler.log"
  sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#' "$OUT/r5_26772_COMPILER_STATUS.txt"
}
verify_candidate_patches(){
  python3 -S r5_26772_make_patches.py "$BASE" "$CAND" "$OUT/patch_proof" | tee "$OUT/r5_26772_patch_validation.txt"
  sort -u 26772_RUNTIME_CHANGED_PATHS.txt > "$OUT/expected_runtime_changed_paths.sorted"
  sort -u "$OUT/patch_proof/r5_26772_PATCH_CHANGED_PATHS.txt" > "$OUT/actual_patch_changed_paths.sorted"
  [[ "$(wc -l < "$OUT/expected_runtime_changed_paths.sorted")" -eq 68 ]] || fail "expected runtime allowlist is not 68 paths"
  cmp -s "$OUT/expected_runtime_changed_paths.sorted" "$OUT/actual_patch_changed_paths.sorted" || { diff -u "$OUT/expected_runtime_changed_paths.sorted" "$OUT/actual_patch_changed_paths.sorted" || true; fail "patch changed-file allowlist differs from exact 26772 runtime allowlist"; }
  cp "$OUT/patch_proof/r5_26772_FORWARD_FULL_INDEX_abbrev40.patch" "$OUT/r5_26772_FORWARD_FULL_INDEX.patch"
  cp "$OUT/patch_proof/r5_26772_ROLLBACK_FULL_INDEX_abbrev40.patch" "$OUT/r5_26772_ROLLBACK_FULL_INDEX.patch"
  pass "deterministic full-index forward/rollback patch proof: exact 68-path successful-26771 -> repaired-26772 transition"
}
prebuild_safety(){
  universe_equal "$CAND" "$POST_LANG"
  python3 -S r3_26772_validate.py "$BASE" "$FAILED" "$CAND"
  grep -F 'REAL GLSL COMPILE: PASS' "$OUT/r5_26772_COMPILER_STATUS.txt" >/dev/null
  grep -F 'REAL KOTLIN COMPILE: PASS' "$OUT/r5_26772_COMPILER_STATUS.txt" >/dev/null
  grep -F 'REAL JAVA COMPILE: PASS' "$OUT/r5_26772_COMPILER_STATUS.txt" >/dev/null
  grep -F 'NATIVE/NDK COMPILE: PASS' "$OUT/r5_26772_COMPILER_STATUS.txt" >/dev/null
  grep -F 'PASS deterministic binary full-index forward/rollback patch proof: 68 changed paths; core.abbrev 7/12/40; exact forward replay; exact rollback; non-empty transition' "$OUT/r5_26772_patch_validation.txt" >/dev/null || fail "68-path patch proof missing"
  echo 'PRE-BUILD SAFETY PROOF PASSED' | tee "$OUT/r5_26772_PREBUILD_SAFETY.txt"
}
assemble(){
  ./gradlew :app:assembleDebug --stacktrace | tee "$OUT/r5_26772_gradle_assemble.log"
  mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk')
  [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#apks[@]}"
  cp "${apks[0]}" "$FINAL"
  [[ -f "$FINAL" ]] || fail "final APK missing"
  sha256sum "$FINAL" > "$OUT/r5_26772_APK.sha256"
  sed -i 's#FULL ANDROID ASSEMBLE:.*#FULL ANDROID ASSEMBLE: PASS (exactly one APK)#' "$OUT/r5_26772_COMPILER_STATUS.txt"
}
postbuild_proof(){
  # Generated app/build and app/.cxx are excluded; actual runtime source must remain byte-identical.
  rm -rf "$WORK/postbuild"; mkdir -p "$WORK/postbuild"; cp -a app "$WORK/postbuild/app"; rm -rf "$WORK/postbuild/app/build" "$WORK/postbuild/app/.cxx"
  universe_equal "$CAND" "$WORK/postbuild"
  for manifest in 26772_PROTECTED_AUTHORITY.sha256 26772_NATIVE_AUTHORITY.sha256 26772_VENDOR_AUTHORITY.sha256 26772_DNG_AUTHORITY.sha256 26772_EXPECTED_ASSET_SHADER_UNIVERSE.sha256 26772_PROTECTED_ASSET_SHADERS.sha256; do
    (cd "$WORK/postbuild" && sha256sum -c "$ROOT/$manifest" >/dev/null) || fail "postbuild $manifest"
  done
  tar -czf "$OUT/r5_26772_candidate_app_source.tar.gz" -C "$CAND" app
  sha256sum "$OUT/r5_26772_candidate_app_source.tar.gz" > "$OUT/r5_26772_candidate_app_source.tar.gz.sha256"
  (cd "$CAND" && find app -type f -print0 | sort -z | xargs -0 sha256sum) > "$OUT/r5_26772_candidate_full_app.sha256"
  sed -i 's#POST-BUILD INVARIANCE:.*#POST-BUILD INVARIANCE: PASS#' "$OUT/r5_26772_COMPILER_STATUS.txt"
  pass "authority-seeded post-build protected/DNG/native/vendor/source invariance"
}
clean_extract_replay(){
  python3 -S r3_26772_validate.py "$BASE" "$FAILED" "$CAND"
  sha256sum -c r5_26772_HANDOFF_HASHES.sha256 >/dev/null
  sha256sum -c r3_26772_HANDOFF_HASHES.sha256 >/dev/null
  rm -rf "$OUT/final_patch_replay"
  python3 -S r5_26772_make_patches.py "$BASE" "$CAND" "$OUT/final_patch_replay" | tee "$OUT/r5_26772_final_patch_replay.txt"
  for n in 7 12 40; do
    cmp -s "$OUT/patch_proof/r5_26772_FORWARD_FULL_INDEX_abbrev${n}.patch" "$OUT/final_patch_replay/r5_26772_FORWARD_FULL_INDEX_abbrev${n}.patch" || fail "final forward patch replay differs at abbrev=$n"
    cmp -s "$OUT/patch_proof/r5_26772_ROLLBACK_FULL_INDEX_abbrev${n}.patch" "$OUT/final_patch_replay/r5_26772_ROLLBACK_FULL_INDEX_abbrev${n}.patch" || fail "final rollback patch replay differs at abbrev=$n"
  done
  cmp -s "$OUT/expected_runtime_changed_paths.sorted" "$OUT/final_patch_replay/r5_26772_PATCH_CHANGED_PATHS.txt" || fail "final patch replay allowlist differs"
  grep -F 'PRE-BUILD SAFETY PROOF PASSED' "$OUT/r5_26772_PREBUILD_SAFETY.txt" >/dev/null
  for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$OUT/r5_26772_COMPILER_STATUS.txt" >/dev/null || fail "final proof missing: $proof"; done
  pass "final R5 clean replay of package hashes/ownership/version/patches/compiler/build proofs"
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
printf '\n=========================================\n26772 R5 STRICT MECHANICS REPAIR: PASS\nRuntime authority: 26771 R2 %s\nVerification mechanics authority: 26752 %s\nRuntime candidate delta vs intended 26772: 1 repaired file (CustomBinding.java); R5 adds 0 runtime files vs R3\nInfrastructure delta: nonzero R5 wrapper/workflow only; compiler/native mechanics restored from successful 26771/26752\nReal GLSL/Kotlin/Java/NDK/full assemble: PASS\nExactly one APK: PASS\n=========================================\n' "$RUNTIME_AUTHORITY_COMMIT" "$MECHANICS_AUTHORITY_COMMIT"
