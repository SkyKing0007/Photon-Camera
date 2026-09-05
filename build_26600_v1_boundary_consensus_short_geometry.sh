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
BASE_SUCCESS_COMMIT="4c4962354fab1603db98d190cff6f9bba5ed46ba"
MECHANICS_GOLDEN_COMMIT="7c485416a8f41f9bf8a834bf4282e7c2318fa9fb"
HANDOFF_PARENT_COMMIT="4c4962354fab1603db98d190cff6f9bba5ed46ba"
BASE_RUN_ID="33946659672"
BASE_JOB_ID="101253882718"
BASE_ARTIFACT_ID="9963583434"
BASE_ARTIFACT_NAME="photon-26599-v1-effective-short-shared-hdr-tone"
BASE_ARTIFACT_SHA="cc775a06b499a268a75bfd74bae630190dd3578cfb0c6d0924e90703a77cf40f"
BASE_TAR_SHA="efac0414844b664943991f3b118154c54e6235a0dc31c8ff22b85bd502c4f361"
VERSION_NAME="0.9726600"
VERSION_BUILD="26600"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
SEALED_PAYLOAD_COUNT=31
HANDOFF="$ROOT/V1_26600_HANDOFF_HASHES.sha256"
BASE_FULL="$ROOT/V1_26600_BASE_26599_FULL_APP.sha256"; CAND_FULL="$ROOT/V1_26600_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/V1_26600_PROTECTED_UNCHANGED_BASE.sha256"; CAND_PROTECTED="$ROOT/V1_26600_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/V1_26600_NATIVE_PROTECTED_BASE.sha256"; CAND_NATIVE="$ROOT/V1_26600_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/V1_26600_VENDOR_BASE.sha256"; CAND_VENDOR="$ROOT/V1_26600_VENDOR_CANDIDATE.sha256"
BASE_DNG="$ROOT/V1_26600_DNG_BASE.sha256"; CAND_DNG="$ROOT/V1_26600_DNG_CANDIDATE.sha256"
CHANGED="$ROOT/V1_26600_RUNTIME_CHANGED_PATHS.txt"; PREWRITE="$ROOT/V1_26600_PREWRITE_SOURCE_HASHES.sha256"; EXPECTED_CHANGED="$ROOT/V1_26600_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/V1_26600_RUNTIME_DELTA_FROM_26599.patch"; ROLLBACK="$ROOT/V1_26600_RUNTIME_ROLLBACK_TO_26599.patch"; SHADER_PIN="$ROOT/V1_26600_RUNTIME_EXPANDED_SHADERS.sha256"
TRANSFORM="$ROOT/transform_26600_v1.py"; VALIDATE="$ROOT/validate_26600_v1.py"; AUTHORITY="$ROOT/verify_26600_v1_authority.py"; INFRA="$ROOT/verify_26600_v1_infrastructure.py"; PATCHVERIFY="$ROOT/verify_26600_v1_patches.py"; SHADERVERIFY="$ROOT/verify_26600_v1_shaders.py"; GATEVERIFY="$ROOT/verify_26600_v1_regressions.py"
BUILD_SCRIPT="$ROOT/build_26600_v1_boundary_consensus_short_geometry.sh"; WORKFLOW="$ROOT/.github/workflows/build-26600-v1-boundary-consensus-short-geometry.yml"
OUT="$ROOT/build_26600_v1_boundary_consensus_short_geometry_outputs"; WORK="$ROOT/.build_26600_v1_boundary_consensus_short_geometry_work"; ARTZIP="$WORK/26599_v1_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_26599_v1_compiled_candidate"; AFTER="$WORK/candidate_26600"; AFTER2="$WORK/candidate_26600_replay"; SHADER_OUT="$WORK/runtime_expanded_shaders"; GLSLANG_DIR="$WORK/glslang-16.5.0"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-boundary-consensus-short-geometry-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""; if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26599 V1 artifact ZIP"; LOCAL_ART="$2"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26600_V1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26600_V1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME AUTHORITY: NOT RUN
VERIFICATION MECHANICS AUTHORITY: NOT RUN
BACKUP STATUS: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE DELTA AUDIT: NOT RUN
NEW RUNTIME AUTHORITY: NOT RUN
SUPERSEDED / NEUTRALIZED AUTHORITY: NOT RUN
UPSTREAM SEMANTIC COMPATIBILITY: NOT RUN
DOWNSTREAM DUPLICATE-AUTHORITY CHECK: NOT RUN
FEEDBACK-LOOP CHECK: NOT RUN
STALE-BEHAVIOR ABSENCE CHECK: NOT RUN
BOUNDARY CONSENSUS SHORT GEOMETRY REGRESSION: NOT RUN
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
TARGET VERSION/BUILD: 0.9726600 / 26600
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26600_V1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26600_V1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26600_V1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26600_V1_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){ local authority_root="$1" live_root="$2" dest_root="$3"; rm -rf "$dest_root"; mkdir -p "$dest_root"; cp -a "$authority_root/." "$dest_root/"; rm -rf "$dest_root/app/src"; cp -a "$live_root/app/src" "$dest_root/app/"; cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"; cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"; }
verify_package(){
  [[ -f "$HANDOFF" ]] || fail "handoff hash manifest missing"; sha256sum -c "$HANDOFF"; [[ "$(wc -l < "$HANDOFF")" -eq "$SEALED_PAYLOAD_COUNT" ]] || fail "sealed payload count"
  [[ "$(wc -l < "$CHANGED")" -eq 3 ]] || fail "runtime allowlist must be 3"; [[ "$(wc -l < "$BASE_FULL")" -eq 1708 && "$(wc -l < "$CAND_FULL")" -eq 1708 ]] || fail "full app count"; [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1705 ]] || fail "protected count"; [[ "$(wc -l < "$BASE_NATIVE")" -eq 802 ]] || fail "native count"; [[ "$(wc -l < "$BASE_VENDOR")" -eq 778 ]] || fail "vendor count"; [[ "$(wc -l < "$BASE_DNG")" -eq 7 ]] || fail "DNG count"
  [[ "$(sha "$BASE_FULL")" == "75702a703cbfbcbfd86a1d1540f9314e54471064e97dbf8f06f5c7919176dff2" ]] || fail "base manifest SHA"; [[ "$(sha "$CAND_FULL")" == "7fbd78551792035d39063a15e7727610605abbd64c8a1c970de6402cb55176c3" ]] || fail "candidate manifest SHA"; [[ "$(sha "$BASE_PROTECTED")" == "2ea0810b27e53ff5430d27e741ae532d9d888e31acc9a8749b26ec9ac400dbe2" ]] || fail "protected manifest SHA"; cmp "$BASE_PROTECTED" "$CAND_PROTECTED" || fail "protected invariance"; [[ "$(sha "$BASE_NATIVE")" == "7a1a107b63493937aac11297743876ca1544bc5e5b92d73fd8b06404cb25660e" ]] || fail "native manifest SHA"; cmp "$BASE_NATIVE" "$CAND_NATIVE" || fail "native invariance"; [[ "$(sha "$BASE_VENDOR")" == "7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8" ]] || fail "vendor manifest SHA"; cmp "$BASE_VENDOR" "$CAND_VENDOR" || fail "vendor invariance"; [[ "$(sha "$BASE_DNG")" == "90192bdf78607cc64415343d93aae54bbf17903d5442cab0674b6768faed7eab" ]] || fail "DNG manifest SHA"; cmp "$BASE_DNG" "$CAND_DNG" || fail "DNG invariance"; [[ "$(sha "$PREWRITE")" == "b09f433561b358dce041366a4ee249afb3622de16c2e06c15b16224b04b1933e" ]] || fail "prewrite SHA"; [[ "$(sha "$EXPECTED_CHANGED")" == "c87fad274c1a78eccde3e905b6cf7ead7780d47fcc6c5fbe775790cee07cd8dd" ]] || fail "expected changed SHA"; [[ "$(sha "$FORWARD")" == "52c7a55f1b2b883b5fbfa6ff3dc3fb3fbc5f6e07f9f505423cd7d79e201b5d64" ]] || fail "forward SHA"; [[ "$(sha "$ROLLBACK")" == "4ef2b0640e1a589c845168b5277f201f0f535bb2589aa5664cd71bad88324457" ]] || fail "rollback SHA"; [[ "$(sha "$SHADER_PIN")" == "c69f6f55cab8d72df54b37e34366301b26b099f59dae8cbf38c72a2e2ae9f0c5" ]] || fail "shader manifest SHA"
  ! awk '{print $2}' "$HANDOFF" | grep -Eq '(^|/)(\.build_|build_.*_outputs|__pycache__)(/|$)|(^|/)app/(build|\.cxx)/|\.pyc$|\.apk$' || fail "transient/generated path sealed in handoff manifest"
  bash -n "$BUILD_SCRIPT"; python3 -S - "$TRANSFORM" "$VALIDATE" "$AUTHORITY" "$INFRA" "$PATCHVERIFY" "$SHADERVERIFY" "$GATEVERIFY" <<'PY'
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
  python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26600_infrastructure_local.txt"; set_report "INFRASTRUCTURE DELTA AUDIT" "PASS (identity/scope/semantic validators only; exact successful-26599 compiler/build mechanics order preserved)"; pass "sealed package syntax/hash/regression contract"
}
verify_scope(){
  if [[ -n "$LOCAL_ART" ]]; then set_report "BACKUP STATUS" "PASS (user explicitly requested no new backup; deterministic rollback packaged)"; set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed handoff; exact three-file allowlist validated after transform)"; return; fi
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"; [[ "$(git rev-parse HEAD^)" == "$HANDOFF_PARENT_COMMIT" ]] || fail "26600 must be one clean handoff commit directly on successful 26599 V1"
  python3 -S - "$HANDOFF" > "$WORK/expected_scope.txt" <<'PY'
from pathlib import Path
import sys
names=[line.split('  ',1)[1] for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]
names.append('V1_26600_HANDOFF_HASHES.sha256')
print('\n'.join(sorted(names)))
PY
  git diff --name-only "$HANDOFF_PARENT_COMMIT"..HEAD | sort > "$WORK/actual_scope.txt"; diff -u "$WORK/expected_scope.txt" "$WORK/actual_scope.txt" || fail "handoff commit scope mismatch"; ! grep -Eq '^app/' "$WORK/actual_scope.txt" || fail "handoff commit contains live app source"; set_report "BACKUP STATUS" "PASS (user explicitly requested no new backup; deterministic rollback packaged)"; set_report "CHANGED RUNTIME SCOPE" "PASS (sealed infrastructure/payload only; runtime written only in Actions)"
}
obtain_authority(){
  if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
  [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26599 artifact ZIP SHA"; unzip -q "$ARTZIP" -d "$ARTDIR"; local tarball="$ARTDIR/build_26599_v1_effective_short_shared_hdr_tone_outputs/26599_V1_candidate_app_source.tar.gz"; [[ -f "$tarball" ]] || fail "compiled 26599 candidate tar missing"; [[ "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "compiled 26599 candidate tar SHA"; tar -xzf "$tarball" -C "$BASE"; find "$ARTDIR" -type f -name '*.apk' -delete; (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null && sha256sum -c "$BASE_PROTECTED" >/dev/null && sha256sum -c "$BASE_NATIVE" >/dev/null && sha256sum -c "$BASE_VENDOR" >/dev/null && sha256sum -c "$BASE_DNG" >/dev/null && sha256sum -c "$PREWRITE" >/dev/null); set_report "RUNTIME AUTHORITY" "PASS (successful 26599 V1 commit/run/job/artifact exact compiled candidate)"; pass "exact successful 26599 compiled-candidate authority"
}
make_candidate(){
  rm -rf "$AFTER" "$AFTER2"; python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26600_transform.txt"; python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26600_transform_replay.txt"; python3 -S - "$AFTER" "$AFTER2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2]);assert a==b, 'candidate transform replay mismatch';print(f'PASS deterministic candidate reconstruction files={len(a)}')
PY
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; cmp "$ROOT/handoff_payload_26600_v1/$rel" "$AFTER/$rel" || fail "sealed payload differs frozen candidate $rel"; done < "$CHANGED"; python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26600_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$AFTER" | tee "$OUT/26600_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26600_authority_candidate.txt"; set_report "NEW RUNTIME AUTHORITY" "PASS (boundary-consensus SHORT geometry + successful-26599 effective-loss/tone/capture retained)"; set_report "SUPERSEDED / NEUTRALIZED AUTHORITY" "PASS (poisoned active flow.w max-range veto retired; 26599 effective-loss/tone owners retained)"; set_report "UPSTREAM SEMANTIC COMPATIBILITY" "PASS (successful-26599 HAL AE/capture/tone/color/sceneWhite/SR producers inherited byte-identical)"; set_report "DOWNSTREAM DUPLICATE-AUTHORITY CHECK" "PASS (SHORT geometry only; true2x detail/presentation and DNG owners unchanged)"; set_report "FEEDBACK-LOOP CHECK" "PASS (no exposure/tone/capture feedback added; geometry field is SHORT-only and GPU-local)"; set_report "STALE-BEHAVIOR ABSENCE CHECK" "PASS (active max-range flow veto absent; old fixed-radius region owner not linked; fail-closed conflict remains)"; set_report "BOUNDARY CONSENSUS SHORT GEOMETRY REGRESSION" "PASS"; set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (1708 full / 1705 protected / 802 native / 778 vendor / 7 DNG)"; set_report "PROTECTED/DNG/NATIVE/VENDOR INVARIANCE" "PASS";
}
verify_candidate_patches(){ python3 -S "$PATCHVERIFY" "$BASE" "$AFTER" "$FORWARD" "$ROLLBACK" | tee "$OUT/26600_patch_validation.txt"; set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"; }
verify_shaders(){
  rm -rf "$SHADER_OUT"; mkdir -p "$SHADER_OUT"
  if [[ -n "$LOCAL_ART" ]]; then python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" | tee "$OUT/26600_shader_validation.txt"; cmp "$SHADER_OUT/V1_26600_RUNTIME_EXPANDED_SHADERS.sha256" "$SHADER_PIN" || fail "local shader pin mismatch"; cp "$SHADER_OUT/V1_26600_SHADER_VERIFICATION.json" "$OUT/26600_shader_verification.json"; set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (19 exact variants)"; set_report "REAL GLSL COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL GLSL COMPILE" "NOT RUN locally (Actions required)"; return; fi
  mkdir -p "$GLSLANG_DIR"; local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"; [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive SHA"; tar -tzf "$archive" > "$OUT/26600_glslang_archive_contents.txt"; tar -xzf "$archive" -C "$GLSLANG_DIR"; local compiler; compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "glslang missing"; chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26600_glslang_version.txt"; python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" --glslang "$compiler" | tee "$OUT/26600_shader_validation.txt"; cmp "$SHADER_OUT/V1_26600_RUNTIME_EXPANDED_SHADERS.sha256" "$SHADER_PIN" || fail "Actions shader pin mismatch"; cp "$SHADER_OUT/V1_26600_SHADER_VERIFICATION.json" "$OUT/26600_shader_verification.json"; set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (19 exact variants)"; set_report "REAL GLSL COMPILE" "PASS (pinned Khronos glslangValidator 16.5.0)"; set_compiler "REAL GLSL COMPILE" "PASS (pinned Khronos glslangValidator 16.5.0)"
}
install_and_build(){
  [[ -z "$LOCAL_ART" ]] || return 0
  local success26599Script="$WORK/successful_26599_build.sh" success26599Workflow="$WORK/successful_26599_workflow.yml" golden26593Script="$WORK/successful_26593_build.sh" golden26593Workflow="$WORK/successful_26593_workflow.yml"
  curl -L --fail --retry 3 "https://raw.githubusercontent.com/SkyKing0007/Photon-Camera/$BASE_SUCCESS_COMMIT/build_26599_v1_effective_short_shared_hdr_tone.sh" -o "$success26599Script"; curl -L --fail --retry 3 "https://raw.githubusercontent.com/SkyKing0007/Photon-Camera/$BASE_SUCCESS_COMMIT/.github/workflows/build-26599-v1-effective-short-shared-hdr-tone.yml" -o "$success26599Workflow"
  curl -L --fail --retry 3 "https://raw.githubusercontent.com/SkyKing0007/Photon-Camera/$MECHANICS_GOLDEN_COMMIT/build_26593_v1_total_frame_hdr_ownership.sh" -o "$golden26593Script"; curl -L --fail --retry 3 "https://raw.githubusercontent.com/SkyKing0007/Photon-Camera/$MECHANICS_GOLDEN_COMMIT/.github/workflows/build-26593-v1-total-frame-hdr-ownership.yml" -o "$golden26593Workflow"
  python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" --success-26599-script "$success26599Script" --success-26599-workflow "$success26599Workflow" --golden-26593-script "$golden26593Script" --golden-26593-workflow "$golden26593Workflow" | tee "$OUT/26600_infrastructure_actions.txt"; set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (exact successful-26599 implementation + successful-26593 compiler/build order)"
  rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"; snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"; python3 -S "$VALIDATE" "$BASE" "$LIVE_CANON" | tee "$OUT/26600_live_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$LIVE_CANON" | tee "$OUT/26600_live_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$LIVE_CANON" | tee "$OUT/26600_live_authority.txt"; python3 -S - "$AFTER" "$LIVE_CANON" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2]);assert a==b,'live compiler candidate differs frozen candidate';print(f'PASS authority-seeded live compiler candidate byte-identical files={len(a)}')
PY
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26600_gradle_language_compilers.log"; set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26600_gradle_native_compiler.log"; set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
  verify_candidate_patches; set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26600 PRE-BUILD SAFETY PROOF PASSED"
  ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26600_gradle_assemble.log"; set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
  mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort); [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK"; mv "${apks[0]}" "$FINAL"; mapfile -t roots < <(find "$ROOT" -maxdepth 1 -type f -name '*.apk' | sort); [[ "${#roots[@]}" -eq 1 && "${roots[0]}" == "$FINAL" ]] || fail "exactly one final root APK"; sha256sum "$FINAL" > "$OUT/26600_V1_APK.sha256"; set_report "EXACTLY ONE APK" "PASS"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"; python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26600_postbuild_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$POST" | tee "$OUT/26600_postbuild_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26600_postbuild_authority.txt"; python3 -S - "$AFTER" "$POST" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2]);assert a==b,'postbuild candidate differs frozen candidate';print(f'PASS authority-seeded postbuild candidate byte-identical files={len(a)}')
PY
  set_report "POST-BUILD INVARIANCE" "PASS (candidate/protected/DNG/native/vendor exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"; tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26600_V1_candidate_app_source.tar.gz"; sha256sum "$OUT/26600_V1_candidate_app_source.tar.gz" > "$OUT/26600_V1_candidate_app_source.tar.gz.sha256"; cp "$CAND_FULL" "$OUT/26600_V1_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26600_V1_native_protected_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26600_V1_vendor_protected_postbuild.sha256"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests)"
}
verify_package
verify_scope
obtain_authority
make_candidate
verify_shaders
if [[ -n "$LOCAL_ART" ]]; then verify_candidate_patches; set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (successful-26599 implementation + successful-26593 order/pins packaged; exact prior source replay requires Actions)"; set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real pinned GLSL + Kotlin/Java/NDK/full Android gates require Actions)"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN (local prebuild stops before Android build)"; cp "$OUT/26600_V1_STRICT_HANDOFF_REPORT.txt" "$OUT/26600_local_prebuild_report.txt"; pass "26600 V1 LOCAL PREBUILD PREPARED: exact successful-26599 authority/boundary-geometry/patch/static-shader gates passed; real GLSL/Kotlin/Java/NDK/full Android gates explicitly unproven locally"; exit 0; fi
install_and_build
pass "26600 REAL GLSL + KOTLIN/JAVA + NDK + FULL ASSEMBLE PASSED"
pass "26600 POST-BUILD INVARIANCE PASSED"
