#!/usr/bin/env python3
from pathlib import Path
import re,hashlib,sys,tempfile,subprocess,shutil,argparse
ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('base'); ap.add_argument('cand'); ap.add_argument('--compiler'); a=ap.parse_args()
pkg=Path(a.root); base=Path(a.base); root=Path(a.cand)
out=Path(tempfile.mkdtemp(prefix='i26740_expanded_'))
vrel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
srel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')

def raw_triple(rel,name):
    s=(root/rel).read_text()
    m=re.search(r'(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S)
    if not m: raise AssertionError(f'missing triple {name}')
    return m.group(1)
def trim(v):
    lines=v.replace('\r\n','\n').replace('\r','\n').split('\n')
    if lines and not lines[0].strip(): lines=lines[1:]
    if lines and not lines[-1].strip(): lines=lines[:-1]
    nb=[l for l in lines if l.strip()]; ind=min((len(l)-len(l.lstrip()) for l in nb),default=0)
    return '\n'.join(l[ind:] if l.strip() else '' for l in lines)
def runtime(rel,name):
    raw=raw_triple(rel,name)
    if '$common' in raw: raw=raw.replace('$common',trim(raw_triple(rel,'common')))
    if '$wronskiSensorOutputBody26739' in raw: raw=raw.replace('$wronskiSensorOutputBody26739',trim(raw_triple(srel,'wronskiSensorOutputBody26739')))
    x=trim(raw); assert '$' not in x,(name,'unresolved interpolation'); return x
def once(s,o,n,label):
    assert s.count(o)==1,(label,s.count(o)); return s.replace(o,n,1)
def highzoom_detail_merge():
    src=runtime(srel,'true2xMerge26564')
    outputs='''layout(location = 0) out vec4 oColorAndRWeight;\nlayout(location = 1) out vec2 oWeightsGb;\nlayout(location = 2) out vec4 oPhaseOccupancy;\nlayout(location = 3) out vec4 oTemporalLumaStats;'''
    scalar='''layout(location = 0) out vec4 oTemporalLumaStats;\nlayout(location = 1) out vec4 oPhaseOccupancy;'''
    rgb='''    color *= frameWeight;\n    weights *= frameWeight;\n    oColorAndRWeight = vec4(color, weights.r);\n    oWeightsGb = weights.gb;\n\n'''
    src=once(src,outputs,scalar,'detail-outputs'); src=once(src,rgb,'','detail-rgb-write')
    assert 'oColorAndRWeight' not in src and 'oWeightsGb' not in src
    return src
def highzoom_stability_merge():
    src=highzoom_detail_merge()
    src=once(src,'uniform float uRawClipThreshold;',
        'uniform float uRawClipThreshold;\nuniform int uReferenceObservation26740;\nuniform int uRowFlickerEnabled;\nuniform int uRowFlickerHarmonic;\nuniform vec2 uRowFlickerAB;\nuniform float uRowFlickerStrength;','uniforms')
    src=once(src,'float kernelWeight(vec2 offset, vec3 covariance) {',
        'float iris26740ReferenceRowReliability(float rowUv){if(uRowFlickerEnabled==0||uRowFlickerHarmonic<=0||uRowFlickerStrength<=0.0)return 1.0;float phase=6.283185307179586*float(uRowFlickerHarmonic)*clamp(rowUv,0.0,1.0);float logModulation=uRowFlickerAB.x*cos(phase)+uRowFlickerAB.y*sin(phase);float amplitude=length(uRowFlickerAB);float darkMagnitude=max(-logModulation,0.0);float darkBand=smoothstep(0.010,max(0.030,amplitude*0.90),darkMagnitude);return mix(1.0,0.08,clamp(darkBand*clamp(uRowFlickerStrength,0.0,1.0),0.0,1.0));}\n\nfloat kernelWeight(vec2 offset, vec3 covariance) {','row-helper')
    src=once(src,'float frameWeight = sampleRejection(referenceUv);',
        'float frameWeight = sampleRejection(referenceUv);\n    if(uReferenceObservation26740!=0)frameWeight*=iris26740ReferenceRowReliability(sampleUv.y);','frame-weight')
    return src
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 uvec2 uvec3 uvec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def scan(fn,src):
    clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
    ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
    bad=sorted(set(ids)&reserved); impl=sorted(set(x for x in ids if '__' in x or x.startswith('gl_')))
    assert not bad,(fn,'reserved',bad); assert not impl,(fn,'impl',impl)
    assert clean.count('{')==clean.count('}'),(fn,'brace mismatch'); assert '#import' not in clean,(fn,'import remains')
specs=[
(vrel,'seed','26740_vgn_seed.comp','comp'),
(vrel,'universalAdaptiveColor26561','26740_universal_adaptive_color.comp','comp'),
(None,None,'26740_highzoom_stability_merge.frag','frag'),
(srel,'highZoomRgbStabilize26740','26740_highzoom_rgb_stabilize.frag','frag'),
]
expected={}
for l in (pkg/'26740_RUNTIME_EXPANDED_CANDIDATE.sha256').read_text().splitlines():
    if l.strip(): h,n=l.split(None,1); expected[n.strip()]=h
assert len(expected)==4,len(expected)
for rel,name,fn,stage in specs:
    shader=highzoom_stability_merge() if rel is None else runtime(rel,name)
    scan(fn,shader); hh=hashlib.sha256(shader.encode()).hexdigest(); assert expected.get(fn)==hh,(fn,hh,expected.get(fn))
    q=out/fn; q.write_text(shader)
    if a.compiler:
        cp=subprocess.run([str(Path(a.compiler)),'-S',stage,str(q)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if cp.returncode: print(cp.stdout); raise SystemExit(f'glslang FAIL {fn}')
# Runtime semantics: confidence gate is generic reconstruction evidence, not semantic object/color classification.
stab=(out/'26740_highzoom_rgb_stabilize.frag').read_text()
for t in ['uPhaseOccupancy','uTemporalLumaStats','uNativeVgnGuide','phaseGate','temporalGate','agreementGate','shapeTrust','directAuthority','highlightFallback']:
    assert t in stab,('stabilizer',t)
for forbidden in ['barcode','font','textDetector','semanticClass']:
    assert forbidden not in stab,('semantic special case',forbidden)
ev=(out/'26740_highzoom_stability_merge.frag').read_text()
for t in ['oTemporalLumaStats','oPhaseOccupancy','uReferenceObservation26740','iris26740ReferenceRowReliability']:
    assert t in ev,('stability evidence',t)
seed=(out/'26740_vgn_seed.comp').read_text(); final=(out/'26740_universal_adaptive_color.comp').read_text()
assert 'IRIS_26740_BRIGHT_COLOR_REQUIRES_INDEPENDENT_PHYSICAL_CONTINUATION' in seed
assert 'physicalColorContinuation26735' in seed
assert 'IRIS_26740_HEADROOM_OVERRIDE_REQUIRES_PHYSICAL_REAL_COLOR' in final
assert 'physicalRealColorVeto26735' in final
# Asset shader universe remains byte invariant; modified runtime shaders are Kotlin carriers.
def ah(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
assert len(ah(base))==len(ah(root))==271 and ah(base)==ah(root)
shutil.rmtree(out,ignore_errors=True)
print(f'PASS 26740 shaders: exact 4 changed/new runtime-expanded variants; reserved/structure clean; asset-shader universe 271 invariant; real_compiler={bool(a.compiler)}')
