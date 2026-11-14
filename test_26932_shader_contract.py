#!/usr/bin/env python3
"""Real GLSL source contract and reproducible extracted ESSL bodies. Not a compiler substitute."""
from pathlib import Path
import sys,re,hashlib,textwrap
from build_26932_incremental import R,OUT,fail

SRC={
 'raw_lens_median':('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt','val shader'),
 'lkr_smooth_white':('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt','val shader'),
 'motion_render':('app/src/main/assets/shaders/motionv2/render.glsl',None),
 'motion_gainmap':('app/src/main/assets/shaders/motionv2/gainmap.glsl',None),
 'b_native_final':('app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag',None),
}
SORT_SEQUENCE='p1,p2 p4,p5 p7,p8 p0,p1 p3,p4 p6,p7 p1,p2 p4,p5 p7,p8 p0,p3 p5,p8 p4,p7 p3,p6 p1,p4 p2,p5 p4,p7 p4,p2 p6,p4 p4,p2'

def get(name,live):
 p,lit=SRC[name];root=R if live else R/'handoff_payload_26932'
 text=(root/p).read_text()
 if lit:
  matches=list(re.finditer(re.escape(lit)+r'\s*=\s*"""',text))
  if len(matches)!=1:fail('missing or duplicate inline shader '+name)
  body=textwrap.dedent(text[matches[0].end():].split('""".trimIndent()',1)[0]).strip()+'\n'
 else:body=text
 return body

def main():
 live='--live' in sys.argv or '--extract' in sys.argv
 if '--extract' in sys.argv and not '--live' in sys.argv:fail('must extract from true runtime, never staged substitute')
 bodies={k:get(k,live) for k in SRC}
 for name,body in bodies.items():
  uncommented=re.sub(r'/\*.*?\*/|//[^\n]*','',body,flags=re.S)
  if re.search(r'\bcoherent\b',uncommented):fail('invalid reserved coherent keyword in active shader '+name)
  if re.search(r'\b(gl_[A-Za-z0-9_]+)\s*=\s*',uncommented):fail('illegal GLSL built-in assignment '+name)
  if 'void main()' not in body and name!='b_native_final':fail('missing shader main '+name)
  if name.startswith('motion_') and '#version' in uncommented:fail('motion shader falsely carries #version '+name)
  if name=='b_native_final' and not body.startswith('#version 310 es'):fail('50MP final not ESSL310')
  if name in ('raw_lens_median','lkr_smooth_white') and not body.startswith('#version 300 es'):fail('inline shaders not ESSL300')
 m=bodies['raw_lens_median']
 sorts=re.findall(r'CC_SORT\((p\d),(p\d)\)',m)
 if len(sorts)!=19 or ' '.join(','.join(x) for x in sorts)!=SORT_SEQUENCE:fail('not original RawLens 2.2.86 median compare/exchange network')
 for needle in ('p4=c.rb-c.g','max(vec3(c.g+p4.x,c.g,c.g+p4.y)','original.a'):
  if needle not in m:fail('RawLens exact green/chroma/alpha semantics changed '+needle)
 h=bodies['lkr_smooth_white']
 for needle in ('uNativeSensorClip','uBayerPattern','uAmazeWb','uInverseAmazeWb','fade=max(earlyFade,sensorFade)'):
  if needle not in h:fail('native clip-to-white source incomplete '+needle)
 for n in ('motion_render','motion_gainmap'):
  x=bodies[n]
  if 'iris26932BOffSdrLiftEnabled' not in x or 'iris26932BOffSdrBridge(' not in x:fail('gain-map/SDR matched mapping not active '+n)
 if '--extract' in sys.argv:
  OUT.mkdir(exist_ok=True)
  for n,body in bodies.items():
   if n=='b_native_final':
    (OUT/f'26932_{n}_es310.frag').write_text(body)
   else:
    s=body if body.startswith('#version 300 es') else '#version 300 es\n#line 1\n'+body
    (OUT/f'26932_{n}_es300.frag').write_text(s)
    (OUT/f'26932_{n}_es310.frag').write_text(s.replace('#version 300 es','#version 310 es',1))
  print('PASS all five current active shaders extracted directly from live source for real GLSL')
 else:print('PASS 26932 exact 19-swap RawLens median, clip/uniform ABI, no reserved GLSL coherent, five GLSL contracts')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
