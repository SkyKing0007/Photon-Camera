#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
resolve_glslang_compiler(){ local root="$1" compiler="" compat=""; compiler="$(find "$root" -type f -name glslang -print -quit)"; if [[ -z "$compiler" ]]; then compat="$(find "$root" \( -type f -o -type l \) -name glslangValidator -print -quit)"; if [[ -n "$compat" ]]; then compiler="$(readlink -f "$compat" 2>/dev/null || true)"; fi; fi; [[ -n "$compiler" && -f "$compiler" ]] || return 1; printf '%s\n' "$compiler"; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
UPLOAD_BASE_COMMIT="ce1ebd051bc8708733afb8bba75909eb12138824"
RUNTIME_AUTHORITY_COMMIT="ce1ebd051bc8708733afb8bba75909eb12138824"
BASE_RUN_ID="35926194546"
BASE_ARTIFACT_ID="10779656771"
BASE_ARTIFACT_NAME="photon-26693-global-ui-spektra-lifecycle"
BASE_ARTIFACT_SHA="a5c4d67a04a8ca442eaf81786e81041a85c8dd4bcbe42bbf52ff9703f22b5fa1"
BASE_TAR_SHA="3b67997d17a02093053ce7be78128f72f39a6f666b267a54e05b507b62bd5c68"
VERSION_NAME="0.9726694"; VERSION_BUILD="26694"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
MECHANICS_AUTHORITY_COMMIT="ce1ebd051bc8708733afb8bba75909eb12138824"
AUTH_26693_BUILD_SCRIPT_BLOB="51c0145a150d59bd2dfdd83a26b6ea4cec281202"
AUTH_26693_WORKFLOW_BLOB="b81f1586da46bc8263b98d275436983d956c7927"
AUTH_26691_BUILD_SCRIPT_BLOB="d90369a024f59bda416d2cbcbf54d3296a47d36c"
AUTH_26691_WORKFLOW_BLOB="5ff663e24c9b547fae90fcb1604a58985dc3084c"
HANDOFF="$ROOT/26694_HANDOFF_HASHES.sha256"; UPLOADS="$ROOT/26694_UPLOAD_PATHS.txt"
BASE_FULL="$ROOT/26694_BASE_26693_FULL_APP.sha256"; CAND_FULL="$ROOT/26694_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/26694_PROTECTED_UNCHANGED_BASE.sha256"; CAND_PROTECTED="$ROOT/26694_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/26694_NATIVE_PROTECTED_BASE.sha256"; CAND_NATIVE="$ROOT/26694_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_NATIVE_FULL="$ROOT/26694_NATIVE_FULL_BASE.sha256"; CAND_NATIVE_FULL="$ROOT/26694_NATIVE_FULL_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/26694_VENDOR_PROTECTED_BASE.sha256"; CAND_VENDOR="$ROOT/26694_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/26694_DNG_BASE.sha256"; CAND_DNG="$ROOT/26694_DNG_CANDIDATE.sha256"
SHADER_BASE="$ROOT/26694_ASSET_SHADER_UNIVERSE_BASE.sha256"; SHADER_CAND="$ROOT/26694_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256"
CHANGED="$ROOT/26694_RUNTIME_CHANGED_PATHS.txt"; PREWRITE="$ROOT/26694_PREWRITE_SOURCE_HASHES.sha256"; EXPECTED_CHANGED="$ROOT/26694_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/26694_RUNTIME_DELTA_FROM_26693.patch"; ROLLBACK="$ROOT/26694_RUNTIME_ROLLBACK_TO_26693.patch"
TRANSFORM="$ROOT/transform_26694.py"; VALIDATE="$ROOT/validate_26694.py"; AUTHORITY="$ROOT/repair_26694_authority.py"; INFRA="$ROOT/repair_26694_infrastructure.py"; PATCHVERIFY="$ROOT/repair_26694_patches.py"; GATEVERIFY="$ROOT/repair_26694_regressions.py"
BUILD_SCRIPT="$ROOT/build_26694_spektra_integration_fix.sh"; WORKFLOW="$ROOT/.github/workflows/build-26694-spektra-integration-fix.yml"
OUT="$ROOT/build_26694_spektra_integration_fix_outputs"; WORK="$ROOT/.build_26694_spektra_integration_fix_work"
ARTZIP="$WORK/26693_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_successful_26693_compiled_candidate"; AFTER="$WORK/candidate_26694"; AFTER2="$WORK/candidate_26694_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; GLSLANG_DIR="$WORK/glslang-${GLSLANG_VERSION}"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-spektra-integration-fix-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""; LOCAL_ONLY=0
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26693 artifact ZIP"; LOCAL_ART="$2"; LOCAL_ONLY=1; elif [[ -n "${1:-}" ]]; then fail "unknown argument: $1"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26694_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
JNI CALLBACK CLASS ABI: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
APK JNI CONTRACT: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26694_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME AUTHORITY: NOT RUN
VERIFICATION MECHANICS AUTHORITY: NOT RUN
BACKUP STATUS: NONE (user explicitly requested no backup; exact 26693 authority + deterministic rollback patch)
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE CHANGED FILES: new 26694 identity/scope/regression/build/workflow/handoff wrappers only; successful 26693 / inherited 26691 compiler-build mechanics preserved
INFRASTRUCTURE DELTA FROM LAST SUCCESS: identity/scope/regression assertions only; compiler/build stage ordering unchanged
RUNTIME OWNERSHIP: NOT RUN
DORMANT-OWNER REJECTION: NOT RUN
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
26692 R1 RAWFORMAT IMPORT REGRESSION: NOT RUN
SPEKTRA CENTERED SENSOR AE METER: NOT RUN
SPEKTRA DCIM/CAMERA PUBLICATION: NOT RUN
SPEKTRA CAPTURE/PROCESSING UI BRIDGE: NOT RUN
SPEKTRA GALLERY URI BRIDGE: NOT RUN
SPEKTRA 1.1.2 NATIVE INVARIANCE: NOT RUN
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
TARGET VERSION/BUILD: 0.9726694 / 26694
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26694_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26694_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26694_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26694_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){ local authority_root="$1" live_root="$2" dest_root="$3"; rm -rf "$dest_root"; mkdir -p "$dest_root"; cp -a "$authority_root/." "$dest_root/"; rm -rf "$dest_root/app/src"; cp -a "$live_root/app/src" "$dest_root/app/"; cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"; cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"; }
compare_app_trees(){ python3 -S - "$1" "$2" <<'PY2'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a=H(sys.argv[1]);b=H(sys.argv[2]);assert len(a)==len(b)==1822 and a==b,(len(a),len(b),sorted(set(a)^set(b))[:10]);print('PASS authority-seeded candidate byte-identical: 1822 files')
PY2
}
verify_package(){
 [[ -f "$HANDOFF" && -f "$UPLOADS" && -d "$ROOT/handoff_payload_26694" ]] || fail "sealed 26694 package incomplete"
 [[ "$(find "$ROOT/handoff_payload_26694" -type f | wc -l)" -eq 7 ]] || fail "runtime payload must contain exactly 7 files"
 [[ "$(wc -l < "$CHANGED")" -eq 7 ]] || fail "26694 changed-file count"
 [[ "$(wc -l < "$ROOT/26694_ADDED_PATHS_MUST_BE_ABSENT.txt")" -eq 0 ]] || fail "26694 added-file count"
 sha256sum -c "$HANDOFF" >/dev/null
 [[ "$(wc -l < "$BASE_FULL")" -eq 1822 && "$(wc -l < "$CAND_FULL")" -eq 1822 ]] || fail "full app count"
 [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1815 && "$(wc -l < "$BASE_NATIVE")" -eq 819 && "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$BASE_DNG")" -eq 7 ]] || fail "protected/native/vendor/DNG counts"
 [[ "$(wc -l < "$SHADER_BASE")" -eq 271 && "$(wc -l < "$SHADER_CAND")" -eq 271 ]] || fail "shader universe count"
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
 if [[ "$LOCAL_ONLY" -eq 1 ]]; then set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed candidate: exact 7 modified paths; 0 additions/removals; successful 26693 compiled authority)"; return; fi
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
 git merge-base --is-ancestor "$UPLOAD_BASE_COMMIT" HEAD || fail "successful 26693 activation commit not ancestor"
 [[ "$(git rev-parse "${MECHANICS_AUTHORITY_COMMIT}:build_26693_global_ui_spektra_lifecycle.sh")" == "$AUTH_26693_BUILD_SCRIPT_BLOB" ]] || fail "successful 26692 build-script blob changed"
 [[ "$(git rev-parse "${MECHANICS_AUTHORITY_COMMIT}:.github/workflows/build-26693-global-ui-spektra-lifecycle.yml")" == "$AUTH_26693_WORKFLOW_BLOB" ]] || fail "successful 26692 workflow blob changed"
 git diff --name-only "$UPLOAD_BASE_COMMIT"..HEAD | sort > "$WORK/actual_upload_scope.txt"; sort "$UPLOADS" > "$WORK/expected_upload_scope.txt"; diff -u "$WORK/expected_upload_scope.txt" "$WORK/actual_upload_scope.txt" || fail "26694 upload scope mismatch"
 ! grep -Eq '^app/' "$WORK/actual_upload_scope.txt" || fail "handoff commit contains live app source"
 set_report "CHANGED RUNTIME SCOPE" "PASS (7 runtime paths carried only inside sealed payload; live app source not committed)"
}
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
 [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "successful 26693 artifact ZIP SHA"
 unzip -q "$ARTZIP" -d "$ARTDIR"; local tarball="$ARTDIR/build_26693_global_ui_spektra_lifecycle_outputs/26693_candidate_app_source.tar.gz"
 [[ -f "$tarball" && "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "successful 26693 compiled candidate TAR authority"
 tar -xzf "$tarball" -C "$BASE"; (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null) || fail "exact successful 26693 base manifest"
 set_report "RUNTIME AUTHORITY" "PASS (successful 26693 commit ${RUNTIME_AUTHORITY_COMMIT}/run ${BASE_RUN_ID}/artifact ${BASE_ARTIFACT_ID}/artifact SHA ${BASE_ARTIFACT_SHA}/compiled candidate TAR ${BASE_TAR_SHA})"
 set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS"
}
make_candidate(){
 python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26694_transform.txt"; python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26694_transform_replay.txt"; compare_app_trees "$AFTER" "$AFTER2"
 python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26694_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$AFTER" | tee "$OUT/26694_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26694_authority_candidate.txt"
 set_report "RUNTIME OWNERSHIP" "PASS (Unspektrawesome owns sensor AE/RAW/RCD/save; Iris owns only capture UI/gallery presentation)"
 set_report "DORMANT-OWNER REJECTION" "PASS (26693 histogram worker remains absent; fixed UI geometry remains protected; dormant Spektra owner remains rejected)"
 set_report "26692 R1 RAWFORMAT IMPORT REGRESSION" "PASS"
 set_report "SPEKTRA CENTERED SENSOR AE METER" "PASS (CenterWeighted=0 carrier configured at normalized center 0.5/0.5; no arbitrary EV owner)"
 set_report "SPEKTRA DCIM/CAMERA PUBLICATION" "PASS (single active publisher writes DCIM/Camera; gallery query already includes DCIM/Camera)"
 set_report "SPEKTRA CAPTURE/PROCESSING UI BRIDGE" "PASS (accepted RAW capture maps to Iris capture progress; RCD begins Iris processing ring; failures contained)"
 set_report "SPEKTRA GALLERY URI BRIDGE" "PASS (successful MediaStore Uri feeds Iris gallery thumbnail; stale generations rejected)"
 set_report "SPEKTRA 1.1.2 NATIVE INVARIANCE" "PASS (exact arm64 SHA f40b4707...)"
 set_report "PROTECTED/DNG/NATIVE/VENDOR INVARIANCE" "PASS"
}
verify_successful_26693_mechanics(){ python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26694_infrastructure.txt"; set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (successful 26693 build-script ${AUTH_26693_BUILD_SCRIPT_BLOB} + workflow ${AUTH_26693_WORKFLOW_BLOB}; inherited successful-26691 compiler/build order retained)"; }
prepare_glslang(){
 local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz" compiler
 curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"; [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive SHA"
 rm -rf "$GLSLANG_DIR"; mkdir -p "$GLSLANG_DIR"; tar -xzf "$archive" -C "$GLSLANG_DIR"; compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "pinned glslang compiler missing"; "$compiler" --version | tee "$OUT/26694_glslang_version.txt"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; [[ -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "pinned glslang is not executable"
}
compile_spektra_raw_shader(){ local compiler="$IRIS26681_SPEKTRA_GLSLANG" outspv="$WORK/SpektraRawDevelop.comp.spv"; "$compiler" -V "$AFTER/app/src/main/cpp/spektra/SpektraRawDevelop.comp" -o "$outspv" 2>&1 | tee "$OUT/26694_glslang_raw_develop.log"; [[ -s "$outspv" ]] || fail "Spektra RAW shader SPIR-V missing"; sha256sum "$AFTER/app/src/main/cpp/spektra/SpektraRawDevelop.comp" "$outspv" > "$OUT/26694_spektra_raw_shader_compile.sha256"; set_report "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; inherited shader; successful 26692 order retained)"; set_compiler "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; inherited SpektraRawDevelop.comp)"; }
verify_candidate_patches(){ python3 -S "$PATCHVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26694_patch_validation.txt"; set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"; }
install_frozen_candidate_live(){ rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"; snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"; compare_app_trees "$AFTER" "$LIVE_CANON"; }
verify_compiled_jni_callback(){ local cls; cls="$(find "$ROOT/app/build" -type f -path '*/com/unspektrawesome/diagnostics/InternalLogRecorder.class' -print -quit)"; [[ -n "$cls" && -f "$cls" ]] || fail "compiled InternalLogRecorder.class missing"; javap -s "$cls" | tee "$OUT/26694_internal_log_recorder_javap.txt"; grep -Fq 'public static void recordNative(int, java.lang.String, java.lang.String);' "$OUT/26694_internal_log_recorder_javap.txt" || fail "compiled recordNative method missing"; grep -Fq 'descriptor: (ILjava/lang/String;Ljava/lang/String;)V' "$OUT/26694_internal_log_recorder_javap.txt" || fail "compiled recordNative JNI descriptor mismatch"; set_report "JNI CALLBACK CLASS ABI" "PASS"; set_compiler "JNI CALLBACK CLASS ABI" "PASS"; }
verify_apk_jni_contract(){ python3 -S - "$FINAL" "$OUT/26694_apk_jni_contract.txt" <<'PY2'
import hashlib,sys,zipfile
apk,out=sys.argv[1],sys.argv[2]
with zipfile.ZipFile(apk) as z:
 names=z.namelist(); dex=[n for n in names if n.startswith('classes') and n.endswith('.dex')]; hits=[]
 for n in dex:
  data=z.read(n)
  if b'Lcom/unspektrawesome/diagnostics/InternalLogRecorder;' in data:hits.append((n,data))
 assert len(hits)==1 and b'recordNative' in hits[0][1]
 so_name='lib/arm64-v8a/libunspektrawesome_vulkan.so'; assert so_name in names; h=hashlib.sha256(z.read(so_name)).hexdigest(); assert h=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd'
 result=f'PASS APK JNI CONTRACT: {hits[0][0]} contains InternalLogRecorder + recordNative; native SHA-256 {h}\n'; open(out,'w').write(result); print(result,end='')
PY2
 set_report "APK JNI CONTRACT" "PASS"; set_compiler "APK JNI CONTRACT" "PASS"; }
postbuild_proof(){
 snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"; compare_app_trees "$AFTER" "$POST"; (cd "$POST" && sha256sum -c "$CAND_PROTECTED" >/dev/null && sha256sum -c "$CAND_NATIVE" >/dev/null && sha256sum -c "$CAND_NATIVE_FULL" >/dev/null && sha256sum -c "$CAND_VENDOR" >/dev/null && sha256sum -c "$CAND_DNG" >/dev/null && sha256sum -c "$SHADER_CAND" >/dev/null) || fail "post-build invariance"; python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26694_postbuild_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$POST" | tee "$OUT/26694_postbuild_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26694_postbuild_authority.txt"; set_report "POST-BUILD INVARIANCE" "PASS"; set_compiler "POST-BUILD INVARIANCE" "PASS"
 tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26694_candidate_app_source.tar.gz"; sha256sum "$OUT/26694_candidate_app_source.tar.gz" > "$OUT/26694_candidate_app_source.tar.gz.sha256"; cp "$CAND_FULL" "$OUT/26694_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26694_native_protected_postbuild.sha256"; cp "$CAND_NATIVE_FULL" "$OUT/26694_native_full_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26694_vendor_protected_postbuild.sha256"; cp "$CAND_DNG" "$OUT/26694_dng_postbuild.sha256"; cp "$SHADER_CAND" "$OUT/26694_asset_shader_universe_postbuild.sha256"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests)"
}
# IRIS_26694_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_26693_mechanics
if [[ -n "$LOCAL_ART" ]]; then
 verify_candidate_patches
 set_report "REAL GLSL COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_report "JNI CALLBACK CLASS ABI" "NOT RUN by real project javac locally (Actions required)"; set_report "REAL NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real compiler/NDK/full Android require Actions)"; set_report "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_report "EXACTLY ONE APK" "NOT RUN locally (Actions required)"; set_report "APK JNI CONTRACT" "NOT RUN (requires final Actions APK)"; set_report "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN locally (Actions required)"
 set_compiler "REAL GLSL COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_compiler "JNI CALLBACK CLASS ABI" "NOT RUN by real project javac locally (Actions required)"; set_compiler "NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_compiler "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_compiler "APK JNI CONTRACT" "NOT RUN locally (Actions required)"; set_compiler "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"
 cp "$OUT/26694_STRICT_HANDOFF_REPORT.txt" "$OUT/26694_local_prebuild_report.txt"
 pass "26694 LOCAL PREBUILD PREPARED: exact successful 26693 compiled authority; successful 26693 / inherited 26691 mechanics retained; all locally available gates passed; real compiler/build/APK gates explicitly unproven locally"
 exit 0
fi
prepare_glslang
compile_spektra_raw_shader
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26694_gradle_language_compilers.log"
set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
verify_compiled_jni_callback
snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"; compare_app_trees "$AFTER" "$WORK/after_language_compiler_snapshot"
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26694_gradle_native_compiler.log"
set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs; successful-26692 native/compiler ordering retained)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
verify_candidate_patches
set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26694 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26694_gradle_assemble.log"
set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort)
[[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK"
mv "${apks[0]}" "$FINAL"; [[ -f "$FINAL" ]] || fail "final APK missing after move"; set_report "EXACTLY ONE APK" "PASS"; sha256sum "$FINAL" > "$OUT/26694_APK.sha256"
verify_apk_jni_contract
postbuild_proof
pass "26694 ACTIONS BUILD COMPLETE"
