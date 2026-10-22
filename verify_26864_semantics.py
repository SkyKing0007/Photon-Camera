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
# IRIS_26864_NDK_VK11_UNRESOLVED_LINK_REGRESSION_39714213244
# Android NDK: function addresses of directly linked Vulkan functions cannot
# be queried as bool; additionally >=1.1 API support does NOT imply that its
# core Vulkan 1.1 symbols are linkable from Android's libvulkan.so stub.
# Require typed device-proc dispatch and test actual production snippets
# against an Android-like linker stub exporting NO post-1.0 functions.
import hashlib as _v11hash
import shutil as _v11shutil
import re as _v11re
_vendor=cpp/'vendor/rawr'
_memory_source=(_vendor/'native/multiframe/pipeline/src/ResourceArena.cpp').read_text()
_memory_proof=__import__('json').loads((_vendor/'IRIS26864_TWOSLOT_RUNTIME_SOURCE_PROOF.json').read_text())
_memory_lock=__import__('json').loads((_vendor/'IRIS26864_RAWR_VENDOR_SOURCE_LOCK.json').read_text())
_adapter=_memory_proof['android_vk11_memory_requirements_adapter']
assert _adapter['upstream_sha256']==_memory_lock['files'][_adapter['relative_path']]['sha256']
assert _v11hash.sha256(_memory_source.encode()).hexdigest()==_adapter['candidate_sha256']=='0e98b658523532ac52381724e15d93ed9fb32335254e47b9351158849b33530a'
assert _adapter['linker_regression_run']==39714213244 and _adapter['device_proc_dispatch_count']==2
_device_source=(root/'src/main/cpp/iris26856/amaze/src/VulkanDeviceOwner.cpp').read_text()
assert 'app.apiVersion = VK_API_VERSION_1_1;' in _device_source
assert 'if (props.apiVersion < VK_API_VERSION_1_1) continue;' in _device_source
assert 'requirements.pNext = &dedicated;' in _memory_source
assert _memory_source.count('dedicated.requiresDedicatedAllocation == VK_TRUE')==2
assert _memory_source.count('vkGetDeviceProcAddr(d, "vkGetImageMemoryRequirements2")')==1
assert _memory_source.count('vkGetDeviceProcAddr(d, "vkGetBufferMemoryRequirements2")')==1
assert _memory_source.count('reinterpret_cast<PFN_vkGetImageMemoryRequirements2>')==1
assert _memory_source.count('reinterpret_cast<PFN_vkGetBufferMemoryRequirements2>')==1
assert _memory_source.count('getImageMemoryRequirements2(d, &requirementsInfo, &requirements);')==1
assert _memory_source.count('getBufferMemoryRequirements2(d, &requirementsInfo, &requirements);')==1
assert 'if (!getImageMemoryRequirements2 || !getBufferMemoryRequirements2)' in _memory_source
assert _memory_source.index('if (!getImageMemoryRequirements2 || !getBufferMemoryRequirements2)') < _memory_source.index('struct PendingImage'), 'missing dispatch must fail before allocating arena resources'
# Previous real Clang historical regression: Vulkan link-name bool checks.
assert not _v11re.search(r'if\s*\(\s*vkGet(?:Image|Buffer)MemoryRequirements2\s*\)',_memory_source)
# NEW linker regression: all Iris and pinned RAWR native files must avoid any
# directly called Vulkan-1.1 symbol (unless provided by the NDK loader).
_v11_calls={'vkGetImageMemoryRequirements2','vkGetBufferMemoryRequirements2'}
_v11_native_count=0
for _src_file in (root/'src/main/cpp').rglob('*'):
 if _src_file.is_file() and _src_file.suffix in ('.cpp','.cc','.c','.h','.hpp','.inc'):
  _data=_src_file.read_text(errors='replace')
  _code=_v11re.sub(r'/\*.*?\*/|//[^\n]*',' ',_data,flags=_v11re.S)
  for _name in _v11_calls:
   assert not _v11re.search(r'\b'+_name+r'\s*\(',_code),('reintroduced NDK 39714213244 unresolved Vulkan symbol',_src_file,_name)
  _v11_native_count+=1
# Exact typed production snippet to compile+link; do not duplicate the fixed
# device dispatcher in a separately maintained fake implementation.
_dispatch_start=_memory_source.index('        const auto getImageMemoryRequirements2 =')
_dispatch_end=_memory_source.index('        struct PendingImage {',_dispatch_start)
_dispatch_text=_memory_source[_dispatch_start:_dispatch_end]
assert 'throw std::runtime_error' in _dispatch_text
_img_call='getImageMemoryRequirements2(d, &requirementsInfo, &requirements);'
_buf_call='getBufferMemoryRequirements2(d, &requirementsInfo, &requirements);'
assert _memory_source.count(_img_call)==_memory_source.count(_buf_call)==1
if a.numeric:
 clang=_v11shutil.which('clang++')
 assert clang is not None, 'real Clang required for Vulkan 1.1 linker ABI regression'
 # This source-level tool does not replace Android NDK compilation; it tests
 # the SAME production loader and invocation statements with typed Vulkan ABI
 # against a library that only exports Vulkan-1.0 vkGetDeviceProcAddr.
 header='''#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <stdexcept>
struct VkDevice_T {}; using VkDevice=VkDevice_T*;
struct VkImageMemoryRequirementsInfo2 {uint32_t sType; void* pNext;};
struct VkBufferMemoryRequirementsInfo2 {uint32_t sType; void* pNext;};
struct VkMemoryRequirements2 {uint32_t sType; void* pNext;};
using PFN_vkVoidFunction=void (*)();
using PFN_vkGetImageMemoryRequirements2=void (*)(VkDevice,const VkImageMemoryRequirementsInfo2*,VkMemoryRequirements2*);
using PFN_vkGetBufferMemoryRequirements2=void (*)(VkDevice,const VkBufferMemoryRequirementsInfo2*,VkMemoryRequirements2*);
extern "C" PFN_vkVoidFunction vkGetDeviceProcAddr(VkDevice,const char*);
'''
 # Proof: actual production dispatch loads both names using device-proc,
 # then calls the resulting typed function pointers with exact ABI arguments.
 harness=header+'''
extern "C" int return_null;
extern "C" int invoked_image;
extern "C" int invoked_buffer;
void run_owned_arena(VkDevice d) {
'''+_dispatch_text+'''
  VkImageMemoryRequirementsInfo2 image{};
  VkBufferMemoryRequirementsInfo2 buffer{};
  VkMemoryRequirements2 requirements{};
  {
   const auto& requirementsInfo = image;
'''+_img_call+'''
  }
  {
   const auto& requirementsInfo = buffer;
'''+_buf_call+'''
  }
}
int main(){ VkDevice_T dev{};if(std::getenv("DUMMY_NULL"))return_null=1;try{run_owned_arena(&dev);}catch(const std::runtime_error&){return return_null?0:12;}
return (!return_null && invoked_image==1 && invoked_buffer==1)?0:13; }
'''
 stub=header+'''
extern "C" {int return_null=0;int invoked_image=0;int invoked_buffer=0;}
static void image(VkDevice,const VkImageMemoryRequirementsInfo2*,VkMemoryRequirements2*){ ++invoked_image; }
static void buffer(VkDevice,const VkBufferMemoryRequirementsInfo2*,VkMemoryRequirements2*){ ++invoked_buffer; }
extern "C" PFN_vkVoidFunction vkGetDeviceProcAddr(VkDevice,const char* name){
  if(return_null)return nullptr;
  if(std::strcmp(name,"vkGetImageMemoryRequirements2")==0)return reinterpret_cast<PFN_vkVoidFunction>(&image);
  if(std::strcmp(name,"vkGetBufferMemoryRequirements2")==0)return reinterpret_cast<PFN_vkVoidFunction>(&buffer);
  return nullptr;
}
'''
 with tempfile.TemporaryDirectory(prefix='26864_vk11_link_') as _temp:
  _temp=Path(_temp); stub_file=_temp/'ndk_vulkan_1_0_stub.cpp'; main_file=_temp/'actual_ra_device_dispatch.cpp'
  stub_file.write_text(stub);main_file.write_text(harness)
  lib=_temp/'libvulkan_android_stub.so';exe=_temp/'preflight';runtime=_temp/'runtime'
  compile_stub=subprocess.run([clang,'-std=c++17','-shared','-fPIC','-Werror',str(stub_file),'-o',str(lib)],capture_output=True,text=True)
  assert compile_stub.returncode==0,('stub compiler failed',compile_stub.stderr)
  cmd=[clang,'-std=c++17','-Wall','-Wextra','-Werror=pointer-bool-conversion','-Wl,--no-undefined',str(main_file),'-L'+str(_temp),'-Wl,-rpath,'+str(_temp),'-lvulkan_android_stub','-o',str(exe)]
  positive=subprocess.run(cmd,capture_output=True,text=True)
  assert positive.returncode==0,('actual production Vulkan 1.1 dispatcher does not link',positive.stderr)
  invoke=subprocess.run([str(exe)],capture_output=True,text=True)
  assert invoke.returncode==0,('actual production Vulkan proc dispatch failed',invoke.stdout,invoke.stderr)
  fail_null=subprocess.run([str(exe)],env={**__import__('os').environ,'DUMMY_NULL':'1'},capture_output=True,text=True)
  assert fail_null.returncode==0,('absent driver function did not fail closed',fail_null.stdout,fail_null.stderr)
  # The separate negative fixture must fail to link if directly invoked names
  # reappear, even though the typed prototypes are present.
  old=harness.replace(_img_call,'vkGetImageMemoryRequirements2(d, &requirementsInfo, &requirements);').replace(_buf_call,'vkGetBufferMemoryRequirements2(d, &requirementsInfo, &requirements);')
  old=old.replace('extern "C" PFN_vkVoidFunction vkGetDeviceProcAddr(VkDevice,const char*);', 'extern "C" PFN_vkVoidFunction vkGetDeviceProcAddr(VkDevice,const char*);\nextern "C" void vkGetImageMemoryRequirements2(VkDevice,const VkImageMemoryRequirementsInfo2*,VkMemoryRequirements2*);\nextern "C" void vkGetBufferMemoryRequirements2(VkDevice,const VkBufferMemoryRequirementsInfo2*,VkMemoryRequirements2*);')
  main_file.write_text(old)
  negative=subprocess.run(cmd,capture_output=True,text=True)
  assert negative.returncode!=0 and 'vkGetImageMemoryRequirements2' in negative.stderr and 'vkGetBufferMemoryRequirements2' in negative.stderr,('original NDK linker failure not reproduced',negative.stderr)
  # Historical 39712359645 exact warning-as-error condition remains blocked.
  old_bool=header+'''
extern "C" void vkGetImageMemoryRequirements2(VkDevice,const VkImageMemoryRequirementsInfo2*,VkMemoryRequirements2*);
extern "C" void vkGetBufferMemoryRequirements2(VkDevice,const VkBufferMemoryRequirementsInfo2*,VkMemoryRequirements2*);
int main(){ if(vkGetImageMemoryRequirements2 && vkGetBufferMemoryRequirements2)return 0;return 1;}
'''
  main_file.write_text(old_bool)
  pointer_negative=subprocess.run([clang,'-std=c++17','-Werror=pointer-bool-conversion','-fsyntax-only',str(main_file)],capture_output=True,text=True)
  assert pointer_negative.returncode!=0 and 'pointer-bool-conversion' in pointer_negative.stderr,('historical 39712359645 Clang error not reproduced',pointer_negative.stderr)
 print('PASS actual 26864 production device-proc dispatch host C++ link/run, missing-entry fail-closed; both original missing-symbol errors reproduced by negative link; NDK pointer-bool warnings rejected')
print('PASS full native Vulkan 1.1 symbol domain audited:',_v11_native_count,'native source files, no direct 1.1 imports; inherited Vulkan 1.1 device gate and dedicated allocation preserved')
