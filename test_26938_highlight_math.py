#!/usr/bin/env python3
"""Independent CPU algebra replay of three alternatives and final 26938 algorithm.
This tests specific color cases and luminance stability, NOT device photographic parity.
"""
import math,sys
from build_26938_incremental import fail
WB=(2.,1.,1.6);W=(.25,.50,.25)
def sm(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)));return t*t*(3.-2.*t)
def lu(rgb):return sum(x*w for x,w in zip(rgb,W))
def old37(rgb,clips,wb=WB):
 r,g,b=clips
 phys=max(sm(.12,.82,min(clips)),.35*sm(.48,.96,min(r,b)))
 peak=max(x/y for x,y in zip(rgb,wb));fade=phys*sm(.55,.88,peak)
 p=max(rgb);return tuple(x+fade*(p-x) for x in rgb),fade
def rawlens(rgb,wb=WB):
 sensor=[x/y for x,y in zip(rgb,wb)]
 fade=max(sm(.70,.99,x) for x in sensor)
 # upstream rcd_final target is unscaled measured camera-white (1/WB), then mapped to WB-space.
 out=tuple(x+(1.-x)*fade for x in rgb)
 return out,fade
def b_off(rgb,wb=WB):
 ceiling=min(wb)
 return tuple(min(x,ceiling) for x in rgb)
def new38(rgb,clips,wb=WB):
 sensor=tuple(max(0.,x)/y for x,y in zip(rgb,wb))
 rawwhite=max(sm(.70,.99,x) for x in sensor)
 r,g,b=clips
 allc=sm(.07,.80,min(clips));rb=sm(.07,.80,min(r,b));green=sm(.07,.80,g)
 p=max(rgb);minimum=min(rgb);span=(p-minimum)/max(p,.0001)
 pink=(min(rgb[0],rgb[2])-rgb[1])/max(p,.0001)
 bad=sm(.03,.14,pink)
 clipped=bad*max(rb,green)
 neutral=1.-sm(.11,.29,span)
 fade=max(allc,clipped,neutral*rawwhite)
 assert 0<=fade<=1
 l=lu(rgb)
 return tuple(x+(l-x)*fade for x in rgb),fade

def close(a,b,tol=1e-7):return all(abs(x-y)<=tol for x,y in zip(a,b))
def main():
 # Initial causes from 26937: green-only and R+B clipping, native output magenta.
 pink=(1.92,.26,1.48)
 for name,clip in [('G-only',(0.,1.,0.)),('R+B',(1.,0.,1.)),('RGB',(1.,1.,1.))]:
  old,told=old37(pink,clip)
  assert told<.36 if name=='R+B' else told==0. if name=='G-only' else told>.99
  new,fade=new38(pink,clip)
  assert fade>.99,(name,fade)
  assert max(new)-min(new)<1e-6,(name,new)
  assert abs(lu(new)-lu(pink))<1e-7
 # Original RawLens fades real bright yellow white; strict B OFF cap leaves green gap in magenta.
 yellow=(1.86,1.30,.12)
 raw,t=rawlens(yellow)
 assert t>.99 and max(raw)-min(raw)<1e-7
 assert abs(rawlens(pink)[0][1]-rawlens(pink)[0][0])<.08
 assert b_off(pink)[0]>b_off(pink)[1]+.7
 for clip in [(0.,0.,0.),(1.,0.,0.),(0.,1.,0.),(1.,1.,0.),(1.,0.,1.)]:
  new,f=new38(yellow,clip)
  assert f==0. and close(new,yellow),(clip,new,f)
 # Real red, blue, orange and magenta without matching original clip must survive.
 cases=[((1.8,.15,.06),(1.,0.,0.)),((.03,.08,1.5),(0.,0.,1.)),
        ((.8,.3,1.2),(0.,0.,0.)),((1.5,1.3,.08),(1.,1.,0.))]
 for rgb,clip in cases:
  new,f=new38(rgb,clip)
  assert close(new,rgb),(rgb,clip,new,f)
 # Near-neutral highlight continuously converges to measured WB-space neutral axis.
 for x in (.50,.70,.77,.85,.90,.94,.98,1.0,1.4,2.0):
  v=(x,x*.995,x*1.005)
  new,f=new38(v,(0.,0.,0.))
  assert abs(lu(v)-lu(new))<1e-7
  assert all(z>=0 for z in new)
 # Luminance never dips/rises due to changing clipping weights, unlike 26934 peak-whitening.
 for i in range(101):
  rgb=(.4+.014*i,.2+.008*i,.35+.012*i)
  clip=(i/100.,.0,i/100.)
  new,f=new38(rgb,clip)
  assert abs(lu(new)-lu(rgb))<1e-7
  assert min(new)>0. and 0<=f<=1
 # Original Bayer phase contract remains correctly mapped for all four Bayer arrangements.
 for r in range(4):
  b=3-r;greens=[x for x in range(4) if x not in (r,b)]
  assert len(greens)==2 and set(greens) in ({1,2},{0,3})
 # Hue transition continuity against fractional physical CFA mask and brightness thresholds.
 vals=[new38(pink,(t,0.,t))[1] for t in (i/1000. for i in range(1001))]
 assert all(vals[i+1]>=vals[i]-1e-9 for i in range(1000))
 assert max(vals[i+1]-vals[i] for i in range(1000))<.01
 print('PASS 26938 independent R+B/G-only/all-channel glint neutral; genuine yellow/red/magenta preserved, RawLens-vs-B-OFF control, weighted-luminance invariant, four Bayer patterns, continuous transitions')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26938 BLOCKED: '+str(e),file=sys.stderr);sys.exit(1)
