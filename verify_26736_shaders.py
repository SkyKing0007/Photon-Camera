#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re,subprocess,tempfile,shutil
ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('base'); ap.add_argument('cand'); ap.add_argument('--compiler'); ap.add_argument('--base-only',action='store_true'); a=ap.parse_args()
pkg=Path(a.root); base=Path(a.base); cand=Path(a.cand); out=Path(tempfile.mkdtemp(prefix='i26736_expanded_'))
vrel='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'; srel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
def raw_triple(root,rel,name):
 s=(root/rel).read_text(); m=re.search(r'(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S); assert m,name; return m.group(1)
def trim(v):
 lines=v.replace('\r\n','\n').replace('\r','\n').split('\n')
 if lines and lines[0].strip()=='': lines=lines[1:]
 if lines and lines[-1].strip()=='': lines=lines[:-1]
 nb=[l for l in lines if l.strip()]; ind=min((len(l)-len(l.lstrip()) for l in nb),default=0)
 return '\n'.join(l[ind:] if l.strip() else '' for l in lines)
def runtime(root,rel,name):
 raw=raw_triple(root,rel,name)
 if '$common' in raw: raw=raw.replace('$common',trim(raw_triple(root,rel,'common')))
 x=trim(raw); assert '$' not in x,(name,'unresolved Kotlin interpolation'); return x
def once(s,old,new,label):
 c=s.count(old); assert c==1,(label,c); return s.replace(old,new,1)
def highzoom_merge(root):
 ks=(root/srel).read_text(); src=runtime(root,srel,'true2xMerge26564')
 has26736='IRIS_26736_TRUSTED_FLOW_OWNS_SUPERRES_PHASE' in ks
 uniforms='uniform float uRawClipThreshold;\nuniform float uObservationConfidence;\n'
 if has26736: uniforms+='uniform int uReferenceObservation26736;\n'
 uniforms+='uniform int uRowFlickerEnabled;\nuniform int uRowFlickerHarmonic;\nuniform vec2 uRowFlickerAB;\nuniform float uRowFlickerStrength;'
 src=once(src,'uniform float uRawClipThreshold;',uniforms,'highzoom uniforms')
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
 src=once(src,'float kernelWeight(vec2 offset, vec3 covariance) {',helper,'highzoom helper')
 frame='''float frameWeight = sampleRejection(referenceUv);
    frameWeight *= clamp(uObservationConfidence, 0.05, 1.0);
    frameWeight *= iris26720HighZoomRowReliability(sampleUv.y);'''
 if has26736:
  frame+='''
    /* IRIS_26736_TRUSTED_FLOW_OWNS_SUPERRES_PHASE */
    float refinementTrust26736 = uReferenceObservation26736 != 0 ? 1.0 : clamp(flow.a, 0.0, 1.0);
    frameWeight *= refinementTrust26736;'''
 src=once(src,'float frameWeight = sampleRejection(referenceUv);',frame,'highzoom frame confidence')
 if has26736:
  src=once(src,'if (temporalWeight > 0.0) {','if (temporalWeight > 0.0 && refinementTrust26736 >= 0.55) {','trusted phase occupancy')
 return src
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,p=l.split(None,1); d[p.strip()]=h
 return d
specs=[
(vrel,'seed','26736_vgn_seed.comp','comp'),(vrel,'localMedian','26736_vgn_local_median.comp','comp'),(vrel,'directionalSmooth','26736_vgn_directional.comp','comp'),(vrel,'iirRgb','26736_vgn_iir_rgb.comp','comp'),(vrel,'universalAdaptiveColor26561','26736_universal_adaptive_color.comp','comp'),
(srel,'restoreExtendedHdrAfterVgn','26728_restore_extended_hdr_after_vgn.frag','frag'),(srel,'true2xGuideRender26568','26734_true2x_guide_render.frag','frag'),(srel,'highZoomFlowRefine26724','26736_highzoom_flow_refine.frag','frag'),(None,None,'26736_highzoom_rgb_merge.frag','frag'),(srel,'highZoomRgbProtect26724','26736_digital_highzoom_native_chroma_protect.frag','frag')]
def expand(root,rel,name): return highzoom_merge(root) if rel is None else runtime(root,rel,name)
bm=load('26736_RUNTIME_EXPANDED_BASE.sha256'); cm=load('26736_RUNTIME_EXPANDED_CANDIDATE.sha256'); assert len(bm)==len(cm)==10
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 uvec2 uvec3 uvec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def scan(fn,src):
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved); impl=sorted(set(x for x in ids if '__' in x or x.startswith('gl_')))
 assert not bad and not impl,(fn,bad,impl); assert clean.count('{')==clean.count('}'),fn; assert '#import' not in clean,fn
changed=[]
for rel,name,fn,stage in specs:
 bs=expand(base,rel,name); cs=expand(cand,rel,name); bh=hashlib.sha256(bs.encode()).hexdigest(); ch=hashlib.sha256(cs.encode()).hexdigest()
 assert bh==bm[fn],('base hash',fn,bh,bm[fn]); expected=(bm if a.base_only else cm)[fn]; assert ch==expected,('candidate hash',fn,ch,expected)
 if bs!=cs: changed.append(fn)
 scan(fn,cs); (out/fn).write_text(cs)
if a.base_only:
 assert base.resolve()==cand.resolve() or not changed,changed
else:
 assert set(changed)=={'26736_highzoom_flow_refine.frag','26736_highzoom_rgb_merge.frag','26736_digital_highzoom_native_chroma_protect.frag'},changed
# Exact successful 26735 protected expanded owners.
frozen={
'26736_vgn_seed.comp':'d126eae91eaaa52e3cef3f71bc7adaed33e5b61fee57d172f8b843eeff667e72',
'26736_vgn_local_median.comp':'5c19050fb7f9d9c4328662c34b9c3e58385c503aea310b90b90964afcf31d060',
'26736_vgn_directional.comp':'c0272ec1648dd3e8d1be5c80920f0cea24e34d504cb6bb3446890d9425eba878',
'26736_vgn_iir_rgb.comp':'841fcd86f84a1eca424f51b7d6e0db3b040d43f62eb8c7154a62396b198ce9c7',
'26736_universal_adaptive_color.comp':'dd77446c70efaed10c981459c54c654b4ba484c4cbe8e60128dffd0a90bec5bf',
'26728_restore_extended_hdr_after_vgn.frag':'ee8a4b306a2e0e2f6ff067f036fb626f75d02ca215a24f83e0cedaa3217d5cc8',
'26734_true2x_guide_render.frag':'f4125575ccb3bd6451a321c939d97ae782fd8f4416801b97834e8d7c55eba216'}
for fn,h in frozen.items(): assert bm[fn]==cm[fn]==h,(fn,bm[fn],cm[fn])
if not a.base_only:
 flow=runtime(cand,srel,'highZoomFlowRefine26724'); merge=highzoom_merge(cand); protect=runtime(cand,srel,'highZoomRgbProtect26724')
 for t in ['IRIS_26736_WRONSKI_PHASE_OWNERSHIP_CONFIDENCE','coherentSparseTrust=sparseVariationTrust*sparseAffineTrust','phaseOwnershipConfidence26736=accept?1.0:0.75*coherentSparseTrust']: assert t in flow,t
 for t in ['IRIS_26736_TRUSTED_FLOW_OWNS_SUPERRES_PHASE','uniform int uReferenceObservation26736;','refinementTrust26736 >= 0.55','frameWeight *= refinementTrust26736']: assert t in merge,t
 for t in ['IRIS_26736_TRUSTED_PHASE_DIVERSITY_OWNER','IRIS_26736_CFA_PHASE_ALIAS_VETO','IRIS_26736_TRUSTED_HIGH_ZOOM_STRUCTURAL_LUMA_REINFORCEMENT','IRIS_26735_DIGITAL_LUMA_ONLY_DETAIL_NO_CHROMA_GAIN','trustedPhaseCompleteness26736','phaseAliasVeto26736']: assert t in protect,t
# Asset shader universe remains exact successful-26735 authority.
def ah(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
assert len(ah(base))==len(ah(cand))==271 and ah(base)==ah(cand)
if a.compiler:
 comp=Path(a.compiler); assert comp.exists(),comp
 for _,_,fn,stage in specs:
  cp=subprocess.run([str(comp),'-S',stage,str(out/fn)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  if cp.returncode: print(cp.stdout); raise SystemExit(f'glslang FAIL {fn}')
shutil.rmtree(out,ignore_errors=True)
mode='successful-26735-base' if a.base_only else '26736-candidate'
print(f'PASS 26736 shaders {mode}: exact 10 runtime-expanded variants; exactly flow/merge/protect changed; 271 assets invariant; explicit SR + VGN + 26731 owners frozen; reserved/structure clean; real_compiler={bool(a.compiler)}')
