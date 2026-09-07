#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
PKG=Path(__file__).resolve().parent
CHANGED=[x for x in (PKG/'V1_26609_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
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
    v=(c/'app/version.properties').read_text(); need(v,'VERSION_NAME=0.9726609','version'); need(v,'VERSION_BUILD=26609','version')

    # Successful 26608 acquisition + preview lifecycle are explicitly frozen in 26609.
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
        if (b/r).read_bytes()!=(c/r).read_bytes(): fail('successful-26608 frozen owner changed '+r)

    # SHORT acquisition invariance: the exact 26608 trigger strings must survive unchanged because CaptureController is frozen.
    cc=(c/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
    for t in ['universalHdrExposureDecision=true','broadHdrConflict=','mixedHdrConflict=','compactHdrConflict=',
              'signal >= 0.980f','quadPhases >= 2']:
        need(cc,t,'26608 universal HDR acquisition inheritance')

    # SHORT protection parity: only photometric reference agreement may relax in proven censored core.
    sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
    rescue=shader(sh,'shortRescueWeight26607'); rejection=shader(sh,'rejection')
    for t in ['layout(location = 2) out float oPhysicalReverseWeight;',
              'oPhysicalReverseWeight = clamp(unblocker, 0.0, 1.0);']:
        need(rejection,t,'26609 common physical rejection output')
    for t in ['uniform sampler2D uPhysicalWeight;',
              'float physicalWeight = texture(uPhysicalWeight, referenceUv).r;',
              'float censoredCoreWeight = min(physicalWeight, rescueConfidence);',
              'float finalWeight = mix(ordinaryWeight, censoredCoreWeight, targetLoss);',
              'oRescueOnlyWeight = clamp(censoredCoreWeight * targetLoss, 0.0, 1.0);']:
        need(rescue,t,'26609 SHORT protection parity')
    forbid(rescue,'mix(ordinaryWeight, rescueConfidence, targetLoss)','unprotected 26608 rescue replacement')
    need(rescue,'float localGeometry = mix(localResidualConfidence, 1.0, literalCore);','censored-core geometry exception')
    need(rescue,'shortHeadroom, min(componentTrust, localGeometry)','SHORT geometry/headroom contract')

    st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
    active=section(st,'private fun processSabreFrames','private data class SabreNormalDngSupportStats')
    for t in ['IRIS_26609_SHARED_NORMAL_SHORT_PHYSICAL_PROTECTION_TEXTURE',
              'renderDilation(shortPhysicalReverseWeight26609, shortPhysicalWeight26609)',
              'physicalWeight = shortPhysicalWeight26609',
              'frameWeight = rescuedWeight',
              'if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)',
              'if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)']:
        need(active,t,'26609 common Sabre/SR/DNG ownership')
    # No private or late SHORT compositor may be revived.
    for t in ['sabreShortBoundaryAnchorProgram26606 = 0','sabreShortBoundaryPropagateProgram26606 = 0',
              'sabreShortRescueWeightProgram26606 = 0','sabreShortProtectedAccumulatorFuseProgram26602 = 0',
              'sabreShortRestoreRgba16fProgram26587 = 0']:
        need(st,t,'dormant legacy SHORT owner')

    # 1x SDR/UHDR sample-calibrated Iris rendition. Photon samples are visual references only.
    mr=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
    for t in ['IRIS_26609_SDR_P99_TARGET = 0.88f','IRIS_26609_SDR_P998_TARGET = 0.995f',
              'IRIS_26609_HDR_P99_BOOST = 1.35f','IRIS_26609_HDR_P998_BOOST = 2.40f',
              'motionV2ToneP99Guide','motionV2ToneP998Guide','motionV2ToneAdaptiveStrength',
              'iris26609StretchMotionSdrMapped','iris26609MapHdrTargetLuma',
              'IRIS_26592_MOTION_UHDR_MAX_RATIO = 8.0f',
              'glProg.setVar("iris26609HdrP99Final"','IRIS_26609_SDR_UHDR_SR_RENDITION_PARITY=true']:
        need(mr,t,'26609 1x SDR/UHDR owner')
    # Never add semantic scene classifiers to production rendition owners.
    production='\n'.join([
      mr,
      (c/'app/src/main/assets/shaders/motionv2/render.glsl').read_text(),
      (c/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text(),
      (c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text(),
    ])
    code=re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"',' ',production,flags=re.S).lower()
    for word in ['cloud','chandelier','ceiling','window','bulb','reflection','snow','curtain']:
        if re.search(r'\b'+word+r'\b',code): fail('scene-semantic rendition classifier '+word)

    # SR path must receive exact same derived tone plan and regenerate its own base+gain with those anchors.
    enc=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text()
    cpp=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
    for t in ['final MotionV2Render.Iris26609TonePlan iris26609Tone',
              'iris26609Tone.oldP99Mapped, iris26609Tone.oldP998Mapped',
              'iris26609Tone.hdrP99Final, iris26609Tone.hdrP998Final',
              'iris26609Tone.strength']:
        need(enc,t,'26609 true2x Java parity')
    for t in ['targetP99=0.88f,targetP998=0.995f','1.35f+t*(2.40f-1.35f)',
              'targetP99=0.88,targetP998=0.995','boost=mix(1.35,2.40,t)',
              'uIris26609OldP99Mapped','uIris26609HdrP998Final','uIris26609ToneStrength']:
        need(cpp,t,'26609 true2x CPU/GPU parity')

    # DNG and SR-detail ownership remain unchanged: SHORT contributes to common guide/reconstruction, not detail/DNG source roles.
    need(active,'if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)','SR detail NORMAL-only ownership')
    need(active,'if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)','DNG NORMAL-only ownership')

    print('PASS exact 10-file runtime scope from successful 26608 V1 authority; version 0.9726609/26609')
    print('PASS successful-26608 universal HDR SHORT acquisition + preview lifecycle frozen byte-identical')
    print('PASS SHORT protection parity: physical/unblocker+dilation cap survives targetLoss=1; only censored-reference photometric agreement can relax')
    print('PASS 1x SDR + UHDR and true2x CPU/GPU publication share one sample-calibrated Iris rendition plan; no scene classifier')
    print('PASS SR detail and DNG role ownership preserved')
if __name__=='__main__': main()
