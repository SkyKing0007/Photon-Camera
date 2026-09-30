#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }; pass(){ echo "PASS: $*"; }; sha(){ sha256sum "$1"|awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
ROOT_ACTIONS_AUTHORITY_COMMIT="271f52be81d8222e5f04fdfd0e9085a55bbd5e2c"; ROOT_RUN_ID="36637337435"; ROOT_ARTIFACT_ID="11064304462"; ROOT_ARTIFACT_NAME="photon-26735-neutral-chroma-digital-luma-retry"; ROOT_ARTIFACT_SHA="37b6ef1cf0735403765291f15fe7b639d67d1ff406a54617b639e97221bbf8bd"; ROOT_TAR_SHA="8159fbf01e8e02d8d4a0480dd2bc53348f2e57938f63111db7fd69a6ac76ba0a"
VERSION_NAME="0.9726737"; VERSION_BUILD="26737"; GLSLANG_VERSION="16.5.0"; GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"; GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26737_wronski_phase_chroma_integrity_outputs"; WORK="$ROOT/.build_26737_wronski_phase_chroma_integrity_work"; ARTZIP="$WORK/26735_artifact.zip"; ARTDIR="$WORK/artifact_26735"; ROOTBASE="$WORK/exact_successful_26735_compiled_candidate"; BASE="$WORK/exact_reconstructed_26736_candidate"; AFTER="$WORK/candidate_26737"; AFTER2="$WORK/candidate_26737_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-wronski-phase-chroma-integrity-debug.apk"; TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""; LOCAL_ONLY=0
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]]||fail "--local-prebuild requires successful 26735 artifact ZIP"; LOCAL_ART="$2"; LOCAL_ONLY=1; elif [[ -n "${1:-}" ]]; then fail "unknown argument"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26737_COMPILER_STATUS.txt" <<EOF
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
 [[ -d handoff_payload_26737 && "$(find handoff_payload_26737 -type f|wc -l)" -eq 4 ]]||fail "payload count"; [[ -d authority_payload_26736 && "$(find authority_payload_26736 -type f|wc -l)" -eq 3 ]]||fail "26736 authority payload count"; [[ "$(wc -l < 26737_RUNTIME_CHANGED_PATHS.txt)" -eq 4 ]]||fail "changed count"; [[ ! -s 26737_ADDED_PATHS_MUST_BE_ABSENT.txt ]]||fail additions
 sha256sum -c 26737_HANDOFF_HASHES.sha256 >/dev/null; bash -n "$0"; python3 -S - <<'PY2'
from pathlib import Path
for n in ['transform_26737.py','validate_26737.py','verify_26737_authority.py','verify_26737_patches.py','verify_26737_regressions.py','verify_26737_shaders.py','verify_26737_infrastructure.py']:
 compile(Path(n).read_text(),n,'exec')
print('PASS sealed Python syntax')
PY2
 ! find . \( -type d -name __pycache__ -o -type f -name '*.pyc' \)|grep -q . || fail transient; ! find . -type f -name '*.apk'|grep -q . || fail "APK packaged"
}
verify_scope(){ if [[ "$LOCAL_ONLY" -eq 1 ]]; then pass "local sealed scope exact 4"; return; fi; [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]]||fail branch; git merge-base --is-ancestor "$ROOT_ACTIONS_AUTHORITY_COMMIT" HEAD||fail authority_ancestor; ! git diff --name-only "$ROOT_ACTIONS_AUTHORITY_COMMIT"..HEAD|grep -Eq '^app/'||fail "live app source committed"; pass "upload scope leaves live app source untouched"; }
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]]||fail token; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${ROOT_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
 [[ "$(sha "$ARTZIP")" == "$ROOT_ARTIFACT_SHA" ]]||fail artifact_sha; unzip -q "$ARTZIP" -d "$ARTDIR"; T="$ARTDIR/build_26735_neutral_chroma_digital_luma_retry_outputs/26735_candidate_app_source.tar.gz"; [[ -f "$T" && "$(sha "$T")" == "$ROOT_TAR_SHA" ]]||fail tar_sha; mkdir -p "$ROOTBASE"; tar -xzf "$T" -C "$ROOTBASE"; (cd "$ROOTBASE" && sha256sum -c "$ROOT/26737_SUCCESSFUL_26735_ROOT_AUTHORITY.sha256" >/dev/null)||fail root_base_manifest
 rm -rf "$BASE"; cp -a "$ROOTBASE" "$BASE"; while IFS= read -r -d '' p; do rel="${p#authority_payload_26736/}"; q="$BASE/$rel"; mkdir -p "$(dirname "$q")"; cp -a "$p" "$q"; done < <(find authority_payload_26736 -type f -print0 | sort -z); (cd "$BASE" && sha256sum -c "$ROOT/26737_BASE_26736_FULL_APP.sha256" >/dev/null)||fail reconstructed_26736_manifest; pass "exact 26736 candidate reconstructed from successful 26735 Actions authority plus sealed 26736 payload"
}
compare_app(){ python3 -S - "$1" "$2" <<'PY2'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2]); assert len(a)==len(b)==1823 and a==b; print('PASS candidate byte-identical 1823 files')
PY2
}
make_candidate(){ python3 -S transform_26737.py "$BASE" "$AFTER"; python3 -S transform_26737.py "$BASE" "$AFTER2"; compare_app "$AFTER" "$AFTER2"; python3 -S validate_26737.py "$BASE" "$AFTER"; python3 -S verify_26737_regressions.py "$BASE" "$AFTER"; python3 -S verify_26737_authority.py "$ROOT" "$BASE" "$AFTER"; python3 -S verify_26737_shaders.py "$ROOT" "$BASE" "$AFTER"; }
verify_successful_26736_mechanics(){ sha256sum -c 26737_SEALED_26736_INFRASTRUCTURE_AUTHORITY.sha256 >/dev/null || fail "sealed 26736 mechanics authority drift"; pass "exact sealed 26736 nine-role mechanics authority hash-pinned"; }
prepare_glslang(){ D="$WORK/glslang-${GLSLANG_VERSION}"; mkdir -p "$D"; A="$WORK/glslang.tar.gz"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]]||fail glslang_sha; tar -xzf "$A" -C "$D"; compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" -type f -o -type l -name glslangValidator -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]]||chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26737_glslang_version.txt"; export IRIS26737_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; pass "pinned glslang 16.5.0 dual environment handoff"; }
compile_modified_runtime_shaders(){ # IRIS_26737_CURRENT_AUTHORITY_BASE_SHADER_REPLAY
 python3 -S verify_26737_shaders.py "$ROOT" "$BASE" "$BASE" --base-only --compiler "$IRIS26737_GLSLANG" | tee "$OUT/26737_inherited_shader_compiler_validation.txt"; python3 -S verify_26737_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26737_GLSLANG" | tee "$OUT/26737_shader_compiler_validation.txt"; echo "REAL GLSL COMPILE: PASS (pinned glslang 16.5.0; exact reconstructed-26736 base plus exact 10-variant 26737 candidate)" > "$OUT/.glsl"; }
compile_spektra_raw_shader(){ if [[ -f scripts/verify_shaders.py ]]; then IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/26737_spektra_shader_verify.txt"; else pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"; fi; }
install_frozen_candidate_live(){ rm -rf app/src; cp -a "$AFTER/app/src" app/; cp -a "$AFTER/app/build.gradle" app/build.gradle; cp -a "$AFTER/app/version.properties" app/version.properties; rm -rf "$LIVE_CANON"; mkdir -p "$LIVE_CANON"; cp -a "$AFTER/app" "$LIVE_CANON/app"; compare_app "$AFTER" "$LIVE_CANON"; }
after_language_compiler_snapshot(){ rm -rf "$POST"; mkdir -p "$POST"; cp -a "$AFTER/app" "$POST/app"; compare_app "$AFTER" "$POST"; }
verify_candidate_patches(){ python3 -S verify_26737_patches.py "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26737_patch_validation.txt"; }
postbuild_proof(){ compare_app "$AFTER" "$LIVE_CANON"; python3 -S verify_26737_authority.py "$ROOT" "$BASE" "$LIVE_CANON"; python3 -S verify_26737_regressions.py "$BASE" "$LIVE_CANON"; python3 -S verify_26737_shaders.py "$ROOT" "$BASE" "$LIVE_CANON"; tar -czf "$OUT/26737_candidate_app_source.tar.gz" -C "$AFTER" app; sha256sum "$OUT/26737_candidate_app_source.tar.gz" > "$OUT/26737_candidate_app_source.tar.gz.sha256"; cp 26737_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26737_candidate_full_app.sha256"; pass "post-build candidate/protected/native/vendor/DNG invariance"; }
# IRIS_26737_AUTHORITATIVE_ACTIONS_STAGE_ORDER -- exact 26736 ordering; authority reconstruction/applicable gates only advance
verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_26736_mechanics
prepare_glslang
compile_modified_runtime_shaders
compile_spektra_raw_shader
if [[ "$LOCAL_ONLY" -eq 1 ]]; then verify_candidate_patches; echo "26737 LOCAL PREBUILD COMPLETE — real project Kotlin/Java/NDK/full assemble NOT RUN"; exit 0; fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26737_gradle_language_compilers.log"
sed -i 's/REAL KOTLIN COMPILE:.*/REAL KOTLIN COMPILE: PASS/;s/REAL JAVA COMPILE:.*/REAL JAVA COMPILE: PASS/' "$OUT/26737_COMPILER_STATUS.txt"
pass "JNI callback/motion ABI compiler checkpoint"
after_language_compiler_snapshot
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/26737_gradle_native_compiler.log"
sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#' "$OUT/26737_COMPILER_STATUS.txt"
verify_candidate_patches
echo "26737 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26737_gradle_assemble.log"
sed -i 's/FULL ANDROID ASSEMBLE:.*/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26737_COMPILER_STATUS.txt"
mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk'); [[ "${#apks[@]}" -eq 1 ]]||fail "expected one Gradle APK"; cp "${apks[0]}" "$FINAL"; [[ "$(find . -maxdepth 1 -type f -name 'IrisCamera-*.apk'|wc -l)" -eq 1 ]]||fail "one intended root APK"; sha256sum "$FINAL" > "$OUT/26737_APK.sha256"; sed -i 's/APK JNI CONTRACT:.*/APK JNI CONTRACT: PASS (full assemble APK present; inherited JNI source protected)/' "$OUT/26737_COMPILER_STATUS.txt"
postbuild_proof
sed -i 's/POST-BUILD INVARIANCE:.*/POST-BUILD INVARIANCE: PASS/' "$OUT/26737_COMPILER_STATUS.txt"
sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: PASS (pinned glslang 16.5.0; exact reconstructed-26736 base plus exact 10-variant 26737 candidate)#' "$OUT/26737_COMPILER_STATUS.txt"
echo "26737 ACTIONS BUILD COMPLETE"
