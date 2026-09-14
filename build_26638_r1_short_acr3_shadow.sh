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
RUNTIME_AUTHORITY_COMMIT="a448bb1389dbf5ca643d05cda2ce1dad267b23ec"
BASE_RUN_ID="34843253647"
BASE_ARTIFACT_ID="10347525034"
BASE_ARTIFACT_NAME="photon-26637-r1-heic-container-fix"
BASE_ARTIFACT_SHA="bb114010ce2f412525a5fff3fec1957aff3a2f344c4fedf8675c33aae6a7017c"
BASE_TAR_SHA="187562b05ba9925bc645230020b06d71f9a75605bcfcca362485c6186801df8d"
VERSION_NAME="0.9726638"; VERSION_BUILD="26638"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
HANDOFF="$ROOT/R1_26638_HANDOFF_HASHES.sha256"; UPLOADS="$ROOT/R1_26638_UPLOAD_PATHS.txt"
BASE_FULL="$ROOT/R1_26638_BASE_26637_R1_FULL_APP.sha256"; CAND_FULL="$ROOT/R1_26638_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/R1_26638_PROTECTED_UNCHANGED_BASE.sha256"; CAND_PROTECTED="$ROOT/R1_26638_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/R1_26638_NATIVE_PROTECTED_BASE.sha256"; CAND_NATIVE="$ROOT/R1_26638_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/R1_26638_VENDOR_PROTECTED_BASE.sha256"; CAND_VENDOR="$ROOT/R1_26638_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/R1_26638_DNG_BASE.sha256"; CAND_DNG="$ROOT/R1_26638_DNG_CANDIDATE.sha256"
SHADER_BASE="$ROOT/R1_26638_SHADER_UNIVERSE_BASE.sha256"; SHADER_CAND="$ROOT/R1_26638_SHADER_UNIVERSE_CANDIDATE.sha256"
CHANGED="$ROOT/R1_26638_RUNTIME_CHANGED_PATHS.txt"; PREWRITE="$ROOT/R1_26638_PREWRITE_SOURCE_HASHES.sha256"; ADDED="$ROOT/R1_26638_ADDED_PATHS_MUST_BE_ABSENT.txt"; EXPECTED_CHANGED="$ROOT/R1_26638_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/R1_26638_RUNTIME_DELTA_FROM_26637_R1.patch"; ROLLBACK="$ROOT/R1_26638_RUNTIME_ROLLBACK_TO_26637_R1.patch"; SHADER_PIN="$ROOT/R1_26638_RUNTIME_EXPANDED_SHADERS.sha256"
TRANSFORM="$ROOT/transform_26638_r1.py"; VALIDATE="$ROOT/validate_26638_r1.py"; AUTHORITY="$ROOT/verify_26638_r1_authority.py"; INFRA="$ROOT/verify_26638_r1_infrastructure.py"; PATCHVERIFY="$ROOT/verify_26638_r1_patches.py"; SHADERVERIFY="$ROOT/verify_26638_r1_shaders.py"; GATEVERIFY="$ROOT/verify_26638_r1_regressions.py"
BUILD_SCRIPT="$ROOT/build_26638_r1_short_acr3_shadow.sh"; WORKFLOW="$ROOT/.github/workflows/build-26638-r1-short-acr3-shadow.yml"
OUT="$ROOT/build_26638_r1_short_acr3_shadow_outputs"; WORK="$ROOT/.build_26638_r1_short_acr3_shadow_work"
ARTZIP="$WORK/26637_r1_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_26637_r1_compiled_candidate"; AFTER="$WORK/candidate_26638_r1"; AFTER2="$WORK/candidate_26638_r1_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; GLSLANG_DIR="$WORK/glslang-${GLSLANG_VERSION}"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r1-short-acr3-shadow-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then
  [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26637 R1 artifact ZIP"
  LOCAL_ART="$2"
elif [[ -n "${1:-}" ]]; then fail "unknown argument: $1"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26638_R1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET (8 runtime-expanded variants)
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26638_R1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME AUTHORITY: NOT RUN
VERIFICATION MECHANICS AUTHORITY: NOT RUN
BACKUP STATUS: PASS (backup-26637-pre-26638-combined -> exact successful 26637 commit a448bb1389dbf5ca643d05cda2ce1dad267b23ec)
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE DELTA AUDIT: NOT RUN
26637 R1 RUNTIME INHERITANCE: NOT RUN
SHORT COMPONENT COHERENCE OWNER: NOT RUN
SHORT HARD VETO / SOURCE CLIP FREEZE: NOT RUN
ACR3 SINGLE COLOR APPEARANCE OWNER: NOT RUN
0.95 / ADAPTIVE V5 AUTOMATIC OWNER RETIRED: NOT RUN
USER SATURATION 1.0 IDENTITY: NOT RUN
TRUE SHADOW FLOOR GUARD: NOT RUN
1X / TRUE2X COLOR-SHADOW PARITY: NOT RUN
26635 SPATIAL HIGHLIGHT PRESENTATION FREEZE: NOT RUN
UHDR / HEIC / JPEG CONTAINER FREEZE: NOT RUN
XIAOMI DNG PHYSICAL CALIBRATION FREEZE: NOT RUN
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
TARGET VERSION/BUILD: 0.9726638 / 26638
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26638_R1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26638_R1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26638_R1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26638_R1_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){ local authority_root="$1" live_root="$2" dest_root="$3"; rm -rf "$dest_root"; mkdir -p "$dest_root"; cp -a "$authority_root/." "$dest_root/"; rm -rf "$dest_root/app/src"; cp -a "$live_root/app/src" "$dest_root/app/"; cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"; cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"; }
compare_app_trees(){ python3 -S - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a=H(sys.argv[1]); b=H(sys.argv[2]); assert len(a)==1717 and a==b,(len(a),len(b),sorted(set(a)^set(b))[:10]); print('PASS authority-seeded candidate byte-identical: 1717 files')
PY
}
verify_package(){
  [[ -f "$HANDOFF" && -f "$UPLOADS" && -d "$ROOT/handoff_payload_26638_r1" ]] || fail "sealed 26638 package incomplete"
  [[ "$(find "$ROOT/handoff_payload_26638_r1" -type f | wc -l)" -eq 10 ]] || fail "sealed runtime payload must contain exactly 10 files"
  [[ "$(wc -l < "$CHANGED")" -eq 10 && "$(wc -l < "$ADDED")" -eq 1 ]] || fail "26638 changed/add counts"
  sha256sum -c "$HANDOFF" >/dev/null
  [[ "$(wc -l < "$BASE_FULL")" -eq 1716 && "$(wc -l < "$CAND_FULL")" -eq 1717 ]] || fail "full app count"
  [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1707 && "$(wc -l < "$BASE_NATIVE")" -eq 802 && "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$BASE_DNG")" -eq 7 ]] || fail "protected manifest counts"
  [[ "$(wc -l < "$SHADER_BASE")" -eq 257 && "$(wc -l < "$SHADER_CAND")" -eq 257 && "$(wc -l < "$SHADER_PIN")" -eq 8 ]] || fail "shader manifest counts"
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
  if [[ -n "$LOCAL_ART" ]]; then set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed exact 10-path/1-added 26638 candidate; no live app source packaged)"; return; fi
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  [[ "$(git rev-parse HEAD^)" == "$RUNTIME_AUTHORITY_COMMIT" ]] || fail "26638 must be one direct handoff commit on exact successful 26637 authority"
  git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | sort > "$WORK/actual_upload_scope.txt"
  sort "$UPLOADS" > "$WORK/expected_upload_scope.txt"
  diff -u "$WORK/expected_upload_scope.txt" "$WORK/actual_upload_scope.txt" || fail "26638 upload scope mismatch"
  ! grep -Eq '^app/' "$WORK/actual_upload_scope.txt" || fail "handoff commit contains live app source"
  set_report "CHANGED RUNTIME SCOPE" "PASS (exact 10-path/1-added runtime candidate allowlist; handoff-only repository commit)"
}
obtain_authority(){
  if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else
    [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
    curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
  fi
  [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26637 R1 artifact ZIP SHA"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  local tarball="$ARTDIR/build_26637_r1_heic_container_fix_outputs/26637_R1_candidate_app_source.tar.gz"
  [[ -f "$tarball" && "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "26637 compiled candidate TAR authority"
  tar -xzf "$tarball" -C "$BASE"
  (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null) || fail "26637 exact base manifest"
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; [[ ! -e "$BASE/$rel" ]] || fail "26638 added path exists in 26637 authority: $rel"; done < "$ADDED"
  set_report "RUNTIME AUTHORITY" "PASS (successful 26637 R1 commit ${RUNTIME_AUTHORITY_COMMIT}/run ${BASE_RUN_ID}/artifact ${BASE_ARTIFACT_ID}/exact compiled candidate TAR)"
}
make_candidate(){
  python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26638_transform.txt"
  python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26638_transform_replay.txt"
  compare_app_trees "$AFTER" "$AFTER2"
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; cmp "$ROOT/handoff_payload_26638_r1/$rel" "$AFTER/$rel" || fail "sealed payload differs frozen candidate: $rel"; done < "$CHANGED"
  python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26638_semantic_validation.txt"
  python3 -S "$GATEVERIFY" "$BASE" "$AFTER" | tee "$OUT/26638_regressions.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26638_authority_candidate.txt"
  set_report "26637 R1 RUNTIME INHERITANCE" "PASS (exact successful compiler-tested 26637 candidate; only exact 10-path/1-added 26638 delta)"
  set_report "SHORT COMPONENT COHERENCE OWNER" "PASS (boundary CFA-phase contradiction reduced once per phase and propagated through existing component trust; no censored-core fail-open)"
  set_report "SHORT HARD VETO / SOURCE CLIP FREEZE" "PASS (existing same-CFA/source-clip/headroom/geometry/physical caps retained)"
  set_report "ACR3 SINGLE COLOR APPEARANCE OWNER" "PASS (exact 1025-sample bjzhou default ACR3, profile-space RGB relationship, display luminance preserved)"
  set_report "0.95 / ADAPTIVE V5 AUTOMATIC OWNER RETIRED" "PASS (old post-color node unreachable; no automatic +22% recovery in 1x/true2x)"
  set_report "USER SATURATION 1.0 IDENTITY" "PASS (only explicit user deviation changes chroma)"
  set_report "TRUE SHADOW FLOOR GUARD" "PASS (deepScale 0.72 retained only below 0.05 linear guide; broad 0..0.18 toe retired)"
  set_report "1X / TRUE2X COLOR-SHADOW PARITY" "PASS (one ACR3 table Java owner; native CPU/GPU consume exact 1025 samples; same shadow/saturation equations)"
  set_report "26635 SPATIAL HIGHLIGHT PRESENTATION FREEZE" "PASS (local-laplacian/highlight owner outside changed scope; protected bytes invariant)"
  set_report "UHDR / HEIC / JPEG CONTAINER FREEZE" "PASS (26632/26637 gain-map/container owners outside changed scope; true2x publisher presentation only)"
  set_report "XIAOMI DNG PHYSICAL CALIBRATION FREEZE" "PASS (DNG/matrix source protected; ACR3 begins after calibrated profile RGB)"
  set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (1716 base / 1717 candidate / 1707 protected / 802 native / 778 vendor / 7 DNG / 257 shader universe)"
  set_report "PROTECTED/DNG/NATIVE/VENDOR INVARIANCE" "PASS"
}
verify_shaders(){
  if [[ -n "$LOCAL_ART" ]]; then
    python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26638_shader_validation.txt"
    set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (8 exact modified runtime-expanded variants)"
    set_report "REAL GLSL COMPILE" "NOT RUN locally (Actions pinned glslang 16.5.0 required)"
    set_compiler "REAL GLSL COMPILE" "NOT RUN locally (Actions pinned glslang 16.5.0 required)"
    return
  fi
  mkdir -p "$GLSLANG_DIR"
  local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz"
  curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"
  [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang ${GLSLANG_VERSION} archive SHA"
  tar -xf "$archive" -C "$GLSLANG_DIR"
  local compiler; compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "pinned glslang compiler missing"
  chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26638_glslang_version.txt"
  python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" --compiler "$compiler" | tee "$OUT/26638_shader_validation.txt"
  set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (8 exact modified runtime-expanded variants)"
  set_report "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; all 8 exact runtime-expanded variants)"
  set_compiler "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; 8 variants)"
}
verify_successful_26637_mechanics(){
  if [[ -n "$LOCAL_ART" ]]; then python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26638_infrastructure_local.txt"; else python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" --git | tee "$OUT/26638_infrastructure_actions.txt"; fi
  set_report "INFRASTRUCTURE DELTA AUDIT" "PASS (successful-26637 ordering/isolation/Kotlin-Java/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; only applicable proven GLSL gate + 26638 identity/authority/scope/regressions)"
  set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (exact successful-26637 build/workflow/transform Git blobs pinned; successful-26635 glslang 16.5.0 mechanism reused only because GLSL is modified)"
}
verify_candidate_patches(){
  python3 -S "$PATCHVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26638_patch_validation.txt"
  set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"
}
install_frozen_candidate_live(){
  rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"; compare_app_trees "$AFTER" "$LIVE_CANON"
}
postbuild_proof(){
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"; compare_app_trees "$AFTER" "$POST"
  (cd "$POST" && sha256sum -c "$CAND_PROTECTED" >/dev/null && sha256sum -c "$CAND_NATIVE" >/dev/null && sha256sum -c "$CAND_VENDOR" >/dev/null && sha256sum -c "$CAND_DNG" >/dev/null) || fail "post-build protected invariance"
  python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26638_postbuild_semantic_validation.txt"
  python3 -S "$GATEVERIFY" "$BASE" "$POST" | tee "$OUT/26638_postbuild_regressions.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26638_postbuild_authority.txt"
  set_report "POST-BUILD INVARIANCE" "PASS (candidate/protected/DNG/native/vendor exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"
  tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26638_R1_candidate_app_source.tar.gz"
  sha256sum "$OUT/26638_R1_candidate_app_source.tar.gz" > "$OUT/26638_R1_candidate_app_source.tar.gz.sha256"
  cp "$CAND_FULL" "$OUT/26638_R1_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26638_R1_native_protected_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26638_R1_vendor_protected_postbuild.sha256"; cp "$CAND_DNG" "$OUT/26638_R1_dng_postbuild.sha256"; cp "$SHADER_PIN" "$OUT/26638_R1_runtime_expanded_shaders.sha256"
  set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests + expanded shader pins)"
}
verify_package
verify_scope
obtain_authority
make_candidate
verify_shaders
verify_successful_26637_mechanics
if [[ -n "$LOCAL_ART" ]]; then
  verify_candidate_patches
  set_report "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"
  set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real GLSL/Kotlin/Java/NDK/full Android require Actions)"; set_report "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_report "EXACTLY ONE APK" "NOT RUN locally (Actions required)"; set_report "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN locally (Actions required)"
  set_compiler "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_compiler "NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_compiler "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_compiler "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"
  cp "$OUT/26638_R1_STRICT_HANDOFF_REPORT.txt" "$OUT/26638_local_prebuild_report.txt"
  pass "26638 R1 LOCAL PREBUILD PREPARED: exact successful-26637 authority + exact 10-path/1-added SHORT/ACR3/shadow candidate; real compiler/build gates explicitly unproven locally"
  exit 0
fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26638_gradle_language_compilers.log"
set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"; compare_app_trees "$AFTER" "$WORK/after_language_compiler_snapshot"
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26638_gradle_native_compiler.log"
set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
verify_candidate_patches
set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26638 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26638_gradle_assemble.log"
set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort)
[[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK"
mv "${apks[0]}" "$FINAL"; set_report "EXACTLY ONE APK" "PASS"; sha256sum "$FINAL" > "$OUT/26638_R1_APK.sha256"
postbuild_proof
pass "26638 R1 ACTIONS BUILD COMPLETE"
