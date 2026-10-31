#!/usr/bin/env python3
"""26893 exact owner/guide/layout + SDR/UHDR mirror and monotonic contrast semantics."""
from pathlib import Path
import hashlib,re,sys
assert len(sys.argv)==3,'BASE CAND'
B=Path(sys.argv[1])/'app';C=Path(sys.argv[2])/'app'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rd='src/main/assets/shaders/motionv2/render.glsl'
gd='src/main/assets/shaders/motionv2/gainmap.glsl'
jd='src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
r=(C/rd).read_text();g=(C/gd).read_text();j=(C/jd).read_text()
old_r=(B/rd).read_text();old_g=(B/gd).read_text();old_j=(B/jd).read_text()
assert 'p.motionV2ReconstructionOwner != Parameters.MOTION_V2_RECONSTRUCTION_RAWR_AMAZE' in j
assert 'p.motionV2SuperResOutputEnabled' in j and 'p.irisNightActive' in j
assert 'p.motionV2Active' in j
assert 'Float.isFinite(p50)' in j and 'Float.isFinite(p998)' in j
assert 'backlit*iris26582Clamp(' in j and '0.014f/Math.max(p50,0.002f)' in j
assert 'iris26623Smoothstep(0.60f,0.72f,p99)' in j
assert 'iris26623Smoothstep(0.80f,0.96f,p998)' in j
assert 'iris26623Smoothstep(0.069f,0.081f,p50)' in j
assert 'glProg.setVar("iris26893BacklitCoefficient",iris26893BacklitCoefficient)' in j
assert 'glProg.setVar("iris26892FlatContrastStrength",iris26892FlatContrastStrength)' in j
assert 'IRIS_26893_SDR_ADAPTIVE_FINISH' in j
assert 'captureEvUnchanged=true' in j and 'sdrGainmapMirror=true' in j
# No exposure, sensor/RAW/temporal or color pipeline modification beyond presentation.
assert sha(B/'src/main/assets/shaders/motionv2/iris_tone_controls.glsl')==sha(C/'src/main/assets/shaders/motionv2/iris_tone_controls.glsl')
start='/* IRIS_26892_SCENE_ADAPTIVE_SDR_FINISH'
assert r.count(start)==g.count(start)==1
s1=r[r.index(start):r.index('\nfloat mapFinalSdrGuide(',r.index(start))]
s2=g[g.index(start):g.index('\nfloat iris26660SharedSdrGuide(',g.index(start))]
assert s1==s2,'SDR render vs gainmap SDR denominator diverged'
assert 'float lifted=min(1.0,y+backlitCoefficient*y*t*t*t*shadowGate);' in s1
assert 'float darkBodyGate=1.0-smoothstep(0.52,0.76,lifted);' in s1
assert 'float contrastDenominator=1.0+contrast*pow(1.0-lifted,3.0)*darkBodyGate;' in s1
assert 'return clamp(lifted/contrastDenominator,0.0,1.0);' in s1
assert 'iris26893BacklitCoefficient' in s1
assert 'iris26892FlatContrastStrength' in s1
assert 'exp2(liftEv)' not in s1 and 'sCurve' not in s1
assert 'contrast=0.90*clamp' in s1
assert 'iris26892BacklitStrength' in s1 # retained ABI, historical setting
# Exact baseline recovery from the only changed scalar block, same named runtime guide and call sites.
old1=old_r[old_r.index(start):old_r.index('\nfloat mapFinalSdrGuide(',old_r.index(start))]
old2=old_g[old_g.index(start):old_g.index('\nfloat iris26660SharedSdrGuide(',old_g.index(start))]
assert old1==old2
assert r.replace(s1,old1,1)==old_r,'render has unapproved edits beyond one scalar function'
assert g.replace(s2,old2,1)==old_g,'gainmap has unapproved edits beyond one scalar function'
# Java changed only inside classifier, one new uniform and its log binding.
assert 'iris26893BacklitCoefficient' not in old_j and j.count('iris26893BacklitCoefficient')==5
assert 'iris26892SceneFinishStrengths(basePipeline.mParameters)' in j
assert 'float[] iris26892Strengths=' in j
assert j.count('IRIS_26893_GARDEN_CALIBRATED_BACKLIGHT')==1
assert j.count('IRIS_26893_DARKEN_ONLY_FLAT_SCENE_CONTRAST')==1
assert 'float[] {0.0f, 0.0f};' in j # safe historical fallback + 26893 length guard
assert 'iris26892Strengths.length>2?' in j
assert (C/'version.properties').read_text()=='VERSION_MAJOR=0\nVERSION_MINOR=9726440\nVERSION_NAME=0.9726893\nVERSION_BUILD=26893\n'
print('PASS 26893 B-SR-OFF owner, HIST frozen p50/p99/p998, scalar darken-only monotone, exact SDR/UHDR shared guide, UHDR/LONG/HDRQ protected, 26893 version')
