#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
resolve_glslang_compiler(){ local root="$1" compiler="" compat=""; compiler="$(find "$root" -type f -name glslang -print -quit)"; if [[ -z "$compiler" ]]; then compat="$(find "$root" \( -type f -o -type l \) -name glslangValidator -print -quit)"; if [[ -n "$compat" ]]; then compiler="$(readlink -f "$compat" 2>/dev/null || true)"; fi; fi; [[ -n "$compiler" && -f "$compiler" ]] || return 1; printf '%s\n' "$compiler"; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
UPLOAD_PARENT_COMMIT="5031e403553928e6e9411789a2ff7deab01390ed"
RUNTIME_AUTHORITY_COMMIT="5031e403553928e6e9411789a2ff7deab01390ed"
BASE_RUN_ID="35170004987"
BASE_ARTIFACT_ID="10476700363"
BASE_ARTIFACT_NAME="photon-26653-r1-final-highlight-tone-fine-structure"
BASE_ARTIFACT_SHA="2cd27a12ca2339fa4e1df02b661b6f7836487deb2d9576a353d18fec8f1e2bce"
BASE_TAR_SHA="aa2febedc278945e13055cadc7fde11c8637de3bfb8ea04e47908edbd70bf369"
VERSION_NAME="0.9726654"; VERSION_BUILD="26654"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
AUTH_26653_BUILD_SCRIPT_BLOB="7ae9e53a2cb57347cb03a546624125ac50b75917"
AUTH_26653_WORKFLOW_BLOB="ba5daffd6ed95622366538cf8f7d3231d1f0576d"
HANDOFF="$ROOT/R1_26654_HANDOFF_HASHES.sha256"; UPLOADS="$ROOT/R1_26654_UPLOAD_PATHS.txt"
BASE_FULL="$ROOT/R1_26654_BASE_26653_FULL_APP.sha256"; CAND_FULL="$ROOT/R1_26654_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/R1_26654_PROTECTED_UNCHANGED_BASE.sha256"; CAND_PROTECTED="$ROOT/R1_26654_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/R1_26654_NATIVE_PROTECTED_BASE.sha256"; CAND_NATIVE="$ROOT/R1_26654_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/R1_26654_VENDOR_PROTECTED_BASE.sha256"; CAND_VENDOR="$ROOT/R1_26654_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/R1_26654_DNG_BASE.sha256"; CAND_DNG="$ROOT/R1_26654_DNG_CANDIDATE.sha256"
SHADER_BASE="$ROOT/R1_26654_SHADER_UNIVERSE_BASE.sha256"; SHADER_CAND="$ROOT/R1_26654_SHADER_UNIVERSE_CANDIDATE.sha256"
CHANGED="$ROOT/R1_26654_RUNTIME_CHANGED_PATHS.txt"; PREWRITE="$ROOT/R1_26654_PREWRITE_SOURCE_HASHES.sha256"; ADDED="$ROOT/R1_26654_ADDED_PATHS_MUST_BE_ABSENT.txt"; EXPECTED_CHANGED="$ROOT/R1_26654_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/R1_26654_RUNTIME_DELTA_FROM_26653.patch"; ROLLBACK="$ROOT/R1_26654_RUNTIME_ROLLBACK_TO_26653.patch"; SHADER_PIN="$ROOT/R1_26654_RUNTIME_EXPANDED_SHADERS.sha256"
TRANSFORM="$ROOT/transform_26654.py"; VALIDATE="$ROOT/validate_26654.py"; AUTHORITY="$ROOT/verify_26654_authority.py"; INFRA="$ROOT/verify_26654_infrastructure.py"; PATCHVERIFY="$ROOT/verify_26654_patches.py"; SHADERVERIFY="$ROOT/verify_26654_shaders.py"; GATEVERIFY="$ROOT/verify_26654_regressions.py"
BUILD_SCRIPT="$ROOT/build_26654_r1_final_highlight_authority_cleanup.sh"; WORKFLOW="$ROOT/.github/workflows/build-26654-r1-final-highlight-authority-cleanup.yml"
OUT="$ROOT/build_26654_r1_final_highlight_authority_cleanup_outputs"; WORK="$ROOT/.build_26654_r1_final_highlight_authority_cleanup_work"
ARTZIP="$WORK/26653_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_successful_26653_compiled_candidate"; AFTER="$WORK/candidate_26654_r1"; AFTER2="$WORK/candidate_26654_r1_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; GLSLANG_DIR="$WORK/glslang-${GLSLANG_VERSION}"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r1-final-highlight-authority-cleanup-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26653 artifact ZIP"; LOCAL_ART="$2"; elif [[ -n "${1:-}" ]]; then fail "unknown argument: $1"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26654_R1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26654_R1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME AUTHORITY: NOT RUN
VERIFICATION MECHANICS AUTHORITY: NOT RUN
BACKUP STATUS: PASS (no backup created/requested)
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE DELTA AUDIT: NOT RUN
26653 FUSION / FINE-STRUCTURE PROTECTION: NOT RUN
LOCAL-LAPLACIAN STALE AUTHORITY REMOVED: NOT RUN
SINGLE FINAL HIGHLIGHT TONE AUTHORITY: NOT RUN
IRIS SCENE-WHITE TAIL AUTHORITY: NOT RUN
BRIGHTNESS MATCHER NON-COMPENSATION: NOT RUN
UHDR / LOCAL-DETAIL SHARED CONTRACT: NOT RUN
NIGHT/TEMPORAL/SR/DNG/UHDR/HEIC PROTECTION: NOT RUN
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
TARGET VERSION/BUILD: 0.9726654 / 26654
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26654_R1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26654_R1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26654_R1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26654_R1_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){ local authority_root="$1" live_root="$2" dest_root="$3"; rm -rf "$dest_root"; mkdir -p "$dest_root"; cp -a "$authority_root/." "$dest_root/"; rm -rf "$dest_root/app/src"; cp -a "$live_root/app/src" "$dest_root/app/"; cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"; cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"; }
compare_app_trees(){ python3 -S - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a=H(sys.argv[1]); b=H(sys.argv[2]); assert len(a)==1721 and a==b,(len(a),len(b),sorted(set(a)^set(b))[:10]); print('PASS authority-seeded candidate byte-identical: 1721 files')
PY
}
verify_package(){
 [[ -f "$HANDOFF" && -f "$UPLOADS" && -d "$ROOT/handoff_payload_26654" ]] || fail "sealed 26654 package incomplete"
 [[ "$(find "$ROOT/handoff_payload_26654" -type f | wc -l)" -eq 8 ]] || fail "sealed runtime payload must contain exactly 8 files"
 [[ "$(wc -l < "$CHANGED")" -eq 8 && ! -s "$ADDED" ]] || fail "26654 allowlist/addition count"
 sha256sum -c "$HANDOFF" >/dev/null
 [[ "$(wc -l < "$BASE_FULL")" -eq 1721 && "$(wc -l < "$CAND_FULL")" -eq 1721 ]] || fail "full app count"
 [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1713 && "$(wc -l < "$BASE_NATIVE")" -eq 807 && "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$BASE_DNG")" -eq 7 ]] || fail "protected manifest counts"
 [[ "$(wc -l < "$SHADER_BASE")" -eq 257 && "$(wc -l < "$SHADER_CAND")" -eq 257 && "$(wc -l < "$SHADER_PIN")" -eq 4 ]] || fail "shader manifest counts"
 cmp "$BASE_NATIVE" "$CAND_NATIVE"; cmp "$BASE_VENDOR" "$CAND_VENDOR"; cmp "$BASE_DNG" "$CAND_DNG"
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
}
verify_scope(){
 if [[ -n "$LOCAL_ART" ]]; then set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed 26654 candidate; exact 8 changed / 0 added from successful 26653 compiled authority)"; return; fi
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
 [[ "$(git rev-parse HEAD^)" == "$UPLOAD_PARENT_COMMIT" ]] || fail "26654 handoff parent must be exact successful 26653 commit ${UPLOAD_PARENT_COMMIT}"
 git diff --name-only "$UPLOAD_PARENT_COMMIT"..HEAD | sort > "$WORK/actual_upload_scope.txt"; sort "$UPLOADS" > "$WORK/expected_upload_scope.txt"; diff -u "$WORK/expected_upload_scope.txt" "$WORK/actual_upload_scope.txt" || fail "26654 upload scope mismatch"
 ! grep -Eq '^app/' "$WORK/actual_upload_scope.txt" || fail "handoff commit contains live app source"
 set_report "CHANGED RUNTIME SCOPE" "PASS (8 runtime paths / 0 additions, carried only inside sealed handoff payload; live app source not committed)"
}
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
 [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "successful 26653 artifact ZIP SHA"
 unzip -q "$ARTZIP" -d "$ARTDIR"; local tarball="$ARTDIR/build_26653_r1_final_highlight_tone_fine_structure_outputs/26653_R1_candidate_app_source.tar.gz"
 [[ -f "$tarball" && "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "successful 26653 compiled candidate TAR authority"
 tar -xzf "$tarball" -C "$BASE"; (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null) || fail "exact successful 26653 base manifest"
 set_report "RUNTIME AUTHORITY" "PASS (successful 26653 commit ${RUNTIME_AUTHORITY_COMMIT}/run ${BASE_RUN_ID}/artifact ${BASE_ARTIFACT_ID}/compiled candidate TAR ${BASE_TAR_SHA})"
}
make_candidate(){
 python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26654_transform.txt"; python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26654_transform_replay.txt"; compare_app_trees "$AFTER" "$AFTER2"
 python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26654_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$AFTER" | tee "$OUT/26654_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26654_authority_candidate.txt"
 set_report "26653 FUSION / FINE-STRUCTURE PROTECTION" "PASS (successful 26653 NORMAL-master scalar fusion, trusted chroma and full-resolution SHORT fine-structure guard byte-identical)"
 set_report "LOCAL-LAPLACIAN STALE AUTHORITY REMOVED" "PASS (Local Laplacian has no HC toggle; HC-ON absolute upper-tone base is global and local contribution is bounded zero-DC source-structure detail only)"
 set_report "SINGLE FINAL HIGHLIGHT TONE AUTHORITY" "PASS (final extended-linear tone runs only after frozen brightness target; HC-ON absolute upper-tone base is single global 26654 map; exact inherited lower path through source 0.65)"
 set_report "IRIS SCENE-WHITE TAIL AUTHORITY" "PASS (Photon adaptive-white estimate telemetry-only; >1 tail consumes solved Iris adaptiveSceneWhite/baseSceneWhite ratio)"
 set_report "BRIGHTNESS MATCHER NON-COMPENSATION" "PASS (MotionV2ViewfinderExposureMatcher byte-identical to successful 26653 and remains on 26623/OFF mapping)"
 set_report "UHDR / LOCAL-DETAIL SHARED CONTRACT" "PASS (SDR render and UHDR gainmap share the same global tone plus bounded zero-DC source-structure residual contract; Local-Laplacian global seed shares exact global function)"
 set_report "NIGHT/TEMPORAL/SR/DNG/UHDR/HEIC PROTECTION" "PASS (NORMAL temporal/rejection + Night Long + DNG + SR preserved; HEIC encoders/DNG/capture protected; UHDR gainmap change limited to shared final SDR tone intent)"
 set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (1721 base / 1721 candidate / 1713 protected / 807 native / 778 vendor / 7 DNG / 257 standalone shaders / 8 changed / 0 added)"
 set_report "PROTECTED/DNG/NATIVE/VENDOR INVARIANCE" "PASS"
}
verify_shaders(){
 if [[ -n "$LOCAL_ART" ]]; then python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26654_shader_validation.txt"; set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (4 exact runtime GLSL variants (render/local-global/local-remap/gainmap); complete 257-file standalone universe pinned)"; set_report "REAL GLSL COMPILE" "NOT RUN locally (Actions required; pinned 16.5.0 gate packaged)"; set_compiler "REAL GLSL COMPILE" "NOT RUN locally (Actions required; pinned 16.5.0 gate packaged)"; return; fi
 local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz" compiler; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"; [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive SHA"; mkdir -p "$GLSLANG_DIR"; tar -xzf "$archive" -C "$GLSLANG_DIR"; compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "pinned glslang compiler missing"; "$compiler" --version | tee "$OUT/26654_glslang_version.txt"; python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" --compiler "$compiler" | tee "$OUT/26654_shader_validation.txt"; set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (4 exact runtime GLSL variants (render/local-global/local-remap/gainmap); complete 257-file standalone universe pinned)"; set_report "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; exact 4 runtime variants including all modified GLSL assets)"; set_compiler "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; exact 4 runtime variants including all modified GLSL assets)"
}
verify_successful_26653_mechanics(){ python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26654_infrastructure.txt"; set_report "INFRASTRUCTURE DELTA AUDIT" "PASS (functional build mechanics delta ZERO; 26654 identity/authority/8-path scope and required shader/semantic validator coverage only; exact successful 26653 compiler/native/patch/PRE-BUILD/assemble/postbuild sequence retained)"; set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (successful 26653 build-script ${AUTH_26653_BUILD_SCRIPT_BLOB} + workflow ${AUTH_26653_WORKFLOW_BLOB})"; }
verify_candidate_patches(){ python3 -S "$PATCHVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26654_patch_validation.txt"; set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"; }
install_frozen_candidate_live(){ rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"; snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"; compare_app_trees "$AFTER" "$LIVE_CANON"; }
postbuild_proof(){
 snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"; compare_app_trees "$AFTER" "$POST"; (cd "$POST" && sha256sum -c "$CAND_PROTECTED" >/dev/null && sha256sum -c "$CAND_NATIVE" >/dev/null && sha256sum -c "$CAND_VENDOR" >/dev/null && sha256sum -c "$CAND_DNG" >/dev/null) || fail "post-build protected invariance"; python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26654_postbuild_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$POST" | tee "$OUT/26654_postbuild_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26654_postbuild_authority.txt"; set_report "POST-BUILD INVARIANCE" "PASS (candidate/protected/DNG/native/vendor exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"
 tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26654_R1_candidate_app_source.tar.gz"; sha256sum "$OUT/26654_R1_candidate_app_source.tar.gz" > "$OUT/26654_R1_candidate_app_source.tar.gz.sha256"; cp "$CAND_FULL" "$OUT/26654_R1_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26654_R1_native_protected_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26654_R1_vendor_protected_postbuild.sha256"; cp "$CAND_DNG" "$OUT/26654_R1_dng_postbuild.sha256"; cp "$SHADER_PIN" "$OUT/26654_R1_runtime_expanded_shaders.sha256"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests + runtime-expanded shader pins)"
}
verify_package
verify_scope
obtain_authority
make_candidate
verify_shaders
verify_successful_26653_mechanics
if [[ -n "$LOCAL_ART" ]]; then
 verify_candidate_patches
 set_report "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real GLSL/Kotlin/Java/NDK/full Android require Actions)"; set_report "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_report "EXACTLY ONE APK" "NOT RUN locally (Actions required)"; set_report "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN locally (Actions required)"
 set_compiler "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_compiler "NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_compiler "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_compiler "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; cp "$OUT/26654_R1_STRICT_HANDOFF_REPORT.txt" "$OUT/26654_R1_local_prebuild_report.txt"; pass "26654 R1 LOCAL PREBUILD PREPARED: exact successful 26653 compiled authority; all locally applicable packaged gates passed; real compiler/build gates explicitly unproven locally"; exit 0
fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26654_gradle_language_compilers.log"
set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"; compare_app_trees "$AFTER" "$WORK/after_language_compiler_snapshot"
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26654_gradle_native_compiler.log"
set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
verify_candidate_patches
set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26654 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26654_gradle_assemble.log"
set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort)
[[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK"
mv "${apks[0]}" "$FINAL"; [[ -f "$FINAL" ]] || fail "final APK missing after move"; set_report "EXACTLY ONE APK" "PASS"; sha256sum "$FINAL" > "$OUT/26654_R1_APK.sha256"
postbuild_proof
pass "26654 R1 ACTIONS BUILD COMPLETE"
