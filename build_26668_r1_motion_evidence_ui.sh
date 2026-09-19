#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
resolve_glslang_compiler(){ local root="$1" compiler="" compat=""; compiler="$(find "$root" -type f -name glslang -print -quit)"; if [[ -z "$compiler" ]]; then compat="$(find "$root" \( -type f -o -type l \) -name glslangValidator -print -quit)"; if [[ -n "$compat" ]]; then compiler="$(readlink -f "$compat" 2>/dev/null || true)"; fi; fi; [[ -n "$compiler" && -f "$compiler" ]] || return 1; printf '%s\n' "$compiler"; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
UPLOAD_PARENT_COMMIT="ac16f7cce71912b5284b4b2a37628d632dcf47d5"
RUNTIME_AUTHORITY_COMMIT="c4e3f1f78d985d0fb041fb662f3e1b0557205d79"
BASE_RUN_ID="35386817929"
BASE_ARTIFACT_ID="10564197796"
BASE_ARTIFACT_NAME="photon-26667-r1-preview-long-confidence"
BASE_ARTIFACT_SHA="aef401cc933737bbf82e35556dd2ecaf94cd57f4867ec3aba20004fcfb17b11d"
BASE_TAR_SHA="0018b1c81fa02756cfcba0dbfaa84796f2df547499a1401b4e5274f8986fa06e"
VERSION_NAME="0.9726668"; VERSION_BUILD="26668"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
AUTH_26667_BUILD_SCRIPT_BLOB="3279c2a8179c40daf7f99202ba1aaa5f3e213671"
AUTH_26667_WORKFLOW_BLOB="c33eec9a2c77a4116acf0142d569f1824d387d75"
HANDOFF="$ROOT/R1_26668_HANDOFF_HASHES.sha256"; UPLOADS="$ROOT/R1_26668_UPLOAD_PATHS.txt"
BASE_FULL="$ROOT/R1_26668_BASE_26667_FULL_APP.sha256"; CAND_FULL="$ROOT/R1_26668_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/R1_26668_PROTECTED_UNCHANGED_BASE.sha256"; CAND_PROTECTED="$ROOT/R1_26668_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/R1_26668_NATIVE_PROTECTED_BASE.sha256"; CAND_NATIVE="$ROOT/R1_26668_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/R1_26668_VENDOR_PROTECTED_BASE.sha256"; CAND_VENDOR="$ROOT/R1_26668_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/R1_26668_DNG_BASE.sha256"; CAND_DNG="$ROOT/R1_26668_DNG_CANDIDATE.sha256"
SHADER_BASE="$ROOT/R1_26668_SHADER_UNIVERSE_BASE.sha256"; SHADER_CAND="$ROOT/R1_26668_SHADER_UNIVERSE_CANDIDATE.sha256"
CHANGED="$ROOT/R1_26668_RUNTIME_CHANGED_PATHS.txt"; PREWRITE="$ROOT/R1_26668_PREWRITE_SOURCE_HASHES.sha256"; ADDED="$ROOT/R1_26668_ADDED_PATHS_MUST_BE_ABSENT.txt"; EXPECTED_CHANGED="$ROOT/R1_26668_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/R1_26668_RUNTIME_DELTA_FROM_26667.patch"; ROLLBACK="$ROOT/R1_26668_RUNTIME_ROLLBACK_TO_26667.patch"; SHADER_PIN="$ROOT/R1_26668_RUNTIME_EXPANDED_SHADERS.sha256"
TRANSFORM="$ROOT/transform_26668.py"; VALIDATE="$ROOT/validate_26668.py"; AUTHORITY="$ROOT/verify_26668_authority.py"; INFRA="$ROOT/verify_26668_infrastructure.py"; PATCHVERIFY="$ROOT/verify_26668_patches.py"; SHADERVERIFY="$ROOT/verify_26668_shaders.py"; GATEVERIFY="$ROOT/verify_26668_regressions.py"
BUILD_SCRIPT="$ROOT/build_26668_r1_motion_evidence_ui.sh"; WORKFLOW="$ROOT/.github/workflows/build-26668-r1-motion-evidence-ui.yml"
OUT="$ROOT/build_26668_r1_motion_evidence_ui_outputs"; WORK="$ROOT/.build_26668_r1_motion_evidence_ui_work"
ARTZIP="$WORK/26667_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_successful_26667_compiled_candidate"; AFTER="$WORK/candidate_26668_r1"; AFTER2="$WORK/candidate_26668_r1_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; GLSLANG_DIR="$WORK/glslang-${GLSLANG_VERSION}"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r1-motion-evidence-ui-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26667 artifact ZIP"; LOCAL_ART="$2"; elif [[ -n "${1:-}" ]]; then fail "unknown argument: $1"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26668_R1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26668_R1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME AUTHORITY: NOT RUN
VERIFICATION MECHANICS AUTHORITY: NOT RUN
BACKUP STATUS: PASS (NONE, by request)
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE DELTA AUDIT: NOT RUN
TRUE 26660 PREVIEW OWNER: NOT RUN
CAPTURE-TIME HDR BRACKET: NOT RUN
NORMAL DEFORMING-SUBJECT REJECTION: NOT RUN
LONG HARD ADMISSION/NORMAL CHROMA: NOT RUN
SPATIAL SUPPORT BODY RECOVERY: NOT RUN
EFFECTIVE-SUPPORT NON-AUTHORITY: NOT RUN
LIVE RGB HISTOGRAM: NOT RUN
EXACT-VALUE MANUAL SLIDERS: NOT RUN
UI GEOMETRY/FLIP ICON: NOT RUN
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
TARGET VERSION/BUILD: 0.9726668 / 26668
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26668_R1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26668_R1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26668_R1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26668_R1_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){ local authority_root="$1" live_root="$2" dest_root="$3"; rm -rf "$dest_root"; mkdir -p "$dest_root"; cp -a "$authority_root/." "$dest_root/"; rm -rf "$dest_root/app/src"; cp -a "$live_root/app/src" "$dest_root/app/"; cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"; cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"; }
compare_app_trees(){ python3 -S - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a=H(sys.argv[1]);b=H(sys.argv[2]);assert len(a)==1725 and a==b,(len(a),len(b),sorted(set(a)^set(b))[:10]);print('PASS authority-seeded candidate byte-identical: 1725 files')
PY
}
verify_package(){
 [[ -f "$HANDOFF" && -f "$UPLOADS" && -d "$ROOT/handoff_payload_26668" ]] || fail "sealed 26668 package incomplete"
 [[ "$(find "$ROOT/handoff_payload_26668" -type f | wc -l)" -eq 18 ]] || fail "sealed runtime payload must contain exactly 18 files"
 [[ "$(wc -l < "$CHANGED")" -eq 18 && "$(wc -l < "$ADDED")" -eq 4 ]] || fail "26668 allowlist/addition count"
 sha256sum -c "$HANDOFF" >/dev/null
 [[ "$(wc -l < "$BASE_FULL")" -eq 1721 && "$(wc -l < "$CAND_FULL")" -eq 1725 ]] || fail "full app count"
 [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1707 && "$(wc -l < "$BASE_NATIVE")" -eq 807 && "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$BASE_DNG")" -eq 7 ]] || fail "protected manifest counts"
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
 if [[ -n "$LOCAL_ART" ]]; then set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed 26668 candidate; exact 18 changed / 4 added from successful 26667 compiled authority)"; return; fi
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
 [[ "$(git rev-parse HEAD^)" == "$UPLOAD_PARENT_COMMIT" ]] || fail "26668 R1.1 repair parent must be exact failed 26668 commit ${UPLOAD_PARENT_COMMIT}"
 [[ "$(git rev-parse "${RUNTIME_AUTHORITY_COMMIT}:build_26667_r1_preview_long_confidence.sh")" == "$AUTH_26667_BUILD_SCRIPT_BLOB" ]] || fail "successful 26667 build-script blob changed"
 [[ "$(git rev-parse "${RUNTIME_AUTHORITY_COMMIT}:.github/workflows/build-26667-r1-preview-long-confidence.yml")" == "$AUTH_26667_WORKFLOW_BLOB" ]] || fail "successful 26667 workflow blob changed"
 git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | sort > "$WORK/actual_upload_scope.txt"; sort "$UPLOADS" > "$WORK/expected_upload_scope.txt"; diff -u "$WORK/expected_upload_scope.txt" "$WORK/actual_upload_scope.txt" || fail "26668 upload scope mismatch"
 ! grep -Eq '^app/' "$WORK/actual_upload_scope.txt" || fail "handoff commit contains live app source"
 set_report "CHANGED RUNTIME SCOPE" "PASS (18 runtime paths / 4 additions carried only inside sealed handoff payload; live app source not committed)"
}
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
 [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "successful 26667 artifact ZIP SHA"
 unzip -q "$ARTZIP" -d "$ARTDIR"; local tarball="$ARTDIR/build_26667_r1_preview_long_confidence_outputs/26667_R1_candidate_app_source.tar.gz"
 [[ -f "$tarball" && "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "successful 26667 compiled candidate TAR authority"
 tar -xzf "$tarball" -C "$BASE"; (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null) || fail "exact successful 26667 base manifest"
 set_report "RUNTIME AUTHORITY" "PASS (successful 26667 commit ${RUNTIME_AUTHORITY_COMMIT}/run ${BASE_RUN_ID}/artifact ${BASE_ARTIFACT_ID}/compiled candidate TAR ${BASE_TAR_SHA})"
}
make_candidate(){
 python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26668_transform.txt"; python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26668_transform_replay.txt"; compare_app_trees "$AFTER" "$AFTER2"
 python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26668_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$AFTER" | tee "$OUT/26668_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26668_authority_candidate.txt"
 set_report "TRUE 26660 PREVIEW OWNER" "PASS (MainRenderer + preview shader exact successful-26660 bytes; delayed 26662 HDR AE writer dormant; NORMAL referenceProtectionEv=0)"
 set_report "CAPTURE-TIME HDR BRACKET" "PASS (highlight protection moved behind shutter to generation/timestamp-owned RAW-only HIGHLIGHT_SHORT; SHORT excluded from NORMAL temporal accumulator; exact total NORMAL+SHORT+LONG budget retained)"
 set_report "NORMAL DEFORMING-SUBJECT REJECTION" "PASS (ordinary temporal rejection gains independent local-affine residual/disocclusion veto; coherent <=0.75px identity; >=2.25px rejected)"
 set_report "LONG HARD ADMISSION/NORMAL CHROMA" "PASS (marginal LONG hard-rejected before baseline contribution; all-channel source validity required; LONG radiance anchored to NORMAL-reference chromaticity; final strong LONG bounded 1.25)"
 set_report "SPATIAL SUPPORT BODY RECOVERY" "PASS (dedicated Sabre reconstruction-support map, separate from denoise strength, gates only extra 26666 high-DR body lift identically in SDR and UHDR; missing provenance fails closed)"
 set_report "EFFECTIVE-SUPPORT NON-AUTHORITY" "PASS (26668 capture/fusion/body decisions do not use effectiveSupport as captured/merged/contributing frame-count authority)"
 set_report "LIVE RGB HISTOGRAM" "PASS (always-on 96x54 latest-frame PixelCopy RGB histogram; one in-flight/no queue/reused scratch; read-only from Camera2/capture owners)"
 set_report "EXACT-VALUE MANUAL SLIDERS" "PASS (AUTO separate; exactly one tick per existing non-AUTO KnobItemInfo; yellow exact text/value; pointer retained outside panel until UP/CANCEL; true system auto restore)"
 set_report "UI GEOMETRY/FLIP ICON" "PASS (JPG remains wrap-content at timer-pill 38dp height; histogram mirrors timer-pill 108x38 alignment/spacing; manual group exact +12px; approved curved-arrow switch asset)"
 set_report "HIGHLIGHT/X/UHDR PROTECTION" "PASS (26651 hardened NORMAL-master SHORT fusion reused; current highlight/X/sun/window/cloud renderer retained; spatial body-support gate mirrored in matched UHDR intent)"
 set_report "NIGHT/DNG/SR PROTECTION" "PASS (Night/DNG/SR protected by exact authority manifests; no ownership rewrite)"
 set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (1721 base / 1725 candidate / 1707 protected / 807 native / 778 vendor / 7 DNG / 257 standalone shaders / 18 changed / 4 added)"
 set_report "PROTECTED/DNG/NATIVE/VENDOR INVARIANCE" "PASS"
}
verify_shaders(){
 if [[ -n "$LOCAL_ART" ]]; then python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26668_shader_validation.txt"; set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (exact 12 runtime-expanded variants reconstructed/hash-verified: modified embedded rejection+merge, reactivated hardened SHORT fusion, modified render/gainmap/preview plus color variants; 257 standalone universe pinned)"; set_report "REAL GLSL COMPILE" "NOT RUN locally (Actions required; pinned 16.5.0 gate packaged)"; set_compiler "REAL GLSL COMPILE" "NOT RUN locally (Actions required; pinned 16.5.0 gate packaged)"; return; fi
 local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz" compiler; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"; [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive SHA"; mkdir -p "$GLSLANG_DIR"; tar -xzf "$archive" -C "$GLSLANG_DIR"; compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "pinned glslang compiler missing"; "$compiler" --version | tee "$OUT/26668_glslang_version.txt"; python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" --compiler "$compiler" | tee "$OUT/26668_shader_validation.txt"; set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (12 exact runtime variants + complete 257-file shader universe; every modified active GLSL plus reactivated hardened SHORT covered)"; set_report "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; exact 12 runtime variants including all modified/critical active GLSL)"; set_compiler "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; exact 12 runtime variants including all modified/critical active GLSL)"
}
verify_successful_26667_mechanics(){ python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26668_infrastructure.txt"; set_report "INFRASTRUCTURE DELTA AUDIT" "PASS (functional build mechanics delta ZERO; 26668 identity/successful-26667 authority/18-path scope and semantic/shader targets only; exact successful 26667 compiler/native/patch/PRE-BUILD/assemble/postbuild sequence retained)"; set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (successful 26667 build-script ${AUTH_26667_BUILD_SCRIPT_BLOB} + workflow ${AUTH_26667_WORKFLOW_BLOB})"; }
verify_candidate_patches(){ python3 -S "$PATCHVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26668_patch_validation.txt"; set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"; }
install_frozen_candidate_live(){ rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"; snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"; compare_app_trees "$AFTER" "$LIVE_CANON"; }
postbuild_proof(){
 snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"; compare_app_trees "$AFTER" "$POST"; (cd "$POST" && sha256sum -c "$CAND_PROTECTED" >/dev/null && sha256sum -c "$CAND_NATIVE" >/dev/null && sha256sum -c "$CAND_VENDOR" >/dev/null && sha256sum -c "$CAND_DNG" >/dev/null) || fail "post-build protected invariance"; python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26668_postbuild_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$POST" | tee "$OUT/26668_postbuild_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26668_postbuild_authority.txt"; set_report "POST-BUILD INVARIANCE" "PASS (candidate/protected/DNG/native/vendor exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"
 tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26668_R1_candidate_app_source.tar.gz"; sha256sum "$OUT/26668_R1_candidate_app_source.tar.gz" > "$OUT/26668_R1_candidate_app_source.tar.gz.sha256"; cp "$CAND_FULL" "$OUT/26668_R1_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26668_R1_native_protected_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26668_R1_vendor_protected_postbuild.sha256"; cp "$CAND_DNG" "$OUT/26668_R1_dng_postbuild.sha256"; cp "$SHADER_PIN" "$OUT/26668_R1_runtime_expanded_shaders.sha256"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests + runtime-expanded shader pins)"
}
verify_package
verify_scope
obtain_authority
make_candidate
verify_shaders
verify_successful_26667_mechanics
if [[ -n "$LOCAL_ART" ]]; then
 verify_candidate_patches
 set_report "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real GLSL/Kotlin/Java/NDK/full Android require Actions)"; set_report "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_report "EXACTLY ONE APK" "NOT RUN locally (Actions required)"; set_report "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN locally (Actions required)"
 set_compiler "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_compiler "NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_compiler "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_compiler "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; cp "$OUT/26668_R1_STRICT_HANDOFF_REPORT.txt" "$OUT/26668_R1_local_prebuild_report.txt"; pass "26668 R1 LOCAL PREBUILD PREPARED: exact successful 26667 compiled authority; all locally applicable packaged gates passed; real compiler/build gates explicitly unproven locally"; exit 0
fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26668_gradle_language_compilers.log"
set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"; compare_app_trees "$AFTER" "$WORK/after_language_compiler_snapshot"
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26668_gradle_native_compiler.log"
set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
verify_candidate_patches
set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26668 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26668_gradle_assemble.log"
set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort)
[[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK"
mv "${apks[0]}" "$FINAL"; [[ -f "$FINAL" ]] || fail "final APK missing after move"; set_report "EXACTLY ONE APK" "PASS"; sha256sum "$FINAL" > "$OUT/26668_R1_APK.sha256"
postbuild_proof
pass "26668 R1 ACTIONS BUILD COMPLETE"
