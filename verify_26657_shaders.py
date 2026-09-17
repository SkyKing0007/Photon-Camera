#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile
if len(sys.argv) not in (4,6): raise SystemExit('usage: verify_26657_shaders.py ROOT BASE CANDIDATE [--compiler PATH]')
root,base,cand=map(Path,sys.argv[1:4]);compiler=None
if len(sys.argv)==6:
 if sys.argv[4]!='--compiler': raise SystemExit('expected --compiler')
 compiler=sys.argv[5]
def readm(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
bm=readm(root/'R1_26657_SHADER_UNIVERSE_BASE.sha256');cm=readm(root/'R1_26657_SHADER_UNIVERSE_CANDIDATE.sha256');assert len(bm)==len(cm)==262
for r,h in bm.items(): assert sha(base/r)==h,r
for r,h in cm.items(): assert sha(cand/r)==h,r
changed={r for r in set(bm)|set(cm) if bm.get(r)!=cm.get(r)}
assert changed==set(),changed
def preprocess(src,defs):
 lines=src.splitlines();out=[];active=[True]
 for line in lines:
  s=line.strip();m=re.match(r'#define\s+(\w+)\s+(.+)',s)
  if m and m.group(1) in defs:
   if active[-1]: out.append(f'#define {m.group(1)} {defs[m.group(1)]}')
   continue
  m=re.match(r'#if\s+(\w+)\s*==\s*(\d+)',s)
  if m:
   active.append(active[-1] and int(defs.get(m.group(1),-999))==int(m.group(2)));continue
  if s=='#else':
   if len(active)<2: raise SystemExit('FAIL unexpected #else')
   parent=active[-2];active[-1]=parent and not active[-1];continue
  if s=='#endif':
   if len(active)<2: raise SystemExit('FAIL unexpected #endif')
   active.pop();continue
  if active[-1]: out.append(line)
 if len(active)!=1: raise SystemExit('FAIL preprocessor stack')
 return '\n'.join(out)+'\n'
def plain(rel): return '#version 310 es\n#line 1\n'+(cand/rel).read_text()
def pp(rel,defs): return '#version 310 es\n#line 1\n'+preprocess((cand/rel).read_text(),defs)
variants={
'local_laplacian_downsample_luma.frag':pp('app/src/main/assets/shaders/local_laplacian/downsample.glsl',{'INPUT_RGB':0}),
'local_laplacian_downsample_rgb.frag':pp('app/src/main/assets/shaders/local_laplacian/downsample.glsl',{'INPUT_RGB':1}),
'local_laplacian_reconstruct_mid.frag':pp('app/src/main/assets/shaders/local_laplacian/reconstruct.glsl',{'FINE_RGB':0,'FINAL_OUTPUT':0}),
'local_laplacian_reconstruct_final.frag':pp('app/src/main/assets/shaders/local_laplacian/reconstruct.glsl',{'FINE_RGB':1,'FINAL_OUTPUT':1}),
'motionv2_gainmap.frag':plain('app/src/main/assets/shaders/motionv2/gainmap.glsl'),
'photon_new_log_luma.frag':plain('app/src/main/assets/shaders/motionv2/photon_new_log_luma.glsl'),
'photon_new_precolor.frag':plain('app/src/main/assets/shaders/motionv2/photon_new_precolor.glsl'),
'photon_new_prepare.frag':plain('app/src/main/assets/shaders/motionv2/photon_new_prepare.glsl')}
native=(cand/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text();m=re.search(r'static const char\*kIris26571PublicationCompute=R"GLSL\(\n(.*?)\n\)GLSL";',native,re.S)
if not m: raise SystemExit('FAIL true2x compute extraction')
variants['motionv2_true2x_publication.comp']=m.group(1)+'\n'
expected_hash=readm(root/'R1_26657_RUNTIME_EXPANDED_SHADERS.sha256');assert len(expected_hash)==9 and set(expected_hash)==set(variants)
reserved=set("attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major gl_PerVertex".split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def scan(name,src):
 if not src.startswith('#version 310 es\n'): raise SystemExit(f'FAIL {name}: not exact runtime GLSL ES source')
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S);clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved);impl=sorted(set(i for i in ids if '__' in i or i.startswith('gl_')))
 if bad: raise SystemExit(f'FAIL {name}: reserved identifiers {bad}')
 if impl: raise SystemExit(f'FAIL {name}: implementation-reserved identifiers {impl}')
 if clean.count('{')!=clean.count('}'): raise SystemExit(f'FAIL {name}: brace mismatch')
with tempfile.TemporaryDirectory(prefix='iris26657_shader_') as td:
 out=Path(td)
 for name,src in sorted(variants.items()):
  scan(name,src);got=hashlib.sha256(src.encode()).hexdigest();assert expected_hash[name]==got,(name,expected_hash[name],got)
  if compiler:
   p=out/name;p.write_text(src);stage='comp' if name.endswith('.comp') else 'frag';cp=subprocess.run([compiler,'-S',stage,str(p)],capture_output=True,text=True)
   if cp.returncode!=0: raise SystemExit(f'26657 GLSL FAIL {name}\n{cp.stdout}\n{cp.stderr}')
print(f'PASS 26657 exact runtime GLSL variants=9 reserved/structure/exact-hash real_compiler={bool(compiler)} standaloneShaderUniverse=262 unchangedFromSuccessful26656')
