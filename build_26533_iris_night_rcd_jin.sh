#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
manifest_all(){ local r="$1" o="$2"; (cd "$r" && find app/src/main app/version.properties app/build.gradle -type f -print0 | sort -z | xargs -0 sha256sum) > "$o"; }
manifest_runtime(){ local r="$1" o="$2"; (cd "$r" && find app/src/main app/version.properties -type f -print0 | sort -z | xargs -0 sha256sum) > "$o"; }
manifest_audited_live(){ local r="$1" o="$2"; (cd "$r" && find app/src/main app/version.properties app/build.gradle \
  \( -path 'app/src/main/cpp/libjpeg-turbo' -o -path 'app/src/main/cpp/libultrahdr' \) -prune -o -type f -print0 | sort -z | xargs -0 sha256sum) > "$o"; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
SUCCESSFUL_26532_HEAD="22222d162053fefade881a4c37dc388c6f68c581"
BASE_WORKFLOW="build-26532-iris-superres20-pink-foliage.yml"
BASE_ARTIFACT="photon-26532-iris-superres20-pink-foliage"
BASE_SOURCE_TAR_NAME="26532_candidate_app_source.tar.gz"
BASE_SOURCE_MANIFEST_NAME="26532_candidate_source.sha256"
EXPECTED_BASE_FILES=951
BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
JIN_UPSTREAM_HEAD="2a0681eae7c2bbc120a019d5bb71bcbd12291df7"
JIN_CHECKPOINT_URL="https://www.dropbox.com/s/0ykpsm1d48f74ao/LOL_params_0900000.pt?dl=1"
ORT_ANDROID_VERSION="1.29.0"
VERSION_NAME="0.9726533"; VERSION_BUILD="26533"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"

APPLY="$ROOT/apply_26533_iris_night_rcd_jin.py"
MODEL_PREP="$ROOT/prepare_26533_jin_model.py"
VALIDATE="$ROOT/validate_26533_iris_night_rcd_jin.py"
HANDOFF="$ROOT/26533_HANDOFF_HASHES.sha256"
OWNER_HASHES="$ROOT/26533_EXACT_26532_OWNER_HASHES.sha256"
HISTORICAL_REL="transform_26489_bjzhou_host_bayer_rcd_v2.py"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"

# Inherited successful-26532 preflights. These are source-controlled proof tools, not runtime owners.
SHADER_PREFLIGHT="$ROOT/preflight_26532_iris_shaders.py"
NATIVE_JPEG_PREFLIGHT="$ROOT/preflight_26532_native_jpeg_syntax.py"
JAVA_XML_PREFLIGHT="$ROOT/preflight_26532_java_xml_syntax.py"
EMBEDDED_PREFLIGHT="$ROOT/preflight_26529_iris_embedded_shaders_v3.py"
INHERITED_SHADER_PREFLIGHT="$ROOT/preflight_26526_inherited_shaders.py"
KOTLIN_API_PREFLIGHT="$ROOT/preflight_26531_iris_kotlin_api_contracts.py"
NATIVE_DNG_PREFLIGHT="$ROOT/preflight_26527_native_syntax.py"
DNG_TEST="$ROOT/test_26527_dng_subifd.py"

OUT="$ROOT/build_26533_iris_night_rcd_jin_outputs"
WORK="$ROOT/.build_26533_iris_night_rcd_jin_work"
ART="$WORK/26532_artifact"
BASE="$WORK/tested26532"
AFTER="$WORK/candidate26533"
PATCHREPO="$WORK/patchrepo"
FORWARDCHECK="$WORK/forwardcheck"
ROLLBACKCHECK="$WORK/rollbackcheck"
UPSTREAM="$WORK/night-enhancement"
MODEL_VENV="$WORK/modelvenv"
MODEL_CKPT="$WORK/LOL_params_0900000.pt"
MODEL_PROVENANCE="$OUT/26533_jin_model_provenance.json"
HISTORICAL_RCD="$WORK/$HISTORICAL_REL"
BJ="$WORK/bjzhou_vendor"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-iris-night-rcd-jin-debug.apk"
SOURCE_TAR_OUT="$OUT/26533_candidate_app_source.tar.gz"
SOURCE_MANIFEST_OUT="$OUT/26533_candidate_source.sha256"

rm -rf "$OUT" "$WORK" "$FINAL"
mkdir -p "$OUT" "$ART" "$BASE" "$AFTER"
find "$ROOT" -maxdepth 1 -type f -name 'IrisCamera-*-debug.apk' -delete
exec > >(tee "$OUT/26533_build.log") 2>&1

echo "=== 26533 GATE 0: exact 26532 lineage + handoff integrity ==="
BRANCH="$(git branch --show-current)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch: $BRANCH"
git merge-base --is-ancestor "$SUCCESSFUL_26532_HEAD" HEAD || fail "handoff HEAD is not descended from exact successful 26532 V1.4"
for f in "$APPLY" "$MODEL_PREP" "$VALIDATE" "$HANDOFF" "$OWNER_HASHES" "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE" \
         "$SHADER_PREFLIGHT" "$NATIVE_JPEG_PREFLIGHT" "$JAVA_XML_PREFLIGHT" "$EMBEDDED_PREFLIGHT" \
         "$INHERITED_SHADER_PREFLIGHT" "$KOTLIN_API_PREFLIGHT" "$NATIVE_DNG_PREFLIGHT" "$DNG_TEST"; do
  [[ -f "$f" ]] || fail "missing $(basename "$f")"
done
sha256sum -c "$HANDOFF"
python3 - "$OWNER_HASHES" <<'PYHASH'
import re,sys
rows=[]
for raw in open(sys.argv[1],encoding='utf-8'):
    line=raw.strip()
    if not line or line.startswith('#'): continue
    parts=line.split(None,1)
    if len(parts)!=2 or not re.fullmatch(r'[0-9a-f]{64}',parts[0]):
        raise SystemExit('invalid exact-26532 owner hash contract line: '+line)
    rows.append((parts[0],parts[1].strip()))
if len(rows)!=8 or len({p for _,p in rows})!=8:
    raise SystemExit('exact-26532 owner hash contract must contain exactly 8 unique entries')
print('PASS: exact-26532 owner hash contract syntax/cardinality')
PYHASH
python3 -m py_compile "$APPLY" "$MODEL_PREP" "$VALIDATE" "$SHADER_PREFLIGHT" "$NATIVE_JPEG_PREFLIGHT" \
  "$JAVA_XML_PREFLIGHT" "$EMBEDDED_PREFLIGHT" "$INHERITED_SHADER_PREFLIGHT" "$KOTLIN_API_PREFLIGHT" \
  "$NATIVE_DNG_PREFLIGHT" "$DNG_TEST"
bash -n "$0"
command -v gh >/dev/null || fail "GitHub CLI unavailable"
[[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing"
command -v glslangValidator >/dev/null || fail "glslangValidator unavailable"
glslangValidator --version | grep -F '16.5.0' >/dev/null || fail "wrong glslangValidator version"
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_VENDOR_HEAD" ]] || fail "native dependency commit drift"
# The handoff itself may not commit runtime/build-infrastructure changes. Those are produced only in the audited temp candidate.
git diff --name-only "$SUCCESSFUL_26532_HEAD"..HEAD -- app/src/main app/version.properties > "$OUT/26533_committed_runtime_drift_after_26532.txt"
[[ ! -s "$OUT/26533_committed_runtime_drift_after_26532.txt" ]] || fail "committed runtime drift after successful 26532"
git diff --name-only "$SUCCESSFUL_26532_HEAD"..HEAD -- gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties app/build.gradle app/proguard-rules.pro > "$OUT/26533_committed_build_infrastructure_drift.txt"
[[ ! -s "$OUT/26533_committed_build_infrastructure_drift.txt" ]] || fail "committed build infrastructure drift after successful 26532"
# Pin the historical RCD payload source to the exact 26532 lineage, not the handoff commit.
git show "$SUCCESSFUL_26532_HEAD:$HISTORICAL_REL" > "$HISTORICAL_RCD"
[[ -s "$HISTORICAL_RCD" ]] || fail "historical certified RCD transform unavailable at 26532 lineage"
pass "exact 26532 V1.4 lineage + handoff integrity verified"

echo "=== 26533 GATE 1: recover ACTUAL successful 26532 candidate-source artifact ==="
RUN_JSON="$WORK/26532_runs.json"
gh run list --repo "$REPO" --workflow "$BASE_WORKFLOW" --branch "$EXPECTED_BRANCH" --status success --limit 50 \
  --json databaseId,headSha,conclusion,createdAt > "$RUN_JSON"
RUN_ID="$(python3 - "$RUN_JSON" "$SUCCESSFUL_26532_HEAD" <<'PY'
import json,sys
runs=json.load(open(sys.argv[1])); head=sys.argv[2]
xs=[r for r in runs if r.get('headSha')==head and r.get('conclusion')=='success']
if not xs: raise SystemExit('no successful 26532 workflow at exact HEAD '+head)
xs.sort(key=lambda r:r.get('createdAt',''), reverse=True)
print(xs[0]['databaseId'])
PY
)"
[[ "$RUN_ID" =~ ^[0-9]+$ ]] || fail "invalid 26532 workflow run id"
echo "$RUN_ID" > "$OUT/26533_base_26532_successful_run_id.txt"
gh run download "$RUN_ID" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$ART"
mapfile -t SOURCE_TARS < <(find "$ART" -type f -name "$BASE_SOURCE_TAR_NAME" -print)
mapfile -t SOURCE_MANIFESTS < <(find "$ART" -type f -name "$BASE_SOURCE_MANIFEST_NAME" -print)
[[ "${#SOURCE_TARS[@]}" -eq 1 && "${#SOURCE_MANIFESTS[@]}" -eq 1 ]] || fail "26532 candidate-source artifact cardinality mismatch"
SOURCE_TAR="${SOURCE_TARS[0]}"; SOURCE_MANIFEST="${SOURCE_MANIFESTS[0]}"
sha256sum "$SOURCE_TAR" > "$OUT/26533_base_26532_source_tar.sha256"
sha256sum "$SOURCE_MANIFEST" > "$OUT/26533_base_26532_source_manifest_file.sha256"
[[ "$(wc -l < "$SOURCE_MANIFEST")" -eq "$EXPECTED_BASE_FILES" ]] || fail "26532 source manifest count drift"
python3 - "$SOURCE_TAR" <<'PY'
import sys,tarfile
with tarfile.open(sys.argv[1],'r:gz') as t:
    names=[m.name.lstrip('./') for m in t.getmembers() if m.name not in ('.','./')]
for n in names:
    if not (n in {'app','app/','app/src','app/src/','app/src/main','app/src/main/','app/version.properties'} or n.startswith('app/src/main/')):
        raise SystemExit('unexpected path in 26532 candidate archive: '+n)
print('PASS: 26532 archive contains runtime source + version only')
PY
tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26533_base_26532_manifest_check.txt"
# app/build.gradle was intentionally outside the 26532 candidate archive; recover it from the exact successful 26532 HEAD.
mkdir -p "$BASE/app"
git show "$SUCCESSFUL_26532_HEAD:app/build.gradle" > "$BASE/app/build.gradle"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "0.9726532" ]] || fail "base version name mismatch"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "26532" ]] || fail "base build mismatch"
# V1.1: verify the complete critical-owner contract recovered by the earlier exact-26532 source probe.
# This happens BEFORE model work and BEFORE the 26533 transformer can touch the isolated candidate.
( cd "$BASE" && sha256sum -c "$OWNER_HASHES" ) | tee "$OUT/26533_exact_26532_owner_contract_check.txt"
pass "exact 8-owner 26532 source-probe contract verified against recovered candidate"
cp -a "$BASE/." "$AFTER/"
pass "exact successful 26532 candidate recovered; repository app/src remains non-authoritative"

echo "=== 26533 GATE 1A: pin + convert Jin low-light generator ==="
git clone --filter=blob:none --no-checkout https://github.com/jinyeying/night-enhancement.git "$UPSTREAM"
git -C "$UPSTREAM" fetch --depth=1 origin "$JIN_UPSTREAM_HEAD"
git -C "$UPSTREAM" checkout --detach FETCH_HEAD
[[ "$(git -C "$UPSTREAM" rev-parse HEAD)" == "$JIN_UPSTREAM_HEAD" ]] || fail "Jin upstream commit mismatch"
curl --fail --location --silent --show-error --retry 5 "$JIN_CHECKPOINT_URL" -o "$MODEL_CKPT"
[[ "$(stat -c %s "$MODEL_CKPT")" -gt 1000000 ]] || fail "Jin checkpoint download suspiciously small"
sha256sum "$MODEL_CKPT" > "$OUT/26533_jin_downloaded_checkpoint.sha256"
python3 -m venv "$MODEL_VENV"
"$MODEL_VENV/bin/pip" install --disable-pip-version-check --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.7.1
"$MODEL_VENV/bin/pip" install --disable-pip-version-check --no-cache-dir numpy==2.2.6 onnx==1.18.0 onnxruntime==1.22.0
mkdir -p "$AFTER/app/src/main/assets/models"
"$MODEL_VENV/bin/python" "$MODEL_PREP" --upstream "$UPSTREAM" --checkpoint "$MODEL_CKPT" \
  --output "$AFTER/app/src/main/assets/models/iris_night_jin_lol_512.onnx" --provenance "$MODEL_PROVENANCE"
[[ -s "$MODEL_PROVENANCE" ]] || fail "Jin model provenance missing"
pass "pinned Jin checkpoint converted + PyTorch/ONNX equivalence verified"

echo "=== 26533 GATE 1B: complete transform in isolated candidate ==="
python3 "$APPLY" "$AFTER" --historical-rcd-transform "$HISTORICAL_RCD" --base-owner-hashes "$OWNER_HASHES"
python3 "$VALIDATE" "$AFTER" --model-provenance "$MODEL_PROVENANCE" --base-owner-hashes "$OWNER_HASHES" | tee "$OUT/26533_prebuild_anti_hybrid_validation.txt"
# Version must remain 26532 until every source/patch/preflight gate passes.
[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "0.9726532" ]] || fail "transform changed version too early"
[[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "26532" ]] || fail "transform changed build too early"
pass "complete 26533 transform resolved without touching live checkout"

echo "=== 26533 GATE 2: exact changed-file allowlist + forward/rollback proof ==="
EXPECTED_CHANGED="$OUT/26533_expected_changed_files.txt"
cat > "$EXPECTED_CHANGED" <<'EOF'
app/build.gradle
app/src/main/assets/models/iris_night_jin_lol_512.onnx
app/src/main/assets/shaders/motionv2/rcd26489_diag_direction.glsl
app/src/main/assets/shaders/motionv2/rcd26489_diag_residual.glsl
app/src/main/assets/shaders/motionv2/rcd26489_green.glsl
app/src/main/assets/shaders/motionv2/rcd26489_green_rb.glsl
app/src/main/assets/shaders/motionv2/rcd26489_lpf.glsl
app/src/main/assets/shaders/motionv2/rcd26489_opposite.glsl
app/src/main/assets/shaders/motionv2/rcd26489_populate.glsl
app/src/main/assets/shaders/motionv2/rcd26489_vh_direction.glsl
app/src/main/assets/shaders/irisnight/raw16_to_linear_bayer.glsl
app/src/main/assets/shaders/motionv2/rcd26489_write.glsl
app/src/main/cpp/motionv2_jpeg444_jni.cpp
app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisNightBayerInput.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java
app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/FrameNumberSelector.java
app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java
app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightMgc1271Bridge.kt
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java
app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java
EOF
sort -o "$EXPECTED_CHANGED" "$EXPECTED_CHANGED"
cp -a "$BASE/." "$PATCHREPO/"
(
  cd "$PATCHREPO"
  git init -q; git config user.email iris26533@example.invalid; git config user.name Iris26533
  git add -A; git commit -qm base
  rsync -a --delete --exclude=.git "$AFTER/" ./
  git add -A
  git diff --cached --name-only | sort > "$OUT/26533_actual_changed_files.txt"
  diff -u "$EXPECTED_CHANGED" "$OUT/26533_actual_changed_files.txt"
  git diff --cached --binary --full-index > "$OUT/26533_RUNTIME_DELTA_FROM_26532.patch"
  git diff --cached --binary --full-index -R > "$OUT/26533_RUNTIME_ROLLBACK_TO_26532.patch"
)
[[ -s "$OUT/26533_RUNTIME_DELTA_FROM_26532.patch" && -s "$OUT/26533_RUNTIME_ROLLBACK_TO_26532.patch" ]] || fail "forward/rollback patch generation failed"
sha256sum "$OUT/26533_RUNTIME_DELTA_FROM_26532.patch" > "$OUT/26533_RUNTIME_DELTA_FROM_26532.patch.sha256"
sha256sum "$OUT/26533_RUNTIME_ROLLBACK_TO_26532.patch" > "$OUT/26533_RUNTIME_ROLLBACK_TO_26532.patch.sha256"
# Prove forward patch reproduces the candidate byte-for-byte.
cp -a "$BASE/." "$FORWARDCHECK/"
(
  cd "$FORWARDCHECK"; git init -q; git config user.email check@example.invalid; git config user.name Check
  git add -A; git commit -qm base
  git apply --check "$OUT/26533_RUNTIME_DELTA_FROM_26532.patch"
  git apply --binary "$OUT/26533_RUNTIME_DELTA_FROM_26532.patch"
)
manifest_all "$AFTER" "$OUT/26533_candidate_manifest_preversion.sha256"
manifest_all "$FORWARDCHECK" "$OUT/26533_forwardcheck_manifest.sha256"
cmp -s "$OUT/26533_candidate_manifest_preversion.sha256" "$OUT/26533_forwardcheck_manifest.sha256" || fail "forward patch does not reproduce candidate byte-for-byte"
# Prove rollback removes all 26533 changes and returns exact 26532 + exact 26532 app/build.gradle.
cp -a "$AFTER/." "$ROLLBACKCHECK/"
(
  cd "$ROLLBACKCHECK"; git init -q; git config user.email check@example.invalid; git config user.name Check
  git add -A; git commit -qm after
  git apply --check "$OUT/26533_RUNTIME_ROLLBACK_TO_26532.patch"
  git apply --binary "$OUT/26533_RUNTIME_ROLLBACK_TO_26532.patch"
)
manifest_all "$BASE" "$OUT/26533_base_manifest_for_rollback.sha256"
manifest_all "$ROLLBACKCHECK" "$OUT/26533_rollback_manifest.sha256"
cmp -s "$OUT/26533_base_manifest_for_rollback.sha256" "$OUT/26533_rollback_manifest.sha256" || fail "rollback does not restore exact 26532 base"
pass "changed-file allowlist exact; forward and rollback patches independently proven"

echo "=== 26533 GATE 3: inherited 26532 + Night/RCD/model preflights ==="
python3 "$VALIDATE" "$AFTER" --model-provenance "$MODEL_PROVENANCE" --base-owner-hashes "$OWNER_HASHES" | tee "$OUT/26533_owner_preflight.txt"
python3 "$SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26533_inherited_26532_shader_preflight.txt"
python3 "$EMBEDDED_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26533_inherited_embedded_shader_preflight.txt"
python3 "$INHERITED_SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26533_inherited_shader_preflight.txt"
python3 "$KOTLIN_API_PREFLIGHT" --root "$AFTER" | tee "$OUT/26533_kotlin_api_preflight.txt"
python3 "$NATIVE_DNG_PREFLIGHT" --root "$AFTER" | tee "$OUT/26533_dng_native_preflight.txt"
python3 "$NATIVE_JPEG_PREFLIGHT" --root "$AFTER" | tee "$OUT/26533_native_jpeg_preflight.txt"
python3 "$JAVA_XML_PREFLIGHT" --root "$AFTER" | tee "$OUT/26533_java_xml_preflight.txt"
python3 "$DNG_TEST" --root "$AFTER" | tee "$OUT/26533_dng_subifd_preflight.txt"
# Verify no global hybrid rewrite exists in the generated candidate.
! grep -R --include='*.java' --include='*.kt' -F 'CameraMode.MOTION || CameraMode.NIGHT' "$AFTER/app/src/main" >/dev/null || fail "global Motion/Night hybrid gate detected"
! grep -R --include='*.java' --include='*.kt' -F 'CameraMode.NIGHT || CameraMode.MOTION' "$AFTER/app/src/main" >/dev/null || fail "global Night/Motion hybrid gate detected"
# Original Motion MGC owner and shared Spatial implementation must remain byte-exact 26532.
expected_owner_sha(){ awk -v p="$1" '$2==p {print $1}' "$OWNER_HASHES"; }
FUSION_REL="app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt"
BRIDGE_REL="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt"
[[ "$(sha "$AFTER/$FUSION_REL")" == "$(expected_owner_sha "$FUSION_REL")" ]] || fail "26532 MGC fusion owner changed"
[[ "$(sha "$AFTER/$BRIDGE_REL")" == "$(expected_owner_sha "$BRIDGE_REL")" ]] || fail "26532 Motion bridge changed"
# Model must be the exact file proven by provenance and the Android dependency must be pinned.
python3 - "$MODEL_PROVENANCE" "$AFTER/app/src/main/assets/models/iris_night_jin_lol_512.onnx" "$JIN_UPSTREAM_HEAD" <<'PY'
import hashlib,json,sys
p=json.load(open(sys.argv[1])); f=sys.argv[2]; pin=sys.argv[3]
a=hashlib.sha256(open(f,'rb').read()).hexdigest()
assert p['upstream_commit']==pin and p['onnx_sha256']==a and p['shape']==[1,3,512,512]
assert p['max_abs_pytorch_onnx'] <= 0.0025
print('PASS: 26533 neural provenance + numerical equivalence')
PY
grep -F "onnxruntime-android:$ORT_ANDROID_VERSION" "$AFTER/app/build.gradle" >/dev/null || fail "Android ONNX Runtime pin missing"

echo "PRE-BUILD SAFETY PROOF PASSED"
pass "26533 exact-base + anti-hybrid + RCD + neural + DNG/SR static proof"

echo "=== 26533 GATE 4: version increment + live copy + native restore + compile/build in one guarded block ==="
# The version increment and APK build intentionally live in the SAME guarded command block.
{
  sed -i "s/^VERSION_NAME=.*/VERSION_NAME=$VERSION_NAME/; s/^VERSION_BUILD=.*/VERSION_BUILD=$VERSION_BUILD/" "$AFTER/app/version.properties"
  [[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "$VERSION_NAME" ]] || fail "version name increment failed"
  [[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "$VERSION_BUILD" ]] || fail "build increment failed"
  python3 "$VALIDATE" "$AFTER" --model-provenance "$MODEL_PROVENANCE" --base-owner-hashes "$OWNER_HASHES" | tee "$OUT/26533_versioned_owner_validation.txt"
  manifest_audited_live "$AFTER" "$OUT/26533_pre_gradle_audited_runtime.sha256"

  rm -rf "$ROOT/app/src/main"
  cp -a "$AFTER/app/src/main" "$ROOT/app/src/"
  cp "$AFTER/app/version.properties" "$ROOT/app/version.properties"
  cp "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"

  # Restore the exact successful-26532 native dependency procedure inherited from V1.4.
  rm -rf "$BJ"
  git clone --filter=blob:none --no-checkout https://github.com/bjzhou/PhotonCamera.git "$BJ"
  git -C "$BJ" config core.sparseCheckout true
  mkdir -p "$BJ/.git/info"
  cat > "$BJ/.git/info/sparse-checkout" <<'EOF'
/app/src/main/cpp/libjpeg-turbo/
/app/src/main/cpp/libultrahdr/
EOF
  git -C "$BJ" fetch --depth=1 origin "$BJZHOU_VENDOR_HEAD"
  git -C "$BJ" checkout --detach FETCH_HEAD
  [[ "$(git -C "$BJ" rev-parse HEAD)" == "$BJZHOU_VENDOR_HEAD" ]] || fail "native vendor checkout head mismatch"
  [[ -f "$BJ/app/src/main/cpp/libjpeg-turbo/CMakeLists.txt" ]] || fail "libjpeg-turbo sentinel missing"
  [[ -f "$BJ/app/src/main/cpp/libultrahdr/ultrahdr_api.h" ]] || fail "libultrahdr API sentinel missing"
  [[ -f "$BJ/app/src/main/cpp/libultrahdr/lib/src/ultrahdr_api.cpp" ]] || fail "libultrahdr source sentinel missing"
  [[ ! -e "$BJ/app/src/main/cpp/libultrahdr/CMakeLists.txt" ]] || fail "unexpected obsolete libultrahdr CMakeLists sentinel returned"
  rm -rf "$ROOT/app/src/main/cpp/libjpeg-turbo" "$ROOT/app/src/main/cpp/libultrahdr"
  cp -a "$BJ/app/src/main/cpp/libjpeg-turbo" "$ROOT/app/src/main/cpp/"
  cp -a "$BJ/app/src/main/cpp/libultrahdr" "$ROOT/app/src/main/cpp/"
  (cd "$ROOT" && sha256sum -c "$BJZHOU_MANIFEST") | tee "$OUT/26533_native_dependency_manifest_check.txt"
  pass "exact successful-26532 native vendor checkout + full manifest verified before Gradle"

  chmod +x ./gradlew
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
  ./gradlew :app:assembleDebug --stacktrace
}

echo "=== 26533 GATE 5: post-build source integrity + owner revalidation ==="
manifest_audited_live "$ROOT" "$OUT/26533_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26533_pre_gradle_audited_runtime.sha256" "$OUT/26533_post_gradle_audited_runtime.sha256" || fail "Gradle/build mutated audited 26533 source"
python3 "$VALIDATE" "$ROOT" --model-provenance "$MODEL_PROVENANCE" --base-owner-hashes "$OWNER_HASHES" | tee "$OUT/26533_postbuild_owner_validation.txt"
python3 "$JAVA_XML_PREFLIGHT" --root "$ROOT" | tee "$OUT/26533_postbuild_java_xml_preflight.txt"
python3 "$NATIVE_JPEG_PREFLIGHT" --root "$ROOT" | tee "$OUT/26533_postbuild_native_jpeg_preflight.txt"
# Native vendor dependencies must also remain exact after Gradle.
(cd "$ROOT" && sha256sum -c "$BJZHOU_MANIFEST") | tee "$OUT/26533_postbuild_native_dependency_manifest_check.txt"
pass "compile/build completed and audited source remained byte-identical"

echo "=== 26533 GATE 6: exactly one APK + deterministic candidate artifact ==="
mapfile -t BUILT_APKS < <(find "$ROOT/app/build/outputs/apk" -type f -name '*.apk' -print 2>/dev/null)
[[ "${#BUILT_APKS[@]}" -eq 1 ]] || fail "expected exactly one Gradle APK, found ${#BUILT_APKS[@]}"
cp "${BUILT_APKS[0]}" "$FINAL"
find "$ROOT/app/build" -type f -name '*.apk' -delete
[[ -f "$FINAL" ]] || fail "final APK missing"
[[ "$(find "$ROOT" -maxdepth 1 -type f -name '*.apk' | wc -l)" -eq 1 ]] || fail "root APK count is not exactly one"
sha256sum "$FINAL" > "$OUT/26533_APK.sha256"
# Strip build-only vendor trees before exporting the authoritative next candidate source.
rm -rf "$AFTER/app/src/main/cpp/libjpeg-turbo" "$AFTER/app/src/main/cpp/libultrahdr"
manifest_all "$AFTER" "$SOURCE_MANIFEST_OUT"
EXPECTED_AFTER_FILES="$(python3 - "$BASE" "$EXPECTED_CHANGED" <<'PY'
from pathlib import Path
import sys
base=Path(sys.argv[1]); changed=[x.strip() for x in open(sys.argv[2]) if x.strip()]
base_count=sum(1 for p in list((base/'app/src/main').rglob('*')) if p.is_file())+2 # version + app/build.gradle
new=sum(1 for rel in changed if not (base/rel).exists())
print(base_count+new)
PY
)"
[[ "$(wc -l < "$SOURCE_MANIFEST_OUT")" -eq "$EXPECTED_AFTER_FILES" ]] || fail "26533 candidate file count mismatch"
(
  cd "$AFTER"
  tar --sort=name --mtime='UTC 2026-08-23 00:00:00' --owner=0 --group=0 --numeric-owner \
    -czf "$SOURCE_TAR_OUT" app/src/main app/version.properties app/build.gradle
)
sha256sum "$SOURCE_TAR_OUT" > "$OUT/26533_candidate_app_source.tar.gz.sha256"
sha256sum "$SOURCE_MANIFEST_OUT" > "$OUT/26533_candidate_source_manifest_file.sha256"
python3 - "$SOURCE_TAR_OUT" <<'PY'
import sys,tarfile
with tarfile.open(sys.argv[1],'r:gz') as t:
    names=[m.name.lstrip('./') for m in t.getmembers() if m.name not in ('.','./')]
for n in names:
    if not (n in {'app','app/','app/src','app/src/','app/src/main','app/src/main/','app/version.properties','app/build.gradle'} or n.startswith('app/src/main/')):
        raise SystemExit('unexpected path in 26533 candidate archive: '+n)
print('PASS: deterministic 26533 archive contains runtime + version + pinned app dependency only')
PY
cat > "$OUT/26533_SCOPE_PROVENANCE.txt" <<EOF
BASE_BRANCH=$EXPECTED_BRANCH
BASE_SUCCESSFUL_26532_HEAD=$SUCCESSFUL_26532_HEAD
BASE_SUCCESSFUL_26532_RUN_ID=$RUN_ID
BASE_ARTIFACT=$BASE_ARTIFACT
TARGET_VERSION=$VERSION_NAME
TARGET_BUILD=$VERSION_BUILD
JIN_UPSTREAM_HEAD=$JIN_UPSTREAM_HEAD
JIN_CHECKPOINT_SHA256=$(awk '{print $1}' "$OUT/26533_jin_downloaded_checkpoint.sha256")
JIN_ONNX_SHA256=$(python3 -c 'import json;print(json.load(open("'$MODEL_PROVENANCE'"))["onnx_sha256"])')
ORT_ANDROID_VERSION=$ORT_ANDROID_VERSION
NIGHT_CAPTURE_OWNER=IRIS
NIGHT_MERGE_OWNER=MGC_SPATIAL
NIGHT_NATIVE_OUTPUT=BAYER_TO_CERTIFIED_RCD
NIGHT_NEURAL=JIN_LOL_512_TO_32X32_GAIN_FIELD
NIGHT_FULL_RES_NEURAL=false
NIGHT_50MP_NEURAL=false
NIGHT_SUPERRES_OUTPUT=26532_STREAMED_2X
PHOTON_NIGHT_FALLBACK=false
MOTION_RUNTIME_BASE=26532_V1.4_PRESERVED
EOF
pass "single APK + deterministic 26533 next-candidate source exported"

echo "=== FINAL 26533 PASS SUMMARY ==="
pass "26533 exact successful-26532 V1.4 lineage + forward/rollback + anti-hybrid safety proof"
pass "26533 Kotlin/Java/native build + post-build source/dependency integrity proof"
pass "26533 single APK + 12MP/50MP Night/RCD/Jin architecture + deterministic next candidate proof"
