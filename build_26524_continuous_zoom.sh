#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
SUCCESSFUL_26523_HEAD="c53d891c698ec29efbe4152407f024dff49e9abe"
BASE_WORKFLOW="build-26523-ui-focus-temporal-support.yml"
BASE_ARTIFACT="photon-26523-ui-focus-temporal-support-v1"
BASE_SOURCE_TAR_NAME="26523_candidate_app_source.tar.gz"
BASE_SOURCE_MANIFEST_NAME="26523_candidate_source.sha256"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
APPLY="$ROOT/apply_26524_continuous_zoom.py"
VALIDATE="$ROOT/validate_26524_continuous_zoom.py"
PREFLIGHT="$ROOT/preflight_26524_zoom_shaders.py"
HANDOFF="$ROOT/26524_HANDOFF_HASHES.sha256"
BASE_FILE="$ROOT/26524_BASE_26523_HEAD.txt"
PROVENANCE="$ROOT/26524_SCOPE_PROVENANCE.txt"
BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"
OUT="$ROOT/build_26524_continuous_zoom_outputs"
WORK="$ROOT/.build_26524_continuous_zoom_work"
ART="$WORK/26523_artifact"
BASE="$WORK/tested26523"
AFTER="$WORK/candidate26524"
BJ="$WORK/bjzhou_vendor"
VERSION_NAME="0.9726524"; VERSION_BUILD="26524"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-continuous-zoom-debug.apk"

rm -rf "$OUT" "$WORK"
mkdir -p "$OUT" "$ART" "$BASE" "$AFTER"
exec > >(tee "$OUT/26524_build.log") 2>&1

echo "=== 26524 GATE 0: exact successful-26523 lineage + handoff integrity ==="
BRANCH="$(git branch --show-current)"; START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch: $BRANCH"
git merge-base --is-ancestor "$SUCCESSFUL_26523_HEAD" HEAD || fail "handoff HEAD is not descended from successful 26523"
[[ "$(tr -d '\r\n' < "$BASE_FILE")" == "$SUCCESSFUL_26523_HEAD" ]] || fail "base-26523 file drift"
for f in "$APPLY" "$VALIDATE" "$PREFLIGHT" "$HANDOFF" "$PROVENANCE" "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do
  [[ -f "$f" ]] || fail "missing required file $(basename "$f")"
done
sha256sum -c "$HANDOFF"
python3 -m py_compile "$APPLY" "$VALIDATE" "$PREFLIGHT"
bash -n "$0"
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_VENDOR_HEAD" ]] || fail "vendor dependency commit drift"
git diff --name-only "$SUCCESSFUL_26523_HEAD"..HEAD -- app/src/main app/version.properties > "$OUT/26524_committed_runtime_drift_after_26523.txt"
[[ ! -s "$OUT/26524_committed_runtime_drift_after_26523.txt" ]] || fail "committed runtime drift after successful 26523"
git diff --name-only "$SUCCESSFUL_26523_HEAD"..HEAD -- gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties app/build.gradle app/proguard-rules.pro > "$OUT/26524_protected_build_infrastructure_drift.txt"
[[ ! -s "$OUT/26524_protected_build_infrastructure_drift.txt" ]] || fail "protected build infrastructure drift after successful 26523"
command -v glslangValidator >/dev/null || fail "glslangValidator unavailable"
pass "26524 handoff-only lineage is directly descended from successful 26523"

echo "=== 26524 GATE 1: recover ACTUAL successful 26523 candidate-source artifact ==="
command -v gh >/dev/null || fail "GitHub CLI unavailable"
[[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing"
RUN_JSON="$WORK/26523_runs.json"
gh run list --repo "$REPO" --workflow "$BASE_WORKFLOW" --branch "$EXPECTED_BRANCH" --status success --limit 50 --json databaseId,headSha,conclusion,createdAt > "$RUN_JSON"
RUN_ID="$(python3 - "$RUN_JSON" "$SUCCESSFUL_26523_HEAD" <<'PYRUN'
import json,sys
runs=json.load(open(sys.argv[1])); head=sys.argv[2]
exact=[r for r in runs if r.get('headSha')==head and r.get('conclusion')=='success']
if not exact: raise SystemExit('no successful 26523 workflow at exact HEAD '+head)
exact.sort(key=lambda r:r.get('createdAt',''), reverse=True)
print(exact[0]['databaseId'])
PYRUN
)"
[[ "$RUN_ID" =~ ^[0-9]+$ ]] || fail "invalid successful-26523 run id"
gh run download "$RUN_ID" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$ART"
mapfile -t SOURCE_TARS < <(find "$ART" -type f -name "$BASE_SOURCE_TAR_NAME" -print)
mapfile -t SOURCE_MANIFESTS < <(find "$ART" -type f -name "$BASE_SOURCE_MANIFEST_NAME" -print)
[[ "${#SOURCE_TARS[@]}" -eq 1 && "${#SOURCE_MANIFESTS[@]}" -eq 1 ]] || fail "26523 source artifact cardinality mismatch"
SOURCE_TAR="${SOURCE_TARS[0]}"; SOURCE_MANIFEST="${SOURCE_MANIFESTS[0]}"
BASE_TAR_SHA="$(sha "$SOURCE_TAR")"; SOURCE_MANIFEST_SHA="$(sha "$SOURCE_MANIFEST")"
python3 - "$SOURCE_TAR" <<'PYTAR'
import sys,tarfile
with tarfile.open(sys.argv[1],'r:gz') as t:
    names=[m.name.lstrip('./') for m in t.getmembers() if m.name not in ('.','./')]
for n in names:
    if not (n in {'app','app/','app/src','app/src/','app/src/main','app/src/main/','app/version.properties'} or n.startswith('app/src/main/')):
        raise SystemExit('unexpected path in 26523 source archive: '+n)
print('PASS: 26523 candidate archive contains runtime source + version only')
PYTAR
tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26523_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "0.9726523" ]] || fail "26523 base version mismatch"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "26523" ]] || fail "26523 base build mismatch"
for marker in IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT_MOMENTS IRIS_26523_ACTIVE_CROP_FOCUS_MAPPING IRIS_26523_ABOUT_MINIMAL_IRIS; do
  grep -R -F "$marker" "$BASE/app/src/main" >/dev/null || fail "successful-26523 marker missing: $marker"
done
pass "manifest-verified successful 26523 runtime recovered; repository app/src is not runtime authority"

echo "=== 26524 GATE 1B: resolve COMPLETE transform + rollback patch BEFORE candidate writes ==="
PATCH="$OUT/26524_RUNTIME_DELTA_FROM_SUCCESSFUL_26523.patch"
PATCH_SHA="$OUT/26524_RUNTIME_DELTA_FROM_SUCCESSFUL_26523.patch.sha256"
python3 "$APPLY" "$BASE" --check-only --patch-out "$PATCH" --patch-sha-out "$PATCH_SHA" | tee "$OUT/26524_in_memory_transform_proof.txt"
( cd "$OUT" && sha256sum -c "$(basename "$PATCH_SHA")" )
[[ -s "$PATCH" ]] || fail "rollback/runtime patch missing"
pass "26524 rollback patch exists and is hashed before candidate runtime writes"

echo "=== 26524 GATE 2: apply exact transform + owner/GLSL validation ==="
cp -a "$BASE/." "$AFTER/"
python3 "$APPLY" "$AFTER"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --patch "$PATCH" --patch-sha "$PATCH_SHA" | tee "$OUT/26524_prebuild_validator.txt"
python3 "$PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26524_zoom_glslang_preflight.txt"
python3 "$ROOT/preflight_26523_iris_embedded_shaders.py" --root "$AFTER" --validator glslangValidator | tee "$OUT/26524_inherited_spatial_glslang_preflight.txt"
[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "0.9726523" ]] || fail "version changed before guarded build block"
[[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "26523" ]] || fail "build changed before guarded build block"
echo "PRE-BUILD SAFETY PROOF PASSED"

echo "=== 26524 GATE 3: version $VERSION_NAME/$VERSION_BUILD + APK build in SAME guarded block ==="
python3 - "$AFTER/app/version.properties" "$VERSION_NAME" "$VERSION_BUILD" <<'PYVER'
from pathlib import Path
import sys
p=Path(sys.argv[1]); vn=sys.argv[2]; vb=sys.argv[3]; s=p.read_text()
assert 'VERSION_NAME=0.9726523' in s and 'VERSION_BUILD=26523' in s
p.write_text(s.replace('VERSION_NAME=0.9726523','VERSION_NAME='+vn,1)
              .replace('VERSION_BUILD=26523','VERSION_BUILD='+vb,1))
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
( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26524_vendor_manifest_check.txt"

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
  { find app/src/main -type f ! -path 'app/src/main/cpp/third_party_26507/*' ! -path 'app/src/main/cpp/deps/*' -print
    echo app/src/main/cpp/deps/.gitignore
    echo app/version.properties
  } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done
}
assert_cpp_deps_exact pre
audited_runtime_manifest > "$OUT/26524_pre_gradle_audited_runtime.sha256"
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace
assert_cpp_deps_exact post
audited_runtime_manifest > "$OUT/26524_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26524_pre_gradle_audited_runtime.sha256" "$OUT/26524_post_gradle_audited_runtime.sha256" || {
  diff -u "$OUT/26524_pre_gradle_audited_runtime.sha256" "$OUT/26524_post_gradle_audited_runtime.sha256" > "$OUT/26524_gradle_runtime_source_diff.txt" || true
  fail "Gradle mutated audited 26524 runtime source"
}
pass "Gradle preserved validated 26524 runtime source; generated deps are exact"

echo "=== 26524 GATE 4: post-build exact deterministic runtime proof ==="
# V1.2: rerun the same deterministic validator after Gradle instead of relying
# on historical comment-marker names. This proves every allowlisted runtime
# file still equals the exact 26524 transform of successful 26523 and rechecks
# the protected MGC/Spatial RGB/DNG/support owners after the build.
python3 "$VALIDATE" \
  --base "$BASE" \
  --candidate "$ROOT" \
  --patch "$PATCH" \
  --patch-sha "$PATCH_SHA" \
  | tee "$OUT/26524_postbuild_owner_proof.txt"
pass "post-build runtime exactly equals deterministic 26524 transform; protected 26523 owners preserved"

mapfile -t APKS < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' -print)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#APKS[@]}"
rm -f "$FINAL"; cp "${APKS[0]}" "$FINAL"; [[ -s "$FINAL" ]] || fail "final APK missing"
sha256sum "$FINAL" | tee "$OUT/26524_APK.sha256"

rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26524_candidate_source.sha256"
tar --sort=name --mtime='UTC 2026-08-21 00:00:00' --owner=0 --group=0 --numeric-owner \
  -czf "$OUT/26524_candidate_app_source.tar.gz" -C "$AFTER" app/src/main app/version.properties
sha256sum "$OUT/26524_candidate_app_source.tar.gz" > "$OUT/26524_candidate_app_source.tar.gz.sha256"

cat > "$OUT/26524_build_provenance.txt" <<PROOF
HANDOFF_START_HEAD=$START_HEAD
SUCCESSFUL_26523_HEAD=$SUCCESSFUL_26523_HEAD
SUCCESSFUL_26523_RUN_ID=$RUN_ID
26523_SOURCE_TAR_SHA256=$BASE_TAR_SHA
26523_SOURCE_MANIFEST_SHA256=$SOURCE_MANIFEST_SHA
VERSION_NAME=$VERSION_NAME
VERSION_BUILD=$VERSION_BUILD
ACTIVE_BRANCH=$EXPECTED_BRANCH
ZOOM_MAX_WITH_TELE=50.0x
ZOOM_MAX_WITHOUT_TELE=20.0x
ZOOM_UI=LIVE_VALUE_INSIDE_OWNING_OPTICAL_BUTTON
PREVIEW=CAMERA2_ZOOM_PLUS_GPU_RESIDUAL
MOTION_JPEG=FULL_NATIVE_BINNED_DIMENSIONS_GPU_CROP
MOTION_DNG=FULL_NATIVE_BINNED_DATA_UNCHANGED
UHDR=FULL_RES_GAINMAP_GEOMETRY_MATCHED_TO_ZOOM
MGC_SPATIAL_RGB=SUCCESSFUL_26523_BYTE_IDENTICAL
DNG_SUPPORT=SUCCESSFUL_26523_BYTE_IDENTICAL
TEMPORAL_SUPPORT_RECOVERY=NOT_IN_26524
PROOF

pass "26524 exact successful-26523 Motion merge/DNG/support architecture preserved"
pass "26524 continuous cross-lens zoom + 50x/20x policy + focus/UI/full-size Motion JPEG geometry completed"
pass "26524 APK, pre-write rollback patch, GLSL proof, post-Gradle audit, and candidate source artifact are complete"
