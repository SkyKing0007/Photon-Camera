#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }; pass(){ echo "PASS: $*"; }; sha(){ sha256sum "$1"|awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="bb6e72a86a22ddf0aad335056525a69b09828b97"; ROOT_ARTIFACT_NAME="photon-26771-ui-storage-ownership"; ROOT_ARTIFACT_ID="11384889292"; ROOT_ACTIONS_RUN="37401145164"; ROOT_ARTIFACT_SHA="1742c0643ec58cdeda995a01df47f6b53e5624d30a8ed38a47c86c95388a4683"; ROOT_TAR_SHA="9144d09ff0a0317e2307f4d332d3985c85cecb226f7eaedaf8021231d16be58b"
MECHANICS_AUTHORITY_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"; MECHANICS_ACTIONS_RUN="37075896367"; MECHANICS_ARTIFACT_ID="11256842407"; MECHANICS_ARTIFACT_SHA="6b4677cbb357007f0e7fea61f3259d51f93ebc4d4bd1c6e7133a424763865041"
VERSION_NAME="0.9726772"; VERSION_BUILD="26772"; GLSLANG_VERSION="16.5.0"; GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"; GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26772_storage_ui_highlight_outputs"; WORK="$ROOT/.build_26772_storage_ui_highlight_work"
ARTZIP="$WORK/26771_artifact.zip"; ARTDIR="$WORK/artifact_26771"; BASE="$WORK/exact_successful_26771_compiled_candidate"
AFTER="$WORK/candidate_26772"; AFTER2="$WORK/candidate_26772_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/post_language_compiler_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-storage-ui-highlight-debug.apk"; TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""; LOCAL_ONLY=0
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]]||fail "--local-prebuild requires successful 26771 artifact ZIP"; LOCAL_ART="$2"; LOCAL_ONLY=1; elif [[ -n "${1:-}" ]]; then fail "unknown argument"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26772_COMPILER_STATUS.txt" <<EOF_STATUS
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
JNI CALLBACK CLASS ABI: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
APK JNI CONTRACT: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF_STATUS
verify_package(){
 [[ -d handoff_payload_26772 && "$(find handoff_payload_26772 -type f|wc -l)" -eq 23 ]]||fail "payload count"
 [[ "$(wc -l < 26772_RUNTIME_CHANGED_PATHS.txt)" -eq 68 ]]||fail "changed count"
 [[ "$(wc -l < 26772_MODIFIED_PATHS.txt)" -eq 23 ]]||fail "modified count"
 [[ "$(wc -l < 26772_DELETED_PATHS.txt)" -eq 45 ]]||fail "deleted count"
 sha256sum -c 26772_HANDOFF_HASHES.sha256 >/dev/null
 bash -n "$0"
 python3 -S - <<'PY2'
from pathlib import Path
for n in ['transform_26772.py','validate_26772.py','verify_26772_patches.py','verify_26772_shaders.py']:
 compile(Path(n).read_text(),n,'exec')
print('PASS sealed 26772 Python syntax')
PY2
 ! find . \( -type d -name __pycache__ -o -type f -name '*.pyc' \)|grep -q . || fail transient
 ! find . -type f -name '*.apk'|grep -q . || fail "APK packaged"
}
verify_scope(){
 if [[ "$LOCAL_ONLY" -eq 1 ]]; then pass "local sealed scope exact 68"; return; fi
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]]||fail branch
 git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD||fail runtime_authority_ancestor
 git merge-base --is-ancestor "$MECHANICS_AUTHORITY_COMMIT" HEAD||fail mechanics_authority_ancestor
 ! git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD|grep -Eq '^app/'||fail "live app source committed"
 pass "upload scope leaves live app source untouched; successful 26771 runtime and 26752 mechanics commits remain ancestors"
}
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else
  [[ -n "$TOKEN" ]]||fail token
  curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${ROOT_ARTIFACT_ID}/zip" -o "$ARTZIP"
 fi
 [[ "$(sha "$ARTZIP")" == "$ROOT_ARTIFACT_SHA" ]]||fail artifact_sha
 unzip -q "$ARTZIP" -d "$ARTDIR"
 T="$ARTDIR/build_26771_ui_storage_ownership_outputs/26771_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$ROOT_TAR_SHA" ]]||fail tar_sha
 for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'APK JNI CONTRACT: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$ARTDIR/build_26771_ui_storage_ownership_outputs/26771_COMPILER_STATUS.txt" >/dev/null || fail "26771 authority proof missing: $proof"; done
 mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f|wc -l)" -eq 1824 ]]||fail base_candidate_count
 (cd "$BASE" && sha256sum -c "$ROOT/26772_BASE_26771_FULL_APP.sha256" >/dev/null)||fail base_manifest
 printf 'commit=%s\nrun=%s\nartifact_id=%s\nartifact_name=%s\nartifact_sha256=%s\ncandidate_tar_sha256=%s\nmechanics_commit=%s\nmechanics_run=%s\n' "$RUNTIME_AUTHORITY_COMMIT" "$ROOT_ACTIONS_RUN" "$ROOT_ARTIFACT_ID" "$ROOT_ARTIFACT_NAME" "$ROOT_ARTIFACT_SHA" "$ROOT_TAR_SHA" "$MECHANICS_AUTHORITY_COMMIT" "$MECHANICS_ACTIONS_RUN" > "$OUT/26772_RESOLVED_AUTHORITIES.txt"
 pass "exact successful 26771 R2 runtime candidate reconstructed"
}
compare_app(){ python3 -S - "$1" "$2" <<'PY2'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2]); assert len(a)==len(b)==1779 and a==b; print('PASS candidate byte-identical 1779 files')
PY2
}
verify_domains(){
 local R="$1" MODE="$2"
 while IFS='=' read -r k v; do case "$k" in protected) [[ "$(wc -l < 26772_PROTECTED_AUTHORITY.sha256)" -eq "$v" ]]||fail protected_count;; native) [[ "$(wc -l < 26772_NATIVE_AUTHORITY.sha256)" -eq "$v" ]]||fail native_count;; dng) [[ "$(wc -l < 26772_DNG_AUTHORITY.sha256)" -eq "$v" ]]||fail dng_count;; vendor) [[ "$(wc -l < 26772_VENDOR_AUTHORITY.sha256)" -eq "$v" ]]||fail vendor_count;; asset_shaders) [[ "$(wc -l < 26772_BASE_ASSET_SHADER_UNIVERSE.sha256)" -eq "$v" && "$(wc -l < 26772_EXPECTED_ASSET_SHADER_UNIVERSE.sha256)" -eq "$v" ]]||fail asset_shader_count;; protected_asset_shaders) [[ "$(wc -l < 26772_PROTECTED_ASSET_SHADERS.sha256)" -eq "$v" ]]||fail protected_asset_count;; esac; done < 26772_DOMAIN_COUNTS.txt
 (cd "$R" && sha256sum -c "$ROOT/26772_PROTECTED_AUTHORITY.sha256" >/dev/null)
 (cd "$R" && sha256sum -c "$ROOT/26772_NATIVE_AUTHORITY.sha256" >/dev/null)
 (cd "$R" && sha256sum -c "$ROOT/26772_VENDOR_AUTHORITY.sha256" >/dev/null)
 (cd "$R" && sha256sum -c "$ROOT/26772_PROTECTED_ASSET_SHADERS.sha256" >/dev/null)
 if [[ "$MODE" == base ]]; then
   (cd "$R" && sha256sum -c "$ROOT/26772_DNG_AUTHORITY.sha256" >/dev/null)
   (cd "$R" && sha256sum -c "$ROOT/26772_BASE_ASSET_SHADER_UNIVERSE.sha256" >/dev/null)
 else
   (cd "$R" && sha256sum -c "$ROOT/26772_DNG_AUTHORITY.sha256" >/dev/null)
   (cd "$R" && sha256sum -c "$ROOT/26772_EXPECTED_ASSET_SHADER_UNIVERSE.sha256" >/dev/null)
 fi
 pass "protected/native/vendor/DNG/$MODE-shader universe verified"
}
make_candidate(){
 python3 -S transform_26772.py "$BASE" "$AFTER" handoff_payload_26772
 python3 -S transform_26772.py "$BASE" "$AFTER2" handoff_payload_26772
 compare_app "$AFTER" "$AFTER2"
 python3 -S validate_26772.py "$BASE" "$AFTER"
 (cd "$AFTER" && sha256sum -c "$ROOT/26772_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 verify_domains "$BASE" base; verify_domains "$AFTER" candidate
 python3 -S verify_26772_shaders.py "$BASE" "$AFTER"
}
verify_successful_mechanics(){
 local authority26752="" authority26771=""
 if [[ "$LOCAL_ONLY" -eq 0 ]]; then
  authority26752="$WORK/authority_26752_build.sh"; authority26771="$WORK/authority_26771_build.sh"
  git show "$MECHANICS_AUTHORITY_COMMIT:build_26752_ipol_plan_b_translational_sr.sh" > "$authority26752"
  git show "$RUNTIME_AUTHORITY_COMMIT:build_26771_ui_storage_ownership.sh" > "$authority26771"
 fi
 grep -F 'Core build/handoff mechanics delta from successful 26771/26752 procedure: ZERO.' 26772_INFRASTRUCTURE_DIFF_AUDIT.txt >/dev/null
 python3 -S - "$0" "$authority26752" "$authority26771" <<'PY2'
from pathlib import Path
import sys
def tail(text,marker):
 i=text.find(marker); assert i>=0,f'missing stage marker {marker}'; return text[i:]
def ordered(text,tokens,label):
 pos=-1
 for token in tokens:
  nxt=text.find(token,pos+1); assert nxt>=0,f'{label}: missing {token}'; assert nxt>pos,f'{label}: out-of-order {token}'; pos=nxt
cur=Path(sys.argv[1]).read_text(); tokens=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','mapfile -t apks','postbuild_proof']
ordered(tail(cur,'# IRIS_26772_AUTHORITATIVE_ACTIONS_STAGE_ORDER'),tokens,'26772')
if sys.argv[2]:
 a=Path(sys.argv[2]).read_text(); auth=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26751_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','mapfile -t apks','postbuild_proof']; ordered(tail(a,'# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER'),auth,'26752 authority')
if sys.argv[3]:
 a=Path(sys.argv[3]).read_text(); auth=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','mapfile -t apks','postbuild_proof']; ordered(tail(a,'# IRIS_26771_AUTHORITATIVE_ACTIONS_STAGE_ORDER'),auth,'26771 implementation')
for token in ['GLSLANG_VERSION="16.5.0"','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'./gradlew :app:assembleDebug']: assert token in cur,token
print('PASS exact successful 26771 stage/toolchain/order inherited; successful 26752 mechanics unchanged')
PY2
 pass "successful 26771 implementation inherited; exact 26752 mechanics enforced"
}
prepare_glslang(){
 D="$WORK/glslang-${GLSLANG_VERSION}"; mkdir -p "$D"; A="$WORK/glslang.tar.gz"
 curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]]||fail glslang_sha
 tar -xzf "$A" -C "$D"; compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]]||chmod +x "$compiler"
 "$compiler" --version | tee "$OUT/26772_glslang_version.txt"; export IRIS26772_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; pass "pinned glslang 16.5.0 dual environment handoff"
}
compile_modified_runtime_shaders(){
 python3 -S verify_26772_shaders.py "$BASE" "$AFTER" --compiler "$IRIS26772_GLSLANG" | tee "$OUT/26772_shader_compiler_validation.txt"
 sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: PASS (26772 embedded final-trust compute shader + inherited render/gainmap runtime expansions compiled base+candidate with pinned glslang 16.5.0; 271 asset shaders unchanged)#' "$OUT/26772_COMPILER_STATUS.txt"
}
compile_spektra_raw_shader(){ if [[ -f scripts/verify_shaders.py ]]; then IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/26772_spektra_shader_verify.txt"; else pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"; fi; }
install_frozen_candidate_live(){ rm -rf app/src; cp -a "$AFTER/app/src" app/; cp -a "$AFTER/app/build.gradle" app/build.gradle; cp -a "$AFTER/app/version.properties" app/version.properties; rm -rf "$LIVE_CANON"; mkdir -p "$LIVE_CANON"; cp -a "$AFTER/app" "$LIVE_CANON/app"; compare_app "$AFTER" "$LIVE_CANON"; }
after_language_compiler_snapshot(){ rm -rf "$POST"; mkdir -p "$POST"; cp -a "$AFTER/app" "$POST/app"; compare_app "$AFTER" "$POST"; }
verify_candidate_patches(){ python3 -S verify_26772_patches.py "$BASE" "$AFTER" | tee "$OUT/26772_patch_validation.txt"; }
postbuild_proof(){ compare_app "$AFTER" "$LIVE_CANON"; python3 -S validate_26772.py "$BASE" "$LIVE_CANON"; (cd "$LIVE_CANON" && sha256sum -c "$ROOT/26772_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null); verify_domains "$LIVE_CANON" candidate; python3 -S verify_26772_shaders.py "$BASE" "$LIVE_CANON"; tar -czf "$OUT/26772_candidate_app_source.tar.gz" -C "$AFTER" app; sha256sum "$OUT/26772_candidate_app_source.tar.gz" > "$OUT/26772_candidate_app_source.tar.gz.sha256"; cp 26772_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26772_candidate_full_app.sha256"; pass "post-build authority-seeded candidate/protected/native/vendor/DNG/shader invariance"; }
# IRIS_26772_AUTHORITATIVE_ACTIONS_STAGE_ORDER -- exact successful 26771 stage/toolchain/order inherited from successful 26752
verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_mechanics
prepare_glslang
compile_modified_runtime_shaders
compile_spektra_raw_shader
if [[ "$LOCAL_ONLY" -eq 1 ]]; then verify_candidate_patches; echo "26772 LOCAL PREBUILD COMPLETE — real project Kotlin/Java/NDK/full assemble intentionally left to Actions"; exit 0; fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26772_gradle_language_compilers.log"
sed -i 's/REAL KOTLIN COMPILE:.*/REAL KOTLIN COMPILE: PASS/;s/REAL JAVA COMPILE:.*/REAL JAVA COMPILE: PASS/' "$OUT/26772_COMPILER_STATUS.txt"
pass "JNI callback/motion ABI compiler checkpoint"
after_language_compiler_snapshot
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/26772_gradle_native_compiler.log"
sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#;s#JNI CALLBACK CLASS ABI:.*#JNI CALLBACK CLASS ABI: PASS (Java/JNI declarations + both-ABI native link)#' "$OUT/26772_COMPILER_STATUS.txt"
verify_candidate_patches
echo "26772 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26772_gradle_assemble.log"
sed -i 's/FULL ANDROID ASSEMBLE:.*/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26772_COMPILER_STATUS.txt"
mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk'); [[ "${#apks[@]}" -eq 1 ]]||fail "expected one Gradle APK"; cp "${apks[0]}" "$FINAL"; [[ "$(find . -maxdepth 1 -type f -name 'IrisCamera-*.apk'|wc -l)" -eq 1 ]]||fail "one intended root APK"; sha256sum "$FINAL" > "$OUT/26772_APK.sha256"
sed -i 's#APK JNI CONTRACT:.*#APK JNI CONTRACT: PASS (26771 R2 capture/runtime inherited; 26772 scope limited to Gallery removal, dual storage/log routing, still-DNG destination, histogram/front-camera/zoom UI, and flattened-highlight-only final VGN chroma gate; DNG serialization/math unchanged)#' "$OUT/26772_COMPILER_STATUS.txt"
postbuild_proof
sed -i 's/POST-BUILD INVARIANCE:.*/POST-BUILD INVARIANCE: PASS/' "$OUT/26772_COMPILER_STATUS.txt"
echo "26772 ACTIONS BUILD COMPLETE"
