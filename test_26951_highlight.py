#!/usr/bin/env python3
"""26951 B OFF/Night matched SDR image + UHDR SDR-base tone shoulder. Static audit complements real compiler."""
import math,re,sys
from build_26951_incremental import R,scope,sha,fail
D='app/src/main/assets/shaders/motionv2/'
JAVA='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
FLAG='iris26951BOffHdrqSdrHighlightProtect'
def smooth(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)));return t*t*(3.-2.*t)
def shoulder(t):
 if t<=0.82:return t
 excess=t-0.82
 older=0.82+0.18*(1.-math.exp(-excess/0.18))
 separate=0.82+0.18*excess/(excess+0.18)
 fade=smooth(1.50,2.70,t)
 return separate*(1-fade)+older*fade
def matched(prior,source,requested,enabled):
 prior=max(prior,0.)
 target=max(prior,max(source,0.)*requested)
 if not enabled or target<=0.82:return shoulder(target)
 anchor=max(prior,0.82);excess=max(target-anchor,0.)
 restraint=0.75*(1.-smooth(2.1,2.7,target))
 retained=anchor+excess/(1.+restraint*excess)
 return shoulder(retained)
def extract(s,name):
 m=re.search(r'\bfloat\s+'+re.escape(name)+r'\s*\(',s)
 if not m:fail('missing GLSL function '+name)
 i=s.index('{',m.end());j=i+1;depth=1
 while depth:
  if j>=len(s):fail('unterminated GLSL function '+name)
  if s[j]=='{':depth+=1
  if s[j]=='}':depth-=1
  j+=1
 return s[m.start():j]
def check():
 _,_,source=scope()
 root=R if '--live' in sys.argv else R/'handoff_payload_26951'
 paths=(D+'render.glsl',D+'gainmap.glsl',JAVA)
 for p in paths:
  if not (root/p).is_file() or sha(root/p)!=source[p]:fail('26951 SDR/glsl/java unsealed '+p)
 render=(root/paths[0]).read_text();gain=(root/paths[1]).read_text();java=(root/paths[2]).read_text()
 for label,s in (('render',render),('gainmap',gain)):
  if s.count('uniform int '+FLAG+';')!=1:fail('unbound new SDR flag '+label)
  if s.count('float iris26948BHeadroomShoulder(float target)')!=1:fail('historical 26948 shoulder changed '+label)
  code=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
  if re.search(r'\bcoherent\b',code):fail('GLSL reserved coherent identifier '+label)
  if '#version' in code or code.count('void main()')!=1:fail('runtime-expanded GLSL invalid '+label)
  for t in ('float anchor=max(prior,0.82);','float excess=max(target-anchor,0.0);',
    'float restraint=0.75*(1.0-smoothstep(2.10,2.70,target));',
    'float retained=anchor+excess/(1.0+restraint*excess);',
    f'if({FLAG}==0 || target<=0.82)'):
   if t not in code:fail('SDR matched shoulder changed '+label+' '+t)
  if code.count('iris26948BMatchedSdrPrimary(')!=(3 if label=='render' else 2):fail('unequal output branches '+label)
 normalize=lambda s:re.sub(r'\s+','',s)
 if normalize(extract(render,'iris26948BHeadroomShoulder'))!=normalize(extract(gain,'iris26948BHeadroomShoulder')):fail('shoulder mismatches SDR/gainmap')
 a=extract(render,'iris26948BMatchedSdrPrimary').replace('outputExposureScale','EXPOSURE')
 b=extract(gain,'iris26948BMatchedSdrPrimary').replace('hdrExposureScale','EXPOSURE')
 if normalize(a)!=normalize(b):fail('SDR/gainmap matched denominator implementation diverged')
 if java.count('final boolean '+FLAG+' =')!=1 or java.count('glProg.setVar("'+FLAG+'",')!=2:fail('SDR and UHDR flag not both bound')
 owner=java.split('final boolean '+FLAG+' =',1)[1].split(';',1)[0]
 for token in ('iris26906ExperimentBSelected','!basePipeline.mParameters.motionV2SuperResOutputEnabled','iris26941BOffHdrqLowZoom','iris26903NightB','motionV2Active'):
  if token not in owner:fail('wrong B-only owner '+token)
 if 'iris26948BMatchedSdrPrimary(mappedGuide,guide)' not in render or 'iris26948BMatchedSdrPrimary(mappedGuide,sourceGuide)' not in render:fail('render branches not matched')
 if 'iris26948BMatchedSdrPrimary(finalSdr,sourceGuide)' not in gain:fail('UHDR denominator not matched')
 n=0
 for prior in (0.,0.1,0.3,0.5,0.7,0.8,0.82,0.9,0.97,1.0):
  for req in (0.75,1.,1.5,3.,6.):
   last=-1.
   for i in range(3001):
    src=3*i/3000.;target=max(prior,src*req)
    old=matched(prior,src,req,False);new=matched(prior,src,req,True)
    if not math.isfinite(new) or not (0<=new<=old+1.e-9):fail('SDR highlight non-finite/brightened')
    if (target<=0.82 or target>=2.7) and abs(new-old)>1.e-12:fail('outside shoulder range changed')
    if last>new+1.e-9:fail('nonmonotone SDR halo shoulder')
    last=new;n+=1
 for slope in (0.,0.1,0.2,0.5,0.8,1.,2.):
  for start in (0.,0.2,0.4,0.6,0.8):
   for gainval in (0.75,1.,1.5,3.,6.):
    last=-1.
    for i in range(3001):
     src=3*i/3000.;prior=min(1.,start+slope*src)
     value=matched(prior,src,gainval,True)
     if last>value+1.e-9:fail('joint SDR source/local highlight nonmonotonic')
     last=value;n+=1
 print(f'PASS 26951 B OFF/Night matched SDR/gainmap, bounded sky/foliage headroom, {n} monotone cases')
if __name__=='__main__':
 try:check()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
