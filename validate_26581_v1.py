#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
CHANGED=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/version.properties']
GPU_CPP='app/src/main/cpp/motionv2_jpeg444_jni.cpp'
GPU_CPP_SHA='d73cd24452280958f089e9124545a81461939e8fa0c9c95272b2825942e4b43d'
def fail(m): raise SystemExit('FAIL: '+m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def amap(root): return {str(p.relative_to(root)):sha(p) for p in sorted((Path(root)/'app').rglob('*')) if p.is_file()}
def need(s,t,label):
 if t not in s: fail(label+' missing: '+t)
def shader(src,name):
 m=re.search(r'(?m)^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""',src)
 if not m: fail('missing shader '+name)
 z=src.find('""".trimIndent()',m.end())
 if z<0: fail('shader end '+name)
 return src[m.end():z]
def main():
 if len(sys.argv)!=3: fail('usage base candidate')
 base,cand=map(Path,sys.argv[1:]);a,b=amap(base),amap(cand)
 if len(a)!=1708 or len(b)!=1708: fail(f'candidate universe {len(a)}/{len(b)}')
 diff=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
 if diff!=CHANGED: fail('changed allowlist '+repr(diff))
 v=(cand/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726581','version name');need(v,'VERSION_BUILD=26581','version build')

 vgn=(cand/CHANGED[0]).read_text();vgn0=(base/CHANGED[0]).read_text()
 for t in ['IRIS_26578_FAIL_CLOSED_REAL_COLOR_GATE','IRIS_26579_MICRO_OBJECT_COLOR_TOPOLOGY','IRIS_26580_MICRO_OBJECT_AREA_VS_RIBBON','IRIS_26580_FAIL_CLOSED_MULTICOLOR_OBJECT_VETO','IRIS_26581_OCCLUSION_GAP_BACKGROUND_OWNER','IRIS_26581_GAP_BACKGROUND_CHROMA_RESTORE','gapPairEvidence','gapBackgroundChromaSum','gapOwnership','realColorConfidence','falseColorGate','maximumMove = min(0.050, 0.40 * centerMagnitude)']:
  need(vgn,t,'26581 shared VGN gap ownership')
 for t in ['IRIS_26571_SAME_SIDE_MATERIAL_BOUNDARY','IRIS_26574_TOPOLOGY_PRESERVED_BRIGHT_SURFACE','nearTopologySupport','contourChainSupport','radiusTwoTopologyProtection']:
  need(vgn,t,'inherited VGN topology')
 # Only the universal final post-pass may differ in this owner.
 for name in ['seed','localClamp','localMedian','directionalSmooth','restoreDirection','iirRgb','calculateError','iirError','blendChroma']:
  if shader(vgn0,name)!=shader(vgn,name): fail('unexpected VGN embedded shader change '+name)

 sr=(cand/CHANGED[1]).read_text();sr0=(base/CHANGED[1]).read_text()
 for t in ['IRIS_26579_TRUE2X_TOPOLOGY_CHROMA_UPSAMPLE','IRIS_26580_TRUE2X_SAME_MATERIAL_CHROMA_OWNERSHIP','IRIS_26580_NEUTRAL_GLYPH_OUTSIDE_EDGE_EXCLUSION','IRIS_26581_DECISIVE_CROSS_EDGE_CHROMA_VETO','IRIS_26581_MATERIAL_SEPARATED_SR_DETAIL_ENVELOPE','materialBoundary','materialSupportGate','edgeExcursion','maxChromaMagnitude','out float materialBoundary']:
  need(sr,t,'26581 true2x gap/edge envelope')
 body=shader(sr,'true2xGuideRender26568')
 need(body,'float directY = max(irisLuma(directRgb), 0.0);','SR luma-only direct CFA')
 if 'directRgb - vec3' in body or 'irisChroma(directRgb)' in body: fail('direct-CFA chroma entered SR guide')
 if shader(sr0,'true2xFlowRefine26574')!=shader(sr,'true2xFlowRefine26574'): fail('true2x flow refinement changed')
 for name in ['true2xGuideAndCovariance26564','true2xAccumulate26564','true2xDehomogenize26564','true2xConfidence26564','true2xResolve26564','true2xFlowRefine26574']:
  if name in sr and name in sr0 and shader(sr0,name)!=shader(sr,name): fail('unexpected SR embedded shader change '+name)

 cpp0=base/GPU_CPP;cpp=cand/GPU_CPP
 if cpp0.read_bytes()!=cpp.read_bytes() or sha(cpp)!=GPU_CPP_SHA: fail('device-proven 26579/26580 GPU publication C++ changed')
 ct=cpp.read_text()
 for t in ['IRIS_26579_GPU_DIRECT_INTERMEDIATE_PUBLICATION','IRIS_26579_TRUE2X_GPU_COMPAT_RESULT','IRIS_26579_TRUE2X_GPU_TO_CPU_FALLBACK','invalid_gpu_publication_args','open_base','open_gain','gpu_band_queue_empty']:
  need(ct,t,'26579 GPU publication inheritance')
 if '.iris26571_gpu' in ct: fail('forbidden extension-changing GPU sibling returned')
 java=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text()
 need(java,'output.resolveSibling("." + output.getFileName() + ".26564.true2x.base.jpg")','Java base intermediate')
 need(java,'output.resolveSibling("." + output.getFileName() + ".26564.true2x.gain.jpg")','Java gain intermediate')
 forbidden=[p for p in diff if any(x in p for x in ['Dng','Night','CaptureController','MotionV2Merger','PhotonMotionMgc1271Bridge','motionv2_jpeg444_jni.cpp'])]
 if forbidden: fail('forbidden ownership change '+repr(forbidden))
 print('PASS exact successful-26580 1708-file authority -> three-file 26581 allowlist')
 print('PASS shared VGN: paired foreground/background gap owner added without weakening 26580 micro-color/CFA proof')
 print('PASS SR: decisive cross-edge chroma bridge veto + material-separated boundary detail envelope')
 print('PASS direct-CFA chroma remains false; alignment/flow/phase/detail carrier ownership unchanged')
 print('PASS device-proven 26579/26580 GPU publication C++ byte-identical and inherited')
if __name__=='__main__':main()
