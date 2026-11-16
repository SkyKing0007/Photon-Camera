#!/usr/bin/env python3
"""Reference numerical no-regression model of conservative extra RAW motion veto."""
import math,sys
from build_26944_incremental import scope,fail

def ss(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)))
 return t*t*(3.-2.*t)
def after(support,mismatch,original):
 evidence=ss(.48,.82,1.-support)*ss(.10,.27,mismatch)
 return original if evidence==0. else 1.-(1.-original)*(1.-evidence)
def main():
 scope()
 # Static and uncertain regions match original 26942 reference coefficients.
 for sup in (.52,.65,.8,.95,1.):
  for m in (0.,.08,.10,.14,.30,.50):
   for original in (0.,.02,.16,.5,.91,1.):
    assert after(sup,m,original)==original,(sup,m,original,after(sup,m,original))
 for sup in (0.,.1,.25,.4,.50,1.):
  for mm in (0.,.06,.1,.16,.27,.7):
   prev=-1.
   for old in [i/100 for i in range(101)]:
    now=after(sup,mm,old)
    if not (old-1e-7<=now<=1.0000001 and now>=prev):fail('nonmonotone or invented motion weighting')
    prev=now
 assert after(.08,.6,.2)>0.99999
 assert after(.15,.5,.3)>0.99999
 assert after(1.,.7,.42)==.42
 assert after(.15,.03,.42)==.42
 # Motion strength increases only with coherent RAW+HDRq evidence.
 for mm in (.10,.14,.2,.27,.5):
  last=-1.
  for n in range(101):
   val=after(1.-n/100.,mm,.27)
   if val+1e-8<last:fail('motion evidence must be monotone')
   last=val
 print('PASS motion: identity stationary, noise/mismatch double gate, conservative monotonically stronger reference substitution, no spatial tile mask')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
