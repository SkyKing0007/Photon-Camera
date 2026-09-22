#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
resolve_glslang_compiler(){ local root="$1" compiler="" compat=""; compiler="$(find "$root" -type f -name glslang -print -quit)"; if [[ -z "$compiler" ]]; then compat="$(find "$root" \( -type f -o -type l \) -name glslangValidator -print -quit)"; if [[ -n "$compat" ]]; then compiler="$(readlink -f "$compat" 2>/dev/null || true)"; fi; fi; [[ -n "$compiler" && -f "$compiler" ]] || return 1; printf '%s\n' "$compiler"; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
UPLOAD_BASE_COMMIT="2b3b5cabb3726e52758756e1db81fd4646e1823c"
RUNTIME_AUTHORITY_COMMIT="2b3b5cabb3726e52758756e1db81fd4646e1823c"
BASE_RUN_ID="35735608607"
BASE_ARTIFACT_ID="10697832130"
BASE_ARTIFACT_NAME="photon-26685-r1-spektra-verified-autodiscovery-native-geometry"
BASE_ARTIFACT_SHA="486f5719d1f20cff2baa12d95d82d8f067ca657b0c9aa1d37b869db60768ed45"
BASE_TAR_SHA="7d35ca857c262e07725d2045618e5a19a2cebb1ebac10e434abf46efbcec6eda"
VERSION_NAME="0.9726686"; VERSION_BUILD="26686"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
MECHANICS_AUTHORITY_COMMIT="2b3b5cabb3726e52758756e1db81fd4646e1823c"
AUTH_26685_BUILD_SCRIPT_BLOB="9c6392bed9f8e53214e2ecba796427555f775c37"
AUTH_26685_WORKFLOW_BLOB="6d400980e4f5c573fcfb60718ab4cac142e7e8e6"
HANDOFF="$ROOT/R1_26686_HANDOFF_HASHES.sha256"; UPLOADS="$ROOT/R1_26686_UPLOAD_PATHS.txt"
BASE_FULL="$ROOT/R1_26686_BASE_26685_R1_FULL_APP.sha256"; CAND_FULL="$ROOT/R1_26686_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/R1_26686_PROTECTED_UNCHANGED_BASE.sha256"; CAND_PROTECTED="$ROOT/R1_26686_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/R1_26686_NATIVE_PROTECTED_BASE.sha256"; CAND_NATIVE="$ROOT/R1_26686_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/R1_26686_VENDOR_PROTECTED_BASE.sha256"; CAND_VENDOR="$ROOT/R1_26686_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/R1_26686_DNG_BASE.sha256"; CAND_DNG="$ROOT/R1_26686_DNG_CANDIDATE.sha256"
SHADER_BASE="$ROOT/R1_26686_ASSET_SHADER_UNIVERSE_BASE.sha256"; SHADER_CAND="$ROOT/R1_26686_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256"; NEW_SHADER="$ROOT/R1_26686_NEW_NATIVE_SHADER.sha256"
CHANGED="$ROOT/R1_26686_RUNTIME_CHANGED_PATHS.txt"; PREWRITE="$ROOT/R1_26686_PREWRITE_SOURCE_HASHES.sha256"; EXPECTED_CHANGED="$ROOT/R1_26686_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/R1_26686_RUNTIME_DELTA_FROM_26685_R1.patch"; ROLLBACK="$ROOT/R1_26686_RUNTIME_ROLLBACK_TO_26685_R1.patch"
TRANSFORM="$ROOT/transform_26686.py"; VALIDATE="$ROOT/validate_26686.py"; AUTHORITY="$ROOT/verify_26686_authority.py"; INFRA="$ROOT/verify_26686_infrastructure.py"; PATCHVERIFY="$ROOT/verify_26686_patches.py"; GATEVERIFY="$ROOT/verify_26686_regressions.py"
BUILD_SCRIPT="$ROOT/build_26686_r1_spektra_native_raw_vulkan_owner.sh"; WORKFLOW="$ROOT/.github/workflows/build-26686-r1-spektra-native-raw-vulkan-owner.yml"
OUT="$ROOT/build_26686_r1_spektra_native_raw_vulkan_owner_outputs"; WORK="$ROOT/.build_26686_r1_spektra_native_raw_vulkan_owner_work"
ARTZIP="$WORK/26685_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_successful_26685_compiled_candidate"; AFTER="$WORK/candidate_26686"; AFTER2="$WORK/candidate_26686_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; GLSLANG_DIR="$WORK/glslang-${GLSLANG_VERSION}"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r1-spektra-native-raw-vulkan-owner-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26685 artifact ZIP"; LOCAL_ART="$2"; elif [[ -n "${1:-}" ]]; then fail "unknown argument: $1"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26686_R1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26686_R1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME AUTHORITY: NOT RUN
VERIFICATION MECHANICS AUTHORITY: NOT RUN
BACKUP STATUS: NONE (user explicitly requested no backup; exact hashes + deterministic rollback patch)
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE CHANGED FILES: outer 26686 workflow/build/transform/validator/handoff wrappers; runtime-native scope also intentionally changes app/src/main/cpp/CMakeLists.txt + spektra/EmbedSpektraSpirv.cmake to compile/embed the new shader
INFRASTRUCTURE DELTA FROM LAST SUCCESS: successful 26685 compiler/build ordering unchanged; only 26686 authority/version/scope/regressions and required modified-shader real-glslang gate added
SPEKTRA NATIVE RAW OWNER: NOT RUN
SPEKTRA RAW-DOMAIN GEOMETRY: NOT RUN
SPEKTRA PACKED RAW LIFETIME: NOT RUN
SPEKTRA CFA/LSC/MATRIX CONTRACT: NOT RUN
SPEKTRA DISCOVERY/SESSION REGRESSIONS: NOT RUN
IRIS GL/RCD ACTIVE-PATH ABSENCE: NOT RUN
26681-26685 FAILURE REGRESSIONS: NOT RUN
ASSET SHADER UNIVERSE INVARIANCE: NOT RUN
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
TARGET VERSION/BUILD: 0.9726686 / 26686
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26686_R1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26686_R1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26686_R1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26686_R1_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){ local authority_root="$1" live_root="$2" dest_root="$3"; rm -rf "$dest_root"; mkdir -p "$dest_root"; cp -a "$authority_root/." "$dest_root/"; rm -rf "$dest_root/app/src"; cp -a "$live_root/app/src" "$dest_root/app/"; cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"; cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"; }
compare_app_trees(){ python3 -S - "$1" "$2" <<'PY2'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a=H(sys.argv[1]);b=H(sys.argv[2]);assert len(a)==len(b)==1767 and a==b,(len(a),len(b),sorted(set(a)^set(b))[:10]);print('PASS authority-seeded candidate byte-identical: 1767 files')
PY2
}
verify_package(){
 [[ -f "$HANDOFF" && -f "$UPLOADS" && -d "$ROOT/handoff_payload_26686" ]] || fail "sealed 26686 package incomplete"
 [[ "$(find "$ROOT/handoff_payload_26686" -type f | wc -l)" -eq 14 ]] || fail "runtime payload must contain exactly 14 files"
 [[ "$(wc -l < "$CHANGED")" -eq 14 ]] || fail "26686 changed-file count"
 [[ "$(wc -l < "$ROOT/R1_26686_ADDED_PATHS_MUST_BE_ABSENT.txt")" -eq 3 ]] || fail "26686 added-file count"
 sha256sum -c "$HANDOFF" >/dev/null
 [[ "$(wc -l < "$BASE_FULL")" -eq 1764 && "$(wc -l < "$CAND_FULL")" -eq 1767 ]] || fail "full app count"
 [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1753 && "$(wc -l < "$BASE_NATIVE")" -eq 804 && "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$BASE_DNG")" -eq 7 ]] || fail "protected manifest counts"
 [[ "$(wc -l < "$SHADER_BASE")" -eq 271 && "$(wc -l < "$SHADER_CAND")" -eq 271 && "$(wc -l < "$NEW_SHADER")" -eq 1 ]] || fail "shader manifest counts"
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
 if [[ -n "$LOCAL_ART" ]]; then set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed candidate: exact 14 paths = 11 modified + 3 added; no deletions from successful 26685 compiled authority)"; return; fi
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
 git merge-base --is-ancestor "$UPLOAD_BASE_COMMIT" HEAD || fail "successful 26685 R1 commit must remain ancestor"
 [[ "$(git rev-parse "${MECHANICS_AUTHORITY_COMMIT}:build_26685_r1_spektra_verified_autodiscovery_native_geometry.sh")" == "$AUTH_26685_BUILD_SCRIPT_BLOB" ]] || fail "successful 26685 build-script blob changed"
 [[ "$(git rev-parse "${MECHANICS_AUTHORITY_COMMIT}:.github/workflows/build-26685-r1-spektra-verified-autodiscovery-native-geometry.yml")" == "$AUTH_26685_WORKFLOW_BLOB" ]] || fail "successful 26685 workflow blob changed"
 git diff --name-only "$UPLOAD_BASE_COMMIT"..HEAD | sort > "$WORK/actual_upload_scope.txt"; sort "$UPLOADS" > "$WORK/expected_upload_scope.txt"; diff -u "$WORK/expected_upload_scope.txt" "$WORK/actual_upload_scope.txt" || fail "26686 upload scope mismatch"
 ! grep -Eq '^app/' "$WORK/actual_upload_scope.txt" || fail "handoff commit contains live app source"
 set_report "CHANGED RUNTIME SCOPE" "PASS (14 runtime/native paths carried only inside sealed payload; live app source not committed)"
}
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
 [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "successful 26685 artifact ZIP SHA"
 unzip -q "$ARTZIP" -d "$ARTDIR"; local tarball="$ARTDIR/build_26685_r1_spektra_verified_autodiscovery_native_geometry_outputs/26685_R1_candidate_app_source.tar.gz"
 [[ -f "$tarball" && "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "successful 26685 compiled candidate TAR authority"
 tar -xzf "$tarball" -C "$BASE"; (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null) || fail "exact successful 26685 base manifest"
 set_report "RUNTIME AUTHORITY" "PASS (successful 26685 R1 commit ${RUNTIME_AUTHORITY_COMMIT}/run ${BASE_RUN_ID}/artifact ${BASE_ARTIFACT_ID}/artifact SHA ${BASE_ARTIFACT_SHA}/compiled candidate TAR ${BASE_TAR_SHA})"
}
make_candidate(){
 python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26686_transform.txt"; python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26686_transform_replay.txt"; compare_app_trees "$AFTER" "$AFTER2"
 python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26686_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$AFTER" | tee "$OUT/26686_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26686_authority_candidate.txt"
 set_report "SPEKTRA NATIVE RAW OWNER" "PASS (one persistent Vulkan device/queue/pipeline owner; reusable mapped buffers; saved priority; preview drop-before-work; no Iris GL texture tracking)"
 set_report "SPEKTRA RAW-DOMAIN GEOMETRY" "PASS (rawBounds/sourceCrop/activeRawDomain all RAW-raster coordinates; active-array mapping explicit; unresolved fractional Bayer origin fails closed)"
 set_report "SPEKTRA PACKED RAW LIFETIME" "PASS (VF-S native consumes live Camera2 plane before Image.close; saved recovery stores durable packed RAW bytes/stride/format/geometry; CPU meter only)"
 set_report "SPEKTRA CFA/LSC/MATRIX CONTRACT" "PASS (phase-shifted CFA/black; active-domain LSC interpolation; G-even/G-odd sensor-row parity uses verified Bayer offset; explicit row-major sensor->linear matrix)"
 set_report "SPEKTRA DISCOVERY/SESSION REGRESSIONS" "PASS (26684/26685 auto discovery + RAW10-first verification + shared-session still + preview resume preserved)"
 set_report "IRIS GL/RCD ACTIVE-PATH ABSENCE" "PASS"
 set_report "26681-26685 FAILURE REGRESSIONS" "PASS"
 set_report "ASSET SHADER UNIVERSE INVARIANCE" "PASS (271/271 inherited asset shaders byte-identical; 1 new Spektra native compute shader separately compiled)"
 set_report "PROTECTED/DNG/NATIVE/VENDOR INVARIANCE" "PASS"
}
verify_successful_26685_mechanics(){ python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26686_infrastructure.txt"; set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (successful 26685 R1 build-script ${AUTH_26685_BUILD_SCRIPT_BLOB} + workflow ${AUTH_26685_WORKFLOW_BLOB}; exact compiler/build order preserved)"; }
prepare_glslang(){
 local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz" compiler
 curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"
 [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive SHA"
 rm -rf "$GLSLANG_DIR"; mkdir -p "$GLSLANG_DIR"; tar -xzf "$archive" -C "$GLSLANG_DIR"
 compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "pinned glslang compiler missing"
 "$compiler" --version | tee "$OUT/26686_glslang_version.txt"
 export IRIS26681_SPEKTRA_GLSLANG="$compiler"; [[ -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "pinned glslang is not executable"
}
compile_new_native_shader(){
 local compiler="$IRIS26681_SPEKTRA_GLSLANG" outspv="$WORK/SpektraRawDevelop.comp.spv"
 "$compiler" -V "$AFTER/app/src/main/cpp/spektra/SpektraRawDevelop.comp" -o "$outspv" 2>&1 | tee "$OUT/26686_glslang_raw_develop.log"
 [[ -s "$outspv" ]] || fail "new native shader SPIR-V missing"
 sha256sum "$AFTER/app/src/main/cpp/spektra/SpektraRawDevelop.comp" "$outspv" > "$OUT/26686_new_native_shader_compile.sha256"
 set_report "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; exact SpektraRawDevelop.comp)"; set_compiler "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; exact SpektraRawDevelop.comp)"
}
verify_candidate_patches(){ python3 -S "$PATCHVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26686_patch_validation.txt"; set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"; }
install_frozen_candidate_live(){ rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"; snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"; compare_app_trees "$AFTER" "$LIVE_CANON"; }
postbuild_proof(){
 snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"; compare_app_trees "$AFTER" "$POST"; (cd "$POST" && sha256sum -c "$CAND_PROTECTED" >/dev/null && sha256sum -c "$CAND_NATIVE" >/dev/null && sha256sum -c "$CAND_VENDOR" >/dev/null && sha256sum -c "$CAND_DNG" >/dev/null && sha256sum -c "$SHADER_CAND" >/dev/null) || fail "post-build invariance"; python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26686_postbuild_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$POST" | tee "$OUT/26686_postbuild_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26686_postbuild_authority.txt"; set_report "POST-BUILD INVARIANCE" "PASS (candidate/protected/DNG/native/vendor/inherited asset shaders exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"
 tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26686_R1_candidate_app_source.tar.gz"; sha256sum "$OUT/26686_R1_candidate_app_source.tar.gz" > "$OUT/26686_R1_candidate_app_source.tar.gz.sha256"; cp "$CAND_FULL" "$OUT/26686_R1_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26686_R1_native_protected_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26686_R1_vendor_protected_postbuild.sha256"; cp "$CAND_DNG" "$OUT/26686_R1_dng_postbuild.sha256"; cp "$SHADER_CAND" "$OUT/26686_R1_asset_shader_universe_postbuild.sha256"; cp "$NEW_SHADER" "$OUT/26686_R1_new_native_shader_source.sha256"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests)"
}
verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_26685_mechanics
if [[ -n "$LOCAL_ART" ]]; then
 verify_candidate_patches
 set_report "REAL GLSL COMPILE" "NOT RUN locally (pinned compiler unavailable here; Actions required)"; set_report "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real GLSL/Kotlin/Java/NDK/full Android require Actions)"; set_report "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_report "EXACTLY ONE APK" "NOT RUN locally (Actions required)"; set_report "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN locally (Actions required)"
 set_compiler "REAL GLSL COMPILE" "NOT RUN locally (pinned compiler unavailable here; Actions required)"; set_compiler "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_compiler "NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_compiler "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_compiler "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; cp "$OUT/26686_R1_STRICT_HANDOFF_REPORT.txt" "$OUT/26686_R1_local_prebuild_report.txt"; pass "26686 R1 LOCAL PREBUILD PREPARED: exact successful 26685 compiled authority; successful-26685 order retained; all locally available packaged gates passed; real compiler/build gates explicitly unproven locally"; exit 0
fi
prepare_glslang
compile_new_native_shader
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26686_gradle_language_compilers.log"
set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"; compare_app_trees "$AFTER" "$WORK/after_language_compiler_snapshot"
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26686_gradle_native_compiler.log"
set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs; CMake recompiles/embeds exact new shader using same pinned glslang)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
verify_candidate_patches
set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26686 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26686_gradle_assemble.log"
set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort)
[[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK"
mv "${apks[0]}" "$FINAL"; [[ -f "$FINAL" ]] || fail "final APK missing after move"; set_report "EXACTLY ONE APK" "PASS"; sha256sum "$FINAL" > "$OUT/26686_R1_APK.sha256"
postbuild_proof
pass "26686 R1 ACTIONS BUILD COMPLETE"
