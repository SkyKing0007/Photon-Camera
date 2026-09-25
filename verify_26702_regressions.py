#!/usr/bin/env python3
from pathlib import Path
import sys,re
if len(sys.argv)!=3:raise SystemExit('usage: verify_26702_regressions.py BASE26701 CANDIDATE')
b=Path(sys.argv[1]);c=Path(sys.argv[2])
def txt(root,rel):return (root/rel).read_text()
def method(text,sig):
 i=text.index(sig);brace=text.index('{',i);d=0
 for j in range(brace,len(text)):
  if text[j]=='{':d+=1
  elif text[j]=='}':
   d-=1
   if d==0:return text[i:j+1]
 raise AssertionError(sig)
# Permanent regression: 26701 changed a dormant Spektra owner while active RawVulkan still used portrait-locked Display rotation.
raw=txt(c,'app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt')
cap=raw[raw.index('    fun captureStill(): Boolean'):raw.index('    fun configure(',raw.index('    fun captureStill(): Boolean'))]
assert 'PhotonCamera.getGravity().getCameraRotation(sensorOrientation)' in cap
assert 'displayRotationDegrees()' not in cap
assert 'owner.camera.facing == LensFacing.FRONT' in cap
spek=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java')
assert 'IRIS_26701_SPEKTRA_CAPTURE_ORIENTATION' not in spek
# Permanent regression: OFF must skip construction, not compute a zero-strength pyramid.
r=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
block=r[r.index('final boolean iris26702LocalLaplacianEnabled'):r.index('final boolean iris26640KeepLocalToneForGainMap')]
assert 'iris26621BuildLocalLaplacianTone(extendedLinearHdr)' in block and 'iris26621LocalTone = null;' in block
assert 'strength = 0' not in block and '0.0f)' not in block.split('else {',1)[1]
# ON algorithm bodies stay byte-identical to successful 26701.
br=txt(b,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
for sig in ['    private GLTexture iris26621BuildLocalLaplacianTone(','    private GLTexture iris26626ApplyBoundedSourceDomainPreservation(']:assert method(br,sig)==method(r,sig)
# Existing 26701 highlight/stability owners cannot be altered by toggle plumbing.
bc=txt(b,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java');cc=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for sig in ['    private boolean updateMotion26701BoundedHighlightProtection(','    private void updateMotion26680StablePreviewAuthority(','    public boolean getMotion26678PreviewFlicker(','    private boolean applyMotion26678NormalRowFlickerCorrection(','    private boolean motion26676ProtectionIncreasePendingForShutter(','    private boolean motion26676DeferShutterUntilProtectedGeneration(']:assert method(bc,sig)==method(cc,sig),sig
assert '\n                updateMotion26662GoogleReferenceExposureAuthority(result);' not in cc
# True2x global fallback must keep Motion HDR handoff true; never disguise OFF as Night/legacy.
enc=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java')
assert 'publicationSceneWhite, parameters.motionV2Active, localToneRequired,' in enc
cpp=txt(c,'app/src/main/cpp/motionv2_jpeg444_jni.cpp')
assert 'p.motionHdrHandoff=motionHdrHandoff==JNI_TRUE' in cpp
assert 'if(!p.motionHdrHandoff||!p.localToneLogMap' in cpp
assert 'float globalMapped=iris26621MapMotionSdrFinalGuide(guide,p.displayGain);' in cpp
# No shader modification, no gain-map remap regression.
for rel in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
for rel in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
print('PASS 26702 permanent regressions: active Spektra owner only; real Laplacian bypass; 26701 ON/highlight/stability/gain-map/Sabre contracts preserved; true2x OFF remains Motion global-tone path')
