#!/usr/bin/env python3
"""26937 successful compiled authority -> two 26938 changes, B ON white only."""
import sys
from build_26938_incremental import R,scope,sha,exact,fail
M='app/src/main/java/com/hinnka/mycamera/processor/'

def main():
 changed,added,old,new=scope()
 live='--live' in sys.argv
 root=R if live else R/'handoff_payload_26938'
 if live:exact(R,'26938_EXPECTED_FULL_APP.sha256','exact 26938 source full universe')
 else:
  for path in changed:
   if sha(root/path)!=new[path]:fail('payload mutated '+path)
 if added or changed!={M+'GlesIris26932RawLensMedian.kt','app/version.properties'}:
  fail('unexpected source change')
 v=(root/'app/version.properties').read_text()
 if 'VERSION_BUILD=26938' not in v or 'VERSION_NAME=0.9726938' not in v:fail('wrong version')
 s=(root/(M+'GlesIris26932RawLensMedian.kt')).read_text()
 for flag in ('IRIS_26938_B_ON_SINGLE_CAMERA_LINEAR_WHITE_OWNER',
  'float rawLensWhite=max(whiteCurve.r,max(whiteCurve.g,whiteCurve.b));',
  'vec3 sensorRgb=medianRgb/wb;',
  'float clippedPink=wrongMagenta*max(rbEvidence,greenEvidence);',
  'float fade=clamp(max(max(allEvidence,clippedPink),',
  'vec3 corrected=mix(medianRgb,vec3(luma),fade);',
  'oRgb=vec4(corrected,original.a);'):
  if s.count(flag)!=1:fail('single source white owner missing or duplicated '+flag)
 for bad in ('0.35*smoothstep(0.48,0.96,rbClip)','vec3 corrected=mix(medianRgb,vec3(peak)','float physicalEvidence=',
  'CC_SORT(x','uLkrPostWbRgb2'):
  if bad in s:fail('old ineffective clipped-white adjustment or second median '+bad)
 # Source bytes from historical 26937 are the only baseline. Protected sources
 # include the prior successful post-Lab neutral-only check and B OFF median/FCC.
 for key in (M+'GlesIris26932LkrSmoothWhite.kt',M+'GlesMgcRawSpatialStacker.kt',
  M+'GlesIris26870PostAmazeChroma.kt',M+'GlesIris26856RawrColorContract.kt',
  M+'GlesIris26931LkrBridge.java',
  'app/src/main/cpp/iris26864/Iris26931LkrAndroidInterop.cpp',
  'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
  'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26935BOnSession.java',
  'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
  'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26876BGpuFinalRenderer.java'):
  if old.get(key)!=new.get(key) or key in changed:fail('protected mode or native source modified '+key)
 print('PASS 26938 only one LKR median shader and version changed; 2048 protected incl native/viewfinder/shutter/B OFF exact')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26938 BLOCKED:',str(e),file=sys.stderr);sys.exit(1)
