#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile,textwrap
if len(sys.argv) not in (4,6): raise SystemExit('usage: verify_26719_shaders.py ROOT BASE CAND [--compiler PATH]')
root,base,cand=map(Path,sys.argv[1:4]); compiler=None
if len(sys.argv)==6: assert sys.argv[4]=='--compiler'; compiler=sys.argv[5]
def load(n):
 d={}
 for l in (root/n).read_text().splitlines():
  if l.strip(): h,r=l.split(None,1); d[r.strip()]=h
 return d
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
bm=load('26719_ASSET_SHADER_UNIVERSE_BASE.sha256'); cm=load('26719_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256'); assert len(bm)==len(cm)==271 and bm==cm
for r,h in bm.items(): assert sha(base/r)==h,r
for r,h in cm.items(): assert sha(cand/r)==h,r
preview='#version 300 es\n #line 1\n'+(cand/'app/src/main/assets/shaders/preview/main_fs.glsl').read_text()
pb=load('26719_PREVIEW_RUNTIME_EXPANDED_BASE.sha256'); pc=load('26719_PREVIEW_RUNTIME_EXPANDED_CANDIDATE.sha256'); assert pb==pc and hashlib.sha256(preview.encode()).hexdigest()==pc['preview_main_fs_runtime_expanded.frag']
k=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
def triple(name):
 m=re.search(r'val\s+'+re.escape(name)+r'\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',k,re.S); assert m,name
 return textwrap.dedent(m.group(1))+'\n'
def triple_lazy(name):
 m=re.search(r'val\s+'+re.escape(name)+r'\s*:\s*String\s+by\s+lazy\s*\{\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)\s*\}',k,re.S); assert m,name
 return textwrap.dedent(m.group(1))+'\n'
merge=triple('true2xMerge26564')
out='layout(location = 0) out vec4 oColorAndRWeight;\nlayout(location = 1) out vec2 oWeightsGb;\nlayout(location = 2) out vec4 oPhaseOccupancy;\nlayout(location = 3) out vec4 oTemporalLumaStats;'
rgb='    color *= frameWeight;\n    weights *= frameWeight;\n    oColorAndRWeight = vec4(color, weights.r);\n    oWeightsGb = weights.gb;\n\n'
assert merge.count(out)==1 and merge.count(rgb)==1
merge=merge.replace(out,'layout(location = 0) out vec4 oTemporalLumaStats;\nlayout(location = 1) out vec4 oPhaseOccupancy;',1).replace(rgb,'',1)
assert 'oColorAndRWeight' not in merge and 'oWeightsGb' not in merge
resolve=triple_lazy('highZoomDetailResolve26718')
render='#version 310 es\n#line 1\n'+(cand/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
gain='#version 310 es\n#line 1\n'+(cand/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
sources={'26719_inherited_preview_runtime_expanded.frag':preview,'26719_highzoom_merge_runtime_expanded.frag':merge,'26719_highzoom_resolve_runtime_expanded.frag':resolve,'26719_motionv2_render_runtime_expanded.frag':render,'26719_motionv2_gainmap_runtime_expanded.frag':gain}
exp=load('26719_RUNTIME_EXPANDED_CANDIDATE.sha256')
for n in [x for x in sources if 'preview' not in x]: assert hashlib.sha256(sources[n].encode()).hexdigest()==exp[n],n
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major gl_PerVertex'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
for name,src in sources.items():
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean); ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean); bad=sorted(set(ids)&reserved); impl=sorted(set(i for i in ids if '__' in i or i.startswith('gl_'))); assert not bad and not impl,(name,bad,impl); assert clean.count('{')==clean.count('}') and '#import' not in clean,name
if compiler:
 for name,src in sources.items():
  with tempfile.TemporaryDirectory(prefix='iris26719_shader_') as td:
   p=Path(td)/name; p.write_text(src); cp=subprocess.run([compiler,'-S','frag',str(p)],capture_output=True,text=True)
   if cp.returncode: raise SystemExit(f'26719 GLSL FAIL {name}\n{cp.stdout}\n{cp.stderr}')
print(f'PASS 26719 shaders: 271-asset universe unchanged; inherited preview + highzoom merge/resolve + unchanged render/gainmap runtime-expanded sources validated; real_compiler={bool(compiler)}')
