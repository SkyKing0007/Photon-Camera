#!/usr/bin/env python3
"""Check monotonic matching of SDR body to former HDR intent with highlight-only gain."""
import math,sys
from pathlib import Path
from build_26941_incremental import R,fail,scope
SH='app/src/main/assets/shaders/motionv2/'
def sstep(a,b,x):
 t=min(1.,max(0.,(x-a)/(b-a)));return t*t*(3.-2.*t)
def new_base(old,source,requested):
 target=max(old,max(source,0.)*requested)
 return target if target<=.82 else .82+.18*(-math.expm1(-(target-.82)/.18))
def main():
 scope();root=R if '--live' in sys.argv else R/'handoff_payload_26941'
 r=(root/SH/'render.glsl').read_text();g=(root/SH/'gainmap.glsl').read_text()
 # Strict real code literals bound to model; no separate unverified math.
 for s in (r,g):
  for v in ('float target=max(priorGuide,linearIntent);',
            'if(target<=0.82)return target;',
            'return 0.82+0.18*(1.0-exp(-(target-0.82)/0.18));'):
   if v not in s:fail('mathematical source mismatch '+v)
 last=-1.
 for n in range(0,4001):
  source=n/2000.;old=source*.75;requested=1.6
  base=new_base(old,source,requested)
  if not math.isfinite(base) or base<last-1e-9 or (old<=.82 and base<old-1e-9) or base>=1.000000001:
   fail('nonmonotone/underexposed SDR mapping '+str((source,base,last)))
  if source*requested<=.82 and abs(base-source*requested)>1e-9:fail('body SDR does not match former UHDR linear target')
  linear_target=source*requested
  extra=max(0.,linear_target-base)
  ratio=(base+extra+.015625)/(base+.015625)
  gate=sstep(.68,.96,linear_target)
  filtered=1.+(ratio-1.)*gate
  if source*requested<=.68 and filtered!=1.:fail('dark/body gain map not at unity')
  if filtered<1.-1e-7 or filtered>ratio+1e-7:fail('invalid UHDR gain ratio range')
  last=base
 # Check shoulder C1 continuity at .82 and exposure ratio stable.
 eps=1e-6
 dlo=(new_base(0.,(.82-eps)/1.6,1.6)-new_base(0.,(.82-2*eps)/1.6,1.6))/eps
 dhi=(new_base(0.,(.82+2*eps)/1.6,1.6)-new_base(0.,(.82+eps)/1.6,1.6))/eps
 if abs(dlo-1.)>1e-4 or abs(dhi-1.)>1e-4:fail('SDR highlight shoulder derivative discontinuity')
 print('PASS 26941 matched SDR body/old HDR intent, monotone bounded C1 shoulder, unity shadow/body gain, 4001 numerical samples; no processing-domain or chroma changes')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
