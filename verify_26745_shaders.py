#!/usr/bin/env python3
from pathlib import Path
import re,hashlib,sys,tempfile,subprocess,shutil,argparse
ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('base'); ap.add_argument('cand'); ap.add_argument('--compiler'); ap.add_argument('--emit-base'); ap.add_argument('--emit-candidate'); a=ap.parse_args()
pkg=Path(a.root); base=Path(a.base); cand=Path(a.cand)
vrel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'); crel=Path('app/src/main/assets/shaders/motionv2/color_transform.glsl'); nrel=Path('app/src/main/cpp/motionv2_jpeg444_jni.cpp')
def raw_triple(root,rel,name):
 s=(root/rel).read_text(); m=re.search(r'(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S); assert m,name; return m.group(1)
def trim(v):
 lines=v.replace('\r\n','\n').replace('\r','\n').split('\n');
 if lines and not lines[0].strip(): lines=lines[1:]
 if lines and not lines[-1].strip(): lines=lines[:-1]
 nb=[l for l in lines if l.strip()]; ind=min((len(l)-len(l.lstrip()) for l in nb),default=0); return '\n'.join(l[ind:] if l.strip() else '' for l in lines)
def runtime_vgn(root):
 raw=raw_triple(root,vrel,'universalAdaptiveColor26561'); raw=raw.replace('$common',trim(raw_triple(root,vrel,'common'))); x=trim(raw); assert '$' not in x; return x
def runtime_color(root,h,l,z):
 src=(root/crel).read_text().replace('\r\n','\n').replace('\r','\n')
 repl={'#define USE_PROFILE_HUESAT 0':f'#define USE_PROFILE_HUESAT {h}','#define USE_PROFILE_LOOK 0':f'#define USE_PROFILE_LOOK {l}','#define USE_IRIS_26720_HIGH_ZOOM_RGB 0':f'#define USE_IRIS_26720_HIGH_ZOOM_RGB {z}'}
 for old,new in repl.items(): assert src.count(old)==1,(old,src.count(old)); src=src.replace(old,new,1)
 assert '#version' not in src
 return '#version 310 es\n\n#line 1\n'+src
def runtime_native(root):
 s=(root/nrel).read_text(); m=re.search(r'static const char\*kIris26571PublicationCompute=R"GLSL\((.*?)\)GLSL";',s,re.S); assert m; return m.group(1)
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 uvec2 uvec3 uvec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def scan(fn,src):
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean); ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean); bad=sorted(set(ids)&reserved); impl=sorted(set(x for x in ids if '__' in x or x.startswith('gl_'))); assert not bad,(fn,bad); assert not impl,(fn,impl); assert clean.count('{')==clean.count('}'),fn; assert '#import' not in clean,fn
def specs(root):
 d={'universal_adaptive_color.comp':(runtime_vgn(root),'comp'),'true2x_publication.comp':(runtime_native(root),'comp')}
 for h in (0,1):
  for l in (0,1):
   for z in (0,1): d[f'color_transform_h{h}_l{l}_z{z}.frag']=(runtime_color(root,h,l,z),'frag')
 return d
def load(n):
 d={}
 for line in (pkg/n).read_text().splitlines():
  if line.strip(): h,p=line.split(None,1); d[p.strip()]=h
 return d
out=Path(tempfile.mkdtemp(prefix='i26745_expanded_')); allhash={}
for label,root,manifest,emit in [('base',base,'26745_BASE_26743_RUNTIME_EXPANDED.sha256',a.emit_base),('candidate',cand,'26745_RUNTIME_EXPANDED_CANDIDATE.sha256',a.emit_candidate)]:
 sp=specs(root); hs={}
 for fn,(src,stage) in sp.items():
  scan(label+'_'+fn,src); hs[fn]=hashlib.sha256(src.encode()).hexdigest(); q=out/(label+'_'+fn); q.write_text(src)
  if a.compiler:
   cp=subprocess.run([str(Path(a.compiler)),'-S',stage,str(q)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
   if cp.returncode: print(cp.stdout); raise SystemExit(f'glslang FAIL {label} {fn}')
 if emit: Path(emit).write_text(''.join(f'{hs[n]}  {n}\n' for n in sorted(hs)))
 else: assert hs==load(manifest),(label,hs,load(manifest))
 allhash[label]=hs
assert len(allhash['base'])==len(allhash['candidate'])==10
assert set(k for k in allhash['base'] if allhash['base'][k]!=allhash['candidate'][k])==set(allhash['base'])
cv=specs(cand)['universal_adaptive_color.comp'][0]
for t in ['IRIS_26745_CONNECTED_BRIGHT_FRINGE_COLOR_AUTHORITY','connectedSecondRingCore26745','physicalBrightColorVeto26745','visibleHighlightNeutralAuthority26745']: assert t in cv,t
for fn,(src,_) in specs(cand).items():
 if fn.startswith('color_transform_'):
  for t in ['IRIS_26745_POST_VGN_ACR3_HUE_AUTHORITY','iris26745ProtectBrightNeutralHue','rotationAuthority=1.0-smoothstep(0.997,0.9998,directionAgreement)']: assert t in src,(fn,t)
nv=specs(cand)['true2x_publication.comp'][0]
for t in ['iris26745ProtectBrightNeutralHue','rotation=1.0-smoothstep(0.997,0.9998,agreement)']: assert t in nv,t
# Complete asset shader universe: exactly one intended asset shader differs.
def ah(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
A,B=ah(base),ah(cand); assert len(A)==len(B)==271; assert {k for k in A|B if A.get(k)!=B.get(k)}=={'app/src/main/assets/shaders/motionv2/color_transform.glsl'}
shutil.rmtree(out,ignore_errors=True)
print(f'PASS 26745 shaders: base+candidate exact 10 modified runtime-expanded variants (1 VGN compute + 8 color-transform define variants + 1 true2x native compute); reserved/structure clean; asset-shader universe 271 with exactly color_transform changed; real_compiler={bool(a.compiler)}')
