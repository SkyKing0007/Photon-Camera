#!/usr/bin/env python3
"""26958 exact Iris HDRQ noise calibration, temporal pair and proven modes."""
import hashlib,re,subprocess,sys,shutil,tempfile
from pathlib import Path
from build_26958_incremental import R,scope,exact,fail

def require(src, tokens, label):
 for t in tokens:
  if t not in src: fail(label+" missing "+t)

def main():
 changed, added, old, new = scope()
 expected={
  'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp',
  'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp',
  'app/version.properties'
 }
 if changed!=expected or added or len(old)!=2055 or len(old)-len(changed)!=2052:
  fail('bad source scope')
 root=R if '--live' in sys.argv else R/'handoff_payload_26958'
 if '--live' in sys.argv: exact(R,'26958_EXPECTED_FULL_APP.sha256','live latest candidate')
 for f in changed:
  if hashlib.sha256((root/f).read_bytes()).hexdigest()!=new[f]:fail('bad candidate '+f)
 if 'VERSION_BUILD=26958' not in (root/'app/version.properties').read_text():fail('version build')
 owner=(root/'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp').read_text()
 coord=(root/'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp').read_text()
 require(owner,['if (!sr) { hdrq.strength = bOffReusable ? 11.0f : 13.0f; hdrq.tileSize = 32u; }',
 'sr?MergeAlgorithm::Wronski:MergeAlgorithm::HdrPlusFrequency','result.outputExtent.width!=frozen.width'], 'Photo B OFF strength 11, Night remains 13')
 require(coord,['recorder.setNoise(alpha*range,beta*range*range);',
 'const std::uint32_t neighbour = ref + 1u < frameCount ? ref + 1u : ref - 1u;',
 'std::rotate(order.begin(), where, where + 1u);',
 'if (pass == 0u && i == order.front() &&',
 'const auto fit = fitBurstNoise(static_cast<const float*>(noiseStats_.mapped), bx * by);',
 'if (fit && rawr::raw_merge_wronski_gpu::valid(fit->profile))',
 'recorder.setMeasuredRawNoise(slopes, offsets, measured);',
 'recorder.recordEffectiveFramesCopy(command_, noiseStats_.buffer);',
 'hdrqEffectiveFrames = float(double(tileCount) / inverse);',
 'singleFrameTiles','lowSupportTiles'], 'Rawr matched noise and nearest frame')
 # The old constant-variance fallback had an unsupported zero slope and a
 # noisy 20th percentile. No alternate generated model may feed the gate.
 region=coord.split('BurstRunResult AndroidBurstCoordinator::runHdrPlusFrequency(',1)[1]
 if 'offsets[s] = std::max(variances[q]' in region or 'std::nth_element(variances.begin()' in region:
  fail('old artificial constant-noise fallback survived')
 if 'const float* stats = static_cast<const float*>(noiseStats_.mapped)' in region.split('recorder.setMeasuredRawNoise',1)[0]:
  fail('unexpected pre-gate unqualified estimated profile')
 if coord.count('rawr::raw_merge_wronski_gpu::CfaNoiseProfile')!=2:
  fail('26957 V1 wrong noise-profile namespace restored')
 if '--live' in sys.argv:
  for f in ('app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp',
            'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp',
            'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMerge.comp',
            'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMismatchNorm.comp',
            'app/src/main/cpp/iris26864/bridge/Iris26864HdrqCanonicalGpuBridge.cpp',
            'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
            'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/pipeline/src/BurstNoiseEstimate.cpp',
            'app/src/main/assets/shaders/motionv2/render.glsl',
            'app/src/main/assets/shaders/motionv2/gainmap.glsl'):
   if hashlib.sha256((R/f).read_bytes()).hexdigest()!=old[f]:fail('protected shader/Rawr/SDR changed '+f)
   if f.endswith('.comp'):
    t=re.sub(r'/\*.*?\*/|//[^\n]*','',(R/f).read_text(),flags=re.S)
    if re.search(r'\b(?:float|int|uint|vec[234]|ivec[234])\s+(?:flat|coherent)\b',t):
     fail('GLSL illegal reserved identifier '+f)
  # Compile a stand-alone C++17 unit against the REAL successful vendor
  # noise header. Old 26957 V1 namespace negative remains historical.
  inc=R/'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/merge_wronski/include'
  unit="""+#include <rawr/raw_merge_wronski_gpu/RawMergeWronskiGpu.h>
+#include <algorithm>
+#include <vector>
+#include <optional>
+void verify(){std::vector<unsigned> v{0,1,2,3,4};auto w=std::find(v.begin(),v.end(),3u);std::rotate(v.begin(),w,w+1);
+ std::optional<rawr::raw_merge_wronski_gpu::CfaNoiseProfile> p;rawr::raw_merge_wronski_gpu::CfaNoiseProfile q{};
+ q.slopeBySite={.1f,.1f,.1f,.1f};q.offsetBySite={.001f,.001f,.001f,.001f};
+ if(rawr::raw_merge_wronski_gpu::valid(q))p=q;}
+""".replace('\n+','\n').lstrip('+')
  cc=shutil.which('clang++') or shutil.which('g++')
  if not cc:fail('C++17 host compiler missing')
  v=subprocess.run([cc,'-std=c++17','-Wall','-Wextra','-pedantic-errors','-Werror',
                    '-fsyntax-only','-x','c++','-','-I',str(inc)],input=unit,text=True,capture_output=True)
  if v.returncode:fail('pinned header/temporal order C++17 compile failed '+v.stderr[-400:])
 print('PASS 26958 3 exact B-only source changes, configured-noise fallback, adjacent RAW, 11/32, 2052 protected')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26958 SOURCE BLOCKED '+str(e),file=sys.stderr);sys.exit(1)
