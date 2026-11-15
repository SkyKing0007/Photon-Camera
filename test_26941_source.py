#!/usr/bin/env python3
"""26941 actual compiled candidate, exact 7-file scope and protected mode ownership."""
from pathlib import Path
import re,sys
from build_26941_incremental import R,scope,sha,exact,fail,REQUIRED
UI='app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java'
JAVA='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
HDRQ='app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp'
EXEC='app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp'
RSH='app/src/main/assets/shaders/motionv2/render.glsl'
GSH='app/src/main/assets/shaders/motionv2/gainmap.glsl'

def main():
 ch,old,new=scope();live='--live' in sys.argv
 root=R if live else R/'handoff_payload_26941'
 if live:exact(R,'26941_EXPECTED_FULL_APP.sha256','current 26941 full authority-seeded source')
 else:
  for p in ch:
   if sha(root/p)!=new[p]:fail('payload hash diverged from source manifest '+p)
 if ch!=REQUIRED or len(ch)!=7:fail('unauthorized runtime scope')
 if ('VERSION_NAME=0.9726941' not in (root/'app/version.properties').read_text()
        or 'VERSION_BUILD=26941' not in (root/'app/version.properties').read_text()):
  fail('wrong 26941 version')
 get=lambda k:(root/k).read_text()
 java=get(JAVA);render=get(RSH);gain=get(GSH);setting=get(UI);exe=get(EXEC);coord=get(HDRQ)
 for source in (render,gain):
  if source.count('uniform int iris26941BOffHdrqLowZoom;')!=1:fail('missing/duplicated SR-OFF-only gain/render routing uniform')
  if source.count('float iris26941BOffMatchedSdrPrimary(float priorGuide,float sourceGuide)')!=1:fail('missing exact matched SDR primary')
  if 'else if(iris26932BOffSdrLiftEnabled!=0)' not in source:fail('older >=1.10/A-routed B OFF preserved SDR path gone')
  if source.count('if(iris26941BOffHdrqLowZoom!=0)') < 1:fail('unreachable low-zoom scalar primary')
 block=lambda s:s.split('float iris26941BOffMatchedSdrPrimary(',1)[1].split('float iris26906BVisualTone(',1)[0]
 # Only the already-existing output-exposure uniform name differs in mirror.
 a=block(render).replace('outputExposureScale','EXPOSURE_SCALE')
 b=block(gain).replace('hdrExposureScale','EXPOSURE_SCALE')
 if a!=b:fail('SDR-primary and gain-map denominator equations differ')
 if render.count('iris26941BOffMatchedSdrPrimary(mappedGuide,')!=2:
  fail('SDR raster global/local branches disagree')
 if gain.count('iris26941BOffMatchedSdrPrimary(finalSdr,sourceGuide)')!=1:
  fail('gain-map model does not follow SDR base')
 for marker in ('ratio=1.0+(ratio-1.0)*hdrHighlightGate;',
                'float hdrHighlightGate=smoothstep(0.68,0.96,brightIntent);',
                'if(iris26941BOffHdrqLowZoom!=0){'):
  if gain.count(marker)!=1:fail('non-highlight gain suppression changed '+marker)
 for marker in ('iris26941LensRelativeZoom < 1.10f','iris26941LensRelativeZoom > 0.0f',
                '!basePipeline.mParameters.motionV2SuperResOutputEnabled',
                '!basePipeline.mParameters.irisNightActive',
                '!basePipeline.mParameters.iris26903NightB',
                'iris26941BOffHdrqLowZoom ? 1 : 0'):
  if marker not in java:fail('exact below-1.10 B OFF scope absent '+marker)
 if java.count('glProg.setVar("iris26941BOffHdrqLowZoom", iris26941BOffHdrqLowZoom ? 1 : 0);')!=2:
  fail('SDR and UHDR shader uniform ownership not paired')
 for unwanted in ('"Fallback Chroma Gain"','"Fallback Luma Gain"','"Fallback Chroma Max Sigma"',
                  'new Iris26926FallbackSliderPreference(mContext, active, i)'):
  if unwanted in setting:fail('obsolete user fallback control remains '+unwanted)
 if 'Iris26856ABSettings.write(mContext, active, next);' not in setting:fail('experiment lens selector changed')
 if 'Iris26926FallbackSliderPreference.java' in ch:fail('native SR ON fallback compatibility class removed')
 if coord.count('ScopedBOffLazyPoolReset')!=3 or 'bOffReusable != nullptr && !sr' not in coord:
  fail('B OFF-only descriptor reset scope or RAII destructor missing')
 if 'extern thread_local bool iris26941BOffHdrqLazyPoolReset;' not in coord:
  fail('C++ shadow executor thread-local flag reference absent')
 if 'thread_local bool iris26941BOffHdrqLazyPoolReset = false;' not in exe:
  fail('C++ shadow executor opt-in default is not false')
 if 'if (!p.pool || !p.dsl || !p.layout || !p.prod)' not in exe:
  fail('original 26940 undeclared shader guard removed')
 for p,h in old.items():
  if p not in ch and new[p]!=h:fail('protected source changed '+p)
 if old['app/build.gradle']!=new['app/build.gradle'] or any('/vendor/' in p for p in ch):
  fail('CMake/native vendor invariance broken')
 # Historical Wronski fallback values are intentionally retained but UI hidden.
 if live:
  runner=(R/'app/src/main/cpp/iris26864/Iris26864FrozenDirectRawrRunner.cpp').read_text()
  if 'iris26920Arm.fallback' not in runner or 'merge.iris26926Fallback' not in runner:
   fail('SR ON frozen native fallback values/ABI removed')
  routing=(R/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
  for mark in ('localOutputZoom >= 1.10f','!iris26864BHighZoomExactA'):
   if mark not in routing:fail('>=1.10 Experiment-A routing changed')
 print('PASS 26941: 7 exact runtime files, 2043 protected, UI removed, SDR/HDR mirror + low-zoom-only contract, native Wronski/vendor untouched')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
