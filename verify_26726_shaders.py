#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re,textwrap,subprocess,tempfile,shutil
ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('base'); ap.add_argument('cand'); ap.add_argument('--compiler'); a=ap.parse_args()
pkg=Path(a.root); base=Path(a.base); cand=Path(a.cand); out=Path(tempfile.mkdtemp(prefix='i26724_expanded_'))
ks=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
def triple(name):
 m=re.search(r'val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',ks,re.S); assert m,name
 return textwrap.dedent(m.group(1))
def lazy_triple(name):
 m=re.search(r'val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s+by\s+lazy\s*\{\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',ks,re.S); assert m,name
 return textwrap.dedent(m.group(1))
def once(src,old,new,label):
 c=src.count(old); assert c==1,(label,c); return src.replace(old,new,1)
rejection=triple('rejection'); merge=triple('merge'); tmerge=triple('true2xMerge26564'); tflow=triple('true2xFlowRefine26574'); guide=triple('true2xGuideRender26568'); hdetailresolve=lazy_triple('highZoomDetailResolve26718')
# inherited 26720 high-zoom RGB merge
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
# inherited 26723 3x3 flow transform
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
hflow=once(tflow,oldres,newres,'flow residual 26723')
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
hflow=once(hflow,oldh,newh,'flow hessian 26723')
hflow=once(hflow,'bool accept=bounded&&conditioning>0.012&&improvement>0.08&&uniqueness>0.04&&variationRaw<2.0;','bool accept=bounded&&conditioning>0.008&&improvement>0.055&&uniqueness>0.025&&variationRaw<2.0;','flow acceptance 26723')
# 26724 noise-aware robust transform, exact runtime expansion
hflow=once(hflow,'uniform vec4 uCurrentPhaseBlackTerms;','uniform vec4 uCurrentPhaseBlackTerms;\nuniform float uNoiseShot;\nuniform float uNoiseRead;','noise uniforms')
hflow=once(hflow,
'''float r=currentAt(currentCenterQ+vec2(d[i]))-referenceAt(centerQ+d[i]);
        cost+=w[i]*r*r;''',
'''float ref=referenceAt(centerQ+d[i]);
        float cur=currentAt(currentCenterQ+vec2(d[i]));
        float r=cur-ref;
        float signal=max(max(ref,cur),0.0);
        float variance=max(uNoiseShot*signal+uNoiseRead,1.0e-8);
        float nr=r*inversesqrt(variance);
        float robust=nr*inversesqrt(1.0+0.25*nr*nr);
        cost+=w[i]*robust*robust;''','noise cost')
hflow=once(hflow,
'''float residual=currentAt(vec2(q)+quadFlow)-ref;
        float wi=w[i];
        hxx+=wi*gx*gx;hxy+=wi*gx*gy;hyy+=wi*gy*gy;
        bx+=wi*gx*residual;by+=wi*gy*residual;baseCost+=wi*residual*residual;''',
'''float cur=currentAt(vec2(q)+quadFlow);
        float residual=cur-ref;
        float signal=max(max(ref,cur),0.0);
        float variance=max(uNoiseShot*signal+uNoiseRead,1.0e-8);
        float invSigma=inversesqrt(variance);
        float nr=residual*invSigma;
        float robustDen=1.0+0.25*nr*nr;
        float robustCostWeight=1.0/robustDen;
        float robustSolveWeight=robustCostWeight*robustCostWeight;
        float wi=w[i]*robustSolveWeight;
        float ngx=gx*invSigma,ngy=gy*invSigma;
        hxx+=wi*ngx*ngx;hxy+=wi*ngx*ngy;hyy+=wi*ngy*ngy;
        bx+=wi*ngx*nr;by+=wi*ngy*nr;
        baseCost+=w[i]*nr*nr*robustCostWeight;''','noise hessian')
# 26723 protect then 26724 adaptation
old='float targetY = max(guideY + detailScaleY * directDetail * detailConfidence, 0.0);'
new='''/* IRIS_26723_HIGH_ZOOM_PROVEN_MICROCONTRAST */
            float provenMicrocontrastGain = 1.0 + 0.10 * irisSmooth01((detailConfidence - 0.45) / 0.45);
            float targetY = max(guideY + detailScaleY * directDetail * detailConfidence * provenMicrocontrastGain, 0.0);'''
protect=once(guide,old,new,'microcontrast 26723')
protect=once(protect,'uniform ivec2 uGuideSize;','uniform ivec2 uGuideSize;\nuniform float uHighZoomSourceZoom;\nuniform float uHighZoomNoiseSigma;','protect uniforms')
protect=once(protect,
'''vec3 guideRgb = irisTopologyGuide(globalP, bilinearGuideRgb, directY, confidence,
        materialBoundary);''',
'''vec3 guideRgb = irisTopologyGuide(globalP, bilinearGuideRgb, directY, confidence,
        materialBoundary);
    /* IRIS_26724_WEAK_DISAGREEING_NATIVE_CHROMA_ADAPTATION */
    vec3 nativeGuideChroma=guideRgb-vec3(guideY);
    float normalizedNativeChroma=length(nativeGuideChroma)/max(guideY,0.060);
    float weakNativeChroma=1.0-irisSmooth01((normalizedNativeChroma-0.080)/0.180);
    float directGuideDisagreement=irisSmooth01((chromaDistance-0.025)/0.090);
    float zoomSeverity=irisSmooth01((uHighZoomSourceZoom-3.0)/8.0);
    float noiseSeverity=irisSmooth01((uHighZoomNoiseSigma-0.010)/0.045);
    float weakFalseColorEvidence=weakNativeChroma*directGuideDisagreement*
        mix(0.35,1.0,max(1.0-temporalGate,noiseSeverity));
    float nativeChromaKeep=1.0-0.32*zoomSeverity*weakFalseColorEvidence;
    guideRgb=vec3(guideY)+nativeGuideChroma*clamp(nativeChromaKeep,0.68,1.0);''','weak native chroma')
protect=once(protect,
'''/* IRIS_26723_HIGH_ZOOM_PROVEN_MICROCONTRAST */
            float provenMicrocontrastGain = 1.0 + 0.10 * irisSmooth01((detailConfidence - 0.45) / 0.45);
            float targetY = max(guideY + detailScaleY * directDetail * detailConfidence * provenMicrocontrastGain, 0.0);''',
'''/* IRIS_26724_HIGH_ZOOM_STRUCTURAL_LUMA_REINFORCEMENT */
    float structuralDetail=irisSmooth01((abs(directDetail)-0.020)/0.120);
    float provenStructure=structuralDetail*irisSmooth01((detailConfidence-0.30)/0.55);
    float zoomDetailGate=irisSmooth01((uHighZoomSourceZoom-3.0)/8.0);
    float provenMicrocontrastGain=1.0+0.18*provenStructure*mix(0.55,1.0,zoomDetailGate);
    float targetY=max(guideY+detailScaleY*directDetail*detailConfidence*provenMicrocontrastGain,0.0);''','structural luma')
# scalar fallback unchanged
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
color=(cand/'app/src/main/assets/shaders/motionv2/color_transform.glsl').read_text()
def color_variant(enable):
 lines=[]
 for line in color.splitlines():
  if '#define USE_IRIS_26720_HIGH_ZOOM_RGB ' in line: line=f'#define USE_IRIS_26720_HIGH_ZOOM_RGB {1 if enable else 0}'
  lines.append(line)
 return '#version 310 es\n\n#line 1\n'+'\n'.join(lines)+'\n'
shaders={
'26724_sabre_rejection.frag':rejection,
'26724_sabre_merge.frag':merge,
'26724_highzoom_rgb_merge.frag':hmerge,
'26724_highzoom_native_chroma_protect.frag':protect,
'26724_highzoom_flow_refine.frag':hflow,
'26724_explicit_sr_flow_refine_inherited.frag':tflow,
'26724_highzoom_scalar_fallback_merge.frag':hdetail,
'26724_highzoom_scalar_fallback_resolve.frag':hdetailresolve,
'26724_color_transform_disabled.frag':color_variant(False),
'26724_color_transform_highzoom_rgb.frag':color_variant(True),
}
# all shader assets unchanged from 26723 authority
bassets={p.relative_to(base).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (base/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
cassets={p.relative_to(cand).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (cand/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
assert len(bassets)==len(cassets)==271 and bassets==cassets
# reserved/structure scan same model as 26723
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
for n,src in shaders.items():
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved); impl=sorted(set(x for x in ids if '__' in x or x.startswith('gl_')))
 assert not bad and not impl,(n,bad,impl); assert clean.count('{')==clean.count('}'),n; assert '#import' not in clean,n
 (out/n).write_text(src)
# inherited hashes from successful 26723 must remain exact for 8 variants
inherited={
'26724_sabre_rejection.frag':'589d6625fc755eed21ff5445e95166c40921efce9140d7cd5543ea2d3533b677',
'26724_sabre_merge.frag':'0ef4263b273b56818e4e1e465d8834667091e6f9a720986cdbfd3792d2eaf96a',
'26724_highzoom_rgb_merge.frag':'cce092976469adcf5f0aad48b79fa8ff7fe20950ab91ceecb12da76148cc5eb7',
'26724_explicit_sr_flow_refine_inherited.frag':'adf306a01cdfd0a3c777ae2d4f52d2b6efbe95ec6975999a02ea70abed0f10b7',
'26724_highzoom_scalar_fallback_merge.frag':'684f430c15de912a9801daa78a8110a2383dc1f9420a8a141a4e954d5373135c',
'26724_highzoom_scalar_fallback_resolve.frag':'8e2ef6eee71b6656cbd2ebc77a0fa3c9314c24bac41f354f1b1479fbd151e883',
'26724_color_transform_disabled.frag':'484f213313a476783e44bcd1ce84d7af0a4e239586a2d75ac3b70fb6be07d7c3',
'26724_color_transform_highzoom_rgb.frag':'43e795cb55851670cee04667303575636c21c5688f027fd3c0d790ce53509879',
}
for n,h in inherited.items(): assert hashlib.sha256(shaders[n].encode()).hexdigest()==h,(n,'inherited drift')
assert 'robustCostWeight=1.0/robustDen' in hflow and 'baseCost+=w[i]*nr*nr*robustCostWeight' in hflow
assert 'directChromaConfidence' not in protect and 'IRIS_26580_TRUE2X_SAME_MATERIAL_CHROMA_OWNERSHIP' in protect
assert 'IRIS_26724_WEAK_DISAGREEING_NATIVE_CHROMA_ADAPTATION' in protect and 'IRIS_26724_HIGH_ZOOM_STRUCTURAL_LUMA_REINFORCEMENT' in protect
manifest=''.join(f'{hashlib.sha256(src.encode()).hexdigest()}  {n}\n' for n,src in sorted(shaders.items()))
expected=pkg/'26726_RUNTIME_EXPANDED_CANDIDATE.sha256'
assert expected.exists() and expected.read_text()==manifest, 'runtime-expanded manifest drift'
if a.compiler:
 comp=Path(a.compiler); assert comp.exists(),comp
 for n,src_text in shaders.items():
  f=out/n
  cp=subprocess.run([str(comp),'-S','frag',str(f)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  if cp.returncode:
   print(cp.stdout); raise SystemExit(f'glslang FAIL {n}')
shutil.rmtree(out,ignore_errors=True)
print(f'PASS 26726 shaders: 271-asset universe unchanged; 10 runtime-expanded variants; 8 inherited hashes exact; 2 modified variants reserved/structure clean; noise-aware robust flow/native-guide chroma/luma-only detail; real_compiler={bool(a.compiler)}')
