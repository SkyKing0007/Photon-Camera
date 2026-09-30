#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re,subprocess,tempfile,shutil
ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('base'); ap.add_argument('cand'); ap.add_argument('--compiler'); ap.add_argument('--base-only',action='store_true'); a=ap.parse_args()
pkg=Path(a.root); base=Path(a.base); cand=Path(a.cand); out=Path(tempfile.mkdtemp(prefix='i26738_expanded_'))
vrel='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'; srel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
def raw_triple(root,rel,name):
 s=(root/rel).read_text(); m=re.search(r'(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S); assert m,name; return m.group(1)
def trim(v):
 lines=v.replace('\r\n','\n').replace('\r','\n').split('\n')
 if lines and not lines[0].strip(): lines=lines[1:]
 if lines and not lines[-1].strip(): lines=lines[:-1]
 nb=[l for l in lines if l.strip()]; ind=min((len(l)-len(l.lstrip()) for l in nb),default=0)
 return '\n'.join(l[ind:] if l.strip() else '' for l in lines)
def runtime(root,rel,name):
 raw=raw_triple(root,rel,name)
 if '$common' in raw: raw=raw.replace('$common',trim(raw_triple(root,rel,'common')))
 x=trim(raw); assert '$' not in x,(name,'unresolved'); return x
def once(s,o,n,label): assert s.count(o)==1,(label,s.count(o)); return s.replace(o,n,1)
def hmerge(root):
 ks=(root/srel).read_text(); src=runtime(root,srel,'true2xMerge26564')
 is38='IRIS_26738_CONTINUOUS_RAW_OBSERVATION_ROBUSTNESS' in ks; is37='IRIS_26737_PHOTOMETRICALLY_TRUSTED_FLOW_OWNS_SUPERRES_PHASE' in ks; assert is38 or is37
 uniforms='uniform float uRawClipThreshold;\nuniform float uObservationConfidence;\nuniform int uReferenceObservation26737;\nuniform int uRowFlickerEnabled;\nuniform int uRowFlickerHarmonic;\nuniform vec2 uRowFlickerAB;\nuniform float uRowFlickerStrength;'
 src=once(src,'uniform float uRawClipThreshold;',uniforms,'uniforms')
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
 src=once(src,'float kernelWeight(vec2 offset, vec3 covariance) {',helper,'helper')
 if is38:
  frame='''float frameWeight = sampleRejection(referenceUv);
    /* IRIS_26738_CONTINUOUS_RAW_OBSERVATION_ROBUSTNESS
     * Flow phase certainty is confidence, not a hard admission switch.  Sabre
     * photometric rejection/covariance plus continuous RAW flow confidence remain the normalized-convolution owners;
     * an aperture-limited observation is downweighted but cannot disappear solely
     * because a discrete phase label was uncertain. */
    float phaseTrust26738 = uReferenceObservation26737 != 0 ? 1.0 : clamp(flow.a, 0.0, 1.0);
    float continuousFlowTrust26738 = uReferenceObservation26737 != 0 ? 1.0 : phaseTrust26738;
    frameWeight *= clamp(uObservationConfidence, 0.05, 1.0) * continuousFlowTrust26738;
    /* Row-flicker ownership is single-source: alternate NORMAL rejection already
     * contains row reliability.  Only the reference, which bypasses rejection,
     * receives it here. */
    if (uReferenceObservation26737 != 0) frameWeight *= iris26720HighZoomRowReliability(sampleUv.y);
    float phaseTrust26737 = phaseTrust26738;'''
 else:
  frame='''float frameWeight = sampleRejection(referenceUv);
    frameWeight *= clamp(uObservationConfidence, 0.05, 1.0);
    frameWeight *= iris26720HighZoomRowReliability(sampleUv.y);
    /* IRIS_26737_PHOTOMETRICALLY_TRUSTED_FLOW_OWNS_SUPERRES_PHASE */
    float phaseTrust26737 = uReferenceObservation26737 != 0 ? 1.0 : clamp(flow.a, 0.0, 1.0);
    frameWeight *= phaseTrust26737;'''
 src=once(src,'float frameWeight = sampleRejection(referenceUv);',frame,'frame')
 src=once(src,'if (temporalWeight > 0.0) {','if (temporalWeight > 0.0 && phaseTrust26737 >= 0.80) {','occupancy')
 return src
specs=[(vrel,'seed','26738_vgn_seed.comp','comp'),(vrel,'localMedian','26738_vgn_local_median.comp','comp'),(vrel,'directionalSmooth','26738_vgn_directional.comp','comp'),(vrel,'iirRgb','26738_vgn_iir_rgb.comp','comp'),(vrel,'universalAdaptiveColor26561','26738_universal_adaptive_color.comp','comp'),(srel,'restoreExtendedHdrAfterVgn','26728_restore_extended_hdr_after_vgn.frag','frag'),(srel,'true2xGuideRender26568','26734_true2x_guide_render.frag','frag'),(srel,'highZoomFlowRefine26724','26738_highzoom_flow_refine.frag','frag'),(None,None,'26738_highzoom_rgb_merge.frag','frag'),(srel,'highZoomRgbProtect26724','26738_highzoom_raw_rgb_master.frag','frag')]
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 uvec2 uvec3 uvec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def exp(root,rel,name): return hmerge(root) if rel is None else runtime(root,rel,name)
def scan(fn,src):
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved); impl=sorted(set(x for x in ids if '__' in x or x.startswith('gl_')))
 assert not bad and not impl,(fn,bad,impl); assert clean.count('{')==clean.count('}'),fn; assert '#import' not in clean,fn
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,p=l.split(None,1); d[p.strip()]=h
 return d
bm=load('26738_RUNTIME_EXPANDED_BASE.sha256'); cm=load('26738_RUNTIME_EXPANDED_CANDIDATE.sha256'); assert len(bm)==len(cm)==10
changed=[]
for rel,name,fn,stage in specs:
 bs=exp(base,rel,name); cs=exp(cand,rel,name); bh=hashlib.sha256(bs.encode()).hexdigest(); ch=hashlib.sha256(cs.encode()).hexdigest()
 assert bh==bm[fn],('base hash',fn,bh,bm[fn]); expected=(bm if a.base_only else cm)[fn]; assert ch==expected,('candidate hash',fn,ch,expected)
 if bs!=cs: changed.append(fn)
 scan(fn,cs); (out/fn).write_text(cs)
if a.base_only:
 assert base.resolve()==cand.resolve() or not changed,changed
else:
 assert set(changed)=={'26738_universal_adaptive_color.comp','26738_highzoom_flow_refine.frag','26738_highzoom_rgb_merge.frag','26738_highzoom_raw_rgb_master.frag'},changed
 frozen={'26738_vgn_seed.comp':'488fe96fc378bdbba9e4040e24c295cc5181fbe3bea503d46528a31d768213e3','26738_vgn_local_median.comp':'5c19050fb7f9d9c4328662c34b9c3e58385c503aea310b90b90964afcf31d060','26738_vgn_directional.comp':'c0272ec1648dd3e8d1be5c80920f0cea24e34d504cb6bb3446890d9425eba878','26738_vgn_iir_rgb.comp':'841fcd86f84a1eca424f51b7d6e0db3b040d43f62eb8c7154a62396b198ce9c7','26728_restore_extended_hdr_after_vgn.frag':'ee8a4b306a2e0e2f6ff067f036fb626f75d02ca215a24f83e0cedaa3217d5cc8','26734_true2x_guide_render.frag':'f4125575ccb3bd6451a321c939d97ae782fd8f4416801b97834e8d7c55eba216'}
 for fn,h in frozen.items(): assert bm[fn]==cm[fn]==h,(fn,bm[fn],cm[fn])
 flow=runtime(cand,srel,'highZoomFlowRefine26724'); merge=hmerge(cand); protect=runtime(cand,srel,'highZoomRgbProtect26724'); adaptive=runtime(cand,vrel,'universalAdaptiveColor26561')
 for t in ['IRIS_26738_CONTINUOUS_RAW_PHOTOMETRIC_FLOW_CONFIDENCE','flowConfidence26738','photometricAgreement26738','photometricUniqueness26738']: assert t in flow,t
 for t in ['IRIS_26738_CONTINUOUS_RAW_OBSERVATION_ROBUSTNESS','continuousFlowTrust26738','if (uReferenceObservation26737 != 0) frameWeight *= iris26720HighZoomRowReliability']: assert t in merge,t
 for t in ['IRIS_26738_WRONSKI_NORMALIZED_CONVOLUTION_MASTER','IRIS_26738_DIRECT_RAW_CFA_CHROMA_PARITY_CLEAN','IRIS_26738_PHASE_COUNT_IS_DIAGNOSTIC_NOT_ADMISSION','meanN*max(directY,0.060)','vec3 masterRgb=mix(guideRgb,directMatched,directWeight)']: assert t in protect,t
 for t in ['IRIS_26738_UNIVERSAL_CFA_PERIOD_CHROMA_OWNER','IRIS_26738_INHERITED_COLOR_HIGHLIGHT_VETO','IRIS_26738_FINAL_ALIAS_FLOOR_VETO']: assert t in adaptive,t
# Asset shader universe invariant.
def ah(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
assert len(ah(base))==len(ah(cand))==271 and ah(base)==ah(cand)
if a.compiler:
 comp=Path(a.compiler); assert comp.exists(),comp
 for _,_,fn,stage in specs:
  cp=subprocess.run([str(comp),'-S',stage,str(out/fn)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  if cp.returncode: print(cp.stdout); raise SystemExit(f'glslang FAIL {fn}')
shutil.rmtree(out,ignore_errors=True)
mode='26737-base' if a.base_only else '26738-candidate'
print(f'PASS 26738 shaders {mode}: exact 10 runtime-expanded variants; exactly adaptive/flow/merge/raw-master changed; frozen seed/localMedian/26731 directional-IIR/explicit-SR/HDR-restore exact; reserved/structure clean; real_compiler={bool(a.compiler)}')
