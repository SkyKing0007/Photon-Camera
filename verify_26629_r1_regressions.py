#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, random, re, sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26629_r1_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
# Permanent R1 NDK compiler regression remains applicable because the JNI source changes again.
nat=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
if 'float y=luma(center)' in nat: raise SystemExit('FAIL permanent 26628 R1 NDK regression: local float y shadows pixel-coordinate y')
if nat.count('float lum=luma(center)')!=2: raise SystemExit('FAIL permanent 26628 R1 NDK regression: expected exactly two lum declarations')
# Permanent R2 Java regression is inherited byte-identical.
auxrel='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/AuxButtonsLayout.java'
if sha(B/auxrel)!=sha(C/auxrel): raise SystemExit('FAIL inherited R2 Java repair changed')
aux=(C/auxrel).read_text()
for tok in ['if (!(child instanceof TextView)) continue;','TextView button = (TextView) child;']:
    if tok not in aux: raise SystemExit(f'FAIL permanent R2 Java type regression {tok}')
if re.search(r'\bButton\b',aux): raise SystemExit('FAIL permanent R2 Java regression: standalone Button survived')
# All inherited 26628 color owners/protections must remain exact.
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/IrisJpegColorSolver.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisNightUltraHdr.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
]:
    if sha(B/rel)!=sha(C/rel): raise SystemExit(f'FAIL inherited 26628 authority changed {rel}')
solver=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/IrisJpegColorSolver.java').read_text()
for bad in ['IRIS_26627_DUAL_ILLUMINANT_FORWARD_PLACEHOLDER_REJECT','forwardDelta <= 1.0e-6f','Build.MANUFACTURER','Build.MODEL']:
    if bad in solver: raise SystemExit(f'FAIL stale DNG color regression {bad}')
ads=(C/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text()
for bad in ['1.32','1.12','coherentColorActivation','MAX_WEAK_CHROMA_GAIN']:
    if bad in ads: raise SystemExit(f'FAIL stale adaptive color authority {bad}')
# Android Gainmap metadata remains scalar/equal-channel; ALPHA_8 gain image remains authoritative.
ultra=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java').read_text()
renderj=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
for tok in ['gainmap.setRatioMin(MIN_RATIO, MIN_RATIO, MIN_RATIO);','gainmap.setRatioMax(safeMax, safeMax, safeMax);',
            'gainmap.setGamma(1.0f, 1.0f, 1.0f);','gainmap.setEpsilonSdr(EPSILON, EPSILON, EPSILON);',
            'gainmap.setEpsilonHdr(EPSILON, EPSILON, EPSILON);']:
    if tok not in ultra: raise SystemExit(f'FAIL scalar Android Gainmap metadata {tok}')
if 'Bitmap.Config.ALPHA_8' not in renderj: raise SystemExit('FAIL Motion UHDR gain map is no longer single-plane ALPHA_8')
# Fixed-luminance color math fixture mirrors shader/CPU constants using stdlib only.
W=(0.22897456,0.69173852,0.07928691)
def clamp(x,a=0.0,b=1.0): return min(max(x,a),b)
def smooth(a,b,x):
    t=clamp((x-a)/(b-a)); return t*t*(3.0-2.0*t)
def restore(rgb):
    rgb=tuple(clamp(x) for x in rgb); y=clamp(sum(rgb[i]*W[i] for i in range(3)))
    c=tuple(x-y for x in rgb); rel=math.sqrt(sum(x*x for x in c))/(y+0.05)
    gain=1.0+0.20*smooth(.025,.055,y)*(1.0-smooth(.13,.36,y))*smooth(.035,.11,rel)*(1.0-.65*smooth(.38,.72,rel))
    lim=1.0e6
    for x in c:
        if x>1e-8: q=max(1.0,(1.0-y)/x)
        elif x<-1e-8: q=max(1.0,y/(-x))
        else: q=1.0e6
        lim=min(lim,q)
    applied=min(gain,lim); out=tuple(clamp(y+x*applied) for x in c)
    return y,out,gain,applied
rng=random.Random(26629); worst=0.0
for _ in range(30000):
    rgb=(rng.random(),rng.random(),rng.random()); y,out,requested,applied=restore(rgb)
    yo=sum(out[i]*W[i] for i in range(3)); worst=max(worst,abs(yo-y))
    if not all(-1e-7<=x<=1.0000001 for x in out): raise SystemExit('FAIL color restore gamut fixture')
    if requested<0.999999 or requested>1.200001 or applied<0.999999: raise SystemExit('FAIL color restore gain bound fixture')
if worst>1e-6: raise SystemExit(f'FAIL luminance lock fixture worst={worst}')
# Bright pixels receive no chroma restoration by construction.
for rgb in [(0.5,0.4,0.3),(0.9,0.5,0.2),(0.4,0.4,0.4)]:
    y,out,req,app=restore(rgb)
    if y>=0.36 and abs(req-1.0)>1e-9: raise SystemExit('FAIL bright chroma taper fixture')
# True2x CPU/GPU constants and ordering must remain exact parity.
for tok in ['0.025f,0.055f','0.13f,0.36f','0.035f,0.11f','0.38f,0.72f','0.65f','0.20f']:
    if tok not in nat: raise SystemExit(f'FAIL true2x CPU restore constant {tok}')
for tok in ['0.025,0.055','0.13,0.36','0.035,0.11','0.38,0.72','0.65','0.20']:
    if tok not in nat: raise SystemExit(f'FAIL true2x GPU restore constant {tok}')
# UHDR body floor parity and Night non-interference.
g=(C/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
if g.count('bodyLuminanceRatio=1.25')!=1: raise SystemExit('FAIL Motion gainmap body floor count')
if nat.count('sourceGuide,1.25')!=3: raise SystemExit('FAIL Motion true2x CPU/GPU body floor count')
nightrel='app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisNightUltraHdr.java'
if sha(B/nightrel)!=sha(C/nightrel): raise SystemExit('FAIL Night UHDR changed')
print(f'PASS 26629 regressions: inherited R1/R2/DNG/color/Night protections; scalar Android gainmap; luminance-lock math worstYError={worst:.3e}; true2x CPU/GPU color+UHDR parity')
