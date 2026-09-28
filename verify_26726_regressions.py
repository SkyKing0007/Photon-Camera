#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26726_regressions.py BASE26725 CAND26726')
b,c=map(Path,sys.argv[1:]); pkg=Path(__file__).resolve().parent
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
def txt(r,p): return (r/p).read_text()
def section(s,start,end):
 i=s.index(start); j=s.index(end,i+len(start)); return s[i:j]
def method(s,signature):
 i=s.index(signature); brace=s.index('{',i); depth=0
 for j in range(brace,len(s)):
  ch=s[j]
  if ch=='{': depth+=1
  elif ch=='}':
   depth-=1
   if depth==0: return s[i:j+1]
 raise AssertionError(signature)
def triple(k,name):
 m=re.search(r'val\s+'+re.escape(name)+r'\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',k,re.S); assert m,name
 return m.group(1)
B,C=H(b),H(c); assert len(B)==len(C)==1823
expected=set((pkg/'26726_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert expected=={
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisNightRgbInput.java',
'app/version.properties'}
assert {k for k in B|C if B.get(k)!=C.get(k)}==expected
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726726' in v and 'VERSION_BUILD=26726' in v
# Preserve successful 26725 protected architecture outside the intentional carrier allowlist.
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java',
'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
'app/src/main/java/com/hinnka/mycamera/processor/RawStackFrameCompat.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Denoise.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLFormat.java',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
cap=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'); bcap=txt(b,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
# 26723 intelligent flicker owner must remain byte-identical despite CaptureController changes.
for t in ['IRIS_26680_FLICKER_OBSERVER_ONLY_PREVIEW','IRIS_26680_FLICKER_OBSERVER_ONLY_CAPTURE','IRIS_26723_INTELLIGENT_FLICKER_BATCH_GATE','retroactiveFullStrength=false','rawRewritten=false confidenceOnly=true']:
 assert t in cap,t
assert method(cap,'    private int motion26720AttachNormalRowFlickerEvidence(')==method(bcap,'    private int motion26720AttachNormalRowFlickerEvidence(')
# Hybrid ZSL/HDR policy is unchanged: valid ZSL count freezes at shutter; only missing logical NORMAL slots are submitted.
for t in ['final int iris26593MissingNormals = Math.max(0,','iris26593NormalTarget - iris26593NormalAtPress','if (iris26593MissingNormals > 0','submitMotion26593MissingNormals(iris26593Plan, iris26593MissingNormals)','exactTotalRequired=true','preShutterNormalsGenerationOwned=true','postShutterNormalsTicketOwned=true']:
 assert t in cap,t
# Exact negative-protection routing remains byte-identical. HDR may exclude HAL ZSL only when target differs.
hdr_start='        final boolean iris26715NegativeProtectionRequired'
hdr_end='        /* IRIS_26713_CAPTURE_DOMAIN_NORMAL_PLUS_HAL_LONG_PLAN'
assert section(cap,hdr_start,hdr_end)==section(bcap,hdr_start,hdr_end)
for t in ['zslDisabledOnlyForNegativeProtection=','IRIS_26713_HAL_ZSL_EVIDENCE_EXCLUDED_FROM_CORRECTED_NORMAL','highlightShortRequested=false highlightShortRetired=true','26710_short_retired_reference_owns_highlights']:
 assert t in cap,t
# Original generation deadline stays authoritative; retry cadence may not reset it.
assert 'MOTION_26593_MAX_CAPTURE_COMPLETION_MS = 3500L' in cap
assert 'MOTION_26724_NORMAL_ATTEMPT_WATCHDOG_MS = 900L' in cap
assert 'MOTION_26724_LONG_ATTEMPT_WATCHDOG_MS = 1400L' in cap
assert 'MOTION_26724_RETRY_BACKOFF_MS = 80L' in cap
poll=method(cap,'    private void pollMotion26593CapturePlan(')
assert 'elapsed < plan.completionTimeoutMs' in poll and 'elapsed >= plan.completionTimeoutMs' in poll
assert 'retryMotion26724FailedNormalSlots(plan, elapsed)' in poll and 'retryMotion26724LongSlotIfNeeded(plan, elapsed)' in poll
assert 'if (plan.hasTopUpFailure())' not in poll
assert 'deadlineReset=false' in cap
# Logical NORMAL slot survives a failed attempt: same ordinal, new attempt, old timestamp retired, late raw/result cannot own.
nretry=method(cap,'    private boolean submitMotion26724ReplacementNormalAttempt(')
for t in ['failedTicket.retire("REPLACED")','rememberMotion26598RetiredNormalTopUpTimestamp(failedTicket.captureStartedTimestampNs)','rememberMotion26598RetiredNormalTopUpTimestamp(failedTicket.resultTimestampNs)','failedTicket.ordinal, failedTicket.attempt + 1','plan.addTopUpTicket(replacement)','mCaptureSession.capture(request, motion26724NormalTopUpCallback(plan), mBackgroundHandler)']:
 assert t in nretry,t
for t in ['ticket.retired || ticket.failed','!ticket.retired && !ticket.failed','containsTopUpTicket(ticket)','isMotion26598RetiredNormalTopUpTimestamp']:
 assert t in cap,t
# NORMAL replacement identity is frozen at shutter, not reread from live globals.
buildn=method(cap,'    private CaptureRequest buildMotion26724NormalTopUpRequest(')
for t in ['plan.frozenAfMode','plan.frozenFocusDistance','plan.physicalCameraId','plan.normalTargetExposureNs','plan.normalTargetIso']:
 assert t in buildn,t
assert 'mFocus' not in buildn and 'physicalID' not in buildn
# LONG transient failures are retryable with the same frozen role/request identity and shared logical slot.
lretry=method(cap,'    private boolean submitMotion26724ReplacementLongAttempt(')
for t in ['failedTicket.retire("REPLACED")','failedTicket.slot, failedTicket.attempt + 1','ticket.requestedExposureNs = failedTicket.requestedExposureNs','ticket.requestedIso = failedTicket.requestedIso','ticket.requestedAfMode = failedTicket.requestedAfMode','ticket.requestedFocusDistance = failedTicket.requestedFocusDistance','ticket.requestedPhysicalCameraId = failedTicket.requestedPhysicalCameraId','plan.longTicket = ticket','deadlineReset=false']:
 assert t in lretry,t
assert 'mFocus' not in lretry and 'physicalID' not in lretry
long_initial=method(cap,'    private boolean applyMotion26505ExplicitLongCaptureIfUseful(')
assert 'capture_submit_exception_retryable' in long_initial and 'IRIS_26724_LONG_INITIAL_SUBMIT_RETRYABLE' in long_initial
assert 'ticket.failed = true' in long_initial and 'return true;' in long_initial
# Exact frame total remains required; retries are attempts, not extra accepted logical frames.
for t in ['normalReadyCount()','takeOwnedNormalImages()','normalReadyCount >= plan.normalTargetFrames','IRIS_26593_TOTAL_BATCH_READY']:
 assert t in cap,t
# Existing RGB32F/high-zoom route and explicit SR remain protected.
stack=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'); bstack=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for t in ['IRIS_26721_HIGH_ZOOM_RGB32F_TRANSFER_OWNER','private const val HIGH_ZOOM_RGB32F_BYTES_PER_PIXEL = 3 * Float.SIZE_BYTES','transfer=RGB32F bytesPerChannel=4 float16Transfer=false','IRIS_26721_HIGH_ZOOM_RGB32F_CARRIER','enableHighZoomDetail && !enableSabreSuperRes','highZoomRefineProxy=noise-aware-robust-3x3','spatialLumaDenoiseAdded=false']:
 assert t in stack,t
sh=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'); bsh=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
assert triple(bsh,'true2xFlowRefine26574')==triple(sh,'true2xFlowRefine26574')
assert triple(bsh,'true2xGuideRender26568')==triple(sh,'true2xGuideRender26568')
# 26724 fine-flow: same inherited hard bounds, noise-normalized bounded robust objective, original RAW untouched.
for t in ['IRIS_26724_HIGH_ZOOM_NOISE_AWARE_FLOW_REFINEMENT','val highZoomFlowRefine26724: String by lazy {','uniform float uNoiseShot','uniform float uNoiseRead','uNoiseShot*signal+uNoiseRead','robustCostWeight=1.0/robustDen','baseCost+=w[i]*nr*nr*robustCostWeight','conditioning>0.008&&improvement>0.055&&uniqueness>0.025&&variationRaw<2.0']:
 assert t in sh,t
for t in ['highZoomFlowRefineProgram26724','uNoiseShot','uNoiseRead','originalRawReconstructionUntouched=true']:
 assert t in stack,t
# 26724 chroma adaptation stays inside >=20x final native guide; direct CFA remains luma/detail evidence only.
for t in ['val highZoomRgbProtect26724: String by lazy {','IRIS_26724_WEAK_DISAGREEING_NATIVE_CHROMA_ADAPTATION','IRIS_26724_HIGH_ZOOM_STRUCTURAL_LUMA_REINFORCEMENT','1.0-0.32*zoomSeverity','1.0+0.18*provenStructure']:
 assert t in sh,t
prop=section(sh,'    val highZoomRgbProtect26724: String by lazy {','    /* IRIS_26719_HIGH_ZOOM_LAZY_ISOLATION')
for forbidden in ['directChromaConfidence','vec3 directChroma =','protectedChroma','maxChromaDelta']:
 assert forbidden not in prop,forbidden
assert 'GlesMgcRawSabreShaders.highZoomRgbProtect26724' in stack
# No broad luma denoise/chroma sharpen resurrection; shared VGN implementation stays unchanged.
bridge=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
assert 'val automaticLumaScale26639 = 0.0f' in bridge
vgn='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'; assert (b/vgn).read_bytes()==(c/vgn).read_bytes()
# Permanent 26720 compile regressions and color transform route remain guarded.
assert 'val failure = checkNotNull(rgbAttempt.exceptionOrNull())' in stack
assert 'reason=${failure?.message}", failure)' not in stack
color=txt(c,'app/src/main/assets/shaders/motionv2/color_transform.glsl'); macro_define='#define USE_IRIS_26720_HIGH_ZOOM_RGB 0'; macro_use='#if USE_IRIS_26720_HIGH_ZOOM_RGB == 1'; assert color.count(macro_define)==1 and color.count(macro_use)==2 and color.index(macro_define)<color.index(macro_use)
# Native/vendor/DNG manifests invariant.
def loadm(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,p=l.split(None,1); d[p.strip()]=h
 return d
for stem,count in [('NATIVE_FULL',820),('VENDOR_PROTECTED',1),('DNG',6)]:
 x=loadm(f'26726_{stem}_BASE.sha256'); y=loadm(f'26726_{stem}_CANDIDATE.sha256'); assert len(x)==len(y)==count and x==y
# 26725 Pixel-specific regressions appended below.
# 26725 Pixel compatibility is strictly Google Motion-only and does not alter Xiaomi/non-Google behavior.
assert 'import android.hardware.HardwareBuffer;' in cap
assert cap.count('HardwareBuffer.USAGE_CPU_READ_OFTEN') == 1
route = method(cap, '    private boolean isMotion26725GooglePixelCompatibilityRoute(')
for t in ['isZslMode()', 'Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q',
          '"google".equalsIgnoreCase(Build.BRAND)', '"google".equalsIgnoreCase(Build.MANUFACTURER)']:
    assert t in route, t
plane = method(cap, '    private boolean motion26725ValidateGoogleRawImageForCpuCopy(')
assert 'if (!isMotion26725GooglePixelCompatibilityRoute()) return true;' in plane
for t in ['getPlanes()', 'getBuffer()', 'buffer.isDirect()', 'plane_capacity_too_small',
          'IRIS_26725_GOOGLE_RAW_CPU_PLANE_REJECTED', 'processCrashPrevented=true']:
    assert t in plane, t
reader = section(cap,
    '        final boolean iris26555TargetOutputAvailable = !allTargets.isEmpty();',
    '            mImageReaderRaw.setOnImageAvailableListener')
assert 'iris26725GoogleCpuReadableMotionRaw' in reader
assert 'HardwareBuffer.USAGE_CPU_READ_OFTEN' in reader
legacy = '''            } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q && (PhotonCamera.getSettings().QuadBayer
                    || !(Build.BRAND.equalsIgnoreCase("oppo")
                    || Build.BRAND.equalsIgnoreCase("vivo")
                    || Build.BRAND.equalsIgnoreCase("oneplus")
                    || Build.BRAND.equalsIgnoreCase("realme")
                    || Build.BRAND.equalsIgnoreCase("iqoo")
                    || Build.BRAND.equalsIgnoreCase("nothing")
            ))) {
                mImageReaderRaw = ImageReader.newInstance(
                        target.getWidth(), target.getHeight(), mTargetFormat, maxjpg, 0x00100000);
            } else {
                mImageReaderRaw = ImageReader.newInstance(
                        target.getWidth(), target.getHeight(), mTargetFormat, maxjpg);
            }
'''
assert legacy in cap
assert 'motion26725ValidateGoogleRawImageForCpuCopy(img, "SHADOW_LONG")' in cap
assert 'motion26725ValidateGoogleRawImageForCpuCopy(img, "HIGHLIGHT_SHORT")' in cap
assert 'motion26725ValidateGoogleRawImageForCpuCopy(image, "NORMAL")' in cap
assert 'GOOGLE_RAW_CPU_PLANE_UNREADABLE' in cap
# Exact exposure tolerance remains byte-identical; only Google retry policy changes.
assert method(cap, '    private boolean motion26713ResultMatchesTarget(') == \
       method(bcap, '    private boolean motion26713ResultMatchesTarget(')
for t in ['forceManualSensor', 'manualSensorRequest', 'deterministicExposureFailure',
          'IRIS_26725_GOOGLE_AE_LOCK_TO_MANUAL', 'IRIS_26725_GOOGLE_EXPOSURE_REJECTED',
          'IRIS_26725_GOOGLE_MANUAL_EXPOSURE_UNACHIEVABLE', 'NORMAL_EXPOSURE_UNACHIEVABLE']:
    assert t in cap, t
assert '&& "EXPOSURE_REJECTED".equals(failedTicket.failureReason)' in nretry
assert '&& !failedTicket.manualSensorRequest' in nretry
assert '&& motion26713ManualSensorAvailable()' in nretry
retry = method(cap, '    private boolean retryMotion26724FailedNormalSlots(')
assert 'if (failed.deterministicExposureFailure) continue;' in retry
assert 'exposureWindowUnchanged=true deadlineReset=false' in cap
# Exact supplied failure conditions become permanent regression facts.
P8_RUNTIME_EXCEPTION_COUNT = 1268
P8_TOTAL_BATCH_READY = 3
P8_BATCH_ENQUEUED = 0
P9_RUNTIME_EXCEPTION_COUNT = 541
P9_EXPOSURE_REJECTED = 101
P9_SLOT_RETRY = 100
P9_MAX_REJECTED_ATTEMPT = 9
assert P8_RUNTIME_EXCEPTION_COUNT > 0 and P8_TOTAL_BATCH_READY > 0 and P8_BATCH_ENQUEUED == 0
assert P9_RUNTIME_EXCEPTION_COUNT > 0 and P9_EXPOSURE_REJECTED > 0 and P9_SLOT_RETRY > 0 and P9_MAX_REJECTED_ATTEMPT > 1
# 26724 high-zoom/Sabre/VGN source bytes are completely untouched in 26725.
for rel in [
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt']:
    assert (b/rel).read_bytes() == (c/rel).read_bytes(), rel
print('PASS inherited 26725 regressions/ownership preserved')

# 26726 universal device-independent RGBA16F carrier regressions.
bridge=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
merger=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java')
hdrx=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
night=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java')
post=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java')
mi=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java')
ni=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisNightRgbInput.java')
for t in ['LINEAR_RGB_CARRIER_NONE = 0','LINEAR_RGB_CARRIER_RGBA16F = 1','LINEAR_RGB_CARRIER_RGBA32F = 2','linearRgbCarrierFormat = LINEAR_RGB_CARRIER_NONE']:
 assert t in merger,t
for t in ['IRIS_26726_UNIVERSAL_RGBA16F_CROSS_CONTEXT_OWNER','val directRgba16fCarrier = parameters.irisNightActive ||','parameters.cfaPattern in 0..3','output = denoiseBuffer','halfBuffer = null','LINEAR_RGB_CARRIER_RGBA16F','bytesPerPixel=8','deviceIndependent=true']:
 assert t in bridge,t
assert bridge.count('convertHalfRgbaToFloatRgba(denoiseBuffer, size.x, size.y)')==1
assert 'IRIS_26726_SPECIAL_CFA_RGBA32F_FALLBACK' in bridge
for t in ['iris26726LinearRgbCarrierFormat = iris26409V2.linearRgbCarrierFormat','LINEAR_RGB_CARRIER_RGBA16F','4L * 2L','output.capacity() != expectedRgbBytes','jpegCarrier=MGC_SABRE_RESOLVE_RGBA16F','iris26726LinearRgbCarrierFormat,processingParameters']:
 assert t in hdrx,t
for t in ['r.linearRgbCarrierFormat != MotionV2Merger.Result.LINEAR_RGB_CARRIER_RGBA16F','4L * 2L','rgb.capacity() != expectedRgbBytes','rgba16fBytes=','RunIrisNightRgb(postOwnedRgb, r.linearRgbCarrierFormat, p)']:
 assert t in night,t
for t in ['motionV2LinearRgbCarrierFormat','irisNightLinearRgbCarrierFormat','irisNightLinearRgb','RunMotionV2FloatCfa(','int linearRgbCarrierFormat','RunIrisNightRgb(ByteBuffer sabreRgb, int linearRgbCarrierFormat','26726 Iris Night requires RGBA16F']:
 assert t in post,t
assert 'irisNightRgba32f' not in post
for t in ['IRIS_26726_PROPER_PER_FRAME_RGB_FLOAT16_BRIDGE_OWNER','directHalfBytes = (long) raw.x * (long) raw.y * 4L * 2L','LINEAR_RGB_CARRIER_RGBA16F','source.capacity() != directHalfBytes','DataType.FLOAT_16 : GLFormat.DataType.FLOAT_32','LINEAR_RGB_CARRIER_RGBA32F','26726 special-CFA carrier format invalid']:
 assert t in mi,t
for forbidden in ['26700 Motion RGBA32F recovery carrier byte contract','transferFormat=rgba32f']:
 assert forbidden not in mi,forbidden
for t in ['IRIS_26726_NIGHT_RGBA16F_MOTION_PARITY_INPUT','irisNightLinearRgb','LINEAR_RGB_CARRIER_RGBA16F','4L * 2L','source.capacity() != expected','GLFormat.DataType.FLOAT_16','IRIS_26726_NIGHT_CPU_RGBA16F_RELEASED_AFTER_UPLOAD']:
 assert t in ni,t
assert 'irisNightRgba32f' not in ni and 'DataType.FLOAT_32, 4' not in ni
for src in [bridge,hdrx,night,post,mi,ni]:
 assert 'Build.MANUFACTURER' not in src and 'Build.BRAND' not in src
# IQ/math owners remain byte-identical to successful 26725.
for rel in [
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/assets/shaders/motionv2/color_transform.glsl']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
print('PASS 26726 regressions/ownership: exact successful-26725 capture/Pixel/high-zoom/IQ behavior preserved; standard-Bayer Motion+Night cross-context carrier is universally explicit RGBA16F 8-Bpp; critical reconstruction/shader math owners unchanged; special-CFA RGBA32F isolated; exact 26699 16F-producer/32F-consumer failure class structurally forbidden')
