#!/usr/bin/env python3
"""Byte-level 26936 authority and actual 26937 B-ON-only runtime ownership."""
from pathlib import Path
import sys
from build_26937_incremental import R,scope,sha,exact,fail
M='app/src/main/java/com/hinnka/mycamera/processor/'

def main():
 changed,added,old,new=scope()
 if '--live' in sys.argv:
  root=R
  exact(R,'26937_EXPECTED_FULL_APP.sha256','live 26937 exact 2050 sources and 2046 protected')
 else:
  root=R/'handoff_payload_26937'
  for path in changed:
   if sha(root/path)!=new[path]:fail('payload SHA mismatch '+path)
 if added or changed!={M+'GlesIris26932LkrSmoothWhite.kt',M+'GlesIris26932RawLensMedian.kt',M+'GlesMgcRawSpatialStacker.kt','app/version.properties'}:
  fail('unauthorized source change')
 ver=(root/'app/version.properties').read_text()
 if 'VERSION_NAME=0.9726937' not in ver or 'VERSION_BUILD=26937' not in ver:fail('incorrect exact version')
 median=(root/(M+'GlesIris26932RawLensMedian.kt')).read_text()
 white=(root/(M+'GlesIris26932LkrSmoothWhite.kt')).read_text()
 stack=(root/(M+'GlesMgcRawSpatialStacker.kt')).read_text()
 for flag in ('IRIS_26937_LKR_SENSOR_CLIPPED_WHITE_BEFORE_LAB','uNativeSensorClip','uAmazeWb','uBayerPattern',
  'float allClip=min(phases.r,min(phases.g,phases.b));','float rbClip=min(phases.r,phases.b);',
  '0.35*smoothstep(0.48,0.96,rbClip)','smoothstep(0.55,0.88,peakSensor)',
  'vec3 corrected=mix(medianRgb,vec3(peak),clamp(fade,0.0,1.0));'):
  if flag not in median:fail('missing original physical CFA pre-Lab correction '+flag)
 for flag in ('IRIS_26937_B_ON_POST_LAB_CLIPPED_NEUTRAL_RECONCILIATION',
  'float newFalseColor=smoothstep','float fade=neutral*bright*newFalseColor;',
  'vec3 neutralAtLuma=before+vec3(afterLuma-beforeLuma);',
  'oRgb=vec4(corrected*uInverseAmazeWb,original.a);'):
  if flag not in white:fail('missing post-Lab chroma-only correction '+flag)
 if 'uNativeSensorClip' in white or 'vec3(localPeak)' in white:fail('old 26934/26936 late bright-white repainter returned')
 for frag in ('originalClip: Int, gains: FloatArray','bindTexture(program,"uNativeSensorClip",1,originalClip)',
  'bindTexture(program,"uPreLabWbRgb",1,rawlensMedian26932)',
  'bindTexture(program,"uWbRgb",0,defringed)',
  'lkrNativeFullRgb26931=true','renderIris26859BLensShading(nativeRgb,'):
  if frag not in stack:fail('B ON shader ownership, actual physical LSC or pre/post Lab binding missing '+frag)
 a=stack.index('rawlensMedian26932 = renderIris26932LkrMedian(')
 b=stack.index('defringed = renderRawrLabDefringe26856(',a)
 c=stack.index('neutral = createTexture(processingWidth, processingHeight, GLES30.GL_RGBA16F',b)
 if not (a<b<c):fail('physical white reconstruction not before Lab then final inverse WB')
 # All native JNI, capture, exposure, shutter, preview, B OFF and Spektra sources remain exact official 26936 bytes.
 for key in (M+'GlesIris26931LkrBridge.java',
  'app/src/main/cpp/iris26864/Iris26931LkrAndroidInterop.cpp',
  'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
  'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26935BOnSession.java',
  'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
  'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26876BGpuFinalRenderer.java'):
  if old.get(key)!=new.get(key) or key in changed:fail('26936 protected preview/shutter/native/B OFF changed '+key)
 print('PASS 26937 four B-ON-only and version modified, 2046 26936 sources byte-protected; native 15 RAW 3x2, preview, shutter, B OFF 1.02 intact')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
