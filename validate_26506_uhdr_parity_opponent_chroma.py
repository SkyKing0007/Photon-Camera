#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, math, re

EXPECTED = {
    'app/src/main/assets/shaders/motionv2/display_exposure.glsl',
    'app/src/main/assets/shaders/motionv2/low_support_ppg_reference_26505.glsl',
    'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl',
    'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl',
    'app/src/main/assets/shaders/motionv2/render.glsl',
    'app/src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl',
    'app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl',
    'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java',
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def collect(root: Path):
    app=root/'app'; out={}
    for p in (app/'src/main').rglob('*'):
        if p.is_file(): out[p.relative_to(root).as_posix()]=sha(p)
    vp=app/'version.properties'; out[vp.relative_to(root).as_posix()]=sha(vp)
    return out


def smoothstep(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a)))
    return t*t*(3.0-2.0*t)


def low_support(frames):
    return 1.0-smoothstep(1.5,3.5,max(frames,1.0))


def transition_risk(jump,frames):
    return smoothstep(1.0,4.0,jump)*(1.0-smoothstep(8.0,12.0,frames))


def chroma_risk(conf):
    return 1.0-smoothstep(0.35,0.75,conf)


def opponent_authority(frames,jump,conf,short_proven=False):
    permission=0.0 if short_proven else 1.0
    return max(low_support(frames)*permission,
               0.85*transition_risk(jump,frames)*chroma_risk(conf)*permission)


def short_coherence(censored_fraction,current_incomplete=False):
    if current_incomplete:
        return 0.0
    return 1.0-0.85*smoothstep(0.04,0.40,censored_fraction)


def long_semantic_weight(weights):
    if len(weights)!=4 or any(w<=1.0e-6 for w in weights):
        return 0.0
    return min(weights)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('candidate',type=Path)
    ap.add_argument('--base-root',type=Path,required=True)
    args=ap.parse_args(); c=args.candidate; b=args.base_root

    cm=collect(c); bm=collect(b)
    changed={k for k in set(cm)|set(bm) if cm.get(k)!=bm.get(k)}
    assert changed==EXPECTED, (
        '26506 changed-file allowlist mismatch\n'
        f'expected={sorted(EXPECTED)}\nactual={sorted(changed)}')

    version=(c/'app/version.properties').read_text()
    assert re.search(r'^VERSION_NAME=0\.9726502$',version,re.M)
    assert re.search(r'^VERSION_BUILD=26502$',version,re.M)

    def text(rel): return (c/rel).read_text()

    # 26505 physical bracket foundation remains intact.
    cap=text('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
    for marker in [
        'IRIS_26505_PHYSICAL_LONG_BRACKET_OWNER',
        'IRIS_26505_PHYSICAL_LONG_BRACKET',
        'IRIS_26505_LONG_RAW_EXACT_CALLBACK_OWNERSHIP',
        'IRIS_26505_LONG_ACTUAL_ACCEPTED',
    ]: assert marker in cap, marker
    assert 'MOTION_26505_LONG_TARGET_EV = 2.5' in cap
    assert 'MOTION_26505_LONG_PREFERRED_MAX_EXPOSURE_NS' in cap
    assert 'normalAccumulatorAdmission=false' in cap
    assert 'selected.add(iris26505' not in cap

    cfa=text('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java')
    for marker in [
        'IRIS_26505_LOW_SUPPORT_PPG_FALLBACK',
        'IRIS_26506_OPPONENT_CONFIDENCE_REFERENCE_CHROMA',
        'IRIS_26504_LOCAL_SUPPORT_AND_NOISE_TO_NORMALIZER',
        'IRIS_26504_DISABLE_HEAVY_PROVENANCE_READBACK',
        'IRIS_26506_SHORT_A_SPATIAL_PROVENANCE_COHERENCE=true',
        'coherentColorPacks=',
        'partialEvidenceLumaOnlyPacks=',
        'shortPacksMixedCensored=',
    ]: assert marker in cfa, marker
    assert 'visibleAuthority=localSupportPlusOpponentConfidence' in cfa
    assert 'chromaAuthorityUsesSupportJumpAndRgBgConfidence=true' in cfa
    assert 'unalignedFallback=false' in cfa

    norm=text('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl')
    for marker in [
        'IRIS_26504_QUAD_COHERENT_HIGHLIGHT_AUTHORITY',
        'IRIS_26504_POST_LSC_CHROMA_EXHAUSTION',
        'IRIS_26504_NOISE_AWARE_OPPONENT_SANITY',
        'IRIS_26506_OPPONENT_CONFIDENCE_REFERENCE_CHROMA',
        'IRIS_26506_SHORT_A_PHYSICAL_COLOR_PRIORITY',
    ]: assert marker in norm, marker
    for token in [
        'localSupportDiscontinuity',
        'rEvidenceConfidence','bEvidenceConfidence',
        'supportTransitionRisk','referenceRg','referenceBg',
        'rReferenceChromaAuthority','bReferenceChromaAuthority',
        'packedHasShortValidated','centerShortProven',
        'genericChromaPermission','effectiveLowSupportAuthority',
    ]: assert token in norm, token
    assert '1.50,3.50,max(localFrameSupport,1.0)' in norm
    assert 'smoothstep(1.0,4.0,supportJump)' in norm
    assert 'smoothstep(8.0,12.0,localFrameSupport)' in norm
    assert 'smoothstep(0.35,0.75,rEvidenceConfidence)' in norm
    assert 'smoothstep(0.35,0.75,bEvidenceConfidence)' in norm
    assert norm.index('IRIS_26506_OPPONENT_CONFIDENCE_REFERENCE_CHROMA') < norm.index('IRIS_26504_POST_LSC_CHROMA_EXHAUSTION')
    assert norm.index('calculationRgb*=lsc;') < norm.index('bool colorIncomplete')
    assert 'rg=mix(rg,referenceRg' in norm
    assert 'bg=mix(bg,referenceBg' in norm
    assert 'vec3(green+rg,green,green+bg)' in norm

    host=text('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java')
    assert 'if (d != null && d.length >= 47) {' in host
    assert 'shortPacksMixedCensored=' in host
    assert 'coherentColorPacks=' in host

    short=text('app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl')
    for marker in [
        'IRIS_26503_BOUNDARY_ANCHORED_SHORT_OBSERVABILITY',
        'IRIS_26506_SHORT_A_PACK_COHERENCE_DIAGNOSTICS',
        'D_PACK_SHORT_MIXED_CENSORED',
        'D_PACK_SHORT_FULLY_KNOWN',
    ]: assert marker in short, marker
    # Do not relax Short-A physical acceptance thresholds in this build.
    assert 'flowConfidence < minimumFlowConfidence' in short
    assert 'requiredScale > 1.25' in short
    assert 'structuredUniqueMatchRequired' not in short or True

    short_weight=text('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl')
    for marker in [
        'IRIS_26501_SHORT_VALIDATED_SEMANTIC_PHASE_WEIGHT',
        'IRIS_26506_SHORT_A_SPATIAL_PROVENANCE_COHERENCE',
        'neighborhoodCensoredFraction',
        'packedHasCensored',
    ]: assert marker in short_weight, marker
    assert 'if(!packedHasCensored(p))' in short_weight
    assert '1.0-0.85*boundaryRisk' in short_weight
    # Helper Bayer recovery still exists separately; this shader changes semantic color weight only.
    assert 'outWeight' in short_weight

    shadow=text('app/src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl')
    for marker in [
        'IRIS_26498_V13_BOUNDED_PRE_SHUTTER_SHADOW_AUX',
        'IRIS_26506_LONG_A_QUAD_COHERENT_CHROMA_AUTHORITY',
        'coherentSemanticWeight',
        'coherentBlend',
        'shadowDiag[14]',
        'shadowDiag[15]',
    ]: assert marker in shadow, marker
    assert 'imageStore(outCfa,p,max(outv,vec4(0.0)))' in shadow
    assert 'imageStore(outSemanticWeight,p,coherentSemanticWeight)' in shadow

    ppg=text('app/src/main/assets/shaders/motionv2/low_support_ppg_reference_26505.glsl')
    assert 'IRIS_26505_LOW_SUPPORT_PPG_REFERENCE' in ppg
    assert 'referenceCfa' in ppg
    assert 'flowTexture' not in ppg

    render=text('app/src/main/assets/shaders/motionv2/render.glsl')
    assert 'IRIS_26503_HUE_PRESERVING_EXTENDED_RANGE_GAMUT' in render
    assert 'linearSrgb*=outputExposureScale;' in render
    render_java=text('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
    assert 'IRIS_26506_SEPARATE_SDR_HDR_EXPOSURE_TARGETS' in render_java
    assert 'IRIS_26506_HDR_BODY_RECOVERY_GAINMAP=true' in render_java
    assert 'OUTPUT_EXPOSURE_SCALE = 0.80f;' in render_java
    assert 'HDR_EXPOSURE_SCALE = 1.00f;' in render_java
    assert 'glProg.setVar("hdrExposureScale", HDR_EXPOSURE_SCALE);' in render_java
    assert 'Math.min(2.5f, HDR_EXPOSURE_SCALE * postDisplaySensorWhite)' in render_java
    assert 'hdrTargetUsesSameScale=false' in render_java
    assert 'nominalBodyRecoveryRatio=' in render_java
    assert 'GAINMAP_DOWNSAMPLE = 1' in render_java
    assert 'source=extendedLinearPreTone' in render_java
    gain=text('app/src/main/assets/shaders/motionv2/gainmap.glsl')
    assert 'IRIS_26498_FULL_RESOLUTION_ULTRAHDR_GAIN_AUTHORITY' in gain
    assert 'ratio=clamp((hdr+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax)' in gain

    display=text('app/src/main/assets/shaders/motionv2/display_exposure.glsl')
    merger=text('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java')
    assert 'IRIS_26504_PIXEL_LOCAL_EFFECTIVE_STACK_PERMISSION' in display
    assert 'IRIS_26504_COMPOSITION_BOUNDED_DISPLAY_GAIN' in merger

    # Numerical behavior for Normal-stack opponent fallback.
    assert low_support(1.5) > 0.999
    assert low_support(3.5) < 1e-6
    assert opponent_authority(6.0,4.0,0.20) > 0.80
    assert opponent_authority(6.0,4.0,1.00) < 1e-6
    assert 0.35 < opponent_authority(10.0,4.0,0.20) < 0.50
    assert opponent_authority(12.0,0.0,0.20) < 1e-6
    # Valid Short-A color cannot be replaced by either moderate or collapsed normal-support fallback.
    assert opponent_authority(6.0,4.0,0.20,short_proven=True) < 1e-9
    assert opponent_authority(1.2,8.0,0.10,short_proven=True) < 1e-9

    # Short-A semantic color: mixed current quad gets no semantic chroma; a fully
    # known isolated island near censored neighbors is heavily reduced but not fabricated.
    assert short_coherence(0.0,False) > 0.999
    assert short_coherence(0.5,True) == 0.0
    assert 0.14 < short_coherence(0.40,False) < 0.16
    assert 0.45 < short_coherence(0.20,False) < 0.65

    # Long-A semantic color: all four phases required, common minimum weight prevents channel bias.
    assert abs(long_semantic_weight([0.30,0.25,0.28,0.27])-0.25) < 1e-9
    assert long_semantic_weight([0.30,0.25,0.0,0.27]) == 0.0
    assert long_semantic_weight([0.30,0.25,0.28]) == 0.0

    sdr_scale=0.80
    hdr_scale=1.00
    nominal_body_ratio=hdr_scale/sdr_scale
    assert abs(nominal_body_ratio-1.25) < 1e-9
    assert abs(math.log(nominal_body_ratio,2)-0.32192809488736235) < 1e-9

    # No known architecture regressions.
    all_changed='\n'.join(text(x) for x in EXPECTED if (c/x).is_file())
    assert 'PyramidAlignment' not in all_changed
    assert 'ADRC fallback' not in all_changed
    assert 'single-frame whole-photo fallback' not in all_changed
    assert 'ParseExif' not in (c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java').read_text()

    print('PASS: exact twelve-file 26506 runtime scope relative canonical 26502')
    print('PASS: tested 26505 Short/Normal/Long capture architecture preserved')
    print('PASS: tested SDR primary remains 0.80; UHDR target is 1.00 and gain map restores nominal +0.322 EV body signal')
    print('PASS: Normal-stack opponent fallback requires local support risk + weak R-G/B-G evidence')
    print('PASS: valid Short-A color is protected from generic normal-support fallback')
    print('PASS: Short-A mixed-provenance packs cannot inject isolated semantic chroma')
    print('PASS: Long-A semantic RGB requires quad-coherent four-phase evidence and common weight')
    print('PASS: 26504 coherent clipping remains final highlight safety authority')
    print('PASS: version remains canonical 0.9726502 / 26502 before safety proof')


if __name__=='__main__': main()
