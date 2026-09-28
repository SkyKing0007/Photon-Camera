#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re,subprocess,tempfile,sys
ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('base'); ap.add_argument('cand'); ap.add_argument('--compiler'); a=ap.parse_args()
pkg=Path(a.root); base=Path(a.base); cand=Path(a.cand)
ks=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
def triple(name):
 m=re.search(r'val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',ks,re.S); assert m,name
 import textwrap; return textwrap.dedent(m.group(1))
def lazy_triple(name):
 m=re.search(r'val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s+by\s+lazy\s*\{\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',ks,re.S); assert m,name
 import textwrap; return textwrap.dedent(m.group(1))
def once(src,old,new,label): assert src.count(old)==1,(label,src.count(old)); return src.replace(old,new,1)
rejection=triple('rejection'); merge=triple('merge'); tmerge=triple('true2xMerge26564'); tflow=triple('true2xFlowRefine26574'); guide=triple('true2xGuideRender26568'); hdetailresolve=lazy_triple('highZoomDetailResolve26718')
# Exact 26720 high-zoom RGB merge runtime transform.
hmerge=once(tmerge,'uniform float uRawClipThreshold;','uniform float uRawClipThreshold;\nuniform float uObservationConfidence;\nuniform int uRowFlickerEnabled;\nuniform int uRowFlickerHarmonic;\nuniform vec2 uRowFlickerAB;\nuniform float uRowFlickerStrength;','hz uniforms')
helper='''float iris26720HighZoomRowReliability(float rowUv) {
    if (uRowFlickerEnabled == 0 || uRowFlickerHarmonic <= 0 || uRowFlickerStrength <= 0.0) return 1.0;
    float phase = 6.283185307179586 * float(uRowFlickerHarmonic) * clamp(rowUv, 0.0, 1.0);
    float logModulation = uRowFlickerAB.x * cos(phase) + uRowFlickerAB.y * sin(phase);
    float amplitude = length(uRowFlickerAB);
    float darkMagnitude = max(-logModulation, 0.0);
    float darkBand = smoothstep(0.010, max(0.030, amplitude * 0.90), darkMagnitude);
    return mix(1.0, 0.08, clamp(darkBand * clamp(uRowFlickerStrength, 0.0, 1.0), 0.0, 1.0));
}

float kernelWeight(vec2 offset, vec3 covariance) {'''
hmerge=once(hmerge,'float kernelWeight(vec2 offset, vec3 covariance) {',helper,'hz helper')
hmerge=once(hmerge,'float frameWeight = sampleRejection(referenceUv);','float frameWeight = sampleRejection(referenceUv);\n    frameWeight *= clamp(uObservationConfidence, 0.05, 1.0);\n    frameWeight *= iris26720HighZoomRowReliability(sampleUv.y);','hz weight')
# Exact 26723 high-zoom flow transform, leaving explicit-SR 26574 untouched.
oldres='''float residualCost(ivec2 centerQ,vec2 currentCenterQ){
    const ivec2 d[5]=ivec2[5](ivec2(0,0),ivec2(1,0),ivec2(-1,0),ivec2(0,1),ivec2(0,-1));
    float cost=0.0;
    for(int i=0;i<5;++i){float r=currentAt(currentCenterQ+vec2(d[i]))-referenceAt(centerQ+d[i]);cost+=r*r;}
    return cost;
}'''
newres='''float residualCost(ivec2 centerQ,vec2 currentCenterQ){
    const ivec2 d[9]=ivec2[9](ivec2(0,0),ivec2(1,0),ivec2(-1,0),ivec2(0,1),ivec2(0,-1),
        ivec2(1,1),ivec2(-1,1),ivec2(1,-1),ivec2(-1,-1));
    const float w[9]=float[9](4.0,2.0,2.0,2.0,2.0,1.0,1.0,1.0,1.0);
    float cost=0.0;
    for(int i=0;i<9;++i){
        float r=currentAt(currentCenterQ+vec2(d[i]))-referenceAt(centerQ+d[i]);
        cost+=w[i]*r*r;
    }
    return cost;
}'''
hflow=once(tflow,oldres,newres,'flow residual')
oldh='''    const ivec2 d[5]=ivec2[5](ivec2(0,0),ivec2(1,0),ivec2(-1,0),ivec2(0,1),ivec2(0,-1));
    float hxx=0.0,hxy=0.0,hyy=0.0,bx=0.0,by=0.0,baseCost=0.0;
    for(int i=0;i<5;++i){
        ivec2 q=centerQ+d[i];
        float ref=referenceAt(q);
        float gx=0.5*(referenceAt(q+ivec2(1,0))-referenceAt(q-ivec2(1,0)));
        float gy=0.5*(referenceAt(q+ivec2(0,1))-referenceAt(q-ivec2(0,1)));
        float residual=currentAt(vec2(q)+quadFlow)-ref;
        hxx+=gx*gx;hxy+=gx*gy;hyy+=gy*gy;bx+=gx*residual;by+=gy*residual;baseCost+=residual*residual;
    }'''
newh='''    const ivec2 d[9]=ivec2[9](ivec2(0,0),ivec2(1,0),ivec2(-1,0),ivec2(0,1),ivec2(0,-1),
        ivec2(1,1),ivec2(-1,1),ivec2(1,-1),ivec2(-1,-1));
    const float w[9]=float[9](4.0,2.0,2.0,2.0,2.0,1.0,1.0,1.0,1.0);
    float hxx=0.0,hxy=0.0,hyy=0.0,bx=0.0,by=0.0,baseCost=0.0;
    for(int i=0;i<9;++i){
        ivec2 q=centerQ+d[i];
        float ref=referenceAt(q);
        float gx=0.5*(referenceAt(q+ivec2(1,0))-referenceAt(q-ivec2(1,0)));
        float gy=0.5*(referenceAt(q+ivec2(0,1))-referenceAt(q-ivec2(0,1)));
        float residual=currentAt(vec2(q)+quadFlow)-ref;
        float wi=w[i];
        hxx+=wi*gx*gx;hxy+=wi*gx*gy;hyy+=wi*gy*gy;
        bx+=wi*gx*residual;by+=wi*gy*residual;baseCost+=wi*residual*residual;
    }'''
hflow=once(hflow,oldh,newh,'flow hessian')
hflow=once(hflow,'bool accept=bounded&&conditioning>0.012&&improvement>0.08&&uniqueness>0.04&&variationRaw<2.0;','bool accept=bounded&&conditioning>0.008&&improvement>0.055&&uniqueness>0.025&&variationRaw<2.0;','flow acceptance')
# Exact 26723 high-zoom protect: only support-gated zero-mean luma residual gets +0..10% gain.
old='float targetY = max(guideY + detailScaleY * directDetail * detailConfidence, 0.0);'
new='''/* IRIS_26723_HIGH_ZOOM_PROVEN_MICROCONTRAST */
            float provenMicrocontrastGain = 1.0 + 0.10 * irisSmooth01((detailConfidence - 0.45) / 0.45);
            float targetY = max(guideY + detailScaleY * directDetail * detailConfidence * provenMicrocontrastGain, 0.0);'''
protect=once(guide,old,new,'microcontrast')
# 26719 scalar fallback merge transform.
outputs='''layout(location = 0) out vec4 oColorAndRWeight;
layout(location = 1) out vec2 oWeightsGb;
layout(location = 2) out vec4 oPhaseOccupancy;
layout(location = 3) out vec4 oTemporalLumaStats;'''
scalar='''layout(location = 0) out vec4 oTemporalLumaStats;
layout(location = 1) out vec4 oPhaseOccupancy;'''
rgb='''    color *= frameWeight;
    weights *= frameWeight;
    oColorAndRWeight = vec4(color, weights.r);
    oWeightsGb = weights.gb;

'''
hdetail=once(tmerge,outputs,scalar,'detail outputs'); hdetail=once(hdetail,rgb,'','detail rgb')
# Color transform gets runtime #version; disabled and highzoom define variants.
color=(cand/'app/src/main/assets/shaders/motionv2/color_transform.glsl').read_text()
def color_variant(enable):
 lines=[]
 for line in color.splitlines():
  if '#define USE_IRIS_26720_HIGH_ZOOM_RGB ' in line:
   line=f'#define USE_IRIS_26720_HIGH_ZOOM_RGB {1 if enable else 0}'
  lines.append(line)
 return '#version 310 es\n\n#line 1\n'+'\n'.join(lines)+'\n'
shaders={
'26723_sabre_rejection.frag':rejection,
'26723_sabre_merge.frag':merge,
'26723_highzoom_rgb_merge.frag':hmerge,
'26723_highzoom_native_chroma_protect.frag':protect,
'26723_highzoom_flow_refine.frag':hflow,
'26723_explicit_sr_flow_refine_inherited.frag':tflow,
'26723_highzoom_scalar_fallback_merge.frag':hdetail,
'26723_highzoom_scalar_fallback_resolve.frag':hdetailresolve,
'26723_color_transform_disabled.frag':color_variant(False),
'26723_color_transform_highzoom_rgb.frag':color_variant(True),
}
# Asset manifests must prove the exact unchanged shader universe against both authority and candidate.
def load_manifest(name):
 d={}
 for line in (pkg/name).read_text().splitlines():
  if line.strip():
   h,r=line.split(None,1); d[r.strip()]=h
 return d
def file_sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
bm=load_manifest('26723_ASSET_SHADER_UNIVERSE_BASE.sha256'); cm=load_manifest('26723_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256')
assert len(bm)==len(cm)==271 and bm==cm
for r,h in bm.items(): assert file_sha(base/r)==h,r
for r,h in cm.items(): assert file_sha(cand/r)==h,r
# Structural / reserved scan on exact runtime-expanded source.
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
for n,src in shaders.items():
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved); impl=sorted(set(x for x in ids if '__' in x or x.startswith('gl_')))
 assert not bad and not impl,(n,bad,impl); assert clean.count('{')==clean.count('}'),n; assert '#import' not in clean,n
inherited_hashes={
 '26723_sabre_rejection.frag':'589d6625fc755eed21ff5445e95166c40921efce9140d7cd5543ea2d3533b677',
 '26723_sabre_merge.frag':'0ef4263b273b56818e4e1e465d8834667091e6f9a720986cdbfd3792d2eaf96a',
 '26723_highzoom_rgb_merge.frag':'cce092976469adcf5f0aad48b79fa8ff7fe20950ab91ceecb12da76148cc5eb7',
 '26723_explicit_sr_flow_refine_inherited.frag':'adf306a01cdfd0a3c777ae2d4f52d2b6efbe95ec6975999a02ea70abed0f10b7',
 '26723_highzoom_scalar_fallback_merge.frag':'684f430c15de912a9801daa78a8110a2383dc1f9420a8a141a4e954d5373135c',
 '26723_highzoom_scalar_fallback_resolve.frag':'8e2ef6eee71b6656cbd2ebc77a0fa3c9314c24bac41f354f1b1479fbd151e883',
 '26723_color_transform_disabled.frag':'484f213313a476783e44bcd1ce84d7af0a4e239586a2d75ac3b70fb6be07d7c3',
 '26723_color_transform_highzoom_rgb.frag':'43e795cb55851670cee04667303575636c21c5688f027fd3c0d790ce53509879',
}
for n,h in inherited_hashes.items(): assert hashlib.sha256(shaders[n].encode()).hexdigest()==h,(n,'inherited runtime-expanded drift')
assert hashlib.sha256(hflow.encode()).hexdigest()=='ad6ec17fd8d68245dbbe80508b9fa0f9eac6bc025539b3a106b395a277d39b32'
assert hashlib.sha256(protect.encode()).hexdigest()=='ae1ccf9c9b5381ea711dfe856363d23e19ebad6b9a1fef04f12d79ceb3b0e9e0'
assert 'directChromaConfidence' not in protect and 'IRIS_26580_TRUE2X_SAME_MATERIAL_CHROMA_OWNERSHIP' in protect and 'IRIS_26723_HIGH_ZOOM_PROVEN_MICROCONTRAST' in protect
assert 'const ivec2 d[9]' in hflow and 'variationRaw<2.0' in hflow
# hashes manifest
manifest=''.join(f'{hashlib.sha256(src.encode()).hexdigest()}  {n}\n' for n,src in sorted(shaders.items()))
expected=pkg/'26723_RUNTIME_EXPANDED_CANDIDATE.sha256'
if expected.exists(): assert expected.read_text()==manifest
else: expected.write_text(manifest)
if a.compiler:
 comp=Path(a.compiler); assert comp.exists()
 with tempfile.TemporaryDirectory(prefix='i26723_glsl_') as td:
  td=Path(td)
  for n,src in shaders.items():
   f=td/n; f.write_text(src)
   cp=subprocess.run([str(comp),'-S','frag',str(f)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
   if cp.returncode: print(cp.stdout); raise SystemExit(f'glslang FAIL {n}')
print(f'PASS 26723 shaders: 271-asset universe unchanged; 26722 native-Sabre/VGN chroma and high-zoom RGB merge preserved; high-zoom-only 3x3 fine-flow proxy + support-gated luma microcontrast; explicit SR flow inherited unchanged; 10 runtime-expanded variants reserved/structure/hash proof; real_compiler={bool(a.compiler)}')
