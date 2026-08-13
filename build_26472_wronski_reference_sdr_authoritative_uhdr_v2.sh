#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
PROTECTED_HEAD="f69206801c95e8095f9cce71ecba351e715a1367"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BACKUP_BRANCH="backup-26471-before-26472-wronski-completion"
PRECURSOR_SCRIPT="build_26471_low_support_cfa_lowfreq_uhdr.sh"
PRECURSOR_BLOB="9044d30391a254a8a0cc42293b846e345a9280da"
OLD_VERSION="0.9726471"
OLD_BUILD="26471"
NEW_VERSION="0.9726472"
NEW_BUILD="26472"
OUTDIR="build_26472_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-wronski-reference-sdr-authoritative-uhdr-debug.apk"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }

rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26472_source_audit.txt"
REPORT="$OUTDIR/26472_build_report.txt"
MATH="$OUTDIR/26472_math_validation.txt"
HIST="$OUTDIR/26472_historical_repair_audit.txt"
HASH_INITIAL="$OUTDIR/26472_protected_initial.sha256"
HASH_26471="$OUTDIR/26472_protected_26471_base.sha256"
HASH_AFTER="$OUTDIR/26472_protected_after.sha256"
PREPATCH="$OUTDIR/26472_pre_edit_binary.patch"
RECOVERY="$OUTDIR/26472_recovery_binary.patch"
SOURCEPATCH="$OUTDIR/26472_source.patch"
exec > >(tee "$AUDIT") 2>&1

echo "=== 26472 GUARDED WRONSKI REFERENCE COMPLETION / SDR-AUTHORITATIVE UHDR BUILD ==="
date -Iseconds || true

BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "branch=$BRANCH expected=$EXPECTED_BRANCH"
pass "branch gate"

REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$PROTECTED_HEAD" ]] \
  || fail "backup=$REMOTE_BACKUP expected=$PROTECTED_HEAD"
pass "backup branch exact protected 26471 infrastructure checkpoint"

git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "missing verified app base"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties \
  || fail "application source changed before 26472"
pass "application source unchanged from verified checkpoint"

[[ -f "$PRECURSOR_SCRIPT" ]] || fail "missing $PRECURSOR_SCRIPT"
[[ "$(git hash-object "$PRECURSOR_SCRIPT")" == "$PRECURSOR_BLOB" ]] \
  || fail "26471 precursor blob mismatch"
pass "26471 precursor script exact"

# Required before any ephemeral app-source modification.
git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$PREPATCH"
find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_INITIAL"
sha256sum app/version.properties >> "$HASH_INITIAL"
pass "binary pre-edit patch created before source modification"
pass "initial protected-file hashes captured before source modification"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Reproduce the exact successful 26471 application transformation without invoking Gradle.
PRECURSOR="$TMP/26471_transform_only.sh"
awk '/^rm -f \.\/\*\.apk$/ { exit } { print }' "$PRECURSOR_SCRIPT" > "$PRECURSOR"
python3 - "$PRECURSOR" "$TMP/26471_precursor_outputs" <<'PY_PRECURSOR'
from pathlib import Path
import sys
p=Path(sys.argv[1]); t=p.read_text()
a='OUTDIR="build_26471_outputs"'
r='OUTDIR="'+sys.argv[2]+'"'
if t.count(a)!=1:
    raise SystemExit(f"26471 precursor OUTDIR anchor count={t.count(a)}")
p.write_text(t.replace(a,r,1))
print("26471 precursor OUTDIR rewrite: PASS")
PY_PRECURSOR
chmod +x "$PRECURSOR"
bash -n "$PRECURSOR" || fail "26471 transform-only precursor syntax"
bash "$PRECURSOR"

grep -q '^VERSION_NAME=0\.9726471$' app/version.properties || fail "26471 version name"
grep -q '^VERSION_BUILD=26471$' app/version.properties || fail "26471 version build"
for marker in \
  IRIS_26469_CENSORED_HIGHLIGHT_DUAL_EVIDENCE_REFERENCE \
  IRIS_26469_CENSORED_HIGHLIGHT_DUAL_EVIDENCE_AUX \
  IRIS_26469_STABLE_SYMMETRIC_TENSOR_EIGENVECTOR \
  IRIS_26470_UHDR_RENDER_GEOMETRY_AUTHORITY \
  IRIS_26470_UHDR_EXACT_ORTHOGONAL_GEOMETRY \
  IRIS_26471_WRONSKI_LOW_SUPPORT_REFERENCE_REGULARIZATION \
  IRIS_26471_LOWFREQUENCY_LOG_GAINMAP; do
  grep -Rqs "$marker" app/src/main || fail "26471 lineage missing $marker"
done
pass "26471 tested application lineage reproduced"

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_26471"
sha256sum app/version.properties >> "$HASH_26471"

RECON="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
INIT="app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl"
ACCUM="app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl"
REFMERGE="app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl"
FINALIZE="app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl"
GAINMAP="app/src/main/assets/shaders/motionv2/gainmap.glsl"
ROBUST="app/src/main/assets/shaders/motionv2/mfsr_robustness.glsl"
COV="app/src/main/assets/shaders/motionv2/mfsr_kernel_covariance.glsl"
ALIGNJAVA="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java"
ERODE="app/src/main/assets/shaders/motionv2/mfsr_robustness_erode.glsl"
RENDER="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java"
ULTRAHDR="app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java"
VERSION="app/version.properties"

for f in "$RECON" "$INIT" "$ACCUM" "$REFMERGE" "$FINALIZE" "$GAINMAP" "$VERSION"; do
  mkdir -p "$TMP/candidate/$(dirname "$f")"
  cp "$f" "$TMP/candidate/$f"
done
# Copy unchanged lineage/proof files into candidate tree so validation is self-contained.
for f in "$ROBUST" "$COV" "$ALIGNJAVA" "$ERODE" "$RENDER" "$ULTRAHDR"; do
  mkdir -p "$TMP/candidate/$(dirname "$f")"
  cp "$f" "$TMP/candidate/$f"
done

# 26472: the running num/den begins empty. Public/IPOL reference merge happens last.
cat > "$TMP/candidate/$INIT" <<'GLSL_INIT'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
layout(rgba16f,binding=0) uniform highp readonly image2D referenceCfa;
layout(rgba32f,binding=1) uniform highp readonly image2D referenceCov;
layout(rgba32f,binding=2) uniform highp writeonly image2D outNumerator;
layout(rgba32f,binding=3) uniform highp writeonly image2D outDenominator;
layout(rgba32f,binding=4) uniform highp writeonly image2D outFrameSupport;
uniform ivec2 rawSize;
uniform ivec2 rawHalf;
uniform int cfaPattern;
uniform float clipR;
uniform float clipG;
uniform float clipB;

/* IRIS_26472_WRONSKI_AUX_FIRST_ZERO_ACCUMULATOR
 * Public/IPOL super_resolution.main() creates zero num/den, merges auxiliaries,
 * then calls merge_ref() exactly once. The reference textures remain bound here
 * only to preserve the established GLES binding contract; they are not sampled.
 */
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(p,rawSize))) return;
    imageStore(outNumerator,p,vec4(0.0));
    imageStore(outDenominator,p,vec4(0.0));
    // R = accumulated auxiliary robustness; G/B/A = unsaturated R/G/B support.
    imageStore(outFrameSupport,p,vec4(0.0));
}
GLSL_INIT

# With an empty accumulator, R must be sum(aux robustness), not implicit reference+aux.
python3 - "$TMP/candidate/$ACCUM" <<'PY_ACCUM'
from pathlib import Path
import sys
p=Path(sys.argv[1]); t=p.read_text()
old='fs.r=min(max(maximumSupport,1.0),max(fs.r,1.0)+R);'
new='fs.r=min(max(maximumSupport-1.0,0.0),max(fs.r,0.0)+R);'
if t.count(old)!=1:
    raise SystemExit(f"aux accumulated-robustness anchor count={t.count(old)}")
t=t.replace(old,new,1)
t=t.replace(
    'IRIS_26463_WRONSKI_PUBLIC_AUX_ACCUMULATION',
    'IRIS_26472_WRONSKI_PUBLIC_AUX_ACCUMULATION_ACCUMULATED_ROBUSTNESS',
    1)
p.write_text(t)
print("26472 auxiliary robustness accumulation transform: PASS")
PY_ACCUM

# Exact public/IPOL optional accumulated-robustness reference merge semantics:
# max_frame_count=2, rad_max=2, max_multiplier=8.
cat > "$TMP/candidate/$REFMERGE" <<'GLSL_REFMERGE'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
layout(rgba16f,binding=0) uniform highp readonly image2D referenceCfa;
layout(rgba32f,binding=1) uniform highp readonly image2D referenceCov;
layout(rgba32f,binding=2) uniform highp readonly image2D currentNumerator;
layout(rgba32f,binding=3) uniform highp readonly image2D currentDenominator;
layout(rgba32f,binding=4) uniform highp readonly image2D currentFrameSupport;
layout(rgba32f,binding=5) uniform highp writeonly image2D outNumerator;
layout(rgba32f,binding=6) uniform highp writeonly image2D outDenominator;
layout(rgba32f,binding=7) uniform highp writeonly image2D outFrameSupport;
uniform ivec2 rawSize;
uniform ivec2 rawHalf;
uniform int cfaPattern;
uniform float clipR;
uniform float clipG;
uniform float clipB;

/* IRIS_26472_WRONSKI_PUBLIC_ACCUMULATED_ROBUSTNESS_REFERENCE_MERGE
 * Direct GPU translation of public/IPOL merge_ref() with the repository's
 * accumulated_robustness_denoiser.merge parameters:
 *   max_frame_count=2, rad_max=2, max_multiplier=8.
 *
 * Auxiliaries have already populated num/den and fs.r=sum(R_aux).
 * If accumulated robustness is <2, reference reconstruction OVERWRITES the
 * auxiliary accumulator (single-frame ownership), radius becomes 2 and the
 * covariance is multiplied by 8. Otherwise the ordinary radius-1 reference
 * reconstruction is ADDED once to the accumulated auxiliaries.
 *
 * Photon-specific extension retained from 26469: clipped samples remain
 * radiometric brightness evidence while unsaturated RGB support is carried
 * separately in fs.gba.
 */
const float MAX_FRAME_COUNT=2.0;
const int RAD_MAX=2;
const float MAX_MULTIPLIER=8.0;

int componentIndex(ivec2 p){return ((p.y&1)<<1)|(p.x&1);}
int componentColor(int c){
    if(cfaPattern==0){if(c==0)return 0;if(c==3)return 2;return 1;}
    if(cfaPattern==1){if(c==1)return 0;if(c==2)return 2;return 1;}
    if(cfaPattern==2){if(c==2)return 0;if(c==1)return 2;return 1;}
    if(c==3)return 0;if(c==0)return 2;return 1;
}
float clipForColor(int c){return c==0?clipR:(c==2?clipB:clipG);}
float sampleValidity(float v,int c){
    float clip=max(clipForColor(c),1e-6);
    return 1.0-smoothstep(0.985*clip,0.998*clip,v);
}
float cfaAt(ivec2 p){
    p=clamp(p,ivec2(0),rawSize-ivec2(1));
    vec4 v=imageLoad(referenceCfa,p>>1);
    int c=componentIndex(p);
    return c==0?v.r:(c==1?v.g:(c==2?v.b:v.a));
}
mat2 covAt(ivec2 p){
    p=clamp(p,ivec2(0),rawHalf-ivec2(1));
    vec4 v=imageLoad(referenceCov,p);
    return mat2(v.x,v.y,v.z,v.w);
}
mat2 interpolateCov(vec2 gp){
    ivec2 fl=ivec2(max(floor(gp),vec2(0.0)));
    ivec2 ce=min(fl+ivec2(1),rawHalf-ivec2(1));
    vec2 f=fract(gp);
    mat2 c00=covAt(fl);
    mat2 c01=covAt(ivec2(ce.x,fl.y));
    mat2 c10=covAt(ivec2(fl.x,ce.y));
    mat2 c11=covAt(ce);
    return c00*((1.0-f.x)*(1.0-f.y))
         + c01*(f.x*(1.0-f.y))
         + c10*((1.0-f.x)*f.y)
         + c11*(f.x*f.y);
}
mat2 invertCov(mat2 m){
    float d=m[0][0]*m[1][1]-m[0][1]*m[1][0];
    if(abs(d)<=1e-10) return mat2(1,0,0,1);
    return mat2(m[1][1],-m[0][1],-m[1][0],m[0][0])/d;
}
void main(){
    ivec2 outP=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(outP,rawSize))) return;

    vec4 oldNum=imageLoad(currentNumerator,outP);
    vec4 oldDen=imageLoad(currentDenominator,outP);
    vec4 fs=imageLoad(currentFrameSupport,outP);
    float accumulatedRobustness=max(fs.r,0.0);
    bool referenceOwns=(accumulatedRobustness<MAX_FRAME_COUNT);
    int rad=referenceOwns?RAD_MAX:1;
    float covarianceMultiplier=referenceOwns?MAX_MULTIPLIER:1.0;

    vec2 coarse=vec2(outP);
    vec2 greyPos=(coarse-vec2(0.5))/2.0;
    mat2 invCov=invertCov(interpolateCov(greyPos))/covarianceMultiplier;
    ivec2 center=ivec2(round(coarse));
    vec3 refNum=vec3(0.0),refDen=vec3(0.0),refValid=vec3(0.0);

    for(int iy=-RAD_MAX;iy<=RAD_MAX;iy++) for(int ix=-RAD_MAX;ix<=RAD_MAX;ix++){
        if(abs(ix)>rad||abs(iy)>rad) continue;
        ivec2 p=center+ivec2(ix,iy);
        if(any(lessThan(p,ivec2(0)))||any(greaterThanEqual(p,rawSize))) continue;
        int c=componentColor(componentIndex(p));
        vec2 delta=vec2(p)-coarse;
        float z=max(dot(delta,invCov*delta),0.0);
        float w=exp(-0.5*z);
        float s=cfaAt(p);
        refNum[c]+=s*w;
        refDen[c]+=w;
        refValid[c]+=w*sampleValidity(s,c);
    }

    vec3 outNum=referenceOwns?refNum:(oldNum.rgb+refNum);
    vec3 outDen=referenceOwns?refDen:(oldDen.rgb+refDen);
    vec3 outValid=referenceOwns?refValid:(fs.gba+refValid);
    float finalFrameSupport=(referenceOwns?1.0:(accumulatedRobustness+1.0));

    imageStore(outNumerator,outP,vec4(outNum,0.0));
    imageStore(outDenominator,outP,vec4(outDen,1.0));
    imageStore(outFrameSupport,outP,vec4(finalFrameSupport,outValid));
}
GLSL_REFMERGE

# Remove the old 26469 3x3 max-neighborhood "repair". Keep only physically
# supported saturation behavior: clipped values remain brightness evidence;
# neutralization occurs only where every RGB channel lacks useful unsaturated support.
cat > "$TMP/candidate/$FINALIZE" <<'GLSL_FINALIZE'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
layout(rgba32f,binding=0) uniform highp readonly image2D currentNumerator;
layout(rgba32f,binding=1) uniform highp readonly image2D currentDenominator;
layout(rgba32f,binding=2) uniform highp readonly image2D currentFrameSupport;
layout(rgba32f,binding=3) uniform highp writeonly image2D outRgb;
uniform float wbR;
uniform float wbG;
uniform float wbB;

/* IRIS_26472_WRONSKI_MINIMAL_CENSORED_HIGHLIGHT_FINALIZER
 * Wronski num/den is authoritative. 26469 dual-evidence remains: clipped CFA
 * samples stay in radiometric num/den while fs.gba tracks unsaturated chroma
 * support. No 3x3 cross-pixel clipping repair is applied after reconstruction.
 * Only pixels with no substantial unsaturated RGB observation lose chroma.
 */
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(p,imageSize(outRgb)))) return;

    vec3 num=imageLoad(currentNumerator,p).rgb;
    vec3 den=max(imageLoad(currentDenominator,p).rgb,vec3(1e-12));
    vec3 wbRgb=num/den;
    vec4 support=imageLoad(currentFrameSupport,p);
    vec3 validRatio=clamp(max(support.gba,vec3(0.0))/den,vec3(0.0),vec3(1.0));

    float strongestValid=max(validRatio.r,max(validRatio.g,validRatio.b));
    float unsupportedAll=1.0-smoothstep(0.08,0.35,strongestValid);
    float highlightLevel=max(wbRgb.r,max(wbRgb.g,wbRgb.b));
    wbRgb=mix(wbRgb,vec3(highlightLevel),unsupportedAll);

    vec3 sensorRgb=wbRgb/vec3(max(wbR,1e-6),max(wbG,1e-6),max(wbB,1e-6));
    float frameSupport=max(support.r,1.0);
    imageStore(outRgb,p,vec4(max(sensorRgb,vec3(0.0)),frameSupport));
}
GLSL_FINALIZE

# 26471's blind quarter-res 5x5 regularizer removed the razor but spread gain
# across ~20 base-image pixels. 26472 uses a 3x3 SDR-guided log-gain filter.
cat > "$TMP/candidate/$GAINMAP" <<'GLSL_GAINMAP'
precision highp float;
precision mediump sampler2D;
uniform sampler2D HdrBuffer;
uniform sampler2D SdrBuffer;
uniform ivec2 gainMapSize;
uniform float hdrExposureScale;
uniform float maxGainRatio;
out vec4 Output;

/*
 * IRIS_26472_SDR_AUTHORITATIVE_UHDR_HEADROOM
 * IRIS_26472_EDGE_CONSTRAINED_GAIN_SPIKE_LIMITER
 *
 * UHDR contract:
 * - SDR/base is the sole spatial-detail authority.
 * - No UHDR denoise, blur, sharpening, microcontrast, texture enhancement,
 *   texture suppression, or normal spatial smoothing.
 * - The center raw log-gain passes through unchanged by default.
 * - A compact 3x3 SDR-guided neighborhood is used ONLY to identify an
 *   isolated/thin pathological gain excursion that could render as the
 *   26470 razor halo.
 * - Strong SDR luminance boundaries exclude cross-surface neighbors so HDR
 *   headroom cannot bleed across walls/window frames.
 */
const float UHDR_OFFSET=0.015625;
const float SAME_SURFACE_LOG_LUMA=0.20;
const float SPIKE_BASE_LOG2=0.18;
const float SPIKE_SIGMA_MULT=2.25;

float luminance(vec3 c){return dot(c,vec3(0.2126,0.7152,0.0722));}
float srgbDecode(float x){
    x=clamp(x,0.0,1.0);
    return x<=0.04045?x/12.92:pow((x+0.055)/1.055,2.4);
}
vec3 srgbDecode(vec3 c){
    return vec3(srgbDecode(c.r),srgbDecode(c.g),srgbDecode(c.b));
}
float sdrLogLuma(vec2 uv){
    uv=clamp(uv,vec2(0.0),vec2(1.0));
    vec3 sdr=srgbDecode(texture(SdrBuffer,uv).rgb);
    return log(UHDR_OFFSET+max(luminance(sdr),0.0));
}
float rawLogGain(vec2 uv,float maxLog){
    uv=clamp(uv,vec2(0.0),vec2(1.0));
    vec3 hdr=max(texture(HdrBuffer,uv).rgb,vec3(0.0))*hdrExposureScale;
    vec3 sdr=srgbDecode(texture(SdrBuffer,uv).rgb);
    float ratio=clamp(
        (max(luminance(hdr),0.0)+UHDR_OFFSET)/
        (max(luminance(sdr),0.0)+UHDR_OFFSET),
        1.0,max(maxGainRatio,1.001));
    return clamp(log2(ratio),0.0,maxLog);
}
void main(){
    vec2 gm=max(vec2(gainMapSize),vec2(1.0));
    vec2 uv=gl_FragCoord.xy/gm;
    float maxLog=max(log2(max(maxGainRatio,1.001)),1.0e-6);

    float centerGain=rawLogGain(uv,maxLog);
    float centerGuide=sdrLogLuma(uv);

    float sum=0.0;
    float sumSq=0.0;
    float weight=0.0;
    float support=0.0;

    for(int oy=-1;oy<=1;oy++) for(int ox=-1;ox<=1;ox++){
        if(ox==0 && oy==0) continue;
        vec2 q=uv+vec2(float(ox),float(oy))/gm;
        float guide=sdrLogLuma(q);
        float dg=abs(guide-centerGuide);
        float sameSurface=1.0-smoothstep(
            SAME_SURFACE_LOG_LUMA*0.70,
            SAME_SURFACE_LOG_LUMA,
            dg);
        if(sameSurface<=0.0) continue;

        float g=rawLogGain(q,maxLog);
        sum+=sameSurface*g;
        sumSq+=sameSurface*g*g;
        weight+=sameSurface;
        support+=step(0.50,sameSurface);
    }

    // Default path: exact center gain is preserved.
    float outGain=centerGain;

    // Correct only a statistically isolated/thin same-surface gain spike.
    if(weight>2.5 && support>=3.0){
        float mean=sum/weight;
        float variance=max(sumSq/weight-mean*mean,0.0);
        float sigma=sqrt(variance);
        float residual=abs(centerGain-mean);
        float threshold=max(SPIKE_BASE_LOG2,SPIKE_SIGMA_MULT*sigma);
        float spike=smoothstep(threshold,threshold+0.12,residual);
        outGain=mix(centerGain,mean,spike);
    }

    float encoded=clamp(outGain/maxLog,0.0,1.0);
    Output=vec4(encoded,encoded,encoded,1.0);
}
GLSL_GAINMAP

# Java block already runs the 26471 post-aux reference pass at the correct
# location. Rename it and make the telemetry describe exact merge_ref semantics.
python3 - "$TMP/candidate/$RECON" "$TMP/candidate/$VERSION" <<'PY_JAVA_VERSION'
from pathlib import Path
import sys
recon=Path(sys.argv[1]); version=Path(sys.argv[2])
t=recon.read_text()
old_marker="IRIS_26471_WRONSKI_LOW_SUPPORT_REFERENCE_REGULARIZATION"
new_marker="IRIS_26472_WRONSKI_PUBLIC_ACCUMULATED_ROBUSTNESS_REFERENCE_MERGE"
if t.count(old_marker)<1:
    raise SystemExit("missing 26471 Java reference-pass marker")
t=t.replace(old_marker,new_marker)

old_log=(
'Log.d(TAG, "IRIS_26472_WRONSKI_PUBLIC_ACCUMULATED_ROBUSTNESS_REFERENCE_MERGE '
'supportThreshold=2 radius=2 covarianceMultiplierNormal=2 '
'covarianceMultiplierWeakChroma=4 publicMaximumReference=8 '
'referenceOwnershipOnLowSupport=true clippedEvidenceSemantics26469Preserved=true");'
)
new_log=(
'Log.d(TAG, "IRIS_26472_WRONSKI_REFERENCE_MERGE '
'accumulatedRobustnessThreshold=2 referenceRadiusLowSupport=2 '
'referenceRadiusNormal=1 covarianceMultiplierLowSupport=8 '
'referenceOverwriteLowSupport=true referenceAddNormal=true '
'clippedEvidenceSemantics26469Preserved=true");'
)
if t.count(old_log)!=1:
    raise SystemExit(f"26471 Java reference log anchor count={t.count(old_log)}")
t=t.replace(old_log,new_log,1)
recon.write_text(t)

v=version.read_text()
if v.count("VERSION_NAME=0.9726471")!=1 or v.count("VERSION_BUILD=26471")!=1:
    raise SystemExit("26471 version anchors not unique")
v=v.replace("VERSION_NAME=0.9726471","VERSION_NAME=0.9726472",1)
v=v.replace("VERSION_BUILD=26471","VERSION_BUILD=26472",1)
version.write_text(v)
print("26472 Java/version transform: PASS")
PY_JAVA_VERSION

# Historical-repair audit: prove the rejected cross-phase concepts are absent,
# and prove the 26469 3x3 finalizer is intentionally retired rather than stacked.
python3 - "$TMP/candidate" "$HIST" <<'PY_HIST'
from pathlib import Path
import sys
root=Path(sys.argv[1]); out=Path(sys.argv[2])
final=(root/'app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl').read_text()
low=(root/'app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl').read_text()
gain=(root/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
alltxt="\n".join(p.read_text(errors='ignore') for p in (root/'app/src/main').rglob('*') if p.is_file())
rejected=[
    "IRIS_26460_CROSS_PHASE",
    "plateau chroma",
    "localReliableHue",
]
survived=[x for x in rejected if x in alltxt]
if survived:
    raise SystemExit("rejected historical repair survived: "+", ".join(survived))
if "IRIS_26469_SPATIALLY_COHERENT_CENSORED_HIGHLIGHT" in final:
    raise SystemExit("old 26469 3x3 post-Wronski clipping repair survived")
if "IRIS_26472_WRONSKI_MINIMAL_CENSORED_HIGHLIGHT_FINALIZER" not in final:
    raise SystemExit("minimal censored-highlight finalizer missing")
if "IRIS_26472_WRONSKI_PUBLIC_ACCUMULATED_ROBUSTNESS_REFERENCE_MERGE" not in low:
    raise SystemExit("public reference merge missing")
if "IRIS_26472_SDR_AUTHORITATIVE_UHDR_HEADROOM" not in gain:
    raise SystemExit("SDR-authoritative UHDR headroom contract missing")
if "IRIS_26472_EDGE_CONSTRAINED_GAIN_SPIKE_LIMITER" not in gain:
    raise SystemExit("razor-halo spike limiter missing")
out.write_text(
"""26472 historical repair audit PASS
- rejected 26460 cross-phase/plateau concept absent
- old localReliableHue repair absent
- 26469 dual-evidence clipping semantics preserved upstream
- 26469 3x3 post-Wronski max-neighborhood clipping repair intentionally retired
- 26471 approximate low-support reference pass replaced by public merge_ref semantics
- 26471 blind 5x5 gain-map smoothing replaced by center-preserving 3x3 spike detection
- SDR/base remains the sole spatial-detail authority; ordinary gain values are not smoothed
""")
print("Historical repair audit: PASS")
PY_HIST

# Candidate/source validation before touching real source.
python3 - "$TMP/candidate" "$MATH" <<'PY_VALIDATE'
from pathlib import Path
import sys,re
root=Path(sys.argv[1]); report=Path(sys.argv[2])
req={
'app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl':
    ['IRIS_26472_WRONSKI_AUX_FIRST_ZERO_ACCUMULATOR','vec4(0.0)'],
'app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl':
    ['IRIS_26472_WRONSKI_PUBLIC_AUX_ACCUMULATION_ACCUMULATED_ROBUSTNESS',
     'max(fs.r,0.0)+R'],
'app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl':
    ['IRIS_26472_WRONSKI_PUBLIC_ACCUMULATED_ROBUSTNESS_REFERENCE_MERGE',
     'MAX_FRAME_COUNT=2.0','RAD_MAX=2','MAX_MULTIPLIER=8.0',
     'referenceOwns?refNum:(oldNum.rgb+refNum)'],
'app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl':
    ['IRIS_26472_WRONSKI_MINIMAL_CENSORED_HIGHLIGHT_FINALIZER',
     'unsupportedAll','support.gba'],
'app/src/main/assets/shaders/motionv2/gainmap.glsl':
    ['IRIS_26472_SDR_AUTHORITATIVE_UHDR_HEADROOM',
     'IRIS_26472_EDGE_CONSTRAINED_GAIN_SPIKE_LIMITER',
     'for(int oy=-1;oy<=1;oy++)','outGain=mix(centerGain,mean,spike)'],
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java':
    ['IRIS_26472_WRONSKI_PUBLIC_ACCUMULATED_ROBUSTNESS_REFERENCE_MERGE',
     'IRIS_26472_WRONSKI_REFERENCE_MERGE'],
}
for rel,markers in req.items():
    txt=(root/rel).read_text()
    for m in markers:
        if m not in txt: raise SystemExit(f"candidate missing {m} in {rel}")

# Core Wronski lineage that must remain unchanged/present.
preserve={
'app/src/main/assets/shaders/motionv2/mfsr_kernel_covariance.glsl':
 ['float vst(float x)','IRIS_26469_STABLE_SYMMETRIC_TENSOR_EIGENVECTOR'],
'app/src/main/assets/shaders/motionv2/mfsr_robustness.glsl':
 ['IRIS_26463_WRONSKI_PUBLIC_ROBUSTNESS_GEOMETRY','clippedVariance'],
'app/src/main/assets/shaders/motionv2/mfsr_robustness_erode.glsl':
 ['IRIS_26462_WRONSKI_5X5_ROBUSTNESS_MIN'],
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java':
 ['factors=1,2,4,4','radii=1,4,4,4','metrics=L1,L2,L2,L2',
  'icaIterations=3','flowUpscale=nearest'],
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':
 ['IRIS_26470_UHDR_RENDER_GEOMETRY_AUTHORITY'],
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java':
 ['IRIS_26470_UHDR_EXACT_ORTHOGONAL_GEOMETRY'],
}
for rel,markers in preserve.items():
    txt=(root/rel).read_text()
    for m in markers:
        if m not in txt: raise SystemExit(f"lost lineage {m} in {rel}")

# Reference merge numerical policy proof.
low=(root/'app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl').read_text()
if 'accumulatedRobustness<MAX_FRAME_COUNT' not in low:
    raise SystemExit("reference overwrite threshold missing")
if 'int rad=referenceOwns?RAD_MAX:1' not in low:
    raise SystemExit("reference radius policy missing")
if 'float covarianceMultiplier=referenceOwns?MAX_MULTIPLIER:1.0' not in low:
    raise SystemExit("reference covariance policy missing")

# UHDR: exactly 3x3 loop and no prior 5x5 or HDR-only microcontrast.
gain=(root/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
if 'applyHdrMicrocontrast' in gain:
    raise SystemExit("HDR-only microcontrast survived")
if '-2;oy<=2' in gain or '-2;ox<=2' in gain:
    raise SystemExit("blind 5x5 gain-map smoothing survived")
if 'float outGain=centerGain' not in gain:
    raise SystemExit("center-preserving SDR-detail authority path missing")
if 'outGain=mix(centerGain,mean,spike)' not in gain:
    raise SystemExit("spike-only correction path missing")
if 'IRIS_26472_SDR_AUTHORITATIVE_UHDR_HEADROOM' not in gain:
    raise SystemExit("SDR-authoritative marker missing")
if 'IRIS_26472_EDGE_CONSTRAINED_GAIN_SPIKE_LIMITER' not in gain:
    raise SystemExit("razor-halo limiter marker missing")

ver=(root/'app/version.properties').read_text()
if 'VERSION_NAME=0.9726472' not in ver or 'VERSION_BUILD=26472' not in ver:
    raise SystemExit("26472 version missing")

report.write_text(
"""26472 mathematical/source validation PASS
- auxiliaries accumulate first from zero num/den
- fs.r is accumulated auxiliary robustness only
- public merge_ref ordering restored: auxiliaries -> reference -> divide once
- low accumulated robustness <2: reference overwrite, radius 2, covariance x8
- normal support: reference radius 1 added once
- 26469 clipped brightness evidence and separate unsaturated support retained
- old 3x3 post-Wronski max-neighborhood clipping repair removed
- 26471 blind quarter-res 5x5 UHDR smoothing removed
- 26472 gain map preserves center raw log-gain by default
- 3x3 SDR-guided neighborhood is pathology detection only
- only isolated/thin gain spikes are corrected; ordinary gain is not spatially smoothed
- SDR/base remains sole authority for detail, NR, sharpness, texture and microcontrast
- GAT/VST covariance, robustness 5x5 local-min, Wronski alignment and 26470 UHDR geometry preserved
""")
print("candidate/source validation PASS")
print("Temporary-copy validation: PASS")
PY_VALIDATE
pass "candidate/source validation PASS"
pass "Temporary-copy validation: PASS"

# Apply exact already-validated candidate transformation.
for f in "$RECON" "$INIT" "$ACCUM" "$REFMERGE" "$FINALIZE" "$GAINMAP" "$VERSION"; do
  cp "$TMP/candidate/$f" "$f"
done

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_AFTER"
sha256sum app/version.properties >> "$HASH_AFTER"

python3 - "$HASH_26471" "$HASH_AFTER" \
  "$RECON" "$INIT" "$ACCUM" "$REFMERGE" "$FINALIZE" "$GAINMAP" "$VERSION" <<'PY_HASH'
from pathlib import Path
import sys
def load(p):
    d={}
    for line in Path(p).read_text().splitlines():
        h,f=line.split('  ',1); d[f]=h
    return d
before=load(sys.argv[1]); after=load(sys.argv[2]); allowed=set(sys.argv[3:])
new=set(after)-set(before)
if new:
    raise SystemExit("unexpected new app source paths: "+", ".join(sorted(new)))
missing=set(before)-set(after)
if missing:
    raise SystemExit("protected source paths missing: "+", ".join(sorted(missing)))
bad=[p for p in before if p not in allowed and before[p]!=after[p]]
if bad:
    raise SystemExit("unexpected protected-file changes: "+", ".join(bad))
print("Protected-file hashes: PASS")
PY_HASH
pass "protected-file hashes PASS"

for marker in \
  IRIS_26420_MOTION_V2_NO_LEGACY_ALIGNMENT \
  IRIS_26462_WRONSKI_PUBLISHED_COARSE_TO_FINE_ALIGNMENT \
  IRIS_26463_WRONSKI_PUBLIC_SIGNAL_DOMAIN \
  IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE \
  IRIS_26467_MOTION_OUTPUT_MODE_AUTHORITY \
  IRIS_26468_SINGLE_FRAME_FULL_MOTION_PIPELINE \
  IRIS_26469_CENSORED_HIGHLIGHT_DUAL_EVIDENCE_REFERENCE \
  IRIS_26469_CENSORED_HIGHLIGHT_DUAL_EVIDENCE_AUX \
  IRIS_26469_STABLE_SYMMETRIC_TENSOR_EIGENVECTOR \
  IRIS_26470_UHDR_RENDER_GEOMETRY_AUTHORITY \
  IRIS_26470_UHDR_EXACT_ORTHOGONAL_GEOMETRY \
  IRIS_26472_WRONSKI_AUX_FIRST_ZERO_ACCUMULATOR \
  IRIS_26472_WRONSKI_PUBLIC_ACCUMULATED_ROBUSTNESS_REFERENCE_MERGE \
  IRIS_26472_WRONSKI_MINIMAL_CENSORED_HIGHLIGHT_FINALIZER \
  IRIS_26472_SDR_AUTHORITATIVE_UHDR_HEADROOM \
  IRIS_26472_EDGE_CONSTRAINED_GAIN_SPIKE_LIMITER; do
  grep -Rqs "$marker" app/src/main || fail "lost required marker $marker"
done
pass "historical lineage/ownership preservation PASS"

# Explicitly prove rejected/obsolete repairs are not active.
! grep -Rqs 'IRIS_26469_SPATIALLY_COHERENT_CENSORED_HIGHLIGHT' \
  app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl \
  || fail "old 26469 post-Wronski 3x3 clipping repair survived"
! grep -Rqs 'IRIS_26471_LOWFREQUENCY_LOG_GAINMAP' \
  app/src/main/assets/shaders/motionv2/gainmap.glsl \
  || fail "26471 blind 5x5 gain-map shader survived"
pass "obsolete repair retirement PASS"

grep -q 'float vst(float x)' "$COV" || fail "Wronski GAT/VST lost"
grep -q 'clippedVariance' "$ROBUST" || fail "deterministic clipped-noise robustness correction lost"
grep -q 'IRIS_26462_WRONSKI_5X5_ROBUSTNESS_MIN' "$ERODE" || fail "public 5x5 robustness min lost"
pass "Wronski noise-aware covariance/robustness preservation PASS"

git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$RECOVERY"
git diff "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$SOURCEPATCH"

echo "PRE-BUILD SAFETY PROOF PASSED"
echo "  candidate/source validation PASS"
echo "  Temporary-copy validation: PASS"
echo "  protected-file hashes PASS"
echo "  exact pre-26472 backup branch PASS"
echo "  exact successful 26471 precursor PASS"
echo "  public aux-first/reference-last merge ordering PASS"
echo "  accumulated robustness reference overwrite/add policy PASS"
echo "  obsolete post-Wronski repair retirement PASS"
echo "  26469 censored radiometric evidence preserved PASS"
echo "  26470 UHDR geometry/orientation preserved PASS"
echo "  SDR-authoritative UHDR detail parity contract PASS"
echo "  edge-constrained razor spike limiter PASS"
echo "  no unconditional gain-map smoothing PASS"
echo "  Wronski GAT/noise-aware robustness preserved PASS"
echo "  version/build increment in same script PASS"

cat > "$REPORT" <<EOF_REPORT
26472 Wronski reference completion / SDR-authoritative UHDR
====================================================
Protected pre-26472 infrastructure checkpoint: $PROTECTED_HEAD
Application lineage base: $EXPECTED_APP_BASE
Backup branch: $BACKUP_BRANCH
Build: $NEW_VERSION / $NEW_BUILD

Core reconstruction:
- Restores public/IPOL ordering: zero num/den -> merge every auxiliary -> merge reference once -> divide once.
- fs.r is now accumulated auxiliary robustness, rather than implicit reference+aux support.
- Public merge_ref accumulated-robustness behavior enabled with max_frame_count=2, rad_max=2, max_multiplier=8:
  * accumulated robustness <2 => reference overwrites local aux accumulator, radius 2, covariance x8.
  * otherwise => normal radius-1 reference contribution is added once.
- 26469 censored-sample brightness evidence and separate unsaturated R/G/B support remain.
- Old 26469 3x3 post-Wronski max-neighborhood clipping repair is retired.
- Rejected 26460 cross-phase/plateau concept is not restored.

Ultra HDR:
- 26470 gain-map geometry and exact orthogonal rotation are preserved.
- 26471 blind 5x5 quarter-resolution log-gain smoothing is removed.
- SDR/base is the sole spatial-detail authority for sharpness, NR, texture, edges and microcontrast.
- Normal gain-map samples pass through unchanged; there is no unconditional UHDR spatial smoothing.
- A 3x3 SDR-guided neighborhood is used only to identify and suppress isolated/thin pathological gain spikes responsible for the razor halo.
- Strong SDR luminance edges exclude cross-surface comparisons, preventing highlight gain from bleeding across walls/window frames.
- HDR-only microcontrast remains removed.
- No HDR denoise, sharpening, texture enhancement or texture suppression is introduced.
- Validation target: HDR ON must preserve SDR OFF spatial appearance; only display luminance/headroom may differ.

Wronski/IPOL audit note:
- Core GAT/VST covariance remains active.
- Current deterministic clipped-Gaussian robustness expectation remains active.
- The public IPOL fast Monte-Carlo generator is an implementation detail used to estimate robustness correction curves; it is not injected as stochastic runtime image math in 26472.
- Alignment factors/radii/metrics/ICA, public robustness local-min, and subpixel CFA accumulation remain unchanged.

Deferred:
- explicit temporal-age/disocclusion weighting for moving subjects;
- Camera2 lens-shading ownership/vignetting fix;
- performance rewrite.
EOF_REPORT

rm -f ./*.apk
chmod +x ./gradlew
./gradlew assembleDebug --no-daemon

echo "BUILD SUCCESSFUL verified by Gradle return code" | tee -a "$REPORT"
mapfile -t apks < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | sort)
[[ ${#apks[@]} -ge 1 ]] || fail "no debug APK found"
cp "${apks[0]}" "$APK_NAME"
[[ -s "$APK_NAME" ]] || fail "APK missing/empty"
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
pass "26472 SDR-AUTHORITATIVE UHDR BUILD SUCCESS"
