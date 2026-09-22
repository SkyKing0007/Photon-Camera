#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
resolve_glslang_compiler(){ local root="$1" compiler="" compat=""; compiler="$(find "$root" -type f -name glslang -print -quit)"; if [[ -z "$compiler" ]]; then compat="$(find "$root" \( -type f -o -type l \) -name glslangValidator -print -quit)"; if [[ -n "$compat" ]]; then compiler="$(readlink -f "$compat" 2>/dev/null || true)"; fi; fi; [[ -n "$compiler" && -f "$compiler" ]] || return 1; printf '%s\n' "$compiler"; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
UPLOAD_BASE_COMMIT="807d51185046298761edba21e1a8311bec8bd59a"
RUNTIME_AUTHORITY_COMMIT="807d51185046298761edba21e1a8311bec8bd59a"
BASE_RUN_ID="35674780414"
BASE_ARTIFACT_ID="10672782633"
BASE_ARTIFACT_NAME="photon-26682-r1-spektra-mode-ownership"
BASE_ARTIFACT_SHA="9db1c727c144dd3e87ac9c871fc7ae224a9517e925ff352d6a978d3431e78bc1"
BASE_TAR_SHA="42e88f2b259d1e19f78522a4db1fae973b9354d59e1f966e3c4b9e7577e07614"
VERSION_NAME="0.9726683"; VERSION_BUILD="26683"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
MECHANICS_AUTHORITY_COMMIT="807d51185046298761edba21e1a8311bec8bd59a"
AUTH_26682_BUILD_SCRIPT_BLOB="2d92d9fc1122a2ef9c8d1b1223101fe08c780083"
AUTH_26682_WORKFLOW_BLOB="9cbf2a3b4622041672ffd7f0387677e56345766d"
HANDOFF="$ROOT/R1_26683_HANDOFF_HASHES.sha256"; UPLOADS="$ROOT/R1_26683_UPLOAD_PATHS.txt"
BASE_FULL="$ROOT/R1_26683_BASE_26682_R1_1_FULL_APP.sha256"; CAND_FULL="$ROOT/R1_26683_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/R1_26683_PROTECTED_UNCHANGED_BASE.sha256"; CAND_PROTECTED="$ROOT/R1_26683_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/R1_26683_NATIVE_PROTECTED_BASE.sha256"; CAND_NATIVE="$ROOT/R1_26683_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/R1_26683_VENDOR_PROTECTED_BASE.sha256"; CAND_VENDOR="$ROOT/R1_26683_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/R1_26683_DNG_BASE.sha256"; CAND_DNG="$ROOT/R1_26683_DNG_CANDIDATE.sha256"
SHADER_BASE="$ROOT/R1_26683_SHADER_UNIVERSE_BASE.sha256"; SHADER_CAND="$ROOT/R1_26683_SHADER_UNIVERSE_CANDIDATE.sha256"
CHANGED="$ROOT/R1_26683_RUNTIME_CHANGED_PATHS.txt"; PREWRITE="$ROOT/R1_26683_PREWRITE_SOURCE_HASHES.sha256"; EXPECTED_CHANGED="$ROOT/R1_26683_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/R1_26683_RUNTIME_DELTA_FROM_26682_R1_1.patch"; ROLLBACK="$ROOT/R1_26683_RUNTIME_ROLLBACK_TO_26682_R1_1.patch"
TRANSFORM="$ROOT/transform_26683.py"; VALIDATE="$ROOT/validate_26683.py"; AUTHORITY="$ROOT/verify_26683_authority.py"; INFRA="$ROOT/verify_26683_infrastructure.py"; PATCHVERIFY="$ROOT/verify_26683_patches.py"; GATEVERIFY="$ROOT/verify_26683_regressions.py"
BUILD_SCRIPT="$ROOT/build_26683_r1_spektra_end_to_end_owner.sh"; WORKFLOW="$ROOT/.github/workflows/build-26683-r1-spektra-end-to-end-owner.yml"
OUT="$ROOT/build_26683_r1_spektra_end_to_end_owner_outputs"; WORK="$ROOT/.build_26683_r1_spektra_end_to_end_owner_work"
ARTZIP="$WORK/26682_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_successful_26682_compiled_candidate"; AFTER="$WORK/candidate_26683"; AFTER2="$WORK/candidate_26683_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; GLSLANG_DIR="$WORK/glslang-${GLSLANG_VERSION}"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r1-spektra-end-to-end-owner-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26682 artifact ZIP"; LOCAL_ART="$2"; elif [[ -n "${1:-}" ]]; then fail "unknown argument: $1"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26683_R1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26683_R1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME AUTHORITY: NOT RUN
VERIFICATION MECHANICS AUTHORITY: NOT RUN
BACKUP STATUS: NONE (user requested no backup; exact hashes + deterministic rollback patch)
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE CHANGED FILES: 26683 handoff/build/validator wrapper files only; app build infrastructure unchanged
INFRASTRUCTURE DELTA FROM LAST SUCCESS: build ordering unchanged; authority/version/scope and 26683 regressions updated
SPEKTRA MODE/CAMERA OWNER AUTHORITY: NOT RUN
SPEKTRA PHYSICAL/LOGICAL ROUTE: NOT RUN
SPEKTRA SHUTTER ROUTE: NOT RUN
SPEKTRA FIRST-FRAME PRESENTATION: NOT RUN
SPEKTRA WATCHDOG/RAW CONTRACT: NOT RUN
STRICT CROSS-MODE OWNER RETIREMENT: NOT RUN
SPEKTRA PREVIEW DRAIN: NOT RUN
26681/26682 FAILURE REGRESSIONS: NOT RUN
SHADER UNIVERSE INVARIANCE: NOT RUN
PROTECTED/DNG/NATIVE/VENDOR INVARIANCE: NOT RUN
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
TARGET VERSION/BUILD: 0.9726683 / 26683
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26683_R1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26683_R1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26683_R1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26683_R1_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){ local authority_root="$1" live_root="$2" dest_root="$3"; rm -rf "$dest_root"; mkdir -p "$dest_root"; cp -a "$authority_root/." "$dest_root/"; rm -rf "$dest_root/app/src"; cp -a "$live_root/app/src" "$dest_root/app/"; cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"; cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"; }
compare_app_trees(){ python3 -S - "$1" "$2" <<'PY2'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a=H(sys.argv[1]);b=H(sys.argv[2]);assert len(a)==len(b)==1764 and a==b,(len(a),len(b),sorted(set(a)^set(b))[:10]);print('PASS authority-seeded candidate byte-identical: 1764 files')
PY2
}
verify_package(){
 [[ -f "$HANDOFF" && -f "$UPLOADS" && -d "$ROOT/handoff_payload_26683" ]] || fail "sealed 26683 package incomplete"
 [[ "$(find "$ROOT/handoff_payload_26683" -type f | wc -l)" -eq 6 ]] || fail "runtime payload must contain exactly 6 files"
 [[ "$(wc -l < "$CHANGED")" -eq 6 ]] || fail "26683 changed-file count"
 sha256sum -c "$HANDOFF" >/dev/null
 [[ "$(wc -l < "$BASE_FULL")" -eq 1764 && "$(wc -l < "$CAND_FULL")" -eq 1764 ]] || fail "full app count"
 [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1758 && "$(wc -l < "$BASE_NATIVE")" -eq 804 && "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$BASE_DNG")" -eq 7 ]] || fail "protected manifest counts"
 [[ "$(wc -l < "$SHADER_BASE")" -eq 271 && "$(wc -l < "$SHADER_CAND")" -eq 271 ]] || fail "shader manifest counts"
 cmp "$BASE_NATIVE" "$CAND_NATIVE"; cmp "$BASE_VENDOR" "$CAND_VENDOR"; cmp "$BASE_DNG" "$CAND_DNG"; cmp "$SHADER_BASE" "$SHADER_CAND"
 bash -n "$BUILD_SCRIPT"
 python3 -S - "$TRANSFORM" "$VALIDATE" "$AUTHORITY" "$INFRA" "$PATCHVERIFY" "$GATEVERIFY" <<'PY2'
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
PY2
}
verify_scope(){
 if [[ -n "$LOCAL_ART" ]]; then set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed candidate: exact 6 modified / 0 added / 0 deleted from successful 26682 compiled authority)"; return; fi
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
 git merge-base --is-ancestor "$UPLOAD_BASE_COMMIT" HEAD || fail "successful 26682 R1 commit must remain ancestor; split handoff commits are allowed"
 [[ "$(git rev-parse "${MECHANICS_AUTHORITY_COMMIT}:build_26682_r1_spektra_mode_ownership.sh")" == "$AUTH_26682_BUILD_SCRIPT_BLOB" ]] || fail "successful 26682 build-script blob changed"
 [[ "$(git rev-parse "${MECHANICS_AUTHORITY_COMMIT}:.github/workflows/build-26682-r1-spektra-mode-ownership.yml")" == "$AUTH_26682_WORKFLOW_BLOB" ]] || fail "successful 26682 workflow blob changed"
 git diff --name-only "$UPLOAD_BASE_COMMIT"..HEAD | sort > "$WORK/actual_upload_scope.txt"; sort "$UPLOADS" > "$WORK/expected_upload_scope.txt"; diff -u "$WORK/expected_upload_scope.txt" "$WORK/actual_upload_scope.txt" || fail "26683 upload scope mismatch"
 ! grep -Eq '^app/' "$WORK/actual_upload_scope.txt" || fail "handoff commit contains live app source"
 set_report "CHANGED RUNTIME SCOPE" "PASS (6 runtime modifications carried only inside sealed payload; live app source not committed)"
}
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
 [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "successful 26682 artifact ZIP SHA"
 unzip -q "$ARTZIP" -d "$ARTDIR"; local tarball="$ARTDIR/build_26682_r1_spektra_mode_ownership_outputs/26682_R1_candidate_app_source.tar.gz"
 [[ -f "$tarball" && "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "successful 26682 compiled candidate TAR authority"
 tar -xzf "$tarball" -C "$BASE"; (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null) || fail "exact successful 26682 base manifest"
 set_report "RUNTIME AUTHORITY" "PASS (successful 26682 R1 commit ${RUNTIME_AUTHORITY_COMMIT}/run ${BASE_RUN_ID}/artifact ${BASE_ARTIFACT_ID}/artifact SHA ${BASE_ARTIFACT_SHA}/compiled candidate TAR ${BASE_TAR_SHA})"
}
make_candidate(){
 python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26683_transform.txt"; python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26683_transform_replay.txt"; compare_app_trees "$AFTER" "$AFTER2"
 python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26683_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$AFTER" | tee "$OUT/26683_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26683_authority_candidate.txt"
 set_report "SPEKTRA MODE/CAMERA OWNER AUTHORITY" "PASS (persisted/cache/fragment mirrors synchronized before restart; legacy owner retired before destination commit)"
 set_report "SPEKTRA PHYSICAL/LOGICAL ROUTE" "PASS (direct logical/direct physical + logical-parent physical-output discovery; unrelated camera fallback removed)"
 set_report "SPEKTRA SHUTTER ROUTE" "PASS (Spektra shutter admitted only while dedicated owner STREAMING; no legacy/Motion fallthrough)"
 set_report "SPEKTRA FIRST-FRAME PRESENTATION" "PASS (legacy preview remains visible until a validated Spektra RAW frame is rendered and posted)"
 set_report "SPEKTRA WATCHDOG/RAW CONTRACT" "PASS (bounded open/preview/still/restore states + strict RAW plane geometry validation)"
 set_report "STRICT CROSS-MODE OWNER RETIREMENT" "PASS (departing owner retired before destination preference/open; legacy CameraBackground joined; Spektra generation retired)"
 set_report "SPEKTRA PREVIEW DRAIN" "PASS (active preview render shares retirement lock; no Spektra render survives handoff return)"
 set_report "26681/26682 FAILURE REGRESSIONS" "PASS (binary resource, provenance, GLSL collision/validator, Java compiler, native-glslang setup, and mode-owner split guarded)"
 set_report "PROTECTED/DNG/NATIVE/VENDOR INVARIANCE" "PASS"
}
verify_shader_invariance(){
 cmp "$SHADER_BASE" "$SHADER_CAND" || fail "shader universe changed"
 local prior_runtime="$WORK/authority_26682_runtime_expanded_shaders.sha256" prior_upstream="$WORK/authority_26682_upstream_spektra_shader_blobs.txt"
 if [[ -n "$LOCAL_ART" ]]; then
  cp "$ROOT/R1_26683_INHERITED_SPEKTRA_RUNTIME_EXPANDED_SHADERS.sha256" "$prior_runtime"
  cp "$ROOT/R1_26683_INHERITED_SPEKTRA_UPSTREAM_SHADER_BLOBS.txt" "$prior_upstream"
 else
  git show "${RUNTIME_AUTHORITY_COMMIT}:R1_26682_INHERITED_SPEKTRA_RUNTIME_EXPANDED_SHADERS.sha256" > "$prior_runtime" || fail "successful 26682 runtime-expanded shader proof missing"
  git show "${RUNTIME_AUTHORITY_COMMIT}:R1_26682_INHERITED_SPEKTRA_UPSTREAM_SHADER_BLOBS.txt" > "$prior_upstream" || fail "successful 26682 upstream shader proof missing"
 fi
 cmp "$prior_runtime" "$ROOT/R1_26683_INHERITED_SPEKTRA_RUNTIME_EXPANDED_SHADERS.sha256" || fail "26682 runtime shader proof mismatch"
 cmp "$prior_upstream" "$ROOT/R1_26683_INHERITED_SPEKTRA_UPSTREAM_SHADER_BLOBS.txt" || fail "26682 upstream shader proof mismatch"
 set_report "SHADER UNIVERSE INVARIANCE" "PASS (271/271 source shaders byte-identical to successful 26682; exact 14 runtime-expanded + 10 upstream proof pins inherited)"
 set_report "REAL GLSL COMPILE" "PASS inherited from successful 26682 (all shader bytes identical; no modified GLSL)"; set_compiler "REAL GLSL COMPILE" "PASS inherited from successful 26682 (all shader bytes identical; no modified GLSL)"
}
prepare_inherited_glslang_for_native(){
 local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz" compiler
 curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"
 [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive SHA"
 rm -rf "$GLSLANG_DIR"; mkdir -p "$GLSLANG_DIR"
 tar -xzf "$archive" -C "$GLSLANG_DIR"
 compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "pinned glslang compiler missing"
 "$compiler" --version | tee "$OUT/26683_glslang_version.txt"
 export IRIS26681_SPEKTRA_GLSLANG="$compiler"
 [[ -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "IRIS26681_SPEKTRA_GLSLANG is not executable"
 pass "26683 inherited native Spektra glslang contract prepared: ${IRIS26681_SPEKTRA_GLSLANG}"
}
verify_successful_26682_mechanics(){ python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26683_infrastructure.txt"; set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (successful 26682 R1 build-script ${AUTH_26682_BUILD_SCRIPT_BLOB} + workflow ${AUTH_26682_WORKFLOW_BLOB}; same compiler/build order)"; }
verify_candidate_patches(){ python3 -S "$PATCHVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26683_patch_validation.txt"; set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"; }
install_frozen_candidate_live(){ rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"; snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"; compare_app_trees "$AFTER" "$LIVE_CANON"; }
postbuild_proof(){
 snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"; compare_app_trees "$AFTER" "$POST"; (cd "$POST" && sha256sum -c "$CAND_PROTECTED" >/dev/null && sha256sum -c "$CAND_NATIVE" >/dev/null && sha256sum -c "$CAND_VENDOR" >/dev/null && sha256sum -c "$CAND_DNG" >/dev/null && sha256sum -c "$SHADER_CAND" >/dev/null) || fail "post-build invariance"; python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26683_postbuild_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$POST" | tee "$OUT/26683_postbuild_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26683_postbuild_authority.txt"; set_report "POST-BUILD INVARIANCE" "PASS (candidate/protected/DNG/native/vendor/shaders exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"
 tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26683_R1_candidate_app_source.tar.gz"; sha256sum "$OUT/26683_R1_candidate_app_source.tar.gz" > "$OUT/26683_R1_candidate_app_source.tar.gz.sha256"; cp "$CAND_FULL" "$OUT/26683_R1_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26683_R1_native_protected_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26683_R1_vendor_protected_postbuild.sha256"; cp "$CAND_DNG" "$OUT/26683_R1_dng_postbuild.sha256"; cp "$SHADER_CAND" "$OUT/26683_R1_shader_universe_postbuild.sha256"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests)"
}
verify_package
verify_scope
obtain_authority
make_candidate
verify_shader_invariance
verify_successful_26682_mechanics
if [[ -n "$LOCAL_ART" ]]; then
 verify_candidate_patches
 set_report "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real Kotlin/Java/NDK/full Android require Actions)"; set_report "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_report "EXACTLY ONE APK" "NOT RUN locally (Actions required)"; set_report "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN locally (Actions required)"
 set_compiler "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_compiler "NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_compiler "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_compiler "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; cp "$OUT/26683_R1_STRICT_HANDOFF_REPORT.txt" "$OUT/26683_R1_local_prebuild_report.txt"; pass "26683 R1 LOCAL PREBUILD PREPARED: exact successful 26682 compiled authority; successful-26682 build ordering retained; all locally applicable packaged gates passed; real Android compiler/build gates explicitly unproven locally"; exit 0
fi
prepare_inherited_glslang_for_native
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26683_gradle_language_compilers.log"
set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"; compare_app_trees "$AFTER" "$WORK/after_language_compiler_snapshot"
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26683_gradle_native_compiler.log"
set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
verify_candidate_patches
set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26683 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26683_gradle_assemble.log"
set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort)
[[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK"
mv "${apks[0]}" "$FINAL"; [[ -f "$FINAL" ]] || fail "final APK missing after move"; set_report "EXACTLY ONE APK" "PASS"; sha256sum "$FINAL" > "$OUT/26683_R1_APK.sha256"
postbuild_proof
pass "26683 R1 ACTIONS BUILD COMPLETE"
