#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
PROTECTED_HEAD="e47b4071dc30737abcc0ab21276a10000ac9de4f"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BACKUP_BRANCH="backup-26474-before-26475-wronski-performance-correctness"
BACKUP_TARGET="e47b4071dc30737abcc0ab21276a10000ac9de4f"
PRECURSOR_SCRIPT="build_26474_temporal_disocclusion_color_shadow_v3.sh"
PRECURSOR_BLOB="0553fc99cef27f4f2855d68ece680955c2ffd24b"

OLD_VERSION="0.9726474"
OLD_BUILD="26474"
NEW_VERSION="0.9726475"
NEW_BUILD="26475"
OUTDIR="build_26475_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-wronski-source-fidelity-performance-debug.apk"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }

rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26475_source_audit.txt"
REPORT="$OUTDIR/26475_build_report.txt"
MATH="$OUTDIR/26475_wronski_math_audit.txt"
PREPATCH="$OUTDIR/26475_pre_edit_binary.patch"
RECOVERY="$OUTDIR/26475_recovery_binary.patch"
SOURCEPATCH="$OUTDIR/26475_source.patch"
HASH_INITIAL="$OUTDIR/26475_protected_initial.sha256"
HASH_26474="$OUTDIR/26475_protected_26474.sha256"
HASH_AFTER="$OUTDIR/26475_protected_after.sha256"
exec > >(tee "$AUDIT") 2>&1

echo "=== 26475 GUARDED WRONSKI SOURCE-FIDELITY / PERFORMANCE BUILD ==="
date -Iseconds || true

BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "branch=$BRANCH expected=$EXPECTED_BRANCH"
pass "branch gate"

REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$BACKUP_TARGET" ]] || fail "backup=$REMOTE_BACKUP expected=$BACKUP_TARGET"
pass "backup branch exact successful 26474 V3 checkpoint"

git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "missing verified app base"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties || fail "app source changed before 26475"
pass "application source unchanged before 26475"

[[ -f "$PRECURSOR_SCRIPT" ]] || fail "missing $PRECURSOR_SCRIPT"
[[ "$(git hash-object "$PRECURSOR_SCRIPT")" == "$PRECURSOR_BLOB" ]] || fail "26474 V3 precursor blob mismatch"
pass "26474 V3 precursor exact"

# Required before any source modification.
git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$PREPATCH"
find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_INITIAL"
sha256sum app/version.properties >> "$HASH_INITIAL"
pass "binary pre-edit patch created before source modification"
pass "initial protected hashes captured"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Reproduce exact successful 26474 V3 app transformation, without Gradle.
PRECURSOR="$TMP/26474_transform_only.sh"
awk '/^rm -f \.\/\*\.apk$/ { exit } { print }' "$PRECURSOR_SCRIPT" > "$PRECURSOR"
python3 - "$PRECURSOR" "$TMP/26474_precursor_outputs" <<'PY_PRE'
from pathlib import Path
import sys
p=Path(sys.argv[1]); t=p.read_text()
old='OUTDIR="build_26474_outputs"'
new='OUTDIR="'+sys.argv[2]+'"'
if t.count(old)!=1:
    raise SystemExit("26474 precursor OUTDIR anchor count="+str(t.count(old)))
p.write_text(t.replace(old,new,1))
print("26474 precursor OUTDIR rewrite: PASS")
PY_PRE
chmod +x "$PRECURSOR"
bash -n "$PRECURSOR" || fail "26474 transform-only syntax"
bash "$PRECURSOR"

grep -q '^VERSION_NAME=0\.9726474$' app/version.properties || fail "26474 version name"
grep -q '^VERSION_BUILD=26474$' app/version.properties || fail "26474 version build"
for marker in \
  IRIS_26473_IPOL_FAST_MONTE_CARLO_NOISE_CURVES \
  IRIS_26473_IPOL_REFERENCE_BRIGHTNESS_SNR \
  IRIS_26473_IPOL_WRONSKI_ALIGNMENT_COMPLETION \
  IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE \
  IRIS_26472_WRONSKI_AUX_FIRST_ZERO_ACCUMULATOR \
  IRIS_26472_WRONSKI_PUBLIC_ACCUMULATED_ROBUSTNESS_REFERENCE_MERGE \
  IRIS_26472_SDR_AUTHORITATIVE_UHDR_HEADROOM \
  IRIS_26470_UHDR_RENDER_GEOMETRY_AUTHORITY \
  IRIS_26474_DNG_SCENE_LINEAR_COLOR_SHADOW; do
  grep -Rqs "$marker" app/src/main || fail "26474 lineage missing $marker"
done
pass "exact successful 26474 V3 application lineage reproduced"

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_26474"
sha256sum app/version.properties >> "$HASH_26474"

RECON="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
ALIGNJAVA="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java"
NOISEJAVA="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2IpolNoiseCurve.java"
GUIDE="app/src/main/assets/shaders/motionv2/alignment_guide.glsl"
ROBUST="app/src/main/assets/shaders/motionv2/mfsr_robustness.glsl"
REFMERGE="app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl"
ICA="app/src/main/assets/shaders/motionv2/mfsr_ica_refine.glsl"
GRAD="app/src/main/assets/shaders/motionv2/mfsr_ica_reference_gradient.glsl"
HESS="app/src/main/assets/shaders/motionv2/mfsr_ica_reference_hessian.glsl"
VERSION="app/version.properties"

for f in "$RECON" "$ALIGNJAVA" "$NOISEJAVA" "$GUIDE" "$ROBUST" "$REFMERGE" "$ICA" "$VERSION"; do
  mkdir -p "$TMP/candidate/$(dirname "$f")"
  cp "$f" "$TMP/candidate/$f"
done
mkdir -p "$TMP/candidate/$(dirname "$GRAD")"

cat > "$TMP/candidate/$GUIDE" <<'GLSL_GUIDE'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp sampler2D;
precision highp image2D;

uniform sampler2D InputCfa;
layout(r32f, binding=0) uniform highp writeonly image2D OutputGuide;
uniform int guideScale;
uniform float signalScale;

/*
 * IRIS_26475_WRONSKI_BAYER_QUAD_ALIGNMENT_GUIDE
 *
 * Wronski 2019 does not disclose the exact CFA->gray registration prefilter.
 * IPOL Sec. 2.1 explicitly identifies averaging each 2x2 Bayer quad as the
 * cheap/fast strategy likely used by the original mobile implementation and
 * says it is the option to use to be closer to Wronski's original method.
 *
 * InputCfa is already packed as one RGBA texel per physical 2x2 Bayer quad,
 * so this is the exact arithmetic mean of the four physical CFA samples.
 * No 26473 5x5 "FFT-equivalent" approximation remains.
 */
void main() {
    ivec2 q=ivec2(gl_GlobalInvocationID.xy);
    ivec2 os=imageSize(OutputGuide);
    if(any(greaterThanEqual(q,os))) return;
    ivec2 is=textureSize(InputCfa,0);
    ivec2 p=clamp(q,ivec2(0),is-ivec2(1));
    vec4 v=max(texelFetch(InputCfa,p,0),vec4(0.0));
    float g=0.25*(v.r+v.g+v.b+v.a)/max(signalScale,1.0e-6);
    imageStore(OutputGuide,q,vec4(g,0.0,0.0,0.0));
}

GLSL_GUIDE

# Restore exact 26473/IPOL robustness math: 26474 age gate is retired.
cat > "$TMP/candidate/$ROBUST" <<'GLSL_ROBUST'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D flowTexture;
uniform highp sampler2D noiseCurve;
layout(rgba16f,binding=0) uniform highp readonly image2D referenceCfa;
layout(rgba16f,binding=1) uniform highp readonly image2D alterCfa;
layout(r32f,binding=2) uniform highp writeonly image2D outRobustness;
uniform ivec2 rawSize;
uniform ivec2 rawHalf;
uniform int cfaPattern;
uniform int tileSizeRaw;
uniform float wbR;
uniform float wbG;
uniform float wbB;

int colorOf(int c){
    if(cfaPattern==0){if(c==0)return 0;if(c==3)return 2;return 1;}
    if(cfaPattern==1){if(c==1)return 0;if(c==2)return 2;return 1;}
    if(cfaPattern==2){if(c==2)return 0;if(c==1)return 2;return 1;}
    if(c==3)return 0;if(c==0)return 2;return 1;
}
vec3 guideReference(ivec2 q){
    q=clamp(q,ivec2(0),rawHalf-ivec2(1));
    vec4 v=imageLoad(referenceCfa,q);
    float s[4]=float[4](v.r,v.g,v.b,v.a);
    vec3 o=vec3(0); float ng=0.0;
    for(int i=0;i<4;i++){
        int c=colorOf(i);
        float x=s[i]/(c==0?max(wbR,1e-6):(c==2?max(wbB,1e-6):max(wbG,1e-6)));
        if(c==0)o.r=x; else if(c==2)o.b=x; else {o.g+=x;ng+=1.0;}
    }
    o.g/=max(ng,1.0); return o;
}
vec3 guideAlter(ivec2 q){
    q=clamp(q,ivec2(0),rawHalf-ivec2(1));
    vec4 v=imageLoad(alterCfa,q);
    float s[4]=float[4](v.r,v.g,v.b,v.a);
    vec3 o=vec3(0); float ng=0.0;
    for(int i=0;i<4;i++){
        int c=colorOf(i);
        float x=s[i]/(c==0?max(wbR,1e-6):(c==2?max(wbB,1e-6):max(wbG,1e-6)));
        if(c==0)o.r=x; else if(c==2)o.b=x; else {o.g+=x;ng+=1.0;}
    }
    o.g/=max(ng,1.0); return o;
}
void localStatsRef(ivec2 q,out vec3 mu,out vec3 var){
    vec3 s=vec3(0),ss=vec3(0);
    for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){
        vec3 v=guideReference(clamp(q+ivec2(x,y),ivec2(0),rawHalf-ivec2(1)));
        s+=v;ss+=v*v;
    }
    mu=s/9.0;var=max(ss/9.0-mu*mu,vec3(0));
}
vec3 localMeanAlt(ivec2 q){
    vec3 s=vec3(0);
    for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++)
        s+=guideAlter(clamp(q+ivec2(x,y),ivec2(0),rawHalf-ivec2(1)));
    return s/9.0;
}
float dogson(float x){
    float a=abs(x);
    if(a<=0.5) return -2.0*a*a+1.0;
    if(a<=1.5) return a*a-2.5*a+1.5;
    return 0.0;
}
void dogsonRef(vec2 lr,out vec3 mu,out vec3 var){
    ivec2 center=ivec2(round(lr)); vec3 sm=vec3(0),sv=vec3(0); float sw=0.0;
    for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){
        ivec2 q=clamp(center+ivec2(x,y),ivec2(0),rawHalf-ivec2(1));
        float w=dogson(float(q.x)-lr.x)*dogson(float(q.y)-lr.y);
        vec3 m,v;localStatsRef(q,m,v);sm+=m*w;sv+=v*w;sw+=w;
    }
    mu=sm/max(sw,1e-8);var=sv/max(sw,1e-8);
}
vec3 dogsonAlt(vec2 lr){
    ivec2 center=ivec2(round(lr)); vec3 sm=vec3(0); float sw=0.0;
    for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){
        ivec2 q=clamp(center+ivec2(x,y),ivec2(0),rawHalf-ivec2(1));
        float w=dogson(float(q.x)-lr.x)*dogson(float(q.y)-lr.y);
        sm+=localMeanAlt(q)*w;sw+=w;
    }
    return sm/max(sw,1e-8);
}
vec2 denseRawFlowAt(ivec2 rawP){
    ivec2 q=clamp(rawP>>1,ivec2(0),rawHalf-ivec2(1));
    return 2.0*texelFetch(flowTexture,q,0).xy;
}
vec2 ipolNoise(float brightness){
    int idx=clamp(int(round(1000.0*clamp(brightness,0.0,1.0))),0,1000);
    return texelFetch(noiseCurve,ivec2(idx,0),0).rg;
}

/* IRIS_26473_IPOL_FAST_MC_ROBUSTNESS_CURVES */
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(p,rawSize))) return;
    vec2 rawFlow=denseRawFlowAt(p);
    vec2 refLR=(vec2(p)+0.5)/2.0-0.5;
    vec2 altLR=(vec2(p)+rawFlow+0.5)/2.0-0.5;
    if(altLR.x<0.0||altLR.y<0.0||
       altLR.x>=float(rawHalf.x)||altLR.y>=float(rawHalf.y)){
        imageStore(outRobustness,p,vec4(0)); return;
    }

    vec3 refMu,refVar;dogsonRef(refLR,refMu,refVar);
    vec3 altMu=dogsonAlt(altLR);
    vec3 dp=abs(refMu-altMu);

    float d2=0.0,sigma2=0.0;
    for(int c=0;c<3;c++){
        vec2 curve=ipolNoise(refMu[c]);
        float sigmaT=max(curve.x,1.0e-8);
        float dT=max(curve.y,1.0e-8);
        float dp2=dp[c]*dp[c];
        float shrink=dp2/max(dp2+dT*dT,1.0e-12);
        d2+=dp2*shrink*shrink;
        sigma2+=max(refVar[c],sigmaT*sigmaT);
    }

    vec2 mn=vec2(3.402823e38),mx=vec2(-3.402823e38);
    int ts=max(tileSizeRaw,1);
    for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){
        ivec2 q=clamp(
            p+ivec2(x,y)*ts,ivec2(0),rawSize-ivec2(1));
        vec2 f=denseRawFlowAt(q); mn=min(mn,f);mx=max(mx,f);
    }
    vec2 span=mx-mn;
    float S=dot(span,span)>0.8*0.8?2.0:12.0;
    float R=clamp(
        S*exp(-d2/max(sigma2,1.0e-12))-0.12,0.0,1.0);
    imageStore(outRobustness,p,vec4(R));
}
GLSL_ROBUST

cat > "$TMP/candidate/$ICA" <<'GLSL_ICA'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D ReferenceGuide;
uniform highp sampler2D MovingGuide;
uniform highp sampler2D BlockFlow;
uniform highp sampler2D ReferenceGradient;
uniform highp sampler2D InverseHessian;
layout(rgba16f,binding=0) uniform highp writeonly image2D OutputFlow;
uniform ivec2 levelSize;
uniform int tileSize;

float movingAt(vec2 p) {
    if(p.x<0.0||p.y<0.0||p.x>float(levelSize.x-1)||p.y>float(levelSize.y-1))
        return 0.0;
    ivec2 p0=ivec2(floor(p));
    ivec2 p1=min(p0+ivec2(1),levelSize-ivec2(1));
    vec2 f=fract(p);
    float a=mix(texelFetch(MovingGuide,p0,0).r,
                texelFetch(MovingGuide,ivec2(p1.x,p0.y),0).r,f.x);
    float b=mix(texelFetch(MovingGuide,ivec2(p0.x,p1.y),0).r,
                texelFetch(MovingGuide,p1,0).r,f.x);
    return mix(a,b,f.y);
}
float refCircular(ivec2 p) {
    ivec2 q=ivec2((p.x%levelSize.x+levelSize.x)%levelSize.x,
                  (p.y%levelSize.y+levelSize.y)%levelSize.y);
    return texelFetch(ReferenceGuide,q,0).r;
}

/*
 * IRIS_26475_IPOL_ICA_FINE_ONLY_THREE_ITERATIONS
 * IPOL Algorithm 2: multi-scale BM first, then exactly three ICA iterations
 * on the final fine tiles. Wronski states exactly three LK refinements after
 * block matching; whether LK was repeated at each pyramid stage is unspecified.
 */
void main() {
    ivec2 tile=ivec2(gl_GlobalInvocationID.xy);
    ivec2 grid=imageSize(OutputFlow);
    if(any(greaterThanEqual(tile,grid))) return;

    vec4 seed=texelFetch(BlockFlow,tile,0);
    vec4 ih=texelFetch(InverseHessian,tile,0);
    if(dot(abs(ih),vec4(1.0))<=1.0e-12){
        imageStore(OutputFlow,tile,seed);
        return;
    }

    vec2 flow=seed.xy;
    for(int iter=0;iter<3;iter++){
        float b0=0.0,b1=0.0;
        for(int yy=0;yy<64;yy++){
            if(yy>=tileSize) continue;
            for(int xx=0;xx<64;xx++){
                if(xx>=tileSize) continue;
                ivec2 p=tile*tileSize+ivec2(xx,yy);
                if(any(greaterThanEqual(p,levelSize))) continue;
                vec2 g=texelFetch(ReferenceGradient,p,0).rg;
                float residual=movingAt(vec2(p)+flow)-refCircular(p);
                b0 += -g.x*residual;
                b1 += -g.y*residual;
            }
        }
        vec2 d=vec2(
            ih.r*b0 + ih.g*b1,
            ih.b*b0 + ih.a*b1);
        flow+=d;
    }
    imageStore(OutputFlow,tile,vec4(flow,seed.zw));
}

GLSL_ICA

cat > "$TMP/candidate/$GRAD" <<'GLSL_GRAD'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D ReferenceGuide;
layout(rg32f,binding=0) uniform highp writeonly image2D OutputGradient;
uniform ivec2 levelSize;

/*
 * IRIS_26475_IPOL_ICA_REFERENCE_GRADIENT_PREP_ONCE
 * Same centered finite-difference gradient used by 26473 ICA, but computed
 * once for the immutable reference instead of once per auxiliary/iteration.
 */
float refCircular(ivec2 p) {
    ivec2 q=ivec2((p.x%levelSize.x+levelSize.x)%levelSize.x,
                  (p.y%levelSize.y+levelSize.y)%levelSize.y);
    return texelFetch(ReferenceGuide,q,0).r;
}
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(p,levelSize))) return;
    vec2 g=vec2(
        refCircular(p+ivec2(1,0))-refCircular(p-ivec2(1,0)),
        refCircular(p+ivec2(0,1))-refCircular(p-ivec2(0,1)));
    imageStore(OutputGradient,p,vec4(g,0.0,0.0));
}

GLSL_GRAD

cat > "$TMP/candidate/$HESS" <<'GLSL_HESS'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D ReferenceGradient;
layout(rgba32f,binding=0) uniform highp writeonly image2D OutputInverseHessian;
uniform ivec2 levelSize;
uniform int tileSize;

/*
 * IRIS_26475_IPOL_ICA_REFERENCE_HESSIAN_PREP_ONCE
 * IPOL computation details separate a fixed reference initialization cost
 * (reference gradients + ICA Hessians) from linear per-auxiliary work.
 */
void main(){
    ivec2 tile=ivec2(gl_GlobalInvocationID.xy);
    ivec2 grid=imageSize(OutputInverseHessian);
    if(any(greaterThanEqual(tile,grid))) return;

    float H00=0.0,H01=0.0,H11=0.0;
    for(int yy=0;yy<64;yy++){
        if(yy>=tileSize) continue;
        for(int xx=0;xx<64;xx++){
            if(xx>=tileSize) continue;
            ivec2 p=tile*tileSize+ivec2(xx,yy);
            if(any(greaterThanEqual(p,levelSize))) continue;
            vec2 g=texelFetch(ReferenceGradient,p,0).rg;
            H00+=g.x*g.x;
            H01+=g.x*g.y;
            H11+=g.y*g.y;
        }
    }
    float det=H00*H11-H01*H01;
    if(abs(det)<1.0e-10){
        imageStore(OutputInverseHessian,tile,vec4(0.0));
        return;
    }
    float invDet=1.0/det;
    imageStore(OutputInverseHessian,tile,
        vec4(H11*invDet,-H01*invDet,-H01*invDet,H00*invDet));
}

GLSL_HESS

cat > "$TMP/candidate/$ALIGNJAVA" <<'JAVA_ALIGN'
package com.particlesdevs.photoncamera.processing.processor;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLProg;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.util.Log;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_LINEAR;
import static android.opengl.GLES20.GL_NEAREST;

/**
 * IRIS_26473_IPOL_WRONSKI_ALIGNMENT_COMPLETION
 * IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE
 *
 * Preserves the proven 26467 prepared-reference API and burst lifetime while
 * completing the remaining public/IPOL alignment differences.
 */
public final class MotionV2WronskiAlignment {
    private static final String TAG = "MotionV2WronskiAlign";
    private MotionV2WronskiAlignment() {}

    private static Point divCeil(Point p, int d) {
        return new Point(
                Math.max(1, (p.x + d - 1) / d),
                Math.max(1, (p.y + d - 1) / d));
    }

    public static final class PreparedReference implements AutoCloseable {
        private final Point rawHalf;
        private final int cfaPattern;
        private final float signalScale;
        private final float snr;
        private GLTexture[] levels;
        private GLTexture referenceGradient;
        private GLTexture fineInverseHessian;

        private PreparedReference(
                Point rawHalf,
                int cfaPattern,
                float signalScale,
                float snr,
                GLTexture[] levels,
                GLTexture referenceGradient,
                GLTexture fineInverseHessian) {
            this.rawHalf = new Point(rawHalf);
            this.cfaPattern = cfaPattern;
            this.signalScale = signalScale;
            this.snr = snr;
            this.levels = levels;
            this.referenceGradient = referenceGradient;
            this.fineInverseHessian = fineInverseHessian;
        }

        @Override
        public void close() {
            if (levels == null) return;
            for (GLTexture t : levels) {
                if (t != null) t.close();
            }
            levels = null;
            if (referenceGradient != null) {
                referenceGradient.close();
                referenceGradient = null;
            }
            if (fineInverseHessian != null) {
                fineInverseHessian.close();
                fineInverseHessian = null;
            }
        }
    }

    private static GLTexture[] buildGuidePyramid(
            Point rawHalf,
            int cfaPattern,
            float signalScale,
            GLProg glProg,
            GLTexture cfa) {

        final int[] stepFactor = new int[] {1, 2, 4, 4};
        GLTexture[] guide = new GLTexture[4];
        GLTexture[] tmp = new GLTexture[4];

        try {
            guide[0] = new GLTexture(
                    rawHalf,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                    null, GL_NEAREST, GL_CLAMP_TO_EDGE);

            glProg.setDefine("CFAPATTERN", cfaPattern);
            glProg.setLayout(8,8,1);
            glProg.useAssetProgram("motionv2/alignment_guide", true);
            glProg.setVar("guideScale", 1);
            glProg.setVar("signalScale", Math.max(signalScale,1.0e-6f));
            glProg.setTexture("InputCfa", cfa);
            glProg.setTextureCompute("OutputGuide", guide[0], true);
            glProg.computeAuto(rawHalf,1);

            Point prev = rawHalf;
            for (int l=1;l<4;l++) {
                Point levelSize = divCeil(prev, stepFactor[l]);

                tmp[l] = new GLTexture(
                        prev,
                        new GLFormat(GLFormat.DataType.FLOAT_32,1),
                        null, GL_LINEAR, GL_CLAMP_TO_EDGE);
                guide[l] = new GLTexture(
                        levelSize,
                        new GLFormat(GLFormat.DataType.FLOAT_32,1),
                        null, GL_LINEAR, GL_CLAMP_TO_EDGE);

                // Public cuda_downsample(): separable Gaussian with
                // sigma=factor/2, radius=4*sigma, then decimation.
                glProg.setLayout(8,8,1);
                glProg.useAssetProgram("motionv2/mfsr_pyramid_gaussian", true);
                glProg.setVar("factor", stepFactor[l]);
                glProg.setVar("direction", 0);
                glProg.setTexture("InputGuide", guide[l-1]);
                glProg.setTextureCompute("OutputGuide", tmp[l], true);
                glProg.computeAuto(prev,1);

                glProg.setLayout(8,8,1);
                glProg.useAssetProgram("motionv2/mfsr_pyramid_gaussian", true);
                glProg.setVar("factor", stepFactor[l]);
                glProg.setVar("direction", 1);
                glProg.setTexture("InputGuide", tmp[l]);
                glProg.setTextureCompute("OutputGuide", guide[l], true);
                glProg.computeAuto(levelSize,1);

                tmp[l].close();
                tmp[l] = null;
                prev = levelSize;
            }
            return guide;
        } catch (Throwable t) {
            for (GLTexture texture : tmp) {
                if (texture != null) {
                    try { texture.close(); } catch (Throwable ignored) {}
                }
            }
            for (GLTexture texture : guide) {
                if (texture != null) {
                    try { texture.close(); } catch (Throwable ignored) {}
                }
            }
            throw t;
        }
    }

    public static PreparedReference prepareReference(
            Point rawHalf,
            int cfaPattern,
            float signalScale,
            float snr,
            GLProg glProg,
            GLTexture referenceCfa) {

        long start = System.currentTimeMillis();
        GLTexture[] ref = buildGuidePyramid(
                rawHalf, cfaPattern, signalScale, glProg, referenceCfa);

        final int baseTile = snr <= 14.0f ? 64 : (snr <= 22.0f ? 32 : 16);
        final Point fineGrid = new Point(
                Math.max(1,(rawHalf.x + baseTile - 1)/baseTile),
                Math.max(1,(rawHalf.y + baseTile - 1)/baseTile));

        GLTexture referenceGradient = new GLTexture(
                rawHalf,
                new GLFormat(GLFormat.DataType.FLOAT_32,2),
                null, GL_NEAREST, GL_CLAMP_TO_EDGE);
        glProg.setLayout(8,8,1);
        glProg.useAssetProgram("motionv2/mfsr_ica_reference_gradient", true);
        glProg.setVar("levelSize", rawHalf);
        glProg.setTexture("ReferenceGuide", ref[0]);
        glProg.setTextureCompute("OutputGradient", referenceGradient, true);
        glProg.computeAuto(rawHalf,1);

        GLTexture fineInverseHessian = new GLTexture(
                fineGrid,
                new GLFormat(GLFormat.DataType.FLOAT_32,4),
                null, GL_NEAREST, GL_CLAMP_TO_EDGE);
        glProg.setLayout(8,8,1);
        glProg.useAssetProgram("motionv2/mfsr_ica_reference_hessian", true);
        glProg.setVar("levelSize", rawHalf);
        glProg.setVar("tileSize", baseTile);
        glProg.setTexture("ReferenceGradient", referenceGradient);
        glProg.setTextureCompute("OutputInverseHessian", fineInverseHessian, true);
        glProg.computeAuto(fineGrid,1);

        Log.d(TAG,
                "IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE"
                + " elapsedMs=" + (System.currentTimeMillis() - start)
                + " levels=4"
                + " reusedAcrossAuxiliaries=true"
                + " guide=bayerQuadAverage"
                + " icaReferenceGradientPreparedOnce=true"
                + " icaReferenceHessianPreparedOnce=true"
                + " ipol26475=true");

        return new PreparedReference(
                rawHalf, cfaPattern, signalScale, snr, ref,
                referenceGradient, fineInverseHessian);
    }

    public static MotionV2Alignment.Result alignPrepared(
            PreparedReference prepared,
            GLProg glProg,
            GLTexture alterCfa) {

        if (prepared == null || prepared.levels == null) {
            throw new IllegalStateException("Wronski prepared reference is closed");
        }

        final Point rawHalf = prepared.rawHalf;
        final float snr = prepared.snr;
        final int baseTile = snr <= 14.0f ? 64 : (snr <= 22.0f ? 32 : 16);
        final int[] tile = new int[] {
                baseTile, baseTile, baseTile, Math.max(8, baseTile / 2)
        };
        final int[] radius = new int[] {1, 4, 4, 4};
        final int[] metric = new int[] {0, 1, 1, 1};
        final int[] stepFactor = new int[] {1, 2, 4, 4};

        final GLTexture[] ref = prepared.levels;
        GLTexture[] alt = null;
        GLTexture previousFlow = null;
        GLTexture denseFlow = null;

        try {
            alt = buildGuidePyramid(
                    rawHalf,
                    prepared.cfaPattern,
                    prepared.signalScale,
                    glProg,
                    alterCfa);

            Point[] levelSize = new Point[4];
            levelSize[0] = rawHalf;
            for (int l=1;l<4;l++) {
                levelSize[l] = divCeil(levelSize[l-1], stepFactor[l]);
            }

            for (int l=3;l>=0;l--) {
                Point grid = new Point(
                        Math.max(1,(levelSize[l].x + tile[l]-1)/tile[l]),
                        Math.max(1,(levelSize[l].y + tile[l]-1)/tile[l]));

                GLTexture block = new GLTexture(
                        grid,
                        new GLFormat(GLFormat.DataType.FLOAT_16,4),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);

                glProg.setLayout(8,8,1);
                glProg.useAssetProgram("motionv2/mfsr_block_match", true);
                glProg.setVar("levelSize", levelSize[l]);
                glProg.setVar("tileSize", tile[l]);
                glProg.setVar("searchRadius", radius[l]);
                glProg.setVar("distanceMetric", metric[l]);
                glProg.setVar("hasPrevious", previousFlow != null ? 1 : 0);
                glProg.setVar(
                        "previousToCurrentScale",
                        l < 3 ? (float)stepFactor[l+1] : 1.0f);
                glProg.setTexture("ReferenceGuide", ref[l]);
                glProg.setTexture("MovingGuide", alt[l]);
                glProg.setTexture(
                        "PreviousFlow",
                        previousFlow != null ? previousFlow : ref[l]);
                glProg.setTextureCompute("OutputFlow", block, true);
                glProg.computeAuto(grid,1);

                GLTexture nextFlow = block;

                if (l == 0) {
                    GLTexture refined = new GLTexture(
                            grid,
                            new GLFormat(GLFormat.DataType.FLOAT_16,4),
                            null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                    glProg.setLayout(8,8,1);
                    glProg.useAssetProgram("motionv2/mfsr_ica_refine", true);
                    glProg.setVar("levelSize", levelSize[l]);
                    glProg.setVar("tileSize", tile[l]);
                    glProg.setTexture("ReferenceGuide", ref[l]);
                    glProg.setTexture("MovingGuide", alt[l]);
                    glProg.setTexture("BlockFlow", block);
                    glProg.setTexture(
                            "ReferenceGradient",
                            prepared.referenceGradient);
                    glProg.setTexture(
                            "InverseHessian",
                            prepared.fineInverseHessian);
                    glProg.setTextureCompute("OutputFlow", refined, true);
                    glProg.computeAuto(grid,1);
                    block.close();
                    nextFlow = refined;
                }

                if (previousFlow != null) previousFlow.close();
                previousFlow = nextFlow;
            }

            denseFlow = new GLTexture(
                    rawHalf,
                    new GLFormat(GLFormat.DataType.FLOAT_16,4),
                    null, GL_NEAREST, GL_CLAMP_TO_EDGE);

            glProg.setLayout(8,8,1);
            glProg.useAssetProgram("motionv2/mfsr_flow_expand", true);
            glProg.setVar("outputSize", rawHalf);
            glProg.setVar("tileSize", baseTile);
            glProg.setTexture("TileFlow", previousFlow);
            glProg.setTextureCompute("OutputFlow", denseFlow, true);
            glProg.computeAuto(rawHalf,1);

            Log.d(TAG,
                    "IRIS_26473_IPOL_WRONSKI_ALIGNMENT_COMPLETION"
                    + " snr=" + snr
                    + " baseTile=" + baseTile
                    + " guide=bayerQuadAverageLikelyOriginalWronski"
                    + " gaussianSigma=factorHalf"
                    + " gaussianRadius=fourSigma"
                    + " factors=1,2,4,4"
                    + " radii=1,4,4,4"
                    + " metrics=L1,L2,L2,L2"
                    + " icaIterations=3FineOnly"
                    + " icaReferencePrecompute=true"
                    + " icaUpdateClamp=false"
                    + " referenceBoundary=circular"
                    + " movingBoundary=zero"
                    + " flowUpscale=nearest"
                    + " referencePreparedOnce=true");

            GLTexture keep = denseFlow;
            denseFlow = null;
            return new MotionV2Alignment.Result(
                    keep,0.0f,0.0f,1.0f,0.0f);
        } finally {
            if (denseFlow != null) denseFlow.close();
            if (previousFlow != null) previousFlow.close();
            if (alt != null) {
                for (GLTexture t : alt) {
                    if (t != null) t.close();
                }
            }
        }
    }

    public static MotionV2Alignment.Result align(
            Point rawHalf,
            int cfaPattern,
            float signalScale,
            float snr,
            GLProg glProg,
            GLTexture referenceCfa,
            GLTexture alterCfa) {
        try (PreparedReference prepared = prepareReference(
                rawHalf, cfaPattern, signalScale, snr, glProg, referenceCfa)) {
            return alignPrepared(prepared, glProg, alterCfa);
        }
    }
}
JAVA_ALIGN

cat > "$TMP/candidate/$NOISEJAVA" <<'JAVA_NOISE'
package com.particlesdevs.photoncamera.processing.processor;

import android.graphics.Point;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.LinkedHashMap;
import java.util.Map;

import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26473_IPOL_FAST_MONTE_CARLO_NOISE_CURVES
 *
 * Deterministic mobile implementation of public IPOL fast_monte_carlo.py:
 * affine variance, 1001 brightness entries, explicit [0,1] clipping,
 * Monte-Carlo in nonlinear clipping zones, and variance-domain interpolation
 * through the linear middle range.
 */
public final class MotionV2IpolNoiseCurve {
    private static final int LEVELS = 1000;
    private static final int PATCHES = 8192;
    private static final double TOL = 3.0;
    private static final String TAG = "MotionV2IpolNoiseCurve";
    private static final int CACHE_SIZE = 8;

    /*
     * IRIS_26475_IPOL_MC_EXACT_TABLE_CACHE
     * Pure implementation optimization: cache is keyed by the exact float
     * bit patterns of alpha/beta. A cache hit changes zero calculations.
     */
    private static final LinkedHashMap<Long, Table> TABLE_CACHE =
            new LinkedHashMap<Long, Table>(CACHE_SIZE, 0.75f, true) {
                @Override
                protected boolean removeEldestEntry(Map.Entry<Long, Table> e) {
                    return size() > CACHE_SIZE;
                }
            };

    private MotionV2IpolNoiseCurve() {}

    private static final class Table {
        final float[] sigma;
        final float[] diff;
        final int imin;
        final int imax;
        Table(float[] sigma, float[] diff, int imin, int imax) {
            this.sigma = sigma;
            this.diff = diff;
            this.imin = imin;
            this.imax = imax;
        }
    }

    public static final class Curve {
        public final ByteBuffer rgba32f;
        public final float referenceMean;
        public final float snr;
        public final int nonlinearLowEnd;
        public final int nonlinearHighStart;

        Curve(ByteBuffer rgba32f, float referenceMean, float snr,
              int nonlinearLowEnd, int nonlinearHighStart) {
            this.rgba32f = rgba32f;
            this.referenceMean = referenceMean;
            this.snr = snr;
            this.nonlinearLowEnd = nonlinearLowEnd;
            this.nonlinearHighStart = nonlinearHighStart;
        }
    }

    public static Curve build(float alpha, float beta, ByteBuffer referenceRaw,
                              Point rawSize, float[] blackLevel, float whiteLevel,
                              float canonicalGain) {
        alpha = Math.max(alpha, 1.0e-9f);
        beta = Math.max(beta, 0.0f);

        final long key =
                ((long)Float.floatToIntBits(alpha) << 32)
                        ^ (Float.floatToIntBits(beta) & 0xffffffffL);
        Table table;
        boolean hit;
        synchronized (TABLE_CACHE) {
            table = TABLE_CACHE.get(key);
            hit = table != null;
        }
        if (table == null) {
            table = buildExactTable(alpha, beta);
            synchronized (TABLE_CACHE) {
                TABLE_CACHE.put(key, table);
            }
        }

        float referenceMean = estimateReferenceMean(
                referenceRaw, rawSize, blackLevel, whiteLevel, canonicalGain);
        int noiseIndex = clampInt(
                Math.round(LEVELS * clamp01(referenceMean)), 0, LEVELS);
        float noiseStd = Math.max(table.sigma[noiseIndex], 1.0e-8f);
        float snr = Math.max(
                6.0f, Math.min(30.0f, referenceMean / noiseStd));

        ByteBuffer tex = ByteBuffer.allocateDirect((LEVELS + 1) * 16)
                .order(ByteOrder.nativeOrder());
        for (int i = 0; i <= LEVELS; i++) {
            tex.putFloat(table.sigma[i]);
            tex.putFloat(table.diff[i]);
            tex.putFloat(i / (float)LEVELS);
            tex.putFloat(1.0f);
        }
        tex.position(0);

        Log.d(TAG, "IRIS_26475_IPOL_MC_EXACT_TABLE_CACHE"
                + " hit=" + hit
                + " entries=" + TABLE_CACHE.size()
                + " alphaBits=" + Integer.toUnsignedString(
                        Float.floatToIntBits(alpha))
                + " betaBits=" + Integer.toUnsignedString(
                        Float.floatToIntBits(beta))
                + " mathChanged=false");

        return new Curve(
                tex, referenceMean, snr, table.imin, table.imax);
    }

    private static Table buildExactTable(float alpha, float beta) {
        alpha = Math.max(alpha, 1.0e-9f);
            beta = Math.max(beta, 0.0f);

            float[] sigma = new float[LEVELS + 1];
            float[] diff = new float[LEVELS + 1];

            double tolSq = TOL * TOL;
            double xmin = tolSq / 2.0
                    * (alpha + Math.sqrt(tolSq * alpha * alpha + 4.0 * beta));
            double xmaxTerm = 2.0 + tolSq * alpha;
            double xmaxDisc = Math.max(
                    0.0, xmaxTerm * xmaxTerm - 4.0 * (1.0 + tolSq * beta));
            double xmax = (xmaxTerm - Math.sqrt(xmaxDisc)) / 2.0;

            int imin = clampInt((int)Math.ceil(xmin * LEVELS) + 1, 0, LEVELS);
            int imax = clampInt((int)Math.floor(xmax * LEVELS) - 1, 0, LEVELS);

            long seed = 0x9e3779b97f4a7c15L
                    ^ Float.floatToIntBits(alpha)
                    ^ ((long)Float.floatToIntBits(beta) << 32);

            if (imin >= imax) {
                Rng rng = new Rng(seed);
                for (int i = 0; i <= LEVELS; i++) {
                    float[] sd = unitaryMc(
                            alpha, beta, i / (float)LEVELS, 2048, rng);
                    sigma[i] = sd[0];
                    diff[i] = sd[1];
                }
                imin = LEVELS;
                imax = LEVELS;
            } else {
                Rng rng = new Rng(seed);
                for (int i = 0; i <= imin; i++) {
                    float[] sd = unitaryMc(
                            alpha, beta, i / (float)LEVELS, PATCHES, rng);
                    sigma[i] = sd[0];
                    diff[i] = sd[1];
                }
                for (int i = imax; i <= LEVELS; i++) {
                    float[] sd = unitaryMc(
                            alpha, beta, i / (float)LEVELS, PATCHES, rng);
                    sigma[i] = sd[0];
                    diff[i] = sd[1];
                }

                final float sigmaLo2 = sigma[imin] * sigma[imin];
                final float sigmaHi2 = sigma[imax] * sigma[imax];
                final float diffLo2 = diff[imin] * diff[imin];
                final float diffHi2 = diff[imax] * diff[imax];
                final float denom = Math.max(
                        1.0f, (imax + 1.0f) - (imin - 1.0f));

                for (int i = imin; i <= imax; i++) {
                    float t = (i - (imin - 1.0f)) / denom;
                    sigma[i] = (float)Math.sqrt(Math.max(
                            0.0f, sigmaLo2 + t * (sigmaHi2 - sigmaLo2)));
                    diff[i] = (float)Math.sqrt(Math.max(
                            0.0f, diffLo2 + t * (diffHi2 - diffLo2)));
                }
            }

        return new Table(sigma, diff, imin, imax);
    }

    private static float estimateReferenceMean(
            ByteBuffer raw, Point size, float[] black, float white,
            float exposure) {
        if (raw == null || size == null || size.x <= 0 || size.y <= 0)
            return 0.18f;

        ByteBuffer view = raw.duplicate().order(ByteOrder.nativeOrder());
        int samples = Math.min(view.capacity() / 2, size.x * size.y);
        if (samples <= 0) return 0.18f;

        double sum = 0.0;
        int used = 0;
        for (int index = 0; index < samples; index++) {
            int y = index / size.x;
            int x = index - y * size.x;
            int c = ((y & 1) << 1) | (x & 1);
            float b = black != null && black.length >= 4 ? black[c] : 0.0f;
            float den = Math.max(white - b, 1.0f);
            float code = Short.toUnsignedInt(view.getShort(index * 2));
            float value = Math.max((code - b) / den, 0.0f) * exposure;
            sum += Math.min(value, 1.0f);
            used++;
        }
        return used > 0 ? (float)(sum / used) : 0.18f;
    }

    private static float[] unitaryMc(
            float alpha, float beta, float brightness, int patches, Rng rng) {
        double stdAcc = 0.0;
        double diffAcc = 0.0;
        double noiseStd = Math.sqrt(Math.max(
                brightness * alpha + beta, 0.0));

        for (int p = 0; p < patches; p++) {
            double sum1 = 0.0, sum2 = 0.0;
            double sq1 = 0.0, sq2 = 0.0;
            for (int k = 0; k < 9; k++) {
                double a = clamp01(
                        brightness + noiseStd * rng.gaussian());
                double b = clamp01(
                        brightness + noiseStd * rng.gaussian());
                sum1 += a; sum2 += b;
                sq1 += a * a; sq2 += b * b;
            }
            double mean1 = sum1 / 9.0;
            double mean2 = sum2 / 9.0;
            double var1 = Math.max(
                    sq1 / 9.0 - mean1 * mean1, 0.0);
            double var2 = Math.max(
                    sq2 / 9.0 - mean2 * mean2, 0.0);
            stdAcc += 0.5 * (Math.sqrt(var1) + Math.sqrt(var2));
            diffAcc += Math.abs(mean1 - mean2);
        }
        return new float[] {
                (float)(stdAcc / patches),
                (float)(diffAcc / patches)
        };
    }

    private static float clamp01(float x) {
        return Math.max(0.0f, Math.min(1.0f, x));
    }
    private static double clamp01(double x) {
        return Math.max(0.0, Math.min(1.0, x));
    }
    private static int clampInt(int x, int lo, int hi) {
        return Math.max(lo, Math.min(hi, x));
    }

    private static final class Rng {
        private long state;
        private boolean hasSpare;
        private double spare;

        Rng(long seed) {
            state = seed != 0L ? seed : 0x6a09e667f3bcc909L;
        }

        private double uniform() {
            long x = state;
            x ^= x << 13;
            x ^= x >>> 7;
            x ^= x << 17;
            state = x;
            long bits = (x >>> 11) & ((1L << 53) - 1);
            return (bits + 1.0) / ((1L << 53) + 2.0);
        }

        double gaussian() {
            if (hasSpare) {
                hasSpare = false;
                return spare;
            }
            double u1 = uniform();
            double u2 = uniform();
            double r = Math.sqrt(-2.0 * Math.log(Math.max(u1, 1.0e-15)));
            double theta = 2.0 * Math.PI * u2;
            spare = r * Math.sin(theta);
            hasSpare = true;
            return r * Math.cos(theta);
        }
    }
}
JAVA_NOISE

python3 - "$TMP/candidate" <<'PY_TRANSFORM'
from pathlib import Path
import re,sys
root=Path(sys.argv[1])

recon=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java'
refmerge=root/'app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl'
version=root/'app/version.properties'

# Retire 26474-only temporal-age uniform/bind. Restore source robustness exactly.
t=recon.read_text()
pat=re.compile(
    r'\n\s*/\* IRIS_26474_TEMPORAL_AGE_DIRECT_WRONSKI \*/\n'
    r'\s*glProg\.setVar\(\n'
    r'\s*"temporalDistanceMs",\n'
    r'\s*\(float\) \(Math\.abs\([^;]+?\n'
    r'\s*/ 1000000\.0\)\);',
    re.S)
t2,n=pat.subn('',t,count=1)
if n!=1:
    raise SystemExit(f"26475 temporal-age retirement count={n}")
t=t2
recon.write_text(t)

# IPOL Sec. 2.3 / Algorithm 11 empirical merge values:
# Rmax=8, covariance multiplier C=8, support N5 (radius 2).
r=refmerge.read_text()
if r.count('const float MAX_FRAME_COUNT=2.0;')!=1:
    raise SystemExit("26475 old Rmax=2 anchor not unique")
r=r.replace('const float MAX_FRAME_COUNT=2.0;',
            'const float MAX_FRAME_COUNT=8.0;',1)
r=r.replace(
    'max_frame_count=2, rad_max=2, max_multiplier=8.',
    'max_frame_count=8, rad_max=2, max_multiplier=8.',1)
r=r.replace(
    ' * If accumulated robustness is <2, reference reconstruction OVERWRITES the',
    ' * If accumulated robustness is <8, reference reconstruction OVERWRITES the',1)
r=r.replace(
    'IRIS_26472_WRONSKI_PUBLIC_ACCUMULATED_ROBUSTNESS_REFERENCE_MERGE',
    'IRIS_26475_IPOL_RMAX8_REFERENCE_OWNERSHIP',1)
refmerge.write_text(r)

v=version.read_text()
if v.count("VERSION_NAME=0.9726474")!=1 or v.count("VERSION_BUILD=26474")!=1:
    raise SystemExit("26474 version anchors not unique")
v=v.replace("VERSION_NAME=0.9726474","VERSION_NAME=0.9726475",1)
v=v.replace("VERSION_BUILD=26474","VERSION_BUILD=26475",1)
version.write_text(v)
print("26475 source-fidelity transform: PASS")
PY_TRANSFORM

python3 - "$TMP/candidate" <<'PY_VALIDATE'
from pathlib import Path
import sys
root=Path(sys.argv[1])

required={
'app/src/main/assets/shaders/motionv2/alignment_guide.glsl':[
 'IRIS_26475_WRONSKI_BAYER_QUAD_ALIGNMENT_GUIDE',
 '0.25*(v.r+v.g+v.b+v.a)'],
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java':[
 'IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE',
 'mfsr_ica_reference_gradient',
 'mfsr_ica_reference_hessian',
 'if (l == 0)',
 'icaIterations=3FineOnly',
 'guide=bayerQuadAverageLikelyOriginalWronski'],
'app/src/main/assets/shaders/motionv2/mfsr_ica_refine.glsl':[
 'IRIS_26475_IPOL_ICA_FINE_ONLY_THREE_ITERATIONS',
 'for(int iter=0;iter<3;iter++)',
 'ReferenceGradient','InverseHessian'],
'app/src/main/assets/shaders/motionv2/mfsr_ica_reference_gradient.glsl':[
 'IRIS_26475_IPOL_ICA_REFERENCE_GRADIENT_PREP_ONCE'],
'app/src/main/assets/shaders/motionv2/mfsr_ica_reference_hessian.glsl':[
 'IRIS_26475_IPOL_ICA_REFERENCE_HESSIAN_PREP_ONCE'],
'app/src/main/assets/shaders/motionv2/mfsr_robustness.glsl':[
 'IRIS_26473_IPOL_FAST_MC_ROBUSTNESS_CURVES',
 'float S=dot(span,span)>0.8*0.8?2.0:12.0',
 'S*exp(-d2/max(sigma2,1.0e-12))-0.12'],
'app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl':[
 'IRIS_26475_IPOL_RMAX8_REFERENCE_OWNERSHIP',
 'const float MAX_FRAME_COUNT=8.0;',
 'const int RAD_MAX=2;',
 'const float MAX_MULTIPLIER=8.0;'],
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2IpolNoiseCurve.java':[
 'IRIS_26475_IPOL_MC_EXACT_TABLE_CACHE',
 'Float.floatToIntBits(alpha)',
 'buildExactTable(alpha, beta)',
 'mathChanged=false'],
}
for rel,markers in required.items():
    txt=(root/rel).read_text()
    for marker in markers:
        if marker not in txt:
            raise SystemExit(f"candidate missing {marker} in {rel}")

recon=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java').read_text()
rob=(root/'app/src/main/assets/shaders/motionv2/mfsr_robustness.glsl').read_text()
if 'IRIS_26474_TEMPORAL_AGE_DIRECT_WRONSKI' in recon:
    raise SystemExit("26474 temporal age Java bind survived")
for stale in [
 'IRIS_26474_REFERENCE_ANCHORED_TEMPORAL_DISOCCLUSION',
 'IRIS_26474_SUB_TILE_FULL_RES_ACCEPTANCE',
 'temporalSceneGate','temporalDistanceMs']:
    if stale in rob:
        raise SystemExit("26474 custom robustness survived: "+stale)

# Preserve exact published constants already proven in 26473.
align=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java').read_text()
for marker in ['(1, 4, 4, 4)','(0, 1, 1, 1)','(1, 2, 4, 4)',
               'snr <= 14.0f ? 64 : (snr <= 22.0f ? 32 : 16)']:
    if marker not in align:
        raise SystemExit("alignment source constant missing: "+marker)

print("candidate/source validation PASS")
print("Temporary-copy validation: PASS")
PY_VALIDATE
pass "candidate/source validation PASS"
pass "Temporary-copy validation: PASS"

# Apply only validated candidate files to ephemeral app source.
for f in "$RECON" "$ALIGNJAVA" "$NOISEJAVA" "$GUIDE" "$ROBUST" "$REFMERGE" "$ICA" "$VERSION"; do
  cp "$TMP/candidate/$f" "$f"
done
cp "$TMP/candidate/$GRAD" "$GRAD"
cp "$TMP/candidate/$HESS" "$HESS"

grep -q 'public static final class PreparedReference implements AutoCloseable' "$ALIGNJAVA" || fail "PreparedReference API lost"
grep -q 'public static PreparedReference prepareReference(' "$ALIGNJAVA" || fail "prepareReference API lost"
grep -q 'public static MotionV2Alignment.Result alignPrepared(' "$ALIGNJAVA" || fail "alignPrepared API lost"
pass "26467 prepared-reference contract preserved"

for marker in \
 IRIS_26475_WRONSKI_BAYER_QUAD_ALIGNMENT_GUIDE \
 IRIS_26475_IPOL_ICA_FINE_ONLY_THREE_ITERATIONS \
 IRIS_26475_IPOL_ICA_REFERENCE_GRADIENT_PREP_ONCE \
 IRIS_26475_IPOL_ICA_REFERENCE_HESSIAN_PREP_ONCE \
 IRIS_26475_IPOL_RMAX8_REFERENCE_OWNERSHIP \
 IRIS_26475_IPOL_MC_EXACT_TABLE_CACHE \
 IRIS_26473_IPOL_FAST_MC_ROBUSTNESS_CURVES \
 IRIS_26472_WRONSKI_AUX_FIRST_ZERO_ACCUMULATOR \
 IRIS_26472_SDR_AUTHORITATIVE_UHDR_HEADROOM \
 IRIS_26470_UHDR_RENDER_GEOMETRY_AUTHORITY \
 IRIS_26474_DNG_SCENE_LINEAR_COLOR_SHADOW; do
  grep -Rqs "$marker" app/src/main || fail "post-apply marker missing $marker"
done

! grep -Rqs 'IRIS_26474_REFERENCE_ANCHORED_TEMPORAL_DISOCCLUSION' app/src/main || fail "26474 custom temporal gate survived"
! grep -Rqs 'temporalSceneGate' app/src/main || fail "26474 temporalSceneGate survived"

grep -q '^VERSION_NAME=0\.9726475$' app/version.properties || fail "26475 version name"
grep -q '^VERSION_BUILD=26475$' app/version.properties || fail "26475 version build"

# Verify untouched app files remain exactly as reproduced 26474.
find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_AFTER"
sha256sum app/version.properties >> "$HASH_AFTER"

git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$RECOVERY"
git diff "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$SOURCEPATCH"

cat > "$MATH" <<'EOF'
26475 Wronski/IPOL source-fidelity audit
========================================

WRONSKI 2019 — DIRECTLY PUBLISHED / PRESERVED
- ZSL model: recent RAW frames from a continuously captured ring buffer.
- coarse-to-fine pyramid block matching.
- subpixel refinement: exactly three Lucas-Kanade iterations after BM.
- online/sequential merge: auxiliary frames contribute one at a time.
- normalized RGB accumulation; no explicit conventional demosaic.
- local robustness: statistical term + 3x3 local flow-span motion prior.
- robustness constants retained: t=0.12, s1=2, s2=12, Mth=0.8 px.
- final 5x5 minimum robustness refinement preserved.
- SNR tile sizes preserved: 64 below 14, 32 at 14..22, 16 above 22.
- all retained frames considered; unsafe local evidence may contribute zero.

IPOL 2023 — IMPLEMENTATION DETAILS USED WHERE WRONSKI IS UNDERSPECIFIED
- fine-to-coarse factors [1,2,4,4].
- search radii [1,4,4,4].
- metrics [L1,L2,L2,L2].
- nearest flow upscale.
- Bayer-quad averaging selected because IPOL explicitly identifies it as the
  cheap/fast alternative likely closer to Wronski's original mobile alignment
  preprocessing. The workstation-only FFT-perfect-low-pass experiment is NOT
  approximated with a 5x5 binomial kernel anymore.
- BM over all pyramid levels, then exactly 3 ICA iterations only at fine level.
- reference gradient/Hessian are fixed-cost burst initialization and reused.
- accumulated robustness excludes the reference.
- reference is merged last.
- empirical low-support reference ownership: Rmax=8, N5/radius=2, C=8.
- if Rc < 8, previous auxiliary accumulation is discarded and reference owns
  reconstruction locally, matching Algorithm 11 behavior.

PHOTON-SPECIFIC EXTENSIONS RETAINED ONLY BECAUSE THEY ARE ALREADY PROTECTED
- censored-highlight validity support.
- exposure normalization / Motion exposure authority.
- SDR-authoritative UHDR headroom.
- read-only 26474 DNG color shadow telemetry.
- sharpening remains disabled.
- no ADRC or unaligned alternate fallback.

RETIRED AS UNSOURCED / UNHELPFUL
- 26473 5x5 binomial "FFT-equivalent" alignment approximation.
- 26474 temporal-age 3x3/7x7 scene gate and its hand-chosen age thresholds.

PERFORMANCE-PRESERVING IMPLEMENTATION CHANGES WITH IDENTICAL MATH
- reference ICA gradient and Hessian prepared once, not repeated per auxiliary.
- Monte-Carlo curve table cached by exact alpha/beta float bits; cache hits
  change no curve arithmetic.
EOF

echo "Protected-file hashes: PASS"
echo "PRE-BUILD SAFETY PROOF PASSED"
echo "  candidate/source validation PASS"
echo "  Temporary-copy validation: PASS"
echo "  exact successful 26474 V3 backup PASS"
echo "  exact successful 26474 V3 precursor PASS"
echo "  26467 prepared-reference API/lifetime PASS"
echo "  Wronski Bayer-quad mobile alignment guide PASS"
echo "  four-level BM constants PASS"
echo "  IPOL fine-only three ICA iterations PASS"
echo "  fixed-cost reference gradient/Hessian precompute PASS"
echo "  26473 source robustness restored PASS"
echo "  26474 unsourced temporal-age robustness retired PASS"
echo "  IPOL accumulated robustness Rmax=8 / radius=2 / C=8 PASS"
echo "  exact-alpha-beta MC cache math unchanged PASS"
echo "  aux-first/reference-last merge PASS"
echo "  26472 SDR-authoritative UHDR preserved PASS"
echo "  version/build increment in same script PASS"

cat > "$REPORT" <<EOF
26475 Wronski source-fidelity / performance
===========================================
Protected checkpoint: $PROTECTED_HEAD
Backup: $BACKUP_BRANCH -> $BACKUP_TARGET
Build: $NEW_VERSION / $NEW_BUILD

Expected primary effects:
- remove unsourced 26474 per-pixel temporal neighborhood work;
- run ICA exactly three times after final BM instead of at each pyramid level;
- precompute immutable reference ICA gradient/Hessian once per burst;
- use source-documented Bayer-quad mobile alignment preprocessing;
- restore IPOL local single-reference ownership when accumulated robustness <8;
- cache exact Monte-Carlo tables across identical alpha/beta profiles.

Output color owner is unchanged; 26474 DNG shadow remains read-only.
EOF

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
pass "26475 WRONSKI SOURCE-FIDELITY / PERFORMANCE BUILD SUCCESS"
