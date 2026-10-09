#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, sys, textwrap, math, random

if len(sys.argv) != 3: raise SystemExit('usage: validate_26791.py BASE_ROOT CANDIDATE_ROOT')
BASE,CAND=map(Path,sys.argv[1:])
ALLOW={
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties',
}

def need(c,m):
    if not c: raise AssertionError(m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def universe(root):
    return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()}
def shader(root,name, rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'):
    t=(root/rel).read_text()
    m=re.search(r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""',t,re.M)
    need(m, f'{name} declaration')
    b=t.find('""".trimIndent()',m.end()); need(b>=0, f'{name} terminator')
    return textwrap.dedent(t[m.end():b]).strip('\n')+'\n'

b=universe(BASE); c=universe(CAND)
need(len(b)==1779 and len(c)==1779,(len(b),len(c)))
mod={p for p in b.keys()&c.keys() if b[p]!=c[p]}
need(mod==ALLOW, f'changed allowlist mismatch {sorted(mod)}')
need(not(c.keys()-b.keys()) and not(b.keys()-c.keys()), 'added/deleted files')
print('PASS 26791 authority-seeded scope: 1779 files, exactly 4 modified / 0 added / 0 deleted')

v=(CAND/'app/version.properties').read_text()
need('VERSION_NAME=0.9726791' in v and 'VERSION_BUILD=26791' in v,'version')
print('PASS 26791 version 0.9726791 / 26791')

merge=shader(CAND,'merge')
base_merge=shader(BASE,'merge')
need('IRIS_26791_SABRE_SCALAR_CFA_LCA_OWNER' in merge,'scalar owner marker')
need('IRIS_26791_SABRE_SOLE_RGB_OWNER' in merge,'sole RGB owner marker')
need('void correctedCfaScalar26791(' in merge,'scalar helper')
_hs=merge.index('void correctedCfaScalar26791(')
_hf=merge.index('void fillCorrectedCfaNeighborhood26791(', _hs)
helper=merge[_hs:_hf]
need('out float rawValue' in helper and 'out float sourceHeadroomConfidence' in helper,'scalar outputs')
need('out vec3' not in helper and 'vec3 rawValue' not in helper,'scalar helper emits RGB')
need('sampleFixedPhaseDng26790(' not in merge,'old direct phase reconstructor survived')
need('accumulatedColor = vec3(rI, g0I + g1I, bI);' not in merge,'direct four-phase RGB survived')
need(not re.search(r'for \(int channel = 0; channel < 3;',merge),'per-channel topology survived')
need(merge.count('sampleNeighborhoodRbf(')==2, f'expected definition+one active call got {merge.count("sampleNeighborhoodRbf(")}')
need('fillCorrectedCfaNeighborhood26791(' in merge,'scalar neighborhood producer')
need('int phaseIndex = phaseAt26790(nominalSourcePixel);' in helper,'phase from nominal physical CFA missing')
need('correctedSourceCenter' in helper and 'phaseAt26790(corrected' not in helper,'corrected coordinate redefines phase')
need('ivec2 source = q * 2 + offset;' in helper,'same phase lattice source missing')
need('bayerValue[sx][sy] = rawValue;' in merge and 'sourceValidity[sx][sy] = headroom;' in merge,'scalar+validity footprint mismatch')
# Existing Sabre topology/type equations must survive exactly.
for token in [
'int type = (((position.y + bayerOffset.y) & 1) << 1) +',
'vec4 cornerWeights = vec4(',
'vec2 upDownWeights = vec2(weights[1][0], weights[1][2]);',
'vec2 leftRightWeights = vec2(weights[0][1], weights[2][1]);',
'accumulatedIntensities = vec3(',
'intensities.g + intensities.b,',
]: need(token in merge, f'Sabre topology token missing: {token}')
print('PASS 26791 ownership: DNG-derived owner is scalar-only; Sabre remains sole 3x3 CFA->RGB topology')

# No-LCA path within sampleNeighborhoodRbf must keep inherited extracted-Bayer fetch and headroom equation.
need('bayerValue = get3x3FromExtractedBayer(position);' in merge,'no-LCA inherited fetch missing')
need('float headroomStart = max(1.0, uSourceClippingPoint * 0.9925);' in merge,'no-LCA headroom changed')
print('PASS 26791 no-LCA Sabre path preserved')

# LONG block must be byte-identical between successful 26790 and 26791.
def block(txt,start_marker,end_marker):
    a=txt.index(start_marker); b=txt.index(end_marker,a); return txt[a:b]
long_b=block(base_merge,'/* IRIS_26790_LONG_CHROMA_NO_REINTRODUCTION','    float frameWeight')
long_c=block(merge,'/* IRIS_26790_LONG_CHROMA_NO_REINTRODUCTION','    float frameWeight')
need(long_b==long_c,'LONG chroma consensus block changed')
print('PASS 26791 completed-NORMAL LONG chroma guard byte-preserved')

# Protected shaders must remain byte-identical to successful 26790.
protected=[
'jpegNeutralHighlightClamp26790','normalChromaConsensus26790','jpegPhaseSafeCfaLca26788',
'universalNormalMasterShortFusion26651','jpegNeutralHighlightClamp26787','normalDngMerge']
for name in protected: need(shader(BASE,name)==shader(CAND,name), f'protected shader changed {name}')
for name,rel in [
('normalizeBayer','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt'),
('EDGE_FALSE_COLOR_SUPPRESSOR_26778','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'),
('universalAdaptiveColor26561','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'),
('bipolarColorTrust26769','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'),
]: need(shader(BASE,name,rel)==shader(CAND,name,rel), f'protected shader changed {name}')
print('PASS 26791 protected DNG/neutral/SHORT/residual/VGN shader owners byte-identical to successful 26790')

# Host ownership/lifecycle.
stack=(CAND/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
bridge=(CAND/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
need('IRIS_26791_JPEG_CFA_OPTIONS' in stack and 'directFourPhaseRgb=false' in stack and 'singleRbfTopology=true' in stack,'runtime owner log')
need('IRIS_26791_NEUTRAL_ONLY_DNG_ACCUMULATOR_LIFECYCLE' in stack,'neutral-only DNG accumulator lazy link')
need('if (sabreNormalDngMergeProgram == 0)' in stack,'lazy link condition')
need('normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL' in stack,'NORMAL-only DNG accumulator')
need('IRIS_26791_NIGHT_SHARED_PHYSICAL_NEUTRAL_RULE' in bridge,'Night neutral owner')
need('"NIGHT_DEFAULTS_NEUTRAL_26791"' in bridge,'Night source marker')
night=bridge[bridge.index('val dngOptions26786 = if (parameters.irisNightActive)'):bridge.index('if (irisSettings.customNoiseModelEnabled)')]
need(re.search(r'IrisMotionSettings\.DngOptions\.Snapshot\([\s\S]*?\n\s*true,\n\s*"NIGHT_DEFAULTS_NEUTRAL_26791"',night),'Night neutralClamp true')
need('nightBase26791.lcaEnabled' in night and 'nightBase26791.kR' in night and 'nightBase26791.kB' in night,'Night inherits default LCA')
print('PASS 26791 Night: shared fixed-phase LCA defaults + neutral clamp true; no separate Night reconstruction owner')

# Night/Movement host change should not touch exposure/frame/routing keywords outside the local DNG options hunk.
base_bridge=(BASE/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
# Compare everything before and after local changed region using stable anchors.
a='            val dngOptions26786 = if (parameters.irisNightActive) {'
z='            if (irisSettings.customNoiseModelEnabled) {'
need(base_bridge[:base_bridge.index(a)]==bridge[:bridge.index(a)],'Bridge changed before DNG options')
need(base_bridge[base_bridge.index(z):]==bridge[bridge.index(z):],'Bridge changed after DNG options')
print('PASS 26791 Night host delta confined to DNG/LCA/neutral option ownership')

# Synthetic geometry: LCA changes scalar coordinate, never requested phase/topology.
def phase(p): return ((p[1]&1)<<1)+(p[0]&1)
def offset(ph): return (ph&1,(ph>>1)&1)
def corrected(target,flow,k,center):
    return (center[0]+(target[0]-center[0])*(1-k)+flow[0], center[1]+(target[1]-center[1])*(1-k)+flow[1])
random.seed(26791)
for _ in range(500):
    nominal=(random.randint(4,4090),random.randint(4,3066))
    flow=(random.uniform(-3,3),random.uniform(-3,3))
    k=random.choice([0.000144,-0.000072,0.0])
    ph=phase(nominal)
    target=(nominal[0]+0.5-flow[0],nominal[1]+0.5-flow[1])
    src=corrected(target,flow,k,(2048.0,1536.0))
    off=offset(ph)
    lat=((src[0]-(off[0]+0.5))/2.0,(src[1]-(off[1]+0.5))/2.0)
    q=(math.floor(lat[0]),math.floor(lat[1]))
    for dx,dy in [(0,0),(1,0),(0,1),(1,1)]:
        sp=(2*(q[0]+dx)+off[0],2*(q[1]+dy)+off[1])
        need(phase(sp)==ph,'same-phase lattice violated')
print('PASS 26791 synthetic phase-boundary fixture: corrected coordinates cannot change CFA identity')

# Neutral owner is identical to successful 26790 and the physical threshold remains exact.
neut=shader(CAND,'jpegNeutralHighlightClamp26790')
need('gw0 <= 0.000051 && gw1 <= 0.000051' in neut and 'source.rgb = min(source.rgb, vec3(1.0));' in neut,'neutral fixture')
print('PASS 26791 neutral highlight regression: literal two-green DNG support and full neutral-white ceiling preserved')


# Permanent modified-shader uniform completeness regression.
clean_merge=re.sub(r'/\*.*?\*/',' ',merge,flags=re.S)
clean_merge=re.sub(r'//.*',' ',clean_merge)
used=set(re.findall(r'\bu[A-Z][A-Za-z0-9_]*\b',clean_merge))
declared=set(re.findall(r'\buniform\s+(?:(?:highp|mediump|lowp)\s+)?[A-Za-z_]\w*\s+(u[A-Z][A-Za-z0-9_]*)',clean_merge))
need(not (used-declared), f'merge used-but-undeclared uniforms: {sorted(used-declared)}')
print(f'PASS 26791 merge uniform completeness: used={len(used)} declared={len(declared)}')

print('PASS 26791 candidate semantic/ownership validation')
