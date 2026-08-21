#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
SUCCESSFUL_26519_HEAD="9b59a27235747733bacdde68bf6a888ebffefa18"
BACKUP_26519="backup-26519-before-26520-zsl-stacked-dng"
BASE_WORKFLOW="build-26519-per-lens-viewfinder-response.yml"
BASE_ARTIFACT="photon-26519-per-lens-viewfinder-response-v2"
BASE_SOURCE_TAR_NAME="26519_candidate_app_source.tar.gz"
BASE_SOURCE_MANIFEST_NAME="26519_candidate_source.sha256"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
RELEASE_SPATIAL_HEAD="c4ff5a3e99b5f9f6027ba1c038eb7cc850bb9b01"
RELEASE_STACKER_BLOB="24613918b7d830f19b573346ab02c9684e92eb6f"
RELEASE_SHADERS_BLOB="2d6aea082730d2f6d10f5c6e0930d6e2199006cc"
SPATIAL_RAW_SLOT_HEAD="0cecf08986eef838134d332ef34081faa632f56a"
SPATIAL_ALIGN_HEAD="b0d4c6926358c93f1698cc90263c78b14dd941f2"
SPATIAL_CONTINUOUS_HEAD="1b84bf860ba24aa826f981daa407fa213dc0590c"
BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"
APPLY_V4="$ROOT/apply_26520_v4_live_mgc_dng.py"
APPLY="$ROOT/apply_26520_v5_spatial_correctness.py"
VALIDATE="$ROOT/validate_26520_v5_spatial_correctness.py"
PREFLIGHT="$ROOT/preflight_26520_released_embedded_shaders.py"
HANDOFF="$ROOT/26520_V5_HANDOFF_HASHES.sha256"
BASE_FILE="$ROOT/26520_V5_BASE_26519_COMMIT.txt"
REF_FILE="$ROOT/26520_V5_BJZHOU_RELEASE_SPATIAL_REF.txt"
SPATIAL_PROVENANCE="$ROOT/26520_V5_SPATIAL_FIX_PROVENANCE.txt"
OUT="$ROOT/build_26520_v5_spatial_correctness_outputs"
WORK="$ROOT/.build_26520_v5_spatial_correctness_work"
ART="$WORK/26519_artifact"
BASE="$WORK/tested26519"
AFTER="$WORK/candidate26520"
REL="$WORK/bjzhou_released_c4ff"
BJ="$WORK/bjzhou_vendor"
VERSION_NAME="0.9726520"; VERSION_BUILD="26520"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v5-spatial-correctness-debug.apk"

rm -rf "$OUT" "$WORK"
mkdir -p "$OUT" "$ART" "$BASE" "$AFTER"
exec > >(tee "$OUT/26520_v5_build.log") 2>&1

echo "=== 26520 V5 GATE 0: exact 26519 lineage + backup + handoff integrity ==="
BRANCH="$(git branch --show-current)"
START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch: $BRANCH"
git merge-base --is-ancestor "$SUCCESSFUL_26519_HEAD" HEAD || fail "current handoff HEAD is not descended from successful 26519"
REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_26519" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$SUCCESSFUL_26519_HEAD" ]] || fail "backup missing/wrong: $BACKUP_26519 -> ${REMOTE_BACKUP:-MISSING}"
[[ "$(tr -d '\r\n' < "$BASE_FILE")" == "$SUCCESSFUL_26519_HEAD" ]] || fail "base-commit file drift"
for f in "$APPLY_V4" "$APPLY" "$VALIDATE" "$PREFLIGHT" "$HANDOFF" "$REF_FILE" "$SPATIAL_PROVENANCE" "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do
  [[ -f "$f" ]] || fail "missing required handoff/dependency file $(basename "$f")"
done
sha256sum -c "$HANDOFF"
python3 -m py_compile "$APPLY_V4" "$APPLY" "$VALIDATE" "$PREFLIGHT"
bash -n "$0"
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_VENDOR_HEAD" ]] || fail "26507 vendor dependency commit drift"
grep -F "BJZHOU_RELEASE_SPATIAL_COMMIT=$RELEASE_SPATIAL_HEAD" "$REF_FILE" >/dev/null || fail "c4ff reference commit drift"
grep -F "STACKER_BLOB=$RELEASE_STACKER_BLOB" "$REF_FILE" >/dev/null || fail "c4ff stacker blob drift"
grep -F "SHADERS_BLOB=$RELEASE_SHADERS_BLOB" "$REF_FILE" >/dev/null || fail "c4ff shader blob drift"
grep -F "RAW_SLOT_LIFETIME_COMMIT=$SPATIAL_RAW_SLOT_HEAD" "$SPATIAL_PROVENANCE" >/dev/null || fail "0cecf089 provenance drift"
grep -F "ALIGNMENT_ARCHITECTURE_COMMIT=$SPATIAL_ALIGN_HEAD" "$SPATIAL_PROVENANCE" >/dev/null || fail "b0d4 provenance drift"
grep -F "CONTINUOUS_TRANSPORT_COMMIT=$SPATIAL_CONTINUOUS_HEAD" "$SPATIAL_PROVENANCE" >/dev/null || fail "1b84 provenance drift"
grep -F "EXCLUDED_62927DB=true" "$SPATIAL_PROVENANCE" >/dev/null || fail "RawTilePlanner exclusion proof missing"
grep -F "DEFERRED_SPATIAL_CHROMA_IIR=true" "$SPATIAL_PROVENANCE" >/dev/null || fail "chroma/IIR deferral proof missing"
git diff --name-only "$SUCCESSFUL_26519_HEAD"..HEAD -- app/src/main app/version.properties > "$OUT/26520_committed_runtime_drift_after_26519.txt"
[[ ! -s "$OUT/26520_committed_runtime_drift_after_26519.txt" ]] || fail "committed runtime drift after successful 26519"
git diff --name-only "$SUCCESSFUL_26519_HEAD"..HEAD -- gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties app/build.gradle app/proguard-rules.pro > "$OUT/26520_protected_build_infrastructure_drift.txt"
[[ ! -s "$OUT/26520_protected_build_infrastructure_drift.txt" ]] || fail "protected build infrastructure drift after 26519"
pass "26520 V5 handoff-only lineage and exact 26519 rollback branch verified"

echo "=== 26520 V5 GATE 1: recover ACTUAL successful 26519 runtime artifact ==="
command -v gh >/dev/null || fail "GitHub CLI unavailable"
[[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing"
RUN_JSON="$WORK/26519_runs.json"
gh run list --repo "$REPO" --workflow "$BASE_WORKFLOW" --branch "$EXPECTED_BRANCH" --status success --limit 50 --json databaseId,headSha,conclusion,createdAt > "$RUN_JSON"
RUN_ID="$(python3 - "$RUN_JSON" "$SUCCESSFUL_26519_HEAD" <<'PYRUN'
import json,sys
runs=json.load(open(sys.argv[1])); head=sys.argv[2]
exact=[r for r in runs if r.get('headSha')==head and r.get('conclusion')=='success']
if not exact: raise SystemExit('no successful 26519 workflow at exact HEAD '+head)
exact.sort(key=lambda r:r.get('createdAt',''), reverse=True)
print(exact[0]['databaseId'])
PYRUN
)"
[[ "$RUN_ID" =~ ^[0-9]+$ ]] || fail "invalid 26519 run id"
gh run download "$RUN_ID" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$ART"
mapfile -t SOURCE_TARS < <(find "$ART" -type f -name "$BASE_SOURCE_TAR_NAME" -print)
mapfile -t SOURCE_MANIFESTS < <(find "$ART" -type f -name "$BASE_SOURCE_MANIFEST_NAME" -print)
[[ "${#SOURCE_TARS[@]}" -eq 1 && "${#SOURCE_MANIFESTS[@]}" -eq 1 ]] || fail "26519 source artifact cardinality mismatch"
SOURCE_TAR="${SOURCE_TARS[0]}"; SOURCE_MANIFEST="${SOURCE_MANIFESTS[0]}"
BASE_TAR_SHA="$(sha "$SOURCE_TAR")"; SOURCE_MANIFEST_SHA="$(sha "$SOURCE_MANIFEST")"
python3 - "$SOURCE_TAR" <<'PYTAR'
import sys,tarfile
with tarfile.open(sys.argv[1],'r:gz') as t:
    names=[m.name.lstrip('./') for m in t.getmembers() if m.name not in ('.','./')]
for n in names:
    if not (n in {'app','app/','app/src','app/src/','app/src/main','app/src/main/','app/version.properties'} or n.startswith('app/src/main/')):
        raise SystemExit('unexpected path in 26519 source archive: '+n)
print('PASS: 26519 source archive contains runtime source + version only')
PYTAR
tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26519_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "0.9726519" ]] || fail "base version name mismatch"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "26519" ]] || fail "base build mismatch"
pass "manifest-verified successful 26519 runtime recovered; repository app/src is not runtime authority"

echo "=== 26520 V5 GATE 1A: ACTIVE_PATH_PROOF before any transform ==="
python3 - "$BASE" "$OUT/26520_active_path_proof.txt" <<'PYACTIVE'
from pathlib import Path
import re,sys
root=Path(sys.argv[1]); out=Path(sys.argv[2])
hdr=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
bridge=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
fusion=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt').read_text()
stack=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt').read_text()
checks={
 'Hdrx PhotonMotionMgc1271Bridge.reconstruct call':len(re.findall(r'PhotonMotionMgc1271Bridge\.reconstruct\s*\(',hdr)),
 'Hdrx MotionV2CfaReconstruction.reconstruct call':len(re.findall(r'MotionV2CfaReconstruction\.reconstruct\s*\(',hdr)),
 'Fusion released-owner marker':fusion.count('IRIS_26517_RELEASED_1271_SPATIAL_RGB_OWNER'),
 'Released stacker ABI marker':stack.count('IRIS_26518_RELEASED_1271_RESULT_ABI_SNR_BRIDGE'),
}
assert checks['Hdrx PhotonMotionMgc1271Bridge.reconstruct call']==1, checks
assert checks['Hdrx MotionV2CfaReconstruction.reconstruct call']==0, checks
assert 'outputMode = MgcSpatialOutputMode.RGB' in bridge
assert 'mergeMethod = MgcMergeMethod.SPATIAL_RGB' in bridge
assert checks['Fusion released-owner marker']>=1
assert fusion.count('GlesMgc1271ReleasedSpatialStacker(')==1
assert checks['Released stacker ABI marker']==1
assert 'mgcDenoiseTuningSnr = bayerKernelTuning.referenceSnr' in stack
assert 'mgcSharpenTuningSnr = bayerKernelTuning.referenceSnr' in stack
out.write_text('\n'.join(f'{k}={v}' for k,v in checks.items())+'\nbridge outputMode=RGB\nbridge mergeMethod=SPATIAL_RGB\n')
print('PASS: active 26519 owner is Hdrx -> PhotonMotionMgc1271Bridge -> released-c4ff SPATIAL_RGB')
print('PASS: legacy MotionV2CfaReconstruction has zero active Hdrx reconstruct calls')
PYACTIVE

echo "=== 26520 V5 GATE 1B: exact released-c4ff provenance + only documented 26518 ABI delta ==="
rm -rf "$REL"
git init -q "$REL"
git -C "$REL" remote add origin https://github.com/bjzhou/PhotonCamera.git
git -C "$REL" config core.sparseCheckout true
mkdir -p "$REL/.git/info"
cat > "$REL/.git/info/sparse-checkout" <<'SPARSE'
/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt
SPARSE
git -C "$REL" fetch --depth=1 origin "$RELEASE_SPATIAL_HEAD"
git -C "$REL" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$REL" rev-parse HEAD)" == "$RELEASE_SPATIAL_HEAD" ]] || fail "c4ff checkout drift"
[[ "$(git -C "$REL" hash-object app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt)" == "$RELEASE_STACKER_BLOB" ]] || fail "c4ff stacker blob mismatch"
[[ "$(git -C "$REL" hash-object app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt)" == "$RELEASE_SHADERS_BLOB" ]] || fail "c4ff shader blob mismatch"
python3 - "$BASE" "$REL" "$OUT/26520_c4ff_provenance_proof.txt" <<'PYC4FF'
from pathlib import Path
import sys
base=Path(sys.argv[1]); rel=Path(sys.argv[2]); report=Path(sys.argv[3])
up_stack=(rel/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text().replace('\r\n','\n').replace('\r','\n')
up_shader=(rel/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt').read_text().replace('\r\n','\n').replace('\r','\n')
expected_stack=up_stack.replace('GlesMgcRawSpatialStacker','GlesMgc1271ReleasedSpatialStacker').replace('GlesMgcRawSpatialShaders','GlesMgc1271ReleasedSpatialShaders')
anchor='''                mgcSpatialStrengthMap = spatialNoiseModel?.strengthMap?.let(
                    ::mapSpatialStrengthToOutputCoordinates,
                ),
                mgcSpatialReferenceOnlyDiagnostic = referenceOnly,
'''
replacement='''                mgcSpatialStrengthMap = spatialNoiseModel?.strengthMap?.let(
                    ::mapSpatialStrengthToOutputCoordinates,
                ),
                /* IRIS_26518_RELEASED_1271_RESULT_ABI_SNR_BRIDGE
                 * Released c4ff already computes bayerKernelTuning.referenceSnr and uses it for
                 * its Spatial kernel selection. Its historical RawStackResult predates the later
                 * process-local tuning-SNR fields. Export that same c4ff value into the newer ABI
                 * only; do not import post-Sabre Spatial tuning or Sabre TET attenuation math.
                 */
                mgcDenoiseTuningSnr = bayerKernelTuning.referenceSnr,
                mgcSharpenTuningSnr = bayerKernelTuning.referenceSnr,
                mgcSpatialReferenceOnlyDiagnostic = referenceOnly,
'''
assert expected_stack.count(anchor)==1, 'upstream c4ff ABI anchor drift'
expected_stack=expected_stack.replace(anchor,replacement,1)
actual_stack=(base/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt').read_text().replace('\r\n','\n').replace('\r','\n')
expected_shader=up_shader.replace('GlesMgcRawSpatialShaders','GlesMgc1271ReleasedSpatialShaders')
actual_shader=(base/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialShaders.kt').read_text().replace('\r\n','\n').replace('\r','\n')
assert actual_stack==expected_stack, 'successful 26519 released stacker differs from exact c4ff + documented 26518 ABI bridge'
assert actual_shader==expected_shader, 'successful 26519 released shaders differ from exact renamed c4ff shaders'
for forbidden in ('MgcRawProcessorPipeline','MgcSpatialMergeTuning','MgcSabreResolveTuning','mgcSharpenAttenuationScale ='):
    assert forbidden not in actual_stack, 'forbidden post-c4ff hybrid token '+forbidden
report.write_text('releasedStacker=c4ff exact rename + 26518 two-field SNR ABI only\nreleasedShaders=c4ff exact rename only\n')
print('PASS: successful 26519 released stacker = exact c4ff + documented 26518 SNR ABI fields only')
print('PASS: successful 26519 released shaders = exact renamed c4ff shader source')
PYC4FF

echo "=== 26520 V5 GATE 1B2: pin audited Spatial-only upstream correction semantics ==="
git -C "$REL" fetch --depth=1 origin "$SPATIAL_RAW_SLOT_HEAD" "$SPATIAL_ALIGN_HEAD" "$SPATIAL_CONTINUOUS_HEAD"
for c in "$SPATIAL_RAW_SLOT_HEAD" "$SPATIAL_ALIGN_HEAD" "$SPATIAL_CONTINUOUS_HEAD"; do
  git -C "$REL" cat-file -e "$c^{commit}" || fail "missing audited upstream commit $c"
done
git -C "$REL" show "$SPATIAL_RAW_SLOT_HEAD:app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt" > "$WORK/upstream_0ce_stacker.kt"
git -C "$REL" show "$SPATIAL_ALIGN_HEAD:app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt" > "$WORK/upstream_b0d4_stacker.kt"
git -C "$REL" show "$SPATIAL_CONTINUOUS_HEAD:app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt" > "$WORK/upstream_1b84_shaders.kt"
python3 - "$WORK" "$OUT/26520_v5_upstream_spatial_semantics.txt" <<'PYSPATIAL'
from pathlib import Path
import re,sys
w=Path(sys.argv[1]); report=Path(sys.argv[2])
slot=(w/'upstream_0ce_stacker.kt').read_text()
align=(w/'upstream_b0d4_stacker.kt').read_text()
shader=(w/'upstream_1b84_shaders.kt').read_text()
for t in ('val rawSlots: IntArray','val passWindow: GlesGpuScheduler.PassWindow','rawSlots = intArrayOf(reusableRawTexture, secondRawTexture)','awaitResources(','reads = longArrayOf(rawResource)'):
    assert t in slot, '0ce Spatial RAW-lifetime semantic missing '+t
for t in ('renderMergeDomainFlow(bayerAlignment, flow)','upsampleL1=level-transitions-only/3-candidate','MergeBayer requires a valid finest-level LK alignment'):
    assert t in align, 'b0d4 Spatial alignment semantic missing '+t
m=re.search(r'val\s+convertBayerAlignment\s*=\s*"""(.*?)"""\.trimIndent\(\)',shader,re.S)
assert m, '1b84 convertBayerAlignment block missing'
block=m.group(1)
for t in ('vec2 resampledFlow(vec2 sourceGrid)','vec2 flow = resampledFlow(sourceGrid)','mix(flow00, flow10, fraction.x)'):
    assert t in block, '1b84 continuous transport semantic missing '+t
for t in ('cancelInterpolation','uInterpolationFlowTolerance','uAlignmentToBayerQuads'):
    assert t not in block, '1b84 coarse-grid/legacy token survived '+t
assert 'cancelInterpolation' in shader, '1b84 native merge discontinuity gate missing'
report.write_text('0ce=two tracked Spatial RAW slots\nb0d4=finest LK transported to merge domain; rejection derived from merge flow\n1b84=continuous LK resample before native merge gate\n')
print('PASS: exact upstream commits prove the three Spatial-only semantics being backported')
PYSPATIAL

echo "=== 26520 V5 GATE 1C: prove complete V5 transform against ACTUAL artifact BEFORE writes ==="
python3 "$APPLY" "$BASE" --apply-v4 "$APPLY_V4" --check-only | tee "$OUT/26520_v5_in_memory_transform_proof.txt"
python3 - "$BASE" <<'PYANCHOR'
from pathlib import Path
import sys
root=Path(sys.argv[1])
stack=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt').read_text()
required=(
 'val accumulatorColor = if (outputMode == MgcSpatialOutputMode.BAYER)',
 'clearAccumulator(accumulatorColor)',
 'rawTexture = referenceRaw',
 'val temporalFrameRange = if (referenceOnly)',
 'val prepared = prepareTemporalFrame(',
 'weightTexture = mergeWeight',
 'val bayer16 = renderBayer16(',
 'outputExposureScale = outputExposure.normalizationScale',
 'RawStackResult(',
 'val range = max(sensorWhiteLevel - canonicalBlackLevel[canonicalChannel], 1f)',
 'bayerPhaseGains[phase] = exposureScale / range',
)
for token in required:
    assert token in stack, 'required released-c4ff semantic anchor missing: '+token
assert 'normalStackedDngRaw16' not in stack
print('PASS: all live c4ff reference/temporal/Bayer-finalization/sensor-domain anchors exist before transform')
PYANCHOR

echo "=== 26520 V5 GATE 2: patch FIRST, then exact candidate transform/validation ==="
cp -a "$BASE/." "$AFTER/"
PATCH="$OUT/26520_V5_RUNTIME_DELTA_FROM_TESTED_26519.patch"
PATCH_SHA="$OUT/26520_V5_RUNTIME_DELTA_FROM_TESTED_26519.patch.sha256"
python3 "$APPLY" "$AFTER" --apply-v4 "$APPLY_V4" --patch-out "$PATCH" --patch-sha-out "$PATCH_SHA"
( cd "$OUT" && sha256sum -c "$(basename "$PATCH_SHA")" )
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --apply-v5 "$APPLY" --apply-v4 "$APPLY_V4" --patch "$PATCH" --patch-sha "$PATCH_SHA" | tee "$OUT/26520_v5_prebuild_validator.txt"
[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "0.9726519" ]] || fail "version changed before guarded build block"
[[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "26519" ]] || fail "build changed before guarded build block"
command -v glslangValidator >/dev/null || fail "pinned glslangValidator unavailable"
glslangValidator --version | head -1 | grep -F '16.5.0' >/dev/null || fail "unexpected glslang version"
python3 "$PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26520_v5_glslang_preflight.txt"
echo "PRE-BUILD SAFETY PROOF PASSED"

echo "=== 26520 V5 GATE 3: version $VERSION_NAME/$VERSION_BUILD + APK build in SAME guarded block ==="
python3 - "$AFTER/app/version.properties" "$VERSION_NAME" "$VERSION_BUILD" <<'PYVER'
from pathlib import Path
import sys
p=Path(sys.argv[1]); vn=sys.argv[2]; vb=sys.argv[3]; s=p.read_text()
assert 'VERSION_NAME=0.9726519' in s and 'VERSION_BUILD=26519' in s
s=s.replace('VERSION_NAME=0.9726519','VERSION_NAME='+vn,1).replace('VERSION_BUILD=26519','VERSION_BUILD='+vb,1)
p.write_text(s)
PYVER

# Rehydrate the exact successful 26507 bjzhou libjpeg-turbo/libultrahdr vendor closure used by 26519 lineage.
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
( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26520_vendor_manifest_check.txt"

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
audited_runtime_manifest > "$OUT/26520_pre_gradle_audited_runtime.sha256"
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace
assert_cpp_deps_exact post
audited_runtime_manifest > "$OUT/26520_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26520_pre_gradle_audited_runtime.sha256" "$OUT/26520_post_gradle_audited_runtime.sha256" || {
  diff -u "$OUT/26520_pre_gradle_audited_runtime.sha256" "$OUT/26520_post_gradle_audited_runtime.sha256" > "$OUT/26520_gradle_runtime_source_diff.txt" || true
  fail "Gradle mutated audited 26520 V5 runtime source"
}
pass "Gradle preserved the validated 26520 V5 runtime source; generated deps are exact"

# Post-Gradle active-owner proof uses the exact bytes that produced the APK.
python3 - "$ROOT" "$OUT/26520_post_gradle_active_owner_proof.txt" <<'PYPOST'
from pathlib import Path
import re,sys
root=Path(sys.argv[1]); out=Path(sys.argv[2])
hdr=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
bridge=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
fusion=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt').read_text()
stack=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt').read_text()
assert len(re.findall(r'PhotonMotionMgc1271Bridge\.reconstruct\s*\(',hdr))==1
assert len(re.findall(r'MotionV2CfaReconstruction\.reconstruct\s*\(',hdr))==0
assert 'IRIS_26520_V4_SHARED_NORMAL_BATCH_DNG' in hdr
assert 'exportNormalStackedDng = produceNormalStackedDng' in bridge
assert 'IRIS_26517_RELEASED_1271_SPATIAL_RGB_OWNER' in fusion
assert fusion.count('GlesMgc1271ReleasedSpatialStacker(')==1
assert 'IRIS_26520_V4_NORMAL_ONLY_DNG_READY' in stack
assert 'frame.role == RawBurstFrameRole.NORMAL' in stack
assert 'weightTexture = prepared.weightTexture' in stack
assert 'outputExposureScale = 1f' in stack
assert 'IRIS_26518_RELEASED_1271_RESULT_ABI_SNR_BRIDGE' in stack
assert 'IRIS_26520_V5_FINAL_FINEST_LK_OWNER' in stack
assert 'IRIS_26520_V5_MERGE_DOMAIN_REJECTION_FLOW' in stack
assert 'IRIS_26520_V5_SPATIAL_RGB_TWO_SLOT_RAW_LIFETIME' in stack
shaders=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialShaders.kt').read_text()
assert 'IRIS_26520_V5_CONTINUOUS_FINEST_LK_TRANSPORT' in shaders
assert 'vec2 flow = resampledFlow(sourceGrid)' in shaders
for tok in ('MgcRawProcessorPipeline','GlesMgcRawSabre','MgcSabre','ResolveSabre'):
    assert tok not in stack+'\n'+shaders, 'Sabre token leaked into released Spatial owner '+tok
out.write_text('activeHdrxOwner=PhotonMotionMgc1271Bridge\nactiveSpatialRgbOwner=GlesMgc1271ReleasedSpatialStacker\ndngOwner=normal-only c4ff Bayer sidecar\nspatialAlignment=continuous finest-LK to native merge-domain\nrawLifetime=two tracked RAW slots\n')
print('PASS: post-Gradle runtime still owns JPEG with released c4ff Spatial RGB and DNG with NORMAL-only sidecar')
PYPOST

mapfile -t APKS < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' -print)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#APKS[@]}"
rm -f "$FINAL"
cp "${APKS[0]}" "$FINAL"
[[ -s "$FINAL" ]] || fail "final APK missing"
sha256sum "$FINAL" | tee "$OUT/26520_V5_APK.sha256"

# Source artifact stays self-contained and excludes build-only third_party rehydration.
rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26520_candidate_source.sha256"
tar --sort=name --mtime='UTC 2026-08-21 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$OUT/26520_candidate_app_source.tar.gz" -C "$AFTER" app/src/main app/version.properties
sha256sum "$OUT/26520_candidate_app_source.tar.gz" > "$OUT/26520_candidate_app_source.tar.gz.sha256"
cat > "$OUT/26520_v5_build_provenance.txt" <<PROOF
HANDOFF_START_HEAD=$START_HEAD
SUCCESSFUL_26519_HEAD=$SUCCESSFUL_26519_HEAD
26519_RUN_ID=$RUN_ID
26519_SOURCE_TAR_SHA256=$BASE_TAR_SHA
26519_SOURCE_MANIFEST_SHA256=$SOURCE_MANIFEST_SHA
RELEASE_C4FF_HEAD=$RELEASE_SPATIAL_HEAD
VERSION_NAME=$VERSION_NAME
VERSION_BUILD=$VERSION_BUILD
JPEG_OWNER=GlesMgc1271ReleasedSpatialStacker_SPATIAL_RGB
DNG_OWNER=NORMAL_ONLY_LIVE_C4FF_BAYER_SIDECAR
SPATIAL_ALIGNMENT=FINAL_B0D4_PLUS_1B84_CONTINUOUS_FINEST_LK_TO_MERGE_DOMAIN
SPATIAL_RAW_LIFETIME=0CECF089_TWO_RESOURCE_TRACKED_RAW_SLOTS
PROOF

pass "26520 V5 Frame Count 1 + variable-count ZSL normal population + metadata-only grace are validated"
pass "26520 V5 JPEG/UHDR remains on released Spatial RGB with audited continuous alignment + two-slot RAW lifetime; no Sabre/hybrid owner"
pass "26520 V5 APK and manifest-verified candidate source artifact are complete"
