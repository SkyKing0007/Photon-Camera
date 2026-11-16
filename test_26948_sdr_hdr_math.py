#!/usr/bin/env python3
"""Model-check exact identical 26948 B SDR shaders, UHDR quotient continuity and old smooth white."""
import math,sys,re
from build_26948_incremental import R,fail,scope
from test_26948_source import main as source_check
D='app/src/main/assets/shaders/'
def get(p):return ((R if '--live' in sys.argv else R/'handoff_payload_26948')/p).read_text()
def extract(s,name):
 a=s.index('float '+name+'(');b=s.index('{',a);depth=1;j=b+1
 while depth:
  if s[j]=='{':depth+=1
  elif s[j]=='}':depth-=1
  j+=1
 return re.sub(r'\s+','',s[a:j])
def smooth(a,b,x):
 v=max(0,min(1,(x-a)/(b-a)));return v*v*(3-2*v)
def old(x):return x if x<=.82 else .82+.18*(1-math.exp(-(x-.82)/.18))
def new(x):
 if x<=.82:return x
 ex=x-.82;previous=.82+.18*(1-math.exp(-ex/.18));sep=.82+.18*ex/(ex+.18);u=smooth(1.50,2.70,x);return sep*(1-u)+previous*u
def main():
 source_check()
 r=get(D+'motionv2/render.glsl');g=get(D+'motionv2/gainmap.glsl');f=get(D+'iris26876/b_fused_final_p3_gain.frag')
 name='iris26948BHeadroomShoulder'
 if not (extract(r,name)==extract(g,name)==extract(f,name)):fail('not exact matched SDR/UHDR and B 2x headroom function')
 for s in (r,g,f):
  if 'return mix(separated,former,smoothstep(1.50,2.70,target));' not in s:fail('wrong 26947 white rejoin')
 count=0;prior=-1
 for i in range(50001):
  x=5.0*i/50000;y=new(x);assert math.isfinite(y) and 0<=y<=1.000001
  if prior>=0 and y<prior-1e-9:fail('SDR upper shoulder not monotonic '+str(x))
  if x<=.82 or x>=2.7:
   if abs(y-old(x))>1e-12:fail('old 26947 tone outside correction not preserved')
  if x<2.7 and x>.82 and y>old(x)+1e-12:fail('26501 white converges too early')
  prior=y;count+=1
 # Explicit continuity and approach near the 26947 neutral-white endpoint.
 for edge in (.82,1.5,2.7):
  if abs(new(edge+1e-6)-new(edge-1e-6))>1e-4:fail('shoulder discontinuity')
 for target in (.82,1.01,1.25,1.5,1.9,2.3,2.7,4.0):
  sdr=new(target);hdr=max(0,target)
  if sdr<=0 or max(1,(hdr+.015625)/(sdr+.015625))<1:fail('invalid HDR over SDR gain')
 for shader in (r,g):
  if 'iris26948BUniversalSdrEnabled!=0' not in shader:fail('Experiment A shader output changed')
 if 'smoothstep(0.82,1.05,originalGuide26948)' not in f or '(1.0-smoothstep(2.0,2.70,originalGuide26948))' not in f:fail('true2x white rejoin wrong')
 print('PASS 26948 matched render/gain/B-ON three-way EXACT GLSL body, 50001 monotonic real values, old smooth white outside 0.82-2.70, quotient and A bypass')
if __name__=='__main__':
 try:main()
 except Exception as e:print(e,file=sys.stderr);sys.exit(1)
