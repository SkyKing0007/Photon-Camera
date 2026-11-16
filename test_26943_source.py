#!/usr/bin/env python3
"""26943 V5: strict native cross-references against 26942 compiled authority.
Android API26 NDK, original GLSL, Kotlin/Java and full assemble remain mandatory.
"""
import sys,re,subprocess,tempfile,ctypes
from pathlib import Path
from build_26943_incremental import R,BASE,scope,exact,fail,sha
DIR='app/src/main/cpp/iris26864/'
def src(rel,live):
 p=R/rel if live else R/'handoff_payload_26943'/rel
 if not p.is_file():fail('missing runtime changed/added source '+rel)
 return p.read_text()
def require(s,items,name):
 for x in items:
  if x not in s:fail('missing '+name+' contract '+x)
def verify_hdrq_descriptor_abi(executor,rec,mismatch,border):
 """Match actual active GLSL set0/binding, Vulkan layout and each recorder dispatch.

 26943 device regression: VkResult=-13 occurred at hdrq_mismatch pipeline
 creation because shader set=0 binding5 had no executor descriptor layout.
 The next active hdrq_border pass similarly lacked shader binding2.
 This test runs in existing mandatory source-contract step, no weakening of
 real glslang/SPIR-V/NDK/Kotlin/Java/assemble gates.
 """
 def bindings_from_shader(code,stage):
  decls=re.findall(r'layout\s*\(\s*set\s*=\s*0\s*,\s*binding\s*=\s*(\d+)\s*,[^)]*\)\s*(?:(?:readonly|writeonly|coherent|restrict|volatile)\s+)*uniform\s+(image\w+)\s+(\w+)\s*;',code)
  if not decls:fail('26943 missing actual '+stage+' shader descriptor declarations')
  d=[(int(n),typ,name) for n,typ,name in decls]
  if len({n for n,_,_ in d})!=len(d):fail('26943 duplicate '+stage+' GLSL descriptor')
  return d
 def spec(name,nextname):
  begin=executor.find('{"'+name+'",');end=executor.find('{"'+nextname+'",',begin+1)
  if begin<0 or end<0 or executor.count('{"'+name+'",')!=1:fail('missing/duplicate executor spec '+name)
  section=executor[begin:end]
  b=[(int(n),kind) for n,kind in re.findall(r'\{(\d+)\s*,\s*VK_DESCRIPTOR_TYPE_(STORAGE_IMAGE|STORAGE_BUFFER)\s*\}',section)]
  if len(set(n for n,_ in b))!=len(b):fail('duplicate '+name+' executor binding')
  return b
 def record(name):
  # Extract the active C++ bindings block (and fail on another untracked call).
  matches=list(re.finditer(r'executor_\.record\(c,\s*ShaderId::'+name+r'\s*,\s*\{\{(.*?)\},\s*\{\}\}\s*,',rec,re.S))
  if len(matches)!=1:fail('missing/ambiguous recorder dispatch '+name)
  return [int(n) for n in re.findall(r'\bib\(\s*(\d+)\s*,',matches[0].group(1))]
 for name,next_name,shader,idname,expected in (
  ('hdrq_mismatch','hdrq_region_mean',mismatch,'HdrqMismatch',(0,1,2,3,4,5)),
  ('hdrq_border','hdrq_accumulate',border,'HdrqBorder',(0,1,2))):
  shader_decl=bindings_from_shader(shader,name)
  shader_ids=[x for x,_,_ in shader_decl]
  layout=spec(name,next_name)
  recorder=record(idname)
  if tuple(shader_ids)!=expected or tuple(n for n,_ in layout)!=expected or tuple(recorder)!=expected:
   fail(f'26943 Vulkan descriptor ABI disagreement {name}: shader={shader_ids}, executor={layout}, recorder={recorder}, expected={expected}')
  if not all(t=='STORAGE_IMAGE' for _,t in layout) or not all(t.startswith('image') for _,t,_ in shader_decl):
   fail('26943 Vulkan descriptor image type disagreement '+name)
 # Validate active public runtime dispatch mechanics and matching ABI sizes.
 for x in ('for (auto b : s.b) bs.push_back({b.n, b.t, 1, VK_SHADER_STAGE_COMPUTE_BIT, nullptr});',
           'ck(vkCreateDescriptorSetLayout(d, &dc, nullptr, &p.dsl)',
           'ck(vkCreatePipelineLayout(d, &lc, nullptr, &p.layout)',
           'for (const auto expected : s.b)',
           'if (count != 1) throw std::invalid_argument("multiframe executor: missing/duplicate required binding")',
           'vkUpdateDescriptorSets(device_, uint32_t(w.size()), w.data(), 0, nullptr)',
           'VkPushConstantRange pr{VK_SHADER_STAGE_COMPUTE_BIT, 0, 128};'):
  if x not in executor:fail('26943 Vulkan descriptor pipeline invariant missing '+x)
 if 'static_assert(sizeof(MismatchPc) == 100u' not in rec and 'static_assert(sizeof(MismatchPc)==100u' not in rec:
  fail('26943 mismatch push ABI 100 not constrained')
 if 'static_assert(sizeof(BorderPc)==16u' not in rec and 'static_assert(sizeof(BorderPc) == 16u' not in rec:
  fail('26943 border push ABI 16 not constrained')


def descriptor_abi_negative_tests(executor,rec,mismatch,border):
 # Inject the exact device crash root causes, plus downstream recorder / GLSL
 # and type ABI corruption. EACH MUST fail before the next Actions build.
 begin=executor.index('{"hdrq_mismatch",');end=executor.index('{"hdrq_region_mean",',begin)
 t=executor[begin:end]
 assert t.count('{5, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}')==1
 wrong_type=executor[:begin]+t.replace('{5, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}', '{5, VK_DESCRIPTOR_TYPE_STORAGE_BUFFER}',1)+executor[end:]
 mm=executor[:begin]+t.replace(', {5, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}','')+executor[end:]
 begin=executor.index('{"hdrq_border",');end=executor.index('{"hdrq_accumulate",',begin)
 t=executor[begin:end]
 assert t.count('{2, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}')==1
 bd=executor[:begin]+t.replace(', {2, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}','')+executor[end:]
 bad=[('missing mismatch layout5',mm,rec,mismatch,border),
      ('missing border layout2',bd,rec,mismatch,border),
      ('wrong descriptor type',wrong_type,rec,mismatch,border),
      ('wrong mismatch recorder5',executor,rec.replace('ib(5, arena_.image("hdrq_motion_min"))','ib(6, arena_.image("hdrq_motion_min"))'),mismatch,border),
      ('missing border shader2',executor,rec,mismatch,re.sub(r'^layout\(set = 0, binding = 2,.*\n','',border,count=1,flags=re.M))]
 for name,e,r,ms,bs in bad:
  if (e,r,ms,bs)==(executor,rec,mismatch,border):fail('26943 negative mutation did not change '+name)
  try:verify_hdrq_descriptor_abi(e,r,ms,bs)
  except RuntimeError:pass
  else:fail('26943 missed descriptor ABI negative '+name)

def main():
 paths,old,new=scope();live='--live' in sys.argv
 if live:exact(R,'26943_EXPECTED_FULL_APP.sha256','current source 2054 compiled candidate inputs')
 def cp(f):return src(DIR+f,live)
 ring=cp('Iris26943GpuZslRing.cpp');hdr=cp('Iris26943GpuZslRing.hpp');ingress=cp('Iris26943RawAhbIngress.cpp')
 jni=cp('Iris26864JniGpuInteropImpl.inc');device=src('app/src/main/cpp/iris26856/amaze/src/VulkanDeviceOwner.cpp',live)
 device_h=src('app/src/main/cpp/iris26856/amaze/include/amaze/VulkanDeviceOwner.hpp',live)
 run=cp('Iris26864FrozenDirectRawrRunner.cpp');run_h=cp('Iris26864FrozenDirectRawrRunner.hpp')
 coord=cp('Iris26864RealRawrCoordinator.cpp');coord_h=cp('Iris26864RealRawrCoordinator.hpp')
 rec=cp('bridge/Iris26887BOffHdrqRecorder.cpp');border=cp('bridge/Iris26943BOffHdrqBorder.comp')
 mismatch=cp('bridge/Iris26888BOffHdrqMismatch.comp')
 require(ring,('std::make_unique<TwoSlotRaw16Uploader>','images_->uploadHardwareBufferInto','std::unordered_set<uint64_t> seen','frames_[i].ready && frames_[i].timestamp==ts','bridgeForMerge','uploads_->execute','VK_NULL_HANDLE'),'GPU ring')
 require(hdr,('Iris26943GpuZslRing','select(', 'stage(', 'generation()'), 'GPU ring header')
 require(ingress,('importDirect(','importGpuBuffer(','AHardwareBuffer_lock(','kCameraRaw16PixelFormat=0x20u','kR16UintPixelFormat=0x39u','AHardwareBuffer_describe','desc.stride','VK_FORMAT_R16_UINT','waitForCameraFence','uploadHardwareBufferInto','vkCmdCopyImage','vkCmdCopyBufferToImage','quarantineUnresolved'),'RAW hardware-buffer ingress')
 if re.search(r'AHardwareBuffer_lockPlanes\s*\(',ingress):fail('Android API29 lockPlanes would break API26 native compilation')
 if 'AHARDWAREBUFFER_FORMAT_R16_UINT' in ingress:fail('newer AHB R16 enum must not be referenced with API26 NDK headers')
 if ingress.count('AHardwareBuffer_Desc desc{}')!=1:fail('AHB descriptor redeclaration breaks C++ compilation')

 # 26943 V3 regression for failed V2 R2 API26 NDK shared-library linkage.
 # Vulkan 1.1 instance commands are NOT API26 libvulkan.so global ELF exports.
 # Require real owning-instance dispatch, not direct linking, and preserve
 # native :app:assembleDebug (NDK dual ABI) as the mandatory verification.
 uploader=cp('Iris26864TwoSlotRaw16Uploader.hpp')
 require(device_h,('VkInstance instance() const noexcept { return instance_; }',
                   'VkInstance instance_ = VK_NULL_HANDLE;'),'live Vulkan instance owner')
 require(uploader,('AHardwareBuffer* source, int cameraFenceFd, uint32_t queueFamily, VkInstance instance);',),
        'AHB importer instance ABI declaration')
 require(ring,('images_->uploadHardwareBufferInto(slot,ahb,cameraFenceFd,family_,owner_.instance());',),
        'owning Vulkan instance forwarded to ingress queue')
 require(ingress,('std::unique_ptr<Imported> importDirect(VkInstance instance,VkPhysicalDevice p',
                  'int cameraFenceFd,uint32_t queueFamily,VkInstance instance)',
                  'if (quarantined_ || !ahb || !instance ||',
                  'source=importDirect(instance,physical_,device_,ahb,width_,height_);',
                  'PFN_vkGetPhysicalDeviceImageFormatProperties2',
                  'vkGetInstanceProcAddr(instance,"vkGetPhysicalDeviceImageFormatProperties2")',
                  'if (!queryFormat2)',
                  'queryFormat2(p,&fi,&supported)'), 'API26 loadable 1.1 instance dispatch')
 if re.search(r'\bvkGetPhysicalDeviceImageFormatProperties2\s*\(',ingress):
  fail('Vulkan 1.1 function is not API26 NDK libvulkan.so exported link-time symbol')
 if ingress.count('vkGetInstanceProcAddr(instance,"vkGetPhysicalDeviceImageFormatProperties2")')!=1:
  fail('unexpected Vulkan instance dispatch count')
 require(device,('app.apiVersion = VK_API_VERSION_1_1;',
                 'props.apiVersion < VK_API_VERSION_1_1'), 'Vulkan 1.1 owner device admission')
 # Prove the symbol-resolution mode with host ELF shared linking in the same
 # fail-closed style as the NDK link. This is NOT a real Android NDK compile.
 with tempfile.TemporaryDirectory(prefix='photon_26943_api26_link_') as td:
  tmp=Path(td)
  (tmp/'stub.cpp').write_text('extern "C" void *vkGetInstanceProcAddr(void *, const char *) {return nullptr;}\n')
  (tmp/'dynamic.cpp').write_text('extern "C" void *vkGetInstanceProcAddr(void *, const char *);\nusing FormatQuery=int(*)(void *, const void *, void *);\nextern "C" int probe(void *instance, void* physical) {\n auto fn=reinterpret_cast<FormatQuery>(vkGetInstanceProcAddr(instance,"vkGetPhysicalDeviceImageFormatProperties2"));\n return fn ? fn(physical,nullptr,nullptr) : -1;\n}\n')
  (tmp/'direct.cpp').write_text('extern "C" int vkGetPhysicalDeviceImageFormatProperties2(void *,const void *,void *);\nextern "C" int probe(void* physical) {return vkGetPhysicalDeviceImageFormatProperties2(physical,nullptr,nullptr);}\n')
  good=subprocess.run(['g++','-std=c++17','-shared','-fPIC','-Wl,--no-undefined',
             str(tmp/'dynamic.cpp'),str(tmp/'stub.cpp'),'-o',str(tmp/'dynamic.so')],capture_output=True,text=True)
  if good.returncode:fail('API26 modeled dynamic VkInstance loader did not link '+good.stderr[-900:])
  loaded=ctypes.CDLL(str(tmp/'dynamic.so'))
  loaded.probe.argtypes=(ctypes.c_void_p,ctypes.c_void_p)
  loaded.probe.restype=ctypes.c_int
  if loaded.probe(None,None)!=-1:
   fail('API26 optional Vulkan1.1 lookup unexpectedly proceeded with null function pointer')
  bad=subprocess.run(['g++','-std=c++17','-shared','-fPIC','-Wl,--no-undefined',
             str(tmp/'direct.cpp'),str(tmp/'stub.cpp'),'-o',str(tmp/'direct.so')],capture_output=True,text=True)
  if bad.returncode==0 or 'vkGetPhysicalDeviceImageFormatProperties2' not in bad.stderr:
   fail('API26 modeled Vulkan1.1 direct-link negative regression was not rejected')

 require(jni,('Iris26943IngressWorker','pending.size()>=3u','std::try_to_lock','AHardwareBuffer_acquire','AHardwareBuffer_release','bOffCache->ring->select(selected,','req.preStagedGpu','req.initialWaitSemaphore','vkDeviceWaitIdle(ctx.device)','nativeTryZslGpuStage'),'nonblocking camera worker')
 require(device,('const bool twoQueues = photoBOffTwoQueue','queueCount >= 2','q.queueCount = twoQueues ? 2u : 1u','ingressQueue_ = queue','vkGetDeviceQueue(dev, i, 1u, &queue_)','const float priorities[2] = {1.0f, 1.0f}'),'isolated queues')
 require(device_h,('VulkanDeviceOwner(bool photoBOffTwoQueue','ingressQueue()','hasSeparateIngressQueue()'),'queue owner ABI')
 require(run,('const bool alreadyStaged=hdrq && !request.preStagedGpu.empty()','!bOffReusable','merge.prepareNormal=[](std::uint32_t){}','pre_shutter_gpu_ring','post_shutter_resident','two_slot','- RAW post-shutter upload calls: ','- GPU fence waits (includes execution): ','result.submissionCount','iris26943HostChunkTimings.fenceWaitMs','t.totalMs'),'run/EXIF')
 if re.search(r'\bt\.chunk(?:GpuMs|WaitMs|RecordMs|SubmitMs|Count)\b',run):
  fail('unimplemented vendor BurstStageTimings chunk member used by native runner')
 require(run_h,('std::vector<TransientImageView> preStagedGpu','VkSemaphore initialWaitSemaphore'),'frozen GPU handoff')
 require(coord,('initialWaitSemaphore','VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT','vkQueueSubmit','Stage::RecordBegin','Stage::RecordEnd','Stage::SubmitBegin','Stage::SubmitEnd','Stage::FenceWaitBegin','Stage::FenceWaitEnd','std::chrono::steady_clock'),'real native StageSink clock')
 require(coord_h,('VkSemaphore initialWaitSemaphore','extern thread_local Iris26943HostChunkTimings'),'coordinator ABI')
 require(rec,('hdrq_motion_min','mp.motionEnabled = iris26941BOffHdrqLazyPoolReset','sizeof(BorderPc)==16u','sizeof(MismatchPc) == 100u','ShaderId::HdrqBorder'),'motion support')
 require(mismatch,('layout(set = 0, binding = 5, r32f)','int motionEnabled;','if (p.motionEnabled != 0)','pointSupport(','sSupport[64]'),'motion mismatch')
 require(border,('layout(set = 0, binding = 2, r32f)','int motionEnabled;','if (p.motionEnabled != 0)','imageLoad(refRgba','smoothstep(0.24,0.78','imageStore(img'),'reference blend')
 executor=cp('bridge/Iris26888BOffVulkanExecutor.cpp')
 verify_hdrq_descriptor_abi(executor,rec,mismatch,border)
 descriptor_abi_negative_tests(executor,rec,mismatch,border)
 for f in (mismatch,border):
  if re.search(r'(?:\bfloat\s+|\bvec\d\s+|\bint\s+)coherent\b',f):fail('GLSL reserved word used as identifier')
 vendor=cp('Iris26864VendorRawr.cmake');cmake=src('app/src/main/cpp/CMakeLists.txt',live)
 require(vendor,('Iris26943BOffHdrqBorder.comp','Iris26888BOffHdrqMismatch.comp','Iris26887BOffHdrqRecorder.cpp'),'private vendor shadow')
 require(cmake,('Iris26943GpuZslRing.cpp','Iris26943RawAhbIngress.cpp'),'real CMake inputs')
 version=src('app/version.properties',live)
 require(version,('VERSION_NAME=0.9726943','VERSION_BUILD=26943'),'version')
 if live:
  pinned=(R/'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/pipeline/include/rawr/raw_gpu_pipeline/AndroidBurstCoordinator.h').read_text()
  require(pinned,('struct BurstStageTimings','double totalMs','std::uint32_t submissionCount','using StageSink','FenceWaitBegin','FenceWaitEnd'),'actual pinned 26942 vendor ABI')
  if re.search(r'\b(?:chunkGpuMs|chunkWaitMs|chunkRecordMs|chunkSubmitMs|chunkCount)\b',pinned):
   fail('26943 native timing ABI audit must be updated for new vendor members')
  base_executor=(BASE/'app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp').read_text()
  stage1=base_executor.index('{"hdrq_mismatch",');stage2=base_executor.index('{"hdrq_region_mean",',stage1)
  source=base_executor[stage1:stage2]
  target=source.replace('{4, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}}}',
                        '{4, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}, {5, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}}}')
  if target==source or source.count('{4, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}}}')!=1:fail('26942 mismatch layout authority changed')
  predicted=base_executor[:stage1]+target+base_executor[stage2:]
  stage1=predicted.index('{"hdrq_border",');stage2=predicted.index('{"hdrq_accumulate",',stage1)
  source=predicted[stage1:stage2]
  target=source.replace('{1, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}}}',
                        '{1, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}, {2, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}}}')
  if target==source or source.count('{1, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}}}')!=1:fail('26942 border layout authority changed')
  predicted=predicted[:stage1]+target+predicted[stage2:]
  if predicted!=executor:fail('26943 executor modifies more than two mandatory descriptor bindings')
  # Existing successful 26942 scheduler, shader and vendor byte-invariance.
  for protected in ('app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp',
                    'app/src/main/assets/shaders/motionv2/render.glsl',
                    'app/src/main/assets/shaders/motionv2/gainmap.glsl'):
   if old.get(protected)!=new.get(protected):fail('successful 26942 protected path altered '+protected)
   if sha(BASE/protected)!=sha(R/protected):fail('previous compiled runtime protected content mismatch')
 print('PASS 26943 V5 camera GPU ZSL/API26/Vulkan1.1, HDRq shader-executor-recorder descriptor ABIs and five mutation negatives, 18 changed+4 added, 2032 protected')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
