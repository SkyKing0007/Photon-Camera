#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
SUCCESSFUL_26525_HEAD="10b4cc9ce59c98b4c163878a87fe8a07168cc290"
BASE_WORKFLOW="build-26525-dng-zoom-parity.yml"
BASE_ARTIFACT="photon-26525-dng-zoom-parity-v1"
BASE_SOURCE_TAR_NAME="26525_candidate_app_source.tar.gz"
BASE_SOURCE_MANIFEST_NAME="26525_candidate_source.sha256"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"

APPLY="$ROOT/apply_26526_combined_zoom_temporal_audit.py"
VALIDATE="$ROOT/validate_26526_combined_zoom_temporal_audit.py"
AUDIT="$ROOT/audit_26526_temporal_support.py"
PREFLIGHT="$ROOT/preflight_26526_inherited_shaders.py"
HANDOFF="$ROOT/26526_HANDOFF_HASHES.sha256"
BASE_FILE="$ROOT/26526_BASE_26525_HEAD.txt"
PROVENANCE="$ROOT/26526_SCOPE_PROVENANCE.txt"

PREV_ZOOM_APPLY="$ROOT/apply_26524_continuous_zoom.py"
PREV_ZOOM_APPLY_SHA="056dbbd4c72bed95054682c22c90de3041f88af4dfcc53dab3f6efb240d96bf3"
PREV_DNG_APPLY="$ROOT/apply_26525_dng_zoom_parity.py"
PREV_DNG_APPLY_SHA="25522634fbcba20638ccf9637475b5ac200ebe6a17d8242733e7de4e06577bbb"

BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"

OUT="$ROOT/build_26526_combined_zoom_temporal_audit_outputs"
WORK="$ROOT/.build_26526_combined_zoom_temporal_audit_work"
ART="$WORK/26525_artifact"
BASE="$WORK/tested26525"
AFTER="$WORK/candidate26526"
BJ="$WORK/bjzhou_vendor"

VERSION_NAME="0.9726526"; VERSION_BUILD="26526"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-combined-zoom-temporal-audit-debug.apk"

rm -rf "$OUT" "$WORK"
mkdir -p "$OUT" "$ART" "$BASE" "$AFTER"
exec > >(tee "$OUT/26526_build.log") 2>&1

echo "=== 26526 GATE 0: exact successful-26525 lineage + handoff integrity ==="
BRANCH="$(git branch --show-current)"; START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch: $BRANCH"
git merge-base --is-ancestor "$SUCCESSFUL_26525_HEAD" HEAD || fail "handoff HEAD is not descended from successful 26525 V1.1"
[[ "$(tr -d '\r\n' < "$BASE_FILE")" == "$SUCCESSFUL_26525_HEAD" ]] || fail "base-26525 file drift"

for f in "$APPLY" "$VALIDATE" "$AUDIT" "$PREFLIGHT" "$HANDOFF" "$PROVENANCE"          "$PREV_ZOOM_APPLY" "$PREV_DNG_APPLY" "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do
  [[ -f "$f" ]] || fail "missing required file $(basename "$f")"
done

sha256sum -c "$HANDOFF"
[[ "$(sha "$PREV_ZOOM_APPLY")" == "$PREV_ZOOM_APPLY_SHA" ]] || fail "exact 26524 zoom transformer drift"
[[ "$(sha "$PREV_DNG_APPLY")" == "$PREV_DNG_APPLY_SHA" ]] || fail "exact 26525 DNG transformer drift"
python3 -m py_compile "$APPLY" "$VALIDATE" "$AUDIT" "$PREFLIGHT"
python3 "$APPLY" --self-test
bash -n "$0"
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_VENDOR_HEAD" ]] || fail "vendor dependency commit drift"

git diff --name-only "$SUCCESSFUL_26525_HEAD"..HEAD -- app/src/main app/version.properties   > "$OUT/26526_committed_runtime_drift_after_26525.txt"
[[ ! -s "$OUT/26526_committed_runtime_drift_after_26525.txt" ]] || fail "committed runtime drift after successful 26525"

git diff --name-only "$SUCCESSFUL_26525_HEAD"..HEAD --   gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties app/build.gradle app/proguard-rules.pro   > "$OUT/26526_protected_build_infrastructure_drift.txt"
[[ ! -s "$OUT/26526_protected_build_infrastructure_drift.txt" ]] || fail "protected build infrastructure drift after successful 26525"

command -v glslangValidator >/dev/null || fail "glslangValidator unavailable"
pass "26526 handoff-only lineage verified from successful 26525 V1.1"

echo "=== 26526 GATE 1: recover ACTUAL successful 26525 candidate-source artifact ==="
command -v gh >/dev/null || fail "GitHub CLI unavailable"
[[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing"
RUN_JSON="$WORK/26525_runs.json"
gh run list --repo "$REPO" --workflow "$BASE_WORKFLOW" --branch "$EXPECTED_BRANCH" --status success   --limit 50 --json databaseId,headSha,conclusion,createdAt > "$RUN_JSON"
RUN_ID="$(python3 - "$RUN_JSON" "$SUCCESSFUL_26525_HEAD" <<'PYRUN'
import json,sys
runs=json.load(open(sys.argv[1])); head=sys.argv[2]
exact=[r for r in runs if r.get("headSha")==head and r.get("conclusion")=="success"]
if not exact: raise SystemExit("no successful 26525 workflow at exact HEAD "+head)
exact.sort(key=lambda r:r.get("createdAt",""), reverse=True)
print(exact[0]["databaseId"])
PYRUN
)"
[[ "$RUN_ID" =~ ^[0-9]+$ ]] || fail "invalid successful-26525 run id"

gh run download "$RUN_ID" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$ART"
mapfile -t SOURCE_TARS < <(find "$ART" -type f -name "$BASE_SOURCE_TAR_NAME" -print)
mapfile -t SOURCE_MANIFESTS < <(find "$ART" -type f -name "$BASE_SOURCE_MANIFEST_NAME" -print)
[[ "${#SOURCE_TARS[@]}" -eq 1 && "${#SOURCE_MANIFESTS[@]}" -eq 1 ]] || fail "26525 source artifact cardinality mismatch"
SOURCE_TAR="${SOURCE_TARS[0]}"; SOURCE_MANIFEST="${SOURCE_MANIFESTS[0]}"
BASE_TAR_SHA="$(sha "$SOURCE_TAR")"; SOURCE_MANIFEST_SHA="$(sha "$SOURCE_MANIFEST")"

python3 - "$SOURCE_TAR" <<'PYTAR'
import sys,tarfile
with tarfile.open(sys.argv[1],"r:gz") as t:
    names=[m.name.lstrip("./") for m in t.getmembers() if m.name not in (".","./")]
for n in names:
    if not (n in {"app","app/","app/src","app/src/","app/src/main","app/src/main/","app/version.properties"}
            or n.startswith("app/src/main/")):
        raise SystemExit("unexpected path in 26525 candidate archive: "+n)
print("PASS: 26525 candidate archive contains runtime source + version only")
PYTAR

tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26525_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "0.9726525" ]] || fail "26525 base version mismatch"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "26525" ]] || fail "26525 base build mismatch"
pass "manifest-verified exact successful 26525 runtime recovered; repository app/src is not runtime authority"

echo "=== 26526 GATE 1A: exact active-owner, DNG, zoom and temporal prechange proof ==="
python3 "$AUDIT" --root "$BASE" --out "$OUT/26526_temporal_base_audit.json" | tee "$OUT/26526_temporal_base_audit.txt"

python3 - "$BASE" "$PREV_ZOOM_APPLY" <<'PYACTIVE'
from pathlib import Path
import hashlib,importlib.util,sys
root=Path(sys.argv[1]); prev=Path(sys.argv[2])
spec=importlib.util.spec_from_file_location("p26524",prev)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
zoom=(root/"app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java").read_text().replace("\r\n","\n")
if zoom != m.ZOOM_SOURCE.replace("\r\n","\n"):
    raise SystemExit("successful-26525 zoom owner differs from exact proven 26524 generated source")
cap=(root/"app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java").read_text()
for token in (
    "IRIS_26524_CAMERA2_ZOOM_REQUEST_OWNER",
    "IRIS_26524_ACTUAL_HAL_ZOOM_RESULT_OWNER",
    "PhotonCamera.getSettings().mCameraID",
):
    if token not in cap:
        raise SystemExit("successful-26525 CaptureController prechange owner missing: "+token)
import re
if re.search(r"\bCameraDevice\s+mCameraDevice\s*;", cap) is None:
    raise SystemExit("successful-26525 CaptureController CameraDevice mCameraDevice declaration missing")
print("PASS: successful-26525 camera-device field proven semantically (visibility-independent)")
saver=(root/"app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java").read_text()
dng=(root/"app/src/main/cpp/dngCreator.cpp").read_text()
for token in (
    "dngCreator.setDefaultCropZoom(parameters.motionV2OutputZoom);",
    "IRIS_26525_DNG_DEFAULT_CROP_ZOOM_PARITY",
):
    if token not in saver+dng: raise SystemExit("proven 26525 DNG crop anchor missing: "+token)
print("PASS: exact 26525 zoom/DNG prechange contract proven")
PYACTIVE

echo "=== 26526 GATE 1B: resolve COMPLETE transform + rollback patch BEFORE candidate writes ==="
PATCH="$OUT/26526_RUNTIME_DELTA_FROM_SUCCESSFUL_26525.patch"
PATCH_SHA="$OUT/26526_RUNTIME_DELTA_FROM_SUCCESSFUL_26525.patch.sha256"
python3 "$APPLY" "$BASE" --check-only --patch-out "$PATCH" --patch-sha-out "$PATCH_SHA"   | tee "$OUT/26526_in_memory_transform_proof.txt"
( cd "$OUT" && sha256sum -c "$(basename "$PATCH_SHA")" )
[[ -s "$PATCH" ]] || fail "26526 rollback/runtime patch missing"
pass "26526 runtime rollback patch exists and is hashed before candidate writes"

echo "=== 26526 GATE 2: exact two-file transform + protected-owner validation ==="
cp -a "$BASE/." "$AFTER/"
python3 "$APPLY" "$AFTER"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --patch "$PATCH" --patch-sha "$PATCH_SHA"   | tee "$OUT/26526_prebuild_validator.txt"

python3 "$AUDIT" --root "$AFTER" --out "$OUT/26526_temporal_candidate_audit.json"   | tee "$OUT/26526_temporal_candidate_audit.txt"
python3 - "$OUT/26526_temporal_base_audit.json" "$OUT/26526_temporal_candidate_audit.json" <<'PYTA'
import json,sys
a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2]))
if a["files"] != b["files"]:
    raise SystemExit("temporal image-math hashes changed in zoom build")
if b.get("temporalImageMathChanged") is not False:
    raise SystemExit("unexpected temporal image-math mutation")
print("PASS: exact temporal owner hashes unchanged by 26526 zoom correction")
PYTA

python3 "$PREFLIGHT" --root "$AFTER" --validator glslangValidator   | tee "$OUT/26526_inherited_shader_preflight.txt"

[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "0.9726525" ]] || fail "version changed before guarded build block"
[[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "26525" ]] || fail "build changed before guarded build block"
echo "PRE-BUILD SAFETY PROOF PASSED"

echo "=== 26526 GATE 3: version $VERSION_NAME/$VERSION_BUILD + APK build in SAME guarded block ==="
python3 - "$AFTER/app/version.properties" "$VERSION_NAME" "$VERSION_BUILD" <<'PYVER'
from pathlib import Path
import sys
p=Path(sys.argv[1]); vn=sys.argv[2]; vb=sys.argv[3]; s=p.read_text()
assert s.count("VERSION_NAME=0.9726525")==1 and s.count("VERSION_BUILD=26525")==1
p.write_text(s.replace("VERSION_NAME=0.9726525","VERSION_NAME="+vn,1)
              .replace("VERSION_BUILD=26525","VERSION_BUILD="+vb,1))
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
( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26526_vendor_manifest_check.txt"

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
audited_runtime_manifest > "$OUT/26526_pre_gradle_audited_runtime.sha256"
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace
assert_cpp_deps_exact post
audited_runtime_manifest > "$OUT/26526_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26526_pre_gradle_audited_runtime.sha256" "$OUT/26526_post_gradle_audited_runtime.sha256" || {
  diff -u "$OUT/26526_pre_gradle_audited_runtime.sha256" "$OUT/26526_post_gradle_audited_runtime.sha256"     > "$OUT/26526_gradle_runtime_source_diff.txt" || true
  fail "Gradle mutated audited 26526 runtime source"
}
pass "Gradle preserved validated 26526 runtime source; generated deps are exact"

echo "=== 26526 GATE 4: post-build sanitized deterministic proof ==="
POSTCHECK="$WORK/postbuild_runtime_for_validator"
rm -rf "$POSTCHECK"; mkdir -p "$POSTCHECK/app/src" "$POSTCHECK/app"
cp -a "$ROOT/app/src/main" "$POSTCHECK/app/src/main"
cp "$ROOT/app/version.properties" "$POSTCHECK/app/version.properties"

( cd "$ROOT/app/src/main/cpp/third_party_26507" && sha256sum -c "$BJZHOU_MANIFEST" )   > "$OUT/26526_postbuild_vendor_manifest_check.txt"

rm -rf "$POSTCHECK/app/src/main/cpp/third_party_26507"
rm -f   "$POSTCHECK/app/src/main/cpp/deps/archive.h"   "$POSTCHECK/app/src/main/cpp/deps/archive_entry.h"   "$POSTCHECK/app/src/main/cpp/deps/technicallyflac.h"   "$POSTCHECK/app/src/main/cpp/deps/tiny_dng_writer.h"

python3 "$VALIDATE" --base "$BASE" --candidate "$POSTCHECK" --patch "$PATCH" --patch-sha "$PATCH_SHA" --postbuild   | tee "$OUT/26526_postbuild_owner_proof.txt"
python3 "$AUDIT" --root "$POSTCHECK" --out "$OUT/26526_temporal_postbuild_audit.json"   | tee "$OUT/26526_temporal_postbuild_audit.txt"

mapfile -t APKS < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' -print)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#APKS[@]}"
rm -f "$FINAL"; cp "${APKS[0]}" "$FINAL"; [[ -s "$FINAL" ]] || fail "final APK missing"
sha256sum "$FINAL" | tee "$OUT/26526_APK.sha256"

rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; }   | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done )   > "$OUT/26526_candidate_source.sha256"

tar --sort=name --mtime='UTC 2026-08-22 00:00:00' --owner=0 --group=0 --numeric-owner   -czf "$OUT/26526_candidate_app_source.tar.gz" -C "$AFTER" app/src/main app/version.properties
sha256sum "$OUT/26526_candidate_app_source.tar.gz"   > "$OUT/26526_candidate_app_source.tar.gz.sha256"

cat > "$OUT/26526_build_provenance.txt" <<PROOF
HANDOFF_START_HEAD=$START_HEAD
SUCCESSFUL_26525_HEAD=$SUCCESSFUL_26525_HEAD
SUCCESSFUL_26525_RUN_ID=$RUN_ID
26525_SOURCE_TAR_SHA256=$BASE_TAR_SHA
26525_SOURCE_MANIFEST_SHA256=$SOURCE_MANIFEST_SHA
TARGET_VERSION=$VERSION_NAME
TARGET_BUILD=$VERSION_BUILD
RUNTIME_CHANGED_FILES=2
ZOOM_CAPTURE_RESULT_DRIVES_SOFTWARE_CROP=false
ZOOM_RESULT_IDENTITY=CameraCaptureSession.getDevice().getId()
ZOOM_HANDOFF_TRANSACTIONAL=true
ZOOM_HANDOFF_HYSTERESIS_FRACTION=0.02
DNG_26525_DEFAULT_CROP_CHANGED=false
TEMPORAL_IMAGE_MATH_CHANGED=false
TEMPORAL_SUPPORT_ACTION=EXACT_CANDIDATE_ARCHITECTURE_AUDIT_ONLY
LATEST_NON_SABRE_BJZHOU_REFERENCE=c317bf97d2649ae9296bc1459979ce63cb3364b2
PROOF

echo "PASS: 26526 COMBINED ZOOM + TEMPORAL ARCHITECTURE AUDIT BUILD COMPLETE"
echo "PASS: DNG/JPEG 1:1 CROP + ALL IMAGE-PRODUCING IQ OWNERS PRESERVED"
echo "PASS: CANDIDATE SOURCE + PROOF BUNDLE READY"
