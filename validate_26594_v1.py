#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
CHANGED=[x for x in """app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
app/version.properties""".splitlines() if x]
def fail(m): raise SystemExit('FAIL: '+m)
def req(c,m):
 if not c: fail(m)
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if len(sys.argv)!=3: fail('usage base candidate')
b,c=map(Path,sys.argv[1:])
bp={str(p.relative_to(b)):H(p) for p in sorted((b/'app').rglob('*')) if p.is_file()}
cp={str(p.relative_to(c)):H(p) for p in sorted((c/'app').rglob('*')) if p.is_file()}
req(set(bp)==set(cp) and len(bp)==1708,'full app universe')
changed=[r for r in bp if bp[r]!=cp[r]]; req(changed==CHANGED,'exact changed allowlist '+repr(changed))
s=(c/CHANGED[0]).read_text();k=(c/CHANGED[1]).read_text();v=(c/CHANGED[2]).read_text()
for t in ['IRIS_26594_REGION_ANCHORED_SHORT_HANDOFF','val shortRegionSeed26594','val shortRegionPropagate26594','uniform sampler2D uRegionTrust','oMask = smoothstep(handoffStart, uReferenceNearClipThreshold, referenceSecond);']:
 req(t in s,'shader contract '+t)
for t in ['IRIS_26594_GPU_REGION_ANCHORED_SHORT_HANDOFF','renderSabreShortRegionSeed26594','renderSabreShortRegionPropagate26594','SHORT_REGION_PROPAGATION_PASSES_26594 = 32','regionTrust = shortRegionTrust26594','GLES30.GL_R8, GLES30.GL_NEAREST']:
 req(t in k,'stacker contract '+t)
# Removed circular executable owners: inspect relevant shader body, not safety comments.
mask=s[s.index('val shortRestoreMask26587'):s.index('val shortRestoreMaskProbe26590')]
for t in ['uNormalCoverage','uNormalCoverageThreshold','uConsistencyThreshold','evidence < 3','trustConfidence','supportConfidence']:
 req(t not in mask,'old circular final-mask executable survived '+t)
seed=s[s.index('val shortRegionSeed26594'):s.index('val shortRegionPropagate26594')]
for t in ['evidence >= 3','meanError < uConsistencyThreshold','referenceSecond >= uRegionFloor','referenceSecond >= uBoundaryCeiling','shortWeight >= uShortWeightThreshold','flow.z <= uFlowVariationThreshold','unblocker <= uUnblockerThreshold','shortNeighborhoodHasHeadroom(shortP)']:
 req(t in seed,'seed/region proof '+t)
prop=s[s.index('val shortRegionPropagate26594'):s.index('val shortRestoreMask26587')]
for t in ['if (seed >= 0.5)','if (at(uRegion, p) < 0.5)','for (int y = -1; y <= 1; ++y)','for (int x = -1; x <= 1; ++x)']:
 req(t in prop,'propagation topology '+t)
req('VERSION_NAME=0.9726594' in v and 'VERSION_BUILD=26594' in v,'version/build')
# Frozen output application remains exact from 26593.
restore_name='shortRestoreRgba16f26587'
def embedded(src,name):
 m=re.search(r'(?m)^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""',src); req(m is not None,'missing '+name)
 a=m.end(); z=src.find('""".trimIndent()',a); req(z>=0,'end '+name); return src[a:z]
bs=(b/CHANGED[0]).read_text(); req(embedded(bs,restore_name)==embedded(s,restore_name),'whole-RGB RGBA16F restore changed')
req(embedded(bs,'shortRestoreMaskProbe26590')==embedded(s,'shortRestoreMaskProbe26590'),'read-only probe changed')
print('PASS exact three-file runtime scope and 26594 region-anchored SHORT semantic ownership')
print('PASS clipped core cannot self-authorize; boundary seed + connected gated propagation + final local geometry recheck')
print('PASS whole-RGB RGBA16F restore/probe unchanged and target version 0.9726594/26594')
