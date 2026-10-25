#!/usr/bin/env python3
"""26879 permanent real regression: B 50MP GPU intent, sensor-colored neon, Spektra RAW FOV.
Run only on the actual successful 26878 and reconstructed 26879 source universes.
"""
from pathlib import Path
import sys,math,hashlib,re
assert len(sys.argv)==3
A,B=(Path(x) for x in sys.argv[1:])
def read(root,part):return (root/'app/src/main/java'/part).read_text()
h='com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'
o,n=read(A,h),read(B,h)
assert 'prepareRawrBPublication26856(iris26856BTrue2xRgbPath != null)' in o
assert 'prepareRawrBPublication26856(iris26856BTrue2xRgbPath != null)' not in n
seg=n.split('IRIS_26879_B_50MP_GPU_INTENT_NO_LEGACY_FILE_GATE',1)[1].split('PostPipeline pipeline',1)[0]
for e in ['iris26879Requested2x = processingParameters.motionV2SuperResOutputEnabled',
          'iris26879Gpu2xPresent = mIris26876B2xGpuForCleanup != null',
          'iris26879GpuGuidePresent = mIris26876B1xGuideForCleanup != null',
          'iris26879Requested2x != iris26879Gpu2xPresent',
          'iris26879Requested2x != iris26879GpuGuidePresent',
          'processingParameters.prepareRawrBPublication26856(iris26879Requested2x)',
          'throw new IllegalStateException']:
 assert e in seg,('26878 50MP demotion reintroduced',e)
assert 'final boolean iris26876BFinalGpu = iris26856BOnly &&' in n
assert 'saveB26876SuperResGpuJpeg(' in n and 'saveB26876SuperResGpuHeic(' in n
p='com/hinnka/mycamera/processor/GlesIris26858BNoiseHighlight.kt';s=read(B,p)
assert 'IRIS_26879_NATIVE_B_COLORED_NEON_HUE_GUARD' in s
assert s.count('1.0-smoothstep(0.045,0.18,colorStrength)')==2
assert 'colorStrength=(hi-lo)/max(hi,0.0001)' in s
assert 'smoothstep(0.0,0.25,clippedCoverage)*nearNeutral' in s
# Numerical contract for saturated red/blue signs vs neutral white; true sensor evidence
# and the original WB-domain unmodified RGB are required. No neighbor hue donation.
def smooth(a,b,v):
 x=max(0.,min(1.,(v-a)/(b-a)));return x*x*(3.-2.*x)
def fade(rgb,clip):
 hi=max(rgb);lo=min(rgb);strength=(hi-lo)/max(hi,0.0001)
 return smooth(0.,0.25,clip)*(1.-smooth(.045,.18,strength))
for rgb in [(1.,.04,.04),(.02,.08,.98),(.9,.15,.01),(.02,.98,.13)]:
 assert fade(rgb,1.)==0.,('colored neon must remain chromatic',rgb)
assert abs(fade((.91,.9,.90),1.)-1.)<1e-9
assert fade((.2,.8,.2),0.)==0.
plan=read(B,'com/unspektrawesome/preview/RawPreviewPlanSelector.kt')
assert 'RawPreviewPolicy.selectCaptureOutput(eligibleOutputs, candidateFormats)' in plan
assert 'selectedOutput?.let(::listOf)' in plan
assert 'val allowedFormats = selectedOutput?.let { setOf(it.format) } ?: candidateFormats' in plan
assert 'TARGET_FRAMES_PER_SECOND' in plan
mode=read(B,'com/particlesdevs/photoncamera/spektra/SpektraModeController.java')
assert 'RawPreviewQuality.FULL,' in mode and 'RawPreviewQuality.LOW,' not in mode
# Sensor crop and Vulkan lifecycle must remain protected 26878 success bytes.
for p in ['com/unspektrawesome/capture/FrameGeometrySnapshot.kt',
          'com/unspektrawesome/preview/RawVulkanPreviewController.kt',
          'com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
          'com/particlesdevs/photoncamera/processing/ImageSaver.java']:
 assert hashlib.sha256(read(A,p).encode()).digest()==hashlib.sha256(read(B,p).encode()).digest(),p
print('PASS 26879 real 26878 50MP no-file regression, B-only colored-neon preservation, Spektra full still-matched RAW stream and inherited owners')
