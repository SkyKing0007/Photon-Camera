#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_APP_BASE="8c4ed0ec731e212f54fb83224d17cc2e734c2476"
BACKUP_BRANCH="backup-26467-before-26468-correctness-seam"
BASE_26467_SCRIPT="build_26467_exact_wronski_performance.sh"
BASE_26467_SCRIPT_BLOB="2740f202c9a9c299198f5b702e94c3252d44409f"

OLD_VERSION="0.9726467"
OLD_BUILD="26467"
NEW_VERSION="0.9726468"
NEW_BUILD="26468"

OUTDIR="build_26468_outputs"
mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26468_source_audit.txt"
BUILDLOG="$OUTDIR/26468_build_report.txt"
REPORT="$OUTDIR/26468_correctness_diagnostics.txt"
PATCH="$OUTDIR/26468_pre_edit_binary.patch"
HASH_BEFORE="$OUTDIR/26468_protected_before.sha256"
HASH_AFTER="$OUTDIR/26468_protected_after.sha256"

exec > >(tee "$AUDIT") 2>&1

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }

echo "=== 26468 GUARDED CORRECTNESS / SINGLE-FRAME / SEAM DIAGNOSTIC BUILD ==="
date -Iseconds || true

BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "branch=$BRANCH expected=$EXPECTED_BRANCH"
pass "branch gate"

git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "missing expected app checkpoint"
REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$EXPECTED_APP_BASE" ]] || fail "backup branch mismatch: $REMOTE_BACKUP"
pass "backup branch exact current checkpoint"

git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties \
  || fail "application source differs from verified checkpoint before edit"
pass "application source unchanged from verified checkpoint"

[[ -f "$BASE_26467_SCRIPT" ]] || fail "missing $BASE_26467_SCRIPT"
[[ "$(git hash-object "$BASE_26467_SCRIPT")" == "$BASE_26467_SCRIPT_BLOB" ]] \
  || fail "26467 precursor script blob mismatch"
pass "26467 precursor script exact"

git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$PATCH"
cp "$PATCH" "$OUTDIR/26468_pre_edit_binary_recovery.patch"
find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_BEFORE"
pass "binary pre-edit patch created"
pass "protected-file hashes captured"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Reproduce tested 26467 app lineage without running its Gradle build.
PRECURSOR="$TMP/26467_transform_only.sh"
awk '
  /^chmod \+x \.\/gradlew$/ { exit }
  { print }
' "$BASE_26467_SCRIPT" > "$PRECURSOR"

python3 - "$PRECURSOR" "$TMP/26467_precursor_outputs" <<'PY_PRECURSOR_OUTDIR'
from pathlib import Path
import sys

path = Path(sys.argv[1])
replacement = 'OUTDIR="' + sys.argv[2] + '"'
text = path.read_text()
anchor = 'OUTDIR="build_26467_outputs"'
count = text.count(anchor)
if count != 1:
    raise SystemExit(
        f"26467 precursor OUTDIR anchor expected exactly 1, found {count}")
path.write_text(text.replace(anchor, replacement, 1))
print("26467 precursor OUTDIR rewrite: PASS")
PY_PRECURSOR_OUTDIR

chmod +x "$PRECURSOR"

bash -n "$PRECURSOR" || fail "26467 transform-only precursor syntax"
bash "$PRECURSOR"

grep -q '^VERSION_NAME=0\.9726467$' app/version.properties || fail "26467 precursor VERSION_NAME"
grep -q '^VERSION_BUILD=26467$' app/version.properties || fail "26467 precursor VERSION_BUILD"
grep -q 'IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java \
  || fail "26467 reference-prep lineage missing"
grep -q 'IRIS_26467_MOTION_OUTPUT_MODE_AUTHORITY' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java \
  || fail "26467 output-routing lineage missing"
pass "26467 tested application lineage reproduced"

RECON="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
ALIGN="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java"
INIT="app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl"
ACCUM="app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl"
FINALIZE="app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl"
PREF="app/src/main/res/xml/preferences.xml"
VERSION="app/version.properties"

for f in "$RECON" "$INIT" "$ACCUM" "$FINALIZE" "$PREF" "$VERSION"; do
  mkdir -p "$TMP/candidate/$(dirname "$f")"
  cp "$f" "$TMP/candidate/$f"
done

python3 - "$TMP/candidate" <<'PY'
from pathlib import Path
import sys, xml.etree.ElementTree as ET

root = Path(sys.argv[1])
recon = root / "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
init = root / "app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl"
accum = root / "app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl"
finalize = root / "app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl"
pref = root / "app/src/main/res/xml/preferences.xml"
version = root / "app/version.properties"

def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {n}")
    return text.replace(old, new, 1)

t = recon.read_text()

t = replace_once(
    t,
    '''        if (inputImages.size() == 1) {
            return MotionV2Merger.referenceFoundation(inputImages, referenceTimestamp);
        }

''',
    '',
    "single-frame early return")

t = replace_once(
    t,
    '''        final int frameCount = images.size();
        final int tile = 8;
''',
    '''        final int frameCount = images.size();
        final int tile = 8;

        if (frameCount == 1) {
            Log.d(TAG, "IRIS_26468_SINGLE_FRAME_FULL_MOTION_PIPELINE"
                    + " retainedFrames=1"
                    + " auxiliaryAlignment=false"
                    + " directRgbReconstruction=true"
                    + " downstreamMotionPostPipeline=true"
                    + " diagnosticControl=true");
            try {
                com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                        "IRIS_26468_SINGLE_FRAME_FULL_MOTION_PIPELINE",
                        "retainedFrames=1 auxiliaryAlignment=false"
                                + " directRgbReconstruction=true"
                                + " downstreamMotionPostPipeline=true");
            } catch (Throwable ignored) {}
        }
''',
    "single-frame trace marker")

t = replace_once(
    t,
    '''            output.order(ByteOrder.nativeOrder());
            output.position(0);

            Log.d(TAG, "IRIS_26416_V2_PROVEN_FLOAT32_BRIDGE"
''',
    '''            output.order(ByteOrder.nativeOrder());
            output.position(0);

            Log.d(TAG, "IRIS_26468_PRE_DENOISE_DIRECT_RGB_HANDOFF"
                    + " carrier=rgba32f"
                    + " fullResolution=" + directBayer
                    + " frameCount=" + frameCount
                    + " beforeMotionV2ColorTransform=true"
                    + " beforeMotionV2Denoise=true"
                    + " imageMathUnchanged=true");
            try {
                com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                        "IRIS_26468_PRE_DENOISE_DIRECT_RGB_HANDOFF",
                        "carrier=rgba32f frameCount=" + frameCount
                                + " beforeColorTransform=true"
                                + " beforeDenoise=true");
            } catch (Throwable ignored) {}

            Log.d(TAG, "IRIS_26416_V2_PROVEN_FLOAT32_BRIDGE"
''',
    "pre-denoise handoff marker")

t = replace_once(
    t,
    '''            float supportRoughness = 0.0f;
            int supportRoughCount = 0;
            for (int y = 0; y < summary.gridHeight; y++) {
''',
    '''            float supportRoughness = 0.0f;
            int supportRoughCount = 0;
            float iris26468StrongestSeamDelta = 0.0f;
            int iris26468SeamX = -1;
            int iris26468SeamY = -1;
            String iris26468SeamOrientation = "none";
            for (int y = 0; y < summary.gridHeight; y++) {
''',
    "seam variables")

t = replace_once(
    t,
    '''                    if (x + 1 < summary.gridWidth) {
                        supportRoughness += Math.abs(
                                c - summary.coarseGrid[idx + 1]);
                        supportRoughCount++;
                    }
                    if (y + 1 < summary.gridHeight) {
                        supportRoughness += Math.abs(
                                c - summary.coarseGrid[
                                        idx + summary.gridWidth]);
                        supportRoughCount++;
                    }
''',
    '''                    if (x + 1 < summary.gridWidth) {
                        float d = Math.abs(c - summary.coarseGrid[idx + 1]);
                        supportRoughness += d;
                        supportRoughCount++;
                        if (d > iris26468StrongestSeamDelta) {
                            iris26468StrongestSeamDelta = d;
                            iris26468SeamX = x;
                            iris26468SeamY = y;
                            iris26468SeamOrientation = "verticalBoundary";
                        }
                    }
                    if (y + 1 < summary.gridHeight) {
                        float d = Math.abs(
                                c - summary.coarseGrid[idx + summary.gridWidth]);
                        supportRoughness += d;
                        supportRoughCount++;
                        if (d > iris26468StrongestSeamDelta) {
                            iris26468StrongestSeamDelta = d;
                            iris26468SeamX = x;
                            iris26468SeamY = y;
                            iris26468SeamOrientation = "horizontalBoundary";
                        }
                    }
''',
    "seam measurement")

t = replace_once(
    t,
    '''            Log.d(TAG, "IRIS_26436_V2_SPATIAL_SUPPORT"
                    + " grid12x8=" + supportGrid12x8
                    + " meanNeighborDelta=" + supportRoughness
                    + " retainedFrames=" + frameCount
                    + " loggingOnly=true");
''',
    '''            Log.d(TAG, "IRIS_26436_V2_SPATIAL_SUPPORT"
                    + " grid12x8=" + supportGrid12x8
                    + " meanNeighborDelta=" + supportRoughness
                    + " retainedFrames=" + frameCount
                    + " loggingOnly=true");
            Log.d(TAG, "IRIS_26468_PROCESSING_SEAM_DIAGNOSTIC"
                    + " strongestSupportDelta=" + iris26468StrongestSeamDelta
                    + " gridX=" + iris26468SeamX
                    + " gridY=" + iris26468SeamY
                    + " orientation=" + iris26468SeamOrientation
                    + " grid=" + summary.gridWidth + "x" + summary.gridHeight
                    + " geometryUnchanged=true");
            try {
                com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                        "IRIS_26468_PROCESSING_SEAM_DIAGNOSTIC",
                        "strongestSupportDelta=" + iris26468StrongestSeamDelta
                                + " gridX=" + iris26468SeamX
                                + " gridY=" + iris26468SeamY
                                + " orientation=" + iris26468SeamOrientation
                                + " geometryUnchanged=true");
            } catch (Throwable ignored) {}
''',
    "seam trace")

# Aux-stage timing anchors.
t = replace_once(
    t,
    '''                    glProg.setLayout(tile, tile, 1);
                    glProg.useAssetProgram("motionv2/raw_to_cfa", true);
''',
    '''                    long iris26468RawToCfaStart = System.currentTimeMillis();
                    glProg.setLayout(tile, tile, 1);
                    glProg.useAssetProgram("motionv2/raw_to_cfa", true);
''',
    "RAW-to-CFA timer start")

t = replace_once(
    t,
    '''                    glProg.computeAuto(rawHalf, 1);

                    if (directBayer) {
                        final float wronskiWbR = directSensorGains[0]
''',
    '''                    glProg.computeAuto(rawHalf, 1);
                    long iris26468RawToCfaMs =
                            System.currentTimeMillis() - iris26468RawToCfaStart;

                    if (directBayer) {
                        long iris26468WbStart = System.currentTimeMillis();
                        final float wronskiWbR = directSensorGains[0]
''',
    "RAW-to-CFA timer end/WB start")

t = replace_once(
    t,
    '''                        glProg.computeAuto(rawHalf, 1);

                        wronskiAlterCov = new GLTexture(
''',
    '''                        glProg.computeAuto(rawHalf, 1);
                        long iris26468WbMs =
                                System.currentTimeMillis() - iris26468WbStart;

                        long iris26468CovStart = System.currentTimeMillis();
                        wronskiAlterCov = new GLTexture(
''',
    "WB timer end/cov start")

t = replace_once(
    t,
    '''                        glProg.computeAuto(rawHalf, 1);
                    }

                    MotionV2Alignment.Result ownedAlignment = null;
''',
    '''                        glProg.computeAuto(rawHalf, 1);
                        long iris26468CovMs =
                                System.currentTimeMillis() - iris26468CovStart;
                        Log.d(TAG, "IRIS_26468_STAGE_TIMING"
                                + " frame=" + i
                                + " rawToCfaMs=" + iris26468RawToCfaMs
                                + " wbCfaMs=" + iris26468WbMs
                                + " covarianceMs=" + iris26468CovMs);
                    }

                    MotionV2Alignment.Result ownedAlignment = null;
''',
    "cov timer end")

t = replace_once(
    t,
    '''                            GLTexture mfsrRobustRaw = new GLTexture(
''',
    '''                            long iris26468RobustStart = System.currentTimeMillis();
                            GLTexture mfsrRobustRaw = new GLTexture(
''',
    "robust timer start")

t = replace_once(
    t,
    '''                                glProg.computeAuto(raw, 1);

                                glProg.setLayout(tile, tile, 1);
                                glProg.useAssetProgram(
                                        "motionv2/mfsr_robustness_erode", true);
''',
    '''                                glProg.computeAuto(raw, 1);
                                long iris26468RobustMs =
                                        System.currentTimeMillis() - iris26468RobustStart;

                                long iris26468ErodeStart = System.currentTimeMillis();
                                glProg.setLayout(tile, tile, 1);
                                glProg.useAssetProgram(
                                        "motionv2/mfsr_robustness_erode", true);
''',
    "robust timer end/erode start")

t = replace_once(
    t,
    '''                                glProg.computeAuto(raw, 1);

                                glProg.setLayout(tile, tile, 1);
                                glProg.useAssetProgram(
                                        "motionv2/direct_rgb_accumulate", true);
''',
    '''                                glProg.computeAuto(raw, 1);
                                long iris26468ErodeMs =
                                        System.currentTimeMillis() - iris26468ErodeStart;

                                long iris26468AccumulateStart = System.currentTimeMillis();
                                glProg.setLayout(tile, tile, 1);
                                glProg.useAssetProgram(
                                        "motionv2/direct_rgb_accumulate", true);
''',
    "erode timer end/accum start")

t = replace_once(
    t,
    '''                                glProg.computeAuto(raw, 1);
                            } finally {
''',
    '''                                glProg.computeAuto(raw, 1);
                                long iris26468AccumulateMs =
                                        System.currentTimeMillis()
                                                - iris26468AccumulateStart;
                                Log.d(TAG, "IRIS_26468_STAGE_TIMING"
                                        + " frame=" + i
                                        + " robustnessMs=" + iris26468RobustMs
                                        + " erosion5x5Ms=" + iris26468ErodeMs
                                        + " directRgbAccumulateMs="
                                        + iris26468AccumulateMs);
                            } finally {
''',
    "accum timer end")

recon.write_text(t)

# Saturation-valid reference accumulation.
t = init.read_text()
t = replace_once(
    t,
    '''        float cfaSample=cfaAt(p);
        num[c]+=cfaSample*w;
        den[c]+=w;
        validDen[c]+=w*sampleValidity(cfaSample,c);
''',
    '''        float cfaSample=cfaAt(p);
        float validity=sampleValidity(cfaSample,c);
        float validW=w*validity;
        num[c]+=cfaSample*validW;
        den[c]+=validW;
        validDen[c]+=w;
''',
    "reference saturation-valid accumulation")
t = t.replace("IRIS_26465_CFA_UNSATURATED_SUPPORT_CARRIER",
              "IRIS_26468_CFA_VALID_NUMERATOR_TOTAL_SUPPORT_CARRIER")
t = t.replace("independent unsaturated Wronski denominator for R/G/B.",
              "total Wronski kernel denominator for R/G/B; currentDenominator carries valid support.")
init.write_text(t)

# Saturation-valid auxiliary accumulation.
t = accum.read_text()
t = replace_once(
    t,
    '''        float cfaSample=cfaAt(p);
        addNum[c]+=w*cfaSample;
        addDen[c]+=w;
        addValidDen[c]+=w*sampleValidity(cfaSample,c);
''',
    '''        float cfaSample=cfaAt(p);
        float validity=sampleValidity(cfaSample,c);
        float validW=w*validity;
        addNum[c]+=validW*cfaSample;
        addDen[c]+=validW;
        addValidDen[c]+=w;
''',
    "aux saturation-valid accumulation")
t = t.replace("IRIS_26465_WRONSKI_CFA_SATURATION_PROVENANCE",
              "IRIS_26468_WRONSKI_CFA_SATURATION_VALID_ACCUMULATION")
accum.write_text(t)

# Finalize from valid denominator; use total denominator only for validity ratio.
t = finalize.read_text()
t = replace_once(
    t,
    '''    vec3 num=imageLoad(currentNumerator,p).rgb;
    vec3 den=max(imageLoad(currentDenominator,p).rgb,vec3(1e-12));
    vec3 wbRgb=num/den;
    vec4 support=imageLoad(currentFrameSupport,p);
    vec3 validDen=max(support.gba,vec3(0.0));
    vec3 validRatio=clamp(validDen/den,vec3(0.0),vec3(1.0));
    float strongestValid=max(validRatio.r,max(validRatio.g,validRatio.b));
    float unsupportedAll=1.0-smoothstep(0.08,0.35,strongestValid);
    float highlightLevel=max(wbRgb.r,max(wbRgb.g,wbRgb.b));
    vec3 neutralWb=vec3(highlightLevel);
    wbRgb=mix(wbRgb,neutralWb,unsupportedAll);
''',
    '''    vec3 num=imageLoad(currentNumerator,p).rgb;
    vec3 validDen=max(imageLoad(currentDenominator,p).rgb,vec3(1e-12));
    vec3 wbRgb=num/validDen;
    vec4 support=imageLoad(currentFrameSupport,p);
    vec3 totalDen=max(support.gba,vec3(1e-12));
    vec3 validRatio=clamp(validDen/totalDen,vec3(0.0),vec3(1.0));

    /* IRIS_26468_PARTIAL_CLIP_CHANNEL_RECOVERY */
    vec3 missing=vec3(1.0)-smoothstep(vec3(0.08),vec3(0.35),validRatio);
    float supportedHighlight=max(
            wbRgb.r*(1.0-missing.r),
            max(wbRgb.g*(1.0-missing.g),wbRgb.b*(1.0-missing.b)));
    float anyObserved=max(1.0-missing.r,max(1.0-missing.g,1.0-missing.b));
    float allMissing=1.0-step(1e-5,anyObserved);
    float fallbackHighlight=max(wbRgb.r,max(wbRgb.g,wbRgb.b));
    supportedHighlight=max(supportedHighlight,allMissing*fallbackHighlight);
    wbRgb=mix(wbRgb,vec3(supportedHighlight),missing);
''',
    "finalizer validity semantics")
t = t.replace("IRIS_26465_FULLY_CLIPPED_NEUTRAL_HIGHLIGHT_RECOVERY",
              "IRIS_26468_SATURATION_VALID_PARTIAL_CHANNEL_RECOVERY")
finalize.write_text(t)

# Remove only Motion IQ Lab submenu from Settings XML.
tree = ET.parse(pref)
root_el = tree.getroot()
removed = 0
for child in list(root_el):
    vals = set(child.attrib.values())
    if "pref_motion_iq_lab_submenu" in vals or "Motion IQ Lab" in vals:
        root_el.remove(child)
        removed += 1
if removed != 1:
    raise SystemExit(f"Motion IQ Lab XML removal expected 1 submenu, removed {removed}")
ET.indent(tree, space="    ")
tree.write(pref, encoding="utf-8", xml_declaration=True)

v = version.read_text()
v = replace_once(v, "VERSION_NAME=0.9726467", "VERSION_NAME=0.9726468", "VERSION_NAME")
v = replace_once(v, "VERSION_BUILD=26467", "VERSION_BUILD=26468", "VERSION_BUILD")
version.write_text(v)
PY

grep -q 'IRIS_26468_SINGLE_FRAME_FULL_MOTION_PIPELINE' "$TMP/candidate/$RECON" \
  || fail "candidate single-frame full pipeline marker"
! grep -q 'return MotionV2Merger.referenceFoundation(inputImages, referenceTimestamp)' \
  "$TMP/candidate/$RECON" || fail "single-frame RAW foundation bypass survived"
grep -q 'IRIS_26468_PRE_DENOISE_DIRECT_RGB_HANDOFF' "$TMP/candidate/$RECON" \
  || fail "candidate pre-denoise marker"
grep -q 'IRIS_26468_PROCESSING_SEAM_DIAGNOSTIC' "$TMP/candidate/$RECON" \
  || fail "candidate seam diagnostic"
grep -q 'IRIS_26468_STAGE_TIMING' "$TMP/candidate/$RECON" \
  || fail "candidate stage timing"
grep -q 'IRIS_26468_CFA_VALID_NUMERATOR_TOTAL_SUPPORT_CARRIER' "$TMP/candidate/$INIT" \
  || fail "candidate reference saturation validity"
grep -q 'IRIS_26468_WRONSKI_CFA_SATURATION_VALID_ACCUMULATION' "$TMP/candidate/$ACCUM" \
  || fail "candidate auxiliary saturation validity"
grep -q 'IRIS_26468_PARTIAL_CLIP_CHANNEL_RECOVERY' "$TMP/candidate/$FINALIZE" \
  || fail "candidate partial clip recovery"
! grep -q 'pref_motion_iq_lab_submenu' "$TMP/candidate/$PREF" \
  || fail "Motion IQ Lab submenu survived"
grep -q '^VERSION_NAME=0\.9726468$' "$TMP/candidate/$VERSION" || fail "candidate version name"
grep -q '^VERSION_BUILD=26468$' "$TMP/candidate/$VERSION" || fail "candidate version build"
pass "candidate/source validation PASS"

python3 - "$TMP/candidate" <<'PY'
from pathlib import Path
import sys, xml.etree.ElementTree as ET
r=Path(sys.argv[1])
for rel in [
    "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java",
    "app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl",
    "app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl",
    "app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl",
]:
    p=r/rel
    s=p.read_text()
    if s.count("{") != s.count("}"):
        raise SystemExit(f"brace mismatch: {rel}")
ET.parse(r/"app/src/main/res/xml/preferences.xml")
print("Temporary-copy validation: PASS")
PY
pass "Temporary-copy validation: PASS"

for f in "$RECON" "$INIT" "$ACCUM" "$FINALIZE" "$PREF" "$VERSION"; do
  cp "$TMP/candidate/$f" "$f"
done

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_AFTER"
python3 - "$HASH_BEFORE" "$HASH_AFTER" \
  "$ALIGN" "$HDRX" "$RECON" "$INIT" "$ACCUM" "$FINALIZE" "$PREF" <<'PY'
from pathlib import Path
import sys
before, after = map(Path, sys.argv[1:3])
allowed = set(sys.argv[3:])
def load(p):
    out={}
    for line in p.read_text().splitlines():
        h,f=line.split("  ",1); out[f]=h
    return out
b=load(before); a=load(after)
if set(b)!=set(a):
    raise SystemExit("protected-file path set changed")
bad=[p for p in b if p not in allowed and b[p]!=a[p]]
if bad:
    raise SystemExit("unexpected protected-file changes: "+", ".join(bad))
print("Protected-file hashes: PASS")
PY

for marker in \
  IRIS_26420_MOTION_V2_NO_LEGACY_ALIGNMENT \
  IRIS_26462_WRONSKI_PUBLISHED_COARSE_TO_FINE_ALIGNMENT \
  IRIS_26463_WRONSKI_PUBLIC_SIGNAL_DOMAIN \
  IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE \
  IRIS_26467_MOTION_OUTPUT_MODE_AUTHORITY
do
  grep -Rqs "$marker" app/src/main || fail "lost protected lineage marker $marker"
done
pass "historical lineage/ownership preservation PASS"

echo "PRE-BUILD SAFETY PROOF PASSED"
echo "  candidate/source validation PASS"
echo "  Temporary-copy validation: PASS"
echo "  protected-file hashes PASS"
echo "  exact backup branch PASS"
echo "  26467 tested lineage reproduced PASS"
echo "  one-frame full Motion V2 JPEG path PASS"
echo "  processing seam diagnostic PASS"
echo "  saturation-valid RGB accumulation PASS"
echo "  Motion IQ Lab Settings removal PASS"
echo "  version/build increment in same script PASS"

cat > "$REPORT" <<EOF
26468 correctness / diagnostic scope
====================================
Base checkpoint: $EXPECTED_APP_BASE
Build: $NEW_VERSION / $NEW_BUILD

Included:
- Reproduces tested 26467 reference-prep/output-routing lineage first.
- Frame slider=1 traverses Motion V2 direct-RGB reconstruction and the same
  ColorTransform -> MotionV2Denoise -> Render -> JPEG path as multi-frame Motion.
- Clipped CFA samples are excluded from RGB numerator and valid denominator.
  Total kernel support is retained separately for per-channel validity.
- Missing clipped channels are recovered only where validity is weak.
- Existing per-channel direct-RGB support telemetry remains active.
- Strongest coarse temporal-support discontinuity is logged for seam correlation.
- Per-aux timings: RAW->CFA, WB CFA, covariance, robustness, 5x5 erosion,
  direct RGB accumulation. Existing 26467 alignmentOnlyMs remains alignment timing.
- Pre-denoise direct-RGB handoff is explicitly marked in log/trace.
- Motion IQ Lab submenu removed from Settings XML only.
- No major shader pass-split performance rewrite in this build.
- No exposure/tone/sharpening redesign.
EOF

chmod +x ./gradlew
set +e
./gradlew assembleDebug --stacktrace 2>&1 | tee "$BUILDLOG"
GRADLE_STATUS=${PIPESTATUS[0]}
set -e
[[ "$GRADLE_STATUS" -eq 0 ]] || fail "Gradle build failed; see $BUILDLOG"
grep -q 'BUILD SUCCESSFUL' "$BUILDLOG" || fail "BUILD SUCCESSFUL marker missing"

APK="$(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | head -n 1)"
[[ -n "$APK" && -f "$APK" ]] || fail "debug APK not found"

OUTAPK="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-correctness-singleframe-seam-debug.apk"
cp "$APK" "$OUTAPK"
cp "$OUTAPK" "$OUTDIR/$OUTAPK"

git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties \
  > "$OUTDIR/26468_exact_source_changes.patch"

{
  echo
  echo "BUILD SUCCESS"
  echo "APK=$OUTAPK"
  echo "SHA256=$(sha256sum "$OUTAPK" | awk '{print $1}')"
  echo "VERSION=$NEW_VERSION"
  echo "BUILD=$NEW_BUILD"
  echo "dev_untouched=true"
  echo "experimental_source_not_committed=true"
} | tee -a "$BUILDLOG"

pass "26468 BUILD SUCCESS"
