#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26752_regressions.py BASE26733 CAND26752')
b,c=map(Path,sys.argv[1:])
def txt(r,p): return (r/p).read_text()
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
changed=set(Path(__file__).with_name('26752_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); B,C=H(b),H(c); assert {k for k in B|C if B.get(k)!=C.get(k)}==changed
cpp=txt(c,'app/src/main/cpp/motionv2_jpeg444_jni.cpp'); stack=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'); contracts=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt'); bridge=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'); renderjava=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'); params=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java'); nativejava=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisTrue2xSrNative.java'); render=txt(c,'app/src/main/assets/shaders/motionv2/render.glsl'); gain=txt(c,'app/src/main/assets/shaders/motionv2/gainmap.glsl')
# Exact paper core constants and revised sequence-wide Tukey zero extension.
for t in ['kPseudoInverseEps = 1.0e-9','kIrlsEtaFloor = 1.0e-2','kIrlsRelativeStop = 1.0e-5','kIrlsMaxIterations = 50','kTukeyR = 0.025','solveWeighted','residualNorm','blockPseudoInverse','fft2d','tukeyProfile']:
 assert t in cpp,t
assert 'maxAbsDx=std::max(maxAbsDx,std::fabs(dx[(size_t)j]))' in cpp
assert 'Dx=maxAbsDx*zx' in cpp and 'Dy=maxAbsDy*zy' in cpp
assert 'double eta=std::max(iris26752planb::kIrlsEtaFloor,z)' in cpp
assert 'std::fabs(E-prev)<=iris26752planb::kIrlsRelativeStop*std::fabs(prev)' in cpp
# JNI exact declarations exist both sides.
for n in ['writePlanBLumaTile','reconstructPlanBIrls','buildPlanBDetail','composePlanBRender']:
 assert nativejava.count('native boolean '+n)==1,n
 assert cpp.count('IrisTrue2xSrNative_'+n+'(')==1,n
# Device/lens-relative routing. No model gate and old global-20 activation gone from active bridge route.
assert 'localOutputZoom >= 1.10f' in bridge
assert 'deviceGate=false' in stack
assert 'frames[ev.frameIndex].lensState == referenceLens' in stack
assert 'frames[ev.frameIndex].role == RawBurstFrameRole.NORMAL' in stack
for bad in ['Build.MODEL','Build.MANUFACTURER','Xiaomi 15','xiaomi 15','displayedGlobalZoom >= 20','displayedGlobalZoom>=20']:
 assert bad not in stack+bridge,bad
# Plan B is luma/detail only; native Sabre/VGN remains chroma/highlight owner.
for t in ['lumaDetailOwner=IPOL_PLAN_B_IRLS','nativeSabreVgnChromaOwner=true','directChromaOwner=false','highlightOwnerUnchanged=true','rgbOwner=NATIVE_SABRE_VGN','chromaOwner=NATIVE_SABRE_VGN']:
 assert t in stack+bridge,t
assert 'highZoomRgbResult = null' in stack
assert '26752 Plan-B must never publish high-zoom RGB/chroma' in bridge
# Bright/flattened detail hard protection and agreement gates.
for t in ['float hg=1.f-iris26564::smooth01((peak-.72f)/.20f)','float confidence=clampf(signal*hg*ag*apod,0.f,1.f)','if(hg<=.001f)highlightBlocked++']:
 assert t in cpp,t
assert 'highlightFlattenedProtection=UNCHANGED' in stack
# No optional IPOL Section-7 sharpening introduced in Plan-B core/routing.
planb=cpp[cpp.index('IRIS_26752_IPOL_PLAN_B_TRANSLATIONAL_SUPERRES'):]
for bad in ['frequency amplification','kSharpen','PlanBSharpen','sharpening(']: assert bad not in planb,bad
# DNG cannot be Plan B owner; exact 26733 direct-CFA DNG boundary retained only when requested.
assert 'IRIS_26752_DNG_OWNER_UNCHANGED' in stack and 'reconstructDirectTrue2x26733' in stack
assert 'dngOwner=${if (preserveLinearRgbForDng) "DIRECT_CFA_26733" else "NONE"}' in stack
assert 'rawResult.backend=="PLAN_B"' in stack
# Arbitrary/non-integer geometry is float-carried end to end.
for t in ['highZoomDetailScaleX: Float','highZoomDetailScaleY: Float','highZoomDetailOriginXF: Float','highZoomDetailOriginYF: Float']:
 assert t in contracts,t
for t in ['motionV2HighZoomDetailScaleX','motionV2HighZoomDetailScaleY','motionV2HighZoomDetailOriginXF','motionV2HighZoomDetailOriginYF']:
 assert t in params+bridge+renderjava,t
for shader in (render,gain):
 for t in ['uniform vec2 iris26752PlanBDetailScale','uniform vec2 iris26752PlanBDetailOrigin','sourcePixel*iris26752PlanBDetailScale-iris26752PlanBDetailOrigin']:
  assert t in shader,t
# Fail-closed normal zoom. Plan B cannot prevent capture/publication if proof is insufficient.
assert 'IRIS_26752_PLAN_B_HIGH_ZOOM_FAIL_CLOSED' in stack
assert 'highZoomDetailResult = null' in stack
assert 'IRIS_26752_PLAN_B_HIGH_ZOOM_NATIVE_FALLBACK' in bridge
# Super Res same Plan-B engine.
assert 'val planB = reconstructPlanB26752(' in stack and 'publicationScale = 2f' in stack and 'backend = "PLAN_B"' in stack
# Evidence cap is an integration adaptation only; solver constants stay exact.
assert 'PLAN_B_MAX_EVIDENCE_26752 = 9' in stack
# Critical 26733 Motion capture transaction regressions fixed in the same 26752 handoff.
capture=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for t in ['IRIS_26752_CAPTURE_TRANSACTION_RACE_FIX','IRIS_26752_EARLY_NORMAL_RAW_TIMESTAMP_STAGING','MOTION_26752_EARLY_NORMAL_RAW_STAGING_MS = 150L','MOTION_26752_EARLY_NORMAL_RAW_LIMIT = 4','stageEarlyTopUpRaw(img)','claimStagedTopUpRaw(ticket, timestamp)','IRIS_26752_EARLY_NORMAL_RAW_CLAIMED_BY_RESULT','normalTargetMatchedHalAtShutter','requestModeFrozenAtShutter=']:
 assert t in capture,t
# The failed 26733 sequence must never be possible again: a manual top-up result cannot redefine
# later retry mode as HAL-equivalent. Shutter-time HAL equivalence is immutable.
assert 'final boolean halEquivalent = Boolean.TRUE.equals(aeLockAvailable)\n                && plan.normalTargetMatchedHalAtShutter;' in capture
assert 'plan.normalReferenceResult != null\n                && motion26713ResultMatchesTarget' not in capture
assert 'iris26713NormalTargetExp, iris26713NormalTargetIso,\n                iris26713TargetMatchesHal, iris26713NormalTargetOffsetEv' in capture
# Early unowned RAWs remain fail-closed: bounded staging only, exact timestamp ticket claim mandatory,
# expiry closes unmatched repeating RAWs, and final/failure cleanup closes every leftover staged RAW.
for t in ['ticket.offerRaw(staged.image)','expireStagedTopUpRaw(iris26752EarlyTs)','closeStagedEarlyTopUpRaws();','exactTimestampOwnerNeverArrived=true']:
 assert t in capture,t

# Version and no accidental 26750/26751 fine-color owners inherited because runtime reset is 26733.
vp=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726752' in vp and 'VERSION_BUILD=26752' in vp
post='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'; assert hashlib.sha256((b/post).read_bytes()).digest()==hashlib.sha256((c/post).read_bytes()).digest()
# Existing protected highlight/color owner carrier files outside allowlist are byte identical.
for p in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/src/main/assets/shaders/motionv2/color_transform.glsl']:
 assert (b/p).read_bytes()==(c/p).read_bytes(),p
print('PASS 26752 permanent regressions: lens-relative 1.10x all-device routing; same-lens NORMAL only; exact IPOL core constants/Tukey; no RGB/chroma/DNG/highlight ownership; no sharpening; noninteger geometry; fail-closed native fallback; critical early-RAW ownership + frozen NORMAL retry mode')
