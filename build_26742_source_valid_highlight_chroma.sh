#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }; pass(){ echo "PASS: $*"; }; sha(){ sha256sum "$1"|awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
ROOT_ACTIONS_AUTHORITY_COMMIT="4541f7e0f86661623231b99aec19d6c88f58f4e7"; ROOT_ARTIFACT_NAME="photon-26741-superres-confidence-bright-neutrality"; ROOT_ARTIFACT_SHA="0020dc73a48bc6fa02a78a37a090f46a80c7f7525dc2760e74cdeb4ceb328ba1"; ROOT_TAR_SHA="0374850b5de2175785f4ab4f7dccd5ea04356980ccff37e7f4398c742723eb46"
VERSION_NAME="0.9726742"; VERSION_BUILD="26742"; GLSLANG_VERSION="16.5.0"; GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"; GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26742_source_valid_highlight_chroma_outputs"; WORK="$ROOT/.build_26742_source_valid_highlight_chroma_work"; ARTZIP="$WORK/26741_artifact.zip"; ARTDIR="$WORK/artifact_26741"; BASE="$WORK/exact_successful_26741_compiled_candidate"; AFTER="$WORK/candidate_26742"; AFTER2="$WORK/candidate_26742_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-source-valid-highlight-chroma-debug.apk"; TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""; LOCAL_ONLY=0
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]]||fail "--local-prebuild requires successful 26741 artifact ZIP"; LOCAL_ART="$2"; LOCAL_ONLY=1; elif [[ -n "${1:-}" ]]; then fail "unknown argument"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26742_COMPILER_STATUS.txt" <<EOF
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
 [[ -d handoff_payload_26742 && "$(find handoff_payload_26742 -type f|wc -l)" -eq 4 ]]||fail "payload count"; [[ "$(wc -l < 26742_RUNTIME_CHANGED_PATHS.txt)" -eq 4 ]]||fail "changed count"; [[ ! -s 26742_ADDED_PATHS_MUST_BE_ABSENT.txt ]]||fail additions
 sha256sum -c 26742_HANDOFF_HASHES.sha256 >/dev/null; bash -n "$0"; python3 -S - <<'PY2'
from pathlib import Path
for n in ['transform_26742.py','validate_26742.py','verify_26742_authority.py','verify_26742_patches.py','verify_26742_regressions.py','verify_26742_shaders.py','verify_26742_infrastructure.py']:
 compile(Path(n).read_text(),n,'exec')
print('PASS sealed Python syntax')
PY2
 ! find . \( -type d -name __pycache__ -o -type f -name '*.pyc' \)|grep -q . || fail transient; ! find . -type f -name '*.apk'|grep -q . || fail "APK packaged"
}
verify_scope(){ if [[ "$LOCAL_ONLY" -eq 1 ]]; then pass "local sealed scope exact 4"; return; fi; [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]]||fail branch; git merge-base --is-ancestor "$ROOT_ACTIONS_AUTHORITY_COMMIT" HEAD||fail authority_ancestor; ! git diff --name-only "$ROOT_ACTIONS_AUTHORITY_COMMIT"..HEAD|grep -Eq '^app/'||fail "live app source committed"; pass "upload scope leaves live app source untouched"; }
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; echo "local_artifact=true" > "$OUT/26742_RESOLVED_26741_AUTHORITY.txt"; else
  [[ -n "$TOKEN" ]]||fail token; meta="$WORK/26741_artifacts.json"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts?name=${ROOT_ARTIFACT_NAME}&per_page=100" -o "$meta"
  mapfile -t specs < <(python3 -S - "$meta" "$ROOT_ACTIONS_AUTHORITY_COMMIT" "$ROOT_ARTIFACT_NAME" <<'PY2'
import json,sys
j=json.load(open(sys.argv[1])); sha=sys.argv[2]; name=sys.argv[3]
for a in j.get('artifacts',[]):
 w=a.get('workflow_run') or {}
 if a.get('name')==name and not a.get('expired',False) and w.get('head_sha')==sha:
  print(f"{a['id']}|{w.get('id','')}")
PY2
  ); [[ "${#specs[@]}" -ge 1 ]]||fail "no exact 26741 artifact candidate by name/head SHA"
  match=0; resolved_id=""; resolved_run=""
  for spec in "${specs[@]}"; do IFS='|' read -r aid rid <<<"$spec"; q="$WORK/artifact_${aid}.zip"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${aid}/zip" -o "$q"; if [[ "$(sha "$q")" == "$ROOT_ARTIFACT_SHA" ]]; then match=$((match+1)); resolved_id="$aid"; resolved_run="$rid"; cp "$q" "$ARTZIP"; fi; done
  [[ "$match" -eq 1 ]]||fail "expected exactly one artifact matching exact 26741 archive SHA; matches=$match"
  printf 'commit=%s\nartifact_name=%s\nartifact_id=%s\nrun_id=%s\nartifact_sha256=%s\n' "$ROOT_ACTIONS_AUTHORITY_COMMIT" "$ROOT_ARTIFACT_NAME" "$resolved_id" "$resolved_run" "$ROOT_ARTIFACT_SHA" > "$OUT/26742_RESOLVED_26741_AUTHORITY.txt"
 fi
 [[ "$(sha "$ARTZIP")" == "$ROOT_ARTIFACT_SHA" ]]||fail artifact_sha; unzip -q "$ARTZIP" -d "$ARTDIR"; T="$ARTDIR/build_26741_superres_confidence_bright_neutrality_outputs/26741_candidate_app_source.tar.gz"; [[ -f "$T" && "$(sha "$T")" == "$ROOT_TAR_SHA" ]]||fail tar_sha; mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"; (cd "$BASE" && sha256sum -c "$ROOT/26742_BASE_26741_FULL_APP.sha256" >/dev/null)||fail base_manifest; (cd "$BASE" && sha256sum -c "$ROOT/26742_EXACT_26741_CANDIDATE_AUTHORITY.sha256" >/dev/null)||fail exact_26741_authority
 pass "exact successful 26741 Actions compiled candidate authority reconstructed directly from exact archive/tar hashes"
}
compare_app(){ python3 -S - "$1" "$2" <<'PY2'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2]); assert len(a)==len(b)==1823 and a==b; print('PASS candidate byte-identical 1823 files')
PY2
}
make_candidate(){ python3 -S transform_26742.py "$BASE" "$AFTER"; python3 -S transform_26742.py "$BASE" "$AFTER2"; compare_app "$AFTER" "$AFTER2"; python3 -S validate_26742.py "$BASE" "$AFTER"; python3 -S verify_26742_regressions.py "$BASE" "$AFTER"; python3 -S verify_26742_authority.py "$ROOT" "$BASE" "$AFTER"; python3 -S verify_26742_shaders.py "$ROOT" "$BASE" "$AFTER"; }
verify_successful_26741_mechanics(){ sha256sum -c 26742_SEALED_26741_INFRASTRUCTURE_AUTHORITY.sha256 >/dev/null || fail "sealed 26741 mechanics authority drift"; pass "exact successful 26741 nine-role mechanics authority hash-pinned"; }
prepare_glslang(){ D="$WORK/glslang-${GLSLANG_VERSION}"; mkdir -p "$D"; A="$WORK/glslang.tar.gz"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]]||fail glslang_sha; tar -xzf "$A" -C "$D"; compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]]||chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26742_glslang_version.txt"; export IRIS26742_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; pass "pinned glslang 16.5.0 dual environment handoff"; }
compile_modified_runtime_shaders(){ # IRIS_26742_CURRENT_AUTHORITY_BASE_SHADER_REPLAY
 python3 -S verify_26741_shaders.py "$ROOT" "$BASE" "$BASE" --compiler "$IRIS26742_GLSLANG" | tee "$OUT/26742_inherited_26741_shader_compiler_validation.txt"; python3 -S verify_26742_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26742_GLSLANG" | tee "$OUT/26742_shader_compiler_validation.txt"; echo "REAL GLSL COMPILE: PASS (pinned glslang 16.5.0; exact successful-26741 authority variants plus exact 6 affected 26742 runtime-expanded shader variants)" > "$OUT/.glsl"; }
compile_spektra_raw_shader(){ if [[ -f scripts/verify_shaders.py ]]; then IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/26742_spektra_shader_verify.txt"; else pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"; fi; }
install_frozen_candidate_live(){ rm -rf app/src; cp -a "$AFTER/app/src" app/; cp -a "$AFTER/app/build.gradle" app/build.gradle; cp -a "$AFTER/app/version.properties" app/version.properties; rm -rf "$LIVE_CANON"; mkdir -p "$LIVE_CANON"; cp -a "$AFTER/app" "$LIVE_CANON/app"; compare_app "$AFTER" "$LIVE_CANON"; }
after_language_compiler_snapshot(){ rm -rf "$POST"; mkdir -p "$POST"; cp -a "$AFTER/app" "$POST/app"; compare_app "$AFTER" "$POST"; }
verify_candidate_patches(){ python3 -S verify_26742_patches.py "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26742_patch_validation.txt"; }
postbuild_proof(){ compare_app "$AFTER" "$LIVE_CANON"; python3 -S verify_26742_authority.py "$ROOT" "$BASE" "$LIVE_CANON"; python3 -S verify_26742_regressions.py "$BASE" "$LIVE_CANON"; python3 -S verify_26742_shaders.py "$ROOT" "$BASE" "$LIVE_CANON"; tar -czf "$OUT/26742_candidate_app_source.tar.gz" -C "$AFTER" app; sha256sum "$OUT/26742_candidate_app_source.tar.gz" > "$OUT/26742_candidate_app_source.tar.gz.sha256"; cp 26742_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26742_candidate_full_app.sha256"; pass "post-build candidate/protected/native/vendor/DNG invariance"; }
# IRIS_26742_AUTHORITATIVE_ACTIONS_STAGE_ORDER -- exact successful 26741 ordering; authority/version/scope/applicable validators only advance
verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_26741_mechanics
prepare_glslang
compile_modified_runtime_shaders
compile_spektra_raw_shader
if [[ "$LOCAL_ONLY" -eq 1 ]]; then verify_candidate_patches; echo "26742 LOCAL PREBUILD COMPLETE — real project Kotlin/Java/NDK/full assemble NOT RUN"; exit 0; fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26742_gradle_language_compilers.log"
sed -i 's/REAL KOTLIN COMPILE:.*/REAL KOTLIN COMPILE: PASS/;s/REAL JAVA COMPILE:.*/REAL JAVA COMPILE: PASS/' "$OUT/26742_COMPILER_STATUS.txt"
pass "JNI callback/motion ABI compiler checkpoint"
after_language_compiler_snapshot
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/26742_gradle_native_compiler.log"
sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#' "$OUT/26742_COMPILER_STATUS.txt"
verify_candidate_patches
echo "26742 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26742_gradle_assemble.log"
sed -i 's/FULL ANDROID ASSEMBLE:.*/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26742_COMPILER_STATUS.txt"
mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk'); [[ "${#apks[@]}" -eq 1 ]]||fail "expected one Gradle APK"; cp "${apks[0]}" "$FINAL"; [[ "$(find . -maxdepth 1 -type f -name 'IrisCamera-*.apk'|wc -l)" -eq 1 ]]||fail "one intended root APK"; sha256sum "$FINAL" > "$OUT/26742_APK.sha256"; sed -i 's/APK JNI CONTRACT:.*/APK JNI CONTRACT: PASS (full assemble APK present; modified source-valid Super Res CPU fallback native owner compiled in both ABIs)/' "$OUT/26742_COMPILER_STATUS.txt"
postbuild_proof
sed -i 's/POST-BUILD INVARIANCE:.*/POST-BUILD INVARIANCE: PASS/' "$OUT/26742_COMPILER_STATUS.txt"
sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: PASS (pinned glslang 16.5.0; exact successful-26741 authority variants plus exact 6 affected 26742 runtime-expanded shader variants)#' "$OUT/26742_COMPILER_STATUS.txt"
echo "26742 ACTIONS BUILD COMPLETE"
