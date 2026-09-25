#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
resolve_glslang_compiler(){ local root="$1" compiler="" compat=""; compiler="$(find "$root" -type f -name glslang -print -quit)"; if [[ -z "$compiler" ]]; then compat="$(find "$root" \( -type f -o -type l \) -name glslangValidator -print -quit)"; if [[ -n "$compat" ]]; then compiler="$(readlink -f "$compat" 2>/dev/null || true)"; fi; fi; [[ -n "$compiler" && -f "$compiler" ]] || return 1; printf '%s\n' "$compiler"; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
UPLOAD_BASE_COMMIT="fdc1a06a0fe252de84f0dfde3593927e7c9a428a"
RUNTIME_AUTHORITY_COMMIT="fdc1a06a0fe252de84f0dfde3593927e7c9a428a"
BASE_RUN_ID="36088833926"
BASE_ARTIFACT_ID="10845117229"
BASE_ARTIFACT_NAME="photon-26701-highlight-orientation-gainmap"
BASE_ARTIFACT_SHA="b83ff245ee439d0b40e90b3b7fcb557e63a9a0cbb8bca57ec4f295140227375e"
BASE_TAR_SHA="cfe219ac6ced5635768dc276125b5d57221fc19d3f1f43d2e76a0a327a0fc6bd"
VERSION_NAME="0.9726702"; VERSION_BUILD="26702"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
MECHANICS_AUTHORITY_COMMIT="fdc1a06a0fe252de84f0dfde3593927e7c9a428a"
AUTH_26701_BUILD_SCRIPT_BLOB="c8c0ce0fea4e3b5b7addd7b7212f4b96946b7a04"
AUTH_26701_WORKFLOW_BLOB="84f0c35d972e2d37dc951c4ca9bfdd2a9ec6527b"
HANDOFF="$ROOT/26702_HANDOFF_HASHES.sha256"; UPLOADS="$ROOT/26702_UPLOAD_PATHS.txt"
BASE_FULL="$ROOT/26702_BASE_26701_FULL_APP.sha256"; CAND_FULL="$ROOT/26702_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/26702_PROTECTED_UNCHANGED_BASE.sha256"; CAND_PROTECTED="$ROOT/26702_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/26702_NATIVE_PROTECTED_BASE.sha256"; CAND_NATIVE="$ROOT/26702_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_NATIVE_FULL="$ROOT/26702_NATIVE_FULL_BASE.sha256"; CAND_NATIVE_FULL="$ROOT/26702_NATIVE_FULL_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/26702_VENDOR_PROTECTED_BASE.sha256"; CAND_VENDOR="$ROOT/26702_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/26702_DNG_BASE.sha256"; CAND_DNG="$ROOT/26702_DNG_CANDIDATE.sha256"
SHADER_BASE="$ROOT/26702_ASSET_SHADER_UNIVERSE_BASE.sha256"; SHADER_CAND="$ROOT/26702_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256"
CHANGED="$ROOT/26702_RUNTIME_CHANGED_PATHS.txt"; ADDED="$ROOT/26702_ADDED_PATHS_MUST_BE_ABSENT.txt"; PREWRITE="$ROOT/26702_PREWRITE_26701_SOURCE_HASHES.sha256"; EXPECTED_CHANGED="$ROOT/26702_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/26702_RUNTIME_DELTA_FROM_26701.patch"; ROLLBACK="$ROOT/26702_RUNTIME_ROLLBACK_TO_26701.patch"
TRANSFORM="$ROOT/transform_26702.py"; VALIDATE="$ROOT/validate_26702.py"; AUTHORITY="$ROOT/verify_26702_authority.py"; INFRA="$ROOT/verify_26702_infrastructure.py"; PATCHVERIFY="$ROOT/verify_26702_patches.py"; GATEVERIFY="$ROOT/verify_26702_regressions.py"
BUILD_SCRIPT="$ROOT/build_26702_laplacian_ab_spektra_orientation.sh"; WORKFLOW="$ROOT/.github/workflows/build-26702-laplacian-ab-spektra-orientation.yml"
OUT="$ROOT/build_26702_laplacian_ab_spektra_orientation_outputs"; WORK="$ROOT/.build_26702_laplacian_ab_spektra_orientation_work"
ARTZIP="$WORK/26701_artifact.zip"; ARTDIR="$WORK/artifact_26701"; BASE="$WORK/exact_successful_26701_compiled_candidate"; AFTER="$WORK/candidate_26702"; AFTER2="$WORK/candidate_26702_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; GLSLANG_DIR="$WORK/glslang-${GLSLANG_VERSION}"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-laplacian-ab-spektra-orientation-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""; LOCAL_ONLY=0
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26701 artifact ZIP"; LOCAL_ART="$2"; LOCAL_ONLY=1; elif [[ -n "${1:-}" ]]; then fail "unknown argument: $1"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26702_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
JNI CALLBACK CLASS ABI: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
APK JNI CONTRACT: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26702_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME AUTHORITY: NOT RUN
VERIFICATION MECHANICS AUTHORITY: NOT RUN
BACKUP STATUS: NONE (user explicitly requested no backup; exact successful 26701 authority + deterministic rollback patch)
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE CHANGED FILES: 26702 identity/authority/scope/regression/build/workflow/handoff wrappers only; successful 26701 compiler-build mechanics preserved
INFRASTRUCTURE DELTA FROM LAST SUCCESS: successful 26701 mechanics retained exactly in ordering; only 26702 identity/authority/scope/native-contract/regression wrappers adapted
RUNTIME OWNERSHIP: NOT RUN
MOTION HIGHLIGHT/STABILITY PRESERVATION: NOT RUN
LOCAL LAPLACIAN A/B CONTRACT: NOT RUN
UHDR/TRUE2X FALLBACK PARITY: NOT RUN
SPEKTRA ACTIVE ORIENTATION: NOT RUN
THERMAL OBSERVER CONTRACT: NOT RUN
GAINMAP 26701 PRESERVATION: NOT RUN
NATIVE DELTA CONTRACT: NOT RUN
INHERITED 26701 CONTRACTS: NOT RUN
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
PROTECTED/DNG/NATIVE/VENDOR INVARIANCE: NOT RUN
REAL GLSL COMPILE: NOT RUN
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
JNI CALLBACK CLASS ABI: NOT RUN
REAL NATIVE/NDK COMPILE: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
PRE-BUILD SAFETY PROOF: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
EXACTLY ONE APK: NOT RUN
APK JNI CONTRACT: NOT RUN
POST-BUILD INVARIANCE: NOT RUN
CLEAN ARTIFACT SOURCE EXPORT: NOT RUN
TARGET VERSION/BUILD: 0.9726702 / 26702
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26702_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26702_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26702_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26702_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){ local authority_root="$1" live_root="$2" dest_root="$3"; rm -rf "$dest_root"; mkdir -p "$dest_root"; cp -a "$authority_root/." "$dest_root/"; rm -rf "$dest_root/app/src"; cp -a "$live_root/app/src" "$dest_root/app/"; cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"; cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"; }
compare_app_trees(){ python3 -S - "$1" "$2" <<'PY2'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a=H(sys.argv[1]);b=H(sys.argv[2]);assert len(a)==len(b)==1823 and a==b,(len(a),len(b),sorted(set(a)^set(b))[:10]);print('PASS authority-seeded candidate byte-identical: 1823 files')
PY2
}
verify_package(){
 [[ -f "$HANDOFF" && -f "$UPLOADS" && -d "$ROOT/handoff_payload_26702" ]] || fail "sealed 26702 package incomplete"
 [[ "$(find "$ROOT/handoff_payload_26702" -type f | wc -l)" -eq 15 ]] || fail "runtime payload must contain exactly 15 files"
 [[ "$(wc -l < "$CHANGED")" -eq 15 ]] || fail "26702 changed-file count"
 [[ ! -s "$ADDED" ]] || fail "26702 added-file count"
 sha256sum -c "$HANDOFF" >/dev/null
 [[ "$(wc -l < "$BASE_FULL")" -eq 1823 && "$(wc -l < "$CAND_FULL")" -eq 1823 ]] || fail "full app count"
 [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1808 && "$(wc -l < "$BASE_NATIVE")" -eq 818 && "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$BASE_DNG")" -eq 7 ]] || fail "protected/native/vendor/DNG counts"
 [[ "$(wc -l < "$SHADER_BASE")" -eq 271 && "$(wc -l < "$SHADER_CAND")" -eq 271 ]] || fail "shader universe count"
 cmp "$BASE_PROTECTED" "$CAND_PROTECTED"; cmp "$BASE_NATIVE" "$CAND_NATIVE"; [[ "$(wc -l < "$BASE_NATIVE_FULL")" -eq 819 && "$(wc -l < "$CAND_NATIVE_FULL")" -eq 819 ]] || fail "native-full count"; ! cmp -s "$BASE_NATIVE_FULL" "$CAND_NATIVE_FULL" || fail "26702 requires exactly one intentional native source delta"; cmp "$BASE_VENDOR" "$CAND_VENDOR"; cmp "$BASE_DNG" "$CAND_DNG"; cmp "$SHADER_BASE" "$SHADER_CAND"
 bash -n "$BUILD_SCRIPT"
 python3 -S - "$TRANSFORM" "$VALIDATE" "$AUTHORITY" "$INFRA" "$PATCHVERIFY" "$GATEVERIFY" <<'PY2'
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
 if bad:raise SystemExit(f'FAIL non-stdlib dependency {p.name}: {sorted(set(bad))}')
 compile(src,str(p),'exec')
print('PASS sealed Python stdlib-only syntax/import gate')
PY2
 ! find "$ROOT" \( -type d -name '__pycache__' -o -type f -name '*.pyc' \) | grep -q . || fail "transient Python files packaged"
}
verify_scope(){
 if [[ "$LOCAL_ONLY" -eq 1 ]]; then set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed candidate: exact 15 modified paths; 0 additions/removals; exact successful 26701 compiled authority)"; return; fi
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
 git merge-base --is-ancestor "$UPLOAD_BASE_COMMIT" HEAD || fail "successful 26701 activation commit not ancestor"
 [[ "$(git rev-parse "${MECHANICS_AUTHORITY_COMMIT}:build_26701_highlight_orientation_gainmap.sh")" == "$AUTH_26701_BUILD_SCRIPT_BLOB" ]] || fail "successful 26701 build-script blob changed"
 [[ "$(git rev-parse "${MECHANICS_AUTHORITY_COMMIT}:.github/workflows/build-26701-highlight-orientation-gainmap.yml")" == "$AUTH_26701_WORKFLOW_BLOB" ]] || fail "successful 26701 workflow blob changed"
 git diff --name-only "$UPLOAD_BASE_COMMIT"..HEAD | sort > "$WORK/actual_upload_scope.txt"; sort "$UPLOADS" > "$WORK/expected_upload_scope.txt"; diff -u "$WORK/expected_upload_scope.txt" "$WORK/actual_upload_scope.txt" || fail "26702 upload scope mismatch"
 ! grep -Eq '^app/' "$WORK/actual_upload_scope.txt" || fail "handoff commit contains live app source"
 set_report "CHANGED RUNTIME SCOPE" "PASS (15 runtime paths carried only inside sealed payload; live app source not committed)"
}
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else
  [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
  curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
 fi
 [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "successful 26701 artifact ZIP SHA"
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local tarball="$ARTDIR/build_26701_highlight_orientation_gainmap_outputs/26701_candidate_app_source.tar.gz"
 [[ -f "$tarball" && "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "successful 26701 compiled candidate TAR authority"
 tar -xzf "$tarball" -C "$BASE"
 (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null) || fail "exact successful 26701 base manifest"
 set_report "RUNTIME AUTHORITY" "PASS (successful 26701 commit ${RUNTIME_AUTHORITY_COMMIT}/run ${BASE_RUN_ID}/artifact ${BASE_ARTIFACT_ID}/artifact SHA ${BASE_ARTIFACT_SHA}/compiled candidate TAR ${BASE_TAR_SHA})"
 set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (successful 26701 compiled candidate is sole runtime authority)"
}
make_candidate(){
 python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26702_transform.txt"; python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26702_transform_replay.txt"; compare_app_trees "$AFTER" "$AFTER2"
 python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26702_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$AFTER" | tee "$OUT/26702_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26702_authority_candidate.txt"
 set_report "RUNTIME OWNERSHIP" "PASS (exact successful 26701 candidate inherited; active Spektra still orientation + shutter-frozen Laplacian A/B + explicit true2x fallback + version only)"
 set_report "MOTION HIGHLIGHT/STABILITY PRESERVATION" "PASS (26701 bounded RAW highlight protection, 26680 physical-reframe AE/AWB latch, observer-only flicker, and shutter/session recovery preserved)"
 set_report "LOCAL LAPLACIAN A/B CONTRACT" "PASS (default ON is exact 26701 builder behavior; OFF skips primary and source-preservation pyramids and selects existing global monotonic tone fallback)"
 set_report "UHDR/TRUE2X FALLBACK PARITY" "PASS (UHDR/render shaders byte-identical; OFF uses existing global tone; true2x JNI requires map when ON and rejects stale map when OFF while retaining Motion HDR handoff)"
 set_report "SPEKTRA ACTIVE ORIENTATION" "PASS (active RawVulkanPreviewController saved still freezes Motion Gravity rotation; live preview remains display-based; dormant 26701 owner neutralized)"
 set_report "THERMAL OBSERVER CONTRACT" "PASS (render begin/end PowerManager thermal status + battery temperature only; no glFinish/readback/probe added)"
 set_report "GAINMAP 26701 PRESERVATION" "PASS (26701 byte-array/LUT gain-map optimization and all gain-map shaders/math are byte-identical)"
 set_report "NATIVE DELTA CONTRACT" "PASS (exactly one native source delta: motionv2_jpeg444_jni.cpp; other 818 native files invariant)"
 set_report "INHERITED 26701 CONTRACTS" "PASS (RGBA32F carrier/release, Sabre, denoise, color, JPEG 4:4:4, HEIC, DNG, UHDR math and frame roles protected outside explicit scope)"
 set_report "PROTECTED/DNG/NATIVE/VENDOR INVARIANCE" "PASS (1808 protected; 818 native-protected; 778 vendor; 7 DNG; 271 shaders invariant)"
}
verify_successful_26701_mechanics(){ python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26702_infrastructure.txt"; set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (exact successful 26701 build-script ${AUTH_26701_BUILD_SCRIPT_BLOB} + workflow ${AUTH_26701_WORKFLOW_BLOB}; compiler/build stage order unchanged)"; }
prepare_glslang(){
 local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz" compiler
 curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"; [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive SHA"
 rm -rf "$GLSLANG_DIR"; mkdir -p "$GLSLANG_DIR"; tar -xzf "$archive" -C "$GLSLANG_DIR"; compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "pinned glslang compiler missing"; "$compiler" --version | tee "$OUT/26702_glslang_version.txt"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; [[ -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "pinned glslang is not executable"
}
compile_spektra_raw_shader(){ local compiler="$IRIS26681_SPEKTRA_GLSLANG" outspv="$WORK/SpektraRawDevelop.comp.spv"; "$compiler" -V "$AFTER/app/src/main/cpp/spektra/SpektraRawDevelop.comp" -o "$outspv" 2>&1 | tee "$OUT/26702_glslang_raw_develop.log"; [[ -s "$outspv" ]] || fail "Spektra RAW shader SPIR-V missing"; sha256sum "$AFTER/app/src/main/cpp/spektra/SpektraRawDevelop.comp" "$outspv" > "$OUT/26702_spektra_raw_shader_compile.sha256"; set_report "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; inherited shader; successful 26701 order retained)"; set_compiler "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; inherited SpektraRawDevelop.comp)"; }
verify_candidate_patches(){ python3 -S "$PATCHVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26702_patch_validation.txt"; set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"; }
install_frozen_candidate_live(){ rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"; snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"; compare_app_trees "$AFTER" "$LIVE_CANON"; }
verify_compiled_jni_callback(){ local cls; cls="$(find "$ROOT/app/build" -type f -path '*/com/unspektrawesome/diagnostics/InternalLogRecorder.class' -print -quit)"; [[ -n "$cls" && -f "$cls" ]] || fail "compiled InternalLogRecorder.class missing"; javap -s "$cls" | tee "$OUT/26702_internal_log_recorder_javap.txt"; grep -Fq 'public static void recordNative(int, java.lang.String, java.lang.String);' "$OUT/26702_internal_log_recorder_javap.txt" || fail "compiled recordNative method missing"; grep -Fq 'descriptor: (ILjava/lang/String;Ljava/lang/String;)V' "$OUT/26702_internal_log_recorder_javap.txt" || fail "compiled recordNative JNI descriptor mismatch"; set_report "JNI CALLBACK CLASS ABI" "PASS"; set_compiler "JNI CALLBACK CLASS ABI" "PASS"; }

verify_compiled_motion_jni(){ local cls; cls="$(find "$ROOT/app/build" -type f -path '*/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.class' -print -quit)"; [[ -n "$cls" && -f "$cls" ]] || fail "compiled MotionV2Jpeg444Encoder.class missing"; javap -s -private "$cls" | tee "$OUT/26702_motionv2_encoder_javap.txt"; grep -Fq 'writeTrue2xNative' "$OUT/26702_motionv2_encoder_javap.txt" || fail "compiled writeTrue2xNative missing"; grep -Fq 'localToneEnabled' "$AFTER/app/src/main/cpp/motionv2_jpeg444_jni.cpp" || fail "native localToneEnabled contract missing"; set_report "NATIVE DELTA CONTRACT" "PASS (Java native declaration compiled; C++ explicit localToneEnabled contract present; NDK compile follows in inherited order)"; }
verify_apk_jni_contract(){ python3 -S - "$FINAL" "$OUT/26702_apk_jni_contract.txt" <<'PY2'
import hashlib,sys,zipfile
apk,out=sys.argv[1],sys.argv[2]
with zipfile.ZipFile(apk) as z:
 names=z.namelist(); dex=[n for n in names if n.startswith('classes') and n.endswith('.dex')]; hits=[]
 for n in dex:
  data=z.read(n)
  if b'Lcom/unspektrawesome/diagnostics/InternalLogRecorder;' in data:hits.append((n,data))
 assert len(hits)==1 and b'recordNative' in hits[0][1]
 so_name='lib/arm64-v8a/libunspektrawesome_vulkan.so'; assert so_name in names; h=hashlib.sha256(z.read(so_name)).hexdigest(); assert h=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd'; motion='lib/arm64-v8a/libmotionv2jpeg.so'; assert motion in names; md=z.read(motion); assert b'Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_writeTrue2xNative' in md
 result=f'PASS APK JNI CONTRACT: {hits[0][0]} contains InternalLogRecorder + recordNative; Spektra native SHA-256 {h}; MotionV2 writeTrue2x JNI symbol present\n'; open(out,'w').write(result); print(result,end='')
PY2
 set_report "APK JNI CONTRACT" "PASS"; set_compiler "APK JNI CONTRACT" "PASS"; }
postbuild_proof(){
 snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"; compare_app_trees "$AFTER" "$POST"; (cd "$POST" && sha256sum -c "$CAND_PROTECTED" >/dev/null && sha256sum -c "$CAND_NATIVE" >/dev/null && sha256sum -c "$CAND_NATIVE_FULL" >/dev/null && sha256sum -c "$CAND_VENDOR" >/dev/null && sha256sum -c "$CAND_DNG" >/dev/null && sha256sum -c "$SHADER_CAND" >/dev/null) || fail "post-build invariance"; python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26702_postbuild_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$POST" | tee "$OUT/26702_postbuild_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26702_postbuild_authority.txt"; set_report "POST-BUILD INVARIANCE" "PASS"; set_compiler "POST-BUILD INVARIANCE" "PASS"
 tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26702_candidate_app_source.tar.gz"; sha256sum "$OUT/26702_candidate_app_source.tar.gz" > "$OUT/26702_candidate_app_source.tar.gz.sha256"; cp "$CAND_FULL" "$OUT/26702_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26702_native_protected_postbuild.sha256"; cp "$CAND_NATIVE_FULL" "$OUT/26702_native_full_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26702_vendor_protected_postbuild.sha256"; cp "$CAND_DNG" "$OUT/26702_dng_postbuild.sha256"; cp "$SHADER_CAND" "$OUT/26702_asset_shader_universe_postbuild.sha256"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests)"
}
# IRIS_26702_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_26701_mechanics
if [[ -n "$LOCAL_ART" ]]; then
 verify_candidate_patches
 set_report "REAL GLSL COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_report "JNI CALLBACK CLASS ABI" "NOT RUN by real project javac locally (Actions required)"; set_report "REAL NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real compiler/NDK/full Android require Actions)"; set_report "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_report "EXACTLY ONE APK" "NOT RUN locally (Actions required)"; set_report "APK JNI CONTRACT" "NOT RUN (requires final Actions APK)"; set_report "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN locally (Actions required)"
 set_compiler "REAL GLSL COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_compiler "JNI CALLBACK CLASS ABI" "NOT RUN by real project javac locally (Actions required)"; set_compiler "NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_compiler "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_compiler "APK JNI CONTRACT" "NOT RUN locally (Actions required)"; set_compiler "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"
 cp "$OUT/26702_STRICT_HANDOFF_REPORT.txt" "$OUT/26702_local_prebuild_report.txt"
 pass "26702 LOCAL PREBUILD PREPARED: exact successful 26701 compiled authority; exact successful 26701 mechanics retained; all locally available gates passed; real compiler/build/APK gates explicitly unproven locally"
 exit 0
fi
prepare_glslang
compile_spektra_raw_shader
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26702_gradle_language_compilers.log"
set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
verify_compiled_jni_callback
verify_compiled_motion_jni
snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"; compare_app_trees "$AFTER" "$WORK/after_language_compiler_snapshot"
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26702_gradle_native_compiler.log"
set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs; successful-26701 native/compiler ordering retained)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
verify_candidate_patches
set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26702 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26702_gradle_assemble.log"
set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort)
[[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK"
mv "${apks[0]}" "$FINAL"; [[ -f "$FINAL" ]] || fail "final APK missing after move"; set_report "EXACTLY ONE APK" "PASS"; sha256sum "$FINAL" > "$OUT/26702_APK.sha256"
verify_apk_jni_contract
postbuild_proof
pass "26702 ACTIONS BUILD COMPLETE"
