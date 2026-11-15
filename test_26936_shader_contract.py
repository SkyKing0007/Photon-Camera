#!/usr/bin/env python3
"""Guarded exact 26936 current-shader source expansion and reserved-identifier/ABI verification.
Actual pinned glslang 16.5 + spirv-opt/spirv-val MUST run later in Actions.
"""
import re,sys,textwrap
from pathlib import Path
from build_26936_incremental import R,OUT,fail

SRC={
 'raw_lens_median':('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt',True),
 'lkr_smooth_white':('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt',True),
 'motion_render':('app/src/main/assets/shaders/motionv2/render.glsl',False),
 'motion_gainmap':('app/src/main/assets/shaders/motionv2/gainmap.glsl',False),
 'b_native_final':('app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag',False),
}

def get(kind,live):
 path,embedded=SRC[kind]
 if live:
  file=R/path
 else:
  file=R/'handoff_payload_26936'/path
  if not file.is_file():return None # protected under identical 26935 published SHA
 if not file.is_file():fail('current shader source missing '+path)
 s=file.read_text()
 if embedded:
  markers=list(re.finditer(r'\bval\s+shader\s*=\s*"""',s))
  if len(markers)!=1 or '""".trimIndent()' not in s[markers[0].end():]:
   fail('missing or duplicate current embedded ESSL shader '+kind)
  s=textwrap.dedent(s[markers[0].end():].split('""".trimIndent()',1)[0]).strip()+'\n'
 return s

def main():
 live='--live' in sys.argv or '--extract' in sys.argv
 if '--extract' in sys.argv and '--live' not in sys.argv:
  fail('pinned real shader compilation must extract ONLY actual 26935-seeded current candidate')
 bodies={n:get(n,live) for n in SRC}
 for n,s in bodies.items():
  if s is None:continue
  uncommented=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
  if re.search(r'\bcoherent\b',uncommented):fail('forbidden GLSL reserved keyword coherent in '+n)
  if re.search(r'\b(?:readonly|writeonly|restrict|volatile)\s*=',uncommented):
   fail('reserved GLSL identifier in '+n)
  if re.search(r'\bgl_[A-Za-z0-9_]+\s*=',uncommented):fail('invalid GLSL builtin assignment '+n)
  if n!='b_native_final' and s.count('void main()')!=1:
   fail('current ESSL shader missing or duplicated entry point '+n)
  if n=='b_native_final' and not s.startswith('#version 310 es'):
   fail('fused native shader ABI wrong version')
  if n in ('raw_lens_median','lkr_smooth_white') and not s.startswith('#version 300 es'):
   fail('embedded ESSL300 shader ABI missing '+n)
  if n.startswith('motion_') and '#version' in uncommented:
   fail('preexisting motion asset must receive exactly one injected GLSL version '+n)
 h=bodies['lkr_smooth_white'];assert h is not None
 for key in ('uniform sampler2D uWbRgb;','uniform sampler2D uPreLabWbRgb;',
   'uniform sampler2D uNativeSensorClip;','uniform vec3 uInverseAmazeWb;',
   'uniform vec3 uAmazeWb;','uniform int uBayerPattern;',
   'uniform ivec2 uSize;','phaseColorClipAt(ivec2 cell)',
   'clipAt(sensorP)',
   'float balanced=smoothstep(0.42,0.72,third/max(peak,0.0001));',
   'float allColors=min(phaseSupport.r,min(phaseSupport.g,phaseSupport.b));',
   'float sensorFade=smoothstep(0.12,0.82,coverage)*physicalWhite*',
   'float fade=clamp(max(visibleShoulder,sensorFade),0.0,1.0);',
   'vec3 corrected=mix(original.rgb,vec3(localPeak),fade);',
   'oRgb=vec4(corrected*uInverseAmazeWb,original.a);'):
  if h.count(key)!=1:fail('26936 exact color-preserving LKR shader missing/duplicate '+key)
 for bad in ('vec3 whiteCurve=smoothstep(vec3(0.70),vec3(0.99),visualRgb);',
             'float visualFade=max(whiteCurve.r','max(visualFade,clipFade)',
             'float neutral=max(hi,wbSafe)','float sensorWhite'):
  if bad in h:fail('prior indiscriminate/gray-white 26934 material repaint returned '+bad)
 if h.count('float[4](clipAt(base)')!=1 or h.count('clipAt(sensorP)')!=1:
  fail('original exact Bayer R16F physical clipping provenance modified')
 m=bodies['raw_lens_median']
 if m is not None:
  if len(re.findall(r'\bCC_SORT\(p\d,p\d\)',m))!=19:fail('protected original RawLens median sorting network modified')
  for k in ('p4=c.rb-c.g','original.a'):
   if k not in m:fail('protected original RawLens median chroma missing '+k)
 for n in ('motion_render','motion_gainmap'):
  if bodies[n] and ('iris26932BOffSdrLiftEnabled' not in bodies[n]
       or 'iris26932BOffSdrBridge(' not in bodies[n]):
   fail('successful 26935 B OFF SDR/UHDR shader protection lost '+n)
 if '--extract' in sys.argv:
  OUT.mkdir(exist_ok=True)
  for n,body in bodies.items():
   if body is None:fail('cannot compile with missing protected shader '+n)
   if n=='b_native_final':
    (OUT/f'26936_{n}_es310.frag').write_text(body)
   else:
    es300=body if body.startswith('#version 300 es') else '#version 300 es\n#line 1\n'+body
    (OUT/f'26936_{n}_es300.frag').write_text(es300)
    (OUT/f'26936_{n}_es310.frag').write_text(es300.replace('#version 300 es','#version 310 es',1))
 print('PASS 26936 LKR 3x2 original physical clip, color-preserving white rolloff, no GLSL coherent/reserved identifiers')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
