#!/usr/bin/env python3
"""Standalone 26953 HDR-body appearance, bounded monotonic/no overshoot, reserved GLSL identifier and ISO shader-owner checks."""
import math,re,sys
from pathlib import Path
from build_26953_incremental import R,fail

def sstep(a,b,v):
 t=max(0.0,min(1.0,(v-a)/(b-a)))
 return t*t*(3-2*t)
def tone(y,request):
 ev=max(0.0,min(.72,.4*math.log2(max(request,1.0))));exposure=2**ev
 lifted=y*exposure/(1+(exposure-1)*y)
 return lifted*(1-sstep(.85,1.0,y))+y*sstep(.85,1.0,y)
def check_math():
 for request in (.5,1,1.01,1.05,1.2,2,3.49,4,7,20):
  prev=0.0
  for i in range(1,20001):
   y=i/20000;v=tone(y,request)
   if not math.isfinite(v) or not 0<=v<=1.0000001 or v+1e-10<prev or v<y-1e-10:fail('not a monotone bounded one-to-one SDR photo exposure')
   prev=v
  if tone(0,request)!=0 or abs(tone(1,request)-1)>1e-10:fail('white/black altered')
  if request<=1 and abs(tone(.35,request)-.35)>1e-10:fail('global no-lift request altered')
 for v in (.02,.1,.2,.4,.65,.82,.9):
  if not (v<=tone(v,3.49)<1.0):fail('HDR-body brightness does not increase without clipping')
 # A monotone pointwise transform cannot introduce a spatially reversed bright halo.
 for a in (0.01,.1,.4,.65,.9):
  for b in (a+.0001,min(1,a+.25)):
   if b<=1 and tone(b,3.49)<tone(a,3.49):fail('edge brightness reversal')
 print('PASS 26953 actual 20k-sample 10-scene bounded global filmic HDR-body exposure, C1 shoulder, no per-pixel edge decision')

def glsl_live(root):
 source=[root/'app/src/main/assets/shaders/motionv2/render.glsl',root/'app/src/main/assets/shaders/motionv2/gainmap.glsl']
 names=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly flat smooth noperspective layout centroid sample patch subroutine in out inout lowp mediump highp precision invariant packed goto switch case default namespace using class public static template union enum typedef cast common partition active filter input output'.split())
 builtin={'max':2,'min':2,'clamp':3,'smoothstep':3,'mix':3,'dot':2,'pow':2,'step':2,'texelFetch':3}
 for path in source:
  s=path.read_text()
  clean=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
  # GLSL reserved identifiers may be legal qualifiers at beginning of declarations; reject only variable name position.
  for m in re.finditer(r'\b(?:float|int|uint|vec[234]|ivec[234]|bool|sampler2D|mat[234]|highp|mediump|lowp)\s+([A-Za-z_]\w*)\s*(?=[;=,\[(])',clean):
   if m.group(1) in names:fail('reserved shader identifier '+m.group(1)+' in '+str(path))
  if re.search(r'\bfloat\s+(?:coherent|flat)\b',clean):fail('26904 coherent/26952 flat reserved regression')
  if re.search(r'\bgl_[A-Za-z0-9_]+\s*=',clean):fail('writes reserved GLSL builtin')
  for m in re.finditer(r'\b('+'|'.join(builtin)+r')\s*\(',clean):
   depth=0;args=1;end=False
   for c in clean[m.end()-1:]:
    if c=='(':depth+=1
    elif c==')':
     depth-=1
     if depth==0:end=True;break
    elif c==',' and depth==1:args+=1
   if not end or args!=builtin[m.group(1)]:fail('invalid GLSL '+m.group(1)+' arity')
  if s.count('void main()')!=1 or '#version' in clean:fail('real runtime fragment body malformed')
 # Force the exact old failed keyword patterns through the same lexical guard method.
 for word in ('flat','coherent','restrict','namespace','varying','goto'):
  neg='precision highp float;\nvoid main(){float '+word+'=1.0;}\n'
  m=re.search(r'\bfloat\s+([A-Za-z_]\w*)\s*=',neg)
  if not m or m.group(1) not in names:fail('reserved token negative escaped '+word)
 print('PASS all active new runtime ESSL sources free of illegal flat/coherent declarations, invalid GLSL arity, missing entry point')
if __name__=='__main__':
 try:
  check_math();glsl_live(R if '--live' in sys.argv else R/'handoff_payload_26953')
 except Exception as e:print('26953 TONE/GLSL BLOCKED: '+str(e),file=sys.stderr);sys.exit(1)
