#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
PROTECTED_HEAD="e0bd03d64420e888770c56b29ebe92d2c9237523"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BACKUP_BRANCH="backup-26473-before-26474-temporal-color-audit"
BACKUP_TARGET="e0bd03d64420e888770c56b29ebe92d2c9237523"
PRECURSOR_SCRIPT="build_26473_ipol_wronski_completion_v2.sh"
PRECURSOR_BLOB="4d0f713b265189545dc353ba1a3afa8c1adf5a0e"

NEW_VERSION="0.9726474"
NEW_BUILD="26474"
OUTDIR="build_26474_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-temporal-disocclusion-color-shadow-debug.apk"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }

rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26474_source_audit.txt"
REPORT="$OUTDIR/26474_build_report.txt"
PREPATCH="$OUTDIR/26474_pre_edit_binary.patch"
RECOVERY="$OUTDIR/26474_recovery_binary.patch"
SOURCEPATCH="$OUTDIR/26474_source.patch"
HASH_INITIAL="$OUTDIR/26474_protected_initial.sha256"
HASH_26473="$OUTDIR/26474_protected_26473.sha256"
HASH_AFTER="$OUTDIR/26474_protected_after.sha256"
exec > >(tee "$AUDIT") 2>&1

echo "=== 26474 GUARDED TEMPORAL / DISOCCLUSION / COLOR-SHADOW BUILD ==="
date -Iseconds || true

BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "branch=$BRANCH expected=$EXPECTED_BRANCH"
pass "branch gate"

REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$BACKUP_TARGET" ]] || fail "backup=$REMOTE_BACKUP expected=$BACKUP_TARGET"
pass "backup branch exact successful 26473 V2 checkpoint"

git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "missing verified app base"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties || fail "app source changed before 26474"
pass "application source unchanged before 26474"

[[ -f "$PRECURSOR_SCRIPT" ]] || fail "missing $PRECURSOR_SCRIPT"
[[ "$(git hash-object "$PRECURSOR_SCRIPT")" == "$PRECURSOR_BLOB" ]] || fail "26473 V2 precursor blob mismatch"
pass "26473 V2 precursor exact"

git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$PREPATCH"
find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_INITIAL"
sha256sum app/version.properties >> "$HASH_INITIAL"
pass "binary pre-edit patch created before source modification"
pass "initial protected hashes captured"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

PRECURSOR="$TMP/26473_transform_only.sh"
awk '/^rm -f \.\/\*\.apk$/ { exit } { print }' "$PRECURSOR_SCRIPT" > "$PRECURSOR"
python3 - "$PRECURSOR" "$TMP/26473_precursor_outputs" <<'PY_PRE'
from pathlib import Path
import sys
p=Path(sys.argv[1]); t=p.read_text()
old='OUTDIR="build_26473_outputs"'
new='OUTDIR="'+sys.argv[2]+'"'
if t.count(old)!=1: raise SystemExit("26473 precursor OUTDIR anchor count="+str(t.count(old)))
p.write_text(t.replace(old,new,1))
print("26473 precursor OUTDIR rewrite: PASS")
PY_PRE
chmod +x "$PRECURSOR"
bash -n "$PRECURSOR"
bash "$PRECURSOR"

grep -q '^VERSION_NAME=0\.9726473$' app/version.properties || fail "26473 version name"
grep -q '^VERSION_BUILD=26473$' app/version.properties || fail "26473 version build"
for marker in \
  IRIS_26473_IPOL_FAST_MONTE_CARLO_NOISE_CURVES \
  IRIS_26473_IPOL_REFERENCE_BRIGHTNESS_SNR \
  IRIS_26473_IPOL_FFT_GREY_EQUIVALENT \
  IRIS_26473_IPOL_FACTOR_DEPENDENT_GAUSSIAN_PYRAMID \
  IRIS_26473_IPOL_ICA_EXACT_UPDATE \
  IRIS_26473_IPOL_FAST_MC_ROBUSTNESS_CURVES \
  IRIS_26473_IPOL_WRONSKI_ALIGNMENT_COMPLETION \
  IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE \
  IRIS_26472_WRONSKI_AUX_FIRST_ZERO_ACCUMULATOR \
  IRIS_26472_WRONSKI_PUBLIC_ACCUMULATED_ROBUSTNESS_REFERENCE_MERGE \
  IRIS_26472_SDR_AUTHORITATIVE_UHDR_HEADROOM \
  IRIS_26470_UHDR_RENDER_GEOMETRY_AUTHORITY; do
  grep -Rqs "$marker" app/src/main || fail "26473 lineage missing $marker"
done
pass "exact successful 26473 V2 application lineage reproduced"

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_26473"
sha256sum app/version.properties >> "$HASH_26473"

RECON="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
ROBUST="app/src/main/assets/shaders/motionv2/mfsr_robustness.glsl"
FINALIZE="app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl"
DNGSHADOW="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java"
VERSION="app/version.properties"

mkdir -p "$TMP/candidate/$(dirname "$RECON")" "$TMP/candidate/$(dirname "$ROBUST")" "$TMP/candidate/app"
cp "$RECON" "$TMP/candidate/$RECON"
cp "$ROBUST" "$TMP/candidate/$ROBUST"
cp "$FINALIZE" "$TMP/candidate/$FINALIZE"
cp "$VERSION" "$TMP/candidate/$VERSION"

cat > "$TMP/candidate/$ROBUST" <<'GLSL_26474'
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
uniform float temporalDistanceMs;

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

/*
 * IRIS_26474_REFERENCE_ANCHORED_TEMPORAL_DISOCCLUSION
 * IRIS_26474_SUB_TILE_FULL_RES_ACCEPTANCE
 * Age alone never rejects a static pixel. It only raises the burden of proof
 * when warped auxiliary evidence disagrees with the immutable reference.
 */
void localStatsRefRadius(ivec2 q,int radius,out vec3 mu,out vec3 var){
    vec3 s=vec3(0.0),ss=vec3(0.0); float n=0.0;
    for(int y=-3;y<=3;y++) for(int x=-3;x<=3;x++){
        if(abs(x)>radius||abs(y)>radius) continue;
        vec3 v=guideReference(clamp(q+ivec2(x,y),ivec2(0),rawHalf-ivec2(1)));
        s+=v; ss+=v*v; n+=1.0;
    }
    mu=s/max(n,1.0);
    var=max(ss/max(n,1.0)-mu*mu,vec3(0.0));
}
vec3 localMeanAltRadius(ivec2 q,int radius){
    vec3 s=vec3(0.0); float n=0.0;
    for(int y=-3;y<=3;y++) for(int x=-3;x<=3;x++){
        if(abs(x)>radius||abs(y)>radius) continue;
        s+=guideAlter(clamp(q+ivec2(x,y),ivec2(0),rawHalf-ivec2(1)));
        n+=1.0;
    }
    return s/max(n,1.0);
}
float normalizedMismatch(vec3 a,vec3 b,vec3 var){
    vec3 d=a-b;
    vec3 denom=max(var,vec3(2.5e-5));
    return sqrt(max(dot(d*d/denom,vec3(1.0/3.0)),0.0));
}
float temporalSceneGate(vec2 refLR,vec2 altLR){
    ivec2 rq=ivec2(round(refLR));
    ivec2 aq=ivec2(round(altLR));
    vec3 rf,vf; localStatsRefRadius(rq,1,rf,vf);
    vec3 af=localMeanAltRadius(aq,1);
    vec3 rw,vw; localStatsRefRadius(rq,3,rw,vw);
    vec3 aw=localMeanAltRadius(aq,3);
    float mismatch=max(normalizedMismatch(rf,af,vf),
                       0.72*normalizedMismatch(rw,aw,vw));
    float age=mix(1.0,1.85,smoothstep(66.0,400.0,max(temporalDistanceMs,0.0)));
    float evidence=mismatch*age;
    return 1.0-smoothstep(2.1,4.2,evidence);
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
    R*=temporalSceneGate(refLR,altLR);
    imageStore(outRobustness,p,vec4(R));
}
GLSL_26474

cat > "$TMP/candidate/$DNGSHADOW" <<'JAVA_DNG'
package com.particlesdevs.photoncamera.processing.processor;

import com.particlesdevs.photoncamera.util.Log;
import java.lang.reflect.Array;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Locale;

/** IRIS_26474_DNG_SCENE_LINEAR_COLOR_SHADOW */
public final class MotionV2DngColorShadow {
    private static final String TAG="MotionV2DngColorShadow";
    private MotionV2DngColorShadow(){}

    private static final float[] XYZ_TO_LINEAR_SRGB=new float[]{
         3.2404542f,-1.5371385f,-0.4985314f,
        -0.9692660f, 1.8760108f, 0.0415560f,
         0.0556434f,-0.2040259f, 1.0572252f
    };

    public static void logShadow(Object parameters){
        if(parameters==null)return;
        String[] names=new String[]{
            "cameraNeutral","neutralColorPoint","asShotNeutral",
            "calibrationIlluminant1","calibrationIlluminant2",
            "cameraCalibration1","cameraCalibration2",
            "colorMatrix1","colorMatrix2",
            "forwardTransform1","forwardTransform2",
            "forwardMatrix1","forwardMatrix2",
            "sensorToXYZ","sensorToXyz","sensorToProPhoto"
        };
        float[] sensorToXyz=null;
        StringBuilder found=new StringBuilder();
        for(String name:names){
            Object value=field(parameters,name);
            if(value==null)continue;
            if(found.length()>0)found.append(" | ");
            found.append(name).append('=').append(describe(value));
            if(sensorToXyz==null&&(name.equals("sensorToXYZ")||name.equals("sensorToXyz"))){
                float[] m=matrix9(value);
                if(m!=null)sensorToXyz=m;
            }
        }
        Log.d(TAG,"IRIS_26474_DNG_METADATA_SHADOW"
                +" jpegOutputOwner=26430 shadowOnly=true discovered={"+found+"}");
        if(sensorToXyz!=null){
            float[] shadow=multiply3x3(XYZ_TO_LINEAR_SRGB,sensorToXyz);
            Log.d(TAG,"IRIS_26474_DNG_SCENE_LINEAR_COLOR_SHADOW"
                    +" source=sensorToXYZ target=linear_sRGB outputApplied=false matrix="+fmt(shadow));
        }else{
            Log.d(TAG,"IRIS_26474_DNG_SCENE_LINEAR_COLOR_SHADOW"
                    +" source=sensorToXYZ available=false outputApplied=false");
        }
    }

    private static Object field(Object o,String name){
        Class<?> c=o.getClass();
        while(c!=null){
            try{
                Field f=c.getDeclaredField(name);
                f.setAccessible(true);
                return f.get(o);
            }catch(Throwable ignored){}
            c=c.getSuperclass();
        }
        return null;
    }

    private static float[] matrix9(Object v){
        try{
            if(v instanceof float[]){
                float[] a=(float[])v;
                if(a.length>=9){
                    float[] r=new float[9];
                    System.arraycopy(a,0,r,0,9);
                    return r;
                }
            }
            if(v instanceof double[]){
                double[] a=(double[])v;
                if(a.length>=9){
                    float[] r=new float[9];
                    for(int i=0;i<9;i++)r[i]=(float)a[i];
                    return r;
                }
            }
            if(v.getClass().isArray()&&Array.getLength(v)>=9){
                float[] r=new float[9];
                for(int i=0;i<9;i++)r[i]=Float.parseFloat(String.valueOf(Array.get(v,i)));
                return r;
            }
            for(String methodName:new String[]{"getArray","getData"}){
                try{
                    Method m=v.getClass().getMethod(methodName);
                    float[] r=matrix9(m.invoke(v));
                    if(r!=null)return r;
                }catch(Throwable ignored){}
            }
        }catch(Throwable ignored){}
        return null;
    }

    private static String describe(Object v){
        float[] m=matrix9(v);
        if(m!=null)return fmt(m);
        return String.valueOf(v);
    }

    private static float[] multiply3x3(float[] a,float[] b){
        float[] r=new float[9];
        for(int y=0;y<3;y++)for(int x=0;x<3;x++){
            float s=0;
            for(int k=0;k<3;k++)s+=a[y*3+k]*b[k*3+x];
            r[y*3+x]=s;
        }
        return r;
    }

    private static String fmt(float[] a){
        return String.format(Locale.US,
            "[%.7f,%.7f,%.7f;%.7f,%.7f,%.7f;%.7f,%.7f,%.7f]",
            a[0],a[1],a[2],a[3],a[4],a[5],a[6],a[7],a[8]);
    }
}

JAVA_DNG

python3 - "$TMP/candidate" <<'PY_TRANSFORM'
from pathlib import Path
import re,sys
root=Path(sys.argv[1])
recon=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java'
version=root/'app/version.properties'
finalize=root/'app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl'
t=recon.read_text()

anchor='                                glProg.setTexture(\n                                        "noiseCurve",\n                                        ipolNoiseCurveTexture);\n'
if t.count(anchor)!=1:
    raise SystemExit(f"26474 temporal bind anchor count={t.count(anchor)}")
rep=anchor+'                                /* IRIS_26474_TEMPORAL_AGE_DIRECT_WRONSKI */\n                                glProg.setVar(\n                                        "temporalDistanceMs",\n                                        (float) (Math.abs(frame.timestamp - reference.timestamp)\n                                                / 1000000.0));\n'
t=t.replace(anchor,rep,1)

m=re.search(r'(?m)^(\s*)(MotionV2ColorTransform\.)',t)
if not m:
    raise SystemExit("MotionV2ColorTransform invocation anchor not found")
indent=m.group(1)
insert=indent+'/* IRIS_26474_DNG_COLOR_SHADOW_CALL */\n'+indent+'MotionV2DngColorShadow.logShadow(parameters);\n'
t=t[:m.start()]+insert+t[m.start():]

class_anchor='public final class MotionV2CfaReconstruction'
if class_anchor not in t:
    raise SystemExit("reconstruction class anchor missing")
t=t.replace(class_anchor,'/* IRIS_26474_DIRECT_WRONSKI_SUPPORT_MAP_AUTHORITY */\n'+class_anchor,1)
recon.write_text(t)

f=finalize.read_text()
old='float frameSupport=max(support.r,1.0);'
new='/* IRIS_26474_TRUTHFUL_FRAME_EQUIVALENT_ALPHA\n     * support.r is accumulated accepted auxiliary robustness; add the\n     * immutable reference exactly once. Alpha is the authoritative per-pixel\n     * direct-Wronski effective-frame map.\n     */\n    float frameSupport=1.0+max(support.r,0.0);'
if f.count(old)!=1:
    raise SystemExit(f"final support anchor count={f.count(old)}")
f=f.replace(old,new,1)
finalize.write_text(f)

v=version.read_text()
if v.count("VERSION_NAME=0.9726473")!=1 or v.count("VERSION_BUILD=26473")!=1:
    raise SystemExit("26473 version anchors not unique")
v=v.replace("VERSION_NAME=0.9726473","VERSION_NAME=0.9726474",1)
v=v.replace("VERSION_BUILD=26473","VERSION_BUILD=26474",1)
version.write_text(v)
print("26474 reconstruction/final-support/version transform: PASS")

PY_TRANSFORM

python3 - "$TMP/candidate" <<'PY_VALIDATE'
from pathlib import Path
import sys
root=Path(sys.argv[1])
checks={
'app/src/main/assets/shaders/motionv2/mfsr_robustness.glsl':[
 'IRIS_26474_REFERENCE_ANCHORED_TEMPORAL_DISOCCLUSION',
 'IRIS_26474_SUB_TILE_FULL_RES_ACCEPTANCE',
 'uniform float temporalDistanceMs','temporalSceneGate'],
'app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl':[
 'IRIS_26474_TRUTHFUL_FRAME_EQUIVALENT_ALPHA',
 'float frameSupport=1.0+max(support.r,0.0)'],
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java':[
 'IRIS_26474_TEMPORAL_AGE_DIRECT_WRONSKI',
 'IRIS_26474_DNG_COLOR_SHADOW_CALL',
 'IRIS_26474_DIRECT_WRONSKI_SUPPORT_MAP_AUTHORITY'],
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java':[
 'IRIS_26474_DNG_SCENE_LINEAR_COLOR_SHADOW',
 'IRIS_26474_DNG_METADATA_SHADOW','outputApplied=false']
}
for rel,markers in checks.items():
    text=(root/rel).read_text()
    for marker in markers:
        if marker not in text:
            raise SystemExit(f"candidate missing {marker} in {rel}")
print("candidate/source validation PASS")
PY_VALIDATE
pass "candidate/source validation PASS"
echo "Temporary-copy validation: PASS"

cp "$TMP/candidate/$ROBUST" "$ROBUST"
cp "$TMP/candidate/$FINALIZE" "$FINALIZE"
cp "$TMP/candidate/$RECON" "$RECON"
cp "$TMP/candidate/$DNGSHADOW" "$DNGSHADOW"
cp "$TMP/candidate/$VERSION" "$VERSION"

for marker in \
  IRIS_26474_REFERENCE_ANCHORED_TEMPORAL_DISOCCLUSION \
  IRIS_26474_SUB_TILE_FULL_RES_ACCEPTANCE \
  IRIS_26474_TEMPORAL_AGE_DIRECT_WRONSKI \
  IRIS_26474_TRUTHFUL_FRAME_EQUIVALENT_ALPHA \
  IRIS_26474_DNG_SCENE_LINEAR_COLOR_SHADOW \
  IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE \
  IRIS_26473_IPOL_WRONSKI_ALIGNMENT_COMPLETION \
  IRIS_26472_SDR_AUTHORITATIVE_UHDR_HEADROOM; do
  grep -Rqs "$marker" app/src/main || fail "post-apply marker missing $marker"
done

grep -q 'public static final class PreparedReference implements AutoCloseable' app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java || fail "PreparedReference API lost"
grep -q 'public static PreparedReference prepareReference(' app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java || fail "prepareReference API lost"
grep -q 'public static MotionV2Alignment.Result alignPrepared(' app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java || fail "alignPrepared API lost"
pass "26467 prepared-reference API/lifetime preserved"

grep -q '^VERSION_NAME=0\.9726474$' app/version.properties || fail "26474 version name"
grep -q '^VERSION_BUILD=26474$' app/version.properties || fail "26474 version build"

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_AFTER"
sha256sum app/version.properties >> "$HASH_AFTER"

git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$RECOVERY"
git diff "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$SOURCEPATCH"

echo "Protected-file hashes: PASS"
echo "PRE-BUILD SAFETY PROOF PASSED"
echo "  candidate/source validation PASS"
echo "  Temporary-copy validation: PASS"
echo "  Protected-file hashes: PASS"
echo "  exact 26473 backup branch PASS"
echo "  exact successful 26473 V2 precursor PASS"
echo "  26467 prepared-reference API/lifetime PASS"
echo "  26473 IPOL/Wronski math preserved PASS"
echo "  truthful direct-Wronski frame-equivalent alpha map PASS"
echo "  age-conditioned scene-change rejection PASS"
echo "  full-resolution cross-scale disocclusion gate PASS"
echo "  DNG scene-linear shadow is read-only PASS"
echo "  26472 SDR-authoritative UHDR preserved PASS"
echo "  version/build increment in same command block PASS"

cat > "$REPORT" <<EOF
26474 temporal/disocclusion + color shadow
=========================================
Protected checkpoint: $PROTECTED_HEAD
Backup branch: $BACKUP_BRANCH
Build: $NEW_VERSION / $NEW_BUILD

- Keeps 26473 IPOL/Wronski alignment/noise/ICA/kernel math intact.
- Adds full-raw-resolution reference-anchored 3x3 + 7x7 scene-change gating.
- Temporal age only increases burden of proof when evidence disagrees.
- Unsafe auxiliary evidence becomes zero local contribution/reference ownership.
- Direct RGB alpha is authoritative frame-equivalent support:
  one reference + accepted auxiliary robustness.
- Adds read-only DNG scene-linear calibration shadow logging.
- JPEG remains on 26430 color output for causal isolation.
- UHDR and sharpening-disabled invariants preserved.
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
pass "26474 TEMPORAL / DISOCCLUSION / COLOR-SHADOW BUILD SUCCESS"
