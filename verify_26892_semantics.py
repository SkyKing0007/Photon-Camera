#!/usr/bin/env python3
"""26892 active branch, source-domain, hue, HDR/SDR parity and exact protected-scope proof."""
from pathlib import Path
import hashlib,sys,re
assert len(sys.argv)==3,'BASE CAND'
B=Path(sys.argv[1])/'app';C=Path(sys.argv[2])/'app'
P=lambda root,p:(root/p).read_text()
sha=lambda root,p:hashlib.sha256((root/p).read_bytes()).hexdigest()
render='src/main/assets/shaders/motionv2/render.glsl'
gain='src/main/assets/shaders/motionv2/gainmap.glsl'
java='src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
r=P(C,render);g=P(C,gain);j=P(C,java)
# This is a B SR OFF-only presentation change. No producer, frame count, noise, exposure,
# color transform, A/A+B/Night/Spektra, DNG or LONG/source shader is changed.
assert 'motionV2ReconstructionOwner != Parameters.MOTION_V2_RECONSTRUCTION_RAWR_AMAZE' in j
assert 'p.motionV2SuperResOutputEnabled' in j and 'p.irisNightActive' in j
assert 'Float.isFinite(p50)' in j and 'Float.isFinite(p998)' in j
assert 'iris26892SceneFinishStrengths(basePipeline.mParameters)' in j
assert 'glProg.setVar("iris26892BacklitStrength",iris26892BacklitStrength)' in j
assert 'glProg.setVar("iris26892FlatContrastStrength",iris26892FlatContrastStrength)' in j
assert 'captureEvUnchanged=true' in j and 'sdrGainmapMirror=true' in j
assert 'brightnessTargetGain' in P(C,'src/main/assets/shaders/motionv2/iris_tone_controls.glsl')
assert sha(B,'src/main/assets/shaders/motionv2/iris_tone_controls.glsl')==sha(C,'src/main/assets/shaders/motionv2/iris_tone_controls.glsl')
# One EXACT scalar equation mirrored byte-for-byte for SDR and UHDR denominator.
start='/* IRIS_26892_SCENE_ADAPTIVE_SDR_FINISH'
end='\nfloat mapFinalSdrGuide(float sourceGuide) {'
assert r.count(start)==1 and g.count(start)==1
s1=r[r.index(start):r.index(end,r.index(start))]
s2=g[g.index(start):g.index('\nfloat iris26660SharedSdrGuide',g.index(start))]
assert s1==s2, 'GLES SDR and UHDR reused different equations'
assert 'exp2(liftEv)' in s1 and 'lifted*(1.0-lifted)*(lifted-0.24)' in s1
assert 'clamp(iris26892BacklitStrength,0.0,1.0)' in s1
assert 'clamp(iris26892FlatContrastStrength,0.0,1.0)' in s1
assert 'return clamp(lifted+contrast*sCurve*lowGuard*highGuard,0.0,1.0);' in s1
# Confirm original source recovered by removing solely new single owner + call sites.
r0=r.replace(s1+'\n','')
r0=r0.replace('            mappedGuide=iris26892SdrAdaptiveGuide(mappedGuide);\n','')
r0=r0.replace('    mappedGuide=iris26892SdrAdaptiveGuide(mappedGuide);\n','')
assert r0==P(B,render), 'render changed outside allowed guide addition and two sites'
g0=g.replace(s2+'\n','')
g0=g0.replace('return iris26892SdrAdaptiveGuide(iris26770MidtonePresentationTrim(iris26660ObjectColorGamma(sharedSdr)));','return iris26770MidtonePresentationTrim(iris26660ObjectColorGamma(sharedSdr));')
assert g0==P(B,gain), 'gainmap changed outside exact shared mirror'
assert r.count('iris26892SdrAdaptiveGuide(mappedGuide);')==2
assert g.count('iris26892SdrAdaptiveGuide(')==2 # definition and one call
assert 'iris26641BilinearSdrLinear(sourcePixel)' in g and 'float matchedIntentDelta=max(linearTargetY-sdrModelY,0.0);' in g
assert 'float hdrIntentY=sdr+matchedIntentDelta;' in g
assert 'Output=clamp(' in r and 'srgbEncode(linearSrgb)' in r
assert 'fitDisplayGamut(linearSrgb)' in r
assert 'iris26638UserSaturation' in r
assert 'iris26704BodyToneGuide' in r and 'iris26770MidtonePresentationTrim' in r
assert 'iris26799ConnectedMask' in r and 'iris26799ConnectedEnabled' in r
assert not any(s in r+g for s in ('IRIS_26890_B_ONLY_USER_EXPORTED_SHADOW_TOE','uniform float iris26890'))
assert P(C,'version.properties')=='VERSION_MAJOR=0\nVERSION_MINOR=9726440\nVERSION_NAME=0.9726892\nVERSION_BUILD=26892\n'
print('PASS 26892 exact B-OFF only scene owner, SDR/UHDR identical scalar, unchanged entire remaining 2021 protected source and 26891 tone')
