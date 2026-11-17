#!/usr/bin/env python3
"""26950 V2 matched B OFF/Night SDR highlight math, source routing and numeric monotonicity.
Static guard supplements, NEVER replaces, mandatory pinned glslang/SPIR-V/NDK/Java.
"""
import math,re,sys
from build_26950_incremental import R,scope,sha,fail
D='app/src/main/assets/shaders/motionv2/'
JAVA='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
FLAG='iris26950BOffHdrqSdrHighlightProtect'
def smooth(a,b,x):
 t=max(0.0,min(1.0,(x-a)/(b-a)));return t*t*(3.0-2.0*t)
def shoulder(t):
 if t<=0.82:return t
 excess=t-0.82
 old=0.82+0.18*(1.0-math.exp(-excess/0.18))
 separate=0.82+0.18*excess/(excess+0.18)
 a=smooth(1.5,2.7,t)
 return separate*(1-a)+old*a
def matched(prior,src,requested,protect):
 prior=max(prior,0.0)
 target=max(prior,max(src,0.0)*requested)
 if not protect or target<=0.82:return shoulder(target)
 anchor=max(prior,0.82)
 extra=max(target-anchor,0.0)
 restraint=0.75*(1.0-smooth(2.1,2.7,target))
 retained=anchor+extra/(1.0+restraint*extra)
 return shoulder(retained)
def extract(s,name):
 m=re.search(r'\bfloat\s+'+re.escape(name)+r'\s*\(',s)
 if not m:fail('missing function '+name)
 i=s.index('{',m.end());pos=i+1;depth=1
 while depth:
  if pos>=len(s):fail('unclosed GLSL '+name)
  if s[pos]=='{':depth+=1
  if s[pos]=='}':depth-=1
  pos+=1
 return s[m.start():pos]
def check():
 scope();root=R if '--live' in sys.argv else R/'handoff_payload_26950'
 files=(D+'render.glsl',D+'gainmap.glsl',JAVA)
 expected={p:h for p,h in scope()[2].items() if p in files}
 for p in files:
  if not (root/p).is_file() or sha(root/p)!=expected[p]:fail('current HDRQ SDR source does not match sealed candidate '+p)
 render=(root/files[0]).read_text();gain=(root/files[1]).read_text();java=(root/files[2]).read_text()
 for name,s in (('SDR render',render),('UHDR denominator',gain)):
  if s.count('uniform int '+FLAG+';')!=1:fail(name+' new GLSL flag absent or duplicate')
  if s.count('float iris26948BHeadroomShoulder(float target)')!=1:fail(name+' existing shoulder touched')
  code=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
  if re.search(r'\b(?:float|int|uint|vec[234]|ivec[234])\s+coherent\b',code):fail(name+' reserved GLSL identifier coherent')
  if '#version' in code or code.count('void main()')!=1:fail(name+' active GLES source invalid')
  for phrase in ('float anchor=max(prior,0.82);','float excess=max(target-anchor,0.0);','float restraint=0.75*(1.0-smoothstep(2.10,2.70,target));','float retained=anchor+excess/(1.0+restraint*excess);',f'if({FLAG}==0 || target<=0.82)'):
   if phrase not in code:fail(name+' original/limited highlighter altered '+phrase)
  if code.count('iris26948BMatchedSdrPrimary(')!=(3 if name=='SDR render' else 2):fail(name+' SDR target not consumed on all expected paths')
 original=extract(render,'iris26948BHeadroomShoulder')
 if re.sub(r'\s+','',original)!=re.sub(r'\s+','',extract(gain,'iris26948BHeadroomShoulder')):fail('original 26948 shoulder mismatch')
 rd=extract(render,'iris26948BMatchedSdrPrimary').replace('outputExposureScale','EXPOSURE')
 gn=extract(gain,'iris26948BMatchedSdrPrimary').replace('hdrExposureScale','EXPOSURE')
 if re.sub(r'\s+','',rd)!=re.sub(r'\s+','',gn):fail('SDR/UHDR denominator mathematical mismatch')
 if java.count('final boolean '+FLAG+' =')!=1 or java.count('glProg.setVar("'+FLAG+'",')!=2:fail('frozen B OFF/Night flag not identically bound in primary and gain map')
 block=java.split('final boolean '+FLAG+' =',1)[1].split(';',1)[0]
 for term in ('iris26906ExperimentBSelected','!basePipeline.mParameters.motionV2SuperResOutputEnabled','iris26941BOffHdrqLowZoom','iris26903NightB','motionV2Active'):
  if term not in block:fail('B HDRQ mode selector missing '+term)
 if 'iris26948BMatchedSdrPrimary(mappedGuide,guide)' not in render or 'iris26948BMatchedSdrPrimary(mappedGuide,sourceGuide)' not in render:fail('render global/local paths differ')
 if 'iris26948BMatchedSdrPrimary(finalSdr,sourceGuide)' not in gain:fail('gain map SDR mirror missing')
 n=0
 for prior in (0,.1,.3,.5,.7,.8,.82,.9,.97,1.0):
  for requested in (.75,1.,1.5,3.,6.):
   previous=-1
   for k in range(3001):
    src=3*k/3000
    base=matched(prior,src,requested,False)
    new=matched(prior,src,requested,True)
    target=max(prior,src*requested)
    if not (math.isfinite(new) and 0<=new<=base+1e-9):fail('new SDR clipped/brightened illegally')
    if target<=.82 or target>=2.7:
     if abs(base-new)>1e-12:fail('outside highlight interval SDR changed')
    if previous>new+1e-9:fail('new smooth shoulder causes false contours/nonmonotonic highlight')
    previous=new;n+=1
 # simultaneous scene/local-guide monotonicity, including empty/dark to extreme overexposure
 for slope in (0,.1,.2,.5,.8,1,2):
  for start in (0,.2,.4,.6,.8):
   for gainValue in (.75,1,1.5,3,6):
    previous=-1
    for i in range(3001):
     src=3*i/3000;prior=min(1.,start+slope*src)
     new=matched(prior,src,gainValue,True)
     if previous>new+1e-9:fail('joint source/local-guide monotonicity violation')
     previous=new;n+=1
 print('PASS 26950 V2 B OFF/Night-only brightness restriction, full SDR/gainmap mirror, original white endpoints, '+str(n)+' monotone highlight cases')
if __name__=='__main__':
 try:check()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
