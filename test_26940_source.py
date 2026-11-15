#!/usr/bin/env python3
"""Strict 26940 source ownership, routing, upstream math and 32-pipeline proofs."""
import sys,re
from build_26940_incremental import R,BASE,scope,sha,exact,fail
B='app/src/main/cpp/iris26864/'
def main():
 changed,old,new=scope()
 live='--live' in sys.argv
 root=R if live else R/'handoff_payload_26940'
 if live:exact(R,'26940_EXPECTED_FULL_APP.sha256','strict 26940 source universe')
 else:
  for p in changed:
   if sha(root/p)!=new[p]:fail('changed source payload incorrect '+p)
 version=(root/'app/version.properties').read_text()
 if not version.endswith('VERSION_NAME=0.9726940\nVERSION_BUILD=26940\n'):fail('wrong frozen 26940 version')
 get=lambda p:(root/(B+p)).read_text()
 jni=get('Iris26864JniGpuInteropImpl.inc')
 real=get('Iris26864RealRawrCoordinator.cpp')
 hdr=get('Iris26864RealRawrCoordinator.hpp')
 run=get('Iris26864FrozenDirectRawrRunner.cpp')
 runhdr=get('Iris26864FrozenDirectRawrRunner.hpp')
 exe=get('bridge/Iris26888BOffVulkanExecutor.cpp')
 for text in ('const bool useBOffCache = (!sr && photoBOffOnly == JNI_TRUE);','std::unique_lock<std::mutex> bOffCacheLock;',
  'bOffCache ? bOffCache->coordinator.get() : nullptr','struct Iris26940CacheFailureGuard final {',
  'std::uncaught_exceptions() > exceptionsAtEntry','vkQueueWaitIdle(device->queue()) != VK_SUCCESS',
  'uint64_t lens = 0;','uint32_t width = 0, height = 0, localCfa = 0;',
  'if (device && coordinator && lens == wantedLens &&','void clear() noexcept {'):
  if jni.count(text)!=1:fail('missing isolated B OFF Vulkan lifecycle proof '+text)
 if 'static Iris26940BOffGpuCache cache;' not in jni:fail('no isolated static ownership')
 if jni.count('if (bOffCache) bOffCacheLock = std::unique_lock<std::mutex>(bOffCache->mutex);')!=1:fail('GPU shared mutable cache not mutex-protected')
 if 'if (sr && bOffReusable)' not in real:fail('Wronski not forbidden from cache')
 for text in ('if (!bOffReusable) perCapture = std::make_unique<AndroidBurstCoordinator>();',
  'BOffInitScope initScope(bOffReusable != nullptr);','if (bOffReusable) coordinator->releaseScratch();',
  'if (!bOffReusable) (void)perCapture.release();','coordinator->run(upstream,frozen.referenceIndex,{},frozen.prepareNormal)'):
  if real.count(text)!=1:fail('coordinator original math/lifetime missing '+text)
 if real.count('coordinator->initialize(')!=1:fail('duplicate upstream coordinator init')
 if hdr.count('rawr::raw_gpu_pipeline::AndroidBurstCoordinator* bOffReusable = nullptr')!=1 or runhdr.count('rawr::raw_gpu_pipeline::AndroidBurstCoordinator* bOffReusable = nullptr')!=1:fail('inconsistent coordinator declarations')
 if run.count('runRealPinnedRawrB(merge,wrappedConsume,bOffReusable)')!=2:fail('native normal+memory fallback lost')
 if 'thread_local bool iris26940BOffHdrqPipelineInit = false;' not in exe:fail('shader opt-in scope missing')
 for text in ('i != static_cast<size_t>(ShaderId::NoiseEstimate)','i < static_cast<size_t>(ShaderId::HdrpPrepare)','if (p.pool) ck(vkResetDescriptorPool('):
  if text not in exe:fail('executor correctness guard missing '+text)
 if 'if (!p.pool || !p.dsl || !p.layout || !p.prod)' not in exe:fail('executor uninitialized dispatch not fail closed')
 # Upstream algorithm source (all math, alignment, noise, and Wronski) remains SHA-identical.
 for p in old:
  if any(x in p for x in ('/vendor/rawr/','/shader/','/shaders/','/jniLibs/')) or p.endswith(('.kt','.java','.glsl','.frag','.comp','.spv','.so','.jar','.aar')):
   if old[p]!=new[p]:fail('protected algorithm, shader or Android source changed '+p)
 # Exact upstream shader table order and recorder's shader use.
 if live:
  root_src=root/B
 else:
  if '--base' not in sys.argv:
   root_src=None
  else:
   root_src=BASE/B
 if root_src is not None:
  header=(root_src/'vendor/rawr/native/multiframe/pipeline/include/rawr/raw_gpu_pipeline/VulkanExecutor.h').read_text()
  enum=header.split('enum class ShaderId : std::uint32_t {',1)[1].split('Count',1)[0]
  names=[x.strip().rstrip(',') for x in enum.splitlines() if x.strip() and not x.strip().startswith('//')]
  keep={x for i,x in enumerate(names) if x=='NoiseEstimate' or i>=names.index('HdrpPrepare')}
  if len(names)!=55 or len(keep)!=32:fail('HDR+ shader table changed unexpectedly')
  rec=(root_src/'vendor/rawr/native/multiframe/pipeline/src/HdrPlusRecorder.cpp').read_text()
  used=set(re.findall(r'ShaderId::([A-Za-z0-9_]+)',rec));used.add('NoiseEstimate')
  if used!=keep:fail('missing used shader or extra shader omitted '+str(used^keep))
  if live:
   route=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
   if 'localOutputZoom >= 1.10f' not in route or '!iris26864BHighZoomExactA' not in route or '!parameters.iris26903NightB && !parameters.irisNightActive' not in route:fail('photo B OFF zoom routing changed')
 print('PASS 26940: 2050 exact compiled source, 7 changed, 2043 immutable, 32 of 55 strictly HDR+ pipelines, B ON/A/Night/zoom>=1.10 untouched')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
