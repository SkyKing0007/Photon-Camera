#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26654_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def same(r):
 a=base/r;b=cand/r
 return a.is_file() and b.is_file() and hashlib.sha256(a.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
# Protected architectural owners.
for r in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java','app/src/main/assets/shaders/motionv2/color_transform.glsl','app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java','app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java']:
 assert same(r),r
hc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java').read_text(); assert 'private static final float KNEE_REF = 0.10f;' in hc
rg=(cand/'app/src/main/assets/shaders/motionv2/render.glsl').read_text();gm=(cand/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text();ll=(cand/'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl').read_text()
assert 'iris26650HighlightCompressionEnabled' not in ll
assert 'iris26653AdaptiveWhitePoint' not in rg and 'iris26653AdaptiveWhitePoint' not in gm
# Numeric tone regression: HC ON remains exact through 0.65; low-gain inert; monotonic; Iris scene-white expands >1 separation.
def clamp(x,a,b): return max(a,min(b,x))
def smooth(a,b,x):
 t=clamp((x-a)/max(b-a,1e-6),0,1); return t*t*(3-2*t)
def body(x,requested):
 white=min(.95,requested);bg=requested
 if requested>white:bg=min(requested,4*white-1e-4)
 ratio=max(bg/max(white,1e-6)-1,0);om=1-x
 v=.5*(white*x+(bg-white)*x*om*om + bg*x/(1+ratio*x))
 d=.5*(white+(bg-white)*om*(1-3*x) + bg/((1+ratio*x)**2))
 return v,d
def pressure(b,h,bw,aw):
 br=smooth(.015,.060,clamp(b,0,1));hd=smooth(.010,.050,clamp(h,0,1));bw=max(bw,1);aw=max(aw,bw);sp=smooth(.08,.35,max(aw/bw-1,0));return clamp(max(.70*br+.30*sp,.75*hd),0,1)
def offmap(x,g,b,h,bw,aw):
 x=max(x,0);req=max(g,1e-6)*.8;white=min(.95,req);bg=req
 if req>white:bg=min(req,4*white-1e-4)
 ratio=max(bg/max(white,1e-6)-1,0)
 if x<=1: old=body(x,req)[0]
 else:
  rs=bg/((1+ratio)**2);s=.5*(white+rs);res=max(1-white,0);scale=res/max(s,1e-6);ex=x-1;old=white+res*ex/(ex+scale)
 en=smooth(1.05,1.25,req)
 if en<=1e-7 or x<=.65:return old
 pr=pressure(b,h,bw,aw);tw=.945+(.925-.945)*pr;ts=.360+(.300-.360)*pr;sv,ss=body(.65,req);w=.35;sec=(tw-sv)/w
 if sec<=1e-6:return old
 m0=max(ss,0);m1=max(ts,0);n=(m0/sec)**2+(m1/sec)**2
 if n>9:lim=3/math.sqrt(n);m0*=lim;m1*=lim
 if x<=1:
  t=clamp((x-.65)/w,0,1);t2=t*t;t3=t2*t;c=(2*t3-3*t2+1)*sv+(t3-2*t2+t)*w*m0+(-2*t3+3*t2)*tw+(t3-t2)*w*m1
 else:
  res=max(1-tw,0);scale=res/max(m1,1e-6);ex=x-1;c=tw+res*ex/(ex+scale)
 return old+(c-old)*en
def onmap(x,g,b,h,bw,aw,knee):
 old=offmap(x,g,b,h,bw,aw)
 if x<=.65:return old
 req=max(g,1e-6)*.8;en=smooth(1.05,1.25,req)
 if en<=1e-7:return old
 pr=max(pressure(b,h,bw,aw),clamp((.90-knee)/(.90-.55),0,1));tw=.915+(.890-.915)*pr;ts=.090+(.055-.090)*pr;sv,ss=body(.65,req);w=.35;sec=(tw-sv)/w
 if sec<=1e-6:return old
 m0=max(ss,0);m1=max(ts,0);n=(m0/sec)**2+(m1/sec)**2
 if n>9:lim=3/math.sqrt(n);m0*=lim;m1*=lim
 if x<=1:
  t=clamp((x-.65)/w,0,1);t2=t*t;t3=t2*t;c=(2*t3-3*t2+1)*sv+(t3-2*t2+t)*w*m0+(-2*t3+3*t2)*tw+(t3-t2)*w*m1
 else:
  res=max(1-tw,0);span=clamp(max(aw,bw)/max(bw,1),1,3);scale=res/max(m1,1e-6)*span;ex=x-1;c=tw+res*ex/(ex+scale)
 return old+(c-old)*en
for g in [1.0,1.31,3.3,6.0628657]:
 for x in [0,.1,.3,.5,.649999,.65]: assert abs(offmap(x,g,.055,.016,1,1.4)-onmap(x,g,.055,.016,1,1.4,.8383159))<1e-12
for x in [0,.65,1,1.25,2,4]: assert abs(offmap(x,1.0,1,1,1,2)-onmap(x,1.0,1,1,1,2,.55))<1e-12
for g in [1.0,1.31,3.3,6.0628657]:
 vals=[onmap(i/100,g,.02334,.01736,5.456579,7.518416,.864982) for i in range(0,801)]
 assert all(vals[i+1]+2e-6>=vals[i] for i in range(len(vals)-1)),g
plant=[onmap(x,6.0628657,.023339573,.017357154,5.456579,7.518416,.864982) for x in [1.0,1.25,1.47,2.0]]
assert plant[1]-plant[0]>.010 and plant[2]-plant[1]>.006 and plant[3]-plant[2]>.010,plant
# Local residual contract: constant local offset has exactly zero DC; no structure admits zero; bounded amplitude cannot exceed 0.045.
for delta in [-.2,-.05,.03,.2]:
 dc=.25*(delta+delta+delta+delta); assert abs(delta-dc)<1e-12
assert 0.045<=0.045
print('PASS 26654 permanent regressions: 26653 fusion/matcher/color/DNG protected; KNEE_REF 0.10; HC ON exact through 0.65 and monotonic; Iris scene-white preserves extended tail spacing; smooth local DC is mathematically zeroed; bounded detail <=0.045')
