#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse

ROOT = None

def fail(msg: str):
    raise SystemExit("ERROR: " + msg)

def one(src: str, old: str, new: str, label: str) -> str:
    n = src.count(old)
    if n != 1:
        fail(f"{label}: expected one anchor, found {n}")
    return src.replace(old, new, 1)

def replace_function(src: str, signature_token: str, replacement: str, label: str) -> str:
    start = src.find(signature_token)
    if start < 0:
        fail(f"{label}: signature token not found: {signature_token}")
    if src.find(signature_token, start + 1) >= 0:
        fail(f"{label}: signature token is not unique")
    brace = src.find("{", start)
    if brace < 0:
        fail(f"{label}: opening brace not found")
    depth = 0
    in_str = False
    esc = False
    in_line = False
    in_block = False
    i = brace
    while i < len(src):
        ch = src[i]
        nxt = src[i + 1] if i + 1 < len(src) else ""
        if in_line:
            if ch == "\n":
                in_line = False
        elif in_block:
            if ch == "*" and nxt == "/":
                in_block = False
                i += 1
        elif in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == "/" and nxt == "/":
                in_line = True
                i += 1
            elif ch == "/" and nxt == "*":
                in_block = True
                i += 1
            elif ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return src[:start] + replacement.rstrip() + src[i + 1:]
        i += 1
    fail(f"{label}: closing brace not found")

def edit(rel: str, fn):
    p = ROOT / rel
    if not p.is_file():
        fail(f"missing {rel}")
    before = p.read_text()
    after = fn(before)
    if after == before:
        fail(f"{rel}: transform made no change")
    p.write_text(after)
    print("CHANGED", rel)

def motion_merger(src: str) -> str:
    replacement = r'''    /* IRIS_26504_COMPOSITION_BOUNDED_DISPLAY_GAIN
     * The one post-Wronski display multiplier remains the sole large-scale
     * brightness authority. The selected reference CaptureResult supplies the
     * frozen HAL/capture scene key. Sparse RAW percentiles are residual evidence
     * only and are bounded to +/-0.25 EV around that capture-state anchor.
     *
     * This deliberately prevents two near-identical compositions from producing
     * multi-EV brightness swings merely because a window occupies more pixels.
     * Nothing here feeds Camera2 or live AE.
     */
    public static float computeDisplayGain(
            ByteBuffer raw, int width, int height, Parameters parameters,
            double referenceExposureEnergy) {
        if (raw == null || width <= 0 || height <= 0
                || parameters == null || parameters.whiteLevel <= 0
                || parameters.blackLevel == null || parameters.blackLevel.length < 4) {
            return 1.0f;
        }

        final int bins = 2048;
        final int[] histogram = new int[bins];
        long total = 0L;
        ByteBuffer view = raw.duplicate().order(ByteOrder.nativeOrder());
        view.clear();
        ShortBuffer shorts = view.asShortBuffer();
        int sx = Math.max(1, width / 256);
        int sy = Math.max(1, height / 192);
        float white = parameters.whiteLevel;

        for (int y = sy / 2; y < height; y += sy) {
            for (int x = sx / 2; x < width; x += sx) {
                int index = y * width + x;
                if (index < 0 || index >= shorts.limit()) continue;
                int rawValue = Short.toUnsignedInt(shorts.get(index));
                int phase = ((y & 1) << 1) | (x & 1);
                float black = parameters.blackLevel[phase];
                float span = Math.max(1.0f, white - black);
                float measured = Math.max(
                        0.0f,
                        Math.min(1.0f, (rawValue - black) / span));
                int bin = Math.min(
                        bins - 1,
                        Math.max(0, (int)(measured * (bins - 1))));
                histogram[bin]++;
                total++;
            }
        }
        if (total < 64L) return 1.0f;

        float p50 = quantile(histogram, total, 0.50f);
        float p90 = quantile(histogram, total, 0.90f);
        float p99 = quantile(histogram, total, 0.99f);

        double exposureSeconds = parameters.exposureTime;
        float iso = Math.max(1.0f, (float) parameters.iso);
        float aperture = parameters.aperture;
        boolean frozenCaptureValid = Double.isFinite(exposureSeconds)
                && exposureSeconds > 0.0 && exposureSeconds < 30.0
                && Float.isFinite(iso) && iso > 0.0f
                && Float.isFinite(aperture) && aperture > 0.1f;
        float ev100 = 4.0f;
        if (frozenCaptureValid) {
            double ev =
                    Math.log((aperture * aperture) / exposureSeconds) / Math.log(2.0)
                    - Math.log(iso / 100.0) / Math.log(2.0);
            if (Double.isFinite(ev)) {
                ev100 = (float) ev;
            } else {
                frozenCaptureValid = false;
            }
        }

        float anchorScene = frozenCaptureValid
                ? smoothstep(2.0f, 5.0f, ev100)
                : 0.65f;
        float captureAnchorGain = mix(1.0f, 2.15f, anchorScene);

        float darknessSceneKey = frozenCaptureValid
                ? smoothstep(1.5f, 5.5f, ev100)
                : 0.65f;
        float targetP50 = mix(0.0020f, 0.050f, darknessSceneKey);
        float targetP90 = mix(0.0120f, 0.180f, darknessSceneKey);
        float gain50 = targetP50 / Math.max(p50, 1.0e-5f);
        float gain90 = targetP90 / Math.max(p90, 1.0e-5f);
        float histogramGain = (float)Math.sqrt(
                Math.max(1.0f, gain50) * Math.max(1.0f, gain90));
        histogramGain = Math.max(1.0f, Math.min(16.0f, histogramGain));

        float rawResidualRatio =
                histogramGain / Math.max(captureAnchorGain, 1.0e-6f);
        float residualEv = (float)(
                Math.log(Math.max(rawResidualRatio, 1.0e-6f)) / Math.log(2.0));
        residualEv = Math.max(-0.25f, Math.min(0.25f, residualEv));

        float predictedNearClip = fractionAbove(
                histogram,
                total,
                Math.min(
                        1.0f,
                        0.985f / Math.max(captureAnchorGain, 1.0f)));
        float occupancyPressure = smoothstep(0.015f, 0.18f, predictedNearClip);
        if (residualEv > 0.0f) {
            residualEv *= 1.0f - 0.70f * occupancyPressure;
        }

        float residualGain = (float)Math.pow(2.0, residualEv);
        float gain = captureAnchorGain * residualGain;
        gain = Math.max(1.0f, Math.min(4.0f, gain));
        if (!Float.isFinite(gain)) gain = 1.0f;
        if (gain < 1.02f) gain = 1.0f;

        Log.d(TAG, "IRIS_26504_COMPOSITION_BOUNDED_DISPLAY_GAIN"
                + " rawP50=" + p50
                + " rawP90=" + p90
                + " rawP99=" + p99
                + " aperture=" + aperture
                + " exposureSeconds=" + exposureSeconds
                + " iso=" + iso
                + " frozenCaptureValid=" + frozenCaptureValid
                + " ev100=" + ev100
                + " captureAnchorGain=" + captureAnchorGain
                + " histogramGain=" + histogramGain
                + " residualEvBound=0.25"
                + " residualEv=" + residualEv
                + " predictedNearClip=" + predictedNearClip
                + " occupancyPressure=" + occupancyPressure
                + " displayGain=" + gain
                + " referenceExposureEnergyDiagnosticOnly="
                    + referenceExposureEnergy
                + " globalExposureOwner=true"
                + " liveAeFeedback=false"
                + " previewKeyImplemented=false");
        return gain;
    }'''
    return replace_function(
        src,
        "    public static float computeDisplayGain(",
        replacement,
        "MotionV2Merger.computeDisplayGain")

FINAL_NORMALIZER = r'''precision highp float;
precision highp int;

uniform highp sampler2D semanticAccumulator;
uniform highp sampler2D opponentWeightAccumulator;
uniform highp sampler2D fallbackCfa;
uniform highp sampler2D highlightProvenance;
uniform highp sampler2D lensShadingMap;
uniform highp sampler2D frameSupportTexture;
uniform ivec2 rawSize;
uniform ivec2 packedSize;
uniform vec3 cameraDomainScale;
uniform vec3 noiseShotRgb;
uniform vec3 noiseReadRgb;
uniform int useLensShading;
out vec4 Output;

/* IRIS_26504_QUAD_COHERENT_HIGHLIGHT_AUTHORITY
 * The physical trust unit is the exact parent 2x2 Bayer quad. NORMAL (0) and
 * SHORT_VALIDATED (2) are known observations; CENSORED (1) is unknown.
 */
const float SUPPORT_EPS=1.0e-7;
float phaseDivisor(int q){return q==0?1.0:(q==1?3.0:(q==2?9.0:27.0));}
float phaseState(ivec2 packedP,int q){
    packedP=clamp(packedP,ivec2(0),packedSize-ivec2(1));
    float code=texelFetch(highlightProvenance,packedP,0).r;
    return mod(floor(code/phaseDivisor(q)),3.0);
}
bool packedHasCensored(ivec2 packedP){
    for(int q=0;q<4;++q){
        if(abs(phaseState(packedP,q)-1.0)<0.25)return true;
    }
    return false;
}
bool expandedCensoredDecision(ivec2 packedP){
    for(int oy=-1;oy<=1;++oy){
        for(int ox=-1;ox<=1;++ox){
            ivec2 q=clamp(packedP+ivec2(ox,oy),ivec2(0),packedSize-ivec2(1));
            if(packedHasCensored(q))return true;
        }
    }
    return false;
}
float packedNeutralAt(ivec2 packedP){
    packedP=clamp(packedP,ivec2(0),packedSize-ivec2(1));
    vec4 v=max(texelFetch(fallbackCfa,packedP,0),vec4(0.0));
    return max(max(v.r,v.g),max(v.b,v.a));
}
float neutralFallback(ivec2 rawP){
    vec2 packedPosition=(vec2(rawP)+vec2(0.5))*0.5-vec2(0.25);
    vec2 p=packedPosition-vec2(0.5);
    ivec2 lo=ivec2(floor(p));
    vec2 f=fract(p);
    ivec2 hi=lo+ivec2(1);
    float a=packedNeutralAt(lo);
    float b=packedNeutralAt(ivec2(hi.x,lo.y));
    float c=packedNeutralAt(ivec2(lo.x,hi.y));
    float d=packedNeutralAt(hi);
    return mix(mix(a,b,f.x),mix(c,d,f.x),f.y);
}
vec3 lensShadingRgb(ivec2 rawP){
    if(useLensShading==0)return vec3(1.0);
    vec2 uv=(vec2(rawP)+vec2(0.5))/vec2(rawSize);
    vec4 g=texture(lensShadingMap,clamp(uv,vec2(0.0),vec2(1.0)));
    return max(vec3(g.r,0.5*(g.g+g.b),g.a),vec3(0.0));
}
float opponentSupportQuality(float greenWeight,float opponentWeight){
    if(greenWeight<=SUPPORT_EPS||opponentWeight<=SUPPORT_EPS)return 0.0;
    return clamp(opponentWeight/max(0.30*greenWeight,SUPPORT_EPS),0.0,1.0);
}
void accumulateNeighborOpponent(
        ivec2 q,float centerGreen,float spatialWeight,
        inout vec2 opponentSums,inout vec2 neighborWeightSums){
    if(any(lessThan(q,ivec2(0)))||any(greaterThanEqual(q,rawSize)))return;
    vec4 neighborSemantic=texelFetch(semanticAccumulator,q,0);
    vec2 neighborOpponentWeight=texelFetch(opponentWeightAccumulator,q,0).rg;
    if(neighborSemantic.a<=SUPPORT_EPS)return;
    float neighborGreen=neighborSemantic.r/neighborSemantic.a;
    float sigma=max(0.004,0.035*max(centerGreen,0.02));
    float z=(neighborGreen-centerGreen)/sigma;
    float edgeWeight=exp(-0.5*z*z)*spatialWeight;
    if(neighborOpponentWeight.r>SUPPORT_EPS){
        float qualityR=opponentSupportQuality(
                neighborSemantic.a,neighborOpponentWeight.r);
        float wR=edgeWeight*qualityR;
        opponentSums.r+=(neighborSemantic.g/neighborOpponentWeight.r)*wR;
        neighborWeightSums.r+=wR;
    }
    if(neighborOpponentWeight.g>SUPPORT_EPS){
        float qualityB=opponentSupportQuality(
                neighborSemantic.a,neighborOpponentWeight.g);
        float wB=edgeWeight*qualityB;
        opponentSums.g+=(neighborSemantic.b/neighborOpponentWeight.g)*wB;
        neighborWeightSums.g+=wB;
    }
}
float opponentAgreement(
        float centerOpponent,float localOpponent,float green,float centerQuality){
    float threshold=max(0.010,0.25*max(green,0.02));
    float chromaEdge=smoothstep(
            threshold,2.5*threshold,abs(centerOpponent-localOpponent));
    return 1.0-centerQuality*chromaEdge;
}
float localEvidenceQuality(float neighborWeightSum){
    return smoothstep(0.25,1.75,neighborWeightSum);
}
float residualOpponentKeep(
        float opponent,float signalA,float signalB,
        float shotA,float readA,float shotB,float readB,
        float localFrameSupport,float darkGate){
    float n=max(localFrameSupport,1.0);
    float varA=max(shotA*max(signalA,0.0)+readA,0.0)/n;
    float varB=max(shotB*max(signalB,0.0)+readB,0.0)/n;
    float sigma=sqrt(max(varA+varB,1.0e-10));
    float z=abs(opponent)/max(sigma,1.0e-6);
    float noiseLike=1.0-smoothstep(1.50,3.25,z);
    return 1.0-0.82*darkGate*noiseLike;
}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    if(any(greaterThanEqual(p,rawSize))){Output=vec4(0.0);return;}

    vec4 semantic=texelFetch(semanticAccumulator,p,0);
    vec4 opponentWeights=texelFetch(opponentWeightAccumulator,p,0);
    float gWeight=semantic.a;
    float rWeight=opponentWeights.r;
    float bWeight=opponentWeights.g;
    float green=gWeight>SUPPORT_EPS?semantic.r/gWeight:0.0;
    bool centerRPresent=rWeight>SUPPORT_EPS;
    bool centerBPresent=bWeight>SUPPORT_EPS;
    float centerRg=centerRPresent?semantic.g/rWeight:0.0;
    float centerBg=centerBPresent?semantic.b/bWeight:0.0;
    float centerQr=opponentSupportQuality(gWeight,rWeight);
    float centerQb=opponentSupportQuality(gWeight,bWeight);

    vec2 opponentSums=vec2(0.0);
    vec2 neighborWeightSums=vec2(0.0);
    accumulateNeighborOpponent(p+ivec2(-1, 0),green,1.0,opponentSums,neighborWeightSums);
    accumulateNeighborOpponent(p+ivec2( 1, 0),green,1.0,opponentSums,neighborWeightSums);
    accumulateNeighborOpponent(p+ivec2( 0,-1),green,1.0,opponentSums,neighborWeightSums);
    accumulateNeighborOpponent(p+ivec2( 0, 1),green,1.0,opponentSums,neighborWeightSums);
    accumulateNeighborOpponent(p+ivec2(-1,-1),green,0.70710678,opponentSums,neighborWeightSums);
    accumulateNeighborOpponent(p+ivec2( 1,-1),green,0.70710678,opponentSums,neighborWeightSums);
    accumulateNeighborOpponent(p+ivec2(-1, 1),green,0.70710678,opponentSums,neighborWeightSums);
    accumulateNeighborOpponent(p+ivec2( 1, 1),green,0.70710678,opponentSums,neighborWeightSums);

    bool localRPresent=neighborWeightSums.r>SUPPORT_EPS;
    bool localBPresent=neighborWeightSums.g>SUPPORT_EPS;
    float localRg=localRPresent
            ?opponentSums.r/neighborWeightSums.r:centerRg;
    float localBg=localBPresent
            ?opponentSums.g/neighborWeightSums.g:centerBg;
    float localQr=localEvidenceQuality(neighborWeightSums.r);
    float localQb=localEvidenceQuality(neighborWeightSums.g);

    float neutral=neutralFallback(p);
    float physicalHighlight=max(max(green,neutral),0.0);
    float darkGate=1.0-smoothstep(0.018,0.085,max(green,0.0));

    float rShadowBlend=darkGate*mix(0.70,0.38,centerQr)
            *opponentAgreement(centerRg,localRg,green,centerQr)*localQr;
    float bShadowBlend=darkGate*mix(0.70,0.38,centerQb)
            *opponentAgreement(centerBg,localBg,green,centerQb)*localQb;
    float rg=centerRPresent
            ?mix(centerRg,localRg,
                    localRPresent?clamp(rShadowBlend,0.0,1.0):0.0)
            :(localRPresent?localRg:0.0);
    float bg=centerBPresent
            ?mix(centerBg,localBg,
                    localBPresent?clamp(bShadowBlend,0.0,1.0):0.0)
            :(localBPresent?localBg:0.0);

    /* IRIS_26504_NOISE_AWARE_OPPONENT_SANITY */
    float localFrameSupport=max(
            texelFetch(frameSupportTexture,p,0).r,1.0);
    float rSignal=max(green+rg,0.0);
    float bSignal=max(green+bg,0.0);
    rg*=residualOpponentKeep(
            rg,rSignal,green,
            noiseShotRgb.r,noiseReadRgb.r,
            noiseShotRgb.g,noiseReadRgb.g,
            localFrameSupport,darkGate);
    bg*=residualOpponentKeep(
            bg,bSignal,green,
            noiseShotRgb.b,noiseReadRgb.b,
            noiseShotRgb.g,noiseReadRgb.g,
            localFrameSupport,darkGate);

    vec3 calculationRgb=max(
            vec3(green+rg,green,green+bg),vec3(0.0));

    /* IRIS_26504_POST_LSC_CHROMA_EXHAUSTION */
    vec3 lsc=lensShadingRgb(p);
    calculationRgb*=lsc;

    ivec2 parentPacked=clamp(p/2,ivec2(0),packedSize-ivec2(1));
    bool expandedIncomplete=expandedCensoredDecision(parentPacked);
    float physicalHighlightGate=smoothstep(0.45,0.72,physicalHighlight);
    bool colorIncomplete=physicalHighlightGate>0.001&&expandedIncomplete;

    if(colorIncomplete||gWeight<=SUPPORT_EPS){
        float stableNeutral=max(
                calculationRgb.g,
                max(neutral,green)*max(lsc.g,0.0));
        calculationRgb=vec3(max(stableNeutral,0.0));
    }

    vec3 cameraRgb=calculationRgb*cameraDomainScale;

    /* IRIS_26504_LOCAL_FRAME_EQUIVALENT_SUPPORT_CARRIER */
    Output=vec4(
            max(cameraRgb,vec3(0.0)),
            min(localFrameSupport,65504.0));
}
'''

def normalizer(src: str) -> str:
    if "IRIS_26502_STACK_AWARE_SEMANTIC_NORMALIZE" not in src:
        fail("normalizer is not canonical tested 26502")
    if "IRIS_26504_QUAD_COHERENT_HIGHLIGHT_AUTHORITY" in src:
        fail("normalizer already contains 26504")
    return FINAL_NORMALIZER

FINAL_DISPLAY_SHADER = r'''precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float displayGain;
uniform float shadowRecoveryStrength;
uniform float shadowFloorStop;
uniform float retainedFrames;
out vec3 Output;

/* IRIS_26504_PIXEL_LOCAL_EFFECTIVE_STACK_PERMISSION */
float luminance(vec3 c){
    return dot(c,vec3(0.2126,0.7152,0.0722));
}
vec3 recoverSupportedShadow(
        vec3 displayed,vec3 sensorRgb,float localFrameSupport){
    displayed=max(displayed,vec3(0.0));
    sensorRgb=max(sensorRgb,vec3(0.0));
    float sensorY=max(luminance(sensorRgb),0.0);
    float displayedY=max(luminance(displayed),0.0);
    if(sensorY<=1.0e-8||shadowRecoveryStrength<=0.0)return displayed;

    float floorWidth=max(0.006,1.5*shadowFloorStop);
    float floorGate=smoothstep(
            shadowFloorStop,shadowFloorStop+floorWidth,sensorY);
    float shadowGate=1.0-smoothstep(0.12,0.30,displayedY);

    float frameDenom=max(retainedFrames-1.0,1.0);
    float localRatio=clamp(
            (max(localFrameSupport,1.0)-1.0)/frameDenom,0.0,1.0);
    float localDepth=smoothstep(
            1.5,8.0,max(localFrameSupport,1.0));
    float localPermission=localRatio*(0.30+0.70*localDepth);

    float scale=1.0+clamp(shadowRecoveryStrength,0.0,0.10)
            *floorGate*shadowGate*localPermission;
    return displayed*scale;
}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    vec4 carrier=max(texelFetch(InputBuffer,p,0),vec4(0.0));
    vec3 c=carrier.rgb;
    vec3 displayed=c*max(displayGain,1.0);
    Output=recoverSupportedShadow(displayed,c,carrier.a);
}
'''

def display_shader(src: str) -> str:
    if "IRIS_26503_EVIDENCE_BASED_STACK_AWARE_SHADOW_RECOVERY" not in src:
        fail("display shader missing audited 26503 seed")
    return FINAL_DISPLAY_SHADER

FINAL_DISPLAY_JAVA = r'''package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26504_SINGLE_EXPOSURE_LOCAL_SUPPORT
 * One post-Wronski global display multiplier plus bounded local shadow
 * permission from the actual Motion stack. No Photon AutoExposure/Fusion owner.
 */
public final class MotionV2DisplayExposure extends Node {
    public MotionV2DisplayExposure() {
        super("", "MotionV2DisplayExposure");
    }

    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException(
                    "MotionV2DisplayExposure used outside Motion V2");
        }

        float gain = Math.max(
                1.0f,
                basePipeline.mParameters.motionV2DisplayGain);
        float retainedFrames = Math.max(
                1.0f,
                (float) com.particlesdevs.photoncamera.processing
                        .MotionMetrics.retainedFrames());
        float effectiveSupport = Math.max(
                1.0f,
                basePipeline.mParameters.motionV2EffectiveSupport);
        float effectiveStackRatio = Math.max(
                0.10f,
                Math.min(1.0f, effectiveSupport / retainedFrames));
        float stackDepthConfidence = Math.max(
                0.0f,
                Math.min(1.0f, (effectiveSupport - 1.0f) / 7.0f));
        float iso = Math.max(
                1.0f,
                (float) basePipeline.mParameters.iso);
        float isoRisk = Math.max(
                0.0f,
                Math.min(1.0f, (iso - 800.0f) / 3200.0f));
        float shadowRecoverability =
                effectiveStackRatio
                        * (0.35f + 0.65f * stackDepthConfidence)
                        * (1.0f - 0.55f * isoRisk);
        float shadowRecoveryStrength = Math.max(
                0.0f,
                Math.min(0.10f, 0.10f * shadowRecoverability));
        float shadowFloorStop = 0.006f + 0.010f * isoRisk;

        glProg.useAssetProgram("motionv2/display_exposure");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("displayGain", gain);
        glProg.setVar(
                "shadowRecoveryStrength", shadowRecoveryStrength);
        glProg.setVar("shadowFloorStop", shadowFloorStop);
        glProg.setVar("retainedFrames", retainedFrames);
        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;

        Log.d(Name, "IRIS_26504_SINGLE_EXPOSURE_LOCAL_SUPPORT"
                + " displayGain=" + gain
                + " largeScaleOwner=motionV2DisplayGain"
                + " globalResidualGain=1.0"
                + " retainedFrames=" + retainedFrames
                + " effectiveSupport=" + effectiveSupport
                + " effectiveStackRatio=" + effectiveStackRatio
                + " iso=" + iso
                + " isoRisk=" + isoRisk
                + " shadowRecoverability=" + shadowRecoverability
                + " shadowRecoveryStrength=" + shadowRecoveryStrength
                + " shadowFloorStop=" + shadowFloorStop
                + " pixelLocalSupportFromCarrierAlpha=true"
                + " localHueScaleOnly=true"
                + " insideWronski=false"
                + " photonAutoExposure=false"
                + " photonExposureFusion=false"
                + " previewKeyImplemented=false");
    }
}
'''

def display_java(src: str) -> str:
    if "IRIS_26503_SINGLE_EXPOSURE_SHADOW_AUTHORITY" not in src:
        fail("display Java missing audited 26503 seed")
    return FINAL_DISPLAY_JAVA

def cfa_host(src: str) -> str:
    src = one(
        src,
        '                    glProg.setTexture("lensShadingMap", iris26501LensShading);\n',
        '                    glProg.setTexture("lensShadingMap", iris26501LensShading);\n'
        '                    /* IRIS_26504_LOCAL_SUPPORT_AND_NOISE_TO_NORMALIZER */\n'
        '                    glProg.setTexture("frameSupportTexture", currentDirectFrameSupport);\n'
        '                    glProg.setVar("noiseShotRgb", new float[]{\n'
        '                            iris26487ReferenceWbNoise[0],\n'
        '                            iris26487ReferenceWbNoise[1],\n'
        '                            iris26487ReferenceWbNoise[2]});\n'
        '                    glProg.setVar("noiseReadRgb", new float[]{\n'
        '                            iris26487ReferenceWbNoise[3],\n'
        '                            iris26487ReferenceWbNoise[4],\n'
        '                            iris26487ReferenceWbNoise[5]});\n',
        "CFA normalizer local support + noise binding")

    already_disabled = (
        'if (false && /* IRIS_26480_DISABLE_DIRECT_SUPPORT_GPU_READBACK_V2 */ '
        'directBayer && currentDirectSupport != null) {'
    )
    if already_disabled not in src:
        fail("CFA canonical direct-support readback-disable invariant missing")

    src = one(
        src,
        'if (directBayer && iris26492ReadbackProvenance != null) {',
        'if (false && /* IRIS_26504_DISABLE_HEAVY_PROVENANCE_READBACK */ '
        'directBayer && iris26492ReadbackProvenance != null) {',
        "CFA provenance diagnostic readback disable")
    return src

def main():
    global ROOT
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    args = ap.parse_args()
    ROOT = args.root

    edit(
        "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java",
        motion_merger)
    edit(
        "app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl",
        normalizer)
    edit(
        "app/src/main/assets/shaders/motionv2/display_exposure.glsl",
        display_shader)
    edit(
        "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java",
        display_java)
    edit(
        "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java",
        cfa_host)

    print("PASS: 26504 integrated HDR strong-clipping transforms applied")
    print("PASS: Wronski/capture/Camera2 color/EXIF/UHDR architecture untouched")

if __name__ == "__main__":
    main()
