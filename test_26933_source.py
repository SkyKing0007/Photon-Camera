#!/usr/bin/env python3
"""Full protected source / B-only ownership and one original-sensor binary clip guard."""
import sys
from pathlib import Path
from build_26933_incremental import R,scope,sha,fail

def main():
 ch,ad,base,n=scope()
 root=R if '--live' in sys.argv else R/'handoff_payload_26933'
 shader=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt'
 s=shader.read_text()
 for key in ('IRIS_26933_B_ON_CLIPPED_WHITE_DOMAIN_CORRECT','visualNeutral=','thirdChannelNear=',
             'sensorFade=measuredFade*thirdChannelNear*brightWitness','clipAt(sensorP)',
             'uNativeSensorClip','uBayerPattern','uAmazeWb','uInverseAmazeWb',
             'oRgb=vec4(mix(original.rgb,vec3(neutral)',
             'uSize/2','float[4](clipAt(base)'):
  if key not in s:fail('B SR ON highlight source missing verified upstream invariant '+key)
 for bad in ('whiteWitness=','sourceColorBalance=','oRgb=original;','gl_FragCoord.xy+','uNativeSensorClip='):
  if bad in s:fail('26932 faulty source/domain returned '+bad)
 ver=(root/'app/version.properties').read_text()
 if 'VERSION_BUILD=26933' not in ver or 'VERSION_NAME=0.9726933' not in ver:fail('wrong build label')
 if '--live' in sys.argv:
  for p in ch|ad:
   if sha(root/p)!=n[p]:fail('live edited source inconsistent with published candidate '+p)
  for k in ('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
            'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt',
            'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26858BNoiseHighlight.kt',
            'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26876BGpuFinalRenderer.java',
            'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
            'app/src/main/assets/shaders/motionv2/gainmap.glsl',
            'app/src/main/assets/shaders/motionv2/render.glsl',
            'app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag'):
   if sha(root/k)!=base[k]:fail('B OFF or active routing/color/UHDR source changed '+k)
  router=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
  for token in ('if(lkrNativeFullRgb26931)','GlesIris26932LkrSmoothWhite.shader','if (!lkrNativeFullRgb26931)',
                'GlesIris26932RawLensMedian.shader','renderRawrLabDefringe26856('):
   if token not in router:fail('LKR selected branch missing '+token)
  if router.count('GlesIris26932LkrSmoothWhite.shader')!=1:fail('B ON shader duplicated/never called')
  if 'VERSION_BUILD=26932' not in (R/'.photon_26933_incremental_work/authority_26932/app/version.properties').read_text():fail('reference version invalid')
 print('PASS 26933 strictly B/SR ON shader corrected; all 2046 protected including B OFF bright SDR + UHDR and LKR3x2 identical')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
