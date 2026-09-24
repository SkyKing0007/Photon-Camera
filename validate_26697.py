#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26697.py BASE26696R1 CANDIDATE')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def H(root): return {'app/'+str(p.relative_to(root/'app')):h(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
def t(rel): return (c/rel).read_text()
B=H(b); C=H(c); exp=[x.strip() for x in (pkg/'26697_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
changed=sorted(k for k in set(B)|set(C) if B.get(k)!=C.get(k))
assert len(B)==len(C)==1823 and changed==sorted(exp) and len(changed)==5
assert not (pkg/'26697_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().strip()
ae=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraExposureController.java')
raw=t('app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt')
sess=t('app/src/main/java/com/unspektrawesome/camera/session/Camera2RawSession.java')
meta=t('app/src/main/java/com/unspektrawesome/camera/session/RawCaptureMetadata.java')
# Exact 1.1.2 signed-EV contract. Native shader already applies 18.4% reference.
assert 'IRIS_26697_SIGNED_NATIVE_METER_EV' in ae
assert 'meterErrorEv = signedMeterEv + exposureCompensationEv;' in ae
assert 'rawTargetTotalEv = actualTotalEv + meterErrorEv;' in ae
assert 'TARGET_LINEAR' not in ae and 'log2(TARGET_LINEAR' not in ae
# Exact 1.1.2 recovered timing/settling constants.
for x in [
 'STARTUP_NS = 1_500_000_000L','HISTORY_NS = 300_000_000L','MIN_UPDATE_NS = 16_000_000L',
 'FIRST_DT_SECONDS = 1.0 / 30.0','STARTUP_TARGET_TAU_SECONDS = 0.025','STEADY_TARGET_TAU_SECONDS = 0.100',
 'STARTUP_CORRECTION_TAU_SECONDS = 0.050','STEADY_CORRECTION_TAU_SECONDS = 0.100',
 'STARTUP_RATE_EV_PER_SECOND = 12.0','STEADY_RATE_EV_PER_SECOND = 4.0','MAX_STEP_EV = 0.20',
 'STARTUP_DEADBAND_EV = 0.025','STEADY_DEADBAND_EV = 0.040','LIMIT_TOLERANCE_EV = 0.08',
 'AE_BALANCE_MIN_EV = -1.5','AE_BALANCE_MAX_EV = 3.0','HISTORY_NS']:
 assert x in ae,x
assert 'final double robustTargetTotalEv = fast' in ae and 'medianTargetTotalEv()' in ae
assert 'Math.min(MAX_STEP_EV, dtSeconds * rateEvPerSecond)' in ae
assert 'SpektraExposureController(CameraCharacteristics c, Float equivalentFocalLengthMm)' in ae
assert 'equivalentFocalLengthMm' in raw and 'camera.equivalentFocalLengthMm' in raw
assert 'exposureCompensationEv = ev;' in ae and 'clamp(ev, -8.0, 8.0)' not in ae
assert 'val requestedIso = frame.metadata.requestedSensitivityIso ?: return 0L' in raw
assert 'exposureGeneration != owner.exposure.exposureGeneration' in raw
# Exact originating request/frame state and stale-generation rejection.
for x in ['frameExposureGeneration != exposureGeneration','requestedIso != null && requestedIso > 0','? requestedIso : actualIso','log2(isoForTarget) + log2(actualExposureNs)']:
 assert x in ae,x
assert 'pending.sensorTimestampNs,' in raw and 'pending.exposureGeneration,' in raw and 'pending.requestedIso,' in raw
assert 'System.nanoTime(),' not in raw[raw.index('owner.exposure.update('):raw.index('owner.exposure.update(')+350]
assert 'if (sequence <= 0L || !meter.isFinite()) return false' in raw
assert 'meter <= 0.0' not in raw
# Camera2 manual request tagging mirrors 1.1.2; concrete tuple is captured by posted runnable.
for x in ['setSensorExposure(int iso, long exposureNs, long exposureGeneration)','handler.post(() -> applySensorExposureToRepeating(iso, exposureNs, exposureGeneration))','request.setTag(new ExposureRequestTag(sensorExposureGeneration))','request.setTag(new ExposureRequestTag(stillExposureGeneration))','result.getRequest()','completedRequest.getTag()','requestedSensitivityIso = completedRequest.get(CaptureRequest.SENSOR_SENSITIVITY)']:
 assert x in sess,x
assert 'handler.post(this::applyCurrentExposureToRepeating)' not in sess
for x in ['public final long exposureGeneration;','public final Integer requestedSensitivityIso;']:
 assert x in meta,x
# Mode/limits and dormant compiler compatibility remain.
for x in ['mode == Mode.ISO_PRIORITY || mode == Mode.MANUAL','mode == Mode.SHUTTER_PRIORITY || mode == Mode.MANUAL','if (mode == Mode.MANUAL) return null;','DEFAULT_AE_SLOWEST_EXPOSURE_NS = 33_333_333L','public synchronized Solution update(long nowNs, double signedMeterEv)']:
 assert x in ae,x
dorm=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java')
assert dorm.count('exposureController.update(System.nanoTime(), meter)')==1
# 26696 R1 working features stay byte-protected by scope and are semantically present.
for rel in [
 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPipelineWarmup.java',
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java',
 'app/src/main/java/com/unspektrawesome/capture/JpegMediaStoreWriter.kt',
 'app/src/main/java/com/unspektrawesome/vulkan/VulkanRenderer.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
assert 'VERSION_NAME=0.9726697' in t('app/version.properties') and 'VERSION_BUILD=26697' in t('app/version.properties')
print('PASS 26697 semantic/ownership validation: exact 1.1.2 signed-EV sensor AE contract; request-tagged frame authority; 26696 R1 working owners preserved')
