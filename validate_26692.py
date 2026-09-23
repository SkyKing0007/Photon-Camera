#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26692.py BASE CANDIDATE')
base=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def t(rel): return (c/rel).read_text()
def H(root): return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
bh,ch=H(base),H(c)
changed=sorted(set(bh)^set(ch)|{k for k in bh.keys()&ch if bh[k]!=ch[k]})
expected=[x for x in (pkg/'R1_26692_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
assert len(bh)==len(ch)==1822 and changed==expected,(len(bh),len(ch),changed,expected)
plan=t('app/src/main/java/com/unspektrawesome/preview/RawPreviewPlanSelector.kt')
policy=t('app/src/main/java/com/unspektrawesome/camera/RawPreviewPolicy.java')
sess=t('app/src/main/java/com/unspektrawesome/camera/session/Camera2RawSession.java')
frame=t('app/src/main/java/com/unspektrawesome/camera/session/RawHardwareFrame.java')
pack=t('app/src/main/java/com/unspektrawesome/camera/session/PackedRawPlaneBuffer.java')
ctrl=t('app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt')
hist=t('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/SpektraLiveHistogramView.java')
frag=t('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java')
layout=t('app/src/main/res/layout/camera_fragment.xml')
ui=t('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
# Exact 1.1.2-compatible stream preference and universal packed carrier.
assert 'rawSensorOutputs' not in plan and 'previewOutputs = selectedOutput?.let(::listOf) ?: eligibleOutputs' in plan
assert 'new RawFormat[]{RawFormat.RAW10, RawFormat.RAW12, RawFormat.RAW_SENSOR}' in policy
assert 'HardwareBuffer.USAGE_GPU_SAMPLED_IMAGE' not in sess and 'HardwareBuffer.USAGE_CPU_READ_OFTEN' in sess
assert sess.count('PackedRawPlaneBuffer.prepare(')==2 and 'hardwareBufferImport=false' in sess
assert 'RAW_SENSOR must use its HardwareBuffer image' not in frame
for x in ('case RAW10:','case RAW12:','case RAW_SENSOR:','width * 2L','rowStrideBytes * (height - 1L) + meaningfulRowBytes'): assert x in pack,x
# 26691 LSC and Spektra saved owner retained.
assert 'requireNotNull(latestLensShadingMap)' not in ctrl
assert re.search(r'val\s+captureLensShading\s*=\s*stillLensShading\s*\?:\s*request\.lensShadingMap',ctrl)
for marker in ('IRIS_26691_SPEKTRA_CAPTURE_ACCEPT','IRIS_26691_SPEKTRA_RCD_OK','IRIS_26691_SPEKTRA_JPEG_SAVED'): assert marker in ctrl
assert 'ROW_STRIDE_BUFFER' in ctrl
# Unspektra AE remains authority; no speculative brightness multiplier.
ae='app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraExposureController.java'
assert (c/ae).read_bytes()==(base/ae).read_bytes()
assert 'SpektraExposureController' in ctrl and 'pollExposureMeter' in ctrl
# Spektra histogram data is reduced, never drawn as the mini preview; Photo histogram untouched.
iris='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java'
assert (c/iris).read_bytes()==(base/iris).read_bytes()
assert 'drawBitmap' not in hist and 'Bitmap.createBitmap' not in hist and 'BINS = 64' in hist
for token in ('Color.rgb(255, 70, 70)','Color.rgb(68, 235, 96)','Color.rgb(70, 115, 255)','darkCap = max * 1.25f'): assert token in hist
assert 'spektra_histogram_toggle' not in layout and 'spektraHistogramToggle' not in frag and 'spektraHistogramEnabled' not in frag
for token in ('android:layout_width="108dp"','android:layout_height="38dp"','android:layout_marginTop="12dp"','android:layout_marginEnd="8dp"','android:background="@drawable/exif_background"','android:elevation="16dp"'): assert token in layout
assert 'setSpektraActive(spektraVisible)' in frag
# Video/RAW Video keeps recording visuals but shares Photo geometry.
for bad in ('88.0f * density','74.0f * density','-48.0f * density','-30.0f * density'): assert bad not in ui,bad
for good in ('preferredLensTranslationY = 0.0f','params.width = Math.round(92.0f * density)','params.height = Math.round(92.0f * density)','params.topMargin = Math.round(56.0f * density)','applyAdaptiveBottomSafeLayout(false);'): assert good in ui,good
assert ui.count('mShutterButton.setScaleX(0.83f)')>=2 and 'R.drawable.video_record_button' in ui
v=t('app/version.properties'); assert 'VERSION_NAME=0.9726692' in v and 'VERSION_BUILD=26692' in v
so=c/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so'
assert hashlib.sha256(so.read_bytes()).hexdigest()=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd'
print('PASS 26692 semantic/ownership validation: standalone-compatible RAW carrier, preserved Unspektra AE/LSC/native owner, Photo-style Spektra histogram, Photo geometry for Video/RAW Video')
