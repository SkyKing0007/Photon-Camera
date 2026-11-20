#!/usr/bin/env python3
"""A 22-knot monotone Option2 reference; B mirrored tone and native saturation route."""
import pathlib,sys,re,math
R=pathlib.Path(__file__).resolve().parent;P=R if '--live' in sys.argv else R/'handoff_payload_26967'
S=(P/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
G=(P/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
J=(P/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
x=[0,8,16,24,32,40,48,56,64,72,80,90,100,110,120,140,160,180,200,220,240,255]
y=[0,6.5,11.6,18.5,26.3,34.8,45,56.1,68.8,83.2,98,116.6,135,154,171,193.4,208.6,220.6,232,241,250,255]
t=S[S.index('float iris26967Option2Encoded('):S.index('/* IRIS_26632_SMOOTHER_UPPER_TONE')]
vals=[tuple(map(float,z)) for z in re.findall(r'x0=([0-9.]+);dx=([0-9.]+);y0=([0-9.]+);y1=([0-9.]+);m0=([0-9.]+);m1=([0-9.]+);',t)]
assert len(vals)==21 and t.count('if(x<')==20 and t.count('else if(x<')==19
assert all(xx==x[i] and dx==x[i+1]-x[i] and a==y[i] and b==y[i+1] and m0>=0 and m1>=0 for i,(xx,dx,a,b,m0,m1) in enumerate(vals))
def option2(v):
 for xx,dx,a,b,m0,m1 in vals:
  if v<=xx+dx:
   u=max(0,min(1,(v-xx)/dx));u2=u*u;u3=u2*u
   return (2*u3-3*u2+1)*a+(u3-2*u2+u)*dx*m0+(-2*u3+3*u2)*b+(u3-u2)*dx*m1
 return 255.
assert all(abs(option2(z)-w)<1e-5 for z,w in zip(x,y))
assert abs(option2(128)-181.13)<.03
assert all(option2(i/16+1/16)+1e-7>=option2(i/16) for i in range(16*255))
assert S.index('linearSrgb=iris26638UserSaturation(')<S.index('iris26967EncodedSdr=clamp(srgbEncode(linearSrgb)')
assert S.index('iris26967EncodedSdr=clamp(srgbEncode(linearSrgb)')<S.index('if(iris26967AOption2Enabled!=0)')
assert 'iris26967AOption2Enabled' not in G
f=lambda s:s[s.index('float iris26906BVisualTone(float y) {'):s.index('\n}',s.index('float iris26906BVisualTone(float y) {'))+2]
assert f(S)==f(G),'B SDR tone does not mirror UHDR SDR model'
assert 'float toe=x*(1.0-0.495*toeGate);' in f(S)
assert 'float mid=0.25*(x-0.230)*clamp(midLow*midHigh,0.0,1.0);' in f(S)
assert 'return selectedPhotoBOff ? 0.23f' in J
assert abs(.495/.330-1.5)<1e-8 and abs(.25/.15-5/3)<1e-8
def smooth(a,b,v):
 t=max(0,min(1,(v-a)/(b-a)));return t*t*(3-2*t)
def bcurve(v):
 if v>=.7:return v
 return max(v*(1-.495*(1-smooth(.015,.145,v)))+.25*(v-.23)*smooth(.13,.19,v)*(1-smooth(.5,.7,v)),0.)
for i in range(7000):assert bcurve((i+1)/10000)+1e-9>=bcurve(i/10000),(i,bcurve(i/10000))
assert all(bcurve(z)==z for z in (.7,.75,.85,1.))
print('PASS 26967 Option2 P3 22-knot monotone encoded tone; B OFF identical SDR/UHDR guide 30% toe 25% mid, 1.00 sat')
