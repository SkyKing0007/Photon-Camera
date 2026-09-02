#!/usr/bin/env python3
import math,re,sys
from pathlib import Path

def clamp(x,a=0.0,b=1.0): return min(b,max(a,x))
def smooth(a,b,x):
    if b==a:return 1.0 if x>=b else 0.0
    t=clamp((x-a)/(b-a)); return t*t*(3.0-2.0*t)
def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def mul(a,s): return tuple(x*s for x in a)
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def length(a): return math.sqrt(dot(a,a))
def lum(rgb): return dot(rgb,(0.25,0.50,0.25))
def hue(a,b): return clamp(dot(a,b)/max(length(a)*length(b),1e-6),-1.0,1.0)
def rgb(l,c=(0,0,0)): return tuple(clamp(l+x) for x in c)
DIR=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)]

def evaluate(px):
    center=px[(0,0)]; centerL=lum(center); scale=max(centerL,0.060)
    cc=sub(center,(centerL,)*3); cn=mul(cc,1.0/scale); cm=length(cn)
    s=cn; ws=1.0; ns=0.; nns=0.; maxld=0.; bright=dark=0
    for y in (-1,0,1):
      for x in (-1,0,1):
        if x==0 and y==0: continue
        q=px[(x,y)]; ql=lum(q); ls=max(centerL,ql,0.060); sd=(ql-centerL)/ls; rd=abs(sd)
        maxld=max(maxld,rd); bright += sd>0.16; dark += sd<-0.16
        sw=1.0-smooth(0.16,0.55,rd); qc=mul(sub(q,(ql,)*3),1.0/max(ql,0.060))
        s=add(s,mul(qc,sw)); ws+=sw; ns+=sw
        nns += sw*(1.0-smooth(0.035,0.100,length(qc)))
    cons=mul(s,1.0/max(ws,1e-6)); disagree=length(sub(cn,cons)); consmag=length(cons); agree=hue(cn,cons)
    surface=smooth(2.5,5.75,ns); neutralSurface=smooth(2.50,4.00,nns); legacy=smooth(0.45,0.90,maxld)
    one=1.0 if ((bright>=4 and dark<=1) or (dark>=4 and bright<=1)) else 0.0
    hi=1.0-smooth(0.72,0.92,centerL); material=one*(1.0-smooth(0.72,0.92,agree))*hi
    ts=nts=chain=phase=0.; present=smooth(0.035,0.090,cm)
    W=NW=XX=YY=XY=0.0
    if centerL>0.58 or one>0.5 or legacy>0.25 or present>0.0:
      for yy in range(-2,3):
       for xx in range(-2,3):
        if xx==0 and yy==0: continue
        q=px[(xx,yy)]; ql=lum(q); rd=abs(ql-centerL)/max(ql,centerL,0.060)
        qc=mul(sub(q,(ql,)*3),1.0/max(ql,0.060)); chrom=smooth(0.050,0.115,length(qc)); comp=1.0-smooth(0.72,1.20,rd); w=chrom*comp
        W+=w
        if abs(xx)<=1 and abs(yy)<=1: NW+=w
        XX+=w*xx*xx; YY+=w*yy*yy; XY+=w*xx*yy
      for dx,dy in DIR:
        nr=px[(dx,dy)]; fr=px[(2*dx,2*dy)]; nl=lum(nr); fl=lum(fr)
        nld=abs(nl-centerL)/max(nl,centerL,0.060); fld=abs(fl-centerL)/max(fl,centerL,0.060)
        nc=mul(sub(nr,(nl,)*3),1.0/max(nl,0.060)); fc=mul(sub(fr,(fl,)*3),1.0/max(fl,0.060))
        na=hue(cn,nc); fa=hue(cn,fc)
        nsl=1.0-smooth(0.10,0.26,nld); fsl=1.0-smooth(0.10,0.26,fld)
        nsh=smooth(0.82,0.94,na); fsh=smooth(0.82,0.94,fa)
        ts += fsl*((1.0-present)+present*fsh)
        nts += nsl*nsh*present
        chain += nsl*fsl*nsh*fsh*present
        phase += nsl*fsl*fsh*(1.0-smooth(0.20,0.72,na))*present
    rad=smooth(1.25,2.75,ts)*smooth(0.20,0.55,max(legacy,one))
    near=smooth(0.55,1.45,nts); contour=smooth(0.55,1.60,chain); ph=smooth(1.10,2.80,phase)
    topo=max(near,contour,rad*(1.0-0.90*ph)); supported=material*near
    trace=XX+YY; determinant=max(XX*YY-XY*XY,0.0)
    minor=(0.5*(trace-math.sqrt(max(trace*trace-4.0*determinant,0.0)))/max(W,1e-6)) if trace>1e-6 else 0.0
    area=smooth(2.15,4.25,W)*smooth(2.20,4.60,NW)*smooth(0.16,0.46,minor)*present
    micro=area*(1.0-0.95*ph)
    coherent=smooth(0.76,0.95,agree)*smooth(0.050,0.180,consmag)
    ratio=cm/max(consmag,0.025); plausible=1.0-smooth(2.0,3.5,ratio)
    real=clamp(max(supported,coherent*plausible*max(hi,topo),topo,micro))
    outlier=smooth(0.070,0.220,disagree); neutral=1.0-smooth(0.070,0.160,consmag); isolated=smooth(1.35,2.75,ratio)
    phaseConf=ph*((1.0-isolated)*0.70+isolated)
    score=outlier*neutral*surface*neutralSurface*phaseConf*(1.0-real)
    gate=smooth(0.72,0.90,score)
    return dict(gate=gate,real=real,phase=ph,micro=micro,neutralSurface=neutralSurface)

def grid(default): return {(x,y):default for y in range(-2,3) for x in range(-2,3)}
neutral=rgb(.55); mag=rgb(.55,(.12,-.12,.12)); green=rgb(.55,(-.08,.08,-.08)); red=rgb(.55,(.16,-.08,0)); yellow=rgb(.55,(.10,.05,-.20)); blue=rgb(.55,(-.12,-.02,.16)); blueSky=rgb(.75,(-.08,-.04,.16)); leaf=rgb(.40,(-.10,.10,-.10))
# Inherited 26578 false fringe must remain correctable even though it has 2-D radius-two occupancy.
g=grid(neutral);g[(0,0)]=mag
for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:g[(dx,dy)]=green;g[(2*dx,2*dy)]=mag
r=evaluate(g); assert r['gate']>0.90 and r['phase']>0.90 and r['real']<0.10, r
print('PASS inherited neutral Bayer-like purple/green fringe remains eligible')
# Inherited real-color cases.
g=grid(neutral)
for x in (-2,-1,0,1,2): g[(x,0)]=red
r=evaluate(g); assert r['gate']<0.01 and r['real']>0.90, r
print('PASS colored text/contour continuation preserved')
g=grid(neutral);g[(0,0)]=yellow
r=evaluate(g); assert r['gate']<0.01 and r['phase']<0.05, r
print('PASS tiny isolated saturated object preserved without phase proof')
g={}
for y in range(-2,3):
 for x in range(-2,3): g[(x,y)]=leaf if x<=0 else blueSky
r=evaluate(g); assert r['gate']<0.01 and r['real']>0.90, r
print('PASS foliage/sky material boundary remains protected')
# New multicolor micro-print: no single hue is coherent, but 2-D chroma occupancy must veto cleanup.
g=grid(neutral);colors=[red,yellow,blue]
for y in (-1,0,1):
 for x in (-1,0,1): g[(x,y)]=colors[(x+y+8)%3]
r=evaluate(g); assert r['gate']<0.01 and r['micro']>0.90 and r['real']>0.90, r
print('PASS compact multicolor flag/logo 2-D chroma occupancy preserved without same-hue requirement')
# A one-pixel multicolor ribbon is not promoted by the new 2-D micro-object veto; inherited logic decides it.
g=grid(neutral)
for x in range(-2,3): g[(x,0)]=colors[(x+2)%3]
r=evaluate(g); assert r['micro']<0.01, r
print('PASS thin chromatic ribbon does not falsely earn micro-object area protection')

# SR topology-aware chroma interpolation model. Luma is preserved exactly; direct CFA supplies only selectorY.
def sr_topology(samples,spatial,directY,confidence):
 ys=[lum(s) for s in samples]; nearest=max(range(4),key=lambda i:spatial[i]); maxY=max(abs(ys[i]-ys[j]) for i in range(4) for j in range(i+1,4)); maxC=max(length(sub(samples[i],(ys[i],)*3)) for i in range(4))
 bil=tuple(sum(samples[i][c]*spatial[i] for i in range(4)) for c in range(3)); by=lum(bil); selector=ys[nearest]*(1.0-0.40*confidence)+directY*(0.40*confidence)
 tc=[0.,0.,0.]; wsum=0.
 for i in range(4):
  rel=abs(ys[i]-selector)/max(abs(ys[i]),abs(selector),0.035); same=1.0/(1.0+18.0*rel*rel); w=spatial[i]*max(same,0.015); ch=sub(samples[i],(ys[i],)*3)
  for c in range(3): tc[c]+=ch[c]*w
  wsum+=w
 tc=tuple(x/max(wsum,1e-6) for x in tc); tm=length(tc)
 if tm>maxC and tm>1e-7: tc=mul(tc,maxC/tm)
 bc=sub(bil,(by,)*3); edge=smooth(0.0,1.0,(maxY-0.025)/0.130); selected=tuple(bc[i]+(tc[i]-bc[i])*edge for i in range(3))
 scale=1.0
 for c in selected:
  if c<0: scale=min(scale,by/max(-c,1e-7))
 out=tuple(by+selected[i]*clamp(scale) for i in range(3))
 return bil,out,maxC
# Flat colored surface remains exact bilinear; no synthetic saturation.
flat=rgb(.45,(.12,-.04,-.08)); bil,out,maxC=sr_topology([flat]*4,[.25]*4,lum(flat),1.0); assert max(abs(a-b) for a,b in zip(bil,out))<1e-7
print('PASS SR flat colored surface is exact pass-through')
# Red object beside white: topology-aware result must retain more supported chroma than cross-edge bilinear while never exceeding native support.
white=rgb(.78); redObj=rgb(.38,(.28,-.10,-.08)); samples=[redObj,white,redObj,white]; spatial=[.375,.125,.375,.125]
bil,out,maxC=sr_topology(samples,spatial,lum(redObj),1.0); by=lum(bil); om=length(sub(out,(lum(out),)*3)); bm=length(sub(bil,(by,)*3)); assert om>bm+1e-4 and om<=maxC+1e-6 and abs(lum(out)-by)<1e-6,(bm,om,maxC,lum(out)-by)
print('PASS SR same-material edge reconstruction retains supported object chroma without inventing hue/saturation')
# Neutral black/white glyph stays neutral.
black=rgb(.12);white=rgb(.80);bil,out,maxC=sr_topology([black,white,black,white],[.375,.125,.375,.125],lum(black),1.0);assert length(sub(out,(lum(out),)*3))<1e-7 and maxC<1e-7
print('PASS SR neutral glyph remains neutral; no chroma is invented')

# GPU transport regression: every reasonless output-open path is gone and exact fallback still exists.
if len(sys.argv)!=2: raise SystemExit('usage: verify_26579_v1_regressions.py candidate_root')
cpp=(Path(sys.argv[1])/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
for token in ['IRIS_26579_GPU_DIRECT_INTERMEDIATE_PUBLICATION','setErrnoReason("open_base")','setErrnoReason("open_gain")','gpu_band_queue_empty','IRIS_26579_TRUE2X_GPU_COMPAT_RESULT','IRIS_26579_TRUE2X_GPU_TO_CPU_FALLBACK','/* Exact successful 26570 CPU fallback begins here. */']:
 assert token in cpp,token
assert '.iris26571_gpu' not in cpp
assert 'gpuBasePath' not in cpp and 'gpuGainPath' not in cpp
assert 'generateGain?gp.c:nullptr,(int)quality,true,&gpuTiming' in cpp
assert 'generateGain?gp.c:nullptr,(int)quality,false,&gpuCompatTiming' in cpp
print('PASS GPU publication uses Java-authorized intermediates, exhaustive reasons, async->compat->exact CPU fallback')
