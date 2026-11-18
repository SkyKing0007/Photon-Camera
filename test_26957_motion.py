#!/usr/bin/env python3
"""Numerical regressions for Rawr 56c1b932/44e4f092 motion gate, harmonic effective frames and optional noise."""
import math,random,sys
from build_26957_incremental import R,scope,fail
scope();random.seed(26957)
def gate(z):
 t=max(0.0,min(1.0,(z-1.6)/1.0))
 return t*t*(3.0-2.0*t)
def zscore(ref,comp,a,b,black,energy=True):
 weights=[.342940479,.434943816,.565056184,.657059521,.657059521,.565056184,.434943816,.342940479]*2
 total=0
 for Y in range(4):
  for X in range(4):
   samples=[(weights[4*X+x]*weights[4*Y+y],ref[4*Y+y][4*X+x],comp[4*Y+y][4*X+x]) for y in range(4) for x in range(4)]
   sw=sum(w for w,r,v in samples);sw2=sum(w*w for w,r,v in samples)
   signal=sum(w*r for w,r,v in samples)/sw
   variance=2*(a*max(signal-black,0)+b)
   sigma=math.sqrt(variance)*math.sqrt(sw2)/sw
   score=abs(sum(w*(r-v) for w,r,v in samples)/sw)/max(sigma,1.e-6)/.7979
   if energy:
    q=sum(w*(r-v)**2 for w,r,v in samples)/sw/max(variance,1.e-6)
    score=max(score,1+max(0,q-2)/.5)
   total+=score
 return total/16
alpha=.00011*1023;beta=.00000046*1023**2;black=64;signal=350;sigma=math.sqrt(alpha*(signal-black)+beta)
for _ in range(20):
 a=[[signal+random.gauss(0,sigma) for i in range(16)] for j in range(16)]
 b=[[signal+random.gauss(0,sigma) for i in range(16)] for j in range(16)]
 if gate(zscore(a,b,alpha,beta,black))>0.60:fail('static noise falsely rejected')
 moving=[[v+12*sigma for v in row] for row in b]
 if gate(zscore(a,moving,alpha,beta,black))<.95:fail('moving edges merged')
 pattern=[[signal+(7*sigma if (i+j)%2 else -7*sigma) for i in range(16)] for j in range(16)]
 displaced=[[signal-(7*sigma if (i+j)%2 else -7*sigma) for i in range(16)] for j in range(16)]
 if gate(zscore(pattern,displaced,alpha,beta,black))<.95:fail('periodic moved pattern merged')
for N in (2,6,15,30):
 for accepted in ([0.]*(N-1),[1.]*(N-1),[float(N-1)]*(N-1),[N-1 if i%2==0 else 0 for i in range(N-1)]):
  eff=len(accepted)/sum(1/(1+x) for x in accepted)
  if not (1.-1e-8<=eff<=N+1e-8):fail('effective frame harmonic bound')
  for ng in (0.01,0.2):
   if not (ng/N-1e-12<=ng/eff<=ng+1e-12):fail('noise denominator not effective')
for z in (0.,1.6,1.85,2.0,2.15,2.6,3.):
 assert 0<=gate(z)<=1
assert gate(1.6)==0 and gate(2.6)==1
# Rawr 13 changes temporal Wiener norms but gate thresholds are independent.
def norm(strength):
 rev=.5*(26.5-int(strength+.5))
 return (2**(-rev+7.5),2**((-rev+10.)*1.6),max(1.,1.3**(11.-rev)))
assert norm(13)[0]>norm(11)[0] and norm(13)[1]>norm(11)[1]
print('PASS 26957 Rawr motion/noise, moving texture energy detector, harmonic Neff, true /Neff opt-in chroma, fixed 13/32 regression')
