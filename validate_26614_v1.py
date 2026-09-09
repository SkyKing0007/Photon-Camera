#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26614_v1.py BASE CANDIDATE')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); P=Path(__file__).resolve().parent
ALLOW=[x.strip() for x in (P/'V1_26614_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
b,c=H(B),H(C)
assert len(b)==1708 and len(c)==1708,(len(b),len(c))
assert set(b)==set(c),'candidate universe changed'
changed=sorted(k for k in b if b[k]!=c[k]); assert changed==sorted(ALLOW),changed
assert len(changed)==12
assert 'VERSION_NAME=0.9726613' in (B/'app/version.properties').read_text() and 'VERSION_BUILD=26613' in (B/'app/version.properties').read_text()
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726614' in v and 'VERSION_BUILD=26614' in v
# No generated build/.cxx can contaminate the authority-seeded source universe.
assert not any(k.startswith('app/build/') or k.startswith('app/.cxx/') for k in c)
# Canonical source-domain appearance math. White anchor cannot move downward with display gain.
def m(x,g):
    req=max(g,1e-6)*.8; a=min(.95,req); body=req
    if req>a: body=min(req,4*a-1e-4)
    x=max(x,0.0)
    if x<=1.0: return a*x+(body-a)*x*(1-x)*(1-x)
    r=1-a
    if r<=1e-6:return a
    t=r/max(a,1e-6); e=x-1.0
    return a+r*e/(e+t)
for g in [.5,.8,1.0,1.25,2.531,2.557,3.399,5.0,10.0]:
    xs=[i/1000 for i in range(0,20001)]; ys=[m(x,g) for x in xs]
    assert all(math.isfinite(y) for y in ys)
    assert all(ys[i+1]>=ys[i]-1e-12 for i in range(len(ys)-1)),g
    assert m(1.0,g)<=.9500001
    h=1e-6; dl=(m(1,g)-m(1-h,g))/h; dr=(m(1+h,g)-m(1,g))/h
    assert abs(dl-dr)<5e-5,(g,dl,dr)
    assert m(20,g)<1.0
render=(C/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
adap=(C/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text()
rj=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
view=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text()
cpp=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
enc=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text()
for s in [render,adap,rj,view,cpp]: assert 'iris26614MapMotionSdrFinalGuide' in s
assert 'mappedFinal = MotionV2Render.iris26614MapMotionSdrFinalGuide(guide, gain);' in view
assert 'public static final float IRIS_26614_SDR_WHITE_ANCHOR = 0.95f;' in rj
assert 'MotionV2Render.IRIS_26614_SDR_WHITE_ANCHOR' in enc
# 26613 display-domain knee must not remain the active Motion appearance owner.
for s in [render,adap,cpp]: assert 'iris26613MapSdrSourceFinal' not in s
# UHDR: SDR is appearance authority; Motion gain unity <= source white and headroom-only >1.
g=(C/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
for t in ['IRIS_26614_CANONICAL_APPEARANCE_UHDR_EXTENSION','sourceGuide=max(max3(hdrPositive),luminance(hdrPositive));','ratio=clamp(max(sourceGuide,1.0),1.0,safeMax);']:
    assert t in g,t
assert 'HEALTHY_HDR_MASTER_VS_SDR' not in rj
assert 'CANONICAL_SDR_PLUS_SOURCE_HEADROOM_ONLY' in rj
# Night retains legacy HDR/SDR quotient branch.
assert 'float hdrTargetScale=hdrExposureScale;' in g and 'ratio=clamp((hdr+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);' in g
# True2x CPU and embedded GPU use the same Motion headroom-only ratio.
assert cpp.count('sourceGuide=std::max(peak(hp),luma(hp));')==2
assert cpp.count('ratio=clampf(std::max(sourceGuide,1.f),1.f,contentMax);')==2
assert 'float sourceGuide=max(irisPeak(hp),irisLuma(hp));' in cpp and 'ratio=clamp(max(sourceGuide,1.0),1.0,contentMax);' in cpp
# RAW/CFA physical color validity is separate from total contribution weight.
sab=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
st=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
pp=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text()
for t in ['uValidityWeightScale','mat3 sourceValidity','validAccumulatedWeights','layout(location = 2) out vec4 oValidWeights','oColorAndRWeight = vec4(accumulatedColor, accumulatedWeight.r);','oWeightsGb = accumulatedWeight.gb;']:
    assert t in sab,t
for t in ['GLES30.GL_RGB10_A2','validityWeightScale26614','accumulatedValidity26614','sabreValidWeights = accumulatedValidity26614']:
    assert t in st,t
assert 'GLES30.GL_RGBA16F' not in st[st.index('IRIS_26614_RAW_CFA_CHANNEL_VALIDITY_OWNER'):st.index('IRIS_26614_RAW_CFA_CHANNEL_VALIDITY_OWNER')+700]
for t in ['uSabreValidWeights','loadSabreChannelValidity','centerChannelValidity','measuredColorProtection','validConsensusNormalizedChroma','channelInvalidity','componentRepair=clamp(channelInvalidity','physicalFalseColorScore','physicalAuthority']:
    assert t in pp,t
# Physical path is not vetoed by reconstructed-RGB realColorConfidence and has no hard score dead zone.
physical=pp[pp.index('/* Physical validity does not require a neutral target.'):pp.index('/* IRIS_26581_GAP_BACKGROUND_CHROMA_RESTORE')]
assert 'realColorConfidence' not in physical.split('float physicalFalseColorScore',1)[0]
assert 'smoothstep(0.10, 0.55, physicalFalseColorScore)' not in pp
assert 'clamp(physicalFalseColorScore, 0.0, 1.0)' in pp
# Existing temporal/Resolve/VGN ownership is explicitly unchanged by sidecar.
assert all(t in st for t in ['changesTemporalWeights=false','changesColorAccumulator=false','changesResolve=false','changesVgn=false'])
# DNG path exact invariance.
for line in (P/'V1_26614_DNG_BASE.sha256').read_text().splitlines():
    if not line.strip(): continue
    _,rel=line.split('  ',1); assert b[rel]==c[rel],rel
print('PASS 26614 semantic validation: exact authority/scope, canonical SDR/UHDR appearance, solver parity, RAW-CFA validity, true-color protection, DNG invariance')
