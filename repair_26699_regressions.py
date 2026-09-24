#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: repair_26699_regressions.py BASE26698 CANDIDATE')
b=Path(sys.argv[1]);c=Path(sys.argv[2]);t=lambda r:(c/r).read_text();bt=lambda r:(b/r).read_bytes();ct=lambda r:(c/r).read_bytes()
assert not any((c/'app/build').glob('**/*')) if (c/'app/build').exists() else True
assert not any((c/'app/.cxx').glob('**/*')) if (c/'app/.cxx').exists() else True
# Critical photographic owners outside the explicit transport/sync scope remain exact 26698 bytes.
protected=['app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/java/com/particlesdevs/photoncamera/control/TouchFocus.java','app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraExposureController.java','app/src/main/java/com/unspektrawesome/camera/session/Camera2RawSession.java','app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java']
for rel in protected:assert bt(rel)==ct(rel),rel
# No acquisition/fusion equations or denoise invocation removed.
br=t('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
for tok in ('MgcFullResolutionDenoise.denoise(','forceOpaqueHalfAlpha(denoiseBuffer','stackCompletionTimeline?.releasePending()','egl?.close()'):assert tok in br,tok
s=t('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for tok in ('renderSabreNormalMasterShortFusion26651(','renderSabreDehomogenize(','renderSabreOutputTransform(','renderSabreRestoreExtendedHdr26605('):assert tok in s,tok
# Only Video/RAW Video focus exclusion; Motion/Photo focus path has no mode exclusion.
sw=t('app/src/main/java/com/particlesdevs/photoncamera/control/Swipe.java');assert sw.count('CameraMode.MOTION')==0 and 'CameraMode.VIDEO || mode == CameraMode.RAWVIDEO' in sw
# Grid geometry algorithms unchanged, only paint alpha/stroke.
gr=t('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/SurfaceViewOverViewfinder.java')
for tok in ('draw3x3(canvas)','draw4x4(canvas)','drawGoldenRatio(canvas)','drawSuperDiag(canvas)'):assert tok in gr,tok
# 26698 post-save diagnostic decode remains retired.
img=t('app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java');m0=img.index('private static void iris26642ScheduleUltraHdrDecodeProof');m1=img.index('public static boolean saveBitmapAsJPG',m0);assert 'decodeFile' not in img[m0:m1]
# Shaders/native/vendor/DNG are byte protected by manifests; no shader source may differ.
for pb in (b/'app/src/main/assets/shaders').rglob('*'):
 if pb.is_file(): rel=pb.relative_to(b);assert pb.read_bytes()==(c/rel).read_bytes(),rel
print('PASS 26699 regressions: photographic owners protected; CPU denoise/fusion retained; timeline/EGL barriers retained; UI changes isolated; post-save decode remains retired')
