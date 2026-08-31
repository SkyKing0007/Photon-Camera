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
BASE_SUCCESS_COMMIT="cd57770a427f63a3000a6b7d594fcda425fcd351"
BASE_RUN_ID="33410892866"
BASE_ARTIFACT_ID="9765167937"
BASE_ARTIFACT_NAME="photon-26569-v1-1-encoder-ui"
BASE_ARTIFACT_SHA="9cefd4d7a8e35c5f1c9f54c5e7e66ab165208edaca8e9f66ad2a7b4c7e528575"
BASE_TAR_SHA="5cefcc1b02367bfa2e285ba54c48a62594cf367cda5f41543dfb4a94f9a40c82"
VERSION_NAME="0.9726570"
VERSION_BUILD="26570"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
HANDOFF="$ROOT/V1_26570_HANDOFF_HASHES.sha256"
BASE_FULL="$ROOT/V1_26570_BASE_26569_FULL_APP.sha256"
CAND_FULL="$ROOT/V1_26570_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/V1_26570_PROTECTED_UNCHANGED_BASE.sha256"
CAND_PROTECTED="$ROOT/V1_26570_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/V1_26570_NATIVE_PROTECTED_BASE.sha256"
CAND_NATIVE="$ROOT/V1_26570_EXPECTED_NATIVE_PROTECTED.sha256"
BASE_DNG="$ROOT/V1_26570_DNG_PROTECTED_BASE.sha256"
CAND_DNG="$ROOT/V1_26570_DNG_PROTECTED_CANDIDATE.sha256"
BASE_ARCH="$ROOT/V1_26570_PROTECTED_ARCHITECTURE_BASE.sha256"
CAND_ARCH="$ROOT/V1_26570_PROTECTED_ARCHITECTURE_CANDIDATE.sha256"
CHANGED="$ROOT/V1_26570_RUNTIME_CHANGED_PATHS.txt"
PREWRITE="$ROOT/V1_26570_PREWRITE_SOURCE_HASHES.sha256"
EXPECTED_CHANGED="$ROOT/V1_26570_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/V1_26570_RUNTIME_DELTA_FROM_26569.patch"
ROLLBACK="$ROOT/V1_26570_RUNTIME_ROLLBACK_TO_26569.patch"
SHADER_PIN="$ROOT/V1_26570_RUNTIME_EXPANDED_SHADERS.sha256"
TRANSFORM="$ROOT/transform_26570_v1.py"
VALIDATE="$ROOT/validate_26570_v1.py"
AUTHORITY="$ROOT/verify_26570_v1_authority.py"
PATCHVERIFY="$ROOT/verify_26570_v1_patches.py"
SHADERVERIFY="$ROOT/verify_26570_v1_shaders.py"
BUILD_SCRIPT="$ROOT/build_26570_v1_surface_performance.sh"
WORKFLOW="$ROOT/.github/workflows/build-26570-v1-surface-performance.yml"
OUT="$ROOT/build_26570_v1_surface_performance_outputs"
WORK="$ROOT/.build_26570_v1_surface_performance_work"
ARTZIP="$WORK/26569_v1_1_artifact.zip"
ARTDIR="$WORK/artifact"
BASE="$WORK/exact_26569_v1_1_compiled_candidate"
AFTER="$WORK/candidate_26570"
AFTER2="$WORK/candidate_26570_replay"
SHADER_OUT="$WORK/runtime_expanded_shaders"
GLSLANG_DIR="$WORK/glslang-16.5.0"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"
POST="$WORK/postbuild_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-surface-performance-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact 26569 V1.1 artifact ZIP"; LOCAL_ART="$2"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"

cat > "$OUT/26570_V1_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
cat > "$OUT/26570_V1_STRICT_HANDOFF_REPORT.txt" <<'EOF'
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
SURFACE CONTINUITY CONTRACT: NOT RUN
TRUE2X PERFORMANCE CONTRACT: NOT RUN
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
TARGET VERSION/BUILD: 0.9726570 / 26570
EOF
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26570_V1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26570_V1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26570_V1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26570_V1_COMPILER_STATUS.txt"; }

snapshot_candidate_from_authority(){
  local authority_root="$1" live_root="$2" dest_root="$3"
  rm -rf "$dest_root"; mkdir -p "$dest_root"
  # Exact successful 26569 mechanics: authority file universe first, then only live runtime source domain.
  cp -a "$authority_root/." "$dest_root/"
  rm -rf "$dest_root/app/src"
  cp -a "$live_root/app/src" "$dest_root/app/"
  cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"
  cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"
}

verify_package(){
  [[ -f "$HANDOFF" ]] || fail "handoff hash manifest missing"
  sha256sum -c "$HANDOFF"
  python3 -S - "$HANDOFF" <<'PY'
from pathlib import Path
import sys
m=Path(sys.argv[1]); root=m.parent
listed={line.split('  ',1)[1] for line in m.read_text().splitlines() if line.strip()}
actual=set()
for p in root.rglob('*'):
 if not p.is_file() or p==m: continue
 rel=p.relative_to(root)
 if rel.parts and rel.parts[0] in {'build_26570_v1_surface_performance_outputs','.build_26570_v1_surface_performance_work'}: continue
 actual.add(str(rel))
# Generated local/Actions proof directories are runtime outputs, never sealed handoff inputs.
if actual!=listed:
 raise SystemExit(f'FAIL sealed package set mismatch missing={sorted(listed-actual)} extra={sorted(actual-listed)}')
print(f'PASS exact sealed package file set count={len(actual)}')
PY
  [[ "$(wc -l < "$CHANGED")" -eq 3 ]] || fail "runtime allowlist count must be 3"
  [[ "$(wc -l < "$BASE_FULL")" -eq 1708 && "$(wc -l < "$CAND_FULL")" -eq 1708 ]] || fail "full app manifest count"
  [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1705 && "$(wc -l < "$CAND_PROTECTED")" -eq 1705 ]] || fail "protected manifest count"
  [[ "$(wc -l < "$BASE_NATIVE")" -eq 803 && "$(wc -l < "$CAND_NATIVE")" -eq 803 ]] || fail "native protected count"
  [[ "$(wc -l < "$BASE_DNG")" -eq 7 && "$(wc -l < "$CAND_DNG")" -eq 7 ]] || fail "DNG count"
  [[ "$(sha "$BASE_FULL")" == "0bb4e7e0b3d120a3416ee45f825b69e7e3087bce22f2e1afc69462164bad3be9" ]] || fail "base full manifest SHA"
  [[ "$(sha "$CAND_FULL")" == "892587575030f4d867e062d8b24ad3c5c2bf28e2a3a9a0123b386a82bfe5e671" ]] || fail "candidate full manifest SHA"
  [[ "$(sha "$BASE_PROTECTED")" == "0fdb3396a3d1133ce32088c2dc0a4546d0faeb5ce0017075b9e07eb7a968f182" ]] || fail "protected manifest SHA"
  [[ "$(sha "$BASE_NATIVE")" == "e18448ce43c57ccf93d0e1fc69bd25f36c7e2dce9e241093f18856a171e00133" ]] || fail "native protected manifest SHA"
  [[ "$(sha "$BASE_DNG")" == "de9ccc599a5a31f150ba4b3c3f91028cbb9b98a4938db8fd22eef5cb1c94f592" ]] || fail "DNG manifest SHA"
  [[ "$(sha "$BASE_ARCH")" == "125176c8518c96a54206089dd332831eaec76e692fd27d76428ec1bf3b2924a4" ]] || fail "architecture manifest SHA"
  [[ "$(sha "$PREWRITE")" == "e42913a8a70dbc2e369781f8531e8a4031b03da8cc8dcaf28a0961d1235abbb6" ]] || fail "prewrite SHA"
  [[ "$(sha "$EXPECTED_CHANGED")" == "32a13e49439c4ce1264c2ec25dd5c69568ca656499e429afceb8d4d522b786be" ]] || fail "expected changed-source SHA"
  [[ "$(sha "$FORWARD")" == "ae91c08e8a0b0ff37f2b458c2de776b111acde07d61deb031604c11afab1dd5a" ]] || fail "forward patch SHA"
  [[ "$(sha "$ROLLBACK")" == "c4a1def05754801e3452e4c22608ff4a54165878fc6f1199c6bd590e1a277bf8" ]] || fail "rollback patch SHA"
  [[ "$(sha "$SHADER_PIN")" == "0972c3501b5d457f66bf595ac38f1b12d523fdeb120b2a2ef8d33aeae8f14fab" ]] || fail "shader pin SHA"
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
  grep -F 'run 33401928594 / job 99520075790' "$ROOT/REGRESSION_V1_26570_CARRIED_FAILURES.txt" >/dev/null || fail "26569 native failure regression absent"
  grep -F 'IRIS_26570_ONE_SIDED_EDGE_LUMA_AUTHORITY' "$ROOT/REGRESSION_V1_26570_SURFACE_PERFORMANCE_CONTRACT.txt" >/dev/null || fail "surface regression contract missing"
  grep -F 'No verification order is weakened' "$ROOT/V1_26570_INFRASTRUCTURE_DIFF_AUDIT.txt" >/dev/null || fail "infrastructure diff audit missing"
  ! grep -Eq 'pip(3)?[[:space:]]+install' "$TRANSFORM" "$VALIDATE" "$AUTHORITY" "$PATCHVERIFY" "$SHADERVERIFY" "$BUILD_SCRIPT" "$WORKFLOW" || fail "package-manager dependency introduced"
  pass "sealed package syntax/hash/regression contract"
  set_report "INFRASTRUCTURE DELTA AUDIT" "PASS (26569 order/mechanics preserved; only authority pins, 3-file allowlist, modified embedded-shader expansion, and target regressions differ)"
  set_report "CARRIED FAILURE REGRESSIONS" "PASS"
}

verify_scope(){
  if [[ -n "$LOCAL_ART" ]]; then
    set_report "BACKUP STATUS" "PASS (no new backup: localized correction; exact 26569 authority + deterministic rollback)"
    set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed handoff; runtime allowlist validated after transform)"
    return
  fi
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  [[ "$(git rev-parse HEAD^)" == "$BASE_SUCCESS_COMMIT" ]] || fail "26570 handoff must be one clean commit directly on successful 26569 V1.1"
  python3 -S - "$HANDOFF" > "$WORK/expected_scope.txt" <<'PY'
from pathlib import Path
import sys
names=[line.split('  ',1)[1] for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]
names.append('V1_26570_HANDOFF_HASHES.sha256')
print('\n'.join(sorted(names)))
PY
  git diff --name-only "$BASE_SUCCESS_COMMIT"..HEAD | sort > "$WORK/actual_scope.txt"
  diff -u "$WORK/expected_scope.txt" "$WORK/actual_scope.txt" || fail "handoff commit scope mismatch"
  ! grep -Eq '^app/' "$WORK/actual_scope.txt" || fail "handoff commit contains live runtime app source"
  set_report "BACKUP STATUS" "PASS (no new backup: localized VGN/encoder correction; exact hashes + rollback)"
  set_report "CHANGED RUNTIME SCOPE" "PASS (handoff commit sealed infrastructure/payload only; runtime source written only inside Actions)"
}

obtain_authority(){
  if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else
    [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
    curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
  fi
  [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26569 V1.1 artifact ZIP authority SHA mismatch"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  local tarball="$ARTDIR/build_26569_v1_1_encoder_ui_outputs/26569_V1_1_candidate_app_source.tar.gz"
  [[ -f "$tarball" ]] || fail "compiled 26569 candidate tar missing"
  [[ "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "compiled 26569 candidate tar SHA mismatch"
  tar -xzf "$tarball" -C "$BASE"
  find "$ARTDIR" -type f -name '*.apk' -delete
  (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null && sha256sum -c "$BASE_PROTECTED" >/dev/null && sha256sum -c "$BASE_NATIVE" >/dev/null && sha256sum -c "$BASE_DNG" >/dev/null && sha256sum -c "$BASE_ARCH" >/dev/null && sha256sum -c "$PREWRITE" >/dev/null)
  set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (26569 V1.1 commit $BASE_SUCCESS_COMMIT run $BASE_RUN_ID artifact $BASE_ARTIFACT_ID SHA $BASE_ARTIFACT_SHA tar $BASE_TAR_SHA)"
  pass "exact successful 26569 V1.1 compiled candidate authority"
}

make_candidate(){
  cp -a "$BASE/." "$AFTER/"; cp -a "$BASE/." "$AFTER2/"
  python3 -S "$TRANSFORM" "$AFTER" | tee "$OUT/26570_transform.txt"
  python3 -S "$TRANSFORM" "$AFTER2" | tee "$OUT/26570_transform_replay.txt"
  python3 -S - "$AFTER" "$AFTER2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2])
if a!=b:raise SystemExit('FAIL candidate transform replay mismatch')
print(f'PASS deterministic candidate reconstruction files={len(a)}')
PY
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; cmp "$ROOT/handoff_payload_26570_v1/$rel" "$AFTER/$rel" || fail "sealed payload differs frozen candidate $rel"; done < "$CHANGED"
  python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26570_semantic_validation.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26570_authority_candidate.txt"
  set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (1708 full / 1705 protected / 803 native protected / 7 DNG)"
  set_report "PROTECTED ARCHITECTURE INVARIANCE" "PASS (158 focused Sabre/SR/capture/UHDR ownership files byte-identical; all other protected app bytes exact)"
  set_report "DNG INVARIANCE" "PASS (7 DNG/ImageSaver owners byte-identical)"
  set_report "SURFACE CONTINUITY CONTRACT" "PASS (illumination-normalized continuity + one-sided luma + cross-edge chroma + IIR edge reset)"
  set_report "TRUE2X PERFORMANCE CONTRACT" "PASS (publication scheduling only; exact quality/4:4:4/gain geometry/band bounds preserved)"
  set_report "RUNTIME OWNERSHIP" "PASS (shared current-MGC VGN owner + native true2x publication owner)"
  set_report "DORMANT-OWNER REJECTION" "PASS (candidate diff exact; no alternate Sabre/SR/capture owner changed)"
}

verify_candidate_patches(){
  python3 -S "$PATCHVERIFY" "$BASE" "$AFTER" "$FORWARD" "$ROLLBACK" | tee "$OUT/26570_patch_validation.txt"
  set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"
}

verify_shaders(){
  rm -rf "$SHADER_OUT"; mkdir -p "$SHADER_OUT"
  if [[ -n "$LOCAL_ART" ]]; then
    python3 -S "$SHADERVERIFY" "$AFTER" --out "$SHADER_OUT" | tee "$OUT/26570_shader_validation.txt"
    cmp "$SHADER_OUT/V1_26570_RUNTIME_EXPANDED_SHADERS.sha256" "$SHADER_PIN" || fail "local runtime-expanded shader pin mismatch"
    set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (4 modified exact embedded compute shaders)"
    set_report "REAL GLSL COMPILE" "NOT RUN locally (modified shaders require Actions pinned compiler)"
    set_compiler "REAL GLSL COMPILE" "NOT RUN locally (Actions required)"
    return
  fi
  mkdir -p "$GLSLANG_DIR"; local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz"
  curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"
  [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "pinned glslang archive SHA mismatch"
  tar -tzf "$archive" > "$OUT/26570_glslang_archive_contents.txt"; tar -xzf "$archive" -C "$GLSLANG_DIR"
  local compiler; compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "glslang executable missing after pinned extraction"; chmod +x "$compiler"
  "$compiler" --version | tee "$OUT/26570_glslang_version.txt"
  python3 -S "$SHADERVERIFY" "$AFTER" --out "$SHADER_OUT" --glslang "$compiler" | tee "$OUT/26570_shader_validation.txt"
  cmp "$SHADER_OUT/V1_26570_RUNTIME_EXPANDED_SHADERS.sha256" "$SHADER_PIN" || fail "Actions runtime-expanded shader pin mismatch"
  cp "$SHADER_OUT/V1_26570_SHADER_VERIFICATION.json" "$OUT/26570_shader_verification.json"
  set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (4 exact modified runtime-expanded variants)"
  set_report "REAL GLSL COMPILE" "PASS (pinned Khronos glslangValidator $GLSLANG_VERSION)"; set_compiler "REAL GLSL COMPILE" "PASS (pinned Khronos glslangValidator $GLSLANG_VERSION)"
}

install_and_build(){
  [[ -z "$LOCAL_ART" ]] || return 0
  rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"
  python3 -S "$VALIDATE" "$BASE" "$LIVE_CANON" | tee "$OUT/26570_live_semantic_validation.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$LIVE_CANON" | tee "$OUT/26570_live_authority.txt"
  python3 -S - "$AFTER" "$LIVE_CANON" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2])
if a!=b:raise SystemExit('FAIL live compiler candidate differs from frozen candidate')
print(f'PASS authority-seeded live compiler candidate byte-identical files={len(a)}')
PY
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26570_gradle_language_compilers.log"
  set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26570_gradle_native_compiler.log"
  set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
  verify_candidate_patches
  set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26570 PRE-BUILD SAFETY PROOF PASSED"
  ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26570_gradle_assemble.log"
  set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
  mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort); [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK, got ${#apks[@]}"
  mv "${apks[0]}" "$FINAL"; mapfile -t roots < <(find "$ROOT" -maxdepth 1 -type f -name '*.apk' | sort); [[ "${#roots[@]}" -eq 1 && "${roots[0]}" == "$FINAL" ]] || fail "exactly one final root APK required"
  sha256sum "$FINAL" > "$OUT/26570_V1_APK.sha256"; set_report "EXACTLY ONE APK" "PASS"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"
  python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26570_postbuild_semantic_validation.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26570_postbuild_authority.txt"
  set_report "POST-BUILD INVARIANCE" "PASS (authority-seeded candidate/protected/DNG/native exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"
  tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26570_V1_candidate_app_source.tar.gz"
  sha256sum "$OUT/26570_V1_candidate_app_source.tar.gz" > "$OUT/26570_V1_candidate_app_source.tar.gz.sha256"; cp "$CAND_FULL" "$OUT/26570_V1_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26570_V1_native_protected_postbuild.sha256"
  set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests)"
}

verify_package
verify_scope
obtain_authority
make_candidate
verify_shaders
if [[ -n "$LOCAL_ART" ]]; then
  verify_candidate_patches
  set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real modified GLSL/Kotlin/NDK/full Android gates require Actions)"
  set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN (local prebuild stops before Android build)"
  cp "$OUT/26570_V1_STRICT_HANDOFF_REPORT.txt" "$OUT/26570_local_prebuild_report.txt"
  pass "26570 LOCAL PREBUILD PREPARED: modified real GLSL/Kotlin/NDK/full Android gates explicitly unproven locally"
  exit 0
fi
install_and_build
pass "26570 REAL GLSL + KOTLIN/JAVA + NDK + FULL ASSEMBLE PASSED"
pass "26570 POST-BUILD INVARIANCE PASSED"
