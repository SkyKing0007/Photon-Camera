#!/usr/bin/env python3
"""26856 B-native Motion regression; SOURCE-ONLY (not compiler/runtime proof)."""
from pathlib import Path
root=Path(__file__).resolve().parent.parent/'handoff_payload_26856'/'app/src/main/java'
bridge=(root/'com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
hdrx=(root/'com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
params=(root/'com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text()
cap=(root/'com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
stacker=(root/'com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
def check(v,msg):
 assert v,msg
 print('PASS',msg)
code=bridge.split('val highZoomDetailEnabled =',1)[1].split('parameters.motionV2HighZoomDetailPath = null',1)[0]
check('!sabreSuperResEnabled' in code and 'localOutputZoom >= 1.10f' in code and
      'experiment26856 != Iris26856ABSettings.Mode.AMAZE_26855' not in code,
      'B and A local zoom >=1.10x request native-output NORMAL CFA high-zoom detail with SR toggle off')
check('enableHighZoomDetail = highZoomDetailEnabled,' in bridge and
      bridge.count('enableHighZoomDetail = highZoomDetailEnabled,')==2,
      'A+B performs both B and A high-zoom sidecars independently')
for mode in ('A','B','AB'):
 for sr in (False,True):
  for z in (1.0,1.099,1.10,4.0,20.0):
   enabled=not sr and z>=1.10
   first=enabled
   historical=enabled and mode=='AB'
   assert first==(not sr and z>=1.10)
   assert historical==(mode=='AB' and not sr and z>=1.10)
check('iris26856AmazeCfaConsumer = if (!parameters.irisNightActive &&' in bridge and
      'experiment26856 != Iris26856ABSettings.Mode.ORIGINAL_26850' in bridge and
      'GlesIris26856AmazeNative.execute(' in bridge,
      'B native AMaZE consumer remains independent of optional true2x output')
check('iris26856RawrRgbSidecar' in stacker and
      'val zoomDetailGuide26856 = if (bIndependentZoom26856)' in stacker and
      '"26856 B high zoom requires live independent AMaZE RGB guide"' in stacker and
      'nativeVgnGuideTexture = zoomDetailGuide26856' in stacker,
      'B high-zoom detail is resolved using B AMaZE RGB, never A VGN guide')
check('if (iris26856BOnly) {' in hdrx and
      'output = iris26856BBuffer;' in hdrx and
      'processingParameters.prepareRawrBPublication26856(iris26856BTrue2xRgbPath != null);' in hdrx,
      'B-only publication retains B RGB master and uses own post params')
check('motionV2HighZoomDetailPath = null;' in params and
      'Iris26856BHighZoomDetail bZoom = iris26856BHighZoomDetail;' in params and
      'motionV2HighZoomDetailPath = bZoom.path;' in params and
      'motionV2SuperResOutputEnabled = independentTrue2x;' in params,
      'B publication explicitly retires A sidecar and activates only B-owned detail')
check('iris26856BHighZoomDetailHandedOff' in bridge and
      'mIris26856BHighZoomDetailPathForCleanup' in hdrx,
      'B independent high-zoom file has explicit bridge and publisher failure cleanup')
check('final boolean iris26480ShortHighlightRequested = false' in cap and
      'final int iris26593AuxCount = iris26505LongRequested ? 1 : 0' in cap,
      'Motion uses normal frame and optional LONG, with SHORT retired')
check('renderIris26856BVerifiedLongLuma(' in stacker and
      'if (iris26856RawrRgbSidecar != 0 && shadowLongLumaGain26833 != 0)' in stacker,
      'B AMaZE/Lab/FCC retains bounded LONG luma scalar independently from zoom detail')
check('iris26856BPostParameters = processingParameters.snapshotForIndependentMotionPost26856();' in hdrx and
      'iris26856BPostPipeline.RunMotionV2FloatCfa(' in hdrx and
      'ImageSaver.Util.saveBitmapAsJPGMotionV2(' in hdrx,
      'A+B B post uses independent HDR/SDR carrier and dual-JPEG routing')
print('PASS B ordinary Motion zoom source regression; real Kotlin/Java/GLSL/NDK device tests NOT RUN')
