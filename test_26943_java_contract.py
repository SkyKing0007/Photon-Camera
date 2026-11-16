#!/usr/bin/env python3
"""Java/Kotlin/C++ active routing, API visibility and RAWR EXIF wiring.
Real project Kotlin/Java compilers remain mandatory on the official Actions run.
"""
import sys
from build_26943_incremental import R,scope,fail
PATH={
'capture':'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'native':'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26864NativeRawr.java',
'bridge':'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'jpeg':'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'jni':'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc',
'runner':'app/src/main/cpp/iris26864/Iris26864FrozenDirectRawrRunner.cpp',
}
def main():
 scope();live='--live' in sys.argv
 texts={k:(R/path if live else R/'handoff_payload_26943'/path).read_text() for k,path in PATH.items()}
 def expect(k,marks):
  for m in marks:
   if m not in texts[k]:fail('missing Java/native cross-reference '+k+': '+m)
 expect('capture',('iris26943StageOptionalGpuZsl(img);','SDK_INT < 33','img.getHardwareBuffer()','img.getFence()',
  'fence.getSignalTime()','S​IGNAL_TIME_PENDING'.replace('\u200b',''),'S​IGNAL_TIME_INVALID'.replace('\u200b',''),
  'zoom.outputLocalZoom >= 1.10f','!iris26871BExposureSelected()','PreferenceKeys.isIrisSuperResOn()',
  'mIris26548CameraHealthGeneration','tryZslGpuStage(','buffer.close();'))
 if 'getFdDup()' in texts['capture'] or 'getFd(' in texts['capture']:fail('Android public SyncFence FD API invalid')
 expect('native',('nativeTryZslGpuStage','nativeTakeLastTimings','recordTiming(','takeTiming('))
 expect('jni',('Java_com_hinnka_mycamera_processor_GlesIris26864NativeRawr_nativeTryZslGpuStage','AHardwareBuffer_acquire','std::try_to_lock'))
 expect('bridge',('recordTiming(referenceTimestamp)','GlesIris26864NativeRawr.run('))
 expect('jpeg',('Iris Photo B HDR+ Higher Quality','GlesIris26864NativeRawr.takeTiming','exifData.IMAGE_DESCRIPTION','iris26943Timing'))
 expect('runner',('Java_com_hinnka_mycamera_processor_GlesIris26864NativeRawr_nativeTakeLastTimings','iris26943LastTimings.clear()'))
 print('PASS active Camera2 RAW callbacks/API33 public AHB and SyncFence, nonblocking JNI, exact per-shot/native cross-reference and Photo B-only JPEG EXIF')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
