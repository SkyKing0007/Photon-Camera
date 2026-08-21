#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
SUCCESSFUL_26518_HEAD="18582e3ca2c9a7fdaf5bb5c816036d215e887f95"
BASE_WORKFLOW="build-26518-released-spatial-abi.yml"
BASE_ARTIFACT="photon-26518-released-spatial-abi-v1"
BASE_SOURCE_TAR_NAME="26518_candidate_app_source.tar.gz"
BASE_SOURCE_MANIFEST_NAME="26518_candidate_source.sha256"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"

BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"
RELEASE_SPATIAL_HEAD="c4ff5a3e99b5f9f6027ba1c038eb7cc850bb9b01"
RELEASE_STACKER_BLOB="24613918b7d830f19b573346ab02c9684e92eb6f"
RELEASE_SHADERS_BLOB="2d6aea082730d2f6d10f5c6e0930d6e2199006cc"

MATCHER_REFERENCE="$ROOT/apply_26516_profile_viewfinder_match.py"
APPLY="$ROOT/apply_26519_per_lens_viewfinder_response.py"
VALIDATE="$ROOT/validate_26519_per_lens_viewfinder_response.py"
HANDOFF="$ROOT/26519_HANDOFF_HASHES.sha256"
REF_FILE="$ROOT/26519_BJZHOU_RELEASE_SPATIAL_REF.txt"

OUT="$ROOT/build_26519_per_lens_viewfinder_response_outputs"
WORK="$ROOT/.build_26519_direct_26518_work"
ART="$WORK/26518_artifact"
BASE="$WORK/tested26518"
AFTER="$WORK/candidate26519"
REL="$WORK/bjzhou_released_1271_spatial"
BJ="$WORK/bjzhou_vendor"

VERSION_NAME="0.9726519"; VERSION_BUILD="26519"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-per-lens-viewfinder-response-debug.apk"

rm -rf "$OUT" "$WORK"
mkdir -p "$OUT" "$ART" "$BASE" "$AFTER"
exec > >(tee "$OUT/26519_build.log") 2>&1

echo "=== 26519 GATE 0: exact successful-26518 lineage + no runtime drift + handoff integrity ==="
BRANCH="$(git branch --show-current)"
START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch $BRANCH"
git merge-base --is-ancestor "$SUCCESSFUL_26518_HEAD" HEAD || fail "26519 handoff is not descended from successful 26518"

for f in "$APPLY" "$VALIDATE" "$HANDOFF" "$REF_FILE" "$MATCHER_REFERENCE" "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do
  [[ -f "$f" ]] || fail "missing $(basename "$f")"
done
sha256sum -c "$HANDOFF"
python3 -m py_compile "$APPLY" "$VALIDATE" "$MATCHER_REFERENCE"
bash -n "$0"

[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_VENDOR_HEAD" ]] || fail "pinned vendor dependency commit drift"
grep -F "BJZHOU_RELEASE_SPATIAL_COMMIT=$RELEASE_SPATIAL_HEAD" "$REF_FILE" >/dev/null || fail "released Spatial commit manifest drift"
grep -F "GlesMgcRawSpatialStacker.kt_BLOB=$RELEASE_STACKER_BLOB" "$REF_FILE" >/dev/null || fail "released stacker blob manifest drift"

# User explicitly requested no new backup for 26519.
echo "NO_BACKUP_REQUESTED_BY_USER=true" > "$OUT/26519_backup_policy.txt"

RUNTIME_DRIFT="$OUT/26519_committed_runtime_drift_after_26518.txt"
git diff --name-only "$SUCCESSFUL_26518_HEAD"..HEAD -- app/src/main app/version.properties > "$RUNTIME_DRIFT"
[[ ! -s "$RUNTIME_DRIFT" ]] || { cat "$RUNTIME_DRIFT" >&2; fail "committed runtime drift exists after successful 26518"; }

PROTECTED_DRIFT="$OUT/26519_protected_build_infrastructure_drift.txt"
git diff --name-only "$SUCCESSFUL_26518_HEAD"..HEAD -- gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties app/build.gradle app/proguard-rules.pro > "$PROTECTED_DRIFT"
[[ ! -s "$PROTECTED_DRIFT" ]] || { cat "$PROTECTED_DRIFT" >&2; fail "protected build infrastructure drifted after successful 26518"; }

HISTORICAL_REF_DRIFT="$OUT/26519_26516_reference_drift.txt"
git diff --name-only "$SUCCESSFUL_26518_HEAD"..HEAD -- apply_26516_profile_viewfinder_match.py > "$HISTORICAL_REF_DRIFT"
[[ ! -s "$HISTORICAL_REF_DRIFT" ]] || { cat "$HISTORICAL_REF_DRIFT" >&2; fail "historical 26516 matcher reference was modified"; }
pass "successful 26518 lineage + no runtime/protected/reference drift; no-backup request recorded"

echo "=== 26519 GATE 1: recover ACTUAL successful-26518 source artifact + re-prove released c4ff owner ==="
command -v gh >/dev/null || fail "GitHub CLI (gh) unavailable"
[[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing"

RUN_JSON="$WORK/26518_runs.json"
gh run list --repo "$REPO" --workflow "$BASE_WORKFLOW" --branch "$EXPECTED_BRANCH" --status success --limit 50 --json databaseId,headSha,conclusion,createdAt > "$RUN_JSON"
RUN_ID="$(python3 - "$RUN_JSON" "$SUCCESSFUL_26518_HEAD" <<'PYRUN'
import json,sys
runs=json.load(open(sys.argv[1])); head=sys.argv[2]
exact=[r for r in runs if r.get('headSha')==head and r.get('conclusion')=='success']
if not exact: raise SystemExit('no successful 26518 workflow run found at exact HEAD '+head)
print(exact[0]['databaseId'])
PYRUN
)"
[[ "$RUN_ID" =~ ^[0-9]+$ ]] || fail "invalid 26518 run id: $RUN_ID"
gh run download "$RUN_ID" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$ART"

mapfile -t SOURCE_TARS < <(find "$ART" -type f -name "$BASE_SOURCE_TAR_NAME" -print)
mapfile -t SOURCE_MANIFESTS < <(find "$ART" -type f -name "$BASE_SOURCE_MANIFEST_NAME" -print)
[[ "${#SOURCE_TARS[@]}" -eq 1 && "${#SOURCE_MANIFESTS[@]}" -eq 1 ]] || fail "26518 source artifact cardinality mismatch"
SOURCE_TAR="${SOURCE_TARS[0]}"
SOURCE_MANIFEST="${SOURCE_MANIFESTS[0]}"
BASE_TAR_SHA="$(sha "$SOURCE_TAR")"
SOURCE_MANIFEST_SHA="$(sha "$SOURCE_MANIFEST")"

python3 - "$SOURCE_TAR" <<'PYTAR'
import sys,tarfile
with tarfile.open(sys.argv[1],'r:gz') as t:
    names=[m.name.lstrip('./') for m in t.getmembers() if m.name not in ('.','./')]
for n in names:
    if not (n in {'app','app/','app/src','app/src/','app/src/main','app/src/main/','app/version.properties'} or n.startswith('app/src/main/')):
        raise SystemExit('unexpected path in 26518 source archive: '+n)
print('PASS: 26518 source archive contains runtime source + version only')
PYTAR

tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26518_artifact_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties"|cut -d= -f2)" == "0.9726518" && "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties"|cut -d= -f2)" == "26518" ]] || fail "artifact source is not 0.9726518/26518"

MATCHER="$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java"
PREFS="$BASE/app/src/main/res/xml/preferences.xml"
STACK="$BASE/app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt"
FUSION="$BASE/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt"
BRIDGE="$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt"

grep -F 'IRIS_26517_SYMMETRIC_VIEWFINDER_PRESENTATION_SOLVER' "$MATCHER" >/dev/null || fail "successful 26518 matcher lineage missing"
grep -F 'reason=distribution_mismatch' "$MATCHER" >/dev/null || fail "26518 distribution-mismatch regression anchor missing"
! grep -F 'pref_motion_viewfinder_match_strength' "$PREFS" >/dev/null || fail "26519 slider unexpectedly already present"
grep -F 'IRIS_26518_RELEASED_1271_RESULT_ABI_SNR_BRIDGE' "$STACK" >/dev/null || fail "successful 26518 SNR ABI bridge missing"
grep -F 'mgcDenoiseTuningSnr = bayerKernelTuning.referenceSnr' "$STACK" >/dev/null || fail "26518 c4ff denoise SNR export missing"
grep -F 'mgcSharpenTuningSnr = bayerKernelTuning.referenceSnr' "$STACK" >/dev/null || fail "26518 c4ff sharpen SNR export missing"
grep -F 'private val guideWidth = max(1, width / 4)' "$STACK" >/dev/null || fail "released quarter-guide contract missing"
grep -F 'IRIS_26517_RELEASED_1271_SPATIAL_RGB_OWNER' "$FUSION" >/dev/null || fail "released route missing"
grep -F 'missing/malformed MGC tuning SNR' "$BRIDGE" >/dev/null || fail "bridge parity contract drifted"

# Exact c4ff reference, used only to prove 26518 pink-artifact-fixed owner is still pristine.
rm -rf "$REL"; git init -q "$REL"; git -C "$REL" remote add origin https://github.com/bjzhou/PhotonCamera.git
git -C "$REL" config core.sparseCheckout true; mkdir -p "$REL/.git/info"
cat > "$REL/.git/info/sparse-checkout" <<'SPARSE'
/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt
/app/build.gradle.kts
SPARSE
git -C "$REL" fetch --depth=1 origin "$RELEASE_SPATIAL_HEAD"
git -C "$REL" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$REL" rev-parse HEAD)" == "$RELEASE_SPATIAL_HEAD" ]] || fail "released Spatial checkout drift"
[[ "$(git -C "$REL" rev-parse HEAD:app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt)" == "$RELEASE_STACKER_BLOB" ]] || fail "released stacker blob drift"
[[ "$(git -C "$REL" rev-parse HEAD:app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt)" == "$RELEASE_SHADERS_BLOB" ]] || fail "released shaders blob drift"
grep -F 'versionName = "1.27.1"' "$REL/app/build.gradle.kts" >/dev/null || fail "c4ff reference is not version 1.27.1"

python3 - "$STACK" "$REL/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt" <<'PYC4'
from pathlib import Path
import sys
built=Path(sys.argv[1]).read_text().replace('\r\n','\n').replace('\r','\n')
up=Path(sys.argv[2]).read_text().replace('\r\n','\n').replace('\r','\n')
up=up.replace('GlesMgcRawSpatialStacker','GlesMgc1271ReleasedSpatialStacker').replace('GlesMgcRawSpatialShaders','GlesMgc1271ReleasedSpatialShaders')
abi='''                /* IRIS_26518_RELEASED_1271_RESULT_ABI_SNR_BRIDGE
                 * Released c4ff already computes bayerKernelTuning.referenceSnr and uses it for
                 * its Spatial kernel selection. Its historical RawStackResult predates the later
                 * process-local tuning-SNR fields. Export that same c4ff value into the newer ABI
                 * only; do not import post-Sabre Spatial tuning or Sabre TET attenuation math.
                 */
                mgcDenoiseTuningSnr = bayerKernelTuning.referenceSnr,
                mgcSharpenTuningSnr = bayerKernelTuning.referenceSnr,
'''
assert built.replace(abi,'',1)==up, '26518 owner is not exact c4ff + documented ABI bridge'
print('PASS: successful 26518 owner is exact c4ff + result-SNR ABI bridge only')
PYC4

cat > "$OUT/26519_BASE_SOURCE_PROVENANCE.txt" <<EOF
BASE_HEAD=$SUCCESSFUL_26518_HEAD
BASE_WORKFLOW=$BASE_WORKFLOW
BASE_ARTIFACT=$BASE_ARTIFACT
BASE_RUN_ID=$RUN_ID
BASE_SOURCE_TAR_SHA256=$BASE_TAR_SHA
BASE_SOURCE_MANIFEST_SHA256=$SOURCE_MANIFEST_SHA
RELEASE_SPATIAL_COMMIT=$RELEASE_SPATIAL_HEAD
RELEASE_STACKER_BLOB=$RELEASE_STACKER_BLOB
RELEASE_SHADERS_BLOB=$RELEASE_SHADERS_BLOB
NO_BACKUP_REQUESTED_BY_USER=true
MATCHER_REFERENCE=EXACT_26516_SOLVER_RELATIONSHIP
DEFAULT_RESPONSE_PERCENT=65
EOF
pass "actual successful 26518 source + frozen c4ff owner + 26516 matcher reference proven"

echo "=== 26519 GATE 2: patch FIRST; restore 26516 solver relationship + per-lens response slider; exact validator ==="
cp -a "$BASE/." "$AFTER/"
PATCH="$OUT/26519_RUNTIME_DELTA_FROM_TESTED_26518.patch"
PATCH_SHA="$OUT/26519_RUNTIME_DELTA_FROM_TESTED_26518.patch.sha256"
python3 "$APPLY" "$AFTER" --matcher-reference-script "$MATCHER_REFERENCE" --patch-out "$PATCH" --patch-sha-out "$PATCH_SHA"
( cd "$OUT" && sha256sum -c "$(basename "$PATCH_SHA")" )

python3 "$VALIDATE"   --base "$BASE" --candidate "$AFTER" --released-root "$REL"   --matcher-reference-script "$MATCHER_REFERENCE" --apply-script "$APPLY"   --patch "$PATCH" --patch-sha "$PATCH_SHA" | tee "$OUT/26519_prebuild_validator.txt"

[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties"|cut -d= -f2)" == "0.9726518" && "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties"|cut -d= -f2)" == "26518" ]] || fail "version changed before guarded build block"
echo "PRE-BUILD SAFETY PROOF PASSED"
pass "only matcher + settings slider changed; c4ff/ABI/bridge/render owners frozen"

echo "=== 26519 GATE 3: VERSION ${VERSION_NAME}/${VERSION_BUILD} + APK build in SAME guarded block ==="
python3 - "$AFTER/app/version.properties" "$VERSION_NAME" "$VERSION_BUILD" <<'PYVER'
from pathlib import Path
import sys
p=Path(sys.argv[1]); vn=sys.argv[2]; vb=sys.argv[3]
s=p.read_text()
assert 'VERSION_NAME=0.9726518' in s and 'VERSION_BUILD=26518' in s
s=s.replace('VERSION_NAME=0.9726518','VERSION_NAME='+vn,1).replace('VERSION_BUILD=26518','VERSION_BUILD='+vb,1)
p.write_text(s)
PYVER

# Rehydrate the exact same pinned JPEG/UHDR vendor trees used by this direct-artifact line.
rm -rf "$BJ"; git init -q "$BJ"; git -C "$BJ" remote add origin https://github.com/bjzhou/PhotonCamera.git
git -C "$BJ" config core.sparseCheckout true; mkdir -p "$BJ/.git/info"
cat > "$BJ/.git/info/sparse-checkout" <<'SPARSE'
/app/src/main/cpp/libjpeg-turbo/
/app/src/main/cpp/libultrahdr/
SPARSE
git -C "$BJ" fetch --depth=1 origin "$BJZHOU_VENDOR_HEAD"
git -C "$BJ" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$BJ" rev-parse HEAD)" == "$BJZHOU_VENDOR_HEAD" ]] || fail "pinned vendor checkout drift"

THIRD="$AFTER/app/src/main/cpp/third_party_26507"
rm -rf "$THIRD"; mkdir -p "$THIRD"
cp -a "$BJ/app/src/main/cpp/libjpeg-turbo" "$THIRD/libjpeg-turbo"
cp -a "$BJ/app/src/main/cpp/libultrahdr" "$THIRD/libultrahdr"
( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26519_bjzhou_vendor_manifest_check.txt"

# Overlay authenticated candidate runtime into this ephemeral Actions checkout.
rm -rf app/src/main
mkdir -p app/src
cp -a "$AFTER/app/src/main" app/src/main
cp "$AFTER/app/version.properties" app/version.properties

# Match the exact successful 26518 Gradle-mutation audit:
# - third_party_26507 is a temporary rehydrated vendor tree and is audited separately by its pinned manifest.
# - app/src/main/cpp/deps is populated by the build; only the known generated headers may appear.
# - every other runtime source file plus version.properties must remain byte-identical.
assert_cpp_deps_exact() {
  local phase="$1" expected actual
  if [[ "$phase" == pre ]]; then
    expected=$'.gitignore'
  else
    expected=$'.gitignore\narchive.h\narchive_entry.h\ntechnicallyflac.h\ntiny_dng_writer.h'
  fi
  actual="$(find app/src/main/cpp/deps -mindepth 1 -maxdepth 1 -type f -printf '%f\n' | LC_ALL=C sort)"
  [[ "$actual" == "$expected" ]] || fail "unexpected app/src/main/cpp/deps contents ($phase)"
}
audited_runtime_manifest() {
  {
    find app/src/main -type f \
      ! -path 'app/src/main/cpp/third_party_26507/*' \
      ! -path 'app/src/main/cpp/deps/*' -print
    echo app/src/main/cpp/deps/.gitignore
    echo app/version.properties
  } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done
}

assert_cpp_deps_exact pre
audited_runtime_manifest > "$OUT/26519_pre_gradle_audited_runtime.sha256"
./gradlew clean :app:assembleDebug --stacktrace
assert_cpp_deps_exact post
audited_runtime_manifest > "$OUT/26519_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26519_pre_gradle_audited_runtime.sha256" "$OUT/26519_post_gradle_audited_runtime.sha256" || {
  diff -u "$OUT/26519_pre_gradle_audited_runtime.sha256" "$OUT/26519_post_gradle_audited_runtime.sha256" \
    > "$OUT/26519_gradle_runtime_source_diff.txt" || true
  fail "Gradle mutated audited 26519 runtime source"
}
pass "Gradle preserved validated 26519 runtime source; generated deps matched exact 26518 contract"

mapfile -t APKS < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' -print)
[[ "${#APKS[@]}" -eq 1 ]] || { printf '%s\n' "${APKS[@]}" >&2; fail "expected exactly one debug APK, found ${#APKS[@]}"; }
rm -f "$FINAL"
cp "${APKS[0]}" "$FINAL"
[[ -s "$FINAL" ]] || fail "final APK missing/empty"
sha256sum "$FINAL" | tee "$OUT/26519_APK.sha256"

# Produce the next authenticated runtime source artifact.
SOURCE_OUT="$OUT/26519_candidate_app_source.tar.gz"
MANIFEST_OUT="$OUT/26519_candidate_source.sha256"
( cd "$AFTER" && find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum; sha256sum app/version.properties ) > "$MANIFEST_OUT"
tar -czf "$SOURCE_OUT" -C "$AFTER" app/src/main app/version.properties
( mkdir -p "$WORK/source_verify" && tar -xzf "$SOURCE_OUT" -C "$WORK/source_verify" && cd "$WORK/source_verify" && sha256sum -c "$MANIFEST_OUT" ) > "$OUT/26519_candidate_source_manifest_check.txt"

cat > "$OUT/26519_FINAL_PROVENANCE.txt" <<EOF
BUILD=0.9726519/26519
BASE_HEAD=$SUCCESSFUL_26518_HEAD
BASE_RUN_ID=$RUN_ID
BASE_ARTIFACT=$BASE_ARTIFACT
RELEASE_SPATIAL_COMMIT=$RELEASE_SPATIAL_HEAD
ACTIVE_SPATIAL_MODE=SPATIAL_RGB
C4FF_STACKER_FROZEN=true
C4FF_RESULT_SNR_ABI_FROZEN=true
MATCHER_RELATIONSHIP=26516_P25_P50_LOG_LUMA_SOLVER
VIEWFINDER_MATCH_STRENGTH_DEFAULT_PERCENT=65
REFERENCE_MAPPING=1.764EV_x_0.65_about_1.147EV
SLIDER_RANGE_PERCENT=0..100
PER_LENS=EXISTING_SAVE_PER_LENS_SETTINGS
FIXED_EV_CLAMP=false
DISTRIBUTION_MISMATCH_HARD_FALLBACK=false
CAMERA2_AE_SHUTTER_ISO_CHANGED=false
SHORT_LONG_CHANGED=false
MANUAL_IRIS_EXPOSURE_REMAINS_LATER=true
NO_BACKUP_REQUESTED_BY_USER=true
EOF

echo "PASS 1/3: authenticated successful 26518 + released c4ff pink-artifact fix preserved"
echo "PASS 2/3: exact 26516 adaptive solver restored with 0-100% per-lens response, default 65%"
echo "PASS 3/3: version/build increment + APK build completed in same guarded block"
