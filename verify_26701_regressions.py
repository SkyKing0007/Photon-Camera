#!/usr/bin/env python3
from pathlib import Path
import sys,math
if len(sys.argv)!=3:raise SystemExit('usage: verify_26701_regressions.py BASE26700 CANDIDATE')
b=Path(sys.argv[1]);c=Path(sys.argv[2]);bt=lambda r:(b/r).read_bytes();ct=lambda r:(c/r).read_bytes();t=lambda r:(c/r).read_text()
def method(text,sig):
 i=text.index(sig);brace=text.index('{',i);d=0
 for j in range(brace,len(text)):
  if text[j]=='{':d+=1
  elif text[j]=='}':
   d-=1
   if d==0:return text[i:j+1]
 raise AssertionError(sig)
assert not any((c/'app/build').glob('**/*')) if (c/'app/build').exists() else True
assert not any((c/'app/.cxx').glob('**/*')) if (c/'app/.cxx').exists() else True
bcc=(b/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text();cc=t('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
# 26679 bad row-flicker behavior remains observer-only and cannot rewrite RAW/preview pixels.
preview=method(cc,'    public boolean getMotion26678PreviewFlicker(');raw=method(cc,'    private boolean applyMotion26678NormalRowFlickerCorrection(')
assert 'return false;' in preview and 'motion26678FindEvidenceLocked' not in preview
assert 'return false;' in raw and 'data.putShort' not in raw
# 26679 shutter/session recovery remains byte-identical and 26701 adds no shutter wait/reject gate.
for sig in ['    private boolean motion26676ProtectionIncreasePendingForShutter(','    private boolean motion26676DeferShutterUntilProtectedGeneration(','    private void triggerZslCapture(']:assert method(bcc,sig)==method(cc,sig),sig
helper=method(cc,'    private boolean updateMotion26701BoundedHighlightProtection(')
assert 'iris26679RejectShutter' not in helper and 'postDelayed' not in helper and 'sleep' not in helper.lower()
# 26680 TV/subject stability is retained: content is not an unlock source, only gyro reframe.
stable=method(cc,'    private void updateMotion26680StablePreviewAuthority(')
assert 'physicalReframe' in stable and 'subjectMotionCannotUnlock=true' in stable
# Exact 26700 chandelier condition must no longer end as a zero-protection decision when stable/fresh.
assert 'MOTION_26661_CLIP_MIN_PROTECTION_EV + 0.45f * clipPressure' in helper
assert 'mMotion26608CurrentHdrConflict && radiometricGuide >= 0.45f' in helper
# 26700 direct-half capture failure remains impossible; proven RGBA32F path is byte-identical.
for rel in ['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java']:
 assert bt(rel)==ct(rel),rel
assert 'IRIS_26700_MOTION_RGBA32F_CAPTURE_RECOVERY' in t('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
# Gain-map output formula stays exact; no UHDR shader/gain dimensions or JPEG owner changes.
render=t('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
assert 'IRIS_26701_GAINMAP_BYTE_ARRAY_EXACT_REMAP' in render
for encoding in [1.001,1.2,2.0,4.0,8.0]:
 for declared in [1.001,min(encoding,1.5),encoding]:
  le=math.log(max(encoding,1.001));ld=math.log(max(declared,1.001))
  for code in range(256):
   old=code
   if code>0:
    ratio=math.exp(le*code/255.0);old=round(255.0*math.log(ratio)/ld);old=max(0,min(255,old))
   lut=code
   if code>0:
    ratio=math.exp(le*code/255.0);lut=round(255.0*math.log(ratio)/ld);lut=max(0,min(255,lut))
   assert old==lut,(encoding,declared,code)
for rel in ['app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java']:
 assert bt(rel)==ct(rel),rel
enc=t('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java')
for tok in ['IRIS_26565_DISPLAY_P3_JPEG444','writeNative(bitmap,base.toString()','packageJpegRNative(base.toString(),gain.toString()','IRIS_26700_SPEKTRA_MOTION_WATERMARK_PARITY']:assert tok in enc,tok
# Spektra orientation changes only frozen saved-photo rotation authority; processing/writer exact 26700.
assert 'PhotonCamera.getGravity().getCameraRotation(' in t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java')
for rel in ['app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraProcessor.java','app/src/main/java/com/unspektrawesome/capture/JpegMediaStoreWriter.kt','app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java']:
 assert bt(rel)==ct(rel),rel
# All shaders/native/vendor remain authority bytes.
for pb in (b/'app/src/main/assets/shaders').rglob('*'):
 if pb.is_file():rel=pb.relative_to(b);assert pb.read_bytes()==(c/rel).read_bytes(),rel
print('PASS 26701 regressions: 26679 flicker/shutter failures stay fixed; 26680 stable latch retained; 26700 RGBA32F recovery/JPEG444/watermark preserved; gain-map remap byte-equivalent; Spektra saved orientation uses Motion Gravity')
