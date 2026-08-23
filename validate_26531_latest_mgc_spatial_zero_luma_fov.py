#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, re, sys

ALLOWED={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialMergeTuning.kt',
'app/src/main/java/com/hinnka/mycamera/processor/MgcAlignmentInputScale.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
}
PROTECTED_SABRE=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreProcessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt',
]
PROTECTED_CONTRACT=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def files(root):
    root=Path(root)
    return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file() and (p.relative_to(root).as_posix().startswith('app/src/main/') or p.relative_to(root).as_posix()=='app/version.properties')}
def require(x,msg):
    if not x: raise SystemExit('FAIL: '+msg)
def extract_triple(text,name):
    m=re.search(r'val\s+'+re.escape(name)+r'\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)
    require(m is not None,f'missing triple string {name}')
    return m.group(1).strip()+"\n"
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base',required=True); ap.add_argument('--candidate',required=True); ap.add_argument('--patch'); ap.add_argument('--rollback'); ap.add_argument('--json-out'); ap.add_argument('--postbuild',action='store_true'); a=ap.parse_args()
    b=Path(a.base); c=Path(a.candidate)
    fb,fc=files(b),files(c)
    changed=sorted(k for k in set(fb)|set(fc) if fb.get(k)!=fc.get(k))
    # version may differ only in postbuild checkpoint because base is V1.2 same 26530; runtime patch excludes it.
    runtime_changed=[x for x in changed if x!='app/version.properties']
    require(set(runtime_changed)==ALLOWED,f'changed scope {runtime_changed}')
    base_version=(b/'app/version.properties').read_text()
    candidate_version=(c/'app/version.properties').read_text()
    require('VERSION_NAME=0.9726530' in base_version and 'VERSION_BUILD=26530' in base_version,
            'base is not successful 0.9726530/26530')
    if a.postbuild:
        require('VERSION_NAME=0.9726531' in candidate_version and 'VERSION_BUILD=26531' in candidate_version,
                'postbuild candidate is not 0.9726531/26531')
    else:
        require(candidate_version==base_version, 'prebuild transform changed version before guarded build block')
    for rel in PROTECTED_SABRE+PROTECTED_CONTRACT:
        require((b/rel).is_file() and (c/rel).is_file(),f'missing protected {rel}')
        require(sha(b/rel)==sha(c/rel),f'protected file changed {rel}')

    bridge=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
    stack=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt').read_text()
    shaders=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt').read_text()
    post=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text()
    tuning=(c/'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialMergeTuning.kt').read_text()
    align=(c/'app/src/main/java/com/hinnka/mycamera/processor/MgcAlignmentInputScale.kt').read_text()
    render=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
    fusion=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt').read_text()

    # Sabre semantic gate: allow dormant source, forbid active selection from Motion.
    require('mergeMethod = MgcMergeMethod.SPATIAL_RGB' in bridge,'Motion lost SPATIAL_RGB selection')
    require('MgcMergeMethod.SABRE' not in bridge,'Motion bridge references SABRE selector')
    require('Pass.SABRE_DEFAULT' not in bridge,'Motion bridge references SABRE denoise pass')
    require('pass = MgcFullResolutionDenoise.Pass.SPATIAL_DEFAULT' in bridge,'Motion denoise pass is not SPATIAL_DEFAULT')
    require('if (mergeMethod == MgcMergeMethod.SABRE)' in fusion,'dormant Sabre route unexpectedly missing')
    require('GlesIris26521SpatialRgbStacker' in fusion,'Iris Spatial owner route missing')

    # New MGC Spatial findings.
    require('IRIS_26530_V1_3_FINAL_BAYER_ALIGNMENT_AUTHORITY' in shaders,'final Bayer alignment shader marker missing')
    strength=extract_triple(shaders,'strengthAlignment')
    require('uniform sampler2D uAlignment;' in strength and 'texture(uAlignment' in strength,'strength atlas not using final alignment')
    require('uFlow' not in strength,'strength atlas still uses generic flow')
    require('alignmentTexture = bentoBayerAlignmentTexture' in stack,'Bento strength not final Bayer aligned')
    require('alignmentTexture = prepared.bayerAlignmentTexture' in stack,'temporal strength not final Bayer aligned')
    require('bindTexture(strengthAlignmentProgram, "uAlignment", 0, alignmentTexture)' in stack,'strength host binding not final alignment')
    require('flowTexture = bentoFlowTexture' not in stack,'old Bento flow strength capture survived')

    # 26531 V1.3 Kotlin/API regression proof: final Bayer alignment is strength-only.
    require('flowTexture = prepared.flowTexture' in stack,
            'long-frame clipping guard lost dense flow authority')
    long_branch=stack.find('RawBurstFrameRole.SHADOW_LONG ->')
    long_call=stack.find('renderAlignedLongFrameClippingMask(', long_branch)
    require(long_call >= 0, 'long-frame clipping call missing')
    long_end=stack.find(')', long_call)
    long_text=stack[long_call:long_end+1]
    require('flowTexture = prepared.flowTexture' in long_text,
            'long-frame clipping call does not pass flowTexture')
    require('alignmentTexture = prepared.bayerAlignmentTexture' not in long_text,
            'final Bayer grid leaked into long-frame flow shader')
    require('val referenceGreenShotNoiseFactor: Float' in stack and
            'val referenceGreenReadVariance: Float' in stack,
            'Iris Bayer tuning green noise fields missing')
    require('referenceGreenShotNoiseFactor = shotNoise.getOrElse(1) { 0f }' in stack and
            'referenceGreenReadVariance = readNoise.getOrElse(1) { 0f }' in stack,
            'Iris Bayer tuning green noise fields not initialized')
    require('baseShotNoiseFactor = kernelTuning.referenceGreenShotNoiseFactor' in stack and
            'baseReadVariance = kernelTuning.referenceGreenReadVariance' in stack,
            'expected merge weight does not consume initialized Iris green noise fields')

    require('IRIS_26530_V1_3_MGC_ALIGNMENT_S16_SCALE' in align and 'S16_DOMAIN_SCALE / (whiteLevel + 1f)' in align,'MGC S16 alignment scaling missing')
    require('MgcAlignmentInputScale.compute(' in stack and 'whiteLevel = sensorWhiteLevel' in stack,'Iris alignment does not consume sensor white scaling')
    require('IRIS_26530_V1_3_MGC_EXPECTED_MERGE_WEIGHT' in tuning and 'fun expectedMergeWeight(' in tuning,'expected merge-weight helper missing')
    require('MgcSpatialMergeTuning.expectedMergeWeight(' in stack,'Iris does not use expected merge weight')
    require('alternateShotNoiseFactor = sourceShot.getOrElse(1)' in stack and 'alternateReadVariance = sourceRead.getOrElse(1)' in stack,'shot+read expected weight inputs missing')
    require('IRIS_26530_V1_3_PROPAGATED_OUTPUT_SNR' in tuning and 'fun outputNoiseModelSnr(' in tuning,'output NoiseModel SNR helper missing')
    require('mgcDenoiseTuningSnr = finishRawDenoiseSnr' in stack,'FinishRaw denoise SNR not propagated output model')
    require('spatial-output-noise-model' in stack,'output SNR source telemetry missing')

    # c317 direction moment superseded only in post-fusion direction selector.
    require('IRIS_26530_V1_3_RGB_DIRECTION_ONLY' in post,'RGB-direction supersession marker missing')
    require('directionMomentAt(' not in post and 'structureScale=' not in post and 'axis2[8]' not in post,'c317 direction-moment steering survived')
    require('g[i]=rgbGradient' in post,'post-fusion direction is not direct RGB gradient')
    # Core shared-green geometry remains intact for CFA/RG/BG reconstruction and SR.
    require('float targetGreen = greenSum / max(greenWeight' in shaders,'shared green reconstruction lost')
    require('(nativeValue - localGreen)' in shaders,'R-G/B-G opponent reconstruction lost')
    require('mergeRgbSuperRes' in shaders and 'uLumaTemporalScale' in shaders,'26530 SR/luma path lost')

    # Luma master experiment and zoom telemetry.
    require('val requestedLumaScale = irisSettings.lumaDenoise' in bridge,'requested luma telemetry missing')
    require('val lumaScale = 0f' in bridge,'effective MGC luma is not zero')
    require('val chromaScale = irisSettings.chromaDenoise' in bridge,'chroma ownership changed')
    require('requestedLuma=$requestedLumaScale effectiveMgcLuma=$lumaScale' in bridge,'requested/effective luma telemetry missing')
    require('sabreSelected=false' in bridge,'Sabre dormant telemetry missing')
    require('finalRenderLocalZoom=$localOutputZoom' in bridge,'bridge final render zoom telemetry missing')
    require('motionV2OutputZoom / spatialReconstructionZoom' not in render,'old residual FOV division survived')
    require('IRIS_26530_V1_3_FINAL_FOV_ZOOM' in render,'final FOV authority marker missing')
    require('basePipeline.mParameters.motionV2OutputZoom);' in render,'renderer does not use full requested local zoom')

    # Preserve low-zoom proven 26530 merge/normalizer strings; only strength shader is new here.
    bsh=(b/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt').read_text()
    require(extract_triple(bsh,'mergeRgb')==extract_triple(shaders,'mergeRgb'),'legacy mergeRgb changed')
    require(extract_triple(bsh,'normalizeRgb16')==extract_triple(shaders,'normalizeRgb16'),'legacy normalizeRgb16 changed')

    # Known already-correct latest MGC rejected-sample semantics must remain identity 1.0.
    smg=(c/'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialStrengthMapGenerator.kt').read_text()
    require('REJECTED_DENOISE_MULTIPLIER = 1f' in smg,'rejected-sample denoise multiplier not identity')

    out={'postbuild':a.postbuild,'changed_runtime_files':runtime_changed,'sabre_active':False,'motion_merge':'SPATIAL_RGB','mgc_luma':0.0,'chroma_owner':'irisSettings.chromaDenoise','fov_authority':'motionV2OutputZoom','sr_sampling_scale':'motionV2SpatialReconstructionZoom','latest_mgc_semantics':['final_bayer_alignment_strength','alignment_s16_sensor_white_scale','expected_merge_weight_shot_read','propagated_output_noise_snr','rgb_gradient_postfusion_direction','rejected_multiplier_identity']}
    if a.json_out: Path(a.json_out).write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2)); print('PASS: 26531 Iris Spatial + zero-luma + FOV + Kotlin API validator')
if __name__=='__main__': main()
