#!/usr/bin/env python3
"""Sensor-phase, yellow-preservation, clipped-neutral, intensity and gray-edge algebra.
Host numerical reference is NOT device IQ proof or a GLSL compiler substitute.
"""
import math,sys
from build_26937_incremental import R,fail

def smooth(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)))
 return t*t*(3-2*t)

def phase(samples,red):
 assert len(samples)==4 and red in range(4)
 blue=3-red
 green=(samples[1]+samples[2])/2 if red in (0,3) else (samples[0]+samples[3])/2
 return (samples[red],green,samples[blue])

def whiten(rgb,clips,wb=(2.,1.,1.6)):
 r,g,b=clips
 allc=min(r,g,b)
 rb=min(r,b)
 physical=max(smooth(.12,.82,allc),.35*smooth(.48,.96,rb))
 peak_sensor=max(rgb[i]/wb[i] for i in range(3))
 fade=physical*smooth(.55,.88,peak_sensor)
 peak=max(rgb)
 return tuple(v+(peak-v)*fade for v in rgb),fade

def post(before,after):
 bmax=max(before);bmin=min(before);amax=max(after);amin=min(after)
 neutral=smooth(.90,.995,bmin/max(bmax,.0001))
 bright=smooth(.95,1.35,bmax)
 false=smooth(.015,.20,max((amax-amin)-(bmax-bmin),0.))
 fade=neutral*bright*false
 lb=sum(before[i]*w for i,w in enumerate((.25,.5,.25)))
 la=sum(after[i]*w for i,w in enumerate((.25,.5,.25)))
 target=tuple(v+(la-lb) for v in before)
 rgb=tuple(after[i]+(target[i]-after[i])*fade for i in range(3))
 return rgb,fade

def close(a,b,atol=1e-7):return all(abs(x-y)<=atol for x,y in zip(a,b))

def main():
 for red in range(4):
  bits=[0.,0.,0.,0.];bits[red]=1.;bits[3-red]=.75
  r,g,b=phase(bits,red)
  assert abs(r-1)<1e-9 and abs(b-.75)<1e-9 and abs(g)<1e-9
  full=phase([1.,1.,1.,1.],red)
  assert full==(1.,1.,1.)
 # Not a broad brightness-driven desaturation; real yellow, orange and warm leaves survive even at high peak.
 yellow=(2.4,1.7,.12)
 actual,t=whiten(yellow,(1.,1.,0.))
 assert t==0 and close(actual,yellow),('yellow whitened',actual,t)
 for f in ((0.,0.,0.),(1.,0.,0.),(0.,1.,0.),(0.,0.,1.)):
  res,t=whiten(yellow,f)
  assert t==0 and close(res,yellow)
 # White clipped in all physical colour phases: even magenta recovered by native gets white.
 magenta=(2.,.28,1.55)
 result,t=whiten(magenta,(1.,1.,1.))
 assert abs(t-1.)<1e-8 and max(result)-min(result)<1e-7
 # Partial R+B clip: a soft glint boundary, no forced full whitening of warm materials.
 rbresult,t=whiten(magenta,(1.,0.,1.))
 assert 0.3<t<.36 and rbresult[1]>magenta[1]
 # Under every physically gated neutralization, no channel darkens -> avoid introducing gray contours.
 for x in range(20):
  rgb=(.7+.05*x,.1+.01*x,.25+.02*x)
  for r in (0.,.2,.5,.8,1.):
   for g in (0.,.2,.5,.8,1.):
    for b in (0.,.2,.5,.8,1.):
     corrected,fade=whiten(rgb,(r,g,b))
     assert 0<=fade<=1 and all(a+1e-8>=v for a,v in zip(corrected,rgb))
 # Lab may inject a colored fringe into a previously sensor-neutral white pixel;
 # final touch-up must preserve original post-Lab weighted brightness exactly.
 pre=(1.8,1.8,1.8);after=(2.05,1.32,1.9)
 fixed,t=post(pre,after)
 assert t>.5 and t<1.01 and (max(fixed)-min(fixed))<(max(after)-min(after))
 assert abs(sum((.25,.5,.25)[i]*(fixed[i]-after[i]) for i in range(3)))<1e-7
 # Authentic color is NEVER whitened again by the post-Lab stage.
 real_yellow=(2.2,1.6,.1);repaired,t=post(real_yellow,(2.3,1.5,.1))
 assert t==0 and close(repaired,(2.3,1.5,.1))
 # Near thresholds no sudden binary jumps; local fade should be continuous.
 vals=[whiten(magenta,(p,p,p))[1] for p in (i/200. for i in range(201))]
 assert all(0<=v<=1 for v in vals) and all(vals[i+1]>=vals[i]-1e-7 for i in range(200))
 assert max(vals[i+1]-vals[i] for i in range(200))<.03
 print('PASS 26937 four physical Bayer patterns, true clipped white, yellow preservation, soft partial glint, no preLab darkening, postLab luma continuity, threshold continuity')
if __name__=='__main__':
 try:main()
 except Exception as exc:print('26937 BLOCKED: '+str(exc),file=sys.stderr);sys.exit(1)
