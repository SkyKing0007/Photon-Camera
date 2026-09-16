#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
resolve_glslang_compiler(){
  local root="$1" compiler="" compat=""
  compiler="$(find "$root" -type f -name glslang -print -quit)"
  if [[ -z "$compiler" ]]; then
    compat="$(find "$root" \( -type f -o -type l \) -name glslangValidator -print -quit)"
    if [[ -n "$compat" ]]; then compiler="$(readlink -f "$compat" 2>/dev/null || true)"; fi
  fi
  [[ -n "$compiler" && -f "$compiler" ]] || return 1
  printf '%s\n' "$compiler"
}
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_PARENT_COMMIT="fd0e9f9de32f976c6dcf7f3449f02d3c457354d2"
RUNTIME_AUTHORITY_COMMIT="3b46a176d4d018613b17912bce30ebdb6e2fd7e7"
BASE_RUN_ID="35053661730"
BASE_ARTIFACT_ID="10429479923"
BASE_ARTIFACT_NAME="photon-26648-r1-2-universal-fusion-heic-ui"
BASE_ARTIFACT_SHA="3d88827bcd17f5361e32b448519f77fbb9b140afd6b21bafeb37deb814a5ce17"
BASE_TAR_SHA="5b4bbc97b0958e7bcf68bfb39651fee051271610ffc69d8d8692eb664c1f46ca"
VERSION_NAME="0.9726649"; VERSION_BUILD="26649"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
AUTH_R1_2_BUILD_SCRIPT_BLOB="940320d3b7b6d60cdb9bb8f0f2e9dc61b7d932f7"
AUTH_R1_2_WORKFLOW_BLOB="ef04fa514a63464d71cc4db630dcf72c8f040283"
HANDOFF="$ROOT/R1_26649_HANDOFF_HASHES.sha256"; REPAIR_HANDOFF="$ROOT/R1_1_26649_HANDOFF_HASHES.sha256"; UPLOADS="$ROOT/R1_1_26649_UPLOAD_PATHS.txt"
BASE_FULL="$ROOT/R1_26649_BASE_26648_R1_2_FULL_APP.sha256"; CAND_FULL="$ROOT/R1_26649_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/R1_26649_PROTECTED_UNCHANGED_BASE.sha256"; CAND_PROTECTED="$ROOT/R1_26649_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/R1_26649_NATIVE_PROTECTED_BASE.sha256"; CAND_NATIVE="$ROOT/R1_26649_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/R1_26649_VENDOR_PROTECTED_BASE.sha256"; CAND_VENDOR="$ROOT/R1_26649_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/R1_26649_DNG_BASE.sha256"; CAND_DNG="$ROOT/R1_26649_DNG_CANDIDATE.sha256"
SHADER_BASE="$ROOT/R1_26649_SHADER_UNIVERSE_BASE.sha256"; SHADER_CAND="$ROOT/R1_26649_SHADER_UNIVERSE_CANDIDATE.sha256"
CHANGED="$ROOT/R1_26649_RUNTIME_CHANGED_PATHS.txt"; PREWRITE="$ROOT/R1_26649_PREWRITE_SOURCE_HASHES.sha256"; ADDED="$ROOT/R1_26649_ADDED_PATHS_MUST_BE_ABSENT.txt"; EXPECTED_CHANGED="$ROOT/R1_26649_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/R1_26649_RUNTIME_DELTA_FROM_26648_R1_2.patch"; ROLLBACK="$ROOT/R1_26649_RUNTIME_ROLLBACK_TO_26648_R1_2.patch"; SHADER_PIN="$ROOT/R1_1_26649_RUNTIME_EXPANDED_SHADERS.sha256"
TRANSFORM="$ROOT/transform_26649.py"; VALIDATE="$ROOT/validate_26649.py"; AUTHORITY="$ROOT/verify_26649_authority.py"; INFRA="$ROOT/verify_r1_1_26649_infrastructure.py"; PATCHVERIFY="$ROOT/verify_26649_patches.py"; SHADERVERIFY="$ROOT/verify_r1_1_26649_shaders.py"; GATEVERIFY="$ROOT/verify_26649_regressions.py"
BUILD_SCRIPT="$ROOT/build_r1_1_26649_glsl_expansion_repair.sh"; WORKFLOW="$ROOT/.github/workflows/build-26649-r1-1-glsl-expansion-repair.yml"
OUT="$ROOT/build_r1_1_26649_glsl_expansion_repair_outputs"; WORK="$ROOT/.build_r1_1_26649_glsl_expansion_repair_work"
ARTZIP="$WORK/26648_r1_2_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_successful_26648_r1_2_compiled_candidate"; AFTER="$WORK/candidate_26649_r1"; AFTER2="$WORK/candidate_26649_r1_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; GLSLANG_DIR="$WORK/glslang-${GLSLANG_VERSION}"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r1-1-photon-highlight-compression-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then
  [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26648 R1.2 artifact ZIP"
  LOCAL_ART="$2"
elif [[ -n "${1:-}" ]]; then fail "unknown argument: $1"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26649_R1_1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26649_R1_1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME AUTHORITY: NOT RUN
VERIFICATION MECHANICS AUTHORITY: NOT RUN
BACKUP STATUS: PASS (no backup created/requested)
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE DELTA AUDIT: NOT RUN
PHOTON HIGHLIGHT COMPRESSION PARITY: NOT RUN
UNIVERSAL HIGHLIGHT PRESERVATION: NOT RUN
OLD BRIGHT-BASE LIFT RETIRED: NOT RUN
COLOR/TONE OUTSIDE HIGHLIGHT OWNER: NOT RUN
SHORT/FUSION AUTHORITY INVARIANCE: NOT RUN
JPEG UHDR INVARIANCE: NOT RUN
HEIC INVARIANCE: NOT RUN
BASE/CANDIDATE MANIFEST COMPLETENESS: NOT RUN
PROTECTED/DNG/NATIVE/VENDOR INVARIANCE: NOT RUN
RUNTIME-EXPANDED GLSL RESERVED SCAN: NOT RUN
REAL GLSL COMPILE: NOT RUN
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
REAL NATIVE/NDK COMPILE: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
PRE-BUILD SAFETY PROOF: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
EXACTLY ONE APK: NOT RUN
POST-BUILD INVARIANCE: NOT RUN
CLEAN ARTIFACT SOURCE EXPORT: NOT RUN
TARGET VERSION/BUILD: 0.9726649 / 26649
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26649_R1_1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26649_R1_1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26649_R1_1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26649_R1_1_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){ local authority_root="$1" live_root="$2" dest_root="$3"; rm -rf "$dest_root"; mkdir -p "$dest_root"; cp -a "$authority_root/." "$dest_root/"; rm -rf "$dest_root/app/src"; cp -a "$live_root/app/src" "$dest_root/app/"; cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"; cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"; }
compare_app_trees(){ python3 -S - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a=H(sys.argv[1]); b=H(sys.argv[2]); assert len(a)==1720 and a==b,(len(a),len(b),sorted(set(a)^set(b))[:10]); print('PASS authority-seeded candidate byte-identical: 1720 files')
PY
}
verify_package(){
  [[ -f "$HANDOFF" && -f "$UPLOADS" && -d "$ROOT/handoff_payload_26649" ]] || fail "sealed 26649 package incomplete"
  [[ "$(find "$ROOT/handoff_payload_26649" -type f | wc -l)" -eq 5 ]] || fail "sealed runtime payload must contain exactly 5 files"
  [[ "$(wc -l < "$CHANGED")" -eq 5 && "$(wc -l < "$ADDED")" -eq 0 ]] || fail "26649 changed/add counts"
  sha256sum -c "$HANDOFF" >/dev/null
  sha256sum -c "$REPAIR_HANDOFF" >/dev/null
  [[ "$(wc -l < "$BASE_FULL")" -eq 1720 && "$(wc -l < "$CAND_FULL")" -eq 1720 ]] || fail "full app count"
  [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1715 && "$(wc -l < "$BASE_NATIVE")" -eq 807 && "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$BASE_DNG")" -eq 7 ]] || fail "protected manifest counts"
  [[ "$(wc -l < "$SHADER_BASE")" -eq 257 && "$(wc -l < "$SHADER_CAND")" -eq 257 && "$(wc -l < "$SHADER_PIN")" -eq 3 ]] || fail "shader manifest counts"
  cmp "$BASE_PROTECTED" "$CAND_PROTECTED"; cmp "$BASE_NATIVE" "$CAND_NATIVE"; cmp "$BASE_VENDOR" "$CAND_VENDOR"; cmp "$BASE_DNG" "$CAND_DNG"
  bash -n "$BUILD_SCRIPT"
  python3 -S - "$TRANSFORM" "$VALIDATE" "$AUTHORITY" "$INFRA" "$PATCHVERIFY" "$SHADERVERIFY" "$GATEVERIFY" <<'PY'
import ast,sys
from pathlib import Path
allowed=set(sys.stdlib_module_names)
for raw in sys.argv[1:]:
 p=Path(raw); src=p.read_text(); tree=ast.parse(src,filename=str(p)); bad=[]
 for n in ast.walk(tree):
  names=[]
  if isinstance(n,ast.Import): names=[a.name.split('.',1)[0] for a in n.names]
  elif isinstance(n,ast.ImportFrom) and n.module: names=[n.module.split('.',1)[0]]
  bad += [x for x in names if x not in allowed]
 if bad: raise SystemExit(f'FAIL non-stdlib dependency {p.name}: {sorted(set(bad))}')
 compile(src,str(p),'exec')
print('PASS sealed Python stdlib-only syntax/import gate')
PY
}
verify_scope(){
  if [[ -n "$LOCAL_ART" ]]; then set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed 26649 candidate; exactly 5 runtime changed / 0 added from exact successful 26648 R1.2 candidate)"; return; fi
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  [[ "$(git rev-parse HEAD^)" == "$EXPECTED_PARENT_COMMIT" ]] || fail "26649 R1.1 repair parent must be exact failed 26649 R1 commit"
  git diff --name-only "$EXPECTED_PARENT_COMMIT"..HEAD | sort > "$WORK/actual_upload_scope.txt"
  sort "$UPLOADS" > "$WORK/expected_upload_scope.txt"
  diff -u "$WORK/expected_upload_scope.txt" "$WORK/actual_upload_scope.txt" || fail "26649 upload scope mismatch"
  ! grep -Eq '^app/' "$WORK/actual_upload_scope.txt" || fail "26649 handoff contains live app source"
  set_report "CHANGED RUNTIME SCOPE" "PASS (candidate-only exact allowlist: 5 runtime changed / 0 added; live repository app source untouched before guarded install)"
}
obtain_authority(){
  if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else
    [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
    curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
  fi
  [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "successful 26648 R1.2 artifact ZIP SHA"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  local tarball="$ARTDIR/build_r1_2_26648_universal_fusion_heic_ui_outputs/26648_R1_2_candidate_app_source.tar.gz"
  [[ -f "$tarball" && "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "successful 26648 R1.2 compiled candidate TAR authority"
  tar -xzf "$tarball" -C "$BASE"
  (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null) || fail "26648 R1.2 exact base manifest"
  set_report "RUNTIME AUTHORITY" "PASS (successful 26648 R1.2 commit ${RUNTIME_AUTHORITY_COMMIT}/run ${BASE_RUN_ID}/artifact ${BASE_ARTIFACT_ID}/artifact SHA ${BASE_ARTIFACT_SHA}/compiled candidate TAR ${BASE_TAR_SHA})"
}
make_candidate(){
  python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26649_transform.txt"
  python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26649_transform_replay.txt"
  compare_app_trees "$AFTER" "$AFTER2"
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; cmp "$ROOT/handoff_payload_26649/$rel" "$AFTER/$rel" || fail "sealed payload differs frozen candidate: $rel"; done < "$CHANGED"
  python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26649_semantic_validation.txt"
  python3 -S "$GATEVERIFY" "$BASE" "$AFTER" | tee "$OUT/26649_regressions.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26649_authority_candidate.txt"
  set_report "PHOTON HIGHLIGHT COMPRESSION PARITY" "PASS (Photon knee law 0.90->0.55 at clippedFraction/ref=0.10 and exact quadratic shoulder reproduced; identity below knee; 1.0 remains 1.0)"
  set_report "UNIVERSAL HIGHLIGHT PRESERVATION" "PASS (one scene-wide scalar shoulder applies to all upper-range content before Local Laplacian; no object/texture/edge semantic eligibility)"
  set_report "OLD BRIGHT-BASE LIFT RETIRED" "PASS (26635 smooth bright-base lift and 0.78 small-residual suppression removed from the post-Local-Laplacian recombination owner)"
  set_report "COLOR/TONE OUTSIDE HIGHLIGHT OWNER" "PASS (existing exposure/26623 tone decision, ACR/color matrices, saturation and shadow owners protected; Photon shoulder identity below adaptive knee)"
  set_report "SHORT/FUSION AUTHORITY INVARIANCE" "PASS (26648 NORMAL+SHORT fusion, alignment, temporal/SR-detail/DNG isolation byte-identical)"
  set_report "JPEG UHDR INVARIANCE" "PASS (JPEG Ultra HDR encoder/gain-map owner byte-identical; completed SDR appearance changes only through common 26649 highlight presentation)"
  set_report "HEIC INVARIANCE" "PASS (HEIC Java/native/hardware/container files byte-identical; HEIC no-pop work intentionally deferred)"
  set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (1720 base / 1720 candidate / 1715 protected / 807 native / 778 vendor / 7 DNG / 257 shader universe; exactly 5 runtime changes)"
  set_report "PROTECTED/DNG/NATIVE/VENDOR INVARIANCE" "PASS"
}
verify_shaders(){
  if [[ -n "$LOCAL_ART" ]]; then
    python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26649_shader_validation.txt"
    set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (3 exact modified runtime-expanded asset shaders; complete 257-file shader universe pinned)"
    set_report "REAL GLSL COMPILE" "NOT RUN locally (Actions required; pinned 16.5.0 gate packaged)"
    set_compiler "REAL GLSL COMPILE" "NOT RUN locally (Actions required; pinned 16.5.0 gate packaged)"
    return
  fi
  local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz" compiler
  curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"
  [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive SHA"
  mkdir -p "$GLSLANG_DIR"; tar -xzf "$archive" -C "$GLSLANG_DIR"
  compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "pinned glslang compiler missing"
  "$compiler" --version | tee "$OUT/26649_glslang_version.txt"
  python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" --compiler "$compiler" | tee "$OUT/26649_shader_validation.txt"
  set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (3 exact modified runtime-expanded asset shaders; complete 257-file shader universe pinned)"
  set_report "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; exact 3 modified runtime-expanded shaders)"
  set_compiler "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; exact 3 modified runtime-expanded shaders)"
}
verify_successful_26648_mechanics(){
  python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26649_infrastructure.txt"
  set_report "INFRASTRUCTURE DELTA AUDIT" "PASS (R1.1 infrastructure-only repair; intended 26649 runtime candidate unchanged; exact successful 26648 R1.2 compiler/native/patch/PRE-BUILD/assemble/postbuild order retained; raw-asset GLSL shortcut removed)"
  set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (successful 26648 R1.2 build-script ${AUTH_R1_2_BUILD_SCRIPT_BLOB} + workflow ${AUTH_R1_2_WORKFLOW_BLOB}; exact sequence inherited; failed R1 shader-expansion defect permanently regressed)"
}
verify_candidate_patches(){
  python3 -S "$PATCHVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26649_patch_validation.txt"
  set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"
}
install_frozen_candidate_live(){
  rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"; compare_app_trees "$AFTER" "$LIVE_CANON"
}
postbuild_proof(){
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"; compare_app_trees "$AFTER" "$POST"
  (cd "$POST" && sha256sum -c "$CAND_PROTECTED" >/dev/null && sha256sum -c "$CAND_NATIVE" >/dev/null && sha256sum -c "$CAND_VENDOR" >/dev/null && sha256sum -c "$CAND_DNG" >/dev/null) || fail "post-build protected invariance"
  python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26649_postbuild_semantic_validation.txt"
  python3 -S "$GATEVERIFY" "$BASE" "$POST" | tee "$OUT/26649_postbuild_regressions.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26649_postbuild_authority.txt"
  set_report "POST-BUILD INVARIANCE" "PASS (candidate/protected/DNG/native-protected/vendor exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"
  tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26649_R1_1_candidate_app_source.tar.gz"
  sha256sum "$OUT/26649_R1_1_candidate_app_source.tar.gz" > "$OUT/26649_R1_1_candidate_app_source.tar.gz.sha256"
  cp "$CAND_FULL" "$OUT/26649_R1_1_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26649_R1_1_native_protected_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26649_R1_1_vendor_protected_postbuild.sha256"; cp "$CAND_DNG" "$OUT/26649_R1_1_dng_postbuild.sha256"; cp "$SHADER_PIN" "$OUT/26649_R1_1_runtime_expanded_shaders.sha256"
  set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests + expanded shader pins)"
}
verify_package
verify_scope
obtain_authority
make_candidate
verify_shaders
verify_successful_26648_mechanics
if [[ -n "$LOCAL_ART" ]]; then
  verify_candidate_patches
  set_report "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"
  set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real GLSL/Kotlin/Java/NDK/full Android require Actions)"; set_report "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_report "EXACTLY ONE APK" "NOT RUN locally (Actions required)"; set_report "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN locally (Actions required)"
  set_compiler "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_compiler "NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_compiler "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_compiler "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"
  cp "$OUT/26649_R1_1_STRICT_HANDOFF_REPORT.txt" "$OUT/26649_R1_1_local_prebuild_report.txt"
  pass "26649 R1.1 LOCAL PREBUILD PREPARED: exact successful 26648 R1.2 compiled candidate + exact 5-path Photon Highlight Compression candidate; applicable real compiler/build gates explicitly unproven locally"
  exit 0
fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26649_gradle_language_compilers.log"
set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"; compare_app_trees "$AFTER" "$WORK/after_language_compiler_snapshot"
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26649_gradle_native_compiler.log"
set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
verify_candidate_patches
set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26649 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26649_gradle_assemble.log"
set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort)
[[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK"
mv "${apks[0]}" "$FINAL"; [[ -f "$FINAL" ]] || fail "final APK missing after move"; set_report "EXACTLY ONE APK" "PASS"; sha256sum "$FINAL" > "$OUT/26649_R1_1_APK.sha256"
postbuild_proof
pass "26649 R1.1 ACTIONS BUILD COMPLETE"
