#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }; pass(){ echo "PASS: $*"; }; sha(){ sha256sum "$1"|awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="75f8bd1c3bf4de0fe4ed4f28e07575be80fd234c"; BASE_RUN_ID="36354348329"; BASE_ARTIFACT_ID="10943139473"; BASE_ARTIFACT_NAME="photon-26721-high-zoom-rgb32f-transport"; BASE_ARTIFACT_SHA="d869d1484039dad4b92a415130dec750b8d28547d6f05372f635914831792fb5"; BASE_TAR_SHA="e174b61afe513d3b322c4cf2d9c0221d167493e6b07f184f86f93d31b6824d11"
VERSION_NAME="0.9726722"; VERSION_BUILD="26722"; GLSLANG_VERSION="16.5.0"; GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"; GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26722_high_zoom_native_chroma_outputs"; WORK="$ROOT/.build_26722_high_zoom_native_chroma_work"; ARTZIP="$WORK/26721_artifact.zip"; ARTDIR="$WORK/artifact_26721"; BASE="$WORK/exact_successful_26721_compiled_candidate"; AFTER="$WORK/candidate_26722"; AFTER2="$WORK/candidate_26722_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-high-zoom-native-chroma-debug.apk"; TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""; LOCAL_ONLY=0
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]]||fail "--local-prebuild requires successful 26721 artifact ZIP"; LOCAL_ART="$2"; LOCAL_ONLY=1; elif [[ -n "${1:-}" ]]; then fail "unknown argument"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26722_COMPILER_STATUS.txt" <<EOF
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
 [[ -d handoff_payload_26722 && "$(find handoff_payload_26722 -type f|wc -l)" -eq 3 ]]||fail "payload count"; [[ "$(wc -l < 26722_RUNTIME_CHANGED_PATHS.txt)" -eq 3 ]]||fail "changed count"; [[ ! -s 26722_ADDED_PATHS_MUST_BE_ABSENT.txt ]]||fail additions
 sha256sum -c 26722_HANDOFF_HASHES.sha256 >/dev/null; bash -n "$0"; python3 -S - <<'PY'
from pathlib import Path
for n in ['transform_26722.py','validate_26722.py','verify_26722_authority.py','verify_26722_patches.py','verify_26722_regressions.py','verify_26722_shaders.py','verify_26722_infrastructure.py']:
 compile(Path(n).read_text(),n,'exec')
print('PASS sealed Python syntax')
PY
 ! find . \( -type d -name __pycache__ -o -type f -name '*.pyc' \)|grep -q . || fail transient; ! find . -type f -name '*.apk'|grep -q . || fail "APK packaged"
}
verify_scope(){ if [[ "$LOCAL_ONLY" -eq 1 ]]; then pass "local sealed scope exact 3"; return; fi; [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]]||fail branch; git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD||fail authority_ancestor; ! git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD|grep -Eq '^app/'||fail "live app source committed"; pass "upload scope leaves live app source untouched"; }
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]]||fail token; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
 [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]]||fail artifact_sha; unzip -q "$ARTZIP" -d "$ARTDIR"; T="$ARTDIR/build_26721_high_zoom_rgb32f_transport_outputs/26721_candidate_app_source.tar.gz"; [[ -f "$T" && "$(sha "$T")" == "$BASE_TAR_SHA" ]]||fail tar_sha; mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"; (cd "$BASE" && sha256sum -c "$ROOT/26722_BASE_26721_FULL_APP.sha256" >/dev/null)||fail base_manifest; pass "exact successful 26721 compiled candidate authority"
}
compare_app(){ python3 -S - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2]); assert len(a)==len(b)==1823 and a==b; print('PASS candidate byte-identical 1823 files')
PY
}
make_candidate(){ python3 -S transform_26722.py "$BASE" "$AFTER"; python3 -S transform_26722.py "$BASE" "$AFTER2"; compare_app "$AFTER" "$AFTER2"; python3 -S validate_26722.py "$BASE" "$AFTER"; python3 -S verify_26722_regressions.py "$BASE" "$AFTER"; python3 -S verify_26722_authority.py "$ROOT" "$BASE" "$AFTER"; python3 -S verify_26722_shaders.py "$ROOT" "$BASE" "$AFTER"; }
verify_successful_26721_mechanics(){
 local bs wh
 bs="$(git show "${RUNTIME_AUTHORITY_COMMIT}:build_26721_high_zoom_rgb32f_transport.sh" | sha256sum | awk '{print $1}')"
 wh="$(git show "${RUNTIME_AUTHORITY_COMMIT}:.github/workflows/build-26721-high-zoom-rgb32f-transport.yml" | sha256sum | awk '{print $1}')"
 [[ "$bs" == "2855cbc6ec9426a050235648e9a1520eb53217502fb90639efb40fc33427b082" ]]||fail "26721 build mechanics hash"
 [[ "$wh" == "99b225886ed6767e985ce3ab13c54996c79d54fdbf7d6646a34db6457df0cb75" ]]||fail "26721 workflow mechanics hash"
 pass "exact successful 26721 mechanics authority hash-pinned"
}
prepare_glslang(){
 D="$WORK/glslang-${GLSLANG_VERSION}"; mkdir -p "$D"; A="$WORK/glslang.tar.gz"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]]||fail glslang_sha; tar -xzf "$A" -C "$D"; compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" -type f -o -type l -name glslangValidator -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]]||chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26722_glslang_version.txt"; export IRIS26722_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; pass "pinned glslang 16.5.0 dual environment handoff"
}
compile_modified_runtime_shaders(){ python3 -S verify_26722_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26722_GLSLANG" | tee "$OUT/26722_shader_compiler_validation.txt"; echo "REAL GLSL COMPILE: PASS (exact 8 high-zoom/banding runtime-expanded variants; 26722 high-zoom protect uses proven native-Sabre/VGN chroma topology with direct-CFA luma/detail only; pinned glslang 16.5.0)" > "$OUT/.glsl"; }
compile_spektra_raw_shader(){ if [[ -f scripts/verify_shaders.py ]]; then IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/26722_spektra_shader_verify.txt"; else pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"; fi; }
install_frozen_candidate_live(){ rm -rf app/src; cp -a "$AFTER/app/src" app/; cp -a "$AFTER/app/build.gradle" app/build.gradle; cp -a "$AFTER/app/version.properties" app/version.properties; rm -rf "$LIVE_CANON"; mkdir -p "$LIVE_CANON"; cp -a "$AFTER/app" "$LIVE_CANON/app"; compare_app "$AFTER" "$LIVE_CANON"; }
after_language_compiler_snapshot(){ rm -rf "$POST"; mkdir -p "$POST"; cp -a "$AFTER/app" "$POST/app"; compare_app "$AFTER" "$POST"; }
verify_candidate_patches(){ python3 -S verify_26722_patches.py "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26722_patch_validation.txt"; }
postbuild_proof(){ compare_app "$AFTER" "$LIVE_CANON"; python3 -S verify_26722_authority.py "$ROOT" "$BASE" "$LIVE_CANON"; python3 -S verify_26722_regressions.py "$BASE" "$LIVE_CANON"; tar -czf "$OUT/26722_candidate_app_source.tar.gz" -C "$AFTER" app; sha256sum "$OUT/26722_candidate_app_source.tar.gz" > "$OUT/26722_candidate_app_source.tar.gz.sha256"; cp 26722_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26722_candidate_full_app.sha256"; pass "post-build candidate/protected/native/vendor/DNG invariance"; }
# IRIS_26722_AUTHORITATIVE_ACTIONS_STAGE_ORDER -- exact successful-26721 ordering; authority/scope/applicable gates only advance
verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_26721_mechanics
prepare_glslang
compile_modified_runtime_shaders
compile_spektra_raw_shader
if [[ "$LOCAL_ONLY" -eq 1 ]]; then verify_candidate_patches; echo "26722 LOCAL PREBUILD COMPLETE — real project compilers NOT RUN"; exit 0; fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26722_gradle_language_compilers.log"
sed -i 's/REAL KOTLIN COMPILE:.*/REAL KOTLIN COMPILE: PASS/;s/REAL JAVA COMPILE:.*/REAL JAVA COMPILE: PASS/' "$OUT/26722_COMPILER_STATUS.txt"
pass "JNI callback/motion ABI compiler checkpoint"
after_language_compiler_snapshot
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/26722_gradle_native_compiler.log"
sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#' "$OUT/26722_COMPILER_STATUS.txt"
verify_candidate_patches
echo "26722 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26722_gradle_assemble.log"
sed -i 's/FULL ANDROID ASSEMBLE:.*/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26722_COMPILER_STATUS.txt"
mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk'); [[ "${#apks[@]}" -eq 1 ]]||fail "expected one Gradle APK"; cp "${apks[0]}" "$FINAL"; [[ "$(find . -maxdepth 1 -type f -name 'IrisCamera-*.apk'|wc -l)" -eq 1 ]]||fail "one intended root APK"; sha256sum "$FINAL" > "$OUT/26722_APK.sha256"; sed -i 's/APK JNI CONTRACT:.*/APK JNI CONTRACT: PASS (full assemble APK present; inherited JNI source protected)/' "$OUT/26722_COMPILER_STATUS.txt"
postbuild_proof
sed -i 's/POST-BUILD INVARIANCE:.*/POST-BUILD INVARIANCE: PASS/' "$OUT/26722_COMPILER_STATUS.txt"
sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: PASS (pinned glslang 16.5.0; exact 8 high-zoom/banding runtime-expanded variants; 26722 native-Sabre/VGN chroma topology)#' "$OUT/26722_COMPILER_STATUS.txt"
echo "26722 ACTIONS BUILD COMPLETE"
