#!/usr/bin/env python3
"""Exact 26947 published source --> B-only ten-file 26948 scope, no A/native/vendor edits."""
from build_26948_incremental import R,scope,sha,fail
import sys,re
P='app/src/main/java/com/particlesdevs/photoncamera/'
def main():
 ch,old,new=scope(); root=R if '--live' in sys.argv else R/'handoff_payload_26948'
 def read(path):
  f=root/path
  if path not in ch or not f.is_file() or sha(f)!=new[path]:fail('non-allowlisted/missing/tampered candidate '+path)
  return f.read_text()
 version=read('app/version.properties')
 if 'VERSION_BUILD=26948\n' not in version or 'VERSION_NAME=0.9726948' not in version:fail('version wrong')
 render=read('app/src/main/assets/shaders/motionv2/render.glsl')
 gain=read('app/src/main/assets/shaders/motionv2/gainmap.glsl')
 fused=read('app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag')
 mr=read(P+'processing/opengl/postpipeline/MotionV2Render.java')
 fx=read(P+'processing/ultrahdr/Iris26876BGpuFinalRenderer.java')
 cap=read(P+'capture/CaptureController.java')
 sh=read(P+'capture/Iris26909ShutterIsoMath.java')
 tr=read('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856True2xCfa.kt')
 off=read('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
 if render.count('iris26948BUniversalSdrEnabled')<3 or gain.count('iris26948BUniversalSdrEnabled')<2:fail('B-only disabled in SDR or gain-map')
 if mr.count('basePipeline.mParameters.iris26906ExperimentBSelected ? 1 : 0')<2 or 'params.iris26906ExperimentBSelected ? 1 : 0' not in fx:fail('B-only frozen capture identity not wired')
 for t in (render,gain,fused):
  for s in ('iris26948BHeadroomShoulder','smoothstep(1.50,2.70,target)','return mix(separated,former'):
   if s not in t:fail('smooth-white 26947 endpoint not kept '+s)
 if 'uIris26948BUniversalSdrEnabled!=0' not in fused or 'uNightBJinEnabled' not in fused:fail('B 2x primary/gain not intact')
 if 'iris26948BVerifiedPeriodNs(result)' not in cap or 'snapVerifiedBPlan(plan,' not in cap:fail('manual shutter path not connected')
 if 'uBNoiseMomentOwner26858==0' not in off or 'iris26948BRowCorrect' not in off:fail('B only raw row correction missing')
 if 'uRowFlickerEnabled==0' not in tr or 'iris26948BRowGain' not in tr:fail('true2x row correction missing')
 if any(p.startswith('app/src/main/cpp/') or 'Original' in p or '/vendor/' in p or '26850' in p for p in ch):fail('A/native or vendor modified')
 if {p:old[p] for p in old if p not in ch}!={p:new[p] for p in new if p not in ch}:fail('protected source changed')
 for key in ('verifiedMainsPeriodNs','snapVerifiedBPlan','original.targetEnergy'):
  if key not in sh:fail('flicker math not safely gated '+key)
 print('PASS 26948 EXACT 10 B-only shader/Kotlin/Java/source, 2044 protected including A/native/vendor and 26947 smooth white')
if __name__=='__main__':
 try:main()
 except Exception as e:print(e,file=sys.stderr);sys.exit(1)
