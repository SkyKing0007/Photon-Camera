#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_INFRA_PARENT="316a28f078bad14951be3608317c74d1fc923901"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BACKUP_BRANCH="backup-26476-v3-before-26477-strict-wronski-authority"
BACKUP_TARGET="e51a77a2c49282cd36e7a5503961b47c5fc60274"
PRECURSOR_SCRIPT="build_26476_wronski_runtime_shader_portability_v3.sh"
PRECURSOR_BLOB="68b14cd3184d173e6adaef2a548bb9be465f95a6"
TRANSFORM_SCRIPT="transform_26477_strict_wronski_authority_v3.py"

NEW_VERSION="0.9726477"
NEW_BUILD="26477"
OUTDIR="build_26477_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-strict-wronski-authority-debug.apk"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }

rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26477_strict_wronski_source_audit.txt"
REPORT="$OUTDIR/26477_strict_wronski_build_report.txt"
PREPATCH="$OUTDIR/26477_pre_edit_binary.patch"
RECOVERY="$OUTDIR/26477_recovery_binary.patch"
SOURCEPATCH="$OUTDIR/26477_source.patch"
HASH_26476="$OUTDIR/26477_exact_26476.sha256"
HASH_AFTER="$OUTDIR/26477_after.sha256"

exec > >(tee "$AUDIT") 2>&1
echo "=== 26477 V3 STRICT WRONSKI RECONSTRUCTION AUTHORITY ==="
date -Iseconds || true

BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "wrong branch: $BRANCH"
[[ "$(git rev-parse HEAD^)" == "$EXPECTED_INFRA_PARENT" ]] || fail "26477 V3 infrastructure parent is not exact 26477 V2 infrastructure commit"
pass "branch/head lineage gate"

REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$BACKUP_TARGET" ]] || fail "required backup branch missing/wrong"
pass "backup branch exact 26476 V3 checkpoint"

git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "missing app base"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties || fail "app source committed before guarded replay"
pass "repository app source unchanged before guarded replay"

[[ -f "$PRECURSOR_SCRIPT" ]] || fail "missing 26476 V3 precursor"
[[ "$(git hash-object "$PRECURSOR_SCRIPT")" == "$PRECURSOR_BLOB" ]] || fail "26476 V3 precursor blob mismatch"
[[ -f "$TRANSFORM_SCRIPT" ]] || fail "missing 26477 transform script"
python3 -m py_compile "$TRANSFORM_SCRIPT"
pass "transform syntax PASS"

# Backup already verified. Create pre-edit binary patch BEFORE ephemeral app change.
git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$PREPATCH"
pass "binary pre-edit patch created before source modification"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

PRECURSOR="$TMP/26476_transform_only.sh"
awk '/^rm -f \.\/\*\.apk$/ { exit } { print }' "$PRECURSOR_SCRIPT" > "$PRECURSOR"
python3 - "$PRECURSOR" "$TMP/26476_precursor_outputs" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); t=p.read_text()
old='OUTDIR="build_26476_outputs"'
new='OUTDIR="'+sys.argv[2]+'"'
assert t.count(old)==1
p.write_text(t.replace(old,new,1))
PY
chmod +x "$PRECURSOR"
bash -n "$PRECURSOR"
bash "$PRECURSOR"

grep -q '^VERSION_NAME=0\.9726476$' app/version.properties || fail "26476 version replay failed"
grep -q '^VERSION_BUILD=26476$' app/version.properties || fail "26476 build replay failed"

for marker in \
 IRIS_26475_WRONSKI_BAYER_QUAD_ALIGNMENT_GUIDE \
 IRIS_26475_IPOL_ICA_FINE_ONLY_THREE_ITERATIONS \
 IRIS_26475_IPOL_ICA_REFERENCE_GRADIENT_PREP_ONCE \
 IRIS_26475_IPOL_ICA_REFERENCE_HESSIAN_PREP_ONCE \
 IRIS_26475_IPOL_RMAX8_REFERENCE_OWNERSHIP \
 IRIS_26475_IPOL_MC_EXACT_TABLE_CACHE \
 IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE \
 IRIS_26472_WRONSKI_AUX_FIRST_ZERO_ACCUMULATOR \
 IRIS_26472_SDR_AUTHORITATIVE_UHDR_HEADROOM \
 IRIS_26470_UHDR_RENDER_GEOMETRY_AUTHORITY \
 IRIS_26476_ADRENO_RGBA32F_GRADIENT_CARRIER_RG_ONLY; do
  grep -Rqs "$marker" app/src/main || fail "26476 lineage missing $marker"
done
pass "exact 26476 V3 application lineage reproduced"

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_26476"
sha256sum app/version.properties >> "$HASH_26476"

# Build candidate in a full temporary copy of only files that may change.
CAND="$TMP/candidate"
mkdir -p "$CAND"
# IRIS_26477_V3_CANDIDATE_NEW_FILE_PARENT_GUARD
mkdir -p \
  "$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline" \
  "$CAND/app/src/main/assets/shaders/motionv2"
for p in \
 app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java \
 app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java \
 app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java \
 app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java \
 app/version.properties; do
  mkdir -p "$CAND/$(dirname "$p")"
  cp "$p" "$CAND/$p"
done

python3 "$TRANSFORM_SCRIPT" "$CAND"
pass "candidate/source validation PASS"
pass "Temporary-copy validation: PASS"

# Apply the exact validated candidate.
for p in \
 app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java \
 app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java \
 app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java \
 app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java \
 app/version.properties; do
  cp "$CAND/$p" "$p"
done
mkdir -p app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline
mkdir -p app/src/main/assets/shaders/motionv2
cp "$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java" \
   app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java
cp "$CAND/app/src/main/assets/shaders/motionv2/display_exposure.glsl" \
   app/src/main/assets/shaders/motionv2/display_exposure.glsl

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_AFTER"
sha256sum app/version.properties >> "$HASH_AFTER"

python3 - "$HASH_26476" "$HASH_AFTER" <<'PY'
from pathlib import Path
import sys
def read(path):
    d={}
    for line in Path(path).read_text().splitlines():
        if line.strip():
            h,n=line.split(None,1); d[n.strip()]=h
    return d
b=read(sys.argv[1]); a=read(sys.argv[2])
expected={
"app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java",
"app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java",
"app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java",
"app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java",
"app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java",
"app/src/main/assets/shaders/motionv2/display_exposure.glsl",
"app/version.properties",
}
changed={n for n in set(b)|set(a) if b.get(n)!=a.get(n)}
if changed != expected:
    raise SystemExit("changed-file scope mismatch: "+repr(sorted(changed)))
print("Protected-file hashes: PASS")
print("26477 exact changed-file allowlist: PASS")
PY

# Byte-protect Wronski/IPOL core math and current color/UHDR.
for p in \
 app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java \
 app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2IpolNoiseCurve.java \
 app/src/main/assets/shaders/motionv2/mfsr_robustness.glsl \
 app/src/main/assets/shaders/motionv2/mfsr_robustness_erode.glsl \
 app/src/main/assets/shaders/motionv2/mfsr_kernel_covariance.glsl \
 app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl \
 app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl \
 app/src/main/assets/shaders/motionv2/mfsr_ica_reference_gradient.glsl \
 app/src/main/assets/shaders/motionv2/mfsr_ica_reference_hessian.glsl \
 app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java \
 app/src/main/assets/shaders/motionv2/color_transform.glsl \
 app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java \
 app/src/main/assets/shaders/motionv2/render.glsl \
 app/src/main/assets/shaders/motionv2/gainmap.glsl; do
  before="$(awk -v p="$p" '$2==p{print $1}' "$HASH_26476")"
  after="$(awk -v p="$p" '$2==p{print $1}' "$HASH_AFTER")"
  [[ -n "$before" && "$before" == "$after" ]] || fail "protected source changed: $p"
done
pass "Wronski/IPOL/color/UHDR protected hashes PASS"

RECON="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
POST="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"

! grep -q 'NoiseModeler modeler = parameters.noiseModeler' "$RECON" || fail "Photon NoiseModeler still feeds Wronski"
grep -q 'final float canonicalGain = 1.0f;' "$RECON" || fail "Wronski gain is not sensor-domain 1"
grep -q 'CaptureResult.SENSOR_NOISE_PROFILE' "$HDRX" || fail "Camera2 noise profile authority missing"
grep -q 'add(new MotionV2DisplayExposure());' "$POST" || fail "post-Wronski display boundary missing"
! grep -q 'add(new MotionV2Denoise());' "$POST" || fail "residual Motion denoise still active"
grep -q '^VERSION_NAME=0\.9726477$' app/version.properties || fail "wrong version"
grep -q '^VERSION_BUILD=26477$' app/version.properties || fail "wrong build"

for marker in \
 IRIS_26477_STRICT_WRONSKI_SENSOR_AUTHORITY \
 IRIS_26477_WRONSKI_NOISE_AUTHORITY \
 IRIS_26477_WRONSKI_RECONSTRUCTION_AUTHORITY \
 IRIS_26477_POST_WRONSKI_DISPLAY_BOUNDARY \
 IRIS_26477_NO_PHOTON_POST_NOISE_STATE; do
  grep -Rqs "$marker" app/src/main || fail "missing 26477 marker $marker"
done

git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$RECOVERY"
git diff "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$SOURCEPATCH"

echo "PRE-BUILD SAFETY PROOF PASSED"
echo "  candidate/source validation PASS"
echo "  Temporary-copy validation: PASS"
echo "  exact 26476 backup gate PASS"
echo "  exact 26476 V3 replay PASS"
echo "  Photon adaptive-noise tunable cannot feed Wronski PASS"
echo "  Photon NoiseModeler/DynamicNoiseStore cannot feed Wronski PASS"
echo "  Motion black/white/CFA restored from Camera2 after tunable injection PASS"
echo "  26477 V3 candidate new-file parent-directory guard PASS"
echo "  exact 26476 IPOL noise-curve construction preserved PASS"
echo "  Wronski reconstruction sensor-domain gain=1 PASS"
echo "  display normalization moved after Wronski PASS"
echo "  generic Photon post noise state bypassed PASS"
echo "  Motion residual spatial denoise disabled PASS"
echo "  Wronski/IPOL/color/UHDR protected hashes PASS"
echo "  version/build increment in same guarded build PASS"

cat > "$REPORT" <<EOF
26477 STRICT WRONSKI RECONSTRUCTION AUTHORITY
=============================================
Rollback:
  $BACKUP_BRANCH -> $BACKUP_TARGET

Build:
  $NEW_VERSION / $NEW_BUILD

Motion reconstruction authority:
- black/white/CFA: timestamp-owned Camera2 metadata, after Photon tunables
- noise S/O: CaptureResult.SENSOR_NOISE_PROFILE directly
- Photon PyramidMerging adaptive noise: bypassed
- Photon NoiseModeler computeModel/adaptiveMpy: bypassed for Wronski
- DynamicNoiseStore: bypassed for Wronski
- generic noiseRstr: bypassed in Motion post graph
- Wronski reconstruction gain: 1.0 sensor domain
- display normalization: explicit downstream MotionV2DisplayExposure
- residual MotionV2 spatial denoise: disabled for this purity test
- exact 26476 Wronski alignment/ICA/robustness/direct RGB/finalizer: protected
- current Motion color transform and UHDR: protected

No performance optimization is included yet. This build establishes the clean
baseline first. Missing Camera2 SENSOR_NOISE_PROFILE is a hard failure; there is
no Photon noise fallback.
EOF

rm -f ./*.apk
chmod +x ./gradlew
./gradlew assembleDebug --no-daemon

echo "BUILD SUCCESSFUL verified by Gradle return code" | tee -a "$REPORT"
mapfile -t apks < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | sort)
[[ ${#apks[@]} -ge 1 ]] || fail "no debug APK found"
cp "${apks[0]}" "$APK_NAME"
[[ -s "$APK_NAME" ]] || fail "APK missing/empty"
APK_SHA="$(sha256sum "$APK_NAME" | awk '{print $1}')"
echo "APK=$APK_NAME" | tee -a "$REPORT"
echo "SHA256=$APK_SHA" | tee -a "$REPORT"
echo "26477 BUILD SUCCESS"
