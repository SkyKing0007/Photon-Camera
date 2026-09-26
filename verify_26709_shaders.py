#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile
if len(sys.argv) not in (4,6): raise SystemExit('usage: verify_26709_shaders.py ROOT BASE CANDIDATE [--compiler PATH]')
root,base,cand=map(Path,sys.argv[1:4]);compiler=None
if len(sys.argv)==6:
 assert sys.argv[4]=='--compiler';compiler=sys.argv[5]
def readm(n):
 d={}
 for l in (root/n).read_text().splitlines():
  if l.strip():h,r=l.split(None,1);d[r.strip()]=h
 return d
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
bm=readm('26709_ASSET_SHADER_UNIVERSE_BASE.sha256');cm=readm('26709_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256');assert len(bm)==len(cm)==271
for r,h in bm.items():assert sha(base/r)==h,r
for r,h in cm.items():assert sha(cand/r)==h,r
shader_delta=sorted(r for r in bm if bm[r]!=cm[r]);assert shader_delta==['app/src/main/assets/shaders/preview/main_fs.glsl'],shader_delta
# Exact runtime source emitted by MainRenderer.loadShader: GetSupportedVersion() + "\\n #line 1\\n" + asset.
mr=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java').read_text()
assert 'return "#version 300 es";' in mr
assert 'SupportedVersion + "\\n #line 1\\n" + fss' in mr
asset=(cand/'app/src/main/assets/shaders/preview/main_fs.glsl').read_text();src='#version 300 es\n #line 1\n'+asset
exp=readm('26709_PREVIEW_RUNTIME_EXPANDED_CANDIDATE.sha256');assert set(exp)=={'preview_main_fs_runtime_expanded.frag'}
got=hashlib.sha256(src.encode()).hexdigest();assert got==exp['preview_main_fs_runtime_expanded.frag'],(got,exp)
reserved=set("attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major gl_PerVertex".split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S);clean=re.sub(r'//.*',' ',clean)
ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
bad=sorted(set(ids)&reserved);impl=sorted(set(i for i in ids if '__' in i or i.startswith('gl_')))
if bad or impl:raise SystemExit(f'FAIL preview identifiers reserved={bad} impl={impl}')
if clean.count('{')!=clean.count('}'):raise SystemExit('FAIL preview brace mismatch')
if '#import' in clean:raise SystemExit('FAIL preview unresolved import')
if compiler:
 with tempfile.TemporaryDirectory(prefix='iris26709_shader_') as td:
  p=Path(td)/'preview_main_fs_runtime_expanded.frag';p.write_text(src);cp=subprocess.run([compiler,'-S','frag',str(p)],capture_output=True,text=True)
  if cp.returncode:raise SystemExit(f'26709 GLSL FAIL preview_main_fs_runtime_expanded.frag\n{cp.stdout}\n{cp.stderr}')
print(f'PASS 26709 modified runtime-expanded GLSL=1 exact MainRenderer #version/#line source; shader universe=271; complete reserved/structure/exact-hash real_compiler={bool(compiler)}')
