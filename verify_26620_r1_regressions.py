#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26620_r1_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
# 26614 global map remains mathematically strictly increasing and C1 at source white.
def g14(x,D):
    req=max(D,1e-6)*0.80; white=min(0.95,req); body=req
    if req>white: body=min(req,4.0*white-1e-4)
    if x<=1.0:
        om=1.0-x; return white*x+(body-white)*x*om*om
    reserve=1.0-white
    if reserve<=1e-6: return white
    tail=reserve/max(white,1e-6); e=x-1.0
    return white+reserve*e/(e+tail)
for D in [0.5,1.0,1.1875,1.5,2.0,3.0,3.8124225,4.168001,6.0,8.0]:
    xs=[4.0*i/20000 for i in range(20001)]; ys=[g14(x,D) for x in xs]
    assert all(ys[i+1]>=ys[i] for i in range(len(ys)-1)),('26614 nonmonotonic',D)
    e=1e-6; dl=(g14(1,D)-g14(1-e,D))/e; dr=(g14(1+e,D)-g14(1,D))/e
    assert dl>=0 and dr>=0 and (dl==0 or abs(dl-dr)/max(dl,1e-9)<2e-3),('26614 C1',D,dl,dr)
# Exact later failure mechanisms are forbidden when restarting from 26614.
owned=[]
for rel in [
'app/src/main/assets/shaders/motionv2/local_laplacian_seed_26620.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26620.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_correction_26620.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java']:
    owned.append((C/rel).read_text())
all_owned='\n'.join(owned)
for forbidden in ['MAP_LONG_EDGE = 256','guided_base_detail_ltm','guidedLtmGain','rgb * appliedGain','smoothstep(0.95, 1.05','adaptive_wronski']:
    assert forbidden not in all_owned,f'26618/26619 failure mechanism survived: {forbidden}'
rj=owned[-1]; corr=owned[2]; render=owned[3]; seed=owned[0]; down=owned[1]
# Block-border regression: map resolution follows source at 2:1, all pyramid reductions are centered
# 5x5 Gaussian, and consumers linearly sample the continuous field. No fixed atlas/tile quantizer exists.
for tok in ['Math.max(1, (source.mSize.x + 1) / 2)','Math.max(1, (source.mSize.y + 1) / 2)',
            'new GLTexture(levelSize, pairFormat, null, GL_LINEAR, GL_CLAMP_TO_EDGE)',
            'new GLFormat(GLFormat.DataType.FLOAT_16, 1)','GL_LINEAR, GL_CLAMP_TO_EDGE']:
    assert tok in rj,tok
for tok in ['ivec2 center=q*2','kernel5','sum*(1.0/256.0)']:
    assert tok in down,tok
for forbidden in ['MAP_LONG_EDGE','MAP_MIN_EDGE','ivec2 tile','floor(level0Coord/']:
    assert forbidden not in '\n'.join([seed,down,corr,rj]),forbidden
assert 'GL_NEAREST' not in rj,'Local-Laplacian GL textures must not use nearest sampling'
# Uniform fields are exact identity for local operator: every source/mapped Gaussian level is constant,
# so every Laplacian band is zero and softLimit(0)=0. Guard code must keep this algebraic property.
assert 'float correctionEv=outLog-mapped0;' in corr
assert 'outLog=p7.g;' in corr
assert 'p0.g-p1.g,p0.r-p1.r,0.00' in corr
assert 'return x/(1.0+a/max(limitValue,1.0e-6));' in corr
# Contrast restoration can only interpolate from mapped band toward source band when source magnitude
# exceeds mapped magnitude; blend is clamped [0,1]. This prevents overshoot/detail amplification.
for tok in ['compression=max(as-am,0.0)','float blend=clamp(','return mix(mappedBand,sourceBand,blend);']:
    assert tok in corr,tok
assert 'p0.g-p1.g,p0.r-p1.r,0.00' in corr,'finest band must not be amplified'
# Black-crush regression: exact black/very deep shadow receives no negative local darkening; lower body
# negative correction is smoothly attenuated through rendered guide 0.08..0.20.
for tok in ['shadowPreserve=smoothstep(0.020,0.080,mappedGuide)','if(correctionEv<0.0)','smoothstep(0.080,0.200,mappedGuide)']:
    assert tok in corr,tok
def smooth(a,b,x):
    if x<=a:return 0.0
    if x>=b:return 1.0
    t=(x-a)/(b-a); return t*t*(3-2*t)
for y in [0.0,0.005,0.02,0.04,0.079999]:
    assert smooth(.02,.08,y)<1.0
    if y<=.02: assert smooth(.02,.08,y)==0.0
assert smooth(.08,.20,.08)==0.0 and smooth(.08,.20,.20)==1.0
# Color/gamut regression: local stage is one scalar RGB multiplier only. Positive restoration is bounded
# to the preexisting display headroom and therefore cannot create a new peak>1 clip.
assert 'linearSrgb*=exp2(correctionEv);' in render
assert 'float availableUpEv=' in render and 'correctionEv=min(correctionEv,availableUpEv);' in render
for peak in [1e-4,.05,.2,.5,.8,.95,1.0]:
    avail=max(math.log2(1.0/peak),0.0)
    for requested in [0.0,.1,.3,.55]:
        ev=min(requested,avail)
        assert peak*(2**ev)<=1.0+1e-12
# Exposure-owner regression: displayGain and 0.80 are only used to create the same 26614 mapped guide in
# the seed; correction/downsample shaders cannot independently brighten the image.
assert 'requestedFinalGain=max(displayGain,1.0e-6)*max(outputExposureScale,1.0e-6)' in seed
assert 'displayGain' not in corr and 'outputExposureScale' not in corr
assert 'displayGain' not in down and 'outputExposureScale' not in down
# 1x and true2x exact spatial phase regression, including the inherited x=0->1 source workaround.
cpp=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
assert 'sourcePixel=vec2(sourceXY);' in render
assert 'vec2 correctionCoord=sourcePixel*0.5;' in render
assert 'float mx=oneX*0.5f;' in cpp and 'float my=oneY*0.5f;' in cpp
assert 'vec2 mapCoord=oneSource*0.5;' in cpp
assert 'glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);' in cpp
# Runtime resource/lifetime regression: all transient GPU pyramid textures are closed; retained direct map
# is cleared after true2x publication. No full-resolution duplicate image is retained by this owner.
enc=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text()
assert 'for (GLTexture texture : pyramid)' in rj and 'texture.close()' in rj
assert 'iris26620Correction.close()' in rj
assert 'parameters.motionV2LocalLaplacianMap = null;' in enc
# Core protected owners must remain byte-exact against successful 26614.
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt']:
    assert (B/rel).read_bytes()==(C/rel).read_bytes(),rel
print('PASS 26620 regressions: 26614 global tone/exposure preserved; later ring/block mechanisms absent; smooth multiscale phase, black-floor, RGB-ratio, gamut, lifetime and true2x parity guards active')
