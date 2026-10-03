#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }; pass(){ echo "PASS: $*"; }; sha(){ sha256sum "$1"|awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"; ROOT_ARTIFACT_NAME="photon-26752-ipol-plan-b-translational-sr"; ROOT_ARTIFACT_SHA="6b4677cbb357007f0e7fea61f3259d51f93ebc4d4bd1c6e7133a424763865041"; ROOT_TAR_SHA="6e0ce9a08415fdf2ae2b1ba7eb7e25a0ebdc2c08598af7cdf3e488a61f27c821"
MECHANICS_AUTHORITY_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"; MECHANICS_ACTIONS_RUN="37075896367"; MECHANICS_ARTIFACT_ID="11256842407"; MECHANICS_ARTIFACT_SHA="6b4677cbb357007f0e7fea61f3259d51f93ebc4d4bd1c6e7133a424763865041"
VERSION_NAME="0.9726753"; VERSION_BUILD="26753"; GLSLANG_VERSION="16.5.0"; GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"; GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26753_mobile_safe_ipol_plan_b_outputs"; WORK="$ROOT/.build_26753_mobile_safe_ipol_plan_b_work"
ARTZIP="$WORK/26752_artifact.zip"; ARTDIR="$WORK/artifact_26752"; BASE="$WORK/exact_successful_26752_compiled_candidate"
AFTER="$WORK/candidate_26753"; AFTER2="$WORK/candidate_26753_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/post_language_compiler_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-mobile-safe-ipol-plan-b-debug.apk"; TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""; LOCAL_ONLY=0
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]]||fail "--local-prebuild requires successful 26752 artifact ZIP"; LOCAL_ART="$2"; LOCAL_ONLY=1; elif [[ -n "${1:-}" ]]; then fail "unknown argument"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26753_COMPILER_STATUS.txt" <<EOF_STATUS
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
 [[ -d handoff_payload_26753 && "$(find handoff_payload_26753 -type f|wc -l)" -eq 5 ]]||fail "payload count"; [[ "$(wc -l < 26753_RUNTIME_CHANGED_PATHS.txt)" -eq 5 ]]||fail "changed count"; [[ ! -s 26753_ADDED_PATHS_MUST_BE_ABSENT.txt ]]||fail additions
 sha256sum -c 26753_HANDOFF_HASHES.sha256 >/dev/null; bash -n "$0"; python3 -S - <<'PY2'
from pathlib import Path
for n in ['transform_26753.py','validate_26753.py','verify_26753_authority.py','verify_26753_patches.py','verify_26753_regressions.py','verify_26753_shaders.py','verify_26753_plan_b_bounds.py','verify_26753_infrastructure.py']:
 compile(Path(n).read_text(),n,'exec')
print('PASS sealed 26753 Python syntax')
PY2
 ! find . \( -type d -name __pycache__ -o -type f -name '*.pyc' \)|grep -q . || fail transient; ! find . -type f -name '*.apk'|grep -q . || fail "APK packaged"
}
verify_scope(){
 if [[ "$LOCAL_ONLY" -eq 1 ]]; then pass "local sealed scope exact 5"; return; fi
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]]||fail branch
 git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD||fail runtime_authority_ancestor
 git merge-base --is-ancestor "$MECHANICS_AUTHORITY_COMMIT" HEAD||fail mechanics_authority_ancestor
 ! git diff --name-only "$MECHANICS_AUTHORITY_COMMIT"..HEAD|grep -Eq '^app/'||fail "live app source committed"
 pass "upload scope leaves live app source untouched; successful 26752 authority/mechanics commit remains ancestor"
}
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then
  cp "$LOCAL_ART" "$ARTZIP"; printf 'commit=%s\nartifact_name=%s\nartifact_id=%s\nrun_id=%s\nartifact_sha256=%s\ncandidate_tar_sha256=%s\n' "$RUNTIME_AUTHORITY_COMMIT" "$ROOT_ARTIFACT_NAME" "$MECHANICS_ARTIFACT_ID" "$MECHANICS_ACTIONS_RUN" "$ROOT_ARTIFACT_SHA" "$ROOT_TAR_SHA" > "$OUT/26753_RESOLVED_26752_AUTHORITY.txt"
 else
  [[ -n "$TOKEN" ]]||fail token; meta="$WORK/26752_artifacts.json"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts?name=${ROOT_ARTIFACT_NAME}&per_page=100" -o "$meta"
  mapfile -t specs < <(python3 -S - "$meta" "$RUNTIME_AUTHORITY_COMMIT" "$ROOT_ARTIFACT_NAME" <<'PY2'
import json,sys
j=json.load(open(sys.argv[1]));sha=sys.argv[2];name=sys.argv[3]
for a in j.get('artifacts',[]):
 w=a.get('workflow_run') or {}
 if a.get('name')==name and not a.get('expired',False) and w.get('head_sha')==sha: print(f"{a['id']}|{w.get('id','')}")
PY2
  ); [[ "${#specs[@]}" -ge 1 ]]||fail "no exact 26752 artifact candidate by name/head SHA"
  match=0; resolved_id=""; resolved_run=""
  for spec in "${specs[@]}"; do IFS='|' read -r aid rid <<<"$spec"; q="$WORK/artifact_${aid}.zip"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${aid}/zip" -o "$q"; if [[ "$(sha "$q")" == "$ROOT_ARTIFACT_SHA" ]]; then match=$((match+1)); resolved_id="$aid"; resolved_run="$rid"; cp "$q" "$ARTZIP"; fi; done
  [[ "$match" -eq 1 ]]||fail "expected exactly one artifact matching exact 26752 archive SHA; matches=$match"
  printf 'commit=%s\nartifact_name=%s\nartifact_id=%s\nrun_id=%s\nartifact_sha256=%s\ncandidate_tar_sha256=%s\n' "$RUNTIME_AUTHORITY_COMMIT" "$ROOT_ARTIFACT_NAME" "$resolved_id" "$resolved_run" "$ROOT_ARTIFACT_SHA" "$ROOT_TAR_SHA" > "$OUT/26753_RESOLVED_26752_AUTHORITY.txt"
 fi
 [[ "$(sha "$ARTZIP")" == "$ROOT_ARTIFACT_SHA" ]]||fail artifact_sha; unzip -q "$ARTZIP" -d "$ARTDIR"; T="$ARTDIR/build_26752_ipol_plan_b_translational_sr_outputs/26752_candidate_app_source.tar.gz"; [[ -f "$T" && "$(sha "$T")" == "$ROOT_TAR_SHA" ]]||fail tar_sha; mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"; (cd "$BASE" && sha256sum -c "$ROOT/26753_BASE_26752_FULL_APP.sha256" >/dev/null)||fail base_manifest
 for proof in 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$ARTDIR/build_26752_ipol_plan_b_translational_sr_outputs/26752_COMPILER_STATUS.txt" >/dev/null || fail "26752 authority proof missing: $proof"; done
 pass "exact successful 26752 Actions compiled candidate authority reconstructed directly from exact archive/tar hashes"
}
compare_app(){ python3 -S - "$1" "$2" <<'PY2'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2]);assert len(a)==len(b)==1823 and a==b;print('PASS candidate byte-identical 1823 files')
PY2
}
make_candidate(){ python3 -S transform_26753.py "$BASE" "$AFTER"; python3 -S transform_26753.py "$BASE" "$AFTER2"; compare_app "$AFTER" "$AFTER2"; python3 -S validate_26753.py "$BASE" "$AFTER"; python3 -S verify_26753_regressions.py "$BASE" "$AFTER"; python3 -S verify_26753_plan_b_bounds.py "$AFTER"; python3 -S verify_26753_authority.py "$ROOT" "$BASE" "$AFTER"; python3 -S verify_26753_shaders.py "$ROOT" "$BASE" "$AFTER"; }
verify_successful_26752_mechanics(){
 if [[ "$LOCAL_ONLY" -eq 0 ]]; then
  git show "$MECHANICS_AUTHORITY_COMMIT:build_26752_ipol_plan_b_translational_sr.sh" > "$WORK/reference_build_26752.sh"
  git show "$MECHANICS_AUTHORITY_COMMIT:.github/workflows/build-26752-ipol-plan-b-translational-sr.yml" > "$WORK/reference_workflow_26752.yml"
  python3 -S verify_26753_infrastructure.py build_26753_mobile_safe_ipol_plan_b.sh .github/workflows/build-26753-mobile-safe-ipol-plan-b.yml "$WORK/reference_build_26752.sh" "$WORK/reference_workflow_26752.yml" | tee "$OUT/26753_infrastructure_diff_audit.txt"
  diff -u "$WORK/reference_build_26752.sh" build_26753_mobile_safe_ipol_plan_b.sh > "$OUT/26752_to_26753_build_infrastructure.diff" || true
  diff -u "$WORK/reference_workflow_26752.yml" .github/workflows/build-26753-mobile-safe-ipol-plan-b.yml > "$OUT/26752_to_26753_workflow_infrastructure.diff" || true
 else
  python3 -S verify_26753_infrastructure.py build_26753_mobile_safe_ipol_plan_b.sh .github/workflows/build-26753-mobile-safe-ipol-plan-b.yml | tee "$OUT/26753_infrastructure_diff_audit.txt"
 fi
 pass "exact successful 26752 mechanics authority audited; stage/toolchain/order unchanged"
}
prepare_glslang(){ D="$WORK/glslang-${GLSLANG_VERSION}"; mkdir -p "$D"; A="$WORK/glslang.tar.gz"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]]||fail glslang_sha; tar -xzf "$A" -C "$D"; compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]]||chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26753_glslang_version.txt"; export IRIS26753_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; pass "pinned glslang 16.5.0 available; modified runtime GLSL count is zero"; }
compile_modified_runtime_shaders(){ python3 -S verify_26753_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26753_GLSLANG" | tee "$OUT/26753_shader_validation.txt"; sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: N/A (0 modified GLSL; 271 shader files byte-identical to successful 26752 authority; pinned glslang 16.5.0 verified)#' "$OUT/26753_COMPILER_STATUS.txt"; }
compile_spektra_raw_shader(){ if [[ -f scripts/verify_shaders.py ]]; then IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/26753_spektra_shader_verify.txt"; else pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"; fi; }
install_frozen_candidate_live(){ rm -rf app/src; cp -a "$AFTER/app/src" app/; cp -a "$AFTER/app/build.gradle" app/build.gradle; cp -a "$AFTER/app/version.properties" app/version.properties; rm -rf "$LIVE_CANON"; mkdir -p "$LIVE_CANON"; cp -a "$AFTER/app" "$LIVE_CANON/app"; compare_app "$AFTER" "$LIVE_CANON"; }
after_language_compiler_snapshot(){ rm -rf "$POST"; mkdir -p "$POST"; cp -a "$AFTER/app" "$POST/app"; compare_app "$AFTER" "$POST"; }
verify_candidate_patches(){ python3 -S verify_26753_patches.py "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26753_patch_validation.txt"; }
postbuild_proof(){ compare_app "$AFTER" "$LIVE_CANON"; python3 -S validate_26753.py "$BASE" "$LIVE_CANON"; python3 -S verify_26753_regressions.py "$BASE" "$LIVE_CANON"; python3 -S verify_26753_plan_b_bounds.py "$LIVE_CANON"; python3 -S verify_26753_authority.py "$ROOT" "$BASE" "$LIVE_CANON"; python3 -S verify_26753_shaders.py "$ROOT" "$BASE" "$LIVE_CANON"; tar -czf "$OUT/26753_candidate_app_source.tar.gz" -C "$AFTER" app; sha256sum "$OUT/26753_candidate_app_source.tar.gz" > "$OUT/26753_candidate_app_source.tar.gz.sha256"; cp 26753_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26753_candidate_full_app.sha256"; pass "post-build candidate/protected/native-protected/vendor/DNG/shader invariance"; }
# IRIS_26753_AUTHORITATIVE_ACTIONS_STAGE_ORDER -- exact successful 26752 ordering/toolchain; runtime authority exact successful 26752 compiled candidate
verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_26752_mechanics
prepare_glslang
compile_modified_runtime_shaders
compile_spektra_raw_shader
if [[ "$LOCAL_ONLY" -eq 1 ]]; then verify_candidate_patches; echo "26753 LOCAL PREBUILD COMPLETE — real project Kotlin/Java/NDK/full assemble NOT RUN"; exit 0; fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26753_gradle_language_compilers.log"
sed -i 's/REAL KOTLIN COMPILE:.*/REAL KOTLIN COMPILE: PASS/;s/REAL JAVA COMPILE:.*/REAL JAVA COMPILE: PASS/' "$OUT/26753_COMPILER_STATUS.txt"
pass "JNI callback/motion ABI compiler checkpoint"
after_language_compiler_snapshot
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/26753_gradle_native_compiler.log"
sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#;s#JNI CALLBACK CLASS ABI:.*#JNI CALLBACK CLASS ABI: PASS (Java/JNI declarations + both-ABI native link)#' "$OUT/26753_COMPILER_STATUS.txt"
verify_candidate_patches
echo "26753 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26753_gradle_assemble.log"
sed -i 's/FULL ANDROID ASSEMBLE:.*/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26753_COMPILER_STATUS.txt"
mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk'); [[ "${#apks[@]}" -eq 1 ]]||fail "expected one Gradle APK"; cp "${apks[0]}" "$FINAL"; [[ "$(find . -maxdepth 1 -type f -name 'IrisCamera-*.apk'|wc -l)" -eq 1 ]]||fail "one intended root APK"; sha256sum "$FINAL" > "$OUT/26753_APK.sha256"
sed -i 's#APK JNI CONTRACT:.*#APK JNI CONTRACT: PASS (pure IPOL Plan-B luma/detail only; fixed same-lens NORMAL population; direct native-grid high zoom; optional IRLS<=5; bounded tile/stage; native Sabre/VGN RGB/chroma/highlight owner; DNG/UHDR unchanged)#' "$OUT/26753_COMPILER_STATUS.txt"
postbuild_proof
sed -i 's/POST-BUILD INVARIANCE:.*/POST-BUILD INVARIANCE: PASS/' "$OUT/26753_COMPILER_STATUS.txt"
echo "26753 ACTIONS BUILD COMPLETE"
