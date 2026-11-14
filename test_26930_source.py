#!/usr/bin/env python3
"""26930 exact success-seeded 2041-file native B ON scope; protect everything else."""
from pathlib import Path
import sys
from build_26930_incremental import scope,sha
R=Path(__file__).resolve().parent
P=(R/'handoff_payload_26930') if '--payload' in sys.argv else R
changed,added,old,new=scope()
want={'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc',
      'app/src/main/cpp/iris26864/Iris26880WaveletCopy.comp','app/version.properties'}
assert changed==want and not added and len(old)==len(new)==2041
assert len(old.keys()-changed)==2038 and set(old)==set(new)
assert all(old[k]==new[k] for k in old if k not in changed)
assert 'VERSION_NAME=0.9726930\nVERSION_BUILD=26930' in (P/'app/version.properties').read_text()
a=(P/'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc').read_text()
s=(P/'app/src/main/cpp/iris26864/Iris26880WaveletCopy.comp').read_text()
for token in ('IRIS_26930_B_ON_PHYSICAL_LSC_SHADOW_CHROMA_VARIANCE',
              'layout(std430,set=0,binding=2) readonly buffer PhysicalLsc',
              'float conservativeSupport=mix(1.0,min(3.0,p.shot.a),confidence);',
              'vec3 channelVar=(p.shot.rgb*srcSensor+p.readNoise.rgb)*lsc*lsc*p.wb.rgb*p.wb.rgb;',
              ''):
 if token:assert token in s,token
assert 'float originalY=' in s and 'float restoreY=' in s
assert 'if(y>0.00035 && y<0.85' in s
assert 'for(int i=0;i<24;i++)' in s and 'float twoSided=' in s
assert 'min(3.0,p.shot.a)' in s
assert s.count('imageLoad(irisRgb,')==1 and 'imageLoad(denoisedRgb,at)' in s
assert 'static_assert(sizeof(WaveletCopy26930Pc)==80u' in a
assert '{2,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER}' in a
assert 'lscResource.buffer=lsc.buffer;' in a and 'lscResource.bufferRange=lsc.bytes' in a
assert 'const uint32_t redSite=localCfa,blueSite=3u-localCfa;' in a
assert 'fitted.slopeBySite[redSite]' in a and 'fitted.offsetBySite[blueSite]' in a
assert 'params.forceY=0.f;' in a and 'params.forceUv=.75f;' in a
# Absolute original RAWR wavelet remains pinned, not silently modified.
assert 'params.noiseA=f.burstGreenNoisePerMergedSample[0];' in a
assert 'params.noiseB=f.burstGreenNoisePerMergedSample[1];' in a
assert 'f.fallbackChromaGain' not in a
for path in ('app/src/main/java/com/particlesdevs/photoncamera/settings/Iris26926FallbackSettings.java',
             'app/src/main/cpp/iris26864/bridge/Iris26923WronskiFinalize.comp',
             'app/src/main/cpp/iris26864/Iris26885WronskiChromaGuide.comp',
             'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/merge_wronski/shaders/fallback_chroma.comp',
             'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/pipeline/src/BurstNoiseEstimate.cpp'):
 assert old[path]==new[path],path
if '--live' in sys.argv:
 for path in changed:assert sha(R/path)==new[path],path
print('PASS 26930 exact three changed / 2038 unchanged; sliders 4/2/16, vendor, SR OFF and A protected')
