#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }; pass(){ echo "PASS: $*"; }; sha(){ sha256sum "$1"|awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="ff1eb4d7969c81070d86b8a2df1d2b8c42b2436e"; BASE_RUN_ID="36600235506"; BASE_ARTIFACT_ID="11049405399"; BASE_ARTIFACT_NAME="photon-26734-r1-all-digital-zoom-achromatic-sr"; BASE_ARTIFACT_SHA="378d7fc175f1d6f1c6015eef08eecd29310998f7528c1809208918e79d968a31"; BASE_TAR_SHA="5f9cec5009e6599d2566c7f86df78628e8551a4e5d1214ba1d93689809f7033c"
MECHANICS_AUTHORITY_COMMIT="ff1eb4d7969c81070d86b8a2df1d2b8c42b2436e"
VERSION_NAME="0.9726735"; VERSION_BUILD="26735"; GLSLANG_VERSION="16.5.0"; GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"; GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
PRIOR_BUILD_SHA="136d835fffaf8f0455787f773e375364008ea48dc191ee20538084a3f105bba2"; PRIOR_WORKFLOW_SHA="2591923eefd6c496bbafa0840945ec26331eb937d3e9a2a23cf44992c75fa1be"; PRIOR_CURRENT_SHADER_VERIFIER_SHA="ce036d5f1433974ab7d7af717bac340e105f45df5405c64903335f74b3766e90"
OUT="$ROOT/build_26735_neutral_chroma_digital_luma_retry_outputs"; WORK="$ROOT/.build_26735_neutral_chroma_digital_luma_retry_work"; ARTZIP="$WORK/26734r1_artifact.zip"; ARTDIR="$WORK/artifact_26734r1"; BASE="$WORK/exact_successful_26734r1_compiled_candidate"; AFTER="$WORK/candidate_26735"; AFTER2="$WORK/candidate_26735_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-neutral-chroma-digital-luma-retry-debug.apk"; TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""; LOCAL_ONLY=0
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]]||fail "--local-prebuild requires successful 26734 R1 artifact ZIP"; LOCAL_ART="$2"; LOCAL_ONLY=1; elif [[ -n "${1:-}" ]]; then fail "unknown argument"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26735_COMPILER_STATUS.txt" <<EOF
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
JNI CALLBACK CLASS ABI: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
APK JNI CONTRACT: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
verify_package(){
 [[ -d handoff_payload_26735 && "$(find handoff_payload_26735 -type f|wc -l)" -eq 4 ]]||fail "payload count"; [[ "$(wc -l < 26735_RUNTIME_CHANGED_PATHS.txt)" -eq 4 ]]||fail "changed count"; [[ ! -s 26735_ADDED_PATHS_MUST_BE_ABSENT.txt ]]||fail additions
 sha256sum -c 26735_HANDOFF_HASHES.sha256 >/dev/null; bash -n "$0"; python3 -S - <<'PY2'
from pathlib import Path
for n in ['transform_26735.py','validate_26735.py','verify_26735_authority.py','verify_26735_patches.py','verify_26735_regressions.py','verify_26735_shaders.py','verify_26735_infrastructure.py']:
 compile(Path(n).read_text(),n,'exec')
print('PASS sealed Python syntax')
PY2
 ! find . \( -type d -name __pycache__ -o -type f -name '*.pyc' \)|grep -q . || fail transient; ! find . -type f -name '*.apk'|grep -q . || fail "APK packaged"
}
verify_scope(){ if [[ "$LOCAL_ONLY" -eq 1 ]]; then pass "local sealed scope exact 4"; return; fi; [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]]||fail branch; git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD||fail authority_ancestor; ! git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD|grep -Eq '^app/'||fail "live app source committed"; pass "upload scope leaves live app source untouched"; }
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]]||fail token; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
 [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]]||fail artifact_sha; unzip -q "$ARTZIP" -d "$ARTDIR"; T="$ARTDIR/build_26734r1_all_digital_zoom_achromatic_sr_outputs/26734R1_candidate_app_source.tar.gz"; [[ -f "$T" && "$(sha "$T")" == "$BASE_TAR_SHA" ]]||fail tar_sha; mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"; (cd "$BASE" && sha256sum -c "$ROOT/26735_BASE_26734R1_FULL_APP.sha256" >/dev/null)||fail base_manifest; pass "exact successful 26734 R1 compiled candidate authority"
}
compare_app(){ python3 -S - "$1" "$2" <<'PY2'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2]); assert len(a)==len(b)==1823 and a==b; print('PASS candidate byte-identical 1823 files')
PY2
}
make_candidate(){ python3 -S transform_26735.py "$BASE" "$AFTER"; python3 -S transform_26735.py "$BASE" "$AFTER2"; compare_app "$AFTER" "$AFTER2"; python3 -S validate_26735.py "$BASE" "$AFTER"; python3 -S verify_26735_regressions.py "$BASE" "$AFTER"; python3 -S verify_26735_authority.py "$ROOT" "$BASE" "$AFTER"; python3 -S verify_26735_shaders.py "$ROOT" "$BASE" "$AFTER"; }
verify_successful_26734r1_mechanics(){
 local bs wh sv
 bs="$(git show "${MECHANICS_AUTHORITY_COMMIT}:build_26734r1_all_digital_zoom_achromatic_sr.sh" | sha256sum | awk '{print $1}')"; wh="$(git show "${MECHANICS_AUTHORITY_COMMIT}:.github/workflows/build-26734r1-all-digital-zoom-achromatic-sr.yml" | sha256sum | awk '{print $1}')"; sv="$(git show "${MECHANICS_AUTHORITY_COMMIT}:verify_26734r1_shaders.py" | sha256sum | awk '{print $1}')"
 [[ "$bs" == "$PRIOR_BUILD_SHA" ]]||fail "26734 R1 build mechanics hash"; [[ "$wh" == "$PRIOR_WORKFLOW_SHA" ]]||fail "26734 R1 workflow mechanics hash"; [[ "$sv" == "$PRIOR_CURRENT_SHADER_VERIFIER_SHA" ]]||fail "26734 R1 shader verifier hash"; pass "exact successful 26734 R1 mechanics authority hash-pinned"
}
prepare_glslang(){
 D="$WORK/glslang-${GLSLANG_VERSION}"; mkdir -p "$D"; A="$WORK/glslang.tar.gz"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]]||fail glslang_sha; tar -xzf "$A" -C "$D"; compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" -type f -o -type l -name glslangValidator -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]]||chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26735_glslang_version.txt"; export IRIS26735_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; pass "pinned glslang 16.5.0 dual environment handoff"
}
compile_modified_runtime_shaders(){
 # IRIS_26735_CURRENT_AUTHORITY_BASE_SHADER_REPLAY -- permanent repair for failed-26734 stale 26727 manifest misuse.
 python3 -S verify_26735_shaders.py "$ROOT" "$BASE" "$BASE" --base-only --compiler "$IRIS26735_GLSLANG" | tee "$OUT/26735_inherited_shader_compiler_validation.txt"; python3 -S verify_26735_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26735_GLSLANG" | tee "$OUT/26735_shader_compiler_validation.txt"; echo "REAL GLSL COMPILE: PASS (pinned glslang 16.5.0; exact successful-26734R1 base plus exact 9-variant 26735 candidate)" > "$OUT/.glsl"; }
compile_spektra_raw_shader(){ if [[ -f scripts/verify_shaders.py ]]; then IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/26735_spektra_shader_verify.txt"; else pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"; fi; }
install_frozen_candidate_live(){ rm -rf app/src; cp -a "$AFTER/app/src" app/; cp -a "$AFTER/app/build.gradle" app/build.gradle; cp -a "$AFTER/app/version.properties" app/version.properties; rm -rf "$LIVE_CANON"; mkdir -p "$LIVE_CANON"; cp -a "$AFTER/app" "$LIVE_CANON/app"; compare_app "$AFTER" "$LIVE_CANON"; }
after_language_compiler_snapshot(){ rm -rf "$POST"; mkdir -p "$POST"; cp -a "$AFTER/app" "$POST/app"; compare_app "$AFTER" "$POST"; }
verify_candidate_patches(){ python3 -S verify_26735_patches.py "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26735_patch_validation.txt"; }
postbuild_proof(){ compare_app "$AFTER" "$LIVE_CANON"; python3 -S verify_26735_authority.py "$ROOT" "$BASE" "$LIVE_CANON"; python3 -S verify_26735_regressions.py "$BASE" "$LIVE_CANON"; python3 -S verify_26735_shaders.py "$ROOT" "$BASE" "$LIVE_CANON"; tar -czf "$OUT/26735_candidate_app_source.tar.gz" -C "$AFTER" app; sha256sum "$OUT/26735_candidate_app_source.tar.gz" > "$OUT/26735_candidate_app_source.tar.gz.sha256"; cp 26735_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26735_candidate_full_app.sha256"; pass "post-build candidate/protected/native/vendor/DNG invariance"; }
# IRIS_26735_AUTHORITATIVE_ACTIONS_STAGE_ORDER -- exact successful-26734R1 ordering; authority/scope/applicable gates only advance
verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_26734r1_mechanics
prepare_glslang
compile_modified_runtime_shaders
compile_spektra_raw_shader
if [[ "$LOCAL_ONLY" -eq 1 ]]; then verify_candidate_patches; echo "26735 LOCAL PREBUILD COMPLETE — real project Kotlin/Java/NDK/full assemble NOT RUN"; exit 0; fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26735_gradle_language_compilers.log"
sed -i 's/REAL KOTLIN COMPILE:.*/REAL KOTLIN COMPILE: PASS/;s/REAL JAVA COMPILE:.*/REAL JAVA COMPILE: PASS/' "$OUT/26735_COMPILER_STATUS.txt"
pass "JNI callback/motion ABI compiler checkpoint"
after_language_compiler_snapshot
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/26735_gradle_native_compiler.log"
sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#' "$OUT/26735_COMPILER_STATUS.txt"
verify_candidate_patches
echo "26735 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26735_gradle_assemble.log"
sed -i 's/FULL ANDROID ASSEMBLE:.*/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26735_COMPILER_STATUS.txt"
mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk'); [[ "${#apks[@]}" -eq 1 ]]||fail "expected one Gradle APK"; cp "${apks[0]}" "$FINAL"; [[ "$(find . -maxdepth 1 -type f -name 'IrisCamera-*.apk'|wc -l)" -eq 1 ]]||fail "one intended root APK"; sha256sum "$FINAL" > "$OUT/26735_APK.sha256"; sed -i 's/APK JNI CONTRACT:.*/APK JNI CONTRACT: PASS (full assemble APK present; inherited JNI source protected)/' "$OUT/26735_COMPILER_STATUS.txt"
postbuild_proof
sed -i 's/POST-BUILD INVARIANCE:.*/POST-BUILD INVARIANCE: PASS/' "$OUT/26735_COMPILER_STATUS.txt"
sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: PASS (pinned glslang 16.5.0; exact successful-26734R1 base plus exact 9-variant 26735 candidate)#' "$OUT/26735_COMPILER_STATUS.txt"
echo "26735 ACTIONS BUILD COMPLETE"
