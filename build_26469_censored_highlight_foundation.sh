#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BACKUP_BRANCH="backup-26468-before-26469-foundation"
BASE_26468_SCRIPT="build_26468_correctness_singleframe_seam.sh"
BASE_26468_SCRIPT_BLOB="18480278617deb2702abf845a1dcc29d09146b65"
OLD_VERSION="0.9726468"
OLD_BUILD="26468"
NEW_VERSION="0.9726469"
NEW_BUILD="26469"
OUTDIR="build_26469_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-censored-highlight-foundation-debug.apk"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }

rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26469_source_audit.txt"
REPORT="$OUTDIR/26469_build_report.txt"
MATH="$OUTDIR/26469_math_validation.txt"
HASH_INITIAL="$OUTDIR/26469_protected_initial.sha256"
HASH_26468="$OUTDIR/26469_protected_26468_base.sha256"
HASH_AFTER="$OUTDIR/26469_protected_after.sha256"
PREPATCH="$OUTDIR/26469_pre_edit_binary.patch"
RECOVERY="$OUTDIR/26469_recovery_binary.patch"
SOURCEPATCH="$OUTDIR/26469_source.patch"

{
  echo "=== 26469 GUARDED CENSORED-HIGHLIGHT / CFA-COHERENCE FOUNDATION BUILD ==="
  date -Iseconds
} | tee "$AUDIT"

branch="$(git rev-parse --abbrev-ref HEAD)"
[[ "$branch" == "$EXPECTED_BRANCH" ]] || fail "branch gate: got $branch expected $EXPECTED_BRANCH"
pass "branch gate" | tee -a "$AUDIT"

git fetch origin "$BACKUP_BRANCH" --quiet
backup_sha="$(git rev-parse "origin/$BACKUP_BRANCH")"
[[ "$backup_sha" == "$EXPECTED_APP_BASE" ]] || fail "backup branch $BACKUP_BRANCH=$backup_sha expected $EXPECTED_APP_BASE"
pass "backup branch exact 26468 infrastructure checkpoint" | tee -a "$AUDIT"

git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties \
  || fail "application source changed since verified 26468 infrastructure checkpoint"
pass "application source unchanged from verified checkpoint" | tee -a "$AUDIT"

[[ -f "$BASE_26468_SCRIPT" ]] || fail "missing $BASE_26468_SCRIPT"
base_blob="$(git hash-object "$BASE_26468_SCRIPT")"
[[ "$base_blob" == "$BASE_26468_SCRIPT_BLOB" ]] \
  || fail "26468 precursor blob=$base_blob expected=$BASE_26468_SCRIPT_BLOB"
pass "26468 precursor script exact" | tee -a "$AUDIT"

git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$PREPATCH"
pass "binary pre-edit patch created before source modification" | tee -a "$AUDIT"

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_INITIAL"
sha256sum app/version.properties >> "$HASH_INITIAL"
pass "initial protected-file hashes captured before source modification" | tee -a "$AUDIT"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Reproduce the successfully tested 26468 application state without running its Gradle build.
PRECURSOR="$TMP/26468_transform_only.sh"
awk '
  /^chmod \+x \.\/gradlew$/ { exit }
  { print }
' "$BASE_26468_SCRIPT" > "$PRECURSOR"

python3 - "$PRECURSOR" "$TMP/26468_precursor_outputs" <<'PY_PRECURSOR_OUTDIR'
from pathlib import Path
import sys
path = Path(sys.argv[1])
anchor = 'OUTDIR="build_26468_outputs"'
replacement = 'OUTDIR="' + sys.argv[2] + '"'
text = path.read_text()
count = text.count(anchor)
if count != 1:
    raise SystemExit(f"26468 precursor OUTDIR anchor expected exactly 1, found {count}")
path.write_text(text.replace(anchor, replacement, 1))
print("26468 precursor OUTDIR rewrite: PASS")
PY_PRECURSOR_OUTDIR
chmod +x "$PRECURSOR"
bash -n "$PRECURSOR" || fail "26468 transform-only precursor syntax"
bash "$PRECURSOR"

grep -q '^VERSION_NAME=0\.9726468$' app/version.properties || fail "26468 precursor VERSION_NAME"
grep -q '^VERSION_BUILD=26468$' app/version.properties || fail "26468 precursor VERSION_BUILD"
grep -q 'IRIS_26468_SINGLE_FRAME_FULL_MOTION_PIPELINE' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java \
  || fail "26468 single-frame lineage missing"
grep -q 'IRIS_26468_CFA_VALID_NUMERATOR_TOTAL_SUPPORT_CARRIER' \
  app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl \
  || fail "26468 saturation-valid reference lineage missing"
pass "26468 tested application lineage reproduced" | tee -a "$AUDIT"

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_26468"
sha256sum app/version.properties >> "$HASH_26468"

RECON="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
INIT="app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl"
ACCUM="app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl"
FINALIZE="app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl"
COV="app/src/main/assets/shaders/motionv2/mfsr_kernel_covariance.glsl"
VERSION="app/version.properties"

for f in "$RECON" "$INIT" "$ACCUM" "$FINALIZE" "$COV" "$VERSION"; do
  mkdir -p "$TMP/candidate/$(dirname "$f")"
  cp "$f" "$TMP/candidate/$f"
done

python3 - "$TMP/candidate" <<'PY_TRANSFORM'
from pathlib import Path
import sys
root=Path(sys.argv[1])
recon=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java'
init=root/'app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl'
accum=root/'app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl'
finalize=root/'app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl'
cov=root/'app/src/main/assets/shaders/motionv2/mfsr_kernel_covariance.glsl'
version=root/'app/version.properties'

def replace_once(text, old, new, label):
    n=text.count(old)
    if n != 1:
        raise SystemExit(f'{label}: expected exactly one anchor, found {n}')
    return text.replace(old,new,1)

# 26468 incorrectly made saturation validity multiply radiometric signal itself.
# Restore Wronski num/den brightness evidence and keep unsaturated support separate.
t=init.read_text()
t=replace_once(t,
'''        float cfaSample=cfaAt(p);
        float validity=sampleValidity(cfaSample,c);
        float validW=w*validity;
        num[c]+=cfaSample*validW;
        den[c]+=validW;
        validDen[c]+=w;
''',
'''        float cfaSample=cfaAt(p);
        float validity=sampleValidity(cfaSample,c);
        num[c]+=cfaSample*w;
        den[c]+=w;
        validDen[c]+=w*validity;
''', 'reference dual-evidence accumulation')
t=t.replace('IRIS_26468_CFA_VALID_NUMERATOR_TOTAL_SUPPORT_CARRIER',
            'IRIS_26469_CENSORED_HIGHLIGHT_DUAL_EVIDENCE_REFERENCE')
t=t.replace('total Wronski kernel denominator for R/G/B; currentDenominator carries valid support.',
            'unsaturated chroma support for R/G/B; numerator/denominator retain radiometric lower-bound evidence.')
init.write_text(t)

t=accum.read_text()
t=replace_once(t,
'''        float cfaSample=cfaAt(p);
        float validity=sampleValidity(cfaSample,c);
        float validW=w*validity;
        addNum[c]+=validW*cfaSample;
        addDen[c]+=validW;
        addValidDen[c]+=w;
''',
'''        float cfaSample=cfaAt(p);
        float validity=sampleValidity(cfaSample,c);
        addNum[c]+=w*cfaSample;
        addDen[c]+=w;
        addValidDen[c]+=w*validity;
''', 'aux dual-evidence accumulation')
t=t.replace('IRIS_26468_WRONSKI_CFA_SATURATION_VALID_ACCUMULATION',
            'IRIS_26469_CENSORED_HIGHLIGHT_DUAL_EVIDENCE_AUX')
accum.write_text(t)

# Replace 26468 partial-channel recovery with a shared spatial clipping decision.
# Num/den retains brightness evidence. validDen/den says whether chroma is observed.
t=finalize.read_text()
helper='''
vec3 iris26469ValidityAt(ivec2 q){
    ivec2 hi=imageSize(currentDenominator)-ivec2(1);
    q=clamp(q,ivec2(0),hi);
    vec3 den=max(imageLoad(currentDenominator,q).rgb,vec3(1e-12));
    vec3 validDen=max(imageLoad(currentFrameSupport,q).gba,vec3(0.0));
    return clamp(validDen/den,vec3(0.0),vec3(1.0));
}
float iris26469ClipUncertaintyAt(ivec2 q){
    vec3 v=iris26469ValidityAt(q);
    float weakest=min(v.r,min(v.g,v.b));
    return 1.0-smoothstep(0.10,0.45,weakest);
}
float iris26469CoherentClipUncertainty(ivec2 p){
    float u=0.0;
    for(int iy=-1;iy<=1;iy++) for(int ix=-1;ix<=1;ix++)
        u=max(u,iris26469ClipUncertaintyAt(p+ivec2(ix,iy)));
    return u;
}
'''
t=replace_once(t, 'void main(){', helper+'\n/* IRIS_26469_SPATIALLY_COHERENT_CENSORED_HIGHLIGHT */\nvoid main(){', 'finalizer helper insertion')
old='''    vec3 num=imageLoad(currentNumerator,p).rgb;
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
'''
new='''    vec3 num=imageLoad(currentNumerator,p).rgb;
    vec3 den=max(imageLoad(currentDenominator,p).rgb,vec3(1e-12));
    vec3 wbRgb=num/den;
    vec4 support=imageLoad(currentFrameSupport,p);

    /*
     * Clipped CFA values are censored radiometric observations: they cannot
     * determine exact chroma, but they prove the signal is bright. Therefore
     * they remain in Wronski num/den while support.gba tracks only unsaturated
     * chroma evidence. A shared 3x3 uncertainty is applied to ALL RGB channels
     * together so CFA sites cannot create magenta/green razor transitions.
     */
    float clipUncertainty=iris26469CoherentClipUncertainty(p);
    float highlightLevel=max(wbRgb.r,max(wbRgb.g,wbRgb.b));
    vec3 neutralWb=vec3(highlightLevel);
    wbRgb=mix(wbRgb,neutralWb,clipUncertainty);
'''
t=replace_once(t,old,new,'coherent censored highlight finalization')
t=t.replace('IRIS_26468_SATURATION_VALID_PARTIAL_CHANNEL_RECOVERY',
            'IRIS_26469_CENSORED_HIGHLIGHT_BRIGHTNESS_PRESERVATION')
finalize.write_text(t)

# Stable dominant eigenvector for symmetric 2x2 structure tensor.
# The old (M-lambda2 I)[1,1] form cancels at a legitimate 45-degree case.
t=cov.read_text()
old='''    vec2 e1;
    if(abs(jxy)<1e-12 && abs(jxx-jyy)<1e-12) e1=vec2(1.0,0.0);
    else {
        e1=vec2(jxx+jxy-l2,jxy+jyy-l2);
        if(dot(e1,e1)<1e-16) e1=jxx>=jyy?vec2(1,0):vec2(0,1);
        else e1=normalize(e1);
    }
'''
new='''    /* IRIS_26469_STABLE_SYMMETRIC_TENSOR_EIGENVECTOR
     * Two algebraically equivalent lambda1 eigenvectors are evaluated and the
     * better-conditioned one is selected. This removes the diagonal-edge
     * cancellation of (M-lambda2*I)*[1,1] without changing Wronski eigenvalues
     * or the published kernel-selection law.
     */
    vec2 va=vec2(jxy,l1-jxx);
    vec2 vb=vec2(l1-jyy,jxy);
    float na=dot(va,va);
    float nb=dot(vb,vb);
    vec2 e1;
    if(max(na,nb)>1e-20) e1=normalize(na>=nb?va:vb);
    else e1=jxx>=jyy?vec2(1.0,0.0):vec2(0.0,1.0);
'''
t=replace_once(t,old,new,'stable tensor eigensystem')
cov.write_text(t)

# Make runtime lineage truthful without altering ownership/order.
t=recon.read_text()
t=replace_once(t,
    'IRIS_26465_WRONSKI_PLUS_PROVEN_CFA_SATURATION_VALIDITY',
    'IRIS_26469_CENSORED_HIGHLIGHT_COHERENT_RECONSTRUCTION',
    'runtime reconstruction marker')
t=t.replace('+ " saturationValidity=true"', '+ " censoredHighlightDualEvidence=true"', 1)
t=t.replace('+ " fullyClippedNeutralRecovery=true"', '+ " sharedSpatialClipCoherence=true"', 1)
t=t.replace('+ " partialColorPreserved=true"', '+ " clippedBrightnessPreserved=true"', 1)
recon.write_text(t)

v=version.read_text()
v=replace_once(v,'VERSION_NAME=0.9726468','VERSION_NAME=0.9726469','VERSION_NAME')
v=replace_once(v,'VERSION_BUILD=26468','VERSION_BUILD=26469','VERSION_BUILD')
version.write_text(v)
PY_TRANSFORM

# Candidate/source validation before touching real 26468-derived files.
grep -q 'IRIS_26469_CENSORED_HIGHLIGHT_DUAL_EVIDENCE_REFERENCE' "$TMP/candidate/$INIT" || fail "candidate reference dual-evidence marker"
grep -q 'num\[c\]+=cfaSample\*w;' "$TMP/candidate/$INIT" || fail "candidate reference brightness evidence"
grep -q 'validDen\[c\]+=w\*validity;' "$TMP/candidate/$INIT" || fail "candidate reference chroma support"
grep -q 'IRIS_26469_CENSORED_HIGHLIGHT_DUAL_EVIDENCE_AUX' "$TMP/candidate/$ACCUM" || fail "candidate aux dual-evidence marker"
grep -q 'addNum\[c\]+=w\*cfaSample;' "$TMP/candidate/$ACCUM" || fail "candidate aux brightness evidence"
grep -q 'IRIS_26469_SPATIALLY_COHERENT_CENSORED_HIGHLIGHT' "$TMP/candidate/$FINALIZE" || fail "candidate coherent highlight marker"
grep -q 'iris26469CoherentClipUncertainty' "$TMP/candidate/$FINALIZE" || fail "candidate shared clip coherence"
grep -q 'IRIS_26469_STABLE_SYMMETRIC_TENSOR_EIGENVECTOR' "$TMP/candidate/$COV" || fail "candidate stable eigensystem marker"
grep -q '^VERSION_NAME=0\.9726469$' "$TMP/candidate/$VERSION" || fail "candidate version name"
grep -q '^VERSION_BUILD=26469$' "$TMP/candidate/$VERSION" || fail "candidate version build"
! grep -q 'float validW=w\*validity;' "$TMP/candidate/$INIT" || fail "26468 black-core reference weighting survived"
! grep -q 'float validW=w\*validity;' "$TMP/candidate/$ACCUM" || fail "26468 black-core aux weighting survived"
pass "candidate/source validation PASS" | tee -a "$AUDIT"

python3 - "$TMP/candidate" "$MATH" <<'PY_VALIDATE'
from pathlib import Path
import math, sys
root=Path(sys.argv[1]); report=Path(sys.argv[2])
for rel in [
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
 'app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl',
 'app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl',
 'app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl',
 'app/src/main/assets/shaders/motionv2/mfsr_kernel_covariance.glsl']:
    s=(root/rel).read_text()
    if s.count('{') != s.count('}'):
        raise SystemExit(f'brace mismatch: {rel}')

def smoothstep(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a)))
    return t*t*(3-2*t)

def validity(x,clip=1.0):
    return 1.0-smoothstep(.985*clip,.998*clip,x)

# Censored-radiance proof: clipped evidence must not become black.
w=[1.0,0.7,0.4]
s=[1.0,1.0,1.0]
num=sum(a*b for a,b in zip(w,s)); den=sum(w)
wb=num/den
if wb < 0.99: raise SystemExit('clipped brightness lower-bound proof failed')
valid=sum(a*validity(b) for a,b in zip(w,s))/den
if valid > 1e-6: raise SystemExit('clipped chroma-validity proof failed')
unc=1.0-smoothstep(.10,.45,valid)
if unc < .999: raise SystemExit('shared clipping uncertainty proof failed')
# Unsaturated evidence must pass unchanged.
valid2=validity(.5)
unc2=1.0-smoothstep(.10,.45,valid2)
if unc2 > 1e-6: raise SystemExit('unsaturated pass-through proof failed')

# Stable symmetric 2x2 dominant eigenvector residual checks, including the
# old cancellation case [[2,-1],[-1,2]] whose lambda1 vector is diagonal.
def eigvec(a,b,c):
    tr=a+c; disc=math.sqrt(max((a-c)*(a-c)+4*b*b,0.0))
    l1=.5*(tr+disc)
    va=(b,l1-a); vb=(l1-c,b)
    na=va[0]**2+va[1]**2; nb=vb[0]**2+vb[1]**2
    v=va if na>=nb else vb
    n=math.hypot(*v)
    if n < 1e-10: v=(1.0,0.0) if a>=c else (0.0,1.0)
    else: v=(v[0]/n,v[1]/n)
    r0=a*v[0]+b*v[1]-l1*v[0]
    r1=b*v[0]+c*v[1]-l1*v[1]
    return math.hypot(r0,r1)
for m in [(2,-1,2),(2,1,2),(5,.2,1),(1,.2,5),(3,0,3),(10,-3,2)]:
    if eigvec(*m) > 1e-6: raise SystemExit(f'eigenvector residual failed: {m}')
report.write_text('''26469 mathematical validation PASS\n\n- clipped CFA evidence remains positive in Wronski numerator/denominator\n- clipped samples lose chroma authority without losing brightness authority\n- unsaturated samples remain unchanged\n- shared clipping uncertainty is scalar/common to R,G,B\n- stable symmetric 2x2 dominant eigenvector residual < 1e-6 for test matrices\n- explicit +/-45 degree diagonal cases PASS\n''')
print('Temporary-copy validation: PASS')
PY_VALIDATE
pass "Temporary-copy validation: PASS" | tee -a "$AUDIT"

# Apply only the already-validated candidate transformation.
for f in "$RECON" "$INIT" "$ACCUM" "$FINALIZE" "$COV" "$VERSION"; do
  cp "$TMP/candidate/$f" "$f"
done

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_AFTER"
sha256sum app/version.properties >> "$HASH_AFTER"
python3 - "$HASH_26468" "$HASH_AFTER" "$RECON" "$INIT" "$ACCUM" "$FINALIZE" "$COV" "$VERSION" <<'PY_HASH'
from pathlib import Path
import sys
before,after=map(Path,sys.argv[1:3]); allowed=set(sys.argv[3:])
def load(p):
    d={}
    for line in p.read_text().splitlines():
        h,f=line.split('  ',1); d[f]=h
    return d
b=load(before); a=load(after)
if set(b)!=set(a): raise SystemExit('protected-file path set changed')
bad=[p for p in b if p not in allowed and b[p]!=a[p]]
if bad: raise SystemExit('unexpected protected-file changes: '+', '.join(bad))
print('Protected-file hashes: PASS')
PY_HASH

for marker in \
  IRIS_26420_MOTION_V2_NO_LEGACY_ALIGNMENT \
  IRIS_26462_WRONSKI_PUBLISHED_COARSE_TO_FINE_ALIGNMENT \
  IRIS_26463_WRONSKI_PUBLIC_SIGNAL_DOMAIN \
  IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE \
  IRIS_26467_MOTION_OUTPUT_MODE_AUTHORITY \
  IRIS_26468_SINGLE_FRAME_FULL_MOTION_PIPELINE \
  IRIS_26468_PROCESSING_SEAM_DIAGNOSTIC \
  IRIS_26469_CENSORED_HIGHLIGHT_COHERENT_RECONSTRUCTION
do
  grep -Rqs "$marker" app/src/main || fail "lost required lineage marker $marker"
done
pass "historical lineage/ownership preservation PASS" | tee -a "$AUDIT"

git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$RECOVERY"
git diff "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$SOURCEPATCH"

echo "PRE-BUILD SAFETY PROOF PASSED" | tee -a "$AUDIT"
echo "  candidate/source validation PASS" | tee -a "$AUDIT"
echo "  Temporary-copy validation: PASS" | tee -a "$AUDIT"
echo "  protected-file hashes PASS" | tee -a "$AUDIT"
echo "  exact backup branch PASS" | tee -a "$AUDIT"
echo "  26468 tested lineage reproduced PASS" | tee -a "$AUDIT"
echo "  clipped brightness preserved / chroma authority separated PASS" | tee -a "$AUDIT"
echo "  shared spatial RGB clipping transition PASS" | tee -a "$AUDIT"
echo "  stable tensor eigensystem PASS" | tee -a "$AUDIT"
echo "  version/build increment in same script PASS" | tee -a "$AUDIT"

cat > "$REPORT" <<EOF_REPORT
26469 censored-highlight / CFA-coherence foundation
==================================================
Base infrastructure checkpoint: $EXPECTED_APP_BASE
Backup branch: $BACKUP_BRANCH
Build: $NEW_VERSION / $NEW_BUILD

Scope:
- Reproduces successful 26468 app lineage first, including the one-frame full
  Motion V2 control and permanent seam/stage telemetry.
- Corrects 26468 black-core regression: clipped CFA measurements remain in the
  Wronski radiometric numerator/denominator instead of being multiplied toward
  zero by saturation validity.
- Keeps unsaturated support separately as chroma authority.
- Uses a shared 3x3 clipping-uncertainty scalar for R/G/B so adjacent CFA colors
  cannot independently switch reconstruction regime and create pink/green razor
  or zipper edges around clipped highlights.
- Replaces a numerically cancellable symmetric-tensor eigenvector expression
  with a conditioned lambda1 eigenvector selection. Wronski eigenvalues and
  kernel-selection law remain unchanged.
- Does not change Wronski alignment factors/radii/metrics/ICA, robustness,
  exposure, tone, MotionV2Denoise, sharpening state, Ultra HDR, or output routing.
- Performance architecture is intentionally not rewritten in this correctness
  build; 26468 timing telemetry remains available for the next scheduling pass.

Public technical basis reviewed:
- Wronski et al., Handheld Multi-Frame Super-Resolution, SIGGRAPH 2019.
- Lafenetre/Facciolo/Eboli, Implementing Handheld Burst Super-Resolution,
  IPOL 2023 (implementation details; accumulated-robustness denoiser kept out of
  this build to avoid mixing a blur-policy change with the clipping correction).
- Lecouat et al., High Dynamic Range and Super-Resolution from Raw Image Bursts,
  2022, for the distinction between saturated/censored measurements and true HDR
  recovery from bracketed exposure evidence.
EOF_REPORT

# Version increment and APK build occur in this same guarded operation.
rm -f ./*.apk
chmod +x ./gradlew
./gradlew assembleDebug --no-daemon

echo "BUILD SUCCESSFUL verified by Gradle return code" | tee -a "$REPORT"
mapfile -t apks < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | sort)
[[ ${#apks[@]} -ge 1 ]] || fail "no debug APK found"
cp "${apks[0]}" "$APK_NAME"
[[ -s "$APK_NAME" ]] || fail "APK copy missing/empty"
sha="$(sha256sum "$APK_NAME" | awk '{print $1}')"
{
  echo "BUILD SUCCESS"
  echo "APK=$APK_NAME"
  echo "SHA256=$sha"
  echo "VERSION=$NEW_VERSION"
  echo "BUILD=$NEW_BUILD"
  echo "dev_untouched=true"
  echo "experimental_source_not_committed=true"
} | tee -a "$REPORT"
pass "26469 BUILD SUCCESS"
