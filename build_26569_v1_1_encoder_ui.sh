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
BASE_SUCCESS_COMMIT="6e1b655a145c8719fd64681fe5ff0e8eb11b8ce3"
HANDOFF_PARENT_COMMIT="42096f895ef85181faaa70f303f34e1ea586d165"
BASE_RUN_ID="33358885390"
BASE_ARTIFACT_ID="9746086429"
BASE_ARTIFACT_NAME="photon-26568-v1-1-fused-sr-performance-detail"
BASE_ARTIFACT_SHA="224acb3d97ae3387c7f7a2ccfc5a61b29d98c6f89108e2d74f4d1ce7043ead12"
BASE_TAR_SHA="31274487b56a7770fb729345ade2ed24b86e8f6d0b09e413d40879df3784da19"
VERSION_NAME="0.9726569"
VERSION_BUILD="26569"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
HANDOFF="$ROOT/V1_1_26569_HANDOFF_HASHES.sha256"
BASE_PIN="$ROOT/V1_1_26569_BASE_26568_AUDITED_RUNTIME.sha256"
CAND_PIN="$ROOT/V1_1_26569_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
BASE_FULL="$ROOT/V1_1_26569_BASE_26568_FULL_APP.sha256"
CAND_FULL="$ROOT/V1_1_26569_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_VENDOR="$ROOT/V1_1_26569_BASE_26568_NATIVE_VENDOR.sha256"
CAND_VENDOR="$ROOT/V1_1_26569_EXPECTED_NATIVE_VENDOR.sha256"
BASE_DNG="$ROOT/V1_1_26569_DNG_PROTECTED_BASE.sha256"
CAND_DNG="$ROOT/V1_1_26569_DNG_PROTECTED_CANDIDATE.sha256"
BASE_PROTECTED="$ROOT/V1_1_26569_PROTECTED_UNCHANGED_BASE.sha256"
CAND_PROTECTED="$ROOT/V1_1_26569_PROTECTED_UNCHANGED_CANDIDATE.sha256"
SHADER_PIN="$ROOT/V1_1_26569_RUNTIME_EXPANDED_SHADERS.sha256"
CHANGED="$ROOT/V1_1_26569_RUNTIME_CHANGED_PATHS.txt"
PREWRITE="$ROOT/V1_1_26569_PREWRITE_SOURCE_HASHES.sha256"
FORWARD="$ROOT/V1_1_26569_RUNTIME_DELTA_FROM_26568.patch"
ROLLBACK="$ROOT/V1_1_26569_RUNTIME_ROLLBACK_TO_26568.patch"
TRANSFORM="$ROOT/transform_26569_v1_1.py"
VALIDATE="$ROOT/validate_26569_v1_1.py"
AUTHORITY="$ROOT/verify_26569_v1_1_authority.py"
PATCHVERIFY="$ROOT/verify_26569_v1_1_patches.py"
SHADERVERIFY="$ROOT/verify_26569_v1_1_shaders.py"
BUILD_SCRIPT="$ROOT/build_26569_v1_1_encoder_ui.sh"
WORKFLOW="$ROOT/.github/workflows/build-26569-v1-1-encoder-ui.yml"
SEALED_PY=("$TRANSFORM" "$VALIDATE" "$AUTHORITY" "$PATCHVERIFY" "$SHADERVERIFY")
SEALED_DEP_FILES=("${SEALED_PY[@]}" "$BUILD_SCRIPT" "$WORKFLOW")
OUT="$ROOT/build_26569_v1_1_encoder_ui_outputs"
WORK="$ROOT/.build_26569_v1_1_encoder_ui_work"
ARTZIP="$WORK/26568_v1_1_artifact.zip"
ARTDIR="$WORK/artifact"
BASE="$WORK/exact_26568_v1_1_compiled_candidate"
AFTER="$WORK/candidate_26569"
AFTER2="$WORK/candidate_26569_replay"
SHADER_OUT="$WORK/runtime_expanded_shaders"
GLSLANG_DIR="$WORK/glslang-16.5.0"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"
POST="$WORK/postbuild_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-1-encoder-ui-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then
  [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact 26568 V1.1 artifact ZIP"
  LOCAL_ART="$2"
fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"

cat > "$OUT/26569_V1_1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26569_V1_1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME OWNERSHIP: NOT RUN
DORMANT-OWNER REJECTION: NOT RUN
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
BACKUP STATUS: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
CARRIED FAILURE REGRESSIONS: NOT RUN
BASE/CANDIDATE MANIFEST COMPLETENESS: NOT RUN
DNG INVARIANCE: NOT RUN
26568 SR/COLOR INVARIANCE: NOT RUN
ENCODER PROFILE CACHE EQUIVALENCE: NOT RUN
MOTION JIN COPY ELIMINATION: NOT RUN
ENCODER BOUNDED WORKER POLICY: NOT RUN
UHDR/JPEGR INVARIANCE: NOT RUN
UI ADAPTIVE COLLISION GUARD: NOT RUN
UI XML INVARIANCE: NOT RUN
PERFORMANCE TELEMETRY: NOT RUN
RUNTIME-EXPANDED GLSL RESERVED SCAN: NOT RUN
REAL GLSL COMPILE: NOT RUN
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
REAL NATIVE/NDK COMPILE: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
POST-BUILD INVARIANCE: NOT RUN
CLEAN ARTIFACT SOURCE EXPORT: NOT RUN
TARGET VERSION/BUILD: 0.9726569 / 26569
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26569_V1_1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26569_V1_1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26569_V1_1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26569_V1_1_COMPILER_STATUS.txt"; }

snapshot_candidate_from_authority(){
  local authority_root="$1" live_root="$2" dest_root="$3"
  rm -rf "$dest_root"
  mkdir -p "$dest_root"
  # Preserve the exact successful compiled-candidate file universe. Repository-only
  # module scaffolding and generated build outputs must never enter candidate scope.
  cp -a "$authority_root/." "$dest_root/"
  rm -rf "$dest_root/app/src"
  cp -a "$live_root/app/src" "$dest_root/app/"
  cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"
  cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"
}

verify_package(){
  [[ -f "$HANDOFF" ]] || fail "handoff hash manifest missing"
  sha256sum -c "$HANDOFF"
  [[ "$(wc -l < "$HANDOFF")" -eq 28 ]] || fail "sealed payload count must be 28 excluding handoff manifest"
  [[ "$(wc -l < "$CHANGED")" -eq 4 ]] || fail "runtime allowlist count (4)"
  [[ "$(wc -l < "$BASE_PIN")" -eq 931 && "$(wc -l < "$CAND_PIN")" -eq 931 ]] || fail "audited manifest count"
  [[ "$(wc -l < "$BASE_FULL")" -eq 1708 && "$(wc -l < "$CAND_FULL")" -eq 1708 ]] || fail "full app manifest count"
  [[ "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$CAND_VENDOR")" -eq 778 ]] || fail "vendor manifest count"
  [[ "$(wc -l < "$BASE_DNG")" -eq 7 && "$(wc -l < "$CAND_DNG")" -eq 7 ]] || fail "DNG manifest count"
  [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1704 && "$(wc -l < "$CAND_PROTECTED")" -eq 1704 ]] || fail "protected manifest count"
  [[ "$(sha "$BASE_PIN")" == "39853125f987417670b565dffb454e24046499aeea5149a09dc131294ddde435" ]] || fail "base audited manifest SHA"
  [[ "$(sha "$CAND_PIN")" == "ab09dc48368524e0bc6e9cf46aa63f117d33a8863fad4b64051e32334c14329e" ]] || fail "candidate audited manifest SHA"
  [[ "$(sha "$BASE_FULL")" == "3bfae4fa481b21cf9528c8dd6ec894cb2b11f93d193bc05daf4b03056be151aa" ]] || fail "base full manifest SHA"
  [[ "$(sha "$CAND_FULL")" == "292548c53d60632927b9715815d3cc4757afb3111d3a4fcffc65aad4ac69ddd3" ]] || fail "candidate full manifest SHA"
  [[ "$(sha "$BASE_VENDOR")" == "7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8" ]] || fail "vendor manifest SHA"
  [[ "$(sha "$BASE_DNG")" == "de9ccc599a5a31f150ba4b3c3f91028cbb9b98a4938db8fd22eef5cb1c94f592" ]] || fail "DNG manifest SHA"
  [[ "$(sha "$BASE_PROTECTED")" == "8b1910f1948b09ecc50ce335f286f77765fb65b463e3df814c4be36724614a84" ]] || fail "protected manifest SHA"
  [[ "$(sha "$SHADER_PIN")" == "9e149fea3e9b274bad880a539361605003188740b907b1c28dd6913a7f91421e" ]] || fail "runtime-expanded shader manifest SHA"
  [[ "$(sha "$FORWARD")" == "6eb8b13a603837c3ea52b61d7c7da2f5c8cd579a0943c7a0ad2f411528ff2102" ]] || fail "forward patch SHA"
  [[ "$(sha "$ROLLBACK")" == "5a9608fea623ea2b4dfdd3077d718e9db90b5a5a2baa7f782f87277fc7e0b6fe" ]] || fail "rollback patch SHA"
  python3 -S - "${SEALED_PY[@]}" <<'PY'
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
 if bad: raise SystemExit(f'non-stdlib dependency {p.name}: {sorted(set(bad))}')
 compile(src,str(p),'exec')
print('PASS packaged Python stdlib-only syntax/import gate')
PY
  ! grep -Eq '(^|[[:space:]])(import|from)[[:space:]]+numpy' "${SEALED_PY[@]}" || fail "NumPy import in sealed Python"
  ! grep -Eq 'pip(3)?[[:space:]]+install' "${SEALED_DEP_FILES[@]}" || fail "package-manager dependency in sealed files"
  bash -n "$BUILD_SCRIPT"
  grep -F 'run 33339787968, job 99333216734' "$ROOT/REGRESSION_V1_1_26569_CARRIED_FAILURES.txt" >/dev/null || fail "Actions glslang bootstrap regression missing"
  grep -F 'run 33340190659, job 99334293921' "$ROOT/REGRESSION_V1_1_26569_CARRIED_FAILURES.txt" >/dev/null || fail "Actions Kotlin phase-stat regression missing"
  grep -F 'run 33340661287, job 99335599790' "$ROOT/REGRESSION_V1_1_26569_CARRIED_FAILURES.txt" >/dev/null || fail "Actions generated-scope regression missing"
  grep -F 'run 33350507622, job 99362814146' "$ROOT/REGRESSION_V1_1_26569_CARRIED_FAILURES.txt" >/dev/null || fail "Actions repository-scaffolding regression missing"
  grep -F 'run 33357873019, job 99383368441' "$ROOT/REGRESSION_V1_1_26569_CARRIED_FAILURES.txt" >/dev/null || fail "26568 V1 helper-closure regression missing"
  grep -F 'run 33401928594, job 99520075790' "$ROOT/REGRESSION_V1_1_26569_CARRIED_FAILURES.txt" >/dev/null || fail "26569 V1 native namespace-closure regression missing"
  grep -F "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" "$BUILD_SCRIPT" >/dev/null || fail "real native pre-assemble compiler gate missing"
  grep -F 'the 26569 runtime changed-file allowlist is exactly four paths' "$ROOT/REGRESSION_V1_1_26569_CARRIED_FAILURES.txt" >/dev/null || fail "26569 runtime allowlist regression missing"
  grep -F 'Already-safe layouts receive correction 0' "$ROOT/REGRESSION_V1_1_26569_ENCODER_UI_CONTRACT.txt" >/dev/null || fail "UI safe-layout regression missing"
  grep -F 'Motion-only fast path is gated by !jin.enabled()' "$ROOT/REGRESSION_V1_1_26569_ENCODER_UI_CONTRACT.txt" >/dev/null || fail "Motion encoder gate missing"
  grep -F "changed==EXPECTED" "$VALIDATE" >/dev/null || fail "exact changed-runtime allowlist equality gate missing"
  local scopefix="$WORK/canonical_scope_fixture"
  rm -rf "$scopefix"
  mkdir -p "$scopefix/authority/app/src/main/java/fixture" "$scopefix/live/app/src/main/java/fixture" \
    "$scopefix/live/app/build/generated" "$scopefix/live/app/.cxx/generated"
  printf '// authority fixture\n' > "$scopefix/authority/app/src/main/java/fixture/Authority.java"
  printf 'authority-only\n' > "$scopefix/authority/app/authority-only.txt"
  printf 'android {}\n' > "$scopefix/authority/app/build.gradle"
  printf 'VERSION_NAME=authority\nVERSION_BUILD=1\n' > "$scopefix/authority/app/version.properties"
  printf '// unexpected runtime source fixture\n' > "$scopefix/live/app/src/main/java/fixture/UnexpectedSource.java"
  printf 'android {}\n' > "$scopefix/live/app/build.gradle"
  printf 'VERSION_NAME=fixture\nVERSION_BUILD=2\n' > "$scopefix/live/app/version.properties"
  printf 'repo scaffold\n' > "$scopefix/live/app/.gitignore"
  printf 'repo scaffold\n' > "$scopefix/live/app/SupportedList.txt"
  printf 'repo scaffold\n' > "$scopefix/live/app/proguard-rules.pro"
  printf 'generated\n' > "$scopefix/live/app/build/generated/output.txt"
  printf 'generated\n' > "$scopefix/live/app/.cxx/generated/output.txt"
  snapshot_candidate_from_authority "$scopefix/authority" "$scopefix/live" "$scopefix/snapshot"
  [[ -f "$scopefix/snapshot/app/authority-only.txt" ]] || fail "canonical snapshot lost authority file universe"
  [[ -f "$scopefix/snapshot/app/src/main/java/fixture/UnexpectedSource.java" ]] || fail "canonical snapshot hid unexpected runtime source"
  [[ ! -e "$scopefix/snapshot/app/.gitignore" ]] || fail "canonical snapshot admitted repository-only app/.gitignore"
  [[ ! -e "$scopefix/snapshot/app/SupportedList.txt" ]] || fail "canonical snapshot admitted repository-only SupportedList.txt"
  [[ ! -e "$scopefix/snapshot/app/proguard-rules.pro" ]] || fail "canonical snapshot admitted repository-only proguard-rules.pro"
  [[ ! -e "$scopefix/snapshot/app/build/generated/output.txt" ]] || fail "canonical snapshot admitted Gradle generated output"
  [[ ! -e "$scopefix/snapshot/app/.cxx" ]] || fail "canonical snapshot admitted CMake generated output"
  pass "REGRESSION_26569_POSTBUILD_GENERATED_SCOPE: PASS"
  pass "REGRESSION_26569_REPOSITORY_SCAFFOLD_SCOPE: PASS"
  ! grep -F 'py_compile' "$WORKFLOW" >/dev/null || fail "sealed workflow reintroduced py_compile transient contamination"
  local glslfix="$WORK/glslang_symlink_fixture" blind="" resolved=""
  rm -rf "$glslfix"; mkdir -p "$glslfix/bin"
  printf '#!/usr/bin/env bash\nexit 0\n' > "$glslfix/bin/glslang"; chmod +x "$glslfix/bin/glslang"
  ln -s glslang "$glslfix/bin/glslangValidator"
  blind="$(find "$glslfix" -type f -name glslangValidator -print -quit)"
  [[ -z "$blind" ]] || fail "glslang symlink regression fixture did not reproduce V1 failure"
  resolved="$(resolve_glslang_compiler "$glslfix")" || fail "glslang resolver failed symlink fixture"
  [[ "$resolved" == "$glslfix/bin/glslang" ]] || fail "glslang resolver chose wrong fixture executable"
  pass "REGRESSION_26569_GLSLANG_SYMLINK_BOOTSTRAP: PASS"
  pass "sealed package syntax/hash/regression contract"
  set_report "CARRIED FAILURE REGRESSIONS" "PASS"
}

verify_scope(){
  if [[ -n "$LOCAL_ART" ]]; then
    set_report "BACKUP STATUS" "PASS (no new backup requested/required; exact 26568 authority + rollback patch)"
    set_report "CHANGED RUNTIME SCOPE" "PASS (sealed handoff local replay; exact runtime allowlist validated after transform)"
    return
  fi
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  git merge-base --is-ancestor "$BASE_SUCCESS_COMMIT" HEAD || fail "successful 26568 runtime authority is not ancestor"
  [[ "$(git rev-parse HEAD^)" == "$HANDOFF_PARENT_COMMIT" ]] || fail "26569 V1.1 handoff must be one clean retry commit directly on failed 26569 V1 parent"
  set_report "BACKUP STATUS" "PASS (no new backup: localized encoder/UI correction; exact authority + deterministic rollback)"
  python3 - "$HANDOFF" > "$WORK/expected_scope.txt" <<'PY'
from pathlib import Path
import sys
names=[line.split('  ',1)[1] for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]
names.append('V1_1_26569_HANDOFF_HASHES.sha256')
print('\n'.join(sorted(names)))
PY
  git diff --name-only "$HANDOFF_PARENT_COMMIT"..HEAD | sort > "$WORK/actual_scope.txt"
  diff -u "$WORK/expected_scope.txt" "$WORK/actual_scope.txt" || fail "handoff commit scope mismatch"
  ! grep -Eq '^app/' "$WORK/actual_scope.txt" || fail "handoff commit contains runtime app source"
  set_report "CHANGED RUNTIME SCOPE" "PASS (handoff commit sealed files only; runtime app installed only inside Actions)"
}

obtain_authority(){
  if [[ -n "$LOCAL_ART" ]]; then
    cp "$LOCAL_ART" "$ARTZIP"
  else
    [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
    curl -L --fail --retry 3 \
      -H "Authorization: Bearer $TOKEN" \
      -H "Accept: application/vnd.github+json" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" \
      -o "$ARTZIP"
  fi
  [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26568 V1.1 artifact ZIP authority SHA mismatch"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  local tarball="$ARTDIR/build_26568_v1_1_fused_sr_performance_detail_outputs/26568_V1_1_candidate_app_source.tar.gz"
  [[ -f "$tarball" ]] || fail "compiled 26568 V1.1 candidate tar missing from artifact"
  [[ "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "compiled 26568 V1.1 candidate tar SHA mismatch"
  tar -xzf "$tarball" -C "$BASE"
  find "$ARTDIR" -type f -name '*.apk' -delete
  (cd "$BASE" && sha256sum -c "$BASE_PIN" >/dev/null)
  (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null)
  (cd "$BASE" && sha256sum -c "$BASE_VENDOR" >/dev/null)
  (cd "$BASE" && sha256sum -c "$BASE_DNG" >/dev/null)
  (cd "$BASE" && sha256sum -c "$BASE_PROTECTED" >/dev/null)
  (cd "$BASE" && sha256sum -c "$PREWRITE" >/dev/null)
  set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (run $BASE_RUN_ID artifact $BASE_ARTIFACT_ID SHA $BASE_ARTIFACT_SHA tar $BASE_TAR_SHA)"
  pass "exact compiled 26568 V1.1 artifact authority"
}

make_candidate(){
  cp -a "$BASE/." "$AFTER/"
  cp -a "$BASE/." "$AFTER2/"
  python3 -S "$TRANSFORM" "$AFTER" | tee "$OUT/26569_transform.txt"
  python3 -S "$TRANSFORM" "$AFTER2" | tee "$OUT/26569_transform_replay.txt"
  python3 - "$AFTER" "$AFTER2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(r).rglob('*')) if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2])
if a!=b: raise SystemExit('candidate transform replay mismatch')
print(f'PASS deterministic candidate transform files={len(a)}')
PY
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; cmp "$ROOT/handoff_payload_26569_v1_1/$rel" "$AFTER/$rel" || fail "sealed payload differs frozen candidate $rel"; done < "$CHANGED"
  pass "sealed runtime payload byte-identical to frozen 26569 candidate"
  python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26569_semantic_validation.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26569_authority_candidate.txt"
  set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (931 audited / 1708 full / 778 vendor / 7 DNG / 1704 protected)"
  set_report "DNG INVARIANCE" "PASS (all DNG/ImageSaver owners byte-identical to successful 26568)"
  set_report "26568 SR/COLOR INVARIANCE" "PASS (Sabre/VGN/direct-CFA scalar/P3/adaptive-color owners unchanged)"
  set_report "ENCODER PROFILE CACHE EQUIVALENCE" "PASS (unchanged profileColor populates bounded cache; equations identical after lookup substitution)"
  set_report "MOTION JIN COPY ELIMINATION" "PASS (optimized path only when Jin disabled; Jin-enabled path preserves original render/copy behavior)"
  set_report "ENCODER BOUNDED WORKER POLICY" "PASS (Motion 256 rows/max6; Jin path 128 rows/max4; no full-frame scratch)"
  set_report "UHDR/JPEGR INVARIANCE" "PASS (1:1 gain map retained; JPEG-R packager bytes unchanged)"
  set_report "UI ADAPTIVE COLLISION GUARD" "PASS (measured 12dp minimum; correction zero on safe layouts; no device special case)"
  set_report "UI XML INVARIANCE" "PASS (camera/bottombuttons/main-bottombar XML bytes unchanged)"
  set_report "PERFORMANCE TELEMETRY" "PASS (encoder component + JPEG-R package + UI collision markers in actual runtime)"
  set_report "RUNTIME OWNERSHIP" "PASS"
  set_report "DORMANT-OWNER REJECTION" "PASS"
}

verify_candidate_patches(){
  python3 -S "$PATCHVERIFY" "$BASE" "$AFTER" "$FORWARD" "$ROLLBACK" | tee "$OUT/26569_patch_validation.txt"
  set_report "FORWARD PATCH FUZZ=0" "PASS"
  set_report "ROLLBACK PATCH FUZZ=0" "PASS"
}

verify_shaders(){
  rm -rf "$SHADER_OUT"; mkdir -p "$SHADER_OUT"
  if [[ -n "$LOCAL_ART" ]]; then
    python3 -S "$SHADERVERIFY" "$AFTER" --out "$SHADER_OUT" | tee "$OUT/26569_shader_validation.txt"
    cmp "$SHADER_OUT/runtime_expanded_shaders.sha256" "$SHADER_PIN" || fail "local runtime-expanded shader pin mismatch"
    set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (12 variants exact to successful 26568; no shader runtime changes)"
    set_report "REAL GLSL COMPILE" "NOT RUN locally (no shader change; pinned real compiler reruns in Actions)"
    set_compiler "REAL GLSL COMPILE" "NOT RUN locally (reruns in Actions)"
    return
  fi
  mkdir -p "$GLSLANG_DIR"
  local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz"
  curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"
  [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "pinned glslang archive SHA mismatch"
  tar -tzf "$archive" > "$OUT/26569_glslang_archive_contents.txt"
  tar -xzf "$archive" -C "$GLSLANG_DIR"
  local compiler
  compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "glslang executable missing after pinned extraction"
  chmod +x "$compiler"
  "$compiler" --version | tee "$OUT/26569_glslang_version.txt"
  python3 -S "$SHADERVERIFY" "$AFTER" --out "$SHADER_OUT" --glslang "$compiler" | tee "$OUT/26569_shader_validation.txt"
  cmp "$SHADER_OUT/runtime_expanded_shaders.sha256" "$SHADER_PIN" || fail "Actions runtime-expanded shader pin mismatch"
  cp "$SHADER_OUT/shader_verification.json" "$OUT/26569_shader_verification.json"
  set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (12 exact runtime-expanded variants; unchanged from successful 26568)"
  set_report "REAL GLSL COMPILE" "PASS (pinned Khronos glslangValidator $GLSLANG_VERSION)"
  set_compiler "REAL GLSL COMPILE" "PASS (pinned Khronos glslangValidator $GLSLANG_VERSION)"
}

install_and_build(){
  [[ -z "$LOCAL_ART" ]] || return 0
  rm -rf "$ROOT/app/src"
  cp -a "$AFTER/app/src" "$ROOT/app/"
  cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"
  cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"
  python3 -S "$VALIDATE" "$BASE" "$LIVE_CANON" | tee "$OUT/26569_live_semantic_validation.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$LIVE_CANON" | tee "$OUT/26569_live_authority.txt"
  python3 - "$AFTER" "$LIVE_CANON" <<'PYTREE'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(r).rglob('*')) if p.is_file()}
a,b=H(Path(sys.argv[1])),H(Path(sys.argv[2]))
if a != b:
    only_a=sorted(set(a)-set(b)); only_b=sorted(set(b)-set(a)); changed=sorted(k for k in set(a)&set(b) if a[k]!=b[k])
    raise SystemExit(f'live compiler candidate differs from frozen AFTER: only_after={only_a} only_live={only_b} changed={changed}')
print(f'PASS live compiler candidate byte-identical to frozen AFTER files={len(a)}')
PYTREE
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26569_gradle_language_compilers.log"
  set_report "REAL KOTLIN COMPILE" "PASS"
  set_report "REAL JAVA COMPILE" "PASS"
  set_compiler "REAL KOTLIN COMPILE" "PASS"
  set_compiler "REAL JAVA COMPILE" "PASS"
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26569_gradle_native_compiler.log"
  set_report "REAL NATIVE/NDK COMPILE" "PASS (real Android NDK buildCMakeDebug both ABIs)"
  set_compiler "NATIVE/NDK COMPILE" "PASS (real Android NDK buildCMakeDebug both ABIs)"
  verify_candidate_patches
  pass "26569 PRE-BUILD SAFETY PROOF PASSED"
  ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26569_gradle_assemble.log"
  set_report "FULL ANDROID ASSEMBLE" "PASS (includes Android NDK native compile/link)"
  set_compiler "FULL ANDROID ASSEMBLE" "PASS"
  mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort)
  [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK, got ${#apks[@]}"
  mv "${apks[0]}" "$FINAL"
  mapfile -t all_apks < <(find "$ROOT" -type f -name '*.apk' -not -path "$WORK/*" | sort)
  [[ "${#all_apks[@]}" -eq 1 && "${all_apks[0]}" == "$FINAL" ]] || fail "final workspace must contain exactly one intended APK"
  sha256sum "$FINAL" > "$OUT/26569_V1_1_APK.sha256"

  snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26569_postbuild_authority.txt"
  python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26569_postbuild_semantic_validation.txt"
  (cd "$POST" && sha256sum -c "$CAND_VENDOR" >/dev/null)
  (cd "$POST" && sha256sum -c "$CAND_DNG" >/dev/null)
  (cd "$POST" && sha256sum -c "$CAND_PROTECTED" >/dev/null)
  set_report "POST-BUILD INVARIANCE" "PASS (authority-seeded frozen source snapshot; candidate/protected/DNG/native/vendor exact)"
  set_compiler "POST-BUILD INVARIANCE" "PASS"

  tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf \
    "$OUT/26569_V1_1_candidate_app_source.tar.gz" -C "$POST" app
  sha256sum "$OUT/26569_V1_1_candidate_app_source.tar.gz" > "$OUT/26569_V1_1_candidate_app_source.tar.gz.sha256"
  cp "$CAND_PIN" "$OUT/26569_V1_1_candidate_source.sha256"
  cp "$CAND_FULL" "$OUT/26569_V1_1_candidate_full_app.sha256"
  cp "$CAND_VENDOR" "$OUT/26569_vendor_postbuild.sha256"
  set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests)"
}

verify_package
verify_scope
obtain_authority
make_candidate
verify_shaders
if [[ -n "$LOCAL_ART" ]]; then
  verify_candidate_patches
  set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN (local prebuild intentionally stops before Android build)"
  cp "$OUT/26569_V1_1_STRICT_HANDOFF_REPORT.txt" "$OUT/26569_local_prebuild_report.txt"
  pass "26569 LOCAL PREBUILD PREPARED: real Java/native/full Android build gates remain explicitly unproven"
  exit 0
fi
install_and_build
pass "26569 REAL COMPILERS + FULL ASSEMBLE PASSED"
pass "26569 POST-BUILD INVARIANCE PASSED"
