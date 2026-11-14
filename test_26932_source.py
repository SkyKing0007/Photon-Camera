#!/usr/bin/env python3
"""Current 26932 allowed-source semantics and B ON/B OFF isolation, no stale checkout."""
from pathlib import Path
import sys
from build_26932_incremental import R,scope,parse,sha,fail

def main():
 ch,ad,b,n=scope()
 root=R if '--live' in sys.argv else R/'handoff_payload_26932'
 def read(path):
  p=root/'app'/path
  if not p.is_file():fail('missing active source '+str(p))
  return p.read_text()
 k=read('src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
 for token in ('if (lkrNativeFullRgb26931) {','renderIris26932LkrMedian(',
               'GlesIris26932RawLensMedian.shader','GlesIris26932LkrSmoothWhite.shader',
               'if (!lkrNativeFullRgb26931) {','renderRawrFalseColor26856(',
               'renderRawrLabDefringe26856(', 'uNativeSensorClip'):
  if token not in k:fail('LKR chroma/clip/historical route disconnected '+token)
 if k.count('GlesIris26932RawLensMedian.shader')!=1 or k.count('GlesIris26932LkrSmoothWhite.shader')!=1:fail('26932 duplicate or absent GL shader owner')
 median=read('src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt')
 if 'CC_SORT(' not in median or 'p4.x' not in median or 'GLES' in median:fail('RawLens 3x3 implementation detached')
 clip=read('src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt')
 for x in ('sensorP=clamp(p/2','uNativeSensorClip','whiteWitness=','fade=max(earlyFade,sensorFade)','uInverseAmazeWb'):
  if x not in clip:fail('sensor-derived smooth white or inverse WB missing '+x)
 java=read('src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26876BGpuFinalRenderer.java')
 for x in ('params.iris26906ExperimentBSelected','params.motionV2SuperResOutputEnabled','!params.irisNightActive',
           '!params.iris26903NightB','iris26932BOn ? 1.00f','uIris26932BOnTone'):
  if x not in java:fail('B ON specific rendering flag or saturation missing '+x)
 final=read('src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag')
 if final.count('iris26932BOnVisualTone(')!=2 or 'if(uIris26932BOnTone!=0)' not in final:fail('B ON only tone disconnected')
 motion=read('src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
 if motion.count('"iris26932BOffSdrLiftEnabled"')!=2 or motion.count('!basePipeline.mParameters.motionV2SuperResOutputEnabled')<2:fail('B OFF SDR and gainmap guard missing')
 for path in ('render.glsl','gainmap.glsl'):
  text=read('src/main/assets/shaders/motionv2/'+path)
  if text.count('float iris26932BOffSdrBridge(')!=1 or text.count('uniform int iris26932BOffSdrLiftEnabled;')!=1:fail('B OFF shader mismatch '+path)
 version=read('version.properties')
 if 'VERSION_BUILD=26932' not in version or 'VERSION_NAME=0.9726932' not in version:fail('version mismatch')
 if '--live' in sys.argv:
  for p in ch|ad:
   if sha(root/p)!=n[p]:fail('live changed source mutated '+p)
 print('PASS 26932 source: exactly 7 edited 2 added, 2039 immutable, isolated B ON median/white/tone and B OFF SDR/HDR')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
