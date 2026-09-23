#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: repair_26693_regressions.py BASE CANDIDATE')
b=Path(sys.argv[1]); c=Path(sys.argv[2])
def t(r):return (c/r).read_text()
plan=t('app/src/main/java/com/unspektrawesome/preview/RawPreviewPlanSelector.kt'); policy=t('app/src/main/java/com/unspektrawesome/camera/RawPreviewPolicy.java'); sess=t('app/src/main/java/com/unspektrawesome/camera/session/Camera2RawSession.java'); pack=t('app/src/main/java/com/unspektrawesome/camera/session/PackedRawPlaneBuffer.java'); ctrl=t('app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt'); hist=t('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/SpektraLiveHistogramView.java'); mode=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java'); ui=t('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java'); layout=t('app/src/main/res/layout/camera_fragment.xml'); vr=t('app/src/main/java/com/unspektrawesome/vulkan/VulkanRenderer.kt')
# Exact failed 26692 R1 compiler condition remains permanently blocked.
assert plan.count('import com.unspektrawesome.camera.RawFormat')==1
assert 'candidateFormats: Set<RawFormat>' in plan
# 26692 RAW carrier/route + 26691 LSC behavior preserved byte-identical because those owners are outside 26693 scope.
for rel in ['app/src/main/java/com/unspektrawesome/preview/RawPreviewPlanSelector.kt','app/src/main/java/com/unspektrawesome/camera/RawPreviewPolicy.java','app/src/main/java/com/unspektrawesome/camera/session/Camera2RawSession.java','app/src/main/java/com/unspektrawesome/camera/session/PackedRawPlaneBuffer.java','app/src/main/java/com/unspektrawesome/camera/session/RawHardwareFrame.java']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
assert 'HardwareBuffer.USAGE_GPU_SAMPLED_IMAGE' not in sess
assert sess.count('PackedRawPlaneBuffer.prepare(')==2
assert 'case RAW_SENSOR:' in pack and 'width * 2L' in pack and 'hardwareBufferImport=false' in sess
assert 'new RawFormat[]{RawFormat.RAW10, RawFormat.RAW12, RawFormat.RAW_SENSOR}' in policy
# Still capture no preview-LSC gate and still metadata precedence remains.
assert 'requireNotNull(latestLensShadingMap)' not in ctrl
assert re.search(r'val\s+captureLensShading\s*=\s*stillLensShading\s*\?:\s*request\.lensShadingMap',ctrl)
# Photo histogram producer must remain byte-identical.
iris='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java'; assert (c/iris).read_bytes()==(b/iris).read_bytes()
# 26692 crash exact condition cannot recur; custom Iris worker is forbidden.
assert 'pixels.length' not in hist or 'pixels == null' in hist
for bad in ('HandlerThread','Iris26692SpektraHistogram','startPolling()','pollOnce()'):
 assert bad not in hist
assert 'public int[] histogramPixels' not in mode and 'fun histogramPixels(scale' not in ctrl
assert 'nativeHistogramPixels(current, scale) ?: IntArray(0)' in vr
# Lifecycle states cannot be owned by histogram: producer is render-success scoped and failures are contained.
assert 'publishHistogramFromRenderedFrameLocked(owner, now)' in ctrl
assert 'runCatching { listener.onHistogramPixels(pixels) }.onFailure' in ctrl
assert 'clearHistogramLocked()' in ctrl
# Exact device UI failure: dummy preview may change; final fixed chrome must not consume it.
assert layout.count('app:layout_constraintBottom_toBottomOf="@id/control_geometry_reference"')==2
assert 'controlReferenceBottom + previewClearancePx' in ui
assert 'viewfinderBottom + previewClearancePx' not in ui
assert 'IRIS_26693_UI_GEOMETRY_INVARIANT' in ui
# Video retains appearance/state but may not own scale/position math.
assert 'R.drawable.video_record_button' in ui
m=ui[ui.index('private void applyAdaptiveBottomSafeLayout'):ui.index('private void applyBottomGeometry')]
assert 'if (videoStyle' not in m and 'if(videoStyle' not in m
# Unspektra AE remains exact owner; native 1.1.2 is unchanged.
ae='app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraExposureController.java'; assert (c/ae).read_bytes()==(b/ae).read_bytes(); assert 'SpektraExposureController' in ctrl and 'pollExposureMeter' in ctrl
so=(c/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so').read_bytes(); import hashlib; assert hashlib.sha256(so).hexdigest()=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd'
assert b'Java_com_unspektrawesome_vulkan_VulkanRenderer_nativeHistogramPixels' in so
print('PASS 26693 permanent regressions: 26692 RawFormat/compiler + RAW carrier/LSC + final UI invariant + histogram null/lifecycle/duplicate-owner rejection')
