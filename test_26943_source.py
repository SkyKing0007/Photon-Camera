#!/usr/bin/env python3
"""Strict complete source cross-references and 2050->2054 26942 authority.
Full Android native/Kotlin/Java GLSL compilers remain mandatory in Actions.
"""
import sys,re
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
 require(ingress,('importDirect(','importGpuBuffer(','AHardwareBuffer_lockPlanes','VK_FORMAT_R16_UINT','waitForCameraFence','uploadHardwareBufferInto','vkCmdCopyImage','vkCmdCopyBufferToImage','quarantineUnresolved'),'RAW hardware-buffer ingress')
 require(jni,('Iris26943IngressWorker','pending.size()>=3u','std::try_to_lock','AHardwareBuffer_acquire','AHardwareBuffer_release','bOffCache->ring->select(selected,','req.preStagedGpu','req.initialWaitSemaphore','vkDeviceWaitIdle(ctx.device)','nativeTryZslGpuStage'),'nonblocking camera worker')
 require(device,('const bool twoQueues = photoBOffTwoQueue','queueCount >= 2','q.queueCount = twoQueues ? 2u : 1u','ingressQueue_ = queue','vkGetDeviceQueue(dev, i, 1u, &queue_)','const float priorities[2] = {1.0f, 1.0f}'),'isolated queues')
 require(device_h,('VulkanDeviceOwner(bool photoBOffTwoQueue','ingressQueue()','hasSeparateIngressQueue()'),'queue owner ABI')
 require(run,('const bool alreadyStaged=hdrq && !request.preStagedGpu.empty()','!bOffReusable','merge.prepareNormal=[](std::uint32_t){}','pre_shutter_gpu_ring','post_shutter_resident','two_slot','- RAW post-shutter upload calls: ','- GPU fence waits (includes execution): '),'run/EXIF')
 require(run_h,('std::vector<TransientImageView> preStagedGpu','VkSemaphore initialWaitSemaphore'),'frozen GPU handoff')
 require(coord,('initialWaitSemaphore','VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT','vkQueueSubmit'),'cross queue dependency')
 require(coord_h,('VkSemaphore initialWaitSemaphore'),'coordinator API')
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
  # Existing 26942 B scheduler and all vendor revisions are byte-identical.
  for protected in ('app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp',
                    'app/src/main/assets/shaders/motionv2/render.glsl',
                    'app/src/main/assets/shaders/motionv2/gainmap.glsl'):
   if old.get(protected)!=new.get(protected):fail('existing successful 26942 protected path altered '+protected)
   if sha(BASE/protected)!=sha(R/protected):fail('actual previous runtime protected content mismatch')
 print('PASS 26943 native ring/ingress/queues/exact 15 frozen frames/cross-queue dependency/motion reference/RAWR timings; 17 changed+4 added, 2033 protected')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
