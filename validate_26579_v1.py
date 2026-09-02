#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
CHANGED=[
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/version.properties']

def fail(m): raise SystemExit('FAIL: '+m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def amap(root): return {str(p.relative_to(root)):sha(p) for p in sorted((Path(root)/'app').rglob('*')) if p.is_file()}
def need(s,t,label):
 if t not in s: fail(label+' missing: '+t)
def extract_raw_string(s,name):
 m=re.search(r'static const char\*'+re.escape(name)+r'=R"GLSL\((.*?)\)GLSL";',s,re.S)
 if not m: fail('native embedded shader missing '+name)
 return m.group(1)
def extract_between(s,a,b,label):
 i=s.find(a); j=s.find(b,i+len(a))
 if i<0 or j<0: fail(label+' markers')
 return s[i:j]
def main():
 if len(sys.argv)!=3: fail('usage base candidate')
 base,cand=map(Path,sys.argv[1:])
 a,b=amap(base),amap(cand)
 if len(a)!=1708 or len(b)!=1708: fail(f'candidate universe {len(a)}/{len(b)}')
 diff=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
 if diff!=CHANGED: fail('changed allowlist '+repr(diff))
 v=(cand/'app/version.properties').read_text(); need(v,'VERSION_NAME=0.9726579','version name'); need(v,'VERSION_BUILD=26579','version build')

 vgn=(cand/CHANGED[1]).read_text(); vgn_base=(base/CHANGED[1]).read_text()
 for t in ['IRIS_26578_FAIL_CLOSED_REAL_COLOR_GATE','IRIS_26579_MICRO_OBJECT_COLOR_TOPOLOGY','microChromaWeight','microMomentXX','microMomentYY','microMomentXY','microMinorMoment','microAreaEvidence','microObjectProtection','realColorConfidence','phaseLikeEvidence','falseColorGate','maximumMove = min(0.050, 0.40 * centerMagnitude)','supportedTarget']:
  need(vgn,t,'26579 shared real-color gate')
 for t in ['IRIS_26571_SAME_SIDE_MATERIAL_BOUNDARY','IRIS_26574_TOPOLOGY_PRESERVED_BRIGHT_SURFACE','nearTopologySupport','contourChainSupport','radiusTwoTopologyProtection']:
  need(vgn,t,'inherited VGN topology')
 # 26579 only extends the active universal post-VGN shader in this owner; all other embedded shader bytes stay identical.
 def shader(src,name):
  m=re.search(r'(?m)^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""',src)
  if not m: fail('missing shader '+name)
  z=src.find('""".trimIndent()',m.end())
  if z<0: fail('shader end '+name)
  return src[m.end():z]
 for name in ['seed','localClamp','localMedian','directionalSmooth','restoreDirection','iirRgb','calculateError','iirError','blendChroma','finalCameraRgb']:
  if shader(vgn_base,name)!=shader(vgn,name): fail('unexpected VGN embedded shader change '+name)

 sr=(cand/CHANGED[2]).read_text(); sr_base=(base/CHANGED[2]).read_text()
 for t in ['IRIS_26579_TRUE2X_TOPOLOGY_CHROMA_UPSAMPLE','irisTopologyGuide','sameMaterial','maxChromaMagnitude','bilinearChroma','selectedChroma','nonNegativeScale','vec3 guideRgb = irisTopologyGuide(globalP, bilinearGuideRgb, directY, confidence)','oRenderRgb = vec4(max(guideRgb * factor, vec3(0.0))']:
  need(sr,t,'26579 true2x chroma upsample')
 # Direct-CFA remains luma-only. It may select material side through directY, but no directRgb chroma vector may enter guideRgb.
 body=shader(sr,'true2xGuideRender26568')
 need(body,'float directY = max(irisLuma(directRgb), 0.0);','SR luma-only direct CFA')
 if 'directRgb - vec3' in body or 'irisChroma(directRgb)' in body: fail('direct-CFA chroma entered SR guide')
 # Alignment/refinement shader is frozen.
 if shader(sr_base,'true2xFlowRefine26574')!=shader(sr,'true2xFlowRefine26574'): fail('true2x flow refinement changed')

 native=(cand/CHANGED[0]).read_text(); native_base=(base/CHANGED[0]).read_text()
 # Publication compute/pixel math stays byte-identical: transport only.
 if extract_raw_string(native_base,'kIris26571PublicationCompute')!=extract_raw_string(native,'kIris26571PublicationCompute'):
  fail('26571 publication compute/pixel math changed')
 for t in ['IRIS_26579_GPU_DIRECT_INTERMEDIATE_PUBLICATION','invalid_gpu_publication_args','missing_gain_path','open_base','open_gain','gpu_band_order','base_jpeg_band_encode','gain_jpeg_band_encode','gpu_band_queue_empty','IRIS_26579_TRUE2X_GPU_COMPAT_RESULT','IRIS_26579_TRUE2X_GPU_TO_CPU_FALLBACK']:
  need(native,t,'26579 GPU publication transport')
 if '.iris26571_gpu' in native: fail('extension-changing GPU sibling path survives')
 # Direct Java-authorized intermediate target must be used by both GPU tiers.
 async_call='generateGain?gp.c:nullptr,(int)quality,true,&gpuTiming'
 compat_call='generateGain?gp.c:nullptr,(int)quality,false,&gpuCompatTiming'
 cpu='/* Exact successful 26570 CPU fallback begins here. */'
 for t in [async_call,compat_call,cpu]: need(native,t,'GPU publication ordering')
 if not (native.index(async_call)<native.index(compat_call)<native.index(cpu)): fail('GPU async -> compat -> CPU order changed')
 # Exact CPU fallback and all suffix code are preserved from the successful 26578 runtime.
 if native_base[native_base.index(cpu):] != native[native.index(cpu):]: fail('exact 26570 CPU fallback suffix changed')
 # No reasonless false exit in the GPU encode wrapper. There are exactly four direct false exits;
 # each is the argument/file-open guard and assigns its reason before returning. All producer/consumer/
 # JPEG/flush/close failures reach the final reason closure.
 fn=extract_between(native,'inline bool iris26571EncodeGpuPublication(', '\n}\n\nstruct StreamingBandTiming','GPU wrapper')
 if fn.count('return false;') != 4: fail('GPU wrapper direct false-exit count changed')
 for exact in [
  'setReason("invalid_gpu_publication_args");return false;',
  'setReason("missing_gain_path");return false;',
  'setErrnoReason("open_base");return false;',
  'setErrnoReason("open_gain");fclose(baseOut);unlink(basePath);return false;',
 ]: need(fn,exact,'GPU reason-before-return')
 if 'queue.finish(false,"open base")' in fn or 'queue.finish(false,"open gain")' in fn: fail('reasonless old output-open path survives')
 need(fn,'if(!streamed&&reason&&reason->empty())*reason=consumerReason.empty()?"gpu_band_queue_empty":consumerReason;','GPU final reason closure')
 need(fn,'setSavedErrnoReason("flush_base",bfErr)','GPU base flush reason')
 need(fn,'setSavedErrnoReason("close_base",bcErr)','GPU base close reason')
 need(fn,'setSavedErrnoReason("flush_gain",gfErr)','GPU gain flush reason')
 need(fn,'setSavedErrnoReason("close_gain",gcErr)','GPU gain close reason')

 # The new direct native targets are not invented paths: unchanged Java owns .jpg intermediates and
 # passes them to native. Successful 26578 CPU fallback already proved native fopen/write on these paths.
 java=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text()
 need(java,'output.resolveSibling("." + output.getFileName() + ".26564.true2x.base.jpg")','Java base intermediate')
 need(java,'output.resolveSibling("." + output.getFileName() + ".26564.true2x.gain.jpg")','Java gain intermediate')
 need(java,'generateMotionTrue2xGain ? gain.toString() : null','Java gain target handoff')
 need(java,'target.toString(), Math.max(1, Math.min(100, quality))','Java base target handoff')

 # No unrelated owners can change through this four-file build.
 forbidden=[p for p in diff if any(x in p for x in ['Dng','Night','CaptureController','MotionV2Merger','PhotonMotionMgc1271Bridge'])]
 if forbidden: fail('forbidden ownership change '+repr(forbidden))
 print('PASS exact successful-26578 1708-file authority -> four-file 26579 allowlist')
 print('PASS 26578 fail-closed VGN inherited + multicolor 2-D micro-object veto added')
 print('PASS SR direct-CFA luma-only ownership retained; topology-aware native VGN chroma interpolation added')
 print('PASS true2x flow/alignment refinement byte-identical')
 print('PASS publication compute/pixel math byte-identical; direct Java intermediate transport only')
 print('PASS GPU async -> map-sync compat -> exact CPU fallback order retained')
 print('PASS reasonless GPU wrapper exits closed and extension-changing GPU sibling removed')
if __name__=='__main__': main()
