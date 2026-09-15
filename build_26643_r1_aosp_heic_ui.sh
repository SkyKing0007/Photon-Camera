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
RUNTIME_AUTHORITY_COMMIT="23ef05f61020cfd0ce412ef7ecb0bdc1064f99ba"
BASE_RUN_ID="34930671416"
BASE_ARTIFACT_ID="10381088303"
BASE_ARTIFACT_NAME="photon-26642-r1-heic-ui-prefix"
BASE_ARTIFACT_SHA="a475b50c17f1d2d4cd7da8dc0757089400335bc95a8e6a2a267bd067e667df61"
BASE_TAR_SHA="8c7fbbc120ca3150e19d98c6b2e7c6244204611482bcb638f2163ec329c63a3c"
VERSION_NAME="0.9726643"; VERSION_BUILD="26643"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
# Exact successful 26639 mechanics authority blobs. Identity/scope changes do not authorize reordering.
AUTH26639_BUILD_SCRIPT_AUTHORITY_BLOB="a5870d5776c05b6ec134cc1da50da2c835770419"
AUTH26639_WORKFLOW_AUTHORITY_BLOB="4fc781824f9ecf38291575e4536a361560141bf1"
AUTH26642_BUILD_SCRIPT_AUTHORITY_BLOB="2b7a9f4caeb6fba66dbf3880b7d399acb01af256"
AUTH26642_WORKFLOW_AUTHORITY_BLOB="e9df8c2f964fb4bd839885f63241187d83baf6d1"
AUTH26641_BUILD_SCRIPT_AUTHORITY_BLOB="53bf57126a97d684a35c3d2a04e33bcdaa4f31ee"
AUTH26641_WORKFLOW_AUTHORITY_BLOB="1577eeb875644495578e08196514fd7c0bc99c47"
HANDOFF="$ROOT/R1_26643_HANDOFF_HASHES.sha256"; UPLOADS="$ROOT/R1_26643_UPLOAD_PATHS.txt"
BASE_FULL="$ROOT/R1_26643_BASE_26642_R1_FULL_APP.sha256"; CAND_FULL="$ROOT/R1_26643_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/R1_26643_PROTECTED_UNCHANGED_BASE.sha256"; CAND_PROTECTED="$ROOT/R1_26643_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/R1_26643_NATIVE_PROTECTED_BASE.sha256"; CAND_NATIVE="$ROOT/R1_26643_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/R1_26643_VENDOR_PROTECTED_BASE.sha256"; CAND_VENDOR="$ROOT/R1_26643_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/R1_26643_DNG_BASE.sha256"; CAND_DNG="$ROOT/R1_26643_DNG_CANDIDATE.sha256"
SHADER_BASE="$ROOT/R1_26643_SHADER_UNIVERSE_BASE.sha256"; SHADER_CAND="$ROOT/R1_26643_SHADER_UNIVERSE_CANDIDATE.sha256"
CHANGED="$ROOT/R1_26643_RUNTIME_CHANGED_PATHS.txt"; PREWRITE="$ROOT/R1_26643_PREWRITE_SOURCE_HASHES.sha256"; ADDED="$ROOT/R1_26643_ADDED_PATHS_MUST_BE_ABSENT.txt"; EXPECTED_CHANGED="$ROOT/R1_26643_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/R1_26643_RUNTIME_DELTA_FROM_26642_R1.patch"; ROLLBACK="$ROOT/R1_26643_RUNTIME_ROLLBACK_TO_26642_R1.patch"; SHADER_PIN="$ROOT/R1_26643_RUNTIME_EXPANDED_SHADERS.sha256"
TRANSFORM="$ROOT/transform_26643_r1.py"; VALIDATE="$ROOT/validate_26643_r1.py"; AUTHORITY="$ROOT/verify_26643_r1_authority.py"; INFRA="$ROOT/verify_26643_r1_infrastructure.py"; PATCHVERIFY="$ROOT/verify_26643_r1_patches.py"; SHADERVERIFY="$ROOT/verify_26643_r1_shaders.py"; GATEVERIFY="$ROOT/verify_26643_r1_regressions.py"
BUILD_SCRIPT="$ROOT/build_26643_r1_aosp_heic_ui.sh"; WORKFLOW="$ROOT/.github/workflows/build-26643-r1-aosp-heic-ui.yml"
OUT="$ROOT/build_26643_r1_aosp_heic_ui_outputs"; WORK="$ROOT/.build_26643_r1_aosp_heic_ui_work"
ARTZIP="$WORK/26642_r1_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_26642_r1_compiled_candidate"; AFTER="$WORK/candidate_26643_r1"; AFTER2="$WORK/candidate_26643_r1_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; GLSLANG_DIR="$WORK/glslang-${GLSLANG_VERSION}"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r1-aosp-heic-ui-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then
  [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26642 R1 artifact ZIP"
  LOCAL_ART="$2"
elif [[ -n "${1:-}" ]]; then fail "unknown argument: $1"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26643_R1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT APPLICABLE (0 modified GLSL/runtime-expanded shaders)
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26643_R1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME AUTHORITY: NOT RUN
VERIFICATION MECHANICS AUTHORITY: NOT RUN
BACKUP STATUS: PASS (no backup created/requested; 26643 is a localized Android16-AOSP HEIC publication + camera UI cleanup change)
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE DELTA AUDIT: NOT RUN
26642 PRIOR IQ/SHORT/CAPTURE FREEZE: NOT RUN
SHORT LOCAL MOTION/GEOMETRY SUPPORT: NOT RUN
SHORT STATIONARY HIGHLIGHT RECOVERY RETAINED: NOT RUN
TRUE MATCHED SDR/HDR UHDR DELTA: NOT RUN
UHDR FIXED THRESHOLD RETIRED: NOT RUN
UHDR NO DILATION / SCALAR LUMA: NOT RUN
UHDR HALF-LINEAR PRE-DIVIDE MAP: NOT RUN
HEIC ANDROID16 AOSP CONTRACT: NOT RUN
SHARED GL TEXTURE OWNERSHIP: NOT RUN
SHARED GL FRAMEBUFFER CLEANUP: NOT RUN
UHDR MEASURED STORED RANGE METADATA: NOT RUN
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
TARGET VERSION/BUILD: 0.9726643 / 26643
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26643_R1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26643_R1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26643_R1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26643_R1_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){ local authority_root="$1" live_root="$2" dest_root="$3"; rm -rf "$dest_root"; mkdir -p "$dest_root"; cp -a "$authority_root/." "$dest_root/"; rm -rf "$dest_root/app/src"; cp -a "$live_root/app/src" "$dest_root/app/"; cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"; cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"; }
compare_app_trees(){ python3 -S - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a=H(sys.argv[1]); b=H(sys.argv[2]); assert len(a)==1720 and a==b,(len(a),len(b),sorted(set(a)^set(b))[:10]); print('PASS authority-seeded candidate byte-identical: 1720 files')
PY
}
verify_package(){
  [[ -f "$HANDOFF" && -f "$UPLOADS" && -d "$ROOT/handoff_payload_26643_r1" ]] || fail "sealed 26643 package incomplete"
  [[ "$(find "$ROOT/handoff_payload_26643_r1" -type f | wc -l)" -eq 10 ]] || fail "sealed runtime payload must contain exactly 10 files"
  [[ "$(wc -l < "$CHANGED")" -eq 10 && "$(wc -l < "$ADDED")" -eq 1 ]] || fail "26643 changed/add counts"
  sha256sum -c "$HANDOFF" >/dev/null
  [[ "$(wc -l < "$BASE_FULL")" -eq 1719 && "$(wc -l < "$CAND_FULL")" -eq 1720 ]] || fail "full app count"
  [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1710 && "$(wc -l < "$BASE_NATIVE")" -eq 800 && "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$BASE_DNG")" -eq 7 ]] || fail "protected manifest counts"
  [[ "$(wc -l < "$SHADER_BASE")" -eq 257 && "$(wc -l < "$SHADER_CAND")" -eq 257 && "$(wc -l < "$SHADER_PIN")" -eq 0 ]] || fail "shader manifest counts"
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
  if [[ -n "$LOCAL_ART" ]]; then set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed exact 10-path/1-added 26643 candidate; no live app source packaged)"; return; fi
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  [[ "$(git rev-parse HEAD^)" == "$RUNTIME_AUTHORITY_COMMIT" ]] || fail "26643 must be one direct handoff commit on exact successful 26642 authority"
  git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | sort > "$WORK/actual_upload_scope.txt"
  sort "$UPLOADS" > "$WORK/expected_upload_scope.txt"
  diff -u "$WORK/expected_upload_scope.txt" "$WORK/actual_upload_scope.txt" || fail "26643 upload scope mismatch"
  ! grep -Eq '^app/' "$WORK/actual_upload_scope.txt" || fail "handoff commit contains live app source"
  set_report "CHANGED RUNTIME SCOPE" "PASS (exact 10-path/1-added runtime candidate allowlist; handoff-only repository commit)"
}
obtain_authority(){
  if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else
    [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
    curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
  fi
  [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26642 R1 artifact ZIP SHA"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  local tarball="$ARTDIR/build_26642_r1_heic_ui_prefix_outputs/26642_R1_candidate_app_source.tar.gz"
  [[ -f "$tarball" && "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "26642 compiled candidate TAR authority"
  tar -xzf "$tarball" -C "$BASE"
  (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null) || fail "26642 exact base manifest"
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; [[ ! -e "$BASE/$rel" ]] || fail "26643 added path exists in 26642 authority: $rel"; done < "$ADDED"
  set_report "RUNTIME AUTHORITY" "PASS (successful 26642 R1 commit ${RUNTIME_AUTHORITY_COMMIT}/run ${BASE_RUN_ID}/artifact ${BASE_ARTIFACT_ID}/exact compiled candidate TAR ${BASE_TAR_SHA})"
}
make_candidate(){
  python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26643_transform.txt"
  python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26643_transform_replay.txt"
  compare_app_trees "$AFTER" "$AFTER2"
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; cmp "$ROOT/handoff_payload_26643_r1/$rel" "$AFTER/$rel" || fail "sealed payload differs frozen candidate: $rel"; done < "$CHANGED"
  python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26643_semantic_validation.txt"
  python3 -S "$GATEVERIFY" "$BASE" "$AFTER" | tee "$OUT/26643_regressions.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26643_authority_candidate.txt"
  set_report "26642 PRIOR IQ/SHORT/CAPTURE FREEZE" "PASS (1710 protected files byte-identical; successful 26642 UHDR/shared-GL/SHORT/color/denoise/capture/prefix/mode owners outside exact 10-path HEIC-publication/UI delta)"
  set_report "SHORT LOCAL MOTION/GEOMETRY SUPPORT" "PASS (successful 26642 SHORT shader bytes protected unchanged)"
  set_report "SHORT STATIONARY HIGHLIGHT RECOVERY RETAINED" "PASS (successful 26642 SHORT shader bytes protected unchanged)"
  set_report "TRUE MATCHED SDR/HDR UHDR DELTA" "PASS (full matched SDR-compressed luminance delta restored exactly once; 1/64 quotient offsets; no squared-compression attenuation)"
  set_report "UHDR FIXED THRESHOLD RETIRED" "PASS (no 0.65/0.85 pointwise eligibility)"
  set_report "UHDR NO DILATION / SCALAR LUMA" "PASS"
  set_report "UHDR HALF-LINEAR PRE-DIVIDE MAP" "PASS (Motion 2x linear-light matched HDR/SDR sampling before quotient; Night remains 1/4 inherited path)"
  set_report "HEIC ANDROID16 AOSP CONTRACT" "PASS (single Android-16 AOSP HEIC publication authority: base/tmap Display-P3+sRGB+unspecified matrix+full, gain unspecified/full, visible gain item, essential IPMA, mif1/heic/tmap brands; ISO 21496 payload preserved)"
  set_report "SHARED GL TEXTURE OWNERSHIP" "PASS (no texture-object-name-as-unit/slot; dynamic generation-safe ownership; caller binding restored)"
  set_report "SHARED GL FRAMEBUFFER CLEANUP" "PASS (glGenFramebuffers paired with glDeleteFramebuffers)"
  set_report "UHDR MEASURED STORED RANGE METADATA" "PASS (Motion ALPHA_8 range renormalized to measured scene peak; Night policy unchanged)"
  set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (1719 base / 1720 candidate / 1710 protected / 800 native-protected / 778 vendor / 7 DNG / 257 shader universe)"
  set_report "PROTECTED/DNG/NATIVE/VENDOR INVARIANCE" "PASS"
}
verify_shaders(){
  python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26643_shader_validation.txt"
  set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (257-file shader universe byte-identical; 0 modified runtime-expanded variants)"
  set_report "REAL GLSL COMPILE" "NOT APPLICABLE (0 modified GLSL/runtime-expanded shaders)"
  set_compiler "REAL GLSL COMPILE" "NOT APPLICABLE (0 modified GLSL/runtime-expanded shaders)"
}
verify_successful_26639_mechanics(){
  python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26643_infrastructure.txt"
  set_report "INFRASTRUCTURE DELTA AUDIT" "PASS (successful-26642 ordering/isolation/Kotlin-Java/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; delta limited to 26643 identity/authority/scope/HEIC+UI regressions and 0-GLSL applicability)"
  set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (exact successful 26642 implementation build-script blob ${AUTH26642_BUILD_SCRIPT_AUTHORITY_BLOB} + workflow blob ${AUTH26642_WORKFLOW_AUTHORITY_BLOB}, inheriting successful 26641 blobs ${AUTH26641_BUILD_SCRIPT_AUTHORITY_BLOB}/${AUTH26641_WORKFLOW_AUTHORITY_BLOB} and preserving successful-26639 root ordering blobs ${AUTH26639_BUILD_SCRIPT_AUTHORITY_BLOB}/${AUTH26639_WORKFLOW_AUTHORITY_BLOB})"
}
verify_candidate_patches(){
  python3 -S "$PATCHVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26643_patch_validation.txt"
  set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"
}
install_frozen_candidate_live(){
  rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"; compare_app_trees "$AFTER" "$LIVE_CANON"
}
postbuild_proof(){
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"; compare_app_trees "$AFTER" "$POST"
  (cd "$POST" && sha256sum -c "$CAND_PROTECTED" >/dev/null && sha256sum -c "$CAND_NATIVE" >/dev/null && sha256sum -c "$CAND_VENDOR" >/dev/null && sha256sum -c "$CAND_DNG" >/dev/null) || fail "post-build protected invariance"
  python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26643_postbuild_semantic_validation.txt"
  python3 -S "$GATEVERIFY" "$BASE" "$POST" | tee "$OUT/26643_postbuild_regressions.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26643_postbuild_authority.txt"
  set_report "POST-BUILD INVARIANCE" "PASS (candidate/protected/DNG/native-protected/vendor exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"
  tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26643_R1_candidate_app_source.tar.gz"
  sha256sum "$OUT/26643_R1_candidate_app_source.tar.gz" > "$OUT/26643_R1_candidate_app_source.tar.gz.sha256"
  cp "$CAND_FULL" "$OUT/26643_R1_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26643_R1_native_protected_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26643_R1_vendor_protected_postbuild.sha256"; cp "$CAND_DNG" "$OUT/26643_R1_dng_postbuild.sha256"; cp "$SHADER_PIN" "$OUT/26643_R1_runtime_expanded_shaders.sha256"
  set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests + expanded shader pins)"
}
verify_package
verify_scope
obtain_authority
make_candidate
verify_shaders
verify_successful_26639_mechanics
if [[ -n "$LOCAL_ART" ]]; then
  verify_candidate_patches
  set_report "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"
  set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real GLSL/Kotlin/Java/NDK/full Android require Actions)"; set_report "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_report "EXACTLY ONE APK" "NOT RUN locally (Actions required)"; set_report "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN locally (Actions required)"
  set_compiler "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_compiler "NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_compiler "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_compiler "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"
  cp "$OUT/26643_R1_STRICT_HANDOFF_REPORT.txt" "$OUT/26643_local_prebuild_report.txt"
  pass "26643 R1 LOCAL PREBUILD PREPARED: exact successful-26642 authority + exact 10-path/1-added Android16-AOSP-HEIC/UI candidate; real compiler/build gates explicitly unproven locally"
  exit 0
fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26643_gradle_language_compilers.log"
set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"; compare_app_trees "$AFTER" "$WORK/after_language_compiler_snapshot"
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26643_gradle_native_compiler.log"
set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
verify_candidate_patches
set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26643 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26643_gradle_assemble.log"
set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort)
[[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK"
mv "${apks[0]}" "$FINAL"; set_report "EXACTLY ONE APK" "PASS"; sha256sum "$FINAL" > "$OUT/26643_R1_APK.sha256"
postbuild_proof
pass "26643 R1 ACTIONS BUILD COMPLETE"
