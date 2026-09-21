#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile
args=sys.argv[1:]
if len(args)<3: raise SystemExit('usage: verify_26681_shaders.py ROOT BASE CAND [--compiler PATH] [--external-dir DIR]')
R,B,C=map(Path,args[:3]); compiler=None; extdir=None;i=3
while i<len(args):
 if args[i]=='--compiler': compiler=args[i+1];i+=2
 elif args[i]=='--external-dir': extdir=Path(args[i+1]);i+=2
 else: raise SystemExit('unknown arg '+args[i])

def sha_bytes(x):return hashlib.sha256(x).hexdigest()
def sha(p):return sha_bytes(Path(p).read_bytes())
def readm(p):
 d={}
 for line in Path(p).read_text().splitlines():
  if line.strip():h,n=line.split('  ',1);d[n]=h
 return d
base=readm(R/'R1_26681_SHADER_UNIVERSE_BASE.sha256');cand=readm(R/'R1_26681_SHADER_UNIVERSE_CANDIDATE.sha256')
assert len(base)==257 and len(cand)==271
for rel,h in base.items():assert sha(B/rel)==h,rel
for rel,h in cand.items():assert sha(C/rel)==h,rel
new=sorted(set(cand)-set(base));assert len(new)==14 and all('/spektra/' in x for x in new),new
compute={Path(x).name for x in new if Path(x).name.startswith('rcd')}
def expand(rel):
 p=C/rel;out=[]
 for v in p.read_text().splitlines():
  if p.name in compute and '#define LAYOUT ' in v:
   v='#define LAYOUT layout(local_size_x = 8, local_size_y = 8, local_size_z = 1) in;'
  out.append(v)
 return '#version 310 es\n#line 1\n'+'\n'.join(out)+'\n'
variants={f'local_{Path(rel).stem}.{"comp" if Path(rel).name in compute else "frag"}':expand(rel) for rel in new}
expected=readm(R/'R1_26681_RUNTIME_EXPANDED_SHADERS.sha256');assert len(expected)==14 and set(expected)==set(variants)
reserved=set("attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major gl_PerVertex".split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def scan(name,s):
 clean=re.sub(r'/\*.*?\*/',' ',s,flags=re.S);clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved);impl=sorted(set(x for x in ids if '__' in x or x.startswith('gl_')))
 if bad or impl:raise SystemExit(f'FAIL {name} reserved={bad} impl={impl}')
 if clean.count('{')!=clean.count('}'):raise SystemExit('FAIL braces '+name)
 if '#import' in clean:raise SystemExit('FAIL unresolved import '+name)
for name,s in variants.items():
 scan(name,s);assert sha_bytes(s.encode())==expected[name],name
# Upstream exact sources are supplied by the guarded build script. Validate them if materialized.
pins=[]
for line in (R/'R1_26681_SPEKTRA_UPSTREAM_SHADER_BLOBS.txt').read_text().splitlines():
 if line.strip():h,rel=line.split('  ',1);pins.append((h,rel))
assert len(pins)==10
external={}
if extdir is not None:
 for h,rel in pins:
  p=extdir/rel;assert p.is_file(),p
  cp=subprocess.run(['git','hash-object',str(p)],capture_output=True,text=True,check=True)
  assert cp.stdout.strip()==h,(rel,cp.stdout.strip(),h)
  s=p.read_text();scan('upstream_'+Path(rel).name,s);external[rel]=s
if compiler:
 if extdir is None:raise SystemExit('--compiler requires --external-dir for all 24 shaders')
 with tempfile.TemporaryDirectory(prefix='iris26681_shader_') as td:
  td=Path(td)
  for name,s in sorted(variants.items()):
   p=td/name;p.write_text(s); stage=name.rsplit('.',1)[1]
   cp=subprocess.run([compiler,'-S',stage,str(p)],capture_output=True,text=True)
   if cp.returncode:raise SystemExit(f'26681 local GLSL FAIL {name}\n{cp.stdout}\n{cp.stderr}')
  for rel,s in external.items():
   p=extdir/rel
   cp=subprocess.run([compiler,'-V','-S','comp',str(p)],capture_output=True,text=True)
   if cp.returncode:raise SystemExit(f'26681 upstream Vulkan GLSL FAIL {rel}\n{cp.stdout}\n{cp.stderr}')
print(f'PASS 26681 shaders: localExpanded=14 upstreamPinned={len(pins)} totalModifiedRuntime=24 reserved/structure/hash real_compiler={bool(compiler)} shaderUniverse=257->271')
