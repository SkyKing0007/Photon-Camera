#!/usr/bin/env python3
from pathlib import Path
import re,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26687_regressions.py BASE CAND')
base,cand=map(Path,sys.argv[1:])
def txt(rel): return (cand/rel).read_text()
def same(rel):
    if (base/rel).read_bytes()!=(cand/rel).read_bytes(): raise SystemExit('FAIL protected regression byte '+rel)
def need(text,tok,msg):
    if tok not in text: raise SystemExit('FAIL '+msg+': '+tok)
# Protected Photo/Motion/Night and DNG ownership remains byte-identical.
for rel in [
 'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/ProcessorBase.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java']:
    same(rel)
# 26681-26686 shared mode/discovery/session compiler fixes remain semantically present even where bridge files intentionally change.
param=txt('app/src/main/java/com/particlesdevs/photoncamera/manual/ParamController.java')
need(param,'Math.max(1L, Math.round(currentExposure))','26681 Java conversion regression')
view=txt('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
for t in ['selectFormat(0)','selectFormat(1)','selectFormat(2)','selectHeicFormat()']: need(view,t,'26681 UI symbol regression')
cap=txt('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
ui=txt('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java')
for t in ['IRIS_26683_MODE_AUTHORITY_COMMITTED','IRIS_26687_SPEKTRA_SHUTTER_FAIL_CLOSED','IRIS_26683_MODE_OWNER_DIVERGENCE','IRIS_26684_SPEKTRA_LEGACY_CAMERA_BLOCK']:
    need(cap,t,'mode/camera-owner regression')
if ui.index('retireModeForTransition(previousMode, cameraMode)') > ui.index('commitCameraModeForTransition(cameraMode)'): raise SystemExit('FAIL destination mode committed before source owner retired')
owner=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java')
for t in ['spektra_auto_lens_discovery','enumerateSpektraRoutes()','claimedPhysicalIds','automaticDiscoveryQueue','new int[]{ImageFormat.RAW10, ImageFormat.RAW_SENSOR}','IRIS_26684_SPEKTRA_STILL_SESSION_REUSED=true','IRIS_26684_SPEKTRA_PREVIEW_RESUMED','IRIS_26685_SPEKTRA_PROFILE_VERIFIED']:
    need(owner,t,'26684/26685 discovery/session regression')
if 'stillReader' in owner: raise SystemExit('FAIL separate Spektra still reader returned')
pre=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java')
need(pre,'activity.runOnUiThread(firstFramePresentedCallback)','26685 UI-thread regression')
rawp=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawProcessor.java')
jni=txt('app/src/main/cpp/spektra/SpektraNativeJni.cpp')
shader=txt('app/src/main/cpp/spektra/SpektraRawDevelop.comp')
for t in ['nativeProcessPackedRaw','nativeReleaseRawOwner']: need(rawp,t,'26686 native RAW owner regression')
for t in ['SpektraRawVulkanOwner::instance().process','nativeReleaseRawOwner']: need(jni,t,'26686 JNI Vulkan owner regression')
need(shader,'return vec3(dot(r0,rgb),dot(r1,rgb),dot(r2,rgb))','26686 row-major sensor matrix regression')
meta=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraFrameMetadata.java')
for t in ['activeRawDomain','hint = -1','leftNumerator % pixelArray.getWidth() == 0L','activeRawDomain.width() < 2']:
    need(meta,t,'26686 RAW geometry regression')
for t in ['clampActivePreservePhase','sensorRowParity=(xy.y&1)^((int(p[P_BAYER_OFFSET])>>1)&1)','P_ACTIVE_L','P_ACTIVE_R']:
    need(shader,t,'26686 shader RAW-domain regression')
# Exact 26686 on-device failure becomes permanent 26687 regression.
vk=txt('app/src/main/cpp/spektra/SpektraRawVulkanOwner.cpp')
if 'UINT64_MAX' in re.sub(r'/\*.*?\*/|//.*?$',' ',vk,flags=re.M|re.S): raise SystemExit('FAIL 26686 infinite Vulkan wait returned')
for t in ['kPreviewFenceTimeoutNs','kSavedFenceTimeoutNs','VK_TIMEOUT','try_lock()','IRIS_26687_RAW_VK_TIMEOUT','IRIS_26687_RAW_VK_WARMUP_SELFTEST_PASS']:
    need(vk,t,'26686 first-frame deadlock regression')
raw=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawFrame.java')
m=raw[raw.index('public static SpektraRawFrame copyPreviewFrom'):raw.index('/** Saved path',raw.index('public static SpektraRawFrame copyPreviewFrom'))]
if m.index('image.close()') > m.index('SpektraRawProcessor.processLivePreview'): raise SystemExit('FAIL Camera2 Image retained through Vulkan again')
# Exact control-plane regressions.
for t in ['SPEKTRA_PROFILE_SCHEMA = 26687','CaptureJobState { IDLE, PROCESSING }','previewPresented.get()','startPendingSavedProcess("mode_handoff")','forceCloseCameraTransportForHandoff()']:
    need(owner,t,'26687 isolated owner regression')
if 'CaptureController.isProcessing' in owner:
    raise SystemExit('FAIL Spektra returned to Iris global processing authority')
if 'getSpektraCameraOwner' in owner+cap:
    raise SystemExit('FAIL direct SpektraCameraOwner bridge returned')
need(owner,'RAW_GPU_WARMUP_TIMEOUT_MS = 10000L','pre-camera GPU self-test timeout regression')
need(cap,'IRIS_26687_STALE_SPEKTRA_OWNER_RETIRED','stale-owner regression')
if 'Spektra owner did not retire before mode handoff' in cap: raise SystemExit('FAIL Spektra handoff crash returned')
frag=txt('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java')
need(frag,'shutdownSpektraMode()','terminal Spektra shutdown regression')
print('PASS 26687 permanent regressions: 26681-26686 mode/discovery/session/RAW-domain fixes preserved; infinite GPU wait, camera-buffer hostage, discovery poisoning, false shutter-ready, shared processing authority, teardown crash, stale-owner suppression and missing shutdown are permanently rejected')
