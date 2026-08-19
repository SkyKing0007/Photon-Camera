#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, sys
from pathlib import Path

EXPECTED_CHANGED = {
    'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl',
    'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl',
    'app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl',
    'app/src/main/cpp/CMakeLists.txt',
    'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
}

def sha(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def files(root: Path):
    return {p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file()}

def text(p: Path) -> str:
    return p.read_text(encoding='utf-8')

def need(s: str, needle: str, label: str):
    assert needle in s, f'missing {label}: {needle}'

def forbid(s: str, needle: str, label: str):
    assert needle not in s, f'forbidden {label}: {needle}'

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('candidate_root')
    ap.add_argument('--base-root', required=True)
    a=ap.parse_args()
    cand=Path(a.candidate_root).resolve(); base=Path(a.base_root).resolve()
    ca=cand/'app'; ba=base/'app'
    assert ca.is_dir() and ba.is_dir(), 'candidate/base app missing'
    bf=files(ba); cf=files(ca)
    changed=set()
    for n in set(bf)|set(cf):
        if n not in bf or n not in cf or sha(bf[n])!=sha(cf[n]): changed.add('app/'+n)
    assert changed==EXPECTED_CHANGED, f'changed runtime path set mismatch\nexpected={sorted(EXPECTED_CHANGED)}\nactual={sorted(changed)}'

    vp=text(ca/'version.properties')
    need(vp,'VERSION_NAME=0.9726507','pre-build successful-26507 version')
    need(vp,'VERSION_BUILD=26507','pre-build successful-26507 build')

    cap=text(ca/'src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
    need(cap,'/* updateMotionV2ExposureAuthority(result); intentionally dormant */','dormant Motion AE authority')
    for line in cap.splitlines():
        q=line.strip()
        if 'updateMotionV2ExposureAuthority(result);' in q and not q.startswith('/*') and not q.startswith('//'):
            raise AssertionError('active updateMotionV2ExposureAuthority call found: '+q)

    runtime='\n'.join(text(p) for p in cf.values() if p.suffix in {'.java','.glsl','.cpp','.h','.kt'})
    forbid(runtime,'IRIS_26509_','rejected 26509 runtime marker')
    forbid(runtime,'IRIS_26510_','rejected/no-effect 26510 runtime marker')
    forbid(runtime,'mfsr_spatial_rgb_vgn_chroma_26510','rejected VGN runtime')

    short=text(ca/'src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl')
    need(short,'IRIS_26511_BENTO_REGION_CANDIDATE_OWNER','Bento candidate owner')
    need(short,'layout(r32f, binding = 3)','Bento candidate image binding')
    need(short,'predictedSafeCount > 3.5 && centerGuard ? 0.5 : 0.0','correspondence-only safe-hole eligibility')
    need(short,'centerError <= 0.070','center radiometry guard')
    need(short,'storeBentoCandidate(p, 0.0);\n        addMask(D_FLOW_REJECT','flow reject remains hard')
    need(short,'storeBentoCandidate(p, 0.0);\n        addMask(D_RADIOMETRY_REJECT','radiometry reject remains hard')
    need(short,'sum4(shortSafe(shortCenter)) > 3.5 ? 1.0 : 0.0','direct Bento all-phase physical Short safety')
    forbid(short,'IRIS_26509_BRIDGE','26509 Short bridge')

    sw=text(ca/'src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl')
    need(sw,'IRIS_26511_BENTO_COHERENT_RGB_REGION','coherent Short RGB region owner')
    need(sw,'uniform highp sampler2D bentoCandidate;','candidate input')
    need(sw,'uniform highp sampler2D flowTexture;','stable 26507 Wronski flow input')
    need(sw,'max(df.x,df.y)>0.25','local flow-coherence guard')
    need(sw,'nearCount>=3.0&&wideCount>=8.0&&quadrantCount>=3.0','strict spatial hole-fill support')
    need(sw,'imageStore(outWeight,p,vec4(authority));','single scalar G/R-G/B-G authority')
    need(sw,'D_BENTO_CORR_UNFILLED','unfilled correspondence diagnostic')
    forbid(sw,'phaseState(','old per-phase Short semantic authority')

    norm=text(ca/'src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl')
    need(norm,'IRIS_26511_PROPAGATED_CHROMA_ONLY_FINISH','propagated chroma-only finish')
    need(norm,'shortBentoWeightTexture','Bento-aware highlight normalization')
    need(norm,'if(bentoColorCovered(packedP))return false;','coherent Bento prevents neighbor neutral expansion')
    need(norm,'rg=mix(rg,localRg,rPropagatedBlend);','R-G-only propagated cleanup')
    need(norm,'bg=mix(bg,localBg,bPropagatedBlend);','B-G-only propagated cleanup')
    need(norm,'return clamp(0.55*regionRisk*outlier*localQuality,0.0,0.55);','conservative max chroma blend')
    # Luma/green is not spatially mixed by the 26511 addition; only opponent channels are changed.
    forbid(norm,'green=mix(','luma/green denoise')
    forbid(norm,'calculationRgb=mix(\n            calculationRgb,vec3(local','RGB/luma smoothing')

    host=text(ca/'src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java')
    need(host,'iris26511ShortBentoCandidate=new GLTexture','Bento candidate host allocation')
    need(host,'setTextureCompute("outBentoCandidate",iris26511ShortBentoCandidate,true)','Bento candidate host binding')
    need(host,'setTexture("bentoCandidate",iris26511ShortBentoCandidate)','Bento region candidate binding')
    need(host,'setTexture("flowTexture",iris26480ShortAlignment.flowTexture)','Short region uses existing Wronski flow')
    need(host,'setTexture("shortBentoWeightTexture"','normalizer Bento texture binding')
    need(host,'IRIS_26511_BENTO_COHERENT_RGB_REGION=true','runtime Bento diagnostics')
    forbid(host,'IRIS_26508_SHARED_NORMAL_LONG_MGC_FUSION_OWNER','rejected 26508 Long architecture')

    hdrx=text(ca/'src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
    need(hdrx,'IRIS_26511_ASYNC_JPEGR_NORMAL_PRIORITY_OWNER','async normal-priority output owner')
    need(hdrx,'IRIS_26511_CAPTURE_RELEASE_BEFORE_JPEGR_SAVE','capture release marker')
    need(hdrx,'IRIS_26511_ASYNC_JPEGR_OUTPUT_COMPLETE','async output completion marker')
    need(hdrx,'MOTION_26480_OUTPUT_EXECUTOR.execute','existing serialized output executor')
    need(hdrx,'Process.THREAD_PRIORITY_DEFAULT','normal output-worker priority')
    need(hdrx,'callback.onFinished();return;','capture callback before output save completion')

    enc=text(ca/'src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java')
    need(enc,'IRIS_26511_PARALLEL_JPEGR_ENCODE_OWNER','parallel JPEG owner')
    need(enc,'Executors.newFixedThreadPool(2','two independent encode workers')
    need(enc,'Future<Boolean> baseFuture','parallel base task')
    need(enc,'Future<Boolean> gainFuture','parallel gain task')
    need(enc,'IRIS_26511_JPEG444_PARALLEL_TIMING','parallel timing marker')
    need(enc,'GAINMAP_QUALITY=95','gainmap quality unchanged')
    need(enc,'IRIS_26507_JPEG444','26507 true 4:4:4/JPEG_R authority retained')

    cmake=text(ca/'src/main/cpp/CMakeLists.txt')
    need(cmake,'IRIS_26511_DEBUG_APK_JPEG_OPTIMIZATION_OWNER','debug-APK JPEG optimization owner')
    need(cmake,'target_compile_options(turbojpeg-static PRIVATE -O3)','TurboJPEG release-speed compile option')
    need(cmake,'target_compile_options(jpeg-static PRIVATE -O3)','libjpeg release-speed compile option')
    need(cmake,'target_compile_options(motionv2jpeg PRIVATE -O3)','JNI JPEG wrapper release-speed compile option')

    native=text(ca/'src/main/cpp/motionv2_jpeg444_jni.cpp')
    need(native,'IRIS_26511_JPEG_HUFFMAN_SPEED_OWNER','native JPEG speed owner')
    assert native.count('TJPARAM_OPTIMIZE,0')==2, 'expected exactly two optimize=0 sites'
    assert native.count('TJPARAM_OPTIMIZE,1')==0, 'optimized Huffman search still active'
    need(native,'TJSAMP_444','base 4:4:4 preserved')

    protected=[
      'src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
      'src/main/java/com/particlesdevs/photoncamera/processing/parameters/IsoExpoSelector.java',
      'src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java',
      'src/main/assets/shaders/motionv2/mfsr_flow_expand.glsl',
      'src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java',
      'src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl',
      'src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl',
      'src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl',
      'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
      'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
      'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
      'src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
    ]
    for n in protected:
        bp=ba/n; cp=ca/n
        assert bp.is_file() and cp.is_file(), 'protected file missing: '+n
        assert sha(bp)==sha(cp), 'protected successful-26507 authority drifted: '+n

    print('PASS: 26511 exact eight-path runtime delta from successful 26507')
    print('PASS: 26507 AE / Normal Wronski / rejection / contributor / Long / tone / color / UHDR byte-identical')
    print('PASS: 1.27.1-style coherent Short Bento region uses strict correspondence-only hole fill; hard failures remain hard')
    print('PASS: propagated-noise chroma-only finish changes opponent channels only; luma authority remains 26507')
    print('PASS: JPEG_R capture release + normal-priority parallel base/gain encode; JPEG quality and 4:4:4 preserved')

if __name__=='__main__':
    try: main()
    except AssertionError as e:
        print('ERROR:',e,file=sys.stderr); sys.exit(1)
