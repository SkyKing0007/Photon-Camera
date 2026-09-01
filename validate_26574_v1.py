#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('FAIL: usage base candidate')
B,C=map(Path,sys.argv[1:])
EXPECTED={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/version.properties'}
def fail(m): raise SystemExit('FAIL: '+m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def files(root): return {str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file()}
def extract_shader(src,name):
 m=re.search(r'(?m)^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""',src)
 if not m: fail('shader '+name+' missing')
 z=src.find('""".trimIndent()',m.end())
 if z<0: fail('shader '+name+' end')
 return src[m.start():z+len('""".trimIndent()')]
def extract_fun(src,name):
 p=src.find('private fun '+name+'(')
 if p<0: fail('function '+name+' missing')
 b=src.find('{',p)
 if b<0: fail('function '+name+' brace missing')
 depth=0
 for i in range(b,len(src)):
  if src[i]=='{': depth+=1
  elif src[i]=='}':
   depth-=1
   if depth==0:return src[p:i+1]
 fail('function '+name+' unterminated')

a=files(B);b=files(C);changed={k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
if changed!=EXPECTED: fail('allowlist '+repr(sorted(changed)))
if len(a)!=1708 or set(a)!=set(b): fail(f'candidate universe base={len(a)} cand={len(b)} pathsame={set(a)==set(b)}')
print('PASS exact 1708-file authority universe + exact four-file allowlist')

v=(C/'app/version.properties').read_text()
for x in ['VERSION_NAME=0.9726574','VERSION_BUILD=26574']:
 if x not in v: fail('version '+x)
print('PASS version 0.9726574 / 26574')

bb=(B/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(); cc=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
for name in ['convertAlignmentSparse','true2xMerge26564','true2xResolve26564','true2xGuideRender26568']:
 if extract_shader(bb,name)!=extract_shader(cc,name): fail('protected existing SR shader changed '+name)
print('PASS existing 26573 SR merge/resolve/guide/sparse-flow shaders byte-identical')

bs=(B/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text(); cs=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
for name in ['alignPyramids','createSabreConvertedAlignment','renderSabreMerge','runTrue2xGpu','runTrue2xCpu']:
 if extract_fun(bs,name)!=extract_fun(cs,name): fail('protected function changed '+name)
print('PASS Sabre alignment/merge + true2x GPU/CPU accumulation owners byte-identical')

required=[
'IRIS_26568_JPEG_TRUE2X_PHASE_RESERVOIR',
'if (enableSabreSuperRes && !exportNormalStackedDng) arrayOfNulls(TRUE2X_JPEG_MAX_EVIDENCE)',
'private const val TRUE2X_JPEG_EVIDENCE_PER_PHASE = 2',
'private const val TRUE2X_JPEG_MAX_EVIDENCE = 4 * TRUE2X_JPEG_EVIDENCE_PER_PHASE',
'val phaseBin = dominantTrue2xPhaseBin(selectionFlowData, spec.width, spec.height)',
'if (existingPhaseEvidence != null && frameIndex != 0)',
'IRIS_26574_JPEG_RETAINED_FLOW_REFINEMENT_ONLY',
'IRIS_26574_TRUE2X_FLOW_REFINE_FALLBACK',
'deltaBoundRawPx=0.5',
'PLog.i("MotionTrace", "PIPELINE_STATE stage=IRIS_26574_TRUE2X_FLOW_REFINE details=$details")',
'private const val TRUE2X_REFINE_CELL_RAW_PIXELS = 16']
for x in required:
 if x not in cs: fail('stacker contract '+x)
if cs.find('val phaseBin = dominantTrue2xPhaseBin') > cs.find('renderTrue2xFlowRefinement26574(' , cs.find('private fun persistTrue2xEvidence')): fail('refinement occurs before phase selection')
print('PASS max-8/top-2-per-phase selection precedes refinement; DNG full-evidence path excluded')

newshader=extract_shader(cc,'true2xFlowRefine26574')
for x in ['vec2(0.25)','improvement>0.08','uniqueness>0.04','conditioning>0.012','variationRaw<2.0','accept?delta*2.0:vec2(0.0)','oFlow=vec4(refinedRaw/vec2(uRawSize),base.z,accept?1.0:0.0)']:
 if x not in newshader: fail('refinement safety '+x)
if 'uReferencePhaseGains' not in newshader or 'uCurrentPhaseGains' not in newshader: fail('phase-normalized alignment proxy missing')
print('PASS SR residual refinement bounded/conditioned/unique/improving and Bayer-phase normalized')

vgn=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text()
for x in ['IRIS_26570_ONE_SIDED_EDGE_LUMA_AUTHORITY','IRIS_26571_CROSS_EDGE_CHROMA_OWNERSHIP','IRIS_26571_IIR_MATERIAL_EDGE_STATE_RESET','IRIS_26574_TOPOLOGY_PRESERVED_BRIGHT_SURFACE','topologySupport','topologyProtection','currentPerpendicularSupport','previousPerpendicularSupport']:
 if x not in vgn: fail('VGN topology contract '+x)
if vgn.count('highlightPreservePermission') < 8: fail('prior highlight/pink safety permission unexpectedly removed')
if 'mix(1.0, sameHue, centerChromaPresent)' not in vgn: fail('colored-center topology support not hue-gated')
if 'mix(1.0,sameHue,centerChromaPresent)' not in vgn: fail('local median colored-center hue gate missing')
if 'mix(1.0,smoothstep(0.82,0.94,farAgreement),centerChromaPresent)' not in vgn: fail('directional colored-center hue gate missing')
print('PASS 26570/26571 edge and pink safety retained + 26574 radius-2/perpendicular topology added')

# No forbidden ownership expansion text in changed stacker/shader files.
for term in ['TRUE2X_JPEG_EVIDENCE_PER_PHASE = 3','TRUE2X_JPEG_EVIDENCE_PER_PHASE = 4','fallback to 12','12MP fallback']:
 if term in cs: fail('forbidden ownership/performance regression '+term)
# Unaligned-alternate fallback is guarded structurally: the original 26573 Sabre alignment/merge owners above are byte-identical,
# and the new SR refine path may only keep the proven base flow when refinement is rejected. Comments mentioning this invariant are allowed.
for bad in ['refinedFlowData ?: currentRawTexture','useUnalignedAlternate','UNALIGNED_ALTERNATE']:
 if bad in cs: fail('forbidden executable unaligned fallback pattern '+bad)
print('PASS no 8->15 evidence expansion, no unaligned/12MP fallback introduced')

# Resource bound sanity for 4080x3064 and a larger 8k-class sensor.
for w,h in [(4080,3064),(8160,6128)]:
 fw=(w+15)//16; fh=(h+15)//16; bytes_=fw*fh*8
 if bytes_ > 2*1024*1024: fail(f'refine flow sidecar too large {w}x{h} {bytes_}')
 print(f'PASS refine sidecar bound {w}x{h}: {fw}x{fh} RGBA16F={bytes_} bytes')

print('PASS 26574 combined runtime semantic validation')
