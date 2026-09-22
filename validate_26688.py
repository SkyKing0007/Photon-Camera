#!/usr/bin/env python3
from pathlib import Path
import re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26688.py BASE CAND')
base,cand=map(Path,sys.argv[1:])
def txt(rel): return (cand/rel).read_text()
def same(rel):
    if (base/rel).read_bytes()!=(cand/rel).read_bytes(): raise SystemExit('FAIL protected semantic byte '+rel)
def need(text,tok,msg):
    if tok not in text: raise SystemExit('FAIL '+msg+': '+tok)
def clean(text): return re.sub(r'/\*.*?\*/|//.*?$|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',' ',text,flags=re.M|re.S)
owner=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java')
rawp=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawProcessor.java')
rawf=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawFrame.java')
jni=txt('app/src/main/cpp/spektra/SpektraNativeJni.cpp')
cpu=txt('app/src/main/cpp/spektra/SpektraRawCpuOwner.cpp')
cpuh=txt('app/src/main/cpp/spektra/SpektraRawCpuOwner.h')
cmake=txt('app/src/main/cpp/CMakeLists.txt')
# 26687 isolation remains the control plane.
need(owner,'final class SpektraCameraOwner','package-private camera owner')
for tok in ['CaptureJobState { IDLE, PROCESSING }','previewPresented.get()','savedProcessExecutor','previewDecodeExecutor','forceCloseCameraTransportForHandoff()','startPendingSavedProcess("mode_handoff")']:
    need(owner,tok,'26687 ownership/lifecycle')
if 'CaptureController.isProcessing' in owner: raise SystemExit('FAIL Iris processing authority returned')
# 26688 mode entry must open Camera2 without a RAW preflight/warm-up gate.
start=owner[owner.index('private void startCamera'):owner.index('public void closeCamera()',owner.index('private void startCamera'))]
for bad in ['RAW_GPU_WARMUP','warmUpNativeOwner','10000L']:
    if bad in start: raise SystemExit('FAIL blocking RAW warm-up returned: '+bad)
need(start,'IRIS_26688_SPEKTRA_CAMERA_ENTRY_IMMEDIATE','immediate camera entry marker')
need(start,'openForPreview(g, restart);','immediate Camera2 handoff')
need(owner,'SPEKTRA_PROFILE_SCHEMA = 26688','profile schema')
# Camera2 Images are detached/closed before native RAW processing.
method=rawf[rawf.index('public static SpektraRawFrame copyPreviewFrom'):rawf.index('/** Saved path',rawf.index('public static SpektraRawFrame copyPreviewFrom'))]
method_exec=re.sub(r'/\*.*?\*/|//.*?$',' ',method,flags=re.M|re.S)
close=method_exec.index('image.close()')
if close>method_exec.index('SpektraRawProcessor.processLivePreview') or close>method_exec.index('nativeDecodeMeter'):
    raise SystemExit('FAIL Camera2 Image survives into native RAW work')
# Active native target uses only the new CPU RAW owner. Old Vulkan RAW implementation may remain as dormant authority history only.
target=cmake[cmake.index('add_library(spektra_iris SHARED'):cmake.index('set_target_properties(spektra_iris',cmake.index('add_library(spektra_iris SHARED'))]
need(target,'spektra/SpektraRawCpuOwner.cpp','CPU RAW target')
if 'SpektraRawVulkanOwner.cpp' in target: raise SystemExit('FAIL broken RAW Vulkan owner remains active in target')
need(jni,'#include "SpektraRawCpuOwner.h"','JNI CPU RAW owner')
need(jni,'SpektraRawCpuOwner::instance().process','JNI CPU RAW process')
for bad in ['SpektraRawVulkanOwner','nativeWarmUpRawOwner','warmUp(']:
    if bad in clean(jni): raise SystemExit('FAIL stale RAW Vulkan/warmup JNI authority '+bad)
if 'nativeWarmUpRawOwner' in rawp or 'warmUpNativeOwner' in rawp: raise SystemExit('FAIL Java warm-up API survived')
# CPU engine must own unpack -> normalization/LSC -> demosaic -> color -> RGBA16F, with no GL/Vulkan dependency.
for tok in ['q.format == 37','q.format == 38','std::max(2, q.pixelStride)','blackLevel4','lscGainChannel','semanticLscChannel','normalized*lscGainChannel','demosaicRaw','highlightRecover','sensorToLinear','floatToHalf','applySavedChromaDenoise','IRIS_26688_RAW_CPU_STAGE']:
    need(cpu,tok,'CPU RAW stage')
if 'applyLensShading' in cpu: raise SystemExit('FAIL LSC moved after demosaic; must remain per-photosite before interpolation')
for tok in ['class SpektraRawCpuOwner','RawDevelopRequest','previewDropped','elapsedMicros']:
    need(cpuh,tok,'CPU RAW interface')
cclean=clean(cpu)
for bad in ['vkCreate','vkQueue','vkWait','VkDevice','GLContext','GLProg','GLTexture','RCD26498']:
    if bad in cclean: raise SystemExit('FAIL CPU RAW owner contains forbidden GPU/Iris authority '+bad)
# Preserve the verified RAW geometry/color convention from 26687.
meta=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraFrameMetadata.java')
for tok in ['activeRawDomain','black[q] = sensorBlack[q ^ selectedOffset]','cfa = sensorCfa ^ selectedOffset']:
    need(meta,tok,'RAW geometry/CFA contract')
for tok in ['sensorRowParity=(y&1)^((q.bayerOffset>>1)&1)','q.sensorToLinearSrgb[0]*s.r','q.sensorToLinearSrgb[3]*s.r','q.sensorToLinearSrgb[6]*s.r']:
    need(cpu,tok,'CPU RAW phase/matrix contract')
# Public SPEKTRA film/print engine and IQ assets are unchanged; only RAW frontend changes.
for rel in [
 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraFilmRenderer.java',
 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraColorSolver.java',
 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraJpegPublisher.java',
 'app/src/main/cpp/spektra/SpektraRawDevelop.comp']:
    same(rel)
ver=txt('app/version.properties')
for tok in ['VERSION_NAME=0.9726688','VERSION_BUILD=26688']: need(ver,tok,'version')
print('PASS 26688 semantics: 26687 isolated control plane preserved; Camera2 entry immediate; broken RAW Vulkan owner dormant; staged native CPU RAW developer owns unpack/CFA/LSC/reconstruction/color; public SPEKTRA film/JPEG path unchanged')
