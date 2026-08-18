#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse

ROOT: Path


def fail(msg: str):
    raise SystemExit('ERROR: ' + msg)


def one(src: str, old: str, new: str, label: str) -> str:
    n = src.count(old)
    if n != 1:
        fail(f'{label}: expected one anchor, found {n}')
    return src.replace(old, new, 1)


def edit(rel: str, fn):
    p = ROOT / rel
    if not p.is_file():
        fail(f'missing {rel}')
    before = p.read_text()
    after = fn(before)
    if after == before:
        fail(f'{rel}: transform made no change')
    p.write_text(after)
    print('CHANGED', rel)


def motion_render_java(src: str) -> str:
    if 'IRIS_26506_SEPARATE_SDR_HDR_EXPOSURE_TARGETS' in src:
        fail('MotionV2Render already contains 26506')
    if 'private static final float OUTPUT_EXPOSURE_SCALE = 0.80f;' not in src:
        fail('expected tested 26505 SDR primary exposure scale 0.80')
    src = one(
        src,
        '    private static final float OUTPUT_EXPOSURE_SCALE = 0.80f;\n',
        '''    private static final float OUTPUT_EXPOSURE_SCALE = 0.80f;
    /* IRIS_26506_SEPARATE_SDR_HDR_EXPOSURE_TARGETS
     * Preserve the tested 26505 SDR primary exactly. Ultra HDR is a reversible
     * rendition relationship: the gain map should recover the wanted HDR signal
     * from that SDR primary rather than inheriting the SDR headroom reduction.
     * 1.00 / 0.80 = 1.25 (+0.322 EV) nominal body recovery at full HDR where
     * tone mapping is otherwise identity. Highlight gain remains content-derived.
     */
    private static final float HDR_EXPOSURE_SCALE = 1.00f;
''',
        'separate SDR/HDR exposure targets')
    src = one(
        src,
        '                    Math.min(2.5f, OUTPUT_EXPOSURE_SCALE * postDisplaySensorWhite));\n',
        '                    Math.min(2.5f, HDR_EXPOSURE_SCALE * postDisplaySensorWhite));\n',
        'HDR max gain target uses HDR scale')
    src = one(
        src,
        '                glProg.setVar("hdrExposureScale", OUTPUT_EXPOSURE_SCALE);\n',
        '                glProg.setVar("hdrExposureScale", HDR_EXPOSURE_SCALE);\n',
        'gain map receives independent HDR target scale')
    src = one(
        src,
        '                        + " sdrAndHdrExposureScale=" + OUTPUT_EXPOSURE_SCALE);\n',
        '                        + " sdrExposureScale=" + OUTPUT_EXPOSURE_SCALE\n'
        '                        + " hdrTargetExposureScale=" + HDR_EXPOSURE_SCALE\n'
        '                        + " nominalBodyRecoveryRatio="\n'
        '                            + (HDR_EXPOSURE_SCALE / OUTPUT_EXPOSURE_SCALE)\n'
        '                        + " IRIS_26506_HDR_BODY_RECOVERY_GAINMAP=true");\n',
        'gainmap telemetry separate targets')
    src = one(
        src,
        '                + " hdrTargetUsesSameScale=true"\n',
        '                + " hdrTargetUsesSameScale=false"\n'
        '                + " hdrTargetExposureScale=" + HDR_EXPOSURE_SCALE\n'
        '                + " nominalHdrBodyRecoveryRatio="\n'
        '                    + (HDR_EXPOSURE_SCALE / OUTPUT_EXPOSURE_SCALE)\n'
        '                + " IRIS_26506_SEPARATE_SDR_HDR_EXPOSURE_TARGETS=true"\n',
        'render telemetry HDR target separation')
    return src

def normalizer(src: str) -> str:
    if 'IRIS_26505_LOW_SUPPORT_RECONSTRUCTION_AUTHORITY' not in src:
        fail('26506 normalizer requires applied 26505 candidate')
    if 'IRIS_26506_OPPONENT_CONFIDENCE_REFERENCE_CHROMA' in src:
        fail('normalizer already contains 26506')

    src = one(
        src,
        '''bool packedHasCensored(ivec2 packedP){
    for(int q=0;q<4;++q){
        if(abs(phaseState(packedP,q)-1.0)<0.25)return true;
    }
    return false;
}
''',
        '''bool packedHasCensored(ivec2 packedP){
    for(int q=0;q<4;++q){
        if(abs(phaseState(packedP,q)-1.0)<0.25)return true;
    }
    return false;
}
bool packedHasShortValidated(ivec2 packedP){
    for(int q=0;q<4;++q){
        if(abs(phaseState(packedP,q)-2.0)<0.25)return true;
    }
    return false;
}
''',
        'short provenance helper')

    src = one(
        src,
        '''float localEvidenceQuality(float neighborWeightSum){
    return smoothstep(0.25,1.75,neighborWeightSum);
}
''',
        '''float localEvidenceQuality(float neighborWeightSum){
    return smoothstep(0.25,1.75,neighborWeightSum);
}
float frameSupportAt(ivec2 q){
    q=clamp(q,ivec2(0),rawSize-ivec2(1));
    return max(texelFetch(frameSupportTexture,q,0).r,1.0);
}
float localSupportDiscontinuity(ivec2 p,float centerSupport){
    float jump=0.0;
    jump=max(jump,abs(frameSupportAt(p+ivec2(-1, 0))-centerSupport));
    jump=max(jump,abs(frameSupportAt(p+ivec2( 1, 0))-centerSupport));
    jump=max(jump,abs(frameSupportAt(p+ivec2( 0,-1))-centerSupport));
    jump=max(jump,abs(frameSupportAt(p+ivec2( 0, 1))-centerSupport));
    jump=max(jump,abs(frameSupportAt(p+ivec2(-1,-1))-centerSupport));
    jump=max(jump,abs(frameSupportAt(p+ivec2( 1,-1))-centerSupport));
    jump=max(jump,abs(frameSupportAt(p+ivec2(-1, 1))-centerSupport));
    jump=max(jump,abs(frameSupportAt(p+ivec2( 1, 1))-centerSupport));
    return jump;
}
''',
        'support discontinuity helper')

    src = one(
        src,
        '''    float rShadowBlend=darkGate*mix(0.70,0.38,centerQr)
            *opponentAgreement(centerRg,localRg,green,centerQr)*localQr;
    float bShadowBlend=darkGate*mix(0.70,0.38,centerQb)
            *opponentAgreement(centerBg,localBg,green,centerQb)*localQb;
''',
        '''    float rAgreement=opponentAgreement(centerRg,localRg,green,centerQr);
    float bAgreement=opponentAgreement(centerBg,localBg,green,centerQb);
    float rShadowBlend=darkGate*mix(0.70,0.38,centerQr)
            *rAgreement*localQr;
    float bShadowBlend=darkGate*mix(0.70,0.38,centerQb)
            *bAgreement*localQb;
''',
        'reuse opponent agreement')

    old = '''    vec3 calculationRgb=max(
            vec3(green+rg,green,green+bg),vec3(0.0));

    /* IRIS_26505_LOW_SUPPORT_RECONSTRUCTION_AUTHORITY
     * The windy-foliage failure has high global support but local pockets near
     * one effective frame. In those pixels only, prefer an edge-directed RGB
     * observation reconstructed from the immutable reference CFA. At >=3.5
     * effective frames the current multiframe semantic RGB remains untouched.
     */
    vec3 lowSupportReference=max(
            texelFetch(lowSupportReferenceRgb,p,0).rgb,vec3(0.0));
    float lowSupportAuthority=1.0-smoothstep(
            1.50,3.50,max(localFrameSupport,1.0));
    calculationRgb=mix(
            calculationRgb,lowSupportReference,clamp(lowSupportAuthority,0.0,1.0));

    /* IRIS_26504_POST_LSC_CHROMA_EXHAUSTION */
'''
    new = '''    /* IRIS_26506_OPPONENT_CONFIDENCE_REFERENCE_CHROMA
     * Nominal frame count is not color confidence: windy foliage can retain
     * several effective frames while accepted frames disagree in R-G/B-G. Keep
     * temporal green/luminance detail and replace only an unreliable opponent
     * channel with the deterministic immutable-reference CFA reconstruction.
     */
    vec3 lowSupportReference=max(
            texelFetch(lowSupportReferenceRgb,p,0).rgb,vec3(0.0));
    float referenceRg=lowSupportReference.r-lowSupportReference.g;
    float referenceBg=lowSupportReference.b-lowSupportReference.g;
    float lowSupportAuthority=1.0-smoothstep(
            1.50,3.50,max(localFrameSupport,1.0));

    float supportJump=localSupportDiscontinuity(p,localFrameSupport);
    float supportTransitionRisk=smoothstep(1.0,4.0,supportJump)
            *(1.0-smoothstep(8.0,12.0,localFrameSupport));
    float rEvidenceConfidence=clamp(
            centerQr*mix(0.55,1.0,localQr)*rAgreement,0.0,1.0);
    float bEvidenceConfidence=clamp(
            centerQb*mix(0.55,1.0,localQb)*bAgreement,0.0,1.0);
    float rChromaRisk=1.0-smoothstep(0.35,0.75,rEvidenceConfidence);
    float bChromaRisk=1.0-smoothstep(0.35,0.75,bEvidenceConfidence);

    ivec2 parentPacked=clamp(p/2,ivec2(0),packedSize-ivec2(1));
    bool centerShortProven=packedHasShortValidated(parentPacked)
            && !packedHasCensored(parentPacked);
    /* IRIS_26506_SHORT_A_PHYSICAL_COLOR_PRIORITY
     * A fully measured NORMAL/SHORT_VALIDATED quad is real sensor color. Do not
     * let the generic windy-foliage fallback override it. Mixed/censored Short-A
     * boundaries are handled by the dedicated Short semantic-coherence rule and
     * the 26504 post-LSC neutral exhaustion below.
     */
    float genericChromaPermission=centerShortProven?0.0:1.0;
    float effectiveLowSupportAuthority=lowSupportAuthority*genericChromaPermission;
    float rReferenceChromaAuthority=max(
            effectiveLowSupportAuthority,
            0.85*supportTransitionRisk*rChromaRisk*genericChromaPermission);
    float bReferenceChromaAuthority=max(
            effectiveLowSupportAuthority,
            0.85*supportTransitionRisk*bChromaRisk*genericChromaPermission);
    rg=mix(rg,referenceRg,clamp(rReferenceChromaAuthority,0.0,1.0));
    bg=mix(bg,referenceBg,clamp(bReferenceChromaAuthority,0.0,1.0));

    vec3 calculationRgb=max(
            vec3(green+rg,green,green+bg),vec3(0.0));
    calculationRgb=mix(
            calculationRgb,lowSupportReference,
            clamp(effectiveLowSupportAuthority,0.0,1.0));

    /* IRIS_26504_POST_LSC_CHROMA_EXHAUSTION */
'''
    src = one(src, old, new, 'opponent-confidence selective reference chroma')
    src = one(
        src,
        '    ivec2 parentPacked=clamp(p/2,ivec2(0),packedSize-ivec2(1));\n'
        '    bool expandedIncomplete=expandedCensoredDecision(parentPacked);\n',
        '    bool expandedIncomplete=expandedCensoredDecision(parentPacked);\n',
        'reuse parent packed provenance owner')
    return src


def short_recovery(src: str) -> str:
    if 'IRIS_26503_BOUNDARY_ANCHORED_SHORT_OBSERVABILITY' not in src:
        fail('Short-A shader missing proven 26503 boundary observability')
    if 'IRIS_26506_SHORT_A_PACK_COHERENCE_DIAGNOSTICS' in src:
        fail('Short-A shader already contains 26506')
    src = one(
        src,
        'const uint D_PHASE_STILL_CENSORED = 40u;\n',
        '''const uint D_PHASE_STILL_CENSORED = 40u;
/* IRIS_26506_SHORT_A_PACK_COHERENCE_DIAGNOSTICS */
const uint D_PACK_SHORT_ANY = 44u;
const uint D_PACK_SHORT_MIXED_CENSORED = 45u;
const uint D_PACK_SHORT_FULLY_KNOWN = 46u;
''',
        'Short-A pack diagnostic indices')
    src = one(
        src,
        '''    addMask(D_VALIDATED, D_PHASE_VALIDATED, recoverMask);
    if (sum4(shortClippedMask) > 0.5) {
''',
        '''    addMask(D_VALIDATED, D_PHASE_VALIDATED, recoverMask);
    /* IRIS_26506_SHORT_A_PACK_COHERENCE_DIAGNOSTICS
     * Track whether recovered Short-A color forms a fully measured quad or a
     * mixed SHORT_VALIDATED/CENSORED boundary. Image math is unchanged here;
     * the semantic-weight shader below consumes this provenance spatially.
     */
    float validatedCount=0.0;
    float censoredCount=0.0;
    for(int i=0;i<4;++i){
        if(abs(state[i]-PROVENANCE_SHORT_VALIDATED)<0.25)validatedCount+=1.0;
        if(abs(state[i]-PROVENANCE_CENSORED)<0.25)censoredCount+=1.0;
    }
    if(validatedCount>0.5){
        atomicAdd(shortDiag[D_PACK_SHORT_ANY],1u);
        if(censoredCount>0.5)atomicAdd(shortDiag[D_PACK_SHORT_MIXED_CENSORED],1u);
        else atomicAdd(shortDiag[D_PACK_SHORT_FULLY_KNOWN],1u);
    }
    if (sum4(shortClippedMask) > 0.5) {
''',
        'Short-A pack diagnostic accounting')
    return src


def short_weight(src: str) -> str:
    if 'IRIS_26501_SHORT_VALIDATED_SEMANTIC_PHASE_WEIGHT' not in src:
        fail('Short semantic weight shader is not tested 26505 input')
    if 'IRIS_26506_SHORT_A_SPATIAL_PROVENANCE_COHERENCE' in src:
        fail('Short semantic weight shader already contains 26506')
    old = '''float phaseDivisor(int q){return q==0?1.0:(q==1?3.0:(q==2?9.0:27.0));}
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(p,packedSize)))return;
    float code=texelFetch(highlightProvenance,p,0).r;
    vec4 weight=vec4(0.0);
    for(int q=0;q<4;++q){
        float state=mod(floor(code/phaseDivisor(q)),3.0);
        weight[q]=abs(state-2.0)<0.25?1.0:0.0;
    }
    imageStore(outWeight,p,weight);
}
'''
    new = '''float phaseDivisor(int q){return q==0?1.0:(q==1?3.0:(q==2?9.0:27.0));}
float phaseState(ivec2 p,int q){
    p=clamp(p,ivec2(0),packedSize-ivec2(1));
    float code=texelFetch(highlightProvenance,p,0).r;
    return mod(floor(code/phaseDivisor(q)),3.0);
}
bool packedHasCensored(ivec2 p){
    for(int q=0;q<4;++q)if(abs(phaseState(p,q)-1.0)<0.25)return true;
    return false;
}
float neighborhoodCensoredFraction(ivec2 p){
    float censored=0.0,total=0.0;
    for(int oy=-2;oy<=2;++oy){
        for(int ox=-2;ox<=2;++ox){
            ivec2 q=p+ivec2(ox,oy);
            if(any(lessThan(q,ivec2(0)))||any(greaterThanEqual(q,packedSize)))continue;
            total+=1.0;
            if(packedHasCensored(q))censored+=1.0;
        }
    }
    return total>0.0?censored/total:1.0;
}
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(p,packedSize)))return;
    float code=texelFetch(highlightProvenance,p,0).r;
    vec4 weight=vec4(0.0);

    /* IRIS_26506_SHORT_A_SPATIAL_PROVENANCE_COHERENCE
     * A partially measured quad may still use Short-A in the helper Bayer to
     * preserve real luminance/headroom, but it cannot inject isolated RGB/chroma
     * into the semantic accumulator. Fully measured quads retain Short-A color,
     * smoothly reduced only when surrounded by unresolved clipped neighbors.
     * This converts dotted SHORT_VALIDATED/CENSORED islands into coherent color
     * transitions without globally relaxing correspondence or inventing detail.
     */
    if(!packedHasCensored(p)){
        float boundaryRisk=smoothstep(
                0.04,0.40,neighborhoodCensoredFraction(p));
        float coherence=1.0-0.85*boundaryRisk;
        for(int q=0;q<4;++q){
            float state=mod(floor(code/phaseDivisor(q)),3.0);
            weight[q]=abs(state-2.0)<0.25?coherence:0.0;
        }
    }
    imageStore(outWeight,p,weight);
}
'''
    return one(src, old, new, 'Short-A spatial provenance coherence')


def shadow_fuse(src: str) -> str:
    if 'IRIS_26498_V13_BOUNDED_PRE_SHUTTER_SHADOW_AUX' not in src:
        fail('shadow auxiliary shader is not expected tested input')
    if 'IRIS_26506_LONG_A_QUAD_COHERENT_CHROMA_AUTHORITY' in src:
        fail('shadow auxiliary shader already contains 26506')
    old = '''    if(any)atomicAdd(shadowDiag[13],1u);
    imageStore(outCfa,p,max(outv,vec4(0.0)));
    /* IRIS_26501_SHADOW_VALIDATED_SEMANTIC_WEIGHT
     * Reuse the exact reference-owned correspondence/SNR decision phase by phase as
     * the native shadow RAW semantic authority. One accepted phase never authorizes another.
     * The helper CFA is never color input. */
    imageStore(outSemanticWeight,p,semanticPhaseWeight);
}
'''
    new = '''    if(any)atomicAdd(shadowDiag[13],1u);
    imageStore(outCfa,p,max(outv,vec4(0.0)));

    /* IRIS_26506_LONG_A_QUAD_COHERENT_CHROMA_AUTHORITY
     * The +EV auxiliary may improve physical shadow luminance phase-by-phase in
     * outCfa, but ordinary RGB/chroma authority is stricter. Moving foliage can
     * pass one Bayer phase and fail another; feeding those unequal phase weights
     * into semantic RGB creates magenta/cyan clumps. Grant Long-A semantic color
     * only when all four phases have valid evidence, and use one common minimum
     * blend so the exposure cannot bias R/G/B differently. Partial evidence is
     * retained only as bounded helper-Bayer luminance/fallback evidence.
     */
    vec4 accepted=step(vec4(1.0e-6),semanticPhaseWeight);
    float acceptedCount=sum4(accepted);
    float coherentBlend=min(
            min(semanticPhaseWeight.r,semanticPhaseWeight.g),
            min(semanticPhaseWeight.b,semanticPhaseWeight.a));
    vec4 coherentSemanticWeight=vec4(0.0);
    if(acceptedCount>3.5&&coherentBlend>0.0){
        coherentSemanticWeight=vec4(coherentBlend);
        atomicAdd(shadowDiag[14],1u);
    }else if(any){
        atomicAdd(shadowDiag[15],1u);
    }
    imageStore(outSemanticWeight,p,coherentSemanticWeight);
}
'''
    return one(src, old, new, 'Long-A quad-coherent semantic color')


def cfa_host(src: str) -> str:
    if 'IRIS_26505_LOW_SUPPORT_PPG_FALLBACK' not in src:
        fail('26506 CFA host requires applied 26505 candidate')
    if 'IRIS_26506_OPPONENT_CONFIDENCE_REFERENCE_CHROMA' in src:
        fail('CFA host already contains 26506')
    src = one(
        src,
        '                     * support and grants this texture authority only below the 1.5..3.5-frame\n'
        '                     * transition. The immutable Wronski reference owns all source pixels.\n',
        '                     * support plus per-opponent confidence/support continuity decide authority.\n'
        '                     * The immutable Wronski reference owns all source pixels.\n',
        'CFA fallback authority comment')
    src = one(
        src,
        '                            +" visibleAuthorityLocalSupportOnly=true"\n'
        '                            +" fullAuthorityAtFramesLe=1.5"\n'
        '                            +" zeroAuthorityAtFramesGe=3.5"\n',
        '                            +" visibleAuthority=localSupportPlusOpponentConfidence"\n'
        '                            +" fullRgbAuthorityAtFramesLe=1.5"\n'
        '                            +" chromaAuthorityUsesSupportJumpAndRgBgConfidence=true"\n'
        '                            +" IRIS_26506_OPPONENT_CONFIDENCE_REFERENCE_CHROMA=true"\n',
        'CFA fallback telemetry')
    src = one(
        src,
        '                                    +" supportGt4="+Integer.toUnsignedLong(sd[12])+" packsWithFusion="+Integer.toUnsignedLong(sd[13])\n'
        '                                    +" fusedByPhase="+java.util.Arrays.toString(java.util.Arrays.copyOfRange(sd,16,20))\n',
        '                                    +" supportGt4="+Integer.toUnsignedLong(sd[12])+" packsWithFusion="+Integer.toUnsignedLong(sd[13])\n'
        '                                    +" coherentColorPacks="+Integer.toUnsignedLong(sd[14])\n'
        '                                    +" partialEvidenceLumaOnlyPacks="+Integer.toUnsignedLong(sd[15])\n'
        '                                    +" fusedByPhase="+java.util.Arrays.toString(java.util.Arrays.copyOfRange(sd,16,20))\n',
        'Long-A coherence diagnostics')
    src = one(
        src,
        '                        if (d != null && d.length >= 44) {',
        '                        if (d != null && d.length >= 47) {',
        'Short-A coherence diagnostic length guard')
    src = one(
        src,
        '                                    + " stillCensoredByPhase="\n'
        '                                    + java.util.Arrays.toString(java.util.Arrays.copyOfRange(d, 40, 44))\n'
        '                                    + " imageMathUnchangedByTelemetry=true"\n',
        '                                    + " stillCensoredByPhase="\n'
        '                                    + java.util.Arrays.toString(java.util.Arrays.copyOfRange(d, 40, 44))\n'
        '                                    + " shortPacksAny=" + Integer.toUnsignedLong(d[44])\n'
        '                                    + " shortPacksMixedCensored=" + Integer.toUnsignedLong(d[45])\n'
        '                                    + " shortPacksFullyKnown=" + Integer.toUnsignedLong(d[46])\n'
        '                                    + " IRIS_26506_SHORT_A_SPATIAL_PROVENANCE_COHERENCE=true"\n'
        '                                    + " imageMathChangedOnlyBySemanticColorCoherence=true"\n',
        'Short-A coherence diagnostics')
    return src


def main():
    global ROOT
    ap=argparse.ArgumentParser()
    ap.add_argument('root',type=Path)
    args=ap.parse_args(); ROOT=args.root

    edit('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
         motion_render_java)
    edit('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl',
         normalizer)
    edit('app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl',
         short_recovery)
    edit('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl',
         short_weight)
    edit('app/src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl',
         shadow_fuse)
    edit('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
         cfa_host)

    print('PASS: 26506 integrated UHDR parity + Normal/Short/Long chroma-coherence transforms applied')
    print('PASS: Wronski geometry/capture exposure roles/Camera2 color/EXIF ownership untouched')


if __name__=='__main__':
    main()
