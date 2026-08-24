#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, re

RCD_HASHES = {
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java':'754beea951bdea2fbde31988011a36ee1c77bf35fc503b383529c00b9031cd40',
 'app/src/main/assets/shaders/motionv2/rcd26489_diag_direction.glsl':'1bd8f80b12e06f5ab8c19bb65d27e60f31998327557df0e6f551c682bdfc2b0e',
 'app/src/main/assets/shaders/motionv2/rcd26489_diag_residual.glsl':'47e7041976905fb76a54acb36e19d30d4d29d8e4dd9d25012f0515978170a2e3',
 'app/src/main/assets/shaders/motionv2/rcd26489_green.glsl':'4f268056ae8d8f1da8ae5b3936768cbb7d3841f9ac4e4b54ac6f113ca6a55040',
 'app/src/main/assets/shaders/motionv2/rcd26489_green_rb.glsl':'b0476f9e5a7b130d7c3edc58b7ba4a033edc5fa2c55605fd446feea8e1b3e4ca',
 'app/src/main/assets/shaders/motionv2/rcd26489_lpf.glsl':'95dff8fa0f3c4420de8e13346b766c7a2a80f76b08634b3b8135f775cac06a0c',
 'app/src/main/assets/shaders/motionv2/rcd26489_opposite.glsl':'30e732e00e50aeca0d29d08529230c3d043b81e8df87b0c4504768e89fe80392',
 'app/src/main/assets/shaders/motionv2/rcd26489_populate.glsl':'69ecf068e9229e521ba29e033c4bb0ee48d9919e34cd65525b4d9125a30270aa',
 'app/src/main/assets/shaders/motionv2/rcd26489_vh_direction.glsl':'66831dfd1a39a4b5866631f1058a2883dd237961f33cc4c0bd169a7e02a0873e',
 'app/src/main/assets/shaders/motionv2/rcd26489_write.glsl':'0c3b66a45d0bd8288188c9963cf2b1c7abf0341bb08c59136cdbdd3dc458d346',
}
PROTECTED_26532 = {
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt':'8e10e9dfee15bb306aab74bdd8a41c41df05d9d5df753727887750e08f4c8e1c',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt':'2a4c259a6a47e066fa7605c5aa0b3d40d07d775bad75d1960a0444107eaf7a8a',
}

def req(cond,msg):
    if not cond: raise RuntimeError(msg)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--model-provenance'); a=ap.parse_args(); r=Path(a.root)
    def txt(rel): return (r/rel).read_text(encoding='utf-8')
    cap=txt('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
    iso=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IsoExpoSelector.java')
    night=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java')
    hdr=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
    post=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java')
    bridge=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightMgc1271Bridge.kt')
    grad=txt('app/build.gradle')
    req(cap.count('IrisNightExposureSelector.setExpo')==2,'Night exposure capture routing count !=2')
    req('IRIS_26533_NIGHT_EXPOSURE_SOLE_OWNER' in night,'Night exposure owner missing')
    req('GenerateExpoPair' not in night and 'NIGHT_HANDHELD_CAP' not in night,'Photon Night exposure logic leaked into Iris owner')
    req('if (cameraMode == CameraMode.NIGHT) {\n            ApplyIrisNight26533();\n            return;' in hdr,'Night early isolated dispatch missing')
    block=hdr[hdr.index('private void ApplyIrisNight26533()'):hdr.index('private void ApplyHdrX()')]
    for bad in ('PyramidMerging','ImageFrameDeblur','IsoExpoSelector.fullpairs','ExposureFusionBayer2','ESD3D2','Sharpen2','CaptureSharpening'):
        req(bad not in block,'forbidden Photon Night token in Iris Night block: '+bad)
    req('p.motionV2Active=false' in block,'Night must not masquerade as Motion')
    req('IrisNightMgc1271Bridge.reconstruct' in block and 'PhotonMotionMgc1271Bridge.reconstruct' in block,'12MP Bayer and SR bridge branches both required')
    req('outputMode = MgcSpatialOutputMode.BAYER' in bridge,'Night bridge not BAYER')
    req('mergeMethod = MgcMergeMethod.SPATIAL_BAYER' in bridge,'Night bridge not SPATIAL_BAYER')
    req('IRIS_26533_NIGHT_ISOLATED_POST_GRAPH' in post,'isolated Night post graph missing')
    nightpost=post[post.index('IRIS_26533_NIGHT_ISOLATED_POST_GRAPH'):post.index('IRIS_26410_MOTION_V2_ISOLATED_POST_GRAPH')]
    for good in ('IrisNightBayerInput','MotionV2RcdDemosaic','MotionV2DisplayExposure','MotionV2ColorTransform','MotionV2Render'):
        req(good in nightpost,'Night post node missing: '+good)
    for bad in ('ExposureFusionBayer2','Demosaic3','ESD3D2','CaptureSharpening','Sharpen2','Bayer2Float'):
        req(bad not in nightpost,'legacy Night post node leaked: '+bad)
    inputj=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisNightBayerInput.java')
    req('IRIS_26533_NIGHT_SENSOR_CODE_INPUT' in inputj,'Iris Night sensor-code input owner missing')
    req('Bayer2Float' not in inputj,'Photon Bayer2Float implementation leaked into Iris Night input')
    shader=txt('app/src/main/assets/shaders/irisnight/raw16_to_linear_bayer.glsl')
    req('uniform usampler2D InputBuffer;' in shader and 'Output=max((raw-bl)' in shader,'Iris Night RAW16 physical normalization shader missing')
    req("onnxruntime-android:1.29.0" in grad,'pinned ORT 1.29.0 dependency missing')
    model=r/'app/src/main/assets/models/iris_night_jin_lol_512.onnx'; req(model.exists() and model.stat().st_size>1_000_000,'ONNX model missing/suspiciously small')
    neural=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java')
    req('N=512, GRID=32' in neural and 'fullResInference=false' in neural,'512 control-resolution neural invariant missing')
    req('writeSuperRes' not in neural,'neural node must not allocate/process 50MP output')
    req('IrisMotionSuperResDngWriter.write' in block,'50MP SR DNG writer not reused')
    req('saveBitmapAsJPGMotionV2' in block,'26532 streaming SR JPEG writer not reused')
    req('saveNormalized16StackedRaw' in block,'native fused Bayer DNG path missing')
    # Motion ownership must remain in original bridge; Night bridge is additive.
    req((r/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').exists(),'Motion bridge missing')
    if a.model_provenance:
        pr=json.loads(Path(a.model_provenance).read_text()); req(pr['onnx_sha256']==hashlib.sha256(model.read_bytes()).hexdigest(),'model provenance hash mismatch'); req(pr['upstream_commit']=='2a0681eae7c2bbc120a019d5bb71bcbd12291df7','wrong upstream commit')

    req('configureStrictWronskiSensorAuthority(p);' in block,'Iris Camera2 sensor/color authority not initialized for Night')
    req('p.motionV2GlobalZoom=1.0f' in block and 'p.motionV2RenderResidualZoom=1.0f' in block,'Night V1 identity FOV/SR geometry guard missing')
    for rel in (
        'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
        'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
        'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'):
        t=txt(rel)
        req('motionV2Active || basePipeline.mParameters.irisNightActive' in t,'Iris Night capability guard missing: '+rel)
    req('PhotonCamera.getAssetLoader().getInputStream("models/iris_night_jin_lol_512.onnx")' in neural,'portable asset-loader model access missing')
    req('PhotonCamera.getInstance().getAssets()' not in neural,'invalid PhotonCamera getInstance asset access survived')
    for rel,expected in RCD_HASHES.items():
        f=r/rel; req(f.exists(),'RCD payload missing: '+rel); req(hashlib.sha256(f.read_bytes()).hexdigest()==expected,'RCD certified hash mismatch: '+rel)
    for rel,expected in PROTECTED_26532.items():
        f=r/rel; req(f.exists(),'protected 26532 file missing: '+rel); req(hashlib.sha256(f.read_bytes()).hexdigest()==expected,'protected Motion/Spatial 26532 hash changed: '+rel)
    print('26533 NIGHT ANTI-HYBRID PROOF PASSED')
    print('26533 12MP/50MP PERFORMANCE ARCHITECTURE PROOF PASSED')
    print('26533 RCD/DNG/NEURAL OWNER PROOF PASSED')
if __name__=='__main__': main()
