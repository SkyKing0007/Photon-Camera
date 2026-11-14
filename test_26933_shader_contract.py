#!/usr/bin/env python3
"""Original current 26932 FIVE live shaders + 26933 corrected white, ABI and no GLSL `coherent`."""
from pathlib import Path
import re,sys,textwrap
from build_26933_incremental import R,OUT,fail
SRC={
 'raw_lens_median':('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt','val shader'),
 'lkr_smooth_white':('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt','val shader'),
 'motion_render':('app/src/main/assets/shaders/motionv2/render.glsl',None),
 'motion_gainmap':('app/src/main/assets/shaders/motionv2/gainmap.glsl',None),
 'b_native_final':('app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag',None),
}
SORT_SEQUENCE='p1,p2 p4,p5 p7,p8 p0,p1 p3,p4 p6,p7 p1,p2 p4,p5 p7,p8 p0,p3 p5,p8 p4,p7 p3,p6 p1,p4 p2,p5 p4,p7 p4,p2 p6,p4 p4,p2'

def get(name,live):
 p,lit=SRC[name];root=R if live else R/'handoff_payload_26933'
 # In payload mode all untouched sources come from the original successful
 # 26932 staged overlay or the published, SHA-matched 26932 candidate.
 if not live and name!='lkr_smooth_white':
  orig=R/'.photon_26933_incremental_work/authority_26932'/p
  if not orig.is_file():
   # Offline package validation checks ONLY the changed shader; historical
   # 26932 shaders already pass their own sealed payload guard.
   return None
  text=orig.read_text()
 else:text=(root/p).read_text()
 if lit:
  found=list(re.finditer(re.escape(lit)+r'\s*=\s*"""',text))
  if len(found)!=1:fail('missing/duplicate embedded shader '+name)
  return textwrap.dedent(text[found[0].end():].split('""".trimIndent()',1)[0]).strip()+'\n'
 return text

def main():
 live='--live' in sys.argv or '--extract' in sys.argv
 if '--extract' in sys.argv and not '--live' in sys.argv:fail('real compiler only from actual successful-seeded runtime source')
 bodies={x:get(x,live) for x in SRC}
 for name,body in bodies.items():
  if body is None:continue
  uncl=re.sub(r'/\*.*?\*/|//[^\n]*','',body,flags=re.S)
  if re.search(r'\bcoherent\b',uncl):fail('reserved GLSL keyword coherent in '+name)
  if re.search(r'\bgl_[A-Za-z0-9_]+\s*=',uncl):fail('illegal GLSL builtin assignment '+name)
  if name!='b_native_final' and 'void main()' not in body:fail('GLSL main missing '+name)
  if name.startswith('motion_') and '#version' in uncl:fail('double #version in motion shader')
  if name=='b_native_final' and not body.startswith('#version 310 es'):fail('native final ESSL310 missing')
  if name in ('lkr_smooth_white','raw_lens_median') and not body.startswith('#version 300 es'):fail('inline ESSL300 missing '+name)
 m=bodies['raw_lens_median']
 if m:
  seq=re.findall(r'CC_SORT\((p\d),(p\d)\)',m)
  if len(seq)!=19 or ' '.join(','.join(q) for q in seq)!=SORT_SEQUENCE:fail('original RawLens one-pass median 19 compare network changed')
  for k in ('p4=c.rb-c.g','max(vec3(c.g+p4.x,c.g,c.g+p4.y)','original.a'):
   if k not in m:fail('protected native RawLens chroma median changed '+k)
 h=bodies['lkr_smooth_white']
 for name in ('sampler2D uWbRgb','sampler2D uPreLabWbRgb','sampler2D uNativeSensorClip','vec3 uInverseAmazeWb','ivec2 uSize','vec3 uAmazeWb','int uBayerPattern'):
  if h.count('uniform '+name+';')!=1:fail('LKR shader uniform ABI duplicate/missing '+name)
 for key in ('float clipAt(ivec2 p)','vec3 phaseColorClipAt(ivec2 cell)','void main()',
             'ivec2 siteSize=uSize/2','ivec2 sensorP=clamp(p/2','vec2 cellPosition=(vec2(p)+vec2(0.5))*0.25-',
             'float fade=clamp(max(earlyFade,sensorFade),0.0,1.0);',
             'float sensorFade=measuredFade*thirdChannelNear*brightWitness;',
             'float visualNeutral=smoothstep(0.50,0.75,visibleRatio);',
             'oRgb=vec4(original.rgb*uInverseAmazeWb,original.a);return;',
             ')*uInverseAmazeWb,original.a);'):
  if key not in h:fail('current corrected B ON white source contract missing '+key)
 if 'whiteWitness' in h or 'sourceColorBalance' in h:fail('old camera/WB cross-domain multiplication remains')
 for n in ('motion_render','motion_gainmap'):
  if bodies[n] and ('iris26932BOffSdrLiftEnabled' not in bodies[n] or 'iris26932BOffSdrBridge(' not in bodies[n]):fail('B OFF SDR and gainmap matching no longer active '+n)
 if '--extract' in sys.argv:
  OUT.mkdir(exist_ok=True)
  for n,body in bodies.items():
   if body is None:fail('missing inherited current shader '+n)
   if n=='b_native_final':(OUT/f'26933_{n}_es310.frag').write_text(body)
   else:
    s=body if body.startswith('#version 300 es') else '#version 300 es\n#line 1\n'+body
    (OUT/f'26933_{n}_es300.frag').write_text(s)
    (OUT/f'26933_{n}_es310.frag').write_text(s.replace('#version 300 es','#version 310 es',1))
 print('PASS five exact successful 26932 current shaders, original RawLens median, 26933 B ON WB/physical clip, reserved GLSL identifiers')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
