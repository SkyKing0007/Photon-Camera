#!/usr/bin/env python3
import math,sys
from pathlib import Path

def clamp(x,a=0.,b=1.): return min(b,max(a,x))
def smooth(a,b,x):
    if b==a: return 1. if x>=b else 0.
    t=clamp((x-a)/(b-a)); return t*t*(3.-2.*t)
def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def mul(a,s): return tuple(x*s for x in a)
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def length(a): return math.sqrt(dot(a,a))
def lum(v): return dot(v,(.25,.5,.25))
def hue(a,b): return clamp(dot(a,b)/max(length(a)*length(b),1e-6),-1.,1.)
def rgb(l,c=(0,0,0)): return tuple(clamp(l+x) for x in c)
DIR=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)]

def evaluate(px):
    center=px[(0,0)]; centerL=lum(center); scale=max(centerL,.060)
    cc=sub(center,(centerL,)*3); cn=mul(cc,1/scale); cm=length(cn)
    total=cn; ws=1.; ns=nns=maxld=0.; bright=dark=0
    for y in (-1,0,1):
      for x in (-1,0,1):
        if x==0 and y==0: continue
        q=px[(x,y)]; ql=lum(q); sd=(ql-centerL)/max(centerL,ql,.060); rd=abs(sd)
        maxld=max(maxld,rd); bright += sd>.16; dark += sd<-.16
        sw=1.-smooth(.16,.55,rd); qc=mul(sub(q,(ql,)*3),1/max(ql,.060))
        total=add(total,mul(qc,sw)); ws+=sw; ns+=sw; nns+=sw*(1.-smooth(.035,.100,length(qc)))
    cons=mul(total,1/max(ws,1e-6)); disagree=length(sub(cn,cons)); consmag=length(cons); agree=hue(cn,cons)
    surface=smooth(2.5,5.75,ns); neutralSurface=smooth(2.5,4.,nns); legacy=smooth(.45,.90,maxld)
    one=1. if ((bright>=4 and dark<=1) or (dark>=4 and bright<=1)) else 0.
    hi=1.-smooth(.72,.92,centerL); material=one*(1.-smooth(.72,.92,agree))*hi
    ts=nts=chain=phase=0.; present=smooth(.035,.090,cm)
    W=NW=XX=YY=XY=0.; left=right=up=down=0.
    if centerL>.58 or one>.5 or legacy>.25 or present>0:
      for yy in range(-2,3):
       for xx in range(-2,3):
        if xx==0 and yy==0: continue
        q=px[(xx,yy)]; ql=lum(q); rd=abs(ql-centerL)/max(ql,centerL,.060)
        qc=mul(sub(q,(ql,)*3),1/max(ql,.060)); chrom=smooth(.050,.115,length(qc)); comp=1.-smooth(.72,1.20,rd); w=chrom*comp
        W+=w
        if abs(xx)<=1 and abs(yy)<=1:
            NW+=w
            if xx<0:left=max(left,w)
            if xx>0:right=max(right,w)
            if yy<0:up=max(up,w)
            if yy>0:down=max(down,w)
        XX+=w*xx*xx; YY+=w*yy*yy; XY+=w*xx*yy
      for dx,dy in DIR:
        nr=px[(dx,dy)];fr=px[(2*dx,2*dy)]; nl=lum(nr);fl=lum(fr)
        nld=abs(nl-centerL)/max(nl,centerL,.060); fld=abs(fl-centerL)/max(fl,centerL,.060)
        nc=mul(sub(nr,(nl,)*3),1/max(nl,.060)); fc=mul(sub(fr,(fl,)*3),1/max(fl,.060))
        na=hue(cn,nc);fa=hue(cn,fc);nsl=1.-smooth(.10,.26,nld);fsl=1.-smooth(.10,.26,fld);nsh=smooth(.82,.94,na);fsh=smooth(.82,.94,fa)
        ts+=fsl*((1.-present)+present*fsh); nts+=nsl*nsh*present; chain+=nsl*fsl*nsh*fsh*present
        phase+=nsl*fsl*fsh*(1.-smooth(.20,.72,na))*present
    rad=smooth(1.25,2.75,ts)*smooth(.20,.55,max(legacy,one)); near=smooth(.55,1.45,nts); contour=smooth(.55,1.60,chain); ph=smooth(1.10,2.80,phase)
    topo=max(near,contour,rad*(1.-.90*ph)); supported=material*near
    trace=XX+YY; det=max(XX*YY-XY*XY,0.); minor=.5*(trace-math.sqrt(max(trace*trace-4*det,0.)))/max(W,1e-6) if trace>1e-6 else 0.
    area=smooth(1.35,3.25,W)*smooth(1.15,2.75,NW)*smooth(.10,.32,minor)*present
    axis=smooth(.18,.60,max(left,right))*smooth(.18,.60,max(up,down)); compact=area*axis
    phaseOverride=smooth(.78,.96,ph); micro=max(area*(1.-.98*phaseOverride),compact*(1.-phaseOverride))
    coherent=smooth(.76,.95,agree)*smooth(.050,.180,consmag); ratio=cm/max(consmag,.025); plausible=1.-smooth(2.,3.5,ratio)
    real=clamp(max(supported,coherent*plausible*max(hi,topo),topo,micro))
    outlier=smooth(.070,.220,disagree); neutral=1.-smooth(.070,.160,consmag); isolated=smooth(1.35,2.75,ratio); phaseConf=ph*((1.-isolated)*.70+isolated)
    score=outlier*neutral*surface*neutralSurface*phaseConf*(1.-real); gate=smooth(.72,.90,score)
    return dict(gate=gate,real=real,phase=ph,micro=micro,compact=compact,area=area,minor=minor,axis=axis)

def grid(d): return {(x,y):d for y in range(-2,3) for x in range(-2,3)}
neutral=rgb(.55); mag=rgb(.55,(.12,-.12,.12)); green=rgb(.55,(-.08,.08,-.08)); red=rgb(.55,(.16,-.08,0)); yellow=rgb(.55,(.10,.05,-.20)); blue=rgb(.55,(-.12,-.02,.16)); sky=rgb(.75,(-.08,-.04,.16)); leaf=rgb(.40,(-.10,.10,-.10))
# Overwhelming repeated CFA phase must remain correctable.
g=grid(neutral);g[(0,0)]=mag
for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:g[(dx,dy)]=green;g[(2*dx,2*dy)]=mag
r=evaluate(g); assert r['gate']>.90 and r['phase']>.90 and r['real']<.10,r
print('PASS inherited neutral Bayer-phase fringe remains correctable')
# Real single-hue contour.
g=grid(neutral)
for x in range(-2,3):g[(x,0)]=red
r=evaluate(g);assert r['gate']<.01 and r['real']>.90,r
print('PASS colored contour/text stroke preserved')
# Tiny isolated color has no false proof.
g=grid(neutral);g[(0,0)]=yellow;r=evaluate(g);assert r['gate']<.01 and r['phase']<.05,r
print('PASS isolated tiny real color remains fail-closed')
# Foliage/sky boundary.
g={(x,y):(leaf if x<=0 else sky) for y in range(-2,3) for x in range(-2,3)};r=evaluate(g);assert r['gate']<.01 and r['real']>.90,r
print('PASS foliage/sky material boundary preserved')
# Multicolor 2-D print.
colors=[red,yellow,blue];g=grid(neutral)
for y in (-1,0,1):
 for x in (-1,0,1):g[(x,y)]=colors[(x+y+8)%3]
r=evaluate(g);assert r['gate']<.01 and r['micro']>.90 and r['real']>.90,r
print('PASS compact multicolor flag/logo area preserved')
# Smaller 2x2 multicolor object.
g=grid(neutral);g[(0,0)]=red;g[(1,0)]=yellow;g[(0,1)]=blue;g[(1,1)]=red;r=evaluate(g);assert r['gate']<.01 and r['micro']>.90,r
print('PASS 2x2 multicolor micro-object preserved')
# Ribbons/diagonals do not earn area veto.
for pts,name in [([(x,0) for x in range(-2,3)],'horizontal'), ([(x,x) for x in range(-2,3)],'diagonal')]:
 g=grid(neutral)
 for i,p in enumerate(pts):g[p]=colors[i%3]
 r=evaluate(g);assert r['micro']<.05,r
 print('PASS '+name+' chromatic ribbon does not earn 2-D object veto')

# Exact numeric model of 26580 SR chroma upsampler.
def sr(samples,spatial,directY,confidence):
 ys=[lum(s) for s in samples]; ch=[sub(samples[i],(ys[i],)*3) for i in range(4)]; mags=[length(c) for c in ch]
 nearest=max(range(4),key=lambda i:spatial[i]); maxYD=max(abs(ys[i]-ys[j]) for i in range(4) for j in range(i+1,4)); maxC=max(mags)
 bil=tuple(sum(samples[i][c]*spatial[i] for i in range(4)) for c in range(3)); by=max(lum(bil),0.); selector=ys[nearest]*(1-.60*confidence)+directY*(.60*confidence)
 tc=[0.,0.,0.];ws=0.;cross=occ=nv=0.;anchor=nearest;ascore=-1.
 for i in range(4):
  rel=abs(ys[i]-selector)/max(abs(ys[i]),abs(selector),.035);same=1.-smooth(0.,1.,(rel-.08)/.32);mw=same*same;w=spatial[i]*(.002+.998*mw)
  for c in range(3):tc[c]+=ch[i][c]*w
  ws+=w;cross+=spatial[i]*(1.-same);occ+=spatial[i]*smooth(0.,1.,(mags[i]-.020)/.055);nv+=1.-smooth(0.,1.,(mags[i]-.010)/.050)
  score=spatial[i]*(.15+.85*same)
  if score>ascore:ascore=score;anchor=i
 tc=tuple(v/max(ws,1e-6) for v in tc);tm=length(tc)
 if tm>maxC and tm>1e-7:tc=mul(tc,maxC/tm)
 bc=sub(bil,(by,)*3);edge=smooth(0.,1.,(maxYD-.018)/.095);crossE=smooth(0.,1.,(cross-.06)/.30);tg=edge*((1-crossE)*.70+crossE);sel=tuple(bc[c]+(tc[c]-bc[c])*tg for c in range(3))
 an=1.-smooth(0.,1.,(mags[anchor]-.012)/.050);nn=smooth(0.,1.,(nv-2.55)/.90);lp=smooth(0.,1.,(occ-.20)/.40);own=edge*crossE*an*nn*(1.-lp);sel=tuple(sel[c]+(ch[anchor][c]-sel[c])*(.92*own) for c in range(3))
 scale=1.
 for c in sel:
  if c<0:scale=min(scale,by/max(-c,1e-7))
 out=tuple(by+sel[c]*clamp(scale) for c in range(3));return bil,out,maxC,dict(edge=edge,cross=crossE,owner=own,anchor=anchor,occ=occ,nv=nv)
# Flat pass-through.
flat=rgb(.45,(.12,-.04,-.08));bil,out,mc,d=sr([flat]*4,[.25]*4,lum(flat),1);assert max(abs(a-b) for a,b in zip(bil,out))<1e-7,(bil,out,d)
print('PASS SR flat color remains exact bilinear pass-through')
# Colored object side keeps stronger chroma than bilinear and <= native max.
white=rgb(.80);redObj=rgb(.38,(.28,-.10,-.08));samples=[redObj,white,redObj,white];sp=[.375,.125,.375,.125];bil,out,mc,d=sr(samples,sp,lum(redObj),1);bm=length(sub(bil,(lum(bil),)*3));om=length(sub(out,(lum(out),)*3));assert om>bm and om<=mc+1e-6 and abs(lum(out)-lum(bil))<1e-6,(bm,om,mc,d)
print('PASS SR colored material side retains supported chroma without saturation invention')
# White side next to colored object must leak less chroma than bilinear.
sp=[.125,.375,.125,.375];bil,out,mc,d=sr(samples,sp,lum(white),1);bm=length(sub(bil,(lum(bil),)*3));om=length(sub(out,(lum(out),)*3));assert om<bm*.55,(bm,om,d)
print('PASS SR neutral side excludes opposite colored-object chroma')
# Neutral glyph with one residual purple native edge sample: white-side SR footprint must be materially reduced.
black=rgb(.12); purpleBlack=rgb(.12,(.025,-.020,.015));samples=[purpleBlack,white,black,white];sp=[.125,.375,.125,.375];bil,out,mc,d=sr(samples,sp,lum(white),1);bm=length(sub(bil,(lum(bil),)*3));om=length(sub(out,(lum(out),)*3));assert om<bm*.55,(bm,om,d)
print('PASS SR neutral glyph outside-edge purple/cyan footprint is suppressed')
# Colored text side is not neutral-clamped away.
samples=[redObj,white,redObj,white];sp=[.375,.125,.375,.125];bil,out,mc,d=sr(samples,sp,lum(redObj),1);assert d['owner']<.05 and length(sub(out,(lum(out),)*3))>.8*length(sub(redObj,(lum(redObj),)*3)),d
print('PASS SR colored glyph/object owner is not neutral-clamped')

if len(sys.argv)==2:
 root=Path(sys.argv[1]);vgn=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text();sab=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();cpp_path=root/'app/src/main/cpp/motionv2_jpeg444_jni.cpp';cpp=cpp_path.read_text()
 import hashlib
 assert hashlib.sha256(cpp_path.read_bytes()).hexdigest()=='d73cd24452280958f089e9124545a81461939e8fa0c9c95272b2825942e4b43d'
 for t in ['IRIS_26580_MICRO_OBJECT_AREA_VS_RIBBON','IRIS_26580_FAIL_CLOSED_MULTICOLOR_OBJECT_VETO','phaseOverride = smoothstep(0.78, 0.96','microCompactAreaEvidence']:
  assert t in vgn,t
 for t in ['IRIS_26580_TRUE2X_SAME_MATERIAL_CHROMA_OWNERSHIP','IRIS_26580_NEUTRAL_GLYPH_OUTSIDE_EDGE_EXCLUSION','0.002 + 0.998 * materialWeight','neutralSideOwnership']:
  assert t in sab,t
 for t in ['IRIS_26579_GPU_DIRECT_INTERMEDIATE_PUBLICATION','gpuMode=ASYNC_FENCE' if False else 'IRIS_26579_TRUE2X_GPU_TO_CPU_FALLBACK']:
  assert t in cpp,t
 print('PASS 26580 runtime markers and 26579 GPU publication owner preserved')
