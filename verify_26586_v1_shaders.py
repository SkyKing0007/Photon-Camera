#!/usr/bin/env python3
from pathlib import Path
import argparse,re,subprocess,hashlib,json
RESERVED=set('''attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uvec2 uvec3 uvec4 sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow samplerCubeArray samplerCubeArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler1DArray isampler2DArray isamplerCubeArray usampler1D usampler2D usampler3D usamplerCube usampler1DArray usampler2DArray usamplerCubeArray sampler2DRect sampler2DRectShadow isampler2DRect usampler2DRect samplerBuffer isamplerBuffer usamplerBuffer sampler2DMS isampler2DMS usampler2DMS sampler2DMSArray isampler2DMSArray usampler2DMSArray image1D image2D image3D image2DRect imageCube imageBuffer image1DArray image2DArray imageCubeArray image2DMS image2DMSArray iimage1D iimage2D iimage3D iimage2DRect iimageCube iimageBuffer iimage1DArray iimage2DArray iimageCubeArray iimage2DMS iimage2DMSArray uimage1D uimage2D uimage3D uimage2DRect uimageCube uimageBuffer uimage1DArray uimage2DArray uimageCubeArray uimage2DMS uimage2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using row_major then packed lowp mediump highp precision'''.split())
TYPES=set(x for x in RESERVED if re.match(r'^(?:[diub]?vec[234]|[d]?mat|[iu]?sampler|[iu]?image|float|double|int|uint|bool|void|atomic_uint)',x));TYPES.add('uint')
QUAL=set('const in out inout uniform attribute varying centroid flat smooth noperspective patch sample invariant precise highp mediump lowp readonly writeonly coherent volatile restrict'.split())
def fail(m): raise SystemExit('FAIL: '+m)
def trim_indent(s):
 lines=s.splitlines()
 if lines and not lines[0].strip(): lines=lines[1:]
 if lines and not lines[-1].strip(): lines=lines[:-1]
 non=[len(l)-len(l.lstrip()) for l in lines if l.strip()]; n=min(non) if non else 0
 return '\n'.join(l[n:] for l in lines)+'\n'
def extract_kotlin(src,name):
 m=re.search(r'(?m)^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""',src)
 if not m: fail('missing Kotlin embedded shader '+name)
 a=m.end(); z=src.find('""".trimIndent()',a)
 if z<0: fail('missing shader end '+name)
 return trim_indent(src[a:z])
def strip_comments(s):
 s=re.sub(r'/\*.*?\*/',' ',s,flags=re.S); return re.sub(r'//[^\n]*',' ',s)
def declared(src):
 code='\n'.join('' if l.lstrip().startswith('#') else l for l in strip_comments(src).splitlines())
 found=[]; ta='|'.join(sorted(map(re.escape,TYPES),key=len,reverse=True)); qa='|'.join(sorted(map(re.escape,QUAL),key=len,reverse=True))
 pat=re.compile(r'\b(?:'+qa+r'\s+)*(?:'+ta+r')\s+([A-Za-z_]\w*)')
 for m in pat.finditer(code): found.append((m.group(1),m.start(1)))
 stmt=re.compile(r'\b(?:'+qa+r'\s+)*(?:'+ta+r')\s+([^;{}]+);')
 for sm in stmt.finditer(code):
  tail=sm.group(1); depth=0; last=0; parts=[]
  for i,ch in enumerate(tail):
   if ch in '([': depth+=1
   elif ch in ')]': depth=max(0,depth-1)
   elif ch==',' and depth==0: parts.append(tail[last:i]); last=i+1
  parts.append(tail[last:])
  for part in parts:
   mm=re.match(r'\s*([A-Za-z_]\w*)',part)
   if mm: found.append((mm.group(1),sm.start(1)+tail.find(part)+mm.start(1)))
 return sorted(set(found),key=lambda x:x[1])
def scan(label,src):
 bad=[]
 for name,pos in declared(src):
  if name in RESERVED or name.startswith('gl_') or '__' in name: bad.append((name,src.count('\n',0,pos)+1))
 if bad: fail(label+' reserved declared identifiers '+repr(bad))
 if src.count('{')!=src.count('}'): fail(label+' brace mismatch')
 if not re.search(r'#version\s+(?:300|310)\s+es',src): fail(label+' version missing')
 if '$' in src: fail(label+' unresolved Kotlin interpolation')
 return len(declared(src))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('candidate_root');ap.add_argument('--out',required=True);ap.add_argument('--glslang');ns=ap.parse_args()
 root=Path(ns.candidate_root);out=Path(ns.out);out.mkdir(parents=True,exist_ok=True)
 vgn=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text();common=extract_kotlin(vgn,'common').rstrip()
 sabre=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
 specs=[
  ('vgn_universal_gap_owner_26581',extract_kotlin(vgn,'universalAdaptiveColor26561'),'comp',['IRIS_26578_FAIL_CLOSED_REAL_COLOR_GATE','IRIS_26579_MICRO_OBJECT_COLOR_TOPOLOGY','IRIS_26580_MICRO_OBJECT_AREA_VS_RIBBON','IRIS_26580_FAIL_CLOSED_MULTICOLOR_OBJECT_VETO','IRIS_26581_OCCLUSION_GAP_BACKGROUND_OWNER','IRIS_26581_GAP_BACKGROUND_CHROMA_RESTORE','gapPairEvidence','gapOwnership','falseColorGate','maximumMove']),
  ('vgn_local_median_26574',extract_kotlin(vgn,'localMedian').replace('$common',common),'comp',['topologySupport','topologyProtection']),
  ('vgn_directional_smooth_26574',extract_kotlin(vgn,'directionalSmooth').replace('$common',common),'comp',['topologySupport','0.85*topologyProtection']),
  ('vgn_iir_rgb_26574',extract_kotlin(vgn,'iirRgb').replace('$common',common),'comp',['topologyBoundary','currentPerpendicularSupport','previousPerpendicularSupport']),
  ('true2x_flow_refine_26574',extract_kotlin(sabre,'true2xFlowRefine26574'),'frag',['conditioning>0.012','improvement>0.08','uniqueness>0.04','vec2(0.25)','accept?1.0:0.0']),
  ('true2x_topology_chroma_26581',extract_kotlin(sabre,'true2xGuideRender26568'),'frag',['IRIS_26579_TRUE2X_TOPOLOGY_CHROMA_UPSAMPLE','irisTopologyGuide','sameMaterial','maxChromaMagnitude','directChromaOwner'])
 ]
 specs[-1]=(specs[-1][0],specs[-1][1],specs[-1][2],['IRIS_26579_TRUE2X_TOPOLOGY_CHROMA_UPSAMPLE','IRIS_26580_TRUE2X_SAME_MATERIAL_CHROMA_OWNERSHIP','IRIS_26580_NEUTRAL_GLYPH_OUTSIDE_EDGE_EXCLUSION','IRIS_26581_DECISIVE_CROSS_EDGE_CHROMA_VETO','IRIS_26581_MATERIAL_SEPARATED_SR_DETAIL_ENVELOPE','materialBoundary','materialSupportGate','edgeExcursion','maxChromaMagnitude','bilinearY','confidence'])
 # 26586 runtime GLSL is byte-identical to 26585, so compile the exact same two appearance variants as successful 26585.
 app=(root/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text()
 prefix='#version 310 es\n\n#line 1\n'
 app0=prefix+app
 app1=prefix+app.replace('#define CALIBRATED_PROFILE 0','#define CALIBRATED_PROFILE 1')
 specs.extend([
  ('adaptive_color_appearance_26585_universal',app0,'frag',['IRIS_26585_TONE_AWARE_HIGHLIGHT_CHROMA_PRESERVATION','uniform float sceneWhite','legacyChromaGain','toneSafeHighlightGain','highlightFloorGainLimit','0.995','1.12']),
  ('adaptive_color_appearance_26585_calibrated',app1,'frag',['IRIS_26585_TONE_AWARE_HIGHLIGHT_CHROMA_PRESERVATION','#define CALIBRATED_PROFILE 1','uniform float sceneWhite'])
 ])
 rows=[];manifest=[]
 for label,src,stage,tokens in specs:
  for token in tokens:
   if token not in src: fail(label+' contract '+token)
  ext='comp' if stage=='comp' else 'frag';target=out/(label+'.'+ext);target.write_text(src)
  n=scan(label,src);h=hashlib.sha256(target.read_bytes()).hexdigest();status='NOT RUN'
  if ns.glslang:
   r=subprocess.run([ns.glslang,'-S',stage,str(target)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   if r.returncode:
    print(r.stdout);fail('glslang compile '+label)
   status='PASS'
  manifest.append(f'{h}  {target.name}\n');rows.append({'shader':label,'sha256':h,'declared_identifiers':n,'real_glslang':status})
 (out/'V1_26586_RUNTIME_EXPANDED_SHADERS.sha256').write_text(''.join(manifest))
 (out/'V1_26586_SHADER_VERIFICATION.json').write_text(json.dumps(rows,indent=2)+'\n')
 print('PASS exact runtime-expanded shader extraction + complete reserved scan variants=8')
 print('REAL GLSL COMPILE: '+('PASS' if ns.glslang else 'NOT RUN'))
if __name__=='__main__':main()
