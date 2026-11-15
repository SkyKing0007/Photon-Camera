#!/usr/bin/env python3
"""Current true source ESSL inputs; mandatory PINNED GLSL / SPIR-V compilation remains in Actions."""
import re,sys,textwrap
from pathlib import Path
from build_26938_incremental import R,OUT,fail
SRC={
 'raw_lens_median':('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt',True),
 'lkr_smooth_white':('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt',True),
 'motion_render':('app/src/main/assets/shaders/motionv2/render.glsl',False),
 'motion_gainmap':('app/src/main/assets/shaders/motionv2/gainmap.glsl',False),
 'b_native_final':('app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag',False),
}
def get(kind,live):
 name,embedded=SRC[kind]
 file=(R/name if live or kind!='raw_lens_median' else R/'handoff_payload_26938'/name)
 if not file.is_file():
  if not live and kind!='raw_lens_median':return None
  fail('active current shader missing '+name)
 s=file.read_text()
 if embedded:
  markers=list(re.finditer(r'\bval\s+shader\s*=\s*"""',s))
  if len(markers)!=1 or '""".trimIndent()' not in s[markers[0].end():]:fail('wrong ESSL embedding '+kind)
  s=textwrap.dedent(s[markers[0].end():].split('""".trimIndent()',1)[0]).strip()+'\n'
 return s

def main():
 live='--live' in sys.argv
 if '--extract' in sys.argv and not live:fail('real compiler can only extract 26937-authority-seeded live shader')
 bodies={n:get(n,live) for n in SRC}
 for n,s in bodies.items():
  if s is None:continue
  clean=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
  # Prior documented 26904 optimizer failure: reserved GLSL tokens are forbidden in executable identifier positions.
  if re.search(r'\bcoherent\b|\b(?:readonly|writeonly|restrict|volatile)\s*=',clean):fail('reserved GLSL identifier '+n)
  if re.search(r'\bgl_[A-Za-z0-9_]+\s*=',clean):fail('GLSL builtin overwritten '+n)
  if n=='b_native_final':
   if not s.startswith('#version 310 es'):fail('fused P3 shader ABI changed')
  elif n in ('raw_lens_median','lkr_smooth_white'):
   if not s.startswith('#version 300 es') or s.count('void main()')!=1:fail('bad ESSL300 shader '+n)
  elif '#version' in clean:fail('protected motion shader duplicate version '+n)
 m=bodies['raw_lens_median']
 if len(re.findall(r'\bCC_SORT\(p\d,p\d\)',m))!=19:fail('RawLens original exact 19 compare-exchanges changed')
 for k in ('p4=c.rb-c.g','c.g+p4.x,c.g,c.g+p4.y','uniform sampler2D uNativeSensorClip;',
  'uniform int uBayerPattern;','float originalClip(ivec2 site)','vec3 phaseClip(ivec2 cell)',
  'vec3 sensorRgb=medianRgb/wb;','vec3 whiteCurve=smoothstep(vec3(0.70),vec3(0.99),sensorRgb);',
  'float clippedPink=wrongMagenta*max(rbEvidence,greenEvidence);',
  'float luma=dot(medianRgb,vec3(0.25,0.50,0.25));',
  'vec3 corrected=mix(medianRgb,vec3(luma),fade);','oRgb=vec4(corrected,original.a);'):
  if m.count(k)!=1:fail('missing one-pass color/brightness shader contract '+k)
 if '0.35*smoothstep(0.48,0.96,rbClip)' in m:fail('ineffective old rb gating returned')
 if live:
  s=(R/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
  for mark in ('bindTexture(program,"uNativeSensorClip",1,originalClip)',
   'bindTexture(program,"uPreLabWbRgb",1,rawlensMedian26932)',
   'bindTexture(program,"uWbRgb",0,defringed)',
   'rawlensMedian26932 = renderIris26932LkrMedian('):
   if s.count(mark)!=1:fail('original B ON texture binding or Lab path changed '+mark)
  if not(s.index('rawlensMedian26932 = renderIris26932LkrMedian(')<s.index('defringed = renderRawrLabDefringe26856(')<s.index('neutral = createTexture(processingWidth, processingHeight, GLES30.GL_RGBA16F')):
   fail('white correction is not before Lab')
  for x in ('motion_render','motion_gainmap'):
   if 'iris26932BOffSdrLiftEnabled' not in bodies[x] or 'iris26932BOffSdrBridge(' not in bodies[x]:fail('protected B OFF SDR/UHDR shader changed')
 if '--extract' in sys.argv:
  OUT.mkdir(exist_ok=True)
  for n,body in bodies.items():
   if body is None:fail('real compiler source missing '+n)
   if n=='b_native_final':(OUT/f'26938_{n}_es310.frag').write_text(body)
   else:
    es300=body if body.startswith('#version 300 es') else '#version 300 es\n#line 1\n'+body
    (OUT/f'26938_{n}_es300.frag').write_text(es300)
    (OUT/f'26938_{n}_es310.frag').write_text(es300.replace('#version 300 es','#version 310 es',1))
 print('PASS 26938 source-driven shader ABI, original one-pass median, physical Bayer evidence, RawLens camera-domain threshold, final weighted-luma neutral axis; real compiler required in Actions')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26938 BLOCKED: '+str(e),file=sys.stderr);sys.exit(1)
