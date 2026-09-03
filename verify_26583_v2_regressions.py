#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,sys
OUT=.8; START=.5; LEGACY_TARGET=.97; BROAD_TARGET=.955; COMPACT_TARGET=.965; CS=.002; CF=.025; BNS=.012; BNF=.060; BHS=.0025; BHF=.020; CNS=.004; CNF=.015; LOG=6.; MAXW=12.
GPU='d73cd24452280958f089e9124545a81461939e8fa0c9c95272b2825942e4b43d'; RSH='e0a438e51e12df5e6d8b53dc92892078ba7659791725cee54700869a6bc62b71'
def fail(x): raise SystemExit('FAIL: '+x)
def cl(x,a,b): return max(a,min(b,x))
def sm(a,b,x):
 t=cl((x-a)/max(b-a,1e-9),0,1); return t*t*(3-2*t)
def mix(a,b,t): return a+(b-a)*t
def bw(g): return max(1,min(6,.9*max(1,g)))
def mapped_pre(x,w):
 if x<=START:return x
 q=cl((x-START)/max(w-START,1e-6),0,1); sh=math.log(1+LOG*q)/math.log(1+LOG)
 return START+(1/OUT-START)*sh
def proj(src,g,w=None): return cl(mapped_pre(src*g,w if w is not None else bw(g))*OUT,0,1)
def req(g,src,target):
 b=bw(g); post=src*g
 if not math.isfinite(src) or post<=START:return b
 tp=cl(target,.8,.995)/OUT; shape=cl((tp-START)/(1/OUT-START),0,1); x=(math.exp(shape*math.log(1+LOG))-1)/LOG
 return max(b,min(MAXW,START+(post-START)/max(x,1e-4)))
def q(a,p):
 a=sorted(a); return a[round((len(a)-1)*p)]
def legacy_strength(fr): return sm(CS,CF,fr)
def decision(a,g):
 a=sorted(a); b=bw(g); n=len(a); p99=q(a,.99); p995=q(a,.995); p998=q(a,.998)
 threshold=b/max(g,1e-6); legacy=sum(v>=threshold for v in a)/n; ls=legacy_strength(legacy); lw=b
 if p99*g>b: lw=b+(req(g,p99,LEGACY_TARGET)-b)*ls
 if lw<=b+1e-6: ls=0
 outs=[proj(v,g,b) for v in a]
 bnear=sum(v>=.930 for v in outs)/n; near=sum(v>=.965 for v in outs)/n; hard=sum(v>=.985 for v in outs)/n
 bp=sm(BNS,BNF,bnear); bpressure=sm(.930,.985,proj(p99,g,b)); hp=sm(BHS,BHF,hard); pbs=max(bp*bpressure,.70*hp)
 assist=sm(.020,.080,bnear); bg=mix(p99,max(p99,p995),.45*assist); pbw=b+(req(g,bg,BROAD_TARGET)-b)*pbs
 broadw=max(lw,pbw); broadS=max(ls,pbs)
 cs=sm(CNS,CNF,near)*sm(.965,.995,proj(p995,g,b))*(1-sm(.25,.70,broadS))
 ca=sm(.006,.020,near); cg=mix(p995,max(p995,p998),.35*ca); cw=b+(req(g,cg,COMPACT_TARGET)-b)*cs
 return b,max(broadw,cw),legacy,bnear,near,hard,ls,pbs,cs,p99,p995,p998,lw
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 if len(sys.argv)!=2: fail('usage candidate')
 r=Path(sys.argv[1])
 # ordinary/no-tail remains exact successful 26582 base.
 for a,g in [([.25]*9000+[.55]*1000,4.5),([.35]*9800+[.70]*200,2.0)]:
  b,w,*_=decision(a,g)
  if abs(b-w)>1e-7: fail('ordinary scene changed')
 # isolated <0.2% specular cannot globally pull tone.
 a=[.35]*9985+[1.6]*15; b,w,legacy,bn,n,h,ls,pbs,cs,*_=decision(a,5.2)
 if abs(w-b)>1e-7 or pbs!=0 or cs!=0: fail('isolated specular moved global tone')
 # office/window broad case: old 26582 threshold sees zero clip, projected near-ceiling region must protect it.
 a=[.38]*8500+[.70]*500+[.80]*600+[.88]*400; b,w,legacy,bn,n,h,ls,pbs,cs,p99,p995,p998,lw=decision(a,4.5)
 if legacy!=0 or abs(lw-b)>1e-7: fail('office fixture no longer reproduces 26582 blind spot')
 if not (bn>.08 and pbs>.95 and w>b*1.10): fail('projected broad office/window tail not protected')
 if proj(p995,4.5,w)>.970: fail('office P99.5 still too close to ceiling')
 # broad cloud field: projected broad may only add protection; never less than legacy 26582 result.
 a=[.42]*9000+[.72]*400+[.82]*400+[.90]*200; b,w,legacy,bn,n,h,ls,pbs,cs,p99,p995,p998,lw=decision(a,4.5)
 if w+1e-7<lw or pbs<.9: fail('broad cloud protection regressed')
 # compact sunset: full-frame P99 stays body-dominated but supported P99.5 tail earns headroom.
 a=[.35]*9500+[.62]*400+[.88]*100; b,w,legacy,bn,n,h,ls,pbs,cs,p99,p995,p998,lw=decision(a,5.2)
 if not (p99<.90 and n>=.009 and cs>.45 and w>b*1.04): fail('compact sunset not protected')
 if proj(p995,5.2,w)>.990: fail('compact P99.5 not pulled below ceiling')
 # scalar-RGB and body invariants.
 for x in [0,.05,.2,.49,.5]:
  if abs(proj(x,1,1)-proj(x,1,9))>1e-8: fail('body changed below shoulder')
 rgb=(1.8,.72,.31); guide=max(rgb); scale=mapped_pre(guide,6)/guide; out=tuple(v*scale for v in rgb)
 if abs(out[0]/out[1]-rgb[0]/rgb[1])>1e-6 or abs(out[1]/out[2]-rgb[1]/rgb[2])>1e-6: fail('RGB ratio changed')
 if sha(r/'app/src/main/assets/shaders/motionv2/render.glsl')!=RSH: fail('render shader changed')
 if sha(r/'app/src/main/cpp/motionv2_jpeg444_jni.cpp')!=GPU: fail('GPU publication changed')
 m=(r/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text()
 if 'presentedLuma(s, 1.0f)' in m: fail('26582 compiler regression survived')
 print('PASS ordinary/no-tail scenes keep exact successful 26582 base tone decision')
 print('PASS isolated <0.2% specular cannot globally pull tone')
 print('PASS projected broad office/window tail fixes pre-clipping crowding missed by 26582')
 print('PASS broad cloud protection is never weaker than successful 26582 legacy result')
 print('PASS compact sunset/warm max-channel tail earns supported headroom')
 print('PASS <=0.50 body invariant; correction remains uniform RGB scalar')
 print('PASS 26582 Java signature regression, render shader and GPU publication frozen')
if __name__=='__main__':main()
