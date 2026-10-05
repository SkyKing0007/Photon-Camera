#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile,textwrap
if len(sys.argv) not in (3,5): raise SystemExit('usage: verify_26770_shaders.py BASE26769 CAND26770 [--compiler glslangValidator]')
base,cand=map(Path,sys.argv[1:3]); compiler=None
if len(sys.argv)==5: assert sys.argv[3]=='--compiler'; compiler=sys.argv[4]
post_rel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
render_rel=Path('app/src/main/assets/shaders/motionv2/render.glsl'); gain_rel=Path('app/src/main/assets/shaders/motionv2/gainmap.glsl')
bs=(base/post_rel).read_text(); cs=(cand/post_rel).read_text()
def raw(src,name):
 m=re.search(r'\b(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""(.*?)"""\.trimIndent\(\)',src,re.S); assert m,name; return m.group(1)
def emb(src,name): return textwrap.dedent(raw(src,name)).lstrip('\n')
def asset(root,rel):
 src=(root/rel).read_text()
 # Exact GLInterface runtime expansion for these two files: neither contains #version/#import/#define.
 assert '#version' not in src and '#import' not in src and '#define' not in src
 return '#version 310 es\n\n#line 1\n'+src
reserved=set('attribute const uniform varying layout centroid flat smooth noperspective break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler1DArray isampler2DArray usampler1D usampler2D usampler3D usamplerCube usampler1DArray usampler2DArray sampler2DRect sampler2DRectShadow isampler2DRect usampler2DRect samplerBuffer isamplerBuffer usamplerBuffer sampler2DMS isampler2DMS usampler2DMS sampler2DMSArray isampler2DMS usampler2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234]|sampler2D|usampler2D|uimage2D)'
def scan(label,shader,stage):
 assert shader.startswith('#version 310 es\n'),label
 t=re.sub(r'/\*.*?\*/|//[^\n]*',' ',shader,flags=re.S); names=[]
 for m in re.finditer(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\s*(?:[=;,\[])',t): names.append(m.group(1))
 for m in re.finditer(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\s*\(',t): names.append(m.group(1))
 bad=sorted({n for n in names if n in reserved or n.startswith('__')}); assert not bad,(label,bad)
 assert shader.count('{')==shader.count('}'),(label,'brace'); assert shader.count('(')==shader.count(')'),(label,'paren')
 print(f'PASS 26770 reserved-identifier/structure scan {label}: {len(names)} identifiers')
 if compiler:
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/(label.replace('/','_')+'.'+('comp' if stage=='comp' else 'frag')); f.write_text(shader)
   r=subprocess.run([compiler,'-S',stage,str(f)],text=True,capture_output=True)
   if r.returncode: raise SystemExit(label+'\n'+r.stdout+r.stderr)
  print(f'PASS 26770 pinned real glslang compile exact runtime-expanded {label}')
# Only embedded final trust body changes among postprocessor shader bodies.
names=['universalAdaptiveColor26561','seed','localClamp','localMedian','directionalSmooth','restoreDirection','iirRgb','calculateError','iirError','blendChroma','finalCameraRgb','bipolarColorTrust26769']
changed=[n for n in names if raw(bs,n)!=raw(cs,n)]; assert changed==['bipolarColorTrust26769'],changed
scan('base26769/bipolarColorTrust26769',emb(bs,'bipolarColorTrust26769'),'comp')
scan('candidate26770/bipolarColorTrust26769',emb(cs,'bipolarColorTrust26769'),'comp')
for rel in [render_rel,gain_rel]:
 scan('base26769/'+rel.name,asset(base,rel),'frag'); scan('candidate26770/'+rel.name,asset(cand,rel),'frag')
print('PASS 26770 shader scope: frozen containment bodies protected; modified final trust + render/gainmap exact runtime-expanded coverage complete')
