#!/usr/bin/env python3
from pathlib import Path
import math,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26621_r1_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])

def old20(x,D):
    req=max(D,1e-6)*0.80; white=min(0.95,req); body=req
    if req>white: body=min(req,4.0*white-1e-4)
    if x<=1.0:
        om=1.0-x; return white*x+(body-white)*x*om*om
    reserve=1.0-white
    if reserve<=1e-6:return white
    tail=reserve/max(white,1e-6); e=x-1.0
    return white+reserve*e/(e+tail)

def new21(x,D):
    req=max(D,1e-6)*0.80; white=min(0.95,req); body=req
    if req>white: body=min(req,4.0*white-1e-4)
    ratio=max(body/max(white,1e-6)-1.0,0.0)
    if x<=1.0:
        om=1.0-x
        cubic=white*x+(body-white)*x*om*om
        rational=body*x/(1.0+ratio*x)
        return 0.5*(cubic+rational)
    rationalSlope=body/((1.0+ratio)*(1.0+ratio))
    bodySlope=0.5*(white+rationalSlope)
    reserve=max(1.0-white,0.0)
    if reserve<=1e-6:return white
    tail=reserve/max(bodySlope,1e-6); e=x-1.0
    return white+reserve*e/(e+tail)

def deriv(fn,x,D,h=1e-5): return (fn(x+h,D)-fn(x-h,D))/(2*h)

# Exact 26620/26614 chandelier failure remains reproduced and must not be accepted as merely monotonic.
D_chandelier=5.683
old_sep=old20(0.75,D_chandelier)-old20(0.60,D_chandelier)
assert old_sep < 0.005,old_sep
old_min=min(deriv(old20,0.001+i*(0.998/4000),D_chandelier) for i in range(4001))
assert old_min < 0.01,old_min

# 26621 global tone: exact black, strict monotonicity, meaningful body slope, useful chandelier separation,
# C1 source-white junction, and increasing >1 HDR tail. This is stronger than the old monotonic-only test.
for D in [0.5,1.0,1.1875,1.5,2.0,3.0,3.114,3.8124225,4.168001,5.683,6.0,8.0]:
    assert abs(new21(0.0,D)) < 1e-12,(D,new21(0,D))
    xs=[4.0*i/24000 for i in range(24001)]; ys=[new21(x,D) for x in xs]
    assert all(ys[i+1] > ys[i]-1e-12 for i in range(len(ys)-1)),('nonmonotonic',D)
    body_min=min(deriv(new21,0.001+i*(0.998/5000),D) for i in range(5001))
    assert body_min >= 0.19,(D,body_min)
    eps=1e-5; dl=(new21(1.0,D)-new21(1.0-eps,D))/eps; dr=(new21(1.0+eps,D)-new21(1.0,D))/eps
    assert dl>0 and dr>0 and abs(dl-dr)/max(dl,dr)<2e-3,('C1',D,dl,dr)
    assert new21(1.1,D)>new21(1.0,D) and new21(2.0,D)>new21(1.1,D)
assert new21(0.75,D_chandelier)-new21(0.60,D_chandelier) > 0.030

rj=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
render=(C/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
global_log=(C/'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl').read_text()
down=(C/'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26621.glsl').read_text()
remap=(C/'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl').read_text()
acc=(C/'app/src/main/assets/shaders/motionv2/local_laplacian_accumulate_26621.glsl').read_text()
rec=(C/'app/src/main/assets/shaders/motionv2/local_laplacian_reconstruct_26621.glsl').read_text()
cpp=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
params=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text()
enc=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text()
adapt=(C/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text()
matcher=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text()

# Cross-owner global-tone parity markers and constants. Matcher/adaptive/render/local seed/CPU/GPU publication
# must all carry the same 0.80 request scale, 0.95 white anchor and 50/50 cubic+rational body.
for text in [render,global_log,adapt,cpp]:
    assert ('0.95' in text and ('0.5*(' in text or '0.5f*(' in text or '0.5f * (' in text or '0.5 * (' in text)), 'global tone constants missing'
for tok in ['MotionV2Render.iris26621MapMotionSdrFinalGuide(guide, gain)','IRIS_26621_SOLVER_RENDER_TONE_PARITY']:
    assert tok in matcher,tok
for tok in ['requestedFinalGain = Math.max(brightnessTargetGain, 1.0e-6f)','* OUTPUT_EXPOSURE_SCALE','0.5f * (cubic + rational)']:
    assert tok in rj,tok
# Local stages have no second displayGain/outputExposureScale owner after the global-log seed.
for text,name in [(down,'downsample'),(remap,'remap'),(acc,'accumulate'),(rec,'reconstruct')]:
    assert 'displayGain' not in text and 'outputExposureScale' not in text,f'duplicate exposure in {name}'

# Fast Local-Laplacian remap is continuous, strictly monotonic, and never amplifies fine/detail differences.
sigma=0.35; edge=0.94
def remap_scalar(x,g):
    d=x-g; a=abs(d); m=a if a<=sigma else sigma+edge*(a-sigma)
    return g + (-m if d<0 else m)
for g in [-6,-4,-2,-1,-0.3,0]:
    xs=[-8+i*(9/9000) for i in range(9001)]
    ys=[remap_scalar(x,g) for x in xs]
    assert all(ys[i+1]>=ys[i]-1e-12 for i in range(len(ys)-1))
    # Small/detail differences are exact identity; larger differences are compressed, not boosted.
    for d in [-0.30,-0.1,0.0,0.1,0.30]: assert abs((remap_scalar(g+d,g)-g)-d)<1e-12
    for d in [-2,-1,1,2]: assert abs(remap_scalar(g+d,g)-g) <= abs(d)+1e-12
# Continuity at sigma.
for sign in [-1,1]:
    a=remap_scalar(sign*(sigma-1e-7),0); b=remap_scalar(sign*(sigma+1e-7),0)
    assert abs(a-b)<5e-7

# Reference-slice interpolation is a partition of unity over the entire active mapped log range.
rmin,rmax,n=-6.0,0.0,12; step=(rmax-rmin)/(n-1)
refs=[rmin+i*step for i in range(n)]
for i in range(6001):
    x=rmin+(rmax-rmin)*i/6000
    weights=[max(1.0-abs(x-r)/step,0.0) for r in refs]
    assert abs(sum(weights)-1.0)<2e-12,(x,sum(weights))
    assert sum(w>0 for w in weights)<=2

# Matched REDUCE/EXPAND preserve constants and use one fixed phase; no atlas/tile/nearest reconstruction.
assert 'sum*(1.0/256.0)' in down
for text in [acc,rec]:
    assert 'wm=0.125;wc=0.750;wp=0.125' in text and 'wm=0.0;wc=0.5;wp=0.5' in text
for forbidden in ['GL_NEAREST','MAP_LONG_EDGE','MAP_MIN_EDGE','ivec2 tile','floor(level0Coord/','sourcePixel*0.5']:
    assert forbidden not in rj+render+down+remap+acc+rec,forbidden
# 26620 visible block mechanism is physically removed, not merely unreferenced.
for rel in [
'app/src/main/assets/shaders/motionv2/local_laplacian_seed_26620.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26620.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_correction_26620.glsl']:
    assert (B/rel).is_file() and not (C/rel).exists(),rel

# Uniform-field/black protection: global-log floor cannot lift exact black because final local blend is zero
# until the mapped global result reaches 0.03; RGB application remains one common scalar.
assert 'float localStrength=smoothstep(0.030,0.100,globalMapped);' in render
assert 'linearSrgb=sourceRgb*(mappedGuide/sourceGuide);' in render
assert 'else{\n            linearSrgb=sourceRgb;' in render
for g in [0.0,0.005,0.015,0.029999]:
    t=max(0.0,min(1.0,(g-0.03)/(0.10-0.03))); strength=t*t*(3-2*t)
    assert strength==0.0
# Local target is bounded to <=1 in stored log and true2x consumers; no local stage can invent >1 SDR RGB.
assert 'exp2(clamp(localLog,-12.0,0.0))' in render
assert 'return std::exp2(clampf(logv,-12.f,0.f));' in cpp

# No per-channel local tone/color operation; adaptive-color runtime change is limited to the shared tone predictor.
b_adapt=(B/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text()
def strip_func(text,name):
    m=re.search(r'float\s+'+re.escape(name)+r'\s*\([^)]*\)\s*\{',text); assert m,name
    brace=text.find('{',m.start()); depth=0
    for i in range(brace,len(text)):
        if text[i]=='{': depth+=1
        elif text[i]=='}':
            depth-=1
            if depth==0: return text[:m.start()]+'<TONE_FUNCTION>'+text[i+1:]
    raise AssertionError(name)
base_norm=strip_func(b_adapt,'iris26614MapMotionSdrFinalGuide').replace('iris26614MapMotionSdrFinalGuide','<TONE_CALL>')
cand_norm=strip_func(adapt,'iris26621MapMotionSdrFinalGuide').replace('iris26621MapMotionSdrFinalGuide','<TONE_CALL>')
assert base_norm==cand_norm,'adaptive-color behavior changed outside shared tone predictor'
assert 'linearSrgb=sourceRgb*(mappedGuide/sourceGuide);' in render

# UHDR/DNG/image-formation remain exact successful-26620 bytes.
for rel in [
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java']:
    assert (B/rel).read_bytes()==(C/rel).read_bytes(),rel

# True2x shares the exact full-resolution absolute local target; CPU/GPU use linear sampling and same global map.
for tok in ['IRIS_26621_TRUE2X_SHARED_LOCAL_TONE_MAP','localToneMappedGuide','iris26621MapMotionSdrFinalGuide','IRIS_26621_SINGLE_GLOBAL_PLUS_LOCAL_TONE_OWNER_TRUE2X_CPU']:
    assert tok in cpp,tok
for tok in ['IRIS_26621_TRUE2X_LOCAL_LAPLACIAN_GPU_SHARED_FIELD','irisLocalToneMappedGuide','IRIS_26621_SINGLE_TONE_OWNER_TRUE2X_GPU']:
    assert tok in cpp,tok
assert 'glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);' in cpp
# Exact 26619 native compile regression remains guarded: the inherited spatial-support calls are namespace-qualified.
for tok in ['iris26564::smooth01((guideBlockY-0.015f)/0.055f)','iris26564::smooth01((blockPeak-0.72f)/0.20f)']:
    assert tok in cpp,tok

# GPU lifetime/retained-buffer ownership: transient remap/band/guide textures are closed and retained map cleared after publication.
for tok in ['IRIS_26621_LOCAL_LAPLACIAN_PEAK_LIFETIME','for (GLTexture texture : remap)','bands[level] = null','guide[level] = null','finalTone.textureBuffer(scalar, true)']:
    assert tok in rj,tok
for tok in ['parameters.motionV2LocalToneLogMap = null;','parameters.motionV2LocalToneLogWidth = 0;','parameters.motionV2LocalToneLogHeight = 0;']:
    assert tok in enc,tok

# No rejected later presentation owners remain.
owned='\n'.join([rj,render,global_log,down,remap,acc,rec,cpp,params,enc,adapt,matcher])
for forbidden in ['guided_base_detail_ltm','adaptive_wronski','IRIS_26618_GUIDED','IRIS_26619_GUIDED','motionV2LocalLaplacianMap']:
    assert forbidden not in owned,forbidden
print(f'PASS 26621 regressions: old highlight plateau reproduced sep={old_sep:.6f}/minSlope={old_min:.6f}; new global tone minSlope>=0.19 + C1/>1 headroom; true Local-Laplacian remap monotonic/detail-neutral/reference partition; 26620 block owner removed; black/color/UHDR/true2x/lifetime/native regression guards PASS')
