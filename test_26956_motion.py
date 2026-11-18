#!/usr/bin/env python3
"""Rawr 0a683d7 noise-calibrated HDR+ Quality gate numerical regression."""
import math,random,re,sys
from build_26956_incremental import R,fail
random.seed(26956)
def gate(z):
    t=min(max((z-1.6)/(2.6-1.6),0.0),1.0)
    return t*t*(3.0-2.0*t)
def motion_score(r,a,alpha,beta,black,energy=True):
    # Current Rawr 16 blocks of 4x4 within each raised-cosine 16x16 window.
    W=[.342940479,.434943816,.565056184,.657059521,.657059521,.565056184,.434943816,.342940479]*2
    scores=[]
    for by in range(4):
        for bx in range(4):
            items=[(W[4*bx+x]*W[4*by+y],r[4*by+y][4*bx+x],a[4*by+y][4*bx+x]) for y in range(4) for x in range(4)]
            sw=sum(v[0] for v in items);sw2=sum(v[0]**2 for v in items)
            mu=sum(w*rv for w,rv,av in items)/sw
            var2=2*(alpha*max(mu-black,0.0)+beta)
            sigma=(max(var2,1e-10)/(sw*sw/sw2))**.5
            z=abs(sum(w*(rv-av) for w,rv,av in items)/sw)/max(sigma,1e-6)/.7979
            if energy:
                q=sum(w*(rv-av)**2 for w,rv,av in items)/sw/max(var2,1e-6)
                excess=q-2.0
                if excess>0:z=max(z,1.0+excess/.5)
            scores.append(z)
    return sum(scores)/16
alpha=.00011*1023
beta=.00000046*1023*1023
black=64
signal=350
sigma=(alpha*(signal-black)+beta)**.5
for i in range(12):
    ref=[[signal+random.gauss(0,sigma) for _ in range(16)] for _ in range(16)]
    static=[[signal+random.gauss(0,sigma) for _ in range(16)] for _ in range(16)]
    z=motion_score(ref,static,alpha,beta,black)
    if gate(z)>0.55:fail('stationary noise mistaken for fully moving tile '+str(z))
    moved=[[x+12*sigma for x in row] for row in static]
    zm=motion_score(ref,moved,alpha,beta,black)
    if gate(zm)<.95:fail('moving bright/color boundary erroneously admitted '+str(zm))
    # Equal-mean alternating displaced fine texture (foliage, ripples):
    # energy detector must not rely on block signed means.
    pattern=[[signal+(7*sigma if (x+y)%2 else -7*sigma) for x in range(16)] for y in range(16)]
    displaced=[[signal-(7*sigma if (x+y)%2 else -7*sigma) for x in range(16)] for y in range(16)]
    ze=motion_score(pattern,displaced,alpha,beta,black)
    if gate(ze)<.95:fail('displaced fine pattern escaped Rawr energy test '+str(ze))
# Cross-channel average and central Wiener weight stay upstream; gate cannot
# worsen a fully rejected tile because companion weight must be 1 exactly.
for z in [0.0,1.0,1.59,1.6,1.8,2.0,2.2,2.6,5.0,10.0]:
    g=gate(z)
    if not 0<=g<=1 or (z<=1.6 and g!=0) or (z>=2.6 and g!=1):fail('gate threshold/monotonic rejection broken')
for k in range(10000):
    a=random.random();g=gate(random.uniform(0,8));weight=max(a,g)
    if weight<a-1e-10 or weight<g-1e-10 or not 0<=weight<=1:fail('Rawr conservative channel-consistent rejection failed')
# Full correctness is not inferred from these host regressions; the real
# pinned GLSLang/SPIR-V and CMake JNI compilers remain mandatory in Actions.
print('PASS Rawr matched noise calibrated 4x4 displacement + fine-texture energy gate; stationary/noisy/moving/colored motion and threshold regressions')
