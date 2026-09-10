#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
resolve_glslang_compiler(){
  local root="$1" compiler="" compat=""
  compiler="$(find "$root" -type f -name glslang -print -quit)"
  if [[ -z "$compiler" ]]; then compat="$(find "$root" \( -type f -o -type l \) -name glslangValidator -print -quit)"; if [[ -n "$compat" ]]; then compiler="$(readlink -f "$compat" 2>/dev/null || true)"; fi; fi
  [[ -n "$compiler" && -f "$compiler" ]] || return 1; printf '%s\n' "$compiler"
}
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="34dce306c8f1b333511db8e2fbdb58555e9e9bd2"
HANDOFF_PARENT_COMMIT="7a0532a9aa26ea0d92ab71c8d7c6965a9139524b"
BASE_RUN_ID="34426075869"
BASE_ARTIFACT_ID="10132769400"
BASE_ARTIFACT_NAME="photon-26618-r1-guided-base-detail-ltm"
BASE_ARTIFACT_SHA="3121977d6f6064e6cd2f41e3ad913572505df2f3a892671736af8ef0db1327f1"
BASE_TAR_SHA="150e70d4b044ae8c3caa35758f5dbbffa505dd31b80ec76c535864f55645e3ea"
VERSION_NAME="0.9726619"; VERSION_BUILD="26619"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
HANDOFF="$ROOT/R2_26619_HANDOFF_HASHES.sha256"
BASE_FULL="$ROOT/R2_26619_BASE_26618_R1_FULL_APP.sha256"; CAND_FULL="$ROOT/R2_26619_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/R2_26619_PROTECTED_UNCHANGED_BASE.sha256"; CAND_PROTECTED="$ROOT/R2_26619_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/R2_26619_NATIVE_PROTECTED_BASE.sha256"; CAND_NATIVE="$ROOT/R2_26619_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/R2_26619_VENDOR_PROTECTED_BASE.sha256"; CAND_VENDOR="$ROOT/R2_26619_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/R2_26619_DNG_BASE.sha256"; CAND_DNG="$ROOT/R2_26619_DNG_CANDIDATE.sha256"
CHANGED="$ROOT/R2_26619_RUNTIME_CHANGED_PATHS.txt"; PREWRITE="$ROOT/R2_26619_PREWRITE_SOURCE_HASHES.sha256"; ADDED="$ROOT/R2_26619_ADDED_PATHS_MUST_BE_ABSENT.txt"; DELETED="$ROOT/R2_26619_DELETED_PATHS_MUST_BE_ABSENT.txt"; EXPECTED_CHANGED="$ROOT/R2_26619_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/R2_26619_RUNTIME_DELTA_FROM_26618_R1.patch"; ROLLBACK="$ROOT/R2_26619_RUNTIME_ROLLBACK_TO_26618_R1.patch"; SHADER_PIN="$ROOT/R2_26619_RUNTIME_EXPANDED_SHADERS.sha256"
TRANSFORM="$ROOT/transform_26619_r2.py"; VALIDATE="$ROOT/validate_26619_r2.py"; AUTHORITY="$ROOT/verify_26619_r2_authority.py"; INFRA="$ROOT/verify_26619_r2_infrastructure.py"; PATCHVERIFY="$ROOT/verify_26619_r2_patches.py"; SHADERVERIFY="$ROOT/verify_26619_r2_shaders.py"; GATEVERIFY="$ROOT/verify_26619_r2_regressions.py"
BUILD_SCRIPT="$ROOT/build_26619_r2_monotonic_guided_base_detail_ltm.sh"; WORKFLOW="$ROOT/.github/workflows/build-26619-r2-monotonic-guided-base-detail.yml"
OUT="$ROOT/build_26619_r2_monotonic_guided_base_detail_ltm_outputs"; WORK="$ROOT/.build_26619_r2_monotonic_guided_base_detail_ltm_work"; ARTZIP="$WORK/26618_r1_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_26618_r1_compiled_candidate"; AFTER="$WORK/candidate_26619_r2"; AFTER2="$WORK/candidate_26619_r2_replay"; SHADER_OUT="$WORK/runtime_expanded_shaders"; GLSLANG_DIR="$WORK/glslang-16.5.0"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r2-monotonic-guided-base-detail-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""; if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26618 R1 artifact ZIP"; LOCAL_ART="$2"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26619_R2_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26619_R2_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME AUTHORITY: NOT RUN
VERIFICATION MECHANICS AUTHORITY: NOT RUN
BACKUP STATUS: NO BACKUP (USER REQUEST); exact immutable 26618 artifact + deterministic rollback patch are rollback authority
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE DELTA AUDIT: NOT RUN
26618 R1 RUNTIME INHERITANCE: NOT RUN
MONOTONIC GUIDED BASE/DETAIL OWNERSHIP: NOT RUN
VIEWFINDER TARGET OWNERSHIP: NOT RUN
UHDR BODY/HEADROOM PARITY: NOT RUN
SUPER-RES APPEARANCE PARITY: NOT RUN
RAW/CFA COLOR VALIDITY INHERITANCE: NOT RUN
SABRE/SHORT/DNG INHERITANCE: NOT RUN
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
TARGET VERSION/BUILD: 0.9726619 / 26619
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26619_R2_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26619_R2_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26619_R2_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26619_R2_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){ local authority_root="$1" live_root="$2" dest_root="$3"; rm -rf "$dest_root"; mkdir -p "$dest_root"; cp -a "$authority_root/." "$dest_root/"; rm -rf "$dest_root/app/src"; cp -a "$live_root/app/src" "$dest_root/app/"; cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"; cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"; }
verify_package(){
  [[ -f "$HANDOFF" ]] || fail "handoff hash manifest missing"; sha256sum -c "$HANDOFF" >/dev/null
  [[ "$(wc -l < "$CHANGED")" -eq 13 ]] || fail "runtime allowlist must be 13"
  [[ "$(wc -l < "$PREWRITE")" -eq 11 && "$(wc -l < "$ADDED")" -eq 2 && "$(wc -l < "$DELETED")" -eq 3 ]] || fail "existing/add/delete count"
  [[ "$(wc -l < "$BASE_FULL")" -eq 1712 && "$(wc -l < "$CAND_FULL")" -eq 1711 ]] || fail "full app count"
  [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1701 ]] || fail "protected count"
  [[ "$(wc -l < "$BASE_NATIVE")" -eq 802 && "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$BASE_DNG")" -eq 7 ]] || fail "protected manifest counts"
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
  python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26619_infrastructure_local.txt"
  set_report "INFRASTRUCTURE DELTA AUDIT" "PASS (identity/26618-authority/count/26619 algorithm validators only; exact successful-26618 compiler/build ordering/isolation preserved)"
}
verify_scope(){
  if [[ -n "$LOCAL_ART" ]]; then set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed handoff; exact 13-path runtime allowlist)"; return; fi
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  [[ "$(git rev-parse HEAD^)" == "$HANDOFF_PARENT_COMMIT" ]] || fail "26619 sealed handoff must be one commit on expected repository parent; runtime authority remains exact successful 26618 compiled artifact"
  python3 -S - "$HANDOFF" > "$WORK/expected_scope.txt" <<'PY'
from pathlib import Path
import sys
names=[line.split('  ',1)[1] for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]; names.append('R2_26619_HANDOFF_HASHES.sha256'); print('\n'.join(sorted(names)))
PY
  git diff --name-only "$HANDOFF_PARENT_COMMIT"..HEAD | sort > "$WORK/actual_scope.txt"; diff -u "$WORK/expected_scope.txt" "$WORK/actual_scope.txt" || fail "handoff commit scope mismatch"; ! grep -Eq '^app/' "$WORK/actual_scope.txt" || fail "handoff commit contains live app source"
  set_report "CHANGED RUNTIME SCOPE" "PASS (sealed infrastructure/payload only; exact 13-path candidate runtime delta; no live app source committed)"
}
obtain_authority(){
  if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
  [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26618 R1 artifact ZIP SHA"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  local tarball="$ARTDIR/build_26618_r1_guided_base_detail_ltm_outputs/26618_R1_candidate_app_source.tar.gz"
  [[ -f "$tarball" && "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "26618 R1 compiled candidate TAR authority"
  tar -xzf "$tarball" -C "$BASE"; find "$ARTDIR" -type f -name '*.apk' -delete
  (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null && sha256sum -c "$BASE_PROTECTED" >/dev/null && sha256sum -c "$BASE_NATIVE" >/dev/null && sha256sum -c "$BASE_VENDOR" >/dev/null && sha256sum -c "$BASE_DNG" >/dev/null && sha256sum -c "$PREWRITE" >/dev/null)
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; [[ ! -e "$BASE/$rel" ]] || fail "26619 added path exists in 26618 authority $rel"; done < "$ADDED"
  set_report "RUNTIME AUTHORITY" "PASS (successful 26618 R1 commit 34dce306/run 34426075869/artifact 10132769400/exact compiled candidate TAR)"; pass "exact successful 26618 R1 compiled-candidate authority"
}
make_candidate(){
  rm -rf "$AFTER" "$AFTER2"; python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26619_transform.txt"; python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26619_transform_replay.txt"
  python3 -S - "$AFTER" "$AFTER2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
assert H(sys.argv[1])==H(sys.argv[2]); print('PASS deterministic candidate reconstruction 1711 files')
PY
  while read -r _sha rel; do [[ -n "${rel:-}" ]] || continue; cmp "$ROOT/handoff_payload_26619_r2/$rel" "$AFTER/$rel" || fail "sealed payload differs frozen candidate $rel"; done < "$EXPECTED_CHANGED"
  python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26619_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$AFTER" | tee "$OUT/26619_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26619_authority_candidate.txt"
  set_report "26618 R1 RUNTIME INHERITANCE" "PASS (exact successful 26618 compiled candidate; only 13-path intended 26619 presentation delta)"; set_report "MONOTONIC GUIDED BASE/DETAIL OWNERSHIP" "PASS (single Motion-only guided final-tone-guide base; final renderer maps broad base monotonically and recombines measured log-detail)"; set_report "VIEWFINDER TARGET OWNERSHIP" "PASS (successful-26618 matcher remains target owner; display exposure pass-through; MotionV2Render is sole spatial/final presentation owner)"; set_report "UHDR BODY/HEADROOM PARITY" "PASS (successful-26618 gainmap byte-identical; normalized SDR/UHDR body shares corrected presentation and genuine >1 source remains gainmap headroom authority)"; set_report "SUPER-RES APPEARANCE PARITY" "PASS (true2x consumes exact shared guided base-log field; CPU/cached/GPU use same monotonic base/detail composition)"; set_report "RAW/CFA COLOR VALIDITY INHERITANCE" "PASS (successful-26618 CFA provenance owners byte-identical)"; set_report "SABRE/SHORT/DNG INHERITANCE" "PASS (successful-26618 reconstruction/capture/DNG owners outside runtime delta)"; set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (1712 base / 1711 candidate / 1701 protected / 802 native / 778 vendor / 7 DNG)"; set_report "PROTECTED/DNG/NATIVE/VENDOR INVARIANCE" "PASS"
}
verify_candidate_patches(){ python3 -S "$PATCHVERIFY" "$BASE" "$AFTER" "$FORWARD" "$ROLLBACK" | tee "$OUT/26619_patch_validation.txt"; set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"; }
verify_shaders(){
  rm -rf "$SHADER_OUT"; mkdir -p "$SHADER_OUT"
  if [[ -n "$LOCAL_ART" ]]; then python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" | tee "$OUT/26619_shader_validation.txt"; cmp "$SHADER_OUT/R2_26619_RUNTIME_EXPANDED_SHADERS.sha256" "$SHADER_PIN" || fail "local shader pin mismatch"; cp "$SHADER_OUT/R2_26619_SHADER_VERIFICATION.json" "$OUT/26619_shader_verification.json"; set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (4 exact modified variants)"; set_report "REAL GLSL COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL GLSL COMPILE" "NOT RUN locally (Actions required)"; return; fi
  mkdir -p "$GLSLANG_DIR"; local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"; [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive SHA"; tar -xzf "$archive" -C "$GLSLANG_DIR"; local compiler; compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "pinned glslang compiler missing"; "$compiler" --version | tee "$OUT/26619_glslang_version.txt"; python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" --compiler "$compiler" | tee "$OUT/26619_shader_validation.txt"; cmp "$SHADER_OUT/R2_26619_RUNTIME_EXPANDED_SHADERS.sha256" "$SHADER_PIN" || fail "shader pin mismatch"; cp "$SHADER_OUT/R2_26619_SHADER_VERIFICATION.json" "$OUT/26619_shader_verification.json"; set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (4 exact modified variants)"; set_report "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0)"; set_compiler "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0)"
}
install_and_build(){
  [[ -z "$LOCAL_ART" ]] || return 0
  local success26618Script="$WORK/successful_26618_r1_build.sh" success26618Workflow="$WORK/successful_26618_r1_workflow.yml" success26618Transform="$WORK/successful_26618_r1_transform.py"
  curl -L --fail --retry 3 "https://raw.githubusercontent.com/SkyKing0007/Photon-Camera/$RUNTIME_AUTHORITY_COMMIT/build_26618_r1_guided_base_detail_ltm.sh" -o "$success26618Script"; curl -L --fail --retry 3 "https://raw.githubusercontent.com/SkyKing0007/Photon-Camera/$RUNTIME_AUTHORITY_COMMIT/.github/workflows/build-26618-r1-guided-base-detail-ltm.yml" -o "$success26618Workflow"; curl -L --fail --retry 3 "https://raw.githubusercontent.com/SkyKing0007/Photon-Camera/$RUNTIME_AUTHORITY_COMMIT/transform_26618_r1.py" -o "$success26618Transform"
  [[ "$(sha "$success26618Script")" == "8217bc2daf8cc3d5a48fe7a451c777291241ba043dc7c9a64e4f16e02b068775" ]] || fail "successful 26618 build mechanics SHA"; [[ "$(sha "$success26618Workflow")" == "eb9071c83eb469b29ca685cc05733cb3b6f8f5f626049ec4b3e24b2678121c07" ]] || fail "successful 26618 workflow mechanics SHA"; [[ "$(sha "$success26618Transform")" == "63dc96b362d4c501ab2b7b3cf3bb6b2623490e9a986315aac71f1c7f4fe2ed01" ]] || fail "successful 26618 transform mechanics SHA"
  python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" --success-26618-script "$success26618Script" --success-26618-workflow "$success26618Workflow" --success-26618-transform "$success26618Transform" | tee "$OUT/26619_infrastructure_actions.txt"; set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (exact successful-26618 compiler/build order, toolchain pins, nested candidate isolation and postbuild invariance mechanics preserved)"
  rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"; snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"; python3 -S "$VALIDATE" "$BASE" "$LIVE_CANON" | tee "$OUT/26619_live_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$LIVE_CANON" | tee "$OUT/26619_live_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$LIVE_CANON" | tee "$OUT/26619_live_authority.txt"
  python3 -S - "$AFTER" "$LIVE_CANON" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
assert H(sys.argv[1])==H(sys.argv[2]); print('PASS authority-seeded live compiler candidate byte-identical')
PY
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26619_gradle_language_compilers.log"; set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26619_gradle_native_compiler.log"; set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
  verify_candidate_patches; set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26619 PRE-BUILD SAFETY PROOF PASSED"
  ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26619_gradle_assemble.log"; set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
  mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort); [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK"; mv "${apks[0]}" "$FINAL"; mapfile -t roots < <(find "$ROOT" -maxdepth 1 -type f -name '*.apk' | sort); [[ "${#roots[@]}" -eq 1 && "${roots[0]}" == "$FINAL" ]] || fail "exactly one final root APK"; sha256sum "$FINAL" > "$OUT/26619_R2_APK.sha256"; set_report "EXACTLY ONE APK" "PASS"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"; python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26619_postbuild_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$POST" | tee "$OUT/26619_postbuild_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26619_postbuild_authority.txt"
  python3 -S - "$AFTER" "$POST" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
assert H(sys.argv[1])==H(sys.argv[2]); print('PASS postbuild candidate byte-identical')
PY
  set_report "POST-BUILD INVARIANCE" "PASS (candidate/protected/DNG/native/vendor exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"; tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26619_R2_candidate_app_source.tar.gz"; sha256sum "$OUT/26619_R2_candidate_app_source.tar.gz" > "$OUT/26619_R2_candidate_app_source.tar.gz.sha256"; cp "$CAND_FULL" "$OUT/26619_R2_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26619_R2_native_protected_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26619_R2_vendor_protected_postbuild.sha256"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests)"
}
verify_package
verify_scope
obtain_authority
make_candidate
verify_shaders
if [[ -n "$LOCAL_ART" ]]; then verify_candidate_patches; set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (successful-26618 sequence packaged; Actions real compiler replay required)"; set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real GLSL/Kotlin/Java/NDK/full Android require Actions)"; set_compiler "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_compiler "NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_compiler "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_compiler "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; cp "$OUT/26619_R2_STRICT_HANDOFF_REPORT.txt" "$OUT/26619_local_prebuild_report.txt"; pass "26619 R2 LOCAL PREBUILD PREPARED: exact successful-26618 authority + monotonic final-owner guided base/detail LTM; real compiler/build gates explicitly unproven locally"; exit 0; fi
install_and_build
pass "26619 R2 REAL GLSL + KOTLIN/JAVA + NDK + FULL ASSEMBLE PASSED"
pass "26619 R2 POST-BUILD INVARIANCE PASSED"
