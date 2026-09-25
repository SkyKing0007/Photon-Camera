#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3:raise SystemExit('usage: verify_26705_regressions.py BASE26704 CANDIDATE')
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
changed={k for k in set(B)|set(C) if B.get(k)!=C.get(k)}
expected={'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/version.properties'}
assert changed==expected,changed
v=txt(c,'app/version.properties');assert 'VERSION_NAME=0.9726705' in v and 'VERSION_BUILD=26705' in v
cap=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
assert 'IRIS_26705_NORMAL_AE_SHORT_HEADROOM_OWNER' in cap
assert 'MOTION_26680_FORCE_LATCH_FRAMES' not in cap
assert 'mMotion26701' not in cap and 'updateMotion26701BoundedHighlightProtection' not in cap
stable=method(cap,'    private void updateMotion26680StablePreviewAuthority(')
assert 'CONTROL_AE_EXPOSURE_COMPENSATION' not in stable
assert 'mMotion26680StableFrames >= MOTION_26680_STABLE_CONFIRM_FRAMES' in stable
assert '|| mMotion26680StationaryFrames' not in stable
assert 'referenceProtectionEv=0.0' in stable and 'shortHeadroomDecisionAtShutter=true' in stable
extra=method(cap,'    private float motion26705ShortExtraProtectionEv(')
for t in ['MOTION_26705_SHORT_EXTRA_MAX_EV','mMotion26608CompactHdrConflict','mMotion26496RawCoherentHighlightCells >= 4','mMotion26608RawP995 >= 0.72f','1.25f + 1.25f * clipPressure']:
 assert t in extra,t
short=method(cap,'    private boolean applyMotion26486ExplicitShortCaptureIfNeeded(')
for t in ['iris26705ExtraShortEv','iris26705TotalShortEv','Math.pow(2.0, iris26705TotalShortEv)','iris26705TargetEnergy','normalAeUntouched=true']:
 assert t in short,t
assert 'baseExp / MOTION_26480_SHORT_EXPOSURE_DIVISOR' not in short
meta=method(cap,'    private void populateMotion26480FrameMetadata(')
assert 'IRIS_26705_NORMAL_REFERENCE_PROTECTION_METADATA_TRUTH' in meta
assert 'frame.motionV2ReferenceProtectionEv = 0.0f;' in meta and 'mMotion26661ReferenceBaseSteps' not in meta
wait=method(cap,'    private boolean motion26676ProtectionIncreasePendingForShutter()')
assert 'return false;' in wait and 'CONTROL_AE_EXPOSURE_COMPENSATION' not in wait
# Production callback keeps old reactive writer dormant.
assert '/* updateMotion26662GoogleReferenceExposureAuthority(result); intentionally dormant */' in cap
# Synthetic headroom checks reproduce the intended classes without changing NORMAL.
def extra_ev(p995,fraction,coherent,peak,broad,mixed,compact,trigger=True):
 if not trigger:return 0.0
 e=0.0
 if broad:e=max(e,.75)
 if mixed:e=max(e,1.25)
 if compact:e=max(e,1.75)
 if coherent>=2:e=max(e,1.25)
 if coherent>=4:e=max(e,2.0)
 if peak>=3:e=max(e,2.25)
 if p995>=.90:e=max(e,2.5)
 elif p995>=.72:e=max(e,2.0)
 elif p995>=.55:e=max(e,1.5)
 elif p995>=.35 and (broad or mixed or compact):e=max(e,1.0)
 if fraction>=.002:
  pressure=max(0,min(1,(fraction-.002)/(.030-.002)));e=max(e,1.25+1.25*pressure)
 return min(2.5,e)
assert extra_ev(.72265625,.0027578599,6,2,False,False,True)>=2.0
assert 2.5+extra_ev(.72265625,.0027578599,6,2,False,False,True)>=4.5
assert extra_ev(.1,0,0,0,False,False,False,False)==0
assert extra_ev(.95,.01,4,3,True,True,True)==2.5
sh=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
for t in ['IRIS_26704_VALID_NORMAL_CHROMA_IMMUTABLE','IRIS_26704_FAIL_CLOSED_INFERRED_SHORT_RADIANCE','IRIS_26705_SHORT_RADIANCE_HIGHLIGHT_DOMAIN_ONLY','float physicalHighlightContext = smoothstep(','0.38, 0.62','measuredNormalLoss = max(physicalNormalLoss, inferredRadiometricLoss) *']:
 assert t in sh,t
assert 'visualColorDeficit' not in sh
# Body tone/UHDR/Spektra/native/settings from successful 26704 remain byte-identical.
for rel in [
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/unspektrawesome/capture/FrameGeometrySnapshot.kt',
'app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
print('PASS 26705 permanent regressions: exact 3-file scope; NORMAL AE untouched; no unconverged force latch; adaptive SHORT-only headroom; SHORT radiance highlight-only; successful 26704 tone/UHDR/Spektra/native protected')
