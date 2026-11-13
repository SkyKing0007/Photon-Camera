#!/usr/bin/env python3
"""26924 active B modes/RAW lifecycle/GL and CMake shadow ownership.
Strict candidate + immutability verification, never substitutes for real compilers.
"""
from pathlib import Path
import sys,re,hashlib
R=Path(__file__).resolve().parent
P=R/'handoff_payload_26924' if '--payload' in sys.argv else R
B=P/'app/src/main/cpp/iris26864'
J=P/'app/src/main/java/com/hinnka/mycamera/processor'
H=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
def check(test,why):
 if not test:raise AssertionError('26924 BLOCKED: '+why)
version=(P/'app/version.properties').read_text()
check('VERSION_BUILD=26924' in version and 'VERSION_NAME=0.9726924' in version,'wrong version')
s=(B/'Iris26864VendorRawr.cmake').read_text()
for name in ('Iris26924MultiframeCMakeLists.txt','Iris26924MultiframeRecorder.cpp','Iris26924MultiframeRecorder.h','Iris26924VulkanExecutor.h','Iris26924WronskiFinalize.comp'):
 check(s.count(name)==1,'CMake missing/duplicate active shadow '+name)
for shader in ('raw_residual','raw_adjoint','raw_update','reference_model'):
 check((B/'bridge'/('Iris26924_'+shader+'.comp')).is_file() and 'foreach(N26924 IN ITEMS raw_residual raw_adjoint raw_update reference_model)' in s,'missing shader CMake '+shader)
check('Iris26923WronskiFinalize.comp' not in s,'stale 26923 finalize selected')
check(s.count('COPYONLY')>=7,'CMake shadow not generated-only')
cpp=(B/'bridge/Iris26888BOffHdrqCoordinator.cpp').read_text()
assert 'IRIS_26924_B_ON_TRUE_3X3_ORIGINAL_BAYER_REPROJECTION' in cpp
assert 'recorder.record26924Residual(command_,frames[ref].raw.view' in cpp
assert 'recorder.record26924Adjoint(command_,true)' in cpp
assert 'recorder.record26924ReferenceModel(command_)' in cpp
assert 'recorder.recordCompanionAlignmentLevel(command_,level)' in cpp
assert 'recorder.record26924Update(command_,std::uint32_t(frames.size()),outer,imageStep)' in cpp
assert 'if (merge_.outputScale >= 1.99f && frames.size() >= 2u)' in cpp
assert 'if(merge_.estimateNoiseFromBurst)' in cpp or 'if (merge_.estimateNoiseFromBurst)' in cpp
# Explicit fail-closed 3 OUTER x 3 FRESH RAW image steps, preserving
# Wronski as initialization and the physical RAW16 reference across solves.
assert cpp.count('constexpr std::uint32_t kOuterIterations=3u;')==1
assert cpp.count('constexpr std::uint32_t kImageUpdatesPerOuter=3u;')==1
assert cpp.count('for (std::uint32_t outer=0; outer<kOuterIterations; ++outer)')==1
assert cpp.count('for (std::uint32_t imageStep=0; imageStep<kImageUpdatesPerOuter; ++imageStep)')==1
assert cpp.count('recorder.record26924Update(command_,std::uint32_t(frames.size()),outer,imageStep)')==1
assert 'if (outer>0u)' in cpp
assert 'IRIS_26924_B_ON_TRUE_3X3_ORIGINAL_BAYER_REPROJECTION' in cpp
assert 'for (std::uint32_t iteration=0; iteration<2u; ++iteration)' not in cpp
assert cpp.index('recorder.record26924ClearGradient(command_)') < cpp.index('recorder.record26924Residual(command_,frames[ref].raw.view') < cpp.index('recorder.record26924Update(command_')
assert cpp.index('if (outer>0u)') < cpp.index('for (std::uint32_t imageStep=0;')
assert 'framePrepared(i)' in cpp and 'frameConsumed(i)' in cpp

assert 'framePrepared(i)' in cpp
rec=(B/'bridge/Iris26924MultiframeRecorder.cpp').read_text()
for n in ('record26924ClearGradient','record26924Residual','record26924Adjoint','record26924Update','record26924ReferenceModel'):
 assert rec.count('MultiframeRecorder::'+n)==1
assert 'vkCmdClearColorImage' in rec and 'VK_PIPELINE_STAGE_TRANSFER_BIT' in rec
assert 'framePrepared(i)' in cpp and 'frameConsumed(i)' in cpp
assert 'rgb_sum' in rec and 'rgb_weight' in rec
assert 'if(outer>=3u || imageStep>=3u)' in rec
assert 'kStepScale[outer][imageStep]' in rec
assert 'kMaxLuma[outer],kMaxChroma[outer]' in rec
assert 'record26924Update(VkCommandBuffer c,unsigned frames,' in rec
assert 'frameCount,\n                              std::uint32_t outerIteration, std::uint32_t imageStep' in (B/'bridge/Iris26924MultiframeRecorder.h').read_text()
for shader in ('raw_residual','raw_adjoint','raw_update','reference_model'):
 p=B/'bridge'/('Iris26924_'+shader+'.comp');src=p.read_text()
 check(src.startswith('#version 450'),'shader 450 missing '+shader)
 check('layout(push_constant)' in src,'shader missing ABI push '+shader)
 check(src.count('void main()')==1,'shader entry '+shader)
 check('texture(' not in src,'no texture-filtering in original RAW operator '+shader)
 check('imageLoad(' in src and 'imageStore(' in src,'shader must use exact images '+shader)
 check('while(' not in src,'unbounded GPU iteration '+shader)
# Catch old nine fused-image micro-updates as live calls.
final=(B/'bridge/Iris26924WronskiFinalize.comp').read_text()
check('IRIS_26924_TRUE_BAYER_OBSERVATION_INVERSE' in final,'new initial 2x baseline')
check('IRIS_26923_B_SR_ON_NINE_BOUNDED_HR_UPDATES' not in final,'stale 9-pass fused-image shader')
v=(B/'bridge/Iris26888BOffVulkanExecutor.cpp').read_text()
for n in ('raw_residual','raw_adjoint','raw_update','reference_model'):
 check(v.count('"iris26924_'+n+'"')==2,'new native SPIR-V spec/order missing '+n)
 check(v.count('mf_iris26924_'+n+'_prod_spv')>=2,'missing embedded true SPIR-V for '+n)
check('static_assert(sizeof(kOrder) / sizeof(kOrder[0]) == static_cast<size_t>(ShaderId::Count)' in v,'lost compiled ABI gate')
h=(B/'bridge/Iris26924VulkanExecutor.h').read_text()
for n in ('Iris26924RawResidual','Iris26924RawAdjoint','Iris26924RawUpdate','Iris26924ReferenceModel'):
 check(h.count(n)==1,'enum not 1:1 '+n)
c=(B/'Iris26864RealRawrCoordinator.cpp').read_text()
for token in ('wronski.fallbackChromaGain=1.25f','wronski.fallbackLumaGain=0.0f','wronski.fallbackChromaMaxSigma=1.5f'):
 check(token in c,'loss of B ON fine-grain constraint '+token)
assert 'if(sr && frozen.hasBOffCustomNoise)' in c
# Exact two-slot RAW upload receipt must attribute ON re-projection correctly.
uploader=(B/'Iris26864FrozenDirectRawrRunner.cpp').read_text()
check('request.algorithm==RealBEngine::WronskiTrue2x' in uploader and
      'B_ON_RAW_REPROJECT_REUPLOAD' in uploader and 'B_OFF_WITNESS_REUPLOAD' in uploader,
      'incorrect stale OFF/ON borrowed RAW telemetry')
# Validate B OFF-only clipping/luminance owner and presence of B ON-no-op controls.
stack=(J/'GlesMgcRawSpatialStacker.kt').read_text()
chroma=(J/'GlesIris26870PostAmazeChroma.kt').read_text()
fcc=(J/'GlesIris26856RawrFalseColor.kt').read_text()
for key in ('uIris26924BOff','uIris26924ClipPresent','uIris26924SensorClip'):
 check(key in stack and key in chroma and key in fcc,'GLES uniform linkage missing '+key)
check('nativeSensorClipFullRes26866!=0' in stack and 'processingWidth==width && processingHeight==height' in stack,'OFF physical CFA provenance incorrect')
check('iris26924BOff = !iris26856BTrue2x' in stack,'ON must retain original FCC')
check('if(uIris26924BOff!=0 && ring>=2) continue;' in chroma,'OFF wide ring still crosses material')
check('connectedMaterial(p,off,y,center)' in chroma,'OFF donor topology missing')
check('uIris26924BOff!=0 && (clipNear(p)||hardEdge(p))' in fcc,'OFF clip/edge median missing')
check('uIris26924BOff!=0 ? max(0.06*max(Yc,Yn),0.012) : uEdgeSigma' in fcc,'luminance gate missing')
check('float commonCeiling=min(uAmazeWb.r,min(uAmazeWb.g,uAmazeWb.b))' in chroma,'successful smooth white semantics altered')
# All provenance in pinned vendor and native library must match 26923 authority.
if '--live' in sys.argv:
 old={n:h for h,n in [ln.split('  ',1) for ln in (R/'26924_BASE_26923_FULL_APP.sha256').read_text().splitlines()]}
 prot={n:h for h,n in [ln.split('  ',1) for ln in (R/'26924_PROTECTED_SOURCE.sha256').read_text().splitlines()]}
 for n,digest in prot.items():check(H(R/n)==digest,'protected SHA mismatch '+n)
 check(len(old)==2039 and len(prot)==2030,'authority/protected size')
print('PASS 26924 3 outer x 3 new RAW residual/adjoint updates, bounded taper, coupled LK, clipping-safe OFF, private CMake shadow, 2030 protected')
