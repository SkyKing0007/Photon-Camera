#!/usr/bin/env python3
from pathlib import Path
import hashlib,difflib,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: validate_26658.py BASE CANDIDATE')
base=Path(sys.argv[1]).resolve(); cand=Path(sys.argv[2]).resolve(); root=Path(__file__).resolve().parent
allow=[x for x in (root/'R1_26658_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def H(r): return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
bh,ch=H(base),H(cand); assert len(bh)==len(ch)==1721
actual=sorted(r for r in set(bh)|set(ch) if bh.get(r)!=ch.get(r))
if actual!=sorted(allow): raise SystemExit(f'FAIL 26658 exact allowlist actual={actual}')
if len(actual)!=6: raise SystemExit('FAIL 26658 changed count')
ver=(cand/'app/version.properties').read_text()
for x in ['VERSION_NAME=0.9726658','VERSION_BUILD=26658']:
 if x not in ver: raise SystemExit('FAIL version '+x)
cap=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
for x in [
'IRIS_26658_GOOGLE_HDR_BRACKETING_CAPTURE_OWNER','iris26593ShortSubmitted = false','iris26480ShortHighlightRequested = false',
'26658_google_hdr_bracketing_zsl_reference_group','IRIS_26658_GOOGLE_HDR_BRACKET_LONG_CAPTURE',
'MOTION_26658_LONG_MAX_EXPOSURE_NS = 66_666_667L','MOTION_26658_LONG_MIN_SHUTTER_RATIO = 1.15',
'isoOnlyLongForbidden=true','ImageFrame.MotionV2FrameRole.SHADOW_LONG']:
 if x not in cap: raise SystemExit('FAIL capture contract '+x)
# Active capture plan must not invoke the retired post-shutter SHORT helper.
plan=cap[cap.index('IRIS_26658_GOOGLE_HDR_BRACKETING_CAPTURE_OWNER'):cap.index('final Motion26505LongTicket iris26505LongTicket')+80]
if 'applyMotion26486ExplicitShortCaptureIfNeeded(' in plan: raise SystemExit('FAIL retired Motion SHORT still submitted')
# Legacy Short ticket pointer clearing must not seal the generation-owned nested LONG slot.
clear_start=cap.index('private void clearMotion26490CaptureShortTicket(')
clear_end=cap.index('private void removeMotion26490ExactShortFromNormalRing',clear_start)
clear_body=cap[clear_start:clear_end]
if '.sealAndClose()' in clear_body or 'shadowAuxSlot' in clear_body:
 raise SystemExit('FAIL retired SHORT ticket cleanup can alter nested LONG slot lifecycle')
motion_batch=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java').read_text()
for x in ['public final ShadowAuxSlot shadowAuxSlot = new ShadowAuxSlot();','shadowAuxSlot.freezePresent(shadowExpected);','shadowAuxSlot.sealAndClose();']:
 if x not in motion_batch: raise SystemExit('FAIL generation-owned LONG slot contract '+x)
for stale in ['normalAccumulatorAdmission=false','shadowNeverNormalFusion=true']:
 if stale in cap: raise SystemExit('FAIL stale LONG ownership telemetry '+stale)
bridge=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
for x in [
'IRIS_26658_GOOGLE_HDR_BRACKETING_REFERENCE_OWNER','reference\n            }','COMMON_SABRE_MOTION_GOOGLE_BRACKET_SHADOW_EVIDENCE',
'allowSabreShadowLong = parameters.irisNightActive || longFrame != null','preserveExtendedHdrThroughVgn = !parameters.irisNightActive',
'frame.role == RawBurstFrameRole.NORMAL || frame.role == RawBurstFrameRole.SHADOW_LONG']:
 if x not in bridge: raise SystemExit('FAIL bridge contract '+repr(x))
if 'CAPTURED_BUT_EXCLUDED_FROM_NORMAL_MOTION_SABRE' in bridge: raise SystemExit('FAIL old Motion LONG exclusion survived')
fusion=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt').read_text()
owner=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt').read_text()
for src,x in [(fusion,'preserveExtendedHdrThroughVgn: Boolean = false'),(fusion,'preserveExtendedHdrThroughVgn = preserveExtendedHdrThroughVgn'),(owner,'preserveExtendedHdrThroughVgn = preserveExtendedHdrThroughVgn &&')]:
 if x not in src: raise SystemExit('FAIL VGN HDR carrier contract '+x)
stack=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
for x in ['sourceClipGuard = frame.role == RawBurstFrameRole.SHADOW_LONG','IRIS_26658_LONG_FINAL_WEIGHT_PROOF','productionAccumulatorUnmodifiedByProof=true','if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)','IRIS_26658_GOOGLE_BRACKET_DNG_PRESERVATION']:
 if x not in stack: raise SystemExit('FAIL stacker contract '+x)
# Guard ordinary ZSL exposure policy: CaptureController edits are confined to auxiliary LONG staging/capture and generation planning.
a=(base/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text().splitlines()
b=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text().splitlines()
ud=list(difflib.unified_diff(a,b,n=0))
starts=[]
for line in ud:
 m=re.match(r'^@@ -(\d+)',line)
 if m: starts.append(int(m.group(1)))
allowed_ranges=[(3980,4335),(5680,5760),(6500,6660),(7000,7165),(7320,7620)]
for n in starts:
 if not any(lo<=n<=hi for lo,hi in allowed_ranges): raise SystemExit(f'FAIL CaptureController unexpected hunk oldLine={n}')
# Exact protected color/tone/edge-defense owners from 26653 remain unchanged.
protected=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl']
for r in protected:
 if bh[r]!=ch[r]: raise SystemExit('FAIL protected 26653 IQ owner changed '+r)
print('PASS 26658 semantics: ZSL reference-short + shutter-first SHADOW_LONG common Sabre; post-NORMAL SHORT retired; DNG/SR/26653 RGB-color-tone protections retained')
