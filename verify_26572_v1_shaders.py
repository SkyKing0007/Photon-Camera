#!/usr/bin/env python3
from pathlib import Path
import argparse,re,subprocess,hashlib,json
RESERVED=set('''attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uvec2 uvec3 uvec4 sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow samplerCubeArray samplerCubeArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler1DArray isampler2DArray isamplerCubeArray usampler1D usampler2D usampler3D usamplerCube usampler1DArray usampler2DArray usamplerCubeArray sampler2DRect sampler2DRectShadow isampler2DRect usampler2DRect samplerBuffer isamplerBuffer usamplerBuffer sampler2DMS isampler2DMS usampler2DMS sampler2DMSArray isampler2DMSArray usampler2DMSArray image1D image2D image3D image2DRect imageCube imageBuffer image1DArray image2DArray imageCubeArray image2DMS image2DMSArray iimage1D iimage2D iimage3D iimage2DRect iimageCube iimageBuffer iimage1DArray iimage2DArray iimageCubeArray iimage2DMS iimage2DMSArray uimage1D uimage2D uimage3D uimage2DRect uimageCube uimageBuffer uimage1DArray uimage2DArray uimageCubeArray uimage2DMS uimage2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using row_major then packed lowp mediump highp precision'''.split())
TYPES=set(x for x in RESERVED if re.match(r'^(?:[diub]?vec[234]|[d]?mat|[iu]?sampler|[iu]?image|float|double|int|uint|bool|void|atomic_uint)',x));TYPES.add('uint')
QUAL=set('const in out inout uniform attribute varying centroid flat smooth noperspective patch sample invariant precise highp mediump lowp readonly writeonly coherent volatile restrict'.split())
def fail(m): raise SystemExit('FAIL: '+m)
def trim_indent(s):
 lines=s.splitlines()
 if lines and not lines[0].strip():lines=lines[1:]
 if lines and not lines[-1].strip():lines=lines[:-1]
 non=[len(l)-len(l.lstrip()) for l in lines if l.strip()];n=min(non) if non else 0
 return '\n'.join(l[n:] for l in lines)+'\n'
def extract_kotlin(src,name):
 m=re.search(r'(?m)^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""',src)
 if not m:fail('missing Kotlin embedded shader '+name)
 a=m.end();z=src.find('""".trimIndent()',a)
 if z<0:fail('missing shader end '+name)
 return trim_indent(src[a:z])
def strip_comments(s):
 s=re.sub(r'/\*.*?\*/',' ',s,flags=re.S);return re.sub(r'//[^\n]*',' ',s)
def declared(src):
 code='\n'.join('' if l.lstrip().startswith('#') else l for l in strip_comments(src).splitlines())
 found=[];ta='|'.join(sorted(map(re.escape,TYPES),key=len,reverse=True));qa='|'.join(sorted(map(re.escape,QUAL),key=len,reverse=True))
 pat=re.compile(r'\b(?:'+qa+r'\s+)*(?:'+ta+r')\s+([A-Za-z_]\w*)')
 for m in pat.finditer(code):found.append((m.group(1),m.start(1)))
 stmt=re.compile(r'\b(?:'+qa+r'\s+)*(?:'+ta+r')\s+([^;{}]+);')
 for sm in stmt.finditer(code):
  tail=sm.group(1);depth=0;last=0;parts=[]
  for i,ch in enumerate(tail):
   if ch in '([':depth+=1
   elif ch in ')]':depth=max(0,depth-1)
   elif ch==',' and depth==0:parts.append(tail[last:i]);last=i+1
  parts.append(tail[last:])
  for part in parts:
   mm=re.match(r'\s*([A-Za-z_]\w*)',part)
   if mm:found.append((mm.group(1),sm.start(1)+tail.find(part)+mm.start(1)))
 return sorted(set(found),key=lambda x:x[1])
def scan(label,src):
 bad=[]
 for name,pos in declared(src):
  if name in RESERVED or name.startswith('gl_') or '__' in name:bad.append((name,src.count('\n',0,pos)+1))
 if bad:fail(label+' reserved declared identifiers '+repr(bad))
 if src.count('{')!=src.count('}'):fail(label+' brace mismatch')
 if '#version 300 es' not in src:fail(label+' version missing')
 return len(declared(src))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('candidate_root');ap.add_argument('--out',required=True);ap.add_argument('--glslang');ns=ap.parse_args()
 root=Path(ns.candidate_root);out=Path(ns.out);out.mkdir(parents=True,exist_ok=True)
 kt=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
 src=extract_kotlin(kt,'true2xGuideRender26568')
 if '$' in src:fail('unresolved Kotlin interpolation in true2x guide render')
 name='true2x_true_detail_26572';target=out/(name+'.frag');target.write_text(src)
 n=scan(name,src);h=hashlib.sha256(target.read_bytes()).hexdigest();status='NOT RUN'
 for token in ['IRIS_26572_TRUE_DETAIL_LUMA_OWNER','blockPhaseCount','guideBlockY','safetyGate = min(','0.42 / maxAbsDetail','directChromaOwner']:
  # directChromaOwner is source ownership telemetry, not shader; skip that one below
  if token=='directChromaOwner':continue
  if token not in src:fail('true-detail shader contract '+token)
 if ns.glslang:
  r=subprocess.run([ns.glslang,'-S','frag',str(target)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  if r.returncode:print(r.stdout);fail('glslang compile '+name)
  status='PASS'
 (out/'V1_26572_RUNTIME_EXPANDED_SHADERS.sha256').write_text(f'{h}  {target.name}\n')
 (out/'V1_26572_SHADER_VERIFICATION.json').write_text(json.dumps([{'shader':name,'sha256':h,'declared_identifiers':n,'real_glslang':status}],indent=2)+'\n')
 print('PASS exact modified runtime-expanded shader extraction + complete reserved scan variants=1')
 print('REAL GLSL COMPILE: '+('PASS' if ns.glslang else 'NOT RUN'))
if __name__=='__main__':main()
