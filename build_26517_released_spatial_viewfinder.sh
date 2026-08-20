#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
SUCCESSFUL_26516_V4_HEAD="ba6d23006dfb8aceb366e3f2bac72676b398afda"
BACKUP_26516="backup-26516-before-26517-released-spatial"
BASE_WORKFLOW="build-26516-profile-viewfinder-match.yml"
BASE_ARTIFACT="photon-26516-profile-viewfinder-match-v4"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"
RELEASE_SPATIAL_HEAD="c4ff5a3e99b5f9f6027ba1c038eb7cc850bb9b01"
RELEASE_STACKER_BLOB="24613918b7d830f19b573346ab02c9684e92eb6f"
RELEASE_SHADERS_BLOB="2d6aea082730d2f6d10f5c6e0930d6e2199006cc"
RELEASE_DIAGNOSTIC_GEOMETRY_BLOB="100420a4c0b0ea50e3c187889d1583fb50979480"
RELEASE_RGB_TILE_PLANNER_BLOB="5251813e721c1a81e9bde462296e26ae4cca24b2"
RELEASE_OUTPUT_EXPOSURE_BLOB="8d2bccc7816e1fa5873aa0ba0f390d477dcb15d5"
RELEASE_STRENGTH_GENERATOR_BLOB="ecd98a1cdefe2abc61fd5edc4209c07c295fef42"
APPLY="$ROOT/apply_26517_released_spatial_viewfinder.py"
VALIDATE="$ROOT/validate_26517_released_spatial_viewfinder.py"
HANDOFF="$ROOT/26517_HANDOFF_HASHES.sha256"
REF_FILE="$ROOT/26517_BJZHOU_RELEASE_SPATIAL_REF.txt"
OUT="$ROOT/build_26517_released_spatial_viewfinder_outputs"
WORK="$ROOT/.build_26517_direct_26516_work"
ART="$WORK/26516_artifact"; BASE="$WORK/tested26516"; AFTER="$WORK/candidate26517"
REL="$WORK/bjzhou_released_1271_spatial"; BJ="$WORK/bjzhou_vendor"
VERSION_NAME="0.9726517"; VERSION_BUILD="26517"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-released-spatial-viewfinder-debug.apk"
rm -rf "$OUT" "$WORK"; mkdir -p "$OUT" "$ART" "$BASE" "$AFTER"
exec > >(tee "$OUT/26517_build.log") 2>&1

echo "=== 26517 GATE 0: exact successful-26516 lineage + required backup + handoff-only commit ==="
BRANCH="$(git branch --show-current)"; START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch $BRANCH"
git merge-base --is-ancestor "$SUCCESSFUL_26516_V4_HEAD" HEAD || fail "26517 handoff is not descended from successful 26516 V4"
REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_26516" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$SUCCESSFUL_26516_V4_HEAD" ]] || fail "backup missing/wrong: $BACKUP_26516 -> ${REMOTE_BACKUP:-MISSING}; expected $SUCCESSFUL_26516_V4_HEAD"
for f in "$APPLY" "$VALIDATE" "$HANDOFF" "$REF_FILE" "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do [[ -f "$f" ]] || fail "missing $(basename "$f")"; done
sha256sum -c "$HANDOFF"
python3 -m py_compile "$APPLY" "$VALIDATE"
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_VENDOR_HEAD" ]] || fail "pinned vendor dependency commit drift"
grep -F "BJZHOU_RELEASE_SPATIAL_COMMIT=$RELEASE_SPATIAL_HEAD" "$REF_FILE" >/dev/null || fail "released Spatial commit manifest drift"
grep -F "GlesMgcRawSpatialStacker.kt_BLOB=$RELEASE_STACKER_BLOB" "$REF_FILE" >/dev/null || fail "released stacker blob manifest drift"
grep -F "GlesMgcRawSpatialShaders.kt_BLOB=$RELEASE_SHADERS_BLOB" "$REF_FILE" >/dev/null || fail "released shader blob manifest drift"
grep -F "MgcSpatialDiagnosticGeometry.kt_BLOB=$RELEASE_DIAGNOSTIC_GEOMETRY_BLOB" "$REF_FILE" >/dev/null || fail "released diagnostic geometry manifest drift"
grep -F "MgcSpatialRgbTilePlanner.kt_BLOB=$RELEASE_RGB_TILE_PLANNER_BLOB" "$REF_FILE" >/dev/null || fail "released RGB tile planner manifest drift"
grep -F "MgcSpatialOutputExposure.kt_BLOB=$RELEASE_OUTPUT_EXPOSURE_BLOB" "$REF_FILE" >/dev/null || fail "released output exposure manifest drift"
grep -F "MgcSpatialStrengthMapGenerator.kt_BLOB=$RELEASE_STRENGTH_GENERATOR_BLOB" "$REF_FILE" >/dev/null || fail "released strength generator manifest drift"
RUNTIME_DRIFT="$OUT/26517_committed_runtime_drift_after_26516_v4.txt"
git diff --name-only "$SUCCESSFUL_26516_V4_HEAD"..HEAD -- app/src/main app/version.properties > "$RUNTIME_DRIFT"
[[ ! -s "$RUNTIME_DRIFT" ]] || { cat "$RUNTIME_DRIFT" >&2; fail "committed runtime drift exists after successful 26516 V4"; }
PROTECTED_DRIFT="$OUT/26517_protected_build_infrastructure_drift.txt"
git diff --name-only "$SUCCESSFUL_26516_V4_HEAD"..HEAD -- gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties app/build.gradle app/proguard-rules.pro > "$PROTECTED_DRIFT"
[[ ! -s "$PROTECTED_DRIFT" ]] || { cat "$PROTECTED_DRIFT" >&2; fail "protected build infrastructure drifted after 26516 V4"; }
pass "successful 26516 V4 lineage + backup branch verified; no committed runtime/build drift"

echo "=== 26517 GATE 1: recover ACTUAL successful-26516 source + exact released 1.27.1 Spatial reference ==="
command -v gh >/dev/null || fail "GitHub CLI (gh) unavailable"; [[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing"
RUN_JSON="$WORK/26516_runs.json"
gh run list --repo "$REPO" --workflow "$BASE_WORKFLOW" --branch "$EXPECTED_BRANCH" --status success --limit 50 --json databaseId,headSha,conclusion,createdAt > "$RUN_JSON"
RUN_ID="$(python3 - "$RUN_JSON" "$SUCCESSFUL_26516_V4_HEAD" <<'PYRUN'
import json,sys
runs=json.load(open(sys.argv[1])); head=sys.argv[2]
exact=[r for r in runs if r.get('headSha')==head and r.get('conclusion')=='success']
if not exact: raise SystemExit('no successful 26516 V4 workflow run found at exact HEAD '+head)
print(exact[0]['databaseId'])
PYRUN
)"
[[ "$RUN_ID" =~ ^[0-9]+$ ]] || fail "invalid 26516 run id: $RUN_ID"
gh run download "$RUN_ID" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$ART"
mapfile -t SOURCE_TARS < <(find "$ART" -type f -name '26516_candidate_app_source.tar.gz' -print)
mapfile -t SOURCE_MANIFESTS < <(find "$ART" -type f -name '26516_candidate_source.sha256' -print)
[[ "${#SOURCE_TARS[@]}" -eq 1 && "${#SOURCE_MANIFESTS[@]}" -eq 1 ]] || fail "26516 source artifact cardinality mismatch"
SOURCE_TAR="${SOURCE_TARS[0]}"; SOURCE_MANIFEST="${SOURCE_MANIFESTS[0]}"; BASE_TAR_SHA="$(sha "$SOURCE_TAR")"; SOURCE_MANIFEST_SHA="$(sha "$SOURCE_MANIFEST")"
python3 - "$SOURCE_TAR" <<'PYTAR'
import sys,tarfile
with tarfile.open(sys.argv[1],'r:gz') as t: names=[m.name.lstrip('./') for m in t.getmembers() if m.name not in ('.','./')]
for n in names:
    if not (n in {'app','app/','app/src','app/src/','app/src/main','app/src/main/','app/version.properties'} or n.startswith('app/src/main/')): raise SystemExit('unexpected path in 26516 source archive: '+n)
print('PASS: 26516 source archive contains runtime source + version only')
PYTAR
tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26516_artifact_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties"|cut -d= -f2)" == "0.9726516" && "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties"|cut -d= -f2)" == "26516" ]] || fail "artifact source is not 0.9726516/26516"
grep -F 'IRIS_26516_BJZHOU_STYLE_VIEWFINDER_PRESENTATION_SOLVER' "$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java" >/dev/null || fail "26516 matcher owner missing"
grep -F 'IRIS_26516_DNG_PROFILE_HDR_PRESERVING_DOMAIN' "$BASE/app/src/main/assets/shaders/motionv2/color_transform.glsl" >/dev/null || fail "26516 profile owner missing"
BRIDGE_26516="$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt"
python3 - "$BRIDGE_26516" <<'PYBRIDGEARTIFACT'
from pathlib import Path
import sys
s = Path(sys.argv[1]).read_text()
for token in (
    'IRIS_26515_SHORT_BASELINE_DOMAIN',
    'parameters.motionV2MgcSourceExposureGain = baselineScale',
    'IRIS_26516_VIEWFINDER_PRESENTATION_AUTHORITY',
    'parameters.motionV2DisplayGain = 1.0f',
    'legacyRawDisplayGainDiagnostic=$referenceDisplayGain',
    'solverAfterProfileColor=true camera2Write=false',
    'legacyAssignmentsNeutralized=',
):
    if token not in s:
        raise SystemExit('recovered 26516 bridge runtime evidence missing: ' + token)
legacy = 'parameters.motionV2DisplayGain = referenceDisplayGain'
neutral = 'parameters.motionV2DisplayGain = 1.0f'
if legacy in s:
    raise SystemExit('recovered 26516 bridge still contains legacy referenceDisplayGain authority')
if s.count(neutral) < 2:
    raise SystemExit('recovered 26516 bridge did not neutralize every tested-26515 display path')
denoise_i = s.index('MgcFullResolutionDenoise.denoise(')
pair = ('parameters.motionV2MgcSourceExposureGain = baselineScale\n'
        '            parameters.motionV2DisplayGain = 1.0f')
pair_i = s.index(pair)
telemetry_i = s.index('IRIS_26516_VIEWFINDER_PRESENTATION_AUTHORITY', pair_i)
if not (denoise_i < pair_i < telemetry_i):
    raise SystemExit('recovered 26516 bridge runtime authority ordering drift')
print('PASS: recovered 26516 bridge V4 runtime authority matches successful 26516 validator')
PYBRIDGEARTIFACT
grep -F 'private val guideWidth = ceilDiv(width, 2)' "$BASE/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt" >/dev/null || fail "expected post-Sabre 09c Spatial guide missing"

rm -rf "$REL"; git init -q "$REL"; git -C "$REL" remote add origin https://github.com/bjzhou/PhotonCamera.git
git -C "$REL" config core.sparseCheckout true; mkdir -p "$REL/.git/info"
cat > "$REL/.git/info/sparse-checkout" <<'SPARSE'
/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt
/app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialDiagnosticGeometry.kt
/app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialRgbTilePlanner.kt
/app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialOutputExposure.kt
/app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialStrengthMapGenerator.kt
/app/build.gradle.kts
SPARSE
git -C "$REL" fetch --depth=1 origin "$RELEASE_SPATIAL_HEAD"; git -C "$REL" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$REL" rev-parse HEAD)" == "$RELEASE_SPATIAL_HEAD" ]] || fail "released Spatial checkout drift"
[[ "$(git -C "$REL" rev-parse HEAD:app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt)" == "$RELEASE_STACKER_BLOB" ]] || fail "released stacker blob drift"
[[ "$(git -C "$REL" rev-parse HEAD:app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt)" == "$RELEASE_SHADERS_BLOB" ]] || fail "released shader blob drift"
[[ "$(git -C "$REL" rev-parse HEAD:app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialDiagnosticGeometry.kt)" == "$RELEASE_DIAGNOSTIC_GEOMETRY_BLOB" ]] || fail "released diagnostic geometry blob drift"
[[ "$(git -C "$REL" rev-parse HEAD:app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialRgbTilePlanner.kt)" == "$RELEASE_RGB_TILE_PLANNER_BLOB" ]] || fail "released RGB tile planner blob drift"
[[ "$(git -C "$REL" rev-parse HEAD:app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialOutputExposure.kt)" == "$RELEASE_OUTPUT_EXPOSURE_BLOB" ]] || fail "released output exposure blob drift"
[[ "$(git -C "$REL" rev-parse HEAD:app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialStrengthMapGenerator.kt)" == "$RELEASE_STRENGTH_GENERATOR_BLOB" ]] || fail "released strength generator blob drift"
for helper in MgcSpatialDiagnosticGeometry.kt MgcSpatialRgbTilePlanner.kt MgcSpatialOutputExposure.kt; do
  cmp -s "$REL/app/src/main/java/com/hinnka/mycamera/processor/$helper" "$BASE/app/src/main/java/com/hinnka/mycamera/processor/$helper" || fail "released/current shared Spatial ABI helper drift: $helper"
done
pass "released/current diagnostic geometry, RGB tile planner, and output-exposure helpers are byte-identical"
python3 - "$REL/app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialStrengthMapGenerator.kt" "$BASE/app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialStrengthMapGenerator.kt" <<'PYABI'
import re,sys
def executable(path):
    s=open(path,encoding='utf-8').read()
    s=re.sub(r'/\*.*?\*/','',s,flags=re.S)
    s=re.sub(r'//[^\n]*','',s)
    return ''.join(s.split())
a=executable(sys.argv[1]); b=executable(sys.argv[2])
assert a==b, 'Spatial strength-map generator executable Kotlin drifted between c4ff and tested 26516'
print('PASS: Spatial strength-map generator executable Kotlin is identical after comment stripping')
PYABI
grep -F 'versionName = "1.27.1"' "$REL/app/build.gradle.kts" >/dev/null || fail "c4ff reference is not app version 1.27.1"
grep -F 'private val guideWidth = max(1, width / 4)' "$REL/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt" >/dev/null || fail "released quarter-guide contract missing"
! grep -F 'MgcRawProcessorPipeline' "$REL/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt" >/dev/null || fail "released reference unexpectedly contains Sabre processor contract"

# Dry-run the complete deterministic transform against the authenticated artifact before any candidate write.
python3 - "$APPLY" "$BASE" "$REL" "$OUT/26517_actual_artifact_transform_dry_run.txt" <<'PYDRY'
import importlib.util,sys
from pathlib import Path
script,root,relroot,out=map(Path,sys.argv[1:])
spec=importlib.util.spec_from_file_location('iris26517dry',script); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
released=mod.released_owner_texts(relroot); lines=[]
for rel in sorted(mod.CHANGED):
    p=root/rel
    if not p.is_file() and rel not in mod.NEW_FILES: raise SystemExit('tested-26516 artifact missing '+rel)
    old=p.read_text() if p.is_file() else ''; new=mod.expected_text(rel,old,released)
    if new==old: raise SystemExit('dry-run made no change '+rel)
    lines.append(f'PASS {rel} oldBytes={len(old)} newBytes={len(new)}')
out.write_text('\n'.join(lines)+'\n'); print('PASS: full 26517 transform resolves against actual tested-26516 artifact + pinned c4ff reference')
PYDRY
cat > "$OUT/26517_BASE_SOURCE_PROVENANCE.txt" <<EOF
BASE_HEAD=$SUCCESSFUL_26516_V4_HEAD
BASE_WORKFLOW=$BASE_WORKFLOW
BASE_ARTIFACT=$BASE_ARTIFACT
BASE_RUN_ID=$RUN_ID
BASE_SOURCE_TAR_SHA256=$BASE_TAR_SHA
BASE_SOURCE_MANIFEST_SHA256=$SOURCE_MANIFEST_SHA
RELEASE_SPATIAL_COMMIT=$RELEASE_SPATIAL_HEAD
RELEASE_STACKER_BLOB=$RELEASE_STACKER_BLOB
RELEASE_SHADERS_BLOB=$RELEASE_SHADERS_BLOB
SHARED_ABI_DIAGNOSTIC_GEOMETRY_BLOB=$RELEASE_DIAGNOSTIC_GEOMETRY_BLOB
SHARED_ABI_RGB_TILE_PLANNER_BLOB=$RELEASE_RGB_TILE_PLANNER_BLOB
SHARED_ABI_OUTPUT_EXPOSURE_BLOB=$RELEASE_OUTPUT_EXPOSURE_BLOB
RELEASE_STRENGTH_GENERATOR_BLOB=$RELEASE_STRENGTH_GENERATOR_BLOB
BACKUP_BRANCH=$BACKUP_26516
EOF
pass "actual 26516 runtime + exact released 1.27.1 Spatial reference proven before candidate writes"

echo "=== 26517 GATE 2: rollback patch FIRST; apply released Spatial route + symmetric matcher; exact validator ==="
cp -a "$BASE/." "$AFTER/"
PATCH="$OUT/26517_RUNTIME_DELTA_FROM_TESTED_26516.patch"; PATCH_SHA="$OUT/26517_RUNTIME_DELTA_FROM_TESTED_26516.patch.sha256"
python3 "$APPLY" "$AFTER" --released-root "$REL" --patch-out "$PATCH" --patch-sha-out "$PATCH_SHA"
( cd "$OUT" && sha256sum -c "$(basename "$PATCH_SHA")" )
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --released-root "$REL" --apply-script "$APPLY" --patch "$PATCH" --patch-sha "$PATCH_SHA" | tee "$OUT/26517_prebuild_validator.txt"
[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties"|cut -d= -f2)" == "0.9726516" && "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties"|cut -d= -f2)" == "26516" ]] || fail "version changed before guarded build block"
echo "PRE-BUILD SAFETY PROOF PASSED"
pass "rollback/audit patch existed before writes; released-owner exactness + frozen current owners + matcher invariants validated"

echo "=== 26517 GATE 3: VERSION ${VERSION_NAME}/${VERSION_BUILD} + APK build in SAME guarded block ==="
python3 - "$AFTER/app/version.properties" "$VERSION_NAME" "$VERSION_BUILD" <<'PYVER'
from pathlib import Path
import sys
p=Path(sys.argv[1]); vn=sys.argv[2]; vb=sys.argv[3]; s=p.read_text(); assert 'VERSION_NAME=0.9726516' in s and 'VERSION_BUILD=26516' in s
s=s.replace('VERSION_NAME=0.9726516','VERSION_NAME='+vn,1).replace('VERSION_BUILD=26516','VERSION_BUILD='+vb,1); p.write_text(s)
assert 'VERSION_NAME='+vn in p.read_text() and 'VERSION_BUILD='+vb in p.read_text()
PYVER
# Rehydrate exactly the same pinned JPEG/UHDR vendor trees as successful 26516.
rm -rf "$BJ"; git init -q "$BJ"; git -C "$BJ" remote add origin https://github.com/bjzhou/PhotonCamera.git; git -C "$BJ" config core.sparseCheckout true; mkdir -p "$BJ/.git/info"
cat > "$BJ/.git/info/sparse-checkout" <<'SPARSE'
/app/src/main/cpp/libjpeg-turbo/
/app/src/main/cpp/libultrahdr/
SPARSE
git -C "$BJ" fetch --depth=1 origin "$BJZHOU_VENDOR_HEAD"; git -C "$BJ" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$BJ" rev-parse HEAD)" == "$BJZHOU_VENDOR_HEAD" ]] || fail "pinned vendor checkout drift"
THIRD="$AFTER/app/src/main/cpp/third_party_26507"; rm -rf "$THIRD"; mkdir -p "$THIRD"; cp -a "$BJ/app/src/main/cpp/libjpeg-turbo" "$THIRD/libjpeg-turbo"; cp -a "$BJ/app/src/main/cpp/libultrahdr" "$THIRD/libultrahdr"
( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26517_bjzhou_vendor_manifest_check.txt"
rm -rf app/src/main; cp -a "$AFTER/app/src/main" app/src/main; cp "$AFTER/app/version.properties" app/version.properties
assert_cpp_deps_exact(){ local phase="$1" expected actual; if [[ "$phase" == pre ]]; then expected=$'.gitignore'; else expected=$'.gitignore\narchive.h\narchive_entry.h\ntechnicallyflac.h\ntiny_dng_writer.h'; fi; actual="$(find app/src/main/cpp/deps -mindepth 1 -maxdepth 1 -type f -printf '%f\n'|LC_ALL=C sort)"; [[ "$actual" == "$expected" ]] || fail "unexpected app/src/main/cpp/deps contents ($phase)"; }
audited_runtime_manifest(){ { find app/src/main -type f ! -path 'app/src/main/cpp/third_party_26507/*' ! -path 'app/src/main/cpp/deps/*' -print; echo app/src/main/cpp/deps/.gitignore; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done; }
assert_cpp_deps_exact pre; audited_runtime_manifest > "$OUT/26517_pre_gradle_audited_runtime.sha256"
chmod +x ./gradlew; ./gradlew clean :app:assembleDebug --stacktrace
assert_cpp_deps_exact post; audited_runtime_manifest > "$OUT/26517_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26517_pre_gradle_audited_runtime.sha256" "$OUT/26517_post_gradle_audited_runtime.sha256" || { diff -u "$OUT/26517_pre_gradle_audited_runtime.sha256" "$OUT/26517_post_gradle_audited_runtime.sha256" > "$OUT/26517_gradle_runtime_source_diff.txt" || true; fail "Gradle mutated audited 26517 runtime source"; }
pass "Gradle preserved tested-26516 + validated 26517 runtime source"
mapfile -t APKS < <(find app/build -type f -name '*.apk'|sort); [[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one APK, found ${#APKS[@]}"
[[ "$(basename "${APKS[0]}")" == "IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-debug.apk" ]] || fail "unexpected APK identity $(basename "${APKS[0]}")"
rm -f "$FINAL"; cp "${APKS[0]}" "$FINAL"; sha256sum "$FINAL" > "$OUT/26517_APK.sha256"
rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
( cd "$AFTER" && tar --sort=name --mtime='UTC 2026-08-20 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$OUT/26517_candidate_app_source.tar.gz" app/src/main app/version.properties )
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26517_candidate_source.sha256"
( cd "$AFTER" && sha256sum -c "$OUT/26517_candidate_source.sha256" ) > "$OUT/26517_candidate_source_manifest_check.txt"
cat >> "$OUT/26517_BASE_SOURCE_PROVENANCE.txt" <<EOF
FINAL_APK=$(basename "$FINAL")
FINAL_APK_SHA256=$(sha "$FINAL")
FINAL_SOURCE_TAR_SHA256=$(sha "$OUT/26517_candidate_app_source.tar.gz")
EOF
echo "=== 26517 SUCCESS ==="; echo "APK: $(basename "$FINAL")"; echo "APK SHA256: $(sha "$FINAL")"; echo "BASE_26516_RUN_ID=$RUN_ID"; echo "RELEASE_SPATIAL_HEAD=$RELEASE_SPATIAL_HEAD"
pass "26517 built directly from successful 26516 artifact + exact released-1.27.1 Spatial RGB owner + symmetric viewfinder estimator"
