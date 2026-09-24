#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26694.py BASE CANDIDATE')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def txt(rel): return (c/rel).read_text()
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def allh(root): return {str(p.relative_to(root)):h(p) for p in root.rglob('*') if p.is_file()}
B=allh(b/'app'); C=allh(c/'app'); changed=sorted('app/'+x for x in set(B)|set(C) if B.get(x)!=C.get(x))
expected=sorted(x.strip() for x in (pkg/'26694_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip())
assert changed==expected,(changed,expected); assert len(B)==len(C)==1822 and len(changed)==7
vr=txt('app/src/main/java/com/unspektrawesome/vulkan/VulkanRenderer.kt')
ctrl=txt('app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt')
mode=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java')
cap=txt('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
frag=txt('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java')
writer=txt('app/src/main/java/com/unspektrawesome/capture/JpegMediaStoreWriter.kt')
# Exact 1.1.2 meter carrier contract: CenterWeighted=0, normalized center .5/.5, output remains +24/+32.
for token in ['EXPOSURE_METER_METHOD_OFFSET = 8','EXPOSURE_METER_CENTER_X_OFFSET = 12','EXPOSURE_METER_CENTER_Y_OFFSET = 16','EXPOSURE_METER_METHOD_CENTER_WEIGHTED = 0','EXPOSURE_METER_DEFAULT_CENTER = 0.5f','EXPOSURE_METER_SEQUENCE_OFFSET = 24','EXPOSURE_METER_VALUE_OFFSET = 32']:
 assert token in vr,token
assert 'configureCenterWeightedExposureMeter(it)' in ctrl
assert 'IRIS_26694_SPEKTRA_AE_METER' in ctrl
# No arbitrary brightness owner was introduced; standalone sensor AE remains the exposure authority.
ae='app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraExposureController.java'
assert (b/ae).read_bytes()==(c/ae).read_bytes()
# Active writer remains single publication owner, now in Iris camera album.
assert 'private const val ALBUM_NAME = "Camera"' in writer
assert 'Unspektrawesome"' not in writer[writer.index('companion object'):]
gallery='app/src/main/java/com/particlesdevs/photoncamera/gallery/files/GalleryFileOperations.java'
assert (b/gallery).read_bytes()==(c/gallery).read_bytes() and '%DCIM/Camera/%' in txt(gallery)
# Active controller owns capture/RCD/save; Iris shell only maps lifecycle to proven UI and exact URI thumbnail.
assert 'interface CaptureListener' in ctrl and 'notifyCaptureAcceptedLocked' in ctrl and 'notifyProcessingStartedLocked' in ctrl and 'notifyCaptureSucceededLocked' in ctrl
assert 'IRIS_26694_SPEKTRA_IRIS_CAPTURE_PRESENTATION_BRIDGE' in mode and 'events.onProcessingStarted("Spektra")' in mode and 'events.onProcessingFinished("Spektra")' in mode
assert 'host.onSpektraImageSaved(uri)' in mode and 'cameraFragmentViewModel.updateGalleryThumb(uri)' in frag
assert 'SPEKTRA_CAPTURE_RACE_REJECTED' in cap and 'if (!spektraModeController.takePicture())' in cap
# Dedicated presentation lock prevents RAW-controller-lock -> synchronized controller inversion.
assert 'private final Object captureUiLock = new Object();' in mode
bridge=mode[mode.index('IRIS_26694_SPEKTRA_IRIS_CAPTURE_PRESENTATION_BRIDGE'):mode.index('private void failActivation')]
assert 'synchronized (this)' not in bridge and 'synchronized (SpektraModeController.this)' not in bridge
# Version.
ver=txt('app/version.properties'); assert 'VERSION_NAME=0.9726694' in ver and 'VERSION_BUILD=26694' in ver
print('PASS 26694 semantic/ownership validation: centered standalone AE meter; single DCIM/Camera publisher; Iris capture UI/gallery bridge only')
