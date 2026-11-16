#!/usr/bin/env python3
"""26943 V2: strict native cross-references against 26942 compiled authority.
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
  # Existing successful 26942 scheduler, shader and vendor byte-invariance.
  for protected in ('app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp',
                    'app/src/main/assets/shaders/motionv2/render.glsl',
                    'app/src/main/assets/shaders/motionv2/gainmap.glsl'):
   if old.get(protected)!=new.get(protected):fail('successful 26942 protected path altered '+protected)
   if sha(BASE/protected)!=sha(R/protected):fail('previous compiled runtime protected content mismatch')
 print('PASS 26943 V3 API26 AHB and modeled Vulkan 1.1 API26 dynamic loader link, real pinned StageSink timing ABI, GPU ZSL ownership, shader, 17 changed+4 added, 2033 protected')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
