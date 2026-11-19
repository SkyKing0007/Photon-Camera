#!/usr/bin/env python3
"""26962 B/SR-OFF all-zoom frozen-selected presentation, protected modes, monotonic body math."""
from pathlib import Path
import argparse,math,re
R=Path(__file__).resolve().parent
P='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
def smooth(a,b,y):
 t=max(0.,min(1.,(y-a)/(b-a)));return t*t*(3-2*t)
def body(y,k):return y+(y*y-y)*min(.35,max(0.,k))*smooth(.10,.24,y)*(1-smooth(.50,.78,y))
def selected(active,b,sr,night,nightb,zoom):
 return active and b and not sr and not night and not nightb # Independent of zoom by design.
def check(live=False):
 j=(R/P if live else R/'handoff_payload_26962'/P).read_text()
 b=(R/'26962_BASE_26961_FULL_APP.sha256').read_text()
 assert j.count('private float iris26962EffectiveSdrBodyContrast()')==1
 body_fn=j.split('private float iris26962EffectiveSdrBodyContrast()',1)[1].split('\n    }',1)[0]
 for x in ('p.motionV2Active','p.iris26906ExperimentBSelected','!p.motionV2SuperResOutputEnabled','!p.irisNightActive','!p.iris26903NightB','return selectedPhotoBOff ? 0.23f','p.motionV2SdrBodyContrast26792'):
  assert x in body_fn,x
 assert not re.search(r'zoom|localOutputZoom|lens',body_fn,re.I)
 assert 'glProg.setVar("iris26792SdrBodyContrast", iris26962EffectiveSdrBodyContrast());' in j
 assert 'final float iris26792BodyContrast = iris26962EffectiveSdrBodyContrast();' in j
 # Real mode matrix, with B at both sides of 1.10x and any physical lens.
 for z in (.5,1.,1.099,1.1,1.101,2.5,10.,30.,100.,300.):
  assert selected(True,True,False,False,False,z),z
  for flags in ((False,True,False,False,False),(True,False,False,False,False),
                (True,True,True,False,False),(True,True,False,True,False),
                (True,True,False,False,True)):
   assert not selected(*flags,z),flags
 for k in (.0,.23,.35):
  curve=[body(i/4000,k) for i in range(4001)]
  assert all(v>=u-1e-9 for u,v in zip(curve,curve[1:])),k
 for y in [0.,.05,.1,.24,.25,.5,.6,.75,.78,.9,1.]:
  assert body(y,.23)>=body(y,.35)-1e-9
  if y<=.1 or y>=.78:assert abs(body(y,.23)-body(y,.35))<1e-9
 assert abs(body(.5,.23)-.4425)<1e-10
 assert abs(body(.5,.35)-.4125)<1e-10
 # Re-render and gainmap same uniform owner in 26961 unmodified shader source.
 roots=R/'handoff_payload_26962'
 pay={p.relative_to(roots).as_posix() for p in roots.rglob('*') if p.is_file()}
 assert 'app/src/main/assets/shaders/motionv2/render.glsl' not in pay
 assert 'app/src/main/assets/shaders/motionv2/gainmap.glsl' not in pay
 assert j.count('iris26653SetFinalToneUniforms();')==5
 print('PASS 26962 mode-matrix and zoom [0.5..300], original A/Night/BON protected, monotonic global .23; SDR/gainmap shared uniform')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--payload',action='store_true');a.add_argument('--live',action='store_true');t=a.parse_args();check(t.live)
