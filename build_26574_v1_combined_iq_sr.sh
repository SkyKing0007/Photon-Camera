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
BASE_SUCCESS_COMMIT="33e40571b62f734b9720cd4a993c42900806793e"
BACKUP_COMMIT="33e40571b62f734b9720cd4a993c42900806793e"
BACKUP_BRANCH="backup-26573-pre-combined-iq-sr"
HANDOFF_PARENT_COMMIT="33e40571b62f734b9720cd4a993c42900806793e"
BASE_RUN_ID="33467423463"
BASE_JOB_ID="99730063573"
BASE_ARTIFACT_ID="9785409671"
BASE_ARTIFACT_NAME="photon-26573-v1-true-detail-sr"
BASE_ARTIFACT_SHA="9335551157a04b0fef03c4d45baf0b4cf5753228c191445b081375c411bf9e91"
BASE_TAR_SHA="e6c9815c9e17a1ccbc271b3680fe9d8491e140675dba74c9bba52e61c9bfbd13"
VERSION_NAME="0.9726574"
VERSION_BUILD="26574"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
HANDOFF="$ROOT/V1_26574_HANDOFF_HASHES.sha256"
BASE_FULL="$ROOT/V1_26574_BASE_26573_FULL_APP.sha256"
CAND_FULL="$ROOT/V1_26574_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/V1_26574_PROTECTED_UNCHANGED_BASE.sha256"
CAND_PROTECTED="$ROOT/V1_26574_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/V1_26574_NATIVE_PROTECTED_BASE.sha256"
CAND_NATIVE="$ROOT/V1_26574_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/V1_26574_VENDOR_PROTECTED_BASE.sha256"
CAND_VENDOR="$ROOT/V1_26574_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/V1_26574_DNG_PROTECTED_BASE.sha256"
CAND_DNG="$ROOT/V1_26574_DNG_PROTECTED_CANDIDATE.sha256"
BASE_ARCH="$ROOT/V1_26574_PROTECTED_ARCHITECTURE_BASE.sha256"
CAND_ARCH="$ROOT/V1_26574_PROTECTED_ARCHITECTURE_CANDIDATE.sha256"
CHANGED="$ROOT/V1_26574_RUNTIME_CHANGED_PATHS.txt"
PREWRITE="$ROOT/V1_26574_PREWRITE_SOURCE_HASHES.sha256"
EXPECTED_CHANGED="$ROOT/V1_26574_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/V1_26574_RUNTIME_DELTA_FROM_26573.patch"
ROLLBACK="$ROOT/V1_26574_RUNTIME_ROLLBACK_TO_26573.patch"
SHADER_PIN="$ROOT/V1_26574_RUNTIME_EXPANDED_SHADERS.sha256"
TRANSFORM="$ROOT/transform_26574_v1.py"
VALIDATE="$ROOT/validate_26574_v1.py"
AUTHORITY="$ROOT/verify_26574_v1_authority.py"
PATCHVERIFY="$ROOT/verify_26574_v1_patches.py"
SHADERVERIFY="$ROOT/verify_26574_v1_shaders.py"
BUILD_SCRIPT="$ROOT/build_26574_v1_combined_iq_sr.sh"
WORKFLOW="$ROOT/.github/workflows/build-26574-v1-combined-iq-sr.yml"
OUT="$ROOT/build_26574_v1_combined_iq_sr_outputs"
WORK="$ROOT/.build_26574_v1_combined_iq_sr_work"
ARTZIP="$WORK/26573_v1_artifact.zip"
ARTDIR="$WORK/artifact"
BASE="$WORK/exact_26573_v1_compiled_candidate"
AFTER="$WORK/candidate_26574"
AFTER2="$WORK/candidate_26574_replay"
SHADER_OUT="$WORK/runtime_expanded_shaders"
GLSLANG_DIR="$WORK/glslang-16.5.0"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"
POST="$WORK/postbuild_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-combined-iq-sr-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26573 V1 artifact ZIP"; LOCAL_ART="$2"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"

cat > "$OUT/26574_V1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26574_V1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME OWNERSHIP: NOT RUN
DORMANT-OWNER REJECTION: NOT RUN
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
BACKUP STATUS: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE DELTA AUDIT: NOT RUN
CARRIED FAILURE REGRESSIONS: NOT RUN
BASE/CANDIDATE MANIFEST COMPLETENESS: NOT RUN
PROTECTED ARCHITECTURE INVARIANCE: NOT RUN
DNG INVARIANCE: NOT RUN
VENDOR INVARIANCE: NOT RUN
26573 TRUE2X INVARIANCE: NOT RUN
FOLIAGE/SKY TOPOLOGY CONTRACT: NOT RUN
SR ALIGNMENT REFINEMENT CONTRACT: NOT RUN
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
TARGET VERSION/BUILD: 0.9726574 / 26574
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26574_V1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26574_V1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26574_V1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26574_V1_COMPILER_STATUS.txt"; }

snapshot_candidate_from_authority(){
  local authority_root="$1" live_root="$2" dest_root="$3"
  rm -rf "$dest_root"; mkdir -p "$dest_root"
  # Exact successful 26573 mechanics: authority file universe first, then only live runtime source domain.
  cp -a "$authority_root/." "$dest_root/"
  rm -rf "$dest_root/app/src"
  cp -a "$live_root/app/src" "$dest_root/app/"
  cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"
  cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"
}

verify_package(){
  [[ -f "$HANDOFF" ]] || fail "handoff hash manifest missing"
  sha256sum -c "$HANDOFF"
  [[ "$(wc -l < "$HANDOFF")" -eq 32 ]] || fail "sealed payload count must be 32 excluding handoff manifest"
  [[ "$(wc -l < "$CHANGED")" -eq 4 ]] || fail "runtime allowlist count must be 4"
  [[ "$(wc -l < "$BASE_FULL")" -eq 1708 && "$(wc -l < "$CAND_FULL")" -eq 1708 ]] || fail "full app manifest count"
  [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1704 && "$(wc -l < "$CAND_PROTECTED")" -eq 1704 ]] || fail "protected manifest count"
  [[ "$(wc -l < "$BASE_NATIVE")" -eq 802 && "$(wc -l < "$CAND_NATIVE")" -eq 802 ]] || fail "native protected count"
  [[ "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$CAND_VENDOR")" -eq 778 ]] || fail "vendor protected count"
  [[ "$(wc -l < "$BASE_DNG")" -eq 7 && "$(wc -l < "$CAND_DNG")" -eq 7 ]] || fail "DNG count"
  [[ "$(wc -l < "$BASE_ARCH")" -eq 195 && "$(wc -l < "$CAND_ARCH")" -eq 195 ]] || fail "architecture count"
  [[ "$(sha "$BASE_FULL")" == "2d11bc874b38260c03540783b9dbc0c70fbe0dd13edf7f1a200b6e6fdc0241d5" ]] || fail "base full manifest SHA"
  [[ "$(sha "$CAND_FULL")" == "01881cc458d76b8b5b40ccb3105c75cdb263a6a248241711359547574cd0996b" ]] || fail "candidate full manifest SHA"
  [[ "$(sha "$BASE_PROTECTED")" == "4a5f4b2e4e90543d2d3a3d6618343bc425aa52ebb274dc04636026d145b05490" ]] || fail "protected manifest SHA"
  [[ "$(sha "$BASE_NATIVE")" == "7a1a107b63493937aac11297743876ca1544bc5e5b92d73fd8b06404cb25660e" ]] || fail "native protected manifest SHA"
  [[ "$(sha "$BASE_VENDOR")" == "7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8" ]] || fail "vendor protected manifest SHA"
  [[ "$(sha "$BASE_DNG")" == "90192bdf78607cc64415343d93aae54bbf17903d5442cab0674b6768faed7eab" ]] || fail "DNG manifest SHA"
  [[ "$(sha "$BASE_ARCH")" == "41e6782c57818d2c9dc86176bdf1d2c8e5de8671c91c45595befa95c5cac5204" ]] || fail "architecture manifest SHA"
  [[ "$(sha "$PREWRITE")" == "a08282f132e426ea8b95d6c96ead63c0d70c2ecb185d4ea53e7f5ca55b4e5924" ]] || fail "prewrite SHA"
  [[ "$(sha "$EXPECTED_CHANGED")" == "2e0d2e4e15bc3d0871399ec81f0088535b8febbb912ec02a7b080f042c13188e" ]] || fail "expected changed-source SHA"
  [[ "$(sha "$FORWARD")" == "30521458c8e5c96483feb9cab04cc6f550fa839fc1d2650518e8e8f765634e55" ]] || fail "forward patch SHA"
  [[ "$(sha "$ROLLBACK")" == "a812982c692ed216ff7cd7e7fcaa33d505b4ec397fb49e89f4888a09267362a6" ]] || fail "rollback patch SHA"
  [[ "$(sha "$SHADER_PIN")" == "3cb49ebfaf0864f612561539162bac98177816330442b8210a41867b6475639f" ]] || fail "shader pin SHA"
  python3 -S - "$TRANSFORM" "$VALIDATE" "$AUTHORITY" "$PATCHVERIFY" "$SHADERVERIFY" <<'PY'
import ast,sys
from pathlib import Path
allowed=set(sys.stdlib_module_names)
for raw in sys.argv[1:]:
 p=Path(raw);src=p.read_text();tree=ast.parse(src,filename=str(p));bad=[]
 for n in ast.walk(tree):
  names=[]
  if isinstance(n,ast.Import):names=[a.name.split('.',1)[0] for a in n.names]
  elif isinstance(n,ast.ImportFrom) and n.module:names=[n.module.split('.',1)[0]]
  bad += [x for x in names if x not in allowed]
 if bad:raise SystemExit(f'FAIL non-stdlib dependency {p.name}: {sorted(set(bad))}')
 compile(src,str(p),'exec')
print('PASS sealed Python stdlib-only syntax/import gate')
PY
  bash -n "$BUILD_SCRIPT"
  grep -F 'IRIS_26574_TOPOLOGY_PRESERVED_BRIGHT_SURFACE' "$ROOT/REGRESSION_V1_26574_COMBINED_IQ_SR_CONTRACT.txt" >/dev/null || fail "topology regression contract missing"
  grep -F 'IRIS_26574_JPEG_RETAINED_FLOW_REFINEMENT_ONLY' "$ROOT/REGRESSION_V1_26574_COMBINED_IQ_SR_CONTRACT.txt" >/dev/null || fail "SR refinement regression contract missing"
  grep -F 'run 33433465300 / job 99624165337' "$ROOT/REGRESSION_V1_26574_CARRIED_FAILURES.txt" >/dev/null || fail "26570 checkout-scope regression absent"
  grep -F 'No verification order is weakened' "$ROOT/V1_26574_INFRASTRUCTURE_DIFF_AUDIT.txt" >/dev/null || fail "infrastructure diff audit missing"
  ! grep -Eq 'pip(3)?[[:space:]]+install' "$TRANSFORM" "$VALIDATE" "$AUTHORITY" "$PATCHVERIFY" "$SHADERVERIFY" "$BUILD_SCRIPT" "$WORKFLOW" || fail "package-manager dependency introduced"
  pass "sealed package syntax/hash/regression contract"
  set_report "INFRASTRUCTURE DELTA AUDIT" "PASS (successful 26573 order/mechanics preserved; only authority pins, exact four-file scope, five modified runtime-expanded shaders, additive vendor manifest, and required 26573 backup proof differ)"
  set_report "CARRIED FAILURE REGRESSIONS" "PASS"
}

verify_scope(){
  if [[ -n "$LOCAL_ART" ]]; then
    set_report "BACKUP STATUS" "NOT RUN locally (Actions requires $BACKUP_BRANCH at exact successful 26573 before any live source write)"
    set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed handoff; runtime allowlist validated after transform)"
    return
  fi
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  git merge-base --is-ancestor "$BASE_SUCCESS_COMMIT" HEAD || fail "successful 26573 V1 runtime authority is not an ancestor"
  [[ "$(git rev-parse HEAD^)" == "$HANDOFF_PARENT_COMMIT" ]] || fail "26574 V1 must be one clean handoff commit directly on successful 26573 V1"
  local backup_sha
  backup_sha="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
  [[ "$backup_sha" == "$BACKUP_COMMIT" ]] || fail "$BACKUP_BRANCH missing or not exact successful 26573 authority"
  python3 -S - "$HANDOFF" > "$WORK/expected_scope.txt" <<'PY'
from pathlib import Path
import sys
names=[line.split('  ',1)[1] for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]
names.append('V1_26574_HANDOFF_HASHES.sha256')
print('\n'.join(sorted(names)))
PY
  git diff --name-only "$BASE_SUCCESS_COMMIT"..HEAD | sort > "$WORK/actual_scope.txt"
  diff -u "$WORK/expected_scope.txt" "$WORK/actual_scope.txt" || fail "handoff commit scope mismatch"
  ! grep -Eq '^app/' "$WORK/actual_scope.txt" || fail "handoff commit contains live runtime app source"
  set_report "BACKUP STATUS" "PASS ($BACKUP_BRANCH == exact successful 26573 $BACKUP_COMMIT)"
  set_report "CHANGED RUNTIME SCOPE" "PASS (handoff commit sealed infrastructure/payload only; runtime source written only inside Actions)"
}

obtain_authority(){
  if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else
    [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
    curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
  fi
  [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26573 V1 artifact ZIP authority SHA mismatch"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  local tarball="$ARTDIR/build_26573_v1_true_detail_sr_outputs/26573_V1_candidate_app_source.tar.gz"
  [[ -f "$tarball" ]] || fail "compiled 26573 candidate tar missing"
  [[ "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "compiled 26573 candidate tar SHA mismatch"
  tar -xzf "$tarball" -C "$BASE"
  find "$ARTDIR" -type f -name '*.apk' -delete
  (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null && sha256sum -c "$BASE_PROTECTED" >/dev/null && sha256sum -c "$BASE_NATIVE" >/dev/null && sha256sum -c "$BASE_VENDOR" >/dev/null && sha256sum -c "$BASE_DNG" >/dev/null && sha256sum -c "$BASE_ARCH" >/dev/null && sha256sum -c "$PREWRITE" >/dev/null)
  set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (26573 V1 commit $BASE_SUCCESS_COMMIT run $BASE_RUN_ID job $BASE_JOB_ID artifact $BASE_ARTIFACT_ID SHA $BASE_ARTIFACT_SHA tar $BASE_TAR_SHA)"
  pass "exact successful 26573 V1 compiled candidate authority"
}

make_candidate(){
  rm -rf "$AFTER" "$AFTER2"
  python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26574_transform.txt"
  python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26574_transform_replay.txt"
  python3 -S - "$AFTER" "$AFTER2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2])
if a!=b:raise SystemExit('FAIL candidate transform replay mismatch')
print(f'PASS deterministic candidate reconstruction files={len(a)}')
PY
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; cmp "$ROOT/handoff_payload_26574_v1/$rel" "$AFTER/$rel" || fail "sealed payload differs frozen candidate $rel"; done < "$CHANGED"
  python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26574_semantic_validation.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26574_authority_candidate.txt"
  set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (1708 full / 1704 protected / 802 native / 778 vendor / 7 DNG / 195 protected architecture)"
  set_report "PROTECTED ARCHITECTURE INVARIANCE" "PASS (195 unchanged active processing/capture/UHDR/DNG architecture files byte-identical; all other protected app bytes exact)"
  set_report "DNG INVARIANCE" "PASS (7 DNG/ImageSaver owners byte-identical)"
  set_report "VENDOR INVARIANCE" "PASS (778 persisted native vendor/dependency files byte-identical)"
  set_report "26573 TRUE2X INVARIANCE" "PASS (existing true2x merge/resolve/guide, top-2-per-phase/max-8 selection, temporal proof and GPU/CPU accumulation owners preserved)"
  set_report "FOLIAGE/SKY TOPOLOGY CONTRACT" "PASS (26570/26571 edge/pink protections retained; radius-2/perpendicular same-surface topology added)"
  set_report "SR ALIGNMENT REFINEMENT CONTRACT" "PASS (JPEG-retained-only, <=0.5 RAW-pixel residual, conditioned/unique/improving, proven-flow fallback, DNG/Sabre isolation)"
  set_report "RUNTIME OWNERSHIP" "PASS (shared VGN topology + JPEG true2x retained-flow refinement only; capture/DNG/UHDR/native/publication owners preserved)"
  set_report "DORMANT-OWNER REJECTION" "PASS (candidate diff exact; unchanged Sabre alignment/merge and existing true2x GPU/CPU accumulation owners byte-proven)"
}

verify_candidate_patches(){
  python3 -S "$PATCHVERIFY" "$BASE" "$AFTER" "$FORWARD" "$ROLLBACK" | tee "$OUT/26574_patch_validation.txt"
  set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"
}

verify_shaders(){
  rm -rf "$SHADER_OUT"; mkdir -p "$SHADER_OUT"
  if [[ -n "$LOCAL_ART" ]]; then
    python3 -S "$SHADERVERIFY" "$AFTER" --out "$SHADER_OUT" | tee "$OUT/26574_shader_validation.txt"
    cmp "$SHADER_OUT/V1_26574_RUNTIME_EXPANDED_SHADERS.sha256" "$SHADER_PIN" || fail "local runtime-expanded shader pin mismatch"
    set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (5 exact modified runtime-expanded VGN/SR shaders)"
    set_report "REAL GLSL COMPILE" "NOT RUN locally (modified shaders require Actions pinned compiler)"
    set_compiler "REAL GLSL COMPILE" "NOT RUN locally (Actions required)"
    return
  fi
  mkdir -p "$GLSLANG_DIR"; local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz"
  curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"
  [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "pinned glslang archive SHA mismatch"
  tar -tzf "$archive" > "$OUT/26574_glslang_archive_contents.txt"; tar -xzf "$archive" -C "$GLSLANG_DIR"
  local compiler; compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "glslang executable missing after pinned extraction"; chmod +x "$compiler"
  "$compiler" --version | tee "$OUT/26574_glslang_version.txt"
  python3 -S "$SHADERVERIFY" "$AFTER" --out "$SHADER_OUT" --glslang "$compiler" | tee "$OUT/26574_shader_validation.txt"
  cmp "$SHADER_OUT/V1_26574_RUNTIME_EXPANDED_SHADERS.sha256" "$SHADER_PIN" || fail "Actions runtime-expanded shader pin mismatch"
  cp "$SHADER_OUT/V1_26574_SHADER_VERIFICATION.json" "$OUT/26574_shader_verification.json"
  set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (5 exact modified runtime-expanded VGN/SR shaders)"
  set_report "REAL GLSL COMPILE" "PASS (pinned Khronos glslangValidator $GLSLANG_VERSION)"; set_compiler "REAL GLSL COMPILE" "PASS (pinned Khronos glslangValidator $GLSLANG_VERSION)"
}

install_and_build(){
  [[ -z "$LOCAL_ART" ]] || return 0
  rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"
  python3 -S "$VALIDATE" "$BASE" "$LIVE_CANON" | tee "$OUT/26574_live_semantic_validation.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$LIVE_CANON" | tee "$OUT/26574_live_authority.txt"
  python3 -S - "$AFTER" "$LIVE_CANON" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2])
if a!=b:raise SystemExit('FAIL live compiler candidate differs from frozen candidate')
print(f'PASS authority-seeded live compiler candidate byte-identical files={len(a)}')
PY
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26574_gradle_language_compilers.log"
  set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26574_gradle_native_compiler.log"
  set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
  verify_candidate_patches
  set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26574 PRE-BUILD SAFETY PROOF PASSED"
  ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26574_gradle_assemble.log"
  set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
  mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort); [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK, got ${#apks[@]}"
  mv "${apks[0]}" "$FINAL"; mapfile -t roots < <(find "$ROOT" -maxdepth 1 -type f -name '*.apk' | sort); [[ "${#roots[@]}" -eq 1 && "${roots[0]}" == "$FINAL" ]] || fail "exactly one final root APK required"
  sha256sum "$FINAL" > "$OUT/26574_V1_APK.sha256"; set_report "EXACTLY ONE APK" "PASS"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"
  python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26574_postbuild_semantic_validation.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26574_postbuild_authority.txt"
  set_report "POST-BUILD INVARIANCE" "PASS (authority-seeded candidate/protected/DNG/native/vendor exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"
  tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26574_V1_candidate_app_source.tar.gz"
  sha256sum "$OUT/26574_V1_candidate_app_source.tar.gz" > "$OUT/26574_V1_candidate_app_source.tar.gz.sha256"
  cp "$CAND_FULL" "$OUT/26574_V1_candidate_full_app.sha256"
  cp "$CAND_NATIVE" "$OUT/26574_V1_native_protected_postbuild.sha256"
  cp "$CAND_VENDOR" "$OUT/26574_V1_vendor_protected_postbuild.sha256"
  set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests)"
}

verify_package
verify_scope
obtain_authority
make_candidate
verify_shaders
if [[ -n "$LOCAL_ART" ]]; then
  verify_candidate_patches
  set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real modified GLSL/Kotlin/Java/NDK + project compilers/full Android gates require Actions)"
  set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN (local prebuild stops before Android build)"
  cp "$OUT/26574_V1_STRICT_HANDOFF_REPORT.txt" "$OUT/26574_local_prebuild_report.txt"
  pass "26574 LOCAL PREBUILD PREPARED: real GLSL/Kotlin/Java/NDK/full Android gates explicitly unproven locally"
  exit 0
fi
install_and_build
pass "26574 REAL GLSL + KOTLIN/JAVA + NDK + FULL ASSEMBLE PASSED"
pass "26574 POST-BUILD INVARIANCE PASSED"
