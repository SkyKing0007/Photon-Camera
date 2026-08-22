#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
SUCCESSFUL_26526_HEAD="0c57e0a887a66bcc57c59d868ddf4d2f53c48130"
BASE_WORKFLOW="build-26526-combined-zoom-temporal-audit.yml"
BASE_ARTIFACT="photon-26526-combined-zoom-temporal-audit-v1"
BASE_SOURCE_TAR_NAME="26526_candidate_app_source.tar.gz"
BASE_SOURCE_MANIFEST_NAME="26526_candidate_source.sha256"
EXPECTED_BASE_TAR_SHA="659d69d2314d283c87716889cf6efb47940b9c425b3a2ddf4bfb82aa1b07f29e"
EXPECTED_BASE_MANIFEST_SHA="ffecfff0aaae17e5c0bead2b60d60f19764922acd4b75d4f85e4872aa0ccd9a6"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"

APPLY="$ROOT/apply_26527_final_mgc_zoom_dng.py"
VALIDATE="$ROOT/validate_26527_final_mgc_zoom_dng.py"
AUDIT="$ROOT/audit_26527_temporal_support.py"
PREFLIGHT="$ROOT/preflight_26527_embedded_shaders.py"
NATIVE_PREFLIGHT="$ROOT/preflight_26527_native_syntax.py"
DNG_TEST="$ROOT/test_26527_dng_subifd.py"
HANDOFF="$ROOT/26527_HANDOFF_HASHES.sha256"
BASE_FILE="$ROOT/26527_BASE_26526_HEAD.txt"
PROVENANCE="$ROOT/26527_SCOPE_PROVENANCE.txt"
EXPECTED_PATCH="$ROOT/26527_RUNTIME_DELTA_FROM_SUCCESSFUL_26526.patch"
EXPECTED_PATCH_SHA="$ROOT/26527_RUNTIME_DELTA_FROM_SUCCESSFUL_26526.patch.sha256"
EXPECTED_ROLLBACK="$ROOT/26527_RUNTIME_ROLLBACK_TO_SUCCESSFUL_26526.patch"
EXPECTED_ROLLBACK_SHA="$ROOT/26527_RUNTIME_ROLLBACK_TO_SUCCESSFUL_26526.patch.sha256"
INHERITED_SHADER_PREFLIGHT="$ROOT/preflight_26526_inherited_shaders.py"
INHERITED_SHADER_PREFLIGHT_SHA="638376dd1b6d770cd8d91d3e35ff3d61e6847ab3277b64b446976a88e43b9e2b"

BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
BJZHOU_SPATIAL_REFERENCE="c317bf97d2649ae9296bc1459979ce63cb3364b2"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"

OUT="$ROOT/build_26527_final_mgc_zoom_dng_outputs"
WORK="$ROOT/.build_26527_final_mgc_zoom_dng_work"
ART="$WORK/26526_artifact"
BASE="$WORK/tested26526"
AFTER="$WORK/candidate26527"
POSTCHECK="$WORK/postbuild26527"
VERIFY_NEXT="$WORK/verify_next_candidate"
BJ="$WORK/bjzhou_vendor"

VERSION_NAME="0.9726527"; VERSION_BUILD="26527"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-final-mgc-zoom-dng-debug.apk"

rm -rf "$OUT" "$WORK"
mkdir -p "$OUT" "$ART" "$BASE" "$AFTER"
exec > >(tee "$OUT/26527_build.log") 2>&1

echo "=== 26527 GATE 0: exact successful-26526 lineage + handoff integrity ==="
BRANCH="$(git branch --show-current)"; START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch: $BRANCH"
git merge-base --is-ancestor "$SUCCESSFUL_26526_HEAD" HEAD || fail "handoff HEAD is not descended from successful 26526 V1.2"
[[ "$(tr -d '\r\n' < "$BASE_FILE")" == "$SUCCESSFUL_26526_HEAD" ]] || fail "base-26526 file drift"

for f in "$APPLY" "$VALIDATE" "$AUDIT" "$PREFLIGHT" "$NATIVE_PREFLIGHT" "$DNG_TEST" \
         "$HANDOFF" "$PROVENANCE" "$EXPECTED_PATCH" "$EXPECTED_PATCH_SHA" \
         "$EXPECTED_ROLLBACK" "$EXPECTED_ROLLBACK_SHA" "$INHERITED_SHADER_PREFLIGHT" \
         "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do
  [[ -f "$f" ]] || fail "missing required file $(basename "$f")"
done
sha256sum -c "$HANDOFF"
( cd "$ROOT" && sha256sum -c "$(basename "$EXPECTED_PATCH_SHA")" )
( cd "$ROOT" && sha256sum -c "$(basename "$EXPECTED_ROLLBACK_SHA")" )
[[ "$(sha "$INHERITED_SHADER_PREFLIGHT")" == "$INHERITED_SHADER_PREFLIGHT_SHA" ]] || fail "26526 inherited shader preflight drift"
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_VENDOR_HEAD" ]] || fail "vendor dependency commit drift"
python3 -m py_compile "$APPLY" "$VALIDATE" "$AUDIT" "$PREFLIGHT" "$NATIVE_PREFLIGHT" "$DNG_TEST"
python3 "$APPLY" --self-test
bash -n "$0"
command -v glslangValidator >/dev/null || fail "glslangValidator unavailable"
glslangValidator --version | grep -F '16.5.0' >/dev/null || fail "wrong glslang version"

git diff --name-only "$SUCCESSFUL_26526_HEAD"..HEAD -- app/src/main app/version.properties \
  > "$OUT/26527_committed_runtime_drift_after_26526.txt"
[[ ! -s "$OUT/26527_committed_runtime_drift_after_26526.txt" ]] || fail "committed runtime drift after successful 26526"
git diff --name-only "$SUCCESSFUL_26526_HEAD"..HEAD -- \
  gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties app/build.gradle app/proguard-rules.pro \
  > "$OUT/26527_protected_build_infrastructure_drift.txt"
[[ ! -s "$OUT/26527_protected_build_infrastructure_drift.txt" ]] || fail "protected build infrastructure drift after successful 26526"
pass "26527 handoff-only lineage verified from successful 26526 V1.2"

echo "=== 26527 GATE 1: recover ACTUAL successful 26526 candidate-source artifact ==="
command -v gh >/dev/null || fail "GitHub CLI unavailable"
[[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing"
RUN_JSON="$WORK/26526_runs.json"
gh run list --repo "$REPO" --workflow "$BASE_WORKFLOW" --branch "$EXPECTED_BRANCH" --status success \
  --limit 50 --json databaseId,headSha,conclusion,createdAt > "$RUN_JSON"
RUN_ID="$(python3 - "$RUN_JSON" "$SUCCESSFUL_26526_HEAD" <<'PYRUN'
import json,sys
runs=json.load(open(sys.argv[1])); head=sys.argv[2]
exact=[r for r in runs if r.get('headSha')==head and r.get('conclusion')=='success']
if not exact: raise SystemExit('no successful 26526 workflow at exact HEAD '+head)
exact.sort(key=lambda r:r.get('createdAt',''),reverse=True)
print(exact[0]['databaseId'])
PYRUN
)"
[[ "$RUN_ID" =~ ^[0-9]+$ ]] || fail "invalid successful-26526 run id"
gh run download "$RUN_ID" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$ART"
mapfile -t SOURCE_TARS < <(find "$ART" -type f -name "$BASE_SOURCE_TAR_NAME" -print)
mapfile -t SOURCE_MANIFESTS < <(find "$ART" -type f -name "$BASE_SOURCE_MANIFEST_NAME" -print)
[[ "${#SOURCE_TARS[@]}" -eq 1 && "${#SOURCE_MANIFESTS[@]}" -eq 1 ]] || fail "26526 source artifact cardinality mismatch"
SOURCE_TAR="${SOURCE_TARS[0]}"; SOURCE_MANIFEST="${SOURCE_MANIFESTS[0]}"
[[ "$(sha "$SOURCE_TAR")" == "$EXPECTED_BASE_TAR_SHA" ]] || fail "successful-26526 candidate tar SHA drift"
[[ "$(sha "$SOURCE_MANIFEST")" == "$EXPECTED_BASE_MANIFEST_SHA" ]] || fail "successful-26526 candidate manifest SHA drift"
python3 - "$SOURCE_TAR" <<'PYTAR'
import sys,tarfile
with tarfile.open(sys.argv[1],'r:gz') as t:
    names=[m.name.lstrip('./') for m in t.getmembers() if m.name not in ('.','./')]
for n in names:
    if not (n in {'app','app/','app/src','app/src/','app/src/main','app/src/main/','app/version.properties'} or n.startswith('app/src/main/')):
        raise SystemExit('unexpected path in 26526 candidate archive: '+n)
print('PASS: 26526 candidate archive contains runtime source + version only')
PYTAR
tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26526_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "0.9726526" ]] || fail "26526 base version mismatch"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "26526" ]] || fail "26526 base build mismatch"
pass "manifest+SHA verified exact successful 26526 runtime recovered; repository app/src is not runtime authority"

echo "=== 26527 GATE 1A: exact prechange active-owner / frozen-invariant proof ==="
python3 - "$BASE" <<'PYPRE'
from pathlib import Path
import sys
r=Path(sys.argv[1])
f=(r/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt').read_text()
assert 'IRIS_26521_V5_INDEPENDENT_SPATIAL_RGB_OWNER_ACTIVE' in f
assert 'return GlesIris26521SpatialRgbStacker(' in f
sh=(r/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt').read_text()
st=(r/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt').read_text()
assert 'convertBayerAlignment' in sh+st, 'expected 26526 intermediate Spatial owner anchor absent'
saver=(r/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java').read_text()
assert saver.count('dngCreator.setDefaultCropZoom(parameters.motionV2OutputZoom);')==1
assert 'setEmbeddedPreviewEnabled' not in saver
zoom=(r/'app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java').read_text()
assert 'IRIS_26526_SINGLE_PREVIEW_GEOMETRY_AUTHORITY' in zoom
cap=(r/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
assert 'IRIS_26526_SESSION_BOUND_HAL_TELEMETRY' in cap
print('PASS: exact 26526 active Iris Spatial + zoom + DNG predecessor contract')
PYPRE

echo "=== 26527 GATE 1B: resolve COMPLETE transform + frozen forward/rollback patches BEFORE writes ==="
GEN_PATCH="$OUT/26527_RUNTIME_DELTA_FROM_SUCCESSFUL_26526.patch"
GEN_PATCH_SHA="$OUT/26527_RUNTIME_DELTA_FROM_SUCCESSFUL_26526.patch.sha256"
GEN_ROLLBACK="$OUT/26527_RUNTIME_ROLLBACK_TO_SUCCESSFUL_26526.patch"
GEN_ROLLBACK_SHA="$OUT/26527_RUNTIME_ROLLBACK_TO_SUCCESSFUL_26526.patch.sha256"
python3 "$APPLY" "$BASE" --check-only \
  --patch-out "$GEN_PATCH" --patch-sha-out "$GEN_PATCH_SHA" \
  --rollback-out "$GEN_ROLLBACK" --rollback-sha-out "$GEN_ROLLBACK_SHA" \
  | tee "$OUT/26527_in_memory_transform_proof.txt"
( cd "$OUT" && sha256sum -c "$(basename "$GEN_PATCH_SHA")" && sha256sum -c "$(basename "$GEN_ROLLBACK_SHA")" )
cmp -s "$GEN_PATCH" "$EXPECTED_PATCH" || fail "generated forward patch differs from certified handoff patch"
cmp -s "$GEN_ROLLBACK" "$EXPECTED_ROLLBACK" || fail "generated rollback patch differs from certified handoff rollback"
[[ -s "$GEN_PATCH" && -s "$GEN_ROLLBACK" ]] || fail "forward/rollback patch missing"
pass "26527 forward + rollback patches generated, hashed, and frozen before candidate writes"

echo "=== 26527 GATE 2: exact ten-owner transform + independent certification ==="
cp -a "$BASE/." "$AFTER/"
python3 "$APPLY" "$AFTER"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" \
  --patch "$GEN_PATCH" --patch-sha "$GEN_PATCH_SHA" \
  --rollback "$GEN_ROLLBACK" --rollback-sha "$GEN_ROLLBACK_SHA" \
  --json-out "$OUT/26527_prebuild_validation.json" | tee "$OUT/26527_prebuild_validator.txt"
python3 "$AUDIT" --base "$BASE" --candidate "$AFTER" --out "$OUT/26527_temporal_prebuild_audit.json" \
  | tee "$OUT/26527_temporal_prebuild_audit.txt"
python3 "$PREFLIGHT" --base "$BASE" --candidate "$AFTER" --validator glslangValidator \
  | tee "$OUT/26527_embedded_shader_preflight.txt"
python3 "$INHERITED_SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator \
  | tee "$OUT/26527_inherited_shader_preflight.txt"
python3 "$NATIVE_PREFLIGHT" --root "$AFTER" | tee "$OUT/26527_native_syntax_preflight.txt"
python3 "$DNG_TEST" --root "$AFTER" | tee "$OUT/26527_dng_subifd_preflight.txt"
[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "0.9726526" ]] || fail "version changed before guarded build block"
[[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "26526" ]] || fail "build changed before guarded build block"
echo "TEMPORAL_RUNTIME_TELEMETRY=true"
echo "TEMPORAL_IMAGE_MATH_CHANGED=true"
echo "TEMPORAL_CORRECTION=FINAL_MGC_REJECTION_AND_ALIGNMENT_DOMAIN_PARITY"
echo "PRE-BUILD SAFETY PROOF PASSED"

echo "=== 26527 GATE 3: version $VERSION_NAME/$VERSION_BUILD + APK build in SAME guarded block ==="
python3 - "$AFTER/app/version.properties" "$VERSION_NAME" "$VERSION_BUILD" <<'PYVER'
from pathlib import Path
import sys
p=Path(sys.argv[1]); vn=sys.argv[2]; vb=sys.argv[3]; s=p.read_text()
assert s.count('VERSION_NAME=0.9726526')==1 and s.count('VERSION_BUILD=26526')==1
p.write_text(s.replace('VERSION_NAME=0.9726526','VERSION_NAME='+vn,1).replace('VERSION_BUILD=26526','VERSION_BUILD='+vb,1))
PYVER

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
[[ "$(git -C "$BJ" rev-parse HEAD)" == "$BJZHOU_VENDOR_HEAD" ]] || fail "vendor checkout drift"
THIRD="$AFTER/app/src/main/cpp/third_party_26507"
rm -rf "$THIRD"; mkdir -p "$THIRD"
cp -a "$BJ/app/src/main/cpp/libjpeg-turbo" "$THIRD/libjpeg-turbo"
cp -a "$BJ/app/src/main/cpp/libultrahdr" "$THIRD/libultrahdr"
( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26527_vendor_manifest_check_prebuild.txt"

rm -rf app/src/main
mkdir -p app/src
cp -a "$AFTER/app/src/main" app/src/main
cp "$AFTER/app/version.properties" app/version.properties

assert_cpp_deps_exact(){
  local phase="$1" expected actual
  if [[ "$phase" == pre ]]; then expected=$'.gitignore'
  else expected=$'.gitignore\narchive.h\narchive_entry.h\ntechnicallyflac.h\ntiny_dng_writer.h'; fi
  actual="$(find app/src/main/cpp/deps -mindepth 1 -maxdepth 1 -type f -printf '%f\n' | LC_ALL=C sort)"
  [[ "$actual" == "$expected" ]] || fail "unexpected app/src/main/cpp/deps contents ($phase): [$actual]"
}
audited_runtime_manifest(){
  {
    find app/src/main -type f ! -path 'app/src/main/cpp/third_party_26507/*' ! -path 'app/src/main/cpp/deps/*' -print
    echo app/src/main/cpp/deps/.gitignore
    echo app/version.properties
  } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done
}
assert_cpp_deps_exact pre
audited_runtime_manifest > "$OUT/26527_pre_gradle_audited_runtime.sha256"
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace
assert_cpp_deps_exact post
audited_runtime_manifest > "$OUT/26527_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26527_pre_gradle_audited_runtime.sha256" "$OUT/26527_post_gradle_audited_runtime.sha256" \
  || fail "Gradle mutated audited runtime source/version"
( cd app/src/main/cpp/third_party_26507 && sha256sum -c "$BJZHOU_MANIFEST" ) \
  > "$OUT/26527_vendor_manifest_check_postbuild.txt"

rm -rf "$POSTCHECK"; mkdir -p "$POSTCHECK/app/src" "$POSTCHECK/app"
cp -a app/src/main "$POSTCHECK/app/src/main"
rm -rf "$POSTCHECK/app/src/main/cpp/third_party_26507"
find "$POSTCHECK/app/src/main/cpp/deps" -mindepth 1 -maxdepth 1 -type f ! -name '.gitignore' -delete
cp app/version.properties "$POSTCHECK/app/version.properties"
python3 "$VALIDATE" --base "$BASE" --candidate "$POSTCHECK" \
  --patch "$GEN_PATCH" --patch-sha "$GEN_PATCH_SHA" \
  --rollback "$GEN_ROLLBACK" --rollback-sha "$GEN_ROLLBACK_SHA" --postbuild \
  --json-out "$OUT/26527_postbuild_validation.json" | tee "$OUT/26527_postbuild_owner_proof.txt"
python3 "$AUDIT" --base "$BASE" --candidate "$POSTCHECK" --out "$OUT/26527_temporal_postbuild_audit.json" \
  | tee "$OUT/26527_temporal_postbuild_audit.txt"
python3 "$DNG_TEST" --root "$POSTCHECK" | tee "$OUT/26527_dng_subifd_postbuild.txt"

mapfile -t APKS < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' -print)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#APKS[@]}"
rm -f "$FINAL"; cp "${APKS[0]}" "$FINAL"; [[ -s "$FINAL" ]] || fail "final APK missing"
sha256sum "$FINAL" | tee "$OUT/26527_APK.sha256"

rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } \
  | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26527_candidate_source.sha256"
tar --sort=name --mtime='UTC 2026-08-22 00:00:00' --owner=0 --group=0 --numeric-owner \
  -czf "$OUT/26527_candidate_app_source.tar.gz" -C "$AFTER" app/src/main app/version.properties
sha256sum "$OUT/26527_candidate_app_source.tar.gz" | tee "$OUT/26527_candidate_app_source.tar.gz.sha256"
rm -rf "$VERIFY_NEXT"; mkdir -p "$VERIFY_NEXT"
tar -xzf "$OUT/26527_candidate_app_source.tar.gz" -C "$VERIFY_NEXT"
( cd "$VERIFY_NEXT" && sha256sum -c "$OUT/26527_candidate_source.sha256" ) \
  > "$OUT/26527_next_candidate_manifest_check.txt"

cat > "$OUT/26527_provenance.txt" <<EOF
BUILD=26527
VERSION=0.9726527
HANDOFF_START_HEAD=$START_HEAD
SUCCESSFUL_26526_HEAD=$SUCCESSFUL_26526_HEAD
SUCCESSFUL_26526_CANDIDATE_TAR_SHA256=$EXPECTED_BASE_TAR_SHA
SUCCESSFUL_26526_CANDIDATE_MANIFEST_SHA256=$EXPECTED_BASE_MANIFEST_SHA
BJZHOU_SPATIAL_REFERENCE=$BJZHOU_SPATIAL_REFERENCE
BJZHOU_VENDOR_HEAD=$BJZHOU_VENDOR_HEAD
RUNTIME_CHANGED_FILES=10
TEMPORAL_RUNTIME_TELEMETRY=true
TEMPORAL_IMAGE_MATH_CHANGED=true
TEMPORAL_CORRECTION=FINAL_MGC_REJECTION_AND_ALIGNMENT_DOMAIN_PARITY
DNG_PREVIEW=STACKED_STILL_ONLY_RGB_SUBIFD_TAG_330
RAWVIDEO_PREVIEW=DISABLED_BY_DEFAULT
EOF

pass "26527 exact successful-26526 artifact + patch-first safety proof"
pass "26527 guarded Gradle build + immutable audited runtime + one APK"
pass "26527 postbuild owner/temporal/DNG proof + deterministic next candidate source"
