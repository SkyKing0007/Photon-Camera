#!/usr/bin/env python3
from pathlib import Path
import re,hashlib,sys,tempfile,subprocess,shutil,argparse
ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('base'); ap.add_argument('cand'); ap.add_argument('--compiler'); ap.add_argument('--emit-hashes'); a=ap.parse_args()
pkg=Path(a.root); base=Path(a.base); root=Path(a.cand); out=Path(tempfile.mkdtemp(prefix='i26742_expanded_'))
srel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
def raw_triple(name):
 s=(root/srel).read_text(); m=re.search(r'(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S)
 if not m: raise AssertionError(f'missing triple {name}')
 return m.group(1)
def trim(v):
 lines=v.replace('\r\n','\n').replace('\r','\n').split('\n')
 if lines and not lines[0].strip(): lines=lines[1:]
 if lines and not lines[-1].strip(): lines=lines[:-1]
 nb=[l for l in lines if l.strip()]; ind=min((len(l)-len(l.lstrip()) for l in nb),default=0)
 return '\n'.join(l[ind:] if l.strip() else '' for l in lines)
def runtime(name):
 x=trim(raw_triple(name)); assert '$' not in x,(name,'unresolved interpolation'); return x
def once(s,o,n,label):
 assert s.count(o)==1,(label,s.count(o)); return s.replace(o,n,1)
def detail_merge():
 src=runtime('true2xMerge26564')
 outputs=trim('''
            layout(location = 0) out vec4 oColorAndRWeight;
            layout(location = 1) out vec2 oWeightsGb;
            layout(location = 2) out vec4 oPhaseOccupancy;
            layout(location = 3) out vec4 oTemporalLumaStats;
        ''')
 scalar=trim('''
            layout(location = 0) out vec4 oTemporalLumaStats;
            layout(location = 1) out vec4 oPhaseOccupancy;
        ''')
 rgb='    color *= frameWeight;\n    weights *= frameWeight;\n    oColorAndRWeight = vec4(color, weights.r);\n    oWeightsGb = weights.gb;\n\n'
 src=once(src,outputs,scalar,'detail outputs'); src=once(src,rgb,'','detail rgb'); return src
def stability_merge():
 src=detail_merge()
 src=once(src,'uniform float uRawClipThreshold;','uniform float uRawClipThreshold;\nuniform int uReferenceObservation26740;\nuniform int uRowFlickerEnabled;\nuniform int uRowFlickerHarmonic;\nuniform vec2 uRowFlickerAB;\nuniform float uRowFlickerStrength;','stability uniforms')
 src=once(src,'float kernelWeight(vec2 offset, vec3 covariance) {','float iris26740ReferenceRowReliability(float rowUv){if(uRowFlickerEnabled==0||uRowFlickerHarmonic<=0||uRowFlickerStrength<=0.0)return 1.0;float phase=6.283185307179586*float(uRowFlickerHarmonic)*clamp(rowUv,0.0,1.0);float logModulation=uRowFlickerAB.x*cos(phase)+uRowFlickerAB.y*sin(phase);float amplitude=length(uRowFlickerAB);float darkMagnitude=max(-logModulation,0.0);float darkBand=smoothstep(0.010,max(0.030,amplitude*0.90),darkMagnitude);return mix(1.0,0.08,clamp(darkBand*clamp(uRowFlickerStrength,0.0,1.0),0.0,1.0));}\n\nfloat kernelWeight(vec2 offset, vec3 covariance) {','stability helper')
 return once(src,'float frameWeight = sampleRejection(referenceUv);','float frameWeight = sampleRejection(referenceUv);\n    if(uReferenceObservation26740!=0)frameWeight*=iris26740ReferenceRowReliability(sampleUv.y);','stability weight')
def highzoom_merge():
 src=runtime('true2xMerge26564')
 src=once(src,'layout(location = 2) out vec4 oPhaseOccupancy;\nlayout(location = 3) out vec4 oTemporalLumaStats;','layout(location = 2) out vec4 oValidWeights;','hz outputs')
 src=once(src,'uniform float uRawClipThreshold;','uniform float uRawClipThreshold;\nuniform int uReferenceObservation26739;\nuniform int uRowFlickerEnabled;\nuniform int uRowFlickerHarmonic;\nuniform vec2 uRowFlickerAB;\nuniform float uRowFlickerStrength;','hz uniforms')
 src=once(src,'float kernelWeight(vec2 offset, vec3 covariance) {','float iris26739ReferenceRowReliability(float rowUv){if(uRowFlickerEnabled==0||uRowFlickerHarmonic<=0||uRowFlickerStrength<=0.0)return 1.0;float phase=6.283185307179586*float(uRowFlickerHarmonic)*clamp(rowUv,0.0,1.0);float logModulation=uRowFlickerAB.x*cos(phase)+uRowFlickerAB.y*sin(phase);float amplitude=length(uRowFlickerAB);float darkMagnitude=max(-logModulation,0.0);float darkBand=smoothstep(0.010,max(0.030,amplitude*0.90),darkMagnitude);return mix(1.0,0.08,clamp(darkBand*clamp(uRowFlickerStrength,0.0,1.0),0.0,1.0));}\n\nfloat kernelWeight(vec2 offset, vec3 covariance) {','hz helper')
 src=once(src,'float frameWeight = sampleRejection(referenceUv);','float frameWeight = sampleRejection(referenceUv);\n    if(uReferenceObservation26739!=0)frameWeight*=iris26739ReferenceRowReliability(sampleUv.y);','hz weight')
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
    validWeights26742 *= frameWeight;
    oColorAndRWeight = vec4(color, weights.r);
    oWeightsGb = weights.gb;
    /* IRIS_26742_HIGH_ZOOM_SOURCE_VALIDITY
     * This is the same source validity that already gated chroma before RGB formation. */
    oValidWeights = vec4(validWeights26742, 0.0);'''
 return once(src,old,new,'hz tail')
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 uvec2 uvec3 uvec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def scan(fn,src):
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved); impl=sorted(set(x for x in ids if '__' in x or x.startswith('gl_')))
 assert not bad,(fn,'reserved',bad); assert not impl,(fn,'impl',impl); assert clean.count('{')==clean.count('}'),(fn,'brace mismatch'); assert '#import' not in clean,(fn,'import remains')
specs=[
 ('26742_common_merge.frag',runtime('merge')),
 ('26742_short_fusion.frag',runtime('universalNormalMasterShortFusion26651')),
 ('26742_true2x_merge.frag',runtime('true2xMerge26564')),
 ('26742_highzoom_detail_merge.frag',detail_merge()),
 ('26742_highzoom_stability_merge.frag',stability_merge()),
 ('26742_highzoom_rgb_merge.frag',highzoom_merge()),
]
expanded={}
for fn,shader in specs:
 scan(fn,shader); expanded[fn]=shader; q=out/fn; q.write_text(shader)
 if a.compiler:
  cp=subprocess.run([str(Path(a.compiler)),'-S','frag',str(q)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  if cp.returncode: print(cp.stdout); raise SystemExit(f'glslang FAIL {fn}')
# Candidate semantic markers in exact runtime-expanded shaders.
for t in ['IRIS_26742_SOURCE_VALID_CHROMA_ACCUMULATION','IRIS_26742_SOURCE_HEADROOM_MARGIN','sourceValidMean26742','validIntensities26742']:
 assert t in expanded['26742_common_merge.frag'],t
for t in ['IRIS_26742_SHORT_SOURCE_HEADROOM_MARGIN','IRIS_26648_SAMPLE_LEVEL_SHORT_VALIDITY']:
 assert t in expanded['26742_short_fusion.frag'],t
for t in ['IRIS_26742_TRUE2X_SOURCE_VALID_CHROMA','sourceValidity26742','validAccumulatedWeight26742']:
 assert t in expanded['26742_true2x_merge.frag'],t
for t in ['IRIS_26742_HIGH_ZOOM_SOURCE_VALIDITY','oValidWeights','validWeights26742']:
 assert t in expanded['26742_highzoom_rgb_merge.frag'],t
assert 'oColorAndRWeight' not in expanded['26742_highzoom_detail_merge.frag']
assert 'oWeightsGb' not in expanded['26742_highzoom_detail_merge.frag']
# Asset shader universe must remain byte-invariant; all changes live in runtime Kotlin carriers.
def ah(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
assert len(ah(base))==len(ah(root))==271 and ah(base)==ah(root)
hashes={fn:hashlib.sha256(src.encode()).hexdigest() for fn,src in expanded.items()}
if a.emit_hashes:
 Path(a.emit_hashes).write_text(''.join(f'{hashes[n]}  {n}\n' for n in sorted(hashes)))
else:
 expected={}
 for l in (pkg/'26742_RUNTIME_EXPANDED_CANDIDATE.sha256').read_text().splitlines():
  if l.strip(): h,n=l.split(None,1); expected[n.strip()]=h
 assert expected==hashes,(expected,hashes)
shutil.rmtree(out,ignore_errors=True)
print(f'PASS 26742 shaders: exact 6 affected runtime-expanded variants; lazy derivations exact; reserved/structure clean; asset-shader universe 271 invariant; real_compiler={bool(a.compiler)}')
