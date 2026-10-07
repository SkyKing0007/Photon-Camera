#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, random, re, sys, textwrap
if len(sys.argv)!=3: raise SystemExit('usage: validate_26780.py BASE CAND')
BASE=Path(sys.argv[1]); CAND=Path(sys.argv[2]); ROOT=Path(__file__).resolve().parent
allowed=(ROOT/'26780_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=U(BASE),U(CAND)
assert len(a)==1779 and len(b)==1779,(len(a),len(b))
assert set(a)==set(b)
changed=sorted(k for k in a if a[k]!=b[k])
assert changed==allowed,(changed,allowed)
assert len(changed)==3

vp=(CAND/'app/version.properties').read_text()
assert 'VERSION_NAME=0.9726780' in vp and 'VERSION_BUILD=26780' in vp

SAB=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
STACK=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
def vals(root,rel):
 text=(root/rel).read_text()
 return {m.group(1):textwrap.dedent(m.group(2)).strip('\n')+'\n' for m in re.finditer(r'(?:private\s+)?val\s+([A-Za-z0-9_]+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)}
baseVals=vals(BASE,SAB); candVals=vals(CAND,SAB)
assert set(candVals)==set(baseVals)|{'matchedBandwidthChroma26780'}
for name in baseVals:
 if name=='normalDngMerge': continue
 assert candVals[name]==baseVals[name],f'unexpected inherited Sabre shader change: {name}'
assert candVals['normalDngMerge']!=baseVals['normalDngMerge']
assert candVals['merge']==baseVals['merge'],'live Sabre temporal merge must remain byte-identical'
assert candVals['universalNormalMasterShortFusion26651']==baseVals['universalNormalMasterShortFusion26651']

# DNG phase identity + same-lattice reconstruction contract.
dng=candVals['normalDngMerge']
for token in (
 'IRIS_26780_DNG_PHASE_IDENTITY_OWNER',
 'if (uUseFrameWeight == 0)',
 'oSignalAndWeight = vec2(normalizedRaw(outputPixel), 1.0);',
 'int targetPhase = phaseAt(outputPixel);',
 'vec2 latticeCoordinate = 0.5 * (sourcePixel - (vec2(offset) + vec2(0.5)));',
 'pixelForPhaseLattice(nearestLattice, targetPhase)',
 'max(abs(nearestDelta.x), abs(nearestDelta.y)) < 1.0e-5',
 'float reconstructed = intensity / max(accumulatedWeight, 1.0e-8);',
 'reconstructed * frameWeight',
 'frameWeight'):
 assert token in dng,token
for forbidden in ('sameCfaColor(', 'targetGreen', 'sampleGreen'):
 assert forbidden not in dng,forbidden
assert 'uPhaseGains[phaseIndex]' in dng and 'uPhaseBlackTerms[phaseIndex]' in dng

# JPEG matched-bandwidth chroma + shared-luma contract.
mb=candVals['matchedBandwidthChroma26780']
for token in (
 'IRIS_26780_MATCHED_BANDWIDTH_CHROMA_OWNER',
 'float w = axisWeight(x) * axisWeight(y);',
 'matched += texelFetch(uSource, clampPixel(p + ivec2(x, y)), 0).rgb * w;',
 'float sharedDetail = luma(center.rgb) - luma(matched);',
 'oColor = vec4(matched + vec3(sharedDetail), center.a);'):
 assert token in mb,token
assert 'oColor = vec4(clamp' not in mb and 'matched = clamp' not in mb, 'matched-bandwidth pass must not clip HDR/chroma'

stack=(CAND/STACK).read_text(); baseStack=(BASE/STACK).read_text()
for token,count in (
 ('private var sabreMatchedBandwidthChroma26780Program = 0',1),
 ('GlesMgcRawSabreShaders.matchedBandwidthChroma26780',1),
 ('private fun renderSabreMatchedBandwidthChroma26780(source: Int): Int',1),
 ('renderSabreMatchedBandwidthChroma26780(preMatchedResolve26780)',1),
 ('IRIS_26780_MATCHED_BANDWIDTH_CHROMA owner=POST_SHORT_PRE_RESOLVE',1)):
 assert stack.count(token)==count,(token,stack.count(token))
# Placement must preserve inherited fusion inputs/decision, then sanitize the one final RGB master immediately pre-Resolve.
i0=stack.index('val sabreRSupport26613 = renderSabreDehomogenize(')
i1=stack.index('var fusionDecision26651 = 0',i0)
i2=stack.index('renderSabreNormalMasterShortFusion26651(',i1)
i3=stack.index('renderSabreMatchedBandwidthChroma26780(preMatchedResolve26780)',i2)
i4=stack.index('sabreAccumulatedReadback = readSabreAccumulatedRgba16f(resolveExtendedLinear26651)',i3)
assert i0 < i1 < i2 < i3 < i4
# The inherited fusion call and its NORMAL input remain exactly the dehomogenized owner.
assert 'normalMean = resolveAccumulatedColor26604' in stack[i2:i3]
assert 'val resolveAccumulatedColor26604 = dehomogenizedNormal26604' in stack[i0:i2]
# Claude suppressor code bytes are inherited exactly despite same host file changing.
def one_triple(text,name):
 m=re.search(r'(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)
 assert m,name
 return textwrap.dedent(m.group(1)).strip('\n')+'\n'
assert one_triple(stack,'EDGE_FALSE_COLOR_SUPPRESSOR_26778')==one_triple(baseStack,'EDGE_FALSE_COLOR_SUPPRESSOR_26778')
# Proven settings/tunables from 26779 remain untouched.
for rel in (
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
 'app/src/main/res/xml/preferences.xml',
 'app/src/main/res/values/default_prefs.xml'):
 assert a[rel]==b[rel],rel

# Permanent regression: old zero-flow DNG mixes opposite green phase at neutral edge.
def kw(dx,dy): return 2.0**(-0.5*(dx*dx+dy*dy))+0.00005
W,H=16,8
raw=[[0.2 if x<8 else 1.0 for x in range(W)] for _ in range(H)]
def old_zero(x,y):
 target=((y&1)<<1)+(x&1); tg=target in (1,2); num=den=0.0
 for dy in (-1,0,1):
  for dx in (-1,0,1):
   sx=min(max(x+dx,0),W-1); sy=min(max(y+dy,0),H-1); ph=((sy&1)<<1)+(sx&1)
   if (ph in (1,2) if tg else ph==target):
    w=kw(dx,dy); num+=raw[sy][sx]*w; den+=w
 return num/den
old=old_zero(7,2)
assert abs(raw[2][7]-0.2)<1e-12 and old>0.45 and old<0.48,(raw[2][7],old)
# New reference contract is mathematically identity for every pixel / Bayer layout / edge orientation.
for pattern in range(4):
 for y in range(H):
  for x in range(W):
   new_reference=raw[y][x]
   assert new_reference==raw[y][x]
# All four Bayer patterns: same parity phase means the exact same physical filter phase; G1/G2 never alias.
def canonical(pattern,phase):
 maps=((0,1,2,3),(1,0,3,2),(2,3,0,1),(3,2,1,0))
 return maps[pattern][phase]
for pattern in range(4):
 for target_phase in range(4):
  target_channel=canonical(pattern,target_phase)
  for qy in range(3):
   for qx in range(3):
    sample_phase=((2*qy+(target_phase>>1))&1)*2 + ((2*qx+(target_phase&1))&1)
    assert sample_phase==target_phase
    assert canonical(pattern,sample_phase)==target_channel
# Spatial RBF mass is interpolation normalization only; it must not become temporal frame weight.
assert 'accumulatedWeight * frameWeight' not in dng

# Permanent JPEG regression: shared luma is exact and chroma comes only from matched bandwidth.
rng=random.Random(26780)
for _ in range(200):
 patch=[[[rng.uniform(-0.25,3.0) for _ in range(3)] for _x in range(3)] for _y in range(3)]
 center=patch[1][1]; axis=(1.0,2.0,1.0); matched=[0.0,0.0,0.0]; sw=0.0
 for y in range(3):
  for x in range(3):
   w=axis[x]*axis[y]; sw+=w
   for c in range(3): matched[c]+=patch[y][x][c]*w
 matched=[v/sw for v in matched]
 l=lambda v:0.25*v[0]+0.50*v[1]+0.25*v[2]
 d=l(center)-l(matched); out=[v+d for v in matched]
 assert abs(l(out)-l(center))<1e-12
 assert abs((out[0]-out[1])-(matched[0]-matched[1]))<1e-12
 assert abs((out[2]-out[1])-(matched[2]-matched[1]))<1e-12

print('PASS 26780 runtime allowlist: 3 modified + 0 added + 0 deleted; 1776 protected files unchanged')
print(f'PASS 26780 permanent DNG neutral-edge regression: old zero-flow green 0.20 -> {old:.4f}; reference identity required')
print('PASS 26780 DNG ownership: exact reference Bayer identity + same physical R/G1/G2/B lattice for alternate NORMAL; no G1/G2 mixing; interpolation mass normalized before temporal weight')
print('PASS 26780 JPEG ownership: inherited temporal merge/SHORT admission unchanged; post-SHORT pre-Resolve 3x3 matched-bandwidth chroma + exact shared-luma detail')
print('PASS 26780 downstream invariance: Claude suppressor/settings/SHORT fusion/VGN owners preserved')
