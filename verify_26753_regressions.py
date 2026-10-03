#!/usr/bin/env python3
from pathlib import Path
import sys,re,hashlib
if len(sys.argv)!=3: raise SystemExit('usage: verify_26753_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:])
cpp=(cand/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
java=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisTrue2xSrNative.java').read_text()
kt=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
br=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
# Old 26752 computational hazards must be gone from the active candidate.
for stale in ['kIrlsMaxIterations','reconstructPlanBIrls','PLAN_B_MAX_EVIDENCE_26752','irlsMax=50','true2xFastPhaseSlots']:
    assert stale not in cpp+java+kt,stale
# Pure IPOL direct Moore-Penrose owner; direct WLS happens before outlier detection.
assert 'IRIS_26753_IPOL_PLAN_B_MOBILE_DIRECT_NATIVE' in cpp
assert 'constexpr int kIrlsMaxUpdates = 5;' in cpp
assert 'kJacobiMaxSweeps = 64' in cpp
assert cpp.index('solveWeightedDual(output.data()') < cpp.index('robustOutlierCount(residuals)')
assert 'if(initialOutliers>0)' in cpp
assert 'update<iris26752planb::kIrlsMaxUpdates' in cpp
assert 'kIrlsRelativeStop' in cpp and 'break;' in cpp
# Clean native failure and bounded work across tile solve, accumulation and final publication.
planb_start=cpp.index('IRIS_26753_IPOL_PLAN_B_MOBILE_DIRECT_NATIVE')
planb=cpp[planb_start:]
assert 'exit(' not in planb and 'abort(' not in planb
assert planb.count('catch(const std::bad_alloc&)') >= 5 and planb.count('catch(...)') >= 5
for owner in ['reconstructPlanBTileDirect','accumulatePlanBTile','finalizePlanBAccumulation','buildPlanBDetail','composePlanBRender']:
    assert owner in java and owner in cpp
assert java.count('long maxDurationMs') >= 5
assert 'while(workers>1&&estimated>' in cpp and 'estimateTileBytes' in cpp
# Kotlin keeps every NORMAL frame, strict same-lens ownership, direct native grid, and hard stage/tile bounds.
for s in [
    'require(evidence.all { frames[it.frameIndex].role == RawBurstFrameRole.NORMAL })',
    'require(evidence.all { frames[it.frameIndex].lensState == referenceLens })',
    'val translations = evidence.map { ev ->',
    'requireNotNull(planBGlobalTranslation26753',
    'require(translations.size == evidence.size)',
    'val outputWidth = Math.multiplyExact(width, publicationScale.toInt())',
    'val outputHeight = Math.multiplyExact(height, publicationScale.toInt())',
    'PLAN_B_IRLS_MAX_UPDATES_26753 = 5',
    'PLAN_B_STAGE_MAX_MS_26753 = 20_000L',
    'PLAN_B_TILE_MAX_MS_26753 = 4_000L',
    'PLAN_B_MAX_TILE_COUNT_26753 = 1024',
    'fixedFrameCount=true', 'directNativeGrid=true', 'secondScaler=false',
    'solve=DUAL_FRAME_SPACE_DIRECT_WLS',
    'rgbChromaOwner=NATIVE_SABRE_VGN',
]: assert s in kt,s
assert '.mapNotNull' not in kt[kt.index('private fun reconstructPlanB26753'):kt.index('private fun reconstructPlanB26753')+18000]
assert 'remainingForAccumulate' in kt and 'remainingPlanBMs26753("overlap finalize")' in kt
assert 'remainingPlanBMs26753("detail publication")' in kt and 'remainingPlanBMs26753("2x render composition")' in kt
# Super Res and high zoom use same Plan-B engine; DNG owner marker retained.
assert kt.count('reconstructPlanB26753(') >= 3
assert 'IRIS_26752_DNG_OWNER_UNCHANGED' in kt
# Bridge enforces physical-lens native-size output and full NORMAL count.
for s in ['IRIS_26753_LENS_RELATIVE_PLAN_B_MOBILE_DIRECT_NATIVE','expectedPlanBFrames26753 = frames.count { it.role == RawBurstFrameRole.NORMAL }','stacked.highZoomDetailWidth == size.x && stacked.highZoomDetailHeight == size.y','stacked.highZoomDetailFrames == expectedPlanBFrames26753','IPOL_PLAN_B_DIRECT_WLS_OPTIONAL_IRLS','secondScaler=false']:
    assert s in br,s
# Capture owner and shaders are outside the allowlist and byte-identical, preserving 26752 capture/flicker fixes and IQ owners.
for rel in ['app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java']:
    assert hashlib.sha256((base/rel).read_bytes()).digest()==hashlib.sha256((cand/rel).read_bytes()).digest()
bs={p.relative_to(base/'app').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (base/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
cs={p.relative_to(cand/'app').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (cand/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
assert bs==cs and len(bs)==271
print('PASS 26753 permanent regressions: fixed frames/native grid/no scaler/IRLS<=5/lens isolation/memory+time bounds/clean failure/26752 capture+IQ owners preserved')
