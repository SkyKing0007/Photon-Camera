#!/usr/bin/env python3
from pathlib import Path
import sys,re
if len(sys.argv)!=3:raise SystemExit('usage: verify_26685_regressions.py BASE CAND')
base,cand=map(Path,sys.argv[1:])
def txt(rel):return (cand/rel).read_text()
def same(rel):
 if (base/rel).read_bytes()!=(cand/rel).read_bytes():raise SystemExit('FAIL protected bytes '+rel)
# Permanent build regressions from 26681/26682 and shader/binary assets remain sealed.
for rel in ['app/src/main/assets/spektra/data/SpektraHanatos2025Spectra.f32','app/src/main/assets/spektra/data/SpektraProfileData.bin','app/src/main/assets/spektra/data/SpektraOutputGamutCompression.f32']:same(rel)
for p in (base/'app/src/main/assets').rglob('*'):
 if p.is_file() and p.suffix in {'.glsl','.frag','.vert','.comp'}:same(str(p.relative_to(base)))
param=txt('app/src/main/java/com/particlesdevs/photoncamera/manual/ParamController.java')
if 'Math.max(1L, Math.round(currentExposure))' not in param:raise SystemExit('FAIL 26681 Java conversion regression')
view=txt('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
for token in ['selectFormat(0)','selectFormat(1)','selectFormat(2)','selectHeicFormat()']:
 if token not in view:raise SystemExit('FAIL 26681 UI symbol regression '+token)
cap=txt('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java');ui=txt('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java')
for token in ['getAuthoritativeCameraMode()','commitCameraModeForTransition','IRIS_26683_MODE_AUTHORITY_COMMITTED','IRIS_26683_SPEKTRA_SHUTTER_FAIL_CLOSED','MODE_OWNER_DIVERGENCE']:
 if token not in cap:raise SystemExit('FAIL 26682 mode-owner regression '+token)
if ui.index('retireModeForTransition(previousMode, cameraMode)') > ui.index('commitCameraModeForTransition(cameraMode)'):raise SystemExit('FAIL destination committed before source owner retired')
# 26683/26684 runtime failures remain guarded.
own=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java');rawf=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawFrame.java');rawp=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawProcessor.java');native=txt('app/src/main/cpp/spektra/SpektraNativeJni.cpp');pre=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java');color=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraColorSolver.java');meta=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraFrameMetadata.java')
if 'unpackRaw10' in rawf or 'unpackRaw12' in rawf:raise SystemExit('FAIL 26683 Java RAW unpacker returned')
for token in ['PREVIEW_SHORT_EDGE_DEFAULT = 480','copyPreviewFrom(image, PREVIEW_SHORT_EDGE_DEFAULT,','baseMetadata.cfaArrangement, baseMetadata.blackLevel4, baseMetadata.whiteLevel','previewBayerOffset','submitStill(g, previewReader.getSurface())','watchdogExecutor.schedule']:
 if token not in own:raise SystemExit('FAIL 26683/26684 correction '+token)
if re.search(r'\bstillReader\b',own):raise SystemExit('FAIL separate still reader returned')
for token in ['iris26684BlockLegacyCameraForSpektra("surface_available")','iris26684BlockLegacyCameraForSpektra("openCamera_pre_hal")','iris26684BlockLegacyCameraForSpektra("restart_locked_pre_hal")','iris26684BlockLegacyCameraForSpektra("legacy_onOpened")']:
 if token not in cap:raise SystemExit('FAIL legacy camera collision regression '+token)
# 26684 green-lattice regressions.
if 'mapPreviewCoordinate' in native:raise SystemExit('FAIL sparse Bayer nearest mapping returned')
for token in ['nativeDecodePreviewRgb16f','demosaicCameraRgb','reducedPreviewRgb','averageRawPhaseBox']:
 if token not in native:raise SystemExit('FAIL 26684 CFA-lattice display regression '+token)
for token in ['previewCameraRgb16f','nativeDecodePreviewRgb16f']:
 if token not in rawf:raise SystemExit('FAIL VF-S RGB carrier regression '+token)
for token in ['previewDecodeExecutor','previewDecodeBusy.compareAndSet(false, true)','SpektraVfsRawDecode']:
 if token not in own:raise SystemExit('FAIL Camera2-thread VF-S decode regression '+token)
for token in ['LongSparseArray<Image> previewImages','schedulePreviewDecode(image, result','SpektraFrameMetadata.from(result, characteristics']:
 if token not in own:raise SystemExit('FAIL preview RAW/result exact-pair regression '+token)
for token in ['IRIS_26685_SPEKTRA_VFS_RGB_OWNER','processPreviewRgb','shot.raw.previewCameraRgb16f']:
 if token not in rawp:raise SystemExit('FAIL reduced Bayer regained display ownership '+token)
if 'for (int q = 0; q < 4; ++q)' not in rawf:raise SystemExit('FAIL Bayer estimator even-stride/single-phase regression')
if 'return -1;' not in rawf or 'bayerHint=UNRESOLVED' not in own or 'BAYER_ORIGIN_AMBIGUOUS' not in own:raise SystemExit('FAIL ambiguous Bayer origin no longer fail-closed')
if 'black[q] = sensorBlack[q ^ offset]' not in meta or 'cfa = sensorCfa ^ offset' not in meta:raise SystemExit('FAIL black/CFA phase mismatch')
# Spektra-only automatic discovery; do not mutate general Iris lens ownership.
for token in ['spektra_auto_lens_discovery','enumerateSpektraRoutes()','claimedPhysicalIds','automaticDiscoveryQueue','functionalVerification=preview+still+resume','IRIS_26685_SPEKTRA_PROFILE_VERIFIED']:
 if token not in own:raise SystemExit('FAIL Spektra verified discovery '+token)
if 'new int[] {ImageFormat.RAW10, ImageFormat.RAW_SENSOR}' not in own:raise SystemExit('FAIL RAW10-first/RAW_SENSOR fallback')
for token in ['currentProfileNeedsVerification || verificationCaptureInFlight','SPEKTRA_PROFILE_VERIFYING']:
 if token not in own:raise SystemExit('FAIL unverified profile shutter admission '+token)
# Only Spektra package + version may differ from successful 26684.
changed={
 'app/src/main/cpp/spektra/SpektraNativeJni.cpp',
 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java',
 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraColorSolver.java',
 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraFrameMetadata.java',
 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java',
 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawFrame.java',
 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawProcessor.java',
 'app/version.properties'}
for p in (base/'app').rglob('*'):
 if p.is_file():
  rel=str(p.relative_to(base))
  if rel not in changed and p.read_bytes()!=(cand/rel).read_bytes():raise SystemExit('FAIL non-Spektra/global Iris mutation '+rel)
# Logging flood regression: live preview uses quiet ColorSolver and saved-only RAW success logs.
if 'solveQuiet' not in color or 'solveQuiet' not in pre:raise SystemExit('FAIL preview color log flood')
# Saved JPG and Spektra defaults remain intact.
pub=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraJpegPublisher.java')
if 'Bitmap.CompressFormat.JPEG, 100' not in pub:raise SystemExit('FAIL JPEG100')
for token in ['p.film = 2','p.paper = 3','FilteredEnlarger','LinearRec709','Srgb','DisplaySdr']:
 if token not in native:raise SystemExit('FAIL Spektra factory '+token)
print('PASS 26685 permanent regressions: prior Actions failures + mode ownership + Java RAW backlog/crash + camera collision + 26684 sparse-Bayer/CFA-lattice/unverified-profile/log-flood failures guarded; non-Spektra bytes protected')
