#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
resolve_glslang_compiler(){ local root="$1" compiler="" compat=""; compiler="$(find "$root" -type f -name glslang -print -quit)"; if [[ -z "$compiler" ]]; then compat="$(find "$root" \( -type f -o -type l \) -name glslangValidator -print -quit)"; if [[ -n "$compat" ]]; then compiler="$(readlink -f "$compat" 2>/dev/null || true)"; fi; fi; [[ -n "$compiler" && -f "$compiler" ]] || return 1; printf '%s\n' "$compiler"; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
UPLOAD_BASE_COMMIT="7fcfd4544eaed4b8bff40c64e63db4df1938fea8"
RUNTIME_AUTHORITY_COMMIT="7fcfd4544eaed4b8bff40c64e63db4df1938fea8"
BASE_RUN_ID="35898941969"
BASE_ARTIFACT_ID="10768791147"
BASE_ARTIFACT_NAME="photon-26691-r1-spektra-capture-native-histogram"
BASE_ARTIFACT_SHA="c6078cdca74763a55ba296a8b944d0d3ab2d4e937ed1af1b3cc2c5a560d06f23"
BASE_TAR_SHA="70ad48f9ca632bf2319502fefa0182a752558c183e19c14a4484cb87b0c8c2f2"
VERSION_NAME="0.9726692"; VERSION_BUILD="26692"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
MECHANICS_AUTHORITY_COMMIT="7fcfd4544eaed4b8bff40c64e63db4df1938fea8"
AUTH_26691_BUILD_SCRIPT_BLOB="d90369a024f59bda416d2cbcbf54d3296a47d36c"
AUTH_26691_WORKFLOW_BLOB="5ff663e24c9b547fae90fcb1604a58985dc3084c"
HANDOFF="$ROOT/R1_26692_HANDOFF_HASHES.sha256"; UPLOADS="$ROOT/R1_26692_UPLOAD_PATHS.txt"
BASE_FULL="$ROOT/R1_26692_BASE_26691_R1_FULL_APP.sha256"; CAND_FULL="$ROOT/R1_26692_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/R1_26692_PROTECTED_UNCHANGED_BASE.sha256"; CAND_PROTECTED="$ROOT/R1_26692_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/R1_26692_NATIVE_PROTECTED_BASE.sha256"; CAND_NATIVE="$ROOT/R1_26692_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_NATIVE_FULL="$ROOT/R1_26692_NATIVE_FULL_BASE.sha256"; CAND_NATIVE_FULL="$ROOT/R1_26692_NATIVE_FULL_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/R1_26692_VENDOR_PROTECTED_BASE.sha256"; CAND_VENDOR="$ROOT/R1_26692_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/R1_26692_DNG_BASE.sha256"; CAND_DNG="$ROOT/R1_26692_DNG_CANDIDATE.sha256"
SHADER_BASE="$ROOT/R1_26692_ASSET_SHADER_UNIVERSE_BASE.sha256"; SHADER_CAND="$ROOT/R1_26692_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256"; INHERITED_RAW_SHADER="$ROOT/R1_26692_INHERITED_RAW_SHADER.sha256"
CHANGED="$ROOT/R1_26692_RUNTIME_CHANGED_PATHS.txt"; PREWRITE="$ROOT/R1_26692_PREWRITE_SOURCE_HASHES.sha256"; EXPECTED_CHANGED="$ROOT/R1_26692_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/R1_26692_RUNTIME_DELTA_FROM_26691_R1.patch"; ROLLBACK="$ROOT/R1_26692_RUNTIME_ROLLBACK_TO_26691_R1.patch"
TRANSFORM="$ROOT/transform_26692.py"; VALIDATE="$ROOT/validate_26692.py"; AUTHORITY="$ROOT/verify_26692_authority.py"; INFRA="$ROOT/verify_26692_infrastructure.py"; PATCHVERIFY="$ROOT/verify_26692_patches.py"; GATEVERIFY="$ROOT/verify_26692_regressions.py"
BUILD_SCRIPT="$ROOT/build_26692_r1_spektra_standalone_parity_capture_ui.sh"; WORKFLOW="$ROOT/.github/workflows/build-26692-r1-spektra-standalone-parity-capture-ui.yml"
OUT="$ROOT/build_26692_r1_spektra_standalone_parity_capture_ui_outputs"; WORK="$ROOT/.build_26692_r1_spektra_standalone_parity_capture_ui_work"
ARTZIP="$WORK/26691_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_successful_26691_compiled_candidate"; AFTER="$WORK/candidate_26692"; AFTER2="$WORK/candidate_26692_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; GLSLANG_DIR="$WORK/glslang-${GLSLANG_VERSION}"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r1-spektra-standalone-parity-capture-ui-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26691 artifact ZIP"; LOCAL_ART="$2"; elif [[ -n "${1:-}" ]]; then fail "unknown argument: $1"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26692_R1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
JNI CALLBACK CLASS ABI: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
APK JNI CONTRACT: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26692_R1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME AUTHORITY: NOT RUN
VERIFICATION MECHANICS AUTHORITY: NOT RUN
BACKUP STATUS: NONE (localized Spektra capture/histogram correction; exact successful authority + deterministic rollback patch)
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE CHANGED FILES: outer 26692 workflow/build/transform/validators/handoff wrappers only; successful-26691 compiler/build ordering retained
INFRASTRUCTURE DELTA FROM LAST SUCCESS: successful 26691 mechanics/order retained exactly; build identities/scope/regressions only
26690 DEVICE CRASH REGRESSION: NOT RUN
SPEKTRA STARTUP CONTAINMENT: NOT RUN
26691 NULL-LSC CAPTURE REGRESSION: NOT RUN
26692 SPEKTRA PHOTO-STYLE HISTOGRAM: NOT RUN
SPEKTRA ACTIVE OWNER: NOT RUN
SPEKTRA 1.1.2 JNI CONTRACT: NOT RUN
26687-26690 FAILURE REGRESSIONS: NOT RUN
ASSET SHADER UNIVERSE INVARIANCE: NOT RUN
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
TARGET VERSION/BUILD: 0.9726692 / 26692
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26692_R1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26692_R1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26692_R1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26692_R1_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){ local authority_root="$1" live_root="$2" dest_root="$3"; rm -rf "$dest_root"; mkdir -p "$dest_root"; cp -a "$authority_root/." "$dest_root/"; rm -rf "$dest_root/app/src"; cp -a "$live_root/app/src" "$dest_root/app/"; cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"; cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"; }
compare_app_trees(){ python3 -S - "$1" "$2" <<'PY2'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a=H(sys.argv[1]);b=H(sys.argv[2]);assert len(a)==len(b)==1822 and a==b,(len(a),len(b),sorted(set(a)^set(b))[:10]);print('PASS authority-seeded candidate byte-identical: 1822 files')
PY2
}
verify_package(){
 [[ -f "$HANDOFF" && -f "$UPLOADS" && -d "$ROOT/handoff_payload_26692" ]] || fail "sealed 26692 package incomplete"
 [[ "$(find "$ROOT/handoff_payload_26692" -type f | wc -l)" -eq 11 ]] || fail "runtime payload must contain exactly 11 files"
 [[ "$(wc -l < "$CHANGED")" -eq 11 ]] || fail "26692 changed-file count"
 [[ "$(wc -l < "$ROOT/R1_26692_ADDED_PATHS_MUST_BE_ABSENT.txt")" -eq 0 ]] || fail "26692 added-file count"
 sha256sum -c "$HANDOFF" >/dev/null
 (cd "$ROOT" && sha256sum -c R1_26692_PAYLOAD.sha256 >/dev/null) || fail "runtime payload hash manifest"
 [[ "$(wc -l < "$BASE_FULL")" -eq 1822 && "$(wc -l < "$CAND_FULL")" -eq 1822 ]] || fail "full app count"
 [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1811 && "$(wc -l < "$BASE_NATIVE")" -eq 819 && "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$BASE_DNG")" -eq 7 && "$(wc -l < "$BASE_NATIVE_FULL")" -eq 819 && "$(wc -l < "$CAND_NATIVE_FULL")" -eq 819 ]] || fail "protected/native manifest counts"
 [[ "$(wc -l < "$SHADER_BASE")" -eq 271 && "$(wc -l < "$SHADER_CAND")" -eq 271 && "$(wc -l < "$INHERITED_RAW_SHADER")" -eq 1 ]] || fail "shader manifest counts"
 cmp "$BASE_PROTECTED" "$CAND_PROTECTED"; cmp "$BASE_NATIVE" "$CAND_NATIVE"; cmp "$BASE_NATIVE_FULL" "$CAND_NATIVE_FULL"; cmp "$BASE_VENDOR" "$CAND_VENDOR"; cmp "$BASE_DNG" "$CAND_DNG"; cmp "$SHADER_BASE" "$SHADER_CAND"
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
 if [[ -n "$LOCAL_ART" ]]; then set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed candidate: exact 11 modified paths; 0 additions/removals; successful 26691 compiled authority)"; return; fi
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
 git merge-base --is-ancestor "$UPLOAD_BASE_COMMIT" HEAD || fail "successful 26691 commit must remain ancestor"
 [[ "$(git rev-parse "${MECHANICS_AUTHORITY_COMMIT}:build_26691_r1_spektra_capture_native_histogram.sh")" == "$AUTH_26691_BUILD_SCRIPT_BLOB" ]] || fail "successful 26691 build-script blob changed"
 [[ "$(git rev-parse "${MECHANICS_AUTHORITY_COMMIT}:.github/workflows/build-26691-r1-spektra-capture-native-histogram.yml")" == "$AUTH_26691_WORKFLOW_BLOB" ]] || fail "successful 26691 workflow blob changed"
 git diff --name-only "$UPLOAD_BASE_COMMIT"..HEAD | sort > "$WORK/actual_upload_scope.txt"; sort "$UPLOADS" > "$WORK/expected_upload_scope.txt"; diff -u "$WORK/expected_upload_scope.txt" "$WORK/actual_upload_scope.txt" || fail "26692 upload scope mismatch"
 ! grep -Eq '^app/' "$WORK/actual_upload_scope.txt" || fail "handoff commit contains live app source"
 set_report "CHANGED RUNTIME SCOPE" "PASS (11 runtime paths carried only inside sealed payload; live app source not committed)"
}
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
 [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "successful 26691 artifact ZIP SHA"
 unzip -q "$ARTZIP" -d "$ARTDIR"; local tarball="$ARTDIR/build_26691_r1_spektra_capture_native_histogram_outputs/26691_R1_candidate_app_source.tar.gz"
 [[ -f "$tarball" && "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "successful 26691 compiled candidate TAR authority"
 tar -xzf "$tarball" -C "$BASE"; (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null) || fail "exact successful 26691 base manifest"
 set_report "RUNTIME AUTHORITY" "PASS (successful 26691 commit ${RUNTIME_AUTHORITY_COMMIT}/run ${BASE_RUN_ID}/artifact ${BASE_ARTIFACT_ID}/artifact SHA ${BASE_ARTIFACT_SHA}/compiled candidate TAR ${BASE_TAR_SHA})"
}
make_candidate(){
 python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26692_transform.txt"; python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26692_transform_replay.txt"; compare_app_trees "$AFTER" "$AFTER2"
 python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26692_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$AFTER" | tee "$OUT/26692_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26692_authority_candidate.txt"
 set_report "26690 DEVICE CRASH REGRESSION" "PASS (exact 1.1.2 JNI_OnLoad InternalLogRecorder/recordNative descriptor restored; final APK presence also checked after assemble)"
 set_report "SPEKTRA STARTUP CONTAINMENT" "PASS (ordinary Iris construction/surface binding cannot instantiate RawVulkanPreviewController or load VulkanRenderer native library)"
 set_report "26691 NULL-LSC CAPTURE REGRESSION" "PASS (inherited 26691: preview LSC optional; still metadata preferred, same-route preview fallback, NONE allowed)"
 set_report "26692 SPEKTRA PHOTO-STYLE HISTOGRAM" "PASS (native Spektra sample source reduced to Photo-style 64-bin RGB curves; no toggle; ordinary Iris histogram invariant)"
 set_report "SPEKTRA ACTIVE OWNER" "PASS (RawVulkanPreviewController remains sole hosted Unspektrawesome Camera2/RAW/Vulkan owner; RAW10 preferred; RAW_SENSOR uses native row-stride carrier without AHB-import dependency)"
 set_report "SPEKTRA 1.1.2 JNI CONTRACT" "PASS (exact native .so unchanged; required InternalLogRecorder source contract present)"
 set_report "26687-26690 FAILURE REGRESSIONS" "PASS"
 set_report "ASSET SHADER UNIVERSE INVARIANCE" "PASS (271/271 inherited asset shaders byte-identical; successful-26691 compiler order retained)"
 set_report "PROTECTED/DNG/NATIVE/VENDOR INVARIANCE" "PASS"
}
verify_successful_26691_mechanics(){ python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26692_infrastructure.txt"; set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (successful 26691 build-script ${AUTH_26691_BUILD_SCRIPT_BLOB} + workflow ${AUTH_26691_WORKFLOW_BLOB}; compiler/build order retained; exact successful-26691 compiler/build order retained)"; }
prepare_glslang(){
 local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz" compiler
 curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"
 [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive SHA"
 rm -rf "$GLSLANG_DIR"; mkdir -p "$GLSLANG_DIR"; tar -xzf "$archive" -C "$GLSLANG_DIR"
 compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "pinned glslang compiler missing"
 "$compiler" --version | tee "$OUT/26692_glslang_version.txt"
 export IRIS26681_SPEKTRA_GLSLANG="$compiler"; [[ -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "pinned glslang is not executable"
}
compile_spektra_raw_shader(){
 local compiler="$IRIS26681_SPEKTRA_GLSLANG" outspv="$WORK/SpektraRawDevelop.comp.spv"
 "$compiler" -V "$AFTER/app/src/main/cpp/spektra/SpektraRawDevelop.comp" -o "$outspv" 2>&1 | tee "$OUT/26692_glslang_raw_develop.log"
 [[ -s "$outspv" ]] || fail "Spektra RAW shader SPIR-V missing"
 sha256sum "$AFTER/app/src/main/cpp/spektra/SpektraRawDevelop.comp" "$outspv" > "$OUT/26692_spektra_raw_shader_compile.sha256"
 set_report "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; inherited SpektraRawDevelop.comp; successful-26691 order retained)"; set_compiler "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; inherited SpektraRawDevelop.comp)"
}
verify_candidate_patches(){ python3 -S "$PATCHVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26692_patch_validation.txt"; set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"; }
install_frozen_candidate_live(){ rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"; snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"; compare_app_trees "$AFTER" "$LIVE_CANON"; }
verify_compiled_jni_callback(){
 local cls; cls="$(find "$ROOT/app/build" -type f -path '*/com/unspektrawesome/diagnostics/InternalLogRecorder.class' -print -quit)"
 [[ -n "$cls" && -f "$cls" ]] || fail "compiled InternalLogRecorder.class missing"
 javap -s "$cls" | tee "$OUT/26692_internal_log_recorder_javap.txt"
 grep -Fq 'public static void recordNative(int, java.lang.String, java.lang.String);' "$OUT/26692_internal_log_recorder_javap.txt" || fail "compiled recordNative method missing"
 grep -Fq 'descriptor: (ILjava/lang/String;Ljava/lang/String;)V' "$OUT/26692_internal_log_recorder_javap.txt" || fail "compiled recordNative JNI descriptor mismatch"
 set_report "JNI CALLBACK CLASS ABI" "PASS (real javac output has exact recordNative (ILjava/lang/String;Ljava/lang/String;)V descriptor)"; set_compiler "JNI CALLBACK CLASS ABI" "PASS"
}
verify_apk_jni_contract(){
 python3 -S - "$FINAL" "$OUT/26692_apk_jni_contract.txt" <<'PY2'
import hashlib,sys,zipfile
apk,out=sys.argv[1],sys.argv[2]
with zipfile.ZipFile(apk) as z:
 names=z.namelist(); dex=[n for n in names if n.startswith('classes') and n.endswith('.dex')]
 hits=[]
 for n in dex:
  data=z.read(n)
  if b'Lcom/unspektrawesome/diagnostics/InternalLogRecorder;' in data:
   hits.append((n,data))
 assert len(hits)==1, f'InternalLogRecorder DEX count={len(hits)}'
 assert b'recordNative' in hits[0][1], 'recordNative missing from InternalLogRecorder DEX'
 so_name='lib/arm64-v8a/libunspektrawesome_vulkan.so'
 assert so_name in names, 'exact Unspektrawesome arm64 library missing from APK'
 so=z.read(so_name); h=hashlib.sha256(so).hexdigest()
 assert h=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd',h
 result=f'PASS APK JNI CONTRACT: {hits[0][0]} contains InternalLogRecorder + recordNative; native SHA-256 {h}\n'
 open(out,'w').write(result); print(result,end='')
PY2
 set_report "APK JNI CONTRACT" "PASS (final APK contains InternalLogRecorder+recordNative and exact 1.1.2 arm64 native SHA)"; set_compiler "APK JNI CONTRACT" "PASS"
}
postbuild_proof(){
 snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"; compare_app_trees "$AFTER" "$POST"; (cd "$POST" && sha256sum -c "$CAND_PROTECTED" >/dev/null && sha256sum -c "$CAND_NATIVE" >/dev/null && sha256sum -c "$CAND_NATIVE_FULL" >/dev/null && sha256sum -c "$CAND_VENDOR" >/dev/null && sha256sum -c "$CAND_DNG" >/dev/null && sha256sum -c "$SHADER_CAND" >/dev/null) || fail "post-build invariance"; python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26692_postbuild_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$POST" | tee "$OUT/26692_postbuild_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26692_postbuild_authority.txt"; set_report "POST-BUILD INVARIANCE" "PASS (candidate/protected/DNG/native/vendor/inherited asset shaders exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"
 tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26692_R1_candidate_app_source.tar.gz"; sha256sum "$OUT/26692_R1_candidate_app_source.tar.gz" > "$OUT/26692_R1_candidate_app_source.tar.gz.sha256"; cp "$CAND_FULL" "$OUT/26692_R1_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26692_R1_native_protected_postbuild.sha256"; cp "$CAND_NATIVE_FULL" "$OUT/26692_R1_native_full_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26692_R1_vendor_protected_postbuild.sha256"; cp "$CAND_DNG" "$OUT/26692_R1_dng_postbuild.sha256"; cp "$SHADER_CAND" "$OUT/26692_R1_asset_shader_universe_postbuild.sha256"; cp "$INHERITED_RAW_SHADER" "$OUT/26692_R1_spektra_raw_shader_source.sha256"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests)"
}
verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_26691_mechanics
if [[ -n "$LOCAL_ART" ]]; then
 verify_candidate_patches
 set_report "REAL GLSL COMPILE" "NOT RUN locally (pinned compiler/build environment unavailable here; Actions required)"; set_report "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_report "JNI CALLBACK CLASS ABI" "NOT RUN by real project javac locally (Actions required)"; set_report "REAL NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real compiler/NDK/full Android require Actions)"; set_report "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_report "EXACTLY ONE APK" "NOT RUN locally (Actions required)"; set_report "APK JNI CONTRACT" "NOT RUN (requires final Actions APK)"; set_report "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN locally (Actions required)"
 set_compiler "REAL GLSL COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_compiler "JNI CALLBACK CLASS ABI" "NOT RUN by real project javac locally (Actions required)"; set_compiler "NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_compiler "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_compiler "APK JNI CONTRACT" "NOT RUN locally (Actions required)"; set_compiler "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; cp "$OUT/26692_R1_STRICT_HANDOFF_REPORT.txt" "$OUT/26692_R1_local_prebuild_report.txt"; pass "26692 R1 LOCAL PREBUILD PREPARED: exact successful 26691 compiled authority; successful-26691 mechanics retained exactly; all locally available gates passed; real compiler/build/APK gates explicitly unproven locally"; exit 0
fi
prepare_glslang
compile_spektra_raw_shader
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26692_gradle_language_compilers.log"
set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
verify_compiled_jni_callback
snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"; compare_app_trees "$AFTER" "$WORK/after_language_compiler_snapshot"
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26692_gradle_native_compiler.log"
set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs; successful-26691 native/compiler ordering retained)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
verify_candidate_patches
set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26692 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26692_gradle_assemble.log"
set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort)
[[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK"
mv "${apks[0]}" "$FINAL"; [[ -f "$FINAL" ]] || fail "final APK missing after move"; set_report "EXACTLY ONE APK" "PASS"; sha256sum "$FINAL" > "$OUT/26692_R1_APK.sha256"
verify_apk_jni_contract
postbuild_proof
pass "26692 R1 ACTIONS BUILD COMPLETE"
