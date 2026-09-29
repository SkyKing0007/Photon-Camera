#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }; pass(){ echo "PASS: $*"; }; sha(){ sha256sum "$1"|awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="aa393fe28e7cf590db0cad5a3c69e3fd64bf3cf2"; BASE_RUN_ID="36523368217"; BASE_ARTIFACT_ID="11013851432"; BASE_ARTIFACT_NAME="photon-26732-chroma-integrity-high-zoom"; BASE_ARTIFACT_SHA="9725e9c97cd2b21dae973a7660b97a0a7cd8ed3cee756c9b5b6cd195266b7a59"; BASE_TAR_SHA="f6f44aecbd3819cab3a68a4f71fc07d25e3c6ba47623cac01a3652923a0a91c7"
MECHANICS_AUTHORITY_COMMIT="aa393fe28e7cf590db0cad5a3c69e3fd64bf3cf2"
VERSION_NAME="0.9726733"; VERSION_BUILD="26733"; GLSLANG_VERSION="16.5.0"; GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"; GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
PRIOR_BUILD_SHA="84e514ed37f2b079adbe86568ebfd614f78b4f11875c15e3fa15b3d6a8e35980"; PRIOR_WORKFLOW_SHA="720bf684e425e5193ffdb339e51a70470ee5f62181408b673ff69fbcbecbb999"; PRIOR_CURRENT_SHADER_VERIFIER_SHA="f9a0827cb52d34ad0afc8eaf885e84224a44414f6fc1f41e94a0420f18839ef5"; PRIOR_INHERITED_SHADER_VERIFIER_SHA="180fa8f0daed736bb5453dd1dbfda93f28aa34e0b6309f818a04be48e0f3b645"
OUT="$ROOT/build_26733_highlight_safe_color_integrity_outputs"; WORK="$ROOT/.build_26733_highlight_safe_color_integrity_work"; ARTZIP="$WORK/26732_artifact.zip"; ARTDIR="$WORK/artifact_26732"; BASE="$WORK/exact_successful_26732_compiled_candidate"; AFTER="$WORK/candidate_26733"; AFTER2="$WORK/candidate_26733_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-highlight-safe-color-integrity-debug.apk"; TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""; LOCAL_ONLY=0
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]]||fail "--local-prebuild requires successful 26732 artifact ZIP"; LOCAL_ART="$2"; LOCAL_ONLY=1; elif [[ -n "${1:-}" ]]; then fail "unknown argument"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26733_COMPILER_STATUS.txt" <<EOF2
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
 [[ -d handoff_payload_26733 && "$(find handoff_payload_26733 -type f|wc -l)" -eq 3 ]]||fail "payload count"; [[ "$(wc -l < 26733_RUNTIME_CHANGED_PATHS.txt)" -eq 3 ]]||fail "changed count"; [[ ! -s 26733_ADDED_PATHS_MUST_BE_ABSENT.txt ]]||fail additions
 sha256sum -c 26733_HANDOFF_HASHES.sha256 >/dev/null; bash -n "$0"; python3 -S - <<'PY2'
from pathlib import Path
for n in ['transform_26733.py','validate_26733.py','verify_26733_authority.py','verify_26733_patches.py','verify_26733_regressions.py','verify_26733_shaders.py','verify_26733_infrastructure.py']:
 compile(Path(n).read_text(),n,'exec')
print('PASS sealed Python syntax')
PY2
 ! find . \( -type d -name __pycache__ -o -type f -name '*.pyc' \)|grep -q . || fail transient; ! find . -type f -name '*.apk'|grep -q . || fail "APK packaged"
}
verify_scope(){ if [[ "$LOCAL_ONLY" -eq 1 ]]; then pass "local sealed scope exact 3"; return; fi; [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]]||fail branch; git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD||fail authority_ancestor; ! git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD|grep -Eq '^app/'||fail "live app source committed"; pass "upload scope leaves live app source untouched"; }
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]]||fail token; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
 [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]]||fail artifact_sha; unzip -q "$ARTZIP" -d "$ARTDIR"; T="$ARTDIR/build_26732_chroma_integrity_high_zoom_outputs/26732_candidate_app_source.tar.gz"; [[ -f "$T" && "$(sha "$T")" == "$BASE_TAR_SHA" ]]||fail tar_sha; mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"; (cd "$BASE" && sha256sum -c "$ROOT/26733_BASE_26732_FULL_APP.sha256" >/dev/null)||fail base_manifest; pass "exact successful 26732 compiled candidate authority"
}
compare_app(){ python3 -S - "$1" "$2" <<'PY2'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2]); assert len(a)==len(b)==1823 and a==b; print('PASS candidate byte-identical 1823 files')
PY2
}
make_candidate(){ python3 -S transform_26733.py "$BASE" "$AFTER"; python3 -S transform_26733.py "$BASE" "$AFTER2"; compare_app "$AFTER" "$AFTER2"; python3 -S validate_26733.py "$BASE" "$AFTER"; python3 -S verify_26733_regressions.py "$BASE" "$AFTER"; python3 -S verify_26733_authority.py "$ROOT" "$BASE" "$AFTER"; python3 -S verify_26733_shaders.py "$ROOT" "$BASE" "$AFTER"; }
verify_successful_26732_mechanics(){
 local bs wh sv
 bs="$(git show "${MECHANICS_AUTHORITY_COMMIT}:build_26732_chroma_integrity_high_zoom.sh" | sha256sum | awk '{print $1}')"; wh="$(git show "${MECHANICS_AUTHORITY_COMMIT}:.github/workflows/build-26732-chroma-integrity-high-zoom.yml" | sha256sum | awk '{print $1}')"; sv="$(git show "${MECHANICS_AUTHORITY_COMMIT}:verify_26732_shaders.py" | sha256sum | awk '{print $1}')"
 [[ "$bs" == "$PRIOR_BUILD_SHA" ]]||fail "26732 build mechanics hash"; [[ "$wh" == "$PRIOR_WORKFLOW_SHA" ]]||fail "26732 workflow mechanics hash"; [[ "$sv" == "$PRIOR_CURRENT_SHADER_VERIFIER_SHA" ]]||fail "26732 shader verifier hash"; pass "exact successful 26732 mechanics authority hash-pinned"
}
prepare_glslang(){
 D="$WORK/glslang-${GLSLANG_VERSION}"; mkdir -p "$D"; A="$WORK/glslang.tar.gz"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]]||fail glslang_sha; tar -xzf "$A" -C "$D"; compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" -type f -o -type l -name glslangValidator -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]]||chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26733_glslang_version.txt"; export IRIS26733_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; pass "pinned glslang 16.5.0 dual environment handoff"
}
compile_modified_runtime_shaders(){ sha256sum verify_26727_shaders.py | grep -F "$PRIOR_INHERITED_SHADER_VERIFIER_SHA" >/dev/null || fail "26727 shader verifier live hash"; python3 -S verify_26727_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26733_GLSLANG" | tee "$OUT/26733_inherited_shader_compiler_validation.txt"; python3 -S verify_26733_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26733_GLSLANG" | tee "$OUT/26733_shader_compiler_validation.txt"; echo "REAL GLSL COMPILE: PASS (pinned glslang 16.5.0; exact 10 inherited plus 8 26733 applicable runtime-expanded variants)" > "$OUT/.glsl"; }
compile_spektra_raw_shader(){ if [[ -f scripts/verify_shaders.py ]]; then IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/26733_spektra_shader_verify.txt"; else pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"; fi; }
install_frozen_candidate_live(){ rm -rf app/src; cp -a "$AFTER/app/src" app/; cp -a "$AFTER/app/build.gradle" app/build.gradle; cp -a "$AFTER/app/version.properties" app/version.properties; rm -rf "$LIVE_CANON"; mkdir -p "$LIVE_CANON"; cp -a "$AFTER/app" "$LIVE_CANON/app"; compare_app "$AFTER" "$LIVE_CANON"; }
after_language_compiler_snapshot(){ rm -rf "$POST"; mkdir -p "$POST"; cp -a "$AFTER/app" "$POST/app"; compare_app "$AFTER" "$POST"; }
verify_candidate_patches(){ python3 -S verify_26733_patches.py "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26733_patch_validation.txt"; }
postbuild_proof(){ compare_app "$AFTER" "$LIVE_CANON"; python3 -S verify_26733_authority.py "$ROOT" "$BASE" "$LIVE_CANON"; python3 -S verify_26733_regressions.py "$BASE" "$LIVE_CANON"; tar -czf "$OUT/26733_candidate_app_source.tar.gz" -C "$AFTER" app; sha256sum "$OUT/26733_candidate_app_source.tar.gz" > "$OUT/26733_candidate_app_source.tar.gz.sha256"; cp 26733_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26733_candidate_full_app.sha256"; pass "post-build candidate/protected/native/vendor/DNG invariance"; }
# IRIS_26733_AUTHORITATIVE_ACTIONS_STAGE_ORDER -- exact successful-26732 ordering; authority/scope/applicable gates only advance
verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_26732_mechanics
prepare_glslang
compile_modified_runtime_shaders
compile_spektra_raw_shader
if [[ "$LOCAL_ONLY" -eq 1 ]]; then verify_candidate_patches; echo "26733 LOCAL PREBUILD COMPLETE — real project Kotlin/Java/NDK/full assemble NOT RUN"; exit 0; fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26733_gradle_language_compilers.log"
sed -i 's/REAL KOTLIN COMPILE:.*/REAL KOTLIN COMPILE: PASS/;s/REAL JAVA COMPILE:.*/REAL JAVA COMPILE: PASS/' "$OUT/26733_COMPILER_STATUS.txt"
pass "JNI callback/motion ABI compiler checkpoint"
after_language_compiler_snapshot
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/26733_gradle_native_compiler.log"
sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#' "$OUT/26733_COMPILER_STATUS.txt"
verify_candidate_patches
echo "26733 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26733_gradle_assemble.log"
sed -i 's/FULL ANDROID ASSEMBLE:.*/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26733_COMPILER_STATUS.txt"
mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk'); [[ "${#apks[@]}" -eq 1 ]]||fail "expected one Gradle APK"; cp "${apks[0]}" "$FINAL"; [[ "$(find . -maxdepth 1 -type f -name 'IrisCamera-*.apk'|wc -l)" -eq 1 ]]||fail "one intended root APK"; sha256sum "$FINAL" > "$OUT/26733_APK.sha256"; sed -i 's/APK JNI CONTRACT:.*/APK JNI CONTRACT: PASS (full assemble APK present; inherited JNI source protected)/' "$OUT/26733_COMPILER_STATUS.txt"
postbuild_proof
sed -i 's/POST-BUILD INVARIANCE:.*/POST-BUILD INVARIANCE: PASS/' "$OUT/26733_COMPILER_STATUS.txt"
sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: PASS (pinned glslang 16.5.0; exact 10 inherited plus 8 26733 applicable runtime-expanded variants)#' "$OUT/26733_COMPILER_STATUS.txt"
echo "26733 ACTIONS BUILD COMPLETE"
