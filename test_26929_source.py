#!/usr/bin/env python3
from pathlib import Path
import sys
from build_26929_incremental import scope,sha
R=Path(__file__).resolve().parent
P=(R/'handoff_payload_26929') if '--payload' in sys.argv else R
changes,added,original,target=scope()
want={'app/src/main/cpp/iris26864/Iris26880WaveletCopy.comp',
      'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc','app/version.properties'}
assert changes==want and not added
assert len(original)==len(target)==2041 and len(original.keys()-changes)==2038
v=(P/'app/version.properties').read_text()
assert 'VERSION_NAME=0.9726929\nVERSION_BUILD=26929' in v
sh=(P/'app/src/main/cpp/iris26864/Iris26880WaveletCopy.comp').read_text()
inc=(P/'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc').read_text()
for t in ('IRIS_26929_B_ON_LOCAL_NOISE_AWARE_CHROMA_GRAIN',
          'readonly uniform image2D denoisedRgb;',
          'coherent uniform image2D irisRgb;',
          'float singleShotA;float singleReadB;',
          'float localVar=mix(singleVar,singleVar/max(p.mergedFrames,2.0),confidence);',
          'vec4 source=imageLoad(irisRgb,q);',
          'float yRestore=',
          'for(int i=0;i<12;i++)',
          'vec3 otherRaw=imageLoad(denoisedRgb,at).rgb;',
          'chromaGain=0.52*need*donorCoherence*suspect',
          'shift-=vec3(dot(shift,kLuma));',
          'imageStore(irisRgb,q,vec4(max(outColor,vec3(0)),confidence));'):
 assert t in sh,t
assert sh.count('imageLoad(irisRgb,')==1 and sh.count('imageStore(irisRgb,')==2
assert sh.count('imageLoad(denoisedRgb,')==2
assert 'IRIS_26929_B_ON_LOCAL_NOISE_AWARE_CHROMA_GRAIN' in inc
assert 'static_assert(sizeof(WaveletCopy26929Pc)==32u,' in inc
assert 'f.burstGreenNoisePerMergedSample[0]*float(f.burstNormalCount)' in inc
assert 'f.burstGreenNoisePerMergedSample[1]*float(f.burstNormalCount)' in inc
assert 'params.forceY=0.f;' in inc and 'params.forceUv=.75f;' in inc
assert 'f.fallbackChromaGain' not in inc
for name in ('app/src/main/java/com/particlesdevs/photoncamera/settings/Iris26926FallbackSettings.java',
             'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp',
             'app/src/main/cpp/iris26864/bridge/Iris26923WronskiFinalize.comp',
             'app/src/main/cpp/iris26864/Iris26885WronskiChromaGuide.comp'):
 assert target[name]==original[name],name
for name in original:
 if name not in changes:assert target[name]==original[name],name
if '--live' in sys.argv:
 for name in changes:assert sha(R/name)==target[name],name
print('PASS 26929 actual source 3 changed/2038 protected; no SR OFF, fallback settings, vendor, or other runtime mutation')
