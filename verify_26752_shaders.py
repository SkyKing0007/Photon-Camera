#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re,subprocess,tempfile,shutil
p=argparse.ArgumentParser();p.add_argument('pkg');p.add_argument('base');p.add_argument('candidate');p.add_argument('--compiler');a=p.parse_args();pkg,base,cand=map(Path,[a.pkg,a.base,a.candidate])
rels=['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl']
reserved=set('attribute const uniform varying layout centroid flat smooth noperspective break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant discard return mat2 mat3 mat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow isampler2D usampler2D sampler2DRect sampler2DRectShadow samplerBuffer isamplerBuffer usamplerBuffer sampler2DMS isampler2DMS usampler2DMS sampler2DMSArray isampler2DMSArray usampler2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major packed'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def exp(root,rel):
 src=(root/rel).read_text(); assert '#version' not in src and '#import' not in src
 return '#version 310 es\n\n#line 1\n'+src
def scan(name,src):
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S);clean=re.sub(r'//.*',' ',clean);ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean);bad=sorted(set(ids)&reserved);impl=sorted(set(x for x in ids if '__' in x or x.startswith('gl_')));assert not bad,(name,bad);assert not impl,(name,impl);assert clean.count('{')==clean.count('}'),name
 # exact recent regression class: every 26752 symbol used in shader is explicitly declared as uniform/local/function.
 used=set(re.findall(r'\b[A-Za-z_]\w*26752\b',clean)); declared=set(re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*26752)\b',clean)); declared|=set(re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*26752)\s*\(',clean)); assert not (used-declared),(name,sorted(used-declared))
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip():h,x=l.split(None,1);d[x.strip()]=h
 return d
out=Path(tempfile.mkdtemp(prefix='i26752_shader_'))
try:
 allh={}
 for label,root,man in [('base',base,'26752_RUNTIME_EXPANDED_BASE_26733.sha256'),('candidate',cand,'26752_RUNTIME_EXPANDED_CANDIDATE.sha256')]:
  hs={}
  for rel in rels:
   name=rel.replace('app/src/main/assets/shaders/','').replace('.glsl','.frag');src=exp(root,rel);scan(label+'_'+name,src);hs[name]=hashlib.sha256(src.encode()).hexdigest();q=out/(label+'_'+name.replace('/','_'));q.write_text(src)
   if a.compiler:
    cp=subprocess.run([str(Path(a.compiler)),'-S','frag',str(q)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    if cp.returncode: print(cp.stdout);raise SystemExit(f'glslang FAIL {label} {name}')
  assert hs==load(man),(label,hs,load(man));allh[label]=hs
 assert set(allh['base'])==set(allh['candidate'])=={'motionv2/render.frag','motionv2/gainmap.frag'}
 assert {k for k in allh['base'] if allh['base'][k]!=allh['candidate'][k]}==set(allh['base'])
 for rel in rels:
  s=(cand/rel).read_text(); assert 'iris26752PlanBDetailScale' in s and 'iris26752PlanBDetailOrigin' in s and 'sourcePixel*iris26752PlanBDetailScale-iris26752PlanBDetailOrigin' in s
 # complete asset universe preserved in cardinality and changed exactly at intended two assets.
 def AH(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
 A,B=AH(base),AH(cand);assert len(A)==len(B)==271;assert {k for k in A|B if A.get(k)!=B.get(k)}==set(rels)
finally: shutil.rmtree(out,ignore_errors=True)
print(f'PASS 26752 shaders: exact GLInterface runtime expansion #version 310 es/#line 1; 2 base + 2 candidate modified fragment variants; complete reserved/structure/26752 declaration scan; asset shader universe 271 with exactly two intended changes; real_compiler={bool(a.compiler)}')
