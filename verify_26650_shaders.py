#!/usr/bin/env python3
from pathlib import Path
import hashlib,itertools,re,subprocess,sys,tempfile
if len(sys.argv) not in (4,6): raise SystemExit('usage: verify_26650_shaders.py ROOT BASE CANDIDATE [--compiler PATH]')
root,base,cand=map(Path,sys.argv[1:4]); compiler=None
if len(sys.argv)==6:
 if sys.argv[4]!='--compiler': raise SystemExit('expected --compiler')
 compiler=sys.argv[5]
def readm(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
# Exact GLInterface.readProgram semantics for these two shaders: runtime #version/#line plus define replacement/import expansion.
def expand_runtime(rootp,rel,defs):
 src=(rootp/rel).read_text(); out=[]; versioned=False; linecnt=0
 for raw in src.splitlines():
  linecnt+=1; line=raw
  if '#version' in line: versioned=True
  if '#import' in line:
   if '//' not in line:
    name=line.replace('#','').replace(' ','_')+'.glsl'; imp=(rootp/'app/src/main/assets/shaders/utils'/name).read_text()
    out.extend(['#line 1',imp,f'#line {linecnt+1}'])
   continue
  if '#define' in line:
   for k,v in defs.items():
    if f' {k} ' in line:
     line=f'#define {k} {v}'; break
  out.append(line)
 body='\n'.join(out)+'\n'
 return body if versioned else '#version 310 es\n\n#line 1\n'+body
def variants(rootp):
 out=[]; rel='app/src/main/assets/shaders/motionv2/color_transform.glsl'
 for hs,look,hc in itertools.product((0,1),repeat=3):
  defs={}
  if hs: defs['USE_PROFILE_HUESAT']='1'
  if look: defs['USE_PROFILE_LOOK']='1'
  if hc: defs['USE_PHOTON_HIGHLIGHT_COMPRESSION']='1'
  out.append((f'color_transform_hs{hs}_look{look}_hc{hc}.frag',expand_runtime(rootp,rel,defs),'frag'))
 rel='app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl'; out.append(('local_laplacian_remap_26621.frag',expand_runtime(rootp,rel,{}),'frag'))
 return out
bm=readm(root/'R1_26650_SHADER_UNIVERSE_BASE.sha256'); cm=readm(root/'R1_26650_SHADER_UNIVERSE_CANDIDATE.sha256'); assert len(bm)==len(cm)==257
for r,h in bm.items(): assert sha(base/r)==h,r
for r,h in cm.items(): assert sha(cand/r)==h,r
expected=readm(root/'R1_26650_RUNTIME_EXPANDED_SHADERS.sha256'); assert len(expected)==9
reserved=set('''attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major gl_PerVertex'''.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def scan(name,src):
 if not src.startswith('#version 310 es\n\n#line 1\n'): raise SystemExit(f'FAIL {name}: not exact runtime-expanded ES 3.1 source')
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved); impl=sorted(set(i for i in ids if '__' in i or i.startswith('gl_')))
 if bad: raise SystemExit(f'FAIL {name}: reserved identifiers {bad}')
 if impl: raise SystemExit(f'FAIL {name}: implementation-reserved identifiers {impl}')
 if clean.count('{')!=clean.count('}'): raise SystemExit(f'FAIL {name}: brace mismatch')
 if name.startswith('color_transform'):
  for t in ['IRIS_26650_EXACT_PHOTON_TOGGLE_DIFFERENTIAL','PhotonCurveOff','PhotonCurveOn','photonOn/photonOff','vec3 profileRgb=']:
   if t not in src: raise SystemExit(f'FAIL {name}: missing {t}')
  hc=name.endswith('hc1.frag')
  if hc and '#define USE_PHOTON_HIGHLIGHT_COMPRESSION 1' not in src: raise SystemExit(f'FAIL {name}: HC define not expanded')
  if not hc and '#define USE_PHOTON_HIGHLIGHT_COMPRESSION 0' not in src: raise SystemExit(f'FAIL {name}: HC0 define not preserved')
 if name.startswith('local_laplacian'):
  for t in ['iris26650HighlightCompressionEnabled','legacyBaseOut','legacyResidualWeight']:
   if t not in src: raise SystemExit(f'FAIL {name}: missing {t}')
mods=variants(cand)
with tempfile.TemporaryDirectory(prefix='iris26650_shader_') as td:
 out=Path(td)
 for name,src,stage in mods:
  scan(name,src); got=hashlib.sha256(src.encode()).hexdigest(); assert expected.get(name)==got,(name,expected.get(name),got)
  # 26649 regression: compiler input is ONLY the exact runtime-expanded string above, never raw asset source.
  if compiler:
   p=out/name; p.write_text(src); cp=subprocess.run([compiler,'-S',stage,str(p)],capture_output=True,text=True)
   if cp.returncode!=0: raise SystemExit(f'26650 GLSL FAIL {name}\n{cp.stdout}\n{cp.stderr}')
print(f'PASS 26650 exact runtime-expanded GLSL variants=9 reserved/structure/exact-hash real_compiler={bool(compiler)} shaderUniverse=257')
