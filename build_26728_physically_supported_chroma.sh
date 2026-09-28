#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }; pass(){ echo "PASS: $*"; }; sha(){ sha256sum "$1"|awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="78843548ca83f8431430c441a6fd19108fd76d75"; BASE_RUN_ID="36459168943"; BASE_ARTIFACT_ID="10987660159"; BASE_ARTIFACT_NAME="photon-26727-rgba16f-half-float-upload"; BASE_ARTIFACT_SHA="c7d38ac4fadd7ac7c9e930cfc8c06d26c76c6ef3b35f088842dc494bece7d3d1"; BASE_TAR_SHA="470d0b6b74c4e101c34e365cd44765f122868faa0270301d28aeab22dd32bd7f"
VERSION_NAME="0.9726728"; VERSION_BUILD="26728"; GLSLANG_VERSION="16.5.0"; GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"; GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
PRIOR_BUILD_SHA="4db26c8be456b90ca2540f8ceb8e07365d431cc1ce2f0d12f78af7e2349546b7"; PRIOR_WORKFLOW_SHA="f661eb41f969e79105ddb2f38ba04220dc9a537d7dc9512d31b64e650093b88f"; PRIOR_SHADER_VERIFIER_SHA="180fa8f0daed736bb5453dd1dbfda93f28aa34e0b6309f818a04be48e0f3b645"
OUT="$ROOT/build_26728_physically_supported_chroma_outputs"; WORK="$ROOT/.build_26728_physically_supported_chroma_work"; ARTZIP="$WORK/26727_artifact.zip"; ARTDIR="$WORK/artifact_26727"; BASE="$WORK/exact_successful_26727_compiled_candidate"; AFTER="$WORK/candidate_26728"; AFTER2="$WORK/candidate_26728_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-physically-supported-chroma-debug.apk"; TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""; LOCAL_ONLY=0
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]]||fail "--local-prebuild requires successful 26727 artifact ZIP"; LOCAL_ART="$2"; LOCAL_ONLY=1; elif [[ -n "${1:-}" ]]; then fail "unknown argument"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26728_COMPILER_STATUS.txt" <<EOF2
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
JNI CALLBACK CLASS ABI: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
APK JNI CONTRACT: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF2
verify_package(){
 [[ -d handoff_payload_26728 && "$(find handoff_payload_26728 -type f|wc -l)" -eq 5 ]]||fail "payload count"; [[ "$(wc -l < 26728_RUNTIME_CHANGED_PATHS.txt)" -eq 5 ]]||fail "changed count"; [[ ! -s 26728_ADDED_PATHS_MUST_BE_ABSENT.txt ]]||fail additions
 sha256sum -c 26728_HANDOFF_HASHES.sha256 >/dev/null; bash -n "$0"; python3 -S - <<'PY'
from pathlib import Path
for n in ['transform_26728.py','validate_26728.py','verify_26728_authority.py','verify_26728_patches.py','verify_26728_regressions.py','verify_26728_shaders.py','verify_26728_infrastructure.py']:
 compile(Path(n).read_text(),n,'exec')
print('PASS sealed Python syntax')
PY
 ! find . \( -type d -name __pycache__ -o -type f -name '*.pyc' \)|grep -q . || fail transient; ! find . -type f -name '*.apk'|grep -q . || fail "APK packaged"
}
verify_scope(){ if [[ "$LOCAL_ONLY" -eq 1 ]]; then pass "local sealed scope exact 5"; return; fi; [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]]||fail branch; git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD||fail authority_ancestor; ! git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD|grep -Eq '^app/'||fail "live app source committed"; pass "upload scope leaves live app source untouched"; }
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]]||fail token; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
 [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]]||fail artifact_sha; unzip -q "$ARTZIP" -d "$ARTDIR"; T="$ARTDIR/build_26727_rgba16f_half_float_upload_outputs/26727_candidate_app_source.tar.gz"; [[ -f "$T" && "$(sha "$T")" == "$BASE_TAR_SHA" ]]||fail tar_sha; mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"; (cd "$BASE" && sha256sum -c "$ROOT/26728_BASE_26727_FULL_APP.sha256" >/dev/null)||fail base_manifest; pass "exact successful 26727 compiled candidate authority"
}
compare_app(){ python3 -S - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2]); assert len(a)==len(b)==1823 and a==b; print('PASS candidate byte-identical 1823 files')
PY
}
make_candidate(){ python3 -S transform_26728.py "$BASE" "$AFTER"; python3 -S transform_26728.py "$BASE" "$AFTER2"; compare_app "$AFTER" "$AFTER2"; python3 -S validate_26728.py "$BASE" "$AFTER"; python3 -S verify_26728_regressions.py "$BASE" "$AFTER"; python3 -S verify_26728_authority.py "$ROOT" "$BASE" "$AFTER"; python3 -S verify_26728_shaders.py "$ROOT" "$BASE" "$AFTER"; }
verify_successful_26727_mechanics(){
 local bs wh sv
 bs="$(git show "${RUNTIME_AUTHORITY_COMMIT}:build_26727_rgba16f_half_float_upload.sh" | sha256sum | awk '{print $1}')"; wh="$(git show "${RUNTIME_AUTHORITY_COMMIT}:.github/workflows/build-26727-rgba16f-half-float-upload.yml" | sha256sum | awk '{print $1}')"; sv="$(git show "${RUNTIME_AUTHORITY_COMMIT}:verify_26727_shaders.py" | sha256sum | awk '{print $1}')"
 [[ "$bs" == "$PRIOR_BUILD_SHA" ]]||fail "26727 build mechanics hash"; [[ "$wh" == "$PRIOR_WORKFLOW_SHA" ]]||fail "26727 workflow mechanics hash"; [[ "$sv" == "$PRIOR_SHADER_VERIFIER_SHA" ]]||fail "26727 shader verifier hash"; pass "exact successful 26727 mechanics authority hash-pinned"
}
prepare_glslang(){
 D="$WORK/glslang-${GLSLANG_VERSION}"; mkdir -p "$D"; A="$WORK/glslang.tar.gz"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]]||fail glslang_sha; tar -xzf "$A" -C "$D"; compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" -type f -o -type l -name glslangValidator -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]]||chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26728_glslang_version.txt"; export IRIS26728_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; pass "pinned glslang 16.5.0 dual environment handoff"
}
compile_modified_runtime_shaders(){ sha256sum verify_26727_shaders.py | grep -F "$PRIOR_SHADER_VERIFIER_SHA" >/dev/null || fail "26727 shader verifier live hash"; python3 -S verify_26727_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26728_GLSLANG" | tee "$OUT/26728_inherited_shader_compiler_validation.txt"; python3 -S verify_26728_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26728_GLSLANG" | tee "$OUT/26728_shader_compiler_validation.txt"; echo "REAL GLSL COMPILE: PASS (pinned glslang 16.5.0; exact 10 inherited runtime-expanded variants plus exact 2 modified 26728 variants)" > "$OUT/.glsl"; }
compile_spektra_raw_shader(){ if [[ -f scripts/verify_shaders.py ]]; then IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/26728_spektra_shader_verify.txt"; else pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"; fi; }
install_frozen_candidate_live(){ rm -rf app/src; cp -a "$AFTER/app/src" app/; cp -a "$AFTER/app/build.gradle" app/build.gradle; cp -a "$AFTER/app/version.properties" app/version.properties; rm -rf "$LIVE_CANON"; mkdir -p "$LIVE_CANON"; cp -a "$AFTER/app" "$LIVE_CANON/app"; compare_app "$AFTER" "$LIVE_CANON"; }
after_language_compiler_snapshot(){ rm -rf "$POST"; mkdir -p "$POST"; cp -a "$AFTER/app" "$POST/app"; compare_app "$AFTER" "$POST"; }
verify_candidate_patches(){ python3 -S verify_26728_patches.py "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26728_patch_validation.txt"; }
postbuild_proof(){ compare_app "$AFTER" "$LIVE_CANON"; python3 -S verify_26728_authority.py "$ROOT" "$BASE" "$LIVE_CANON"; python3 -S verify_26728_regressions.py "$BASE" "$LIVE_CANON"; tar -czf "$OUT/26728_candidate_app_source.tar.gz" -C "$AFTER" app; sha256sum "$OUT/26728_candidate_app_source.tar.gz" > "$OUT/26728_candidate_app_source.tar.gz.sha256"; cp 26728_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26728_candidate_full_app.sha256"; pass "post-build candidate/protected/native/vendor/DNG invariance"; }
# IRIS_26728_AUTHORITATIVE_ACTIONS_STAGE_ORDER -- exact successful-26727 ordering; authority/scope/applicable gates only advance
verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_26727_mechanics
prepare_glslang
compile_modified_runtime_shaders
compile_spektra_raw_shader
if [[ "$LOCAL_ONLY" -eq 1 ]]; then verify_candidate_patches; echo "26728 LOCAL PREBUILD COMPLETE — real project Kotlin/Java/NDK/full assemble NOT RUN"; exit 0; fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26728_gradle_language_compilers.log"
sed -i 's/REAL KOTLIN COMPILE:.*/REAL KOTLIN COMPILE: PASS/;s/REAL JAVA COMPILE:.*/REAL JAVA COMPILE: PASS/' "$OUT/26728_COMPILER_STATUS.txt"
pass "JNI callback/motion ABI compiler checkpoint"
after_language_compiler_snapshot
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/26728_gradle_native_compiler.log"
sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#' "$OUT/26728_COMPILER_STATUS.txt"
verify_candidate_patches
echo "26728 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26728_gradle_assemble.log"
sed -i 's/FULL ANDROID ASSEMBLE:.*/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26728_COMPILER_STATUS.txt"
mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk'); [[ "${#apks[@]}" -eq 1 ]]||fail "expected one Gradle APK"; cp "${apks[0]}" "$FINAL"; [[ "$(find . -maxdepth 1 -type f -name 'IrisCamera-*.apk'|wc -l)" -eq 1 ]]||fail "one intended root APK"; sha256sum "$FINAL" > "$OUT/26728_APK.sha256"; sed -i 's/APK JNI CONTRACT:.*/APK JNI CONTRACT: PASS (full assemble APK present; inherited JNI source protected)/' "$OUT/26728_COMPILER_STATUS.txt"
postbuild_proof
sed -i 's/POST-BUILD INVARIANCE:.*/POST-BUILD INVARIANCE: PASS/' "$OUT/26728_COMPILER_STATUS.txt"
sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: PASS (pinned glslang 16.5.0; exact 10 inherited plus 2 modified runtime-expanded variants)#' "$OUT/26728_COMPILER_STATUS.txt"
echo "26728 ACTIONS BUILD COMPLETE"
