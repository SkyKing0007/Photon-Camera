#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,xml.etree.ElementTree as ET
if len(sys.argv)!=3: raise SystemExit('usage: validate_26693.py BASE CANDIDATE')
b=Path(sys.argv[1]); c=Path(sys.argv[2])
def txt(rel): return (c/rel).read_text()
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def allh(root): return {str(p.relative_to(root)):h(p) for p in root.rglob('*') if p.is_file()}
B=allh(b/'app'); C=allh(c/'app'); changed=sorted('app/'+x for x in set(B)|set(C) if B.get(x)!=C.get(x))
expected=sorted(x.strip() for x in (Path(__file__).resolve().parent/'26693_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip())
assert changed==expected,(changed,expected)
assert len(B)==len(C)==1822 and len(changed)==7
ui=txt('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
layout=txt('app/src/main/res/layout/camera_fragment.xml')
hist=txt('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/SpektraLiveHistogramView.java')
mode=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java')
ctrl=txt('app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt')
vr=txt('app/src/main/java/com/unspektrawesome/vulkan/VulkanRenderer.kt')
# XML must be well formed and fixed chrome must anchor to the dedicated Photo reference, not preview dummy.
ET.parse(c/'app/src/main/res/layout/camera_fragment.xml')
assert layout.count('@+id/control_geometry_reference')==1
assert 'app:layout_constraintDimensionRatio="3:4"' in layout
assert layout.count('app:layout_constraintBottom_toBottomOf="@id/control_geometry_reference"')==2
assert 'app:layout_constraintBottom_toBottomOf="@id/dummy_reference_view"' not in layout
# Final owner must consume fixed control reference. aspect/videoStyle are evidence/log only, not scale/position branches.
assert 'iris26693SyncFixedControlGeometryReference' in ui
assert 'controlReferenceBottom + previewClearancePx' in ui
assert 'IRIS_26693_UI_GEOMETRY_INVARIANT' in ui
assert 'finalOwner=fixedPhotoControlReference' in ui and 'videoStyleGeometryAuthority=false' in ui
assert '2145' not in ui and '0.47810364' not in ui
method=ui[ui.index('private void applyAdaptiveBottomSafeLayout'):ui.index('private void applyBottomGeometry')]
assert 'viewfinderBottom + previewClearancePx' not in method
assert 'if (videoStyle' not in method and 'if(videoStyle' not in method
assert 'if (aspect169' not in method and 'if(aspect169' not in method
# Preview/capture aspect ownership remains legitimate and untouched outside runtime scope.
cap='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
assert (b/cap).read_bytes()==(c/cap).read_bytes()
# Spektra visual view is presentation-only: no custom worker/poller/native pull.
for forbidden in ('HandlerThread','POLL_MS','startPolling','stopPolling','schedulePoll','pollOnce','histogramPixels(1.0f)'):
 assert forbidden not in hist,forbidden
assert 'IRIS_26693_SPEKTRA_PRESENTATION_ONLY_HISTOGRAM' in hist
assert 'HistogramListener' in hist and 'acceptHistogramPixels' in hist
# Iris shell delegates only a presentation sink; no pull API remains there.
assert 'setHistogramListener' in mode and 'public int[] histogramPixels' not in mode
# Unspektrawesome preview owner acquires only from a successfully rendered active STREAMING generation.
assert 'IRIS_26693_STANDALONE_HISTOGRAM_LIFECYCLE_OWNER' in ctrl
assert 'publishHistogramFromRenderedFrameLocked(owner, now)' in ctrl
assert 'active !== owner' in ctrl and 'Camera2RawSession.State.STREAMING' in ctrl
assert 'clearHistogramLocked()' in ctrl
assert 'fun histogramPixels(scale' not in ctrl
assert 'HISTOGRAM_MIN_INTERVAL_MS = 50L' in ctrl
assert 'SPEKTRA_HISTOGRAM_PRESENTATION_FAILURE' in ctrl and 'SPEKTRA_HISTOGRAM_CLEAR_FAILURE' in ctrl
# JNI null/no-frame state becomes explicit and cannot cross into Java as a null array.
assert 'nativeHistogramPixels(current, scale) ?: IntArray(0)' in vr
assert 'nativeHistogramPixels(handle: Long, scale: Float): IntArray?' in vr
# Version target.
ver=txt('app/version.properties'); assert 'VERSION_NAME=0.9726693' in ver and 'VERSION_BUILD=26693' in ver
print('PASS 26693 semantic/ownership validation: global control geometry decoupled; standalone Spektra histogram owner; Iris presentation-only')
