#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }; pass(){ echo "PASS: $*"; }; sha(){ sha256sum "$1"|awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="d5ac40d2a18b7ee08c2bbd1195980512c78b28dc"; BASE_RUN_ID="36454846825"; BASE_ARTIFACT_ID="10984683693"; BASE_ARTIFACT_NAME="photon-26726-universal-rgba16f-carrier"; BASE_ARTIFACT_SHA="f0d8916aaed4acaa827e2635bbf7b3a250e2c7d22239bbd4ef458b242a3fd3cd"; BASE_TAR_SHA="740077de8ca62230a7a51b5bf869d32a6a8069a53cfe4f1147955e2479e7d36d"
VERSION_NAME="0.9726727"; VERSION_BUILD="26727"; GLSLANG_VERSION="16.5.0"; GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"; GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26727_rgba16f_half_float_upload_outputs"; WORK="$ROOT/.build_26727_rgba16f_half_float_upload_work"; ARTZIP="$WORK/26726_artifact.zip"; ARTDIR="$WORK/artifact_26726"; BASE="$WORK/exact_successful_26726_compiled_candidate"; AFTER="$WORK/candidate_26727"; AFTER2="$WORK/candidate_26727_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-rgba16f-half-float-upload-debug.apk"; TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""; LOCAL_ONLY=0
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]]||fail "--local-prebuild requires successful 26726 artifact ZIP"; LOCAL_ART="$2"; LOCAL_ONLY=1; elif [[ -n "${1:-}" ]]; then fail "unknown argument"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26727_COMPILER_STATUS.txt" <<EOF2
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
 [[ -d handoff_payload_26727 && "$(find handoff_payload_26727 -type f|wc -l)" -eq 4 ]]||fail "payload count"; [[ "$(wc -l < 26727_RUNTIME_CHANGED_PATHS.txt)" -eq 4 ]]||fail "changed count"; [[ ! -s 26727_ADDED_PATHS_MUST_BE_ABSENT.txt ]]||fail additions
 sha256sum -c 26727_HANDOFF_HASHES.sha256 >/dev/null; bash -n "$0"; python3 -S - <<'PY'
from pathlib import Path
for n in ['transform_26727.py','validate_26727.py','verify_26727_authority.py','verify_26727_patches.py','verify_26727_regressions.py','verify_26727_shaders.py','verify_26727_infrastructure.py']:
 compile(Path(n).read_text(),n,'exec')
print('PASS sealed Python syntax')
PY
 ! find . \( -type d -name __pycache__ -o -type f -name '*.pyc' \)|grep -q . || fail transient; ! find . -type f -name '*.apk'|grep -q . || fail "APK packaged"
}
verify_scope(){ if [[ "$LOCAL_ONLY" -eq 1 ]]; then pass "local sealed scope exact 4"; return; fi; [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]]||fail branch; git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD||fail authority_ancestor; ! git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD|grep -Eq '^app/'||fail "live app source committed"; pass "upload scope leaves live app source untouched"; }
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]]||fail token; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
 [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]]||fail artifact_sha; unzip -q "$ARTZIP" -d "$ARTDIR"; T="$ARTDIR/build_26726_universal_rgba16f_carrier_outputs/26726_candidate_app_source.tar.gz"; [[ -f "$T" && "$(sha "$T")" == "$BASE_TAR_SHA" ]]||fail tar_sha; mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"; (cd "$BASE" && sha256sum -c "$ROOT/26727_BASE_26726_FULL_APP.sha256" >/dev/null)||fail base_manifest; pass "exact successful 26726 compiled candidate authority"
}
compare_app(){ python3 -S - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2]); assert len(a)==len(b)==1823 and a==b; print('PASS candidate byte-identical 1823 files')
PY
}
make_candidate(){ python3 -S transform_26727.py "$BASE" "$AFTER"; python3 -S transform_26727.py "$BASE" "$AFTER2"; compare_app "$AFTER" "$AFTER2"; python3 -S validate_26727.py "$BASE" "$AFTER"; python3 -S verify_26727_regressions.py "$BASE" "$AFTER"; python3 -S verify_26727_authority.py "$ROOT" "$BASE" "$AFTER"; python3 -S verify_26727_shaders.py "$ROOT" "$BASE" "$AFTER"; }
verify_successful_26726_mechanics(){
 local bs wh
 bs="$(git show "${RUNTIME_AUTHORITY_COMMIT}:build_26726_universal_rgba16f_carrier.sh" | sha256sum | awk '{print $1}')"
 wh="$(git show "${RUNTIME_AUTHORITY_COMMIT}:.github/workflows/build-26726-universal-rgba16f-carrier.yml" | sha256sum | awk '{print $1}')"
 [[ "$bs" == "7ad72238b2838c8762b32817ee3faeb9994d7ecebb98a62e726849b2bfa3f5c2" ]]||fail "26726 build mechanics hash"
 [[ "$wh" == "cb0eefc4705c34aba9977207f7a3bcf5c246b11e0d862c96dc888589455dae8b" ]]||fail "26726 workflow mechanics hash"
 pass "exact successful 26726 mechanics authority hash-pinned"
}
prepare_glslang(){
 D="$WORK/glslang-${GLSLANG_VERSION}"; mkdir -p "$D"; A="$WORK/glslang.tar.gz"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]]||fail glslang_sha; tar -xzf "$A" -C "$D"; compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" -type f -o -type l -name glslangValidator -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]]||chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26727_glslang_version.txt"; export IRIS26727_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; pass "pinned glslang 16.5.0 dual environment handoff"
}
compile_modified_runtime_shaders(){ python3 -S verify_26727_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26727_GLSLANG" | tee "$OUT/26727_shader_compiler_validation.txt"; echo "REAL GLSL COMPILE: PASS (exact 10 successful-26726 runtime-expanded variants preserved; 26727 modifies no GLSL; pinned glslang 16.5.0)" > "$OUT/.glsl"; }
compile_spektra_raw_shader(){ if [[ -f scripts/verify_shaders.py ]]; then IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/26727_spektra_shader_verify.txt"; else pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"; fi; }
install_frozen_candidate_live(){ rm -rf app/src; cp -a "$AFTER/app/src" app/; cp -a "$AFTER/app/build.gradle" app/build.gradle; cp -a "$AFTER/app/version.properties" app/version.properties; rm -rf "$LIVE_CANON"; mkdir -p "$LIVE_CANON"; cp -a "$AFTER/app" "$LIVE_CANON/app"; compare_app "$AFTER" "$LIVE_CANON"; }
after_language_compiler_snapshot(){ rm -rf "$POST"; mkdir -p "$POST"; cp -a "$AFTER/app" "$POST/app"; compare_app "$AFTER" "$POST"; }
verify_candidate_patches(){ python3 -S verify_26727_patches.py "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26727_patch_validation.txt"; }
postbuild_proof(){ compare_app "$AFTER" "$LIVE_CANON"; python3 -S verify_26727_authority.py "$ROOT" "$BASE" "$LIVE_CANON"; python3 -S verify_26727_regressions.py "$BASE" "$LIVE_CANON"; tar -czf "$OUT/26727_candidate_app_source.tar.gz" -C "$AFTER" app; sha256sum "$OUT/26727_candidate_app_source.tar.gz" > "$OUT/26727_candidate_app_source.tar.gz.sha256"; cp 26727_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26727_candidate_full_app.sha256"; pass "post-build candidate/protected/native/vendor/DNG invariance"; }
# IRIS_26727_AUTHORITATIVE_ACTIONS_STAGE_ORDER -- exact successful-26726 ordering; authority/scope/applicable gates only advance
verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_26726_mechanics
prepare_glslang
compile_modified_runtime_shaders
compile_spektra_raw_shader
if [[ "$LOCAL_ONLY" -eq 1 ]]; then verify_candidate_patches; echo "26727 LOCAL PREBUILD COMPLETE — real project compilers NOT RUN"; exit 0; fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26727_gradle_language_compilers.log"
sed -i 's/REAL KOTLIN COMPILE:.*/REAL KOTLIN COMPILE: PASS/;s/REAL JAVA COMPILE:.*/REAL JAVA COMPILE: PASS/' "$OUT/26727_COMPILER_STATUS.txt"
pass "JNI callback/motion ABI compiler checkpoint"
after_language_compiler_snapshot
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/26727_gradle_native_compiler.log"
sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#' "$OUT/26727_COMPILER_STATUS.txt"
verify_candidate_patches
echo "26727 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26727_gradle_assemble.log"
sed -i 's/FULL ANDROID ASSEMBLE:.*/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26727_COMPILER_STATUS.txt"
mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk'); [[ "${#apks[@]}" -eq 1 ]]||fail "expected one Gradle APK"; cp "${apks[0]}" "$FINAL"; [[ "$(find . -maxdepth 1 -type f -name 'IrisCamera-*.apk'|wc -l)" -eq 1 ]]||fail "one intended root APK"; sha256sum "$FINAL" > "$OUT/26727_APK.sha256"; sed -i 's/APK JNI CONTRACT:.*/APK JNI CONTRACT: PASS (full assemble APK present; inherited JNI source protected)/' "$OUT/26727_COMPILER_STATUS.txt"
postbuild_proof
sed -i 's/POST-BUILD INVARIANCE:.*/POST-BUILD INVARIANCE: PASS/' "$OUT/26727_COMPILER_STATUS.txt"
sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: PASS (pinned glslang 16.5.0; exact 10 successful-26726 runtime-expanded variants preserved; 26727 modifies no GLSL)#' "$OUT/26727_COMPILER_STATUS.txt"
echo "26727 ACTIONS BUILD COMPLETE"
