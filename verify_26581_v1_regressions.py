#!/usr/bin/env python3
import math,sys,hashlib
from pathlib import Path

def clamp(x,a=0.,b=1.): return min(b,max(a,x))
def smooth(a,b,x):
    if b==a:return 1. if x>=b else 0.
    t=clamp((x-a)/(b-a));return t*t*(3-2*t)
def lum(v): return .25*v[0]+.5*v[1]+.25*v[2]
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def mul(a,s):return tuple(x*s for x in a)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def length(a):return math.sqrt(dot(a,a))
def hue(a,b):return clamp(dot(a,b)/max(length(a)*length(b),1e-6),-1,1)
def rgb(y,c=(0,0,0)):return tuple(clamp(y+x) for x in c)

def gap_model(px):
    c=px[(0,0)]; cy=lum(c); cs=max(cy,.060); cn=mul(sub(c,(cy,)*3),1/cs)
    axes=[(1,0),(0,1),(1,1),(1,-1)]
    W=0.;S=(0.,0.,0.);best=0.
    for dx,dy in axes:
      na=px[(dx,dy)];nb=px[(-dx,-dy)];fa=px[(2*dx,2*dy)];fb=px[(-2*dx,-2*dy)]
      nay,nby,fay,fby=map(lum,(na,nb,fa,fb))
      nda=smooth(.18,.48,(cy-nay)/max(cy,nay,.060));ndb=smooth(.18,.48,(cy-nby)/max(cy,nby,.060))
      fsa=1-smooth(.09,.27,abs(fay-cy)/max(fay,cy,.060));fsb=1-smooth(.09,.27,abs(fby-cy)/max(fby,cy,.060))
      fca=mul(sub(fa,(fay,)*3),1/max(fay,.060));fcb=mul(sub(fb,(fby,)*3),1/max(fby,.060))
      ma,mb=length(fca),length(fcb)
      neutral=(1-smooth(.035,.090,ma))*(1-smooth(.035,.090,mb))
      h=smooth(.72,.92,hue(fca,fcb)); agree=max(neutral,h)
      pair=nda*ndb*fsa*fsb*agree;best=max(best,pair);W+=pair;S=add(S,mul(add(fca,fcb),.5*pair))
    if W<=1e-6:return dict(pair=best,ownership=0,target=cn)
    target=mul(S,1/W);dis=smooth(.045,.150,length(sub(cn,target)));own=smooth(.42,.88,best)*dis
    return dict(pair=best,ownership=own,target=target,center=cn)

sky=rgb(.72,(-.08,-.02,.14)); leaf=rgb(.26,(-.06,.07,-.04)); wrong=rgb(.72,(-.01,.04,-.03))
px={(x,y):sky for y in range(-2,3) for x in range(-2,3)}
px[(0,0)]=wrong;px[(1,0)]=leaf;px[(-1,0)]=leaf
r=gap_model(px);assert r['pair']>.95 and r['ownership']>.90,r
before=length(sub(r['center'],r['target']));after=before*(1-.88*r['ownership']);assert after<before*.25,(before,after,r)
print('PASS paired dark-foreground / blue-background gap gets strong background owner')
# tiny colored object: far field is dark, so it cannot pose as a background gap
obj=rgb(.70,(.20,.02,-.18)); dark=rgb(.20)
px={(x,y):dark for y in range(-2,3) for x in range(-2,3)};px[(0,0)]=obj
r=gap_model(px);assert r['pair']<.01 and r['ownership']<.01,r
print('PASS isolated bright colored micro-object cannot satisfy gap-background proof')
# ordinary sky patch: no opposing foreground edges -> no repair
px={(x,y):sky for y in range(-2,3) for x in range(-2,3)};px[(0,0)]=sky
r=gap_model(px);assert r['ownership']<.01,r
print('PASS ordinary background surface is pass-through')

def detail_model(ys, idx, materialBoundary, confidence=1.0, guideY=.70, guideBlockY=.50):
    directY=ys[idx];low=sum(ys)/4;den=max(low,.015);d=[(y-low)/den for y in ys];ma=max(abs(x) for x in d);ss=min(1,.42/ma) if ma>1e-6 else 0;block=((directY-low)/den)*ss
    rel=[abs(y-directY)/max(y,directY,.030) for y in ys];mw=[1-smooth(0,1,(x-.10)/.34) for x in rel];W=sum(mw);mean=sum(y*w for y,w in zip(ys,mw))/max(W,1e-6);md=max(mean,.015);dev=[(y-mean)/md for y in ys];mma=max(abs(x)*(1 if w>=.20 else 0) for x,w in zip(dev,mw));mss=min(1,.42/mma) if mma>1e-6 else 0;mat=((directY-mean)/md)*mss;support=smooth(0,1,(W-1.15)/1.10)
    detail=block*(1-materialBoundary)+mat*materialBoundary;conf=confidence*((1-materialBoundary)+support*materialBoundary);scale=guideBlockY*(1-materialBoundary)+guideY*materialBoundary;target=max(guideY+scale*detail*conf,0);factor=clamp(target/guideY,.68,1.47)
    vals=[y for y,w in zip(ys,mw) if w>.35]+[directY];rr=(max(vals)-min(vals))/max(mean,.015);exc=clamp(.045+.70*rr,.060,.30);env=clamp(factor,1-exc,1+exc);factor=factor*(1-materialBoundary)+env*materialBoundary
    return dict(factor=factor,W=W,mean=mean,range=rr,support=support,block=block,mat=mat)
# mixed dark leaf / uniform bright sky. sky side must not receive compensating >~6% bright lobe.
ys=[.22,.72,.22,.72]
r=detail_model(ys,1,1.0);assert r['factor']<=1.061,r
print('PASS mixed-material uniform sky side is bounded to halo-free local envelope')
# leaf side likewise cannot be driven by sky compensation.
r2=detail_model(ys,0,1.0);assert r2['factor']>=.939,r2
print('PASS mixed-material leaf side avoids opposite-side compensating dark lobe')
# textured same-material foliage keeps appreciable SR modulation.
ys=[.30,.38,.34,.42]
r=detail_model(ys,3,1.0);assert r['factor']>1.08,r
print('PASS textured same-material foliage retains meaningful direct-CFA detail')
# one isolated material subpixel gets insufficient support and cannot fabricate detail.
ys=[.20,.75,.76,.77]
r=detail_model(ys,0,1.0);assert r['support']<.05 and abs(r['factor']-1)<.02,r
print('PASS single-subpixel material side cannot fabricate SR residual')

if len(sys.argv)==2:
 root=Path(sys.argv[1]);v=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text();s=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();cpp=root/'app/src/main/cpp/motionv2_jpeg444_jni.cpp'
 for t in ['IRIS_26581_OCCLUSION_GAP_BACKGROUND_OWNER','IRIS_26581_GAP_BACKGROUND_CHROMA_RESTORE','gapPairEvidence','gapOwnership']:assert t in v,t
 for t in ['IRIS_26581_DECISIVE_CROSS_EDGE_CHROMA_VETO','IRIS_26581_MATERIAL_SEPARATED_SR_DETAIL_ENVELOPE','materialBoundary','materialSupportGate','edgeExcursion']:assert t in s,t
 assert hashlib.sha256(cpp.read_bytes()).hexdigest()=='d73cd24452280958f089e9124545a81461939e8fa0c9c95272b2825942e4b43d'
 print('PASS device-proven 26579/26580 GPU publication native bytes frozen')
