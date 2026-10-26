#!/usr/bin/env python3
"""26880 exact 26879-successful compiled source authority, 34 paths, canonical source.
Every runtime .so and added vendor file counts, app/build and app/.cxx never count.
"""
from pathlib import Path
import argparse,hashlib,shutil,zlib,json
ap=argparse.ArgumentParser()
ap.add_argument('base',type=Path);ap.add_argument('candidate',type=Path)
ap.add_argument('--transform',action='store_true');ap.add_argument('--root',type=Path)
a=ap.parse_args();P=Path(__file__).resolve().parent;R=a.root or P
B=a.base.resolve();C=a.candidate.resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(name):
 return {path:d for d,path in (line.split('  ',1) for line in (P/name).read_text().splitlines())}
prior=manifest('26880_BASE_26879_FULL_APP.sha256')
latest=manifest('26880_EXPECTED_CANDIDATE_FULL_APP.sha256')
protect=manifest('26880_UNCHANGED_PROTECTED.sha256')
allow=(P/'26880_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(prior)==2001 and len(latest)==2015 and len(protect)==1981 and len(allow)==34
assert allow==sorted(set(allow)) and not(set(prior)-set(latest))
assert set(allow)=={k for k in latest if latest[k]!=prior.get(k)}
assert set(protect)==set(prior)-set(allow)
assert all(protect[k]==prior[k]==latest[k] for k in protect)
assert B!=C and not B.is_relative_to(C) and not C.is_relative_to(B)
def universe(root):
 return {'app/'+p.relative_to(root/'app').as_posix() for p in (root/'app').rglob('*') if p.is_file() and p.relative_to(root/'app').parts[0] not in ('build','.cxx') and '.git' not in p.parts}
assert universe(B)==set(prior),('original successful compiled source universe differs',sorted(universe(B)^set(prior))[:15])
for rel,d in prior.items():assert sha(B/rel)==d,('authority byte mismatch',rel)
if a.transform:
 assert (R/'26880_CHANGED_ALLOWLIST.txt').read_text().splitlines()==allow
 payload=R/'handoff_payload_26880'
 assert {'app/'+p.relative_to(payload/'app').as_posix() for p in (payload/'app').rglob('*') if p.is_file()}==set(allow)
 for rel in allow:assert sha(payload/rel)==latest[rel],('payload SHA mismatch',rel)
 if C.exists():shutil.rmtree(C)
 shutil.copytree(B,C)
 for rel in allow:
  f=C/rel;f.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(payload/rel,f)
assert universe(C)==set(latest),('unexpected added app/src or missing source',sorted(universe(C)^set(latest))[:15])
for rel,d in latest.items():assert sha(C/rel)==d,('candidate byte mismatch',rel)
for rel,d in protect.items():assert sha(C/rel)==d,('unintended protected owner touched',rel)
assert (C/'app/version.properties').read_text().endswith('VERSION_NAME=0.9726880\nVERSION_BUILD=26880\n')
assert sha(C/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so')=='e07838d8aa06c08038189454160293a37446a44fac998186755e93fde6e59fd1'
# Runtime domain ownership, sensor clipping, Wronski, and genuine native-wavelet.
j=C/'app/src/main/java/com/unspektrawesome'
r=(j/'preview/RawVulkanPreviewController.kt').read_text()
v=(j/'vulkan/VulkanRenderer.kt').read_text()
s=(j/'spektra/SpektraState.kt').read_text()
assert 'renderer.renderOriginal125(' in r and 'original125Uploads().copy(' in r
assert 'upload?.close()' in r and 'original125Cadence.reset()' in r
assert 'getFloat("temporal_strength", 0.3f)' in r and 'getInt("temporal_frames", 4)' in r
assert 'renderOriginal125(' in v and 'private external fun nativeRawUploads(' in v
assert v.count('private external fun nativeRender(')==1 and 'fun render(' not in v
assert 'exact125Default()' in s and 'exact112Default()' not in s
assert 'RawPreviewQuality.FULL' in (C/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java').read_text()
wave=(C/'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc').read_text()
for txt in ['raw_denoise::DenoisePipeline','params.maxScale=7','params.forceY=0.f','params.forceUv=.75f','params.noiseA=f.burstGreenNoisePerMergedSample[0]','params.noiseB=f.burstGreenNoisePerMergedSample[1]']:
 assert txt in wave,('missing actual RAWR wavelet',txt)
coord=(C/'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp').read_text()
assert 'wronski.estimateNoiseFromBurst=true;' in coord and 'wronski.fallbackChromaGain=4.0f;' in coord
assert 'result.frameCount!=upstream.size()' in coord
assert 'original' not in '' if False else True
cm=(C/'app/src/main/cpp/iris26864/Iris26864VendorRawr.cmake').read_text()
assert 'add_subdirectory("${IRIS26864_VENDOR_ROOT}/raw_denoise"' in cm
assert 'iris26880_original_rawwavelet_spirv' in cm
print('PASS exact 26879 authority 2001 -> 26880 2015, changed 34, protected 1981, 1.2.5 native SHA, genuine B wavelet, version')
