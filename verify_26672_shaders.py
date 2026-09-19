#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile,textwrap
if len(sys.argv) not in (4,6): raise SystemExit('usage: verify_26672_shaders.py ROOT BASE CANDIDATE [--compiler PATH]')
root,base,cand=map(Path,sys.argv[1:4]); compiler=None
if len(sys.argv)==6:
 assert sys.argv[4]=='--compiler'; compiler=sys.argv[5]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readm(p):
 d={}
 for l in Path(p).read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
def embedded(r):
 s=(r/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(); out={}
 for m in re.finditer(r'\bval\s+([A-Za-z_]\w*)\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S): out[m.group(1)]=textwrap.dedent(m.group(2)).strip('\n')
 return out
def expand(rootdir,rel,defines=None):
 lines=(rootdir/rel).read_text().splitlines(); out=[]; versioned=False; defines=defines or {}
 for v in lines:
  if '#version' in v: versioned=True
  if '#import' in v: raise SystemExit(f'FAIL unexpected import {rel}: {v}')
  if '#define' in v:
   for k,x in defines.items():
    if f' {k} ' in v: v=f'#define {k} {x}'; break
  out.append(v)
 body='\n'.join(out)+'\n'; return body if versioned else '#version 310 es\n#line 1\n'+body
def variants(rootdir):
 mods=embedded(rootdir)
 req=['rejection','merge','universalNormalMasterShortFusion26651']
 for x in req:
  if x not in mods: raise SystemExit('FAIL missing embedded shader '+x)
 out={
  'embedded_sabre_rejection.frag':mods['rejection'],
  'embedded_sabre_merge.frag':mods['merge'],
  'embedded_universalNormalMasterShortFusion26651.frag':mods['universalNormalMasterShortFusion26651'],
  'asset_render.frag':expand(rootdir,'app/src/main/assets/shaders/motionv2/render.glsl'),
  'asset_local_laplacian_global_log_26621.frag':expand(rootdir,'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl'),
  'asset_local_laplacian_remap_26621.frag':expand(rootdir,'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl'),
  'asset_gainmap.frag':expand(rootdir,'app/src/main/assets/shaders/motionv2/gainmap.glsl'),
  'asset_preview_main_fs.frag':expand(rootdir,'app/src/main/assets/shaders/preview/main_fs.glsl'),
 }
 for hs in (0,1):
  for lk in (0,1): out[f'asset_color_transform_huesat{hs}_look{lk}.frag']=expand(rootdir,'app/src/main/assets/shaders/motionv2/color_transform.glsl',{'USE_PROFILE_HUESAT':str(hs),'USE_PROFILE_LOOK':str(lk)})
 return out
bm=readm(root/'R1_26672_SHADER_UNIVERSE_BASE.sha256'); cm=readm(root/'R1_26672_SHADER_UNIVERSE_CANDIDATE.sha256')
assert len(bm)==len(cm)==257
for r,h in bm.items(): assert sha(base/r)==h,r
for r,h in cm.items(): assert sha(cand/r)==h,r
shader_delta=sorted(r for r in bm if bm[r]!=cm[r])
expected_shader_delta=[]
assert shader_delta==expected_shader_delta,shader_delta
bv=variants(base); cv=variants(cand); assert len(bv)==len(cv)==12 and set(bv)==set(cv)
expected=readm(root/'R1_26672_RUNTIME_EXPANDED_SHADERS.sha256'); assert len(expected)==12 and set(expected)==set(cv)
changed_variants=sorted(k for k in bv if hashlib.sha256(bv[k].encode()).hexdigest()!=hashlib.sha256(cv[k].encode()).hexdigest())
expected_changed=[x for x in (root/'R1_26672_RUNTIME_EXPANDED_CHANGED_VARIANTS.txt').read_text().splitlines() if x]
assert changed_variants==expected_changed,(changed_variants,expected_changed)
reserved=set("attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major gl_PerVertex".split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def scan(name,s):
 clean=re.sub(r'/\*.*?\*/',' ',s,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved); impl=sorted(set(i for i in ids if '__' in i or i.startswith('gl_')))
 if bad or impl: raise SystemExit(f'FAIL {name} identifiers reserved={bad} impl={impl}')
 if clean.count('{')!=clean.count('}'): raise SystemExit(f'FAIL {name} braces')
with tempfile.TemporaryDirectory(prefix='iris26672_shader_') as td:
 o=Path(td)
 for n,s in sorted(cv.items()):
  scan(n,s); got=hashlib.sha256(s.encode()).hexdigest(); assert expected[n]==got,(n,expected[n],got)
  if compiler:
   p=o/n; p.write_text(s); cp=subprocess.run([compiler,'-S','frag',str(p)],capture_output=True,text=True)
   if cp.returncode: raise SystemExit(f'26672 GLSL FAIL {n}\n{cp.stdout}\n{cp.stderr}')
print(f'PASS 26672 exact runtime GLSL variants=12 changedVariants={len(changed_variants)} complete reserved/structure/exact-hash real_compiler={bool(compiler)} standaloneShaderUniverse=257')
