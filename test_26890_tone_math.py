#!/usr/bin/env python3
"""Pure Python execution of exact editor PCHIP and actual 26889 lower-body equation.
No SciPy dependency in GitHub Actions; no claim of real GPU compilation here.
"""
import json,math
from pathlib import Path
D=json.loads((Path(__file__).resolve().parent/'26890_USER_EDITOR_POINTS_EXACT.json').read_text())
def pchip(pts):
 x=[t[0] for t in pts];y=[t[1] for t in pts];n=len(x)
 h=[x[i+1]-x[i] for i in range(n-1)];d=[(y[i+1]-y[i])/h[i] for i in range(n-1)];m=[0.]*n
 def end(h0,h1,d0,d1):
  v=((2*h0+h1)*d0-h0*d1)/(h0+h1)
  if (v>0)-(v<0)!=(d0>0)-(d0<0):return 0.
  if (d0>0)-(d0<0)!=(d1>0)-(d1<0) and abs(v)>3*abs(d0):return 3*d0
  return v
 for i in range(1,n-1):
  if d[i-1]*d[i]<=0:m[i]=0.
  else:
   a=2*h[i]+h[i-1];b=h[i]+2*h[i-1];m[i]=(a+b)/(a/d[i-1]+b/d[i])
 m[0]=end(h[0],h[1],d[0],d[1]);m[-1]=end(h[-1],h[-2],d[-1],d[-2])
 def f(t):
  if t<=x[0]:return y[0]
  if t>=x[-1]:return y[-1]
  i=0
  while t>x[i+1]:i+=1
  z=(t-x[i])/h[i];z2=z*z;z3=z2*z
  return (2*z3-3*z2+1)*y[i]+(z3-2*z2+z)*h[i]*m[i]+(-2*z3+3*z2)*y[i+1]+(z3-z2)*h[i]*m[i+1]
 return f
E={k:pchip(v) for k,v in D['user_exported'].items()}
O={k:pchip(v) for k,v in D['editor_defaults'].items()}
assert D['editor_defaults']['compress']==D['user_exported']['compress']
def smooth(t):
 t=max(0.,min(1.,t));return t*t*(3-2*t)
def legacy(x,g):
 req=max(g,1e-6)*.8;white=min(.95,req);body=req
 if req>white:body=min(req,4*white-1e-4)
 ratio=max(body/max(white,1e-6)-1,0)
 return .5*(white*x+(body-white)*x*(1-x)**2+body*x/(1+ratio*x))
def toe(x,g,compressed=False,enabled=True):
 old=legacy(x,g)
 if compressed or not enabled or x<=0 or x>=.25:return old
 r0=max(0.,min(1.,E['darker'](x)/max(O['darker'](x),1e-8)))
 r1=max(0.,min(1.,E['brighter'](x)/max(O['brighter'](x),1e-8)))
 t=smooth((g-1.22)/.28)
 ratio=(1-t)*r0+t*r1
 ratio=ratio+(1-ratio)*smooth((x-.2)/.05)
 return old*ratio
for gain in (.8,1.,1.22,1.35,1.5,1.8,2.5,4.):
 previous=0.
 for j in range(1,10002):
  x=.2501*j/10001
  y=toe(x,gain)
  assert math.isfinite(y) and y>=0,(gain,x,y)
  assert y>=previous-3e-6,(gain,x,previous,y)
  assert y<=legacy(x,gain)+1e-10
  previous=y
 for x in (.25,.30,.65,1.):
  if x<1:
   assert toe(x,gain)==legacy(x,gain)
 for x in (.001,.05,.1,.2,.24):
  assert toe(x,gain,compressed=True)==legacy(x,gain)
  assert toe(x,gain,enabled=False)==legacy(x,gain)
print('PASS actual 26889 lower-body equation, exact exported HTML-PCHIP interpolation, 80k monotone samples, disabled/compressed/>=0.25 identity')
