#!/usr/bin/env python3
"""Numerical whole-RGB +1EV exposure tests plus GLSL keyword/arity fail closed."""
import math,re,sys
from pathlib import Path
from build_26954_incremental import R,fail

def shoulder_peak(peak):
    # Bitwise-equivalent algebra to the 26954 V2 shader's fixed-EV, C1
    # highlight shoulder. Avoid old hard-clipped 0.5..1.0 flat bands.
    if peak <= 0.125:
        return 2.0*peak
    x=min(max((peak-0.125)/0.875,0.0),1.0)
    return ((0.5125*x-1.5125)*x+1.75)*x+0.25

def exposure(rgb):
    positive=tuple(max(c,0.0) for c in rgb)
    peak=max(*positive,0.0)
    mapped=shoulder_peak(peak)
    scale=mapped/max(peak,1e-6)
    return tuple(c*scale for c in positive)

def gain_map(sdr, delta, safe_max=8.0, offset=0.0001):
    # Exact successful-26940 original HDR intent law, with the *new*
    # completed display-linear SDR denominator. The 26941 bright-only gate
    # is disabled ONLY for B OFF/B Night via the shader flag.
    hdr_intent=sdr+max(delta,0.0)
    ratio=min(max((hdr_intent+offset)/(sdr+offset),1.0),safe_max)
    return ratio

def math_check():
    # Exhaustive-looking neutral ramp catches the rejected handoff's
    # plateau (0.50..1.00 input -> identical white) by STRICT monotonicity.
    previous=-1
    for i in range(10001):
        y=i/10000
        out=exposure((y,y,y))[0]
        if i and not out>previous+1e-10:fail('NEUTRAL TONAL PLATEAU / reversal at %.6f: %.9f >= %.9f' %(y,previous,out))
        if not 0<=out<=1+1e-9:fail('SDR ramp gamut overflow')
        if y<=0.125 and abs(out-2*y)>1e-10:fail('true +1EV dark/body exposure incorrect')
        if y>=0.125 and out<y-1e-10:fail('nonpositive global exposure')
        previous=out
    assert abs(shoulder_peak(0.125)-0.25)<1e-12
    assert abs(shoulder_peak(1)-1)<1e-12
    for y, minimum in ((0.2,0.38),(0.4,0.64),(0.5,0.73),(0.8,0.90),(.95,.97)):
        if shoulder_peak(y)<=minimum:fail('unintended highlight compression too strong')
    # Endpoints and slope are C1, not the hard cap, nor a glaring knee.
    h=1e-5
    if abs((shoulder_peak(.125+h)-shoulder_peak(.125))/h-2)>1e-3:fail('shoulder entry derivative discontinuity')
    if abs((shoulder_peak(1)-shoulder_peak(1-h))/h-.30)>1e-3:fail('shoulder clips white / zero endpoint slope')
    # An RGB gain uses the SAME scalar for all channels even in highlights;
    # it does not bleach colored foliage by channel-independent clamping.
    for i in range(30001):
        rgb=(((i*37)%997)/997, ((i*59)%991)/991, ((i*73)%983)/983)
        out=exposure(rgb)
        if not (-1e-9<=min(out) and max(out)<=1+1e-9):fail('SDR gamut exceeded')
        scales=[out[j]/rgb[j] for j in range(3) if rgb[j]>1e-10]
        if scales and max(scales)-min(scales)>1e-9:fail('hue/channel ratio not preserved')
        if max(rgb)<.125 and max(abs(out[k]-2*rgb[k]) for k in range(3))>1e-9:fail('shadow +1EV incorrect')
    # The original UHDR delta is added to the new SDR, never to an
    # approximated previous SDR model. As SDR brightens, computed gain falls
    # but real bright HDR highlights retain positive headroom naturally.
    for y in (0,0.001,.05,.125,.25,.5,.75,.9,1):
        old=y
        new=exposure((y,y,y))[0]
        for delta in (0,.01,.1,.2,.6,1,3):
            before=gain_map(old,delta)
            after=gain_map(new,delta)
            if after<1 or after>8+1e-12:fail('UHDR ratio outside legal range')
            if delta>0 and new>0 and after<=1:fail('UHDR highlight pop disappeared')
            if delta>0 and after>before+1e-9:fail('UHDR gain grows after SDR brightening')
            if delta==0 and abs(after-1)>1e-12:fail('invented UHDR from no HDR intent')
            if abs((new+delta+0.0001)/(new+0.0001)-after)>1e-9 and after<8:fail('wrong original 26940 gainmap law')
    # Pointwise monotone map cannot overshoot a flat or step boundary in
    # neutral synthetic images (no new spatial halo from the 26954 exposure).
    for lo,hi in ((0,.999),(.05,.85),(.3,.7),(.5,.51),(.7,1)):
        seq=[lo]*32+[hi]*32
        mapped=[exposure((q,q,q))[0] for q in seq]
        if any(z<exposure((lo,lo,lo))[0]-1e-9 or z>exposure((hi,hi,hi))[0]+1e-9 for z in mapped):fail('spatial halo introduced')
    # Explicit rejected V1 baseline MUST fail strict monotonicity.
    rejected=lambda x:x*min(2.0,1.0/max(x,1e-6))
    if rejected(.5)!=rejected(.7) or rejected(.7)!=rejected(.9):fail('rejected-V1 numerical negative control no longer rejects plateau')
    print('PASS 10001 strictly rising SDR tones; exact +1EV low/body; C1 positive-slope white shoulder; 30001 channel-ratio cases; original 26940 UHDR gain adapted to new SDR; old hard-cap negative control')

def glsl_check():
 root=R if '--live' in sys.argv else R/'handoff_payload_26954'
 reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly flat smooth noperspective layout centroid sample patch subroutine in out inout lowp mediump highp precision invariant packed goto switch case default namespace using class public static template union enum typedef cast common partition active filter input output'.split())
 keywords={'max':2,'min':2,'clamp':3,'smoothstep':3,'mix':3,'dot':2,'pow':2,'step':2,'texelFetch':3}
 for name in ('render','gainmap'):
  p=root/'app/src/main/assets/shaders/motionv2'/(name+'.glsl');s=p.read_text()
  code=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
  if s.count('void main()')!=1 or '#version' in code:fail('GLSL body entry malformed '+name)
  for m in re.finditer(r'\b(?:float|int|uint|vec[234]|ivec[234]|bool|sampler2D|mat[234]|highp|mediump|lowp)\s+([A-Za-z_]\w*)\s*(?=[;=,\[(])',code):
   if m.group(1) in reserved:fail('GLSL illegal reserved variable '+m.group(1)+' in '+name)
  if re.search(r'\bfloat\s+(?:flat|coherent|restrict)\b',code):fail('26904/26952 known GLSL reserved words regress')
  if re.search(r'\bgl_[A-Za-z0-9_]+\s*=',code):fail('writes GLSL built-in')
  for m in re.finditer(r'\b('+'|'.join(keywords)+r')\s*\(',code):
   depth=0;args=1;done=False
   for c in code[m.end()-1:]:
    if c=='(':depth+=1
    elif c==')':
     depth-=1
     if depth==0:done=True;break
    elif c==',' and depth==1:args+=1
   if not done or args!=keywords[m.group(1)]:fail('wrong GLSL '+m.group(1)+' arity in '+name)
 for bad in ('coherent','flat','restrict','namespace','varying'):
  m=re.search(r'\bfloat\s+([A-Za-z_]\w*)\s*=', 'void main(){float '+bad+'=1.0;}')
  if not m or m.group(1) not in reserved:fail('negative reserved scan not working '+bad)
 print('PASS exact current ESSL shader lexical/keyword/arity and 26904 coherent/26952 flat negative regressions')
if __name__=='__main__':
 try:math_check();glsl_check()
 except Exception as e:print('26954 TONE/GLSL BLOCKED '+str(e),file=sys.stderr);sys.exit(1)
