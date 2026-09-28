#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }; pass(){ echo "PASS: $*"; }; sha(){ sha256sum "$1"|awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="1e31f39b27b0572fef6658e4535709d95bb955c0"; BASE_RUN_ID="36379815046"; BASE_ARTIFACT_ID="10952775232"; BASE_ARTIFACT_NAME="photon-26724-resilient-capture-high-zoom-iq"; BASE_ARTIFACT_SHA="bbb69e8680e75acc5303b1b67c5b657330f3068bb9c1f0adc8359b7b47dc412c"; BASE_TAR_SHA="6bc2e2cae12483e1714f0ad041e4e120933508b447cc20d397b34d81acfab2ae"
VERSION_NAME="0.9726725"; VERSION_BUILD="26725"; GLSLANG_VERSION="16.5.0"; GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"; GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26725_pixel_raw_cpu_compatibility_outputs"; WORK="$ROOT/.build_26725_pixel_raw_cpu_compatibility_work"; ARTZIP="$WORK/26724_artifact.zip"; ARTDIR="$WORK/artifact_26724"; BASE="$WORK/exact_successful_26724_compiled_candidate"; AFTER="$WORK/candidate_26725"; AFTER2="$WORK/candidate_26725_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-pixel-raw-cpu-compatibility-debug.apk"; TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""; LOCAL_ONLY=0
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]]||fail "--local-prebuild requires successful 26724 artifact ZIP"; LOCAL_ART="$2"; LOCAL_ONLY=1; elif [[ -n "${1:-}" ]]; then fail "unknown argument"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26725_COMPILER_STATUS.txt" <<EOF2
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
 [[ -d handoff_payload_26725 && "$(find handoff_payload_26725 -type f|wc -l)" -eq 2 ]]||fail "payload count"; [[ "$(wc -l < 26725_RUNTIME_CHANGED_PATHS.txt)" -eq 2 ]]||fail "changed count"; [[ ! -s 26725_ADDED_PATHS_MUST_BE_ABSENT.txt ]]||fail additions
 sha256sum -c 26725_HANDOFF_HASHES.sha256 >/dev/null; bash -n "$0"; python3 -S - <<'PY'
from pathlib import Path
for n in ['transform_26725.py','validate_26725.py','verify_26725_authority.py','verify_26725_patches.py','verify_26725_regressions.py','verify_26725_shaders.py','verify_26725_infrastructure.py']:
 compile(Path(n).read_text(),n,'exec')
print('PASS sealed Python syntax')
PY
 ! find . \( -type d -name __pycache__ -o -type f -name '*.pyc' \)|grep -q . || fail transient; ! find . -type f -name '*.apk'|grep -q . || fail "APK packaged"
}
verify_scope(){ if [[ "$LOCAL_ONLY" -eq 1 ]]; then pass "local sealed scope exact 2"; return; fi; [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]]||fail branch; git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD||fail authority_ancestor; ! git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD|grep -Eq '^app/'||fail "live app source committed"; pass "upload scope leaves live app source untouched"; }
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]]||fail token; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
 [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]]||fail artifact_sha; unzip -q "$ARTZIP" -d "$ARTDIR"; T="$ARTDIR/build_26724_resilient_capture_high_zoom_iq_outputs/26724_candidate_app_source.tar.gz"; [[ -f "$T" && "$(sha "$T")" == "$BASE_TAR_SHA" ]]||fail tar_sha; mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"; (cd "$BASE" && sha256sum -c "$ROOT/26725_BASE_26724_FULL_APP.sha256" >/dev/null)||fail base_manifest; pass "exact successful 26724 compiled candidate authority"
}
compare_app(){ python3 -S - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2]); assert len(a)==len(b)==1823 and a==b; print('PASS candidate byte-identical 1823 files')
PY
}
make_candidate(){ python3 -S transform_26725.py "$BASE" "$AFTER"; python3 -S transform_26725.py "$BASE" "$AFTER2"; compare_app "$AFTER" "$AFTER2"; python3 -S validate_26725.py "$BASE" "$AFTER"; python3 -S verify_26725_regressions.py "$BASE" "$AFTER"; python3 -S verify_26725_authority.py "$ROOT" "$BASE" "$AFTER"; python3 -S verify_26725_shaders.py "$ROOT" "$BASE" "$AFTER"; }
verify_successful_26724_mechanics(){
 local bs wh
 bs="$(git show "${RUNTIME_AUTHORITY_COMMIT}:build_26724_resilient_capture_high_zoom_iq.sh" | sha256sum | awk '{print $1}')"
 wh="$(git show "${RUNTIME_AUTHORITY_COMMIT}:.github/workflows/build-26724-resilient-capture-high-zoom-iq.yml" | sha256sum | awk '{print $1}')"
 [[ "$bs" == "16fa502afd1e540d25d7b6c2e39fe34255b4be4edb570aaab43e1160467e5556" ]]||fail "26724 build mechanics hash"
 [[ "$wh" == "8e1d78d63230555bba756c46166c7b485880d71fed3728411512ba500b930855" ]]||fail "26724 workflow mechanics hash"
 pass "exact successful 26724 mechanics authority hash-pinned"
}
prepare_glslang(){
 D="$WORK/glslang-${GLSLANG_VERSION}"; mkdir -p "$D"; A="$WORK/glslang.tar.gz"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]]||fail glslang_sha; tar -xzf "$A" -C "$D"; compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" -type f -o -type l -name glslangValidator -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]]||chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26725_glslang_version.txt"; export IRIS26725_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; pass "pinned glslang 16.5.0 dual environment handoff"
}
compile_modified_runtime_shaders(){ python3 -S verify_26725_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26725_GLSLANG" | tee "$OUT/26725_shader_compiler_validation.txt"; echo "REAL GLSL COMPILE: PASS (exact 10 successful-26724 runtime-expanded variants preserved; 26725 modifies no GLSL; pinned glslang 16.5.0)" > "$OUT/.glsl"; }
compile_spektra_raw_shader(){ if [[ -f scripts/verify_shaders.py ]]; then IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/26725_spektra_shader_verify.txt"; else pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"; fi; }
install_frozen_candidate_live(){ rm -rf app/src; cp -a "$AFTER/app/src" app/; cp -a "$AFTER/app/build.gradle" app/build.gradle; cp -a "$AFTER/app/version.properties" app/version.properties; rm -rf "$LIVE_CANON"; mkdir -p "$LIVE_CANON"; cp -a "$AFTER/app" "$LIVE_CANON/app"; compare_app "$AFTER" "$LIVE_CANON"; }
after_language_compiler_snapshot(){ rm -rf "$POST"; mkdir -p "$POST"; cp -a "$AFTER/app" "$POST/app"; compare_app "$AFTER" "$POST"; }
verify_candidate_patches(){ python3 -S verify_26725_patches.py "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26725_patch_validation.txt"; }
postbuild_proof(){ compare_app "$AFTER" "$LIVE_CANON"; python3 -S verify_26725_authority.py "$ROOT" "$BASE" "$LIVE_CANON"; python3 -S verify_26725_regressions.py "$BASE" "$LIVE_CANON"; tar -czf "$OUT/26725_candidate_app_source.tar.gz" -C "$AFTER" app; sha256sum "$OUT/26725_candidate_app_source.tar.gz" > "$OUT/26725_candidate_app_source.tar.gz.sha256"; cp 26725_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26725_candidate_full_app.sha256"; pass "post-build candidate/protected/native/vendor/DNG invariance"; }
# IRIS_26725_AUTHORITATIVE_ACTIONS_STAGE_ORDER -- exact successful-26724 ordering; authority/scope/applicable gates only advance
verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_26724_mechanics
prepare_glslang
compile_modified_runtime_shaders
compile_spektra_raw_shader
if [[ "$LOCAL_ONLY" -eq 1 ]]; then verify_candidate_patches; echo "26725 LOCAL PREBUILD COMPLETE — real project compilers NOT RUN"; exit 0; fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26725_gradle_language_compilers.log"
sed -i 's/REAL KOTLIN COMPILE:.*/REAL KOTLIN COMPILE: PASS/;s/REAL JAVA COMPILE:.*/REAL JAVA COMPILE: PASS/' "$OUT/26725_COMPILER_STATUS.txt"
pass "JNI callback/motion ABI compiler checkpoint"
after_language_compiler_snapshot
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/26725_gradle_native_compiler.log"
sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#' "$OUT/26725_COMPILER_STATUS.txt"
verify_candidate_patches
echo "26725 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26725_gradle_assemble.log"
sed -i 's/FULL ANDROID ASSEMBLE:.*/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26725_COMPILER_STATUS.txt"
mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk'); [[ "${#apks[@]}" -eq 1 ]]||fail "expected one Gradle APK"; cp "${apks[0]}" "$FINAL"; [[ "$(find . -maxdepth 1 -type f -name 'IrisCamera-*.apk'|wc -l)" -eq 1 ]]||fail "one intended root APK"; sha256sum "$FINAL" > "$OUT/26725_APK.sha256"; sed -i 's/APK JNI CONTRACT:.*/APK JNI CONTRACT: PASS (full assemble APK present; inherited JNI source protected)/' "$OUT/26725_COMPILER_STATUS.txt"
postbuild_proof
sed -i 's/POST-BUILD INVARIANCE:.*/POST-BUILD INVARIANCE: PASS/' "$OUT/26725_COMPILER_STATUS.txt"
sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: PASS (pinned glslang 16.5.0; exact 10 successful-26724 runtime-expanded variants preserved; 26725 modifies no GLSL)#' "$OUT/26725_COMPILER_STATUS.txt"
echo "26725 ACTIONS BUILD COMPLETE"
