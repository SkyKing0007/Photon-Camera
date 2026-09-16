#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile,textwrap
if len(sys.argv) not in (4,6): raise SystemExit('usage: verify_26652_shaders.py ROOT BASE CANDIDATE [--compiler PATH]')
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
def embedded(rootp):
 s=(rootp/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(); out={}
 for m in re.finditer(r'\bval\s+([A-Za-z_]\w*)\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S): out[m.group(1)]=textwrap.dedent(m.group(2)).strip('\n')
 return out
bm=readm(root/'R1_26652_SHADER_UNIVERSE_BASE.sha256'); cm=readm(root/'R1_26652_SHADER_UNIVERSE_CANDIDATE.sha256'); assert len(bm)==len(cm)==257 and bm==cm
for r,h in bm.items(): assert sha(base/r)==h,r
for r,h in cm.items(): assert sha(cand/r)==h,r
expected=readm(root/'R1_26652_RUNTIME_EXPANDED_SHADERS.sha256'); assert len(expected)==3
mods=embedded(cand); names=['universalNormalMasterShortFusion26651','universalFusionTelemetry26651','universalShortValidityAugment26651']
reserved=set("attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major gl_PerVertex".split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def scan(name,src):
 if not src.startswith('#version 300 es\n'): raise SystemExit(f'FAIL {name}: not exact runtime GLSL ES source')
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved); impl=sorted(set(i for i in ids if '__' in i or i.startswith('gl_')))
 if bad: raise SystemExit(f'FAIL {name}: reserved identifiers {bad}')
 if impl: raise SystemExit(f'FAIL {name}: implementation-reserved identifiers {impl}')
 if clean.count('{')!=clean.count('}'): raise SystemExit(f'FAIL {name}: brace mismatch')
with tempfile.TemporaryDirectory(prefix='iris26652_shader_') as td:
 out=Path(td)
 for n in names:
  src=mods[n]; fname=n+'.frag'; scan(fname,src); got=hashlib.sha256(src.encode()).hexdigest(); assert expected.get(fname)==got,(fname,expected.get(fname),got)
  if compiler:
   p=out/fname;p.write_text(src); cp=subprocess.run([compiler,'-S','frag',str(p)],capture_output=True,text=True)
   if cp.returncode!=0: raise SystemExit(f'26652 GLSL FAIL {fname}\n{cp.stdout}\n{cp.stderr}')
print(f'PASS 26652 exact runtime embedded GLSL variants=3 reserved/structure/exact-hash real_compiler={bool(compiler)} standaloneShaderUniverse=257 unchanged')
