#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys

CHANGED=[
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
 'app/version.properties',
]
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
    v=(c/'app/version.properties').read_text(); need(v,'VERSION_NAME=0.9726611','version'); need(v,'VERSION_BUILD=26611','version')

    # Successful 26610 acquisition, preview, publication/rendition, native SR, DNG and bridge stay frozen.
    frozen=[
      'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
      'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java',
      'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
      'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
      'app/src/main/assets/shaders/motionv2/render.glsl',
      'app/src/main/assets/shaders/motionv2/gainmap.glsl',
      'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
      'app/src/main/assets/shaders/motionv2/display_exposure.glsl',
      'app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl',
      'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
    ]
    for r in frozen:
        if (b/r).read_bytes()!=(c/r).read_bytes(): fail('successful-26610 frozen owner changed '+r)

    cc=(c/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
    for t in ['universalHdrExposureDecision=true','broadHdrConflict=','mixedHdrConflict=','compactHdrConflict=',
              'signal >= 0.980f','quadPhases >= 2']:
        need(cc,t,'26610 universal HDR acquisition inheritance')

    sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
    anchor=shader(sh,'shortComponentAnchor26607'); propagate=shader(sh,'shortComponentPropagate26607'); rescue=shader(sh,'shortRescueWeight26607'); rejection=shader(sh,'rejection')
    for t in ['layout(location = 2) out float oPhysicalReverseWeight;',
              'oPhysicalReverseWeight = clamp(unblocker, 0.0, 1.0);']:
        need(rejection,t,'common ordinary-rejection physical output')
    for t in [
        'IRIS_26611_SAME_CFA_MEASURABLE_BOUNDARY_SEED',
        '1.0 - smoothstep(0.35, 0.95, max(flow.w, 0.0));',
        'if (literalPhasesHere >= 2) literalLossSeen = 1.0;',
        'IRIS_26611_CLIPPED_INTERIOR_CANNOT_SELF_SEED',
        'componentSourceConfidence, literalLossSeen',
        'anchorQuadEvidence >= 4 && anchorPhaseEvidence >= 8',
        'float relativeError = abs(ns - nr) / max(max(nr, ns), 0.05);',
    ]: need(anchor,t,'26611 same-CFA boundary seed')
    for t in ['IRIS_26611_CFA_PHASE_SAFE_COMPONENT_PROPAGATION','smoothstep(0.50, 1.25, delta)']:
        need(propagate,t,'26611 clipped-interior propagation')
    forbid(anchor,'0.85 * literalLossSeen','literal clipping self-seed')
    forbid(anchor,'smoothstep(2.0, 8.0, max(flow.w, 0.0))','old loose boundary residual')
    forbid(propagate,'smoothstep(4.0, 16.0, delta)','old loose component flow barrier')

    for t in [
        'IRIS_26611_BOUNDARY_PROVEN_SHORT_RESCUE_ONLY',
        'float rescueConfidence = min(shortHeadroom, componentTrust);',
        'IRIS_26611_SHORT_COMPLETE_COMMON_PHYSICAL_CAP',
        'float censoredCoreWeight = min(physicalWeight, rescueConfidence);',
        'IRIS_26610_TWO_PHASE_PHYSICAL_CENSORSHIP_ONLY',
        'if (secondHighest4(referenceRaw) < uSourceClippingPoint) return 0.0;',
        'float physicalCensoring = clamp(literalLoss, 0.0, 1.0);',
        'float finalWeight = mix(ordinaryWeight, censoredCoreWeight, physicalCensoring);',
        'oRescueOnlyWeight = clamp(max(finalWeight - ordinaryWeight, 0.0), 0.0, 1.0);',
    ]: need(rescue,t,'26611 boundary-proven SHORT rescue')
    for stale in ['mix(localResidualConfidence, 1.0, literalCore)','mix(ordinaryWeight, rescueConfidence, targetLoss)',
                  'mix(ordinaryWeight, censoredCoreWeight, targetLoss)','sharedPhysicalProtection = min(physicalWeight, localResidualConfidence)',
                  '1.0 - smoothstep(2.0, 8.0, max(flow.w, 0.0));']:
        forbid(rescue,stale,'old SHORT rescue bypass')

    # VGN direction and cleanup authority.
    hdr_dir=shader(sh,'outputTransformHdrDirectionUint16'); restore=shader(sh,'restoreExtendedHdrAfterVgn')
    for t in ['IRIS_26611_HDR_INDEPENDENT_VGN_COLOR_DIRECTION','float magnitude = max(max3(physical), 1.0);',
              'vec3 directionDomain = clamp(physical / magnitude, 0.0, 1.0);']:
        need(sh,t,'26611 HDR-independent VGN input owner')
    for t in ['float magnitude = max(max3(physical), 1.0);','physical / magnitude']:
        need(hdr_dir,t,'HDR-direction shader')
    for t in ['IRIS_26611_CLEAN_DIRECTION_SCALAR_HDR_RESTORE','float physicalMagnitude = max3(physical);',
              'float cleanedMagnitude = max3(cleaned);','cleaned / cleanedMagnitude',
              'restored = cleanedDirection * physicalMagnitude;']:
        need(sh,t,'26611 clean HDR restore')
    for stale in ['physical + (vgn - normalizedProxy)','vec3 normalizedProxy = clamp(physical, 0.0, 1.0);']:
        forbid(restore,stale,'dirty per-channel HDR resurrection')

    vgn=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text()
    ua=shader(vgn,'universalAdaptiveColor26561')
    for t in ['IRIS_26611_DECISIVE_NEUTRAL_CFA_FALSE_COLOR_OWNER','float decisiveNeutralCfaProof =',
              'smoothstep(0.92, 0.985, falseColorScore)','smoothstep(0.88, 0.985, phaseLikeEvidence)',
              'smoothstep(0.90, 0.995, targetNeutral)','float legacyMaximumMove = min(0.050, 0.40 * centerMagnitude);',
              'float maximumMove = mix(legacyMaximumMove, desiredLength, decisiveNeutralCfaProof);']:
        need(ua,t,'26611 decisive neutral CFA cleanup')
    # Real-color topology remains in the score before the decisive path.
    for t in ['float realColorConfidence =','(1.0 - realColorConfidence);','microObjectProtection','topologyProtection']:
        need(ua,t,'real-color preservation veto')

    st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
    active=section(st,'private fun processSabreFrames','private data class SabreNormalDngSupportStats')
    for t in ['GlesMgcRawSabreShaders.outputTransformHdrDirectionUint16',
              'iris_26611_sabre_output_transform_clean_direction_pre_vgn',
              '26611 clean-direction scalar HDR restoration',
              'literalCoreSelfSeed=false effectiveLossPhotometricBypass=false',
              'boundaryResidualRawPx=0.35..0.95','componentFlowBarrierRawPx=0.50..1.25',
              'renderDilation(shortPhysicalReverseWeight26610, shortPhysicalWeight26610)',
              'physicalWeight = shortPhysicalWeight26610','frameWeight = rescuedWeight',
              'if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)',
              'if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)']:
        need(st,t,'26611 active one-tunnel ownership')
    forbid(st,'literalCoreTwoPhaseClipBypass=true','stale device telemetry')

    # Exact successful 26610 rendition remains frozen and authoritative downstream.
    mr=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
    for t in ['IRIS_26610_SOURCE_DOMAIN_HIGHLIGHT_RENDITION','IRIS_26610_SDR_BODY_ANCHOR = 0.40f',
              'IRIS_26610_SDR_P99_TARGET = 0.95f','IRIS_26610_SDR_P998_TARGET = 0.995f',
              'IRIS_26610_HDR_P99_TARGET = 4.40f','IRIS_26610_HDR_P998_TARGET = 5.15f',
              'IRIS_26592_MOTION_UHDR_MAX_RATIO = 8.0f']:
        need(mr,t,'26610 rendition inheritance')

    # No scene semantic classifier introduced by the 26611 runtime changes.
    production='\n'.join([sh,vgn,st])
    code=re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"',' ',production,flags=re.S).lower()
    for word in ['cloud','chandelier','ceiling','window','bulb','reflection','snow','curtain']:
        if re.search(r'\b'+word+r'\b',code): fail('scene-semantic runtime classifier '+word)

    print('PASS exact 4-file runtime scope from successful 26610 Actions compiled candidate; version 0.9726611/26611')
    print('PASS successful-26610 acquisition/preview/rendition/UHDR/SR/DNG owners frozen byte-identical')
    print('PASS SHORT trust can seed only from sub-pixel same-CFA measurable-boundary radiometry; two-phase clipped interior cannot self-seed')
    print('PASS propagated SHORT trust cannot cross CFA-meaningful neighbor-flow discontinuity; effective/sub-clipping loss keeps ordinary NORMAL weight')
    print('PASS VGN consumes scalar-normalized HDR color direction; decisive neutral CFA proof can fully remove strong supported fringe while real-color topology remains veto')
    print('PASS post-VGN extended HDR restores only one scalar physical max-RGB magnitude onto the cleaned RGB direction; dirty per-channel RGB resurrection absent')
    print('PASS exact 26610 source-domain SDR/UHDR/SR rendition math inherited unchanged')
if __name__=='__main__': main()
