#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
SUCCESSFUL_26521_HEAD="f7ed175670c10ff6bcdcd3df3b2568d86237acd6"
BASE_WORKFLOW="build-26521-v5-iris-spatial-rgb.yml"
BASE_ARTIFACT="photon-26521-v5-iris-spatial-rgb-v1"
BASE_SOURCE_TAR_NAME="26521_candidate_app_source.tar.gz"
BASE_SOURCE_MANIFEST_NAME="26521_candidate_source.sha256"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
APPLY="$ROOT/apply_26522_fullrange_stacked_dng.py"
VALIDATE="$ROOT/validate_26522_fullrange_stacked_dng.py"
PREFLIGHT="$ROOT/preflight_26522_iris_embedded_shaders.py"
HANDOFF="$ROOT/26522_HANDOFF_HASHES.sha256"
BASE_FILE="$ROOT/26522_BASE_26521_HEAD.txt"
PROVENANCE="$ROOT/26522_STACKED_DNG_PROVENANCE.txt"
BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"
OUT="$ROOT/build_26522_fullrange_stacked_dng_outputs"
WORK="$ROOT/.build_26522_fullrange_stacked_dng_work"
ART="$WORK/26521_artifact"
BASE="$WORK/tested26521"
AFTER="$WORK/candidate26522"
BJ="$WORK/bjzhou_vendor"
VERSION_NAME="0.9726522"; VERSION_BUILD="26522"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-fullrange-stacked-dng-debug.apk"

rm -rf "$OUT" "$WORK"
mkdir -p "$OUT" "$ART" "$BASE" "$AFTER"
exec > >(tee "$OUT/26522_build.log") 2>&1

echo "=== 26522 GATE 0: exact successful-26521 lineage + handoff integrity ==="
BRANCH="$(git branch --show-current)"
START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch: $BRANCH"
git merge-base --is-ancestor "$SUCCESSFUL_26521_HEAD" HEAD || fail "current handoff HEAD is not descended from successful 26521"
[[ "$(tr -d '\r\n' < "$BASE_FILE")" == "$SUCCESSFUL_26521_HEAD" ]] || fail "base-26521 file drift"
for f in "$APPLY" "$VALIDATE" "$PREFLIGHT" "$HANDOFF" "$PROVENANCE" "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do
  [[ -f "$f" ]] || fail "missing required handoff/dependency file $(basename "$f")"
done
sha256sum -c "$HANDOFF"
python3 -m py_compile "$APPLY" "$VALIDATE" "$PREFLIGHT"
bash -n "$0"
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_VENDOR_HEAD" ]] || fail "26507 vendor dependency commit drift"
git diff --name-only "$SUCCESSFUL_26521_HEAD"..HEAD -- app/src/main app/version.properties > "$OUT/26522_committed_runtime_drift_after_26521.txt"
[[ ! -s "$OUT/26522_committed_runtime_drift_after_26521.txt" ]] || fail "committed runtime drift after successful 26521"
git diff --name-only "$SUCCESSFUL_26521_HEAD"..HEAD -- gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties app/build.gradle app/proguard-rules.pro > "$OUT/26522_protected_build_infrastructure_drift.txt"
[[ ! -s "$OUT/26522_protected_build_infrastructure_drift.txt" ]] || fail "protected build infrastructure drift after successful 26521"
command -v glslangValidator >/dev/null || fail "glslangValidator unavailable; workflow bootstrap missing"
pass "26522 handoff-only lineage is directly descended from successful 26521"

echo "=== 26522 GATE 1: recover ACTUAL successful 26521 candidate-source artifact ==="
command -v gh >/dev/null || fail "GitHub CLI unavailable"
[[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing"
RUN_JSON="$WORK/26521_runs.json"
gh run list --repo "$REPO" --workflow "$BASE_WORKFLOW" --branch "$EXPECTED_BRANCH" --status success --limit 50 --json databaseId,headSha,conclusion,createdAt > "$RUN_JSON"
RUN_ID="$(python3 - "$RUN_JSON" "$SUCCESSFUL_26521_HEAD" <<'PYRUN'
import json,sys
runs=json.load(open(sys.argv[1])); head=sys.argv[2]
exact=[r for r in runs if r.get('headSha')==head and r.get('conclusion')=='success']
if not exact: raise SystemExit('no successful 26521 workflow at exact HEAD '+head)
exact.sort(key=lambda r:r.get('createdAt',''), reverse=True)
print(exact[0]['databaseId'])
PYRUN
)"
[[ "$RUN_ID" =~ ^[0-9]+$ ]] || fail "invalid successful-26521 run id"
gh run download "$RUN_ID" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$ART"
mapfile -t SOURCE_TARS < <(find "$ART" -type f -name "$BASE_SOURCE_TAR_NAME" -print)
mapfile -t SOURCE_MANIFESTS < <(find "$ART" -type f -name "$BASE_SOURCE_MANIFEST_NAME" -print)
[[ "${#SOURCE_TARS[@]}" -eq 1 && "${#SOURCE_MANIFESTS[@]}" -eq 1 ]] || fail "26521 source artifact cardinality mismatch"
SOURCE_TAR="${SOURCE_TARS[0]}"; SOURCE_MANIFEST="${SOURCE_MANIFESTS[0]}"
BASE_TAR_SHA="$(sha "$SOURCE_TAR")"; SOURCE_MANIFEST_SHA="$(sha "$SOURCE_MANIFEST")"
python3 - "$SOURCE_TAR" <<'PYTAR'
import sys,tarfile
with tarfile.open(sys.argv[1],'r:gz') as t:
    names=[m.name.lstrip('./') for m in t.getmembers() if m.name not in ('.','./')]
for n in names:
    if not (n in {'app','app/','app/src','app/src/','app/src/main','app/src/main/','app/version.properties'} or n.startswith('app/src/main/')):
        raise SystemExit('unexpected path in 26521 source archive: '+n)
print('PASS: 26521 candidate source archive contains runtime source + version only')
PYTAR
tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26521_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "0.9726521" ]] || fail "26521 base version name mismatch"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "26521" ]] || fail "26521 base build mismatch"
pass "manifest-verified successful 26521 runtime recovered; repository app/src is not runtime authority"

echo "=== 26522 GATE 1A: prove successful-26521 active owner and DNG source contract ==="
python3 - "$BASE" "$OUT/26522_base_active_path_proof.txt" <<'PYACTIVE'
from pathlib import Path
import re,sys
root=Path(sys.argv[1]); out=Path(sys.argv[2])
hdr=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
bridge=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
fusion=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt').read_text()
iris=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt').read_text()
shader=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt').read_text()
assert len(re.findall(r'PhotonMotionMgc1271Bridge\.reconstruct\s*\(',hdr))==1
assert len(re.findall(r'MotionV2CfaReconstruction\.reconstruct\s*\(',hdr))==0
for tok in ('IRIS_26521_V5_INDEPENDENT_SPATIAL_RGB_OWNER_ACTIVE','GlesIris26521SpatialRgbStacker('): assert tok in fusion
for tok in ('IRIS_26521_V5_CORRECTED_SPATIAL_INFRASTRUCTURE','IRIS_26520_V5_FINAL_FINEST_LK_OWNER','IRIS_26520_V5_MERGE_DOMAIN_REJECTION_FLOW','IRIS_26520_V5_SPATIAL_RGB_TWO_SLOT_RAW_LIFETIME','IRIS_26520_V4_NORMAL_ONLY_DNG_READY','convertNormalizedBayer16ToSensorCode'):
    assert tok in iris, tok
for tok in ('IRIS_26520_V5_CONTINUOUS_FINEST_LK_TRANSPORT','IRIS_26521_V4_DIRECTIONAL_GREEN','IRIS_26521_V4_ROBUST_SPATIAL_KERNEL','IRIS_26521_V4_ROBUST_COLOR_DIFFERENCE'):
    assert tok in shader, tok
for tok in ('GlesMgcRawSabre','MgcSabre','ResolveSabre','PyramidAlignment'):
    assert tok not in iris+'\n'+shader
out.write_text(
 'baseHead=successful-26521-actions-artifact\n'
 'activeHdrxOwner=PhotonMotionMgc1271Bridge\n'
 'activeSpatialRgbOwner=GlesIris26521SpatialRgbStacker\n'
 'dngBase=26521 NORMAL-only same-alignment sidecar\n'
 'dngBaseSerialization=sensor-code-requantized\n'
)
print('PASS: exact successful-26521 Iris RGB/alignment/lifetime/DNG source contract verified')
PYACTIVE

echo "=== 26522 GATE 1B: prove COMPLETE 26522 transform in memory BEFORE writes ==="
python3 "$APPLY" "$BASE" --check-only | tee "$OUT/26522_in_memory_transform_proof.txt"

echo "=== 26522 GATE 2: patch FIRST, then exact candidate transform/validator + GLSL compile ==="
cp -a "$BASE/." "$AFTER/"
PATCH="$OUT/26522_RUNTIME_DELTA_FROM_SUCCESSFUL_26521.patch"
PATCH_SHA="$OUT/26522_RUNTIME_DELTA_FROM_SUCCESSFUL_26521.patch.sha256"
python3 "$APPLY" "$AFTER" --patch-out "$PATCH" --patch-sha-out "$PATCH_SHA"
( cd "$OUT" && sha256sum -c "$(basename "$PATCH_SHA")" )
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --apply "$APPLY" --patch "$PATCH" --patch-sha "$PATCH_SHA" | tee "$OUT/26522_prebuild_validator.txt"
python3 "$PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26522_glslang_preflight.txt"
[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "0.9726521" ]] || fail "version changed before guarded build block"
[[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "26521" ]] || fail "build changed before guarded build block"
echo "PRE-BUILD SAFETY PROOF PASSED"

echo "=== 26522 GATE 3: version $VERSION_NAME/$VERSION_BUILD + APK build in SAME guarded block ==="
python3 - "$AFTER/app/version.properties" "$VERSION_NAME" "$VERSION_BUILD" <<'PYVER'
from pathlib import Path
import sys
p=Path(sys.argv[1]); vn=sys.argv[2]; vb=sys.argv[3]; s=p.read_text()
assert 'VERSION_NAME=0.9726521' in s and 'VERSION_BUILD=26521' in s
s=s.replace('VERSION_NAME=0.9726521','VERSION_NAME='+vn,1).replace('VERSION_BUILD=26521','VERSION_BUILD='+vb,1)
p.write_text(s)
PYVER

# Exact vendor rehydration procedure inherited from successful 26521.
rm -rf "$BJ"
git init -q "$BJ"
git -C "$BJ" remote add origin https://github.com/bjzhou/PhotonCamera.git
git -C "$BJ" config core.sparseCheckout true
mkdir -p "$BJ/.git/info"
cat > "$BJ/.git/info/sparse-checkout" <<'SPARSEV'
/app/src/main/cpp/libjpeg-turbo/
/app/src/main/cpp/libultrahdr/
SPARSEV
git -C "$BJ" fetch --depth=1 origin "$BJZHOU_VENDOR_HEAD"
git -C "$BJ" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$BJ" rev-parse HEAD)" == "$BJZHOU_VENDOR_HEAD" ]] || fail "vendor checkout drift"
THIRD="$AFTER/app/src/main/cpp/third_party_26507"
rm -rf "$THIRD"; mkdir -p "$THIRD"
cp -a "$BJ/app/src/main/cpp/libjpeg-turbo" "$THIRD/libjpeg-turbo"
cp -a "$BJ/app/src/main/cpp/libultrahdr" "$THIRD/libultrahdr"
( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26522_vendor_manifest_check.txt"

rm -rf app/src/main
mkdir -p app/src
cp -a "$AFTER/app/src/main" app/src/main
cp "$AFTER/app/version.properties" app/version.properties

assert_cpp_deps_exact() {
  local phase="$1" expected actual
  if [[ "$phase" == pre ]]; then
    expected=$'.gitignore'
  else
    expected=$'.gitignore\narchive.h\narchive_entry.h\ntechnicallyflac.h\ntiny_dng_writer.h'
  fi
  actual="$(find app/src/main/cpp/deps -mindepth 1 -maxdepth 1 -type f -printf '%f\n' | LC_ALL=C sort)"
  [[ "$actual" == "$expected" ]] || fail "unexpected app/src/main/cpp/deps contents ($phase): [$actual]"
}
audited_runtime_manifest() {
  {
    find app/src/main -type f ! -path 'app/src/main/cpp/third_party_26507/*' ! -path 'app/src/main/cpp/deps/*' -print
    echo app/src/main/cpp/deps/.gitignore
    echo app/version.properties
  } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done
}
assert_cpp_deps_exact pre
audited_runtime_manifest > "$OUT/26522_pre_gradle_audited_runtime.sha256"
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace
assert_cpp_deps_exact post
audited_runtime_manifest > "$OUT/26522_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26522_pre_gradle_audited_runtime.sha256" "$OUT/26522_post_gradle_audited_runtime.sha256" || {
  diff -u "$OUT/26522_pre_gradle_audited_runtime.sha256" "$OUT/26522_post_gradle_audited_runtime.sha256" > "$OUT/26522_gradle_runtime_source_diff.txt" || true
  fail "Gradle mutated audited 26522 runtime source"
}
pass "Gradle preserved the validated 26522 runtime source; generated deps are exact"

python3 - "$ROOT" "$OUT/26522_post_gradle_active_owner_proof.txt" <<'PYPOST'
from pathlib import Path
import re,sys
root=Path(sys.argv[1]); out=Path(sys.argv[2])
hdr=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
bridge=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
fusion=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt').read_text()
iris=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt').read_text()
shader=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt').read_text()
saver=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java').read_text()
assert len(re.findall(r'PhotonMotionMgc1271Bridge\.reconstruct\s*\(',hdr))==1
assert len(re.findall(r'MotionV2CfaReconstruction\.reconstruct\s*\(',hdr))==0
marker='IRIS_26521_V5_INDEPENDENT_SPATIAL_RGB_OWNER_ACTIVE'; a=fusion.find(marker); b=fusion.find('        return GlesMgcRawSpatialStacker(',a)
assert a>=0 and b>a and fusion[a:b].count('GlesIris26521SpatialRgbStacker(')==1
for tok in ('IRIS_26520_V5_FINAL_FINEST_LK_OWNER','IRIS_26520_V5_MERGE_DOMAIN_REJECTION_FLOW','IRIS_26520_V5_SPATIAL_RGB_TWO_SLOT_RAW_LIFETIME','IRIS_26522_NORMALIZED16_DNG_FULL_PRECISION','IRIS_26522_DNG_EFFECTIVE_SUPPORT_STATS'):
    assert tok in iris, tok
for tok in ('IRIS_26520_V5_CONTINUOUS_FINEST_LK_TRANSPORT','IRIS_26522_DNG_EFFECTIVE_SUPPORT_ACCUMULATOR','IRIS_26522_DNG_EFFECTIVE_SUPPORT_Q8'):
    assert tok in shader, tok
for tok in ('dngCreator.setBitsPerSample(16)','dngCreator.setBlackLevel(new short[]{0, 0, 0, 0})','dngCreator.setWhiteLevel(65535.0)','dngCreator.setNoiseProfile(noiseProfile)'):
    assert tok in saver, tok
assert 'convertNormalizedBayer16ToSensorCode' not in iris
out.write_text(
 'activeHdrxOwner=PhotonMotionMgc1271Bridge\n'
 'activeSpatialRgbOwner=GlesIris26521SpatialRgbStacker_INHERITED\n'
 'alignmentRejectionRawLifetime=SUCCESSFUL_26521_FROZEN\n'
 'dngOwner=NORMAL_ONLY_SAME_ALIGNMENT_SIDECAR\n'
 'dngSampleDomain=BLACK_SUBTRACTED_NORMALIZED16\n'
 'dngBlackLevel=0\n'
 'dngWhiteLevel=65535\n'
 'dngNoiseProfile=CAMERA2_NORMALIZED/HARMONIC_EFFECTIVE_SUPPORT\n'
)
print('PASS: post-Gradle active JPEG/UHDR owner remains successful-26521 Iris Spatial RGB')
print('PASS: post-Gradle DNG is normalized16 NORMAL-only sidecar with measured support/noise metadata')
PYPOST

mapfile -t APKS < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' -print)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#APKS[@]}"
rm -f "$FINAL"
cp "${APKS[0]}" "$FINAL"
[[ -s "$FINAL" ]] || fail "final APK missing"
sha256sum "$FINAL" | tee "$OUT/26522_APK.sha256"

# Self-contained exact candidate source that produced the APK; vendor is build-only rehydration.
rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26522_candidate_source.sha256"
tar --sort=name --mtime='UTC 2026-08-21 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$OUT/26522_candidate_app_source.tar.gz" -C "$AFTER" app/src/main app/version.properties
sha256sum "$OUT/26522_candidate_app_source.tar.gz" > "$OUT/26522_candidate_app_source.tar.gz.sha256"
cat > "$OUT/26522_build_provenance.txt" <<PROOF
HANDOFF_START_HEAD=$START_HEAD
SUCCESSFUL_26521_HEAD=$SUCCESSFUL_26521_HEAD
SUCCESSFUL_26521_RUN_ID=$RUN_ID
26521_SOURCE_TAR_SHA256=$BASE_TAR_SHA
26521_SOURCE_MANIFEST_SHA256=$SOURCE_MANIFEST_SHA
VERSION_NAME=$VERSION_NAME
VERSION_BUILD=$VERSION_BUILD
JPEG_UHDR_OWNER=GlesIris26521SpatialRgbStacker_INHERITED_UNCHANGED
DNG_OWNER=NORMAL_ONLY_SAME_ALIGNMENT_SIDECAR
DNG_PIXEL_DOMAIN=BLACK_SUBTRACTED_NORMALIZED16
DNG_BLACK_LEVEL=0
DNG_WHITE_LEVEL=65535
DNG_NOISE_PROFILE=CAMERA2_NORMALIZED_DIVIDED_BY_HARMONIC_EFFECTIVE_SUPPORT
DNG_SUPPORT=SUM_W_SQUARED_OVER_SUM_W2_SAMPLED_128_LONG_EDGE
PROOF

pass "26522 exact successful-26521 capture/alignment/rejection/RGB architecture preserved"
pass "26522 normalized16 stacked DNG + measured effective support + stacked NoiseProfile completed"
pass "26522 APK, rollback patch, GLSL proof, post-Gradle audit, and manifest-verified candidate source artifact are complete"
