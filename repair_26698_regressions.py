#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: repair_26698_regressions.py BASE26697 CANDIDATE')
b=Path(sys.argv[1]);c=Path(sys.argv[2])
t=lambda rel:(c/rel).read_text();bt=lambda rel:(b/rel).read_bytes();ct=lambda rel:(c/rel).read_bytes()
# Permanent build-source contamination regressions: authority universe only.
assert not any((c/'app/build').glob('**/*')) if (c/'app/build').exists() else True
assert not any((c/'app/.cxx').glob('**/*')) if (c/'app/.cxx').exists() else True
# Frozen major camera/UI/exposure owners not in cleanup scope.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/control/Swipe.java',
'app/src/main/java/com/particlesdevs/photoncamera/control/TouchFocus.java',
'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraExposureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java',
'app/src/main/java/com/unspektrawesome/camera/session/Camera2RawSession.java',
'app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java']
for rel in protected:assert bt(rel)==ct(rel),rel
# StageTelemetry pass-through remains exact input object with explicit completion, no histogram/readback execution.
stage=t('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/StageTelemetry.java');run=stage[stage.index('public void Run()'):]
assert 'WorkingTexture = source;' in run and 'android.opengl.GLES20.glFinish();' in run
assert 'histogram.Compute(source)' not in run and 'chromaOriginStats(source)' not in run
# Sabre production math/owners must still exist; proof routines may remain dormant but have no callers.
s=t('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for token in ['renderSabreNormalMasterShortFusion26651(','renderSabreDehomogenize(','renderSabreRestoreExtendedHdr26605(','readSabreRgb16(','countSabreShortRestoreMaskFull26595(']:assert token in s,token
for name in ['logSabreUniversalFusionDecision26651','logSabreUniversalFusionRadiance26651','logSabreExtendedHdrProbe26605']:assert s.count(name)==1,(name,s.count(name))
# Publication success semantics remain native/encoder return values, not proof results.
h=t('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java')
assert 'return ok;' in h and 'return saved;' in h and h.count('iris26646VerifyPlatformReadback(')==1
img=t('app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java');assert 'savedBytesUnchanged=true' in img
# No shader mutation at all.
for pb in (b/'app/src/main/assets/shaders').rglob('*'):
 if pb.is_file():
  rel=pb.relative_to(b);assert pb.read_bytes()==(c/rel).read_bytes(),rel
print('PASS 26698 permanent regressions: capture/viewfinder/exposure owners protected; production Sabre/publication semantics preserved; proof-only work disabled')
