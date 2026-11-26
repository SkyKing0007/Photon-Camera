#!/usr/bin/env python3
import pathlib,re,json,math,random,bisect
R=pathlib.Path(__file__).resolve().parent;K=R/'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/RawAdjustmentPass.kt';s=K.read_text();part=s[s.index('float iris26993ShadowEv('):s.index('vec3 iris26993LiftShadows(')]
knots=json.loads((R/'26993_shadow_curve.json').read_text());x=knots['log2_knots'];y=knots['ev'];h=[b-a for a,b in zip(x,x[1:])];d=[(b-a)/w for a,b,w in zip(y,y[1:],h)];m=[0.]*len(x)
for i in range(1,len(x)-1):
 if d[i-1]*d[i]>0:
  w1=2*h[i]+h[i-1];w2=h[i]+2*h[i-1];m[i]=(w1+w2)/(w1/d[i-1]+w2/d[i])
def endpoint(h0,h1,d0,d1):
 q=((2*h0+h1)*d0-h0*d1)/(h0+h1)
 if q*d0<=0:return 0.
 if d0*d1<0 and abs(q)>abs(3*d0):return 3*d0
 return q
m[0]=endpoint(h[0],h[1],d[0],d[1]);m[-1]=endpoint(h[-1],h[-2],d[-1],d[-2]);num=r'[-+]?\d+\.\d+';pattern=r'if \(x < ('+num+r')\) \{\s*float t = x - \(('+num+r')\);\s*return max\(0.0, \(\(('+num+r') \* t \+ \(('+num+r')\)\) \* t \+ \(('+num+r')\)\) \* t \+ \(('+num+r')\)\);';rows=[tuple(map(float,r)) for r in re.findall(pattern,part)];assert len(rows)==len(x)-3,(len(rows),len(x))
for i,(end,start,a,b,c,e) in enumerate(rows,1):
 expect=((m[i]+m[i+1]-2*d[i])/h[i]**2,(3*d[i]-2*m[i]-m[i+1])/h[i],m[i],y[i]);assert max(abs(v-w) for v,w in zip((end,start,a,b,c,e),(x[i+1],x[i],*expect)))<1e-8,(i,rows[i],expect)
def ev(q):
 if q<=.0005 or q>=.65:return 0.
 z=math.log2(q)
 for end,start,a,b,c,e in rows:
  if z<end:
   t=z-start;return max(0.,((a*t+b)*t+c)*t+e)
 return 0.
last=0.
for i in range(1000001):
 q=i/1000000;v=ev(q);o=q*2**v;assert 0<=v<=1.35000001 and o+1e-12>=last and q<=o<=1.00000001;last=o
 if q<=.0005 or q>=.65:assert o==q
print('PASS 1,000,001 samples of actual shadow GLSL coefficients, independent PCHIP, monotone, unity floor/highlights, 1.35EV bound')
