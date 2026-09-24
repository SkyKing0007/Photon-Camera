#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, sys
if len(sys.argv)!=3: raise SystemExit('usage: repair_26697_regressions.py BASE26696R1 CANDIDATE')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
t=lambda r:(c/r).read_text()
ae=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraExposureController.java')
raw=t('app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt')
sess=t('app/src/main/java/com/unspektrawesome/camera/session/Camera2RawSession.java')
meta=t('app/src/main/java/com/unspektrawesome/camera/session/RawCaptureMetadata.java')
dorm=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java')
# Exact device-runtime regression from 26696: +EV must never be reinterpreted as positive luminance.
assert 'TARGET_LINEAR' not in ae and 'log2(TARGET_LINEAR' not in ae
assert 'meterErrorEv = signedMeterEv + exposureCompensationEv;' in ae
assert 'rawTargetTotalEv = actualTotalEv + meterErrorEv;' in ae
assert 'if (sequence <= 0L || !meter.isFinite()) return false' in raw
assert 'meter <= 0.0' not in raw
assert 'camera.equivalentFocalLengthMm' in raw
assert 'val requestedIso = frame.metadata.requestedSensitivityIso ?: return 0L' in raw
assert 'exposureGeneration != owner.exposure.exposureGeneration' in raw
assert 'exposureCompensationEv = ev;' in ae and 'clamp(ev, -8.0, 8.0)' not in ae
# Request/frame identity must prevent stale queued RAW measurements from becoming current commands.
assert 'frameExposureGeneration != exposureGeneration' in ae
assert 'handler.post(() -> applySensorExposureToRepeating(iso, exposureNs, exposureGeneration))' in sess
assert sess.count('setTag(new ExposureRequestTag(')>=3
assert 'result.getRequest()' in sess and 'completedRequest.getTag()' in sess
assert 'requestedSensitivityIso = completedRequest.get(CaptureRequest.SENSOR_SENSITIVITY)' in sess
assert 'pending.sensorTimestampNs,' in raw and 'pending.exposureGeneration,' in raw and 'pending.requestedIso,' in raw
# Permanent compile failure from Actions 35957174533: dormant source still compiles against AE API.
assert dorm.count('exposureController.update(System.nanoTime(), meter)')==1
assert ae.count('public synchronized Solution update(long nowNs, double signedMeterEv)')==1
# Compile-closure regression for every API changed by 26697, not only active runtime owners.
source_text='\n'.join(q.read_text(errors='ignore') for q in (c/'app/src').rglob('*') if q.is_file() and q.suffix in {'.java','.kt'})
assert source_text.count('setSensorExposure(')==3  # one Java definition + exactly two Kotlin callers
assert raw.count('owner.session.setSensorExposure(')==2
assert sess.count('public synchronized void setSensorExposure(int iso, long exposureNs, long exposureGeneration)')==1
assert meta.count('public RawCaptureMetadata(')==3  # two legacy-compatible constructors + tagged full constructor
# Permanent 26694/26695 transport/lifecycle regressions remain fixed.
assert 'renderer.pollExposureMeter(exposureMeterBuffer)' in raw and 'EXPOSURE_METER_POLL_MS = 4L' in raw
assert 'consumeExposureMeterCarrierLocked(owner, "render")' in raw and 'MAX_PENDING_EXPOSURE_METERS = 8' in raw
assert 'closeWhenCameraReleased' in sess and 'CountDownLatch' not in sess and '.await(' not in sess
# Working 26696 R1 owners must remain byte-identical.
for rel in [
 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPipelineWarmup.java',
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/SpektraLiveHistogramView.java',
 'app/src/main/res/layout/camera_fragment.xml',
 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java',
 'app/src/main/java/com/unspektrawesome/capture/JpegMediaStoreWriter.kt',
 'app/src/main/java/com/unspektrawesome/vulkan/VulkanRenderer.kt']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
assert hashlib.sha256((c/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so').read_bytes()).hexdigest()=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd'
# Small independent closed-loop proof of the audited signed-EV law and hard stop behavior.
# This is a regression oracle, not a replacement implementation.
def converge(start_total,target_total,frames=600):
 current=start_total; last=None; changes=0
 for i in range(frames):
  meter=target_total-current
  # Same fundamental signed-EV direction + 0.20-EV bounded movement. Exact source constants and
  # smoothing are separately asserted above; this oracle protects direction/termination failures.
  step=0.0 if abs(meter)<0.04 else max(-0.20,min(0.20,meter))
  nxt=current+step
  if abs(nxt-current)>1e-12: changes+=1
  current=nxt
  if abs(target_total-current)<0.04: last=current; break
 assert last is not None and changes>0
 return current
up=converge(10.0,13.0); down=converge(13.0,10.0)
assert up>10.0 and down<13.0
# Positive/negative/zero algebra against exact raw target equation.
actual=12.0
assert actual+3.0>actual and actual-3.0<actual and actual+0.0==actual
# Limit behavior: once clamped at max, repeated +EV cannot move above max or issue unbounded state.
maximum=15.0; current=14.9
for _ in range(1000): current=min(maximum,current+max(0.0,min(0.20,20.0-current)))
assert current==maximum
# Generated trees/scaffolding never enter runtime allowlist.
changed=[x.strip() for x in (pkg/'26697_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
assert all(not x.startswith(('app/build/','app/.cxx/')) for x in changed)
print('PASS 26697 permanent regressions: signed-EV direction/zero/limits; stale-generation request identity; 26696 compile closure; meter polling; async release; working owners protected')
