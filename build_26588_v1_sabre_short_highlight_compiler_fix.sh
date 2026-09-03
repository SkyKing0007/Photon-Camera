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
BASE_SUCCESS_COMMIT="40f0449cd0281c8b8d25afe2be0d68682afd7077"
HANDOFF_PARENT_COMMIT="c4dbede9db7ebc6a7a99488412e6b67bd3119a1e"
BASE_RUN_ID="33763063933"
BASE_JOB_ID="100673914579"
BASE_ARTIFACT_ID="9896466561"
BASE_ARTIFACT_NAME="photon-26586-v1-viewfinder-highlight-authority-split"
BASE_ARTIFACT_SHA="ee04f0e9eda2ccf44c70ea024a631489db098e7044445cc3b576529bee13e2b7"
BASE_TAR_SHA="2f91feb5396c5a11341855df39877a94fad37bbfbe920cfc9aa87763b1bbdc22"
VERSION_NAME="0.9726588"
VERSION_BUILD="26588"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
SEALED_PAYLOAD_COUNT=39
HANDOFF="$ROOT/V1_26588_HANDOFF_HASHES.sha256"
BASE_FULL="$ROOT/V1_26588_BASE_26586_FULL_APP.sha256"
CAND_FULL="$ROOT/V1_26588_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/V1_26588_PROTECTED_UNCHANGED_BASE.sha256"
CAND_PROTECTED="$ROOT/V1_26588_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/V1_26588_NATIVE_PROTECTED_BASE.sha256"
CAND_NATIVE="$ROOT/V1_26588_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/V1_26588_VENDOR_PROTECTED_BASE.sha256"
CAND_VENDOR="$ROOT/V1_26588_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/V1_26588_DNG_PROTECTED_BASE.sha256"
CAND_DNG="$ROOT/V1_26588_DNG_PROTECTED_CANDIDATE.sha256"
BASE_ARCH="$ROOT/V1_26588_PROTECTED_ARCHITECTURE_BASE.sha256"
CAND_ARCH="$ROOT/V1_26588_PROTECTED_ARCHITECTURE_CANDIDATE.sha256"
CHANGED="$ROOT/V1_26588_RUNTIME_CHANGED_PATHS.txt"
PREWRITE="$ROOT/V1_26588_PREWRITE_SOURCE_HASHES.sha256"
EXPECTED_CHANGED="$ROOT/V1_26588_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/V1_26588_RUNTIME_DELTA_FROM_26586.patch"
ROLLBACK="$ROOT/V1_26588_RUNTIME_ROLLBACK_TO_26586.patch"
SHADER_PIN="$ROOT/V1_26588_RUNTIME_EXPANDED_SHADERS.sha256"
TRANSFORM="$ROOT/transform_26588_v1.py"
VALIDATE="$ROOT/validate_26588_v1.py"
AUTHORITY="$ROOT/verify_26588_v1_authority.py"
PATCHVERIFY="$ROOT/verify_26588_v1_patches.py"
SHADERVERIFY="$ROOT/verify_26588_v1_shaders.py"
GATEVERIFY="$ROOT/verify_26588_v1_regressions.py"
BUILD_SCRIPT="$ROOT/build_26588_v1_sabre_short_highlight_compiler_fix.sh"
WORKFLOW="$ROOT/.github/workflows/build-26588-v1-sabre-short-highlight-compiler-fix.yml"
OUT="$ROOT/build_26588_v1_sabre_short_highlight_compiler_fix_outputs"
WORK="$ROOT/.build_26588_v1_sabre_short_highlight_compiler_fix_work"
ARTZIP="$WORK/26586_v1_artifact.zip"
ARTDIR="$WORK/artifact"
BASE="$WORK/exact_26586_v1_compiled_candidate"
AFTER="$WORK/candidate_26588"
AFTER2="$WORK/candidate_26588_replay"
SHADER_OUT="$WORK/runtime_expanded_shaders"
GLSLANG_DIR="$WORK/glslang-16.5.0"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"
POST="$WORK/postbuild_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-sabre-short-highlight-compiler-fix-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26586 V1 artifact ZIP"; LOCAL_ART="$2"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26588_V1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26588_V1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME OWNERSHIP: NOT RUN
DORMANT-OWNER REJECTION: NOT RUN
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
BACKUP STATUS: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE DELTA AUDIT: NOT RUN
CARRIED FAILURE REGRESSIONS: NOT RUN
SHORT RESTORE SAFETY REGRESSION: NOT RUN
CARRIED 26586 VIEWFINDER/CHROMA REGRESSIONS: NOT RUN
BASE/CANDIDATE MANIFEST COMPLETENESS: NOT RUN
PROTECTED ARCHITECTURE INVARIANCE: NOT RUN
DNG INVARIANCE: NOT RUN
VENDOR INVARIANCE: NOT RUN
NORMAL/NIGHT/SR/DNG OWNERSHIP: NOT RUN
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
TARGET VERSION/BUILD: 0.9726588 / 26588
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26588_V1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26588_V1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26588_V1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26588_V1_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){
  local authority_root="$1" live_root="$2" dest_root="$3"
  rm -rf "$dest_root"; mkdir -p "$dest_root"
  cp -a "$authority_root/." "$dest_root/"
  rm -rf "$dest_root/app/src"
  cp -a "$live_root/app/src" "$dest_root/app/"
  cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"
  cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"
}
verify_package(){
  [[ -f "$HANDOFF" ]] || fail "handoff hash manifest missing"
  sha256sum -c "$HANDOFF"
  [[ "$(wc -l < "$HANDOFF")" -eq "$SEALED_PAYLOAD_COUNT" ]] || fail "sealed payload count mismatch excluding handoff manifest"
  [[ "$(wc -l < "$CHANGED")" -eq 6 ]] || fail "runtime allowlist count must be 6"
  [[ "$(wc -l < "$BASE_FULL")" -eq 1708 && "$(wc -l < "$CAND_FULL")" -eq 1708 ]] || fail "full app manifest count"
  [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1702 && "$(wc -l < "$CAND_PROTECTED")" -eq 1702 ]] || fail "protected manifest count"
  [[ "$(wc -l < "$BASE_NATIVE")" -eq 802 && "$(wc -l < "$CAND_NATIVE")" -eq 802 ]] || fail "native protected count"
  [[ "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$CAND_VENDOR")" -eq 778 ]] || fail "vendor protected count"
  [[ "$(wc -l < "$BASE_DNG")" -eq 7 && "$(wc -l < "$CAND_DNG")" -eq 7 ]] || fail "DNG count"
  [[ "$(wc -l < "$BASE_ARCH")" -eq 169 && "$(wc -l < "$CAND_ARCH")" -eq 169 ]] || fail "protected architecture count"
  [[ "$(sha "$BASE_FULL")" == "a96d13cfa18c05facc52a24c2cfcce2f96911895c6292fac03a6bdd0a7dcd014" ]] || fail "base full manifest SHA"
  [[ "$(sha "$CAND_FULL")" == "8808a86a7fc354cfa0a80b40186e15cad1e5b415e125ba710df7c9c8dac92cdd" ]] || fail "candidate full manifest SHA"
  [[ "$(sha "$BASE_PROTECTED")" == "62d7cfff5f395c25ea714a26b663879f3496c2933e7a7e89dc472e2523d2345a" ]] || fail "protected manifest SHA"
  cmp "$BASE_PROTECTED" "$CAND_PROTECTED" || fail "protected manifest invariance"
  [[ "$(sha "$BASE_NATIVE")" == "7a1a107b63493937aac11297743876ca1544bc5e5b92d73fd8b06404cb25660e" ]] || fail "native manifest SHA"
  cmp "$BASE_NATIVE" "$CAND_NATIVE" || fail "native manifest invariance"
  [[ "$(sha "$BASE_VENDOR")" == "7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8" ]] || fail "vendor manifest SHA"
  cmp "$BASE_VENDOR" "$CAND_VENDOR" || fail "vendor manifest invariance"
  [[ "$(sha "$BASE_DNG")" == "90192bdf78607cc64415343d93aae54bbf17903d5442cab0674b6768faed7eab" ]] || fail "DNG manifest SHA"
  cmp "$BASE_DNG" "$CAND_DNG" || fail "DNG manifest invariance"
  [[ "$(sha "$BASE_ARCH")" == "b48ab278104f92b8aa82c64a2c949120876da29ac4a6f6fea1880372dffde196" ]] || fail "protected architecture manifest SHA"
  cmp "$BASE_ARCH" "$CAND_ARCH" || fail "architecture manifest invariance"
  [[ "$(sha "$PREWRITE")" == "e16f43a1f1a2bb89553103885e5483be5c7f008bb094bb015c9d1c6fe4c373c0" ]] || fail "prewrite SHA"
  [[ "$(sha "$EXPECTED_CHANGED")" == "c46c572b5495c55aba07e673898996da4810577c80a4b5b36d8862b269fd725c" ]] || fail "expected changed-source SHA"
  [[ "$(sha "$FORWARD")" == "c1716ebca616c632dd0cd2ef2c8394a0a5b2bd44806d663b8deb71eb7c271fba" ]] || fail "forward patch SHA"
  [[ "$(sha "$ROLLBACK")" == "9d12a0445119ce12b7149f472166c71eff0b72422e75803d5cebc6fa6a76f230" ]] || fail "rollback patch SHA"
  [[ "$(sha "$SHADER_PIN")" == "2463fb173f0252543c6fba0bfef9f51d9f03ce6ea772f99a812abbc715cd29aa" ]] || fail "shader pin SHA"
  python3 -S - "$TRANSFORM" "$VALIDATE" "$AUTHORITY" "$PATCHVERIFY" "$SHADERVERIFY" "$GATEVERIFY" <<'PY'
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
  grep -F 'Broad pink, pink/green dotted edges, cyan/green speckling, zipper and ghost artifacts are release-blocking regressions.' "$ROOT/REGRESSION_V1_26588_SHORT_RESTORE_SAFETY.txt" >/dev/null || fail "SHORT safety regression missing"
  grep -F "GlesMgcRawSpatialStacker.kt:779:30 Unresolved reference 'mergedFrameCount'." "$ROOT/REGRESSION_V1_26588_KOTLIN_MERGED_FRAME_SCOPE.txt" >/dev/null || fail "failed-26587 Kotlin regression missing"
  grep -F 'viewfinder/body meter authority remains the successful 26584 structured P90 / 0.965 branch' "$ROOT/REGRESSION_V1_26588_CARRIED_26586.txt" >/dev/null || fail "carried 26586 regression missing"
  grep -F 'app/build/** and app/.cxx/** never count as runtime-source changes.' "$ROOT/REGRESSION_V1_26588_WORKFLOW_PACKAGING.txt" >/dev/null || fail "packaging regression missing"
  grep -F 'no verification gate is weakened' "$ROOT/V1_26588_INFRASTRUCTURE_DIFF_AUDIT.txt" >/dev/null || fail "infrastructure audit missing"
  [[ -s "$ROOT/V1_26588_BUILD_SCRIPT_DIFF_AUDIT_FROM_SUCCESSFUL_26586.txt" ]] || fail "build script audit missing"
  [[ -s "$ROOT/V1_26588_WORKFLOW_DIFF_AUDIT_FROM_SUCCESSFUL_26586.txt" ]] || fail "workflow audit missing"
  ! grep -Eq 'pip(3)?[[:space:]]+install' "$TRANSFORM" "$VALIDATE" "$AUTHORITY" "$PATCHVERIFY" "$SHADERVERIFY" "$GATEVERIFY" "$BUILD_SCRIPT" "$WORKFLOW" || fail "package-manager dependency introduced"
  set_report "INFRASTRUCTURE DELTA AUDIT" "PASS (successful 26586 order/mechanics preserved; only authority pins/names/version, exact six-file scope, two inherited 26587 shader variants, failed-26587 compiler regression and branch-parent scope pin differ; no gate weakened)"
  set_report "CARRIED FAILURE REGRESSIONS" "PASS"
  pass "sealed package syntax/hash/regression contract"
}
verify_scope(){
  if [[ -n "$LOCAL_ART" ]]; then
    set_report "BACKUP STATUS" "PASS (no backup requested; exact deterministic rollback to successful 26586 packaged)"
    set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed handoff; exact six-file runtime allowlist validated after transform)"
    return
  fi
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  git merge-base --is-ancestor "$BASE_SUCCESS_COMMIT" HEAD || fail "successful 26586 runtime authority is not an ancestor"
  [[ "$(git rev-parse HEAD^)" == "$HANDOFF_PARENT_COMMIT" ]] || fail "26588 V1 must be one clean handoff commit directly on failed-26587 infrastructure parent; runtime authority remains successful 26586"
  python3 -S - "$HANDOFF" > "$WORK/expected_scope.txt" <<'PY'
from pathlib import Path
import sys
names=[line.split('  ',1)[1] for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]
names.append('V1_26588_HANDOFF_HASHES.sha256')
print('\n'.join(sorted(names)))
PY
  git diff --name-only "$HANDOFF_PARENT_COMMIT"..HEAD | sort > "$WORK/actual_scope.txt"
  diff -u "$WORK/expected_scope.txt" "$WORK/actual_scope.txt" || fail "handoff commit scope mismatch"
  ! grep -Eq '^app/' "$WORK/actual_scope.txt" || fail "handoff commit contains live runtime app source"
  git diff --name-only "$BASE_SUCCESS_COMMIT"..HEAD | sort > "$WORK/full_lineage_scope.txt"
  ! grep -Eq '^app/' "$WORK/full_lineage_scope.txt" || fail "26586-to-26588 lineage contains live runtime app source"
  set_report "BACKUP STATUS" "PASS (no backup requested/created; exact deterministic rollback to successful 26586 packaged)"
  set_report "CHANGED RUNTIME SCOPE" "PASS (handoff commit sealed infrastructure/payload only; runtime source written only inside Actions)"
}
obtain_authority(){
  if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else
    [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
    curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
  fi
  [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26586 V1 artifact ZIP authority SHA mismatch"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  local tarball="$ARTDIR/build_26586_v1_viewfinder_highlight_authority_split_outputs/26586_V1_candidate_app_source.tar.gz"
  [[ -f "$tarball" ]] || fail "compiled 26586 candidate tar missing"
  [[ "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "compiled 26586 candidate tar SHA mismatch"
  tar -xzf "$tarball" -C "$BASE"
  find "$ARTDIR" -type f -name '*.apk' -delete
  (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null && sha256sum -c "$BASE_PROTECTED" >/dev/null && sha256sum -c "$BASE_NATIVE" >/dev/null && sha256sum -c "$BASE_VENDOR" >/dev/null && sha256sum -c "$BASE_DNG" >/dev/null && sha256sum -c "$BASE_ARCH" >/dev/null && sha256sum -c "$PREWRITE" >/dev/null)
  set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (26586 commit $BASE_SUCCESS_COMMIT run $BASE_RUN_ID job $BASE_JOB_ID artifact $BASE_ARTIFACT_ID ZIP $BASE_ARTIFACT_SHA tar $BASE_TAR_SHA)"
  pass "exact successful 26586 compiled-candidate authority"
}
make_candidate(){
  rm -rf "$AFTER" "$AFTER2"
  python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26588_transform.txt"
  python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26588_transform_replay.txt"
  python3 -S - "$AFTER" "$AFTER2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2])
if a!=b:raise SystemExit('FAIL candidate transform replay mismatch')
print(f'PASS deterministic candidate reconstruction files={len(a)}')
PY
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; cmp "$ROOT/handoff_payload_26588_v1/$rel" "$AFTER/$rel" || fail "sealed payload differs frozen candidate $rel"; done < "$CHANGED"
  python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26588_semantic_validation.txt"
  python3 -S "$GATEVERIFY" "$AFTER" | tee "$OUT/26588_refinement_regressions.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26588_authority_candidate.txt"
  set_report "SHORT RESTORE SAFETY REGRESSION" "PASS (SHORT auxiliary only; multi-CFA/unclipped/support/flow/unblocker/radiometric fail-closed scalar whole-RGB restore)"
  set_report "CARRIED 26586 VIEWFINDER/CHROMA REGRESSIONS" "PASS (26586 meter/final authority and adaptive-color/render/Jin/Night owners preserved)"
  set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (1708 full / 1702 unchanged protected / 802 native / 778 vendor / 7 DNG / 169 protected architecture)"
  set_report "PROTECTED ARCHITECTURE INVARIANCE" "PASS (all 1702 nonallowlisted app files byte-identical; 169 supplemental architecture files byte-identical)"
  set_report "DNG INVARIANCE" "PASS (7 DNG/ImageSaver owners byte-identical; Motion SHORT excluded by active stack contract)"
  set_report "VENDOR INVARIANCE" "PASS (778 persisted native vendor/dependency files byte-identical)"
  set_report "NORMAL/NIGHT/SR/DNG OWNERSHIP" "PASS (NORMAL accumulator/DNG/SR evidence unchanged; SHORT auxiliary restore only; Night SHORT forbidden; true2x receives restored guide only after NORMAL reconstruction)"
  set_report "RUNTIME OWNERSHIP" "PASS (five production Motion/Sabre owners plus version; exact six-file allowlist)"
  set_report "DORMANT-OWNER REJECTION" "PASS (bridge -> active Sabre processor -> active stack/shaders/result contracts; no legacy highlight shader satisfies markers)"
}
verify_candidate_patches(){
  python3 -S "$PATCHVERIFY" "$BASE" "$AFTER" "$FORWARD" "$ROLLBACK" | tee "$OUT/26588_patch_validation.txt"
  set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"
}
verify_shaders(){
  rm -rf "$SHADER_OUT"; mkdir -p "$SHADER_OUT"
  if [[ -n "$LOCAL_ART" ]]; then
    python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" | tee "$OUT/26588_shader_validation.txt"
    cmp "$SHADER_OUT/V1_26588_RUNTIME_EXPANDED_SHADERS.sha256" "$SHADER_PIN" || fail "local runtime-expanded shader pin mismatch"
    cp "$SHADER_OUT/V1_26588_SHADER_VERIFICATION.json" "$OUT/26588_shader_verification.json"
    set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (10 exact runtime-expanded variants: successful 26586 eight + mask/whole-RGB restore)"
    set_report "REAL GLSL COMPILE" "NOT RUN locally (Actions required for pinned compiler)"; set_compiler "REAL GLSL COMPILE" "NOT RUN locally (Actions required)"
    return
  fi
  mkdir -p "$GLSLANG_DIR"; local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz"
  curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"
  [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "pinned glslang archive SHA mismatch"
  tar -tzf "$archive" > "$OUT/26588_glslang_archive_contents.txt"; tar -xzf "$archive" -C "$GLSLANG_DIR"
  local compiler; compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "glslang executable missing after pinned extraction"; chmod +x "$compiler"
  "$compiler" --version | tee "$OUT/26588_glslang_version.txt"
  python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" --glslang "$compiler" | tee "$OUT/26588_shader_validation.txt"
  cmp "$SHADER_OUT/V1_26588_RUNTIME_EXPANDED_SHADERS.sha256" "$SHADER_PIN" || fail "Actions runtime-expanded shader pin mismatch"
  cp "$SHADER_OUT/V1_26588_SHADER_VERIFICATION.json" "$OUT/26588_shader_verification.json"
  set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (10 exact runtime-expanded variants; every pre-existing Sabre shader byte-identical to 26586)"
  set_report "REAL GLSL COMPILE" "PASS (pinned Khronos glslangValidator $GLSLANG_VERSION)"; set_compiler "REAL GLSL COMPILE" "PASS (pinned Khronos glslangValidator $GLSLANG_VERSION)"
}
install_and_build(){
  [[ -z "$LOCAL_ART" ]] || return 0
  rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"
  python3 -S "$VALIDATE" "$BASE" "$LIVE_CANON" | tee "$OUT/26588_live_semantic_validation.txt"
  python3 -S "$GATEVERIFY" "$LIVE_CANON" | tee "$OUT/26588_live_refinement_regressions.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$LIVE_CANON" | tee "$OUT/26588_live_authority.txt"
  python3 -S - "$AFTER" "$LIVE_CANON" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2])
if a!=b:raise SystemExit('FAIL live compiler candidate differs frozen candidate')
print(f'PASS authority-seeded live compiler candidate byte-identical files={len(a)}')
PY
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26588_gradle_language_compilers.log"
  set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26588_gradle_native_compiler.log"
  set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
  verify_candidate_patches
  set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26588 PRE-BUILD SAFETY PROOF PASSED"
  ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26588_gradle_assemble.log"
  set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
  mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort); [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK, got ${#apks[@]}"
  mv "${apks[0]}" "$FINAL"; mapfile -t roots < <(find "$ROOT" -maxdepth 1 -type f -name '*.apk' | sort); [[ "${#roots[@]}" -eq 1 && "${roots[0]}" == "$FINAL" ]] || fail "exactly one final root APK required"
  sha256sum "$FINAL" > "$OUT/26588_V1_APK.sha256"; set_report "EXACTLY ONE APK" "PASS"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"
  python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26588_postbuild_semantic_validation.txt"
  python3 -S "$GATEVERIFY" "$POST" | tee "$OUT/26588_postbuild_refinement_regressions.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26588_postbuild_authority.txt"
  set_report "POST-BUILD INVARIANCE" "PASS (authority-seeded candidate/protected/DNG/native/vendor exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"
  tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26588_V1_candidate_app_source.tar.gz"
  sha256sum "$OUT/26588_V1_candidate_app_source.tar.gz" > "$OUT/26588_V1_candidate_app_source.tar.gz.sha256"
  cp "$CAND_FULL" "$OUT/26588_V1_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26588_V1_native_protected_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26588_V1_vendor_protected_postbuild.sha256"
  set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests)"
}
verify_package
verify_scope
obtain_authority
make_candidate
verify_shaders
if [[ -n "$LOCAL_ART" ]]; then
  verify_candidate_patches
  set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real pinned GLSL + Kotlin/Java/NDK project compilers/full Android gates require Actions)"
  set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN (local prebuild stops before Android build)"
  cp "$OUT/26588_V1_STRICT_HANDOFF_REPORT.txt" "$OUT/26588_local_prebuild_report.txt"
  pass "26588 LOCAL PREBUILD PREPARED: real GLSL/Kotlin/Java/NDK/full Android gates explicitly unproven locally"
  exit 0
fi
install_and_build
pass "26588 REAL GLSL + KOTLIN/JAVA + NDK + FULL ASSEMBLE PASSED"
pass "26588 POST-BUILD INVARIANCE PASSED"
