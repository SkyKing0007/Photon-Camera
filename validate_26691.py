#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26691.py BASE CANDIDATE')
base=Path(sys.argv[1]); cand=Path(sys.argv[2]); root=Path(__file__).resolve().parent
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in r.rglob('*') if p.is_file()}
def manifest(name):
 d={}
 for line in (root/name).read_text().splitlines():
  if line.strip(): h,p=line.split('  ',1); d[p]=h
 return d
b=H(base); c=H(cand); changed=sorted(p for p in set(b)|set(c) if b.get(p)!=c.get(p))
allowed=sorted(x.strip() for x in (root/'R1_26691_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip())
assert len(b)==1820 and len(c)==1822
assert changed==allowed, (len(changed), sorted(set(changed)^set(allowed))[:10])
assert sum(p not in b for p in changed)==2 and sum(p in b and p in c for p in changed)==5 and not any(p not in c for p in changed)
for a,bn in [('R1_26691_PROTECTED_UNCHANGED_BASE.sha256','R1_26691_PROTECTED_UNCHANGED_CANDIDATE.sha256'),('R1_26691_NATIVE_PROTECTED_BASE.sha256','R1_26691_NATIVE_PROTECTED_CANDIDATE.sha256'),('R1_26691_VENDOR_PROTECTED_BASE.sha256','R1_26691_VENDOR_PROTECTED_CANDIDATE.sha256'),('R1_26691_DNG_BASE.sha256','R1_26691_DNG_CANDIDATE.sha256'),('R1_26691_ASSET_SHADER_UNIVERSE_BASE.sha256','R1_26691_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256')]:
 assert (root/a).read_bytes()==(root/bn).read_bytes(), f'invariance manifest mismatch {a}'
v=(cand/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726691' in v and 'VERSION_BUILD=26691' in v
so=cand/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so'
assert so.stat().st_size==18174352
assert hashlib.sha256(so.read_bytes()).hexdigest()=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd'
raw=so.read_bytes(); assert raw.count(b'com/unspektrawesome/diagnostics/InternalLogRecorder')==1
assert b'recordNative' in raw and raw.count(b'(ILjava/lang/String;Ljava/lang/String;)V')==1
mode=(cand/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java').read_text()
ctrl=(cand/'app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt').read_text()
frag=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java').read_text()
layout=(cand/'app/src/main/res/layout/camera_fragment.xml').read_text()
hist=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/SpektraLiveHistogramView.java').read_text()
iris='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java'
assert (cand/iris).read_bytes()==(base/iris).read_bytes(), 'ordinary Iris histogram source changed'
assert 'requireNotNull(latestLensShadingMap)' not in ctrl
assert re.search(r'val\s+captureLensShading\s*=\s*stillLensShading\s*\?:\s*request\.lensShadingMap',ctrl)
assert 'val lensShadingMap: LensShadingMapParameters?' in ctrl
assert 'lensShadingByteBuffer(captureLensShading)' in ctrl
for marker in ('IRIS_26691_SPEKTRA_CAPTURE_ACCEPT','IRIS_26691_SPEKTRA_STILL_RAW','IRIS_26691_SPEKTRA_RCD_OK','IRIS_26691_SPEKTRA_JPEG_SAVED'):
 assert marker in ctrl, marker
assert 'fun histogramPixels(scale: Float): IntArray' in ctrl
assert 'renderer.histogramPixels(scale)' in ctrl
assert 'public int[] histogramPixels(float scale)' in mode
assert 'NATIVE_SIDE = 128' in hist and 'NATIVE_PIXELS = NATIVE_SIDE * NATIVE_SIDE' in hist
assert 'active.histogramPixels(1.0f)' in hist
assert 'IrisLiveHistogramView' not in hist and 'PixelCopy' not in hist and 'GLPreview' not in hist
assert 'spektra_live_histogram' in layout
assert 'android:id="@+id/spektra_histogram_toggle"' in layout
assert 'ic_spektra_histogram' in layout
assert 'spektraHistogramEnabled = false' in frag
assert 'spektraHistogramEnabled = !spektraHistogramEnabled' in frag
assert 'setSpektraActive(spektraVisible && spektraHistogramEnabled)' in frag
assert 'IRIS_26691_SPEKTRA_HISTOGRAM_TOGGLE_OWNER' in frag
assert 'R.id.iris_live_histogram' in frag and 'spektraVisible ? View.GONE : View.VISIBLE' in frag
ctor=mode[mode.index('public SpektraModeController('):mode.index('public synchronized void bindPreviewSurface')]
bind=mode[mode.index('public synchronized void bindPreviewSurface'):mode.index('private synchronized RawVulkanPreviewController ensureControllerForActivation')]
ensure=mode[mode.index('private synchronized RawVulkanPreviewController ensureControllerForActivation'):mode.index('private void failActivation')]
assert 'new RawVulkanPreviewController' not in ctor and 'new RawVulkanPreviewController' not in bind
assert mode.count('new RawVulkanPreviewController')==1 and ensure.count('new RawVulkanPreviewController')==1
print('PASS 26691 semantic/ownership validation: Spektra nullable-LSC still capture + native histogram only; successful-26690 startup/viewfinder ownership preserved')
