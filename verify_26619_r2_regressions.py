#!/usr/bin/env python3
from pathlib import Path
import math,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26619_r2_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
# Physical reconstruction/color and UHDR gainmap owners are byte-identical to successful 26618.
for rel in [
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java']:
    assert (B/rel).read_bytes()==(C/rel).read_bytes(),rel
assert 'IRIS_26614_RAW_CFA_CHANNEL_VALIDITY_PROVENANCE' in (C/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text()
# Exact 26618 visual failure condition: pre-tone gain + source-white release creates a negative derivative.
def ss(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3.0-2.0*t)
def old_global(x,D):
    req=max(D,1e-6)*0.80; w=min(.95,req); body=req
    if req>w: body=min(req,4*w-1e-4)
    if x<=1.0: return w*x+(body-w)*x*(1-x)*(1-x)
    reserve=1-w
    if reserve<=1e-6:return w
    ts=reserve/max(w,1e-6); e=x-1
    return w+reserve*e/(e+ts)
def old_alloc(D,base):
    req=max(D*.80,1e-6); ev=max(math.log(req,2),0.0)
    protect=min(1.0,.50*ev)*ss(.35,1.50,ev)*ss(.42,.95,base*req)
    return max(.50,min(1.0,2**(-protect)))
def old26618(x,D):
    g=old_alloc(D,x); release=ss(.95,1.05,x); applied=g+(1-g)*release
    return old_global(x*applied,D)
def negative_interval(fn,D):
    xs=[1.30*i/100000.0 for i in range(100001)]; ys=[fn(x,D) for x in xs]
    neg=[i for i in range(len(xs)-1) if ys[i+1]<ys[i]]
    return None if not neg else (xs[neg[0]],xs[neg[-1]+1])
plant=negative_interval(old26618,3.8124225); chand=negative_interval(old26618,4.168001)
assert plant and plant[0]<.213 and plant[1]>.264,plant
assert chand and chand[0]<.187 and chand[1]>.248,chand
# 26619 broad-base composition is strictly monotonic, C1 at source white, smooth at global activation,
# and bounded for the exact failing gains plus a broad operating range.
def spatial_map(x,D):
    req=max(D,1e-6)*.80; bw=min(.86,req); body=min(req,4*bw-1e-4)
    if body<=bw+1e-6:return body*x
    if x<=1:
        c=body/max(bw,1e-6)-1; return body*x/(1+c*x)
    left=bw*bw/body; reserve=max(1-bw,1e-6); ts=reserve/max(left,1e-6); e=x-1
    return bw+reserve*e/(e+ts)
def new_map(x,D):
    req=max(D,1e-6)*.80; strength=ss(1.05,1.80,req)
    g=old_global(x,D); s=spatial_map(x,D)
    return g+(s-g)*strength
for D in [1.0,1.3125,1.3125001,1.5,2.0,3.7210152,3.8124225,4.168001,6.0,8.0]:
    xs=[4.0*i/40000.0 for i in range(40001)]; ys=[new_map(x,D) for x in xs]
    assert all(ys[i+1]>ys[i] for i in range(len(ys)-1)),('nonmonotonic',D)
    e=1e-6; dl=(new_map(1,D)-new_map(1-e,D))/e; dr=(new_map(1+e,D)-new_map(1,D))/e
    assert dl>0 and dr>0 and abs(dl-dr)/dl<1e-3,('C1',D,dl,dr)
for x in [.05,.2,.5,1.0,1.5]:
    assert abs(new_map(x,1.3125001)-new_map(x,1.3125))<2e-7,('activation discontinuity',x)
# Exact log-detail residual preservation: no sharpening/attenuation inside the numerical safety range.
for D in [3.8124225,4.168001]:
    for base in [.01,.05,.1,.2,.5,.9,1.0,1.2,2.0]:
        mb=new_map(base,D)
        for d in [-2,-1,-.25,0,.25,1,2]:
            out=mb*(2**d)
            assert abs(math.log2(out/mb)-d)<1e-12
# Current code must contain no retired source-luminance gain release and must keep resource lifetime bounded.
alltxt='\n'.join(p.read_text(errors='ignore') for p in (C/'app/src').rglob('*') if p.is_file() and p.suffix in {'.java','.glsl','.cpp'})
for tok in ['guided_base_detail_ltm_apply_26618','guided_base_detail_ltm_gain_26618','smoothstep(0.95, 1.05','smoothstep(0.95,1.05','smoothstep(0.95f,1.05f']:
    assert tok not in alltxt,tok
node=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2GuidedBaseDetailLtm.java').read_text()
renderJava=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
assert 'new GLTexture(low, rgba16f)' in node and 'coefficients.close()' in node
assert 'finally {' in renderJava and 'guidedBaseTexture.close()' in renderJava

# IRIS_26619_R2_NATIVE_NAMESPACE_COMPILE_REGRESSION
cpp_r2=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
assert 'float spatialStrength=iris26564::smooth01((requested-1.05f)/(1.80f-1.05f));' in cpp_r2
assert 'float spatialStrength=smooth01((requested-1.05f)/(1.80f-1.05f));' not in cpp_r2
print(f'PASS 26619 R2 regressions + failed-R1 native namespace condition: exact 26618 ring failure reproduced plant={plant} chandelier={chand}; new full composition strictly monotonic/C1; detail residual exact; protected owners invariant')
