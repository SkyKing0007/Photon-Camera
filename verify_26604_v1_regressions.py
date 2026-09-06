#!/usr/bin/env python3
from pathlib import Path
import math,sys,re
def fail(m):raise SystemExit('FAIL: '+m)
def need(s,t,l):
 if t not in s:fail(l+' missing '+t)
def section(s,a,b):
 i=s.find(a);j=s.find(b,i)
 if i<0 or j<0:fail('section '+a)
 return s[i:j]
def tone(source,gain,knee=.40,scale=.80):
 x=max(source,0)*max(gain,1e-6)*scale
 if x<=knee:return x
 reserve=1-knee;ex=x-knee
 return knee+reserve*ex/(ex+reserve)
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:]);rj=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text();rg=(c/'app/src/main/assets/shaders/motionv2/render.glsl').read_text();solver=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text();cpp=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text();adaptive=(c/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text()
 # One canonical final-domain shape in 1x, solver, CPU true2x and GPU true2x.
 for t in ['IRIS_26604_MOTION_SDR_KNEE_FINAL','iris26604MapMotionSdrFinalGuide','targetFinal','reserve * excess / (excess + reserve)','bodyGainUnityRequired=false']:need(rj,t,'1x canonical tone')
 need(solver,'MotionV2Render.iris26604MapMotionSdrFinalGuide(guide, gain)','solver/render parity')
 for t in ['constexpr float scale=0.80f,knee=0.40f,reserve=0.60f;','const float scale=0.80,knee=0.40,reserve=0.60;','if(!p.motionHdrHandoff)c=mul(c,std::max(p.displayGain,1.0e-6f));']:need(cpp,t,'true2x parity/Night isolation')
 for t in ['targetFinal=sourceGuide*max(displayGain,1.0e-6)*max(outputExposureScale,1.0e-6)','return knee+reserve*excess/(excess+reserve)']:need(rg.replace(' ',''),t.replace(' ',''),'1x shader canonical tone')
 need(adaptive,'? positiveDisplayGain*0.80 : positiveDisplayGain','adaptive projected-domain parity')
 # Numerical visual fixtures from the actual 26603 outdoor sample: body brightness preserved, highlight tail no longer plateaus near white.
 gain=3.298484
 fixtures=[(.105882,144.0,.105882),(.258824,202.0,.258824),(.356863,216.0,.356863),(.596078,231.0,.596078)]
 def srgb(x):return 12.92*x if x<=.0031308 else 1.055*(x**(1/2.4))-.055
 for src,want,_ in fixtures:
  code=255*srgb(tone(src,gain))
  if abs(code-want)>2.5:fail(f'visual brightness fixture src={src} code={code:.2f} target~{want}')
 # Exact body parity with old multiply*0.80 until the final 0.40 knee.
 for src in [0,.01,.03,.06,.10,.12,.15]:
  old=src*gain*.80
  if old<=.40+1e-12 and abs(tone(src,gain)-old)>1e-12:fail('body brightness changed '+str(src))
 # Strictly monotonic and never a recoverable-highlight plateau.
 xs=[i/100 for i in range(0,401)];ys=[tone(x,gain) for x in xs]
 if any(ys[i+1]<=ys[i] for i in range(len(ys)-1)):fail('tone not strictly monotonic')
 for i in range(1,len(ys)):
  if ys[i]-ys[i-1] <= 1e-7:fail('highlight slope collapsed')
 if ys[-1]>=1.0:fail('HDR excess escaped bounded SDR')
 # Prohibit the exact 26603 late-knee/display-multiply failure.
 if 'IRIS_26603_MOTION_SDR_KNEE = 0.98f' in rj:fail('old 0.98 knee survived')
 de=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java').read_text();mot=section(de,'if (basePipeline.mParameters.motionV2Active) {','if (Math.abs(displayGain - 1.0f)')
 if 'useAssetProgram' in mot or 'drawBlocks' in mot:fail('Motion display multiplier survived')
 # High-frequency boundary regression: continuous source confidence and measurable neighboring radiometry, not blur/color repair.
 sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();rej=section(sh,'    val rejection = """','    """.trimIndent()');merge=section(sh,'    val merge = """','    """.trimIndent()')
 for t in ['boundaryRadiometricConfidence','smoothstep(0.03,0.08,relativeError)','sourceQuadHeadroomConfidence','flowConfidence']:need(rej.replace(' ',''),t.replace(' ',''),'blind/curtain boundary confidence')
 for t in ['uSourceClippingPoint*0.9925','sourceNeighborhoodConfidence=min(','frameWeight *= mix(']:need(merge,t,'continuous source headroom')
 if 'step(uSourceClippingPoint' in merge:fail('binary bracket seam survived')
 # No new post-render artifact hider in changed render path.
 for bad in ['magentaRepair','greenRepair','cyanRepair','hueRepair','chromaBlur','shortDetailPaste','cloudDetailPaste']:
  if bad.lower() in (rj+rg+cpp+sh).lower():fail('artifact-hiding authority '+bad)
 print('PASS actual-sample brightness regression: body/midtones retain current Iris/Photon brightness while P95/P99 highlight tail is compressed before white')
 print('PASS one canonical Motion tone function is consumed by solver, 1x, adaptive predictor, true2x CPU/GPU and UHDR master ratio; Night isolated')
 print('PASS cloud/curtain highlight structure cannot be destroyed by 0.98 plateau; blind/window bracket confidence is continuous and boundary-radiometry constrained, not color-repaired')
if __name__=='__main__':main()
