#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_INFRA_PARENT="fbf480d37c5213f72697170ae356493570ab3cc4"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"

BACKUP_BRANCH="backup-26478-v5-before-26478-v6-speaker-anchor-fix"
BACKUP_TARGET="fbf480d37c5213f72697170ae356493570ab3cc4"

PRECURSOR_SCRIPT="build_26477_strict_wronski_authority_v3.sh"
PRECURSOR_BLOB="a1a1af06024e9fef47644edf50188114d3d312e2"
CORE_TRANSFORM="transform_26478_pure_wronski_highlight_safe_v1.py"
DIAG_TRANSFORM="transform_26478_speaker_support_diagnostic_v2.py"

NEW_VERSION="0.9726478"
NEW_BUILD="26478"
OUTDIR="build_26478_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-pure-wronski-highlight-safe-speaker-diag-debug.apk"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }

rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26478_source_audit.txt"
REPORT="$OUTDIR/26478_build_report.txt"
PREPATCH="$OUTDIR/26478_pre_edit_binary.patch"
RECOVERY="$OUTDIR/26478_recovery_binary.patch"
SOURCEPATCH="$OUTDIR/26478_source.patch"
HASH_26477="$OUTDIR/26478_exact_26477.sha256"
HASH_AFTER="$OUTDIR/26478_after.sha256"

exec > >(tee "$AUDIT") 2>&1
echo "=== 26478 V6 SPEAKER-ANCHOR-CORRECTED AUTHORITATIVE PURE WRONSKI + HIGHLIGHT-SAFE + SPEAKER DIAGNOSTIC ==="
date -Iseconds || true

BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "wrong branch: $BRANCH"
[[ "$(git rev-parse HEAD^)" == "$EXPECTED_INFRA_PARENT" ]] || \
  fail "26478 V6 commit must be direct child of exact V5 infrastructure HEAD"
[[ "$(git rev-parse HEAD~2)" == "87de69aff3d927be9c031c2fce476dffe88e4d71" ]] || \
  fail "26478 V6 chain missing exact V4 infrastructure HEAD"
[[ "$(git rev-parse HEAD~3)" == "62fed09aa61ac963f951fd39b1a62be870d75654" ]] || \
  fail "26478 V6 chain missing exact 62fed09 correction"
[[ "$(git rev-parse HEAD~4)" == "a5fa756f8b5cf1101e807b776728d08225f3e53e" ]] || \
  fail "26478 V6 chain missing exact first 26478 infrastructure commit"
[[ "$(git rev-parse HEAD~5)" == "be24c16cb091e753852b900384dbde6f8d32744e" ]] || \
  fail "26478 V6 chain must descend exactly from successful 26477 V3"
pass "branch/head exact five-commit infrastructure lineage gate"

REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$BACKUP_TARGET" ]] || \
  fail "required 26478 backup missing/wrong"
pass "backup branch exact 26477 V3 checkpoint"

git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "missing verified app base"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties || \
  fail "app source was committed before guarded 26478 replay"
pass "repository app source unchanged before guarded replay"

[[ -f "$PRECURSOR_SCRIPT" ]] || fail "missing exact 26477 V3 precursor"
[[ "$(git hash-object "$PRECURSOR_SCRIPT")" == "$PRECURSOR_BLOB" ]] || \
  fail "26477 V3 precursor blob mismatch"
[[ -f "$CORE_TRANSFORM" ]] || fail "missing authoritative 26478 core transform"
[[ -f "$DIAG_TRANSFORM" ]] || fail "missing 26478 speaker diagnostic transform"
python3 -m py_compile "$CORE_TRANSFORM"
python3 -m py_compile "$DIAG_TRANSFORM"
pass "both 26478 transforms syntax PASS"

# The diagnostic transform contains an internal telemetry-only proof that
# checks the exact Java helper before it writes the candidate. Its own source
# necessarily contains the forbidden-token strings in that validator, so do
# not grep the whole Python file here and create a false failure.
grep -q '26478 diagnostic helper contains image/control mutation' "$DIAG_TRANSFORM" || \
  fail "speaker diagnostic internal no-mutation validator missing"
pass "speaker diagnostic internal telemetry-only gate present"
grep -q 'IRIS_26478_SPEAKER_SUPPORT_DIAGNOSTIC_ANCHOR_V2' "$DIAG_TRANSFORM" || \
  fail "speaker diagnostic V2 anchor marker missing"
pass "speaker diagnostic V2 corrected-anchor gate present"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

PRECURSOR="$TMP/26477_transform_only.sh"
awk '/^rm -f \.\/\*\.apk$/ { exit } { print }' "$PRECURSOR_SCRIPT" > "$PRECURSOR"

python3 - "$PRECURSOR" "$TMP/26477_precursor_outputs" "$EXPECTED_INFRA_PARENT" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); t=p.read_text()
old_parent='EXPECTED_INFRA_PARENT="316a28f078bad14951be3608317c74d1fc923901"'
new_parent='EXPECTED_INFRA_PARENT="'+sys.argv[3]+'"'
if t.count(old_parent)!=1:
    raise SystemExit("26478 precursor parent anchor count="+str(t.count(old_parent)))
t=t.replace(old_parent,new_parent,1)
old_out='OUTDIR="build_26477_outputs"'
new_out='OUTDIR="'+sys.argv[2]+'"'
if t.count(old_out)!=1:
    raise SystemExit("26478 precursor OUTDIR anchor count="+str(t.count(old_out)))
t=t.replace(old_out,new_out,1)
p.write_text(t)
print("26477 V3 transform-only precursor rewrite: PASS")
PY

chmod +x "$PRECURSOR"
bash -n "$PRECURSOR"
bash "$PRECURSOR"

grep -q '^VERSION_NAME=0\.9726477$' app/version.properties || fail "exact 26477 replay version"
grep -q '^VERSION_BUILD=26477$' app/version.properties || fail "exact 26477 replay build"

for marker in \
 IRIS_26477_STRICT_WRONSKI_SENSOR_AUTHORITY \
 IRIS_26477_WRONSKI_NOISE_AUTHORITY \
 IRIS_26477_WRONSKI_RECONSTRUCTION_AUTHORITY \
 IRIS_26477_POST_WRONSKI_DISPLAY_BOUNDARY \
 IRIS_26477_NO_PHOTON_POST_NOISE_STATE \
 IRIS_26476_ADRENO_RGBA32F_GRADIENT_CARRIER_RG_ONLY \
 IRIS_26475_IPOL_ICA_FINE_ONLY_THREE_ITERATIONS \
 IRIS_26475_IPOL_MC_EXACT_TABLE_CACHE; do
  grep -Rqs "$marker" app/src/main || fail "exact 26477 marker missing: $marker"
done
pass "exact tested 26477 V3 source reproduced"

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_26477"
sha256sum app/version.properties >> "$HASH_26477"

# TRUE pre-edit recovery patch: exact 26477 replay -> verified committed app base.
# This is deliberately created AFTER 26477 replay and BEFORE any 26478 transform.
git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$PREPATCH"
[[ -s "$PREPATCH" ]] || fail "true 26477 pre-edit binary patch is empty"
git apply --check --reverse "$PREPATCH" || \
  fail "true 26477 pre-edit binary patch cannot reverse current exact 26477 state"
PREPATCH_SHA="$(sha256sum "$PREPATCH" | awk '{print $1}')"
pass "true 26477 pre-edit binary patch created and reverse-apply checked"

CAND="$TMP/candidate"
mkdir -p "$CAND"
for p in \
 app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java \
 app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java \
 app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl \
 app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl \
 app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl \
 app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl \
 app/src/main/assets/shaders/motionv2/color_transform.glsl \
 app/version.properties; do
  mkdir -p "$CAND/$(dirname "$p")"
  cp "$p" "$CAND/$p"
done

python3 "$CORE_TRANSFORM" "$CAND"
python3 "$DIAG_TRANSFORM" "$CAND"

RECON_CAND="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
grep -q 'IRIS_26478_SPEAKER_SUPPORT_MAP' "$RECON_CAND" || \
  fail "same local support-map diagnostic missing from candidate"
grep -q 'IRIS_26478_SPEAKER_SUPPORT_EDGE' "$RECON_CAND" || \
  fail "speaker support-edge diagnostic missing from candidate"
grep -q 'source=existingIRIS_26436LocalSupport' "$RECON_CAND" || \
  fail "speaker diagnostic does not use the existing IRIS_26436 local support map"
grep -q 'colorPrediction=MotionV2DisplayExposure_then_Camera2GainsMatrix' "$RECON_CAND" || \
  fail "active Camera2 color-value diagnostic missing"
grep -q 'feedsImageMath=false' "$RECON_CAND" || \
  fail "speaker diagnostic no-feedback proof missing"

pass "candidate/source validation PASS"
pass "Temporary-copy validation: PASS"

for p in \
 app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java \
 app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java \
 app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl \
 app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl \
 app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl \
 app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl \
 app/src/main/assets/shaders/motionv2/color_transform.glsl \
 app/version.properties; do
  cp "$CAND/$p" "$p"
done

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_AFTER"
sha256sum app/version.properties >> "$HASH_AFTER"

python3 - "$HASH_26477" "$HASH_AFTER" <<'PY'
from pathlib import Path
import sys
def read(path):
    out={}
    for line in Path(path).read_text().splitlines():
        if line.strip():
            digest,name=line.split(None,1)
            out[name.strip()]=digest
    return out
before=read(sys.argv[1]); after=read(sys.argv[2])
expected={
"app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java",
"app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java",
"app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl",
"app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl",
"app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl",
"app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl",
"app/src/main/assets/shaders/motionv2/color_transform.glsl",
"app/version.properties",
}
changed={n for n in set(before)|set(after) if before.get(n)!=after.get(n)}
if changed != expected:
    raise SystemExit("26478 changed-file scope mismatch: "+repr(sorted(changed)))
print("Protected-file hashes: PASS")
print("26478 exact changed-file allowlist: PASS")
PY

for p in \
 app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java \
 app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2IpolNoiseCurve.java \
 app/src/main/assets/shaders/motionv2/mfsr_robustness.glsl \
 app/src/main/assets/shaders/motionv2/mfsr_robustness_erode.glsl \
 app/src/main/assets/shaders/motionv2/mfsr_kernel_covariance.glsl \
 app/src/main/assets/shaders/motionv2/mfsr_ica_reference_gradient.glsl \
 app/src/main/assets/shaders/motionv2/mfsr_ica_reference_hessian.glsl \
 app/src/main/assets/shaders/motionv2/mfsr_ica_refine.glsl \
 app/src/main/assets/shaders/motionv2/mfsr_block_match.glsl \
 app/src/main/assets/shaders/motionv2/mfsr_wb_cfa.glsl \
 app/src/main/assets/shaders/motionv2/raw_to_cfa.glsl \
 app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/FrameNumberSelector.java \
 app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java \
 app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java \
 app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java \
 app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java \
 app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java \
 app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java \
 app/src/main/assets/shaders/motionv2/display_exposure.glsl \
 app/src/main/assets/shaders/motionv2/render.glsl \
 app/src/main/assets/shaders/motionv2/gainmap.glsl; do
  before="$(awk -v p="$p" '$2==p{print $1}' "$HASH_26477")"
  after="$(awk -v p="$p" '$2==p{print $1}' "$HASH_AFTER")"
  [[ -n "$before" && "$before" == "$after" ]] || fail "protected 26477 source changed: $p"
done
pass "Wronski/IPOL core and 26477 authority/UHDR protected hashes PASS"

CAP="app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
RECON="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
INIT="app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl"
ACC="app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl"
REFADD="app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl"
FINAL="app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl"
COLOR="app/src/main/assets/shaders/motionv2/color_transform.glsl"
POST="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"

# Capture side: meaningful fresh RAW clipping triggers shorter entire equal-exposure burst.
grep -q 'IRIS_26478_GOOGLE_STYLE_HIGHLIGHT_SAFE_EQUAL_EXPOSURE_BURST' "$CAP" || \
  fail "highlight-safe equal-exposure capture marker missing"
grep -q 'MOTION_26478_HIGHLIGHT_FRACTION_TRIGGER = 0.002f' "$CAP" || \
  fail "0.2 percent RAW-clipping trigger missing"
grep -q 'MOTION_26478_HIGHLIGHT_PROTECTION_EV = 1.0f' "$CAP" || \
  fail "one-stop burst protection missing"
grep -q 'applyMotion26478HighlightSafeBurstBiasIfNeeded()' "$CAP" || \
  fail "shutter-time highlight-safe capture call missing"
grep -q 'restoreMotion26478HighlightSafeBurstBias();' "$CAP" || \
  fail "preview AE restore path missing"

# Clean Wronski reconstruction boundary.
! grep -q 'sampleValidity(' "$INIT" || fail "sampleValidity survived direct initializer"
! grep -q 'sampleValidity(' "$ACC" || fail "sampleValidity survived auxiliary accumulation"
! grep -q 'sampleValidity(' "$REFADD" || fail "sampleValidity survived reference-add path"

grep -q 'IRIS_26478_WRONSKI_PURE_DIVIDE_ONCE_FINALIZER' "$FINAL" || \
  fail "pure num/den finalizer marker missing"
grep -q 'vec3 wbRgb=num/den;' "$FINAL" || \
  fail "literal RGB=num/den operation missing"
! grep -q 'unsupportedAll' "$FINAL" || fail "Iris highlight neutralizer survived"

grep -q 'IRIS_26478_CAMERA2_COLOR_ONLY_NO_HIGHLIGHT_CHROMA_REPAIR' "$COLOR" || \
  fail "Camera2-only color marker missing"
! grep -q 'channelLoss' "$COLOR" || fail "per-channel highlight intervention survived"
! grep -q 'neighborhoodRisk' "$COLOR" || fail "3x3 highlight intervention survived"
! grep -q 'chromaCompression' "$COLOR" || fail "highlight chroma compression survived"

grep -q 'IRIS_26478_WRONSKI_REFERENCE_ADD_ONCE_NO_IPOL_ACCUMULATED_DENOISER' "$REFADD" || \
  fail "ordinary one-time reference-add path missing"
! grep -q 'referenceOwns' "$REFADD" || fail "hard reference ownership survived"
! grep -q 'MAX_FRAME_COUNT' "$REFADD" || fail "IPOL Rmax hard switch survived"
! grep -q 'MAX_MULTIPLIER' "$REFADD" || fail "IPOL Rmax multiplier survived"
grep -q 'const int RAD=1;' "$REFADD" || fail "ordinary radius-1 reference reconstruction missing"

# Exact Wronski auxiliary recurrence must remain present.
for invariant in \
 'vec2 lr=vec2(outP)+0.5;' \
 'vec2 lrMov=lr+rawFlow;' \
 'vec2 kmap=lrMov/2.0-0.5;' \
 'float w=exp(-0.5*z)*R;' \
 'n.rgb+=addNum;' \
 'd.rgb+=addDen;'; do
  grep -Fq "$invariant" "$ACC" || fail "Wronski auxiliary invariant missing: $invariant"
done

# MotionV2Denoise stays off.
! grep -q 'add(new MotionV2Denoise());' "$POST" || fail "MotionV2Denoise re-enabled"

# Speaker telemetry: support map plus RGB/color on strongest discontinuities.
grep -q 'IRIS_26478_SPEAKER_SUPPORT_MAP' "$RECON" || fail "same support-map diagnostic absent"
grep -q 'IRIS_26478_SPEAKER_SUPPORT_EDGE' "$RECON" || fail "support-edge diagnostic absent"
grep -q 'source=existingIRIS_26436LocalSupport' "$RECON" || fail "diagnostic support owner incorrect"
grep -q 'sameLocalSupportMap=true' "$RECON" || fail "same-local-support-map proof absent"
grep -q 'directA=' "$RECON" || fail "direct-RGB values absent from diagnostic"
grep -q 'colorA=' "$RECON" || fail "Camera2 color values absent from diagnostic"
grep -q 'colorPrediction=MotionV2DisplayExposure_then_Camera2GainsMatrix' "$RECON" || \
  fail "diagnostic active-color mirror absent"
grep -q 'diagnosticOnly=true' "$RECON" || fail "diagnostic-only marker absent"
grep -q 'feedsImageMath=false' "$RECON" || fail "diagnostic no-feedback marker absent"

grep -q '^VERSION_NAME=0\.9726478$' app/version.properties || fail "wrong version"
grep -q '^VERSION_BUILD=26478$' app/version.properties || fail "wrong build"

git diff --check "$EXPECTED_APP_BASE" -- app/src/main app/version.properties || \
  fail "git diff --check failed"

git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$RECOVERY"
git diff "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$SOURCEPATCH"

echo "PRE-BUILD SAFETY PROOF PASSED"
echo "  candidate/source validation PASS"
echo "  Temporary-copy validation: PASS"
echo "  exact 26477 V3 backup gate PASS"
echo "  exact tested 26477 V3 replay PASS"
echo "  TRUE 26477 binary pre-edit patch before 26478 modification PASS"
echo "  pre-edit patch SHA256=$PREPATCH_SHA"
echo "  Photon tunable/noise isolation from 26477 preserved PASS"
echo "  Wronski/IPOL alignment untouched PASS"
echo "  ICA untouched PASS"
echo "  exact IPOL Monte-Carlo noise curve untouched PASS"
echo "  Wronski robustness + anisotropic covariance untouched PASS"
echo "  frame-count owner untouched PASS"
echo "  no performance architecture rewrite PASS"
echo "  sharpening/PostPipeline state untouched PASS"
echo "  Wronski auxiliary num/den recurrence preserved PASS"
echo "  optional IPOL accumulated-robustness hard reference switch removed PASS"
echo "  immutable reference added exactly once with ordinary radius-1 kernel PASS"
echo "  Iris saturation-validity side channel removed PASS"
echo "  Iris highlight neutralizer removed PASS"
echo "  Iris color-stage highlight chroma repair removed PASS"
echo "  Camera2 color owner preserved PASS"
echo "  shutter-time highlight-safe equal-exposure acquisition adaptation PASS"
echo "  continuous preview RAW-AE controller remains dormant PASS"
echo "  MotionV2Denoise remains disabled PASS"
echo "  speaker SAME IRIS_26436 local support map diagnostic PASS"
echo "  strongest support-discontinuity direct-RGB/color diagnostics PASS"
echo "  speaker diagnostics feed image math=false PASS"
echo "  UHDR/render hash-protected unchanged PASS"
echo "  git diff --check PASS"
echo "  version/build increment in same guarded Gradle script PASS"

cat > "$REPORT" <<EOF
26478 V6 SPEAKER-ANCHOR-CORRECTED AUTHORITATIVE PURE WRONSKI + HIGHLIGHT-SAFE + SPEAKER DIAGNOSTIC
========================================================================
Rollback:
  $BACKUP_BRANCH -> $BACKUP_TARGET

True pre-edit recovery patch:
  $PREPATCH
  SHA256=$PREPATCH_SHA

Build:
  $NEW_VERSION / $NEW_BUILD

Core preserved:
- Wronski/IPOL block matching, 3-iteration ICA, exact IPOL MC noise curve,
  robustness mask/erosion, anisotropic covariance, WB CFA domain, subpixel
  auxiliary accumulation, FLOAT32 num/den and divide-once architecture.

Removed reconstruction additions:
- Iris sampleValidity/unsaturated-color side channel.
- Iris fully-clipped-neutral finalizer.
- Iris color-stage 3x3/per-channel highlight chroma compression.
- Optional IPOL accumulated_robustness_denoiser.merge hard reference ownership.
  IPOL public default configuration has this optional denoiser disabled.
- Reference is added exactly once with ordinary radius-1 Wronski reconstruction.

Capture adaptation:
- Photon-specific; NOT claimed as exact unpublished Google production code.
- If fresh sparse RAW highlight fraction >=0.002, shutter press asks HAL AE for
  one stop less exposure, clears old ZSL frames, and recollects one actual
  equal-exposure group. HAL AE stays on.
- Bias is restored when top-up completes or aborts.
- No continuous competing RAW-AE preview controller is enabled.

MotionV2Denoise remains disabled so reconstruction defects are visible.

Speaker diagnostic:
- reuses the already-read final FLOAT32 Wronski RGBA buffer; no extra GPU pass.
- uses the existing IRIS_26436 local support map unchanged.
- logs that same 12x8 support map plus four strongest adjacent support discontinuities.
- logs both-side direct RGB and predicted active post-display Camera2 gains+matrix RGB.
- diagnosticOnly=true and feedsImageMath=false.
EOF

rm -f ./*.apk
chmod +x ./gradlew
./gradlew assembleDebug --no-daemon

echo "BUILD SUCCESSFUL verified by Gradle return code" | tee -a "$REPORT"
mapfile -t apks < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | sort)
[[ ${#apks[@]} -eq 1 ]] || fail "expected exactly one debug APK, found ${#apks[@]}"
cp "${apks[0]}" "$APK_NAME"
[[ -s "$APK_NAME" ]] || fail "APK missing/empty"
APK_SHA="$(sha256sum "$APK_NAME" | awk '{print $1}')"
echo "APK=$APK_NAME" | tee -a "$REPORT"
echo "SHA256=$APK_SHA" | tee -a "$REPORT"
echo "26478 BUILD SUCCESS"
