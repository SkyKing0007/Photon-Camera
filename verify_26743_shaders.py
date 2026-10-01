#!/usr/bin/env python3
from pathlib import Path
import re,hashlib,sys,tempfile,subprocess,shutil,argparse
ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('base'); ap.add_argument('cand'); ap.add_argument('--compiler'); ap.add_argument('--emit-hashes'); a=ap.parse_args()
pkg=Path(a.root); base=Path(a.base); root=Path(a.cand); out=Path(tempfile.mkdtemp(prefix='i26743_expanded_'))
srel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'); vrel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
def raw_triple(rel,name):
 s=(root/rel).read_text(); m=re.search(r'(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S)
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
 x=trim(raw); assert '$' not in x,(name,'unresolved interpolation'); return x
def once(s,o,n,label):
 assert s.count(o)==1,(label,s.count(o)); return s.replace(o,n,1)
def detail_merge():
 src=runtime(srel,'true2xMerge26564')
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
 src=runtime(srel,'true2xMerge26564')
 src=once(src,'layout(location = 2) out vec4 oPhaseOccupancy;\nlayout(location = 3) out vec4 oTemporalLumaStats;','layout(location = 2) out vec4 oValidWeights;','hz outputs')
 src=once(src,'uniform float uRawClipThreshold;','uniform float uSourceClippingPoint;\nuniform int uReferenceObservation26739;\nuniform int uRowFlickerEnabled;\nuniform int uRowFlickerHarmonic;\nuniform vec2 uRowFlickerAB;\nuniform float uRowFlickerStrength;','hz uniforms')
 src=once(src,'out vec3 accumulatedColor, out vec3 accumulatedWeight,\n               out float sourceRawPeak)','out vec3 accumulatedColor, out vec3 accumulatedWeight,\n               out vec3 validWeight)','hz sig')
 src=once(src,'sourceRawPeak = 0.0;\n    for (int sx = 0; sx < 3; ++sx) {\n        for (int sy = 0; sy < 3; ++sy) sourceRawPeak = max(sourceRawPeak, bayerValue[sx][sy]);\n    }\n    vec4 cornerWeights = vec4(weights[0][0], weights[0][2], weights[2][0], weights[2][2]);','vec4 cornerWeights = vec4(weights[0][0], weights[0][2], weights[2][0], weights[2][2]);','hz peak retire')
 old='''vec4 channelWeight = vec4(
        dot(cornerWeights, vec4(1.0)),
        dot(upDownWeights, vec2(1.0)),
        dot(leftRightWeights, vec2(1.0)),
        weights[1][1]);
    intensity = swizzleForType(intensity, type);
    channelWeight = swizzleForType(channelWeight, type);
    accumulatedColor = vec3(intensity.r, intensity.g + intensity.b, intensity.a);
    accumulatedWeight = vec3(channelWeight.r, channelWeight.g + channelWeight.b, channelWeight.a);'''
 new='''vec4 channelWeight = vec4(
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
            validWeight = vec3(channelValidWeight.r, channelValidWeight.g + channelValidWeight.b, channelValidWeight.a);'''
 src=once(src,old,new,'hz validity')
 src=once(src,'vec3 color;\n    vec3 weights;\n    float sourceRawPeak;\n    sampleRbf(sampleUv * vec2(uRawFullSize), covariance, color, weights, sourceRawPeak);\n    float frameWeight = sampleRejection(referenceUv);','vec3 color;\n            vec3 weights;\n            vec3 validWeights;\n            sampleRbf(sampleUv * vec2(uRawFullSize), covariance, color, weights, validWeights);\n            float frameWeight = sampleRejection(referenceUv);','hz main')
 src=once(src,'float kernelWeight(vec2 offset, vec3 covariance) {','float iris26739ReferenceRowReliability(float rowUv){if(uRowFlickerEnabled==0||uRowFlickerHarmonic<=0||uRowFlickerStrength<=0.0)return 1.0;float phase=6.283185307179586*float(uRowFlickerHarmonic)*clamp(rowUv,0.0,1.0);float logModulation=uRowFlickerAB.x*cos(phase)+uRowFlickerAB.y*sin(phase);float amplitude=length(uRowFlickerAB);float darkMagnitude=max(-logModulation,0.0);float darkBand=smoothstep(0.010,max(0.030,amplitude*0.90),darkMagnitude);return mix(1.0,0.08,clamp(darkBand*clamp(uRowFlickerStrength,0.0,1.0),0.0,1.0));}\n\nfloat kernelWeight(vec2 offset, vec3 covariance) {','hz helper')
 src=once(src,'float frameWeight = sampleRejection(referenceUv);','float frameWeight = sampleRejection(referenceUv);\n    if(uReferenceObservation26739!=0)frameWeight*=iris26739ReferenceRowReliability(sampleUv.y);','hz weight')
 oldtail='''vec3 frameRgb = color / max(weights, vec3(1.0e-7));
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
 newtail='''color *= frameWeight;
    weights *= frameWeight;
    validWeights *= frameWeight;
    oColorAndRWeight = vec4(color, weights.r);
    oWeightsGb = weights.gb;
    /* IRIS_26739_HIGH_ZOOM_PHYSICAL_VALIDITY
     * Reconstruction keeps every normalized RAW observation exactly as Wronski does.
     * The same near-saturation headroom rule as native Sabre contributes only read-only
     * per-channel support provenance to the unchanged 26733 protection. */
    oValidWeights = vec4(validWeights, 0.0);'''
 return once(src,oldtail,newtail,'hz tail')
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 uvec2 uvec3 uvec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def scan(fn,src):
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved); impl=sorted(set(x for x in ids if '__' in x or x.startswith('gl_')))
 assert not bad,(fn,'reserved',bad); assert not impl,(fn,'impl',impl); assert clean.count('{')==clean.count('}'),(fn,'brace mismatch'); assert '#import' not in clean,(fn,'import remains')
specs=[
 ('26743_common_merge.frag',runtime(srel,'merge'),'frag'),
 ('26743_short_fusion.frag',runtime(srel,'universalNormalMasterShortFusion26651'),'frag'),
 ('26743_true2x_merge.frag',runtime(srel,'true2xMerge26564'),'frag'),
 ('26743_highzoom_detail_merge.frag',detail_merge(),'frag'),
 ('26743_highzoom_stability_merge.frag',stability_merge(),'frag'),
 ('26743_highzoom_rgb_merge.frag',highzoom_merge(),'frag'),
 ('26743_universal_adaptive_color.comp',runtime(vrel,'universalAdaptiveColor26561'),'comp'),
]
expanded={}
for fn,shader,stage in specs:
 scan(fn,shader); expanded[fn]=shader; q=out/fn; q.write_text(shader)
 if a.compiler:
  cp=subprocess.run([str(Path(a.compiler)),'-S',stage,str(q)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  if cp.returncode: print(cp.stdout); raise SystemExit(f'glslang FAIL {fn}')
joined='\n'.join(expanded.values())
for forbidden in ['IRIS_26742_SOURCE_VALID_CHROMA_ACCUMULATION','IRIS_26742_TRUE2X_SOURCE_VALID_CHROMA','sourceValidMean26742','chromaAuthority26742','clipStart26742']:
 assert forbidden not in joined,forbidden
hz=expanded['26743_highzoom_rgb_merge.frag']; assert 'IRIS_26739_HIGH_ZOOM_PHYSICAL_VALIDITY' in hz and 'uSourceClippingPoint' in hz and '0.9925' in hz
final=expanded['26743_universal_adaptive_color.comp']
for t in ['IRIS_26743_VISIBLE_HIGHLIGHT_NEUTRALITY_WB_DOMAIN','IRIS_26743_RENDERED_HIGHLIGHT_APPEARANCE_AUTHORITY','IRIS_26743_VISIBLE_FLATTENED_HIGHLIGHT_NEUTRAL_AUTHORITY','visibleHighlightNeutralAuthority26743','smoothstep(0.72, 0.92, visibleCenterLuma26743)','smoothstep(0.58, 0.72, visibleCenterLuma26743)','correctedRgb * uCalculationGains','protectedPreVgnMagnitude *= 1.0 - visibleHighlightNeutralAuthority26743','IRIS_26741_CLIPPED_FLATTENED_HIGHLIGHT_NEUTRAL_AUTHORITY']:
 assert t in final,t
# Asset shader universe remains byte-invariant; modified runtime shaders are Kotlin carriers.
def ah(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
assert len(ah(base))==len(ah(root))==271 and ah(base)==ah(root)
hashes={fn:hashlib.sha256(src.encode()).hexdigest() for fn,src in expanded.items()}
if a.emit_hashes:
 Path(a.emit_hashes).write_text(''.join(f'{hashes[n]}  {n}\n' for n in sorted(hashes)))
else:
 expected={}
 for l in (pkg/'26743_RUNTIME_EXPANDED_CANDIDATE.sha256').read_text().splitlines():
  if l.strip(): h,n=l.split(None,1); expected[n.strip()]=h
 assert expected==hashes,(expected,hashes)
shutil.rmtree(out,ignore_errors=True)
print(f'PASS 26743 shaders: exact 7 affected runtime-expanded variants; 26742 pre-WB chroma synthesis absent; visible highlight neutrality in calculation-WB domain; reserved/structure clean; asset-shader universe 271 invariant; real_compiler={bool(a.compiler)}')
