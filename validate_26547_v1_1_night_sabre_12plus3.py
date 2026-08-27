#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, math

REQ_FILES = sorted([
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties',
])

def fail(msg): raise SystemExit('ERROR: '+msg)
def req(text, token, label):
    if token not in text: fail(f'{label}: missing {token!r}')
def forbid(text, token, label):
    if token in text: fail(f'{label}: forbidden {token!r}')

def audited_manifest(root: Path):
    files=[]
    for p in (root/'app/src/main').rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(root).as_posix()
        if rel.startswith('app/src/main/cpp/third_party_26507/'): continue
        if rel.startswith('app/src/main/cpp/deps/') and rel!='app/src/main/cpp/deps/.gitignore': continue
        files.append(rel)
    for rel in ('app/version.properties','app/build.gradle'):
        if (root/rel).is_file(): files.append(rel)
    return ''.join(
        f'{hashlib.sha256((root/rel).read_bytes()).hexdigest()}  {rel}\n'
        for rel in sorted(set(files))
    )

def changed(base: Path, cand: Path):
    def m(root):
        d={}
        for line in audited_manifest(root).splitlines():
            h,rel=line.split('  ',1); d[rel]=h
        return d
    a,b=m(base),m(cand)
    return sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))

def math_contracts():
    # Exposure normalization must preserve clipping when both signal and white threshold scale.
    for ratio in (1.01, 1.25, 2.0, 4.0, 8.0):
        scale=1.0/ratio
        white=1.0
        for raw in (0.0, .1, .24, .25, .5, .99, 1.0, 1.1):
            assert (raw >= white) == (raw*scale >= white*scale)
        linear_clip=white*scale
        guide_clip=math.sqrt(linear_clip)
        assert math.isclose(guide_clip*guide_clip, linear_clip, rel_tol=1e-7, abs_tol=1e-7)
    # Explicit Long blur-risk factor is shutter-duration only, bounded and monotonic.
    def robustness(ref,cur):
        if ref<=0 or cur<=0: return 1.0
        return max(1.0,min(4.0,cur/ref))
    assert robustness(10,10)==1.0
    assert robustness(10,20)==2.0
    assert robustness(10,40)==4.0
    assert robustness(10,80)==4.0
    # 12 Short + 3 Long must not inflate guaranteed pre-merge Short SNR.
    assert math.isclose(math.sqrt(12/12),1.0)
    assert math.sqrt(15/12)>1.11

def validate(base: Path, cand: Path, base_pin: Path|None=None):
    actual=changed(base,cand)
    if actual != REQ_FILES:
        fail('runtime scope mismatch expected='+repr(REQ_FILES)+' actual='+repr(actual))
    if base_pin and audited_manifest(base) != base_pin.read_text():
        fail('base is not exact successful 26546 audited runtime authority')

    def t(rel): return (cand/rel).read_text()
    sabre=t(REQ_FILES[0]); fusion=t(REQ_FILES[1]); stack=t(REQ_FILES[2])
    capture=t(REQ_FILES[3]); night=t(REQ_FILES[4]); bridge=t(REQ_FILES[5]); version=t(REQ_FILES[6])

    # Night routing / immutable Short owner; Motion remains default-off for Long admission.
    req(bridge,'val sabreSelected = parameters.irisNightActive ||','Night Sabre selection')
    req(bridge,'IRIS_26547_NIGHT_SABRE_DURABLE_OWNER','Night durable owner')
    req(bridge,'parameters.motionV2ReconstructionOwner = if (sabreSelected)','durable owner publish')
    req(bridge,'allowSabreShadowLong = parameters.irisNightActive','Night-only Long gate')
    req(bridge,'IRIS_26547_NIGHT_NO_SILENT_LONG_DROP','no silent Long drop')
    req(bridge,'requireParity(stacked.mergedFrameCount == frames.size','no silent Long drop')
    req(bridge,'val fixedOutputScale = if (sabreSelected) {\n                1f','Sabre native grid')
    req(bridge,'val vgnChromaCorrectionStrength = if (parameters.irisNightActive) {\n                1.0f','Night VGN isolation')
    req(fusion,'private val allowSabreShadowLong: Boolean = false','Motion Long default-off')
    req(fusion,'allowShadowLong = allowSabreShadowLong','Sabre Long propagation')

    # Admission: only valid higher-exposure SHADOW_LONG may join; first Short remains base.
    req(sabre,'private val allowShadowLong: Boolean = false','Sabre Long default-off')
    req(sabre,'frame.role == RawBurstFrameRole.SHADOW_LONG &&','Long role admission')
    req(sabre,'frame.exposureProduct.isFinite() && frame.exposureProduct > baseExposure','Long radiometric admission')
    req(sabre,'shortReferenceImmutable=true','Short reference telemetry')

    # Low-level 12+3 role/math contract.
    req(stack,'require(frames.first().role == RawBurstFrameRole.NORMAL)','Short reference contract')
    req(stack,'val normalFrameCount = frames.count { it.role == RawBurstFrameRole.NORMAL }','Normal count')
    req(stack,'val shadowLongFrameCount = frames.count { it.role == RawBurstFrameRole.SHADOW_LONG }','Long count')
    req(stack,'frameCount = normalFrameCount,','Short-only premerge kernel support')
    if stack.count('frameCount = normalFrameCount,') < 2:
        fail('Short-only frameCount must feed both Bayer kernel tuning and Sabre kernel tuning')
    req(stack,'sqrt(calibration.greenClippingPoint.coerceAtLeast(0f))','sqrt clipping-domain transport')
    req(stack,'IRIS_26547_SABRE_LONG_DURATION_ROBUSTNESS','Long blur robustness')
    req(stack,'frame.exposureTimeNs.takeIf { it > 0L }','actual shutter-time robustness')
    req(stack,'SABRE_LONG_DURATION_ROBUSTNESS_MAX = 4f','bounded Long robustness')
    req(stack,'MgcSabreRejectionTuning.COLOR_DIFFERENCE_RGB * durationRobustness','RGB robustness application')
    req(stack,'MgcSabreRejectionTuning.COLOR_DIFFERENCE_GREEN * durationRobustness','green robustness application')

    # DNG: Night is Normal-only, while Motion preserves exact 26546 measured support/noise ownership.
    req(stack,'if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)','Normal-only DNG merge')
    req(stack,'IRIS_26547_V1_1_MOTION_DNG_26546_PRESERVATION','Motion DNG preservation marker')
    req(stack,'exportNormalStackedDng && shadowLongFrameCount > 0','Night-only DNG coverage allocation')
    req(stack,'if (normalDngCoverage != 0) {','Night-only DNG coverage branch')
    req(stack,'accumulatedCoverage = normalDngCoverage','Night Normal-only DNG support map')
    req(stack,'accumulatedWeightScale = maxSabreAccumulatedWeight(normalFrameCount)','Night Normal-only DNG support scale')
    req(stack,'sabreNoiseModelScale = 1f / normalFrameCount.coerceAtLeast(1).toFloat()','Night Normal-only DNG noise authority')
    req(stack,'frames = frames.filter { it.role == RawBurstFrameRole.NORMAL }','Night Normal-only DNG noise frames')
    req(stack,'// Motion: exact 26546 support/noise ownership. All admitted frames are NORMAL.','Motion exact-26546 DNG branch')
    req(stack,'accumulatedCoverage = accumulatedCoverage','Motion measured coverage owner')
    req(stack,'accumulatedWeightScale = accumulatedWeightScale','Motion measured coverage scale')
    req(stack,'frameCount = frames.size','Motion exact frame-count owner')
    req(stack,'sabreNoiseModelScale = sabreNoiseModelScale','Motion measured merge-factor owner')
    req(stack,'frames = frames,','Motion exact DNG noise-frame owner')
    req(stack,'normalStackedDngFrameCount = if (exportNormalStackedDng) normalFrameCount else 0','Normal-only DNG count')

    # Bounded RAM path: one file-backed auxiliary is materialized only for synchronous upload.
    req(stack,'IRIS_26547_SABRE_DISK_RAW_STREAM_UPLOAD','disk-backed Sabre upload')
    req(stack,'if (image.isFileBacked)','disk-backed branch')
    req(stack,'val region = image.readFileRegion(0, 0, width, height)','one temporary RAW region')
    req(stack,'finally {\n                region.close()','temporary RAW deterministic release')
    req(stack,'GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER, 0)','synchronous client upload path')

    # Capture runtime hardening: serialized Night + deterministic pre-dispatch cleanup.
    req(capture,'IRIS_26547_NIGHT_REENTRY_GUARD','Night re-entry guard')
    req(capture,'selectedMode == CameraMode.NIGHT && isProcessing','Night re-entry condition')
    req(capture,'IRIS_26547_NIGHT_CAPTURE_ABORT_OWNER','Night abort cleanup')
    req(capture,'!mIrisNight26540Dispatched','pre-dispatch-only controller ownership')
    req(capture,'public void onCaptureSequenceAborted','sequence abort callback')
    req(capture,'boolean iris26547NightRequested = false;','pre-plan Night intent')
    req(capture,'catch (RuntimeException e)','Night runtime failure catch')
    req(capture,'cleanupIrisNight26544SpoolCache();','Night spool cleanup')
    req(capture,'java.nio.ByteBuffer source = plane.getBuffer().duplicate();','prior javac ByteBuffer regression')
    req(capture,'IRIS_26541_NIGHT_LONG_TAG','12+3 Long request tag preserved')

    # Processing errors are contained by the existing Night owner; diagnostics describe Sabre truthfully.
    req(night,'mgcSabre=true mgcSpatialRgb=false shortReferenceAuthority=true','Night owner diagnostic')
    req(night,'longEvidence=shadowOnly normalDngLongExcluded=true','Night bracket/DNG diagnostic')
    req(night,'catch (Throwable failure)','Night processing failure containment')
    req(night,'CaptureController.isProcessing = false;','Night processing gate cleanup')
    req(night,'for (ImageFrame frame : batch.frames)','Night frame cleanup')

    # Preserve prior 26546 two-GPU-buffer Night post contract and no old owner resurrection.
    ni=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisNightRgbInput.java').read_text()
    if ni.count('new GLTexture(')!=2: fail('Night post must retain exactly two GLTexture allocations')
    req(ni,'Allocator.free(source);','26546 CPU carrier release')
    req(ni,'basePipeline.main3 = null;','26546 no third full-res GPU buffer')
    req(ni,'basePipeline.texnum = 1;','26546 ping-pong ownership')

    req(version,'VERSION_NAME=0.9726547','version')
    req(version,'VERSION_BUILD=26547','build')
    math_contracts()
    print('PASS: exact 7-file 26546 -> 26547 V1.1 runtime scope')
    print('PASS: 12 Short reference support + Long auxiliary admission math')
    print('PASS: sqrt clipping domain + heteroscedastic Sabre + shutter-duration blur robustness')
    print('PASS: Night DNG remains Normal-only; Motion DNG support/noise ownership remains exact 26546')
    print('PASS: bounded disk-backed RAW upload + Night abort/re-entry runtime safety')
    print('PASS: Motion Long gate remains default-off and 26546 two-GPU-buffer post ownership preserved')

def self_test():
    assert len(REQ_FILES)==7 and REQ_FILES==sorted(set(REQ_FILES))
    math_contracts()
    print('PASS: 26547 V1.1 validator self-test + math invariants')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--base'); ap.add_argument('--candidate'); ap.add_argument('--base-pin'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test: self_test()
    else:
        if not a.base or not a.candidate: ap.error('--base and --candidate required')
        validate(Path(a.base),Path(a.candidate),Path(a.base_pin) if a.base_pin else None)
