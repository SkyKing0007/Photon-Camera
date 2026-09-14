#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="52be30fe45f9492a765efe6437a6b2c1de6b7ff3"
BASE_RUN_ID="34796574775"
BASE_ARTIFACT_ID="10330345660"
BASE_ARTIFACT_NAME="photon-26636-r1-heic-ultrahdr"
BASE_ARTIFACT_SHA="1e27ea4f52618e2dcd42d1eded2e5aa7f8a47350c4f6bdd3e26d41703c5c5307"
BASE_TAR_SHA="3f6fbb19d7821eaed9a3c76578c5f70edebb14721f920a2e4040fc7da1847960"
VERSION_NAME="0.9726637"; VERSION_BUILD="26637"
HANDOFF="$ROOT/R1_26637_HANDOFF_HASHES.sha256"
UPLOADS="$ROOT/R1_26637_UPLOAD_PATHS.txt"
BASE_FULL="$ROOT/R1_26637_BASE_26636_R1_FULL_APP.sha256"; CAND_FULL="$ROOT/R1_26637_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/R1_26637_PROTECTED_UNCHANGED_BASE.sha256"; CAND_PROTECTED="$ROOT/R1_26637_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/R1_26637_NATIVE_PROTECTED_BASE.sha256"; CAND_NATIVE="$ROOT/R1_26637_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/R1_26637_VENDOR_PROTECTED_BASE.sha256"; CAND_VENDOR="$ROOT/R1_26637_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/R1_26637_DNG_BASE.sha256"; CAND_DNG="$ROOT/R1_26637_DNG_CANDIDATE.sha256"
CHANGED="$ROOT/R1_26637_RUNTIME_CHANGED_PATHS.txt"; PREWRITE="$ROOT/R1_26637_PREWRITE_SOURCE_HASHES.sha256"; ADDED="$ROOT/R1_26637_ADDED_PATHS_MUST_BE_ABSENT.txt"; EXPECTED_CHANGED="$ROOT/R1_26637_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/R1_26637_RUNTIME_DELTA_FROM_26636_R1.patch"; ROLLBACK="$ROOT/R1_26637_RUNTIME_ROLLBACK_TO_26636_R1.patch"; SHADER_PIN="$ROOT/R1_26637_RUNTIME_EXPANDED_SHADERS.sha256"
TRANSFORM="$ROOT/transform_26637_r1.py"; VALIDATE="$ROOT/validate_26637_r1.py"; AUTHORITY="$ROOT/verify_26637_r1_authority.py"; INFRA="$ROOT/verify_26637_r1_infrastructure.py"; PATCHVERIFY="$ROOT/verify_26637_r1_patches.py"; SHADERVERIFY="$ROOT/verify_26637_r1_shaders.py"; GATEVERIFY="$ROOT/verify_26637_r1_regressions.py"
BUILD_SCRIPT="$ROOT/build_26637_r1_heic_container_fix.sh"; WORKFLOW="$ROOT/.github/workflows/build-26637-r1-heic-container-fix.yml"
OUT="$ROOT/build_26637_r1_heic_container_fix_outputs"; WORK="$ROOT/.build_26637_r1_heic_container_fix_work"
ARTZIP="$WORK/26636_r1_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_26636_r1_compiled_candidate"; AFTER="$WORK/candidate_26637_r1"; AFTER2="$WORK/candidate_26637_r1_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r1-heic-container-fix-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then
  [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26636 R1 artifact ZIP"
  LOCAL_ART="$2"
elif [[ -n "${1:-}" ]]; then fail "unknown argument: $1"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26637_R1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT APPLICABLE (0 modified GLSL)
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26637_R1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME AUTHORITY: NOT RUN
VERIFICATION MECHANICS AUTHORITY: NOT RUN
BACKUP STATUS: PASS (no backup requested; narrow HEIC publication correction)
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE DELTA AUDIT: NOT RUN
26636 R1 RUNTIME INHERITANCE: NOT RUN
JPEG/JPEG-R REFERENCE PUBLISHER FREEZE: NOT RUN
SABRE/MGC/DENOISE/EXPOSURE FREEZE: NOT RUN
DISPLAY-P3 SDR + EXISTING GAINMAP PARITY: NOT RUN
HEIC OPAQUE RGB / NO-ALPHA OWNER: NOT RUN
HEIC ICC/NCLX P3+SRGB AGREEMENT: NOT RUN
ANDROID16 HARDWARE HEVC 8-BIT 4:2:0 FREEZE: NOT RUN
HEVC CAPABILITY/SPS DIAGNOSTIC ONLY: NOT RUN
ISO 21496-1 HEIF CONTAINER AUTHORITY: NOT RUN
BASE/CANDIDATE MANIFEST COMPLETENESS: NOT RUN
PROTECTED/DNG/NATIVE/VENDOR INVARIANCE: NOT RUN
RUNTIME-EXPANDED GLSL RESERVED SCAN: NOT APPLICABLE (0 modified GLSL)
REAL GLSL COMPILE: NOT APPLICABLE (0 modified GLSL)
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
TARGET VERSION/BUILD: 0.9726637 / 26637
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26637_R1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26637_R1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26637_R1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26637_R1_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){ local authority_root="$1" live_root="$2" dest_root="$3"; rm -rf "$dest_root"; mkdir -p "$dest_root"; cp -a "$authority_root/." "$dest_root/"; rm -rf "$dest_root/app/src"; cp -a "$live_root/app/src" "$dest_root/app/"; cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"; cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"; }
compare_app_trees(){ python3 -S - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a=H(sys.argv[1]); b=H(sys.argv[2]); assert len(a)==1716 and a==b,(len(a),len(b),sorted(set(a)^set(b))[:10]); print('PASS authority-seeded candidate byte-identical: 1716 files')
PY
}
verify_package(){
  [[ -f "$HANDOFF" && -f "$UPLOADS" && -d "$ROOT/handoff_payload_26637_r1" ]] || fail "sealed 26637 package incomplete"
  [[ "$(find "$ROOT/handoff_payload_26637_r1" -type f | wc -l)" -eq 3 ]] || fail "sealed runtime payload must contain exactly 3 files"
  [[ "$(wc -l < "$CHANGED")" -eq 3 && ! -s "$ADDED" ]] || fail "26637 changed/add counts"
  sha256sum -c "$HANDOFF" >/dev/null
  [[ "$(wc -l < "$BASE_FULL")" -eq 1716 && "$(wc -l < "$CAND_FULL")" -eq 1716 ]] || fail "full app count"
  [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1713 && "$(wc -l < "$BASE_NATIVE")" -eq 802 && "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$BASE_DNG")" -eq 7 ]] || fail "protected manifest counts"
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
  if [[ -n "$LOCAL_ART" ]]; then set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed 3-path 26637 correction; no live app source packaged)"; return; fi
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  [[ "$(git rev-parse HEAD^)" == "$RUNTIME_AUTHORITY_COMMIT" ]] || fail "26637 must be one direct commit on exact successful 26636 R1.4 authority"
  git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | sort > "$WORK/actual_upload_scope.txt"
  sort "$UPLOADS" > "$WORK/expected_upload_scope.txt"
  diff -u "$WORK/expected_upload_scope.txt" "$WORK/actual_upload_scope.txt" || fail "26637 upload scope mismatch"
  ! grep -Eq '^app/' "$WORK/actual_upload_scope.txt" || fail "handoff commit contains live app source"
  set_report "CHANGED RUNTIME SCOPE" "PASS (exact 3-path runtime candidate allowlist; handoff-only repository commit)"
}
obtain_authority(){
  if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else
    [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
    curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
  fi
  [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26636 R1.4 artifact ZIP SHA"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  local tarball="$ARTDIR/build_26636_r1_heic_ultrahdr_outputs/26636_R1_candidate_app_source.tar.gz"
  [[ -f "$tarball" && "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "26636 candidate TAR authority"
  tar -xzf "$tarball" -C "$BASE"
  (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null) || fail "26636 exact base manifest"
  set_report "RUNTIME AUTHORITY" "PASS (successful 26636 R1.4 commit ${RUNTIME_AUTHORITY_COMMIT}/run ${BASE_RUN_ID}/artifact ${BASE_ARTIFACT_ID}/exact compiled candidate TAR)"
}
make_candidate(){
  python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26637_transform.txt"
  python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26637_transform_replay.txt"
  compare_app_trees "$AFTER" "$AFTER2"
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; cmp "$ROOT/handoff_payload_26637_r1/$rel" "$AFTER/$rel" || fail "sealed payload differs frozen candidate: $rel"; done < "$CHANGED"
  python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26637_semantic_validation.txt"
  python3 -S "$GATEVERIFY" "$BASE" "$AFTER" | tee "$OUT/26637_regressions.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26637_authority_candidate.txt"
  set_report "26636 R1 RUNTIME INHERITANCE" "PASS (exact successful compiler-tested 26636 candidate; only exact 3-path 26637 HEIC correction delta)"
  set_report "JPEG/JPEG-R REFERENCE PUBLISHER FREEZE" "PASS (no JPEG/JPEG-R source in changed allowlist)"
  set_report "SABRE/MGC/DENOISE/EXPOSURE FREEZE" "PASS (no merge/denoise/noise/exposure source in changed allowlist)"
  set_report "DISPLAY-P3 SDR + EXISTING GAINMAP PARITY" "PASS (existing ICC/gain-map producer and ISO metadata math preserved)"
  set_report "HEIC OPAQUE RGB / NO-ALPHA OWNER" "PASS (base Bitmap alpha discarded before libheif; interleaved RGB only)"
  set_report "HEIC ICC/NCLX P3+SRGB AGREEMENT" "PASS (Display-P3 ICC + IEC 61966-2-1 NCLX transfer)"
  set_report "ANDROID16 HARDWARE HEVC 8-BIT 4:2:0 FREEZE" "PASS (existing MediaCodec YUV420/hardware-only contract unchanged)"
  set_report "HEVC CAPABILITY/SPS DIAGNOSTIC ONLY" "PASS (capability + parsed emitted SPS logging added without encoder behavior change)"
  set_report "ISO 21496-1 HEIF CONTAINER AUTHORITY" "PASS (existing pinned libheif/libultrahdr gain-map structure preserved)"
  set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (1716 base / 1716 candidate / 1713 protected / 802 native / 778 vendor / 7 DNG)"
  set_report "PROTECTED/DNG/NATIVE/VENDOR INVARIANCE" "PASS"
}
verify_shaders(){
  python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26637_shader_validation.txt"
}
verify_successful_26636_mechanics(){
  if [[ -n "$LOCAL_ART" ]]; then python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26637_infrastructure_local.txt"; else python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" --git | tee "$OUT/26637_infrastructure_actions.txt"; fi
  set_report "INFRASTRUCTURE DELTA AUDIT" "PASS (successful-26636 ordering/isolation/Kotlin-Java/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; authority/scope/container validators only)"
  set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (exact successful-26636 build/workflow/transform Git blobs pinned and ordering replayed)"
}
verify_candidate_patches(){
  python3 -S "$PATCHVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26637_patch_validation.txt"
  set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"
}
install_frozen_candidate_live(){
  rm -rf "$ROOT/app/src"
  cp -a "$AFTER/app/src" "$ROOT/app/"
  cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"
  cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"
  compare_app_trees "$AFTER" "$LIVE_CANON"
}
postbuild_proof(){
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"
  compare_app_trees "$AFTER" "$POST"
  (cd "$POST" && sha256sum -c "$CAND_PROTECTED" >/dev/null && sha256sum -c "$CAND_NATIVE" >/dev/null && sha256sum -c "$CAND_VENDOR" >/dev/null && sha256sum -c "$CAND_DNG" >/dev/null) || fail "post-build protected invariance"
  python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26637_postbuild_semantic_validation.txt"
  python3 -S "$GATEVERIFY" "$BASE" "$POST" | tee "$OUT/26637_postbuild_regressions.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26637_postbuild_authority.txt"
  set_report "POST-BUILD INVARIANCE" "PASS (candidate/protected/DNG/native/vendor exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"
  tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26637_R1_candidate_app_source.tar.gz"
  sha256sum "$OUT/26637_R1_candidate_app_source.tar.gz" > "$OUT/26637_R1_candidate_app_source.tar.gz.sha256"
  cp "$CAND_FULL" "$OUT/26637_R1_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26637_R1_native_protected_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26637_R1_vendor_protected_postbuild.sha256"; cp "$CAND_DNG" "$OUT/26637_R1_dng_postbuild.sha256"
  set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests)"
}
verify_package
verify_scope
obtain_authority
make_candidate
verify_shaders
verify_successful_26636_mechanics
if [[ -n "$LOCAL_ART" ]]; then
  verify_candidate_patches
  set_report "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"
  set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real Kotlin/Java/NDK/full Android require Actions; GLSL N/A)"; set_report "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_report "EXACTLY ONE APK" "NOT RUN locally (Actions required)"; set_report "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN locally (Actions required)"
  set_compiler "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_compiler "NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_compiler "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_compiler "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"
  cp "$OUT/26637_R1_STRICT_HANDOFF_REPORT.txt" "$OUT/26637_local_prebuild_report.txt"
  pass "26637 R1 LOCAL PREBUILD PREPARED: exact successful-26636-R1.4 authority + exact 3-path HEIC container correction; real compiler/build gates explicitly unproven locally"
  exit 0
fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26637_gradle_language_compilers.log"
set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"
compare_app_trees "$AFTER" "$WORK/after_language_compiler_snapshot"
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26637_gradle_native_compiler.log"
set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
verify_candidate_patches
set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26637 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26637_gradle_assemble.log"
set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort)
[[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK"
mv "${apks[0]}" "$FINAL"
set_report "EXACTLY ONE APK" "PASS"; sha256sum "$FINAL" > "$OUT/26637_R1_APK.sha256"
postbuild_proof
pass "26637 R1 ACTIONS BUILD COMPLETE"
