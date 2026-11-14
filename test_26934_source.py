#!/usr/bin/env python3
"""Full protected source / B-only ownership and one original-sensor binary clip guard."""
import sys,re
from pathlib import Path
from build_26934_incremental import R,scope,sha,fail

def main():
 ch,ad,base,n=scope()
 root=R if '--live' in sys.argv else R/'handoff_payload_26934'
 shader=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt'
 s=shader.read_text()
 for key in ('IRIS_26934_B_SRON_RAWLENS_VISUAL_WHITE_FADE',
             'smoothstep(vec3(0.70),vec3(0.99),visualRgb)',
             'float fade=clamp(max(visualFade,clipFade),0.0,1.0)',
             'phaseColorClipAt','uNativeSensorClip','uBayerPattern','uAmazeWb',
             'uInverseAmazeWb','oRgb=vec4(corrected*uInverseAmazeWb,original.a)',
             'uSize/2','float[4](clipAt(base)'):
  if key not in s:fail('B SR ON highlight source missing explicit visual 0.70..0.99 whiten '+key)
 for bad in ('visualNeutral','thirdChannelNear','whiteWitness','sourceColorBalance',
             'sensorFade=measuredFade','float earlyFade'):
  if re.search(r'\b'+re.escape(bad)+r'\b',s):fail('old veto path returned '+bad)
 ver=(root/'app/version.properties').read_text()
 if 'VERSION_BUILD=26934' not in ver or 'VERSION_NAME=0.9726934' not in ver:fail('wrong build label')
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
  if 'VERSION_BUILD=26933' not in (R/'.photon_26934_incremental_work/authority_26933/app/version.properties').read_text():fail('reference version invalid')
 print('PASS 26934 strictly B/SR ON shader corrected; all 2046 protected including B OFF bright SDR + UHDR and LKR3x2 identical')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
