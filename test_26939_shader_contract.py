#!/usr/bin/env python3
"""Current true source ESSL inputs; mandatory PINNED GLSL / SPIR-V compilation remains in Actions."""
import re,sys,textwrap
from pathlib import Path
from build_26939_incremental import R,OUT,fail
SRC={
 'raw_lens_median':('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt',True),
 'lkr_smooth_white':('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt',True),
 'motion_render':('app/src/main/assets/shaders/motionv2/render.glsl',False),
 'motion_gainmap':('app/src/main/assets/shaders/motionv2/gainmap.glsl',False),
 'b_native_final':('app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag',False),
}
def get(kind,live):
 name,embedded=SRC[kind]
 file=(R/name if live or kind!='raw_lens_median' else R/'handoff_payload_26939'/name)
 if not file.is_file():
  if not live and kind!='raw_lens_median':return None
  fail('active current shader missing '+name)
 s=file.read_text()
 if embedded:
  markers=list(re.finditer(r'\bval\s+shader\s*=\s*"""',s))
  if len(markers)!=1 or '""".trimIndent()' not in s[markers[0].end():]:fail('wrong ESSL embedding '+kind)
  s=textwrap.dedent(s[markers[0].end():].split('""".trimIndent()',1)[0]).strip()+'\n'
 return s


# Fail-closed local parser for GLSL builtins with fixed argument counts.
# The prior 26938 V1 shader wrongly used max(a,b,c); the full GitHub
# compiler rejected it, but our old local contract checked only strings.
# This check catches it before packaging even without installed glslang.
_GLSL_ARG_COUNTS={
    'max':2, 'min':2, 'clamp':3, 'smoothstep':3,
    'mix':3, 'dot':2, 'pow':2, 'step':2, 'texelFetch':3,
}
def validate_builtin_calls(source, label):
    clean=re.sub(r'/\*.*?\*/|//[^\n]*','',source,flags=re.S)
    calls=re.finditer(r'\b('+'|'.join(_GLSL_ARG_COUNTS)+r')\s*\(',clean)
    for match in calls:
        op=match.group(1)
        start=match.end()-1
        depth=0
        arguments=1
        done=False
        for i in range(start,len(clean)):
            c=clean[i]
            if c=='(':depth+=1
            elif c==')':
                depth-=1
                if depth==0:
                    done=True
                    break
            elif c==',' and depth==1:
                arguments+=1
            if depth<0:fail('unbalanced builtin GLSL function call '+label+' '+op)
        if not done:fail('unterminated builtin GLSL function call '+label+' '+op)
        if arguments!=_GLSL_ARG_COUNTS[op]:
            fail('invalid GLSL builtin argument count '+label+' '+op+
                 ' expected='+str(_GLSL_ARG_COUNTS[op])+' actual='+str(arguments))

def assert_invalid_shader_rejected():
    for source in ('void main(){float x=max(1.0,2.0,3.0);}',
                   'void main(){float x=max(1.0,\n 2.0,\n 3.0);}',
                   'void main(){float x=min(1.0);}',
                   'void main(){float x=clamp(1.0,0.0);}'):
        try:validate_builtin_calls(source,'NEGATIVE_ARITY')
        except RuntimeError:continue
        fail('local GLSL invalid built-in arity NEGATIVE test escaped')
    validate_builtin_calls('float x=max(max(a,b),c); float y=clamp(x,0.0,1.0);',
                           'VALID_NESTED_CALLS')

def main():
 live='--live' in sys.argv
 if '--extract' in sys.argv and not live:fail('real compiler can only extract 26938-authority-seeded live shader')
 assert_invalid_shader_rejected()
 bodies={n:get(n,live) for n in SRC}
 for n,s in bodies.items():
  if s is None:continue
  validate_builtin_calls(s,n)
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
 for k in ('p4=c.rb-c.g','c.g+p4.x,c.g,c.g+p4.y',
  'uniform sampler2D uLkrPostWbRgb;',
  'uniform sampler2D uNativeSensorClip;',
  'uniform vec3 uAmazeWb;',
  'vec3 cameraRgb=medianRgb/wb;',
  'vec3 cameraWhite=vec3(1.0)/wb;',
  'cameraWhite/=max(cameraWhite.r,max(cameraWhite.g,cameraWhite.b));',
  'vec3 whiteBlendRgb=smoothstep(vec3(0.70),vec3(0.99),cameraRgb);',
  'float whiteBlend=max(whiteBlendRgb.r,max(whiteBlendRgb.g,whiteBlendRgb.b));',
  'vec3 neutralCameraRgb=mix(cameraRgb,cameraWhite,whiteBlend);',
  'vec3 corrected=neutralCameraRgb*wb;',
  'oRgb=vec4(corrected,original.a);'):
  if m.count(k)!=1:fail('missing genuine upstream RawLens early bright-white fade '+k)
 active=m.split('void main(){',1)[1]
 for token in ('originalClip(', 'phaseClip(', 'clippedPink', 'nearNeutral',
               'greenEvidence','allEvidence','rbEvidence','vec3(luma)',
               'uNativeSensorClip','uBayerPattern'):
  if token in active:fail('reintroduced physical clipping or colour veto '+token)
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
   if n=='b_native_final':(OUT/f'26939_{n}_es310.frag').write_text(body)
   else:
    es300=body if body.startswith('#version 300 es') else '#version 300 es\n#line 1\n'+body
    (OUT/f'26939_{n}_es300.frag').write_text(es300)
    (OUT/f'26939_{n}_es310.frag').write_text(es300.replace('#version 300 es','#version 310 es',1))
 print('PASS 26939 single original median, upstream RawLens unconditional early bright white, normalized WB-camera-neutral target, shader builtin-arity negatives; real GLSL/SPIR-V required in Actions')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26939 BLOCKED: '+str(e),file=sys.stderr);sys.exit(1)
