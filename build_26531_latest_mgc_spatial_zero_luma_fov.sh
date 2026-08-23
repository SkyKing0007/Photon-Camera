#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
SUCCESSFUL_26530_HEAD="8e847de9841b5ed3522970a1106f2b53cb3f7eb1"
BASE_WORKFLOW="build-26530-gcam-luma-motion-safe-superres.yml"
BASE_ARTIFACT="photon-26530-gcam-luma-motion-safe-superres-v1-2"
BASE_SOURCE_TAR_NAME="26530_candidate_app_source.tar.gz"
BASE_SOURCE_MANIFEST_NAME="26530_candidate_source.sha256"
EXPECTED_BASE_TAR_SHA="c29b5749351b757e35390b3c6fe451526be2be63a517f6e122833a5448d4b009"
EXPECTED_BASE_MANIFEST_SHA="753c6e2a086b67f1ac8ef7f0b462acc44dcb5da1b95252d420c3867695aa6f04"
EXPECTED_BASE_FILES=950
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"

VERSION_NAME="0.9726531"; VERSION_BUILD="26531"
APPLY="$ROOT/apply_26531_latest_mgc_spatial_zero_luma_fov.py"
VALIDATE="$ROOT/validate_26531_latest_mgc_spatial_zero_luma_fov.py"
NEW_SHADER_PREFLIGHT="$ROOT/preflight_26531_latest_mgc_spatial_shaders.py"
SR_SHADER_PREFLIGHT="$ROOT/preflight_26530_superres_shaders.py"
EMBEDDED_26529_PREFLIGHT="$ROOT/preflight_26529_iris_embedded_shaders_v3.py"
INHERITED_SHADER_PREFLIGHT="$ROOT/preflight_26526_inherited_shaders.py"
NATIVE_PREFLIGHT="$ROOT/preflight_26527_native_syntax.py"
DNG_TEST="$ROOT/test_26527_dng_subifd.py"
PREV_26529_HANDOFF="$ROOT/26529_V3_HANDOFF_HASHES.sha256"
PREV_26530_HANDOFF="$ROOT/26530_V1.2_HANDOFF_HASHES.sha256"
BASE_HEAD_FILE="$ROOT/26531_BASE_SUCCESSFUL_26530_V1.2_HEAD.txt"
HANDOFF="$ROOT/26531_HANDOFF_HASHES.sha256"
EXPECTED_PATCH="$ROOT/26531_RUNTIME_DELTA_FROM_SUCCESSFUL_26530_V1.2.patch"
EXPECTED_PATCH_SHA="$ROOT/26531_RUNTIME_DELTA_FROM_SUCCESSFUL_26530_V1.2.patch.sha256"
EXPECTED_ROLLBACK="$ROOT/26531_RUNTIME_ROLLBACK_TO_SUCCESSFUL_26530_V1.2.patch"
EXPECTED_ROLLBACK_SHA="$ROOT/26531_RUNTIME_ROLLBACK_TO_SUCCESSFUL_26530_V1.2.patch.sha256"

EMBEDDED_26529_PREFLIGHT_SHA="07f2aa8214cecf75ad8d946b72974b884559e22cbbb75efaa34704b35336fba8"
INHERITED_SHADER_PREFLIGHT_SHA="638376dd1b6d770cd8d91d3e35ff3d61e6847ab3277b64b446976a88e43b9e2b"
SR_SHADER_PREFLIGHT_SHA="1ac665a22a3a1e09062760e16d8655deba30066d5d080eb986b00bf271bb8531"

BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"

OUT="$ROOT/build_26531_latest_mgc_spatial_zero_luma_fov_outputs"
WORK="$ROOT/.build_26531_latest_mgc_spatial_zero_luma_fov_work"
ART="$WORK/26530_v12_artifact"
BASE="$WORK/tested26530v12"
AFTER="$WORK/candidate26531"
POSTCHECK="$WORK/postbuild26531"
VERIFY_NEXT="$WORK/verify_next_candidate"
BJ="$WORK/bjzhou_vendor"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-latest-mgc-spatial-zero-luma-fov-debug.apk"

rm -rf "$OUT" "$WORK" "$FINAL"
mkdir -p "$OUT" "$ART" "$BASE" "$AFTER"
exec > >(tee "$OUT/26531_build.log") 2>&1

echo "=== 26531 GATE 0: exact successful-26530 V1.2 lineage + handoff ==="
BRANCH="$(git branch --show-current)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch: $BRANCH"
git merge-base --is-ancestor "$SUCCESSFUL_26530_HEAD" HEAD || fail "handoff HEAD is not descended from successful 26530 V1.2"
[[ "$(tr -d '\r\n' < "$BASE_HEAD_FILE")" == "$SUCCESSFUL_26530_HEAD" ]] || fail "base 26530 V1.2 HEAD file drift"
for f in "$APPLY" "$VALIDATE" "$NEW_SHADER_PREFLIGHT" "$SR_SHADER_PREFLIGHT" \
         "$EMBEDDED_26529_PREFLIGHT" "$INHERITED_SHADER_PREFLIGHT" "$NATIVE_PREFLIGHT" "$DNG_TEST" \
         "$PREV_26529_HANDOFF" "$PREV_26530_HANDOFF" "$HANDOFF" "$BASE_HEAD_FILE" \
         "$EXPECTED_PATCH" "$EXPECTED_PATCH_SHA" "$EXPECTED_ROLLBACK" "$EXPECTED_ROLLBACK_SHA" \
         "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do
  [[ -f "$f" ]] || fail "missing required file $(basename "$f")"
done
sha256sum -c "$HANDOFF"
# V1.2 manifest was renamed in this handoff. Validate its recorded files from repository root.
sed 's#  #  #' "$PREV_26530_HANDOFF" | sha256sum -c -
sha256sum -c "$PREV_26529_HANDOFF"
( cd "$ROOT" && sha256sum -c "$(basename "$EXPECTED_PATCH_SHA")" && sha256sum -c "$(basename "$EXPECTED_ROLLBACK_SHA")" )
[[ "$(sha "$SR_SHADER_PREFLIGHT")" == "$SR_SHADER_PREFLIGHT_SHA" ]] || fail "26530 SR shader preflight drift"
[[ "$(sha "$EMBEDDED_26529_PREFLIGHT")" == "$EMBEDDED_26529_PREFLIGHT_SHA" ]] || fail "26529 embedded shader preflight drift"
[[ "$(sha "$INHERITED_SHADER_PREFLIGHT")" == "$INHERITED_SHADER_PREFLIGHT_SHA" ]] || fail "inherited shader preflight drift"
python3 -m py_compile "$APPLY" "$VALIDATE" "$NEW_SHADER_PREFLIGHT" "$SR_SHADER_PREFLIGHT" \
    "$EMBEDDED_26529_PREFLIGHT" "$INHERITED_SHADER_PREFLIGHT" "$NATIVE_PREFLIGHT" "$DNG_TEST"
python3 "$APPLY" --self-test
bash -n "$0"
command -v gh >/dev/null || fail "GitHub CLI unavailable"
[[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing"
command -v glslangValidator >/dev/null || fail "glslangValidator unavailable"
glslangValidator --version | grep -F '16.5.0' >/dev/null || fail "wrong glslang version"
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_VENDOR_HEAD" ]] || fail "native vendor dependency commit drift"

git diff --name-only "$SUCCESSFUL_26530_HEAD"..HEAD -- app/src/main app/version.properties > "$OUT/26531_committed_runtime_drift_after_26530_v12.txt"
[[ ! -s "$OUT/26531_committed_runtime_drift_after_26530_v12.txt" ]] || fail "committed runtime drift after successful 26530 V1.2"
git diff --name-only "$SUCCESSFUL_26530_HEAD"..HEAD -- gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties app/build.gradle app/proguard-rules.pro > "$OUT/26531_protected_build_infrastructure_drift.txt"
[[ ! -s "$OUT/26531_protected_build_infrastructure_drift.txt" ]] || fail "protected build infrastructure drift after successful 26530 V1.2"

pass "exact successful 26530 V1.2 lineage + handoff verified; no backup branch required"

echo "=== 26531 GATE 1: recover ACTUAL successful 26530 V1.2 candidate-source artifact ==="
RUN_JSON="$WORK/26530_v12_runs.json"
gh run list --repo "$REPO" --workflow "$BASE_WORKFLOW" --branch "$EXPECTED_BRANCH" --status success --limit 50 \
  --json databaseId,headSha,conclusion,createdAt > "$RUN_JSON"
RUN_ID="$(python3 - "$RUN_JSON" "$SUCCESSFUL_26530_HEAD" <<'PY'
import json,sys
runs=json.load(open(sys.argv[1])); head=sys.argv[2]
exact=[r for r in runs if r.get('headSha')==head and r.get('conclusion')=='success']
if not exact: raise SystemExit('no successful 26530 V1.2 workflow at exact HEAD '+head)
exact.sort(key=lambda r:r.get('createdAt',''), reverse=True)
print(exact[0]['databaseId'])
PY
)"
[[ "$RUN_ID" =~ ^[0-9]+$ ]] || fail "invalid successful-26530 V1.2 run id"
gh run download "$RUN_ID" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$ART"
mapfile -t SOURCE_TARS < <(find "$ART" -type f -name "$BASE_SOURCE_TAR_NAME" -print)
mapfile -t SOURCE_MANIFESTS < <(find "$ART" -type f -name "$BASE_SOURCE_MANIFEST_NAME" -print)
[[ "${#SOURCE_TARS[@]}" -eq 1 && "${#SOURCE_MANIFESTS[@]}" -eq 1 ]] || fail "26530 V1.2 source artifact cardinality mismatch"
SOURCE_TAR="${SOURCE_TARS[0]}"; SOURCE_MANIFEST="${SOURCE_MANIFESTS[0]}"
[[ "$(sha "$SOURCE_TAR")" == "$EXPECTED_BASE_TAR_SHA" ]] || fail "successful-26530 V1.2 candidate tar SHA drift"
[[ "$(sha "$SOURCE_MANIFEST")" == "$EXPECTED_BASE_MANIFEST_SHA" ]] || fail "successful-26530 V1.2 candidate manifest SHA drift"
[[ "$(wc -l < "$SOURCE_MANIFEST")" -eq "$EXPECTED_BASE_FILES" ]] || fail "successful-26530 V1.2 manifest file-count drift"
python3 - "$SOURCE_TAR" <<'PY'
import sys,tarfile
with tarfile.open(sys.argv[1],'r:gz') as t:
    names=[m.name.lstrip('./') for m in t.getmembers() if m.name not in ('.','./')]
for n in names:
    if not (n in {'app','app/','app/src','app/src/','app/src/main','app/src/main/','app/version.properties'} or n.startswith('app/src/main/')):
        raise SystemExit('unexpected path in 26530 V1.2 candidate archive: '+n)
print('PASS: successful 26530 V1.2 archive contains runtime source + version only')
PY
tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26530_v12_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "0.9726530" ]] || fail "26530 V1.2 base version mismatch"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "26530" ]] || fail "26530 V1.2 base build mismatch"
pass "manifest+SHA+exact-HEAD verified successful 26530 V1.2 runtime recovered; repository app/src is not runtime authority"

echo "=== 26531 GATE 1B: resolve forward/rollback patches BEFORE candidate writes ==="
GEN_PATCH="$OUT/26531_RUNTIME_DELTA_FROM_SUCCESSFUL_26530_V1.2.patch"
GEN_PATCH_SHA="$OUT/26531_RUNTIME_DELTA_FROM_SUCCESSFUL_26530_V1.2.patch.sha256"
GEN_ROLLBACK="$OUT/26531_RUNTIME_ROLLBACK_TO_SUCCESSFUL_26530_V1.2.patch"
GEN_ROLLBACK_SHA="$OUT/26531_RUNTIME_ROLLBACK_TO_SUCCESSFUL_26530_V1.2.patch.sha256"
python3 "$APPLY" "$BASE" --check-only --patch-out "$GEN_PATCH" --patch-sha-out "$GEN_PATCH_SHA" \
  --rollback-out "$GEN_ROLLBACK" --rollback-sha-out "$GEN_ROLLBACK_SHA" | tee "$OUT/26531_in_memory_transform_proof.txt"
( cd "$OUT" && sha256sum -c "$(basename "$GEN_PATCH_SHA")" && sha256sum -c "$(basename "$GEN_ROLLBACK_SHA")" )
cmp -s "$GEN_PATCH" "$EXPECTED_PATCH" || fail "generated forward patch differs from certified 26531 runtime patch"
cmp -s "$GEN_ROLLBACK" "$EXPECTED_ROLLBACK" || fail "generated rollback differs from certified 26531 rollback"
python3 - "$GEN_PATCH" "$GEN_ROLLBACK" <<'PY'
import sys
expected=sorted([
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/MgcAlignmentInputScale.kt',
'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialMergeTuning.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'])
for p in sys.argv[1:]:
    names=set()
    for line in open(p,encoding='utf-8'):
        if line.startswith(('--- ','+++ ')):
            x=line[4:].split('\t',1)[0].strip()
            if x!='/dev/null': names.add(x[2:] if x[:2] in ('a/','b/') else x)
    if sorted(names)!=expected: raise SystemExit(f'patch scope mismatch {p}: {sorted(names)}')
print('PASS: forward+rollback scopes are exact seven-file Spatial/Iris allowlist; no Sabre owner')
PY
pass "forward + rollback patches regenerated byte-identical before candidate writes"

echo "=== 26531 GATE 2: apply exact candidate + ALL inherited/new preflight proofs ==="
cp -a "$BASE/." "$AFTER/"
python3 "$APPLY" "$AFTER"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --patch "$GEN_PATCH" --rollback "$GEN_ROLLBACK" \
  --json-out "$OUT/26531_prebuild_validation.json" | tee "$OUT/26531_prebuild_validator.txt"

python3 "$NEW_SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26531_latest_mgc_spatial_shader_preflight.txt"
python3 "$SR_SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26531_superres_shader_preflight.txt"
python3 "$EMBEDDED_26529_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26531_26529_embedded_shader_preflight.txt"
python3 "$INHERITED_SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26531_inherited_shader_preflight.txt"
python3 "$NATIVE_PREFLIGHT" --root "$AFTER" | tee "$OUT/26531_native_syntax_preflight.txt"
python3 "$DNG_TEST" --root "$AFTER" | tee "$OUT/26531_dng_subifd_preflight.txt"

PATCHCHECK="$WORK/patchcheck"; ROLLCHECK="$WORK/rollbackcheck"
cp -a "$BASE" "$PATCHCHECK"
patch -d "$PATCHCHECK" -p1 --batch --forward --fuzz=0 --no-backup-if-mismatch < "$GEN_PATCH" >/dev/null
[[ -z "$(find "$PATCHCHECK" -type f \( -name '*.orig' -o -name '*.rej' \) -print -quit)" ]] || fail "forward patch emitted backup/reject artifact"
diff -qr "$PATCHCHECK/app/src/main" "$AFTER/app/src/main" > "$OUT/26531_forward_patch_compare.txt" || fail "forward patch did not reproduce candidate"
cp -a "$AFTER" "$ROLLCHECK"
patch -d "$ROLLCHECK" -p1 --batch --forward --fuzz=0 --no-backup-if-mismatch < "$GEN_ROLLBACK" >/dev/null
[[ -z "$(find "$ROLLCHECK" -type f \( -name '*.orig' -o -name '*.rej' \) -print -quit)" ]] || fail "rollback patch emitted backup/reject artifact"
diff -qr "$ROLLCHECK/app/src/main" "$BASE/app/src/main" > "$OUT/26531_rollback_compare.txt" || fail "rollback did not reproduce exact successful 26530 V1.2"
[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "0.9726530" ]] || fail "version changed before guarded build block"
[[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "26530" ]] || fail "build changed before guarded build block"

echo "TEMPORAL_IMAGE_MATH_CHANGED=true"
echo "LATEST_MGC_SPATIAL_PARITY=FINAL_BAYER_ALIGNMENT_EXPECTED_MERGE_WEIGHT_PROPAGATED_OUTPUT_SNR_RGB_DIRECTION"
echo "ALIGNMENT_SCALE=FRAME_GAIN_X_16384_OVER_SENSOR_WHITE_PLUS_1"
echo "MGC_LUMA_DENOISE=0"
echo "MGC_CHROMA_DENOISE=USER_SETTING"
echo "SUPERRES=RAW_DOMAIN_SHARED_GREEN_GEOMETRY_CAP_2X"
echo "FOV_AUTHORITY=FULL_MOTIONV2_OUTPUT_ZOOM"
echo "SABRE=SOURCE_ALLOWED_RUNTIME_DORMANT"
echo "DNG_ZOOM_CONTRACT=UNCHANGED"
echo "PRE-BUILD SAFETY PROOF PASSED"

echo "=== 26531 GATE 3: increment to $VERSION_NAME/$VERSION_BUILD + APK build in SAME guarded block ==="
python3 - "$AFTER/app/version.properties" "$VERSION_NAME" "$VERSION_BUILD" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); vn=sys.argv[2]; vb=sys.argv[3]; s=p.read_text()
assert s.count('VERSION_NAME=0.9726530')==1 and s.count('VERSION_BUILD=26530')==1
p.write_text(s.replace('VERSION_NAME=0.9726530','VERSION_NAME='+vn,1).replace('VERSION_BUILD=26530','VERSION_BUILD='+vb,1))
PY

# Exact native dependency procedure inherited from successful 26530 V1.2/26529.
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
( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26531_vendor_manifest_check_prebuild.txt"

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
audited_runtime_manifest > "$OUT/26531_pre_gradle_audited_runtime.sha256"
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace
assert_cpp_deps_exact post
audited_runtime_manifest > "$OUT/26531_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26531_pre_gradle_audited_runtime.sha256" "$OUT/26531_post_gradle_audited_runtime.sha256" || fail "Gradle mutated audited 26531 runtime source/version"
( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26531_vendor_manifest_check_postbuild.txt"

rm -rf "$POSTCHECK"; mkdir -p "$POSTCHECK/app/src" "$POSTCHECK/app"
cp -a app/src/main "$POSTCHECK/app/src/main"
rm -rf "$POSTCHECK/app/src/main/cpp/third_party_26507"
find "$POSTCHECK/app/src/main/cpp/deps" -mindepth 1 -maxdepth 1 -type f ! -name '.gitignore' -delete
cp app/version.properties "$POSTCHECK/app/version.properties"
python3 "$VALIDATE" --base "$BASE" --candidate "$POSTCHECK" --patch "$GEN_PATCH" --rollback "$GEN_ROLLBACK" --postbuild \
  --json-out "$OUT/26531_postbuild_validation.json" | tee "$OUT/26531_postbuild_validator.txt"
python3 "$NEW_SHADER_PREFLIGHT" --root "$POSTCHECK" --validator glslangValidator | tee "$OUT/26531_latest_mgc_spatial_shader_postbuild.txt"
python3 "$SR_SHADER_PREFLIGHT" --root "$POSTCHECK" --validator glslangValidator | tee "$OUT/26531_superres_shader_postbuild.txt"
python3 "$EMBEDDED_26529_PREFLIGHT" --root "$POSTCHECK" --validator glslangValidator | tee "$OUT/26531_26529_embedded_shader_postbuild.txt"
python3 "$INHERITED_SHADER_PREFLIGHT" --root "$POSTCHECK" --validator glslangValidator | tee "$OUT/26531_inherited_shader_postbuild.txt"
python3 "$NATIVE_PREFLIGHT" --root "$POSTCHECK" | tee "$OUT/26531_native_syntax_postbuild.txt"
python3 "$DNG_TEST" --root "$POSTCHECK" | tee "$OUT/26531_dng_subifd_postbuild.txt"

mapfile -t APKS < <(find app/build/outputs/apk/debug -type f -name '*.apk' -print)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK, found ${#APKS[@]}"
cp "${APKS[0]}" "$FINAL"
sha256sum "$FINAL" > "$OUT/26531_APK.sha256"

echo "=== 26531 GATE 4: deterministic next-candidate source checkpoint ==="
rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26531_candidate_source.sha256"
[[ "$(wc -l < "$OUT/26531_candidate_source.sha256")" -eq 950 ]] || fail "26531 candidate source expected 950 files"
tar --sort=name --mtime='UTC 2026-08-23 00:00:00' --owner=0 --group=0 --numeric-owner \
  -czf "$OUT/26531_candidate_app_source.tar.gz" -C "$AFTER" app/src/main app/version.properties
sha256sum "$OUT/26531_candidate_app_source.tar.gz" > "$OUT/26531_candidate_app_source.tar.gz.sha256"
rm -rf "$VERIFY_NEXT"; mkdir -p "$VERIFY_NEXT"
tar -xzf "$OUT/26531_candidate_app_source.tar.gz" -C "$VERIFY_NEXT"
( cd "$VERIFY_NEXT" && sha256sum -c "$OUT/26531_candidate_source.sha256" ) > "$OUT/26531_next_candidate_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$VERIFY_NEXT/app/version.properties" | cut -d= -f2)" == "$VERSION_NAME" ]] || fail "next candidate version drift"
[[ "$(grep '^VERSION_BUILD=' "$VERIFY_NEXT/app/version.properties" | cut -d= -f2)" == "$VERSION_BUILD" ]] || fail "next candidate build drift"
sha256sum "$GEN_PATCH" "$GEN_ROLLBACK" "$FINAL" "$OUT/26531_candidate_app_source.tar.gz" > "$OUT/26531_artifact_hashes.sha256"

cat > "$OUT/26531_provenance.txt" <<PROV
26531 latest-MGC Spatial semantics + zero MGC luma + corrected SR/FOV authority
Branch: $BRANCH
Successful predecessor HEAD: $SUCCESSFUL_26530_HEAD
Backup branch policy: none; certified forward/rollback patches are recovery authority
Recovered predecessor source tar SHA256: $EXPECTED_BASE_TAR_SHA
Recovered predecessor manifest SHA256: $EXPECTED_BASE_MANIFEST_SHA
Version/build: $VERSION_NAME / $VERSION_BUILD
Runtime patch SHA256: $(sha "$EXPECTED_PATCH")
MGC reference commits audited after c317bf9: 335840b5, e55e0fa1, b147342c, 4cb75786, 963c9261
Integrated Spatial semantics: final Bayer alignment; sensor-white S16 alignment scale; shot+read expected merge weight; propagated output NoiseModel SNR; RGB-gradient postfusion direction; rejected multiplier identity
AOT policy: recovered MGC V25 AOT is semantic ground truth only; active owner remains Iris Spatial RGB to preserve Motion/SR extensions
Sabre policy: source may exist; active Motion selector is SPATIAL_RGB, denoise pass SPATIAL_DEFAULT, protected Sabre owners byte-identical
MGC luma: forced 0.0 for this test; requested luma logged; chroma remains irisSettings.chromaDenoise
SR: existing 26530 RAW-domain shared-green geometry preserved, cap 2x
FOV: final JPEG/UHDR renderer uses full motionV2OutputZoom; SR scale no longer divides final crop authority
DNG: ImageSaver/render shader contracts protected; DefaultCrop motionV2OutputZoom unchanged
PROV

pass "26531 exact successful-26530 V1.2 artifact + certified patch-first safety proof"
pass "26531 Sabre-dormant semantic gates + latest-MGC Spatial/Iris proofs"
pass "26531 guarded version increment/Gradle build + postbuild proofs + deterministic next candidate"
