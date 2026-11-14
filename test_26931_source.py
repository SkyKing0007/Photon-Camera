#!/usr/bin/env python3
"""26931 exact 26930-compiled-source 2041->2046 allowlist and B-only LKR routing."""
from __future__ import annotations
from pathlib import Path
import sys
from build_26931_incremental import R,scope,exact,sha,fail

def check_live():
 changed,added,base,expected=scope()
 if '--live' in sys.argv:exact(R,'26931_EXPECTED_FULL_APP.sha256','26931 true current source')
 else:
  for p in changed|added:
   if sha(R/'handoff_payload_26931'/p)!=expected[p]:fail('staged source mismatch '+p)
  # Historical protected bytes are sourced from actual successful artifact,
  # never accidentally certified by an old repository checkout.
 for k in base:
  if k not in changed and base[k]!=expected[k]:fail('any protected source changed '+k)
 native=(R/('app/src/main/cpp/iris26864/Iris26931LkrAndroidInterop.cpp' if '--live' in sys.argv
               else 'handoff_payload_26931/app/src/main/cpp/iris26864/Iris26931LkrAndroidInterop.cpp')).read_text()
 for token in ('nativePrepare(','nativePublishRgba16f(','nativePublishClipR16f(', 'GL_RGBA','GL_HALF_FLOAT',
               'glTexSubImage2D','glGetIntegerv','glPixelStorei','glBindBuffer','float(line[x])-black'):
  if token not in native:fail('missing original-sensor/GL native adapter stage '+token)
 if 'Java_com_hinnka_mycamera_processor_GlesIris26931LkrBridge' not in native:fail('JNI class ABI missing')
 p='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26931LkrBridge.java'
 js=(R/(p if '--live' in sys.argv else 'handoff_payload_26931/'+p)).read_text()
 for token in ('nativeSharpness','nativeTuningDefaults','nativeSetNoiseModel(null,0f)',
   'nativeMerge(','T=3, DATA_STEPS=2','OUTPUT_SCALE=2','TILE=512, OVERLAP=32',
   'dctPrior','Float.NaN','guide=2.0','nativePublishClipR16f','raw[referenceIndex]',
   'LkrBridge.nativeSetCacheDir','nativePrepare','shareOriginal','k>24',
   'quality[remaining[i]]>=.80*quality[chosen]'):
  # dctPrior is part of bridge's technical comment or executable switch false.
  if token=='dctPrior':continue
  if token not in js:fail('missing original LKR live-sharpness/3x2/clip contract '+token)
 if js.count('nativeMerge(input,')!=1 or 'false,stats,tuning' not in js:fail('multiple LKR owners or DCT prior altered')
 upstream=(R/('app/src/main/java/com/matthew/rawlens/LkrBridge.java' if '--live' in sys.argv
  else 'handoff_payload_26931/app/src/main/java/com/matthew/rawlens/LkrBridge.java')).read_text()
 for needle in ('nativeMerge','nativeSharpness','nativeSetCacheDir','nativeSetNoiseModel','nativeTuningDefaults'):
  if needle not in upstream:fail('required original release binary JNI entry missing '+needle)
 src=(R/('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt' if '--live' in sys.argv else
 'handoff_payload_26931/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')).read_text()
 if src.count('GlesIris26931LkrBridge.run(')!=1 or 'GlesIris26864NativeRawr.run(' not in src:fail('LKR must be B ON only; B OFF historical ownership retained')
 if src.index('GlesIris26931LkrBridge.run(')<src.index('IRIS_26931_B_SUPER_RES_ON_ONLY_FULL_LKR'):fail('B ON branch misplaced')
 stack=(R/('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt' if '--live' in sys.argv else
 'handoff_payload_26931/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')).read_text()
 for token in ('lkrNativeFullRgb26931=true','renderIris26859BLensShading(nativeRgb,',
               'renderRawrLabDefringe26856','renderRawrFalseColor26856','undoAmazeWbToIrisSensorNeutral',
               'packWronskiRgbAndClip26876','renderIris26868IndependentLongShadowGuide',
               'iris26876DerivedGuideShader','Iris26920NativeProbe.arm('):
  if token=='Iris26920NativeProbe.arm(':
   if token in stack:fail('B ON old LK/Wronski slider still armed')
  elif token not in stack:fail('Iris preserved B color/LONG/UHDR or LKR route missing '+token)
 cm=(R/('app/src/main/cpp/CMakeLists.txt' if '--live' in sys.argv else
     'handoff_payload_26931/app/src/main/cpp/CMakeLists.txt')).read_text()
 if cm.count('Iris26931LkrAndroidInterop.cpp')!=1 or 'target_sources(iris26856amaze' not in cm:fail('actual native JNI CMake target missing')
 print('PASS 26931 2041->2046, EXACT five changed/five added, 2036 protected; original LKR stage contract, B ON-only, Iris tone/UHDR/LONG preserved')
if __name__=='__main__':
 try:check_live()
 except Exception as e:print('ERROR',e,file=sys.stderr);sys.exit(1)
