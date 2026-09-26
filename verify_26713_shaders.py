#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile
if len(sys.argv) not in (4,6): raise SystemExit('usage: verify_26713_shaders.py ROOT BASE CANDIDATE [--compiler PATH]')
root,base,cand=map(Path,sys.argv[1:4]); compiler=None
if len(sys.argv)==6:
    assert sys.argv[4]=='--compiler'; compiler=sys.argv[5]
def readm(n):
    d={}
    for l in (root/n).read_text().splitlines():
        if l.strip(): h,r=l.split(None,1); d[r.strip()]=h
    return d
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
bm=readm('26713_ASSET_SHADER_UNIVERSE_BASE.sha256'); cm=readm('26713_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256')
assert len(bm)==len(cm)==271
changed={r for r in bm|cm if bm.get(r)!=cm.get(r)}; assert changed=={'app/src/main/assets/shaders/preview/main_fs.glsl'},changed
for r,h in bm.items(): assert sha(base/r)==h,r
for r,h in cm.items(): assert sha(cand/r)==h,r
mr=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java').read_text()
assert 'return "#version 300 es";' in mr
assert 'SupportedVersion + \"\\n #line 1\\n\" + fss' in mr
asset=(cand/'app/src/main/assets/shaders/preview/main_fs.glsl').read_text()
src='#version 300 es\n #line 1\n'+asset
assert 'IRIS_26662_FRAME_MATCHED_PREVIEW_PRESENTATION' in asset
assert 'IRIS_26712_FULL_INVERSE_HAL_PREVIEW_PRESENTATION' not in asset
assert hashlib.sha256((cand/'app/src/main/assets/shaders/preview/main_fs.glsl').read_bytes()).hexdigest()=='4f61b83efe5b6ebe64bff6dbd165757576b1c9686e7ea78c24fdd66b3dfa724a'
exp=readm('26713_PREVIEW_RUNTIME_EXPANDED_CANDIDATE.sha256'); got=hashlib.sha256(src.encode()).hexdigest(); assert got==exp['preview_main_fs_runtime_expanded.frag']
reserved=set("attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major gl_PerVertex".split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
bad=sorted(set(ids)&reserved); impl=sorted(set(i for i in ids if '__' in i or i.startswith('gl_')))
assert not bad and not impl,(bad,impl); assert clean.count('{')==clean.count('}') and '#import' not in clean
if compiler:
    with tempfile.TemporaryDirectory(prefix='iris26713_shader_') as td:
        p=Path(td)/'preview_main_fs_runtime_expanded.frag'; p.write_text(src)
        cp=subprocess.run([compiler,'-S','frag',str(p)],capture_output=True,text=True)
        if cp.returncode: raise SystemExit(f'26713 GLSL FAIL\n{cp.stdout}\n{cp.stderr}')
print(f'PASS 26713 shader universe=271; exact 26708 preview shader restored; runtime-expanded reserved/structure/hash proof; real_compiler={bool(compiler)}')
