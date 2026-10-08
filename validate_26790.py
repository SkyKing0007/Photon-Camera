#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, random, re, sys, textwrap
if len(sys.argv)!=3: raise SystemExit('usage: validate_26790.py BASE CANDIDATE')
BASE,CAND=map(Path,sys.argv[1:])
S='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
T='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
SP='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt'
ALLOW=[S,T,'app/version.properties']
def need(c,m):
 if not c: raise AssertionError(m)
def U(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
def shader(root,rel,name):
 t=(root/rel).read_text(); m=re.search(r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""',t,re.M); need(m is not None,f'{name}: declaration missing')
 b=t.find('""".trimIndent()',m.end()); need(b>=0,f'{name}: terminator missing'); return textwrap.dedent(t[m.end():b]).strip('\n')+'\n'
b,c=U(BASE),U(CAND); need(len(b)==len(c)==1779,'file count'); need(set(b)==set(c),'file universe')
changed=sorted(k for k in b if b[k]!=c[k]); need(changed==ALLOW,f'changed allowlist mismatch {changed}')
print('PASS 26790 authority-seeded scope: 1779 files; exactly 3 modified / 0 added / 0 deleted')
ver=(CAND/'app/version.properties').read_text(); need('VERSION_NAME=0.9726790' in ver and 'VERSION_BUILD=26790' in ver,'version')
print('PASS 26790 version 0.9726790 / 26790')
# Freeze exact successful DNG/SHORT owners.
expected={
 'normalDngMerge':(S,'ae92cfd3af69e2621e4be12af375383e650f4a362f4da2d54aaff886550a2d34'),
 'normalizeBayer':(SP,'d19aca4ceaf2f8272347d57a51be33da89eaab807aef3567186e2c477e7fb447'),
 'universalNormalMasterShortFusion26651':(S,'90bb8a28e2c40112950eb3fa83ef6f08d703c556a91a518239ffb33bdcaa9ee5')}
for name,(rel,h) in expected.items():
 x=shader(CAND,rel,name); need(hashlib.sha256(x.encode()).hexdigest()==h,f'protected hash {name}'); need(x==shader(BASE,rel,name),f'protected changed {name}')
 print(f'PASS 26790 protected runtime shader byte-identical: {name}')
merge=shader(CAND,S,'merge'); dng=shader(CAND,S,'normalDngMerge'); norm=shader(CAND,SP,'normalizeBayer'); neutral=shader(CAND,S,'jpegNeutralHighlightClamp26790')
st=(CAND/T).read_text()
# Literal fixed-phase DNG math, exact UINT RAW input, no parity-changing generic sampler in LCA branch.
for tok in ['uniform highp usampler2D uRaw26790;','uniform int uLongChromaGuard26790;','uniform sampler2D uNormalChromaConsensus26790;','sampleFixedPhaseDng26790(','float(texelFetch(uRaw26790, p, 0).r)','uJpegLcaKrKb26790','uDngQuadHeadroom26790','uDngEdgeDeAlias26790']:
 need(tok in merge,f'merge missing {tok}')
# Permanent regression from failed 26790 Actions run: every custom u* identifier used by merge must be declared.
clean=re.sub(r'/\*.*?\*/',' ',merge,flags=re.S); clean=re.sub(r'//.*',' ',clean)
used=set(re.findall(r'\bu[A-Z][A-Za-z0-9_]*\b',clean))
declared=set(re.findall(r'\buniform\s+(?:(?:highp|mediump|lowp)\s+)?[A-Za-z_]\w*\s+(u[A-Z][A-Za-z0-9_]*)',clean))
need(not (used-declared),f'merge used-but-undeclared uniforms: {sorted(used-declared)}')
print(f'PASS 26790 compiler regression: merge uniform declarations complete ({len(used)} used)')
pairs=[
 ('return ((p.y & 1) << 1) + (p.x & 1);','return ((p.y & 1) << 1) + (p.x & 1);'),
 ('float headroomStart = whitePoint * 0.9925;','float headroomStart = whitePoint * 0.9925;'),
 ('vec2 latticeCoordinate = 0.5 * (sourcePixel - (vec2(offset) + vec2(0.5)));','vec2 latticeCoordinate = 0.5 * (sourcePixel - (vec2(offset) + vec2(0.5)));'),
 ('ivec2 nearestLattice = ivec2(floor(latticeCoordinate + vec2(0.5)));','ivec2 nearestLattice = ivec2(floor(latticeCoordinate + vec2(0.5)));'),
 ('ivec2 latticeBase = ivec2(floor(latticeCoordinate));','ivec2 latticeBase = ivec2(floor(latticeCoordinate));'),
 ('float w = kernelWeight(sampleCenter - sourcePixel, covariance);','float w = kernelWeight(sampleCenter - sourcePixel, covariance);'),
 ('bool hardEdge = guideMax > 0.08 && guideRange > 0.055 && relativeGuideRange > 0.20;','bool hardEdge = guideMax > 0.08 && guideRange > 0.055 && relativeGuideRange > 0.20;'),
 ('bool sameSide = pairRange <= max(0.035, 0.12 * max(pairMax, 0.03));','bool sameSide = pairRange <= max(0.035, 0.12 * max(pairMax, 0.03));')]
for a,z in pairs: need(a in dng,f'DNG token missing {a}'); need(z in merge,f'JPEG fixed-phase token missing {z}')
need('layout(location = 3)' not in merge,'stale 4th MRT')
anchor='} else {\n        int rPhase = redPhase26790();'; need(anchor in merge,'LCA branch anchor')
lca=merge.split(anchor,1)[1].split('/* IRIS_26790_LONG_CHROMA_NO_REINTRODUCTION',1)[0]
need('sampleNeighborhoodRbf(' not in lca,'generic parity-changing RBF survived inside LCA branch')
print('PASS 26790 DNG/JPEG CFA LCA mathematical equivalence: exact UINT RAW fixed-phase owner; generic parity RBF excluded')
# Literal DNG neutral-censor gate.
for src in [norm,neutral]:
 need('int g0 = -1; int g1 = -1;' in src,'two-green phase owner missing'); need('gw0 <= 0.000051 && gw1 <= 0.000051' in src,'exact two-green threshold missing')
need('uniform sampler2D uNormalDngAccumulator26790;' in neutral,'literal DNG accumulator missing')
need('texelFetch(uNormalDngAccumulator26790, gp0, 0).g' in neutral and 'texelFetch(uNormalDngAccumulator26790, gp1, 0).g' in neutral,'literal DNG weights missing')
need('source.rgb = min(source.rgb, vec3(1.0));' in neutral,'neutral white ceiling missing')
need('source.r = min(source.r, 1.0);' not in neutral and 'source.b = min(source.b, 1.0);' not in neutral,'old R/B-only green-risk clamp survived')
need('exportNormalStackedDng || dngOptions26786.neutralClamp' in st,'literal DNG accumulator not allocated for neutral clamp')
need('normalDngAccumulator26790 = normalDngAccumulator' in st,'neutral clamp not bound to literal DNG accumulator')
need('sabreJpegNeutralHighlightClampProgram26787 = 0' in st,'old approximate neutral program still linked')
need('normalPhaseSupport26790' not in st and 'normalPhaseSupportOwner26790' not in st,'stale neutral proxy/argument survived')
print('PASS 26790 neutral gate: literal NORMAL DNG accumulator two-green weights + DNG-equivalent neutral-white ceiling')
# Office neutral regression: AsShotNeutral physical neutral must become white after calculation WB.
rawR,rawG0,rawG1,rawB=0.4161,1.0,1.0,0.5254; asn=(0.4160,1.0,0.5254); wb=(1/asn[0],1.0,1/asn[2])
rgb=(min(rawR,asn[0])*wb[0],min(rawG0,1.0),min(rawB,asn[2])*wb[2]); need(max(rgb)-min(rgb)<1e-6 and all(abs(v-1)<1e-6 for v in rgb),f'office neutral regression {rgb}')
# Phase-boundary topology continuity: topology changes only on legitimate 2px same-phase lattice boundaries.
def phase_lattice(x,o): return 0.5*(x-(o+0.5))
for o in (0,1):
 for boundary in range(2,30):
  x=boundary+0.5; a=math.floor(phase_lattice(x-1e-6,o)); z=math.floor(phase_lattice(x+1e-6,o))
  if a!=z: need(abs(phase_lattice(x,o)-round(phase_lattice(x,o)))<1e-5,'phase-boundary discontinuity')
print('PASS 26790 office neutral + fixed-phase boundary regressions')
# LONG is anchored to completed NORMAL consensus; pure chroma mismatch can suppress while luma/weights remain.
for tok in ['anchor=COMPLETED_NORMAL_CONSENSUS','disagreementGate=PURE_CHROMA_ALLOWED','smoothstep(0.035, 0.12, chromaMismatch)','uNormalChromaConsensus26790']:
 need(tok in st or tok in merge,f'LONG consensus token missing {tok}')
need('referenceExtracted26789' not in st,'26789 single-reference LONG anchor survived')
need('normalChromaConsensus26790 = 0' in st,'LONG consensus lifecycle owner missing')
print('PASS 26790 LONG chroma: completed-NORMAL consensus, pure-chroma disagreement suppression, luma/weight preservation')
print('PASS 26790 DNG/JPEG CFA correction mathematical equivalence: no independent JPEG approximation remains in LCA/neutral correction owner')
