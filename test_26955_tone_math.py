#!/usr/bin/env python3
"""26955 +0.4 EV monotone highlight shoulder, hue, gainmap and ESSL keyword/arity tests."""
import math,re,sys
from build_26955_incremental import R,fail
EV=.4;SCALE=2**EV;KNEE=.125;WIDTH=1-KNEE;END_SLOPE=.30
# Cubic Hermite coefficients from 26954 V2's exact boundary constraints:
# F(0.125)=KNEE*SCALE, F'(0.125)=SCALE, F(1)=1, F'(1)=.30
P0=KNEE*SCALE;M0=WIDTH*SCALE;M1=WIDTH*END_SLOPE
A=2*P0+M0-2+M1;B=-3*P0-2*M0+3-M1;C=M0;D=P0
GLSL=(float('-0.2530536003804941'),float('-0.06645431039239985'),
      float('1.1545694219262823'),float('0.16493848884661177'))

def f(y):
 if y<=KNEE:return y*SCALE
 x=min(max((y-KNEE)/WIDTH,0),1)
 return ((GLSL[0]*x+GLSL[1])*x+GLSL[2])*x+GLSL[3]

def original_f(y):
 if y<=KNEE:return 2*y
 x=(y-KNEE)/WIDTH
 return ((.5125*x-1.5125)*x+1.75)*x+.25

def exposure(rgb):
 v=[max(x,0) for x in rgb];peak=max(v);sc=f(peak)/max(peak,1e-6)
 return [x*sc for x in v]

def gain(s,delta,offset=1e-4,limit=8):
 return min(max((s+max(delta,0)+offset)/(s+offset),1),limit)

def main():
 if abs(SCALE-1.3195079107728942)>1e-13:fail('EV constant mismatch')
 for got,want in zip(GLSL,(A,B,C,D)):
  if abs(got-want)>1e-13:fail('shader polynomial not C1 Hermite +0.4EV')
 last=-1
 for i in range(20001):
  y=i/20000;v=f(y)
  if not 0<=v<=1+1e-9 or (i and v<=last+1e-12):fail('flat/reversing/overflowing tonal ramp '+str(y))
  if y<=KNEE and abs(v-y*SCALE)>1e-12:fail('low/body not +0.4EV '+str(y))
  if v<y-1e-9 or v>original_f(y)+1e-9:fail('new brightness not between original and +1 EV '+str(y))
  last=v
 h=1e-5
 if abs((f(KNEE+h)-f(KNEE))/h-SCALE)>1e-3:fail('C1 entry slope lost')
 if abs((f(1)-f(1-h))/h-END_SLOPE)>1e-3:fail('nonzero white slope lost')
 if abs(f(KNEE)-P0)>1e-12 or abs(f(1)-1)>1e-12:fail('curve endpoint lost')
 for i in range(30001):
  rgb=[((i*37)%997)/997,((i*59)%991)/991,((i*73)%983)/983]
  out=exposure(rgb)
  if min(out)<-1e-9 or max(out)>1+1e-9:fail('gamut overflow')
  scales=[out[j]/rgb[j] for j in range(3) if rgb[j]>1e-9]
  if scales and max(scales)-min(scales)>1e-9:fail('RGB channels changed relative hue')
  if max(rgb)<=KNEE and max(abs(out[j]-rgb[j]*SCALE) for j in range(3))>1e-9:fail('RGB +0.4EV off')
 for y in (0,.01,.07,.125,.2,.35,.5,.75,.9,1):
  new=f(y)
  for delta in (0,.01,.1,.2,.6,1,3):
   oldratio=gain(y,delta);newratio=gain(new,delta)
   if not 1-1e-10<=newratio<=8+1e-10:fail('UHDR gain bounds')
   if delta>0 and newratio<=1:fail('HDR highlight pop missing')
   if newratio>oldratio+1e-10:fail('gain did not adapt to brighter SDR denominator')
   if delta==0 and abs(newratio-1)>1e-11:fail('false HDR gain')
 if original_f(.6)<=f(.6) or abs(f(.01)/.01-SCALE)>1e-9:fail('1EV change missing')
 # Strict same-image scene-independent scalar: no spatial neighborhood operands in new section.
 src=(R if '--live' in sys.argv else R/'handoff_payload_26955')/'app/src/main/assets/shaders/motionv2/render.glsl'
 code=src.read_text();portion=code.split('    if(iris26954BOffNight26940Sdr!=0){\n        const float iris26954SdrExposureScale=',1)[1].split('    Output=clamp(',1)[0]
 for forbidden in ('texture(', 'texelFetch(', 'displayGain', 'sourceGuide','imageMedian','sdrBridge','iris26948BMatched'):
  if forbidden in portion:fail('HDR/scene-adaptive/spatial processing in fixed global exposure '+forbidden)
 if code.count('const float iris26954SdrExposureScale=1.3195079107728942;')!=1:fail('new exposure scale absent')
 if 'mappedPeak=((-0.2530536003804941*x-0.06645431039239985)*x+1.1545694219262823)*x+0.16493848884661177;' not in portion:fail('GLSL actual polynomial differs')
 print('PASS 26955 exact +0.4 EV factor=%.12f, 20001 strict tones C1 nonzero-slope highlights, 30001 unchanged RGB ratios, new SDR real gainmap denominator'%SCALE)

def glsl():
 reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly flat smooth noperspective layout centroid sample patch subroutine in out inout lowp mediump highp precision invariant packed goto switch case default namespace using class public static template union enum typedef cast common partition active filter input output'.split())
 keywords={'max':2,'min':2,'clamp':3,'smoothstep':3,'mix':3,'dot':2,'pow':2,'step':2,'texelFetch':3}
 root=R if '--live' in sys.argv else R/'handoff_payload_26955'
 for name in (('render','gainmap') if '--live' in sys.argv else ('render',)):
  p=root/'app/src/main/assets/shaders/motionv2'/(name+'.glsl');s=p.read_text()
  body=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
  if s.count('void main()')!=1 or '#version' in body:fail('GLSL body malformed '+name)
  for m in re.finditer(r'\b(?:float|int|uint|vec[234]|ivec[234]|bool|sampler2D|mat[234]|highp|mediump|lowp)\s+([A-Za-z_]\w*)\s*(?=[;=,\[(])',body):
   if m.group(1) in reserved:fail('GLSL illegal reserved variable '+m.group(1)+' in '+name)
  if re.search(r'\bfloat\s+(?:flat|coherent|restrict)\b',body):fail('26904/26952 illegal GLSL keyword')
  if re.search(r'\bgl_[A-Za-z0-9_]+\s*=',body):fail('writes GLSL builtin')
  for m in re.finditer(r'\b('+'|'.join(keywords)+r')\s*\(',body):
   depth=0;args=1;done=False
   for c in body[m.end()-1:]:
    if c=='(':depth+=1
    elif c==')':
     depth-=1
     if not depth:done=True;break
    elif c==',' and depth==1:args+=1
   if not done or args!=keywords[m.group(1)]:fail('wrong GLSL arity '+m.group(1))
 for bad in ('coherent','flat','restrict','namespace','varying'):
  m=re.search(r'\bfloat\s+([A-Za-z_]\w*)\s*=', 'void main(){float '+bad+'=1.0;}')
  if not m or m.group(1) not in reserved:fail('broken negative-keyword regression '+bad)
 print('PASS current shader reserved coherent/flat/restrict/namespace keyword/arity static; negative injection tests')
if __name__=='__main__':
 try:main();glsl()
 except Exception as e:print('26955 TONE/GLSL BLOCKED '+str(e),file=sys.stderr);sys.exit(1)
