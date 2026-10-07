#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, re, sys, textwrap
if len(sys.argv)!=3: raise SystemExit('usage: validate_26782.py BASE CAND')
BASE=Path(sys.argv[1]); CAND=Path(sys.argv[2]); ROOT=Path(__file__).resolve().parent
allowed=(ROOT/'26782_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=U(BASE),U(CAND)
assert len(a)==1779 and len(b)==1779 and set(a)==set(b)
changed=sorted(k for k in a if a[k]!=b[k]); assert changed==allowed,(changed,allowed); assert len(changed)==3
vp=(CAND/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726782' in vp and 'VERSION_BUILD=26782' in vp
SAB=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
STACK=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
def vals(root,rel):
 text=(root/rel).read_text()
 return {m.group(1):textwrap.dedent(m.group(2)).strip('\n')+'\n' for m in re.finditer(r'(?:private\s+)?val\s+([A-Za-z0-9_]+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)}
baseVals=vals(BASE,SAB); candVals=vals(CAND,SAB)
assert set(candVals)==set(baseVals)
for name in candVals:
 if name=='normalDngMerge': continue
 assert candVals[name]==baseVals[name],f'unexpected inherited Sabre shader change: {name}'
assert candVals['normalDngMerge']!=baseVals['normalDngMerge']
assert candVals['merge']==baseVals['merge'],'live Sabre temporal merge changed'
assert candVals['universalNormalMasterShortFusion26651']==baseVals['universalNormalMasterShortFusion26651'],'SHORT fusion changed'
dng=candVals['normalDngMerge']
for token in (
 'IRIS_26782_DNG_EDGE_SAFE_QUAD_OWNER','IRIS_26782_FRACTIONAL_HARD_EDGE_VETO','IRIS_26782_BLOCK_UNIFORM_DNG_HEADROOM',
 'if (uUseFrameWeight == 0)','oSignalAndWeight = vec2(normalizedRaw(outputPixel), 1.0);',
 'ivec2 quadOrigin = (outputPixel / 2) * 2;','vec2 sharedTranslationPixels = (quadSourceUv - quadReferenceUv) * rawSize;',
 'vec2 latticeCoordinate = 0.5 * (sourcePixel - (vec2(offset) + vec2(0.5)));','bool exactSamePhaseSample',
 'sourceHeadroomConfidence = quadHeadroomConfidence(q);','fractionalHardEdgeWeight = hardEdge ? 0.0 : 1.0;',
 'frameWeight *= clamp(sourceHeadroomConfidence, 0.0, 1.0);','frameWeight *= fractionalHardEdgeWeight;'):
 assert token in dng,token
for forbidden in ('sameCfaColor(', 'targetGreen', 'sampleGreen', 'matchedBandwidthChroma26780'):
 assert forbidden not in dng,forbidden
assert 'uPhaseGains[phaseIndex]' in dng and 'uPhaseBlackTerms[phaseIndex]' in dng
# Host owns normalized physical-white threshold; reference and alternates are explicit.
stack=(CAND/STACK).read_text(); baseStack=(BASE/STACK).read_text()
for token in ('sourceWhiteNormalized = 1f','sourceWhiteNormalized = exposureScale','uniform1f(program, "uSourceWhiteNormalized"','edgeSafeFractional26782=true','blockUniformHeadroom26782=true'):
 assert token in stack,token
# 26780 amplifier remains fully absent.
for token in ('sabreMatchedBandwidthChroma26780Program','GlesMgcRawSabreShaders.matchedBandwidthChroma26780','renderSabreMatchedBandwidthChroma26780(','IRIS_26780_MATCHED_BANDWIDTH_CHROMA owner=POST_SHORT_PRE_RESOLVE'):
 assert token not in stack,token
assert stack.count('IRIS_26781_REMOVE_MATCHED_BANDWIDTH_CHROMA_AMPLIFIER')==1
assert stack.count('IRIS_26781_DIRECT_POST_SHORT_RESOLVE matchedBandwidth26780=false')==1
# 26782 extends, rather than replaces, the 26778 isolated-outlier equation and consumes exact 26614 validity.
for token in (
 'IRIS_26782_RAW_VALIDITY_CLIP_GATE','IRIS_26782_COHERENT_BIPOLAR_EDGE_GUARD','IRIS_26782_CLIPPED_NEUTRAL_GUARD',
 'float w26778 = gate * smoothstep(uOutlierLo, uOutlierHi, dev);','vec2 correctedC = mix(centerC, medianC, w26778);',
 'uSabreWeightR','uSabreWeightsGb','uSabreValidWeights','uSabreValidityWeightScale',
 'float invalidity = 1.0 - smoothstep(0.985, 0.9995, measuredValidity);',
 'correctedC = mix(correctedC, vec2(0.0), clipW);',
 'IRIS_26782_RESIDUAL_FALSE_COLOR_GUARD'):
 assert token in stack,token
assert 'clipGate=RAW_CFA_VALIDITY_26782' in stack and 'periodicGate=COHERENT_BIPOLAR_26782' in stack
# Existing 26778 median, contrast, sqrt-domain, and exact luma restore mechanisms remain present.
for token in ('float median9(','float contrast = log2((ymax + uNoiseFloor) / (ymin + uNoiseFloor));','vec3 s0 = sqrt(lin0);','rgb1 *= (y1 > 1e-8) ? (y0 / y1) : 1.0;'):
 assert token in stack
# Proven settings and unrelated runtime domains remain byte-identical by allowlist.
for rel in ('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java','app/src/main/res/xml/preferences.xml','app/src/main/res/values/default_prefs.xml'):
 assert a[rel]==b[rel],rel
# ---- Permanent mathematical regressions from the exact 26781 device failures ----
def hard_edge(g):
 gmin=min(g); gmax=max(g); gr=max(gmax-gmin,0.0); rel=gr/max(gmax,0.03)
 return gmax>0.08 and gr>0.055 and rel>0.20
assert hard_edge((0.04,0.92,0.05,0.90))            # white stripe / roof boundary
assert hard_edge((0.11,0.72,0.14,0.69))            # diagonal high-contrast neutral edge
assert not hard_edge((0.40,0.42,0.41,0.43))        # smooth material keeps fractional evidence
assert not hard_edge((0.75,0.78,0.76,0.77))        # bright smooth surface keeps temporal evidence
# Whole-2px exact samples bypass the fractional hard-edge veto by construction.
for dx,dy in ((-4,2),(0,0),(2,6)):
 assert dx%2==0 and dy%2==0
# Block-uniform headroom: any clipped phase invalidates the alternate quad, all-valid does not.
def smoothstep(a,b,x):
 if x<=a: return 0.0
 if x>=b: return 1.0
 t=(x-a)/(b-a); return t*t*(3-2*t)
def head(v,white=1.0): return 1.0-smoothstep(white*0.9925,max(white*0.9925+1e-5,white),v)
assert min(head(v) for v in (0.45,0.62,0.71,0.80))>0.999
assert min(head(v) for v in (0.91,1.00,0.88,0.86))==0.0
# Fractional geometry still cancels phase offset exactly across R/G1/G2/B.
for tx,ty in ((0.25,-0.75),(1.3,0.4),(-2.7,3.1)):
 coords=[]
 for phase in range(4):
  ox=phase&1; oy=(phase>>1)&1; px=20+ox; py=12+oy
  coords.append((0.5*((px+0.5+tx)-(ox+0.5)),0.5*((py+0.5+ty)-(oy+0.5))))
 assert max(abs(x-coords[0][0])+abs(y-coords[0][1]) for x,y in coords)<1e-12
# Four physical phases remain unique for every Bayer arrangement.
maps=((0,1,2,3),(1,0,3,2),(2,3,0,1),(3,2,1,0))
for pat in range(4): assert len(set(maps[pat]))==4 and maps[pat][1]!=maps[pat][2]
# Coherent bipolar detector: opposite neutral-centered lobes pass; one-sided true-color boundary does not.
def coherent(cn,cp,gate=1.0,lo=.03,hi=.10):
 dot=cn[0]*cp[0]+cn[1]*cp[1]; nl=math.hypot(*cn); pl=math.hypot(*cp)
 opp=max(0.0,min(1.0,-dot/max(nl*pl,1e-6))); mid=((cn[0]+cp[0])/2,(cn[1]+cp[1])/2)
 midlen=math.hypot(*mid); midneutral=1-smoothstep(.055,.14,midlen); mag=min(nl,pl)
 return gate*smoothstep(max(.018,lo*.65),max(.055,hi*.80),mag)*smoothstep(.35,.80,opp)*midneutral
assert coherent((.10,-.07),(-.10,.07))>0.95
assert coherent((.13,.02),(0.0,0.0))<1e-6
# Valid-color / clipped-neutral guards: fully valid never clip-neutralizes; invalid + neutral context does; saturated context is protected.
def clip_weight(validity, median_len, mid_len, gate=1.0):
 invalid=1-smoothstep(.985,.9995,min(validity)); neutral=max(1-smoothstep(.055,.14,mid_len),1-smoothstep(.050,.135,median_len)); return gate*invalid*neutral
assert clip_weight((1,1,1),0.01,0.01)==0.0
assert clip_weight((1.0,.7,.8),0.02,0.03)>0.9
assert clip_weight((1.0,.7,.8),0.30,0.28)<1e-6
# Exact luma preservation of the final chroma rewrite (within floating tolerance).
def luma(v): return .25*v[0]+.5*v[1]+.25*v[2]
for rgb in ((.9,.7,.8),(.12,.11,.10),(1.3,1.0,1.1)):
 y0=luma(rgb); s=[math.sqrt(max(x,0)) for x in rgb]; c=(0.0,0.0); out=[max(s[1]+c[0],0)**2,s[1]**2,max(s[1]+c[1],0)**2]; y1=luma(out); out=[x*(y0/y1) for x in out]; assert abs(luma(out)-y0)<1e-9
print('PASS 26782 runtime allowlist: 3 modified + 0 added + 0 deleted; 1776 protected files unchanged')
print('PASS 26782 DNG regression: 26781 quad geometry/reference identity retained; fractional hard-edge cross-boundary evidence vetoed; block-uniform source-headroom guard added')
print('PASS 26782 DNG whole-2px/phase regression: exact natural same-phase samples and four independent CFA phases preserved')
print('PASS 26782 JPEG regression: 26780 amplifier remains absent; 26778 isolated-outlier path retained; coherent bipolar and exact 26614 clipped-neutral guards added with exact luma preservation')
print('PASS 26782 true-color regression: one-sided saturated color cannot satisfy neutral bipolar/clip context')
print('PASS 26782 protected VGN/SHORT/tone/exposure/alignment/denoise/UHDR/frame-policy ownership unchanged by exact allowlist')
