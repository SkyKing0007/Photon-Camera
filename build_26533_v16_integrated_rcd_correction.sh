#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
manifest_all(){ local r="$1" o="$2"; (cd "$r" && find app/src/main app/version.properties app/build.gradle -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum) > "$o"; }
manifest_audited_live(){ local r="$1" o="$2"; (cd "$r" && {
  find app/src/main -type f ! -path 'app/src/main/cpp/third_party_26507/*' ! -path 'app/src/main/cpp/deps/*' -print;
  [[ -f app/src/main/cpp/deps/.gitignore ]] && echo app/src/main/cpp/deps/.gitignore;
  echo app/version.properties; echo app/build.gradle;
} | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done) > "$o"; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_V15_HEAD="10d1aa2c1a37adcfd36533ba4c3879046fd29c3e"
BASE_WORKFLOW="build-26533-v15-normalized16-rcd.yml"
BASE_ARTIFACT="photon-26533-v1-5-normalized16-rcd-domain"
BASE_SOURCE_TAR_NAME="26533_v15_candidate_app_source.tar.gz"
BASE_SOURCE_MANIFEST_NAME="26533_v15_candidate_source.sha256"
EXPECTED_BASE_TAR_SHA="2257efa438c2895fa0d516bcff7f6d9ececeff4ce24dafc0237eb1c82356a612"
EXPECTED_BASE_MANIFEST_SHA="8cf21915b0043a6bb4752e6bc184eb40481abec1e96e14e1008350a64b40b1f5"
EXPECTED_BASE_FILES=962
VERSION_NAME="0.9726533"; VERSION_BUILD="26533"
BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"

APPLY="$ROOT/apply_26533_v16_integrated_rcd_correction.py"
VALIDATE="$ROOT/validate_26533_v16_integrated_rcd_correction.py"
HANDOFF="$ROOT/26533_V16_HANDOFF_HASHES.sha256"
ANCHORS="$ROOT/26533_V16_EXACT_V15_ANCHORS.sha256"
BASE_HEAD_FILE="$ROOT/26533_V16_BASE_SUCCESSFUL_V15_HEAD.txt"
BASE_TAR_SHA_FILE="$ROOT/26533_V16_BASE_V15_SOURCE_TAR.sha256"
BASE_MANIFEST_SHA_FILE="$ROOT/26533_V16_BASE_V15_SOURCE_MANIFEST.sha256"
EXPECTED_PATCH="$ROOT/26533_V16_RUNTIME_DELTA_FROM_V15.patch"
EXPECTED_PATCH_SHA="$ROOT/26533_V16_RUNTIME_DELTA_FROM_V15.patch.sha256"
EXPECTED_ROLLBACK="$ROOT/26533_V16_RUNTIME_ROLLBACK_TO_V15.patch"
EXPECTED_ROLLBACK_SHA="$ROOT/26533_V16_RUNTIME_ROLLBACK_TO_V15.patch.sha256"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"

SHADER_PREFLIGHT="$ROOT/preflight_26532_iris_shaders.py"
NATIVE_JPEG_PREFLIGHT="$ROOT/preflight_26532_native_jpeg_syntax.py"
JAVA_XML_PREFLIGHT="$ROOT/preflight_26532_java_xml_syntax.py"
EMBEDDED_PREFLIGHT="$ROOT/preflight_26529_iris_embedded_shaders_v3.py"
INHERITED_SHADER_PREFLIGHT="$ROOT/preflight_26526_inherited_shaders.py"
KOTLIN_API_PREFLIGHT="$ROOT/preflight_26531_iris_kotlin_api_contracts.py"
NATIVE_DNG_PREFLIGHT="$ROOT/preflight_26527_native_syntax.py"
DNG_TEST="$ROOT/test_26527_dng_subifd.py"
V16_SYNTAX_PREFLIGHT="$ROOT/preflight_26533_v16_changed_syntax.py"
V16_PROVENANCE_PREFLIGHT="$ROOT/preflight_26533_v16_provenance_shader.py"

OUT="$ROOT/build_26533_v16_integrated_rcd_correction_outputs"
WORK="$ROOT/.build_26533_v16_integrated_rcd_correction_work"
ART="$WORK/v15_artifact"
BASE="$WORK/tested_v15"
AFTER="$WORK/candidate_v16"
PATCHREPO="$WORK/patchrepo"
FORWARDCHECK="$WORK/forwardcheck"
ROLLBACKCHECK="$WORK/rollbackcheck"
BJ="$WORK/bjzhou_vendor"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-6-integrated-rcd-correction-debug.apk"
SOURCE_TAR_OUT="$OUT/26533_v16_candidate_app_source.tar.gz"
SOURCE_MANIFEST_OUT="$OUT/26533_v16_candidate_source.sha256"
RUNTIME_FILES=(
  app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/SaverImplementation.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisRcdBayerInput.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightMgc1271Bridge.kt
)

rm -rf "$OUT" "$WORK" "$FINAL"
mkdir -p "$OUT" "$ART" "$BASE" "$AFTER"
find "$ROOT" -maxdepth 1 -type f -name 'IrisCamera-*-debug.apk' -delete
exec > >(tee "$OUT/26533_v16_build.log") 2>&1

echo "=== 26533 V1.6 GATE 0: exact successful V1.5 lineage + handoff integrity ==="
BRANCH="$(git branch --show-current)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch: $BRANCH"
git merge-base --is-ancestor "$BASE_V15_HEAD" HEAD || fail "handoff is not descended from exact successful V1.5"
[[ "$(tr -d '\r\n' < "$BASE_HEAD_FILE")" == "$BASE_V15_HEAD" ]] || fail "V1.5 base HEAD contract drift"
[[ "$(awk '{print $1}' "$BASE_TAR_SHA_FILE")" == "$EXPECTED_BASE_TAR_SHA" ]] || fail "V1.5 source tar SHA contract drift"
[[ "$(awk '{print $1}' "$BASE_MANIFEST_SHA_FILE")" == "$EXPECTED_BASE_MANIFEST_SHA" ]] || fail "V1.5 source manifest SHA contract drift"
for f in "$APPLY" "$VALIDATE" "$HANDOFF" "$ANCHORS" "$BASE_HEAD_FILE" "$BASE_TAR_SHA_FILE" "$BASE_MANIFEST_SHA_FILE" \
         "$EXPECTED_PATCH" "$EXPECTED_PATCH_SHA" "$EXPECTED_ROLLBACK" "$EXPECTED_ROLLBACK_SHA" \
         "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE" "$SHADER_PREFLIGHT" "$NATIVE_JPEG_PREFLIGHT" \
         "$JAVA_XML_PREFLIGHT" "$EMBEDDED_PREFLIGHT" "$INHERITED_SHADER_PREFLIGHT" \
         "$KOTLIN_API_PREFLIGHT" "$NATIVE_DNG_PREFLIGHT" "$DNG_TEST" "$V16_SYNTAX_PREFLIGHT" "$V16_PROVENANCE_PREFLIGHT"; do [[ -f "$f" ]] || fail "missing $(basename "$f")"; done
sha256sum -c "$HANDOFF"
sha256sum -c "$EXPECTED_PATCH_SHA"
sha256sum -c "$EXPECTED_ROLLBACK_SHA"
python3 -m py_compile "$APPLY" "$VALIDATE" "$V16_SYNTAX_PREFLIGHT" "$V16_PROVENANCE_PREFLIGHT" "$SHADER_PREFLIGHT" "$NATIVE_JPEG_PREFLIGHT" "$JAVA_XML_PREFLIGHT" \
  "$EMBEDDED_PREFLIGHT" "$INHERITED_SHADER_PREFLIGHT" "$KOTLIN_API_PREFLIGHT" "$NATIVE_DNG_PREFLIGHT" "$DNG_TEST"
python3 "$APPLY" --self-test
python3 "$VALIDATE" --self-test
bash -n "$0"
command -v gh >/dev/null || fail "GitHub CLI unavailable"
[[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing"
command -v glslangValidator >/dev/null || fail "glslangValidator unavailable"
glslangValidator --version | grep -F '16.5.0' >/dev/null || fail "wrong glslangValidator version"
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_VENDOR_HEAD" ]] || fail "native dependency commit drift"
git diff --name-only "$BASE_V15_HEAD"..HEAD -- app/src/main app/version.properties app/build.gradle > "$OUT/26533_v16_committed_runtime_drift.txt"
[[ ! -s "$OUT/26533_v16_committed_runtime_drift.txt" ]] || fail "committed runtime/build drift after successful V1.5"
for rel in preflight_26532_iris_shaders.py preflight_26532_native_jpeg_syntax.py preflight_26532_java_xml_syntax.py \
           preflight_26529_iris_embedded_shaders_v3.py preflight_26526_inherited_shaders.py \
           preflight_26531_iris_kotlin_api_contracts.py preflight_26527_native_syntax.py test_26527_dng_subifd.py \
           26507_BJZHOU_NATIVE_DEPENDENCIES.sha256 26507_BJZHOU_DEPENDENCY_COMMIT.txt; do
  [[ "$(git hash-object "$rel")" == "$(git rev-parse "$BASE_V15_HEAD:$rel")" ]] || fail "inherited proven procedure drift: $rel"
done
pass "exact V1.5 lineage + handoff + inherited procedure integrity"

echo "=== 26533 V1.6 GATE 1: recover ACTUAL successful V1.5 candidate-source artifact ==="
RUN_JSON="$WORK/v15_runs.json"
gh run list --repo "$REPO" --workflow "$BASE_WORKFLOW" --branch "$EXPECTED_BRANCH" --status success --limit 50 --json databaseId,headSha,conclusion,createdAt > "$RUN_JSON"
RUN_ID="$(python3 - "$RUN_JSON" "$BASE_V15_HEAD" <<'PY'
import json,sys
runs=json.load(open(sys.argv[1])); head=sys.argv[2]
xs=[r for r in runs if r.get('headSha')==head and r.get('conclusion')=='success']
if not xs: raise SystemExit('no successful V1.5 workflow at exact HEAD '+head)
xs.sort(key=lambda r:r.get('createdAt',''),reverse=True)
print(xs[0]['databaseId'])
PY
)"
[[ "$RUN_ID" =~ ^[0-9]+$ ]] || fail "invalid V1.5 workflow run id"
echo "$RUN_ID" > "$OUT/26533_v16_base_v15_successful_run_id.txt"
gh run download "$RUN_ID" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$ART"
mapfile -t SOURCE_TARS < <(find "$ART" -type f -name "$BASE_SOURCE_TAR_NAME" -print)
mapfile -t SOURCE_MANIFESTS < <(find "$ART" -type f -name "$BASE_SOURCE_MANIFEST_NAME" -print)
[[ "${#SOURCE_TARS[@]}" -eq 1 && "${#SOURCE_MANIFESTS[@]}" -eq 1 ]] || fail "V1.5 source artifact cardinality mismatch"
SOURCE_TAR="${SOURCE_TARS[0]}"; SOURCE_MANIFEST="${SOURCE_MANIFESTS[0]}"
[[ "$(sha "$SOURCE_TAR")" == "$EXPECTED_BASE_TAR_SHA" ]] || fail "V1.5 source tar SHA drift"
[[ "$(sha "$SOURCE_MANIFEST")" == "$EXPECTED_BASE_MANIFEST_SHA" ]] || fail "V1.5 source manifest SHA drift"
[[ "$(wc -l < "$SOURCE_MANIFEST")" -eq "$EXPECTED_BASE_FILES" ]] || fail "V1.5 source manifest file-count drift"
python3 - "$SOURCE_TAR" <<'PY'
import sys,tarfile
with tarfile.open(sys.argv[1],'r:gz') as t: names=[m.name.lstrip('./') for m in t.getmembers() if m.name not in ('.','./')]
for n in names:
    if not (n in {'app','app/','app/src','app/src/','app/src/main','app/src/main/','app/version.properties','app/build.gradle'} or n.startswith('app/src/main/')):
        raise SystemExit('unexpected V1.5 candidate archive path: '+n)
print('PASS: exact V1.5 archive contains runtime + version + pinned app dependency only')
PY
tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26533_v16_base_v15_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "$VERSION_NAME" ]] || fail "V1.5 base version name mismatch"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "$VERSION_BUILD" ]] || fail "V1.5 base build mismatch"
( cd "$BASE" && sha256sum -c "$ANCHORS" ) | tee "$OUT/26533_v16_exact_v15_anchor_check.txt"
cp -a "$BASE/." "$AFTER/"
pass "exact successful V1.5 candidate recovered; normalized16/RCD/Jin/MGC architecture reused byte-exact"

echo "=== 26533 V1.6 GATE 2: integrated 7-file transform + forward/rollback proof ==="
python3 "$APPLY" "$AFTER"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" | tee "$OUT/26533_v16_prebuild_validation.txt"
python3 - "$BASE" "$AFTER" "${RUNTIME_FILES[@]}" <<'PY' | tee "$OUT/26533_v16_actual_changed_files.txt"
from pathlib import Path
import hashlib,sys
b=Path(sys.argv[1]); c=Path(sys.argv[2]); expected=sorted(sys.argv[3:])
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def m(root):
 d={}
 for top in ('app/src/main','app/version.properties','app/build.gradle'):
  p=root/top
  if p.is_file(): d[top]=h(p)
  else:
   for f in p.rglob('*'):
    if f.is_file(): d[str(f.relative_to(root))]=h(f)
 return d
mb,mc=m(b),m(c); changed=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k))
if changed!=expected: raise SystemExit('V1.6 changed-file allowlist mismatch: '+repr(changed))
print('\n'.join(changed))
PY
rm -rf "$PATCHREPO"; cp -a "$BASE" "$PATCHREPO"
(
 cd "$PATCHREPO"; git init -q; git config user.email iris26533v16@example.invalid; git config user.name Iris26533V16
 git add app/src/main app/version.properties app/build.gradle; git commit -qm base
 for rel in "${RUNTIME_FILES[@]}"; do cp "$AFTER/$rel" "$rel"; done
 git diff --binary --no-ext-diff -- app/src/main > "$OUT/26533_v16_regenerated_forward.patch"
 git diff --binary --no-ext-diff -R -- app/src/main > "$OUT/26533_v16_regenerated_rollback.patch"
)
cmp -s "$OUT/26533_v16_regenerated_forward.patch" "$EXPECTED_PATCH" || fail "regenerated V1.6 forward patch is not byte-identical"
cmp -s "$OUT/26533_v16_regenerated_rollback.patch" "$EXPECTED_ROLLBACK" || fail "regenerated V1.6 rollback patch is not byte-identical"
rm -rf "$FORWARDCHECK"; cp -a "$BASE" "$FORWARDCHECK"
patch -d "$FORWARDCHECK" -p1 --batch --forward --fuzz=0 --no-backup-if-mismatch < "$EXPECTED_PATCH" >/dev/null
manifest_all "$AFTER" "$OUT/26533_v16_candidate_manifest_preversion.sha256"
manifest_all "$FORWARDCHECK" "$OUT/26533_v16_forwardcheck_manifest.sha256"
cmp -s "$OUT/26533_v16_candidate_manifest_preversion.sha256" "$OUT/26533_v16_forwardcheck_manifest.sha256" || fail "forward patch does not reproduce exact V1.6 candidate"
rm -rf "$ROLLBACKCHECK"; cp -a "$AFTER" "$ROLLBACKCHECK"
patch -d "$ROLLBACKCHECK" -p1 --batch --forward --fuzz=0 --no-backup-if-mismatch < "$EXPECTED_ROLLBACK" >/dev/null
manifest_all "$BASE" "$OUT/26533_v16_base_manifest_for_rollback.sha256"
manifest_all "$ROLLBACKCHECK" "$OUT/26533_v16_rollback_manifest.sha256"
cmp -s "$OUT/26533_v16_base_manifest_for_rollback.sha256" "$OUT/26533_v16_rollback_manifest.sha256" || fail "rollback does not restore exact V1.5"
pass "7-file scope + forward/rollback proof exact"

echo "=== 26533 V1.6 GATE 3: inherited shader/API/native/DNG preflights ==="
python3 "$V16_SYNTAX_PREFLIGHT" --root "$AFTER" | tee "$OUT/26533_v16_changed_syntax_preflight.txt"
python3 "$V16_PROVENANCE_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26533_v16_provenance_shader_preflight.txt"
python3 "$SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26533_v16_shader_preflight.txt"
python3 "$EMBEDDED_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26533_v16_embedded_shader_preflight.txt"
python3 "$INHERITED_SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26533_v16_inherited_shader_preflight.txt"
python3 "$KOTLIN_API_PREFLIGHT" --root "$AFTER" | tee "$OUT/26533_v16_kotlin_api_preflight.txt"
python3 "$NATIVE_DNG_PREFLIGHT" --root "$AFTER" | tee "$OUT/26533_v16_dng_native_preflight.txt"
python3 "$NATIVE_JPEG_PREFLIGHT" --root "$AFTER" | tee "$OUT/26533_v16_native_jpeg_preflight.txt"
python3 "$JAVA_XML_PREFLIGHT" --root "$AFTER" | tee "$OUT/26533_v16_java_xml_preflight.txt"
python3 "$DNG_TEST" --root "$AFTER" | tee "$OUT/26533_v16_dng_subifd_preflight.txt"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" | tee "$OUT/26533_v16_integrated_contract_preflight.txt"
echo "PRE-BUILD SAFETY PROOF PASSED"
pass "integrated V1.6 + inherited V1.5/26532 safety proof"

echo "=== 26533 V1.6 GATE 4: reassert build ID + exact native restore + compile/assemble in one guarded block ==="
{
 sed -i "s/^VERSION_NAME=.*/VERSION_NAME=$VERSION_NAME/; s/^VERSION_BUILD=.*/VERSION_BUILD=$VERSION_BUILD/" "$AFTER/app/version.properties"
 [[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "$VERSION_NAME" ]] || fail "version name reassert failed"
 [[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "$VERSION_BUILD" ]] || fail "build reassert failed"
 python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" | tee "$OUT/26533_v16_versioned_validation.txt"
 manifest_audited_live "$AFTER" "$OUT/26533_v16_pre_gradle_audited_runtime.sha256"
 rm -rf "$BJ"; git init -q "$BJ"
 git -C "$BJ" remote add origin https://github.com/bjzhou/PhotonCamera.git
 git -C "$BJ" config core.sparseCheckout true
 mkdir -p "$BJ/.git/info"
 cat > "$BJ/.git/info/sparse-checkout" <<'SPARSE'
/app/src/main/cpp/libjpeg-turbo/
/app/src/main/cpp/libultrahdr/
SPARSE
 git -C "$BJ" fetch --depth=1 origin "$BJZHOU_VENDOR_HEAD"
 git -C "$BJ" checkout -q --detach FETCH_HEAD
 [[ "$(git -C "$BJ" rev-parse HEAD)" == "$BJZHOU_VENDOR_HEAD" ]] || fail "native vendor checkout drift"
 THIRD="$AFTER/app/src/main/cpp/third_party_26507"
 rm -rf "$THIRD"; mkdir -p "$THIRD"
 cp -a "$BJ/app/src/main/cpp/libjpeg-turbo" "$THIRD/libjpeg-turbo"
 cp -a "$BJ/app/src/main/cpp/libultrahdr" "$THIRD/libultrahdr"
 [[ -f "$THIRD/libjpeg-turbo/CMakeLists.txt" ]] || fail "pinned libjpeg-turbo missing"
 [[ -f "$THIRD/libultrahdr/ultrahdr_api.h" ]] || fail "pinned libultrahdr API missing"
 [[ -f "$THIRD/libultrahdr/lib/src/ultrahdr_api.cpp" ]] || fail "pinned libultrahdr core source missing"
 [[ ! -e "$THIRD/libultrahdr/CMakeLists.txt" ]] || fail "unexpected obsolete libultrahdr CMakeLists sentinel returned"
 ( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26533_v16_vendor_manifest_check_prebuild.txt"
 rm -rf "$ROOT/app/src/main"; mkdir -p "$ROOT/app/src"
 cp -a "$AFTER/app/src/main" "$ROOT/app/src/"; cp "$AFTER/app/version.properties" "$ROOT/app/version.properties"; cp "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"
 assert_cpp_deps_exact(){
  local root="$1" phase="$2" expected actual
  if [[ "$phase" == pre ]]; then expected=$'.gitignore'; else expected=$'.gitignore\narchive.h\narchive_entry.h\ntechnicallyflac.h\ntiny_dng_writer.h'; fi
  actual="$(find "$root/app/src/main/cpp/deps" -mindepth 1 -maxdepth 1 -type f -printf '%f\n' | LC_ALL=C sort)"
  [[ "$actual" == "$expected" ]] || fail "unexpected app/src/main/cpp/deps contents ($phase): [$actual]"
 }
 assert_cpp_deps_exact "$ROOT" pre
 manifest_audited_live "$ROOT" "$OUT/26533_v16_installed_pre_gradle_audited_runtime.sha256"
 cmp -s "$OUT/26533_v16_pre_gradle_audited_runtime.sha256" "$OUT/26533_v16_installed_pre_gradle_audited_runtime.sha256" || fail "installed candidate differs before Gradle"
 (cd "$ROOT/app/src/main/cpp/third_party_26507" && sha256sum -c "$BJZHOU_MANIFEST") > "$OUT/26533_v16_installed_vendor_manifest_check_prebuild.txt"
 chmod +x ./gradlew
 ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
 pass "real Android Kotlin + Java compile gates passed"
 ./gradlew :app:assembleDebug --stacktrace
 pass "assembleDebug passed"
}

echo "=== 26533 V1.6 GATE 5: post-build source/native/semantic revalidation ==="
assert_cpp_deps_exact "$ROOT" post
manifest_audited_live "$ROOT" "$OUT/26533_v16_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26533_v16_pre_gradle_audited_runtime.sha256" "$OUT/26533_v16_post_gradle_audited_runtime.sha256" || fail "Gradle/build mutated audited V1.6 source"
(cd "$ROOT/app/src/main/cpp/third_party_26507" && sha256sum -c "$BJZHOU_MANIFEST") > "$OUT/26533_v16_postbuild_native_dependency_manifest_check.txt"
python3 "$VALIDATE" --base "$BASE" --candidate "$ROOT" | tee "$OUT/26533_v16_postbuild_validation.txt"
python3 "$JAVA_XML_PREFLIGHT" --root "$ROOT" | tee "$OUT/26533_v16_postbuild_java_xml_preflight.txt"
python3 "$NATIVE_JPEG_PREFLIGHT" --root "$ROOT" | tee "$OUT/26533_v16_postbuild_native_jpeg_preflight.txt"
pass "post-build runtime and native dependencies remained exact"

echo "=== 26533 V1.6 GATE 6: exactly one APK + deterministic next candidate ==="
mapfile -t BUILT_APKS < <(find "$ROOT/app/build/outputs/apk" -type f -name '*.apk' -print 2>/dev/null)
[[ "${#BUILT_APKS[@]}" -eq 1 ]] || fail "expected exactly one Gradle APK, found ${#BUILT_APKS[@]}"
cp "${BUILT_APKS[0]}" "$FINAL"; find "$ROOT/app/build" -type f -name '*.apk' -delete
[[ -f "$FINAL" ]] || fail "final APK missing"
[[ "$(find "$ROOT" -maxdepth 1 -type f -name '*.apk' | wc -l)" -eq 1 ]] || fail "root APK count is not exactly one"
sha256sum "$FINAL" > "$OUT/26533_v16_APK.sha256"
rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
manifest_all "$AFTER" "$SOURCE_MANIFEST_OUT"
[[ "$(wc -l < "$SOURCE_MANIFEST_OUT")" -eq "$EXPECTED_BASE_FILES" ]] || fail "V1.6 candidate file count drift"
( cd "$AFTER" && tar --sort=name --mtime='UTC 2026-08-24 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$SOURCE_TAR_OUT" app/src/main app/version.properties app/build.gradle )
sha256sum "$SOURCE_TAR_OUT" > "$OUT/26533_v16_candidate_app_source.tar.gz.sha256"
sha256sum "$SOURCE_MANIFEST_OUT" > "$OUT/26533_v16_candidate_source_manifest_file.sha256"
cat > "$OUT/26533_v16_SCOPE_PROVENANCE.txt" <<EOF
BASE_BRANCH=$EXPECTED_BRANCH
BASE_SUCCESSFUL_V15_HEAD=$BASE_V15_HEAD
BASE_SUCCESSFUL_V15_RUN_ID=$RUN_ID
BASE_ARTIFACT=$BASE_ARTIFACT
TARGET_VERSION=$VERSION_NAME
TARGET_BUILD=$VERSION_BUILD
RUNTIME_DELTA_FILES=7
V15_NORMALIZED16_BLACK0_WHITE65535_PRESERVED=true
MOTION_RCD_GPU_CENSORED_PROVENANCE=true
MOTION_SHORT_VALIDATED_INVENTED=false
MOTION_PROVENANCE_CPU_READBACK=false
MOTION_NORMAL_ONLY_SOURCE_GAIN=1
MOTION_PROTECTED_VIEWFINDER_CHAIN_RESTORED=true
NIGHT_EXACT_TIMESTAMP_METADATA=true
NIGHT_PHYSICAL_RAW_LAYOUT=true
NIGHT_CAMERA2_NOISE_BLACK_WHITE_REQUIRED=true
MGC_STACKER_UNCHANGED=true
BENTO_REJECTION_UNCHANGED=true
CAPTURE_EXPOSURE_POLICY_UNCHANGED=true
SUPER_RES_UNCHANGED=true
DNG_UNCHANGED=true
ULTRAHDR_UNCHANGED=true
JIN_MODEL_UNCHANGED=true
EOF

echo "PASS: 26533 V1.6 INTEGRATED RCD REGRESSION CORRECTION"
echo "PASS: 26533 V1.6 COMPILE + ASSEMBLE + POSTBUILD"
echo "PASS: 26533 V1.6 EXACT V1.5 LINEAGE + 7-FILE DELTA + ONE APK"
