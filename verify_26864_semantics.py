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

# IRIS_26864_KOTLIN_NAMED_ARGUMENT_REGRESSION_39708593393
# Actions 39708593393 failed at PhotonMotionMgc1271Bridge.kt:669/671 because
# Fusion and Sabre each dropped two named B-only constructor arguments.
# All THREE constructor declarations and BOTH intermediate value forwards
# must be present before a new guarded build is allowed to reach the Kotlin compiler.
bridge=(root/'src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
kt_dir=root/'src/main/java/com/hinnka/mycamera/processor'
fusion=(kt_dir/'GlesMgcRawFusion.kt').read_text()
sabre=(kt_dir/'GlesIris26545SabreProcessor.kt').read_text()
spatial=(kt_dir/'GlesMgcRawSpatialStacker.kt').read_text()
names=('iris26864RealRawrOwnsBurstNoise','iris26864NativeWronski2x')
def guarded_kotlin_adapter_contract(bridge, fusion, sabre, spatial):
    if bridge.count('iris26864RealRawrOwnsBurstNoise = !parameters.irisNightActive') != 1: return False
    if bridge.count('iris26864NativeWronski2x = if (sabreSuperResEnabled') != 1: return False
    for fragment in (fusion,sabre,spatial):
        for name in names:
            if fragment.count('private val '+name+':') != 1: return False
    for fragment in (fusion,sabre):
        for name in names:
            if fragment.count(name+' = '+name+',') != 1:return False
    if 'if (exactHistorical26850) {' not in sabre:return False
    legacy=sabre.split('if (exactHistorical26850) {',1)[1].split('return GlesMgcRawSpatialStacker(',1)[0]
    if 'GlesMgcRawSpatialStacker26850(' not in legacy:return False
    if any(name+' =' in legacy for name in names):return False
    return True
assert guarded_kotlin_adapter_contract(bridge,fusion,sabre,spatial),'exact 39708593393 missing B-only Kotlin adapter parameters/forwarders'
assert not guarded_kotlin_adapter_contract(bridge,fusion.replace('private val iris26864NativeWronski2x:', 'private val iris26864BROKEN:',1),sabre,spatial)
assert not guarded_kotlin_adapter_contract(bridge,fusion,sabre.replace('private val iris26864RealRawrOwnsBurstNoise:', 'private val iris26864BROKEN:',1),spatial)
print('PASS exact Kotlin Actions 39708593393 named-parameter regression: Bridge->Fusion->Sabre->Spatial; A isolated, negative fixture rejected')

# Audit EVERY named constructor argument across the four real runtime edges,
# not only the two names that happened to fail first on Actions 39708593393.
import re
def kt_params(src,stop):
    header=src[:src.index(stop)]
    return set(re.findall(r'^    (?:private val\s+)?([A-Za-z]\w*)\s*:',header,flags=re.M))
def kt_args(src,begin,end,spaces):
    assert src.count(begin)==1,(begin,src.count(begin))
    start=src.index(begin)+len(begin)
    stop=src.index(end,start)
    return set(re.findall(r'^ {'+str(spaces)+r'}([A-Za-z]\w*)\s*=',src[start:stop],flags=re.M))
ctors={
 'fusion':kt_params(fusion,'    fun processFrames'),
 'sabre':kt_params(sabre,'    fun processFrames'),
 'spatial':kt_params(spatial,'    private data class TextureLevel'),
}
bridges=[
 ('Bridge B -> Fusion',bridge,'val fusion = GlesMgcRawFusion(','\n            )\n',16,'fusion'),
 ('Bridge historical A -> Fusion',bridge,'GlesMgcRawFusion(\n                    width','\n                ).processFrames',20,'fusion'),
 ('Fusion -> Sabre',fusion,'return GlesIris26545SabreProcessor(','\n        ).processFrames',12,'sabre'),
 ('Sabre B -> Spatial',sabre,'return GlesMgcRawSpatialStacker(','\n        ).processFrames',12,'spatial')]
for title,source,begin,end,indent,receiver in bridges:
    args=kt_args(source,begin,end,indent)
    missing=args-ctors[receiver]
    assert not missing,(title,'unknown receiver constructor arguments',sorted(missing))
    print('PASS Kotlin named arguments',title,len(args),'names')
