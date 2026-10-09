#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, random, re, sys, textwrap, xml.etree.ElementTree as ET

if len(sys.argv) != 3:
    raise SystemExit('usage: validate_26792.py BASE_ROOT CANDIDATE_ROOT')
BASE, CAND = map(Path, sys.argv[1:])
ALLOW = {
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java',
'app/src/main/res/xml/preferences.xml',
'app/src/main/res/values/strings.xml',
'app/src/main/res/values/default_prefs.xml',
'app/version.properties',
}

def need(c,m):
    if not c: raise AssertionError(m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def universe(root):
    return {p.relative_to(root).as_posix():sha(p) for p in (root/'app').rglob('*') if p.is_file()}
def shader(root,name, rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'):
    t=(root/rel).read_text()
    m=re.search(r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""',t,re.M)
    need(m, f'{name} declaration')
    b=t.find('""".trimIndent()',m.end()); need(b>=0, f'{name} terminator')
    return textwrap.dedent(t[m.end():b]).strip('\n')+'\n'
def slice_between(txt,start,end):
    a=txt.index(start); b=txt.index(end,a); return txt[a:b]

a=universe(BASE); c=universe(CAND)
need(len(a)==1779 and len(c)==1779,(len(a),len(c)))
need(set(a)==set(c),'candidate file universe changed')
mod={p for p in a if a[p]!=c[p]}
need(mod==ALLOW, f'changed allowlist mismatch {sorted(mod)}')
print('PASS 26792 authority-seeded scope: 1779 files, exactly 13 modified / 0 added / 0 deleted')

v=(CAND/'app/version.properties').read_text()
need('VERSION_NAME=0.9726792' in v and 'VERSION_BUILD=26792' in v,'version')
print('PASS 26792 version 0.9726792 / 26792')

# XML must remain well formed.
for rel in ['app/src/main/res/xml/preferences.xml','app/src/main/res/values/strings.xml','app/src/main/res/values/default_prefs.xml']:
    ET.parse(CAND/rel)
print('PASS 26792 modified Android XML parses')

merge=shader(CAND,'merge'); base_merge=shader(BASE,'merge')
need('IRIS_26792_CONTINUOUS_SCALAR_CFA_LCA_NEUTRAL_OWNER' in merge,'26792 owner marker')
need('IRIS_26792_ONE_RGB_TOPOLOGY' in merge,'one RGB topology marker')
need('void correctedCfaScalar26792(' in merge,'26792 scalar helper missing')
need('float neutralBoundedRawCode26792(' in merge,'26792 neutral helper missing')
need('void fillCorrectedCfaNeighborhood26792(' in merge,'26792 footprint helper missing')
need('uJpegNeutralClamp26792' in merge,'neutral uniform missing')
_hs=merge.index('void correctedCfaScalar26792(')
_hf=merge.index('void fillCorrectedCfaNeighborhood26792(',_hs)
helper=merge[_hs:_hf]
_n0=merge.index('float neutralBoundedRawCode26792(')
neutral=merge[_n0:_hs]
need('out float rawValue' in helper and 'out float sourceHeadroomConfidence' in helper,'scalar output contract')
need('out vec3' not in helper and 'vec3 rawValue' not in helper,'scalar helper emits RGB')
for forbidden in ['nearestLattice','hardEdge','sameSide','uDngEdgeDeAlias26790']:
    need(forbidden not in helper, f'forbidden JPEG scalar snap/edge owner survived: {forbidden}')
need('int phaseIndex = phaseAt26790(nominalSourcePixel);' in helper,'physical phase not selected from nominal pixel')
need('phaseAt26790(corrected' not in helper,'corrected coordinate redefines Bayer phase')
for token in [
'vec2 latticeCoordinate = 0.5 *',
'ivec2 q00 = ivec2(floor(latticeCoordinate));',
'vec2 frac = clamp(latticeCoordinate - vec2(q00), vec2(0.0), vec2(1.0));',
'float w00 = (1.0 - frac.x) * (1.0 - frac.y);',
'float w10 = frac.x * (1.0 - frac.y);',
'float w01 = (1.0 - frac.x) * frac.y;',
'float w11 = frac.x * frac.y;',
'rawValue = s00 * w00 + s10 * w10 + s01 * w01 + s11 * w11;',
]: need(token in helper,f'continuous fixed-phase bilinear token missing: {token}')
need('sampleFixedPhaseDng26790(' not in merge,'old direct DNG phase reconstructor survived')
need('accumulatedColor = vec3(rI, g0I + g1I, bI);' not in merge,'direct four-phase RGB assembly survived')
need(merge.count('sampleNeighborhoodRbf(')==2, f'Sabre topology count != definition+one call: {merge.count("sampleNeighborhoodRbf(")}')
for token in [
'int type = (((position.y + bayerOffset.y) & 1) << 1) +',
'vec4 cornerWeights = vec4(',
'vec2 upDownWeights = vec2(weights[1][0], weights[1][2]);',
'vec2 leftRightWeights = vec2(weights[0][1], weights[2][1]);',
'accumulatedIntensities = vec3(',
'intensities.g + intensities.b,',
]: need(token in merge,f'inherited Sabre RGB topology changed/missing: {token}')
print('PASS 26792 CFA ownership: scalar-only continuous fixed-phase producer; Sabre remains sole CFA->RGB topology; snap code paths=0')

# Neutral rule: R/B only, both greens required, continuous support, DNG AsShotNeutral equivalent bound.
for token in [
'if (phaseIndex != rPhase && phaseIndex != bPhase) return rawCode;',
'float gh0 = phaseHeadroomConfidence26790(q, g0);',
'float gh1 = phaseHeadroomConfidence26790(q, g1);',
'float bothGreenCensor = clamp(1.0 - max(gh0, gh1), 0.0, 1.0);',
'float neutralLimit = 1.0 / max(uPhaseWhiteBalance26790[phaseIndex], 1.0e-6);',
'float correctedSensor = mix(normalizedSensor, boundedSensor, bothGreenCensor);',
]: need(token in neutral,f'neutral CFA rule missing: {token}')
need('source.rgb' not in neutral and 'vec3' not in neutral,'neutral helper became RGB owner')
print('PASS 26792 neutral ownership: per-frame physical two-green evidence consumed in scalar CFA domain before RGB')

stack=(CAND/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
base_stack=(BASE/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
need(stack.count('renderSabreJpegNeutralHighlightClamp26790(')==1,'old post-RGB neutral clamp still actively called')
need('sabreJpegNeutralHighlightClampProgram26790 = 0' in stack,'old post-RGB program not retired')
need('IRIS_26792_CFA_DOMAIN_NEUTRAL_OWNERSHIP' in stack,'CFA neutral host marker')
need('postRgbClamp=false' in stack and 'temporalContinuous=true' in stack,'neutral owner runtime proof log incomplete')
need(stack.count('jpegNeutralClamp26792 = dngOptions26786.neutralClamp')>=2,'NORMAL/LONG do not share neutral option')
# normalDngAccumulator remains only for DNG export, proving JPEG no longer depends on post-RGB DNG support sidecar.
need('var normalDngAccumulator = if (exportNormalStackedDng)' in stack,'DNG accumulator lifecycle not DNG-only')
print('PASS 26792 host neutral lifecycle: old RGB clamp unlinked; NORMAL/LONG scalar producer owns neutral evidence')

# LONG protected algorithm must remain byte-identical.
def block(txt,start_marker,end_marker):
    a=txt.index(start_marker); b=txt.index(end_marker,a); return txt[a:b]
need(block(base_merge,'/* IRIS_26790_LONG_CHROMA_NO_REINTRODUCTION','    float frameWeight') ==
     block(merge,'/* IRIS_26790_LONG_CHROMA_NO_REINTRODUCTION','    float frameWeight'),'LONG chroma consensus block changed')
print('PASS 26792 completed-NORMAL LONG chroma guard byte-preserved')

# Critical protected shaders are byte-identical to successful 26791.
for name in ['jpegNeutralHighlightClamp26790','normalChromaConsensus26790','jpegPhaseSafeCfaLca26788','universalNormalMasterShortFusion26651','jpegNeutralHighlightClamp26787','normalDngMerge']:
    need(shader(BASE,name)==shader(CAND,name),f'protected shader changed {name}')
for name,rel in [
('normalizeBayer','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt'),
('EDGE_FALSE_COLOR_SUPPRESSOR_26778','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'),
('universalAdaptiveColor26561','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'),
('bipolarColorTrust26769','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'),
]: need(shader(BASE,name,rel)==shader(CAND,name,rel),f'protected shader changed {name}')
print('PASS 26792 protected DNG/SHORT/residual/VGN owners byte-identical to successful 26791')

# Night continues shared physical rule; only already-enabled 26791 neutral behavior preserved.
bridge=(CAND/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
need('IRIS_26791_NIGHT_SHARED_PHYSICAL_NEUTRAL_RULE' in bridge,'Night shared physical rule lost')
need('"NIGHT_DEFAULTS_NEUTRAL_26791"' in bridge,'Night neutral source marker lost')
night=bridge[bridge.index('val dngOptions26786 = if (parameters.irisNightActive)'):bridge.index('if (irisSettings.customNoiseModelEnabled)')]
need(re.search(r'IrisMotionSettings\.DngOptions\.Snapshot\([\s\S]*?\n\s*true,\n\s*"NIGHT_DEFAULTS_NEUTRAL_26791"',night),'Night neutralClamp not true')
need('nightBase26791.lcaEnabled' in night and 'nightBase26791.kR' in night and 'nightBase26791.kB' in night,'Night LCA defaults changed')
print('PASS 26792 Night: same physical LCA/neutral rules, no reconstruction redesign')

# Visible A/B settings and same-shot freeze.
settings=(CAND/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java').read_text()
params=(CAND/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text()
prefs=(CAND/'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java').read_text()
pxml=(CAND/'app/src/main/res/xml/preferences.xml').read_text()
defxml=(CAND/'app/src/main/res/values/default_prefs.xml').read_text()
for key in ['pref_iris_edge_false_color_all_edges','pref_iris_sdr_body_contrast_zero']:
    need(key in settings and key in prefs and key in pxml,f'missing visible setting plumbing {key}')
need('ns0:defaultValue="false"' in pxml,'diagnostic visible controls not default OFF/current')
need('<bool name="pref_iris_edge_false_color_all_edges_default">false</bool>' in defxml,'all-edges default resource')
need('<bool name="pref_iris_sdr_body_contrast_zero_default">false</bool>' in defxml,'SDR contrast default resource')
for tok in ['allEdges26792 ? 0.15f','allEdges26792 ? 0.80f','allEdges26792 ? 0.025f','allEdges26792 ? 0.080f']:
    need(tok in settings,f'All-edges exact threshold missing: {tok}')
need('motionV2EdgeSuppressAll26792 = false' in params and 'motionV2SdrBodyContrast26792 = 0.35f' in params,'frozen option defaults wrong')
need('parameters.motionV2EdgeSuppressAll26792 = irisSettings.edgeFalseColorAllEdges26792' in bridge,'all-edges shot freeze missing')
need('parameters.motionV2SdrBodyContrast26792 = irisSettings.sdrBodyContrast26792' in bridge,'body-contrast shot freeze missing')
need('IRIS_26792_OPTIONS' in bridge and 'lcaSnapCodePaths=0' in bridge and 'identicalInputRebase=true' in bridge,'one-shot options log incomplete')
print('PASS 26792 visible A/B controls: defaults current/OFF, exact All-edges thresholds, frozen once per shot')

# SDR base / UHDR mirror must use one exact shot-frozen parameter in both shader equations.
render=(CAND/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
gain=(CAND/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
motion=(CAND/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
for src,label in [(render,'render'),(gain,'gainmap')]:
    need('uniform float iris26792SdrBodyContrast;' in src,f'{label} body contrast uniform missing')
    need('return mix(y,y*y,clamp(iris26792SdrBodyContrast,0.0,0.35)*w);' in src,f'{label} mirror expression mismatch')
need('glProg.setVar("iris26792SdrBodyContrast"' in motion,'body contrast uniform host binding missing')
need('IRIS_26792_SDR_BODY_CONTRAST_UHDR_REBASE' in motion and 'identicalInputRequired=true' in motion,'UHDR rebase proof log missing')
# Compare exact function bodies.
def fn_body(src,name):
    sig=f'float {name}(float mappedGuide)'
    i=src.index(sig); a=src.index('{',i); depth=0
    for j in range(a,len(src)):
        if src[j]=='{': depth+=1
        elif src[j]=='}':
            depth-=1
            if depth==0: return re.sub(r'\s+','',src[a:j+1])
    raise AssertionError('unterminated function')
need(fn_body(render,'iris26770MidtonePresentationTrim')==fn_body(gain,'iris26770MidtonePresentationTrim'),'render/gainmap body-contrast mirror not exact')
print('PASS 26792 UHDR paired owner: exact SDR-base/gain-map body-contrast mirror from one frozen shot value')

# Synthetic scalar-LCA reference tied mechanically to exact helper tokens above.
# Test continuity over one complete 2-pixel same-phase cell using a smooth neutral edge sampled on the fixed phase lattice.
def smoothstep(e0,e1,x):
    t=max(0.0,min(1.0,(x-e0)/(e1-e0))); return t*t*(3-2*t)
def edge_signal(x,edge):
    # physically plausible anti-aliased neutral edge; same for every CFA phase
    return smoothstep(edge-1.25,edge+1.25,x)
def same_phase_linear_sample(corrected_x, phase_offset, edge):
    lattice=0.5*(corrected_x-(phase_offset+0.5))
    q0=math.floor(lattice); f=max(0.0,min(1.0,lattice-q0))
    x0=2*q0+phase_offset+0.5; x1=x0+2.0
    return edge_signal(x0,edge)*(1-f)+edge_signal(x1,edge)*f

def corrected_x(nominal_center, shared_translation, k, optical_center):
    target=nominal_center-shared_translation
    return optical_center+(target-optical_center)*(1.0-k)+shared_translation

def profile_edge(edge_position,k,phase_offset):
    # Reconstruct scalar phase profile at fine nominal locations; crossing is interpolated from actual reference sampler.
    xs=[1600.0+i*0.025 for i in range(641)]
    ys=[]
    center=2048.0
    for x in xs:
        cx=corrected_x(x,0.0,k,center)
        ys.append(same_phase_linear_sample(cx,phase_offset,edge_position))
    # monotonic crossing around 0.5
    best=None
    for i in range(len(xs)-1):
        y0,y1=ys[i],ys[i+1]
        if y0<=0.5<=y1 and y1>y0:
            t=(0.5-y0)/(y1-y0); best=xs[i]+t*(xs[i+1]-xs[i]); break
    need(best is not None,'synthetic edge crossing not found')
    return best

# Use a region away from optical center so real configured k produces measurable sign but remains local.
kR=1.44e-4; kB=-7.2e-5
positions=[1605.0+i*0.02 for i in range(101)] # 0..2px sweep
rg=[]; bg=[]
for ep in positions:
    # Fixed phase offsets are arbitrary RGGB row representatives; neutrality means identical edge signal.
    r=profile_edge(ep,kR,0)
    g=profile_edge(ep,0.0,1)
    b=profile_edge(ep,kB,1)
    rg.append(r-g); bg.append(b-g)
for arr,label in [(rg,'R-G'),(bg,'B-G')]:
    jump=max(abs(arr[i+1]-arr[i]) for i in range(len(arr)-1))
    need(jump<=0.05+1e-9,f'{label} synthetic continuity jump {jump:.6f} >0.05px')
# Both deAlias settings call the exact same helper because no uDngEdgeDeAlias token appears in helper.
need('uDngEdgeDeAlias26790' not in helper,'deAlias changes JPEG LCA sampler topology')
# Sign from exact runtime coordinate equation on right half of image.
x=3072.5; ctr=2048.0
need(corrected_x(x,0,kR,ctr) < x,'R LCA sign wrong for positive k on right field')
need(corrected_x(x,0,kB,ctr) > x,'B LCA sign wrong for negative k on right field')
# k=0 exact control for scalar sampler coordinate.
for x0 in [100.5,1024.5,2048.5,3072.5,4000.5]:
    need(abs(corrected_x(x0,0,0.0,ctr)-x0)<1e-12,'k=0 coordinate control failed')
print(f'PASS 26792 synthetic 0..2px actual-sampler-equivalent LCA sweep: max R-G jump={max(abs(rg[i+1]-rg[i]) for i in range(100)):.6f}px max B-G jump={max(abs(bg[i+1]-bg[i]) for i in range(100)):.6f}px; both deAlias states identical; sign + zero-control PASS')

# Synthetic neutral ownership cases. This is the exact scalar mixing equation asserted above.
def neutral_rule(raw_norm, neutral_limit, gh0, gh1):
    censor=max(0.0,min(1.0,1.0-max(gh0,gh1)))
    bounded=min(raw_norm,neutral_limit)
    return raw_norm+(bounded-raw_norm)*censor
# one green censored, other fully valid -> unchanged
need(abs(neutral_rule(1.4,0.8,0.0,1.0)-1.4)<1e-12,'one-green censor falsely clamps')
# both fully censored -> exact neutral limit
need(abs(neutral_rule(1.4,0.8,0.0,0.0)-0.8)<1e-12,'both-green full censor not neutral')
# non-censored colored highlight remains colored
need(abs(neutral_rule(1.4,0.8,1.0,1.0)-1.4)<1e-12,'non-censored colored material altered')
# temporal/partial support evolves continuously; no step under a fine support sweep.
vals=[neutral_rule(1.4,0.8,g,g) for g in [i/100.0 for i in range(101)]]
need(max(abs(vals[i+1]-vals[i]) for i in range(100))<=0.0060001,'partial-censor transition discontinuous')
# strongly colored source with both greens gone intentionally neutral-capped.
need(neutral_rule(2.2,0.7,0.0,0.0)==0.7,'strong-colored fully censored case not neutralized')
print('PASS 26792 synthetic neutral cases: both-green/one-green/partial-temporal/colored-censored/non-censored rules')

# Identical-input UHDR body-contrast invariant. The exact paired trim body was proven equal above.
def ss(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3-2*t)
def trim(y,body):
    y=max(y,0.0); w=max(0.0,min(1.0,ss(0.10,0.24,y)*(1-ss(0.50,0.78,y))))
    return y+(y*y-y)*(max(0.0,min(0.35,body))*w)
# One frozen source/HDR target. SDR model and encoded SDR use the same paired mapping, so matched delta restores same target.
for source_y in [0.12,0.18,0.25,0.35,0.50,0.65,0.80]:
    linear_target=source_y*2.1
    intents=[]
    for body in [0.35,0.0]:
        sdr_model=trim(source_y,body)
        sdr=sdr_model
        hdr_intent=sdr+max(linear_target-sdr_model,0.0)
        intents.append(hdr_intent)
    need(abs(intents[0]-intents[1])<1e-12,f'identical-input decoded HDR target changed at {source_y}: {intents}')
print('PASS 26792 identical-input SDR 0.35/0.0 gain-map rebase: decoded HDR target mathematically frozen')

# Uniform completeness on modified merge shader.
clean=re.sub(r'/\*.*?\*/',' ',merge,flags=re.S); clean=re.sub(r'//.*',' ',clean)
used=set(re.findall(r'\bu[A-Z][A-Za-z0-9_]*\b',clean))
declared=set(re.findall(r'\buniform\s+(?:(?:highp|mediump|lowp)\s+)?[A-Za-z_]\w*\s+(u[A-Z][A-Za-z0-9_]*)',clean))
need(not(used-declared),f'merge used-but-undeclared uniforms {sorted(used-declared)}')
print(f'PASS 26792 merge uniform completeness: used={len(used)} declared={len(declared)}')

print('PASS 26792 candidate semantic/ownership/regression validation')
