#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys, xml.etree.ElementTree as ET
if len(sys.argv)!=3: raise SystemExit('usage: validate_26699.py BASE26698 CANDIDATE')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def H(root): return {'app/'+str(p.relative_to(root/'app')):h(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
def t(rel): return (c/rel).read_text()
B=H(b);C=H(c);exp=[x.strip() for x in (pkg/'26699_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
changed=sorted(k for k in set(B)|set(C) if B.get(k)!=C.get(k))
assert len(B)==len(C)==1823,(len(B),len(C));assert changed==sorted(exp),(changed,exp);assert len(changed)==13
assert not [x for x in (pkg/'26699_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x.strip()]
for name,root in [('26699_BASE_26698_FULL_APP.sha256',b),('26699_EXPECTED_CANDIDATE_FULL_APP.sha256',c)]:
 for line in (pkg/name).read_text().splitlines():
  if line.strip(): hh,rel=line.split(None,1);assert h(root/rel.strip())==hh,(name,rel)
for rel in B:
 if rel not in exp: assert B[rel]==C[rel],rel
SB={k:v for k,v in B.items() if k.startswith('app/src/main/assets/shaders/')};SC={k:v for k,v in C.items() if k.startswith('app/src/main/assets/shaders/')};assert len(SB)==271 and SB==SC
# Performance/sync ownership.
stage=t('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/StageTelemetry.java');run=stage[stage.index('public void Run()'):]
assert 'IRIS_26699_STAGE_TELEMETRY_REDUNDANT_BARRIER_REMOVED' in run and 'glFinish()' not in run
assert 'histogram.Compute' not in run and 'chromaOriginStats(source)' not in run and 'WorkingTexture = source;' in run
sabre=t('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
assert 'GLES30.glFinish()' not in sabre
for marker in ('IRIS_26699_LONG_PROOF_REDUNDANT_BARRIER_REMOVED','IRIS_26699_FUSION_DECISION_BARRIER_REMOVED','IRIS_26699_FUSION_RADIANCE_BARRIER_REMOVED','IRIS_26699_HDR_PROBE_BARRIER_REMOVED stage=FLOAT_HDR_HANDOFF_PRE_VGN','IRIS_26699_HDR_PROBE_BARRIER_REMOVED stage=POST_VGN_HDR_MASTER'): assert marker in sabre,marker
for token in ('renderSabreNormalMasterShortFusion26651(','renderSabreDehomogenize(','renderSabreRestoreExtendedHdr26605(','readSabreRgb16(','countSabreShortRestoreMaskFull26595('): assert token in sabre,token
bridge=t('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
assert 'val directHalfMotionCarrier = !parameters.irisNightActive && cfa in 0..3' in bridge
assert 'convertHalfRgbaToFloatRgba(denoiseBuffer, size.x, size.y)' in bridge
assert 'if (directHalfMotionCarrier) halfBuffer = null' in bridge
# Cross-context timeline and EGL-lifetime barriers are deliberately retained.
assert 'GLES30.glFinish()\n            gpu.stackCompletionTimeline?.releasePending()' in bridge
assert 'runCatching { GLES30.glFinish() }' in bridge and 'egl?.close()' in bridge
inp=t('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java')
for token in ('GLES30.GL_HALF_FLOAT','GLFormat.DataType.FLOAT_16','Allocator.free(source);','pipeline.motionV2FloatCfa = null;','cpuCarrierReleasedAfterUpload=true'): assert token in inp,token
assert 'new GLFormat(GLFormat.DataType.FLOAT_32, 4)' in inp # fallback contract retained
# Publication timing is observational only; 26698 disabled proof remains disabled.
enc=t('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java');assert 'IRIS_26699_JPEGR_STAGE_TIMING' in enc
for token in ('writeNative(bitmap,base.toString()','encodeGainmapNative(contents,gain.toString()','packageJpegRNative(base.toString(),gain.toString()','isJpegRNative(output.toString())'):assert token in enc,token
img=t('app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java');assert 'IRIS_26699_JPEGR_PUBLICATION_TIMING' in img
m0=img.index('private static void iris26642ScheduleUltraHdrDecodeProof');m1=img.index('public static boolean saveBitmapAsJPG',m0);assert 'decodeFile' not in img[m0:m1]
# UI scope.
swipe=t('app/src/main/java/com/particlesdevs/photoncamera/control/Swipe.java');assert 'IRIS_26699_VIDEO_BOTTOM_TOUCH_FOCUS_EXCLUSION' in swipe
assert 'mode == CameraMode.VIDEO || mode == CameraMode.RAWVIDEO' in swipe and 'R.id.layout_bottombar' in swipe
ui=t('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java');assert 'iris26699VideoRecordingTicker' in ui and 'displayedMode == CameraMode.VIDEO' in ui
ctl=t('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java');assert 'cameraFragment.setVideoRecordingInfoVisible(true);' in ctl and 'cameraFragment.setVideoRecordingInfoVisible(false);' in ctl
frag=t('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java');assert 'void setVideoRecordingInfoVisible(boolean visible)' in frag
layout=c/'app/src/main/res/layout/camera_fragment.xml';ET.parse(layout);ls=layout.read_text();start=ls.index('android:id="@+id/video_recording_info"');blk=ls[start:ls.index('/>',start)+2]
assert 'android:layout_marginTop="4dp"' in blk and 'android:layout_marginEnd="8dp"' in blk and 'app:layout_constraintTop_toBottomOf="@id/iris_live_histogram"' in blk
grid=t('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/SurfaceViewOverViewfinder.java');assert 'whitePaint.setAlpha(153)' in grid and 'whitePaint.setStrokeWidth(1.0f)' in grid
ver=t('app/version.properties');assert 'VERSION_NAME=0.9726699' in ver and 'VERSION_BUILD=26699' in ver
print('PASS validate 26699: exact 13-file combined performance/UI scope; 1810 protected; direct-half/ownership/UI contracts valid; 271 shaders invariant')
