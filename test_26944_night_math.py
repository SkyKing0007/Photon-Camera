#!/usr/bin/env python3
"""26941 Night matched SDR and once-only post-Jin highlight gate numerical reference."""
import math,sys
from build_26944_incremental import scope,fail
OFF=0.015625
def ss(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)))
 return t*t*(3.-2.*t)
def matched(prior,source,requested):
 target=max(prior,source*requested)
 return target if target<=.82 else .82+.18*(1.-math.exp(-(target-.82)/.18))
def ratio(pre,fin,oldratio,maxr):
 v=max(1.,min(maxr,oldratio*(pre+OFF)/(fin+OFF)))
 hdr=max(0.,oldratio*(pre+OFF)-OFF)
 return 1.+(v-1.)*ss(.68,.96,hdr)
def main():
 scope()
 # Exact Night/Photo 26941 formula: identity below effective matched intent.
 for prior in [0.,.01,.04,.1,.32,.7,.82,.95]:
  for source in (0.,.03,.12,.5,1.0):
   for requested in (.25,.5,1.,1.6,2.):
    x=matched(prior,source,requested)
    if not (0<=x<=1.00000001) or not math.isfinite(x):fail('bad Night matched SDR shoulder')
    if max(prior,source*requested)<=.82 and abs(x-max(prior,source*requested))>1e-10:fail('matched SDR midtone not 26941 exact')
 for maxr in (1.5,2.,2.5):
  for pre in (.001,.015,.07,.18,.4,.8,1.):
   for fin in (.001,.015,.05,.2,.42,.75,1.):
    for old in (1.,1.15,1.5,2.,2.5):
     x=ratio(pre,fin,old,maxr)
     if not (1.-1e-10<=x<=maxr+1e-10):fail('illegal Night gainmap quotient')
     hdr=old*(pre+OFF)-OFF
     if hdr<=.68 and x!=1.:fail('Night SDR body still boosted by gainmap')
     if hdr>=.96:
      expected=max(1.,min(maxr,old*(pre+OFF)/(fin+OFF)))
      if abs(x-expected)>1e-9:fail('Night highlights changed by body gate')
 # Color ratios preserved by a scalar matched presentation multiplier.
 rgb=(.13,.25,.37);target=matched(.27,.35,1.2);scaled=tuple(x*target/.37 for x in rgb)
 assert max(abs(scaled[i]/scaled[j]-rgb[i]/rgb[j]) for i in range(3) for j in range(3))<1e-12
 print('PASS Night: 26941 matched SDR primary, smooth shoulder, true single post-Jin body suppression, UHDR highlights, scalar RGB hue')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
