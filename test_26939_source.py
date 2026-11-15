#!/usr/bin/env python3
"""26938 successful compiled authority -> two 26939 changes, B ON white only."""
import sys
from build_26939_incremental import R,scope,sha,exact,fail
M='app/src/main/java/com/hinnka/mycamera/processor/'

def main():
 changed,added,old,new=scope()
 live='--live' in sys.argv
 root=R if live else R/'handoff_payload_26939'
 if live:exact(R,'26939_EXPECTED_FULL_APP.sha256','exact 26939 source full universe')
 else:
  for path in changed:
   if sha(root/path)!=new[path]:fail('payload mutated '+path)
 if added or changed!={M+'GlesIris26932RawLensMedian.kt','app/version.properties'}:
  fail('unexpected source change')
 v=(root/'app/version.properties').read_text()
 if 'VERSION_BUILD=26939' not in v or 'VERSION_NAME=0.9726939' not in v:fail('wrong version')
 s=(root/(M+'GlesIris26932RawLensMedian.kt')).read_text()
 for flag in ('IRIS_26939_B_ON_RAWLENS_EARLY_CAMERA_LINEAR_WHITE_WINDOW',
  'vec3 cameraRgb=medianRgb/wb;',
  'vec3 cameraWhite=vec3(1.0)/wb;',
  'cameraWhite/=max(cameraWhite.r,max(cameraWhite.g,cameraWhite.b));',
  'vec3 whiteBlendRgb=smoothstep(vec3(0.70),vec3(0.99),cameraRgb);',
  'float whiteBlend=max(whiteBlendRgb.r,max(whiteBlendRgb.g,whiteBlendRgb.b));',
  'vec3 neutralCameraRgb=mix(cameraRgb,cameraWhite,whiteBlend);',
  'vec3 corrected=neutralCameraRgb*wb;',
  'oRgb=vec4(corrected,original.a);'):
  if s.count(flag)!=1:fail('RawLens pre-Lab white-window formula missing/duplicated '+flag)
 shader=s.split('val shader = """',1)[1].split('""".trimIndent()',1)[0]
 # Historical physical clipping texture remains as protected caller ABI, but
 # it must NOT drive any white blending in the active shader main().
 active=shader.split('void main(){',1)[1]
 for bad in ('originalClip(', 'phaseClip(', 'float allClip=',
  'float clippedPink=', 'wrongMagenta', 'nearNeutral', 'rbEvidence',
  'greenEvidence', 'physicalEvidence', 'uNativeSensorClip', 'uBayerPattern',
  'float luma=','vec3 corrected=mix(medianRgb,vec3(luma),',
  'float fade=clamp(', 'vec3(peak)', 'uLkrPostWbRgb2'):
  if bad in active:fail('unapproved post-clip threshold/colour veto or second median '+bad)
 if shader.count('CC_SORT(p')!=19:fail('original RawLens 19-exchange median changed')
 # Source bytes from historical 26938 are the only baseline. Protected sources
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
 print('PASS 26939 only one LKR median shader and version changed; 2048 protected incl native/viewfinder/shutter/B OFF exact')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26939 BLOCKED:',str(e),file=sys.stderr);sys.exit(1)
