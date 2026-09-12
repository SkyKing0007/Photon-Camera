#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26630_r1_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
nat=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
# Permanent 26628 R1 native compiler regression.
if 'float y=luma(center)' in nat: raise SystemExit('FAIL permanent 26628 R1 NDK regression: local float y shadows pixel-coordinate y')
if nat.count('float lum=luma(center)')!=2: raise SystemExit('FAIL permanent 26628 R1 NDK regression: expected exactly two lum declarations')
# Fresh-26630 transform-boundary regression: never swallow native geometry/parameter owners.
if nat.count('struct SourceRegion {')!=1 or nat.count('struct Params {')!=1: raise SystemExit('FAIL 26630 native transform-boundary regression')
if nat.count('static const char*kIris26571PublicationCompute=R"GLSL(')!=1: raise SystemExit('FAIL 26630 embedded publication shader owner count')
# Permanent 26628 R2 Java repair inherited byte-identical.
auxrel='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/AuxButtonsLayout.java'
if sha(B/auxrel)!=sha(C/auxrel): raise SystemExit('FAIL inherited R2 Java repair changed')
aux=(C/auxrel).read_text()
for tok in ['if (!(child instanceof TextView)) continue;','TextView button = (TextView) child;']:
    if tok not in aux: raise SystemExit(f'FAIL permanent R2 Java type regression {tok}')
if re.search(r'\bButton\b',aux): raise SystemExit('FAIL permanent R2 Java regression: standalone Button survived')
# Proven DNG/calibration/upstream adaptive owners must remain untouched.
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
    if sha(B/rel)!=sha(C/rel): raise SystemExit(f'FAIL inherited 26629 authority changed {rel}')
solver=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/IrisJpegColorSolver.java').read_text()
for bad in ['IRIS_26627_DUAL_ILLUMINANT_FORWARD_PLACEHOLDER_REJECT','forwardDelta <= 1.0e-6f','Build.MANUFACTURER','Build.MODEL']:
    if bad in solver: raise SystemExit(f'FAIL stale DNG color regression {bad}')
ads=(C/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text()
for bad in ['1.32','1.12','coherentColorActivation','MAX_WEAK_CHROMA_GAIN']:
    if bad in ads: raise SystemExit(f'FAIL stale adaptive color authority {bad}')
# Android Gainmap remains scalar/single-plane and Night UHDR is unchanged.
ultra=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java').read_text(); renderj=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
for tok in ['gainmap.setRatioMin(MIN_RATIO, MIN_RATIO, MIN_RATIO);','gainmap.setRatioMax(safeMax, safeMax, safeMax);','gainmap.setGamma(1.0f, 1.0f, 1.0f);','gainmap.setEpsilonSdr(EPSILON, EPSILON, EPSILON);','gainmap.setEpsilonHdr(EPSILON, EPSILON, EPSILON);']:
    if tok not in ultra: raise SystemExit(f'FAIL scalar Android Gainmap metadata {tok}')
if 'Bitmap.Config.ALPHA_8' not in renderj: raise SystemExit('FAIL Motion UHDR gain map no longer ALPHA_8')
night='app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisNightUltraHdr.java'
if sha(B/night)!=sha(C/night): raise SystemExit('FAIL Night UHDR changed')
# Old knobs may survive only as migration-removal strings in PreferenceKeys, never active consumers/resources.
alltext='\n'.join(p.read_text(errors='ignore') for p in (C/'app/src').rglob('*') if p.is_file() and p.suffix in {'.java','.kt','.xml','.glsl'})
pk=(C/'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java').read_text()
for old in ['pref_motion_viewfinder_match_strength','pref_iris_vgn_chroma_correction']:
    if alltext.count(old)!=pk.count(old) or pk.count(f'map.remove("{old}")')!=3: raise SystemExit(f'FAIL stale active setting authority {old}')
# 1.12 must never reappear as VGN policy.
bridge=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
if 'vgnChromaCorrectionStrength = 1.12' in bridge: raise SystemExit('FAIL stale VGN 1.12 revived')
print('PASS 26630 regressions: permanent R1/R2/DNG/scalar-gainmap/Night protections; native transform-boundary owner preservation; stale VGN/viewfinder authorities neutralized')
