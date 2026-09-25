#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re,math
if len(sys.argv)!=3:raise SystemExit('usage: validate_26701.py BASE26700 CANDIDATE')
b=Path(sys.argv[1]);c=Path(sys.argv[2]);pkg=Path(__file__).resolve().parent
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def H(root):return {'app/'+str(p.relative_to(root/'app')):h(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
def t(rel):return (c/rel).read_text()
def method(text,sig):
 i=text.index(sig);brace=text.index('{',i);d=0
 for j in range(brace,len(text)):
  if text[j]=='{':d+=1
  elif text[j]=='}':
   d-=1
   if d==0:return text[i:j+1]
 raise AssertionError(sig)
B=H(b);C=H(c);exp=[x.strip() for x in (pkg/'26701_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
changed=sorted(k for k in set(B)|set(C) if B.get(k)!=C.get(k));assert len(B)==len(C)==1823;assert changed==sorted(exp) and len(changed)==4,(changed,exp)
for rel in B:
 if rel not in exp:assert B[rel]==C[rel],rel
assert not [x for x in (pkg/'26701_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x.strip()]
# Motion highlight: bounded 26662 math before unchanged 26680 latch, no shutter wait.
bcc=(b/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text();cc=t('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for token in ['IRIS_26701_BOUNDED_PRELATCH_HIGHLIGHT_OWNER','updateMotion26701BoundedHighlightProtection(result, aeSettled, sensorTs)','IRIS_26701_FRAME_MATCHED_PREVIEW_PROTECTION','IRIS_26701_HIGHLIGHT_PROTECTION_COMMIT','IRIS_26701_HIGHLIGHT_PROTECTION_OBSERVED','singleStep=true continuousSceneRewrite=false shutterWaitAdded=false','iris26701BoundedHighlightProtection=true']:
 assert token in cc,token
assert cc.count('                updateMotion26680StablePreviewAuthority(result);')==1
assert cc.count('                updateMotion26662GoogleReferenceExposureAuthority(result);')==0
assert 'updateMotion26662GoogleReferenceExposureAuthority(result); intentionally dormant' in cc
helper=method(cc,'    private boolean updateMotion26701BoundedHighlightProtection(')
for stale in ['mMotion26661ReferenceAppliedProtectionSteps','mMotion26661ReferenceCandidateProtectionSteps','mMotion26661ReferenceCandidateFrames','motion26676DeferShutterUntilProtectedGeneration']:
 assert stale not in helper,stale
assert helper.count('CaptureRequest.CONTROL_AE_EXPOSURE_COMPENSATION')>=3
assert 'MOTION_26701_HIGHLIGHT_CONFIRM_FRAMES = 4' in cc
assert 'MOTION_26701_HIGHLIGHT_FORCE_DECISION_FRAMES = 15' in cc
assert 'mMotion26680StationaryFrames >= MOTION_26701_HIGHLIGHT_FORCE_DECISION_FRAMES' in helper
# 26700/26680 stability owner and 26679 shutter/session/flicker fixes stay exact where not intentionally changed.
for sig in ['    public boolean getMotion26678PreviewFlicker(','    private boolean applyMotion26678NormalRowFlickerCorrection(','    private boolean motion26676ProtectionIncreasePendingForShutter(','    private boolean motion26676DeferShutterUntilProtectedGeneration(','    private void triggerZslCapture(']:
 assert method(bcc,sig)==method(cc,sig),sig
stable=method(cc,'    private void updateMotion26680StablePreviewAuthority(')
for token in ['getFilteredShakiness()','physicalReframe','CaptureRequest.CONTROL_AE_LOCK, true','CaptureRequest.CONTROL_AWB_LOCK, true','subjectMotionCannotUnlock=true']:
 assert token in stable,token
# Exact supplied chandelier failing condition must request the old 26662 clip floor, not 0 EV.
raw_p995=0.55859375; frac=4.13679e-4; coherent=1; current_hdr=True
requested=0.0
if current_hdr or (coherent>0 and current_hdr):
 if raw_p995>0.72:requested=math.log(raw_p995/0.72,2)
 if current_hdr and raw_p995>=0.45:requested=max(requested,0.35)
 current_meaningful=(frac>=0.006) or (coherent>0 and current_hdr)
 if current_meaningful:
  clip=max(0.0,min(1.0,(frac-0.006)/(0.030-0.006)))
  requested=max(requested,0.70+0.45*clip)
assert abs(requested-0.70)<1e-9,requested
# Gain-map performance: same R8 bytes + exact old exp/log/round expression, only access pattern changes.
render=t('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
for token in ['IRIS_26701_GAINMAP_BYTE_ARRAY_EXACT_REMAP','byte[] gainCodes = new byte[pixels]','rgbaRead.get(gainCodes, 0, pixels)','final int[] iris26701GainRemap = new int[256]','Math.exp(logEncodingMax * encodedCode / 255.0)','Math.round(255.0 * Math.log(ratioAtPixel) / logDeclaredMax)','alpha.put(gainCodes, 0, pixels)']:
 assert token in render,token
block=render[render.index('IRIS_26701_GAINMAP_BYTE_ARRAY_EXACT_REMAP'):render.index('Per-pixel gain-map provenance')]
assert 'rgba.get(i)' not in block
# Spektra saved orientation now freezes exact Motion Gravity authority; renderer/color/JPEG path stays separate.
spek=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java')
for token in ['IRIS_26701_SPEKTRA_MOTION_ORIENTATION_PARITY','PhotonCamera.getGravity().getCameraRotation(','IRIS_26701_SPEKTRA_CAPTURE_ORIENTATION','motionParity=true']:
 assert token in spek,token
assert spek.index('final int outputRotation = PhotonCamera.getGravity().getCameraRotation(') < spek.index('final SpektraShot shot = new SpektraShot(')
for rel in ['app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraProcessor.java','app/src/main/java/com/unspektrawesome/capture/JpegMediaStoreWriter.kt']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
# Proven 26700 capture recovery/watermark/JPEG contracts protected.
for rel in ['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java','app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
ver=t('app/version.properties');assert 'VERSION_NAME=0.9726701' in ver and 'VERSION_BUILD=26701' in ver
print('PASS validate 26701: exact 4-file scope; bounded pre-latch highlight protection + stable 26680 latch; Spektra Motion-parity saved orientation; byte-identical gain-map remap math; 26700 recovery/watermark/JPEG contracts protected')
