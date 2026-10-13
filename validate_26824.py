#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,math,re
B,C=map(Path,sys.argv[1:3])
RENDER='app/src/main/assets/shaders/motionv2/render.glsl'
GAIN='app/src/main/assets/shaders/motionv2/gainmap.glsl'
JNI='app/src/main/cpp/motionv2_jpeg444_jni.cpp'
MVR='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
ENC='app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java'
STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
SABRE='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
POST='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
SP='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt'
CLASS='app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl'
PROP='app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl'
A={RENDER,GAIN,JNI,MVR,ENC,'app/version.properties'}
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {p.relative_to(r).as_posix():h(p) for p in (r/'app').rglob('*') if p.is_file()}
def fn(text,name):
    m=re.search(r'(?:^|\n)[^\n{};]*\b'+re.escape(name)+r'\s*\([^;{}]*\)\s*\{',text,re.M)
    assert m,(name,'missing')
    s=m.start()+ (1 if text[m.start():].startswith('\n') else 0); b=text.find('{',m.start()); depth=0
    for i in range(b,len(text)):
        if text[i]=='{': depth+=1
        elif text[i]=='}':
            depth-=1
            if depth==0:return text[s:i+1]
    raise AssertionError((name,'unterminated'))
def smooth(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3.0-2.0*t)
def signed_strength(p50,p95,p99):
    legacy=(1-smooth(.025,.070,p50))*(1-smooth(.080,.180,p95))*smooth(.120,.220,p99)
    adapt=smooth(.090,.170,p50)*smooth(.280,.420,p95)*smooth(.420,.580,p99)
    return max(-1.0,min(1.0,max(0,min(1,legacy))-.85*max(0,min(1,adapt))))
def curve(y,s):
    if s<0:
        w=smooth(.055,.180,y)*(1-smooth(.500,.760,y)); return y+(y*y-y)*(.24*(-s)*max(0,min(1,w)))
    if s<=1e-7 or y<=0 or y>=.35:return y
    g=1-.28*s; toe=.35*(max(0,min(1,y/.35))**g); return y+(toe-y)*smooth(.004,.018,y)
b,c=U(B),U(C); changed={p for p in set(b)|set(c) if b.get(p)!=c.get(p)}
assert changed==A,(sorted(changed),sorted(A)); assert len(b)==1783 and len(c)==1783
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726824' in v and 'VERSION_BUILD=26824' in v
# Exact inherited architecture outside render/tone scope.
for rel in (STACK,SABRE,POST,SP,CLASS,PROP): assert h(B/rel)==h(C/rel),rel
for rel,toks in {
STACK:['IRIS_26823_PHASE_VALID_CLIPPED_NEUTRAL_ATTENUATION','clippedNeutral26823=PHASE_VALID_BRIGHT_NEUTRAL_ATTENUATION'],
SABRE:['IRIS_26819_NORMAL_CLIPPED_CHROMA_VALIDITY_OWNER'],
POST:['IRIS_26818_STRICTER_INDEPENDENT_CHROMA_MAGNITUDE_PROOF'],
SP:['IRIS_26821_DNG_ALL_FOUR_PHASE_NEUTRAL_COHERENCE_OWNER'],
CLASS:['IRIS_26822_SINGLE_OWNER_FALSE_COLOR_CONFIDENCE','IRIS_26822_CONTINUOUS_REAL_MATERIAL_PROTECTION'],
PROP:['IRIS_26822_CONNECTED_FLOOD_RETIRED_PASS_THROUGH'],
}.items():
    text=(C/rel).read_text()
    for token in toks: assert token in text,(rel,token)
# Preserve 26822 final false-color mutation exactly despite render file being in tone allowlist.
br=(B/RENDER).read_text(); cr=(C/RENDER).read_text()
assert fn(br,'iris26822ApplySingleOwnerFalseColor')==fn(cr,'iris26822ApplySingleOwnerFalseColor')
assert fn(br,'iris26822FalseColorConfidence')==fn(cr,'iris26822FalseColorConfidence')
# 26660 gamma and 26792 base body contrast remain exact; gamma=2.5 is not retuned.
for name in ('iris26660ObjectColorGamma','iris26770MidtonePresentationTrim'):
    assert fn(br,name)==fn(cr,name),name
bg=(B/GAIN).read_text(); cg=(C/GAIN).read_text()
for name in ('iris26660ObjectColorGamma','iris26770MidtonePresentationTrim'):
    assert fn(bg,name)==fn(cg,name),('gain',name)
assert 'const float gammaValue=2.50;' in cr and 'const float gammaValue=2.50;' in cg
# New 26824 ownership and curve invariants.
mr=(C/MVR).read_text(); jni=(C/JNI).read_text(); enc=(C/ENC).read_text()
for token in ['IRIS_26824_ADAPTIVE_BODY_S_CURVE','IRIS_26824_MOTION_SATURATION_SCALE = 0.95f','IRIS_26824_BODY_S_MAX_STRENGTH = 0.85f','brightBody = iris26623Smoothstep(0.090f, 0.170f, p50)','bodyRange = iris26623Smoothstep(0.280f, 0.420f, p95)','upperSupport = iris26623Smoothstep(0.420f, 0.580f, p99)','maxAdditionalQuadraticBlend=0.24']:
    assert token in mr,token
for text,label in ((cr,'render'),(cg,'gainmap'),(jni,'jni')):
    assert 'IRIS_26824_ADAPTIVE_BODY_S_CURVE' in text,(label,'marker')
    for token in ['0.055','0.180','0.500','0.760','0.24']:
        assert token in text,(label,token)
assert 'p.bodyToneStrength=clampf((float)bodyToneStrength,-1.f,1.f);' in jni
assert 'MotionV2Render.IRIS_26824_MOTION_SATURATION_SCALE' in enc
assert 'parameters.motionV2Active && toneSettings != null' in enc
# Exact supplied-scene regression: indoor is identity, 190437 gets strong but bounded S-curve.
s1=signed_strength(.05008096,.20409603,.7746914); s2=signed_strength(.04037413,.3566794,.8370077); sout=signed_strength(.171922,.40355465,.5808587)
assert abs(s1)<1e-8 and abs(s2)<1e-8,(s1,s2)
assert -0.83 < sout < -0.80,sout
assert abs(curve(.05,sout)-.05)<1e-8
assert .205 < curve(.25,sout) < .220
assert .44 < curve(.50,sout) < .46
assert abs(curve(.75,sout)-.75)<0.001
# Exposure/highlight authority and existing body-contrast control are frozen.
for token in ['OUTPUT_EXPOSURE_SCALE = 0.80f','IRIS_26653_SINGLE_FINAL_HIGHLIGHT_TONE','iris26792SdrBodyContrast']:
    assert token in mr,token
# No allocation/lifecycle changes in changed owners.
for rel in (MVR,JNI,ENC):
    bt=(B/rel).read_text(); ct=(C/rel).read_text()
    for token in ['new GLTexture','glGenTextures','glGenBuffers','ByteBuffer.allocateDirect']:
        assert bt.count(token)==ct.count(token),(rel,token,bt.count(token),ct.count(token))
# No DNG, capture, merge, noise or false-color source is in the changed set by construction.
print('PASS 26824 exact 6-path scope: adaptive Lightroom-reference body S curve + relative 0.95 Motion saturation; 26823 false-color, capture/exposure, Sabre/VGN/DNG/merge/denoise and gamma-2.5 mechanics protected')
