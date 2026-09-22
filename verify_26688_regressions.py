#!/usr/bin/env python3
from pathlib import Path
import re,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26688_regressions.py BASE CAND')
base,cand=map(Path,sys.argv[1:])
def txt(rel): return (cand/rel).read_text()
def same(rel):
    if (base/rel).read_bytes()!=(cand/rel).read_bytes(): raise SystemExit('FAIL protected regression byte '+rel)
def need(text,tok,msg):
    if tok not in text: raise SystemExit('FAIL '+msg+': '+tok)
owner=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java')
cap=txt('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
frag=txt('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java')
rawf=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawFrame.java')
rawp=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawProcessor.java')
jni=txt('app/src/main/cpp/spektra/SpektraNativeJni.cpp')
cpu=txt('app/src/main/cpp/spektra/SpektraRawCpuOwner.cpp')
cmake=txt('app/src/main/cpp/CMakeLists.txt')
# 26687 isolation/lifecycle regressions remain permanent.
for tok in ['SpektraModeController','IRIS_26687_SPEKTRA_SHUTTER_FAIL_CLOSED','IRIS_26687_STALE_SPEKTRA_OWNER_RETIRED','spektraModeController.isShutterReady()']:
    need(cap,tok,'26687 shell bridge')
if re.search(r'\bSpektraCameraOwner\b',re.sub(r'/\*.*?\*/|//.*?$|"(?:\\.|[^"\\])*"',' ',cap,flags=re.M|re.S)):
    raise SystemExit('FAIL CaptureController direct Spektra owner access returned')
if 'Spektra owner did not retire before mode handoff' in cap: raise SystemExit('FAIL crashing handoff returned')
for tok in ['CaptureJobState { IDLE, PROCESSING }','previewPresented.get()','startPendingSavedProcess("preview_restored")','startPendingSavedProcess("mode_handoff")','startPendingSavedProcess("processor_failure")','forceCloseCameraTransportForHandoff()','SPEKTRA_PROFILE_SCHEMA = 26688']:
    need(owner,tok,'26687 isolated owner regression')
if 'CaptureController.isProcessing' in owner: raise SystemExit('FAIL shared Iris processing authority returned')
on_destroy=frag[frag.index('public void onDestroy()'):frag.index('captureController = null;',frag.index('public void onDestroy()'))]
if on_destroy.index('shutdownSpektraMode()')>on_destroy.index('stopBackgroundThread()'): raise SystemExit('FAIL Spektra shutdown after legacy teardown')
# Exact 26686/26687 on-device failure: no pre-camera RAW-GPU warm-up and no active custom RAW Vulkan target.
start=owner[owner.index('private void startCamera'):owner.index('public void closeCamera()',owner.index('private void startCamera'))]
for bad in ['RAW_GPU_WARMUP','warmUpNativeOwner','RAW_OWNER_WARMUP']:
    if bad in start: raise SystemExit('FAIL 26687 visible warm-up timeout regression returned '+bad)
if 'nativeWarmUpRawOwner' in rawp or 'nativeWarmUpRawOwner' in jni: raise SystemExit('FAIL zombie native warm-up API returned')
target=cmake[cmake.index('add_library(spektra_iris SHARED'):cmake.index('set_target_properties(spektra_iris',cmake.index('add_library(spektra_iris SHARED'))]
if 'SpektraRawVulkanOwner.cpp' in target: raise SystemExit('FAIL broken Vulkan RAW owner reactivated')
need(target,'SpektraRawCpuOwner.cpp','CPU RAW target regression')
if 'SpektraRawVulkanOwner' in jni: raise SystemExit('FAIL JNI still routes RAW through Vulkan owner')
if re.search(r'\bvk[A-Z]\w*\s*\(',cpu): raise SystemExit('FAIL CPU RAW owner contains Vulkan calls')
for tok in ['semanticLscChannel','normalized*lscGainChannel']:
    need(cpu,tok,'per-photosite LSC regression')
if 'applyLensShading' in cpu: raise SystemExit('FAIL post-demosaic lens shading returned')
# Camera buffer hostage remains permanently rejected.
m=rawf[rawf.index('public static SpektraRawFrame copyPreviewFrom'):rawf.index('/** Saved path',rawf.index('public static SpektraRawFrame copyPreviewFrom'))]
m_exec=re.sub(r'/\*.*?\*/|//.*?$',' ',m,flags=re.M|re.S)
if m_exec.index('image.close()')>m_exec.index('SpektraRawProcessor.processLivePreview'): raise SystemExit('FAIL Camera2 Image retained through native RAW work')
# Discovery and camera capability remain independent of processor health.
for tok in ['currentStreamRawSeen','currentStreamResultSeen','isDiscoveryStreamFailure','failProcessor','DISCOVERY_REJECT_DOMAIN_VIOLATION_']:
    need(owner,tok,'processor/discovery separation')
# 26684/26685 transaction mechanics remain present.
for tok in ['spektra_auto_lens_discovery','enumerateSpektraRoutes()','new int[]{ImageFormat.RAW10, ImageFormat.RAW_SENSOR}','IRIS_26684_SPEKTRA_STILL_SESSION_REUSED=true','IRIS_26684_SPEKTRA_PREVIEW_RESUMED','IRIS_26685_SPEKTRA_PROFILE_VERIFIED']:
    need(owner,tok,'camera/session transaction regression')
if 'stillReader' in owner: raise SystemExit('FAIL separate still reader returned')
# RAW geometry/color fidelity contracts.
meta=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraFrameMetadata.java')
for tok in ['activeRawDomain','hint = -1','black[q] = sensorBlack[q ^ selectedOffset]','cfa = sensorCfa ^ selectedOffset']:
    need(meta,tok,'RAW geometry regression')
for tok in ['q.format == 37','q.format == 38','clampActivePreservePhase','lscGainChannel','semanticLscChannel','normalized*lscGainChannel','sensorToLinear','applySavedChromaDenoise']:
    need(cpu,tok,'CPU RAW correctness regression')
# The old raw shader is explicitly dormant and byte-identical; Photo/Motion/Night/DNG remain untouched.
same('app/src/main/cpp/spektra/SpektraRawDevelop.comp')
for rel in [
 'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/ProcessorBase.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java']:
    same(rel)
print('PASS 26688 permanent regressions: 26687 isolation retained; pre-camera GPU warm-up/zombie RAW Vulkan owner permanently rejected; Camera2 buffers detached; discovery separation and transaction mechanics preserved; CPU RAW geometry/color contracts enforced')
