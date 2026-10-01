#!/usr/bin/env python3
from pathlib import Path
import re, hashlib, json, sys
ap=__import__('argparse').ArgumentParser(); ap.add_argument('root'); ap.add_argument('base'); ap.add_argument('cand'); ap.add_argument('--compiler'); a=ap.parse_args()
pkg=Path(a.root); base=Path(a.base); root=Path(a.cand); import tempfile,subprocess,shutil
out=Path(tempfile.mkdtemp(prefix='i26739_expanded_'))
vrel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
srel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')

def raw_triple(rel,name):
    s=(root/rel).read_text()
    # Handles ordinary String triple literals only; transformed lazy shader handled separately.
    m=re.search(r'(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S)
    if not m: raise AssertionError(f'missing triple {name}')
    return m.group(1)
def trim(v):
    lines=v.replace('\r\n','\n').replace('\r','\n').split('\n')
    if lines and not lines[0].strip(): lines=lines[1:]
    if lines and not lines[-1].strip(): lines=lines[:-1]
    nb=[l for l in lines if l.strip()]
    ind=min((len(l)-len(l.lstrip()) for l in nb),default=0)
    return '\n'.join(l[ind:] if l.strip() else '' for l in lines)
def runtime(rel,name):
    raw=raw_triple(rel,name)
    # Exact Kotlin interpolation used by these changed shaders.
    if '$common' in raw: raw=raw.replace('$common',trim(raw_triple(rel,'common')))
    if '$wronskiSensorOutputBody26739' in raw:
        raw=raw.replace('$wronskiSensorOutputBody26739',trim(raw_triple(srel,'wronskiSensorOutputBody26739')))
    x=trim(raw)
    assert '$' not in x, (name,'unresolved interpolation')
    return x

def once(s,o,n,label):
    assert s.count(o)==1,(label,s.count(o)); return s.replace(o,n,1)

def highzoom_merge():
    src=runtime(srel,'true2xMerge26564')
    src=once(src,
        'layout(location = 2) out vec4 oPhaseOccupancy;\nlayout(location = 3) out vec4 oTemporalLumaStats;',
        'layout(location = 2) out vec4 oValidWeights;','validity-output')
    src=once(src,'uniform float uRawClipThreshold;',
        'uniform float uSourceClippingPoint;\nuniform int uReferenceObservation26739;\nuniform int uRowFlickerEnabled;\nuniform int uRowFlickerHarmonic;\nuniform vec2 uRowFlickerAB;\nuniform float uRowFlickerStrength;','uniforms')
    src=once(src,
        'out vec3 accumulatedColor, out vec3 accumulatedWeight,\n               out float sourceRawPeak)',
        'out vec3 accumulatedColor, out vec3 accumulatedWeight,\n               out vec3 validWeight)','sample-signature')
    src=once(src,
        'sourceRawPeak = 0.0;\n    for (int sx = 0; sx < 3; ++sx) {\n        for (int sy = 0; sy < 3; ++sy) sourceRawPeak = max(sourceRawPeak, bayerValue[sx][sy]);\n    }\n    vec4 cornerWeights = vec4(weights[0][0], weights[0][2], weights[2][0], weights[2][2]);',
        'vec4 cornerWeights = vec4(weights[0][0], weights[0][2], weights[2][0], weights[2][2]);','source-peak-retire')
    src=once(src,
'''vec4 channelWeight = vec4(
        dot(cornerWeights, vec4(1.0)),
        dot(upDownWeights, vec2(1.0)),
        dot(leftRightWeights, vec2(1.0)),
        weights[1][1]);
    intensity = swizzleForType(intensity, type);
    channelWeight = swizzleForType(channelWeight, type);
    accumulatedColor = vec3(intensity.r, intensity.g + intensity.b, intensity.a);
    accumulatedWeight = vec3(channelWeight.r, channelWeight.g + channelWeight.b, channelWeight.a);''',
'''vec4 channelWeight = vec4(
                dot(cornerWeights, vec4(1.0)),
                dot(upDownWeights, vec2(1.0)),
                dot(leftRightWeights, vec2(1.0)),
                weights[1][1]);
            float headroomStart26739=max(1.0,uSourceClippingPoint*0.9925);
            vec4 cornerValidity26739=vec4(1.0)-smoothstep(vec4(headroomStart26739),vec4(max(headroomStart26739+1.0e-4,uSourceClippingPoint)),cornerValues);
            vec2 upDownValidity26739=vec2(1.0)-smoothstep(vec2(headroomStart26739),vec2(max(headroomStart26739+1.0e-4,uSourceClippingPoint)),upDownValues);
            vec2 leftRightValidity26739=vec2(1.0)-smoothstep(vec2(headroomStart26739),vec2(max(headroomStart26739+1.0e-4,uSourceClippingPoint)),leftRightValues);
            float centerValidity26739=1.0-smoothstep(headroomStart26739,max(headroomStart26739+1.0e-4,uSourceClippingPoint),bayerValue[1][1]);
            vec4 channelValidWeight = vec4(
                dot(cornerWeights*cornerValidity26739, vec4(1.0)),
                dot(upDownWeights*upDownValidity26739, vec2(1.0)),
                dot(leftRightWeights*leftRightValidity26739, vec2(1.0)),
                weights[1][1]*centerValidity26739);
            intensity = swizzleForType(intensity, type);
            channelWeight = swizzleForType(channelWeight, type);
            channelValidWeight = swizzleForType(channelValidWeight, type);
            accumulatedColor = vec3(intensity.r, intensity.g + intensity.b, intensity.a);
            accumulatedWeight = vec3(channelWeight.r, channelWeight.g + channelWeight.b, channelWeight.a);
            validWeight = vec3(channelValidWeight.r, channelValidWeight.g + channelValidWeight.b, channelValidWeight.a);''','channel-validity')
    src=once(src,
'''vec3 color;
    vec3 weights;
    float sourceRawPeak;
    sampleRbf(sampleUv * vec2(uRawFullSize), covariance, color, weights, sourceRawPeak);
    float frameWeight = sampleRejection(referenceUv);''',
'''vec3 color;
            vec3 weights;
            vec3 validWeights;
            sampleRbf(sampleUv * vec2(uRawFullSize), covariance, color, weights, validWeights);
            float frameWeight = sampleRejection(referenceUv);''','main-validity')
    src=once(src,'float kernelWeight(vec2 offset, vec3 covariance) {',
        'float iris26739ReferenceRowReliability(float rowUv){if(uRowFlickerEnabled==0||uRowFlickerHarmonic<=0||uRowFlickerStrength<=0.0)return 1.0;float phase=6.283185307179586*float(uRowFlickerHarmonic)*clamp(rowUv,0.0,1.0);float logModulation=uRowFlickerAB.x*cos(phase)+uRowFlickerAB.y*sin(phase);float amplitude=length(uRowFlickerAB);float darkMagnitude=max(-logModulation,0.0);float darkBand=smoothstep(0.010,max(0.030,amplitude*0.90),darkMagnitude);return mix(1.0,0.08,clamp(darkBand*clamp(uRowFlickerStrength,0.0,1.0),0.0,1.0));}\n\nfloat kernelWeight(vec2 offset, vec3 covariance) {','row-helper')
    src=once(src,'float frameWeight = sampleRejection(referenceUv);',
        'float frameWeight = sampleRejection(referenceUv);\n    if(uReferenceObservation26739!=0)frameWeight*=iris26739ReferenceRowReliability(sampleUv.y);','frame-weight')
    old='''vec3 frameRgb = color / max(weights, vec3(1.0e-7));
    float frameY = clamp(0.25 * frameRgb.r + 0.50 * frameRgb.g + 0.25 * frameRgb.b, 0.0, 4.0);
    float temporalWeight = (frameWeight > 0.08 && sourceRawPeak < uRawClipThreshold) ? frameWeight : 0.0;
    /* IRIS_26573_CROSS_FRAME_LUMA_MOMENTS
     * Weighted first/second luminance moments plus sum(w),sum(w^2).  These are accumulated
     * across independently aligned RAW observations and are used only to prove that a
     * candidate 2x sample is temporally repeatable; they never become an RGB/chroma owner.
     */
    oTemporalLumaStats = vec4(
        frameY * temporalWeight,
        frameY * frameY * temporalWeight,
        temporalWeight,
        temporalWeight * temporalWeight);
    color *= frameWeight;
    weights *= frameWeight;
    oColorAndRWeight = vec4(color, weights.r);
    oWeightsGb = weights.gb;

    oPhaseOccupancy = vec4(0.0);
    if (temporalWeight > 0.0) {
        vec2 flowPixels = flow.xy * vec2(uRawFullSize);
        vec2 phase = fract(flowPixels);
        int bin = (phase.x >= 0.5 ? 1 : 0) + (phase.y >= 0.5 ? 2 : 0);
        if (bin == 0) oPhaseOccupancy.r = 1.0;
        else if (bin == 1) oPhaseOccupancy.g = 1.0;
        else if (bin == 2) oPhaseOccupancy.b = 1.0;
        else oPhaseOccupancy.a = 1.0;
    }'''
    new='''color *= frameWeight;
    weights *= frameWeight;
    validWeights *= frameWeight;
    oColorAndRWeight = vec4(color, weights.r);
    oWeightsGb = weights.gb;
    /* IRIS_26739_HIGH_ZOOM_PHYSICAL_VALIDITY
     * Reconstruction keeps every normalized RAW observation exactly as Wronski does.
     * The same near-saturation headroom rule as native Sabre contributes only read-only
     * per-channel support provenance to the unchanged 26733 protection. */
    oValidWeights = vec4(validWeights, 0.0);'''
    return once(src,old,new,'tail-validity')

specs=[
(vrel,'seed','26739_vgn_seed.comp','comp'),
(vrel,'universalAdaptiveColor26561','26739_universal_adaptive_color.comp','comp'),
(srel,'universalNormalMasterShortFusion26651','26739_normal_short_fusion.frag','frag'),
(None,None,'26739_highzoom_wronski_merge.frag','frag'),
(srel,'wronskiSensorOutputUint16_26739','26739_sensor_rgb_uint16.frag','frag'),
(srel,'wronskiSensorOutputHdrDirectionUint16_26739','26739_sensor_rgb_hdr_direction.frag','frag'),
(srel,'wronskiSensorOutputFloat_26739','26739_sensor_rgb_float.frag','frag'),
]
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 uvec2 uvec3 uvec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def scan(fn,src):
    clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
    ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
    bad=sorted(set(ids)&reserved); impl=sorted(set(x for x in ids if '__' in x or x.startswith('gl_')))
    assert not bad,(fn,'reserved',bad); assert not impl,(fn,'impl',impl)
    assert clean.count('{')==clean.count('}'),(fn,'brace mismatch')
    assert '#import' not in clean,(fn,'import remains')
manifest=[]
expected={}
for l in (pkg/'26739_RUNTIME_EXPANDED_CANDIDATE.sha256').read_text().splitlines():
    if l.strip(): h,n=l.split(None,1); expected[n.strip()]=h
assert len(expected)==7, len(expected)
for rel,name,fn,stage in specs:
    shader=highzoom_merge() if rel is None else runtime(rel,name)
    scan(fn,shader)
    hh=hashlib.sha256(shader.encode()).hexdigest(); assert expected.get(fn)==hh,(fn,hh,expected.get(fn))
    q=out/fn; q.write_text(shader)
    if a.compiler:
        cp=subprocess.run([str(Path(a.compiler)),'-S',stage,str(q)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if cp.returncode: print(cp.stdout); raise SystemExit(f'glslang FAIL {fn}')
    manifest.append((hh,fn,stage,len(shader.splitlines())))
# Asset shader universe remains byte invariant; runtime-expanded shaders are Kotlin carriers.
def ah(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
assert len(ah(base))==len(ah(root))==271 and ah(base)==ah(root)
# Candidate-specific semantic anchors in the exact compiled text.
checks={
'26739_highzoom_wronski_merge.frag':['uReferenceObservation26739','oValidWeights','IRIS_26739_HIGH_ZOOM_PHYSICAL_VALIDITY'],
'26739_sensor_rgb_uint16.frag':['wronskiCameraRgb26739'],
'26739_sensor_rgb_float.frag':['IRIS_26739_PHYSICAL_CALCULATION_RGB'],
'26739_universal_adaptive_color.comp':['IRIS_26739_NO_POST_HOC_CFA_MOIRE_OWNER'],
'26739_normal_short_fusion.frag':['IRIS_26739_SHORT_DECISION_DOMAIN'],
}
for fn,toks in checks.items():
    ss=(out/fn).read_text()
    for t in toks: assert t in ss,(fn,t)
sh=(out/'26739_highzoom_wronski_merge.frag').read_text(); assert 'uObservationConfidence' not in sh and 'oPhaseOccupancy' not in sh and 'oTemporalLumaStats' not in sh
shutil.rmtree(out,ignore_errors=True)
print(f'PASS 26739 shaders: exact 7 changed/new runtime-expanded variants; reserved/structure clean; asset-shader universe 271 invariant; real_compiler={bool(a.compiler)}')
