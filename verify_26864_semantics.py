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

# IRIS_26864_VULKAN_BARRIER_ARGCOUNT_REGRESSION_39710810277
# Exact NDK error: a nine-argument vkCmdPipelineBarrier at RAW16 uploader line 19.
# The Vulkan 1.0 ABI requires 10 args; no legacy compiler bypass is allowed.
import re as _vkre
import tempfile as _vktmp
from pathlib import Path as _vkp

_uploader_path = root/'src/main/cpp/iris26864/Iris26864TwoSlotRaw16Uploader.cpp'
_uploader_source = _uploader_path.read_text()
_nine_arg_barrier = 'vkCmdPipelineBarrier(c,srcStage,dstStage,0,0,nullptr,0,1,&b);'
_ten_arg_barrier = 'vkCmdPipelineBarrier(c,srcStage,dstStage,0,0,nullptr,0,nullptr,1,&b);'
assert _nine_arg_barrier not in _uploader_source, 'reintroduced exact NDK 39710810277 nine-argument barrier'
assert _uploader_source.count(_ten_arg_barrier)==1, 'missing corrected RAW16 image barrier'

def _vulkan_call_arguments(source, index):
    opening=source.index('(',index)
    level=1
    count=1
    k=opening+1
    while k<len(source) and level:
        ch=source[k]
        if ch=='(':level+=1
        elif ch==')':level-=1
        elif ch==',' and level==1:count+=1
        k+=1
    assert level==0, 'unterminated Vulkan barrier invocation'
    return count

def _vulkan_barrier_count(source):
    matches=list(_vkre.finditer(r'\bvkCmdPipelineBarrier\s*\(',source))
    counts=[_vulkan_call_arguments(source,m.start()) for m in matches]
    assert all(n==10 for n in counts), ('Vk 1.0 barrier requires ten args', counts)
    return len(matches)

_all_barrier_calls=0
for _native in sorted((root/'src/main/cpp/iris26864').rglob('*')):
    if _native.is_file() and _native.suffix in ('.cpp','.inc','.hpp','.h'):
        src=_native.read_text()
        if 'vkCmdPipelineBarrier(' in src:
            _all_barrier_calls+=_vulkan_barrier_count(src)
assert _all_barrier_calls>=10, ('incomplete Vulkan barrier source scan',_all_barrier_calls)
assert _vulkan_call_arguments(_nine_arg_barrier,0)==9, 'historical failure regression no longer represents original error'

if a.numeric:
    # Compile the EXACT production function body with the authentic ten-parameter
    # Vulkan ABI shape from NDK 27 (using host declarations as a syntax test).
    _start=_uploader_source.index('void transition(')
    _begin=_uploader_source.index('{',_start)
    _depth=1;_end=_begin+1
    while _depth:
        assert _end<len(_uploader_source)
        if _uploader_source[_end]=='{':_depth+=1
        elif _uploader_source[_end]=='}':_depth-=1
        _end+=1
    _actual_transition=_uploader_source[_start:_end]
    _vulkan_abi='''#include <cstdint>
#include <cstddef>
using VkCommandBuffer=void*;
using VkImage=void*;
using VkImageLayout=uint32_t;
using VkAccessFlags=uint32_t;
using VkPipelineStageFlags=uint32_t;
using VkDependencyFlags=uint32_t;
struct VkMemoryBarrier {};
struct VkBufferMemoryBarrier {};
struct VkImageSubresourceRange {uint32_t aspectMask,baseMipLevel,levelCount,baseArrayLayer,layerCount;};
struct VkImageMemoryBarrier {
 uint32_t sType; VkAccessFlags srcAccessMask,dstAccessMask;
 VkImageLayout oldLayout,newLayout; uint32_t srcQueueFamilyIndex,dstQueueFamilyIndex;
 VkImage image; VkImageSubresourceRange subresourceRange;
};
constexpr uint32_t VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER=1;
constexpr uint32_t VK_QUEUE_FAMILY_IGNORED=~uint32_t{0};
constexpr uint32_t VK_IMAGE_ASPECT_COLOR_BIT=1;
void vkCmdPipelineBarrier(VkCommandBuffer,VkPipelineStageFlags,VkPipelineStageFlags,
    VkDependencyFlags,uint32_t,const VkMemoryBarrier*,uint32_t,
    const VkBufferMemoryBarrier*,uint32_t,const VkImageMemoryBarrier*);
'''
    with _vktmp.TemporaryDirectory(prefix='26864_native_vk_abi_') as _dir:
        test=_vkp(_dir)/'production_transition.cpp'
        test.write_text(_vulkan_abi+_actual_transition+'\n')
        ok=subprocess.run(['c++','-std=c++17','-Werror','-fsyntax-only',str(test)],capture_output=True,text=True)
        assert ok.returncode==0,('exact source failed Vulkan signature harness',ok.stderr)
        old_transition=_actual_transition.replace(_ten_arg_barrier,_nine_arg_barrier,1)
        assert old_transition!=_actual_transition
        test.write_text(_vulkan_abi+old_transition+'\n')
        bad=subprocess.run(['c++','-std=c++17','-Werror','-fsyntax-only',str(test)],capture_output=True,text=True)
        assert bad.returncode!=0 and ('too few arguments' in bad.stderr or 'requires 10 arguments' in bad.stderr),('original NDK error did not reproduce',bad.stderr)
print('PASS Vulkan NDK 39710810277 regression:',_all_barrier_calls,'native pipeline barriers exact 10-argument ABI; host positive/negative '+('PASS' if a.numeric else 'NOT RUN'))

# IRIS_26864_NDK_VK11_MEMORY_REQUIREMENTS_REGRESSION_39712359645
# NDK27 clang fails when a directly linked Vulkan 1.1 function symbol is
# used as a Boolean (Werror,-Wpointer-bool-conversion), ResourceArena.cpp:85/182.
# Test the actual candidate statements with the authentic Vulkan 1.1 core ABI
# and demonstrate that reintroducing each original condition causes Clang to fail.
import hashlib as _v11hash
import shutil as _v11shutil
_vendor=cpp/'vendor/rawr'
_memory_source=(_vendor/'native/multiframe/pipeline/src/ResourceArena.cpp').read_text()
_memory_proof=__import__('json').loads((_vendor/'IRIS26864_TWOSLOT_RUNTIME_SOURCE_PROOF.json').read_text())
_memory_lock=__import__('json').loads((_vendor/'IRIS26864_RAWR_VENDOR_SOURCE_LOCK.json').read_text())
_adapter=_memory_proof['android_vk11_memory_requirements_adapter']
assert _adapter['upstream_sha256']==_memory_lock['files'][_adapter['relative_path']]['sha256']
assert _v11hash.sha256(_memory_source.encode()).hexdigest()==_adapter['candidate_sha256']=='ad3749757076a9e43a6697a36341b081021b6d2252833477ac4defbe34b8ee83'
_device_source=(root/'src/main/cpp/iris26856/amaze/src/VulkanDeviceOwner.cpp').read_text()
assert 'app.apiVersion = VK_API_VERSION_1_1;' in _device_source
assert 'if (props.apiVersion < VK_API_VERSION_1_1) continue;' in _device_source
assert 'vkGetImageMemoryRequirements2(d, &requirementsInfo, &requirements);' in _memory_source
assert 'vkGetBufferMemoryRequirements2(d, &requirementsInfo, &requirements);' in _memory_source
assert 'requirements.pNext = &dedicated;' in _memory_source
assert _memory_source.count('dedicated.requiresDedicatedAllocation == VK_TRUE')==2
assert not __import__('re').search(r'if\s*\(\s*vkGet(?:Image|Buffer)MemoryRequirements2\s*\)',_memory_source)
# Broader native source scan for this entire function-address misuse class.
for _src_file in (root/'src/main/cpp').rglob('*'):
 if _src_file.is_file() and _src_file.suffix in ('.cpp','.cc','.c','.h','.hpp','.inc'):
  _data=_src_file.read_text(errors='replace')
  assert not __import__('re').search(r'if\s*\(\s*(?:vkGetBufferMemoryRequirements2|vkGetImageMemoryRequirements2)\s*\)',_data),('reintroduced NDK 39712359645 function pointer check',_src_file)
if a.numeric:
 clang=_v11shutil.which('clang++')
 assert clang is not None,'real Clang required for Android NDK pointer-bool-conversion regression'
 # Extract exact new ABI invocation statements rather than rewrite by hand.
 _call_img='vkGetImageMemoryRequirements2(d, &requirementsInfo, &requirements);'
 _call_buf='vkGetBufferMemoryRequirements2(d, &requirementsInfo, &requirements);'
 _header="""#include <cstdint>
struct VkDevice_T; using VkDevice=VkDevice_T*;
struct VkImageMemoryRequirementsInfo2{uint32_t sType; void* pNext;};
struct VkBufferMemoryRequirementsInfo2{uint32_t sType; void* pNext;};
struct VkMemoryRequirements2{uint32_t sType; void* pNext;};
void vkGetImageMemoryRequirements2(VkDevice,const VkImageMemoryRequirementsInfo2*,VkMemoryRequirements2*);
void vkGetBufferMemoryRequirements2(VkDevice,const VkBufferMemoryRequirementsInfo2*,VkMemoryRequirements2*);
"""
 with tempfile.TemporaryDirectory(prefix='26864_vk11_ndk_regression_') as _temporary:
  _cpp=Path(_temporary)/'ResourceArena_abi.cpp'
  for typ,call in [('Image',_call_img),('Buffer',_call_buf)]:
   assert _memory_source.count(call)==1
   def _build(negative):
    _statement=('if ('+('vkGetImageMemoryRequirements2' if typ=='Image' else 'vkGetBufferMemoryRequirements2')+') {\n '+call+'\n}' if negative else call)
    _cpp.write_text(_header+f'void runtime(VkDevice d){{Vk{typ}MemoryRequirementsInfo2 requirementsInfo{{}};VkMemoryRequirements2 requirements{{}};'+_statement+'}\n')
    return subprocess.run([clang,'-std=c++17','-Wall','-Wextra','-Werror=pointer-bool-conversion','-fsyntax-only',str(_cpp)],capture_output=True,text=True)
   positive=_build(False);assert positive.returncode==0,('real Clang rejects updated Vulkan 1.1 call',positive.stderr)
   negative=_build(True);assert negative.returncode!=0 and ('pointer-bool-conversion' in negative.stderr or 'always evaluate to' in negative.stderr),('historical NDK failure not detected',negative.stderr)
 print('PASS real Clang Vulkan 1.1 typed-memory ABI: image+buffer positive and historical two negative fixtures')
print('PASS exact native 39712359645 regression: Vulkan 1.1 core gate, unchanged dedicated requirements, pinned RAWR lock, no symbol-boolean checks')
