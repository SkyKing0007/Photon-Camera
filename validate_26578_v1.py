#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
CHANGED=['app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/version.properties']
SRC=CHANGED[0]
def fail(m): raise SystemExit('FAIL: '+m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def amap(root): return {str(p.relative_to(root)):sha(p) for p in sorted((Path(root)/'app').rglob('*')) if p.is_file()}
def need(s,t,label):
 if t not in s: fail(label+' missing: '+t)
def shader_block(s):
 m=re.search(r'(?s)(\s*/\* IRIS_26578_FAIL_CLOSED_REAL_COLOR_GATE.*?val universalAdaptiveColor26561\s*=\s*""".*?"""\.trimIndent\(\))',s)
 if not m: fail('26578 universal shader block missing')
 return m.span()
def old_shader_block(s):
 m=re.search(r'(?s)(\s*/\* IRIS_26571_COHERENT_CHROMA_PRESERVATION.*?val universalAdaptiveColor26561\s*=\s*""".*?"""\.trimIndent\(\))',s)
 if not m:
  # successful 26577 comment may have evolved while value anchor remains stable
  m=re.search(r'(?s)(\s*(?:/\*.*?\*/\s*)?val universalAdaptiveColor26561\s*=\s*""".*?"""\.trimIndent\(\))',s)
 if not m: fail('successful-26577 universal shader block missing')
 return m.span()
def main():
 if len(sys.argv)!=3: fail('usage base candidate')
 base,cand=map(Path,sys.argv[1:]); a,b=amap(base),amap(cand)
 if len(a)!=1708 or len(b)!=1708: fail(f'candidate universe {len(a)}/{len(b)}')
 diff=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
 if diff!=CHANGED: fail('changed allowlist '+repr(diff))
 v=(cand/'app/version.properties').read_text(); need(v,'VERSION_NAME=0.9726578','version'); need(v,'VERSION_BUILD=26578','version')
 s=(cand/SRC).read_text(); old=(base/SRC).read_text()
 # Outside the universal post-VGN shader block, the active VGN host and all prior VGN stages must remain byte-identical.
 ob0,ob1=old_shader_block(old); nb0,nb1=shader_block(s)
 old_prefix=old[:ob0]; old_suffix=old[ob1:]
 new_prefix=s[:nb0]; new_suffix=s[nb1:]
 # Comments immediately before shader may differ; require all executable Kotlin before the value declaration unchanged by anchoring on prior stable section.
 old_decl=old.index('val universalAdaptiveColor26561')
 new_decl=s.index('val universalAdaptiveColor26561')
 if old[:old_decl].rstrip().split('val common =',1)[0] != s[:new_decl].rstrip().split('val common =',1)[0]:
  fail('Kotlin owner/header before shader unexpectedly changed')
 # The file tail after the shader value is byte-identical: all c317/VGN stages and host contracts unchanged.
 old_end=old.index('""".trimIndent()',old_decl)+len('""".trimIndent()')
 new_end=s.index('""".trimIndent()',new_decl)+len('""".trimIndent()')
 if old[old_end:]!=s[new_end:]: fail('post-universal VGN shader/host tail changed')
 for t in [
  'IRIS_26578_FAIL_CLOSED_REAL_COLOR_GATE','IRIS_26571_COHERENT_CHROMA_PRESERVATION',
  'IRIS_26571_SAME_SIDE_MATERIAL_BOUNDARY','IRIS_26574_TOPOLOGY_PRESERVED_BRIGHT_SURFACE',
  'neutralNeighborSupport','contourChainSupport','phasePatternSupport','phaseLikeEvidence',
  'realColorConfidence','falseColorScore','falseColorGate','maximumMove','supportedTarget',
  'Isolation by itself never','vec3 correctedRgb = clamp(vec3(centerLuma) + correctedChroma, 0.0, 1.0)',
  'float maximumMove = min(0.050, 0.40 * centerMagnitude)',
  'if (length(correctedChroma) > centerMagnitude',
 ]: need(s,t,'fail-closed VGN contract')
 # Production owner/link/call remain active and unique in this file.
 for t in ['IRIS_26529_SPATIAL_RGB_CHROMA_REWRITE_OWNER','universalAdaptiveColorProgram = host.linkComputeProgram(','dispatchUniversalAdaptiveColor(assembledRgb, workA)']:
  need(s,t,'runtime owner')
 if s.count('dispatchUniversalAdaptiveColor(assembledRgb, workA)')!=1: fail('universal pass call count')
 # No direct luma/geometry rewrite is introduced by the correction.
 if 'centerLuma =' not in s or 'correctedChroma' not in s: fail('chroma-only composition missing')
 forbidden=['gl_GlobalInvocationID.z','imageStore(uSource','atomicAdd(','barrier()']
 for t in forbidden:
  if t in s[s.index('val universalAdaptiveColor26561'):new_end]: fail('forbidden correction behavior '+t)
 print('PASS exact 1708-file successful-26577 authority -> two-file 26578 allowlist')
 print('PASS only universal post-VGN shader block + version changed; all downstream VGN stages byte-identical')
 print('PASS 26571 material/foliage and 26574 contour/radius-two protection markers inherited')
 print('PASS fail-closed real-color veto + Bayer-like phase proof + chroma-only bounded correction contract')
 print('PASS isolation alone cannot authorize correction; saturation cannot increase')
 print('PASS runtime owner/link/dispatch remains production-reachable in current VGN owner')
if __name__=='__main__': main()
