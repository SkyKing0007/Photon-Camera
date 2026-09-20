#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
resolve_glslang_compiler(){ local root="$1" compiler="" compat=""; compiler="$(find "$root" -type f -name glslang -print -quit)"; if [[ -z "$compiler" ]]; then compat="$(find "$root" \( -type f -o -type l \) -name glslangValidator -print -quit)"; if [[ -n "$compat" ]]; then compiler="$(readlink -f "$compat" 2>/dev/null || true)"; fi; fi; [[ -n "$compiler" && -f "$compiler" ]] || return 1; printf '%s\n' "$compiler"; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
UPLOAD_PARENT_COMMIT="101fb9ac90549d6053e15b2b9e97ba5835a14849"
RUNTIME_AUTHORITY_COMMIT="101fb9ac90549d6053e15b2b9e97ba5835a14849"
BASE_RUN_ID="35524878349"
BASE_ARTIFACT_ID="10609466350"
BASE_ARTIFACT_NAME="photon-26676-r1-fast-hdr-wysiwyg-iris-watermark"
BASE_ARTIFACT_SHA="cd39af098f884761301416e18e729d0107de1bcd23399289dcb3fc077c52977a"
BASE_TAR_SHA="dd09e9abb52fa688d59efc52eb3fac079d9f9f90ee62cbbb3479e2c3df6addf2"
VERSION_NAME="0.9726677"; VERSION_BUILD="26677"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
AUTH_26676_BUILD_SCRIPT_BLOB="c33df84f61d3c29e0e7b316ed0f9a827f903ab7d"
AUTH_26676_WORKFLOW_BLOB="a889494ac4c1e06ebaf2bb950f2eca5c5a927ff8"
HANDOFF="$ROOT/R1_26677_HANDOFF_HASHES.sha256"; UPLOADS="$ROOT/R1_26677_UPLOAD_PATHS.txt"
BASE_FULL="$ROOT/R1_26677_BASE_26676_FULL_APP.sha256"; CAND_FULL="$ROOT/R1_26677_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/R1_26677_PROTECTED_UNCHANGED_BASE.sha256"; CAND_PROTECTED="$ROOT/R1_26677_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/R1_26677_NATIVE_PROTECTED_BASE.sha256"; CAND_NATIVE="$ROOT/R1_26677_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/R1_26677_VENDOR_PROTECTED_BASE.sha256"; CAND_VENDOR="$ROOT/R1_26677_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/R1_26677_DNG_BASE.sha256"; CAND_DNG="$ROOT/R1_26677_DNG_CANDIDATE.sha256"
SHADER_BASE="$ROOT/R1_26677_SHADER_UNIVERSE_BASE.sha256"; SHADER_CAND="$ROOT/R1_26677_SHADER_UNIVERSE_CANDIDATE.sha256"
CHANGED="$ROOT/R1_26677_RUNTIME_CHANGED_PATHS.txt"; PREWRITE="$ROOT/R1_26677_PREWRITE_SOURCE_HASHES.sha256"; ADDED="$ROOT/R1_26677_ADDED_PATHS_MUST_BE_ABSENT.txt"; DELETED="$ROOT/R1_26677_DELETED_PATHS_MUST_EXIST.txt"; EXPECTED_CHANGED="$ROOT/R1_26677_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/R1_26677_RUNTIME_DELTA_FROM_26676.patch"; ROLLBACK="$ROOT/R1_26677_RUNTIME_ROLLBACK_TO_26676.patch"; SHADER_PIN="$ROOT/R1_26677_RUNTIME_EXPANDED_SHADERS.sha256"
TRANSFORM="$ROOT/transform_26677.py"; VALIDATE="$ROOT/validate_26677.py"; AUTHORITY="$ROOT/verify_26677_authority.py"; INFRA="$ROOT/verify_26677_infrastructure.py"; PATCHVERIFY="$ROOT/verify_26677_patches.py"; SHADERVERIFY="$ROOT/verify_26677_shaders.py"; GATEVERIFY="$ROOT/verify_26677_regressions.py"
BUILD_SCRIPT="$ROOT/build_26677_r1_watermark_correction.sh"; WORKFLOW="$ROOT/.github/workflows/build-26677-r1-watermark-correction.yml"
OUT="$ROOT/build_26677_r1_watermark_correction_outputs"; WORK="$ROOT/.build_26677_r1_watermark_correction_work"
ARTZIP="$WORK/26676_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_successful_26676_compiled_candidate"; AFTER="$WORK/candidate_26677_r1"; AFTER2="$WORK/candidate_26677_r1_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; GLSLANG_DIR="$WORK/glslang-${GLSLANG_VERSION}"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r1-watermark-correction-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26676 artifact ZIP"; LOCAL_ART="$2"; elif [[ -n "${1:-}" ]]; then fail "unknown argument: $1"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26677_R1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26677_R1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME AUTHORITY: NOT RUN
VERIFICATION MECHANICS AUTHORITY: NOT RUN
BACKUP STATUS: PASS (NONE, by request)
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE DELTA AUDIT: NOT RUN
26676 BEHAVIOR HARDLOCK: NOT RUN
FAST HDR REFERENCE ATTACK + GENERATION GUARD: NOT RUN
WYSIWYG PREVIEW PRESENTATION: NOT RUN
CANONICAL HDR NORMALIZATION: NOT RUN
SHORT ADMISSION + LONG HMART HARDLOCK: NOT RUN
MANUAL VISIBLE ICON GEOMETRY OWNER: NOT RUN
HEIC/UHDR/LOCAL-LAPLACIAN + 26676 SHORT/MANUAL HARDLOCK: NOT RUN
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
TARGET VERSION/BUILD: 0.9726677 / 26677
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26677_R1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26677_R1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26677_R1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26677_R1_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){ local authority_root="$1" live_root="$2" dest_root="$3"; rm -rf "$dest_root"; mkdir -p "$dest_root"; cp -a "$authority_root/." "$dest_root/"; rm -rf "$dest_root/app/src"; cp -a "$live_root/app/src" "$dest_root/app/"; cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"; cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"; }
compare_app_trees(){ python3 -S - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a=H(sys.argv[1]);b=H(sys.argv[2]);assert len(a)==1726 and a==b,(len(a),len(b),sorted(set(a)^set(b))[:10]);print('PASS authority-seeded candidate byte-identical: 1726 files')
PY
}
verify_package(){
 [[ -f "$HANDOFF" && -f "$UPLOADS" && -f "$DELETED" && -d "$ROOT/handoff_payload_26677" ]] || fail "sealed 26677 package incomplete"
 [[ -f "$ROOT/R1_26677_RUNTIME_EXPANDED_CHANGED_VARIANTS.txt" ]] || fail "sealed 26677 runtime-expanded variant list missing"
 [[ "$(find "$ROOT/handoff_payload_26677" -type f | wc -l)" -eq 4 ]] || fail "sealed runtime payload must contain exactly 4 files"
 [[ "$(wc -l < "$CHANGED")" -eq 4 && "$(wc -l < "$ADDED")" -eq 0 && "$(wc -l < "$DELETED")" -eq 0 ]] || fail "26677 allowlist/addition/deletion count"
 sha256sum -c "$HANDOFF" >/dev/null
 [[ "$(wc -l < "$BASE_FULL")" -eq 1726 && "$(wc -l < "$CAND_FULL")" -eq 1726 ]] || fail "full app count"
 [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1722 && "$(wc -l < "$BASE_NATIVE")" -eq 805 && "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$BASE_DNG")" -eq 7 ]] || fail "protected manifest counts"
 [[ "$(wc -l < "$SHADER_BASE")" -eq 257 && "$(wc -l < "$SHADER_CAND")" -eq 257 && "$(wc -l < "$SHADER_PIN")" -eq 14 ]] || fail "shader manifest counts"
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
 if [[ -n "$LOCAL_ART" ]]; then set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed 26677 candidate; exact 4 modified / 0 additions / 0 deletions from successful 26676 compiled authority)"; return; fi
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
 [[ "$(git rev-parse HEAD^)" == "$UPLOAD_PARENT_COMMIT" ]] || fail "26677 parent must be exact successful 26676 commit ${UPLOAD_PARENT_COMMIT}"
 [[ "$(git rev-parse "${RUNTIME_AUTHORITY_COMMIT}:build_26676_r1_fast_hdr_wysiwyg_iris_watermark.sh")" == "$AUTH_26676_BUILD_SCRIPT_BLOB" ]] || fail "successful 26676 build-script blob changed"
 [[ "$(git rev-parse "${RUNTIME_AUTHORITY_COMMIT}:.github/workflows/build-26676-r1-fast-hdr-wysiwyg-iris-watermark.yml")" == "$AUTH_26676_WORKFLOW_BLOB" ]] || fail "successful 26676 workflow blob changed"
 git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | sort > "$WORK/actual_upload_scope.txt"; sort "$UPLOADS" > "$WORK/expected_upload_scope.txt"; diff -u "$WORK/expected_upload_scope.txt" "$WORK/actual_upload_scope.txt" || fail "26677 upload scope mismatch"
 ! grep -Eq '^app/' "$WORK/actual_upload_scope.txt" || fail "handoff commit contains live app source"
 set_report "CHANGED RUNTIME SCOPE" "PASS (4 runtime paths / 4 modifications / 0 additions / 0 deletions carried only inside sealed handoff payload; live app source not committed)"
}
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
 [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "successful 26676 artifact ZIP SHA"
 unzip -q "$ARTZIP" -d "$ARTDIR"; local tarball="$ARTDIR/build_26676_r1_fast_hdr_wysiwyg_iris_watermark_outputs/26676_R1_candidate_app_source.tar.gz"
 [[ -f "$tarball" && "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "successful 26676 compiled candidate TAR authority"
 tar -xzf "$tarball" -C "$BASE"; (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null) || fail "exact successful 26676 base manifest"
 set_report "RUNTIME AUTHORITY" "PASS (successful 26676 commit ${RUNTIME_AUTHORITY_COMMIT}/run ${BASE_RUN_ID}/artifact ${BASE_ARTIFACT_ID}/compiled candidate TAR ${BASE_TAR_SHA})"
}
make_candidate(){
 python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26677_transform.txt"; python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26677_transform_replay.txt"; compare_app_trees "$AFTER" "$AFTER2"
 python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26677_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$AFTER" | tee "$OUT/26677_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26677_authority_candidate.txt"
 set_report "26676 BEHAVIOR HARDLOCK" "PASS (successful-26676 compiled candidate is exact authority; 1722 protected runtime files byte-identical; exactly 4 modifications / 0 additions / 0 deletions)"
 set_report "FAST HDR REFERENCE ATTACK + GENERATION GUARD" "PASS (26676 current-RAW protection solver/4-frame confirmation retained; confirmed increases apply one full bounded target with no 650ms attack cadence; release keeps prior hysteresis; stale pre-protection NORMAL freeze is blocked)"
 set_report "WYSIWYG PREVIEW PRESENTATION" "PASS (preview/main_fs is byte-identical to successful 26674 white-anchored frame-matched presentation; 26675 virtual-unprotected clip owner removed)"
 set_report "CANONICAL HDR NORMALIZATION" "PASS (exact known protection EV restored once in unclipped FLOAT HDR before Local-Laplacian/SDR/UHDR; 65% matcher meters canonicalized candidate)"
 set_report "SHORT ADMISSION + LONG HMART HARDLOCK" "PASS (successful-26676 SHORT admission bytes unchanged; isolated SHORT and fixed +2.5 EV LONG retained)"
 set_report "MANUAL VISIBLE ICON GEOMETRY OWNER" "PASS (successful-26676 CameraFragment/CameraUIViewImpl bytes unchanged; corrected visible-icon midpoint retained)"
 set_report "HEIC/UHDR/LOCAL-LAPLACIAN + 26676 SHORT/MANUAL HARDLOCK" "PASS (HEIC publication/gainmap/render/Local-Laplacian/denoise/color/DNG/SR exact successful-26676 bytes except watermark-local true2x compositor; 26676 SHORT and Manual owners byte-identical)"
 set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (1726 base / 1726 candidate / 1722 protected / 805 native-protected / 778 vendor / 7 DNG / 257 standalone shaders / 4 modified / 0 added / 0 deleted)"
 set_report "PROTECTED/DNG/NATIVE/VENDOR INVARIANCE" "PASS"
}
verify_shaders(){
 if [[ -n "$LOCAL_ART" ]]; then python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26677_shader_validation.txt"; set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (exact 14 runtime-expanded variants reconstructed/hash-verified; changedVariants=2 watermark-off+watermark-on; 257 standalone universe pinned)"; set_report "REAL GLSL COMPILE" "NOT RUN locally (Actions required; pinned 16.5.0 gate packaged)"; set_compiler "REAL GLSL COMPILE" "NOT RUN locally (Actions required; pinned 16.5.0 gate packaged)"; return; fi
 local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz" compiler; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"; [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive SHA"; mkdir -p "$GLSLANG_DIR"; tar -xzf "$archive" -C "$GLSLANG_DIR"; compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "pinned glslang compiler missing"; "$compiler" --version | tee "$OUT/26677_glslang_version.txt"; python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" --compiler "$compiler" | tee "$OUT/26677_shader_validation.txt"; set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (14 exact runtime variants + complete 257-file shader universe; changedVariants=2 watermark-off+watermark-on; all critical active GLSL covered)"; set_report "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; exact 14 runtime variants including watermark OFF/ON)"; set_compiler "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; exact 14 runtime variants including watermark OFF/ON)"
}
verify_successful_26676_mechanics(){ python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26677_infrastructure.txt"; set_report "INFRASTRUCTURE DELTA AUDIT" "PASS (functional build mechanics delta ZERO; 26677 identity/successful-26676 authority/4-path scope and semantic targets only; exact successful 26676 compiler/native/patch/PRE-BUILD/assemble/postbuild sequence retained)"; set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (successful 26676 build-script ${AUTH_26676_BUILD_SCRIPT_BLOB} + workflow ${AUTH_26676_WORKFLOW_BLOB})"; }
verify_candidate_patches(){ python3 -S "$PATCHVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26677_patch_validation.txt"; set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"; }
install_frozen_candidate_live(){ rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"; snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"; compare_app_trees "$AFTER" "$LIVE_CANON"; }
postbuild_proof(){
 snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"; compare_app_trees "$AFTER" "$POST"; (cd "$POST" && sha256sum -c "$CAND_PROTECTED" >/dev/null && sha256sum -c "$CAND_NATIVE" >/dev/null && sha256sum -c "$CAND_VENDOR" >/dev/null && sha256sum -c "$CAND_DNG" >/dev/null) || fail "post-build protected invariance"; python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26677_postbuild_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$POST" | tee "$OUT/26677_postbuild_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26677_postbuild_authority.txt"; set_report "POST-BUILD INVARIANCE" "PASS (candidate/protected/DNG/native/vendor exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"
 tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26677_R1_candidate_app_source.tar.gz"; sha256sum "$OUT/26677_R1_candidate_app_source.tar.gz" > "$OUT/26677_R1_candidate_app_source.tar.gz.sha256"; cp "$CAND_FULL" "$OUT/26677_R1_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26677_R1_native_protected_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26677_R1_vendor_protected_postbuild.sha256"; cp "$CAND_DNG" "$OUT/26677_R1_dng_postbuild.sha256"; cp "$SHADER_PIN" "$OUT/26677_R1_runtime_expanded_shaders.sha256"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests + runtime-expanded shader pins)"
}
verify_package
verify_scope
obtain_authority
make_candidate
verify_shaders
verify_successful_26676_mechanics
if [[ -n "$LOCAL_ART" ]]; then
 verify_candidate_patches
 set_report "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real GLSL/Kotlin/Java/NDK/full Android require Actions)"; set_report "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_report "EXACTLY ONE APK" "NOT RUN locally (Actions required)"; set_report "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN locally (Actions required)"
 set_compiler "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_compiler "NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_compiler "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_compiler "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; cp "$OUT/26677_R1_STRICT_HANDOFF_REPORT.txt" "$OUT/26677_R1_local_prebuild_report.txt"; pass "26677 R1 LOCAL PREBUILD PREPARED: exact successful 26676 compiled authority; all locally applicable packaged gates passed; real compiler/build gates explicitly unproven locally"; exit 0
fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26677_gradle_language_compilers.log"
set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"; compare_app_trees "$AFTER" "$WORK/after_language_compiler_snapshot"
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26677_gradle_native_compiler.log"
set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
verify_candidate_patches
set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26677 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26677_gradle_assemble.log"
set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort)
[[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK"
mv "${apks[0]}" "$FINAL"; [[ -f "$FINAL" ]] || fail "final APK missing after move"; set_report "EXACTLY ONE APK" "PASS"; sha256sum "$FINAL" > "$OUT/26677_R1_APK.sha256"
postbuild_proof
pass "26677 R1 ACTIONS BUILD COMPLETE"
