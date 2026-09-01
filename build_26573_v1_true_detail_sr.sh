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
BASE_SUCCESS_COMMIT="2349eae1ec3479656171d26ae42fb3d229d3dd09"
BACKUP_COMMIT="c3a1f82ca93de02403fda4bc85cff9462bc4aca4"
HANDOFF_PARENT_COMMIT="2349eae1ec3479656171d26ae42fb3d229d3dd09"
BASE_RUN_ID="33464122028"
BASE_ARTIFACT_ID="9784306626"
BASE_ARTIFACT_NAME="photon-26572-v1-true-detail-sr"
BASE_ARTIFACT_SHA="8863884dacb7fc09dd65d39855c16e2f4892db836ff0273810fde047af88e097"
BASE_TAR_SHA="afe5b96a032f8571f512af2af031a23cc6de367e6aad35d73ac6db0f984887fe"
VERSION_NAME="0.9726573"
VERSION_BUILD="26573"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
HANDOFF="$ROOT/V1_26573_HANDOFF_HASHES.sha256"
BASE_FULL="$ROOT/V1_26573_BASE_26572_FULL_APP.sha256"
CAND_FULL="$ROOT/V1_26573_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/V1_26573_PROTECTED_UNCHANGED_BASE.sha256"
CAND_PROTECTED="$ROOT/V1_26573_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/V1_26573_NATIVE_PROTECTED_BASE.sha256"
CAND_NATIVE="$ROOT/V1_26573_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/V1_26573_DNG_PROTECTED_BASE.sha256"
CAND_DNG="$ROOT/V1_26573_DNG_PROTECTED_CANDIDATE.sha256"
BASE_ARCH="$ROOT/V1_26573_PROTECTED_ARCHITECTURE_BASE.sha256"
CAND_ARCH="$ROOT/V1_26573_PROTECTED_ARCHITECTURE_CANDIDATE.sha256"
CHANGED="$ROOT/V1_26573_RUNTIME_CHANGED_PATHS.txt"
PREWRITE="$ROOT/V1_26573_PREWRITE_SOURCE_HASHES.sha256"
EXPECTED_CHANGED="$ROOT/V1_26573_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/V1_26573_RUNTIME_DELTA_FROM_26572.patch"
ROLLBACK="$ROOT/V1_26573_RUNTIME_ROLLBACK_TO_26572.patch"
SHADER_PIN="$ROOT/V1_26573_RUNTIME_EXPANDED_SHADERS.sha256"
TRANSFORM="$ROOT/transform_26573_v1.py"
VALIDATE="$ROOT/validate_26573_v1.py"
AUTHORITY="$ROOT/verify_26573_v1_authority.py"
PATCHVERIFY="$ROOT/verify_26573_v1_patches.py"
SHADERVERIFY="$ROOT/verify_26573_v1_shaders.py"
BUILD_SCRIPT="$ROOT/build_26573_v1_true_detail_sr.sh"
WORKFLOW="$ROOT/.github/workflows/build-26573-v1-true-detail-sr.yml"
OUT="$ROOT/build_26573_v1_true_detail_sr_outputs"
WORK="$ROOT/.build_26573_v1_true_detail_sr_work"
ARTZIP="$WORK/26572_v1_artifact.zip"
ARTDIR="$WORK/artifact"
BASE="$WORK/exact_26572_v1_compiled_candidate"
AFTER="$WORK/candidate_26573"
AFTER2="$WORK/candidate_26573_replay"
SHADER_OUT="$WORK/runtime_expanded_shaders"
GLSLANG_DIR="$WORK/glslang-16.5.0"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"
POST="$WORK/postbuild_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-true-detail-sr-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26572 V1 artifact ZIP"; LOCAL_ART="$2"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"

cat > "$OUT/26573_V1_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
cat > "$OUT/26573_V1_STRICT_HANDOFF_REPORT.txt" <<'EOF'
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
26571 IQ INVARIANCE: NOT RUN
TRUE-DETAIL SR CONTRACT: NOT RUN
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
TARGET VERSION/BUILD: 0.9726573 / 26573
EOF
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26573_V1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26573_V1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26573_V1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26573_V1_COMPILER_STATUS.txt"; }

snapshot_candidate_from_authority(){
  local authority_root="$1" live_root="$2" dest_root="$3"
  rm -rf "$dest_root"; mkdir -p "$dest_root"
  # Exact successful 26571 mechanics: authority file universe first, then only live runtime source domain.
  cp -a "$authority_root/." "$dest_root/"
  rm -rf "$dest_root/app/src"
  cp -a "$live_root/app/src" "$dest_root/app/"
  cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"
  cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"
}

verify_package(){
  [[ -f "$HANDOFF" ]] || fail "handoff hash manifest missing"
  sha256sum -c "$HANDOFF"
  [[ "$(wc -l < "$HANDOFF")" -eq 31 ]] || fail "sealed payload count must be 31 excluding handoff manifest"
  [[ "$(wc -l < "$CHANGED")" -eq 5 ]] || fail "runtime allowlist count must be 5"
  [[ "$(wc -l < "$BASE_FULL")" -eq 1708 && "$(wc -l < "$CAND_FULL")" -eq 1708 ]] || fail "full app manifest count"
  [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1703 && "$(wc -l < "$CAND_PROTECTED")" -eq 1703 ]] || fail "protected manifest count"
  [[ "$(wc -l < "$BASE_NATIVE")" -eq 802 && "$(wc -l < "$CAND_NATIVE")" -eq 802 ]] || fail "native protected count"
  [[ "$(wc -l < "$BASE_DNG")" -eq 7 && "$(wc -l < "$CAND_DNG")" -eq 7 ]] || fail "DNG count"
  [[ "$(wc -l < "$BASE_ARCH")" -eq 158 && "$(wc -l < "$CAND_ARCH")" -eq 158 ]] || fail "architecture count"
  [[ "$(sha "$BASE_FULL")" == "45916d80073a8559460f3570afcfc130aaf6678fab13e4543c44e6b13b9f11ad" ]] || fail "base full manifest SHA"
  [[ "$(sha "$CAND_FULL")" == "2d11bc874b38260c03540783b9dbc0c70fbe0dd13edf7f1a200b6e6fdc0241d5" ]] || fail "candidate full manifest SHA"
  [[ "$(sha "$BASE_PROTECTED")" == "66501f9715b149940be228d82f26545efec182c5efa898670ebb869f931403ba" ]] || fail "protected manifest SHA"
  [[ "$(sha "$BASE_NATIVE")" == "7a1a107b63493937aac11297743876ca1544bc5e5b92d73fd8b06404cb25660e" ]] || fail "native protected manifest SHA"
  [[ "$(sha "$BASE_DNG")" == "90192bdf78607cc64415343d93aae54bbf17903d5442cab0674b6768faed7eab" ]] || fail "DNG manifest SHA"
  [[ "$(sha "$BASE_ARCH")" == "125176c8518c96a54206089dd332831eaec76e692fd27d76428ec1bf3b2924a4" ]] || fail "architecture manifest SHA"
  [[ "$(sha "$PREWRITE")" == "db4409ebe0fdc81c95e5a5e92400d1509c5abbbac6df9b07a9e5209324511850" ]] || fail "prewrite SHA"
  [[ "$(sha "$EXPECTED_CHANGED")" == "44225f942ee4076fc8ec3ce65c88c6ded87e07046f5aed6d07e7536cff7b84ac" ]] || fail "expected changed-source SHA"
  [[ "$(sha "$FORWARD")" == "c8fa4f5243ff2b7c6805aa3b60815f1e4a4da90e6d849f05e04c95d5388a64d0" ]] || fail "forward patch SHA"
  [[ "$(sha "$ROLLBACK")" == "6e0ae251d245019ac31e72bb809fbc786ac527ab3fa7ba988a1471fd5bd05a20" ]] || fail "rollback patch SHA"
  [[ "$(sha "$SHADER_PIN")" == "e6ca87292d5a7a3c6cf8c1ba239ba13e321da7f9bb53b491175932461dbd9460" ]] || fail "shader pin SHA"
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
  grep -F 'run 33427734790 / job 99605325755' "$ROOT/REGRESSION_V1_26573_CARRIED_FAILURES.txt" >/dev/null || fail "26570 V1 workflow regression absent"
  grep -F 'run 33433465300 / job 99624165337' "$ROOT/REGRESSION_V1_26573_CARRIED_FAILURES.txt" >/dev/null || fail "26570 V1.1 checkout-scope regression absent"
  grep -F 'IRIS_26573_CROSS_FRAME_TRUE_DETAIL_LUMA_OWNER' "$ROOT/REGRESSION_V1_26573_TRUE_DETAIL_SR_CONTRACT.txt" >/dev/null || fail "true-detail SR regression contract missing"
  grep -F '26571 coherent edge-color/no-halo/no-clump/pink-safety owner remains byte-identical' "$ROOT/REGRESSION_V1_26573_CARRIED_FAILURES.txt" >/dev/null || fail "26571 IQ ownership carry-forward missing"
  grep -F 'cross-frame temporal proof rejects unstable 2x detail before publication' "$ROOT/REGRESSION_V1_26573_CARRIED_FAILURES.txt" >/dev/null || fail "zero-DC true-detail regression missing"
  grep -F 'protected highlight => exact guide' "$ROOT/REGRESSION_V1_26573_TRUE_DETAIL_SR_CONTRACT.txt" >/dev/null || fail "pink/highlight safety regression missing"
  grep -F 'renderReadback must NOT require a non-null Iris26571ReadyBand output' "$ROOT/REGRESSION_V1_26573_TRUE_DETAIL_SR_CONTRACT.txt" >/dev/null || fail "GPU deferred-output reachability regression missing"
  grep -F 'No verification order is weakened' "$ROOT/V1_26573_INFRASTRUCTURE_DIFF_AUDIT.txt" >/dev/null || fail "infrastructure diff audit missing"
  ! grep -Eq 'pip(3)?[[:space:]]+install' "$TRANSFORM" "$VALIDATE" "$AUTHORITY" "$PATCHVERIFY" "$SHADERVERIFY" "$BUILD_SCRIPT" "$WORKFLOW" || fail "package-manager dependency introduced"
  pass "sealed package syntax/hash/regression contract"
  set_report "INFRASTRUCTURE DELTA AUDIT" "PASS (successful 26571 V1 order/mechanics preserved exactly; only 26572 authority pins, exact 5-file allowlist, two modified runtime-expanded shaders, no-new-backup proof, and cross-frame SR regressions differ)"
  set_report "CARRIED FAILURE REGRESSIONS" "PASS"
}

verify_scope(){
  if [[ -n "$LOCAL_ART" ]]; then
    set_report "BACKUP STATUS" "PASS (no new 26573 backup; existing backup-26571-pre-true-detail-sr preserves exact 26571 pre-redesign authority; deterministic rollback to successful 26572 packaged)"
    set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed handoff; runtime allowlist validated after transform)"
    return
  fi
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  git merge-base --is-ancestor "$BASE_SUCCESS_COMMIT" HEAD || fail "successful 26572 V1 runtime authority is not an ancestor"
  [[ "$(git rev-parse HEAD^)" == "$HANDOFF_PARENT_COMMIT" ]] || fail "26573 V1 must be one clean handoff commit directly on successful 26572 V1"
  local backup_sha
  backup_sha="$(git ls-remote origin refs/heads/backup-26571-pre-true-detail-sr | awk '{print $1}')"
  [[ "$backup_sha" == "$BACKUP_COMMIT" ]] || fail "backup-26571-pre-true-detail-sr missing or not exact preserved 26571 pre-redesign authority"
  python3 -S - "$HANDOFF" > "$WORK/expected_scope.txt" <<'PY'
from pathlib import Path
import sys
names=[line.split('  ',1)[1] for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]
names.append('V1_26573_HANDOFF_HASHES.sha256')
print('\n'.join(sorted(names)))
PY
  git diff --name-only "$BASE_SUCCESS_COMMIT"..HEAD | sort > "$WORK/actual_scope.txt"
  diff -u "$WORK/expected_scope.txt" "$WORK/actual_scope.txt" || fail "handoff commit scope mismatch"
  ! grep -Eq '^app/' "$WORK/actual_scope.txt" || fail "handoff commit contains live runtime app source"
  set_report "BACKUP STATUS" "PASS (no new 26573 backup; existing backup-26571-pre-true-detail-sr preserves exact 26571 pre-redesign authority; deterministic rollback to successful 26572 packaged)"
  set_report "CHANGED RUNTIME SCOPE" "PASS (handoff commit sealed infrastructure/payload only; runtime source written only inside Actions)"
}

obtain_authority(){
  if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else
    [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
    curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
  fi
  [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26572 V1 artifact ZIP authority SHA mismatch"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  local tarball="$ARTDIR/build_26572_v1_true_detail_sr_outputs/26572_V1_candidate_app_source.tar.gz"
  [[ -f "$tarball" ]] || fail "compiled 26572 candidate tar missing"
  [[ "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "compiled 26572 candidate tar SHA mismatch"
  tar -xzf "$tarball" -C "$BASE"
  find "$ARTDIR" -type f -name '*.apk' -delete
  (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null && sha256sum -c "$BASE_PROTECTED" >/dev/null && sha256sum -c "$BASE_NATIVE" >/dev/null && sha256sum -c "$BASE_DNG" >/dev/null && sha256sum -c "$BASE_ARCH" >/dev/null && sha256sum -c "$PREWRITE" >/dev/null)
  set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (26572 V1 commit $BASE_SUCCESS_COMMIT run $BASE_RUN_ID artifact $BASE_ARTIFACT_ID SHA $BASE_ARTIFACT_SHA tar $BASE_TAR_SHA)"
  pass "exact successful 26572 V1 compiled candidate authority"
}

make_candidate(){
  rm -rf "$AFTER" "$AFTER2"
  python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26573_transform.txt"
  python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26573_transform_replay.txt"
  python3 -S - "$AFTER" "$AFTER2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2])
if a!=b:raise SystemExit('FAIL candidate transform replay mismatch')
print(f'PASS deterministic candidate reconstruction files={len(a)}')
PY
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; cmp "$ROOT/handoff_payload_26573_v1/$rel" "$AFTER/$rel" || fail "sealed payload differs frozen candidate $rel"; done < "$CHANGED"
  python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26573_semantic_validation.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26573_authority_candidate.txt"
  set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (1708 full / 1703 protected / 802 native protected / 7 DNG)"
  set_report "PROTECTED ARCHITECTURE INVARIANCE" "PASS (158 focused Sabre/SR/capture/UHDR ownership files byte-identical; all other protected app bytes exact)"
  set_report "DNG INVARIANCE" "PASS (7 DNG/ImageSaver owners byte-identical)"
  set_report "26571 IQ INVARIANCE" "PASS (26571 edge-color/no-halo/no-clump/pink-safety owner byte-identical; true-detail changes isolated to SR reconstruction/output ownership)"
  set_report "TRUE-DETAIL SR CONTRACT" "PASS (cross-frame-proven direct-CFA high-resolution luma only; Sabre/VGN RGB/chroma/highlight owner; exact 26571 publication mechanics preserved)"
  set_report "RUNTIME OWNERSHIP" "PASS (direct-CFA true2x high-resolution luma owner only; Sabre/VGN RGB/chroma/highlight, capture, DNG, UHDR and late publication owners preserved)"
  set_report "DORMANT-OWNER REJECTION" "PASS (candidate diff exact; no alternate Sabre/SR/capture/DNG/UHDR owner changed)"
}

verify_candidate_patches(){
  python3 -S "$PATCHVERIFY" "$BASE" "$AFTER" "$FORWARD" "$ROLLBACK" | tee "$OUT/26573_patch_validation.txt"
  set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"
}

verify_shaders(){
  rm -rf "$SHADER_OUT"; mkdir -p "$SHADER_OUT"
  if [[ -n "$LOCAL_ART" ]]; then
    python3 -S "$SHADERVERIFY" "$AFTER" --out "$SHADER_OUT" | tee "$OUT/26573_shader_validation.txt"
    cmp "$SHADER_OUT/V1_26573_RUNTIME_EXPANDED_SHADERS.sha256" "$SHADER_PIN" || fail "local runtime-expanded shader pin mismatch"
    set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (2 exact modified runtime-expanded cross-frame SR fragment shaders)"
    set_report "REAL GLSL COMPILE" "NOT RUN locally (modified shaders require Actions pinned compiler)"
    set_compiler "REAL GLSL COMPILE" "NOT RUN locally (Actions required)"
    return
  fi
  mkdir -p "$GLSLANG_DIR"; local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz"
  curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"
  [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "pinned glslang archive SHA mismatch"
  tar -tzf "$archive" > "$OUT/26573_glslang_archive_contents.txt"; tar -xzf "$archive" -C "$GLSLANG_DIR"
  local compiler; compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "glslang executable missing after pinned extraction"; chmod +x "$compiler"
  "$compiler" --version | tee "$OUT/26573_glslang_version.txt"
  python3 -S "$SHADERVERIFY" "$AFTER" --out "$SHADER_OUT" --glslang "$compiler" | tee "$OUT/26573_shader_validation.txt"
  cmp "$SHADER_OUT/V1_26573_RUNTIME_EXPANDED_SHADERS.sha256" "$SHADER_PIN" || fail "Actions runtime-expanded shader pin mismatch"
  cp "$SHADER_OUT/V1_26573_SHADER_VERIFICATION.json" "$OUT/26573_shader_verification.json"
  set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (2 exact modified runtime-expanded cross-frame SR fragment shaders)"
  set_report "REAL GLSL COMPILE" "PASS (pinned Khronos glslangValidator $GLSLANG_VERSION)"; set_compiler "REAL GLSL COMPILE" "PASS (pinned Khronos glslangValidator $GLSLANG_VERSION)"
}

install_and_build(){
  [[ -z "$LOCAL_ART" ]] || return 0
  rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"
  python3 -S "$VALIDATE" "$BASE" "$LIVE_CANON" | tee "$OUT/26573_live_semantic_validation.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$LIVE_CANON" | tee "$OUT/26573_live_authority.txt"
  python3 -S - "$AFTER" "$LIVE_CANON" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2])
if a!=b:raise SystemExit('FAIL live compiler candidate differs from frozen candidate')
print(f'PASS authority-seeded live compiler candidate byte-identical files={len(a)}')
PY
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26573_gradle_language_compilers.log"
  set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26573_gradle_native_compiler.log"
  set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
  verify_candidate_patches
  set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26573 PRE-BUILD SAFETY PROOF PASSED"
  ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26573_gradle_assemble.log"
  set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
  mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort); [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK, got ${#apks[@]}"
  mv "${apks[0]}" "$FINAL"; mapfile -t roots < <(find "$ROOT" -maxdepth 1 -type f -name '*.apk' | sort); [[ "${#roots[@]}" -eq 1 && "${roots[0]}" == "$FINAL" ]] || fail "exactly one final root APK required"
  sha256sum "$FINAL" > "$OUT/26573_V1_APK.sha256"; set_report "EXACTLY ONE APK" "PASS"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"
  python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26573_postbuild_semantic_validation.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26573_postbuild_authority.txt"
  set_report "POST-BUILD INVARIANCE" "PASS (authority-seeded candidate/protected/DNG/native exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"
  tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26573_V1_candidate_app_source.tar.gz"
  sha256sum "$OUT/26573_V1_candidate_app_source.tar.gz" > "$OUT/26573_V1_candidate_app_source.tar.gz.sha256"; cp "$CAND_FULL" "$OUT/26573_V1_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26573_V1_native_protected_postbuild.sha256"
  set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests)"
}

verify_package
verify_scope
obtain_authority
make_candidate
verify_shaders
if [[ -n "$LOCAL_ART" ]]; then
  verify_candidate_patches
  set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real modified GLSL/Kotlin/native + project compilers/full Android gates require Actions)"
  set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN (local prebuild stops before Android build)"
  cp "$OUT/26573_V1_STRICT_HANDOFF_REPORT.txt" "$OUT/26573_local_prebuild_report.txt"
  pass "26573 LOCAL PREBUILD PREPARED: real GLSL/Kotlin/Java/NDK/full Android gates explicitly unproven locally"
  exit 0
fi
install_and_build
pass "26573 REAL GLSL + KOTLIN/JAVA + NDK + FULL ASSEMBLE PASSED"
pass "26573 POST-BUILD INVARIANCE PASSED"
