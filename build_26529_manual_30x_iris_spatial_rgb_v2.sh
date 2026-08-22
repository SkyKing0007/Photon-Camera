#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
SUCCESSFUL_26528_HEAD="2b1d34f64b86fc39820aaa8ed0c96cad24c77bd9"
BASE_WORKFLOW="build-26528-optical-handoff-ui-thread.yml"
BASE_ARTIFACT="photon-26528-optical-handoff-ui-thread-v1"
BASE_SOURCE_TAR_NAME="26528_candidate_app_source.tar.gz"
BASE_SOURCE_MANIFEST_NAME="26528_candidate_source.sha256"
EXPECTED_BASE_TAR_SHA="d6e21f4249d0d2f2171ad469436ce5a9e545fb0d84f85a1d6a3a93ee71e5dff2"
EXPECTED_BASE_MANIFEST_SHA="1f3fb4d1033064c970dbf7df279d75b336a4ed8c1d4d831fe4f7f85770e3c166"
EXPECTED_BASE_FILES=948
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"

APPLY="$ROOT/apply_26529_manual_30x_iris_spatial_rgb_v2.py"
VALIDATE="$ROOT/validate_26529_manual_30x_iris_spatial_rgb_v2.py"
SHADER_PREFLIGHT="$ROOT/preflight_26529_iris_embedded_shaders_v2.py"
AUDIT_REFERENCE="$ROOT/audit_26529_bjzhou_semantic_reference_v2.py"
IRIS_TEMPLATE="$ROOT/26529_IRIS_SPATIAL_RGB_CHROMA_REWRITE.kt"
EXPECTED_PATCH="$ROOT/26529_V2_RUNTIME_DELTA_FROM_SUCCESSFUL_26528.patch"
EXPECTED_PATCH_SHA="$ROOT/26529_V2_RUNTIME_DELTA_FROM_SUCCESSFUL_26528.patch.sha256"
EXPECTED_ROLLBACK="$ROOT/26529_V2_RUNTIME_ROLLBACK_TO_SUCCESSFUL_26528.patch"
EXPECTED_ROLLBACK_SHA="$ROOT/26529_V2_RUNTIME_ROLLBACK_TO_SUCCESSFUL_26528.patch.sha256"
IRIS_TEMPLATE_SHA="5e112314f0795e4294e3af9e8b127d7d86cdfa494cd8df042fd5c6ba9d7949a4"
HANDOFF="$ROOT/26529_V2_HANDOFF_HASHES.sha256"
BASE_FILE="$ROOT/26529_BASE_26528_HEAD.txt"
PROVENANCE="$ROOT/26529_V2_SCOPE_PROVENANCE.txt"
PROJECT_RULES="$ROOT/26529_V2_PROJECT_RULES.txt"
INHERITED_SHADER_PREFLIGHT="$ROOT/preflight_26526_inherited_shaders.py"
NATIVE_PREFLIGHT="$ROOT/preflight_26527_native_syntax.py"
DNG_TEST="$ROOT/test_26527_dng_subifd.py"
PREV_HANDOFF="$ROOT/26528_HANDOFF_HASHES.sha256"
INHERITED_SHADER_PREFLIGHT_SHA="638376dd1b6d770cd8d91d3e35ff3d61e6847ab3277b64b446976a88e43b9e2b"

BJZHOU_SPATIAL_HEAD="c317bf97d2649ae9296bc1459979ce63cb3364b2"
BJZHOU_POST_REL="app/src/main/java/com/hinnka/mycamera/processor/GlesMgcSpatialRgbChromaPostprocessor.kt"
BJZHOU_POST_BLOB="5f29df5461cb50b199a6b19eea096127bf4af35c"
BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"

OUT="$ROOT/build_26529_manual_30x_iris_spatial_rgb_v2_outputs"
WORK="$ROOT/.build_26529_manual_30x_iris_spatial_rgb_v2_work"
ART="$WORK/26528_artifact"
BASE="$WORK/tested26528"
AFTER="$WORK/candidate26529"
POSTCHECK="$WORK/postbuild26529"
VERIFY_NEXT="$WORK/verify_next_candidate"
BJSP="$WORK/bjzhou_spatial"
BJ="$WORK/bjzhou_vendor"
VENDOR_POST="$WORK/GlesMgcSpatialRgbChromaPostprocessor.c317.kt"

VERSION_NAME="0.9726529"; VERSION_BUILD="26529"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-manual-30x-iris-spatial-rgb-v2-debug.apk"

rm -rf "$OUT" "$WORK" "$FINAL"
mkdir -p "$OUT" "$ART" "$BASE" "$AFTER"
exec > >(tee "$OUT/26529_build.log") 2>&1

echo "=== 26529 GATE 0: exact successful-26528 lineage + handoff integrity ==="
BRANCH="$(git branch --show-current)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch: $BRANCH"
git merge-base --is-ancestor "$SUCCESSFUL_26528_HEAD" HEAD || fail "handoff HEAD is not descended from successful 26528"
[[ "$(tr -d '\r\n' < "$BASE_FILE")" == "$SUCCESSFUL_26528_HEAD" ]] || fail "base-26528 file drift"
for f in "$APPLY" "$VALIDATE" "$SHADER_PREFLIGHT" "$AUDIT_REFERENCE" "$IRIS_TEMPLATE" \
         "$EXPECTED_PATCH" "$EXPECTED_PATCH_SHA" "$EXPECTED_ROLLBACK" "$EXPECTED_ROLLBACK_SHA" \
         "$HANDOFF" "$PREV_HANDOFF" "$PROVENANCE" "$PROJECT_RULES" "$INHERITED_SHADER_PREFLIGHT" "$NATIVE_PREFLIGHT" "$DNG_TEST" \
         "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do
  [[ -f "$f" ]] || fail "missing required file $(basename "$f")"
done
sha256sum -c "$HANDOFF"
sha256sum -c "$PREV_HANDOFF"
( cd "$ROOT" && sha256sum -c "$(basename "$EXPECTED_PATCH_SHA")" && sha256sum -c "$(basename "$EXPECTED_ROLLBACK_SHA")" )
[[ "$(sha "$IRIS_TEMPLATE")" == "$IRIS_TEMPLATE_SHA" ]] || fail "Iris Spatial-RGB rewrite template drift"
[[ "$(sha "$INHERITED_SHADER_PREFLIGHT")" == "$INHERITED_SHADER_PREFLIGHT_SHA" ]] || fail "inherited shader preflight drift"
python3 -m py_compile "$APPLY" "$VALIDATE" "$SHADER_PREFLIGHT" "$AUDIT_REFERENCE" \
    "$INHERITED_SHADER_PREFLIGHT" "$NATIVE_PREFLIGHT" "$DNG_TEST"
python3 "$APPLY" --self-test
bash -n "$0"
command -v glslangValidator >/dev/null || fail "glslangValidator unavailable"
glslangValidator --version | grep -F '16.5.0' >/dev/null || fail "wrong glslang version"
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_VENDOR_HEAD" ]] || fail "native vendor dependency commit drift"

git diff --name-only "$SUCCESSFUL_26528_HEAD"..HEAD -- app/src/main app/version.properties > "$OUT/26529_committed_runtime_drift_after_26528.txt"
[[ ! -s "$OUT/26529_committed_runtime_drift_after_26528.txt" ]] || fail "committed runtime drift after successful 26528"
git diff --name-only "$SUCCESSFUL_26528_HEAD"..HEAD -- gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties app/build.gradle app/proguard-rules.pro > "$OUT/26529_protected_build_infrastructure_drift.txt"
[[ ! -s "$OUT/26529_protected_build_infrastructure_drift.txt" ]] || fail "protected build infrastructure drift after successful 26528"
pass "26529 handoff-only lineage verified; no backup branch required"

echo "=== 26529 GATE 1: recover ACTUAL successful 26528 candidate-source artifact ==="
command -v gh >/dev/null || fail "GitHub CLI unavailable"
[[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing"
RUN_JSON="$WORK/26528_runs.json"
gh run list --repo "$REPO" --workflow "$BASE_WORKFLOW" --branch "$EXPECTED_BRANCH" --status success --limit 50 --json databaseId,headSha,conclusion,createdAt > "$RUN_JSON"
RUN_ID="$(python3 - "$RUN_JSON" "$SUCCESSFUL_26528_HEAD" <<'PY'
import json,sys
runs=json.load(open(sys.argv[1])); head=sys.argv[2]
exact=[r for r in runs if r.get('headSha')==head and r.get('conclusion')=='success']
if not exact: raise SystemExit('no successful 26528 workflow at exact HEAD '+head)
exact.sort(key=lambda r:r.get('createdAt',''), reverse=True)
print(exact[0]['databaseId'])
PY
)"
[[ "$RUN_ID" =~ ^[0-9]+$ ]] || fail "invalid successful-26528 run id"
gh run download "$RUN_ID" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$ART"
mapfile -t SOURCE_TARS < <(find "$ART" -type f -name "$BASE_SOURCE_TAR_NAME" -print)
mapfile -t SOURCE_MANIFESTS < <(find "$ART" -type f -name "$BASE_SOURCE_MANIFEST_NAME" -print)
[[ "${#SOURCE_TARS[@]}" -eq 1 && "${#SOURCE_MANIFESTS[@]}" -eq 1 ]] || fail "26528 source artifact cardinality mismatch"
SOURCE_TAR="${SOURCE_TARS[0]}"; SOURCE_MANIFEST="${SOURCE_MANIFESTS[0]}"
[[ "$(sha "$SOURCE_TAR")" == "$EXPECTED_BASE_TAR_SHA" ]] || fail "successful-26528 candidate tar SHA drift"
[[ "$(sha "$SOURCE_MANIFEST")" == "$EXPECTED_BASE_MANIFEST_SHA" ]] || fail "successful-26528 candidate manifest SHA drift"
[[ "$(wc -l < "$SOURCE_MANIFEST")" -eq "$EXPECTED_BASE_FILES" ]] || fail "successful-26528 source manifest file-count drift"
python3 - "$SOURCE_TAR" <<'PY'
import sys,tarfile
with tarfile.open(sys.argv[1],'r:gz') as t:
    names=[m.name.lstrip('./') for m in t.getmembers() if m.name not in ('.','./')]
for n in names:
    if not (n in {'app','app/','app/src','app/src/','app/src/main','app/src/main/','app/version.properties'} or n.startswith('app/src/main/')):
        raise SystemExit('unexpected path in 26528 candidate archive: '+n)
print('PASS: 26528 candidate archive contains runtime source + version only')
PY
tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26528_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "0.9726528" ]] || fail "26528 base version mismatch"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "26528" ]] || fail "26528 base build mismatch"
pass "manifest+SHA verified exact successful 26528 runtime recovered; repository app/src is not runtime authority"

echo "=== 26529 GATE 1A: audit pinned bjzhou c317 as REFERENCE ONLY ==="
rm -rf "$BJSP"; git init -q "$BJSP"
git -C "$BJSP" remote add origin https://github.com/bjzhou/PhotonCamera.git
git -C "$BJSP" fetch --depth=1 origin "$BJZHOU_SPATIAL_HEAD"
[[ "$(git -C "$BJSP" rev-parse FETCH_HEAD)" == "$BJZHOU_SPATIAL_HEAD" ]] || fail "bjzhou c317 checkout drift"
git -C "$BJSP" show "FETCH_HEAD:$BJZHOU_POST_REL" > "$VENDOR_POST"
[[ "$(git hash-object "$VENDOR_POST")" == "$BJZHOU_POST_BLOB" ]] || fail "bjzhou c317 postprocessor blob drift"
grep -F 'Post-fusion VGN chroma filtering for MGC Spatial RGB.' "$VENDOR_POST" >/dev/null || fail "c317 postprocessor semantic marker missing"
grep -F 'directionMomentAt(p)' "$VENDOR_POST" >/dev/null || fail "c317 direction-moment consumer missing"
grep -F 'uimage2D uInput' "$VENDOR_POST" >/dev/null || fail "c317 contiguous 2D postprocess contract missing"
python3 "$AUDIT_REFERENCE" --reference "$VENDOR_POST" --iris "$IRIS_TEMPLATE" \
  --json-out "$OUT/26529_bjzhou_reference_vs_iris_template.json" | tee "$OUT/26529_bjzhou_reference_vs_iris_template.txt"
pass "bjzhou c317 pinned and audited only as semantic reference; runtime source remains Iris-owned"

echo "=== 26529 GATE 1B: resolve transform + forward/rollback patches BEFORE candidate writes ==="
GEN_PATCH="$OUT/26529_RUNTIME_DELTA_FROM_SUCCESSFUL_26528.patch"
GEN_PATCH_SHA="$OUT/26529_RUNTIME_DELTA_FROM_SUCCESSFUL_26528.patch.sha256"
GEN_ROLLBACK="$OUT/26529_RUNTIME_ROLLBACK_TO_SUCCESSFUL_26528.patch"
GEN_ROLLBACK_SHA="$OUT/26529_RUNTIME_ROLLBACK_TO_SUCCESSFUL_26528.patch.sha256"
python3 "$APPLY" --root "$BASE" --iris-template "$IRIS_TEMPLATE" --check-only \
  --patch-out "$GEN_PATCH" --patch-sha-out "$GEN_PATCH_SHA" \
  --rollback-out "$GEN_ROLLBACK" --rollback-sha-out "$GEN_ROLLBACK_SHA" \
  | tee "$OUT/26529_in_memory_transform_proof.txt"
( cd "$OUT" && sha256sum -c "$(basename "$GEN_PATCH_SHA")" && sha256sum -c "$(basename "$GEN_ROLLBACK_SHA")" )
cmp -s "$GEN_PATCH" "$EXPECTED_PATCH" || fail "generated forward patch differs from certified 26529 V2 patch"
cmp -s "$GEN_ROLLBACK" "$EXPECTED_ROLLBACK" || fail "generated rollback patch differs from certified 26529 V2 rollback"
python3 - "$GEN_PATCH" "$GEN_ROLLBACK" <<'PY'
import re,sys
expected=sorted([
'app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/utils/DirectBufferPixelPacker.kt'])
for p in sys.argv[1:]:
 s=open(p).read(); names=set()
 for line in s.splitlines():
  if line.startswith(('--- ','+++ ')):
   x=line[4:].split('\t',1)[0]
   if x!='/dev/null': names.add(x[2:] if x[:2] in ('a/','b/') else x)
 if sorted(names)!=expected: raise SystemExit(f'patch scope mismatch {p}: {sorted(names)}')
print('PASS: forward+rollback patch scopes are exact five-file 26529 allowlist')
PY
pass "26529 V2 forward + rollback patches regenerated byte-identical to certified handoff patches before candidate writes"

echo "=== 26529 GATE 2: apply exact candidate + independent zoom/DNG/Spatial proof ==="
cp -a "$BASE/." "$AFTER/"
python3 "$APPLY" --root "$AFTER" --iris-template "$IRIS_TEMPLATE"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --patch "$GEN_PATCH" --rollback "$GEN_ROLLBACK" \
  --json-out "$OUT/26529_prebuild_validation.json" | tee "$OUT/26529_prebuild_validator.txt"
python3 "$AUDIT_REFERENCE" --reference "$VENDOR_POST" \
  --iris "$AFTER/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt" \
  --json-out "$OUT/26529_bjzhou_reference_vs_iris_candidate.json" | tee "$OUT/26529_bjzhou_reference_vs_iris_candidate.txt"
python3 "$SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26529_embedded_shader_preflight.txt"
python3 "$INHERITED_SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26529_inherited_shader_preflight.txt"
python3 "$NATIVE_PREFLIGHT" --root "$AFTER" | tee "$OUT/26529_native_syntax_preflight.txt"
python3 "$DNG_TEST" --root "$AFTER" | tee "$OUT/26529_dng_subifd_preflight.txt"
[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "0.9726528" ]] || fail "version changed before guarded build block"
[[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "26528" ]] || fail "build changed before guarded build block"
echo "ZOOM_PHYSICAL_SWITCHING=BUTTON_ONLY"
echo "ZOOM_LOCAL_RANGE=1X_TO_30X_PER_SELECTED_PHYSICAL_LENS"
echo "ZOOM_UI_COORDINATE=OPTICAL_ANCHOR_TIMES_LOCAL_ZOOM"
echo "ZOOM_HAL_POLICY=CLAMP_TO_ADVERTISED_CAPABILITY_PLUS_SAFE_IRIS_RESIDUAL"
echo "DNG_LOCAL_ZOOM_AUTHORITY=PRESERVED_1_TO_1_PARAMETERS_MOTIONV2OUTPUTZOOM"
echo "DNG_RUNTIME_CHANGED=false"
echo "TEMPORAL_REJECTION_ALIGNMENT_CORRECTION=INHERITED_26527_C317_FINAL_PARITY"
echo "SPATIAL_RGB_REFERENCE=BJZHOU_C317_SEMANTICS_ONLY"
echo "SPATIAL_RGB_RUNTIME_OWNER=IRIS_REWRITE"
echo "SPATIAL_RGB_CORRECTION=C317_GLOBAL_FRAME_WEIGHT_DIRECTION_MOMENT_FULL_FRAME_CHROMA"
echo "PRE-BUILD SAFETY PROOF PASSED"

echo "=== 26529 GATE 3: version $VERSION_NAME/$VERSION_BUILD + APK build in SAME guarded block ==="
python3 - "$AFTER/app/version.properties" "$VERSION_NAME" "$VERSION_BUILD" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); vn=sys.argv[2]; vb=sys.argv[3]; s=p.read_text()
assert s.count('VERSION_NAME=0.9726528')==1 and s.count('VERSION_BUILD=26528')==1
p.write_text(s.replace('VERSION_NAME=0.9726528','VERSION_NAME='+vn,1).replace('VERSION_BUILD=26528','VERSION_BUILD='+vb,1))
PY

# Same native dependency procedure as successful 26528.
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
( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26529_vendor_manifest_check_prebuild.txt"

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
audited_runtime_manifest > "$OUT/26529_pre_gradle_audited_runtime.sha256"
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace
assert_cpp_deps_exact post
audited_runtime_manifest > "$OUT/26529_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26529_pre_gradle_audited_runtime.sha256" "$OUT/26529_post_gradle_audited_runtime.sha256" || fail "Gradle mutated audited 26529 runtime source"
( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26529_vendor_manifest_check_postbuild.txt"

# Reconstruct the audited runtime after Gradle exactly as 26528 did: scrub injected native/vendor files.
rm -rf "$POSTCHECK"; mkdir -p "$POSTCHECK/app/src" "$POSTCHECK/app"
cp -a app/src/main "$POSTCHECK/app/src/main"
rm -rf "$POSTCHECK/app/src/main/cpp/third_party_26507"
find "$POSTCHECK/app/src/main/cpp/deps" -mindepth 1 -maxdepth 1 -type f ! -name '.gitignore' -delete
cp app/version.properties "$POSTCHECK/app/version.properties"

# Re-run all reproducible source/interface proofs after Gradle.
python3 "$VALIDATE" --base "$BASE" --candidate "$POSTCHECK" --patch "$GEN_PATCH" --rollback "$GEN_ROLLBACK" --postbuild \
  --json-out "$OUT/26529_postbuild_validation.json" | tee "$OUT/26529_postbuild_validator.txt"
python3 "$AUDIT_REFERENCE" --reference "$VENDOR_POST" \
  --iris "$POSTCHECK/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt" \
  --json-out "$OUT/26529_bjzhou_reference_vs_iris_postbuild.json" | tee "$OUT/26529_bjzhou_reference_vs_iris_postbuild.txt"
python3 "$SHADER_PREFLIGHT" --root "$POSTCHECK" --validator glslangValidator | tee "$OUT/26529_embedded_shader_postbuild.txt"
python3 "$INHERITED_SHADER_PREFLIGHT" --root "$POSTCHECK" --validator glslangValidator | tee "$OUT/26529_inherited_shader_postbuild.txt"
python3 "$NATIVE_PREFLIGHT" --root "$POSTCHECK" | tee "$OUT/26529_native_syntax_postbuild.txt"
python3 "$DNG_TEST" --root "$POSTCHECK" | tee "$OUT/26529_dng_subifd_postbuild.txt"

mapfile -t APKS < <(find app/build/outputs/apk/debug -type f -name '*.apk' -print)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK, found ${#APKS[@]}"
cp "${APKS[0]}" "$FINAL"
sha256sum "$FINAL" > "$OUT/26529_APK.sha256"

echo "=== 26529 GATE 4: deterministic next-candidate source checkpoint ==="
# Same successful-26528 rule: remove temporary native vendor tree before checkpointing runtime authority.
rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26529_candidate_source.sha256"
[[ "$(wc -l < "$OUT/26529_candidate_source.sha256")" -eq 950 ]] || fail "26529 candidate source expected 950 files"
tar --sort=name --mtime='UTC 2026-08-22 00:00:00' --owner=0 --group=0 --numeric-owner \
  -czf "$OUT/26529_candidate_app_source.tar.gz" -C "$AFTER" app/src/main app/version.properties
sha256sum "$OUT/26529_candidate_app_source.tar.gz" > "$OUT/26529_candidate_app_source.tar.gz.sha256"
rm -rf "$VERIFY_NEXT"; mkdir -p "$VERIFY_NEXT"
tar -xzf "$OUT/26529_candidate_app_source.tar.gz" -C "$VERIFY_NEXT"
( cd "$VERIFY_NEXT" && sha256sum -c "$OUT/26529_candidate_source.sha256" ) > "$OUT/26529_next_candidate_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$VERIFY_NEXT/app/version.properties" | cut -d= -f2)" == "$VERSION_NAME" ]] || fail "next candidate version drift"
[[ "$(grep '^VERSION_BUILD=' "$VERIFY_NEXT/app/version.properties" | cut -d= -f2)" == "$VERSION_BUILD" ]] || fail "next candidate build drift"
sha256sum "$GEN_PATCH" "$GEN_ROLLBACK" "$FINAL" "$OUT/26529_candidate_app_source.tar.gz" > "$OUT/26529_artifact_hashes.sha256"

cat > "$OUT/26529_provenance.txt" <<EOF
26529 V2 Manual Physical-Lens 30x + Iris-owned Spatial RGB c317-semantic rewrite
Branch: $BRANCH
Successful predecessor HEAD: $SUCCESSFUL_26528_HEAD
Recovered predecessor source tar SHA256: $EXPECTED_BASE_TAR_SHA
Recovered predecessor manifest SHA256: $EXPECTED_BASE_MANIFEST_SHA
bjzhou Spatial reference commit: $BJZHOU_SPATIAL_HEAD
bjzhou reference postprocessor Git blob: $BJZHOU_POST_BLOB
Iris runtime rewrite SHA256: $IRIS_TEMPLATE_SHA
Reference policy: semantic/mathematical reference only; no bjzhou runtime file is copied
Version/build: $VERSION_NAME / $VERSION_BUILD
Physical lens switching: explicit button only
Local zoom range: 1x..30x on selected physical lens
UI zoom: detected optical anchor * local zoom
HAL zoom: bounded by advertised CONTROL_ZOOM_RATIO/SCALER maximum; residual handled by Iris
DNG: existing local motionV2OutputZoom/DefaultCrop authority preserved byte-identically
Inherited 26527 rejection/alignment correction: protected
New Iris-owned c317-semantic RGB parity: globalFrameWeight + fused-green direction moment + contiguous full-frame VGN chroma
Runtime delta: exactly five files
Routine backup branch: not used by current project procedure
EOF

pass "26529 V2 exact successful-26528 artifact + certified patch-first safety proof"
pass "26529 guarded Gradle build + immutable audited runtime + exactly one APK"
pass "26529 V2 postbuild zoom/DNG/Iris-c317-semantic proof + deterministic next candidate source"
