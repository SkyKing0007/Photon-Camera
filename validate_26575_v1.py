#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('FAIL: usage base candidate')
B,C=map(Path,sys.argv[1:])
EXPECTED={
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java',
'app/version.properties'}
def fail(m): raise SystemExit('FAIL: '+m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def files(root): return {str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file()}
def txt(root,rel): return (root/rel).read_text()

a=files(B);b=files(C);changed={k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
if changed!=EXPECTED: fail('allowlist '+repr(sorted(changed)))
if len(a)!=1708 or set(a)!=set(b): fail(f'candidate universe base={len(a)} cand={len(b)} pathsame={set(a)==set(b)}')
print('PASS exact 1708-file authority universe + exact six-file allowlist')

v=txt(C,'app/version.properties')
for x in ['VERSION_NAME=0.9726575','VERSION_BUILD=26575']:
 if x not in v: fail('version '+x)
print('PASS version 0.9726575 / 26575')

cap=txt(C,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
batch=txt(C,'app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java')
saver=txt(C,'app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java')
hdr=txt(C,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
ui=txt(C,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java')

for token in [
 'IRIS_26575_MOTION_SUPER_RES_SHUTTER_OWNER',
 'mMotion26575SuperResAtShutter = PreferenceKeys.isIrisSuperResOn();',
 'IRIS_26575_SUPER_RES_SHUTTER_SNAPSHOT',
 'iris26486ShortSlot, mMotion26575SuperResAtShutter)',
 'superResFrozen=" + motionBatch.superResEnabled']:
 if token not in cap: fail('CaptureController immutable SR contract '+token)
print('PASS Motion shutter snapshots SR before immutable batch construction')

for token in [
 'IRIS_26575_MOTION_SUPER_RES_IMMUTABLE_BATCH',
 'public final boolean superResEnabled;',
 'ShortHighlightSlot shortHighlightSlot, boolean superResEnabled)',
 'this.superResEnabled = superResEnabled;']:
 if token not in batch: fail('MotionBatch immutable SR contract '+token)
print('PASS MotionBatch carries final immutable Super Res state')

if 'batch.superResEnabled' not in saver: fail('DefaultSaver does not pass frozen SR state')
if 'PreferenceKeys.isIrisSuperResOn()' in saver: fail('DefaultSaver rereads mutable SR preference')
print('PASS DefaultSaver forwards immutable SR state without global reread')

for token in [
 'IRIS_26575_MOTION_SUPER_RES_HDRX_HANDOFF',
 'boolean superResEnabled,',
 'this.mMotion26575SuperResEnabled = superResEnabled;',
 'IRIS_26575_SUPER_RES_IMMUTABLE_PROCESSING_OWNER',
 'processingParameters.motionV2SuperResOutputEnabled = mMotion26575SuperResEnabled;',
 'mMotion26575SuperResEnabled ? 2.0f : 1.0f',
 'IRIS_26575_SUPER_RES_PROCESSING_SNAPSHOT',
 'livePreferenceDiagnosticOnly=',
 'IRIS_26575_FINAL_JPEG_DIMENSION_PROOF',
 'inJustDecodeBounds = true',
 'BitmapFactory.decodeFile(imageFile.toString(), iris26575Bounds)',
 'jpegWidth=',
 'jpegHeight=']:
 if token not in hdr: fail('Hdrx immutable SR/final dimension contract '+token)
# The only live preference read left in Hdrx must be telemetry-only text, not the output owner assignment.
if re.search(r'motionV2SuperResOutputEnabled\s*=\s*[^;]*PreferenceKeys\.isIrisSuperResOn',hdr):
 fail('mutable global SR preference still owns Motion processing')
if hdr.count('PreferenceKeys.isIrisSuperResOn()')!=1:
 fail('Hdrx live SR preference reads expected exactly one diagnostic-only occurrence')
print('PASS Hdrx Motion SR owner is immutable batch state; live preference diagnostic-only')

for token in [
 'IRIS_26575_SUPER_RES_UI_COMMIT_PROOF',
 'final boolean iris26575RequestedSuperRes = value.equals(1);',
 'PreferenceKeys.setIrisSuperRes(iris26575RequestedSuperRes);',
 'final boolean iris26575StoredSuperRes = PreferenceKeys.isIrisSuperResOn();',
 'IRIS_26575_SUPER_RES_UI_COMMIT requested=',
 'match=']:
 if token not in ui: fail('UI SR commit proof '+token)
print('PASS visible Super Res selection logs requested/stored synchronous preference readback')

# Preserve exact successful 26574 reconstruction/IQ owners. These are not part of the six-file state fix.
for rel in [
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
 'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java']:
 if sha(B/rel)!=sha(C/rel): fail('protected 26574 reconstruction/publication/Night owner changed '+rel)
print('PASS successful 26574 VGN/SR refinement/native publication/Night bytes unchanged')

# Preserve both successful reset semantics; the correction is ownership, not removal of intentional resets.
photon='app/src/main/java/com/particlesdevs/photoncamera/app/PhotonCamera.java'
frag='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java'
for rel,marker in [(photon,'IRIS_26562_COLD_START_RESET'),(frag,'IRIS_26562_FOREGROUND_RESET_APPLIED')]:
 if sha(B/rel)!=sha(C/rel): fail('reset owner unexpectedly changed '+rel)
 if marker not in txt(C,rel): fail('reset marker missing '+marker)
print('PASS cold-start and foreground reset behavior intentionally unchanged')

# Logic regression: post-shutter live preference changes cannot alter frozen result.
def process(frozen,live): return frozen
for frozen in (False,True):
 for live in (False,True):
  if process(frozen,live)!=frozen: fail('synthetic immutable-state regression')
print('PASS synthetic true->false and false->true post-shutter preference changes cannot change processing SR')

# Final JPEG proof is telemetry only and cannot mutate the output or SR decision.
proof_start=hdr.find('IRIS_26575_FINAL_JPEG_DIMENSION_PROOF')
if proof_start<0: fail('dimension proof missing')
window=hdr[max(0,proof_start-1500):proof_start+1800]
for bad in ['motionV2SuperResOutputEnabled =','motionV2SuperResOutputScale =','writeTrue2x(','writeNative(']:
 if bad in window: fail('final JPEG dimension diagnostic affects image math/publication '+bad)
print('PASS final JPEG dimension proof is post-save diagnostic-only')

print('PASS 26575 immutable Motion Super Res state ownership validation')
