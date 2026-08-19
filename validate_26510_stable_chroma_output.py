#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, sys
from pathlib import Path

EXPECTED_CHANGED = {
    'app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl',
    'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl',
    'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_vgn_chroma_26510.glsl',
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
    allnames=set(bf)|set(cf)
    changed=set()
    for n in allnames:
        if n not in bf or n not in cf or sha(bf[n])!=sha(cf[n]):
            changed.add('app/'+n)
    assert changed==EXPECTED_CHANGED, f'changed runtime path set mismatch\nexpected={sorted(EXPECTED_CHANGED)}\nactual={sorted(changed)}'

    vp=text(ca/'version.properties')
    need(vp,'VERSION_NAME=0.9726507','pre-build base version')
    need(vp,'VERSION_BUILD=26507','pre-build base build')

    cap=text(ca/'src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
    need(cap,'/* updateMotionV2ExposureAuthority(result); intentionally dormant */','dormant Motion AE authority')
    # Prevent an active call from surviving elsewhere on a non-comment line.
    for line in cap.splitlines():
        q=line.strip()
        if 'updateMotionV2ExposureAuthority(result);' in q and not q.startswith('/*') and not q.startswith('//'):
            raise AssertionError('active updateMotionV2ExposureAuthority call found: '+q)

    runtime_text='\n'.join(text(p) for p in cf.values() if p.suffix in {'.java','.glsl','.cpp','.h','.kt'})
    forbid(runtime_text,'IRIS_26509_','rejected 26509 runtime marker')

    contrib=text(ca/'src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl')
    need(contrib,'IRIS_26510_PHYSICAL_BORDER_EVIDENCE_OWNER','physical border evidence owner')
    forbid(contrib,'phaseClamp(','phase-clamped synthetic CFA support')
    forbid(contrib,'clampPhaseCoordinate(','phase-clamped synthetic CFA support helper')
    need(contrib,'if(inBounds(requested)){ownedPixel=requested;return true;}','physical in-bounds sample authority')

    rej=text(ca/'src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl')
    need(rej,'IRIS_26510_PHYSICAL_MGC_WARP_BOUNDARY','MGC physical warp boundary')
    forbid(rej,'mirrorUv(','mirrored external MGC evidence')
    need(rej,'imageStore(outReverseWeight,p,vec4(0.0));imageStore(outPixelDifference,p,vec4(0.0));return;','OOB rejection zero evidence')

    vgn=text(ca/'src/main/assets/shaders/motionv2/mfsr_spatial_rgb_vgn_chroma_26510.glsl')
    need(vgn,'IRIS_26510_VGN_CHROMA_ONLY_OWNER','VGN chroma-only owner')
    need(vgn,'vec3 toCalculation','calculation-WB entry')
    need(vgn,'vec3 toCamera','calculation-WB exit')
    need(vgn,'Output=vec4(toCamera(filtered),center.a);','26507 support-alpha preservation')
    need(vgn,'float lum(vec3 c)','luma authority')
    forbid(vgn,'flowTexture','temporal resampling in post-fusion chroma stage')
    forbid(vgn,'currentRaw','RAW resampling in post-fusion chroma stage')

    host=text(ca/'src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java')
    need(host,'motionv2/mfsr_spatial_rgb_vgn_chroma_26510','VGN host shader load')
    need(host,'setVar("wbR",wronskiGlobalWbR)','VGN host wbR')
    need(host,'setVar("wbB",wronskiGlobalWbB)','VGN host wbB')
    need(host,'iris26480ReadbackOutput = iris26510VgnChromaOutput;','VGN final readback ownership')
    need(host,'IRIS_26510_VGN_CHROMA_ONLY_APPLIED','VGN runtime marker')
    forbid(host,'IRIS_26508_SHARED_NORMAL_LONG_MGC_FUSION_OWNER','rejected 26508 Long fusion')

    hdrx=text(ca/'src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
    need(hdrx,'IRIS_26510_ASYNC_JPEGR_OUTPUT_OWNER','async JPEG_R output owner')
    need(hdrx,'IRIS_26510_CAPTURE_RELEASE_BEFORE_JPEGR_SAVE','capture release marker')
    need(hdrx,'IRIS_26510_ASYNC_JPEGR_OUTPUT_COMPLETE','async completion marker')
    need(hdrx,'MOTION_26480_OUTPUT_EXECUTOR.execute','existing serialized output executor')
    need(hdrx,'callback.onFinished();return;','capture callback before async save completion')

    native=text(ca/'src/main/cpp/motionv2_jpeg444_jni.cpp')
    assert native.count('TJPARAM_OPTIMIZE,0')==2, 'expected exactly two disabled Huffman optimization sites'
    assert native.count('TJPARAM_OPTIMIZE,1')==0, 'optimized Huffman search still active'
    need(native,'TJSAMP_444','base JPEG 4:4:4 preserved')
    need(native,'IRIS_26510_JPEG_HUFFMAN_SPEED_OWNER','JPEG entropy speed owner')

    enc=text(ca/'src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java')
    need(enc,'GAINMAP_QUALITY=95','gainmap quality preserved')
    need(enc,'IRIS_26507_JPEG444','26507 JPEG444/JPEG_R authority preserved')
    need(enc,'IRIS_26510_JPEG444_TIMING','new JPEG stage timing')

    # Explicit key authority files must be byte-identical to successful 26507.
    protected=[
      'src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
      'src/main/java/com/particlesdevs/photoncamera/processing/parameters/IsoExpoSelector.java',
      'src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java',
      'src/main/assets/shaders/motionv2/mfsr_flow_expand.glsl',
      'src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java',
      'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
      'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
      'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
      'src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
      'src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl',
      'src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl',
      'src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl',
      'src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl',
    ]
    for n in protected:
        bp=ba/n; cp=ca/n
        assert bp.is_file() and cp.is_file(), 'protected file missing: '+n
        assert sha(bp)==sha(cp), 'protected 26507 authority drifted: '+n

    print('PASS: 26510 exact seven-path runtime delta')
    print('PASS: 26507 AE/Wronski/Short/Long/tone/color/render authorities byte-identical')
    print('PASS: physical border evidence + MGC OOB zero-evidence contract')
    print('PASS: VGN-derived full-frame chroma-only stage preserves luma/support authority')
    print('PASS: async JPEG_R ownership + unchanged JPEG quality/444/gainmap quality')

if __name__=='__main__':
    try: main()
    except AssertionError as e:
        print('ERROR:',e,file=sys.stderr); sys.exit(1)
