#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="9e412b827aebac81032901891d33744dc2d8bc3e"
HANDOFF_PARENT_COMMIT="$RUNTIME_AUTHORITY_COMMIT"
BASE_RUN_ID="34717262053"
BASE_ARTIFACT_ID="10305860580"
BASE_ARTIFACT_NAME="photon-26633-r1-short-shadow-luma"
BASE_ARTIFACT_SHA="89448d4b7fc3975c8790d59ba51dbe6af4e3223895c8ea1d346755c303740c9d"
BASE_TAR_SHA="b950291a7face7323031069a197587a21bda9800174b4d4d32327d2d92afb59d"
SUCCESS_26633_BUILD_BLOB="6273260aadd70631d4ac285d5cded5cd8793073e"
SUCCESS_26633_WORKFLOW_BLOB="4cb99e72e04f217aae18ae22afb3ee30e4b1517b"
SUCCESS_26633_TRANSFORM_BLOB="3685fa42ace280c5128d9946663f03a39a28c326"
VERSION_NAME="0.9726634"; VERSION_BUILD="26634"
HANDOFF="$ROOT/R1_26634_HANDOFF_HASHES.sha256"
BASE_FULL="$ROOT/R1_26634_BASE_26633_R1_FULL_APP.sha256"; CAND_FULL="$ROOT/R1_26634_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/R1_26634_PROTECTED_UNCHANGED_BASE.sha256"; CAND_PROTECTED="$ROOT/R1_26634_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/R1_26634_NATIVE_PROTECTED_BASE.sha256"; CAND_NATIVE="$ROOT/R1_26634_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/R1_26634_VENDOR_PROTECTED_BASE.sha256"; CAND_VENDOR="$ROOT/R1_26634_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/R1_26634_DNG_BASE.sha256"; CAND_DNG="$ROOT/R1_26634_DNG_CANDIDATE.sha256"
CHANGED="$ROOT/R1_26634_RUNTIME_CHANGED_PATHS.txt"; PREWRITE="$ROOT/R1_26634_PREWRITE_SOURCE_HASHES.sha256"; ADDED="$ROOT/R1_26634_ADDED_PATHS_MUST_BE_ABSENT.txt"; EXPECTED_CHANGED="$ROOT/R1_26634_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/R1_26634_RUNTIME_DELTA_FROM_26633_R1.patch"; ROLLBACK="$ROOT/R1_26634_RUNTIME_ROLLBACK_TO_26633_R1.patch"; SHADER_PIN="$ROOT/R1_26634_RUNTIME_EXPANDED_SHADERS.sha256"
TRANSFORM="$ROOT/transform_26634_r1.py"; VALIDATE="$ROOT/validate_26634_r1.py"; AUTHORITY="$ROOT/verify_26634_r1_authority.py"; INFRA="$ROOT/verify_26634_r1_infrastructure.py"; PATCHVERIFY="$ROOT/verify_26634_r1_patches.py"; SHADERVERIFY="$ROOT/verify_26634_r1_shaders.py"; GATEVERIFY="$ROOT/verify_26634_r1_regressions.py"
BUILD_SCRIPT="$ROOT/build_26634_r1_local_residual_noise_metadata.sh"; WORKFLOW="$ROOT/.github/workflows/build-26634-r1-local-residual-noise-metadata.yml"
OUT="$ROOT/build_26634_r1_local_residual_noise_metadata_outputs"; WORK="$ROOT/.build_26634_r1_local_residual_noise_metadata_work"
ARTZIP="$WORK/26633_r1_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_26633_r1_compiled_candidate"; AFTER="$WORK/candidate_26634_r1"; AFTER2="$WORK/candidate_26634_r1_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r1-local-residual-noise-metadata-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26633 R1 artifact ZIP"; LOCAL_ART="$2"; elif [[ -n "${1:-}" ]]; then fail "unknown argument: $1"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26634_R1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: N/A (no modified GLSL)
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26634_R1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME AUTHORITY: NOT RUN
VERIFICATION MECHANICS AUTHORITY: NOT RUN
BACKUP STATUS: NO NEW BACKUP (user-directed localized correction)
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE DELTA AUDIT: NOT RUN
26633 R1 RUNTIME INHERITANCE: NOT RUN
LOCAL RESIDUAL NOISE SUPPORT: NOT RUN
DENOISE CEILING PRESERVATION: NOT RUN
MOTIONTRACE/PHOTONLOG PRESERVATION: NOT RUN
PROCESS LIFECYCLE LOG RETIREMENT: NOT RUN
EXIF DIAGNOSTIC CLEANUP: NOT RUN
26633 UHDR/DNG/SUPER-RES FREEZE: NOT RUN
BASE/CANDIDATE MANIFEST COMPLETENESS: NOT RUN
PROTECTED/DNG/NATIVE/VENDOR INVARIANCE: NOT RUN
RUNTIME-EXPANDED GLSL RESERVED SCAN: NOT RUN
REAL GLSL COMPILE: N/A (no modified GLSL)
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
TARGET VERSION/BUILD: 0.9726634 / 26634
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26634_R1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26634_R1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26634_R1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26634_R1_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){ local authority_root="$1" live_root="$2" dest_root="$3"; rm -rf "$dest_root"; mkdir -p "$dest_root"; cp -a "$authority_root/." "$dest_root/"; rm -rf "$dest_root/app/src"; cp -a "$live_root/app/src" "$dest_root/app/"; cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"; cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"; }
verify_package(){
  [[ -f "$HANDOFF" ]] || fail "handoff hash manifest missing"; sha256sum -c "$HANDOFF" >/dev/null
  [[ "$(wc -l < "$CHANGED")" -eq 8 ]] || fail "runtime allowlist must be 8"
  [[ "$(wc -l < "$PREWRITE")" -eq 8 && "$(wc -l < "$ADDED")" -eq 0 ]] || fail "existing/add count"
  [[ "$(wc -l < "$BASE_FULL")" -eq 1713 && "$(wc -l < "$CAND_FULL")" -eq 1713 ]] || fail "full app count"
  [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1705 ]] || fail "protected count"
  [[ "$(wc -l < "$BASE_NATIVE")" -eq 802 && "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$BASE_DNG")" -eq 7 ]] || fail "protected manifest counts (802 native / 778 vendor / 7 DNG)"
  cmp "$BASE_PROTECTED" "$CAND_PROTECTED"; cmp "$BASE_NATIVE" "$CAND_NATIVE"; cmp "$BASE_VENDOR" "$CAND_VENDOR"; cmp "$BASE_DNG" "$CAND_DNG"
  ! awk '{print $2}' "$HANDOFF" | grep -Eq '(^|/)(\.build_|build_.*_outputs|__pycache__)(/|$)|(^|/)app/(build|\.cxx)/|\.pyc$|\.apk$' || fail "transient/generated path sealed"
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
  python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26634_infrastructure_local.txt"
  set_report "INFRASTRUCTURE DELTA AUDIT" "PASS (successful-26633-R1 ordering/isolation/compiler/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; 26634 identity/authority/8-path validators only)"
}
verify_scope(){
  if [[ -n "$LOCAL_ART" ]]; then set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed handoff; exact 8-file runtime allowlist)"; return; fi
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  [[ "$(git rev-parse HEAD^)" == "$HANDOFF_PARENT_COMMIT" ]] || fail "26634 sealed handoff must be one direct packaging commit on successful 26633 R1 authority"
  python3 -S - "$HANDOFF" > "$WORK/expected_scope.txt" <<'PY'
from pathlib import Path
import sys
names=[line.split('  ',1)[1] for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]; names.append('R1_26634_HANDOFF_HASHES.sha256'); print('\n'.join(sorted(names)))
PY
  git diff --name-only "$HANDOFF_PARENT_COMMIT"..HEAD | sort > "$WORK/actual_scope.txt"
  diff -u "$WORK/expected_scope.txt" "$WORK/actual_scope.txt" || fail "handoff commit scope mismatch"
  ! grep -Eq '^app/' "$WORK/actual_scope.txt" || fail "handoff commit contains live app source"
  set_report "CHANGED RUNTIME SCOPE" "PASS (sealed infrastructure/payload only; exact 8-file candidate runtime delta; no live app source committed)"
}
obtain_authority(){
  if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
  [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26633 R1 artifact ZIP SHA"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  local tarball="$ARTDIR/build_26633_r1_short_shadow_luma_outputs/26633_R1_candidate_app_source.tar.gz"
  [[ -f "$tarball" && "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "26633 R1 compiled candidate TAR authority"
  tar -xzf "$tarball" -C "$BASE"; find "$ARTDIR" -type f -name '*.apk' -delete
  (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null && sha256sum -c "$BASE_PROTECTED" >/dev/null && sha256sum -c "$BASE_NATIVE" >/dev/null && sha256sum -c "$BASE_VENDOR" >/dev/null && sha256sum -c "$BASE_DNG" >/dev/null && sha256sum -c "$PREWRITE" >/dev/null)
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; [[ ! -e "$BASE/$rel" ]] || fail "26634 added path exists in 26633 authority: $rel"; done < "$ADDED"
  set_report "RUNTIME AUTHORITY" "PASS (successful 26633 R1 commit 9e412b827aebac81032901891d33744dc2d8bc3e/run 34717262053/artifact 10305860580/exact compiled candidate TAR)"; pass "exact successful 26633 R1 compiled-candidate authority"
}
make_candidate(){
  rm -rf "$AFTER" "$AFTER2"
  python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26634_transform.txt"; python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26634_transform_replay.txt"
  python3 -S - "$AFTER" "$AFTER2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a=H(sys.argv[1]); b=H(sys.argv[2]); assert len(a)==1713 and a==b; print('PASS deterministic candidate reconstruction 1713 files')
PY
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; cmp "$ROOT/handoff_payload_26634_r1/$rel" "$AFTER/$rel" || fail "sealed payload differs frozen candidate: $rel"; done < "$CHANGED"
  python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26634_semantic_validation.txt"
  python3 -S "$GATEVERIFY" "$BASE" "$AFTER" | tee "$OUT/26634_regressions.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26634_authority_candidate.txt"
  set_report "26633 R1 RUNTIME INHERITANCE" "PASS (exact successful compiler-tested 26633 candidate; only exact 8-path 26634 delta)"
  set_report "LOCAL RESIDUAL NOISE SUPPORT" "PASS (same Sabre accumulated-green support owner; local Q8 192..256 reduction-only multiplier)"
  set_report "DENOISE CEILING PRESERVATION" "PASS (local map <= identity; 26633 luma 0.35 ceiling and existing user luma/chroma controls unchanged)"
  set_report "MOTIONTRACE/PHOTONLOG PRESERVATION" "PASS (MotionTrace byte-identical; normal async PhotonLog retained)"
  set_report "PROCESS LIFECYCLE LOG RETIREMENT" "PASS (private lifecycle file/fsync/process-state persistence removed; critical routes to normal PhotonLog)"
  set_report "EXIF DIAGNOSTIC CLEANUP" "PASS (Motion/Night ImageDescription diagnostics removed; normal photographic EXIF preserved; auxiliary app tags cleared)"
  set_report "26633 UHDR/DNG/SUPER-RES FREEZE" "PASS (no UHDR/DNG/native/Super-Res reconstruction runtime file changed)"
  set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (1713 base / 1713 candidate / 1705 protected / 802 native / 778 vendor / 7 DNG)"
  set_report "PROTECTED/DNG/NATIVE/VENDOR INVARIANCE" "PASS"
}
verify_candidate_patches(){ python3 -S "$PATCHVERIFY" "$BASE" "$AFTER" "$FORWARD" "$ROLLBACK" | tee "$OUT/26634_patch_validation.txt"; set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"; }
verify_shaders(){
  python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" | tee "$OUT/26634_shader_validation.txt"
  [[ ! -s "$SHADER_PIN" ]] || fail "26634 shader pin must be empty because runtime GLSL allowlist is empty"
  set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "N/A (no modified GLSL/runtime-expanded shader)"
  set_report "REAL GLSL COMPILE" "N/A (no modified GLSL)"; set_compiler "REAL GLSL COMPILE" "N/A (no modified GLSL)"
}
verify_successful_26633_mechanics(){
  if [[ -n "$LOCAL_ART" ]]; then python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26634_infrastructure_packaged.txt"; set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (successful-26633-R1 sequence packaged; Actions exact parent Git-blob replay required)"; return 0; fi
  [[ "$(git rev-parse "$HANDOFF_PARENT_COMMIT:build_26633_r1_short_shadow_luma.sh")" == "$SUCCESS_26633_BUILD_BLOB" ]] || fail "successful 26633 build-script blob"
  [[ "$(git rev-parse "$HANDOFF_PARENT_COMMIT:.github/workflows/build-26633-r1-short-shadow-luma.yml")" == "$SUCCESS_26633_WORKFLOW_BLOB" ]] || fail "successful 26633 workflow blob"
  [[ "$(git rev-parse "$HANDOFF_PARENT_COMMIT:transform_26633_r1.py")" == "$SUCCESS_26633_TRANSFORM_BLOB" ]] || fail "successful 26633 transform blob"
  local pb="$WORK/successful_26633_r1_build.sh" pw="$WORK/successful_26633_r1_workflow.yml" pt="$WORK/successful_26633_r1_transform.py"
  git show "$HANDOFF_PARENT_COMMIT:build_26633_r1_short_shadow_luma.sh" > "$pb"; git show "$HANDOFF_PARENT_COMMIT:.github/workflows/build-26633-r1-short-shadow-luma.yml" > "$pw"; git show "$HANDOFF_PARENT_COMMIT:transform_26633_r1.py" > "$pt"
  python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" "$pb" "$pw" "$pt" | tee "$OUT/26634_infrastructure_actions.txt"
  set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (exact successful-26633-R1 build/workflow/transform Git blobs replayed; compiler/build ordering and invariance mechanics preserved)"
}
install_and_build(){
  [[ -z "$LOCAL_ART" ]] || return 0
  rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"
  python3 -S "$VALIDATE" "$BASE" "$LIVE_CANON" | tee "$OUT/26634_live_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$LIVE_CANON" | tee "$OUT/26634_live_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$LIVE_CANON" | tee "$OUT/26634_live_authority.txt"
  python3 -S - "$AFTER" "$LIVE_CANON" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
assert H(sys.argv[1])==H(sys.argv[2]); print('PASS authority-seeded live compiler candidate byte-identical')
PY
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26634_gradle_language_compilers.log"
  set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
  # Candidate source must remain frozen after language compilers.
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"
  python3 -S - "$AFTER" "$WORK/after_language_compiler_snapshot" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
assert H(sys.argv[1])==H(sys.argv[2]); print('PASS candidate unchanged after real Kotlin/Java compilers')
PY
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26634_gradle_native_compiler.log"
  set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
  verify_candidate_patches
  set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26634 PRE-BUILD SAFETY PROOF PASSED"
  ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26634_gradle_assemble.log"
  set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
  mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort); [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK"; mv "${apks[0]}" "$FINAL"
  mapfile -t roots < <(find "$ROOT" -maxdepth 1 -type f -name '*.apk' | sort); [[ "${#roots[@]}" -eq 1 && "${roots[0]}" == "$FINAL" ]] || fail "exactly one final root APK"; sha256sum "$FINAL" > "$OUT/26634_R1_APK.sha256"; set_report "EXACTLY ONE APK" "PASS"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"; python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26634_postbuild_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$POST" | tee "$OUT/26634_postbuild_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26634_postbuild_authority.txt"
  python3 -S - "$AFTER" "$POST" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
assert H(sys.argv[1])==H(sys.argv[2]); print('PASS postbuild candidate byte-identical')
PY
  set_report "POST-BUILD INVARIANCE" "PASS (candidate/protected/DNG/native/vendor exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"
  tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26634_R1_candidate_app_source.tar.gz"; sha256sum "$OUT/26634_R1_candidate_app_source.tar.gz" > "$OUT/26634_R1_candidate_app_source.tar.gz.sha256"; cp "$CAND_FULL" "$OUT/26634_R1_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26634_R1_native_protected_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26634_R1_vendor_protected_postbuild.sha256"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests)"
}
verify_package
verify_scope
obtain_authority
make_candidate
verify_shaders
verify_successful_26633_mechanics
if [[ -n "$LOCAL_ART" ]]; then
  verify_candidate_patches
  set_report "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real Kotlin/Java/NDK/full Android require Actions)"; set_report "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_report "EXACTLY ONE APK" "NOT RUN locally (Actions required)"; set_report "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN locally (Actions required)"
  set_compiler "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_compiler "NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_compiler "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_compiler "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"
  cp "$OUT/26634_R1_STRICT_HANDOFF_REPORT.txt" "$OUT/26634_local_prebuild_report.txt"; pass "26634 R1 LOCAL PREBUILD PREPARED: exact successful-26633-R1 authority + fresh 8-path local residual-noise/logging/EXIF delta; real compiler/build gates explicitly unproven locally"; exit 0
fi
install_and_build
pass "26634 R1 REAL KOTLIN/JAVA + NDK + FULL ASSEMBLE PASSED (GLSL N/A: no shader changed)"
pass "26634 R1 POST-BUILD INVARIANCE PASSED"
