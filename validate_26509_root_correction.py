#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, re


def fail(msg: str):
    raise SystemExit('ERROR: ' + msg)

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def files(root: Path):
    out = {}
    for p in (root / 'app/src/main').rglob('*'):
        if p.is_file():
            out[p.relative_to(root).as_posix()] = sha(p)
    return out

def need(text: str, token: str, where: str):
    if token not in text:
        fail(f'{where}: missing {token}')

def forbid(text: str, token: str, where: str):
    if token in text:
        fail(f'{where}: forbidden {token}')

def read(root: Path, rel: str) -> str:
    p = root / rel
    if not p.is_file():
        fail('missing ' + rel)
    return p.read_text()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=Path)
    ap.add_argument('--base-root', type=Path, required=True)
    a = ap.parse_args()
    root, base = a.root.resolve(), a.base_root.resolve()

    before, after = files(base), files(root)
    changed = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
    expected = {
        'app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java',
        'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
        'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java',
        'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
        'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
        'app/src/main/assets/shaders/motionv2/mfsr_flow_expand.glsl',
        'app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl',
        'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl',
        'app/src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl',
        'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl',
        'app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl',
        'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl',
        'app/src/main/assets/shaders/motionv2/mfsr_bridge_flow_compose_26509.glsl',
        'app/src/main/assets/shaders/motionv2/mfsr_short_region_seed_26509.glsl',
        'app/src/main/assets/shaders/motionv2/mfsr_short_region_propagate_26509.glsl',
        'app/src/main/assets/shaders/motionv2/mfsr_short_region_finalize_26509.glsl',
        'app/src/main/assets/shaders/motionv2/mfsr_support_diag_26509.glsl',
    }
    if changed != expected:
        fail('changed-file allowlist mismatch\nactual=' + repr(sorted(changed)) +
             '\nexpected=' + repr(sorted(expected)))

    mb = read(root, 'app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java')
    cc = read(root, 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
    align = read(root, 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java')
    host = read(root, 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java')
    hdrx = read(root, 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
    flow = read(root, 'app/src/main/assets/shaders/motionv2/mfsr_flow_expand.glsl')
    reject = read(root, 'app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl')
    contribute = read(root, 'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl')
    shadow = read(root, 'app/src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl')
    norm = read(root, 'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl')
    short = read(root, 'app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl')
    short_weight = read(root, 'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl')
    compose = read(root, 'app/src/main/assets/shaders/motionv2/mfsr_bridge_flow_compose_26509.glsl')
    seed = read(root, 'app/src/main/assets/shaders/motionv2/mfsr_short_region_seed_26509.glsl')
    prop = read(root, 'app/src/main/assets/shaders/motionv2/mfsr_short_region_propagate_26509.glsl')
    finalizer = read(root, 'app/src/main/assets/shaders/motionv2/mfsr_short_region_finalize_26509.glsl')
    support = read(root, 'app/src/main/assets/shaders/motionv2/mfsr_support_diag_26509.glsl')

    # Exact tested 26507 invariants retained unless deliberately corrected here.
    # Short's old direct-reference MGC block is intentionally replaced by the
    # corrected physical-Normal + bridge MGC path, so prove that lineage from
    # the immutable base and prove the new owner in the candidate.
    base_host = read(base, 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java')
    for token in ('IRIS_26507_MGC_RAW_HALF_GUIDE_PARITY',
                  'IRIS_26507_LONG_A_SHARED_MGC_PRECHROMA_GATE'):
        need(host, token, '26507 host lineage')
    need(base_host, 'IRIS_26507_SHORT_A_SHARED_MGC_PRECHROMA_GATE', '26507 base Short lineage')
    need(host, 'IRIS_26509_SHORT_PHYSICAL_REFERENCE_BRIDGE_MGC_REGION_OWNER', '26509 Short MGC owner')
    need(mb, 'IRIS_26507_IMMUTABLE_AUX_FREEZE', '26507 immutable aux')
    need(cc, 'IRIS_26507_FROZEN_AUX_BATCH_BOUNDARY', '26507 immutable batch boundary')
    need(read(root, 'app/src/main/assets/shaders/motionv2/mfsr_bjzhou_guide.glsl'),
         'IRIS_26507_MGC_RAW_HALF_GUIDE_PARITY', 'RAW/2 guide geometry')
    need(read(root, 'app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl'),
         'IRIS_26507_MGC_RAW_HALF_COVARIANCE_PARITY', 'RAW/2 covariance geometry')
    need(read(root, 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java'),
         'IRIS_26507_FULL_HDR_DISPLAY_CAPACITY_PARITY', 'UHDR preservation')
    need(read(root, 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java'),
         'IRIS_26507_TRUE_JPEG444_JPEGR', 'JPEG_R preservation')

    # Root correction 1: no hard blockwise flow switch; continuous uncertainty is authoritative.
    need(flow, 'IRIS_26509_CONTINUOUS_DENSE_FLOW_UNCERTAINTY_OWNER', 'dense flow')
    need(flow, 'vec2 outF=mix(', 'dense flow')
    need(flow, 'float uncertainty=clamp(disagreement/th,0.0,1.0)', 'dense flow')
    need(flow, 'max(abs(f00.x-outF.x),abs(f00.y-outF.y))', 'component-wise old-threshold semantics')
    forbid(flow, 'length(f00-outF)', 'no diagonal over-penalty')
    forbid(flow, 'if(!cancel)', 'dense flow')
    forbid(flow, 'outF=base', 'dense flow')
    forbid(flow, 'cancel?1.0', 'dense flow')
    need(align, 'IRIS_26509_NO_FAKE_ALIGNMENT_CONFIDENCE', 'alignment telemetry')
    need(align, 'Float.NaN,Float.NaN', 'alignment telemetry')
    forbid(align, 'new MotionV2Alignment.Result(keep,0.0f,0.0f,1.0f,0.0f)', 'alignment telemetry')

    # Root correction 2: one physical boundary rule and MGC consumes uncertainty.
    need(reject, 'IRIS_26509_PHYSICAL_BOUNDARY_ZERO_EVIDENCE', 'MGC boundary')
    need(reject, 'IRIS_26509_MGC_CONSUMES_CONTINUOUS_FLOW_UNCERTAINTY', 'MGC uncertainty')
    need(reject, 'IRIS_26509_SAMPLED_GEOMETRY_DIAGNOSTICS', 'sampled geometry diagnostics')
    need(reject, 'bool diagnosticSample=((p.x&15)==0)&&((p.y&15)==0);', 'sampled geometry diagnostics')
    need(reject, 'uniform float flowVariationThreshold', 'MGC dynamic threshold')
    need(reject, 'weight*=geometryConfidence', 'MGC uncertainty')
    need(reject, 'imageStore(outReverseWeight,p,vec4(1.0))', 'MGC OOB rejection')
    forbid(reject, 'mirrorUv(', 'MGC boundary')
    need(host, 'GeometryDiagBuf', 'geometry diagnostic binding')
    need(host, 'IRIS_26509_GEOMETRY_RESULT', 'geometry result')
    for token in ('uncertainPct=', 'outOfBoundsPct=', 'borderOob=', 'borderUncertain='):
        need(host, token, 'geometry result fields')

    # Root correction 3: opponent support cannot become channel-divergent at aux boundaries.
    need(contribute, 'IRIS_26509_PHASE_BALANCED_AUX_BOUNDARY_SUPPORT', 'Spatial RGB support')
    need(contribute, '(sourceRaw+vec2(1.0))/vec2(rawSize)', '26507 covariance UV preservation')
    need(contribute, 'if(referenceFrame==0&&(weights.y<=1.0e-8||weights.z<=1.0e-8))return;',
         'phase-balanced aux support')
    need(support, 'IRIS_26509_OPPONENT_SUPPORT_DIAGNOSTIC_OWNER', 'support diagnostic shader')
    need(support, 'IRIS_26509_SAMPLED_SUPPORT_DIAGNOSTICS', 'sampled support diagnostics')
    need(support, 'if((p.x&15)!=0||(p.y&15)!=0)return;', 'sampled support diagnostics')
    need(host, 'IRIS_26509_SUPPORT_RESULT', 'support diagnostic result')
    for token in ('rZero=', 'bZero=', 'borderZero=', 'interiorZero='):
        need(host, token, 'support diagnostic fields')

    # Short: keep useful 26508 bridge concept only through corrected 26509 geometry;
    # physical immutable reference owns clipping, never fused helper imageOutput.
    need(mb, 'IRIS_26509_NEAREST_NORMAL_GEOMETRY_BRIDGE_OWNER', 'Short bridge owner')
    need(cc, 'IRIS_26509_CAPTURE_SIDE_GEOMETRY_BRIDGE', 'Short bridge capture')
    need(cc, 'IRIS_26509_FROZEN_GEOMETRY_BRIDGE', 'Short bridge freeze')
    for token in ('IRIS_26509_NEAREST_NORMAL_BRIDGE_SELECTION',
                  'IRIS_26509_SHORT_PHYSICAL_REFERENCE_BRIDGE_MGC_REGION_OWNER'):
        need(host, token, 'Short host')
    need(short, 'IRIS_26509_PHYSICAL_NORMAL_CLIP_AUTHORITY', 'Short physical clip authority')
    need(short, 'IRIS_26509_BRIDGE_GEOMETRY_ONLY_NEVER_CONTRIBUTES_RGB', 'Short bridge geometry-only')
    need(compose, 'IRIS_26509_WRONSKI_BRIDGE_FLOW_COMPOSITION', 'Short composed flow')
    need(seed, 'IRIS_26509_GPU_REGION_BOUNDARY_SEED', 'Short region seed')
    need(prop, 'IRIS_26509_GPU_8_CONNECTED_REGION_PROPAGATION', 'Short region propagation')
    need(finalizer, 'IRIS_26509_REGION_TO_FINAL_PROVENANCE_AUTHORITY', 'Short region finalizer')
    need(short_weight, 'IRIS_26509_REGION_FINAL_SHORT_PHASE_WEIGHT', 'Short final weight')
    need(host, 'glProg.setTexture("normalCfa",referenceCfa)', 'Short host physical reference bind')
    forbid(host, 'glProg.setTexture("normalCfa",imageOutput)', 'Short host fused-helper clip authority')
    if re.search(r'iris26501ContributeRgbFrame\([^;]{0,1400}iris26509Bridge(?:Raw|Cfa)', host, re.S):
        fail('geometry bridge reached RGB contributor')
    for stale in ('IRIS_26497_SHORT_CORRESPONDENCE_REFINEMENT', 'IRIS_26503_BOUNDARY_ANCHORED_SHORT_OBSERVABILITY'):
        forbid(short, stale, 'retired old Short direct-reference proof')
    need(host, 'IRIS_26509_SHORT_ARCHITECTURAL_RESULT', 'Short diagnostics')

    # Resource/lifetime and bridge-copy safety gates.
    need(cc, 'IRIS_26509_BRIDGE_COPY_ONLY_IF_TIMESTAMP_CLOSER', 'Short bridge copy throttling')
    need(cc, 'if (shortTimestamp <= 0L || ts == shortTimestamp) return false;', 'Short bridge timestamp ownership')
    need(cc, 'Math.abs(ts - shortTimestamp) >= Math.abs(existingBridgeTimestamp - shortTimestamp)', 'Short bridge nearest-only copy')
    if host.count('setBufferCompute("GeometryDiagBuf",iris26509GeometryDiag)') != 3:
        fail('all three MGC executions must bind GeometryDiagBuf exactly once')
    if host.count('new GLBuffer(16,new GLFormat(GLFormat.DataType.UNSIGNED_32))') < 2:
        fail('geometry/support diagnostic buffers must each have at least 16 uint entries')
    need(host, 'for(int iris26509RegionPass=0;iris26509RegionPass<4;++iris26509RegionPass)', 'Short topology host pass count')
    need(prop, 'shared uint iris26509Active[64]', 'Short topology 8x8 shared tile')
    need(prop, 'for(int iter=0;iter<8;++iter)', 'Short topology in-tile propagation')
    need(hdrx, 'IRIS_26509_ASYNC_BITMAP_LIFETIME_OWNER', 'async bitmap lifetime')
    need(hdrx, 'if(iris26509Bitmap!=null&&!iris26509Bitmap.isRecycled())', 'async bitmap failure cleanup')
    need(hdrx, 'processingEventsListener.notifyImageSavedStatus(false,iris26509ImagePath)', 'async save failure notification')
    need(hdrx, 'pipeline.close();Allocator.getMemoryCount();', 'capture release pipeline close')
    need(hdrx, 'callback.onFinished();return;', 'capture release before deferred output completes')

    # Long: explicitly reject the 26508 regression. Keep 26507 shadow-only owner.
    need(shadow, 'IRIS_26509_LONG_RETAINS_ISOLATED_SHADOW_ONLY_OWNER', 'Long owner')
    need(shadow, 'IRIS_26506_LONG_A_QUAD_COHERENT_CHROMA_AUTHORITY', 'preserved 26506 Long quad-coherent chroma authority')
    need(host, 'useAssetProgram("motionv2/shadow_aux_bayer_fuse"', 'Long isolated shadow fuse active')
    need(host, 'IRIS_26509_LONG_BUCKET_RESULT', 'Long bucket diagnostics')
    need(host, 'shadowSemanticGateRequired=true unrestrictedLongCommonAdmission=false', 'Long bucket diagnostics')
    forbid(host, 'IRIS_26508_SHARED_NORMAL_LONG_MGC_FUSION_OWNER', 'rejected 26508 Long architecture')
    forbid(host, 'IRIS_26509_SHARED_NORMAL_LONG_MGC_FUSION_OWNER', 'Long common accumulator')
    long_call = re.search(r'iris26501ContributeRgbFrame\(\s*glProg,iris26501RgbFramebuffer,raw,rawHalf,\s*irisV13ShadowRaw(?P<body>[^;]{0,1800});', host, re.S)
    if not long_call:
        fail('preserved 26507 shadow-gated Long semantic contribution call missing')
    need(long_call.group('body'), 'iris26501ShadowWeight', 'Long shadow semantic gate')
    need(long_call.group('body'), 'iris26509AuxFinalWeight', 'Long MGC gate')
    need(shadow, 'shadowDiag[20]', 'Long shadow bucket')
    need(shadow, 'shadowDiag[21]', 'Long midtone bucket')
    need(shadow, 'shadowDiag[22]', 'Long highlight bucket')

    # Dedicated aux MGC resources survive beyond normal-loop scratch lifetime.
    need(host, 'IRIS_26509_POST_NORMAL_AUX_MGC_LIFETIME_OWNER', 'aux MGC lifetime')
    aux_begin = host.find('IRIS_26509_POST_NORMAL_AUX_MGC_LIFETIME_OWNER')
    aux_end = host.find('IRIS_26501_PROPER_SPATIAL_RGB_FINAL_NORMALIZATION', aux_begin)
    if aux_begin < 0 or aux_end < 0:
        fail('aux MGC lifetime span missing')
    aux = host[aux_begin:aux_end]
    for old_name in ('iris26487GuideScratch', 'iris26487UnblockerScratch', 'iris26487RejectFullA',
                     'iris26487RejectFullB', 'iris26487RejectFullC', 'iris26487FinalWeightScratch'):
        if old_name in aux:
            fail('post-normal aux path reuses closed normal-loop scratch: ' + old_name)

    # Exposure authority: HAL AE remains owner. The controller is a hysteretic
    # RAW-signal integrator; request SENSOR_* keys are explicitly not treated as
    # AE targets, preventing the earlier requested-vs-actual false authority.
    need(cc, 'IRIS_26509_NORMAL_RAW_SIGNAL_EXPOSURE_AUTHORITY', 'Normal exposure authority')
    need(cc, 'IRIS_26509_STABLE_RAW_SIGNAL_NORMAL_EXPOSURE_INTEGRATOR', 'Normal exposure integrator state')
    need(cc, 'IRIS_26509_STABLE_RAW_EXPOSURE_AUTHORITY_ACTIVE', 'Normal exposure authority activation')
    need(cc, 'requestSensorKeysAreNotAeTargets=true', 'Normal exposure diagnostics')
    need(cc, 'MOTION_26509_AE_MAX_EXTRA_EV = 2.25f', 'Normal exposure upper bound')
    need(cc, 'MOTION_26509_AE_SLEW_EV = 0.50f', 'Normal exposure slew bound')
    need(cc, 'MOTION_26509_AE_CONFIRM_FRAMES = 8', 'Normal exposure hysteresis')
    need(cc, 'mMotion26509NormalStarvationEma=0.88f*mMotion26509NormalStarvationEma', 'Normal exposure low-pass')
    need(cc, 'CaptureRequest.CONTROL_AE_EXPOSURE_COMPENSATION', 'HAL AE compensation path')
    forbid(cc, 'targetEnergy/actualEnergy', 'non-authoritative request/actual energy target')

    # Highlight rendition: no hard white box for every censored neighborhood.
    need(norm, 'IRIS_26509_CONTINUOUS_UNRECOVERABLE_HIGHLIGHT_EXHAUSTION', 'highlight exhaustion')
    need(norm, 'smoothstep(0.94,0.995,endpointSignal)', 'highlight exhaustion')
    need(norm, 'calculationRgb=mix(calculationRgb,vec3(max(stableNeutral,0.0))', 'highlight exhaustion')
    forbid(norm, 'if(colorIncomplete||gWeight<=SUPPORT_EPS)', 'old hard white-box branch')

    # Output ownership: image math stays same, synchronous save no longer holds capture lock.
    need(hdrx, 'IRIS_26509_ASYNC_JPEGR_OUTPUT_OWNER', 'async JPEG_R')
    need(hdrx, 'MOTION_26480_OUTPUT_EXECUTOR.execute', 'async JPEG_R')
    need(hdrx, 'IRIS_26509_CAPTURE_RELEASE_BEFORE_JPEGR_SAVE', 'async JPEG_R')
    need(hdrx, 'ImageSaver.Util.saveBitmapAsJPGMotionV2', 'same Motion JPEG_R encoder')

    # Final global invariants / forbidden regressions.
    if host.count('IRIS_26501_PROPER_SPATIAL_RGB_FINAL_NORMALIZATION') != 1:
        fail('final Spatial RGB normalization count changed')
    for forbidden in ('PyramidAlignment(', 'fallbackMerge(', 'IRIS_26508_SHARED_NORMAL_LONG_MGC_FUSION_OWNER'):
        if forbidden in host:
            fail('forbidden architecture token in host: ' + forbidden)
    if (root / 'app/version.properties').read_text() != (base / 'app/version.properties').read_text():
        fail('version changed inside 26509 source transform')
    for protected in (
        'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
        'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
        'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
        'app/src/main/cpp/CMakeLists.txt',
        'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
        'app/src/main/cpp/motionv2_jpeg_r_encoder.cpp',
    ):
        if before.get(protected) != after.get(protected):
            fail('protected 26507 output/color domain changed: ' + protected)

    print('PASS: exact 17-file 26509 root-correction delta')
    print('PASS: continuous Wronski flow uncertainty feeds MGC; true OOB auxiliary evidence is zero')
    print('PASS: phase-balanced Spatial RGB support removes boundary chroma-denominator divergence')
    print('PASS: Short uses immutable physical Normal clipping + corrected nearest-Normal geometry')
    print('PASS: Long remains isolated shadow-only; rejected 26508 common accumulator is absent')
    print('PASS: RAW-signal Normal exposure authority, continuous highlight exhaustion, async JPEG_R output are isolated')
    print('PASS: 26507 RAW/2 MGC, Camera2 color, UHDR 0.80/1.00 and JPEG_R 4:4:4 remain protected')

if __name__ == '__main__':
    main()
