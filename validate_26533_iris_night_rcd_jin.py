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
PROTECTED_26532_PATHS = (
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
)

def load_hash_contract(path):
    rows={}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        line=line.strip()
        if not line or line.startswith('#'): continue
        parts=line.split(None,1)
        if len(parts)!=2 or not re.fullmatch(r'[0-9a-f]{64}', parts[0]): raise RuntimeError('invalid exact-26532 owner hash contract line: '+line)
        h,rel=parts[0],parts[1].strip()
        if rel in rows: raise RuntimeError('duplicate exact-26532 owner hash contract path: '+rel)
        rows[rel]=h
    return rows


def java_executable_text(src):
    """Return Java source with comments and string/char literals blanked.

    Anti-hybrid checks must inspect executable tokens, not documentation or
    diagnostics that merely name a forbidden legacy Photon path. Newlines are
    preserved so debugging line structure remains readable.
    """
    out=[]
    i=0
    n=len(src)
    state='code'
    while i<n:
        c=src[i]
        d=src[i+1] if i+1<n else ''
        if state=='code':
            if c=='/' and d=='/':
                out.extend((' ',' ')); i+=2; state='line'; continue
            if c=='/' and d=='*':
                out.extend((' ',' ')); i+=2; state='block'; continue
            if c=='"':
                out.append(' '); i+=1; state='string'; continue
            if c=="'":
                out.append(' '); i+=1; state='char'; continue
            out.append(c); i+=1; continue
        if state=='line':
            if c=='\n': out.append('\n'); state='code'
            else: out.append(' ')
            i+=1; continue
        if state=='block':
            if c=='*' and d=='/':
                out.extend((' ',' ')); i+=2; state='code'; continue
            out.append('\n' if c=='\n' else ' '); i+=1; continue
        if state in ('string','char'):
            quote='"' if state=='string' else "'"
            if c=='\\':
                out.append(' '); i+=1
                if i<n:
                    out.append('\n' if src[i]=='\n' else ' '); i+=1
                continue
            if c==quote:
                out.append(' '); i+=1; state='code'; continue
            out.append('\n' if c=='\n' else ' '); i+=1; continue
    return ''.join(out)

def self_test():
    doc="""
    // GenerateExpoPair and NIGHT_HANDHELD_CAP are forbidden legacy names.
    /* Bayer2Float ExposureFusionBayer2 ESD3D2 Sharpen2 */
    String diagnostic = "CaptureSharpening PyramidMerging Demosaic3";
    char q = '\'';
    int safeOwner = 1;
    """
    code=java_executable_text(doc)
    for bad in ('GenerateExpoPair','NIGHT_HANDHELD_CAP','Bayer2Float','ExposureFusionBayer2','ESD3D2','Sharpen2','CaptureSharpening','PyramidMerging','Demosaic3'):
        req(bad not in code,'validator lexer self-test false-positive: '+bad)
    live='GenerateExpoPair(builder); Bayer2Float node = null; String s="ESD3D2";'
    live_code=java_executable_text(live)
    req('GenerateExpoPair' in live_code,'validator lexer self-test missed live GenerateExpoPair')
    req('Bayer2Float' in live_code,'validator lexer self-test missed live Bayer2Float')
    req('ESD3D2' not in live_code,'validator lexer self-test did not strip string literal')
    # Exercise the real handoff generator, not only synthetic lexer fixtures.
    import importlib.util, tempfile
    apply_path=Path(__file__).with_name('apply_26533_iris_night_rcd_jin.py')
    req(apply_path.is_file(),'validator self-test cannot find 26533 transformer')
    spec=importlib.util.spec_from_file_location('apply26533_selftest',apply_path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    with tempfile.TemporaryDirectory() as td:
        rr=Path(td)
        mod.add_night_exposure(rr); mod.add_night_input(rr)
        generated_night=(rr/'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java').read_text(encoding='utf-8')
        generated_input=(rr/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisNightBayerInput.java').read_text(encoding='utf-8')
        req('GenerateExpoPair' in generated_night,'generator self-test lost explanatory GenerateExpoPair documentation')
        req('GenerateExpoPair' not in java_executable_text(generated_night),'generator self-test sees executable GenerateExpoPair leak')
        req('Bayer2Float' in generated_input,'generator self-test lost explanatory Bayer2Float documentation')
        req('Bayer2Float' not in java_executable_text(generated_input),'generator self-test sees executable Bayer2Float leak')
        hp=rr/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'
        hp.parent.mkdir(parents=True,exist_ok=True); hp.write_text('class H {\nprivate void ApplyHdrX() {\n}\n}\n',encoding='utf-8')
        mod.patch_hdrx(rr); hh=hp.read_text(encoding='utf-8')
        hb=hh[hh.index('private void ApplyIrisNight26533()'):hh.index('private void ApplyHdrX()')]
        hcode=java_executable_text(hb)
        for bad in ('PyramidMerging','ImageFrameDeblur','IsoExpoSelector.fullpairs','ExposureFusionBayer2','ESD3D2','Sharpen2','CaptureSharpening'):
            req(bad not in hcode,'generator Hdrx self-test executable legacy leak: '+bad)
        ncode=java_executable_text(mod.neural_java())
        req('writeSuperRes' not in ncode,'generator neural self-test executable writeSuperRes leak')
        req('PhotonCamera.getInstance().getAssets()' not in ncode,'generator neural self-test invalid executable asset access')
    print('26533 VALIDATOR EXECUTABLE-TOKEN + REAL-GENERATOR SELF-TEST PASSED')


def req(cond,msg):
    if not cond: raise RuntimeError(msg)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',nargs='?'); ap.add_argument('--model-provenance'); ap.add_argument('--base-owner-hashes'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args();
    if a.self_test:
        self_test(); return
    req(a.root is not None,'root is required unless --self-test is used'); req(a.base_owner_hashes is not None,'--base-owner-hashes is required unless --self-test is used'); r=Path(a.root); exact=load_hash_contract(a.base_owner_hashes)
    def txt(rel): return (r/rel).read_text(encoding='utf-8')
    cap=txt('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
    iso=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IsoExpoSelector.java')
    night=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java')
    hdr=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
    post=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java')
    bridge=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightMgc1271Bridge.kt')
    grad=txt('app/build.gradle')
    night_code=java_executable_text(night)
    req(cap.count('IrisNightExposureSelector.setExpo')==2,'Night exposure capture routing count !=2')
    req('IRIS_26533_NIGHT_EXPOSURE_SOLE_OWNER' in night,'Night exposure owner missing')
    req('GenerateExpoPair' not in night_code and 'NIGHT_HANDHELD_CAP' not in night_code,'Photon Night exposure logic leaked into Iris owner')
    req('if (cameraMode == CameraMode.NIGHT) {\n            ApplyIrisNight26533();\n            return;' in hdr,'Night early isolated dispatch missing')
    block=hdr[hdr.index('private void ApplyIrisNight26533()'):hdr.index('private void ApplyHdrX()')]
    block_code=java_executable_text(block)
    for bad in ('PyramidMerging','ImageFrameDeblur','IsoExpoSelector.fullpairs','ExposureFusionBayer2','ESD3D2','Sharpen2','CaptureSharpening'):
        req(bad not in block_code,'forbidden Photon Night executable token in Iris Night block: '+bad)
    req('p.motionV2Active=false' in block,'Night must not masquerade as Motion')
    req('IrisNightMgc1271Bridge.reconstruct' in block and 'PhotonMotionMgc1271Bridge.reconstruct' in block,'12MP Bayer and SR bridge branches both required')
    req('outputMode = MgcSpatialOutputMode.BAYER' in bridge,'Night bridge not BAYER')
    req('mergeMethod = MgcMergeMethod.SPATIAL_BAYER' in bridge,'Night bridge not SPATIAL_BAYER')
    req('IRIS_26533_NIGHT_ISOLATED_POST_GRAPH' in post,'isolated Night post graph missing')
    nightpost=post[post.index('IRIS_26533_NIGHT_ISOLATED_POST_GRAPH'):post.index('IRIS_26410_MOTION_V2_ISOLATED_POST_GRAPH')]
    for good in ('IrisNightBayerInput','MotionV2RcdDemosaic','MotionV2DisplayExposure','MotionV2ColorTransform','MotionV2Render'):
        req(good in nightpost,'Night post node missing: '+good)
    nightpost_code=java_executable_text(nightpost)
    for bad in ('ExposureFusionBayer2','Demosaic3','ESD3D2','CaptureSharpening','Sharpen2','Bayer2Float'):
        req(bad not in nightpost_code,'legacy Night post executable node leaked: '+bad)
    inputj=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisNightBayerInput.java')
    req('IRIS_26533_NIGHT_SENSOR_CODE_INPUT' in inputj,'Iris Night sensor-code input owner missing')
    req('Bayer2Float' not in java_executable_text(inputj),'Photon Bayer2Float executable implementation leaked into Iris Night input')
    shader=txt('app/src/main/assets/shaders/irisnight/raw16_to_linear_bayer.glsl')
    req('uniform usampler2D InputBuffer;' in shader and 'Output=max((raw-bl)' in shader,'Iris Night RAW16 physical normalization shader missing')
    req("onnxruntime-android:1.29.0" in grad,'pinned ORT 1.29.0 dependency missing')
    model=r/'app/src/main/assets/models/iris_night_jin_lol_512.onnx'; req(model.exists() and model.stat().st_size>1_000_000,'ONNX model missing/suspiciously small')
    neural=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java')
    req('N=512, GRID=32' in neural and 'fullResInference=false' in neural,'512 control-resolution neural invariant missing')
    req('writeSuperRes' not in java_executable_text(neural),'neural node must not allocate/process 50MP output')
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
    req('PhotonCamera.getInstance().getAssets()' not in java_executable_text(neural),'invalid executable PhotonCamera getInstance asset access survived')
    for rel,expected in RCD_HASHES.items():
        f=r/rel; req(f.exists(),'RCD payload missing: '+rel); req(hashlib.sha256(f.read_bytes()).hexdigest()==expected,'RCD certified hash mismatch: '+rel)
    for rel in PROTECTED_26532_PATHS:
        req(rel in exact,'exact-26532 owner hash contract missing protected path: '+rel)
        f=r/rel; req(f.exists(),'protected 26532 file missing: '+rel); req(hashlib.sha256(f.read_bytes()).hexdigest()==exact[rel],'protected Motion/Spatial 26532 hash changed: '+rel)
    print('26533 NIGHT ANTI-HYBRID PROOF PASSED')
    print('26533 12MP/50MP PERFORMANCE ARCHITECTURE PROOF PASSED')
    print('26533 RCD/DNG/NEURAL OWNER PROOF PASSED')
if __name__=='__main__': main()
