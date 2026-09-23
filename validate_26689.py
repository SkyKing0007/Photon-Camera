#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26689.py BASE CANDIDATE')
base=Path(sys.argv[1]); cand=Path(sys.argv[2]); root=Path(__file__).resolve().parent
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in r.rglob('*') if p.is_file()}
def manifest(name):
 d={}
 for line in (root/name).read_text().splitlines():
  if line.strip(): h,p=line.split('  ',1); d[p]=h
 return d
b=H(base); c=H(cand); changed=sorted(p for p in set(b)|set(c) if b.get(p)!=c.get(p))
allowed=sorted(x.strip() for x in (root/'R1_26689_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip())
assert len(b)==1770 and len(c)==1819
assert changed==allowed, (len(changed), sorted(set(changed)^set(allowed))[:10])
assert sum(p not in b for p in changed)==49 and sum(p in b and p in c for p in changed)==6 and not any(p not in c for p in changed)
for a,bn in [('R1_26689_PROTECTED_UNCHANGED_BASE.sha256','R1_26689_PROTECTED_UNCHANGED_CANDIDATE.sha256'),('R1_26689_NATIVE_PROTECTED_BASE.sha256','R1_26689_NATIVE_PROTECTED_CANDIDATE.sha256'),('R1_26689_VENDOR_PROTECTED_BASE.sha256','R1_26689_VENDOR_PROTECTED_CANDIDATE.sha256'),('R1_26689_DNG_BASE.sha256','R1_26689_DNG_CANDIDATE.sha256'),('R1_26689_ASSET_SHADER_UNIVERSE_BASE.sha256','R1_26689_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256')]:
 assert (root/a).read_bytes()==(root/bn).read_bytes(), f'invariance manifest mismatch {a}'
# Exact version.
v=(cand/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726689' in v and 'VERSION_BUILD=26689' in v
# Exact Unspektrawesome binary provenance.
so=cand/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so'; params=cand/'app/src/main/assets/spektra/unspektrawesome_1_1_2_default_params.bin'
assert so.stat().st_size==18174352 and hashlib.sha256(so.read_bytes()).hexdigest()=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd'
assert params.stat().st_size==648 and hashlib.sha256(params.read_bytes()).hexdigest()=='0174eac3db67d158d72a61e841128e1c26841d523bb6df7841bb0c3a8d67a656'
# Shell / owner boundary.
mode=(cand/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java').read_text()
frag=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java').read_text()
cap=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
layout=(cand/'app/src/main/res/layout/layout_main_viewfinder.xml').read_text()
ctrl=(cand/'app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt').read_text()
vr=(cand/'app/src/main/java/com/unspektrawesome/vulkan/VulkanRenderer.kt').read_text()
sess=(cand/'app/src/main/java/com/unspektrawesome/camera/session/Camera2RawSession.java').read_text()
prefs=(cand/'app/src/main/java/com/unspektrawesome/settings/CameraPreferences.kt').read_text()
jpeg=(cand/'app/src/main/java/com/unspektrawesome/capture/JpegMediaStoreWriter.kt').read_text()
bg=(cand/'app/build.gradle').read_text()
assert 'SpektraCameraOwner' not in mode and 'RawVulkanPreviewController' in mode and 'RawPreviewQuality.LOW' in mode
assert 'VulkanRawPreviewView' in layout and '<SurfaceView\n                    android:id="@+id/spektra_surface"' not in layout
assert 'bindSpektraPreviewSurface(spektraSurfaceView, getViewLifecycleOwner())' in frag
assert 'onSpektraPreviewPreparing()' in frag and 'setSpektraPreviewVisible(true)' in frag
assert 'LifecycleOwner lifecycleOwner' in cap and 'VulkanRawPreviewView previewView' in cap
# 1.1.2 path contracts.
assert 'nativePollExposureMeter' in vr and 'nativeHistogramPixels' in vr and 'nativeBeginLensSwitchBlur' in vr and 'nativeWarmUp' in vr
assert 'false,\n            true,\n            true,\n            0,' in vr
assert '.warmUp(' not in ctrl
assert 'pollExposureMeter' in ctrl and 'updateExposureFromNativeMeter' in ctrl
assert 'acquireLatestImage()' in sess
assert 'session.capture(stillRequest' in sess or 'session.capture(request' in sess
assert 'DEFAULT_JPEG_QUALITY = 100' in jpeg
assert 'RawPreviewQuality.LOW' in prefs and 'RawPreviewQuality.MEDIUM.name' not in prefs
assert bg.count('org.jetbrains.kotlinx:kotlinx-coroutines-core:1.10.2')==1
# Old recreated frontend is allowed to remain byte-identical but cannot be active from the sole facade.
for forbidden in ('SpektraRawCpuOwner','SpektraRawVulkanOwner','SpektraRawDevelop'):
 assert forbidden not in mode, f'active facade references old owner: {forbidden}'
print('PASS 26689 semantic/ownership validation: exact 55-path Unspektrawesome-hosted mode')
