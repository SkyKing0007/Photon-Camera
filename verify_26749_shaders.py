#!/usr/bin/env python3
from pathlib import Path
import re,hashlib,sys,tempfile,subprocess,shutil,argparse
ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('base'); ap.add_argument('cand'); ap.add_argument('--compiler'); ap.add_argument('--emit-base'); ap.add_argument('--emit-candidate'); a=ap.parse_args()
pkg=Path(a.root); base=Path(a.base); cand=Path(a.cand)
vrel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
srel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
crel=Path('app/src/main/assets/shaders/motionv2/color_transform.glsl'); nrel=Path('app/src/main/cpp/motionv2_jpeg444_jni.cpp')

def raw_triple(root,rel,name):
 s=(root/rel).read_text(); m=re.search(r'(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S); assert m,name; return m.group(1)
def trim(v):
 lines=v.replace('\r\n','\n').replace('\r','\n').split('\n')
 if lines and not lines[0].strip(): lines=lines[1:]
 if lines and not lines[-1].strip(): lines=lines[:-1]
 nb=[l for l in lines if l.strip()]; ind=min((len(l)-len(l.lstrip()) for l in nb),default=0); return '\n'.join(l[ind:] if l.strip() else '' for l in lines)
def expand_kotlin(root,rel,name,seen=()):
 assert name not in seen,(name,seen)
 raw=raw_triple(root,rel,name)
 # Expand only Kotlin string-template identifiers that refer to other triple-quoted shader bodies.
 for dep in re.findall(r'\$([A-Za-z_]\w*)',raw):
  try: repl=trim(expand_kotlin(root,rel,dep,seen+(name,)))
  except AssertionError: continue
  raw=raw.replace('$'+dep,repl)
 return raw
def runtime_vgn(root,name):
 raw=raw_triple(root,vrel,name); raw=raw.replace('$common',trim(raw_triple(root,vrel,'common'))); x=trim(raw); assert '$' not in x; return x
def runtime_sabre(root,name):
 x=trim(expand_kotlin(root,srel,name)); assert '$' not in x,(name,[z for z in re.findall(r'\$\w+',x)]); return x
def runtime_merge(root): return runtime_sabre(root,'merge')
def runtime_color(root,h,l,z):
 src=(root/crel).read_text().replace('\r\n','\n').replace('\r','\n')
 repl={'#define USE_PROFILE_HUESAT 0':f'#define USE_PROFILE_HUESAT {h}','#define USE_PROFILE_LOOK 0':f'#define USE_PROFILE_LOOK {l}','#define USE_IRIS_26720_HIGH_ZOOM_RGB 0':f'#define USE_IRIS_26720_HIGH_ZOOM_RGB {z}'}
 for old,new in repl.items(): assert src.count(old)==1,(old,src.count(old)); src=src.replace(old,new,1)
 assert '#version' not in src; return '#version 310 es\n\n#line 1\n'+src
def runtime_native(root):
 s=(root/nrel).read_text(); m=re.search(r'static const char\*kIris26571PublicationCompute=R"GLSL\((.*?)\)GLSL";',s,re.S); assert m; return m.group(1)
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 uvec2 uvec3 uvec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major packed'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def scan(fn,src):
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved); impl=sorted(set(x for x in ids if '__' in x or x.startswith('gl_'))); assert not bad,(fn,bad); assert not impl,(fn,impl); assert clean.count('{')==clean.count('}'),fn; assert '#import' not in clean,fn

def inherited_specs(root):
 d={'sabre_merge.frag':(runtime_merge(root),'frag'),'universal_adaptive_color.comp':(runtime_vgn(root,'universalAdaptiveColor26561'),'comp'),'vgn_seed.comp':(runtime_vgn(root,'seed'),'comp'),'vgn_local_median.comp':(runtime_vgn(root,'localMedian'),'comp'),'true2x_publication.comp':(runtime_native(root),'comp')}
 for h in (0,1):
  for l in (0,1):
   for z in (0,1): d[f'color_transform_h{h}_l{l}_z{z}.frag']=(runtime_color(root,h,l,z),'frag')
 return d

def candidate_specs(root):
 d=inherited_specs(root)
 d.update({
  'resolvesabre_compatibility_input_26749.frag':(runtime_sabre(root,'resolveSabreCompatibilityInput26749'),'frag'),
  'resolvesabre_reference_float_26749.frag':(runtime_sabre(root,'outputTransformFloat'),'frag'),
  'wronski_resolvesabre_reconcile_uint16_26749.frag':(runtime_sabre(root,'wronskiResolveSabreReconcileUint16_26749'),'frag'),
  'wronski_resolvesabre_reconcile_hdr_direction_uint16_26749.frag':(runtime_sabre(root,'wronskiResolveSabreReconcileHdrDirectionUint16_26749'),'frag'),
  'wronski_resolvesabre_reconcile_float_26749.frag':(runtime_sabre(root,'wronskiResolveSabreReconcileFloat_26749'),'frag'),
 })
 return d

def load(n):
 d={}
 for line in (pkg/n).read_text().splitlines():
  if line.strip(): h,p=line.split(None,1); d[p.strip()]=h
 return d
out=Path(tempfile.mkdtemp(prefix='i26749_expanded_')); allhash={}
for label,root,sp,manifest,emit in [
 ('base',base,inherited_specs(base),'26749_BASE_26748_RUNTIME_EXPANDED.sha256',a.emit_base),
 ('candidate',cand,candidate_specs(cand),'26749_RUNTIME_EXPANDED_CANDIDATE.sha256',a.emit_candidate),
]:
 hs={}
 for fn,(src,stage) in sp.items():
  scan(label+'_'+fn,src); hs[fn]=hashlib.sha256(src.encode()).hexdigest(); q=out/(label+'_'+fn); q.write_text(src)
  if a.compiler:
   cp=subprocess.run([str(Path(a.compiler)),'-S',stage,str(q)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
   if cp.returncode: print(cp.stdout); raise SystemExit(f'glslang FAIL {label} {fn}')
 if emit: Path(emit).write_text(''.join(f'{hs[n]}  {n}\n' for n in sorted(hs)))
 else: assert hs==load(manifest),(label,hs,load(manifest))
 allhash[label]=hs
assert len(allhash['base'])==13 and len(allhash['candidate'])==18,(len(allhash['base']),len(allhash['candidate']))
# Of the 13 inherited runtime variants, only VGN seed is intentionally changed by 26749.
changed_inherited={k for k in allhash['base'] if allhash['base'][k]!=allhash['candidate'][k]}
assert changed_inherited=={'vgn_seed.comp'},changed_inherited
new=set(allhash['candidate'])-set(allhash['base'])
assert new=={
 'resolvesabre_compatibility_input_26749.frag','resolvesabre_reference_float_26749.frag',
 'wronski_resolvesabre_reconcile_uint16_26749.frag','wronski_resolvesabre_reconcile_hdr_direction_uint16_26749.frag',
 'wronski_resolvesabre_reconcile_float_26749.frag'},new
compat=candidate_specs(cand)['resolvesabre_compatibility_input_26749.frag'][0]
assert 'IRIS_26749_RESOLVESABRE_COMPATIBILITY_INPUT' in (cand/srel).read_text()
for t in ['uniform vec3 uCalculationGains','max(sensor.rgb,vec3(0.0))*uCalculationGains']:
 assert t in compat,t
for fn in ['wronski_resolvesabre_reconcile_uint16_26749.frag','wronski_resolvesabre_reconcile_hdr_direction_uint16_26749.frag','wronski_resolvesabre_reconcile_float_26749.frag']:
 src=candidate_specs(cand)[fn][0]
 assert 'IRIS_26749_BOUNDED_RESOLVESABRE_CFA_REFERENCE' in (cand/srel).read_text()
 for t in ['Same hue with lower Resolve saturation is explicitly pass-through.','float realColorProtection=max(0.35*continuation,smoothstep(0.16,0.55,compactColor));','float highlightPermission=1.0-smoothstep(0.72,0.92,wy);','Preserve Wronski calculation-domain luma exactly; Resolve contributes chroma only.']:
  assert t in src,(fn,t)
 assert 'axisA' not in src and 'axisB' not in src,(fn,'invented axis aliases')
seed=candidate_specs(cand)['vgn_seed.comp'][0]
for t in ['IRIS_26749_RESOLVESABRE_CFA_REJECTION_PROVENANCE','resolveCfaReject26749','IRIS_26749_RESOLVESABRE_REJECTED_FRINGE_CANNOT_SELF_PROTECT','if(centerResolveReject26749>0.42){mask=0xFF;count=8;cleanupFallback=1;}']:
 assert t in seed,t
# Permanent 26748 compiler regressions remain locked in inherited candidates.
mv=candidate_specs(cand)['sabre_merge.frag'][0]
scope_decl='vec2 chroma26748 = vec2(0.0);'; scope_if='if (uTemporalChromaEvidence26748 != 0 && frameWeight > 0.08) {'
assert mv.count(scope_decl)==1 and mv.count('vec2 chroma26748 =')==1; assert mv.index(scope_decl)<mv.index(scope_if)<mv.index('oTemporalChromaStats26748 = vec4(')
uv=candidate_specs(cand)['universal_adaptive_color.comp'][0]
assert 'axisA' not in uv and 'axisB' not in uv
lm=candidate_specs(cand)['vgn_local_median.comp'][0]
assert 'uvec4 packed=' not in lm and 'uvec4 packedPixel26748=imageLoad(uInput,q);' in lm
# 26747 highlight authority remains present in VGN.
for t in ['IRIS_26747_CONNECTED_UNRECOVERABLE_HIGHLIGHT_OWNER','IRIS_26747_FULL_26727_UNRECOVERABLE_HEADROOM_VETO']:
 assert t in uv,t
# Asset shader universe is intentionally unchanged.
def ah(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
A,B=ah(base),ah(cand); assert len(A)==len(B)==271 and A==B
shutil.rmtree(out,ignore_errors=True)
print(f'PASS 26749 shaders: base 13 + candidate 18 exact runtime-expanded variants; inherited delta only VGN seed; 5 newly-active ResolveSabre sidecar variants; reserved/structure clean; asset shader universe 271 invariant; real_compiler={bool(a.compiler)}')
