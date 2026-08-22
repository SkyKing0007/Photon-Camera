#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
SUCCESSFUL_26524_HEAD="b8547f3062e164759e5494b31ba595a07c4bfe69"
BASE_WORKFLOW="build-26524-continuous-zoom.yml"
BASE_ARTIFACT="photon-26524-continuous-zoom-v1"
BASE_SOURCE_TAR_NAME="26524_candidate_app_source.tar.gz"
BASE_SOURCE_MANIFEST_NAME="26524_candidate_source.sha256"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"

APPLY="$ROOT/apply_26525_dng_zoom_parity.py"
VALIDATE="$ROOT/validate_26525_dng_zoom_parity.py"
HANDOFF="$ROOT/26525_HANDOFF_HASHES.sha256"
BASE_FILE="$ROOT/26525_BASE_26524_HEAD.txt"
PROVENANCE="$ROOT/26525_SCOPE_PROVENANCE.txt"

BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"

OUT="$ROOT/build_26525_dng_zoom_parity_outputs"
WORK="$ROOT/.build_26525_dng_zoom_parity_work"
ART="$WORK/26524_artifact"
BASE="$WORK/tested26524"
AFTER="$WORK/candidate26525"
BJ="$WORK/bjzhou_vendor"

VERSION_NAME="0.9726525"; VERSION_BUILD="26525"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-dng-zoom-parity-debug.apk"

rm -rf "$OUT" "$WORK"
mkdir -p "$OUT" "$ART" "$BASE" "$AFTER"
exec > >(tee "$OUT/26525_build.log") 2>&1

echo "=== 26525 GATE 0: exact successful-26524 lineage + handoff integrity ==="
BRANCH="$(git branch --show-current)"; START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch: $BRANCH"
git merge-base --is-ancestor "$SUCCESSFUL_26524_HEAD" HEAD || fail "handoff HEAD is not descended from successful 26524"
[[ "$(tr -d '\r\n' < "$BASE_FILE")" == "$SUCCESSFUL_26524_HEAD" ]] || fail "base-26524 file drift"
for f in "$APPLY" "$VALIDATE" "$HANDOFF" "$PROVENANCE" "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do
  [[ -f "$f" ]] || fail "missing required file $(basename "$f")"
done
sha256sum -c "$HANDOFF"
python3 -m py_compile "$APPLY" "$VALIDATE"
bash -n "$0"
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_VENDOR_HEAD" ]] || fail "vendor dependency commit drift"

git diff --name-only "$SUCCESSFUL_26524_HEAD"..HEAD -- app/src/main app/version.properties \
  > "$OUT/26525_committed_runtime_drift_after_26524.txt"
[[ ! -s "$OUT/26525_committed_runtime_drift_after_26524.txt" ]] || fail "committed runtime drift after successful 26524"
git diff --name-only "$SUCCESSFUL_26524_HEAD"..HEAD -- \
  gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties app/build.gradle app/proguard-rules.pro \
  > "$OUT/26525_protected_build_infrastructure_drift.txt"
[[ ! -s "$OUT/26525_protected_build_infrastructure_drift.txt" ]] || fail "protected build infrastructure drift after successful 26524"
command -v glslangValidator >/dev/null || fail "glslangValidator unavailable"
pass "26525 handoff-only lineage is directly descended from successful 26524"

echo "=== 26525 GATE 1: recover ACTUAL successful 26524 candidate-source artifact ==="
command -v gh >/dev/null || fail "GitHub CLI unavailable"
[[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing"
RUN_JSON="$WORK/26524_runs.json"
gh run list --repo "$REPO" --workflow "$BASE_WORKFLOW" --branch "$EXPECTED_BRANCH" --status success \
  --limit 50 --json databaseId,headSha,conclusion,createdAt > "$RUN_JSON"
RUN_ID="$(python3 - "$RUN_JSON" "$SUCCESSFUL_26524_HEAD" <<'PYRUN'
import json,sys
runs=json.load(open(sys.argv[1])); head=sys.argv[2]
exact=[r for r in runs if r.get("headSha")==head and r.get("conclusion")=="success"]
if not exact: raise SystemExit("no successful 26524 workflow at exact HEAD "+head)
exact.sort(key=lambda r:r.get("createdAt",""), reverse=True)
print(exact[0]["databaseId"])
PYRUN
)"
[[ "$RUN_ID" =~ ^[0-9]+$ ]] || fail "invalid successful-26524 run id"

gh run download "$RUN_ID" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$ART"
mapfile -t SOURCE_TARS < <(find "$ART" -type f -name "$BASE_SOURCE_TAR_NAME" -print)
mapfile -t SOURCE_MANIFESTS < <(find "$ART" -type f -name "$BASE_SOURCE_MANIFEST_NAME" -print)
[[ "${#SOURCE_TARS[@]}" -eq 1 && "${#SOURCE_MANIFESTS[@]}" -eq 1 ]] || fail "26524 source artifact cardinality mismatch"
SOURCE_TAR="${SOURCE_TARS[0]}"; SOURCE_MANIFEST="${SOURCE_MANIFESTS[0]}"
BASE_TAR_SHA="$(sha "$SOURCE_TAR")"; SOURCE_MANIFEST_SHA="$(sha "$SOURCE_MANIFEST")"

python3 - "$SOURCE_TAR" <<'PYTAR'
import sys,tarfile
with tarfile.open(sys.argv[1],"r:gz") as t:
    names=[m.name.lstrip("./") for m in t.getmembers() if m.name not in (".","./")]
for n in names:
    if not (n in {"app","app/","app/src","app/src/","app/src/main","app/src/main/","app/version.properties"}
            or n.startswith("app/src/main/")):
        raise SystemExit("unexpected path in 26524 source archive: "+n)
print("PASS: 26524 candidate archive contains runtime source + version only")
PYTAR

tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26524_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "0.9726524" ]] || fail "26524 base version mismatch"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "26524" ]] || fail "26524 base build mismatch"

for marker in \
  IRIS_26524_FULLSIZE_MOTION_ZOOM_RENDER \
  IRIS_26524_UHDR_ZOOM_GEOMETRY_PARITY \
  IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT_MOMENTS \
  IRIS_26523_DNG_SINGLE_METADATA_OWNERSHIP; do
  grep -R -F "$marker" "$BASE/app/src/main" >/dev/null || fail "successful-26524 marker missing: $marker"
done
grep -F 'iris26524OutputLocalZoom' \
  "$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java" >/dev/null \
  || fail "successful-26524 frozen output-local zoom field missing"
pass "manifest-verified successful 26524 runtime recovered; repository app/src is not runtime authority"

echo "=== 26525 GATE 1A: freeze active IQ / zoom owners before DNG-only transform ==="
python3 - "$BASE" "$OUT/26525_frozen_owner_hashes.sha256" <<'PYOWN'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); out=Path(sys.argv[2])
paths=[
"app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt",
"app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt",
"app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt",
"app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java",
"app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java",
"app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java",
"app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java",
"app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java",
"app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java",
"app/src/main/assets/shaders/motionv2/render.glsl",
"app/src/main/assets/shaders/motionv2/gainmap.glsl",
"app/src/main/assets/shaders/preview/main_fs.glsl",
]
rows=[]
for rel in paths:
    p=root/rel
    if not p.is_file(): raise SystemExit("missing protected owner: "+rel)
    rows.append(hashlib.sha256(p.read_bytes()).hexdigest()+"  "+rel)
out.write_text("\n".join(rows)+"\n")
print("PASS: frozen 26524 MGC/Spatial/zoom/render/capture owner hashes recorded")
PYOWN

echo "=== 26525 GATE 1B: resolve COMPLETE transform + rollback patch BEFORE candidate writes ==="
PATCH="$OUT/26525_RUNTIME_DELTA_FROM_SUCCESSFUL_26524.patch"
PATCH_SHA="$OUT/26525_RUNTIME_DELTA_FROM_SUCCESSFUL_26524.patch.sha256"
python3 "$APPLY" "$BASE" --check-only --patch-out "$PATCH" --patch-sha-out "$PATCH_SHA" | tee "$OUT/26525_in_memory_transform_proof.txt"
( cd "$OUT" && sha256sum -c "$(basename "$PATCH_SHA")" )
[[ -s "$PATCH" ]] || fail "rollback/runtime patch missing"
pass "26525 rollback patch exists and is hashed before candidate runtime writes"

echo "=== 26525 GATE 2: apply exact four-file DNG transform + deterministic validation ==="
cp -a "$BASE/." "$AFTER/"
python3 "$APPLY" "$AFTER"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --patch "$PATCH" --patch-sha "$PATCH_SHA" | tee "$OUT/26525_prebuild_validator.txt"
python3 "$ROOT/preflight_26523_iris_embedded_shaders.py" --root "$AFTER" --validator glslangValidator | tee "$OUT/26525_inherited_spatial_glslang_preflight.txt"

[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "0.9726524" ]] || fail "version changed before guarded build block"
[[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "26524" ]] || fail "build changed before guarded build block"
echo "PRE-BUILD SAFETY PROOF PASSED"

echo "=== 26525 GATE 3: version $VERSION_NAME/$VERSION_BUILD + APK build in SAME guarded block ==="
python3 - "$AFTER/app/version.properties" "$VERSION_NAME" "$VERSION_BUILD" <<'PYVER'
from pathlib import Path
import sys
p=Path(sys.argv[1]); vn=sys.argv[2]; vb=sys.argv[3]; s=p.read_text()
assert s.count("VERSION_NAME=0.9726524")==1 and s.count("VERSION_BUILD=26524")==1
p.write_text(s.replace("VERSION_NAME=0.9726524","VERSION_NAME="+vn,1)
              .replace("VERSION_BUILD=26524","VERSION_BUILD="+vb,1))
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
( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26525_vendor_manifest_check.txt"

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
audited_runtime_manifest > "$OUT/26525_pre_gradle_audited_runtime.sha256"
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace
assert_cpp_deps_exact post
audited_runtime_manifest > "$OUT/26525_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26525_pre_gradle_audited_runtime.sha256" "$OUT/26525_post_gradle_audited_runtime.sha256" || {
  diff -u "$OUT/26525_pre_gradle_audited_runtime.sha256" "$OUT/26525_post_gradle_audited_runtime.sha256" > "$OUT/26525_gradle_runtime_source_diff.txt" || true
  fail "Gradle mutated audited 26525 runtime source"
}
pass "Gradle preserved validated 26525 runtime source; generated deps are exact"

echo "=== 26525 GATE 4: generated TinyDNG + post-build deterministic runtime proof ==="
python3 - "app/src/main/cpp/deps/tiny_dng_writer.h" <<'PYHDR'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
for token in (
    "IRIS_26525_TINYDNG_DEFAULT_CROP_TAGS",
    "TIFFTAG_DEFAULT_CROP_ORIGIN = 50719",
    "TIFFTAG_DEFAULT_CROP_SIZE = 50720",
    "IRIS_26525_TINYDNG_DEFAULT_CROP_API",
    "IRIS_26525_TINYDNG_DEFAULT_CROP_IMPL",
    "TIFFTAG_DEFAULT_CROP_ORIGIN), TIFF_LONG, 2",
    "TIFFTAG_DEFAULT_CROP_SIZE), TIFF_LONG, 2",
):
    assert token in s, token
assert s.count("bool DNGImage::SetDefaultCrop(")==1
print("PASS: generated pinned TinyDNG contains exact DefaultCrop LONG[2] extension")
PYHDR

POSTCHECK="$WORK/postbuild_runtime_for_validator"
rm -rf "$POSTCHECK"; mkdir -p "$POSTCHECK/app/src" "$POSTCHECK/app"
cp -a "$ROOT/app/src/main" "$POSTCHECK/app/src/main"
cp "$ROOT/app/version.properties" "$POSTCHECK/app/version.properties"
( cd "$ROOT/app/src/main/cpp/third_party_26507" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26525_postbuild_vendor_manifest_check.txt"
rm -rf "$POSTCHECK/app/src/main/cpp/third_party_26507"
rm -f "$POSTCHECK/app/src/main/cpp/deps/archive.h" "$POSTCHECK/app/src/main/cpp/deps/archive_entry.h" \
      "$POSTCHECK/app/src/main/cpp/deps/technicallyflac.h" "$POSTCHECK/app/src/main/cpp/deps/tiny_dng_writer.h"

python3 "$VALIDATE" --base "$BASE" --candidate "$POSTCHECK" --patch "$PATCH" --patch-sha "$PATCH_SHA" --postbuild | tee "$OUT/26525_postbuild_owner_proof.txt"
pass "post-build sanitized runtime exactly equals deterministic 26525 transform; IQ/zoom owners preserved"

mapfile -t APKS < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' -print)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#APKS[@]}"
rm -f "$FINAL"; cp "${APKS[0]}" "$FINAL"; [[ -s "$FINAL" ]] || fail "final APK missing"
sha256sum "$FINAL" | tee "$OUT/26525_APK.sha256"

rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26525_candidate_source.sha256"
tar --sort=name --mtime='UTC 2026-08-22 00:00:00' --owner=0 --group=0 --numeric-owner \
  -czf "$OUT/26525_candidate_app_source.tar.gz" -C "$AFTER" app/src/main app/version.properties
sha256sum "$OUT/26525_candidate_app_source.tar.gz" > "$OUT/26525_candidate_app_source.tar.gz.sha256"

cat > "$OUT/26525_build_provenance.txt" <<PROOF
HANDOFF_START_HEAD=$START_HEAD
SUCCESSFUL_26524_HEAD=$SUCCESSFUL_26524_HEAD
SUCCESSFUL_26524_RUN_ID=$RUN_ID
26524_SOURCE_TAR_SHA256=$BASE_TAR_SHA
26524_SOURCE_MANIFEST_SHA256=$SOURCE_MANIFEST_SHA
TARGET_VERSION=$VERSION_NAME
TARGET_BUILD=$VERSION_BUILD
RUNTIME_CHANGED_FILES=4
TEMPORAL_MERGE_MATH_CHANGED=false
MULTIFRAME_SR_CHANGED=false
DNG_PIXEL_PAYLOAD_RESAMPLED=false
DNG_DEFAULT_CROP_AUTHORITY=parameters.iris26524OutputLocalZoom
TINYDNG_PINNED_COMMIT=857590b3997818a4ccfbb8a42dd21c76273d6837
TINYDNG_PINNED_GIT_BLOB=624d614bf3e3bccb394ec54d1bca5bbb350859be
PROOF

echo "PASS: 26525 DNG DEFAULT-CROP ZOOM PARITY BUILD COMPLETE"
echo "PASS: MGC/SPATIAL/JPEG/UHDR/TEMPORAL SUPPORT MATH PRESERVED"
echo "PASS: CANDIDATE SOURCE + EXACT PROOF BUNDLE READY FOR 26526"
