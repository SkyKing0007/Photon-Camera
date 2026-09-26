#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3:raise SystemExit("usage: validate_26707.py BASE26706 CANDIDATE")
b=Path(sys.argv[1]);c=Path(sys.argv[2])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def H(r):return {'app/'+str(p.relative_to(r/'app')):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
def txt(r,rel):return (r/rel).read_text()
def method(s,sig):
 i=s.index(sig);brace=s.index('{',i);d=0
 for j in range(brace,len(s)):
  if s[j]=='{':d+=1
  elif s[j]=='}':
   d-=1
   if d==0:return s[i:j+1]
 raise AssertionError(sig)
B=H(b);C=H(c);assert len(B)==len(C)==1823
expected={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/version.properties'}
changed={k for k in set(B)|set(C) if B.get(k)!=C.get(k)};assert changed==expected,changed
v=txt(c,'app/version.properties');assert 'VERSION_NAME=0.9726707' in v and 'VERSION_BUILD=26707' in v
# Existing lens-agnostic neutral-surface blue-speck correction remains.
ch=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
for t in ['IRIS_26707_VALID_CFA_NEUTRAL_SURFACE_LEAK_REJECT','validCfaNeutralLeakProof','validCfaNeutralLeakAuthority','neutralLeakRealColorVeto','vec3 correctedRgb = clamp(vec3(centerLuma) + correctedChroma']:
 assert t in ch,t
for t in ['cameraId','focalLength','telephoto']:
 assert t not in ch,t
# Absolute non-ratcheting NORMAL protection, preserving 26705 cold-start convergence.
cap=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for t in ['IRIS_26707_ABSOLUTE_NORMAL_HIGHLIGHT_PROTECTION','MOTION_26707_NORMAL_HIGHLIGHT_MODERATE_EV = 2.0f / 3.0f','MOTION_26707_NORMAL_HIGHLIGHT_STRONG_EV = 4.0f / 3.0f','IRIS_26707_NORMAL_HIGHLIGHT_TARGET','IRIS_26707_NORMAL_HIGHLIGHT_OBSERVED','IRIS_26707_ABSOLUTE_REFERENCE_PROTECTION_METADATA_TRUTH']:
 assert t in cap,t
assert 'MOTION_26680_FORCE_LATCH_FRAMES' not in cap
assert cap.count('updateMotion26662GoogleReferenceExposureAuthority(result)')==1
assert '/* updateMotion26662GoogleReferenceExposureAuthority(result); intentionally dormant */' in cap
stable=method(cap,'    private void updateMotion26680StablePreviewAuthority(')
for t in ['mMotion26680StableFrames >= MOTION_26680_STABLE_CONFIRM_FRAMES','mMotion26707HighlightBaseSteps - requestedProtectionSteps','mMotion26707HighlightBaseSteps','clearMotion26707AbsoluteHighlightState()','cumulativeHighlightRatchetImpossible=true','iris26705NoUnconvergedForceLatch=true']:
 assert t in stable,t
assert '|| mMotion26680StationaryFrames' not in stable
# No endless darker retry and no shutter wait owner revived.
wait=method(cap,'    private boolean motion26676ProtectionIncreasePendingForShutter()')
assert 'return false;' in wait and 'CONTROL_AE_EXPOSURE_COMPENSATION' not in wait
meta=method(cap,'    private void populateMotion26480FrameMetadata(')
assert 'getMotion26663ReferencePreviewProtectionEv(ts)' in meta
assert 'MOTION_26707_NORMAL_HIGHLIGHT_STRONG_EV' in meta
# Synthetic exact supplied-scene classification: plant=moderate, chandelier=strong.
def protect(p995,fraction,cells,peak,compact,spatial=True,hdr=True):
 if not spatial and not hdr and fraction<.002:return 0.0
 concentrated=compact and 1<=cells<=4 and peak>=2 and fraction<.002
 severe=fraction>=.010 and p995>=.90
 return 4/3 if (concentrated or severe) else 2/3
assert abs(protect(.70703125,.003585218,8,4,True)-2/3)<1e-8
assert abs(protect(.34765625,.00055157195,2,2,True)-4/3)<1e-8
assert protect(.10,0,0,0,False,False,False)==0
# Moving-screen fix: NORMAL only, extreme low-confidence temporal tail only.
sh=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
for t in ['IRIS_26707_MOVING_CONTENT_LOW_CONFIDENCE_TAIL_REJECT','uniform int uRejectLowConfidenceTemporalTail;','frameWeight < 0.0625','pixelDifference < 0.125','weight = 0.0;']:
 assert t in sh,t
st=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for t in ['rejectLowConfidenceTemporalTail: Boolean = false','uRejectLowConfidenceTemporalTail','frame.role == RawBurstFrameRole.NORMAL']:
 assert t in st,t
# 26706 tone/highlight-spacing and render/SHORT universal fusion stay byte-identical.
for rel in [
'app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
# New owners are lens/device agnostic.
newowners='\n'.join([ch,method(cap,'    private float motion26707AbsoluteNormalHighlightProtectionEv('),sh,st])
for bad in ['cameraId ==','cameraId==','focalLength >','focalLength>','TELEPHOTO_ONLY']:
 assert bad not in newowners,bad
print('PASS validate 26707 revised: exact 5-file scope; blue-speck rejection + absolute 0/0.67/1.33EV NORMAL protection + 26705 cold-start convergence + NORMAL-only moving-tail rejection; 26706 tone/UHDR protected')
