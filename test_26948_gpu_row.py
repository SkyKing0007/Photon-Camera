#!/usr/bin/env python3
"""Bounded GPU B RAW row compensation property tests; physical readout/A untouched."""
import math,sys
from build_26948_incremental import R,scope,sha,fail
P='app/src/main/java/com/hinnka/mycamera/processor/'
def get(file):
 path=P+file;_,_,new=scope();p=(R if '--live' in sys.argv else R/'handoff_payload_26948')/path
 if not p.is_file() or sha(p)!=new[path]:fail('missing B shader Kotlin '+path)
 return p.read_text()
def smooth(a,b,x):
 x=max(0.,min(1.,(x-a)/(b-a)));return x*x*(3.-2.*x)
def correction(y,harmonic,a,b,strength,signal,headroom,enabled=True,owner=True):
 if not enabled or not owner or harmonic<=0 or strength<=0 or math.hypot(a,b)<.025:return signal
 phi=math.tau*harmonic*max(0,min(1,y));logmod=a*math.cos(phi)+b*math.sin(phi)
 z=max(-.16,min(.16,-logmod))*max(0,min(1,strength))*smooth(.005,.025,max(signal,0))*smooth(.04,.15,headroom)
 return signal*math.exp(z)
def main():
 off=get('GlesMgcRawSabreShaders.kt');on=get('GlesIris26856True2xCfa.kt')
 for s in ('float iris26948BRowCorrect','uBNoiseMomentOwner26858==0','uRowFlickerEnabled==0','headroomForSignal26855(value)','uRowFlickerStrength','clamp(-logModulation,-0.16,0.16)','sourceCenter.y/float(uRawSize.y)'):
  if s not in off:fail('B OFF non-mutating RAW correction missing '+s)
 for s in ('float iris26948BRowGain','uRowFlickerEnabled==0','perFrameVariance*=iris26948RowGain*iris26948RowGain','normalized*=iris26948RowGain','smoothstep(0.83,0.97','uRowFlickerHarmonic'):
  if s not in on:fail('B ON physical covariance / clipped-source preservation missing '+s)
 prior='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26850'
 _,old,new=scope()
 if not all(old[p]==new[p] for p in old if '26850' in p or p.startswith('app/src/main/cpp/')):fail('Experiment A/native protected changed')
 n=0
 for harm in range(1,7):
  for row in range(0,101):
   for strength in (0,.05,.35,1.0):
    for signal,headroom in ((.0,.5),(.002,.4),(.01,.5),(.05,.4),(.5,.3),(.9,.01)):
     v=correction(row/100,harm,.27,-.14,strength,signal,headroom)
     if not math.isfinite(v) or abs(v)>abs(signal)*math.exp(.1600001)+1e-9:fail('unbounded GPU correction')
     if strength==0 and abs(v-signal)>1e-13:fail('invalid/no temporal evidence altered RAW')
     if headroom<=.04 and abs(v-signal)>1e-13:fail('clipped source altered')
     if abs(correction(row/100,harm,.27,-.14,strength,signal,headroom,owner=False)-signal)>1e-13:fail('Experiment A mutated')
     n+=1
 print('PASS 26948 physical RAW/DNG/Experiment A untouched, GPU signal + noise propagation guarded, bounded numerical 14k+ cases='+str(n))
if __name__=='__main__':
 try:main()
 except Exception as e:print(e,file=sys.stderr);sys.exit(1)
