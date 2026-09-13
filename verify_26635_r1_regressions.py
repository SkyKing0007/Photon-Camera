#!/usr/bin/env python3
from pathlib import Path
import math,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26635_r1_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
sh=(C/'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl').read_text()
block=sh.split('if(iris26626Mode==6){',1)[1].split('if(iris26626Mode==5){',1)[0]
assert 'targetWhite' not in block and '0.96' not in block

def ss(a,b,x):
    t=min(max((x-a)/(b-a),0.0),1.0); return t*t*(3.0-2.0*t)
def f(base,current):
    residual=current-base
    upper=ss(.65,.985,base); sg=ss(.70,.985,base)
    shoulder=1.0-max(1.0-base,0.0)**1.12
    bout=(1.0-.55*sg)*base+.55*sg*shoulder
    structure=ss(.012,.045,abs(residual))
    small=(1.0-upper)+upper*.78
    k=small+(1.0-small)*structure
    return min(max(bout+k*residual,2.0**-12),1.0),bout,k
# smooth base must be monotone, low range exact, bounded lift, no hard target.
prev=-1.0; maxlift=0.0
for i in range(10001):
    b=i/10000.0
    out,bout,k=f(b,b)
    assert bout+1e-9>=prev,(b,bout,prev)
    prev=bout; maxlift=max(maxlift,bout-b)
    assert .0<=bout<=1.0 and .78-1e-6<=k<=1.0+1e-6
    if (2.0**-12)<=b<=.65: assert abs(out-b)<2e-7,(b,out)
assert maxlift<0.011,maxlift
# small bright-field residual variation is reduced; strong structural residual stays unit weight.
_,_,ks=f(.90,.908); _,_,kstrong=f(.90,.96)
assert ks<.90 and abs(kstrong-1.0)<1e-7,(ks,kstrong)
# sign is preserved and there is no overshoot beyond the convex residual scale before final clamp.
for b in (.70,.80,.90,.95,.98):
    for r in (-.08,-.04,-.02,-.008,.008,.02,.04,.08):
        cur=min(max(b+r,2.0**-12),1.0); out,bout,k=f(b,cur)
        assert .78-1e-6<=k<=1.0+1e-6
        raw=bout+k*(cur-b)
        assert abs(out-min(max(raw,2.0**-12),1.0))<1e-7
print(f'PASS 26635 regression math: monotone coherent base, identity <=0.65, max lift={maxlift:.6f}, small-residual weight={ks:.4f}, strong-structure weight={kstrong:.4f}')
