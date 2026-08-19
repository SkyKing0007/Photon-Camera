#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, re

def fail(msg: str): raise SystemExit('ERROR: '+msg)
def sha(p: Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def files(root: Path):
    out={}
    for p in (root/'app/src/main').rglob('*'):
        if p.is_file(): out[p.relative_to(root).as_posix()]=sha(p)
    return out

def need(s: str, token: str, where: str):
    if token not in s: fail(f'{where}: missing {token}')
def forbid(s: str, token: str, where: str):
    if token in s: fail(f'{where}: forbidden stale token {token}')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--base-root',type=Path,required=True)
    a=ap.parse_args();root=a.root.resolve();base=a.base_root.resolve()
    x,y=files(base),files(root)
    changed={k for k in set(x)|set(y) if x.get(k)!=y.get(k)}
    expected={
      'app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java',
      'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
      'app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl',
      'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl',
      'app/src/main/assets/shaders/motionv2/mfsr_bridge_flow_compose_26508.glsl',
      'app/src/main/assets/shaders/motionv2/mfsr_short_region_seed_26508.glsl',
      'app/src/main/assets/shaders/motionv2/mfsr_short_region_propagate_26508.glsl',
      'app/src/main/assets/shaders/motionv2/mfsr_short_region_finalize_26508.glsl',
    }
    if changed!=expected: fail('changed-file allowlist mismatch\nactual='+repr(sorted(changed))+'\nexpected='+repr(sorted(expected)))

    mb=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java').read_text()
    cc=(root/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
    host=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java').read_text()
    short=(root/'app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl').read_text()
    weight=(root/'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl').read_text()
    compose=(root/'app/src/main/assets/shaders/motionv2/mfsr_bridge_flow_compose_26508.glsl').read_text()
    seed=(root/'app/src/main/assets/shaders/motionv2/mfsr_short_region_seed_26508.glsl').read_text()
    prop=(root/'app/src/main/assets/shaders/motionv2/mfsr_short_region_propagate_26508.glsl').read_text()
    fin=(root/'app/src/main/assets/shaders/motionv2/mfsr_short_region_finalize_26508.glsl').read_text()

    # Preserve tested 26507 lineage outside intentionally replaced Short/Long authorities.
    for token in ('IRIS_26507_MGC_RAW_HALF_GUIDE_PARITY','IRIS_26507_MGC_GEOMETRY'):
        need(host,token,'host 26507 preservation')
    need(cc,'IRIS_26507_FROZEN_AUX_BATCH_BOUNDARY','CaptureController 26507 preservation')
    need(mb,'IRIS_26507_IMMUTABLE_AUX_FREEZE','MotionBatch 26507 preservation')
    for rel,token in [
      ('app/src/main/assets/shaders/motionv2/mfsr_bjzhou_guide.glsl','IRIS_26507_MGC_RAW_HALF_GUIDE_PARITY'),
      ('app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl','IRIS_26507_DYNAMIC_MGC_FLOW_THRESHOLD'),
      ('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl','IRIS_26507_COVARIANCE_QUAD_CENTER_UV'),
      ('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java','IRIS_26507_FULL_HDR_DISPLAY_CAPACITY_PARITY'),
      ('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java','IRIS_26507_TRUE_JPEG444_JPEGR'),
    ]:
        need((root/rel).read_text(),token,rel)

    # Architecture 1: one Long/Normal final owner, no post-hoc shadow semantic fuse.
    need(host,'IRIS_26508_SHARED_NORMAL_LONG_MGC_FUSION_OWNER','Long convergence')
    need(host,'samePersistentRgbAccumulator=true oneFinalNormalization=true','Long convergence')
    need(host,'postHocShadowSemanticFuse=false helperBayerMutation=false','Long convergence')
    forbid(host,'useAssetProgram("motionv2/shadow_aux_bayer_fuse"','Long convergence')
    forbid(host,'maxShadowBlend','Long convergence')
    forbid(host,'shadowExposureRatio','Long convergence')
    if host.count('IRIS_26501_PROPER_SPATIAL_RGB_FINAL_NORMALIZATION')!=1:
        fail('final RGB normalization count changed')

    # Architecture 2: bridge geometry-only, immutable capture owner, no old direct reference fallback.
    for token in ('IRIS_26508_NEAREST_NORMAL_GEOMETRY_BRIDGE_OWNER','GeometryBridgeSlot'):
        need(mb,token,'MotionBatch bridge')
    for token in ('IRIS_26508_CAPTURE_SIDE_GEOMETRY_BRIDGE','IRIS_26508_FROZEN_GEOMETRY_BRIDGE','iris26508GenerationId'):
        need(cc,token,'Capture bridge')
    for token in ('IRIS_26508_NEAREST_NORMAL_BRIDGE_SELECTION','IRIS_26508_SHORT_BRIDGE_MGC_REGION_OWNER','pixelContributor=false','unrelatedFallback=false'):
        need(host,token,'host bridge')
    need(short,'IRIS_26508_SHORT_TO_NEAREST_NORMAL_BRIDGE_AUTHORITY','Short bridge shader')
    need(short,'IRIS_26508_BRIDGE_GEOMETRY_ONLY_NEVER_CONTRIBUTES_RGB','Short bridge shader')
    need(compose,'IRIS_26508_WRONSKI_BRIDGE_FLOW_COMPOSITION','bridge compose shader')
    for stale in ('IRIS_26497_SHORT_CORRESPONDENCE_REFINEMENT','IRIS_26503_BOUNDARY_ANCHORED_SHORT_OBSERVABILITY','refineObservableCorrespondence','evaluateCorrespondence','referenceCfa'):
        forbid(short,stale,'retired Short direct-reference authority')
    if 'iris26508BridgeRaw,iris26501ChromaGuideScratch' in host or re.search(r'iris26501ContributeRgbFrame\([^;]{0,1200}iris26508BridgeRaw',host,re.S):
        fail('bridge RAW reached RGB contributor')
    if re.search(r'iris26501ContributeRgbFrame\([^;]{0,1200}iris26508BridgeCfa',host,re.S):
        fail('bridge CFA reached RGB contributor')
    need(host,'noDirectReferenceFallback=true','Short no-fallback proof')

    # Architecture 3: GPU region propagation replaces local one-hop heuristic.
    forbid(weight,'IRIS_26507_GPU_LOCAL_8_CONNECTED_SHORT_TOPOLOGY','Short final weight')
    need(weight,'IRIS_26508_REGION_FINAL_SHORT_PHASE_WEIGHT','Short final weight')
    need(seed,'IRIS_26508_GPU_REGION_BOUNDARY_SEED','region seed')
    need(prop,'IRIS_26508_GPU_8_CONNECTED_REGION_PROPAGATION','region propagation')
    need(prop,'shared uint iris26508Active[64]','region propagation')
    need(host,'for(int iris26508RegionPass=0;iris26508RegionPass<4;++iris26508RegionPass)','GPU multi-pass topology')
    need(fin,'IRIS_26508_REGION_TO_FINAL_PROVENANCE_AUTHORITY','region finalizer')
    span=host.split('IRIS_26508_SHORT_BRIDGE_MGC_REGION_OWNER',1)[0]
    region_start=span.rfind('mfsr_short_region_seed_26508')
    if region_start<0: fail('region seed dispatch missing')
    region_segment=span[region_start:]
    for cpu in ('.BufferLoad()','readBufferIntegers','textureBuffer('):
        if cpu in region_segment: fail('CPU/full-frame readback inserted inside GPU topology: '+cpu)

    # Dedicated aux MGC scratch: never reuse the already-closed normal-loop scratch.
    need(host,'IRIS_26508_AUX_MGC_LIFETIME_OWNER','aux MGC lifetime')
    aux=host[host.find('IRIS_26508_SHARED_NORMAL_LONG_MGC_FUSION_OWNER'):host.find('IRIS_26501_PROPER_SPATIAL_RGB_FINAL_NORMALIZATION')]
    for closed in ('iris26487GuideScratch','iris26487UnblockerScratch','iris26487RejectFullA','iris26487RejectFullB','iris26487RejectFullC','iris26487FinalWeightScratch'):
        if closed in aux: fail('aux path reuses normal-loop scratch: '+closed)

    # Diagnostics required by handoff.
    for token in ('shortPhysicallyAvailablePct','shortPhysicallyClippedPct','noBridgePct','bridgeGeometryRejectedPct','mgcRejectedPct','regionTopologyRejectedPct','radiometryRejectedPct','recoveredPct','unrecoverablePct'):
        need(host,token,'26508 diagnostics')

    # Protected output/capture domains are unchanged by exact allowlist.
    for protected in (
      'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java',
      'app/src/main/cpp/CMakeLists.txt',
      'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
      'app/src/main/cpp/motionv2_jpeg_r_encoder.cpp',
    ):
        if x.get(protected)!=y.get(protected): fail('protected domain changed: '+protected)
    if (root/'app/version.properties').read_text()!=(base/'app/version.properties').read_text():
        fail('version changed inside 26508 source transform')
    if 'ParseExif' in '\n'.join(changed) or 'getMPY' in '\n'.join(changed): fail('EXIF/MPY domain changed')

    print('PASS: exact 9-file 26508 architectural convergence delta')
    print('PASS: Long shares final MGC/RGB owner; old shadow semantic authority absent')
    print('PASS: Short uses nearest Normal bridge + composed Wronski geometry; old 26497/26503 direct proof absent')
    print('PASS: GPU 8-connected region propagation finalizes Short provenance without CPU readback')
    print('PASS: 26507 RAW/2 MGC, immutable aux, UHDR and JPEG444/JPEG_R retained')

if __name__=='__main__': main()
