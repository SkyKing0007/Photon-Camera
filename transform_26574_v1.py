from pathlib import Path
import shutil, hashlib, re, sys
if len(sys.argv) != 3:
    raise SystemExit('usage: transform_26574_combined.py <base_app_root> <candidate_app_root>')
BASE=Path(sys.argv[1]).resolve()
C=Path(sys.argv[2]).resolve()
if not (BASE/'app').is_dir():
    raise SystemExit('FAIL base app root missing app/')
if C.exists():
    shutil.rmtree(C)
shutil.copytree(BASE, C)

def replace_once(path, old, new, label):
    p=C/path
    s=p.read_text()
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'FAIL {label}: anchor count {n}')
    p.write_text(s.replace(old,new,1))
    print('PASS',label)

# --- 1) shared VGN topology protection ---
vgn=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')

# universal adaptive color: add radius-2 topological support around bright/material-boundary candidates.
old='''            float oneSidedLuma = ((brighterSide >= 4 && darkerSide <= 1) ||
                (darkerSide >= 4 && brighterSide <= 1)) ? 1.0 : 0.0;
            float highlightPreservePermission = 1.0 - smoothstep(0.72, 0.92, centerLuma);
            float materialBoundary = oneSidedLuma *
                (1.0 - smoothstep(0.72, 0.92, chromaAgreement)) * highlightPreservePermission;
            float edgeProtection = max(legacyEdgeProtection, materialBoundary);
'''
new='''            float oneSidedLuma = ((brighterSide >= 4 && darkerSide <= 1) ||
                (darkerSide >= 4 && brighterSide <= 1)) ? 1.0 : 0.0;
            float highlightPreservePermission = 1.0 - smoothstep(0.72, 0.92, centerLuma);
            float materialBoundary = oneSidedLuma *
                (1.0 - smoothstep(0.72, 0.92, chromaAgreement)) * highlightPreservePermission;

            /* IRIS_26574_TOPOLOGY_PRESERVED_BRIGHT_SURFACE
             * 26571 deliberately disabled its chroma/material protection in bright pixels to keep
             * clipped pink/magenta cleanup authoritative. That also made legitimate bright sky a
             * minority outlier inside foliage gaps. Restore edge protection only when the center
             * surface proves spatial continuation at radius two. An isolated false-color pixel
             * therefore cannot gain protection merely because it is bright.
             */
            float topologySupport = 0.0;
            if (centerLuma > 0.58 || oneSidedLuma > 0.5 || legacyEdgeProtection > 0.25) {
                const ivec2 topologyDirections[8] = ivec2[8](
                    ivec2(1,0), ivec2(-1,0), ivec2(0,1), ivec2(0,-1),
                    ivec2(1,1), ivec2(-1,-1), ivec2(1,-1), ivec2(-1,1));
                for (int i = 0; i < 8; ++i) {
                    vec3 farRgb = loadRgb(p + topologyDirections[i] * 2);
                    float farLuma = luminanceOf(farRgb);
                    float farScale = max(max(centerLuma, farLuma), 0.060);
                    float farLumaDelta = abs(farLuma - centerLuma) / farScale;
                    vec3 farChroma = (farRgb - vec3(farLuma)) / max(farLuma, 0.060);
                    float farAgreement = dot(centerNormalizedChroma, farChroma) /
                        max(length(centerNormalizedChroma) * length(farChroma), 1.0e-6);
                    float sameLuma = 1.0 - smoothstep(0.10, 0.26, farLumaDelta);
                    float sameHue = smoothstep(0.82, 0.94, clamp(farAgreement, -1.0, 1.0));
                    float centerChromaPresent = smoothstep(0.035, 0.090, centerNormalizedMagnitude);
                    topologySupport += sameLuma * mix(1.0, sameHue, centerChromaPresent);
                }
            }
            float topologyProtection = smoothstep(1.25, 2.75, topologySupport) *
                smoothstep(0.20, 0.55, max(legacyEdgeProtection, oneSidedLuma));
            float edgeProtection = max(max(legacyEdgeProtection, materialBoundary), topologyProtection);
'''
replace_once(vgn,old,new,'VGN universal topology protection')

old='''            float coherentCenterProtection = coherentHue * plausibleCenterMagnitude *
                highlightPreservePermission;
'''
new='''            float coherentCenterProtection = coherentHue * plausibleCenterMagnitude *
                max(highlightPreservePermission, topologyProtection);
'''
replace_once(vgn,old,new,'VGN universal coherent topology permission')

# local median: prevent 3x3 majority from erasing a radius-2 supported bright gap.
old='''            float highlightPreservePermission=1.0-smoothstep(0.72,0.92,centerY);
            float materialBoundary=(sideCount>0.0?1.0:0.0)*
                (1.0-smoothstep(0.72,0.92,sideAgreement))*highlightPreservePermission;
            float edgeProtection=max(max(oneSidedProtection,materialBoundary),smoothstep(0.45,0.90,maximumRelativeLumaDelta));
            float strength=clamp(uChromaStrength,0.0,1.0)*(1.0-edgeProtection);
'''
new='''            float highlightPreservePermission=1.0-smoothstep(0.72,0.92,centerY);
            float materialBoundary=(sideCount>0.0?1.0:0.0)*
                (1.0-smoothstep(0.72,0.92,sideAgreement))*highlightPreservePermission;
            float legacyEdge=smoothstep(0.45,0.90,maximumRelativeLumaDelta);
            float topologySupport=0.0;
            if(centerY>0.58||sideCount>0.0||legacyEdge>0.25){
                const ivec2 td[8]=ivec2[8](ivec2(1,0),ivec2(-1,0),ivec2(0,1),ivec2(0,-1),ivec2(1,1),ivec2(-1,-1),ivec2(1,-1),ivec2(-1,1));
                float centerMagnitude=max(length(vec2(centerChroma)),1.0);
                for(int i=0;i<8;++i){
                    uvec4 farPixel=imageLoad(uInput,safePos(p+td[i]*2));
                    float farY=float(farPixel.r)/65504.0;
                    float farDelta=abs(farY-centerY)/max(max(farY,centerY),0.060);
                    vec2 farChroma=vec2(float(signedChroma(farPixel.g)),float(signedChroma(farPixel.b)));
                    float farAgreement=clamp(chromaAgreement(vec2(centerChroma),farChroma),-1.0,1.0);
                    float sameLuma=1.0-smoothstep(0.10,0.26,farDelta);
                    float centerChromaPresent=smoothstep(128.0,512.0,centerMagnitude);
                    float sameHue=smoothstep(0.82,0.94,farAgreement);
                    topologySupport+=sameLuma*mix(1.0,sameHue,centerChromaPresent);
                }
            }
            float topologyProtection=smoothstep(1.25,2.75,topologySupport)*
                smoothstep(0.20,0.55,max(legacyEdge,sideCount>0.0?1.0:0.0));
            float edgeProtection=max(max(max(oneSidedProtection,materialBoundary),legacyEdge),topologyProtection);
            float strength=clamp(uChromaStrength,0.0,1.0)*(1.0-edgeProtection);
'''
replace_once(vgn,old,new,'VGN local median topology protection')

# directional: if topology proves the center surface, let original center chroma remain the floor.
old='''            float highlightPreservePermission=1.0-smoothstep(0.72,0.92,centerY);
            float edgePreserve=smoothstep(0.08,0.30,edgeEvidence)*highlightPreservePermission;
            float smoothAgreement=clamp(chromaAgreement(originalChroma,smoothChroma),-1.0,1.0);
'''
new='''            float highlightPreservePermission=1.0-smoothstep(0.72,0.92,centerY);
            float topologySupport=0.0;
            if(centerY>0.58||edgeEvidence>0.08){
                const ivec2 td[8]=ivec2[8](ivec2(1,0),ivec2(-1,0),ivec2(0,1),ivec2(0,-1),ivec2(1,1),ivec2(-1,-1),ivec2(1,-1),ivec2(-1,1));
                float centerMagnitude=max(length(originalChroma),1.0);
                for(int i=0;i<8;++i){
                    uvec4 farPixel=imageLoad(uOriginal,safePos(p+td[i]*2));
                    float farY=decodeU16(farPixel.r)/65504.0;
                    float farDelta=abs(farY-centerY)/max(max(farY,centerY),0.060);
                    vec2 farChroma=vec2(float(signedChroma(farPixel.g)),float(signedChroma(farPixel.b)));
                    float farAgreement=clamp(chromaAgreement(originalChroma,farChroma),-1.0,1.0);
                    float sameLuma=1.0-smoothstep(0.10,0.26,farDelta);
                    float centerChromaPresent=smoothstep(128.0,512.0,centerMagnitude);
                    topologySupport+=sameLuma*mix(1.0,smoothstep(0.82,0.94,farAgreement),centerChromaPresent);
                }
            }
            float topologyProtection=smoothstep(1.25,2.75,topologySupport)*smoothstep(0.08,0.30,edgeEvidence);
            float edgePreserve=max(smoothstep(0.08,0.30,edgeEvidence)*highlightPreservePermission,topologyProtection);
            float smoothAgreement=clamp(chromaAgreement(originalChroma,smoothChroma),-1.0,1.0);
'''
replace_once(vgn,old,new,'VGN directional topology protection')
old='''            vec2 selectedChroma=mix(legacyChroma,edgeCandidate,edgePreserve*coherentEdge);
'''
new='''            vec2 selectedChroma=mix(legacyChroma,edgeCandidate,edgePreserve*coherentEdge);
            selectedChroma=mix(selectedChroma,originalChroma,0.85*topologyProtection);
'''
replace_once(vgn,old,new,'VGN directional center-side topology floor')

# IIR: bright moderate boundary may reset only when each side continues perpendicular to scan.
old='''                float highlightPreservePermission=1.0-smoothstep(47162.88,60263.68,max(currentY,previousY));
                bool strongLumaBoundary=edgeRatio>0.55;
                bool materialColorBoundary=edgeRatio>0.24&&chromaJump>0.45&&highlightPreservePermission>0.5;
'''
new='''                float highlightPreservePermission=1.0-smoothstep(47162.88,60263.68,max(currentY,previousY));
                bool strongLumaBoundary=edgeRatio>0.55;
                ivec2 scanStep=uAxis==0?ivec2(step,0):ivec2(0,step);
                ivec2 perpendicular=uAxis==0?ivec2(0,1):ivec2(1,0);
                ivec2 previousP=p-scanStep;
                int currentPerpendicularSupport=0;
                int previousPerpendicularSupport=0;
                for(int side=-1;side<=1;side+=2){
                    uvec4 currentSide=imageLoad(uInput,safePos(p+perpendicular*side));
                    uvec4 previousSide=imageLoad(uInput,safePos(previousP+perpendicular*side));
                    float cy=decodeU16(currentSide.r),py=decodeU16(previousSide.r);
                    vec2 cc=vec2(float(signedChroma(currentSide.g)),float(signedChroma(currentSide.b)));
                    vec2 pc=vec2(float(signedChroma(previousSide.g)),float(signedChroma(previousSide.b)));
                    float currentLumaDelta=abs(cy-currentY)/max(max(cy,currentY),3930.0);
                    float previousLumaDelta=abs(py-previousY)/max(max(py,previousY),3930.0);
                    float currentHue=dot(cc,vec2(inCr,inCb))/max(length(cc)*max(currentChromaMagnitude,1.0),1.0);
                    float previousHue=dot(pc,vec2(previousCr,previousCb))/max(length(pc)*max(previousChromaMagnitude,1.0),1.0);
                    if(currentLumaDelta<0.18&&(currentChromaMagnitude<256.0||currentHue>0.84))currentPerpendicularSupport++;
                    if(previousLumaDelta<0.18&&(previousChromaMagnitude<256.0||previousHue>0.84))previousPerpendicularSupport++;
                }
                bool topologyBoundary=currentPerpendicularSupport>0&&previousPerpendicularSupport>0;
                bool materialColorBoundary=edgeRatio>0.24&&chromaJump>0.45&&
                    (highlightPreservePermission>0.5||topologyBoundary);
'''
replace_once(vgn,old,new,'VGN IIR perpendicular topology reset')

# --- 2) true2x SR flow refinement shader ---
sh=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
anchor='''    /**
     * IRIS_26545_SABRE_NORMALIZED16_DNG
'''
shader='''    /* IRIS_26574_TRUE2X_LOCAL_FLOW_REFINEMENT
     * SR-only one-step inverse-compositional LK refinement. The proven Sabre sparse flow remains
     * immutable and is the fallback. This shader only runs for frames already retained by the
     * unchanged 26568 top-two-per-phase JPEG reservoir. It works on Bayer-quad luma so subpixel
     * residual estimation never interpolates different CFA colours. Accepted delta is bounded to
     * +/-0.25 Bayer quad (= +/-0.5 RAW pixel) per axis.
     */
    val true2xFlowRefine26574 = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uReferenceRaw;
        uniform highp usampler2D uCurrentRaw;
        uniform sampler2D uSparseFlow;
        uniform ivec2 uRawSize;
        uniform ivec2 uOutputSize;
        uniform vec4 uSparseFlowScaleOffset;
        uniform vec4 uReferencePhaseGains;
        uniform vec4 uReferencePhaseBlackTerms;
        uniform vec4 uCurrentPhaseGains;
        uniform vec4 uCurrentPhaseBlackTerms;
        out vec4 oFlow;

        float phaseValue(highp usampler2D rawTex, ivec2 rawP, vec4 gains, vec4 blackTerms) {
            rawP=clamp(rawP,ivec2(0),uRawSize-ivec2(1));
            int phase=((rawP.y&1)<<1)+(rawP.x&1);
            return max(float(texelFetch(rawTex,rawP,0).r)*gains[phase]+blackTerms[phase],0.0);
        }
        float quadValue(highp usampler2D rawTex, ivec2 q, vec4 gains, vec4 blackTerms) {
            ivec2 maxQ=max((uRawSize-ivec2(1))/2,ivec2(0));
            q=clamp(q,ivec2(0),maxQ);
            ivec2 p=q*2;
            return 0.25*(phaseValue(rawTex,p,gains,blackTerms)+
                phaseValue(rawTex,p+ivec2(1,0),gains,blackTerms)+
                phaseValue(rawTex,p+ivec2(0,1),gains,blackTerms)+
                phaseValue(rawTex,p+ivec2(1,1),gains,blackTerms));
        }
        float currentAt(vec2 q) {
            ivec2 q0=ivec2(floor(q));
            vec2 f=fract(q);
            float a=mix(quadValue(uCurrentRaw,q0,uCurrentPhaseGains,uCurrentPhaseBlackTerms),
                quadValue(uCurrentRaw,q0+ivec2(1,0),uCurrentPhaseGains,uCurrentPhaseBlackTerms),f.x);
            float b=mix(quadValue(uCurrentRaw,q0+ivec2(0,1),uCurrentPhaseGains,uCurrentPhaseBlackTerms),
                quadValue(uCurrentRaw,q0+ivec2(1,1),uCurrentPhaseGains,uCurrentPhaseBlackTerms),f.x);
            return mix(a,b,f.y);
        }
        vec4 sparseFlowAt(vec2 referenceUv) {
            vec2 uv=referenceUv*uSparseFlowScaleOffset.xy+uSparseFlowScaleOffset.zw;
            ivec2 size=textureSize(uSparseFlow,0);
            vec2 c=clamp(uv*vec2(size)-vec2(0.5),vec2(0.0),vec2(size-ivec2(1)));
            ivec2 p0=ivec2(floor(c));
            ivec2 p1=min(p0+ivec2(1),size-ivec2(1));
            vec2 f=fract(c);
            vec4 v00=texelFetch(uSparseFlow,p0,0);
            vec4 v10=texelFetch(uSparseFlow,ivec2(p1.x,p0.y),0);
            vec4 v01=texelFetch(uSparseFlow,ivec2(p0.x,p1.y),0);
            vec4 v11=texelFetch(uSparseFlow,p1,0);
            ivec2 nearest=ivec2(floor(c+vec2(0.5)));
            vec4 base=texelFetch(uSparseFlow,clamp(nearest,ivec2(0),size-ivec2(1)),0);
            vec2 rawSize=vec2(uRawSize);
            float maximumDifference=0.0;
            maximumDifference=max(maximumDifference,max(abs((v00.x-base.x)*rawSize.x),abs((v00.y-base.y)*rawSize.y)));
            maximumDifference=max(maximumDifference,max(abs((v10.x-base.x)*rawSize.x),abs((v10.y-base.y)*rawSize.y)));
            maximumDifference=max(maximumDifference,max(abs((v01.x-base.x)*rawSize.x),abs((v01.y-base.y)*rawSize.y)));
            maximumDifference=max(maximumDifference,max(abs((v11.x-base.x)*rawSize.x),abs((v11.y-base.y)*rawSize.y)));
            if(maximumDifference>=1.0)return vec4(base.xy,max(base.z,maximumDifference/max(rawSize.x,rawSize.y)),0.0);
            vec4 a=mix(v00,v10,f.x),b=mix(v01,v11,f.x);
            vec4 linear=mix(a,b,f.y);
            linear.z=max(linear.z,maximumDifference/max(rawSize.x,rawSize.y));
            return linear;
        }
        float referenceAt(ivec2 q){return quadValue(uReferenceRaw,q,uReferencePhaseGains,uReferencePhaseBlackTerms);}
        float residualCost(ivec2 centerQ,vec2 currentCenterQ){
            const ivec2 d[5]=ivec2[5](ivec2(0,0),ivec2(1,0),ivec2(-1,0),ivec2(0,1),ivec2(0,-1));
            float cost=0.0;
            for(int i=0;i<5;++i){float r=currentAt(currentCenterQ+vec2(d[i]))-referenceAt(centerQ+d[i]);cost+=r*r;}
            return cost;
        }
        void main(){
            vec2 referenceUv=gl_FragCoord.xy/vec2(uOutputSize);
            vec4 base=sparseFlowAt(referenceUv);
            vec2 rawFlow=base.xy*vec2(uRawSize);
            vec2 quadFlow=rawFlow*0.5;
            ivec2 centerQ=ivec2(floor(referenceUv*vec2(uRawSize)*0.5));
            const ivec2 d[5]=ivec2[5](ivec2(0,0),ivec2(1,0),ivec2(-1,0),ivec2(0,1),ivec2(0,-1));
            float hxx=0.0,hxy=0.0,hyy=0.0,bx=0.0,by=0.0,baseCost=0.0;
            for(int i=0;i<5;++i){
                ivec2 q=centerQ+d[i];
                float ref=referenceAt(q);
                float gx=0.5*(referenceAt(q+ivec2(1,0))-referenceAt(q-ivec2(1,0)));
                float gy=0.5*(referenceAt(q+ivec2(0,1))-referenceAt(q-ivec2(0,1)));
                float residual=currentAt(vec2(q)+quadFlow)-ref;
                hxx+=gx*gx;hxy+=gx*gy;hyy+=gy*gy;bx+=gx*residual;by+=gy*residual;baseCost+=residual*residual;
            }
            float trace=hxx+hyy;
            float determinant=hxx*hyy-hxy*hxy;
            float conditioning=determinant/max(trace*trace,1.0e-12);
            vec2 delta=vec2(0.0);
            if(determinant>1.0e-10)delta=-vec2(hyy*bx-hxy*by,-hxy*bx+hxx*by)/determinant;
            bool bounded=all(lessThanEqual(abs(delta),vec2(0.25)));
            float newCost=baseCost;
            float oppositeCost=baseCost;
            if(bounded&&conditioning>0.012&&baseCost>1.0e-10){
                newCost=residualCost(centerQ,vec2(centerQ)+quadFlow+delta);
                oppositeCost=residualCost(centerQ,vec2(centerQ)+quadFlow-delta);
            }
            float improvement=(baseCost-newCost)/max(baseCost,1.0e-10);
            float uniqueness=(oppositeCost-newCost)/max(baseCost,1.0e-10);
            float variationRaw=base.z*length(vec2(uRawSize));
            bool accept=bounded&&conditioning>0.012&&improvement>0.08&&uniqueness>0.04&&variationRaw<2.0;
            vec2 refinedRaw=rawFlow+(accept?delta*2.0:vec2(0.0));
            oFlow=vec4(refinedRaw/vec2(uRawSize),base.z,accept?1.0:0.0);
        }
    """.trimIndent()

'''
replace_once(sh,anchor,shader+anchor,'insert true2x flow refinement shader')

# --- 3) stacker orchestration ---
st=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
replace_once(st,
'''    private var true2xMergeProgram26564 = 0
    private var true2xResolveProgram26564 = 0
''',
'''    private var true2xMergeProgram26564 = 0
    private var true2xFlowRefineProgram26574 = 0
    private var true2xResolveProgram26564 = 0
''','add flow refinement program owner')

# calls: reference and current gain raw texture ownership.
old='''                    useFrameWeight = false,
                    existingPhaseEvidence = true2xFastPhaseSlots,
                )
'''
new='''                    useFrameWeight = false,
                    existingPhaseEvidence = true2xFastPhaseSlots,
                    referenceRawTexture = referenceRaw,
                    currentRawTexture = referenceRaw,
                    referenceCalibration = referenceCalibration,
                )
'''
replace_once(st,old,new,'reference true2x evidence refinement inputs')
old='''                        useFrameWeight = true,
                        existingPhaseEvidence = true2xFastPhaseSlots,
                    )
'''
new='''                        useFrameWeight = true,
                        existingPhaseEvidence = true2xFastPhaseSlots,
                        referenceRawTexture = referenceRaw,
                        currentRawTexture = currentRaw,
                        referenceCalibration = referenceCalibration,
                    )
'''
replace_once(st,old,new,'alternate true2x evidence refinement inputs')

# signature.
old='''        useFrameWeight: Boolean,
        existingPhaseEvidence: Array<True2xFrameEvidence?>?,
    ): True2xFrameEvidence {
'''
new='''        useFrameWeight: Boolean,
        existingPhaseEvidence: Array<True2xFrameEvidence?>?,
        referenceRawTexture: Int,
        currentRawTexture: Int,
        referenceCalibration: FrameCalibration,
    ): True2xFrameEvidence {
'''
replace_once(st,old,new,'persist evidence refinement signature')

# selection readback variables: retain sparse until after selection, then optionally refine.
old='''        val (flowData, maxX, maxY) = readTrue2xFlow(flow)
        val spec = checkNotNull(textureSpecs[flow.texture])
        val phaseBin = dominantTrue2xPhaseBin(flowData, spec.width, spec.height)
'''
new='''        val (selectionFlowData, selectionMaxX, selectionMaxY) = readTrue2xFlow(flow)
        val spec = checkNotNull(textureSpecs[flow.texture])
        val phaseBin = dominantTrue2xPhaseBin(selectionFlowData, spec.width, spec.height)
'''
replace_once(st,old,new,'separate selection flow evidence')
replace_once(st,
'''                    LargeDirectBuffer.free(flowData)
''',
'''                    LargeDirectBuffer.free(selectionFlowData)
''','skip frees selection flow')

# Insert refinement after selection before covariance persistence.
anchor='''        val covarianceFile = File(directory, "iris26568_cov_${frameIndex}_${System.nanoTime()}.rgb10a2")
'''
insert='''        var persistedFlowData = selectionFlowData
        var persistedFlowWidth = spec.width
        var persistedFlowHeight = spec.height
        var persistedFlowScaleX = flow.scaleX
        var persistedFlowScaleY = flow.scaleY
        var persistedFlowOffsetX = flow.offsetX
        var persistedFlowOffsetY = flow.offsetY
        var persistedMaxX = selectionMaxX
        var persistedMaxY = selectionMaxY
        /* IRIS_26574_JPEG_RETAINED_FLOW_REFINEMENT_ONLY
         * Selection remains the exact 26568 global top-two-per-phase contract. Only after a frame
         * wins that bounded JPEG reservoir do we spend work on local SR alignment. DNG/full-evidence
         * mode is byte-semantically the 26573 sparse-flow path. Any GL/refinement failure keeps the
         * exact sparse flow rather than failing capture or introducing an unaligned fallback.
         */
        if (existingPhaseEvidence != null && frameIndex != 0) {
            runCatching {
                val refinedFlow = renderTrue2xFlowRefinement26574(
                    referenceRawTexture = referenceRawTexture,
                    currentRawTexture = currentRawTexture,
                    sparseFlow = flow,
                    referenceCalibration = referenceCalibration,
                    currentCalibration = calibration,
                )
                var refinedDataToFree: ByteBuffer? = null
                try {
                    val (refinedData, refinedMaxX, refinedMaxY) = readTrue2xFlow(refinedFlow)
                    refinedDataToFree = refinedData
                    val refineStats = true2xFlowRefineAcceptance(refinedData, refinedFlow)
                    val refinedSpec = checkNotNull(textureSpecs[refinedFlow.texture])
                    val previousFlowData = persistedFlowData
                    persistedFlowData = refinedData
                    refinedDataToFree = null
                    persistedFlowWidth = refinedSpec.width
                    persistedFlowHeight = refinedSpec.height
                    persistedFlowScaleX = refinedFlow.scaleX
                    persistedFlowScaleY = refinedFlow.scaleY
                    persistedFlowOffsetX = refinedFlow.offsetX
                    persistedFlowOffsetY = refinedFlow.offsetY
                    persistedMaxX = refinedMaxX
                    persistedMaxY = refinedMaxY
                    LargeDirectBuffer.free(previousFlowData)
                    val details = "frame=$frameIndex phase=$phaseBin accepted=${refineStats.first}/${refineStats.second} " +
                        "acceptedPct=${refineStats.third} deltaBoundRawPx=0.5"
                    PLog.i(SABRE_TAG, "IRIS_26574_TRUE2X_FLOW_REFINE $details")
                    PLog.i("MotionTrace", "PIPELINE_STATE stage=IRIS_26574_TRUE2X_FLOW_REFINE details=$details")
                } finally {
                    LargeDirectBuffer.free(refinedDataToFree)
                    runCatching { releaseOwnedTexture(refinedFlow.texture, "IRIS26574 true2x refined flow") }
                }
            }.onFailure { error ->
                PLog.e(SABRE_TAG, "IRIS_26574_TRUE2X_FLOW_REFINE_FALLBACK frame=$frameIndex reason=${error.message}", error)
            }
        }

'''
replace_once(st,anchor,insert+anchor,'insert retained-flow refinement')

# result fields use persisted flow.
for old,new,label in [
('''            flowData = flowData,
            flowWidth = spec.width,
            flowHeight = spec.height,
            flowScaleX = flow.scaleX,
            flowScaleY = flow.scaleY,
            flowOffsetX = flow.offsetX,
            flowOffsetY = flow.offsetY,
''','''            flowData = persistedFlowData,
            flowWidth = persistedFlowWidth,
            flowHeight = persistedFlowHeight,
            flowScaleX = persistedFlowScaleX,
            flowScaleY = persistedFlowScaleY,
            flowOffsetX = persistedFlowOffsetX,
            flowOffsetY = persistedFlowOffsetY,
''','persist refined flow fields'),
('''            maxAbsFlowPixelsX = maxX,
            maxAbsFlowPixelsY = maxY,
''','''            maxAbsFlowPixelsX = persistedMaxX,
            maxAbsFlowPixelsY = persistedMaxY,
''','persist refined flow bounds')]: replace_once(st,old,new,label)

# Insert helper functions before persistTrue2xEvidence.
anchor='''    private fun persistTrue2xEvidence(
'''
helpers='''    private fun renderTrue2xFlowRefinement26574(
        referenceRawTexture: Int,
        currentRawTexture: Int,
        sparseFlow: SabreConvertedAlignment,
        referenceCalibration: FrameCalibration,
        currentCalibration: FrameCalibration,
    ): SabreConvertedAlignment {
        if (true2xFlowRefineProgram26574 == 0) {
            true2xFlowRefineProgram26574 = linkProgram(
                GlesMgcRawSabreShaders.true2xFlowRefine26574,
                "iris_26574_true2x_flow_refine",
            )
        }
        val outputWidth = ceilDiv(width, TRUE2X_REFINE_CELL_RAW_PIXELS)
        val outputHeight = ceilDiv(height, TRUE2X_REFINE_CELL_RAW_PIXELS)
        val output = createTexture(outputWidth, outputHeight, GLES30.GL_RGBA16F, GLES30.GL_LINEAR)
        val program = true2xFlowRefineProgram26574
        GLES30.glUseProgram(program)
        bindTexture(program, "uReferenceRaw", 0, referenceRawTexture)
        bindTexture(program, "uCurrentRaw", 1, currentRawTexture)
        bindTexture(program, "uSparseFlow", 2, sparseFlow.texture)
        uniform2i(program, "uRawSize", width, height)
        uniform2i(program, "uOutputSize", outputWidth, outputHeight)
        uniform4f(program, "uSparseFlowScaleOffset", sparseFlow.scaleX, sparseFlow.scaleY, sparseFlow.offsetX, sparseFlow.offsetY)
        uniform4fv(program, "uReferencePhaseGains", referenceCalibration.bayerPhaseGains)
        uniform4fv(program, "uReferencePhaseBlackTerms", referenceCalibration.bayerPhaseBlackTerms)
        uniform4fv(program, "uCurrentPhaseGains", currentCalibration.bayerPhaseGains)
        uniform4fv(program, "uCurrentPhaseBlackTerms", currentCalibration.bayerPhaseBlackTerms)
        draw(program, outputWidth, outputHeight, intArrayOf(output))
        checkGlError("IRIS26574 true2x flow refinement")
        return SabreConvertedAlignment(output, 1f, 1f, 0f, 0f)
    }

    private fun true2xFlowRefineAcceptance(
        flowData: ByteBuffer,
        flow: SabreConvertedAlignment,
    ): Triple<Int, Int, Float> {
        val spec = checkNotNull(textureSpecs[flow.texture])
        val values = flowData.duplicate().order(ByteOrder.nativeOrder()).asShortBuffer()
        val pixels = spec.width * spec.height
        var accepted = 0
        for (index in 0 until pixels) {
            val confidence = Half.toFloat(values.get(index * 4 + 3))
            if (confidence.isFinite() && confidence > 0.5f) accepted++
        }
        val pct = if (pixels > 0) 100f * accepted.toFloat() / pixels.toFloat() else 0f
        return Triple(accepted, pixels, pct)
    }

'''
replace_once(st,anchor,helpers+anchor,'insert true2x refinement helpers')

# constant.
old='''        private const val TRUE2X_GPU_TILE_HEIGHT = 128
        private const val TRUE2X_JPEG_EVIDENCE_PER_PHASE = 2
'''
new='''        private const val TRUE2X_GPU_TILE_HEIGHT = 128
        /* 16 RAW pixels = 8 Bayer quads. This is four times denser per axis than the finest
         * ~32-Bayer-quad LK grid while remaining a small bounded flow sidecar (~255x192 at 4080x3064).
         */
        private const val TRUE2X_REFINE_CELL_RAW_PIXELS = 16
        private const val TRUE2X_JPEG_EVIDENCE_PER_PHASE = 2
'''
replace_once(st,old,new,'add bounded refine cell constant')

# Harden the ownership comment to document that bright chroma is protected only by proven topology.
replace_once(vgn,'''     * across it. No target may exceed the center chroma magnitude, and highlight preservation is
     * disabled so prior pink/magenta false-color suppression remains authoritative.
''','''     * across it. No target may exceed the center chroma magnitude. Bright chroma remains unprotected
     * unless 26574 radius-2 topology proves a continuing surface, preserving pink/magenta cleanup.
''','update VGN ownership comment')

# --- 4) version ---
ver=Path('app/version.properties')
p=C/ver
s=p.read_text()
s2=re.sub(r'^VERSION_NAME=.*$', 'VERSION_NAME=0.9726574', s, flags=re.M)
s2=re.sub(r'^VERSION_BUILD=.*$', 'VERSION_BUILD=26574', s2, flags=re.M)
if s2==s: raise SystemExit('FAIL version anchors')
p.write_text(s2)
print('PASS version 26574')

# scope check
base=BASE
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def mani(root): return {str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file()}
a=mani(base);b=mani(C)
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
expected=sorted([
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/version.properties'])
print('CHANGED',*changed,sep='\n')
if changed!=expected: raise SystemExit(f'FAIL scope {changed}')
print('PASS exact four-file scope')
