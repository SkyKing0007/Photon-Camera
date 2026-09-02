#!/usr/bin/env python3
import math

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
    if centerL>0.58 or one>0.5 or legacy>0.25 or present>0.0:
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
    coherent=smooth(0.76,0.95,agree)*smooth(0.050,0.180,consmag)
    ratio=cm/max(consmag,0.025); plausible=1.0-smooth(2.0,3.5,ratio)
    real=clamp(max(supported,coherent*plausible*max(hi,topo),topo))
    outlier=smooth(0.070,0.220,disagree); neutral=1.0-smooth(0.070,0.160,consmag); isolated=smooth(1.35,2.75,ratio)
    phaseConf=ph*((1.0-isolated)*0.70+isolated)
    score=outlier*neutral*surface*neutralSurface*phaseConf*(1.0-real)
    gate=smooth(0.72,0.90,score)
    return dict(gate=gate,real=real,phase=ph,neutralSurface=neutralSurface,neutralConsensus=neutral,surface=surface)

def grid(default): return {(x,y):default for y in range(-2,3) for x in range(-2,3)}
neutral=rgb(.55); mag=rgb(.55,(.12,-.12,.12)); green=rgb(.55,(-.08,.08,-.08)); red=rgb(.55,(.16,-.08,0)); yellow=rgb(.55,(.10,.05,-.20)); blueSky=rgb(.75,(-.08,-.04,.16)); leaf=rgb(.40,(-.10,.10,-.10))
# 1) Bayer-like false fringe: neutral surface, near opposite hue, far repeats center.
g=grid(neutral); g[(0,0)]=mag
for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]: g[(dx,dy)]=green; g[(2*dx,2*dy)]=mag
r=evaluate(g); assert r['gate']>0.90 and r['phase']>0.90 and r['real']<0.10, r
print('PASS neutral-surface Bayer-like purple/green fringe is eligible for bounded correction')
# 2) real red line/contour: near and far same-side hue continuity must veto.
g=grid(neutral)
for x in (-2,-1,0,1,2): g[(x,0)]=red
r=evaluate(g); assert r['gate']<0.01 and r['real']>0.90, r
print('PASS red text/contour continuation preserved')
# 3) tiny saturated object: isolation alone can never authorize correction.
g=grid(neutral); g[(0,0)]=yellow
r=evaluate(g); assert r['gate']<0.01 and r['phase']<0.05, r
print('PASS tiny isolated saturated flower/LED/thread preserved when phase proof is absent')
# 4) real colored checker: phase-like sampling exists, but colored neighbors make it ambiguous.
g=grid(neutral)
for y in range(-2,3):
 for x in range(-2,3): g[(x,y)]=mag if ((x+y)&1)==0 else green
r=evaluate(g); assert r['gate']<0.01 and r['neutralSurface']<0.05, r
print('PASS opposing real colored microstructure preserved even with phase-like pattern')
# 5) foliage/sky material boundary: both sides have coherent real chroma.
g={}
for y in range(-2,3):
 for x in range(-2,3): g[(x,y)]=leaf if x<=0 else blueSky
r=evaluate(g); assert r['gate']<0.01 and r['real']>0.90, r
print('PASS foliage/sky boundary remains protected')
