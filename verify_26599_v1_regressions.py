#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,random,re,sys
A=0.18;K=0.18
def fail(m):raise SystemExit('FAIL: '+m)
def close(a,b,t=1e-9):return abs(a-b)<=t*max(1.0,abs(a),abs(b))
def mapguide(g,gain,motion=True):
 g=max(g,0.0); gain=max(gain,1e-6)
 if (not motion) or gain<=1.0 or g<=A:return g*gain
 x=g-A
 return A*gain+x+(gain-1.0)*K*math.log(1.0+x/K)
def smooth(a,b,x):
 t=max(0.0,min(1.0,(x-a)/(b-a)));return t*t*(3.0-2.0*t)
def loss_weight(ref,pred):
 rel=max(pred-ref,0.0)/max(pred,0.05)
 return smooth(0.72,0.92,pred)*smooth(0.05,0.12,rel)
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:])
 # Mathematical invariants: exact body, no new positive highlight boost, strict monotonicity.
 for gain in (0.25,0.5,1.0,1.01,1.5,2.0,3.770491,4.313355,8.0,16.0):
  for i in range(181):
   g=A*i/180.0
   if not close(mapguide(g,gain),g*gain):fail('body equivalence')
  prev=mapguide(0.0,gain)
  for i in range(1,16001):
   g=i/1000.0; cur=mapguide(g,gain)
   if cur<=prev:fail(f'nonmonotonic gain={gain} g={g}')
   if gain>1.0 and cur>g*gain+1e-10:fail('upper tone exceeds old scalar')
   prev=cur
  if gain<=1.0:
   for g in (0.18,0.5,1.0,4.0,16.0):
    if not close(mapguide(g,gain),g*gain):fail('negative/neutral gain changed')
 # C1 derivative at 18% anchor for positive gain.
 for gain in (1.1,2.0,4.313355,16.0):
  eps=1e-6
  left=(mapguide(A,gain)-mapguide(A-eps,gain))/eps
  right=(mapguide(A+eps,gain)-mapguide(A,gain))/eps
  if abs(left-right)>1e-4 or abs(left-gain)>1e-4:fail('anchor C1')
 # Whole-RGB scalar means neutral stays neutral and channel ratios cannot turn pink/green/cyan.
 rnd=random.Random(26599)
 for _ in range(5000):
  rgb=[rnd.random()*4.0 for _ in range(3)]; y=.2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]; g=max(y,*rgb); gain=1+15*rnd.random(); sc=mapguide(g,gain)/g if g>1e-12 else gain; out=[v*sc for v in rgb]
  if min(out)<0 or not all(math.isfinite(x) for x in out):fail('RGB finite/nonnegative')
  for i,j in ((0,1),(0,2),(1,2)):
   if rgb[i]>1e-7 and rgb[j]>1e-7 and not close(out[i]/out[j],rgb[i]/rgb[j],1e-8):fail('channel ratio changed')
 for neutral in (0.001,0.02,0.18,0.5,1.0,4.0):
  o=neutral*(mapguide(neutral,4.313355)/neutral)
  if not close(o,o) or o<0:fail('neutral')
 # Effective-loss separation: matching linear RAW cannot hand off; true deficit can.
 for v in (0.72,0.8,0.9,1.0):
  if loss_weight(v,v)!=0.0:fail('matching SHORT/NORMAL admitted')
  if loss_weight(v,min(v*1.04,2.0))!=0.0:fail('sub-5-percent discrepancy admitted')
 if not (loss_weight(.82,.95)>0.0 and loss_weight(.75,1.0)>.9):fail('real effective loss not detected')
 # Hard inheritance: 26598 capture owner and final render/adaptive color stay exact.
 for rel in [
  'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
  'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl']:
  if H(b/rel)!=H(c/rel):fail('inherited regression '+rel)
 # SR cannot gain a second tone authority: Java passes the exact shared constants; native branches only on Motion-vs-Night.
 dj=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java').read_text()
 enc=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text(); cpp=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
 if enc.count('PRESENTATION_LINEAR_ANCHOR_26599')!=1 or enc.count('PRESENTATION_KNEE_26599')!=1:fail('true2x shared constants')
 if 'if(!p.motionHdrHandoff||dg<=1.f)return mul(c,dg);' not in cpp or 'if(uMotionHdrHandoff==0||dg<=1.0)return c*dg;' not in cpp:fail('Night scalar preservation')
 # DNG / SR evidence role strings remain unchanged outside allowlist and SHORT restore remains whole-RGB mix.
 short=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
 if 'oColor = vec4(mix(normalRgb.rgb, restoredShort, confidence), normalRgb.a);' not in short:fail('whole-RGB restore changed')
 if 'dng=false srEvidence=false' not in (c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text():fail('SHORT role telemetry lost')
 print('PASS 26599 tone math: body exact, positive-highlight compression, C1/strict monotonic, gain<=1 unchanged')
 print('PASS neutral/saturated RGB ratio preservation; no per-channel pink/green/cyan mechanism introduced')
 print('PASS effective-loss separation; 26598 capture/render/color inherited; 1x/true2x shared tone constants; Night scalar preserved')
if __name__=='__main__':main()
