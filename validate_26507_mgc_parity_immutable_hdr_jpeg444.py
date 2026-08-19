#!/usr/bin/env python3
from pathlib import Path
import argparse

def fail(m): raise SystemExit('ERROR: '+m)
def must(text,needle,label):
    if needle not in text: fail(label+' missing: '+needle)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--base-root',type=Path,default=None);a=ap.parse_args();r=a.root
    files={
      'host':'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
      'batch':'app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java',
      'capture':'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
      'guide':'app/src/main/assets/shaders/motionv2/mfsr_bjzhou_guide.glsl',
      'cov':'app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl',
      'reject':'app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl',
      'contrib':'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl',
      'short':'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl',
      'normalizer':'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl',
      'ultrahdr':'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
      'render':'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
      'shadow':'app/src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl',
      'save':'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
      'jpegjava':'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
      'cmake':'app/src/main/cpp/CMakeLists.txt',
      'jni':'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
      'jpegr':'app/src/main/cpp/motionv2_jpeg_r_encoder.cpp',
      'hdr':'app/src/main/cpp/motionv2_jpeg_r_encoder.h',
    }
    for k,v in files.items():
        if not (r/v).is_file(): fail('missing '+v)
    t={k:(r/v).read_text() for k,v in files.items()}

    # Exact MGC geometry contract.
    must(t['host'],'IRIS_26507_MGC_RAW_HALF_GUIDE_PARITY','host geometry')
    must(t['host'],'new Point(Math.max(1,rawHalf.x),Math.max(1,rawHalf.y))','RAW/2 guide')
    must(t['host'],'2016.0f / Math.max(1.0f, iris26487GuideSize.x) * 1.0e-4f','dynamic MGC threshold')
    must(t['guide'],'IRIS_26507_MGC_RAW_HALF_GUIDE_PARITY','guide geometry marker')
    if 'ivec2 base=center*2' in t['guide']: fail('old double-scaled guide coordinate survived')
    must(t['guide'],'mirrorGuideCoordinate','guide mirror')
    must(t['cov'],'IRIS_26507_MGC_RAW_HALF_COVARIANCE_PARITY','covariance geometry marker')
    if 'ivec2 base=center*2' in t['cov']: fail('old double-scaled covariance coordinate survived')
    must(t['reject'],'uniform float flowVariationThreshold;','dynamic rejection threshold')
    if 'FLOW_VARIATION_THRESHOLD=' in t['reject']: fail('fixed rejection threshold survived')
    for needle in ['25.0*minimumVariance','boost=6.0','0.35*diffSq.g','0.07*dot(diffSq','exp2(min(-distance,0.0))']:
        must(t['reject'],needle,'MGC rejection equation')
    must(t['contrib'],'IRIS_26507_COVARIANCE_QUAD_CENTER_UV','covariance center')
    must(t['contrib'],'sourceRaw+vec2(1.0)','quad-center covariance lookup')

    # Immutable capture schedule.
    must(t['batch'],'IRIS_26507_IMMUTABLE_AUX_FREEZE','batch freeze')
    must(t['batch'],'awaitExpectedAndSeal','slot deadline seal')
    must(t['capture'],'IRIS_26507_FROZEN_AUX_BATCH_BOUNDARY','capture freeze')
    must(t['capture'],'freezeExpectedAuxiliaries','capture freeze call')
    must(t['capture'],'timeoutMs=80','freeze telemetry')
    must(t['capture'],'lateOffersRejectedBySealedSlot=true','late offer policy')

    # Short/Long must share normal MGC frame rejection before opponent chroma.
    must(t['host'],'IRIS_26507_SHORT_A_SHARED_MGC_PRECHROMA_GATE','Short shared MGC gate')
    must(t['host'],'IRIS_26507_LONG_A_SHARED_MGC_PRECHROMA_GATE','Long shared MGC gate')
    if t['host'].count('flowVariationThreshold",iris26507FlowVariationThreshold') < 3:
        fail('expected normal + Short + Long dynamic MGC threshold binds')
    must(t['host'],'iris26480ShortAlignment.flowTexture,iris26487FinalWeightScratch,iris26501ShortCov','Short MGC frame weight input')
    must(t['host'],'irisV13ShadowAlignment.flowTexture,iris26487FinalWeightScratch,iris26501ShadowCov','Long MGC frame weight input')
    if t['host'].count('false,true,true);') < 2:
        fail('Short/Long semantic contribution not using MGC frame weight')

    # GPU-only topology: no new full provenance readback/CPU connected component pass.
    must(t['short'],'IRIS_26507_GPU_LOCAL_8_CONNECTED_SHORT_TOPOLOGY','Short GPU topology')
    must(t['short'],'connectedShortNeighbors','Short 8-neighbor connectivity')
    must(t['short'],'unresolvedNeighbors','Short unresolved-neighbor gate')
    for forbidden in ['IRIS_26507_BENTO_8_CONNECTED_TOPOLOGY','iris26507LargestEightConnected','iris26507BentoAccept','BENTO_GLOBAL_SHORT_ADMISSION']:
        if forbidden in t['host'] or forbidden in t['short']:
            fail('rejected CPU/global Bento draft survived: '+forbidden)

    # 26506 Short/Long physical coherence remains, but stale provenance cannot bypass newer motion rejection.
    must(t['short'],'IRIS_26506_SHORT_A_SPATIAL_PROVENANCE_COHERENCE','26506 Short coherence lineage')
    must(t['shadow'],'IRIS_26506_LONG_A_QUAD_COHERENT_CHROMA_AUTHORITY','26506 Long coherence lineage')
    must(t['normalizer'],'IRIS_26507_NO_STALE_SHORT_CHROMA_IMMUNITY','normalizer stale immunity removal')
    must(t['normalizer'],'float genericChromaPermission=1.0;','normalizer generic safety permission')
    if 'genericChromaPermission=centerShortProven?0.0:1.0' in t['normalizer']:
        fail('stale Short provenance chroma immunity survived')
    must(t['normalizer'],'IRIS_26506_OPPONENT_CONFIDENCE_REFERENCE_CHROMA','26506 opponent confidence lineage')

    # UHDR: preserve 26506 signal relation; change only full-display capacity metadata.
    must(t['render'],'private static final float OUTPUT_EXPOSURE_SCALE = 0.80f;','tested SDR primary scale')
    must(t['render'],'private static final float HDR_EXPOSURE_SCALE = 1.00f;','26506 HDR target')
    if 'HDR_EXPOSURE_SCALE = 1.25f' in t['render']:
        fail('rejected 1.25 HDR signal target survived')
    must(t['ultrahdr'],'IRIS_26507_FULL_HDR_DISPLAY_CAPACITY_PARITY','UHDR capacity marker')
    must(t['ultrahdr'],'DEFAULT_FULL_HDR_DISPLAY_RATIO = 1.6033f','UHDR full display fallback')
    must(t['ultrahdr'],'setDisplayRatioForFullHdr(fullHdrDisplayRatio)','UHDR capacity metadata')
    must(t['ultrahdr'],'setRatioMax(safeMax, safeMax, safeMax)','content ratioMax preserved')

    # True 4:4:4 and JPEG_R packaging.
    must(t['save'],'IRIS_26507_MOTION_JPEG444','Motion saver 444')
    must(t['save'],'MotionV2Jpeg444Encoder.write','Motion saver native path')
    must(t['jpegjava'],'IRIS_26507_TRUE_JPEG444_JPEGR','Java 444 owner')
    must(t['jni'],'TJPARAM_SUBSAMP,TJSAMP_444','TurboJPEG 444')
    must(t['jni'],'TJPF_RGBA','RGBA source')
    must(t['jpegr'],'uhdr_enc_set_compressed_image','preserve compressed base')
    must(t['jpegr'],'uhdr_enc_set_gainmap_image','JPEG_R gain map')
    must(t['cmake'],'IRIS_26507_TRUE_JPEG444_JPEGR','CMake 444')
    must(t['cmake'],'turbojpeg-static','TurboJPEG target')
    must(t['cmake'],'iris26507-ultrahdr','libultrahdr target')
    must(t['cmake'],'IRIS_26507_V3_NATIVE_DEPENDENCY_LAYOUT_PROOF','native layout proof marker')
    must(t['cmake'],'${IRIS26507_UHDR}/ultrahdr_api.h','libultrahdr public root header')
    must(t['cmake'],'${IRIS26507_UHDR}/lib/src/ultrahdr_api.cpp','libultrahdr core source proof')
    must(t['cmake'],'set(WITH_TESTS OFF CACHE BOOL "" FORCE)','TurboJPEG tests disabled')
    must(t['cmake'],'set(WITH_TOOLS OFF CACHE BOOL "" FORCE)','TurboJPEG tools disabled')
    must(t['cmake'],'set(WITH_JAVA OFF CACHE BOOL "" FORCE)','TurboJPEG Java disabled')
    if '${IRIS26507_UHDR}/lib/include/ultrahdr_api.h' in t['cmake']:
        fail('obsolete libultrahdr public-header path survived')

    if a.base_root and not (a.base_root/'app/src/main').is_dir(): fail('base-root missing app/src/main')
    print('PASS: 26507 root-fix ownership validated: RAW/2 MGC, immutable aux, shared Short/Long pre-chroma rejection, GPU Short topology, UHDR display-capacity parity, true JPEG 4:4:4')
if __name__=='__main__': main()
