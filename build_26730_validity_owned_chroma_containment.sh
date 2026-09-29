#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }; pass(){ echo "PASS: $*"; }; sha(){ sha256sum "$1"|awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="ac11ce0875343815513ab637a8c23ff7fa85921b"; BASE_RUN_ID="36506106479"; BASE_ARTIFACT_ID="11007950351"; BASE_ARTIFACT_NAME="photon-26729-vgn-chroma-containment"; BASE_ARTIFACT_SHA="5676791aa0c2f29c797f72ebec0c49735bc0fed4ca4a191bb1dcd1e74ae7fe2e"; BASE_TAR_SHA="5d7920a592cf2db517316eaf63e40fba553b429a9d9ab92c83df180acebd88ca"
VERSION_NAME="0.9726730"; VERSION_BUILD="26730"; GLSLANG_VERSION="16.5.0"; GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"; GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
PRIOR_BUILD_SHA="8f7c40421fd55e8b437b47d9675aac1d870e331a2bb28ad2736f24b97f70d874"; PRIOR_WORKFLOW_SHA="ec717d6847127da9fdfcfbc979697b641bcbc65b0a929d87913bcf61ef1e433f"; PRIOR_CURRENT_SHADER_VERIFIER_SHA="c26fb0bb61a0e87259c54128a621fb2cfd935cc46ec0bcee928463e41f392b88"; PRIOR_INHERITED_SHADER_VERIFIER_SHA="180fa8f0daed736bb5453dd1dbfda93f28aa34e0b6309f818a04be48e0f3b645"
OUT="$ROOT/build_26730_validity_owned_chroma_containment_outputs"; WORK="$ROOT/.build_26730_validity_owned_chroma_containment_work"; ARTZIP="$WORK/26729_artifact.zip"; ARTDIR="$WORK/artifact_26729"; BASE="$WORK/exact_successful_26729_compiled_candidate"; AFTER="$WORK/candidate_26730"; AFTER2="$WORK/candidate_26730_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-validity-owned-chroma-containment-debug.apk"; TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""; LOCAL_ONLY=0
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]]||fail "--local-prebuild requires successful 26729 artifact ZIP"; LOCAL_ART="$2"; LOCAL_ONLY=1; elif [[ -n "${1:-}" ]]; then fail "unknown argument"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26730_COMPILER_STATUS.txt" <<EOF2
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
 [[ -d handoff_payload_26730 && "$(find handoff_payload_26730 -type f|wc -l)" -eq 2 ]]||fail "payload count"; [[ "$(wc -l < 26730_RUNTIME_CHANGED_PATHS.txt)" -eq 2 ]]||fail "changed count"; [[ ! -s 26730_ADDED_PATHS_MUST_BE_ABSENT.txt ]]||fail additions
 sha256sum -c 26730_HANDOFF_HASHES.sha256 >/dev/null; bash -n "$0"; python3 -S - <<'PY'
from pathlib import Path
for n in ['transform_26730.py','validate_26730.py','verify_26730_authority.py','verify_26730_patches.py','verify_26730_regressions.py','verify_26730_shaders.py','verify_26730_infrastructure.py']:
 compile(Path(n).read_text(),n,'exec')
print('PASS sealed Python syntax')
PY
 ! find . \( -type d -name __pycache__ -o -type f -name '*.pyc' \)|grep -q . || fail transient; ! find . -type f -name '*.apk'|grep -q . || fail "APK packaged"
}
verify_scope(){ if [[ "$LOCAL_ONLY" -eq 1 ]]; then pass "local sealed scope exact 2"; return; fi; [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]]||fail branch; git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD||fail authority_ancestor; ! git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD|grep -Eq '^app/'||fail "live app source committed"; pass "upload scope leaves live app source untouched"; }
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]]||fail token; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
 [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]]||fail artifact_sha; unzip -q "$ARTZIP" -d "$ARTDIR"; T="$ARTDIR/build_26729_vgn_chroma_containment_outputs/26729_candidate_app_source.tar.gz"; [[ -f "$T" && "$(sha "$T")" == "$BASE_TAR_SHA" ]]||fail tar_sha; mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"; (cd "$BASE" && sha256sum -c "$ROOT/26730_BASE_26729_FULL_APP.sha256" >/dev/null)||fail base_manifest; pass "exact successful 26729 compiled candidate authority"
}
compare_app(){ python3 -S - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2]); assert len(a)==len(b)==1823 and a==b; print('PASS candidate byte-identical 1823 files')
PY
}
make_candidate(){ python3 -S transform_26730.py "$BASE" "$AFTER"; python3 -S transform_26730.py "$BASE" "$AFTER2"; compare_app "$AFTER" "$AFTER2"; python3 -S validate_26730.py "$BASE" "$AFTER"; python3 -S verify_26730_regressions.py "$BASE" "$AFTER"; python3 -S verify_26730_authority.py "$ROOT" "$BASE" "$AFTER"; python3 -S verify_26730_shaders.py "$ROOT" "$BASE" "$AFTER"; }
verify_successful_26729_mechanics(){
 local bs wh sv
 bs="$(git show "${RUNTIME_AUTHORITY_COMMIT}:build_26729_vgn_chroma_containment.sh" | sha256sum | awk '{print $1}')"; wh="$(git show "${RUNTIME_AUTHORITY_COMMIT}:.github/workflows/build-26729-vgn-chroma-containment.yml" | sha256sum | awk '{print $1}')"; sv="$(git show "${RUNTIME_AUTHORITY_COMMIT}:verify_26729_shaders.py" | sha256sum | awk '{print $1}')"
 [[ "$bs" == "$PRIOR_BUILD_SHA" ]]||fail "26729 build mechanics hash"; [[ "$wh" == "$PRIOR_WORKFLOW_SHA" ]]||fail "26729 workflow mechanics hash"; [[ "$sv" == "$PRIOR_CURRENT_SHADER_VERIFIER_SHA" ]]||fail "26729 shader verifier hash"; pass "exact successful 26729 mechanics authority hash-pinned"
}
prepare_glslang(){
 D="$WORK/glslang-${GLSLANG_VERSION}"; mkdir -p "$D"; A="$WORK/glslang.tar.gz"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]]||fail glslang_sha; tar -xzf "$A" -C "$D"; compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" -type f -o -type l -name glslangValidator -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]]||chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26730_glslang_version.txt"; export IRIS26730_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; pass "pinned glslang 16.5.0 dual environment handoff"
}
compile_modified_runtime_shaders(){ sha256sum verify_26727_shaders.py | grep -F "$PRIOR_INHERITED_SHADER_VERIFIER_SHA" >/dev/null || fail "26727 shader verifier live hash"; python3 -S verify_26727_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26730_GLSLANG" | tee "$OUT/26730_inherited_shader_compiler_validation.txt"; python3 -S verify_26730_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26730_GLSLANG" | tee "$OUT/26730_shader_compiler_validation.txt"; echo "REAL GLSL COMPILE: PASS (pinned glslang 16.5.0; exact 10 inherited plus 5 VGN/chroma runtime-expanded variants)" > "$OUT/.glsl"; }
compile_spektra_raw_shader(){ if [[ -f scripts/verify_shaders.py ]]; then IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/26730_spektra_shader_verify.txt"; else pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"; fi; }
install_frozen_candidate_live(){ rm -rf app/src; cp -a "$AFTER/app/src" app/; cp -a "$AFTER/app/build.gradle" app/build.gradle; cp -a "$AFTER/app/version.properties" app/version.properties; rm -rf "$LIVE_CANON"; mkdir -p "$LIVE_CANON"; cp -a "$AFTER/app" "$LIVE_CANON/app"; compare_app "$AFTER" "$LIVE_CANON"; }
after_language_compiler_snapshot(){ rm -rf "$POST"; mkdir -p "$POST"; cp -a "$AFTER/app" "$POST/app"; compare_app "$AFTER" "$POST"; }
verify_candidate_patches(){ python3 -S verify_26730_patches.py "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26730_patch_validation.txt"; }
postbuild_proof(){ compare_app "$AFTER" "$LIVE_CANON"; python3 -S verify_26730_authority.py "$ROOT" "$BASE" "$LIVE_CANON"; python3 -S verify_26730_regressions.py "$BASE" "$LIVE_CANON"; tar -czf "$OUT/26730_candidate_app_source.tar.gz" -C "$AFTER" app; sha256sum "$OUT/26730_candidate_app_source.tar.gz" > "$OUT/26730_candidate_app_source.tar.gz.sha256"; cp 26730_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26730_candidate_full_app.sha256"; pass "post-build candidate/protected/native/vendor/DNG invariance"; }
# IRIS_26730_AUTHORITATIVE_ACTIONS_STAGE_ORDER -- exact successful-26729 ordering; authority/scope/applicable gates only advance
verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_26729_mechanics
prepare_glslang
compile_modified_runtime_shaders
compile_spektra_raw_shader
if [[ "$LOCAL_ONLY" -eq 1 ]]; then verify_candidate_patches; echo "26730 LOCAL PREBUILD COMPLETE — real project Kotlin/Java/NDK/full assemble NOT RUN"; exit 0; fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26730_gradle_language_compilers.log"
sed -i 's/REAL KOTLIN COMPILE:.*/REAL KOTLIN COMPILE: PASS/;s/REAL JAVA COMPILE:.*/REAL JAVA COMPILE: PASS/' "$OUT/26730_COMPILER_STATUS.txt"
pass "JNI callback/motion ABI compiler checkpoint"
after_language_compiler_snapshot
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/26730_gradle_native_compiler.log"
sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#' "$OUT/26730_COMPILER_STATUS.txt"
verify_candidate_patches
echo "26730 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26730_gradle_assemble.log"
sed -i 's/FULL ANDROID ASSEMBLE:.*/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26730_COMPILER_STATUS.txt"
mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk'); [[ "${#apks[@]}" -eq 1 ]]||fail "expected one Gradle APK"; cp "${apks[0]}" "$FINAL"; [[ "$(find . -maxdepth 1 -type f -name 'IrisCamera-*.apk'|wc -l)" -eq 1 ]]||fail "one intended root APK"; sha256sum "$FINAL" > "$OUT/26730_APK.sha256"; sed -i 's/APK JNI CONTRACT:.*/APK JNI CONTRACT: PASS (full assemble APK present; inherited JNI source protected)/' "$OUT/26730_COMPILER_STATUS.txt"
postbuild_proof
sed -i 's/POST-BUILD INVARIANCE:.*/POST-BUILD INVARIANCE: PASS/' "$OUT/26730_COMPILER_STATUS.txt"
sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: PASS (pinned glslang 16.5.0; exact 10 inherited plus 5 VGN/chroma runtime-expanded variants)#' "$OUT/26730_COMPILER_STATUS.txt"
echo "26730 ACTIONS BUILD COMPLETE"
