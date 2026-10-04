#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26761_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def read(root,rel): return (root/rel).read_text()
def sha(root,rel): return hashlib.sha256((root/rel).read_bytes()).hexdigest()
def same(rel): assert sha(base,rel)==sha(cand,rel),f'protected regression changed: {rel}'
# Critical architecture owners outside the intended 5-file chroma-control scope stay byte-identical.
for rel in [
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/MgcFullResolutionDenoise.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/IrisZoomController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLPreview.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/MainRenderer.java',
 'app/src/main/assets/shaders/motionv2/render.glsl',
 'app/src/main/assets/shaders/motionv2/gainmap.glsl',
 'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
]:
 if (base/rel).is_file(): same(rel)
# Shared policy is one authority and is based only on propagated measured output tuning SNR.
tune_rel='app/src/main/java/com/hinnka/mycamera/processor/MgcSabreKernelTuning.kt'; tune=read(cand,tune_rel); btune=read(base,tune_rel)
assert tune.count('IRIS_26761_MEASURED_SNR_CHROMA_SCALE')==1
assert tune.count('adaptiveResidualChromaScale26761')==1
m=re.search(r'internal fun adaptiveResidualChromaScale26761\(outputTuningSnr: Float\): Float \{(.*?)\n    \}',tune,re.S); assert m
body=m.group(1)
for token in ['snr <= 10f -> 1.0f','snr >= 20f -> 0.50f','1.0f - 0.05f * (snr - 10f)']: assert token in body,token
for forbidden in ['iso','sensitivity','exposure','shutter','brightness']: assert forbidden not in body.lower(),forbidden
def curve(snr):
 if not math.isfinite(snr): snr=20.0
 snr=max(0.0,snr)
 return 1.0 if snr<=10 else 0.5 if snr>=20 else 1.0-0.05*(snr-10)
for s,e in [(5,1.0),(10,1.0),(12,0.9),(15,0.75),(18,0.6),(20,0.5),(40,0.5)]: assert abs(curve(s)-e)<1e-7,(s,curve(s),e)
assert abs(curve(11.569331)-0.92153345)<1e-7
assert abs(curve(11.51297)-0.9243515)<1e-7
# Normal Motion Auto: fixed 26733 half-scale is replaced; Night/Custom exact and luma authority remain.
bridge_rel='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'; bridge=read(cand,bridge_rel)
for token in ['IRIS_26761_MOTION_MEASURED_SNR_RESIDUAL_CHROMA','AUTO_MEASURED_SNR','adaptiveResidualChromaScale26761(tuningSnr!!)','referenceSnr=$referenceSnr','outputTuningSnr=$tuningSnr','permittedFactor=$automaticResidualChromaFactor26761','IRIS_26728_RESIDUAL_CHROMA_FLOOR_OWNER','automaticLumaScale26639 = 0.0f','if (!parameters.irisNightActive && irisSettings.residualChromaCustom)','chromaStrengthScale = if (customResidualChroma != null) 0f else automaticResidualChromaScale26761']:
 assert token in bridge,token
assert 'automaticResidualChromaScale26733' not in bridge
assert 'AUTO_SNR_HALF' not in bridge
# Adaptive function is evaluated only for Motion Auto; Custom and Night get no new adaptive decision.
needle='if (!parameters.irisNightActive && customResidualChroma == null) {\n                    MgcSabreKernelTuning.adaptiveResidualChromaScale26761(tuningSnr!!)'
assert needle in bridge
# SR: exact propagated output tuning SNR equals the already-published MGC tuning SNR relation.
stack_rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'; stack=read(cand,stack_rel)
assert stack.count('kernelTuning.referenceSnr / sqrt(sabreNoiseModelScale)')>=2
for token in ['IRIS_26761_SR_CHROMA_SNR_CONTROL','adaptiveResidualChromaScale26761(outputTuningSnr26761)','uChromaDenoiseStrength26761','nativeVgnChromaOwner=true','localMaterialGate=true','IRIS_26758_SR_DIRECT_CFA_ONLY_ROUTER']:
 assert token in stack,token
# No ISO/sensitivity/exposure metadata is used as an SR chroma-strength switch near the new policy block.
ix=stack.index('IRIS_26761_SR_CHROMA_SNR_CONTROL'); window=stack[max(0,ix-1200):ix+1800].lower()
for forbidden in ['sensor_sensitivity','sensitivityiso','exposuretime','shutter']: assert forbidden not in window,forbidden
# Shader normalization: the ONLY shader-source delta from successful 26760 is one uniform plus replacing fixed 0.50 with adaptive maximum.
shader_rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'; bs=read(base,shader_rel); cs=read(cand,shader_rel)
assert cs.count('uniform float uChromaDenoiseStrength26761;')==1
assert cs.count('IRIS_26761_SUPER_RES_MEASURED_SNR_CHROMA_BLEND')==1
assert cs.count('IRIS_26760_SUPER_RES_CHROMA_DENOISE_50')==1
old='''            float chromaDenoise26760 = 0.50 * (1.0 - 0.75 * materialBoundary);\n            selectedChroma = mix(selectedChroma, denoisedChroma26760, chromaDenoise26760);\n'''
new='''            /* IRIS_26761_SUPER_RES_MEASURED_SNR_CHROMA_BLEND\n             * Preserve the complete 26760 same-material/native-VGN consensus and coherent-color\n             * retention. Only its maximum blend becomes the shared measured-output-SNR factor.\n             * materialBoundary still retreats the cleanup to 25% of that permitted maximum. */\n            float chromaDenoise26761 = clamp(uChromaDenoiseStrength26761, 0.50, 1.00) *\n                (1.0 - 0.75 * materialBoundary);\n            selectedChroma = mix(selectedChroma, denoisedChroma26760, chromaDenoise26761);\n'''
normalized=cs.replace('        uniform float uChromaDenoiseStrength26761;\n','',1).replace(new,old,1)
assert normalized==bs,'shader changed outside adaptive uniform/blend'
# Active ordinary zoom runtime GLSL remains the independent static shader, byte-identical in source.
def block(src,start,end):
 a=src.index(start); b=src.index(end,a); return src[a:b]
hz_start='val highZoomRgbProtect26724: String ='; hz_end='    val highZoomDetailMerge26718: String by lazy'
assert block(cs,hz_start,hz_end)==block(bs,hz_start,hz_end),'active ordinary high-zoom shader changed'
# Successful SR luma/detail/highlight safety remains.
seg=block(cs,'val true2xGuideRender26568 =','    /* IRIS_26720_HIGH_ZOOM_DIRECT_CFA_RGB_OWNER')
for token in ['IRIS_26759_CONFIDENCE_GATED_DETAIL_REINFORCEMENT','IRIS_26758_SR_ADAPTIVE_ALIGNMENT_REJECTION','unsupportedRow','unsupportedCol','unsupportedChecker','aliasGate','highlightGate','temporalGate','phaseGate','agreementGate','No direct-CFA chroma enters.','0.90 * selectedMag26760','materialBoundary','uNativeVgnGuide']:
 assert token in seg,token
ver=read(cand,'app/version.properties'); assert 'VERSION_NAME=0.9726761' in ver and 'VERSION_BUILD=26761' in ver
print('PASS 26761 regressions: measured-output-SNR policy 1.00<=10 -> 0.50>=20; no ISO scene-brightness switch; Normal Auto + SR share policy; Night/Custom/luma/direct-CFA/ordinary-zoom/VGN/highlight/UHDR/DNG owners protected')
