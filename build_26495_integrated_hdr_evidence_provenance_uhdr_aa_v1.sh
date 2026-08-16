#!/usr/bin/env bash
set -euo pipefail

fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_INFRA_26494="287590c2e847522cac06752ecdc6be4c0ca3b42a"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BACKUP_BRANCH="backup-26494-before-26495-integrated-hdr-evidence-uhdr"
BASELINE_BUNDLE="26494_successful_app_source.tar.gz"
BASELINE_BUNDLE_SHA="ee4ccb614d9cb216e2e39a76adc8f72ce9fe2a07daa75eb6f705e958502e010b"
BASELINE_MANIFEST="26494_successful_after.sha256"
BASELINE_MANIFEST_SHA="939a7555adaf1b9859e8fc9e40798b38ac5b85343dfbdb45cfe34a4a88b500c7"
TRANSFORM="transform_26495_integrated_hdr_evidence_provenance_uhdr_aa_v1.py"
TRANSFORM_SHA="83f4d2b90fb35689277a8964ab639a1bc9cf3c73a34d7d4a8022e4df20d21b0e"
OLD_VERSION="0.9726494"
OLD_BUILD="26494"
NEW_VERSION="0.9726495"
NEW_BUILD="26495"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-integrated-hdr-evidence-provenance-uhdr-aa-debug.apk"

REPO="$(pwd)"
OUTDIR="$REPO/build_26495_outputs"
TMP="${RUNNER_TEMP:-/tmp}/photon_26495_$$"
BASE="$TMP/base26494"
CAND="$TMP/candidate26495"
PREPATCH="$OUTDIR/26495_pre_edit_exact_26494_complete_binary.patch"
DELTA="$OUTDIR/26495_delta_from_exact_26494.patch"
AFTERHASH="$OUTDIR/26495_successful_after.sha256"
NEXTBUNDLE="$OUTDIR/26495_successful_app_source.tar.gz"
BUILDLOG="$OUTDIR/26495_build.log"
SHADERLOG="$OUTDIR/26495_shader_validation.txt"
REPORT="$OUTDIR/26495_build_report.txt"

rm -rf "$OUTDIR" "$TMP"
mkdir -p "$OUTDIR" "$TMP"
cleanup(){
    set +e
    git worktree remove --force "$BASE" >/dev/null 2>&1 || true
    git worktree remove --force "$CAND" >/dev/null 2>&1 || true
    rm -rf "$TMP"
}
trap cleanup EXIT

echo "=== 26495 INTEGRATED HDR EVIDENCE + PROVENANCE-AWARE RCD + BANDLIMITED UHDR ==="
date -Iseconds || true

# Gate 0: exact infrastructure lineage. Application source in the checked-out
# branch remains protected; 26495 is built from the exact successful 26494 bundle.
BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "wrong branch=$BRANCH expected=$EXPECTED_BRANCH"
[[ "$BRANCH" != "dev" ]] || fail "dev is protected"
git cat-file -e "$EXPECTED_INFRA_26494^{commit}" || fail "26494 infrastructure commit unavailable"
git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "protected app base unavailable"
git merge-base --is-ancestor "$EXPECTED_INFRA_26494" HEAD || fail "HEAD does not descend from exact 26494 infrastructure checkpoint"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties \
    || fail "committed app source changed; infrastructure-only workflow contract violated"
remote_backup="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$remote_backup" == "$EXPECTED_INFRA_26494" ]] \
    || fail "required pre-26495 backup missing/moved: $BACKUP_BRANCH=$remote_backup expected=$EXPECTED_INFRA_26494"
pass "exact 26494 lineage + protected branch + backup branch"

# Gate 1: immutable package identity and self-tests.
[[ -f "$BASELINE_BUNDLE" ]] || fail "missing $BASELINE_BUNDLE"
[[ "$(sha "$BASELINE_BUNDLE")" == "$BASELINE_BUNDLE_SHA" ]] || fail "26494 source bundle SHA mismatch"
[[ -f "$BASELINE_MANIFEST" ]] || fail "missing $BASELINE_MANIFEST"
[[ "$(sha "$BASELINE_MANIFEST")" == "$BASELINE_MANIFEST_SHA" ]] || fail "26494 manifest SHA mismatch"
[[ -f "$TRANSFORM" ]] || fail "missing $TRANSFORM"
[[ "$(sha "$TRANSFORM")" == "$TRANSFORM_SHA" ]] || fail "26495 transform SHA mismatch"
python3 -m py_compile "$TRANSFORM" || fail "transform Python syntax"
python3 "$TRANSFORM" --self-test || fail "26495 math self-test"
bash -n "$0" || fail "build script shell syntax"
pass "package identities + exposure/AA/provenance math self-tests"

reconstruct_exact_26494(){
    local d="$1"
    git worktree add --detach "$d" "$EXPECTED_APP_BASE" >/dev/null
    rm -rf "$d/app/src/main"
    rm -f "$d/app/version.properties"
    ( cd "$d" && tar -xzf "$REPO/$BASELINE_BUNDLE" ) || fail "extract exact 26494 source bundle"
    python3 - "$d" "$REPO/$BASELINE_MANIFEST" <<'PY_VERIFY'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); manifest=Path(sys.argv[2])
expected={}
for line in manifest.read_text().splitlines():
    if line.strip():
        h,rel=line.split(None,1); expected[rel.strip()]=h
actual=sorted([str(p.relative_to(root)) for p in (root/'app/src/main').rglob('*') if p.is_file()] + ['app/version.properties'])
if len(expected)!=856: raise SystemExit(f'expected manifest count={len(expected)} !=856')
if actual!=sorted(expected):
    missing=sorted(set(expected)-set(actual)); extra=sorted(set(actual)-set(expected))
    raise SystemExit(f'canonical file list mismatch missing={missing[:10]} extra={extra[:10]}')
for rel,h in expected.items():
    got=hashlib.sha256((root/rel).read_bytes()).hexdigest()
    if got!=h: raise SystemExit(f'canonical hash mismatch {rel}: {got} != {h}')
ver=(root/'app/version.properties').read_text()
if 'VERSION_NAME=0.9726494' not in ver or 'VERSION_BUILD=26494' not in ver:
    raise SystemExit('exact 26494 version proof failed')
print('PASS: exact successful 26494 source verified 856/856')
PY_VERIFY
}

# Gate 2: reconstruct two independent exact copies. BASE remains immutable proof;
# CAND is the only tree transformed/built.
reconstruct_exact_26494 "$BASE"
reconstruct_exact_26494 "$CAND"
pass "two independent exact 26494 source copies reconstructed"

# Mandatory binary pre-modification patch is made BEFORE any 26495 transform.
(
    cd "$BASE"
    git add -N app/src/main app/version.properties >/dev/null 2>&1 || true
    git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties
) > "$PREPATCH"
[[ -s "$PREPATCH" ]] || fail "pre-edit exact-26494 binary patch empty"
sha256sum "$PREPATCH" > "$PREPATCH.sha256"
pass "binary pre-edit exact-26494 patch created before modification"

# Gate 3: transform candidate and prove exact seven-file scope before version bump.
python3 "$REPO/$TRANSFORM" "$CAND" || fail "26495 candidate transform"
python3 - "$BASE" "$CAND" <<'PY_SCOPE'
from pathlib import Path
import hashlib,sys
base=Path(sys.argv[1]); cand=Path(sys.argv[2])
allowed={
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/assets/shaders/motionv2/rcd26489_populate.glsl',
'app/src/main/assets/shaders/motionv2/rcd26489_opposite.glsl',
'app/src/main/assets/shaders/motionv2/rcd26489_green_rb.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
}
def files(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (root/'app/src/main').rglob('*') if p.is_file()} | {
            'app/version.properties':hashlib.sha256((root/'app/version.properties').read_bytes()).hexdigest()}
a,b=files(base),files(cand)
if set(a)!=set(b): raise SystemExit('candidate file set changed')
changed={r for r in a if a[r]!=b[r]}
if changed!=allowed: raise SystemExit(f'scope mismatch changed={sorted(changed)} expected={sorted(allowed)}')
print('PASS: exact scope: only seven intended 26495 files changed; other 849 canonical files byte-identical')
PY_SCOPE
( cd "$CAND" && git diff --check -- app/src/main app/version.properties ) || fail "candidate whitespace/diff check"
pass "temporary-copy transform + exact scope + whitespace validation"

# Gate 4: architecture/regression invariants. These are ownership proofs, not image-tuning greps.
CAP="$CAND/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
RECON="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
HDRX="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
RCDHOST="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java"
POP="$CAND/app/src/main/assets/shaders/motionv2/rcd26489_populate.glsl"
OPP="$CAND/app/src/main/assets/shaders/motionv2/rcd26489_opposite.glsl"
GRB="$CAND/app/src/main/assets/shaders/motionv2/rcd26489_green_rb.glsl"
GAIN="$CAND/app/src/main/assets/shaders/motionv2/gainmap.glsl"
RENDER="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java"
SHORT="$CAND/app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl"
ACC="$CAND/app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl"
NORM="$CAND/app/src/main/assets/shaders/motionv2/mfsr_bayer_normalize.glsl"
WRONSKI="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java"

# 26489 temporal reconstruction remains untouched/authoritative.
grep -q 'IRIS_26489_BJZHOU_PERSISTENT_BAYER_HOST' "$RECON" || fail "26489 persistent Bayer host missing"
grep -q 'IRIS_26489_ADMISSION_EQUALS_ACCUMULATOR_CONTRIBUTION_INVARIANT' "$RECON" || fail "26489 admitted==contributed invariant missing"
grep -q 'IRIS_26489_BJZHOU_BAYER_NORMALIZE_EXACTLY_ONCE' "$RECON" || fail "26489 normalize-once owner missing"
grep -q 'IRIS_26489_BJZHOU_PERSISTENT_BAYER_ACCUMULATOR_OWNER' "$ACC" || fail "26489 accumulator shader owner missing"
grep -q 'IRIS_26489_BJZHOU_BAYER_NORMALIZE_ONCE' "$NORM" || fail "26489 normalize shader owner missing"
grep -q 'IRIS_26487_WRONSKI_DEFERRED_GPU_CHAIN_NO_PER_DISPATCH_FINISH' "$WRONSKI" || fail "Wronski execution contract missing"
grep -q 'IRIS_26486_FREEZE_BUFFER_AT_SHUTTER_NO_TOPUP_WAIT' "$CAP" || fail "no-topup-wait capture contract missing"
grep -q 'IRIS_26490_EXACT_SHORT_RAW_NEVER_ENTERS_NORMAL_RING' "$CAP" || fail "short/raw isolation callback contract missing"
grep -q 'shortInWronskiList=false short excluded from Wronski=true' "$HDRX" || fail "short RAW isolation from Wronski missing"

# Active-vs-legacy short capture coupling is explicitly proven.
[[ "$(grep -o 'applyMotion26486ExplicitShortCaptureIfNeeded(' "$CAP" | wc -l)" -eq 2 ]] || fail "active short path must be definition + one caller"
[[ "$(grep -o 'applyMotion26480ExplicitShortCaptureIfNeeded()' "$CAP" | wc -l)" -eq 1 ]] || fail "legacy 26480 short path unexpectedly called"
grep -q 'IRIS_26495_PHYSICAL_SHORT_HEADROOM_2P5EV' "$CAP" || fail "2.5EV physical short owner missing"
grep -q 'IRIS_26495_CLAMP_AWARE_SHORT_RADIOMETRY' "$CAP" || fail "clamp-aware actual metadata validation missing"
grep -q '5.656854249492381' "$CAP" || fail "2^2.5 divisor exact value missing"
grep -q 'actualHeadroomEv' "$CAP" || fail "actual headroom telemetry missing"

# Short recovery physics itself is protected byte-for-byte from 26494.
[[ "$(sha "$SHORT")" == "9e347ac07d24360af3285e388ff5ae4e6c96d5ff6bd33edd998a8b820d83565f" ]] \
    || fail "26494 short physical recovery shader changed unexpectedly"
[[ "$(sha "$RECON")" == "84139f9e427de796ac1eb55af359bd36922e8ee9017ee7192b76f7cc596801a5" ]] \
    || fail "26494 reconstruction/accumulator/short-radiometry host changed unexpectedly"

# Provenance is now carried into opponent-color source weighting; no final-RGB color eraser.
grep -q 'IRIS_26495_CENSORED_LUMA_ONLY_CHROMA_AUTHORITY' "$POP" || fail "censored luma-only populate contract missing"
grep -q 'IRIS_26495_RCD_OPPOSITE_PROVENANCE_WEIGHT' "$OPP" || fail "opposite-color provenance weighting missing"
grep -q 'IRIS_26495_RCD_GREEN_SITE_PROVENANCE_WEIGHT' "$GRB" || fail "green-site provenance weighting missing"
[[ "$(grep -o 'setTexture("HighlightProvenance"' "$RCDHOST" | wc -l)" -eq 3 ]] \
    || fail "provenance sampler must be bound to populate + two chroma passes"
grep -q 'censoredOpponentColorAuthority=zero' "$RCDHOST" || fail "RCD chroma authority telemetry missing"
! grep -R -q 'IRIS_26493_FINAL_WRITE_CHROMA' "$CAND/app/src/main" || fail "rejected 26493 final-RGB chroma patch reintroduced"

# UHDR geometry/metadata owners are frozen; only pre-decimation sampling changes.
grep -q 'IRIS_26495_BANDLIMITED_UHDR_GAINMAP' "$GAIN" || fail "bandlimited UHDR shader missing"
grep -q 'FILTER_TAPS = 10' "$GAIN" || fail "UHDR prefilter taps changed"
grep -q 'DOWNSAMPLE = 4' "$GAIN" || fail "gain shader 4:1 geometry changed"
grep -q 'GAINMAP_DOWNSAMPLE = 4' "$RENDER" || fail "gain map dimensions changed"
grep -q 'Math.min(2.5f, OUTPUT_EXPOSURE_SCALE \* postDisplaySensorWhite)' "$RENDER" || fail "UHDR max gain ownership changed"
grep -q 'preDecimationBandlimit=positiveGaussian10x10Sigma2p8' "$RENDER" || fail "UHDR prefilter telemetry missing"
pass "PRE-BUILD SAFETY PROOF PASSED: ownership + 26489 + short physics + RCD provenance + UHDR geometry"

# Gate 5: type-aware GLSL static compilation for all changed shaders.
# Photon substitutes LAYOUT at runtime; compile wrappers reproduce that header.
{
    echo '#version 310 es'
    echo '#define LAYOUT layout(local_size_x=8, local_size_y=8, local_size_z=1) in;'
    tail -n +3 "$POP"
} > "$TMP/rcd_populate.comp"
{
    echo '#version 310 es'
    echo '#define LAYOUT layout(local_size_x=8, local_size_y=8, local_size_z=1) in;'
    tail -n +3 "$OPP"
} > "$TMP/rcd_opposite.comp"
{
    echo '#version 310 es'
    echo '#define LAYOUT layout(local_size_x=8, local_size_y=8, local_size_z=1) in;'
    tail -n +3 "$GRB"
} > "$TMP/rcd_greenrb.comp"
{
    echo '#version 300 es'
    cat "$GAIN"
} > "$TMP/gainmap.frag"
: > "$SHADERLOG"
for spec in "$TMP/rcd_populate.comp:comp" "$TMP/rcd_opposite.comp:comp" "$TMP/rcd_greenrb.comp:comp" "$TMP/gainmap.frag:frag"; do
    f="${spec%%:*}"; stage="${spec##*:}"
    glslangValidator -S "$stage" "$f" >> "$SHADERLOG" 2>&1 || { cat "$SHADERLOG"; fail "GLSL validation failed $f"; }
done
pass "changed GLSL compile validation"

# Gate 6: version increment happens only after all pre-build safety gates, in the
# same script invocation that builds the APK.
python3 - "$CAND/app/version.properties" <<'PY_VER'
from pathlib import Path
p=Path(__import__('sys').argv[1]); s=p.read_text()
a='VERSION_NAME=0.9726494'; b='VERSION_BUILD=26494'
if s.count(a)!=1 or s.count(b)!=1: raise SystemExit('26494 version anchors not unique')
s=s.replace(a,'VERSION_NAME=0.9726495',1).replace(b,'VERSION_BUILD=26495',1)
p.write_text(s)
PY_VER
grep -q '^VERSION_NAME=0\.9726495$' "$CAND/app/version.properties" || fail "version name bump failed"
grep -q '^VERSION_BUILD=26495$' "$CAND/app/version.properties" || fail "version build bump failed"
pass "version incremented to 0.9726495 / 26495 in build command"

# Human-reviewable binary delta: exact successful 26494 -> candidate 26495.
git diff --no-index --binary "$BASE/app" "$CAND/app" > "$DELTA" || [[ $? -eq 1 ]] || fail "delta generation"
[[ -s "$DELTA" ]] || fail "26495 delta empty"

# Gate 7: Java/Android compiler and full APK build are authoritative.
(
    cd "$CAND"
    ./gradlew --no-daemon :app:compileDebugJavaWithJavac
    ./gradlew --no-daemon assembleDebug
) 2>&1 | tee "$BUILDLOG"

mapfile -t APKS < <(find "$CAND/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' | sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#APKS[@]}: ${APKS[*]}"
cp "${APKS[0]}" "$REPO/$APK_NAME"
[[ -s "$REPO/$APK_NAME" ]] || fail "final APK missing"
sha256sum "$REPO/$APK_NAME" > "$OUTDIR/$APK_NAME.sha256"

# Gate 8: retain the exact successful post-transform source as next baseline.
(
    cd "$CAND"
    { find app/src/main -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum; sha256sum app/version.properties; } > "$AFTERHASH"
    tar -czf "$NEXTBUNDLE" app/src/main app/version.properties
)
[[ "$(wc -l < "$AFTERHASH")" -eq 856 ]] || fail "26495 successful manifest count not 856"
sha256sum "$NEXTBUNDLE" "$AFTERHASH" "$DELTA" > "$OUTDIR/26495_artifact_hashes.sha256"

cat > "$REPORT" <<EOF
26495 BUILD SUCCESS
Version: $NEW_VERSION / $NEW_BUILD
Baseline: exact successful 26494 post-build source bundle
Baseline infrastructure checkpoint: $EXPECTED_INFRA_26494
Required pre-edit backup branch: $BACKUP_BRANCH
APK: $APK_NAME
APK SHA256: $(sha "$REPO/$APK_NAME")

Integrated architecture correction
1. Normal 26489 Motion stack is frozen: reference frame 0, Wronski alignment, R32F persistent Bayer accumulation, admitted==contributed, normalize once.
2. One isolated short RAW requests 2.5 EV physical headroom at the same ISO when hardware permits. Actual metadata is validated around the clamped request. It never enters the normal ring or Wronski accumulator.
3. 26494 per-phase NORMAL/CENSORED/SHORT_VALIDATED semantics remain authoritative. The short recovery shader and reconstruction host are byte-identical to tested 26494.
4. Unresolved CENSORED phases become shared balanced-luminance constraints. Their synthetic values have zero opponent-color source weight in the two RCD chroma interpolation passes; NORMAL and SHORT_VALIDATED remain full chroma evidence.
5. UHDR remains 1/4 resolution with the same geometry, max-ratio and JPEG attachment. HDR and SDR linear luminance are identically prefiltered by a positive symmetric 10x10 Gaussian before 4:1 sampling. Full-resolution SDR is never filtered.

Math proofs
- 2^2.5 = 5.656854249492381; nominal short ratio = 0.1767766952966369.
- Existing +/-0.35 EV actual-exposure tolerance implies worst shortToNormal scale about 7.210 < existing 8.0 reconstruction clamp.
- Current 4x4 box response at source f=1/8: ~0.6533.
- New 10-tap 1D Gaussian response at f=1/8: ~0.0943; at f=3/16: ~0.0340; all coefficients positive/symmetric/sum 1.
- With all provenance sources trusted, the RCD opponent interpolation equations reduce exactly to 26494 arithmetic.

Protected
- no normal exposure/ISO change
- no normal frame-count or shutter-wait change
- no Wronski/robustness/accumulator change
- no Camera2 color-matrix change
- no tone/display exposure change
- no short-recovery threshold/correspondence math change
- no MotionV2Denoise or sharpening reintroduction
- no rejected 26493 final-RGB chroma stabilizer
EOF

pass "26495 BUILD SUCCESS"
pass "exact successful 26494 -> scoped 26495 lineage proven"
pass "APK + next canonical source baseline emitted"
echo "APK: $REPO/$APK_NAME"
