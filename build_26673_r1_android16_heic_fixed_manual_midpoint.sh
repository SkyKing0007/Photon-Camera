#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
resolve_glslang_compiler(){ local root="$1" compiler="" compat=""; compiler="$(find "$root" -type f -name glslang -print -quit)"; if [[ -z "$compiler" ]]; then compat="$(find "$root" \( -type f -o -type l \) -name glslangValidator -print -quit)"; if [[ -n "$compat" ]]; then compiler="$(readlink -f "$compat" 2>/dev/null || true)"; fi; fi; [[ -n "$compiler" && -f "$compiler" ]] || return 1; printf '%s\n' "$compiler"; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
UPLOAD_PARENT_COMMIT="2b6c3ef726cc8532ebfa5e4499bde6ab79bdbc14"
RUNTIME_AUTHORITY_COMMIT="2b6c3ef726cc8532ebfa5e4499bde6ab79bdbc14"
BASE_RUN_ID="35471368787"
BASE_ARTIFACT_ID="10593065124"
BASE_ARTIFACT_NAME="photon-26672-r1-heic-google-v2-ui-polish"
BASE_ARTIFACT_SHA="a8230bc9ff9e46bd8ad4d2688dd152542386dda22576a577d07b132c5aaba95c"
BASE_TAR_SHA="b82a82930a507698fa3aaedc458c9dd4721dea8f139333cdcdb398a7adc50d86"
VERSION_NAME="0.9726673"; VERSION_BUILD="26673"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
AUTH_26672_BUILD_SCRIPT_BLOB="daa1219054538ff5d8fad6a19b60dba71b6c7576"
AUTH_26672_WORKFLOW_BLOB="3a04ad23f90706c532e37ecb270201e928ccdf28"
HANDOFF="$ROOT/R1_26673_HANDOFF_HASHES.sha256"; UPLOADS="$ROOT/R1_26673_UPLOAD_PATHS.txt"
BASE_FULL="$ROOT/R1_26673_BASE_26672_FULL_APP.sha256"; CAND_FULL="$ROOT/R1_26673_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/R1_26673_PROTECTED_UNCHANGED_BASE.sha256"; CAND_PROTECTED="$ROOT/R1_26673_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/R1_26673_NATIVE_PROTECTED_BASE.sha256"; CAND_NATIVE="$ROOT/R1_26673_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/R1_26673_VENDOR_PROTECTED_BASE.sha256"; CAND_VENDOR="$ROOT/R1_26673_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/R1_26673_DNG_BASE.sha256"; CAND_DNG="$ROOT/R1_26673_DNG_CANDIDATE.sha256"
SHADER_BASE="$ROOT/R1_26673_SHADER_UNIVERSE_BASE.sha256"; SHADER_CAND="$ROOT/R1_26673_SHADER_UNIVERSE_CANDIDATE.sha256"
CHANGED="$ROOT/R1_26673_RUNTIME_CHANGED_PATHS.txt"; PREWRITE="$ROOT/R1_26673_PREWRITE_SOURCE_HASHES.sha256"; ADDED="$ROOT/R1_26673_ADDED_PATHS_MUST_BE_ABSENT.txt"; EXPECTED_CHANGED="$ROOT/R1_26673_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/R1_26673_RUNTIME_DELTA_FROM_26672.patch"; ROLLBACK="$ROOT/R1_26673_RUNTIME_ROLLBACK_TO_26672.patch"; SHADER_PIN="$ROOT/R1_26673_RUNTIME_EXPANDED_SHADERS.sha256"
TRANSFORM="$ROOT/transform_26673.py"; VALIDATE="$ROOT/validate_26673.py"; AUTHORITY="$ROOT/verify_26673_authority.py"; INFRA="$ROOT/verify_26673_infrastructure.py"; PATCHVERIFY="$ROOT/verify_26673_patches.py"; SHADERVERIFY="$ROOT/verify_26673_shaders.py"; GATEVERIFY="$ROOT/verify_26673_regressions.py"
BUILD_SCRIPT="$ROOT/build_26673_r1_android16_heic_fixed_manual_midpoint.sh"; WORKFLOW="$ROOT/.github/workflows/build-26673-r1-android16-heic-fixed-manual-midpoint.yml"
OUT="$ROOT/build_26673_r1_android16_heic_fixed_manual_midpoint_outputs"; WORK="$ROOT/.build_26673_r1_android16_heic_fixed_manual_midpoint_work"
ARTZIP="$WORK/26672_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_successful_26672_compiled_candidate"; AFTER="$WORK/candidate_26673_r1"; AFTER2="$WORK/candidate_26673_r1_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; GLSLANG_DIR="$WORK/glslang-${GLSLANG_VERSION}"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r1-android16-heic-fixed-manual-midpoint-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26672 artifact ZIP"; LOCAL_ART="$2"; elif [[ -n "${1:-}" ]]; then fail "unknown argument: $1"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26673_R1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26673_R1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME AUTHORITY: NOT RUN
VERIFICATION MECHANICS AUTHORITY: NOT RUN
BACKUP STATUS: PASS (NONE, by request)
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE DELTA AUDIT: NOT RUN
26672 BEHAVIOR HARDLOCK: NOT RUN
JPEG / HDR PIPELINE HARDLOCK: NOT RUN
HEIC ANDROID16 PUBLICATION: NOT RUN
HEIC GAINMAP / METADATA IDENTITY: NOT RUN
HEIC SUPERRES HARDLOCK: NOT RUN
MANUAL FIXED 26672 MIDPOINT: NOT RUN
FRONT SWITCH VECTOR HARDLOCK: NOT RUN
HISTOGRAM / CAMERA2 / MANUAL TOUCH HARDLOCK: NOT RUN
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
TARGET VERSION/BUILD: 0.9726673 / 26673
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26673_R1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26673_R1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26673_R1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26673_R1_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){ local authority_root="$1" live_root="$2" dest_root="$3"; rm -rf "$dest_root"; mkdir -p "$dest_root"; cp -a "$authority_root/." "$dest_root/"; rm -rf "$dest_root/app/src"; cp -a "$live_root/app/src" "$dest_root/app/"; cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"; cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"; }
compare_app_trees(){ python3 -S - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a=H(sys.argv[1]);b=H(sys.argv[2]);assert len(a)==1726 and a==b,(len(a),len(b),sorted(set(a)^set(b))[:10]);print('PASS authority-seeded candidate byte-identical: 1726 files')
PY
}
verify_package(){
 [[ -f "$HANDOFF" && -f "$UPLOADS" && -d "$ROOT/handoff_payload_26673" ]] || fail "sealed 26673 package incomplete"
 [[ -f "$ROOT/R1_26673_RUNTIME_EXPANDED_CHANGED_VARIANTS.txt" ]] || fail "sealed 26673 runtime-expanded variant list missing"
 [[ "$(find "$ROOT/handoff_payload_26673" -type f | wc -l)" -eq 3 ]] || fail "sealed runtime payload must contain exactly 3 files"
 [[ "$(wc -l < "$CHANGED")" -eq 3 && "$(wc -l < "$ADDED")" -eq 0 ]] || fail "26673 allowlist/addition count"
 sha256sum -c "$HANDOFF" >/dev/null
 [[ "$(wc -l < "$BASE_FULL")" -eq 1726 && "$(wc -l < "$CAND_FULL")" -eq 1726 ]] || fail "full app count"
 [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1723 && "$(wc -l < "$BASE_NATIVE")" -eq 806 && "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$BASE_DNG")" -eq 7 ]] || fail "protected manifest counts"
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
 if [[ -n "$LOCAL_ART" ]]; then set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed 26673 candidate; exact 3 modified / 0 added / 0 deleted from successful 26672 compiled authority)"; return; fi
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
 [[ "$(git rev-parse HEAD^)" == "$UPLOAD_PARENT_COMMIT" ]] || fail "26673 parent must be exact successful 26672 commit ${UPLOAD_PARENT_COMMIT}"
 [[ "$(git rev-parse "${RUNTIME_AUTHORITY_COMMIT}:build_26672_r1_heic_google_v2_ui_polish.sh")" == "$AUTH_26672_BUILD_SCRIPT_BLOB" ]] || fail "successful 26672 build-script blob changed"
 [[ "$(git rev-parse "${RUNTIME_AUTHORITY_COMMIT}:.github/workflows/build-26672-r1-heic-google-v2-ui-polish.yml")" == "$AUTH_26672_WORKFLOW_BLOB" ]] || fail "successful 26672 workflow blob changed"
 git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | sort > "$WORK/actual_upload_scope.txt"; sort "$UPLOADS" > "$WORK/expected_upload_scope.txt"; diff -u "$WORK/expected_upload_scope.txt" "$WORK/actual_upload_scope.txt" || fail "26673 upload scope mismatch"
 ! grep -Eq '^app/' "$WORK/actual_upload_scope.txt" || fail "handoff commit contains live app source"
 set_report "CHANGED RUNTIME SCOPE" "PASS (3 runtime paths / 3 modifications / 0 additions / 0 deletions carried only inside sealed handoff payload; live app source not committed)"
}
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
 [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "successful 26672 artifact ZIP SHA"
 unzip -q "$ARTZIP" -d "$ARTDIR"; local tarball="$ARTDIR/build_26672_r1_heic_google_v2_ui_polish_outputs/26672_R1_candidate_app_source.tar.gz"
 [[ -f "$tarball" && "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "successful 26672 compiled candidate TAR authority"
 tar -xzf "$tarball" -C "$BASE"; (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null) || fail "exact successful 26672 base manifest"
 set_report "RUNTIME AUTHORITY" "PASS (successful 26672 commit ${RUNTIME_AUTHORITY_COMMIT}/run ${BASE_RUN_ID}/artifact ${BASE_ARTIFACT_ID}/compiled candidate TAR ${BASE_TAR_SHA})"
}
make_candidate(){
 python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26673_transform.txt"; python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26673_transform_replay.txt"; compare_app_trees "$AFTER" "$AFTER2"
 python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26673_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$AFTER" | tee "$OUT/26673_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26673_authority_candidate.txt"
 set_report "26672 BEHAVIOR HARDLOCK" "PASS (successful-26672 compiled candidate is exact authority; 1723 non-allowlisted runtime files byte-identical; no additions or deletions)"
 set_report "JPEG / HDR PIPELINE HARDLOCK" "PASS (render/gainmap shaders, 26672 highlight separation, JPEG/JPEG-R, SHORT/NORMAL/LONG, Motion/Sabre, denoise/noise, Local-Laplacian and viewfinder owners exact successful-26672 bytes)"
 set_report "HEIC ANDROID16 PUBLICATION" "PASS (normal 1x HEIC only: Android16/AOSP HEIC_UHDR explicit P3 full-range YUV420 base; P3+sRGB+matrix-unspecified base/tmap; all-unspecified gain-map color aspects; no HDR recomputation)"
 set_report "HEIC GAINMAP / METADATA IDENTITY" "PASS (Iris HEIC Java readback/numerical proof + hardware encoder exact 26672; native gain-map bytes and ISO 21496 min/max/gamma/offset/capacity/use-base metadata construction text-exact; recomputedGainmap=false)"
 set_report "HEIC SUPERRES HARDLOCK" "PASS (writeSuperResGridNative and its entire native suffix exact successful-26672 bytes)"
 set_report "MANUAL FIXED 26672 MIDPOINT" "PASS (exact final successful-26672 visible geometry is baseline; Focus/Shutter/ISO/EV row midpoint established once from measured slider outer bottom + activated-chevron visible top; hide/reopen changes visibility only and never row Y)"
 set_report "FRONT SWITCH VECTOR HARDLOCK" "PASS (26672 front-switch vector/button/layout/padding/tint/touch bytes exact)"
 set_report "HISTOGRAM / CAMERA2 / MANUAL TOUCH HARDLOCK" "PASS (26672 histogram pill/PixelCopy, Camera2 lifecycle, CameraUIView midpoint baseline and manual slider touch ownership exact successful-26672 bytes)"
 set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (1726 base / 1726 candidate / 1723 protected / 806 native-protected / 778 vendor / 7 DNG / 257 standalone shaders / 3 modified / 0 added / 0 deleted)"
 set_report "PROTECTED/DNG/NATIVE/VENDOR INVARIANCE" "PASS"
}
verify_shaders(){
 if [[ -n "$LOCAL_ART" ]]; then python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26673_shader_validation.txt"; set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (exact 12 runtime-expanded variants reconstructed/hash-verified; changedVariants=0; exact successful-26672 hashes pinned; 257 standalone universe pinned)"; set_report "REAL GLSL COMPILE" "NOT RUN locally (Actions required; pinned 16.5.0 gate packaged)"; set_compiler "REAL GLSL COMPILE" "NOT RUN locally (Actions required; pinned 16.5.0 gate packaged)"; return; fi
 local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz" compiler; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"; [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive SHA"; mkdir -p "$GLSLANG_DIR"; tar -xzf "$archive" -C "$GLSLANG_DIR"; compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "pinned glslang compiler missing"; "$compiler" --version | tee "$OUT/26673_glslang_version.txt"; python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" --compiler "$compiler" | tee "$OUT/26673_shader_validation.txt"; set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (12 exact runtime variants + complete 257-file shader universe; changedVariants=0; all successful-26672 critical active GLSL covered)"; set_report "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; exact 12 runtime variants unchanged from successful 26672)"; set_compiler "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; exact 12 runtime variants unchanged from successful 26672)"
}
verify_successful_26672_mechanics(){ python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26673_infrastructure.txt"; set_report "INFRASTRUCTURE DELTA AUDIT" "PASS (functional build mechanics delta ZERO; 26673 identity/successful-26672 authority/3-path scope and HEIC/UI semantic targets only; exact successful 26672 compiler/native/patch/PRE-BUILD/assemble/postbuild sequence retained)"; set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (successful 26672 build-script ${AUTH_26672_BUILD_SCRIPT_BLOB} + workflow ${AUTH_26672_WORKFLOW_BLOB})"; }
verify_candidate_patches(){ python3 -S "$PATCHVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26673_patch_validation.txt"; set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"; }
install_frozen_candidate_live(){ rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"; snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"; compare_app_trees "$AFTER" "$LIVE_CANON"; }
postbuild_proof(){
 snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"; compare_app_trees "$AFTER" "$POST"; (cd "$POST" && sha256sum -c "$CAND_PROTECTED" >/dev/null && sha256sum -c "$CAND_NATIVE" >/dev/null && sha256sum -c "$CAND_VENDOR" >/dev/null && sha256sum -c "$CAND_DNG" >/dev/null) || fail "post-build protected invariance"; python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26673_postbuild_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$POST" | tee "$OUT/26673_postbuild_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26673_postbuild_authority.txt"; set_report "POST-BUILD INVARIANCE" "PASS (candidate/protected/DNG/native/vendor exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"
 tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26673_R1_candidate_app_source.tar.gz"; sha256sum "$OUT/26673_R1_candidate_app_source.tar.gz" > "$OUT/26673_R1_candidate_app_source.tar.gz.sha256"; cp "$CAND_FULL" "$OUT/26673_R1_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26673_R1_native_protected_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26673_R1_vendor_protected_postbuild.sha256"; cp "$CAND_DNG" "$OUT/26673_R1_dng_postbuild.sha256"; cp "$SHADER_PIN" "$OUT/26673_R1_runtime_expanded_shaders.sha256"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests + runtime-expanded shader pins)"
}
verify_package
verify_scope
obtain_authority
make_candidate
verify_shaders
verify_successful_26672_mechanics
if [[ -n "$LOCAL_ART" ]]; then
 verify_candidate_patches
 set_report "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real GLSL/Kotlin/Java/NDK/full Android require Actions)"; set_report "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_report "EXACTLY ONE APK" "NOT RUN locally (Actions required)"; set_report "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN locally (Actions required)"
 set_compiler "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_compiler "NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_compiler "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_compiler "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; cp "$OUT/26673_R1_STRICT_HANDOFF_REPORT.txt" "$OUT/26673_R1_local_prebuild_report.txt"; pass "26673 R1 LOCAL PREBUILD PREPARED: exact successful 26672 compiled authority; all locally applicable packaged gates passed; real compiler/build gates explicitly unproven locally"; exit 0
fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26673_gradle_language_compilers.log"
set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"; compare_app_trees "$AFTER" "$WORK/after_language_compiler_snapshot"
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26673_gradle_native_compiler.log"
set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
verify_candidate_patches
set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26673 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26673_gradle_assemble.log"
set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort)
[[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK"
mv "${apks[0]}" "$FINAL"; [[ -f "$FINAL" ]] || fail "final APK missing after move"; set_report "EXACTLY ONE APK" "PASS"; sha256sum "$FINAL" > "$OUT/26673_R1_APK.sha256"
postbuild_proof
pass "26673 R1 ACTIONS BUILD COMPLETE"
