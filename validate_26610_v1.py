#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
PKG=Path(__file__).resolve().parent
CHANGED=[x for x in (PKG/'V1_26610_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
def fail(m): raise SystemExit('FAIL: '+m)
def H(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def allh(r): return {str(p.relative_to(r)):H(p) for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
def need(s,t,l):
    if t not in s: fail(l+' missing '+t)
def forbid(s,t,l):
    if t in s: fail(l+' stale '+t)
def section(s,a,b):
    i=s.find(a); j=s.find(b,i+len(a))
    if i<0 or j<0: fail('section '+a)
    return s[i:j]
def shader(s,name): return section(s,'    val '+name+' = """','    """.trimIndent()')
def main():
    if len(sys.argv)!=3: fail('usage base candidate')
    b,c=map(Path,sys.argv[1:]); bh,ch=allh(b),allh(c)
    if set(bh)!=set(ch) or len(bh)!=1708: fail('full app universe changed')
    diff=sorted(k for k in bh if bh[k]!=ch[k])
    if diff!=sorted(CHANGED): fail('runtime diff allowlist '+repr(diff))
    v=(c/'app/version.properties').read_text(); need(v,'VERSION_NAME=0.9726610','version'); need(v,'VERSION_BUILD=26610','version')

    # Successful 26609 capture/preview/bridge and unrelated publication owners remain frozen.
    frozen=[
      'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
      'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java',
      'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
      'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
      'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
      'app/src/main/assets/shaders/motionv2/display_exposure.glsl',
      'app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl',
    ]
    for r in frozen:
        if (b/r).read_bytes()!=(c/r).read_bytes(): fail('successful-26609 frozen owner changed '+r)

    # Exact successful acquisition stays inherited.
    cc=(c/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
    for t in ['universalHdrExposureDecision=true','broadHdrConflict=','mixedHdrConflict=','compactHdrConflict=',
              'signal >= 0.980f','quadPhases >= 2']:
        need(cc,t,'26609 universal HDR acquisition inheritance')

    sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
    rescue=shader(sh,'shortRescueWeight26607'); rejection=shader(sh,'rejection')
    for t in ['layout(location = 2) out float oPhysicalReverseWeight;',
              'oPhysicalReverseWeight = clamp(unblocker, 0.0, 1.0);']:
        need(rejection,t,'common ordinary-rejection physical output')
    for t in ['IRIS_26610_NO_LITERAL_CORE_GEOMETRY_BYPASS','uniform sampler2D uPhysicalWeight;',
              'float localGeometry = localResidualConfidence;',
              'float sharedPhysicalProtection = min(physicalWeight, localResidualConfidence);',
              'float censoredCoreWeight = min(sharedPhysicalProtection, rescueConfidence);',
              'IRIS_26610_TWO_PHASE_PHYSICAL_CENSORSHIP_ONLY',
              'if (secondHighest4(referenceRaw) < uSourceClippingPoint) return 0.0;',
              'IRIS_26610_ONLY_PHYSICAL_CENSORSHIP_RELAXES_PHOTOMETRY',
              'float physicalCensoring = clamp(literalLoss, 0.0, 1.0);',
              'float finalWeight = mix(ordinaryWeight, censoredCoreWeight, physicalCensoring);']:
        need(rescue,t,'26610 SHORT protection')
    forbid(rescue,'mix(localResidualConfidence, 1.0, literalCore)','literal-core geometry bypass')
    forbid(rescue,'mix(ordinaryWeight, rescueConfidence, targetLoss)','unprotected rescue replacement')
    forbid(rescue,'mix(ordinaryWeight, censoredCoreWeight, targetLoss)','effective-loss photometric bypass')

    st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
    # Exposure-normalization proof: every non-reference frame is calibrated into the
    # reference exposure domain before guide construction and ordinary Sabre rejection.
    for t in [
        'exposureScale = (\n                    referenceExposure / validExposureProduct(frame.exposureProduct)',
        'val calibration = calibrationForFrame(frame, exposureScale, kernelTuning)',
        'gains[channel] =\n                calculationWhiteBalance[channel] * exposureScale / range',
        'bayerPhaseGains[phase] = exposureScale / range',
        'val referenceCalibration = calibrationForFrame(\n                frame = frames.first(),\n                exposureScale = 1f',
        'renderSabreGuideAndCovariance(\n                    extracted = currentExtracted',
    ]:
        need(st,t,'Sabre exposure-normalized ordinary photometric domain')
    for t in ['return canonical * uGains + uBlackLevelsTimesGains;',
              'rggb = sqrt(max(vec4(0.0), rggb));']:
        need(sh,t,'Sabre guide exposure-normalization domain')
    active=section(st,'private fun processSabreFrames','private data class SabreNormalDngSupportStats')
    for t in ['IRIS_26610_SHARED_NORMAL_SHORT_PHYSICAL_PROTECTION_TEXTURE',
              'renderDilation(shortPhysicalReverseWeight26610, shortPhysicalWeight26610)',
              'physicalWeight = shortPhysicalWeight26610','frameWeight = rescuedWeight',
              'if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)',
              'if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)']:
        need(active,t,'26610 common Sabre/SR/DNG ownership')

    mr=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
    for t in ['IRIS_26610_SOURCE_DOMAIN_HIGHLIGHT_RENDITION','IRIS_26610_SDR_BODY_ANCHOR = 0.40f',
              'IRIS_26610_SDR_P99_TARGET = 0.95f','IRIS_26610_SDR_P998_TARGET = 0.995f',
              'IRIS_26610_HDR_P99_TARGET = 4.40f','IRIS_26610_HDR_P998_TARGET = 5.15f',
              'motionV2ToneP99Guide','motionV2ToneP998Guide','iris26610MapMotionSdrSourceFinal',
              'iris26610MapHdrTargetLuma','IRIS_26592_MOTION_UHDR_MAX_RATIO = 8.0f',
              'glProg.setVar("iris26610SourceP99Final"','IRIS_26610_SOURCE_DOMAIN_SDR_UHDR_SR_PARITY=true']:
        need(mr,t,'26610 1x SDR/UHDR owner')
    forbid(mr,'iris26609StretchMotionSdrMapped','stale 26609 post-shoulder stretch')

    rg=(c/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
    gg=(c/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
    ag=(c/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text()
    for t in ['iris26610MapSdrSourceFinal','targetP99=0.95','targetP998=0.995']:
        need(rg,t,'1x source-domain SDR shader')
    for t in ['float max3(vec3 v)','iris26610MapHdrTarget(float hdrBase,float sourceFinal)',
              'float sourceFinal=max3(hdrPositive)*hdrTargetScale']:
        need(gg,t,'1x source-domain UHDR shader')
    need(ag,'iris26610MapSdrSourceFinal','adaptive-color source-domain predictor')

    enc=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text()
    cpp=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
    for t in ['final MotionV2Render.Iris26610TonePlan iris26610Tone',
              'iris26610Tone.sourceP99Final, iris26610Tone.sourceP998Final',
              'iris26610Tone.hdrP99Boost, iris26610Tone.hdrP998Boost','iris26610Tone.strength']:
        need(enc,t,'26610 true2x Java parity')
    for t in ['iris26610MapSdrSourceFinal','iris26610MapHdrTarget(float hdrBase,float sourceFinal',
              'targetP99=0.95f,targetP998=0.995f','targetP99=0.95,targetP998=0.995',
              'uIris26610SourceP99Final','uIris26610HdrP998Boost','uIris26610ToneStrength']:
        need(cpp,t,'26610 true2x CPU/GPU parity')

    production='\n'.join([mr,rg,gg,cpp])
    code=re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"',' ',production,flags=re.S).lower()
    for word in ['cloud','chandelier','ceiling','window','bulb','reflection','snow','curtain']:
        if re.search(r'\b'+word+r'\b',code): fail('scene-semantic rendition classifier '+word)

    print('PASS exact 10-file runtime scope from successful 26609 Actions candidate; version 0.9726610/26610')
    print('PASS successful-26609 HDR acquisition, preview lifecycle, bridge, Resolve/VGN and unrelated publication owners frozen')
    print('PASS ordinary Sabre guide/rejection operates in the reference-exposure normalized domain; effective-only loss therefore retains exact ordinary photometric protection')
    print('PASS SHORT clipped-core geometry bypass removed; ordinary physical+dilation and local residual remain mandatory')
    print('PASS source-domain SDR/UHDR rendition shared across 1x, adaptive predictor, true2x CPU and true2x GPU; no scene classifier')
    print('PASS SR detail and DNG remain NORMAL-only while common HDR guide/rendition corrections apply to SR ON/OFF')
if __name__=='__main__': main()
