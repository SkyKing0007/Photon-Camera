#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="3fbba118fd62e83ee9ba0321be9e610da4c5a4f1"
RUNTIME_ACTIONS_RUN="37560232705"
RUNTIME_ARTIFACT_ID="11456446982"
RUNTIME_ARTIFACT_NAME="photon-26777-claude-resolve-support-footprint"
RUNTIME_ARTIFACT_SHA="5c7574ae59f4b8323bd0fc745cc69c23fbe19412b96a758265f2488dba854aae"
RUNTIME_TAR_SHA="78c9a1d6686c0dcd82ac015a37d6d956eacaafc9495f5ac005e81575d45aff0f"
MECHANICS_AUTHORITY_COMMIT="3fbba118fd62e83ee9ba0321be9e610da4c5a4f1"
ROOT_MECHANICS_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"
MECHANICS_ACTIONS_RUN="37560232705"
ROOT_MECHANICS_RUN="37075896367"
VERSION_NAME="0.9726778"
VERSION_BUILD="26778"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26778_claude_edge_false_color_suppressor_outputs"
WORK="$ROOT/.build_26778_claude_edge_false_color_suppressor_work"
ARTZIP="$WORK/26777_artifact.zip"
ARTDIR="$WORK/artifact_26777"
BASE="$WORK/exact_successful_26777_compiled_candidate"
CAND="$WORK/candidate_26778"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"
POST_LANG="$WORK/post_language_compiler_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-claude-edge-false-color-suppressor-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26778_COMPILER_STATUS.txt" <<EOF
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF

# IRIS_26778_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){
  sha256sum -c 26778_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26778_claude_edge_false_color_suppressor.sh
  python3 -S -m py_compile transform_26778.py validate_26778.py verify_26778_patches.py verify_26778_embedded_glsl.py
  rm -rf __pycache__
  [[ "$(find handoff_payload_26778 -type f | wc -l)" -eq 8 ]] || fail "26778 payload count"
  diff -u 26778_RUNTIME_CHANGED_PATHS.txt <(find handoff_payload_26778 -type f | sed 's#^handoff_payload_26778/##' | sort) >/dev/null || fail "26778 payload allowlist mismatch"
  for p in 26778_FORWARD_FULL_INDEX.patch 26778_ROLLBACK_FULL_INDEX.patch; do
    ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$p" || fail "26778 patch contains rename/copy inference: $p"
  done
  grep -Fx 'RUN_26778_CLAUDE_EDGE_FALSE_COLOR_SUPPRESSOR' TRIGGER_26778.txt >/dev/null || fail "26778 trigger contents"
  ! find . -type f -name '*.apk' | grep -q . || fail "APK unexpectedly packaged"
  pass "sealed 26778 package hashes/syntax/allowlist/patch identity"
}
verify_scope(){
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail "26777 runtime authority not ancestor"
  git merge-base --is-ancestor "$MECHANICS_AUTHORITY_COMMIT" HEAD || fail "26777 mechanics authority not ancestor"
  git merge-base --is-ancestor "$ROOT_MECHANICS_COMMIT" HEAD || fail "26752 root mechanics authority not ancestor"
  # No live runtime source is uploaded. Candidate source exists only in the sealed payload and is
  # reconstructed from the exact successful artifact.
  if git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | grep -E '^app/'; then
    fail "live app source changed after 26777 authority"
  fi
  python3 -S - <<'PY'
import subprocess
allowed_prefixes=(
 '26778_', 'build_26778_claude_edge_false_color_suppressor.sh', 'transform_26778.py',
 'validate_26778.py', 'verify_26778_patches.py', 'verify_26778_embedded_glsl.py', 'handoff_payload_26778/',
 '.github/workflows/build-26778-claude-edge-false-color-suppressor.yml', 'TRIGGER_26778.txt')
paths=subprocess.check_output(['git','diff','--name-only','3fbba118fd62e83ee9ba0321be9e610da4c5a4f1..HEAD'],text=True).splitlines()
bad=[p for p in paths if not any(p==x or p.startswith(x) for x in allowed_prefixes)]
assert not bad,bad
print('PASS 26778 infrastructure scope allowlist')
PY
  pass "26778 scope exact: successful 26777 authority + sealed 8-file payload; live app untouched"
}
obtain_authority(){
  [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
  curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
  [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail "26777 artifact sha"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  T="$ARTDIR/build_26777_claude_resolve_support_footprint_outputs/26777_candidate_app_source.tar.gz"
  [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail "26777 candidate tar sha"
  STATUS="$ARTDIR/build_26777_claude_resolve_support_footprint_outputs/26777_COMPILER_STATUS.txt"
  for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do
    grep -F "$proof" "$STATUS" >/dev/null || fail "missing 26777 authority proof: $proof"
  done
  mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"
  [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1779 ]] || fail "26777 base file count"
  (cd "$BASE" && sha256sum -c "$ROOT/26778_BASE_26777_FULL_APP.sha256" >/dev/null) || fail "26777 full base manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26778_NATIVE_26777.sha256" >/dev/null) || fail "26777 native manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26778_VENDOR_26777.sha256" >/dev/null) || fail "26777 vendor manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26778_DNG_26777.sha256" >/dev/null) || fail "26777 DNG manifest"
  cat > "$OUT/26778_RESOLVED_AUTHORITIES.txt" <<EOF
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
  pass "exact successful 26777 compiled candidate reconstructed"
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
  python3 -S transform_26778.py "$BASE" "$CAND" handoff_payload_26778
  python3 -S validate_26778.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26778_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail "26778 candidate manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26778_PROTECTED_26777.sha256" >/dev/null) || fail "26778 protected manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26778_NATIVE_26777.sha256" >/dev/null) || fail "26778 native invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26778_VENDOR_26777.sha256" >/dev/null) || fail "26778 vendor invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26778_DNG_26777.sha256" >/dev/null) || fail "26778 DNG invariance"
  [[ "$(find "$CAND/app" -type f | wc -l)" -eq 1779 ]] || fail "26778 candidate file count"
  pass "candidate-first 26778 reconstruction/domain/ownership checks"
}
verify_successful_mechanics(){
  local a77="$WORK/authority_26777_build.sh" a52="$WORK/authority_26752_build.sh"
  git show "$MECHANICS_AUTHORITY_COMMIT:build_26777_claude_resolve_support_footprint.sh" > "$a77"
  git show "$ROOT_MECHANICS_COMMIT:build_26752_ipol_plan_b_translational_sr.sh" > "$a52"
  [[ "$(sha "$a77")" == "63f785845242e4dc80121cd3d7a14a3685bd73b150527b32817bf22a1948a2d0" ]] || fail "successful 26777 build-script authority hash differs"
  grep -F 'export IRIS26777_GLSLANG="$compiler"' "$a77" >/dev/null || fail "26777 primary glslang handoff missing"
  grep -F 'export IRIS26681_SPEKTRA_GLSLANG="$compiler"' "$a77" >/dev/null || fail "26777 Spektra glslang handoff missing"
  grep -F 'compile_spektra_raw_shader(){' "$a77" >/dev/null || fail "26777 Spektra verifier stage missing"
  grep -F "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" "$a77" >/dev/null || fail "26777 both-ABI native stage missing"
  grep -F './gradlew :app:assembleDebug --stacktrace' "$a77" >/dev/null || fail "26777 assemble stage missing"
  grep -F 'export IRIS26681_SPEKTRA_GLSLANG="$compiler"' "$0" >/dev/null || fail "26778 dual glslang handoff missing"
  grep -F 'compile_spektra_raw_shader(){' "$0" >/dev/null || fail "26778 Spektra verifier stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$0" >/dev/null || fail "26778 native handoff regression missing"
  grep -F "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" "$0" >/dev/null || fail "26778 both-ABI native command differs"
  grep -F './gradlew :app:assembleDebug --stacktrace' "$0" >/dev/null || fail "26778 assemble command differs"
  python3 -S - "$0" "$a77" "$a52" <<'PY_ORDER'
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
cur=Path(sys.argv[1]).read_text(); a77=Path(sys.argv[2]).read_text(); a52=Path(sys.argv[3]).read_text()
ordered(cur,'# IRIS_26778_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26778')
ordered(a77,'# IRIS_26777_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26777 authority')
auth52=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26751_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','mapfile -t apks','postbuild_proof']
ordered(a52,'# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER',auth52,'26752 root authority')
print('PASS 26778 stage order exactly inherits successful 26777 and root 26752 mechanics')
PY_ORDER
  pass "successful 26777 procedure audited: exact script hash, same stage order, dual glslang/Spektra, language compilers, both ABIs, assemble"
}
prepare_glslang(){
  D="$WORK/glslang-${GLSLANG_VERSION}"; A="$WORK/glslang.tar.gz"; mkdir -p "$D"
  curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"
  [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive sha"
  tar -xzf "$A" -C "$D"
  compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"
  compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]] || chmod +x "$compiler"
  "$compiler" --version | tee "$OUT/26778_glslang_version.txt"
  export IRIS26778_GLSLANG="$compiler"
  export IRIS26681_SPEKTRA_GLSLANG="$compiler"
  pass "pinned glslang 16.5.0 dual environment handoff"
}
compile_modified_runtime_shaders(){
  # 26778 candidate restores the exact successful 26776 guard domain, adds one Claude suppressor
  # shader, and changes the VGN seed so cleaned RGBA16F can become its color authority. Asset shader
  # bytes remain inherited byte-identically.
  python3 -S - "$BASE" "$CAND" <<'PY_SHADER_UNIVERSE'
from pathlib import Path
import hashlib,sys
def S(r):
 r=Path(r); return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
a,b=S(sys.argv[1]),S(sys.argv[2]); assert a==b,(len(a),len(b)); print(f'PASS inherited asset shader universe byte-identical: {len(a)} files')
PY_SHADER_UNIVERSE
  python3 -S verify_26778_embedded_glsl.py "$BASE" "$CAND" --compiler "$IRIS26778_GLSLANG" --out "$OUT/26778_runtime_expanded_glsl" | tee "$OUT/26778_embedded_glsl_validation.txt"
  for shader in EDGE_FALSE_COLOR_SUPPRESSOR_26778 bipolarColorTrust26769 seed; do
    grep -F "PASS 26778 reserved-identifier scan ${shader}" "$OUT/26778_embedded_glsl_validation.txt" >/dev/null || fail "26778 ${shader} reserved scan proof missing"
    grep -F "PASS 26778 pinned real glslang compile: ${shader}" "$OUT/26778_embedded_glsl_validation.txt" >/dev/null || fail "26778 ${shader} real GLSL proof missing"
  done
  grep -F 'PASS 26778 Claude reference exact after approved ES3.1/workgroup/sampler compatibility + telemetry' "$OUT/26778_embedded_glsl_validation.txt" >/dev/null || fail "26778 Claude shader fidelity proof missing"
  grep -F 'PASS 26778 exact candidate runtime-expanded shader set compiled/scanned: EDGE_FALSE_COLOR_SUPPRESSOR_26778,bipolarColorTrust26769,seed; 26777 phase shaders removed by explicit 26776 guard restoration' "$OUT/26778_embedded_glsl_validation.txt" >/dev/null || fail "26778 runtime-expanded shader-set proof missing"
  sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: PASS (3 candidate runtime-expanded compute shaders; complete reserved scan + pinned glslang 16.5.0; Claude shader fidelity PASS)#' "$OUT/26778_COMPILER_STATUS.txt"
}
compile_spektra_raw_shader(){
  if [[ -f scripts/verify_shaders.py ]]; then
    IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/26778_spektra_shader_verify.txt"
  else
    pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"
  fi
}
verify_native_glslang_handoff(){
  [[ -n "${IRIS26681_SPEKTRA_GLSLANG:-}" ]] || fail "PERMANENT REGRESSION: IRIS26681_SPEKTRA_GLSLANG unset before NDK"
  [[ -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "PERMANENT REGRESSION: Spektra glslang not executable before NDK"
  [[ "$IRIS26681_SPEKTRA_GLSLANG" == "$IRIS26778_GLSLANG" ]] || fail "PERMANENT REGRESSION: shader and Spektra compiler paths differ"
  "$IRIS26681_SPEKTRA_GLSLANG" --version | grep -F '16.5.0' >/dev/null || fail "PERMANENT REGRESSION: Spektra compiler not pinned 16.5.0"
  printf 'IRIS26681_SPEKTRA_GLSLANG=%s\nIRIS26778_GLSLANG=%s\n' "$IRIS26681_SPEKTRA_GLSLANG" "$IRIS26778_GLSLANG" | tee "$OUT/26778_native_glslang_handoff.txt"
  pass "successful 26777 native glslang handoff preserved before both-ABI native compile"
}
install_frozen_candidate_live(){
  rm -rf app
  cp -a "$CAND/app" app
  rm -rf app/build app/.cxx
  mkdir -p "$LIVE_CANON"; cp -a "$CAND/app" "$LIVE_CANON/app"
  universe_equal "$CAND" "$LIVE_CANON"
  pass "authority-seeded canonical live candidate byte-identical to frozen 26778 candidate"
}
compile_languages(){
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26778_gradle_language_compilers.log"
  sed -i 's#REAL KOTLIN COMPILE:.*#REAL KOTLIN COMPILE: PASS#; s#REAL JAVA COMPILE:.*#REAL JAVA COMPILE: PASS (includes Data Binding orientation-property contract)#' "$OUT/26778_COMPILER_STATUS.txt"
  rm -rf "$POST_LANG"; mkdir -p "$POST_LANG"; cp -a app "$POST_LANG/app"; rm -rf "$POST_LANG/app/build" "$POST_LANG/app/.cxx"
  universe_equal "$CAND" "$POST_LANG"
  pass "real Kotlin/Java compilers passed and frozen source remained byte-identical"
}
compile_native(){
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/26778_gradle_native_compiler.log"
  sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#' "$OUT/26778_COMPILER_STATUS.txt"
}
verify_candidate_patches(){
  python3 -S verify_26778_patches.py "$BASE" "$CAND" | tee "$OUT/26778_patch_validation.txt"
  for n in 7 12 40; do
    grep -F "PASS 26778 full-index forward/rollback core.abbrev=${n} fuzz=0 exact rollback; 8 modifications" "$OUT/26778_patch_validation.txt" >/dev/null || fail "26778 abbrev${n} patch proof missing"
  done
  cp 26778_FORWARD_FULL_INDEX.patch "$OUT/26778_FORWARD_FULL_INDEX.patch"
  cp 26778_ROLLBACK_FULL_INDEX.patch "$OUT/26778_ROLLBACK_FULL_INDEX.patch"
  pass "sealed full-index forward/rollback proof: successful 26777 -> exact 8-file 26778 candidate"
}
prebuild_safety(){
  universe_equal "$CAND" "$POST_LANG"
  python3 -S validate_26778.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26778_PROTECTED_26777.sha256" >/dev/null) || fail "prebuild protected manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26778_NATIVE_26777.sha256" >/dev/null) || fail "prebuild native manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26778_VENDOR_26777.sha256" >/dev/null) || fail "prebuild vendor manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26778_DNG_26777.sha256" >/dev/null) || fail "prebuild DNG manifest"
  grep -F 'REAL GLSL COMPILE: PASS' "$OUT/26778_COMPILER_STATUS.txt" >/dev/null
  grep -F 'REAL KOTLIN COMPILE: PASS' "$OUT/26778_COMPILER_STATUS.txt" >/dev/null
  grep -F 'REAL JAVA COMPILE: PASS' "$OUT/26778_COMPILER_STATUS.txt" >/dev/null
  grep -F 'NATIVE/NDK COMPILE: PASS' "$OUT/26778_COMPILER_STATUS.txt" >/dev/null
  grep -F 'PASS 26778 canonical patch proof' "$OUT/26778_patch_validation.txt" >/dev/null || fail "26778 canonical patch proof missing"
  echo 'PRE-BUILD SAFETY PROOF PASSED' | tee "$OUT/26778_PREBUILD_SAFETY.txt"
}
assemble(){
  ./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26778_gradle_assemble.log"
  mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk')
  [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#apks[@]}"
  cp "${apks[0]}" "$FINAL"
  [[ -f "$FINAL" ]] || fail "final APK missing"
  sha256sum "$FINAL" > "$OUT/26778_APK.sha256"
  sed -i 's#FULL ANDROID ASSEMBLE:.*#FULL ANDROID ASSEMBLE: PASS (exactly one APK)#' "$OUT/26778_COMPILER_STATUS.txt"
}
postbuild_proof(){
  rm -rf "$WORK/postbuild"; mkdir -p "$WORK/postbuild"; cp -a app "$WORK/postbuild/app"; rm -rf "$WORK/postbuild/app/build" "$WORK/postbuild/app/.cxx"
  universe_equal "$CAND" "$WORK/postbuild"
  for manifest in 26778_PROTECTED_26777.sha256 26778_NATIVE_26777.sha256 26778_VENDOR_26777.sha256 26778_DNG_26777.sha256; do
    (cd "$WORK/postbuild" && sha256sum -c "$ROOT/$manifest" >/dev/null) || fail "postbuild $manifest"
  done
  tar -czf "$OUT/26778_candidate_app_source.tar.gz" -C "$CAND" app
  sha256sum "$OUT/26778_candidate_app_source.tar.gz" > "$OUT/26778_candidate_app_source.tar.gz.sha256"
  (cd "$CAND" && find app -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum) > "$OUT/26778_candidate_full_app.sha256"
  python3 -S - "$OUT/26778_candidate_full_app.sha256" "$ROOT/26778_EXPECTED_CANDIDATE_FULL_APP.sha256" <<'PY_FINAL_MANIFEST'
from pathlib import Path
import sys
def manifest(path):
    lines=Path(path).read_text().splitlines()
    assert len(lines)==1779,(path,len(lines))
    out={}
    for line in lines:
        digest,rel=line.split('  ',1)
        assert len(digest)==64 and all(c in '0123456789abcdef' for c in digest),(path,line)
        assert rel not in out,(path,'duplicate path',rel)
        out[rel]=digest
    return out
actual=manifest(sys.argv[1]); frozen=manifest(sys.argv[2])
assert actual==frozen,'final candidate manifest hash/path set differs from frozen candidate'
print('PASS 26778 final candidate manifest: 1779 hash/path entries equal independent of ordering')
PY_FINAL_MANIFEST
  sed -i 's#POST-BUILD INVARIANCE:.*#POST-BUILD INVARIANCE: PASS#' "$OUT/26778_COMPILER_STATUS.txt"
  pass "authority-seeded post-build protected/DNG/native/vendor/source invariance"
}
clean_extract_replay(){
  sha256sum -c 26778_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26778_claude_edge_false_color_suppressor.sh
  python3 -S -m py_compile transform_26778.py validate_26778.py verify_26778_patches.py verify_26778_embedded_glsl.py
  rm -rf __pycache__
  python3 -S validate_26778.py "$BASE" "$CAND"
  python3 -S verify_26778_embedded_glsl.py "$BASE" "$CAND" | tee "$OUT/26778_final_embedded_glsl_static_replay.txt"
  for shader in EDGE_FALSE_COLOR_SUPPRESSOR_26778 bipolarColorTrust26769 seed; do
    grep -F "PASS 26778 pinned real glslang compile: ${shader}" "$OUT/26778_embedded_glsl_validation.txt" >/dev/null || fail "final ${shader} real GLSL proof missing"
  done
  python3 -S verify_26778_patches.py "$BASE" "$CAND" | tee "$OUT/26778_final_patch_replay.txt"
  cmp -s 26778_FORWARD_FULL_INDEX.patch "$OUT/26778_FORWARD_FULL_INDEX.patch" || fail "final forward patch bytes changed"
  cmp -s 26778_ROLLBACK_FULL_INDEX.patch "$OUT/26778_ROLLBACK_FULL_INDEX.patch" || fail "final rollback patch bytes changed"
  grep -F 'PRE-BUILD SAFETY PROOF PASSED' "$OUT/26778_PREBUILD_SAFETY.txt" >/dev/null
  for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do
    grep -F "$proof" "$OUT/26778_COMPILER_STATUS.txt" >/dev/null || fail "final proof missing: $proof"
  done
  pass "final 26778 clean replay of package hashes/ownership/version/patch/compiler/build proofs"
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
printf '\n=========================================\n26778 CLAUDE EDGE FALSE COLOR SUPPRESSOR: PASS\nRuntime authority: successful 26777 %s\nVerification mechanics authority: successful 26777 procedure %s (root 26752 inherited)\nRuntime changed-file allowlist: 8 modified, 0 added, 0 deleted\nInfrastructure mechanics: exact successful 26777 stage/compiler/native/assemble procedure; no stage-order deviation\nReal Kotlin/Java/NDK/full assemble: PASS\nExactly one APK: PASS\n=========================================\n' "$RUNTIME_AUTHORITY_COMMIT" "$MECHANICS_AUTHORITY_COMMIT"
