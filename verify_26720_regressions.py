#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26720_regressions.py BASE26719 CAND26720')
b,c=map(Path,sys.argv[1:]); pkg=Path(__file__).resolve().parent
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
def txt(r,p): return (r/p).read_text()
B,C=H(b),H(c); assert len(B)==len(C)==1823
expected=set((pkg/'26720_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert len(expected)==14; assert {k for k in B|C if B.get(k)!=C.get(k)}==expected
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726720' in v and 'VERSION_BUILD=26720' in v
# Protected owners whose behavior must not move in this build.
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/app/PhotonCamera.java',
'app/src/main/java/com/particlesdevs/photoncamera/util/Log.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
'app/src/main/assets/shaders/preview/main_fs.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java',
'app/src/main/java/com/particlesdevs/photoncamera/api/VendorTagUtils.java']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
# Capture-domain row flicker: exact physical-frame evidence only; no RAW rewrite / no HAL AE mutation.
cap=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for t in [
'IRIS_26720_CAPTURE_ROW_FLICKER_EVIDENCE',
'motion26720FindExactFrameFlickerEvidenceLocked',
'motion26720AttachNormalRowFlickerEvidence(selected)',
'MOTION_26678_FLICKER_MIN_LOG_AMPLITUDE',
'frame.motionV2RowFlickerStrength = 1.0f',
'IRIS_26720_LEAST_FLICKERED_STRUCTURAL_REFERENCE',
'rawRewritten=false confidenceOnly=true',
'shortLongUntouched=true highlightRecoveryUntouched=true dngUntouched=true']:
 assert t in cap,t
m=re.search(r'private boolean applyMotion26678NormalRowFlickerCorrection\([^}]+?\{\s*return false;\s*\}',cap,re.S); assert m,'RAW rewrite must remain disabled'
# The new capture handoff must not use allowRecent/stale preview evidence.
newcap=cap[cap.index('/* IRIS_26720_CAPTURE_ROW_FLICKER_EVIDENCE'):cap.index('/*\n     * IRIS_26380_SPARSE_RAW_SIGNAL_SAMPLER')]
assert 'allowRecent' not in newcap and 'motion26678FindEvidenceLocked' not in newcap
# Per-frame fields and transport: only NORMAL receives flicker; gyro is metadata, never global discard.
img=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java')
for t in ['motionV2RowFlickerValid','motionV2RowFlickerHarmonic','motionV2RowFlickerA','motionV2RowFlickerB','motionV2RowFlickerAmplitude','motionV2RowFlickerStrength']:
 assert t in img,t
compat=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/RawStackFrameCompat.kt')
for t in ['rowFlickerHarmonic','rowFlickerA','rowFlickerB','rowFlickerStrength','gyroShakiness','gyroSampleCount']:
 assert t in compat,t
bridge=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
for t in [
'role == RawBurstFrameRole.NORMAL && frame.motionV2RowFlickerValid',
'gyroShakiness = frame.frameGyro?.shakiness',
'gyroSampleCount = frame.frameGyro?.samples',
'parameters.motionV2Active && !parameters.irisNightActive',
'!sabreSuperResEnabled && displayedGlobalZoom >= 20f && localOutputZoom > 1.00001f',
'parameters.motionV2HighZoomRgbPrepared = true',
'parameters.motionV2ReconstructionZoom = localOutputZoom',
'parameters.motionV2RenderResidualZoom = 1f',
'IRIS_26720_HIGH_ZOOM_RGB_HANDOFF',
'IRIS_26720_HIGH_ZOOM_RGB_FALLBACK_HANDOFF']:
 assert t in bridge,t
assert 'globalGyroDiscard=true' not in bridge
# Stacker: one Sabre merge program; row confidence cannot create a duplicate merge owner.
stack=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for forbidden in ['merge26720RowFlicker','sabreMergeRowFlickerProgram26720']:
 assert forbidden not in stack,forbidden
for t in [
'uRowFlickerEnabled',
'rowFlickerReference26720: RawStackFrame? = null',
'rowFlickerCurrent26720: RawStackFrame? = null',
'frame.role == RawBurstFrameRole.NORMAL',
'IRIS_26720_HIGH_ZOOM_DIRECT_CFA_RGB_GPU',
'highZoomObservationQuality26720',
'globalGyroDiscard=false opticalFlowAuthority=true',
'GlesMgcRawSabreShaders.highZoomRgbMerge26720',
'GlesMgcRawSabreShaders.highZoomRgbProtect26720',
'IRIS_26720_HIGH_ZOOM_RGB_FALLBACK_26719',
'reconstructHighZoomDetail26718',
'rgbOwner=DIRECT_CFA_WITH_NATIVE_SABRE_VGN_LOCAL_FALLBACK',
'rawRewrite=false shortHighlightOwnerUnchanged=true']:
 assert t in stack,t
assert stack.count('uniform1i(program,"uRowFlickerEnabled",if(rowFlickerActive26720)1 else 0)')==1
# Permanent regression from failed 26720 R1 Actions run 36349907215: Result.exceptionOrNull()
# is Throwable?, while PLog.e(tag,message,error) requires a non-null Throwable. In the failure
# branch, prove non-null once before logging and reuse that non-null value.
assert 'val failure = checkNotNull(rgbAttempt.exceptionOrNull())' in stack
assert 'reason=${failure.message}", failure)' in stack
assert 'reason=${failure?.message}", failure)' not in stack
# Explicit SR reservoir remains separate and high zoom retains all admitted NORMAL evidence.
for t in ['val true2xFastPhaseSlots: Array<True2xFrameEvidence?>?','val highZoomEvidence26718 = ArrayList<True2xFrameEvidence>()','existingPhaseEvidence = null','refineForHighZoom26718 = true','enableSabreSuperRes && enableHighZoomDetail']:
 assert t in stack,t
# DNG merge path must remain row-flicker independent.
dngm=re.search(r'private fun renderSabreNormalDngMerge\(.*?\n    \}',stack,re.S); assert dngm
assert 'rowFlicker' not in dngm.group(0)
# Shader contracts: direct chroma is confidence gated, native guide is local fallback, highlight gate retained.
sh=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
for t in [
'IRIS_26720_CAPTURE_ROW_FLICKER_CONFIDENCE',
'IRIS_26720_REFERENCE_ROW_FLICKER_MERGE_CONFIDENCE',
'val highZoomRgbMerge26720: String by lazy',
'val highZoomRgbProtect26720: String by lazy',
'fullPhaseGate', 'strongTemporalGate', 'strictChromaAgreement', 'highlightGate', 'boundarySafe',
'directChromaConfidence', 'protectedChroma',
'IRIS_26719_HIGH_ZOOM_LAZY_ISOLATION']:
 assert t in sh,t
# Raw stack result contract must contain every bridge field, including the compile-miss regression.
contracts=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt')
for t in ['highZoomRgbPath','highZoomRgbWidth','highZoomRgbHeight','highZoomRgbPhaseP10','highZoomRgbRefineAcceptedPct','highZoomRgbFrames']:
 assert t in contracts,t
# Color stage is the sole place where protected compact RGB replaces the camera-linear input.
color=txt(c,'app/src/main/assets/shaders/motionv2/color_transform.glsl')
for t in ['USE_IRIS_26720_HIGH_ZOOM_RGB','iris26720HighZoomRgb','iris26720HighZoomOrigin','iris26720HighZoomFullSize','iris26720HighZoomSourceZoom']:
 assert t in color,t
assert color.count('cameraRgb=max(texture(iris26720HighZoomRgb')==1
# Permanent regression from failed 26720 Actions run 36349017340: GLSL ES forbids
# evaluating an undefined macro in #if. The default definition must precede first use.
macro_define='#define USE_IRIS_26720_HIGH_ZOOM_RGB 0'
macro_use='#if USE_IRIS_26720_HIGH_ZOOM_RGB == 1'
assert color.count(macro_define)==1 and color.count(macro_use)==2
assert color.index(macro_define) < color.index(macro_use), '26720 high-zoom macro used before default definition'
ct=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java')
for t in ['IRIS_26720_HIGH_ZOOM_RGB_TEXTURE_OWNER','motionV2HighZoomRgbPrepared','motionV2HighZoomRgbApplied=true','USE_IRIS_26720_HIGH_ZOOM_RGB']:
 assert t in ct,t
# Final renderer: exact 26719 gating survives and either RGB-applied or scalar-sidecar owns >=20x.
render=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
for t in ['basePipeline.mParameters.motionV2Active','!basePipeline.mParameters.irisNightActive','basePipeline.mParameters.motionV2GlobalZoom >= 20.0f','basePipeline.mParameters.motionV2OutputZoom > 1.00001f','!basePipeline.mParameters.motionV2SuperResOutputEnabled','basePipeline.mParameters.motionV2HighZoomRgbApplied']:
 assert t in render,t
# PostPipeline enforces no leaked geometry below high zoom.
post=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java')
for t in ['final boolean highZoomRgb26720 = mParameters.motionV2HighZoomRgbPrepared','mParameters.motionV2GlobalZoom >= 20.0f','mParameters.motionV2RenderResidualZoom']:
 assert t in post,t
# Exception cleanup is explicit.
hdr=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
assert 'motionV2HighZoomRgbPath' in hdr and 'deleteIfExists' in hdr
# Category invariance remains a semantic requirement.
for stem,count in [('NATIVE_FULL',820),('VENDOR_PROTECTED',1),('DNG',6)]:
 def load(n):
  d={}
  for l in (pkg/n).read_text().splitlines():
   if l.strip(): h,p=l.split(None,1); d[p.strip()]=h
  return d
 x=load(f'26720_{stem}_BASE.sha256'); y=load(f'26720_{stem}_CANDIDATE.sha256'); assert len(x)==len(y)==count and x==y
print('PASS 26720 regressions/ownership: exact-timestamp NORMAL row-flicker confidence with no RAW/AE/SHORT/DNG rewrite; >=20x-only direct-CFA protected RGB with gyro/focus confidence and native Sabre/VGN local fallback; 26719 scalar fallback; <20/Night/explicit-SR isolation preserved')
