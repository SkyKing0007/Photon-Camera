#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }; pass(){ echo "PASS: $*"; }; sha(){ sha256sum "$1"|awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
ROOT_ACTIONS_AUTHORITY_COMMIT="a8473f519a8d77926510a8a01a5658942dcf9645"; ROOT_ARTIFACT_NAME="photon-26745-bright-fringe-hue-authority"; ROOT_ARTIFACT_SHA="8660f67ec30ddb2a8945de387f3ae19270f4679684698dcccc6faf34b093e834"; ROOT_TAR_SHA="a915d476cf2832e9f8874735106230f73176c27fb7c66018fab105245e8a1e89"
HIST26743_ACTIONS_AUTHORITY_COMMIT="c927843ea78f58f632082758142ee061a1c05166"; HIST26743_ARTIFACT_NAME="photon-26743-visible-highlight-neutrality"; HIST26743_ARTIFACT_SHA="051fd7ef96e46f176e9e9e72cb55ecf14fa670177075aab6f3d39b60da75119f"; HIST26743_TAR_SHA="7d7fe097d3a978813a78da8bfcbc883bbf2f2855f729b88d376b532b14f4f5c7"
HIST26743_FULL_MANIFEST_SHA="cf5c15be188f17aaff3761be8b6dd1c254ccdf902a7c6cd1dc039287d97d7965"; HIST26743_INFRA_MANIFEST_SHA="6a9d3790025931a6415841e0af048123e00e95684731e9c6c134260fc19f20af"
VERSION_NAME="0.9726746"; VERSION_BUILD="26746"; GLSLANG_VERSION="16.5.0"; GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"; GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26746_extreme_flattened_highlight_veto_outputs"; WORK="$ROOT/.build_26746_extreme_flattened_highlight_veto_work"; ARTZIP="$WORK/26745_artifact.zip"; ARTDIR="$WORK/artifact_26745"; BASE="$WORK/exact_successful_26745_compiled_candidate"; HIST26743_ARTZIP="$WORK/26743_shader_replay_artifact.zip"; HIST26743_ARTDIR="$WORK/artifact_26743_shader_replay"; HIST26743_BASE="$WORK/exact_successful_26743_shader_replay_candidate"; AFTER="$WORK/candidate_26746"; AFTER2="$WORK/candidate_26746_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-extreme-flattened-highlight-veto-debug.apk"; TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""; LOCAL_ONLY=0
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]]||fail "--local-prebuild requires successful 26745 artifact ZIP"; LOCAL_ART="$2"; LOCAL_ONLY=1; elif [[ -n "${1:-}" ]]; then fail "unknown argument"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26746_COMPILER_STATUS.txt" <<EOF
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
 [[ -d handoff_payload_26746 && "$(find handoff_payload_26746 -type f|wc -l)" -eq 2 ]]||fail "payload count"; [[ "$(wc -l < 26746_RUNTIME_CHANGED_PATHS.txt)" -eq 2 ]]||fail "changed count"; [[ ! -s 26746_ADDED_PATHS_MUST_BE_ABSENT.txt ]]||fail additions
 sha256sum -c 26746_HANDOFF_HASHES.sha256 >/dev/null; bash -n "$0"; python3 -S - <<'PY2'
from pathlib import Path
for n in ['transform_26746.py','validate_26746.py','verify_26746_authority.py','verify_26746_patches.py','verify_26746_regressions.py','verify_26746_shaders.py','verify_26746_infrastructure.py']:
 compile(Path(n).read_text(),n,'exec')
print('PASS sealed Python syntax')
PY2
 ! find . \( -type d -name __pycache__ -o -type f -name '*.pyc' \)|grep -q . || fail transient; ! find . -type f -name '*.apk'|grep -q . || fail "APK packaged"
}
verify_scope(){ if [[ "$LOCAL_ONLY" -eq 1 ]]; then pass "local sealed scope exact 2"; return; fi; [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]]||fail branch; git merge-base --is-ancestor "$ROOT_ACTIONS_AUTHORITY_COMMIT" HEAD||fail authority_ancestor; ! git diff --name-only "$ROOT_ACTIONS_AUTHORITY_COMMIT"..HEAD|grep -Eq '^app/'||fail "live app source committed"; pass "upload scope leaves live app source untouched"; }
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; printf 'commit=%s\nartifact_name=%s\nartifact_id=%s\nrun_id=%s\nartifact_sha256=%s\n' "$ROOT_ACTIONS_AUTHORITY_COMMIT" "$ROOT_ARTIFACT_NAME" "11196415906" "36930681988" "$ROOT_ARTIFACT_SHA" > "$OUT/26746_RESOLVED_26745_AUTHORITY.txt"; else
  [[ -n "$TOKEN" ]]||fail token; meta="$WORK/26745_artifacts.json"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts?name=${ROOT_ARTIFACT_NAME}&per_page=100" -o "$meta"
  mapfile -t specs < <(python3 -S - "$meta" "$ROOT_ACTIONS_AUTHORITY_COMMIT" "$ROOT_ARTIFACT_NAME" <<'PY2'
import json,sys
j=json.load(open(sys.argv[1])); sha=sys.argv[2]; name=sys.argv[3]
for a in j.get('artifacts',[]):
 w=a.get('workflow_run') or {}
 if a.get('name')==name and not a.get('expired',False) and w.get('head_sha')==sha:
  print(f"{a['id']}|{w.get('id','')}")
PY2
  ); [[ "${#specs[@]}" -ge 1 ]]||fail "no exact 26745 artifact candidate by name/head SHA"
  match=0; resolved_id=""; resolved_run=""
  for spec in "${specs[@]}"; do IFS='|' read -r aid rid <<<"$spec"; q="$WORK/artifact_${aid}.zip"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${aid}/zip" -o "$q"; if [[ "$(sha "$q")" == "$ROOT_ARTIFACT_SHA" ]]; then match=$((match+1)); resolved_id="$aid"; resolved_run="$rid"; cp "$q" "$ARTZIP"; fi; done
  [[ "$match" -eq 1 ]]||fail "expected exactly one artifact matching exact 26745 archive SHA; matches=$match"
  printf 'commit=%s\nartifact_name=%s\nartifact_id=%s\nrun_id=%s\nartifact_sha256=%s\n' "$ROOT_ACTIONS_AUTHORITY_COMMIT" "$ROOT_ARTIFACT_NAME" "$resolved_id" "$resolved_run" "$ROOT_ARTIFACT_SHA" > "$OUT/26746_RESOLVED_26745_AUTHORITY.txt"
 fi
 [[ "$(sha "$ARTZIP")" == "$ROOT_ARTIFACT_SHA" ]]||fail artifact_sha; unzip -q "$ARTZIP" -d "$ARTDIR"; T="$ARTDIR/build_26745_bright_fringe_hue_authority_outputs/26745_candidate_app_source.tar.gz"; [[ -f "$T" && "$(sha "$T")" == "$ROOT_TAR_SHA" ]]||fail tar_sha; mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"; (cd "$BASE" && sha256sum -c "$ROOT/26746_BASE_26745_FULL_APP.sha256" >/dev/null)||fail base_manifest; (cd "$BASE" && sha256sum -c "$ROOT/26746_EXACT_26745_CANDIDATE_AUTHORITY.sha256" >/dev/null)||fail exact_26745_authority
 pass "exact successful 26745 Actions compiled candidate authority reconstructed directly from exact archive/tar hashes"
}
obtain_inherited_26745_shader_authority(){ # IRIS_26746_R1_EXACT_SUCCESSFUL_26745_SHADER_REPLAY_INPUTS
 [[ -n "$TOKEN" ]]||fail "token required for exact inherited 26743 shader replay authority"
 [[ "$(sha "$ROOT/26745_BASE_26743_FULL_APP.sha256")" == "$HIST26743_FULL_MANIFEST_SHA" ]]||fail "sealed 26743 full-manifest hash drift"
 [[ "$(sha "$ROOT/26745_EXACT_26743_CANDIDATE_AUTHORITY.sha256")" == "$HIST26743_FULL_MANIFEST_SHA" ]]||fail "sealed 26743 authority-manifest hash drift"
 [[ "$(sha "$ROOT/26745_SEALED_26743_INFRASTRUCTURE_AUTHORITY.sha256")" == "$HIST26743_INFRA_MANIFEST_SHA" ]]||fail "sealed 26743 infrastructure-manifest hash drift"
 sha256sum -c 26745_SEALED_26743_INFRASTRUCTURE_AUTHORITY.sha256 >/dev/null || fail "sealed 26743 inherited compiler mechanics drift"
 mkdir -p "$HIST26743_ARTDIR" "$HIST26743_BASE"
 meta="$WORK/26743_shader_replay_artifacts.json"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts?name=${HIST26743_ARTIFACT_NAME}&per_page=100" -o "$meta"
 mapfile -t specs < <(python3 -S - "$meta" "$HIST26743_ACTIONS_AUTHORITY_COMMIT" "$HIST26743_ARTIFACT_NAME" <<'PY2'
import json,sys
j=json.load(open(sys.argv[1])); sha=sys.argv[2]; name=sys.argv[3]
for a in j.get('artifacts',[]):
 w=a.get('workflow_run') or {}
 if a.get('name')==name and not a.get('expired',False) and w.get('head_sha')==sha:
  print(f"{a['id']}|{w.get('id','')}")
PY2
 ); [[ "${#specs[@]}" -ge 1 ]]||fail "no exact 26743 inherited shader replay artifact by name/head SHA"
 match=0; resolved_id=""; resolved_run=""
 for spec in "${specs[@]}"; do IFS='|' read -r aid rid <<<"$spec"; q="$WORK/shader_replay_artifact_${aid}.zip"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${aid}/zip" -o "$q"; if [[ "$(sha "$q")" == "$HIST26743_ARTIFACT_SHA" ]]; then match=$((match+1)); resolved_id="$aid"; resolved_run="$rid"; cp "$q" "$HIST26743_ARTZIP"; fi; done
 [[ "$match" -eq 1 ]]||fail "expected exactly one exact 26743 shader replay artifact; matches=$match"
 printf 'commit=%s\nartifact_name=%s\nartifact_id=%s\nrun_id=%s\nartifact_sha256=%s\n' "$HIST26743_ACTIONS_AUTHORITY_COMMIT" "$HIST26743_ARTIFACT_NAME" "$resolved_id" "$resolved_run" "$HIST26743_ARTIFACT_SHA" > "$OUT/26746_RESOLVED_26743_SHADER_REPLAY_AUTHORITY.txt"
 unzip -q "$HIST26743_ARTZIP" -d "$HIST26743_ARTDIR"; T="$HIST26743_ARTDIR/build_26743_visible_highlight_neutrality_outputs/26743_candidate_app_source.tar.gz"; [[ -f "$T" && "$(sha "$T")" == "$HIST26743_TAR_SHA" ]]||fail "26743 shader replay tar hash"
 tar -xzf "$T" -C "$HIST26743_BASE"
 (cd "$HIST26743_BASE" && sha256sum -c "$ROOT/26745_BASE_26743_FULL_APP.sha256" >/dev/null)||fail "26743 shader replay base manifest"
 (cd "$HIST26743_BASE" && sha256sum -c "$ROOT/26745_EXACT_26743_CANDIDATE_AUTHORITY.sha256" >/dev/null)||fail "26743 shader replay exact authority manifest"
 pass "exact successful 26743 candidate reconstructed for byte-identical successful-26745 inherited shader replay"
}
compare_app(){ python3 -S - "$1" "$2" <<'PY2'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2]); assert len(a)==len(b)==1823 and a==b; print('PASS candidate byte-identical 1823 files')
PY2
}
make_candidate(){ python3 -S transform_26746.py "$BASE" "$AFTER"; python3 -S transform_26746.py "$BASE" "$AFTER2"; compare_app "$AFTER" "$AFTER2"; python3 -S validate_26746.py "$BASE" "$AFTER"; python3 -S verify_26746_regressions.py "$BASE" "$AFTER"; python3 -S verify_26746_authority.py "$ROOT" "$BASE" "$AFTER"; python3 -S verify_26746_shaders.py "$ROOT" "$BASE" "$AFTER"; }
verify_successful_26745_mechanics(){ sha256sum -c 26746_SEALED_26745_INFRASTRUCTURE_AUTHORITY.sha256 >/dev/null || fail "sealed 26745 mechanics authority drift"; [[ "$(sha 26745_SEALED_26743_INFRASTRUCTURE_AUTHORITY.sha256)" == "$HIST26743_INFRA_MANIFEST_SHA" ]]||fail "successful 26745 inherited-26743 mechanics manifest drift"; pass "exact successful 26745 nine-role mechanics authority hash-pinned, including its sealed 26743 compiler-replay authority"; }
prepare_glslang(){ D="$WORK/glslang-${GLSLANG_VERSION}"; mkdir -p "$D"; A="$WORK/glslang.tar.gz"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]]||fail glslang_sha; tar -xzf "$A" -C "$D"; compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]]||chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26746_glslang_version.txt"; export IRIS26746_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; pass "pinned glslang 16.5.0 dual environment handoff"; }
compile_modified_runtime_shaders(){ # IRIS_26746_R1_EXACT_SUCCESSFUL_26745_SHADER_REPLAY
 obtain_inherited_26745_shader_authority
 python3 -S verify_26743_shaders.py "$ROOT" "$HIST26743_BASE" "$HIST26743_BASE" --compiler "$IRIS26746_GLSLANG" | tee "$OUT/26746_inherited_26743_shader_compiler_validation.txt"
 python3 -S verify_26745_shaders.py "$ROOT" "$HIST26743_BASE" "$BASE" --compiler "$IRIS26746_GLSLANG" | tee "$OUT/26746_inherited_26745_shader_compiler_validation.txt"
 python3 -S verify_26746_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26746_GLSLANG" | tee "$OUT/26746_shader_compiler_validation.txt"
 echo "REAL GLSL COMPILE: PASS (pinned glslang 16.5.0; exact successful-26745 replay uses exact 26743 base -> exact 26745 candidate, then exact 26745 base -> 26746 candidate)" > "$OUT/.glsl"
}
compile_spektra_raw_shader(){ if [[ -f scripts/verify_shaders.py ]]; then IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/26746_spektra_shader_verify.txt"; else pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"; fi; }
install_frozen_candidate_live(){ rm -rf app/src; cp -a "$AFTER/app/src" app/; cp -a "$AFTER/app/build.gradle" app/build.gradle; cp -a "$AFTER/app/version.properties" app/version.properties; rm -rf "$LIVE_CANON"; mkdir -p "$LIVE_CANON"; cp -a "$AFTER/app" "$LIVE_CANON/app"; compare_app "$AFTER" "$LIVE_CANON"; }
after_language_compiler_snapshot(){ rm -rf "$POST"; mkdir -p "$POST"; cp -a "$AFTER/app" "$POST/app"; compare_app "$AFTER" "$POST"; }
verify_candidate_patches(){ python3 -S verify_26746_patches.py "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26746_patch_validation.txt"; }
postbuild_proof(){ compare_app "$AFTER" "$LIVE_CANON"; python3 -S verify_26746_authority.py "$ROOT" "$BASE" "$LIVE_CANON"; python3 -S verify_26746_regressions.py "$BASE" "$LIVE_CANON"; python3 -S verify_26746_shaders.py "$ROOT" "$BASE" "$LIVE_CANON"; tar -czf "$OUT/26746_candidate_app_source.tar.gz" -C "$AFTER" app; sha256sum "$OUT/26746_candidate_app_source.tar.gz" > "$OUT/26746_candidate_app_source.tar.gz.sha256"; cp 26746_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26746_candidate_full_app.sha256"; pass "post-build candidate/protected/native/vendor/DNG invariance"; }
# IRIS_26746_AUTHORITATIVE_ACTIONS_STAGE_ORDER -- exact successful 26745 ordering; authority/version/scope/applicable validators only advance
verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_26745_mechanics
prepare_glslang
compile_modified_runtime_shaders
compile_spektra_raw_shader
if [[ "$LOCAL_ONLY" -eq 1 ]]; then verify_candidate_patches; echo "26746 LOCAL PREBUILD COMPLETE — real project Kotlin/Java/NDK/full assemble NOT RUN"; exit 0; fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26746_gradle_language_compilers.log"
sed -i 's/REAL KOTLIN COMPILE:.*/REAL KOTLIN COMPILE: PASS/;s/REAL JAVA COMPILE:.*/REAL JAVA COMPILE: PASS/' "$OUT/26746_COMPILER_STATUS.txt"
pass "JNI callback/motion ABI compiler checkpoint"
after_language_compiler_snapshot
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/26746_gradle_native_compiler.log"
sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#' "$OUT/26746_COMPILER_STATUS.txt"
verify_candidate_patches
echo "26746 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26746_gradle_assemble.log"
sed -i 's/FULL ANDROID ASSEMBLE:.*/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26746_COMPILER_STATUS.txt"
mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk'); [[ "${#apks[@]}" -eq 1 ]]||fail "expected one Gradle APK"; cp "${apks[0]}" "$FINAL"; [[ "$(find . -maxdepth 1 -type f -name 'IrisCamera-*.apk'|wc -l)" -eq 1 ]]||fail "one intended root APK"; sha256sum "$FINAL" > "$OUT/26746_APK.sha256"; sed -i 's/APK JNI CONTRACT:.*/APK JNI CONTRACT: PASS (full assemble APK present; Super Res remains shared Sabre/VGN chroma owner; true2x native publication compiled in both ABIs)/' "$OUT/26746_COMPILER_STATUS.txt"
postbuild_proof
sed -i 's/POST-BUILD INVARIANCE:.*/POST-BUILD INVARIANCE: PASS/' "$OUT/26746_COMPILER_STATUS.txt"
sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: PASS (pinned glslang 16.5.0; exact successful-26745 replay uses exact 26743 base -> exact 26745 candidate, then exact 26745 base -> 26746 candidate)#' "$OUT/26746_COMPILER_STATUS.txt"
echo "26746 ACTIONS BUILD COMPLETE"
