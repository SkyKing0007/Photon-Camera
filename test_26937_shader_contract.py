#!/usr/bin/env python3
"""Prove current B/ON median and neutral reconciliation actual GLSL inputs and program ABI.
Real PINNED glslang 16.5, SPIR-V optimizer/validator must compile the generated
fragments in Actions; no text check is substituted for compilation.
"""
import re,sys,textwrap
from pathlib import Path
from build_26937_incremental import R,OUT,fail
SRC={
 'raw_lens_median':('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt',True),
 'lkr_smooth_white':('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt',True),
 'motion_render':('app/src/main/assets/shaders/motionv2/render.glsl',False),
 'motion_gainmap':('app/src/main/assets/shaders/motionv2/gainmap.glsl',False),
 'b_native_final':('app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag',False),
}
def get(kind,live):
 path,embedded=SRC[kind]
 file=R/path if live else R/'handoff_payload_26937'/path
 if not file.is_file():
  if not live and kind in ('motion_render','motion_gainmap','b_native_final'):return None
  fail('active shader missing '+path)
 s=file.read_text()
 if embedded:
  markers=list(re.finditer(r'\bval\s+shader\s*=\s*"""',s))
  if len(markers)!=1 or '""".trimIndent()' not in s[markers[0].end():]:fail('missing/duplicate current embedded ESSL shader '+kind)
  s=textwrap.dedent(s[markers[0].end():].split('""".trimIndent()',1)[0]).strip()+'\n'
 return s

def main():
 live='--live' in sys.argv
 if '--extract' in sys.argv and not live:fail('real current shader compiler extraction must use official 26936-seeded candidate')
 bodies={n:get(n,live) for n in SRC}
 for n,s in bodies.items():
  if s is None:continue
  uncommented=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
  if re.search(r'\bcoherent\b|\b(?:readonly|writeonly|restrict|volatile)\s*=',uncommented):fail('forbidden ESSL reserved identifier/qualifier in '+n)
  if re.search(r'\bgl_[A-Za-z0-9_]+\s*=',uncommented):fail('GLSL builtin overwritten '+n)
  if n=='b_native_final':
   if not s.startswith('#version 310 es'):fail('fused P3 shader version mismatch')
  elif n in ('raw_lens_median','lkr_smooth_white'):
   if not s.startswith('#version 300 es') or s.count('void main()')!=1:fail('current embedded ESSL300 entry invalid '+n)
  elif '#version' in uncommented:fail('protected motion asset receives duplicate GLSL version '+n)
 m=bodies['raw_lens_median'];h=bodies['lkr_smooth_white']
 if len(re.findall(r'\bCC_SORT\(p\d,p\d\)',m))!=19:fail('original RawLens 19-exchange median modified')
 for k in ('p4=c.rb-c.g','c.g+p4.x,c.g,c.g+p4.y','original.a','uniform sampler2D uNativeSensorClip;',
   'uniform int uBayerPattern;','float originalClip(ivec2 site)','vec3 phaseClip(ivec2 cell)',
   'float allClip=min(phases.r,min(phases.g,phases.b));',
   'vec3 corrected=mix(medianRgb,vec3(peak),clamp(fade,0.0,1.0));'):
  if m.count(k)!=1:fail('missing B ON original physical mask or single median contract '+k)
 for k in ('uniform sampler2D uWbRgb;','uniform sampler2D uPreLabWbRgb;',
   'uniform vec3 uInverseAmazeWb;','uniform ivec2 uSize;',
   'float fade=neutral*bright*newFalseColor;',
   'vec3 neutralAtLuma=before+vec3(afterLuma-beforeLuma);',
   'oRgb=vec4(corrected*uInverseAmazeWb,original.a);'):
  if h.count(k)!=1:fail('post Lab chroma continuity ABI missing '+k)
 if 'uNativeSensorClip' in h or 'uAmazeWb' in h or 'uBayerPattern' in h:fail('old late-post-Lab physical white owner returned')
 stackfile=R/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt' if live else R/'handoff_payload_26937/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
 stack=stackfile.read_text()
 if stack.count('bindTexture(program,"uNativeSensorClip",1,originalClip)')!=1:fail('physical mask not exclusively bound before Lab')
 if stack.count('bindTexture(program,"uPreLabWbRgb",1,rawlensMedian26932)')!=1:fail('post Lab true precursor missing')
 if stack.count('bindTexture(program,"uWbRgb",0,defringed)')!=1:fail('actual post Lab domain disconnected')
 for n in ('motion_render','motion_gainmap'):
  if bodies[n] and ('iris26932BOffSdrLiftEnabled' not in bodies[n] or 'iris26932BOffSdrBridge(' not in bodies[n]):fail('protected B OFF SDR/UHDR shader contract changed '+n)
 if '--extract' in sys.argv:
  OUT.mkdir(exist_ok=True)
  for n,body in bodies.items():
   if body is None:fail('cannot compile with missing protected shader '+n)
   if n=='b_native_final':(OUT/f'26937_{n}_es310.frag').write_text(body)
   else:
    es300=body if body.startswith('#version 300 es') else '#version 300 es\n#line 1\n'+body
    (OUT/f'26937_{n}_es300.frag').write_text(es300)
    (OUT/f'26937_{n}_es310.frag').write_text(es300.replace('#version 300 es','#version 310 es',1))
 print('PASS 26937 B ON 19-exchange median exact, selected-reference physical clip mask and before/after Lab ESSL ABI; pinned compiler still mandatory')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
