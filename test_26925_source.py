#!/usr/bin/env python3
"""26925 B Super Res ON, exact candidate/source-ownership regression.
Read-only assertions; not a substitute for pinned shader/NDK/Java compilation.
"""
from pathlib import Path
import sys,re
R=Path(__file__).resolve().parent
P=R/'handoff_payload_26925' if '--payload' in sys.argv else R
B=P/'app/src/main/cpp/iris26864'; J=P/'app/src/main/java/com/hinnka/mycamera/processor'
def check(ok,label):
 if not ok:raise AssertionError('26925 BLOCKED '+label)
check('VERSION_BUILD=26925' in (P/'app/version.properties').read_text(),'wrong 26925 build version')
C=(B/'Iris26864VendorRawr.cmake').read_text()
for x in ('Iris26925ScratchLayout.cpp','Iris26925_raw_cfa_weight.comp','Iris26925_support_finish.comp'):
 check(C.count(x)==1,'compiled private CMake shadow source '+x)
check('Iris26923WronskiFinalize.comp' not in C,'stale 26923 selected')
check('  Iris26924' not in C or 'Iris26924Multiframe' in C,'incorrect prior source selection')
check('add_subdirectory("${IRIS26887_VENDOR_SHADOW}/multiframe/pipeline"' in C,'CMake vendor shadow not used')
for f in ('Iris26924_raw_residual.comp','Iris26924_raw_adjoint.comp',
          'Iris26925_raw_cfa_weight.comp','Iris26925_support_finish.comp'):
 p=B/'bridge'/f;src=p.read_text()
 check(src.startswith('#version 450') and 'void main()' in src,'GLSL source '+f)
 check('while(' not in src,'unbounded GPU inner loop '+f)
check('layout(set=0,binding=6,r32f) readonly uniform image2D rawVariance;' in (B/'bridge/Iris26924_raw_adjoint.comp').read_text(),'CFA variance descriptor 6')
check('supportOnly;' in (B/'bridge/Iris26924_raw_adjoint.comp').read_text(),'support-only source push field')
check('std::int32_t rawW,rawH,tileSize,cfa,reference,supportOnly;' in (B/'bridge/Iris26924MultiframeRecorder.cpp').read_text(),'exact C++ adjoint push ABI')
if '--payload' not in sys.argv:
 check('int publishSupport;' not in (B/'bridge/Iris26924_raw_update.comp').read_text(),'stale unused 26924 push field')
coord=(B/'bridge/Iris26888BOffHdrqCoordinator.cpp').read_text();rec=(B/'bridge/Iris26924MultiframeRecorder.cpp').read_text();hdr=(B/'bridge/Iris26924MultiframeRecorder.h').read_text()
check(coord.count('constexpr std::uint32_t kOuterIterations=3u')==1 and coord.count('constexpr std::uint32_t kImageUpdatesPerOuter=3u')==1,'preserve exact 3x3 schedule')
check(coord.count('for (std::uint32_t imageStep=0; imageStep<kImageUpdatesPerOuter; ++imageStep)')==1,'exact nine image steps')
check(coord.index('recorder.record26925CacheFlow(command_,i)')<coord.index('for (std::uint32_t outer=0; outer<kOuterIterations; ++outer)'),'original Wronski flow captured BEFORE RAW updates')
check('if (outer>0u)' in coord and coord.count('recorder.record26925FineRefine(command_,frames[i].raw.view,frames[i].parameters)')==1,'motion refinement only between outer iterations')
check('const bool cachedFineFlow=frames.size()<=16u;' in coord and 'frames.size() <= 16u' in coord,'bounded cache and full >16-frame fallback')
check('recorder.record26925RestoreFlow(command_,i)' in coord,'restored per-frame flow before projection')
check('for(std::uint32_t l=0;l<4u;++l)' in coord,'no dropping frames beyond cached 16')
check(coord.count('recorder.record26924Residual(command_,frames[i].raw.view,frames[i].parameters,false)')>=2,'fresh original Bayer residual on all updates+support')
check('record26925CfaWeight(command_,false)' in coord and 'record26925CfaWeight(command_,true)' in coord,'all-frame all-CFA coherent acceptance')
check('record26924Adjoint(command_,false,true)' in coord and 'record26925SupportFinish(command_,std::uint32_t(frames.size()))' in coord,'separate one-time true RAW support pass')
for n in ('record26925CacheFlow','record26925RestoreFlow','record26925FineRefine','record26925CfaWeight','record26925SupportFinish'):
 check(rec.count('MultiframeRecorder::'+n)==1 and n in hdr,'new native method wired '+n)
check('recordNormalize(c,false,raw,frame)' in rec and 'recordAlignmentInput(c,false,nullptr)' in rec and 'recordPyramid(c,false' not in rec[rec.index('void MultiframeRecorder::record26925FineRefine'):rec.index('void MultiframeRecorder::record26924ClearGradient')],'fine LK without stale 4-level pyramid')
check('vkCmdCopyImageToBuffer' in rec and 'vkCmdCopyBufferToImage' in rec and 'VK_PIPELINE_STAGE_TRANSFER_BIT' in rec,'GPU-only cached flow with synchronization')
check('if (g.output.width > g.raw.width && g.output.height > g.raw.height)' in (B/'bridge/Iris26925ScratchLayout.cpp').read_text(),'correct 2x cropped output flow allocation')
check('iris26925_flow_cache' in (B/'bridge/Iris26925ScratchLayout.cpp').read_text() and 'iris26925_valid_cache' in (B/'bridge/Iris26925ScratchLayout.cpp').read_text(),'both cached flow+valid resources')
f=(B/'bridge/Iris26925_raw_cfa_weight.comp').read_text()
check('dy=-1;dy<=1' in f and 'dx=-1;dx<=1' in f and 'float v=imageLoad(rawVariance,s).x' in f and 'e+=min(d*d/max(v,1e-8),625.0)' in f,'actual 3x3 Bayer-coherent residual normalized by native burst noise')
check('if(p.reference==0)' in f and 'if(total<5.0)w=0.0' in f,'reference preservation and incomplete neighborhood rejection')
s=(B/'bridge/Iris26925_support_finish.comp').read_text()
check('sw[c]*sw[c]/ss[c]' in s and 'min(n.r,min(n.g,n.b))' in s,'original-frame effective temporal support per color')
check('original.rgb,safe' in s,'luma and color unchanged by support-finish')
g=(B/'Iris26885WronskiChromaGuide.comp').read_text()
check('imageLoad(wronskiRgb,px).a' in g and 'imageStore(amazeRgbInPlace,px,vec4(src.rgb,rawNeff))' in g,'native 2x support propagated to post-AMaZE output alpha')
k=(J/'GlesIris26870PostAmazeChroma.kt').read_text()
for t in ('uIris26925SupportPresent','uIris26925OriginalFrames','uIris26925ShotByRgb','uIris26925ReadByRgb','clamp(raw.a,0.0','localMean','physicalVariance'):
 check(t in k,'native support/chroma contract '+t)
check('uIris26922ShotVariance' not in k and 'uIris26922ReadVariance' not in k,'stale global divided variance uniform')
check('uIris26923SrOn;' not in k,'26923 V3 wrong uniform regression')
check('float localCoherence=' in k and 'float coherent=' not in k,'26925 V2 GLSL reserved local variable not reintroduced')
check('if(uIris26924BOff!=0 && ring>=2)' in k,'B OFF long donor safety kept')
kt=(J/'GlesMgcRawSpatialStacker.kt').read_text()
check('uniform1i(applyProgram,"uIris26925SupportPresent",1)' in kt and 'uniform1f(applyProgram,"uIris26925OriginalFrames",nFrames)' in kt,'producer to GLSL support owner')
check('uIris26922ShotVariance' not in kt,'stale global-frame noise reference')
ex=(B/'bridge/Iris26888BOffVulkanExecutor.cpp').read_text();h=(B/'bridge/Iris26924VulkanExecutor.h').read_text()
for name,enum in (('iris26925_raw_cfa_weight','Iris26925RawCfaWeight'),('iris26925_support_finish','Iris26925SupportFinish')):
 check(ex.count('"'+name+'"')==2 and h.count(enum)==1,'current ShaderId spec/order uniqueness '+name)
check('static_assert(sizeof(kOrder) / sizeof(kOrder[0]) == static_cast<size_t>(ShaderId::Count)' in ex,'static GPU eager ABI order retained')
print('PASS 26925 native B ON 3x3 full RAW, cached alignment, CFA-coherent weights, genuine support, photo luma preservation, off invariance, source/no-stale-reference')
