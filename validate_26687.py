#!/usr/bin/env python3
from pathlib import Path
import re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26687.py BASE CAND')
base,cand=map(Path,sys.argv[1:])
def txt(rel): return (cand/rel).read_text()
def need(text,tok,msg='token'):
    if tok not in text: raise SystemExit('FAIL '+msg+': '+tok)
def forbid_code(text,tok,msg='forbidden'):
    clean=re.sub(r'/\*.*?\*/|//.*?$|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',' ',text,flags=re.M|re.S)
    if re.search(r'\b'+re.escape(tok)+r'\b',clean): raise SystemExit('FAIL '+msg+': '+tok)
# Core Spektra ownership boundary.
owner=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java')
fac=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java')
raw=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawFrame.java')
rawp=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawProcessor.java')
pre=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java')
cap=txt('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
frag=txt('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java')
param=txt('app/src/main/java/com/particlesdevs/photoncamera/manual/ParamController.java')
touch=txt('app/src/main/java/com/particlesdevs/photoncamera/control/TouchFocus.java')
ui=txt('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java')
jni=txt('app/src/main/cpp/spektra/SpektraNativeJni.cpp')
vk=txt('app/src/main/cpp/spektra/SpektraRawVulkanOwner.cpp')
vkh=txt('app/src/main/cpp/spektra/SpektraRawVulkanOwner.h')
shader=txt('app/src/main/cpp/spektra/SpektraRawDevelop.comp')
# Owner is hidden and facade is the sole public camera-control boundary.
if not re.search(r'(?m)^final class SpektraCameraOwner\s*\{',owner): raise SystemExit('FAIL Spektra owner must be package-private')
if re.search(r'(?m)^public\s+final\s+class\s+SpektraCameraOwner',owner): raise SystemExit('FAIL Spektra owner leaked public')
for t in ['public final class SpektraModeController','interface Host','resume(','restart(','exitForModeHandoff()','shutdown()','isShutterReady()','takePicture()','setManualControls','touchFocus']:
    need(fac,t,'facade contract')
# No reverse dependency into Iris capture/GL/Motion processing authorities.
spektra_java='\n'.join(p.read_text() for p in (cand/'app/src/main/java/com/particlesdevs/photoncamera/spektra').glob('*.java'))
for t in ['CaptureController','GLPreview','GLContext','GLProg','GLTexture','RCD26498']:
    forbid_code(spektra_java,t,'reverse Spektra dependency')
forbid_code(spektra_java,'isProcessing','Iris global processing state')
# One owner, two internal state domains: camera + saved capture job.
for t in ['enum CaptureJobState { IDLE, PROCESSING }','AtomicReference<CaptureJobState>','savedProcessExecutor','nativeLifecycleExecutor','previewDecodeExecutor','pendingSavedShot']:
    need(owner,t,'Spektra-owned lifecycle')
if re.search(r'enum State\s*\{[^}]*\bPROCESSING\b',owner,re.S): raise SystemExit('FAIL saved processing returned to camera state enum')
# Shutter cannot become ready from STREAMING alone.
ready=owner[owner.index('public boolean isShutterReady()'):owner.index('public String describeStatus()',owner.index('public boolean isShutterReady()'))]
for t in ['isStreaming()','previewPresented.get()','captureJobState.get() == CaptureJobState.IDLE']:
    need(ready,t,'shutter readiness')
stream=owner[owner.index('public boolean isStreaming()'):owner.index('public boolean isShutterReady()',owner.index('public boolean isStreaming()'))]
for t in ['!currentProfileNeedsVerification','!verificationCaptureInFlight']:
    need(stream,t,'verified route readiness')
# Processor failure and discovery capability failure are disjoint domains.
need(owner,'SPEKTRA_PROFILE_SCHEMA = 26687','profile cache invalidation')
fp=owner[owner.index('private void failProcessor'):owner.index('private void fail(',owner.index('private void failProcessor'))]
for tok in ['retryDiscoveryStream','putBoolean','streamFailureKey']:
    if tok in fp: raise SystemExit('FAIL processor failure can poison discovery: '+tok)
for t in ['isDiscoveryStreamFailure','reason.startsWith("PREVIEW_SESSION_CONFIGURE_FAILED")','if (reason.contains("FIRST_FRAME_TIMEOUT")) return !currentStreamRawSeen','DISCOVERY_REJECT_DOMAIN_VIOLATION_']:
    need(owner,t,'discovery/processor domain separation')
# Camera2 Image must be detached before any GPU/native meter call.
for t in ['PREVIEW_RAW_STAGING','detachedRawPlane(image)','image.close()','SpektraRawProcessor.processLivePreview','nativeDecodeMeter']:
    need(raw,t,'detached RAW contract')
method=raw[raw.index('public static SpektraRawFrame copyPreviewFrom'):raw.index('/** Saved path',raw.index('public static SpektraRawFrame copyPreviewFrom'))]
method_code=re.sub(r'/\*.*?\*/|//.*?$|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',' ',method,flags=re.M|re.S)
close=method_code.index('image.close()')
if close > method_code.index('SpektraRawProcessor.processLivePreview') or close > method_code.index('nativeDecodeMeter'): raise SystemExit('FAIL Camera2 Image remains open through native work')
# Saved job is launched after one real resumed preview frame, but survives mode exit/failure.
for t in ['startPendingSavedProcess("preview_restored")','startPendingSavedProcess("mode_handoff")','startPendingSavedProcess("processor_failure")','startPendingSavedProcess("shutdown")']:
    need(owner,t,'saved-job continuity')
# Camera lifecycle cannot wait on native processing.
for t in ['forceCloseCameraTransportForHandoff()','IRIS_26687_SPEKTRA_HANDOFF_TIMEOUT','Camera transport retirement never waits on RAW/film GPU workers']:
    need(owner,t,'handoff containment')
if 'Spektra owner did not retire before mode handoff' in cap: raise SystemExit('FAIL crashing Spektra retirement survived')
# Native calls bounded; stats/release nonblocking; warm-up cannot wait behind healthy prior saved job.
clean_vk=re.sub(r'/\*.*?\*/|//.*?$|"(?:\\.|[^"\\])*"',' ',vk,flags=re.M|re.S)
if 'UINT64_MAX' in clean_vk: raise SystemExit('FAIL unbounded Vulkan fence')
for t in ['kPreviewFenceTimeoutNs','kSavedFenceTimeoutNs','VK_TIMEOUT','IRIS_26687_RAW_VK_TIMEOUT','IRIS_26687_RAW_VK_WARMUP_SELFTEST_PASS']:
    need(vk,t,'bounded Vulkan')
rel=vk[vk.index('void SpektraRawVulkanOwner::release'):vk.index('void SpektraRawVulkanOwner::stats')]
need(rel,'try_lock','nonblocking native release')
stats=vk[vk.index('void SpektraRawVulkanOwner::stats'):]
if 'workMutex' in stats.split('}',1)[0]: raise SystemExit('FAIL native stats blocks on work mutex')
warm=vk[vk.index('bool SpektraRawVulkanOwner::warmUp'):vk.index('void SpektraRawVulkanOwner::release')]
for t in ['initialized.load','!impl_->poisoned.load','try_lock']:
    need(warm,t,'nonblocking warmup')
need(owner,'RAW_GPU_WARMUP_TIMEOUT_MS = 10000L','pre-camera Vulkan warm-up budget')
for t in ['nativeWarmUpRawOwner','warmUpNativeOwner']:
    need(jni+rawp,t,'native warm-up bridge')
# Shell talks only through facade, and Spektra shutdown precedes legacy thread teardown.
for t in ['SpektraModeController','getSpektraModeController','shutdownSpektraMode','IRIS_26687_STALE_SPEKTRA_OWNER_RETIRED','spektraModeController.isShutterReady()']:
    need(cap,t,'Iris shell bridge')
if re.search(r'\bSpektraCameraOwner\b',re.sub(r'/\*.*?\*/|//.*?$|"(?:\\.|[^"\\])*"',' ',cap,flags=re.M|re.S)):
    raise SystemExit('FAIL CaptureController directly reaches Spektra owner')
on_destroy=frag[frag.index('public void onDestroy()'):frag.index('captureController = null;',frag.index('public void onDestroy()'))]
if on_destroy.index('shutdownSpektraMode()') > on_destroy.index('stopBackgroundThread()'): raise SystemExit('FAIL Spektra shutdown occurs after legacy teardown')
for text,name in [(param,'ParamController'),(touch,'TouchFocus'),(ui,'CameraUIController')]:
    if 'getSpektraCameraOwner' in text or re.search(r'\bSpektraCameraOwner\b',text): raise SystemExit('FAIL '+name+' direct owner access')
# Preserve successful 26686 RAW-domain/Vulkan/color contracts unchanged where not intentionally altered.
meta=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraFrameMetadata.java')
for t in ['activeRawDomain','hint = -1','leftNumerator % pixelArray.getWidth() == 0L','black[q] = sensorBlack[q ^ selectedOffset]','cfa = sensorCfa ^ selectedOffset']:
    need(meta,t,'26686 RAW geometry/CFA contract')
for t in ['clampActivePreservePhase','sensorRowParity=(xy.y&1)^((int(p[P_BAYER_OFFSET])>>1)&1)','return vec3(dot(r0,rgb),dot(r1,rgb),dot(r2,rgb))']:
    need(shader,t,'26686 native shader contract')
# Version exact.
ver=txt('app/version.properties')
for t in ['VERSION_NAME=0.9726687','VERSION_BUILD=26687']:
    need(ver,t,'version')
print('PASS 26687 semantics: sealed Spektra facade + Spektra-owned camera/job lifecycles + true shutter readiness + processor/discovery separation + detached Camera2 RAW + bounded/nonblocking Vulkan teardown + successful 26686 RAW-domain contracts preserved')
