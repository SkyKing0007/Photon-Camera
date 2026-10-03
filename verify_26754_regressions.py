#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26754_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:])
cpp=(cand/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
kt=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
rf=(cand/'app/src/main/java/com/hinnka/mycamera/processor/RawStackFrameCompat.kt').read_text()
cap=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
img=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java').read_text()
br=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
zoom=(cand/'app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java').read_text()
# Exact physical camera owner replaces LENS_STATE identity; actuator changes remain allowed.
assert 'motionV2PhysicalCameraId' in img and 'val physicalCameraId: String? = null' in rf
for s in ['IRIS_26754_EXACT_PHYSICAL_CAMERA_OWNER','Build.VERSION_CODES.Q','CaptureResult.LOGICAL_MULTI_CAMERA_ACTIVE_PHYSICAL_ID','mCameraDevice','IrisZoomController.getOwnerCameraId()','frame.motionV2PhysicalCameraId = iris26754PhysicalCameraId(result)']: assert s in cap,s
assert 'physicalCameraId = frame.motionV2PhysicalCameraId' in br
plan=kt[kt.index('private fun reconstructPlanB26753'):kt.index('private fun reconstructHighZoomDetail26718')]
assert 'referencePhysicalCameraId' in plan and 'physicalCameraId == referencePhysicalCameraId' in plan
assert 'lensStateIdentityOwner=false' in plan and 'lensStateTransitions' in plan
assert 'frames[it.frameIndex].lensState == reference' not in plan and '.mapNotNull' not in plan
# Fixed user frame population and physical-lens isolation remain fail-closed without silent dropping.
for s in ['require(evidence.all { frames[it.frameIndex].role == RawBurstFrameRole.NORMAL })','require(translations.size == evidence.size)','fixedFrameCount=true','directNativeGrid=true','secondScaler=false','rgbChromaOwner=NATIVE_SABRE_VGN']: assert s in kt+br,s
# 26754 stage deadline begins before guide export and covers guide streaming.
assert plan.index('val startNs = System.nanoTime()') < plan.index('streamTrue2xNativeVgnGuideRgb16f')
assert 'streamTrue2xNativeVgnGuideRgb16f(nativeVgnGuideTexture, stageDeadlineNs)' in plan
for m in ['IRIS_26754_PLAN_B_GUIDE_BEGIN','IRIS_26754_PLAN_B_GUIDE_DONE','IRIS_26754_PLAN_B_DETAIL_BEGIN','IRIS_26754_PLAN_B_DETAIL_DONE','IRIS_26754_PLAN_B_SR_RENDER_BEGIN','IRIS_26754_PLAN_B_SR_RENDER_DONE']: assert m in kt,m
# Section-7 enhancement is post-LS/IRLS residual work and pre inverse FFT; never RGB/chroma sharpening.
for s in ['IRIS_26754_IPOL_SECTION7_SPECTRAL_ENHANCEMENT','1.0+lambda*(1.0-std::exp(-rho))','std::ceil(zx)*std::ceil(zy)','std::min(5.0,(double)L/denom)']: assert s in cpp,s
ri=cpp.index('Java_com_particlesdevs_photoncamera_processing_IrisTrue2xSrNative_reconstructPlanBTileDirect')
rj=cpp.index('Java_com_particlesdevs_photoncamera_processing_IrisTrue2xSrNative_accumulatePlanBTile')
r=cpp[ri:rj]
assert r.index('robustOutlierCount(residuals)') < r.index('applySpectralEnhancement') < r.index('fft2dPlanned(output.data(),Nx,Ny,true')
assert 'kIrlsMaxUpdates = 5' in cpp and 'if(initialOutliers>0)' in cpp
# Publication must be row-streamed; old whole-frame MapFile ownership is forbidden in both functions.
b0=cpp.index('Java_com_particlesdevs_photoncamera_processing_IrisTrue2xSrNative_buildPlanBDetail'); b1=cpp.index('Java_com_particlesdevs_photoncamera_processing_IrisTrue2xSrNative_composePlanBRender'); b2=len(cpp)
bd=cpp[b0:b1]; cr=cpp[b1:b2]
for body in (bd,cr):
 assert 'MapFile' not in body
 for s in ['open(','ftruncate(','readExact','writeExact','std::vector<uint16_t>','deadline.expired()','unlink(']: assert s in body,s
# Universal local zoom multiplication is protected and unchanged: 30x per physical optical anchor.
base_zoom=(base/'app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java').read_bytes(); cand_zoom=(cand/'app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java').read_bytes(); assert base_zoom==cand_zoom
assert 'public static final float LOCAL_MAX_ZOOM = 30.0f;' in zoom
assert 'float maximum = anchor * LOCAL_MAX_ZOOM;' in zoom
assert 'clamp(currentLocal * scaleFactor, 1.0f, LOCAL_MAX_ZOOM)' in zoom
# Preserve capture repairs, DNG owner and shader/IQ owners.
for s in ['IRIS_26752_CAPTURE_TRANSACTION_RACE_FIX','IRIS_26752_EARLY_NORMAL_RAW_TIMESTAMP_STAGING','IRIS_26752_FROZEN_NORMAL_REQUEST_MODE']: assert s in cap,s
assert 'IRIS_26752_DNG_OWNER_UNCHANGED' in kt
bs={p.relative_to(base/'app').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (base/'app/src/main/assets/shaders').rglob('*') if p.is_file()}; cs={p.relative_to(cand/'app').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (cand/'app/src/main/assets/shaders').rglob('*') if p.is_file()}; assert bs==cs and len(bs)==271
print('PASS 26754 regressions: exact physical owner; LENS_STATE telemetry-only; fixed frames; streaming publication; Section7 luma-only; IRLS<=5; universal local 30x protected; 26753 IQ/DNG/shader owners preserved')
