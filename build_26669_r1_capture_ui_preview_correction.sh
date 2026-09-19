#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
resolve_glslang_compiler(){ local root="$1" compiler="" compat=""; compiler="$(find "$root" -type f -name glslang -print -quit)"; if [[ -z "$compiler" ]]; then compat="$(find "$root" \( -type f -o -type l \) -name glslangValidator -print -quit)"; if [[ -n "$compat" ]]; then compiler="$(readlink -f "$compat" 2>/dev/null || true)"; fi; fi; [[ -n "$compiler" && -f "$compiler" ]] || return 1; printf '%s\n' "$compiler"; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
UPLOAD_PARENT_COMMIT="cd1ff23a4935a0bd4a6c58926047ca74d617feea"
RUNTIME_AUTHORITY_COMMIT="cd1ff23a4935a0bd4a6c58926047ca74d617feea"
BASE_RUN_ID="35420831668"
BASE_ARTIFACT_ID="10577148078"
BASE_ARTIFACT_NAME="photon-26668-r1-motion-evidence-ui"
BASE_ARTIFACT_SHA="1138252581a3a5fd15aabe8d96f1b58e7491dc06d36b0c0475fe9f2c2e35c694"
BASE_TAR_SHA="39ce17755705031d35dc4f8a09383c8dd3461f6b63632f8602b4d042c6c4c86f"
VERSION_NAME="0.9726669"; VERSION_BUILD="26669"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
AUTH_26668_BUILD_SCRIPT_BLOB="9fa6b709cabd900fc7fef68cc01318460a8be45a"
AUTH_26668_WORKFLOW_BLOB="14c7736c06222c9a9b0fb10a45e4989972e669b0"
HANDOFF="$ROOT/R1_26669_HANDOFF_HASHES.sha256"; UPLOADS="$ROOT/R1_26669_UPLOAD_PATHS.txt"
BASE_FULL="$ROOT/R1_26669_BASE_26668_FULL_APP.sha256"; CAND_FULL="$ROOT/R1_26669_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/R1_26669_PROTECTED_UNCHANGED_BASE.sha256"; CAND_PROTECTED="$ROOT/R1_26669_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/R1_26669_NATIVE_PROTECTED_BASE.sha256"; CAND_NATIVE="$ROOT/R1_26669_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/R1_26669_VENDOR_PROTECTED_BASE.sha256"; CAND_VENDOR="$ROOT/R1_26669_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/R1_26669_DNG_BASE.sha256"; CAND_DNG="$ROOT/R1_26669_DNG_CANDIDATE.sha256"
SHADER_BASE="$ROOT/R1_26669_SHADER_UNIVERSE_BASE.sha256"; SHADER_CAND="$ROOT/R1_26669_SHADER_UNIVERSE_CANDIDATE.sha256"
CHANGED="$ROOT/R1_26669_RUNTIME_CHANGED_PATHS.txt"; PREWRITE="$ROOT/R1_26669_PREWRITE_SOURCE_HASHES.sha256"; ADDED="$ROOT/R1_26669_ADDED_PATHS_MUST_BE_ABSENT.txt"; EXPECTED_CHANGED="$ROOT/R1_26669_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/R1_26669_RUNTIME_DELTA_FROM_26668.patch"; ROLLBACK="$ROOT/R1_26669_RUNTIME_ROLLBACK_TO_26668.patch"; SHADER_PIN="$ROOT/R1_26669_RUNTIME_EXPANDED_SHADERS.sha256"
TRANSFORM="$ROOT/transform_26669.py"; VALIDATE="$ROOT/validate_26669.py"; AUTHORITY="$ROOT/verify_26669_authority.py"; INFRA="$ROOT/verify_26669_infrastructure.py"; PATCHVERIFY="$ROOT/verify_26669_patches.py"; SHADERVERIFY="$ROOT/verify_26669_shaders.py"; GATEVERIFY="$ROOT/verify_26669_regressions.py"
BUILD_SCRIPT="$ROOT/build_26669_r1_capture_ui_preview_correction.sh"; WORKFLOW="$ROOT/.github/workflows/build-26669-r1-capture-ui-preview-correction.yml"
OUT="$ROOT/build_26669_r1_capture_ui_preview_correction_outputs"; WORK="$ROOT/.build_26669_r1_capture_ui_preview_correction_work"
ARTZIP="$WORK/26668_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_successful_26668_compiled_candidate"; AFTER="$WORK/candidate_26669_r1"; AFTER2="$WORK/candidate_26669_r1_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; GLSLANG_DIR="$WORK/glslang-${GLSLANG_VERSION}"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r1-capture-ui-preview-correction-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26668 artifact ZIP"; LOCAL_ART="$2"; elif [[ -n "${1:-}" ]]; then fail "unknown argument: $1"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26669_R1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26669_R1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME AUTHORITY: NOT RUN
VERIFICATION MECHANICS AUTHORITY: NOT RUN
BACKUP STATUS: PASS (NONE, by request)
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE DELTA AUDIT: NOT RUN
STATELESS PREVIEW / HAL AE OWNER: NOT RUN
ISOLATED CAPTURE-TIME SHORT: NOT RUN
NORMAL DEFORMING-SUBJECT REJECTION: NOT RUN
LONG HARD ADMISSION/NORMAL CHROMA: NOT RUN
SPATIAL SUPPORT BODY RECOVERY: NOT RUN
EFFECTIVE-SUPPORT NON-AUTHORITY: NOT RUN
LIVE RGB HISTOGRAM: NOT RUN
SINGLE-OWNER EXACT-VALUE MANUAL SLIDERS: NOT RUN
V9 UI GEOMETRY / LEGACY LABEL NEUTRALIZATION: NOT RUN
HIGHLIGHT/X/UHDR PROTECTION: NOT RUN
NIGHT/DNG/SR PROTECTION: NOT RUN
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
TARGET VERSION/BUILD: 0.9726669 / 26669
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26669_R1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26669_R1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26669_R1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26669_R1_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){ local authority_root="$1" live_root="$2" dest_root="$3"; rm -rf "$dest_root"; mkdir -p "$dest_root"; cp -a "$authority_root/." "$dest_root/"; rm -rf "$dest_root/app/src"; cp -a "$live_root/app/src" "$dest_root/app/"; cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"; cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"; }
compare_app_trees(){ python3 -S - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a=H(sys.argv[1]);b=H(sys.argv[2]);assert len(a)==1725 and a==b,(len(a),len(b),sorted(set(a)^set(b))[:10]);print('PASS authority-seeded candidate byte-identical: 1725 files')
PY
}
verify_package(){
 [[ -f "$HANDOFF" && -f "$UPLOADS" && -d "$ROOT/handoff_payload_26669" ]] || fail "sealed 26669 package incomplete"
 [[ "$(find "$ROOT/handoff_payload_26669" -type f | wc -l)" -eq 6 ]] || fail "sealed runtime payload must contain exactly 6 files"
 [[ "$(wc -l < "$CHANGED")" -eq 6 && "$(wc -l < "$ADDED")" -eq 0 ]] || fail "26669 allowlist/no-addition count"
 sha256sum -c "$HANDOFF" >/dev/null
 [[ "$(wc -l < "$BASE_FULL")" -eq 1725 && "$(wc -l < "$CAND_FULL")" -eq 1725 ]] || fail "full app count"
 [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1719 && "$(wc -l < "$BASE_NATIVE")" -eq 807 && "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$BASE_DNG")" -eq 7 ]] || fail "protected manifest counts"
 [[ "$(wc -l < "$SHADER_BASE")" -eq 257 && "$(wc -l < "$SHADER_CAND")" -eq 257 && "$(wc -l < "$SHADER_PIN")" -eq 12 ]] || fail "shader manifest counts"
 cmp "$BASE_NATIVE" "$CAND_NATIVE"; cmp "$BASE_VENDOR" "$CAND_VENDOR"; cmp "$BASE_DNG" "$CAND_DNG"
 bash -n "$BUILD_SCRIPT"
 python3 -S - "$TRANSFORM" "$VALIDATE" "$AUTHORITY" "$INFRA" "$PATCHVERIFY" "$SHADERVERIFY" "$GATEVERIFY" <<'PY'
import ast,sys
from pathlib import Path
allowed=set(sys.stdlib_module_names)
for raw in sys.argv[1:]:
 p=Path(raw);src=p.read_text();tree=ast.parse(src,filename=str(p));bad=[]
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
 if [[ -n "$LOCAL_ART" ]]; then set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed 26669 candidate; exact 6 modified / 0 added from successful 26668 compiled authority)"; return; fi
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
 [[ "$(git rev-parse HEAD^)" == "$UPLOAD_PARENT_COMMIT" ]] || fail "26669 parent must be exact successful 26668 commit ${UPLOAD_PARENT_COMMIT}"
 [[ "$(git rev-parse "${RUNTIME_AUTHORITY_COMMIT}:build_26668_r1_motion_evidence_ui.sh")" == "$AUTH_26668_BUILD_SCRIPT_BLOB" ]] || fail "successful 26668 build-script blob changed"
 [[ "$(git rev-parse "${RUNTIME_AUTHORITY_COMMIT}:.github/workflows/build-26668-r1-motion-evidence-ui.yml")" == "$AUTH_26668_WORKFLOW_BLOB" ]] || fail "successful 26668 workflow blob changed"
 git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | sort > "$WORK/actual_upload_scope.txt"; sort "$UPLOADS" > "$WORK/expected_upload_scope.txt"; diff -u "$WORK/expected_upload_scope.txt" "$WORK/actual_upload_scope.txt" || fail "26669 upload scope mismatch"
 ! grep -Eq '^app/' "$WORK/actual_upload_scope.txt" || fail "handoff commit contains live app source"
 set_report "CHANGED RUNTIME SCOPE" "PASS (6 runtime paths / 0 additions carried only inside sealed handoff payload; live app source not committed)"
}
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
 [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "successful 26668 artifact ZIP SHA"
 unzip -q "$ARTZIP" -d "$ARTDIR"; local tarball="$ARTDIR/build_26668_r1_motion_evidence_ui_outputs/26668_R1_candidate_app_source.tar.gz"
 [[ -f "$tarball" && "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "successful 26668 compiled candidate TAR authority"
 tar -xzf "$tarball" -C "$BASE"; (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null) || fail "exact successful 26668 base manifest"
 set_report "RUNTIME AUTHORITY" "PASS (successful 26668 commit ${RUNTIME_AUTHORITY_COMMIT}/run ${BASE_RUN_ID}/artifact ${BASE_ARTIFACT_ID}/compiled candidate TAR ${BASE_TAR_SHA})"
}
make_candidate(){
 python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26669_transform.txt"; python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26669_transform_replay.txt"; compare_app_trees "$AFTER" "$AFTER2"
 python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26669_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$AFTER" | tee "$OUT/26669_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26669_authority_candidate.txt"
 set_report "STATELESS PREVIEW / HAL AE OWNER" "PASS (HAL/user AE remains sole repeating sensor-exposure owner; delayed 26662 writer dormant; preview shoulder is frame-local/stateless display-only with no histogram or request feedback)"
 set_report "ISOLATED CAPTURE-TIME SHORT" "PASS (26668 shutter-time generation/timestamp SHORT planner retained; bridge now schedules only capture-plan-owned SHORT into hardened one-tunnel Sabre auxiliary path; SHORT remains outside NORMAL temporal list/count)"
 set_report "NORMAL DEFORMING-SUBJECT REJECTION" "PASS (ordinary temporal rejection gains independent local-affine residual/disocclusion veto; coherent <=0.75px identity; >=2.25px rejected)"
 set_report "LONG HARD ADMISSION/NORMAL CHROMA" "PASS (marginal LONG hard-rejected before baseline contribution; all-channel source validity required; LONG radiance anchored to NORMAL-reference chromaticity; final strong LONG bounded 1.25)"
 set_report "SPATIAL SUPPORT BODY RECOVERY" "PASS (dedicated Sabre reconstruction-support map, separate from denoise strength, gates only extra 26666 high-DR body lift identically in SDR and UHDR; missing provenance fails closed)"
 set_report "EFFECTIVE-SUPPORT NON-AUTHORITY" "PASS (26669 preserves 26668 capture/fusion/body decisions without using effectiveSupport as captured/merged/contributing frame-count authority)"
 set_report "LIVE RGB HISTOGRAM" "PASS (always-on 96x54 latest-frame PixelCopy RGB histogram; one in-flight/no queue/reused scratch; read-only from Camera2/capture owners)"
 set_report "SINGLE-OWNER EXACT-VALUE MANUAL SLIDERS" "PASS (slider bound to exact CameraFragment manual console; no singleton duplicate; AUTO separate; one tick per existing value; yellow exact value; full-screen held drag retained)"
 set_report "V9 UI GEOMETRY / LEGACY LABEL NEUTRALIZATION" "PASS (26668 v9 geometry/histogram/JPG/flip bytes protected; legacy 26644/26648 styling cannot re-enable Auto/numeric labels; collapsed state icons-only)"
 set_report "HIGHLIGHT/X/UHDR PROTECTION" "PASS (26651 hardened NORMAL-master SHORT fusion reused; current highlight/X/sun/window/cloud renderer retained; spatial body-support gate mirrored in matched UHDR intent)"
 set_report "NIGHT/DNG/SR PROTECTION" "PASS (Night/DNG/SR protected by exact authority manifests; no ownership rewrite)"
 set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (1725 base / 1725 candidate / 1719 protected / 807 native / 778 vendor / 7 DNG / 257 standalone shaders / 6 changed / 0 added)"
 set_report "PROTECTED/DNG/NATIVE/VENDOR INVARIANCE" "PASS"
}
verify_shaders(){
 if [[ -n "$LOCAL_ART" ]]; then python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26669_shader_validation.txt"; set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (exact 12 runtime-expanded variants reconstructed/hash-verified: modified preview plus inherited hash-pinned embedded rejection+merge, hardened SHORT fusion, render/gainmap and color variants; 257 standalone universe pinned)"; set_report "REAL GLSL COMPILE" "NOT RUN locally (Actions required; pinned 16.5.0 gate packaged)"; set_compiler "REAL GLSL COMPILE" "NOT RUN locally (Actions required; pinned 16.5.0 gate packaged)"; return; fi
 local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz" compiler; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"; [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive SHA"; mkdir -p "$GLSLANG_DIR"; tar -xzf "$archive" -C "$GLSLANG_DIR"; compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "pinned glslang compiler missing"; "$compiler" --version | tee "$OUT/26669_glslang_version.txt"; python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" --compiler "$compiler" | tee "$OUT/26669_shader_validation.txt"; set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (12 exact runtime variants + complete 257-file shader universe; modified preview plus all inherited critical active GLSL covered)"; set_report "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; exact 12 runtime variants including modified preview and inherited critical active GLSL)"; set_compiler "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; exact 12 runtime variants including modified preview and inherited critical active GLSL)"
}
verify_successful_26668_mechanics(){ python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26669_infrastructure.txt"; set_report "INFRASTRUCTURE DELTA AUDIT" "PASS (functional build mechanics delta ZERO; 26669 identity/successful-26668 authority/6-path scope and semantic/shader targets only; exact successful 26668 compiler/native/patch/PRE-BUILD/assemble/postbuild sequence retained)"; set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (successful 26668 build-script ${AUTH_26668_BUILD_SCRIPT_BLOB} + workflow ${AUTH_26668_WORKFLOW_BLOB})"; }
verify_candidate_patches(){ python3 -S "$PATCHVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26669_patch_validation.txt"; set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"; }
install_frozen_candidate_live(){ rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"; snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"; compare_app_trees "$AFTER" "$LIVE_CANON"; }
postbuild_proof(){
 snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"; compare_app_trees "$AFTER" "$POST"; (cd "$POST" && sha256sum -c "$CAND_PROTECTED" >/dev/null && sha256sum -c "$CAND_NATIVE" >/dev/null && sha256sum -c "$CAND_VENDOR" >/dev/null && sha256sum -c "$CAND_DNG" >/dev/null) || fail "post-build protected invariance"; python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26669_postbuild_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$POST" | tee "$OUT/26669_postbuild_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26669_postbuild_authority.txt"; set_report "POST-BUILD INVARIANCE" "PASS (candidate/protected/DNG/native/vendor exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"
 tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26669_R1_candidate_app_source.tar.gz"; sha256sum "$OUT/26669_R1_candidate_app_source.tar.gz" > "$OUT/26669_R1_candidate_app_source.tar.gz.sha256"; cp "$CAND_FULL" "$OUT/26669_R1_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26669_R1_native_protected_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26669_R1_vendor_protected_postbuild.sha256"; cp "$CAND_DNG" "$OUT/26669_R1_dng_postbuild.sha256"; cp "$SHADER_PIN" "$OUT/26669_R1_runtime_expanded_shaders.sha256"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests + runtime-expanded shader pins)"
}
verify_package
verify_scope
obtain_authority
make_candidate
verify_shaders
verify_successful_26668_mechanics
if [[ -n "$LOCAL_ART" ]]; then
 verify_candidate_patches
 set_report "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real GLSL/Kotlin/Java/NDK/full Android require Actions)"; set_report "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_report "EXACTLY ONE APK" "NOT RUN locally (Actions required)"; set_report "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN locally (Actions required)"
 set_compiler "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_compiler "NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_compiler "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_compiler "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; cp "$OUT/26669_R1_STRICT_HANDOFF_REPORT.txt" "$OUT/26669_R1_local_prebuild_report.txt"; pass "26669 R1 LOCAL PREBUILD PREPARED: exact successful 26668 compiled authority; all locally applicable packaged gates passed; real compiler/build gates explicitly unproven locally"; exit 0
fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26669_gradle_language_compilers.log"
set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"; compare_app_trees "$AFTER" "$WORK/after_language_compiler_snapshot"
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26669_gradle_native_compiler.log"
set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
verify_candidate_patches
set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26669 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26669_gradle_assemble.log"
set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort)
[[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK"
mv "${apks[0]}" "$FINAL"; [[ -f "$FINAL" ]] || fail "final APK missing after move"; set_report "EXACTLY ONE APK" "PASS"; sha256sum "$FINAL" > "$OUT/26669_R1_APK.sha256"
postbuild_proof
pass "26669 R1 ACTIONS BUILD COMPLETE"
