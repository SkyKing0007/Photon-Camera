#!/usr/bin/env python3
"""Active path and lifecycle regressions supplementary to mandatory real compilers."""
import argparse,subprocess,tempfile
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('app_root',type=Path);ap.add_argument('--numeric',action='store_true');a=ap.parse_args()
root=a.app_root.resolve();cpp=root/'src/main/cpp/iris26864'
t=(cpp/'Iris26864RealRawrCoordinator.cpp').read_text()
assert t.count('vkQueueWaitIdle(frozen.inheritedQueue)')==1
assert t.index('vkQueueWaitIdle(frozen.inheritedQueue)') < t.index('(void)coordinator.release()'), 'coordinator must be quarantined after failed queue idle'
assert 'if(!result.noiseEstimated)' in t,'Wronski unmeasured-burst noise must reject'
assert 'MergeAlgorithm::HdrPlusFrequency' in t,'native HDRq Higher Quality disabled'
s=(cpp/'Iris26864TwoSlotRaw16Uploader.cpp').read_text()
assert s.count('images_->allocate(width,height,VK_FORMAT_R16_UINT,usage);')==2
assert 'quarantineUnresolved()' in s
j=(cpp/'Iris26864JniGpuInteropImpl.inc').read_text()
assert 'publishedClip=true' in j and 'if(!publishedClip)' in j
assert 'recordWronski2xToAmaze(' in j
assert 'recordCanonicalCfaForAmaze(' in j
assert 'waitCurrentGlOnVulkanFence' in j
assert 'VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT' in j
print('PASS 26864 native RAWR HDRq/Wronski dual owner, measured noise, two-slot, fenced mask publication and coordinator quarantine semantics')
if a.numeric:
 fixture=Path(__file__).resolve().parent/'regressions/gpu_lifetime_mock'
 assert (fixture/'Iris26864RealRawrCoordinator.cpp').read_bytes()==(cpp/'Iris26864RealRawrCoordinator.cpp').read_bytes(), 'GPU RAII exact historical failing runtime source regression drift'
 with tempfile.TemporaryDirectory(prefix='26864_gpu_life_') as tmp:
  exe=Path(tmp)/'gpu_lifetime'
  subprocess.run(['c++','-std=c++17','-O2','-UNDEBUG','-I'+str(fixture),str(fixture/'test.cpp'),str(fixture/'Iris26864RealRawrCoordinator.cpp'),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
 for name in ('26864_clip2x_numeric','26864_sensor_clip2x_green_numeric'):
  src=Path(__file__).resolve().parent/'regressions/numeric'/(name+'.cpp')
  with tempfile.TemporaryDirectory(prefix='26864_num_') as tmp:
   exe=Path(tmp)/name
   subprocess.run(['c++','-std=c++17','-O2','-UNDEBUG','-I'+str(cpp),str(src),'-o',str(exe)],check=True)
   subprocess.run([str(exe)],check=True)
 # Permanent real-source regression for the proven unresolved-fence teardown:
 # compile EXACT runtime .cpp bytes with only Vulkan/RAWR interfaces doubled,
 # never a separately edited imitation of the implementation.
 mock=Path(__file__).resolve().parent/'regressions/gpu_lifetime_mock'
 source=cpp/'Iris26864RealRawrCoordinator.cpp'
 copied=mock/'Iris26864RealRawrCoordinator.cpp'
 assert copied.read_bytes()==source.read_bytes(),'GPU lifetime fixture drifted from exact candidate source'
 with tempfile.TemporaryDirectory(prefix='26864_gpu_lifetime_') as tmp:
  exe=Path(tmp)/'26864_coordinator_lifetime'
  subprocess.run(['c++','-std=c++17','-O2','-UNDEBUG','-I'+str(mock),str(copied),str(mock/'test.cpp'),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
 print('PASS 26864 original-sensor 2x reference/green, 1-bit sidecar and exact-runtime-source GPU lifetime host regressions; host checks only')
