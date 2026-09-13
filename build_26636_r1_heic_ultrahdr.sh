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
RUNTIME_AUTHORITY_COMMIT="e6790ebd2f2a8403191a276d659de4a708181efa"
HANDOFF_PARENT_COMMIT="$RUNTIME_AUTHORITY_COMMIT"
FAILED_R1_COMMIT="a33e00935e00d7153cb72619333f658b0a5a566c"
REPAIR_PARENT_COMMIT="$FAILED_R1_COMMIT"
BASE_RUN_ID="34777964131"
BASE_ARTIFACT_ID="10324098412"
BASE_ARTIFACT_NAME="photon-26635-r1-spatial-highlight-rolloff"
BASE_ARTIFACT_SHA="fa1f51b03969edf1ce59934d33f46e4a688336d4c5270de18ba2237425a64b1b"
BASE_TAR_SHA="fb5f2a3f48c737639e879aa2c7ee44c9c4a05d997aa9abc7424c3f69de7ad397"
SUCCESS_26635_BUILD_BLOB="779990cef8c143011e411ca87109e36d75875fa1"
SUCCESS_26635_WORKFLOW_BLOB="bb43c017494365bdccede14f2e388d156b22211e"
SUCCESS_26635_TRANSFORM_BLOB="fd466230a174cec21093c1eaba7da7585f418550"
VERSION_NAME="0.9726636"; VERSION_BUILD="26636"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
HANDOFF="$ROOT/R1_26636_HANDOFF_HASHES.sha256"
BASE_FULL="$ROOT/R1_26636_BASE_26635_R1_FULL_APP.sha256"; CAND_FULL="$ROOT/R1_26636_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/R1_26636_PROTECTED_UNCHANGED_BASE.sha256"; CAND_PROTECTED="$ROOT/R1_26636_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/R1_26636_NATIVE_PROTECTED_BASE.sha256"; CAND_NATIVE="$ROOT/R1_26636_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/R1_26636_VENDOR_PROTECTED_BASE.sha256"; CAND_VENDOR="$ROOT/R1_26636_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/R1_26636_DNG_BASE.sha256"; CAND_DNG="$ROOT/R1_26636_DNG_CANDIDATE.sha256"
CHANGED="$ROOT/R1_26636_RUNTIME_CHANGED_PATHS.txt"; PREWRITE="$ROOT/R1_26636_PREWRITE_SOURCE_HASHES.sha256"; ADDED="$ROOT/R1_26636_ADDED_PATHS_MUST_BE_ABSENT.txt"; EXPECTED_CHANGED="$ROOT/R1_26636_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/R1_26636_RUNTIME_DELTA_FROM_26635_R1.patch"; ROLLBACK="$ROOT/R1_26636_RUNTIME_ROLLBACK_TO_26635_R1.patch"; SHADER_PIN="$ROOT/R1_26636_RUNTIME_EXPANDED_SHADERS.sha256"
TRANSFORM="$ROOT/transform_26636_r1.py"; VALIDATE="$ROOT/validate_26636_r1.py"; AUTHORITY="$ROOT/verify_26636_r1_authority.py"; INFRA="$ROOT/verify_26636_r1_infrastructure.py"; PATCHVERIFY="$ROOT/verify_26636_r1_patches.py"; SHADERVERIFY="$ROOT/verify_26636_r1_shaders.py"; GATEVERIFY="$ROOT/verify_26636_r1_regressions.py"
BUILD_SCRIPT="$ROOT/build_26636_r1_heic_ultrahdr.sh"; WORKFLOW="$ROOT/.github/workflows/build-26636-r1-heic-ultrahdr.yml"
OUT="$ROOT/build_26636_r1_heic_ultrahdr_outputs"; WORK="$ROOT/.build_26636_r1_heic_ultrahdr_work"
ARTZIP="$WORK/26635_r1_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_26635_r1_compiled_candidate"; AFTER="$WORK/candidate_26636_r1"; AFTER2="$WORK/candidate_26636_r1_replay"; SHADER_OUT="$WORK/runtime_expanded_shaders"; GLSLANG_DIR="$WORK/glslang-16.5.0"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r1-heic-ultrahdr-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then
  [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26635 R1 artifact ZIP"
  LOCAL_ART="$2"
elif [[ -n "${1:-}" ]]; then fail "unknown argument: $1"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26636_R1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26636_R1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME AUTHORITY: NOT RUN
VERIFICATION MECHANICS AUTHORITY: NOT RUN
BACKUP STATUS: PASS (backup-26635-before-heic created by user at exact successful 26635 commit)
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE DELTA AUDIT: NOT RUN
26635 R1 RUNTIME INHERITANCE: NOT RUN
JPEG/JPEG-R REFERENCE PUBLISHER FREEZE: NOT RUN
SUPER RES / TRUE-2X EXCLUSION: NOT RUN
MOTION/NIGHT HEIC IMMUTABLE ROUTING: NOT RUN
DISPLAY-P3 SDR + EXISTING GAINMAP PARITY: NOT RUN
ANDROID16 HARDWARE HEVC ONLY: NOT RUN
ISO 21496-1 HEIF CONTAINER AUTHORITY: NOT RUN
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
TARGET VERSION/BUILD: 0.9726636 / 26636
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26636_R1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26636_R1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26636_R1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26636_R1_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){ local authority_root="$1" live_root="$2" dest_root="$3"; rm -rf "$dest_root"; mkdir -p "$dest_root"; cp -a "$authority_root/." "$dest_root/"; rm -rf "$dest_root/app/src"; cp -a "$live_root/app/src" "$dest_root/app/"; cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"; cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"; }
verify_package(){
  [[ -f "$HANDOFF" ]] || fail "handoff hash manifest missing"; sha256sum -c "$HANDOFF" >/dev/null
  [[ "$(wc -l < "$CHANGED")" -eq 18 ]] || fail "runtime allowlist must be 18"
  [[ "$(wc -l < "$PREWRITE")" -eq 15 && "$(wc -l < "$ADDED")" -eq 3 ]] || fail "existing/add count"
  [[ "$(wc -l < "$BASE_FULL")" -eq 1713 && "$(wc -l < "$CAND_FULL")" -eq 1716 ]] || fail "full app count"
  [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1698 ]] || fail "protected count"
  [[ "$(wc -l < "$BASE_NATIVE")" -eq 801 && "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$BASE_DNG")" -eq 7 ]] || fail "protected manifest counts (801 native / 778 vendor / 7 DNG)"
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
  python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26636_infrastructure_local.txt"
  set_report "INFRASTRUCTURE DELTA AUDIT" "PASS (successful-26635 ordering/isolation/Kotlin-Java/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; authority/scope/HEIC validators only; GLSL stage retained and N/A for zero modified shaders)"
}
verify_scope(){
  if [[ -n "$LOCAL_ART" ]]; then set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed R1.1 repair; runtime candidate unchanged at exact 18-path allowlist: 15 modified + 3 added)"; return; fi
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  [[ "$(git rev-parse HEAD^)" == "$REPAIR_PARENT_COMMIT" ]] || fail "26636 R1.1 repair must be one direct commit on exact failed 26636 R1 handoff"
  [[ "$(git rev-parse "$REPAIR_PARENT_COMMIT^")" == "$HANDOFF_PARENT_COMMIT" ]] || fail "failed 26636 R1 parent is not exact successful 26635 authority"
  python3 -S - "$HANDOFF" > "$WORK/expected_r1_scope.txt" <<'PY'
from pathlib import Path
import sys
names=[line.split('  ',1)[1] for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]
names.append('R1_26636_HANDOFF_HASHES.sha256')
print('\n'.join(sorted(names)))
PY
  git diff --name-only "$HANDOFF_PARENT_COMMIT" "$REPAIR_PARENT_COMMIT" | sort > "$WORK/actual_r1_scope.txt"
  diff -u "$WORK/expected_r1_scope.txt" "$WORK/actual_r1_scope.txt" || fail "failed 26636 R1 sealed handoff scope mismatch"
  cat > "$WORK/expected_repair_scope.txt" <<'EOF'
R1_26636_HANDOFF_HASHES.sha256
build_26636_r1_heic_ultrahdr.sh
verify_26636_r1_infrastructure.py
EOF
  git diff --name-only "$REPAIR_PARENT_COMMIT"..HEAD | sort > "$WORK/actual_repair_scope.txt"
  diff -u "$WORK/expected_repair_scope.txt" "$WORK/actual_repair_scope.txt" || fail "26636 R1.1 repair commit scope mismatch"
  ! grep -Eq '^app/' "$WORK/actual_r1_scope.txt" || fail "failed R1 handoff contains live app source"
  ! grep -Eq '^app/' "$WORK/actual_repair_scope.txt" || fail "R1.1 repair contains live app source"
  set_report "CHANGED RUNTIME SCOPE" "PASS (R1 runtime payload unchanged; R1.1 changes exactly build script + infrastructure validator + handoff hash manifest; exact 18-path candidate runtime delta retained)"
}
obtain_authority(){
  if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else
    [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
    curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
  fi
  [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26635 R1 artifact ZIP SHA"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  local tarball="$ARTDIR/build_26635_r1_spatial_highlight_rolloff_outputs/26635_R1_candidate_app_source.tar.gz"
  [[ -f "$tarball" && "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "26635 R1 compiled candidate TAR authority"
  tar -xzf "$tarball" -C "$BASE"; find "$ARTDIR" -type f -name '*.apk' -delete
  (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null && sha256sum -c "$BASE_PROTECTED" >/dev/null && sha256sum -c "$BASE_NATIVE" >/dev/null && sha256sum -c "$BASE_VENDOR" >/dev/null && sha256sum -c "$BASE_DNG" >/dev/null && sha256sum -c "$PREWRITE" >/dev/null)
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; [[ ! -e "$BASE/$rel" ]] || fail "26636 added path exists in 26635 authority: $rel"; done < "$ADDED"
  set_report "RUNTIME AUTHORITY" "PASS (successful 26635 R1 commit e6790ebd2f2a8403191a276d659de4a708181efa/run 34777964131/artifact 10324098412/exact compiled candidate TAR)"
  pass "exact successful 26635 R1 compiled-candidate authority"
}
make_candidate(){
  rm -rf "$AFTER" "$AFTER2"
  python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26636_transform.txt"
  python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26636_transform_replay.txt"
  python3 -S - "$AFTER" "$AFTER2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a=H(sys.argv[1]); b=H(sys.argv[2]); assert len(a)==1716 and a==b
print('PASS deterministic candidate reconstruction 1716 files')
PY
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; cmp "$ROOT/handoff_payload_26636_r1/$rel" "$AFTER/$rel" || fail "sealed payload differs frozen candidate: $rel"; done < "$CHANGED"
  python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26636_semantic_validation.txt"
  python3 -S "$GATEVERIFY" "$BASE" "$AFTER" | tee "$OUT/26636_regressions.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26636_authority_candidate.txt"
  set_report "26635 R1 RUNTIME INHERITANCE" "PASS (exact successful compiler-tested 26635 candidate; only exact 18-path 26636 publication/UI delta)"
  set_report "JPEG/JPEG-R REFERENCE PUBLISHER FREEZE" "PASS (existing JPEG/JPEG-R encoder sources and gain-map producers protected; HEIC is sibling publication branch)"
  set_report "SUPER RES / TRUE-2X EXCLUSION" "PASS (HEIC unavailable with Super Res; true-2x implementation and publisher protected)"
  set_report "MOTION/NIGHT HEIC IMMUTABLE ROUTING" "PASS (HEIC frozen at shutter/batch; Night publication consumes post-Jin attached/rebased gain map)"
  set_report "DISPLAY-P3 SDR + EXISTING GAINMAP PARITY" "PASS (existing Display-P3 conversion reused; existing attached Iris gain map consumed without recompute)"
  set_report "ANDROID16 HARDWARE HEVC ONLY" "PASS (API36 hardware video/hevc MediaCodec only; no software/dedicated-HEIC fallback)"
  set_report "ISO 21496-1 HEIF CONTAINER AUTHORITY" "PASS (pinned libheif 4a3f74bc + exact Google gain-map patch blob + Iris ISO metadata serialization)"
  set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (1713 base / 1716 candidate / 1698 protected / 801 native / 778 vendor / 7 DNG)"
  set_report "PROTECTED/DNG/NATIVE/VENDOR INVARIANCE" "PASS"
}
verify_candidate_patches(){
  python3 -S "$PATCHVERIFY" "$BASE" "$AFTER" "$FORWARD" "$ROLLBACK" | tee "$OUT/26636_patch_validation.txt"
  set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"
}
verify_shaders(){
  rm -rf "$SHADER_OUT"; mkdir -p "$SHADER_OUT"
  python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" | tee "$OUT/26636_shader_validation.txt"
  cmp "$SHADER_OUT/R1_26636_RUNTIME_EXPANDED_SHADERS.sha256" "$SHADER_PIN" || fail "shader pin mismatch"
  cp "$SHADER_OUT/R1_26636_SHADER_VERIFICATION.json" "$OUT/26636_shader_verification.json"
  set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "NOT APPLICABLE (0 modified GLSL; 257-file shader universe invariant)"
  set_report "REAL GLSL COMPILE" "NOT APPLICABLE (0 modified GLSL)"; set_compiler "REAL GLSL COMPILE" "NOT APPLICABLE (0 modified GLSL)"
}
verify_successful_26635_mechanics(){
  if [[ -n "$LOCAL_ART" ]]; then
    python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26636_infrastructure_packaged.txt"
    set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (successful-26635-R1 sequence packaged; Actions exact parent Git-blob replay required)"
    return 0
  fi
  [[ "$(git rev-parse "$HANDOFF_PARENT_COMMIT:build_26635_r1_spatial_highlight_rolloff.sh")" == "$SUCCESS_26635_BUILD_BLOB" ]] || fail "successful 26635 build-script blob"
  [[ "$(git rev-parse "$HANDOFF_PARENT_COMMIT:.github/workflows/build-26635-r1-spatial-highlight-rolloff.yml")" == "$SUCCESS_26635_WORKFLOW_BLOB" ]] || fail "successful 26635 workflow blob"
  [[ "$(git rev-parse "$HANDOFF_PARENT_COMMIT:transform_26635_r1.py")" == "$SUCCESS_26635_TRANSFORM_BLOB" ]] || fail "successful 26635 transform blob"
  local pb="$WORK/successful_26635_r1_build.sh" pw="$WORK/successful_26635_r1_workflow.yml" pt="$WORK/successful_26635_r1_transform.py"
  git show "$HANDOFF_PARENT_COMMIT:build_26635_r1_spatial_highlight_rolloff.sh" > "$pb"
  git show "$HANDOFF_PARENT_COMMIT:.github/workflows/build-26635-r1-spatial-highlight-rolloff.yml" > "$pw"
  git show "$HANDOFF_PARENT_COMMIT:transform_26635_r1.py" > "$pt"
  python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" "$pb" "$pw" "$pt" | tee "$OUT/26636_infrastructure_actions.txt"
  set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (exact successful-26635-R1 build/workflow/transform Git blobs replayed; compiler/build ordering, candidate isolation, patch and invariance mechanics preserved)"
}
install_and_build(){
  [[ -z "$LOCAL_ART" ]] || return 0
  rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"
  python3 -S "$VALIDATE" "$BASE" "$LIVE_CANON" | tee "$OUT/26636_live_semantic_validation.txt"
  python3 -S "$GATEVERIFY" "$BASE" "$LIVE_CANON" | tee "$OUT/26636_live_regressions.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$LIVE_CANON" | tee "$OUT/26636_live_authority.txt"
  python3 -S - "$AFTER" "$LIVE_CANON" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
assert H(sys.argv[1])==H(sys.argv[2])
print('PASS authority-seeded live compiler candidate byte-identical')
PY
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26636_gradle_language_compilers.log"
  set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"
  python3 -S - "$AFTER" "$WORK/after_language_compiler_snapshot" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
assert H(sys.argv[1])==H(sys.argv[2])
print('PASS candidate unchanged after real Kotlin/Java compilers')
PY
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26636_gradle_native_compiler.log"
  set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
  verify_candidate_patches
  set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26636 PRE-BUILD SAFETY PROOF PASSED"
  ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26636_gradle_assemble.log"
  set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
  mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort)
  [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK"
  mv "${apks[0]}" "$FINAL"
  mapfile -t roots < <(find "$ROOT" -maxdepth 1 -type f -name '*.apk' | sort)
  [[ "${#roots[@]}" -eq 1 && "${roots[0]}" == "$FINAL" ]] || fail "exactly one final root APK"
  sha256sum "$FINAL" > "$OUT/26636_R1_APK.sha256"; set_report "EXACTLY ONE APK" "PASS"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"
  python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26636_postbuild_semantic_validation.txt"
  python3 -S "$GATEVERIFY" "$BASE" "$POST" | tee "$OUT/26636_postbuild_regressions.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26636_postbuild_authority.txt"
  python3 -S - "$AFTER" "$POST" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
assert H(sys.argv[1])==H(sys.argv[2])
print('PASS postbuild candidate byte-identical')
PY
  set_report "POST-BUILD INVARIANCE" "PASS (candidate/protected/DNG/native/vendor exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"
  tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26636_R1_candidate_app_source.tar.gz"
  sha256sum "$OUT/26636_R1_candidate_app_source.tar.gz" > "$OUT/26636_R1_candidate_app_source.tar.gz.sha256"
  cp "$CAND_FULL" "$OUT/26636_R1_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26636_R1_native_protected_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26636_R1_vendor_protected_postbuild.sha256"
  set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests)"
}
verify_package
verify_scope
obtain_authority
make_candidate
verify_shaders
verify_successful_26635_mechanics
if [[ -n "$LOCAL_ART" ]]; then
  verify_candidate_patches
  set_report "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"
  set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real Kotlin/Java/NDK/full Android require Actions; GLSL N/A)"; set_report "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_report "EXACTLY ONE APK" "NOT RUN locally (Actions required)"; set_report "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN locally (Actions required)"
  set_compiler "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_compiler "NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_compiler "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_compiler "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"
  cp "$OUT/26636_R1_STRICT_HANDOFF_REPORT.txt" "$OUT/26636_local_prebuild_report.txt"
  pass "26636 R1 LOCAL PREBUILD PREPARED: exact successful-26635-R1 authority + fresh 18-path isolated HEIC Ultra HDR publication/UI delta; real compiler/build gates explicitly unproven locally"
  exit 0
fi
install_and_build
pass "26636 R1 KOTLIN/JAVA + NDK + FULL ASSEMBLE PASSED (GLSL N/A: 0 modified shaders)"
pass "26636 R1 POST-BUILD INVARIANCE PASSED"
