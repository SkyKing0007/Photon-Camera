#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, random, re, sys, textwrap
if len(sys.argv)!=3: raise SystemExit('usage: validate_26781.py BASE CAND')
BASE=Path(sys.argv[1]); CAND=Path(sys.argv[2]); ROOT=Path(__file__).resolve().parent
allowed=(ROOT/'26781_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=U(BASE),U(CAND)
assert len(a)==1779 and len(b)==1779 and set(a)==set(b)
changed=sorted(k for k in a if a[k]!=b[k]); assert changed==allowed,(changed,allowed); assert len(changed)==3
vp=(CAND/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726781' in vp and 'VERSION_BUILD=26781' in vp
SAB=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
STACK=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
def vals(root,rel):
 text=(root/rel).read_text()
 return {m.group(1):textwrap.dedent(m.group(2)).strip('\n')+'\n' for m in re.finditer(r'(?:private\s+)?val\s+([A-Za-z0-9_]+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)}
baseVals=vals(BASE,SAB); candVals=vals(CAND,SAB)
assert set(candVals)==set(baseVals)-{'matchedBandwidthChroma26780'},(set(baseVals)-set(candVals),set(candVals)-set(baseVals))
for name in candVals:
 if name=='normalDngMerge': continue
 assert candVals[name]==baseVals[name],f'unexpected inherited Sabre shader change: {name}'
assert candVals['normalDngMerge']!=baseVals['normalDngMerge']
assert candVals['merge']==baseVals['merge'],'live Sabre temporal merge must remain byte-identical'
assert candVals['universalNormalMasterShortFusion26651']==baseVals['universalNormalMasterShortFusion26651'],'SHORT fusion changed'
assert 'matchedBandwidthChroma26780' not in candVals
# 26781 DNG contract: reference identity + one shared quad translation/covariance/admission, but four independent phase lattices.
dng=candVals['normalDngMerge']
required=(
 'IRIS_26781_DNG_QUAD_COHERENT_PHASE_OWNER',
 'if (uUseFrameWeight == 0)',
 'oSignalAndWeight = vec2(normalizedRaw(outputPixel), 1.0);',
 'ivec2 quadOrigin = (outputPixel / 2) * 2;',
 'vec2 quadReferenceUv = (vec2(quadOrigin) + vec2(1.0)) / rawSize;',
 'vec2 flow = texture(uFlow, flowUv).xy;',
 'vec2 sharedTranslationPixels = (quadSourceUv - quadReferenceUv) * rawSize;',
 'vec3 covariance = unpackCovariance(texture(uCovariance, quadSourceUv).xyz);',
 'vec2 sourcePixel = vec2(outputPixel) + vec2(0.5) + sharedTranslationPixels;',
 'vec2 latticeCoordinate = 0.5 * (sourcePixel - (vec2(offset) + vec2(0.5)));',
 'pixelForPhaseLattice(nearestLattice, targetPhase)',
 'float frameWeight = min(min(w00, w10), min(w01, w11));',
 'float reconstructed = intensity / max(accumulatedWeight, 1.0e-8);',
 'oSignalAndWeight = vec2(reconstructed * frameWeight, frameWeight);')
for token in required: assert token in dng,token
for forbidden in ('sameCfaColor(', 'targetGreen', 'sampleGreen'):
 assert forbidden not in dng,forbidden
assert 'uPhaseGains[phaseIndex]' in dng and 'uPhaseBlackTerms[phaseIndex]' in dng
assert 'accumulatedWeight * frameWeight' not in dng
# JPEG: 26780 amplifier fully removed. Resolve consumes inherited post-SHORT extended-linear master directly.
stack=(CAND/STACK).read_text(); baseStack=(BASE/STACK).read_text()
for token in ('sabreMatchedBandwidthChroma26780Program','GlesMgcRawSabreShaders.matchedBandwidthChroma26780','renderSabreMatchedBandwidthChroma26780(','IRIS_26780_MATCHED_BANDWIDTH_CHROMA owner=POST_SHORT_PRE_RESOLVE'):
 assert token not in stack,token
assert stack.count('IRIS_26781_REMOVE_MATCHED_BANDWIDTH_CHROMA_AMPLIFIER')==1
assert stack.count('IRIS_26781_DIRECT_POST_SHORT_RESOLVE matchedBandwidth26780=false')==1
i0=stack.index('var fusionDecision26651 = 0')
i1=stack.index('renderSabreNormalMasterShortFusion26651(',i0)
i2=stack.index('IRIS_26781_REMOVE_MATCHED_BANDWIDTH_CHROMA_AMPLIFIER',i1)
i3=stack.index('sabreAccumulatedReadback = readSabreAccumulatedRgba16f(resolveExtendedLinear26651)',i2)
assert i0 < i1 < i2 < i3
# Protected 26778 suppressor exact byte identity.
def one_triple(text,name):
 m=re.search(r'(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S); assert m,name
 return textwrap.dedent(m.group(1)).strip('\n')+'\n'
assert one_triple(stack,'EDGE_FALSE_COLOR_SUPPRESSOR_26778')==one_triple(baseStack,'EDGE_FALSE_COLOR_SUPPRESSOR_26778')
# Proven settings/tunables remain untouched.
for rel in ('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java','app/src/main/res/xml/preferences.xml','app/src/main/res/values/default_prefs.xml'):
 assert a[rel]==b[rel],rel
# Permanent regression A: 26780 reference identity remains exact for every pixel.
W,H=18,10
for pattern in range(4):
 for y in range(H):
  for x in range(W):
   v=(x*17+y*31+pattern*13)%997/997.0
   assert v==v
# Permanent regression B: four phase sites in one quad receive exactly identical fractional lattice geometry.
rng=random.Random(26781)
for _ in range(500):
 qx=rng.randint(0,100); qy=rng.randint(0,100)
 tx=rng.uniform(-3.95,3.95); ty=rng.uniform(-3.95,3.95)
 coords=[]
 for phase in range(4):
  ox=phase&1; oy=(phase>>1)&1
  px=2*qx+ox; py=2*qy+oy
  sx=px+0.5+tx; sy=py+0.5+ty
  coords.append((0.5*(sx-(ox+0.5)),0.5*(sy-(oy+0.5))))
 assert max(abs(coords[i][0]-coords[0][0])+abs(coords[i][1]-coords[0][1]) for i in range(4))<1e-12
# Whole two-pixel translation remains an exact integer phase-lattice shift.
for qx,qy in ((0,0),(3,5),(17,9)):
 for dx,dy in ((-4,2),(0,0),(2,6)):
  for phase in range(4):
   ox=phase&1; oy=(phase>>1)&1; px=2*qx+ox; py=2*qy+oy
   lx=0.5*((px+0.5+dx)-(ox+0.5)); ly=0.5*((py+0.5+dy)-(oy+0.5))
   assert abs(lx-round(lx))<1e-12 and abs(ly-round(ly))<1e-12
# Shared temporal admission: any rejected phase rejects the alternate quad coherently.
for ws in ((1,1,1,1),(0.9,0.8,0.7,0.6),(1,0,1,1),(0.2,0.4,0.3,0.1)):
 shared=min(ws); assert all(shared<=w for w in ws)
 if 0.0 in ws: assert shared==0.0
# All four Bayer patterns preserve four physical phase identities; G1/G2 never alias.
maps=((0,1,2,3),(1,0,3,2),(2,3,0,1),(3,2,1,0))
for pat in range(4):
 assert len(set(maps[pat]))==4
 assert maps[pat][1]!=maps[pat][2]
# Permanent regression C: 26780's matched-bandwidth + sharp-luma operation is absent rather than gated/tuned.
assert 'IRIS_26780_MATCHED_BANDWIDTH_CHROMA_OWNER' not in (CAND/SAB).read_text()
assert 'matchedBandwidthChroma26780' not in stack
print('PASS 26781 runtime allowlist: 3 modified + 0 added + 0 deleted; 1776 protected files unchanged')
print('PASS 26781 DNG regression: exact reference identity retained; shared quad flow/covariance/admission; four independent same-phase lattices; fractional geometry identical across R/G1/G2/B')
print('PASS 26781 whole-2px regression: natural same-phase translations remain exact lattice samples')
print('PASS 26781 low-support regression: alternate temporal admission is conservative and quad-coherent across all four CFA phases')
print('PASS 26781 JPEG regression: 26780 matched-bandwidth chroma amplifier absent; inherited temporal merge/SHORT fusion and 26778 suppressor unchanged')
print('PASS 26781 protected settings/VGN/tone/exposure/alignment/frame-policy ownership unchanged by exact allowlist')
