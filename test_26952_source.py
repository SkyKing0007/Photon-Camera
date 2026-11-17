#!/usr/bin/env python3
"""26952 exact 26951 source-invariance, 3x2 LKR caller and only new artifact ownership."""
from pathlib import Path
import re,sys
from build_26952_incremental import R,scope,sha,parse,fail

def check():
 changed,added,old,new=scope()
 root=R if '--live' in sys.argv else R/'handoff_payload_26952'
 bridge='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26931LkrBridge.java'
 baseline=(R/'26952_BASE_LKR_NATIVE_BRIDGE_REFERENCE.java').read_text()
 if sha(R/'26952_BASE_LKR_NATIVE_BRIDGE_REFERENCE.java')!=old[bridge] or (root/bridge).read_text()!=baseline.replace('2.2.86','2.3.94'):fail('3x2 bridge modified beyond official release name')
 for p in changed|added:
  if not (root/p).is_file() or sha(root/p)!=new[p]:fail('bad overlay '+p)
 if '--live' in sys.argv:
  for p,h in new.items():
   if sha(R/p)!=h:fail('not successful 26951-based current source '+p)
  protected=[
   'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt',
   'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
   'app/src/main/assets/shaders/motionv2/gainmap.glsl',
   'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
   'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMerge.comp',
   'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp',
   'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp',
  ]
  for p in protected:
   if p not in old or old[p]!=new[p] or sha(R/p)!=old[p]:fail('retired pipeline/source regression '+p)
  lkr=(R/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26931LkrBridge.java').read_text()
  base_lkr=(R/'26952_BASE_LKR_NATIVE_BRIDGE_REFERENCE.java').read_text()
  if lkr!=base_lkr.replace('2.2.86','2.3.94'):fail('LKR bridge altered beyond correct official binary version announcement')
  for x in ('T=3, DATA_STEPS=2, OUTPUT_SCALE=2','tuning[0]=T;','tuning[1]=DATA_STEPS;','LkrBridge.nativeMerge(input','Math.multiplyExact(w,2)','Math.multiplyExact(h,2)'):
   if x not in lkr:fail('3x2 schedule and native 50MP routing violated '+x)
  if '8x4' in lkr or '8*4' in lkr:fail('RawLens 8x4 schedule illegally restored')
 med=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt').read_text()
 for needle in ('cc_median(p,m0,1)','cc_median(p,m0,2)','dot(wide,wide)<dot(fine,fine)?wide:fine','vec3(c.g+d.x,c.g,c.g+d.y)','neutralCameraRgb=mix(cameraRgb,cameraWhite,whiteBlend);'):
  if needle not in med:fail('two-radius color reconstruction missing '+needle)
 render=(root/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
 for needle in ('iris26952ConstrainRim(sourceXY,linearSrgb);', 'iris26948BUniversalSdrEnabled==0','iris26592MotionHdrHandoff==0','return rgb*(max(peak*0.975,limited)/max(peak,1.0e-6));'):
  if needle not in render:fail('isolated B-only halo clamp missing '+needle)
 if render.count('iris26952ConstrainRim(sourceXY,linearSrgb);')!=1:fail('halo clamp applied multiple times')
 if 'float flat=' in render or render.count('float plateauDelta=abs(bright1-bright2);')!=1:fail('26952 V3 real compiler reserved flat regression')
 for name in ('coherent','volatile','restrict'):
  glsl=med.split('"""#version 300 es',1)[1].split('""".trimIndent()',1)[0]
  glsl=re.sub(r'//[^\n]*|/\*.*?\*/','',glsl,flags=re.S)
  if re.search(r'\b(?:float|int|bool|vec[234]|ivec[234])\s+'+name+r'\b',glsl):fail('reserved GLSL identifier '+name)
 if (root/'app/version.properties').read_text().count('VERSION_BUILD=26952')!=1:fail('wrong version')
 notice=(root/'app/src/main/assets/licenses/rawlens_2_3_94_lkr_gpl_notice.txt').read_text()
 if '6996d936c22e116f2f6083efe8402b4513310b48266f1efda6d18a162b5710b6' not in notice or 'GNU GENERAL PUBLIC LICENSE' not in notice:fail('official 2.3.94 redistribution notice absent')
 print('PASS 26952 2050 source protected, only four edits and GPL notice; preserved 3x2, FCC, AMaZE, B HDRq, Spektra, A, Night')
if __name__=='__main__':
 try:check()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
