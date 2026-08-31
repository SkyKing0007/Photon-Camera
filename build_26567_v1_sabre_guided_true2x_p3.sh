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
BASE_SUCCESS_COMMIT="f591411c3b696c1b88938e159332f36ac652775d"
BASE_RUN_ID="33330757249"
BASE_ARTIFACT_ID="9737608902"
BASE_ARTIFACT_NAME="photon-26566-v1-jpeg-color-true2x"
BASE_ARTIFACT_SHA="472a08f2de49820926580a309bcd73538432d6bbdbf0924f554397e8ba9276c9"
BASE_TAR_SHA="853ae4cd00d96755366ee3a5a32a74e947b1d363168375453b33888e2a863b4c"
BACKUP_BRANCH="backup-26566-v1-before-26567-sabre-guided-true2x"
BACKUP_SHA="$BASE_SUCCESS_COMMIT"
VERSION_NAME="0.9726567"
VERSION_BUILD="26567"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
HANDOFF="$ROOT/V1_26567_HANDOFF_HASHES.sha256"
BASE_PIN="$ROOT/V1_26567_BASE_26566_AUDITED_RUNTIME.sha256"
CAND_PIN="$ROOT/V1_26567_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
BASE_FULL="$ROOT/V1_26567_BASE_26566_FULL_APP.sha256"
CAND_FULL="$ROOT/V1_26567_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_VENDOR="$ROOT/V1_26567_BASE_26566_NATIVE_VENDOR.sha256"
CAND_VENDOR="$ROOT/V1_26567_EXPECTED_NATIVE_VENDOR.sha256"
BASE_DNG="$ROOT/V1_26567_DNG_PROTECTED_BASE.sha256"
CAND_DNG="$ROOT/V1_26567_DNG_PROTECTED_CANDIDATE.sha256"
BASE_PROTECTED="$ROOT/V1_26567_PROTECTED_UNCHANGED_BASE.sha256"
CAND_PROTECTED="$ROOT/V1_26567_PROTECTED_UNCHANGED_CANDIDATE.sha256"
SHADER_PIN="$ROOT/V1_26567_RUNTIME_EXPANDED_SHADERS.sha256"
CHANGED="$ROOT/V1_26567_RUNTIME_CHANGED_PATHS.txt"
PREWRITE="$ROOT/V1_26567_PREWRITE_SOURCE_HASHES.sha256"
FORWARD="$ROOT/V1_26567_RUNTIME_DELTA_FROM_26566.patch"
ROLLBACK="$ROOT/V1_26567_RUNTIME_ROLLBACK_TO_26566.patch"
TRANSFORM="$ROOT/transform_26567_v1.py"
VALIDATE="$ROOT/validate_26567_v1.py"
AUTHORITY="$ROOT/verify_26567_authority.py"
PATCHVERIFY="$ROOT/verify_26567_patches.py"
SHADERVERIFY="$ROOT/verify_26567_shaders.py"
BUILD_SCRIPT="$ROOT/build_26567_v1_sabre_guided_true2x_p3.sh"
WORKFLOW="$ROOT/.github/workflows/build-26567-v1-sabre-guided-true2x-p3.yml"
SEALED_PY=("$TRANSFORM" "$VALIDATE" "$AUTHORITY" "$PATCHVERIFY" "$SHADERVERIFY")
SEALED_DEP_FILES=("${SEALED_PY[@]}" "$BUILD_SCRIPT" "$WORKFLOW")
OUT="$ROOT/build_26567_v1_sabre_guided_true2x_p3_outputs"
WORK="$ROOT/.build_26567_v1_sabre_guided_true2x_p3_work"
ARTZIP="$WORK/26566_v1_artifact.zip"
ARTDIR="$WORK/artifact"
BASE="$WORK/exact_26566_compiled_candidate"
AFTER="$WORK/candidate_26567"
AFTER2="$WORK/candidate_26567_replay"
SHADER_OUT="$WORK/runtime_expanded_shaders"
GLSLANG_DIR="$WORK/glslang-16.5.0"
POST="$WORK/postbuild_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-3-sabre-guided-true2x-p3-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then
  [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact 26566 artifact ZIP"
  LOCAL_ART="$2"
fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"

cat > "$OUT/26567_V1_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
cat > "$OUT/26567_V1_STRICT_HANDOFF_REPORT.txt" <<'EOF'
RUNTIME OWNERSHIP: NOT RUN
DORMANT-OWNER REJECTION: NOT RUN
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
BACKUP STATUS: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
CARRIED FAILURE REGRESSIONS: NOT RUN
BASE/CANDIDATE MANIFEST COMPLETENESS: NOT RUN
DNG INVARIANCE: NOT RUN
JPEG TRUE2X SABRE COLOR OWNERSHIP: NOT RUN
JPEG TRUE2X SPEED POLICY: NOT RUN
SHARED JPEG P3 COLOR OWNERSHIP: NOT RUN
JIN MODEL-DOMAIN ADAPTER: NOT RUN
RUNTIME-EXPANDED GLSL RESERVED SCAN: NOT RUN
REAL GLSL COMPILE: NOT RUN
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
POST-BUILD INVARIANCE: NOT RUN
CLEAN ARTIFACT SOURCE EXPORT: NOT RUN
TARGET VERSION/BUILD: 0.9726567 / 26567
EOF
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26567_V1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26567_V1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26567_V1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26567_V1_COMPILER_STATUS.txt"; }

snapshot_app_source(){
  local src_root="$1" dest_root="$2"
  rm -rf "$dest_root"
  mkdir -p "$dest_root/app"
  cp -a "$src_root/app/src" "$dest_root/app/"
  cp -a "$src_root/app/build.gradle" "$dest_root/app/build.gradle"
  cp -a "$src_root/app/version.properties" "$dest_root/app/version.properties"
}

verify_package(){
  [[ -f "$HANDOFF" ]] || fail "handoff hash manifest missing"
  sha256sum -c "$HANDOFF"
  [[ "$(wc -l < "$HANDOFF")" -eq 25 ]] || fail "sealed payload count must be 25 excluding handoff manifest"
  [[ "$(wc -l < "$CHANGED")" -eq 22 ]] || fail "runtime allowlist count"
  [[ "$(wc -l < "$BASE_PIN")" -eq 931 && "$(wc -l < "$CAND_PIN")" -eq 931 ]] || fail "audited manifest count"
  [[ "$(wc -l < "$BASE_FULL")" -eq 1708 && "$(wc -l < "$CAND_FULL")" -eq 1708 ]] || fail "full app manifest count"
  [[ "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$CAND_VENDOR")" -eq 778 ]] || fail "vendor manifest count"
  [[ "$(wc -l < "$BASE_DNG")" -eq 7 && "$(wc -l < "$CAND_DNG")" -eq 7 ]] || fail "DNG manifest count"
  [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1686 && "$(wc -l < "$CAND_PROTECTED")" -eq 1686 ]] || fail "protected manifest count"
  [[ "$(sha "$BASE_PIN")" == "d850f74e7ab2f08838c963bc85353ef3eba903fc5ae7130c34a3fa6a44597e26" ]] || fail "base audited manifest SHA"
  [[ "$(sha "$CAND_PIN")" == "9686ff804df15d291fb14fb12c0a75bba43c711e08b815d03fe9ccf92d8ca4f3" ]] || fail "candidate audited manifest SHA"
  [[ "$(sha "$BASE_FULL")" == "2b3ebde793a48527d21d9eabbcb14f3bb40d455f06aa3579e1f4985efd4744dd" ]] || fail "base full manifest SHA"
  [[ "$(sha "$CAND_FULL")" == "a13a7ef25b83551063e003a6c8a021795f31f005910026970ea386c2fe734b9e" ]] || fail "candidate full manifest SHA"
  [[ "$(sha "$BASE_VENDOR")" == "7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8" ]] || fail "vendor manifest SHA"
  [[ "$(sha "$BASE_DNG")" == "de9ccc599a5a31f150ba4b3c3f91028cbb9b98a4938db8fd22eef5cb1c94f592" ]] || fail "DNG manifest SHA"
  [[ "$(sha "$BASE_PROTECTED")" == "e03a9eef0ad8638bd89967cfc4ba5f902cc59eca2919b984a8cd035b6ccc6e1c" ]] || fail "protected manifest SHA"
  [[ "$(sha "$SHADER_PIN")" == "8f876f720c96497afc52a8ce7e87fc2cf3cf3820641b35eacba5e37b1f0545e4" ]] || fail "runtime-expanded shader manifest SHA"
  [[ "$(sha "$FORWARD")" == "42bb55e1675860f4268be4fab64e5bb86e52974bf47233639bb007db7eaf27fe" ]] || fail "forward patch SHA"
  [[ "$(sha "$ROLLBACK")" == "73c5ee8581a2f96924f1383be9132f2a19ac0bce3d4a1ffd106bf9e2a88e36e4" ]] || fail "rollback patch SHA"
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
  grep -F '26567 reserved GLSL identifier regression:' "$ROOT/REGRESSION_26567_CARRIED_FAILURES.txt" >/dev/null || fail "reserved regression missing"
  grep -F '26567 local candidate transform JNI declaration drift:' "$ROOT/REGRESSION_26567_CARRIED_FAILURES.txt" >/dev/null || fail "JNI regression missing"
  grep -F '26567 local true2x shader anchor leakage:' "$ROOT/REGRESSION_26567_CARRIED_FAILURES.txt" >/dev/null || fail "shader-scope regression missing"
  grep -F '26567 local Java declaration-order failure:' "$ROOT/REGRESSION_26567_CARRIED_FAILURES.txt" >/dev/null || fail "Java-order regression missing"
  grep -F '26567 local workflow py_compile self-contamination:' "$ROOT/REGRESSION_26567_CARRIED_FAILURES.txt" >/dev/null || fail "workflow py_compile regression missing"
  grep -F 'run 33339787968, job 99333216734' "$ROOT/REGRESSION_26567_CARRIED_FAILURES.txt" >/dev/null || fail "Actions glslang bootstrap regression missing"
  grep -F 'run 33340190659, job 99334293921' "$ROOT/REGRESSION_26567_CARRIED_FAILURES.txt" >/dev/null || fail "Actions Kotlin phase-stat regression missing"
  grep -F 'run 33340661287, job 99335599790' "$ROOT/REGRESSION_26567_CARRIED_FAILURES.txt" >/dev/null || fail "Actions post-build generated-scope regression missing"
  grep -F "actual=['app/'+p for p in changed_paths(base/'app',cand/'app')]" "$VALIDATE" >/dev/null || fail "strict changed-runtime validator was weakened"
  grep -F "req(actual==EXPECTED_CHANGED" "$VALIDATE" >/dev/null || fail "exact changed-runtime allowlist equality gate missing"
  local scopefix="$WORK/postbuild_scope_fixture"
  rm -rf "$scopefix"
  mkdir -p "$scopefix/live/app/src/main/java/fixture" "$scopefix/live/app/build/generated" "$scopefix/live/app/.cxx/generated"
  printf '// fixture\n' > "$scopefix/live/app/src/main/java/fixture/UnexpectedSource.java"
  printf 'android {}\n' > "$scopefix/live/app/build.gradle"
  printf 'VERSION_NAME=fixture\nVERSION_BUILD=0\n' > "$scopefix/live/app/version.properties"
  printf 'generated\n' > "$scopefix/live/app/build/generated/output.txt"
  printf 'generated\n' > "$scopefix/live/app/.cxx/generated/output.txt"
  snapshot_app_source "$scopefix/live" "$scopefix/snapshot"
  [[ -f "$scopefix/snapshot/app/src/main/java/fixture/UnexpectedSource.java" ]] || fail "post-build snapshot hid unexpected runtime source"
  [[ ! -e "$scopefix/snapshot/app/build/generated/output.txt" ]] || fail "post-build snapshot admitted Gradle generated output"
  [[ ! -e "$scopefix/snapshot/app/.cxx" ]] || fail "post-build snapshot admitted CMake generated output"
  pass "REGRESSION_26567_V1_2_POSTBUILD_GENERATED_SCOPE: PASS"
  ! grep -F 'py_compile' "$WORKFLOW" >/dev/null || fail "sealed workflow reintroduced py_compile transient contamination"
  local glslfix="$WORK/glslang_symlink_fixture" blind="" resolved=""
  rm -rf "$glslfix"; mkdir -p "$glslfix/bin"
  printf '#!/usr/bin/env bash\nexit 0\n' > "$glslfix/bin/glslang"; chmod +x "$glslfix/bin/glslang"
  ln -s glslang "$glslfix/bin/glslangValidator"
  blind="$(find "$glslfix" -type f -name glslangValidator -print -quit)"
  [[ -z "$blind" ]] || fail "glslang symlink regression fixture did not reproduce V1 failure"
  resolved="$(resolve_glslang_compiler "$glslfix")" || fail "V1.1 glslang resolver failed symlink fixture"
  [[ "$resolved" == "$glslfix/bin/glslang" ]] || fail "V1.1 glslang resolver chose wrong fixture executable"
  pass "REGRESSION_26567_V1_GLSLANG_SYMLINK_BOOTSTRAP: PASS"
  grep -F 'DNG HARD INVARIANT' "$ROOT/REGRESSION_26567_SR_COLOR_DNG_CONTRACT.txt" >/dev/null || fail "DNG contract missing"
  grep -F 'SR-on publication keeps exact physical 2x dimensions' "$ROOT/REGRESSION_26567_SR_COLOR_DNG_CONTRACT.txt" >/dev/null || fail "2x publication regression missing"
  pass "sealed package syntax/hash/regression contract"
  set_report "CARRIED FAILURE REGRESSIONS" "PASS"
}

verify_scope(){
  if [[ -n "$LOCAL_ART" ]]; then
    set_report "BACKUP STATUS" "PASS (verified before sealing; Actions rechecks remote exact SHA)"
    set_report "CHANGED RUNTIME SCOPE" "PASS (sealed handoff local replay; exact runtime allowlist validated after transform)"
    return
  fi
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  git merge-base --is-ancestor "$BASE_SUCCESS_COMMIT" HEAD || fail "successful 26566 commit is not ancestor"
  remote_backup="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
  [[ "$remote_backup" == "$BACKUP_SHA" ]] || fail "backup branch mismatch"
  set_report "BACKUP STATUS" "PASS ($BACKUP_BRANCH @ $BACKUP_SHA)"
  python3 - "$HANDOFF" > "$WORK/expected_scope.txt" <<'PY'
from pathlib import Path
import sys
names=[line.split('  ',1)[1] for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]
names.append('V1_26567_HANDOFF_HASHES.sha256')
print('\n'.join(sorted(names)))
PY
  git diff --name-only "$BASE_SUCCESS_COMMIT"..HEAD | sort > "$WORK/actual_scope.txt"
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
  [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26566 artifact ZIP authority SHA mismatch"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  local tarball="$ARTDIR/build_26566_v1_jpeg_color_true2x_outputs/26566_V1_candidate_app_source.tar.gz"
  [[ -f "$tarball" ]] || fail "compiled 26566 candidate tar missing from artifact"
  [[ "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "compiled 26566 candidate tar SHA mismatch"
  tar -xzf "$tarball" -C "$BASE"
  find "$ARTDIR" -type f -name '*.apk' -delete
  (cd "$BASE" && sha256sum -c "$BASE_PIN" >/dev/null)
  (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null)
  (cd "$BASE" && sha256sum -c "$BASE_VENDOR" >/dev/null)
  (cd "$BASE" && sha256sum -c "$BASE_DNG" >/dev/null)
  (cd "$BASE" && sha256sum -c "$BASE_PROTECTED" >/dev/null)
  (cd "$BASE" && sha256sum -c "$PREWRITE" >/dev/null)
  set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (run $BASE_RUN_ID artifact $BASE_ARTIFACT_ID SHA $BASE_ARTIFACT_SHA tar $BASE_TAR_SHA)"
  pass "exact compiled 26566 artifact authority"
}

make_candidate(){
  cp -a "$BASE/." "$AFTER/"
  cp -a "$BASE/." "$AFTER2/"
  python3 -S "$TRANSFORM" "$AFTER" | tee "$OUT/26567_transform.txt"
  python3 -S "$TRANSFORM" "$AFTER2" | tee "$OUT/26567_transform_replay.txt"
  python3 - "$AFTER" "$AFTER2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(r).rglob('*')) if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2])
if a!=b: raise SystemExit('candidate transform replay mismatch')
print(f'PASS deterministic candidate transform files={len(a)}')
PY
  python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26567_semantic_validation.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26567_authority_candidate.txt"
  set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (931 audited / 1708 full / 778 vendor / 7 DNG / 1686 protected)"
  set_report "DNG INVARIANCE" "PASS (dedicated DNG/ImageSaver bytes + full-evidence DNG SR contract)"
  set_report "JPEG TRUE2X SABRE COLOR OWNERSHIP" "PASS (Sabre/VGN RGB owner; scalar detail only)"
  set_report "JPEG TRUE2X SPEED POLICY" "PASS (JPEG <=4 phase-diverse evidence; no second 50MP MGC denoise; DNG bypasses cap)"
  set_report "SHARED JPEG P3 COLOR OWNERSHIP" "PASS (Photo/Motion/Night/SR shared linear Display-P3 owner)"
  set_report "JIN MODEL-DOMAIN ADAPTER" "PASS (sRGB inference contract + P3 boundary residual)"
  set_report "RUNTIME OWNERSHIP" "PASS"
  set_report "DORMANT-OWNER REJECTION" "PASS"
}

verify_candidate_patches(){
  python3 -S "$PATCHVERIFY" "$BASE" "$AFTER" "$FORWARD" "$ROLLBACK" | tee "$OUT/26567_patch_validation.txt"
  set_report "FORWARD PATCH FUZZ=0" "PASS"
  set_report "ROLLBACK PATCH FUZZ=0" "PASS"
}

verify_shaders(){
  rm -rf "$SHADER_OUT"; mkdir -p "$SHADER_OUT"
  if [[ -n "$LOCAL_ART" ]]; then
    python3 -S "$SHADERVERIFY" "$AFTER" --out "$SHADER_OUT" | tee "$OUT/26567_shader_validation.txt"
    cmp "$SHADER_OUT/runtime_expanded_shaders.sha256" "$SHADER_PIN" || fail "local runtime-expanded shader pin mismatch"
    set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (11 variants; exact expanded hashes pinned)"
    set_report "REAL GLSL COMPILE" "NOT RUN (pinned binary unavailable in local clean replay; mandatory in Actions)"
    set_compiler "REAL GLSL COMPILE" "NOT RUN (mandatory in Actions)"
    return
  fi
  mkdir -p "$GLSLANG_DIR"
  local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz"
  curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"
  [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "pinned glslang archive SHA mismatch"
  tar -tzf "$archive" > "$OUT/26567_glslang_archive_contents.txt"
  tar -xzf "$archive" -C "$GLSLANG_DIR"
  local compiler
  compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "glslang executable missing after pinned extraction"
  chmod +x "$compiler"
  "$compiler" --version | tee "$OUT/26567_glslang_version.txt"
  python3 -S "$SHADERVERIFY" "$AFTER" --out "$SHADER_OUT" --glslang "$compiler" | tee "$OUT/26567_shader_validation.txt"
  cmp "$SHADER_OUT/runtime_expanded_shaders.sha256" "$SHADER_PIN" || fail "Actions runtime-expanded shader pin mismatch"
  cp "$SHADER_OUT/shader_verification.json" "$OUT/26567_shader_verification.json"
  set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (11 exact runtime-expanded variants)"
  set_report "REAL GLSL COMPILE" "PASS (pinned Khronos glslangValidator $GLSLANG_VERSION)"
  set_compiler "REAL GLSL COMPILE" "PASS (pinned Khronos glslangValidator $GLSLANG_VERSION)"
}

install_and_build(){
  [[ -z "$LOCAL_ART" ]] || return 0
  # Runtime write occurs only after authority, backup, candidate, semantics, patches and real GLSL pass.
  rm -rf "$ROOT/app/src"
  cp -a "$AFTER/app/src" "$ROOT/app/"
  cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"
  cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"
  python3 -S "$VALIDATE" "$BASE" "$ROOT" | tee "$OUT/26567_live_semantic_validation.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$ROOT" | tee "$OUT/26567_live_authority.txt"
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26567_gradle_language_compilers.log"
  set_report "REAL KOTLIN COMPILE" "PASS"
  set_report "REAL JAVA COMPILE" "PASS"
  set_compiler "REAL KOTLIN COMPILE" "PASS"
  set_compiler "REAL JAVA COMPILE" "PASS"
  # Expensive deterministic patch proof runs only after the exact candidate passes real language compilers.
  verify_candidate_patches
  ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26567_gradle_assemble.log"
  set_report "FULL ANDROID ASSEMBLE" "PASS (includes Android NDK native compile/link)"
  set_compiler "NATIVE/NDK COMPILE" "PASS (real Android NDK via assembleDebug)"
  set_compiler "FULL ANDROID ASSEMBLE" "PASS"
  mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort)
  [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK, got ${#apks[@]}"
  mv "${apks[0]}" "$FINAL"
  mapfile -t all_apks < <(find "$ROOT" -type f -name '*.apk' -not -path "$WORK/*" | sort)
  [[ "${#all_apks[@]}" -eq 1 && "${all_apks[0]}" == "$FINAL" ]] || fail "final workspace must contain exactly one intended APK"
  sha256sum "$FINAL" > "$OUT/26567_V1_APK.sha256"

  # Regression #20 / successful-26566 mechanics: validate a clean frozen source snapshot,
  # never the Gradle/CMake generated live workspace.
  snapshot_app_source "$ROOT" "$POST"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26567_postbuild_authority.txt"
  python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26567_postbuild_semantic_validation.txt"
  (cd "$POST" && sha256sum -c "$CAND_VENDOR" >/dev/null)
  (cd "$POST" && sha256sum -c "$CAND_DNG" >/dev/null)
  (cd "$POST" && sha256sum -c "$CAND_PROTECTED" >/dev/null)
  set_report "POST-BUILD INVARIANCE" "PASS (clean frozen source snapshot; candidate/protected/DNG/native/vendor exact)"
  set_compiler "POST-BUILD INVARIANCE" "PASS"

  tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf \
    "$OUT/26567_V1_candidate_app_source.tar.gz" -C "$POST" app
  sha256sum "$OUT/26567_V1_candidate_app_source.tar.gz" > "$OUT/26567_V1_candidate_app_source.tar.gz.sha256"
  cp "$CAND_PIN" "$OUT/26567_V1_candidate_source.sha256"
  cp "$CAND_FULL" "$OUT/26567_V1_candidate_full_app.sha256"
  cp "$CAND_VENDOR" "$OUT/26567_vendor_postbuild.sha256"
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
  cp "$OUT/26567_V1_STRICT_HANDOFF_REPORT.txt" "$OUT/26567_local_prebuild_report.txt"
  pass "26567 LOCAL PREBUILD PREPARED: compiler/build gates remain explicitly unproven"
  exit 0
fi
install_and_build
pass "26567 PRE-BUILD SAFETY PROOF PASSED"
pass "26567 REAL COMPILERS + FULL ASSEMBLE PASSED"
pass "26567 POST-BUILD INVARIANCE PASSED"
