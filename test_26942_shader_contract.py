#!/usr/bin/env python3
"""Exact live 26942 expanded shaders, built-in arity and reserved identifier preflight.
This is NOT a replacement for the mandatory Actions pinned real GLSL + SPIR-V tools.
"""
import re,sys,textwrap
from pathlib import Path
from build_26942_incremental import R,OUT,fail,scope
SRC={
 'raw_lens_median':('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt',True),
 'lkr_smooth_white':('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt',True),
 'motion_render':('app/src/main/assets/shaders/motionv2/render.glsl',False),
 'motion_gainmap':('app/src/main/assets/shaders/motionv2/gainmap.glsl',False),
 'b_native_final':('app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag',False),
}
ARG={'max':2,'min':2,'clamp':3,'smoothstep':3,'mix':3,'dot':2,'pow':2,'step':2,'texelFetch':3}
def check_arity(s,name):
 clean=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
 for m in re.finditer(r'\b('+'|'.join(ARG)+r')\s*\(',clean):
  depth=0;count=1;done=False
  for c in clean[m.end()-1:]:
   if c=='(':depth+=1
   elif c==')':
    depth-=1
    if depth==0:done=True;break
   elif c==',' and depth==1:count+=1
  if not done or count!=ARG[m.group(1)]:fail('26942 illegal GLSL builtin arity '+name+' '+m.group(1)+' count='+str(count))
 return clean
def shader(name,live):
 path,embedded=SRC[name]
 source=R/path if live else (R/'handoff_payload_26942'/path)
 if not source.is_file():
  if live:fail('missing actual GLSL source '+path)
  return None
 s=source.read_text()
 if embedded:
  match=list(re.finditer(r'\bval\s+shader\s*=\s*"""',s))
  if len(match)!=1 or '""".trimIndent()' not in s[match[0].end():]:fail('original embedded shader malformed '+path)
  s=textwrap.dedent(s[match[0].end():].split('""".trimIndent()',1)[0]).strip()+'\n'
 return s

def main():
 scope();live='--live' in sys.argv
 if '--extract' in sys.argv and not live:fail('current real compile only on authority-seeded live 26942 source')
 for bad in ('float t=max(1.,2.,3.);','float t=min(1.);','float t=clamp(1.,0.);'):
  try:check_arity(bad,'negative')
  except RuntimeError:pass
  else:fail('fixed GLSL function arity negative test escaped')
 body={n:shader(n,live) for n in SRC}
 for n,s in body.items():
  if s is None:continue
  clean=check_arity(s,n)
  if re.search(r'\bcoherent\b|\b(?:readonly|writeonly|restrict|volatile)\s*=',clean):fail('reserved GLSL identifier '+n)
  if re.search(r'\bgl_[A-Za-z0-9_]+\s*=',clean):fail('writes reserved GLSL builtin '+n)
  if n=='b_native_final':
   if not s.startswith('#version 310 es'):fail('protected fused final GLSL ABI changed')
  elif n in ('raw_lens_median','lkr_smooth_white'):
   if not s.startswith('#version 300 es') or s.count('void main()')!=1:fail('inline ESSL 300 required '+n)
  elif '#version' in clean:fail('Motion source already versioned; duplicate ESSL version '+n)
 if body['motion_render'] is not None:
  render=body['motion_render'];gain=body['motion_gainmap']
  for x in (render,gain):
   for mark in ('uniform int iris26941BOffHdrqLowZoom;',
                'float iris26941BOffMatchedSdrPrimary(float priorGuide,float sourceGuide)',
                'if(target<=0.82)return target;'):
    if x.count(mark)!=1:fail('missing 26942 exact B OFF SDR/gain shader ABI '+mark)
  if render.count('iris26941BOffMatchedSdrPrimary(mappedGuide,')!=2:fail('global/local SDR shader parity incomplete')
  if gain.count('float hdrHighlightGate=smoothstep(0.68,0.96,brightIntent);')!=1:fail('UHDR highlight-only guard missing')
  if gain.count('ratio=1.0+(ratio-1.0)*hdrHighlightGate;')!=1:fail('UHDR ratio not highlight-gated')
  if live:
   java=(R/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
   if java.count('glProg.setVar("iris26941BOffHdrqLowZoom", iris26941BOffHdrqLowZoom ? 1 : 0);')!=2:
    fail('live render/gainmap uniform not bound exactly twice')
 if not live:
  # No 26942 GLSL changed: the sealed 26941 authority manifest must prove all
  # five upstream source files are untouched by the two-file runtime patch.
  old,new=scope()[1:]
  for name,(path,_) in SRC.items():
   if old.get(path)!=new.get(path):fail('changed pinned GLSL input '+name)
 if '--extract' in sys.argv:
  OUT.mkdir(exist_ok=True)
  for n,s in body.items():
   if s is None:fail('actual compilation requires all 5 shader inputs '+n)
   if n=='b_native_final':(OUT/f'26942_{n}_es310.frag').write_text(s)
   else:
    base=s if s.startswith('#version 300 es') else '#version 300 es\n#line 1\n'+s
    (OUT/f'26942_{n}_es300.frag').write_text(base)
    (OUT/f'26942_{n}_es310.frag').write_text(base.replace('#version 300 es','#version 310 es',1))
 print('PASS 26942 source shader input/arity/reserved-token negatives, 5 real ESSL300/310 shader variants sealed; Actions glslang+SPIR-V mandatory')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
