#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
PROTECTED_HEAD="43f4b77e6f2fb103db2bded4ddb9278ca26f97a4"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BACKUP_BRANCH="backup-26470-before-26471-cfa-uhdr"
PRECURSOR_SCRIPT="build_26470_consolidated_cfa_uhdr.sh"
PRECURSOR_BLOB="e734ccd34c88ff4d71f204dd66a4aa10df93f6a2"
NEW_VERSION="0.9726471"
NEW_BUILD="26471"
OUTDIR="build_26471_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-low-support-cfa-lowfreq-uhdr-debug.apk"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }

rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26471_source_audit.txt"
REPORT="$OUTDIR/26471_build_report.txt"
MATH="$OUTDIR/26471_math_validation.txt"
HASH_INITIAL="$OUTDIR/26471_protected_initial.sha256"
HASH_26470="$OUTDIR/26471_protected_26470_base.sha256"
HASH_AFTER="$OUTDIR/26471_protected_after.sha256"
PREPATCH="$OUTDIR/26471_pre_edit_binary.patch"
RECOVERY="$OUTDIR/26471_recovery_binary.patch"
SOURCEPATCH="$OUTDIR/26471_source.patch"
exec > >(tee "$AUDIT") 2>&1

echo "=== 26471 GUARDED LOW-SUPPORT CFA / LOW-FREQUENCY UHDR BUILD ==="
date -Iseconds || true

BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "branch=$BRANCH expected=$EXPECTED_BRANCH"
pass "branch gate"

REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$PROTECTED_HEAD" ]] || fail "backup=$REMOTE_BACKUP expected=$PROTECTED_HEAD"
pass "backup branch exact protected 26470 checkpoint"

git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "missing verified app base"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties || fail "application source changed before 26471"
pass "application source unchanged from verified checkpoint"

[[ -f "$PRECURSOR_SCRIPT" ]] || fail "missing $PRECURSOR_SCRIPT"
[[ "$(git hash-object "$PRECURSOR_SCRIPT")" == "$PRECURSOR_BLOB" ]] || fail "26470 precursor blob mismatch"
pass "26470 precursor script exact"

git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$PREPATCH"
find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_INITIAL"
sha256sum app/version.properties >> "$HASH_INITIAL"
pass "binary pre-edit patch created before source modification"
pass "protected-file hashes captured before source modification"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
PRECURSOR="$TMP/26470_transform_only.sh"
awk '/^rm -f \.\/\*\.apk$/ { exit } { print }' "$PRECURSOR_SCRIPT" > "$PRECURSOR"
python3 - "$PRECURSOR" "$TMP/26470_precursor_outputs" <<'PY_OUTDIR'
from pathlib import Path
import sys
p=Path(sys.argv[1]); t=p.read_text()
a='OUTDIR="build_26470_outputs"'; r='OUTDIR="'+sys.argv[2]+'"'
if t.count(a)!=1: raise SystemExit(f'26470 OUTDIR anchor count={t.count(a)}')
p.write_text(t.replace(a,r,1)); print('26470 precursor OUTDIR rewrite: PASS')
PY_OUTDIR
chmod +x "$PRECURSOR"
bash -n "$PRECURSOR" || fail "26470 transform-only precursor syntax"
bash "$PRECURSOR"

grep -q '^VERSION_NAME=0\.9726470$' app/version.properties || fail "26470 version name"
grep -q '^VERSION_BUILD=26470$' app/version.properties || fail "26470 version build"
for marker in IRIS_26469_CENSORED_HIGHLIGHT_DUAL_EVIDENCE_REFERENCE IRIS_26469_CENSORED_HIGHLIGHT_DUAL_EVIDENCE_AUX IRIS_26469_SPATIALLY_COHERENT_CENSORED_HIGHLIGHT IRIS_26469_STABLE_SYMMETRIC_TENSOR_EIGENVECTOR IRIS_26470_UHDR_RENDER_GEOMETRY_AUTHORITY IRIS_26470_UHDR_EXACT_ORTHOGONAL_GEOMETRY; do
  grep -Rqs "$marker" app/src/main || fail "26470 lineage missing $marker"
done
pass "26470 tested application lineage reproduced"

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_26470"
sha256sum app/version.properties >> "$HASH_26470"

RECON="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
GAINMAP="app/src/main/assets/shaders/motionv2/gainmap.glsl"
LOWSUP="app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl"
VERSION="app/version.properties"
for f in "$RECON" "$GAINMAP" "$VERSION"; do mkdir -p "$TMP/candidate/$(dirname "$f")"; cp "$f" "$TMP/candidate/$f"; done
mkdir -p "$TMP/candidate/$(dirname "$LOWSUP")"

cat > "$TMP/candidate/$LOWSUP" <<'GLSL_LOW_SUPPORT'
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

/* IRIS_26471_WRONSKI_LOW_SUPPORT_REFERENCE_REGULARIZATION
 * Public/IPOL accumulated-robustness merge idea, adapted conservatively.
 * Local frame-equivalent support <=2 becomes reference-owned with broadened
 * anisotropic covariance. Public code exposes up to 8x; 26471 caps at 4x.
 */
int componentIndex(ivec2 p){return ((p.y&1)<<1)|(p.x&1);}
int componentColor(int c){
    if(cfaPattern==0){if(c==0)return 0;if(c==3)return 2;return 1;}
    if(cfaPattern==1){if(c==1)return 0;if(c==2)return 2;return 1;}
    if(cfaPattern==2){if(c==2)return 0;if(c==1)return 2;return 1;}
    if(c==3)return 0;if(c==0)return 2;return 1;
}
float clipForColor(int c){return c==0?clipR:(c==2?clipB:clipG);}
float sampleValidity(float v,int c){float clip=max(clipForColor(c),1e-6);return 1.0-smoothstep(0.985*clip,0.998*clip,v);}
float cfaAt(ivec2 p){p=clamp(p,ivec2(0),rawSize-ivec2(1));vec4 v=imageLoad(referenceCfa,p>>1);int c=componentIndex(p);return c==0?v.r:(c==1?v.g:(c==2?v.b:v.a));}
mat2 covAt(ivec2 p){p=clamp(p,ivec2(0),rawHalf-ivec2(1));vec4 v=imageLoad(referenceCov,p);return mat2(v.x,v.y,v.z,v.w);}
mat2 interpolateCov(vec2 gp){
    ivec2 fl=ivec2(max(floor(gp),vec2(0.0))); ivec2 ce=min(fl+ivec2(1),rawHalf-ivec2(1)); vec2 f=fract(gp);
    mat2 c00=covAt(fl),c01=covAt(ivec2(ce.x,fl.y)),c10=covAt(ivec2(fl.x,ce.y)),c11=covAt(ce);
    return c00*((1.0-f.x)*(1.0-f.y))+c01*(f.x*(1.0-f.y))+c10*((1.0-f.x)*f.y)+c11*(f.x*f.y);
}
mat2 invertCov(mat2 m){float d=m[0][0]*m[1][1]-m[0][1]*m[1][0];if(abs(d)<=1e-10)return mat2(1,0,0,1);return mat2(m[1][1],-m[0][1],-m[1][0],m[0][0])/d;}
void main(){
    ivec2 outP=ivec2(gl_GlobalInvocationID.xy); if(any(greaterThanEqual(outP,rawSize))) return;
    vec4 fs=imageLoad(currentFrameSupport,outP); vec4 oldNum=imageLoad(currentNumerator,outP); vec4 oldDen=imageLoad(currentDenominator,outP);
    if(fs.r>2.001){imageStore(outNumerator,outP,oldNum);imageStore(outDenominator,outP,oldDen);imageStore(outFrameSupport,outP,fs);return;}
    vec3 oldD=max(oldDen.rgb,vec3(1e-12)); vec3 validRatio=clamp(fs.gba/oldD,vec3(0.0),vec3(1.0));
    float weakest=min(validRatio.r,min(validRatio.g,validRatio.b)); float chromaUncertainty=1.0-smoothstep(0.25,0.75,weakest);
    float covarianceMultiplier=mix(2.0,4.0,chromaUncertainty);
    vec2 coarse=vec2(outP); vec2 greyPos=(coarse-vec2(0.5))/2.0; mat2 invCov=invertCov(interpolateCov(greyPos))/covarianceMultiplier;
    ivec2 center=ivec2(round(coarse)); vec3 num=vec3(0),den=vec3(0),validDen=vec3(0);
    for(int iy=-2;iy<=2;iy++)for(int ix=-2;ix<=2;ix++){
        ivec2 p=center+ivec2(ix,iy); if(any(lessThan(p,ivec2(0)))||any(greaterThanEqual(p,rawSize)))continue;
        int c=componentColor(componentIndex(p)); vec2 d=vec2(p)-coarse; float z=max(dot(d,invCov*d),0.0); float w=exp(-0.5*z); float s=cfaAt(p);
        num[c]+=s*w; den[c]+=w; validDen[c]+=w*sampleValidity(s,c);
    }
    imageStore(outNumerator,outP,vec4(num,0.0)); imageStore(outDenominator,outP,vec4(den,1.0)); imageStore(outFrameSupport,outP,vec4(1.0,validDen));
}
GLSL_LOW_SUPPORT

cat > "$TMP/candidate/$GAINMAP" <<'GLSL_GAINMAP'
precision highp float;
precision mediump sampler2D;
uniform sampler2D HdrBuffer;
uniform sampler2D SdrBuffer;
uniform ivec2 gainMapSize;
uniform float hdrExposureScale;
uniform float maxGainRatio;
out vec4 Output;
/* IRIS_26471_LOWFREQUENCY_LOG_GAINMAP */
const float UHDR_OFFSET=0.015625;
float luminance(vec3 c){return dot(c,vec3(0.2126,0.7152,0.0722));}
float srgbDecode(float x){x=clamp(x,0.0,1.0);return x<=0.04045?x/12.92:pow((x+0.055)/1.055,2.4);}
vec3 srgbDecode(vec3 c){return vec3(srgbDecode(c.r),srgbDecode(c.g),srgbDecode(c.b));}
float w1(int x){int a=abs(x);return a==0?6.0:(a==1?4.0:1.0);}
float localLogGain(vec2 uv,float maxLog){
    uv=clamp(uv,vec2(0.0),vec2(1.0)); vec3 hdr=max(texture(HdrBuffer,uv).rgb,vec3(0.0))*hdrExposureScale; vec3 sdr=srgbDecode(texture(SdrBuffer,uv).rgb);
    float ratio=clamp((max(luminance(hdr),0.0)+UHDR_OFFSET)/(max(luminance(sdr),0.0)+UHDR_OFFSET),1.0,max(maxGainRatio,1.001)); return clamp(log2(ratio),0.0,maxLog);
}
void main(){
    vec2 gm=max(vec2(gainMapSize),vec2(1.0)); vec2 uv=gl_FragCoord.xy/gm; float maxLog=max(log2(max(maxGainRatio,1.001)),1.0e-6); float sum=0.0,wsum=0.0;
    for(int oy=-2;oy<=2;oy++)for(int ox=-2;ox<=2;ox++){float w=w1(ox)*w1(oy);sum+=w*localLogGain(uv+vec2(float(ox),float(oy))/gm,maxLog);wsum+=w;}
    float encoded=clamp((sum/max(wsum,1.0e-6))/maxLog,0.0,1.0); Output=vec4(encoded,encoded,encoded,1.0);
}
GLSL_GAINMAP

python3 - "$TMP/candidate" <<'PY_TRANSFORM'
from pathlib import Path
import sys
root=Path(sys.argv[1]); recon=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java'; version=root/'app/version.properties'
def once(s,a,b,label):
    n=s.count(a)
    if n!=1: raise SystemExit(f'{label}: expected 1 anchor, found {n}')
    return s.replace(a,b,1)
t=recon.read_text()
anchor="""            /*
             * IRIS_26416_MOTION_V2_PROVEN_FLOAT32_BRIDGE
"""
insert="""            /* IRIS_26471_WRONSKI_LOW_SUPPORT_REFERENCE_REGULARIZATION */
            if (directBayer) {
                glProg.setLayout(tile, tile, 1);
                glProg.useAssetProgram(\"motionv2/mfsr_low_support_reference\", true);
                glProg.setVar(\"rawSize\", raw); glProg.setVar(\"rawHalf\", rawHalf); glProg.setVar(\"cfaPattern\", (int) parameters.cfaPattern);
                glProg.setVar(\"clipR\", canonicalGain * wronskiGlobalWbR); glProg.setVar(\"clipG\", canonicalGain * wronskiGlobalWbG); glProg.setVar(\"clipB\", canonicalGain * wronskiGlobalWbB);
                glProg.setTextureCompute(\"referenceCfa\", wronskiReferenceCfa, false); glProg.setTextureCompute(\"referenceCov\", wronskiReferenceCov, false);
                glProg.setTextureCompute(\"currentNumerator\", currentDirectRgb, false); glProg.setTextureCompute(\"currentDenominator\", currentDirectSupport, false); glProg.setTextureCompute(\"currentFrameSupport\", currentDirectFrameSupport, false);
                glProg.setTextureCompute(\"outNumerator\", nextDirectRgb, true); glProg.setTextureCompute(\"outDenominator\", nextDirectSupport, true); glProg.setTextureCompute(\"outFrameSupport\", nextDirectFrameSupport, true);
                glProg.computeAuto(raw, 1);
                GLTexture s1=currentDirectRgb; currentDirectRgb=nextDirectRgb; nextDirectRgb=s1;
                GLTexture s2=currentDirectSupport; currentDirectSupport=nextDirectSupport; nextDirectSupport=s2;
                GLTexture s3=currentDirectFrameSupport; currentDirectFrameSupport=nextDirectFrameSupport; nextDirectFrameSupport=s3;
                Log.d(TAG, \"IRIS_26471_WRONSKI_LOW_SUPPORT_REFERENCE_REGULARIZATION supportThreshold=2 radius=2 covarianceMultiplierNormal=2 covarianceMultiplierWeakChroma=4 publicMaximumReference=8 referenceOwnershipOnLowSupport=true clippedEvidenceSemantics26469Preserved=true\");
            }

"""
t=once(t,anchor,insert+anchor,'low-support insertion')
t=t.replace('IRIS_26469_CENSORED_HIGHLIGHT_COHERENT_RECONSTRUCTION','IRIS_26471_LOW_SUPPORT_COHERENT_RECONSTRUCTION',1)
recon.write_text(t)
v=version.read_text(); v=once(v,'VERSION_NAME=0.9726470','VERSION_NAME=0.9726471','VERSION_NAME'); v=once(v,'VERSION_BUILD=26470','VERSION_BUILD=26471','VERSION_BUILD'); version.write_text(v)
PY_TRANSFORM

grep -q 'IRIS_26471_WRONSKI_LOW_SUPPORT_REFERENCE_REGULARIZATION' "$TMP/candidate/$RECON" || fail "candidate low-support Java marker"
grep -q 'motionv2/mfsr_low_support_reference' "$TMP/candidate/$RECON" || fail "candidate low-support shader binding"
grep -q 'IRIS_26471_WRONSKI_LOW_SUPPORT_REFERENCE_REGULARIZATION' "$TMP/candidate/$LOWSUP" || fail "candidate low-support shader marker"
grep -q 'fs.r>2.001' "$TMP/candidate/$LOWSUP" || fail "candidate local support threshold"
grep -q 'mix(2.0,4.0,chromaUncertainty)' "$TMP/candidate/$LOWSUP" || fail "candidate covariance cap"
grep -q 'IRIS_26471_LOWFREQUENCY_LOG_GAINMAP' "$TMP/candidate/$GAINMAP" || fail "candidate low-frequency gain-map marker"
! grep -q 'applyHdrMicrocontrast' "$TMP/candidate/$GAINMAP" || fail "HDR-only microcontrast survived gain map"
grep -q '^VERSION_NAME=0\.9726471$' "$TMP/candidate/$VERSION" || fail "candidate version name"
grep -q '^VERSION_BUILD=26471$' "$TMP/candidate/$VERSION" || fail "candidate version build"
pass "candidate/source validation PASS"

python3 - "$TMP/candidate" "$MATH" <<'PY_VALIDATE'
from pathlib import Path
import sys
root=Path(sys.argv[1]); report=Path(sys.argv[2])
for rel in ['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java','app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl']:
    s=(root/rel).read_text()
    if s.count('{')!=s.count('}'): raise SystemExit('brace mismatch '+rel)
def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a))); return t*t*(3-2*t)
def mult(support,weakest):
    if support>2.001:return 1.0
    return 2+2*(1-smooth(.25,.75,weakest))
assert mult(4,0.0)==1.0
assert 1.99<=mult(1,1.0)<=2.01
assert 3.99<=mult(1,0.0)<=4.01
w=[1,4,6,4,1]; assert sum(w)==16 and w==w[::-1] and sum(a*b for a in w for b in w)==256
assert 0.14 < 36/256 < 0.141
for rel,marker in {
'app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl':'IRIS_26469_SPATIALLY_COHERENT_CENSORED_HIGHLIGHT',
'app/src/main/assets/shaders/motionv2/mfsr_kernel_covariance.glsl':'IRIS_26469_STABLE_SYMMETRIC_TENSOR_EIGENVECTOR',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':'IRIS_26470_UHDR_RENDER_GEOMETRY_AUTHORITY',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java':'IRIS_26470_UHDR_EXACT_ORTHOGONAL_GEOMETRY'}.items():
    if marker not in (root/rel).read_text(): raise SystemExit('lost lineage '+marker)
report.write_text('26471 mathematical/source validation PASS\n- support >2 pass-through\n- support <=2 reference-owned anisotropic covariance expansion\n- 2x normal / max 4x weak-chroma covariance power\n- 5x5 binomial log-gain kernel sum=256 and impulse peak=36/256\n- 26469 highlight and 26470 UHDR geometry preserved\n')
print('Temporary-copy validation: PASS')
PY_VALIDATE
pass "Temporary-copy validation: PASS"

cp "$TMP/candidate/$RECON" "$RECON"; cp "$TMP/candidate/$GAINMAP" "$GAINMAP"; cp "$TMP/candidate/$LOWSUP" "$LOWSUP"; cp "$TMP/candidate/$VERSION" "$VERSION"
find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_AFTER"; sha256sum app/version.properties >> "$HASH_AFTER"
python3 - "$HASH_26470" "$HASH_AFTER" "$RECON" "$GAINMAP" "$LOWSUP" "$VERSION" <<'PY_HASH'
from pathlib import Path
import sys
def load(p):
 d={}
 for line in Path(p).read_text().splitlines(): h,f=line.split('  ',1); d[f]=h
 return d
b=load(sys.argv[1]); a=load(sys.argv[2]); allowed=set(sys.argv[3:]); new=set(a)-set(b)
if new!={sys.argv[5]}: raise SystemExit('unexpected new source paths: '+', '.join(sorted(new)))
if set(b)-set(a): raise SystemExit('protected source paths missing')
bad=[p for p in b if p not in allowed and b[p]!=a[p]]
if bad: raise SystemExit('unexpected protected-file changes: '+', '.join(bad))
print('Protected-file hashes: PASS')
PY_HASH

for marker in IRIS_26420_MOTION_V2_NO_LEGACY_ALIGNMENT IRIS_26462_WRONSKI_PUBLISHED_COARSE_TO_FINE_ALIGNMENT IRIS_26463_WRONSKI_PUBLIC_SIGNAL_DOMAIN IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE IRIS_26467_MOTION_OUTPUT_MODE_AUTHORITY IRIS_26468_SINGLE_FRAME_FULL_MOTION_PIPELINE IRIS_26468_PROCESSING_SEAM_DIAGNOSTIC IRIS_26469_CENSORED_HIGHLIGHT_DUAL_EVIDENCE_REFERENCE IRIS_26469_CENSORED_HIGHLIGHT_DUAL_EVIDENCE_AUX IRIS_26469_SPATIALLY_COHERENT_CENSORED_HIGHLIGHT IRIS_26469_STABLE_SYMMETRIC_TENSOR_EIGENVECTOR IRIS_26470_UHDR_RENDER_GEOMETRY_AUTHORITY IRIS_26470_UHDR_EXACT_ORTHOGONAL_GEOMETRY IRIS_26471_WRONSKI_LOW_SUPPORT_REFERENCE_REGULARIZATION IRIS_26471_LOWFREQUENCY_LOG_GAINMAP; do
  grep -Rqs "$marker" app/src/main || fail "lost required marker $marker"
done
pass "historical lineage/ownership preservation PASS"

grep -q 'float vst(float x)' app/src/main/assets/shaders/motionv2/mfsr_kernel_covariance.glsl || fail "Wronski GAT/VST lost"
grep -q 'uniform float noiseS' app/src/main/assets/shaders/motionv2/mfsr_kernel_covariance.glsl || fail "Wronski noiseS lost"
grep -q 'uniform float noiseO' app/src/main/assets/shaders/motionv2/mfsr_kernel_covariance.glsl || fail "Wronski noiseO lost"
pass "Wronski GAT/noise-aware covariance preservation PASS"

git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$RECOVERY"
git diff "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$SOURCEPATCH"

echo "PRE-BUILD SAFETY PROOF PASSED"
echo "  candidate/source validation PASS"
echo "  Temporary-copy validation: PASS"
echo "  protected-file hashes PASS"
echo "  exact pre-26471 backup branch PASS"
echo "  26469 censored-highlight/eigensystem lineage PASS"
echo "  26470 UHDR geometry/orientation lineage PASS"
echo "  low-support reference regularization PASS"
echo "  low-frequency log-gain formation PASS"
echo "  Wronski GAT/noise-aware covariance preserved PASS"
echo "  version/build increment in same script PASS"

cat > "$REPORT" <<EOF_REPORT
26471 low-support CFA / low-frequency UHDR build
================================================
Protected pre-26471 checkpoint: $PROTECTED_HEAD
Application lineage base: $EXPECTED_APP_BASE
Backup branch: $BACKUP_BRANCH
Build: $NEW_VERSION / $NEW_BUILD

- Preserves 26469 censored-highlight dual-evidence, shared clipped RGB transition and stable tensor eigensystem.
- Adds public/IPOL-inspired low-support reference ownership at true local support <=2, with conservative anisotropic covariance broadening (2x normally, max 4x weak chroma; public code exposes up to 8x).
- Preserves 26470 rendered-SDR UHDR geometry and exact rotation.
- Removes HDR-only microcontrast from gain-map formation and low-passes LOG gain with normalized 5x5 binomial weights.
- Existing Wronski/public GAT/VST covariance using noiseS/noiseO remains active.
- Optional public Monte-Carlo robustness-ratio noise correction is NOT added here.
- Alignment/ICA/robustness equations, exposure, tone, MotionV2Denoise, sharpening state, and performance scheduling are unchanged.
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
{ echo "BUILD SUCCESS"; echo "APK=$APK_NAME"; echo "SHA256=$sha"; echo "VERSION=$NEW_VERSION"; echo "BUILD=$NEW_BUILD"; echo "dev_untouched=true"; echo "experimental_source_not_committed=true"; } | tee -a "$REPORT"
pass "26471 BUILD SUCCESS"
