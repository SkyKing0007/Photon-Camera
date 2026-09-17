precision highp float;
precision highp int;
precision mediump sampler2D;

uniform sampler2D GlobalMappedLog;
uniform sampler2D SourceLinear;
uniform sampler2D SourceGuideLog;
uniform sampler2D LocalBand;
uniform sampler2D CoarseReconstruction;
uniform sampler2D CurrentToneLog;
uniform sampler2D DeltaLog;
uniform float referenceLog;
uniform float sourceReferenceLog;
uniform float mappedReferenceLog;
uniform float sigmaEv;
uniform float edgeSlope;
uniform float iris26626PreservationStrength;
uniform float iris26639ShadowBodyStrength;
uniform float iris26639ShadowBodyEnd;
uniform int iris26626Mode;
uniform int iris26655BodyReferenceOnly;
out float Output;

/* IRIS_26621_TRUE_LOCAL_LAPLACIAN_REMAP
 * Mode 0 is the exact successful-26625 remap equation. Other modes are 26626-only helpers used
 * inside the same Local-Laplacian owner; none changes the protected reduce/accumulate/reconstruct
 * shaders or the final uniform-RGB render owner. */
const vec3 IRIS_26626_LUMA=vec3(0.22897456,0.69173852,0.07928691);
const float IRIS_26626_LOG_FLOOR=0.000244140625; /* 2^-12 */

float irisRemapDelta(float x,float center){
    float d=x-center;
    float a=abs(d);
    float mapped=a<=sigmaEv ? a : sigmaEv+edgeSlope*(a-sigmaEv);
    return d<0.0 ? -mapped : mapped;
}
float iris26626SourceGuide(vec3 rgb){
    rgb=max(rgb,vec3(0.0));
    float y=dot(rgb,IRIS_26626_LUMA);
    float peak=max(rgb.r,max(rgb.g,rgb.b));
    return max(y,peak);
}
float irisAt(sampler2D tex,ivec2 p){
    ivec2 sz=textureSize(tex,0);
    return texelFetch(tex,clamp(p,ivec2(0),sz-ivec2(1)),0).r;
}
void irisAxis(int fineCoord,out int base,out float wm,out float wc,out float wp){
    base=fineCoord/2;
    if((fineCoord&1)==0){wm=0.125;wc=0.750;wp=0.125;}
    else{wm=0.0;wc=0.5;wp=0.5;}
}
float irisExpand(sampler2D tex,ivec2 p){
    int bx,by;float wxm,wxc,wxp,wym,wyc,wyp;
    irisAxis(p.x,bx,wxm,wxc,wxp);irisAxis(p.y,by,wym,wyc,wyp);
    float sum=0.0;
    sum+=irisAt(tex,ivec2(bx-1,by-1))*(wxm*wym);
    sum+=irisAt(tex,ivec2(bx  ,by-1))*(wxc*wym);
    sum+=irisAt(tex,ivec2(bx+1,by-1))*(wxp*wym);
    sum+=irisAt(tex,ivec2(bx-1,by  ))*(wxm*wyc);
    sum+=irisAt(tex,ivec2(bx  ,by  ))*(wxc*wyc);
    sum+=irisAt(tex,ivec2(bx+1,by  ))*(wxp*wyc);
    sum+=irisAt(tex,ivec2(bx-1,by+1))*(wxm*wyp);
    sum+=irisAt(tex,ivec2(bx  ,by+1))*(wxc*wyp);
    sum+=irisAt(tex,ivec2(bx+1,by+1))*(wxp*wyp);
    return sum;
}

/* IRIS_26644_VISUAL_HIGHLIGHT_SOURCE_STRUCTURE_OWNER
 * 26635 intentionally reduced small residuals in bright fields, but that also attenuated real
 * pavement/fabric/foliage microstructure when its residual amplitude happened to be small after
 * reconstruction. Detect only balanced structure physically present in the pre-tone linear source.
 * Required opposite samples must exist; image borders fail closed instead of repeating edge texels. */
float iris26644SourceStructure(ivec2 p){
    ivec2 sz=textureSize(SourceLinear,0);
    float center=log2(max(iris26626SourceGuide(texelFetch(SourceLinear,p,0).rgb),IRIS_26626_LOG_FLOOR));
    float evidence=0.0;
    const int R0=2;
    const int R1=6;
    const int R2=16;
    for(int k=0;k<3;k++){
        int r=k==0?R0:(k==1?R1:R2);
        if(p.x-r<0||p.x+r>=sz.x||p.y-r<0||p.y+r>=sz.y) continue;
        float l=log2(max(iris26626SourceGuide(texelFetch(SourceLinear,p-ivec2(r,0),0).rgb),IRIS_26626_LOG_FLOOR));
        float rr=log2(max(iris26626SourceGuide(texelFetch(SourceLinear,p+ivec2(r,0),0).rgb),IRIS_26626_LOG_FLOOR));
        float u=log2(max(iris26626SourceGuide(texelFetch(SourceLinear,p-ivec2(0,r),0).rgb),IRIS_26626_LOG_FLOOR));
        float d=log2(max(iris26626SourceGuide(texelFetch(SourceLinear,p+ivec2(0,r),0).rgb),IRIS_26626_LOG_FLOOR));
        float ax0=abs(center-l),ax1=abs(center-rr);
        float ay0=abs(center-u),ay1=abs(center-d);
        float axMax=max(ax0,ax1),ayMax=max(ay0,ay1);
        float balanceX=axMax>0.002?min(ax0,ax1)/axMax:0.0;
        float balanceY=ayMax>0.002?min(ay0,ay1)/ayMax:0.0;
        float curvatureX=abs(center-0.5*(l+rr));
        float curvatureY=abs(center-0.5*(u+d));
        evidence=max(evidence,max(balanceX*curvatureX,balanceY*curvatureY));
    }
    return smoothstep(0.0035,0.020,evidence);
}
/* IRIS_26645_VISUAL_TEXTURE_ENERGY_OWNER
 * 26644's balanced-curvature proof is intentionally conservative and misses stochastic but coherent
 * grass/pine-straw/foliage texture. Require at least two directional neighbors at two local scales;
 * a single material boundary cannot qualify. All support fails closed at image borders. */
float iris26645SourceTexture(ivec2 p){
    ivec2 sz=textureSize(SourceLinear,0);
    float center=log2(max(iris26626SourceGuide(texelFetch(SourceLinear,p,0).rgb),IRIS_26626_LOG_FLOOR));
    float evidence=0.0;
    for(int k=0;k<2;k++){
        int r=k==0?2:6;
        if(p.x-r<0||p.x+r>=sz.x||p.y-r<0||p.y+r>=sz.y) continue;
        float dl=abs(center-log2(max(iris26626SourceGuide(texelFetch(SourceLinear,p-ivec2(r,0),0).rgb),IRIS_26626_LOG_FLOOR)));
        float dr=abs(center-log2(max(iris26626SourceGuide(texelFetch(SourceLinear,p+ivec2(r,0),0).rgb),IRIS_26626_LOG_FLOOR)));
        float du=abs(center-log2(max(iris26626SourceGuide(texelFetch(SourceLinear,p-ivec2(0,r),0).rgb),IRIS_26626_LOG_FLOOR)));
        float dd=abs(center-log2(max(iris26626SourceGuide(texelFetch(SourceLinear,p+ivec2(0,r),0).rgb),IRIS_26626_LOG_FLOOR)));
        float first=0.0,second=0.0;
        float ds[4]=float[4](dl,dr,du,dd);
        for(int i=0;i<4;i++){
            float v=ds[i];
            if(v>=first){second=first;first=v;}
            else if(v>second){second=v;}
        }
        evidence=max(evidence,second);
    }
    return smoothstep(0.010,0.055,evidence);
}

/* IRIS_26646_EDGE_ISOLATED_SOURCE_RADIANCE_SURVIVAL
 * Preserve only radiance separation that is already present in the extended-linear HDR master and
 * that also lives inside one local material region.  At each scale at least three of four cardinal
 * neighbors must remain within a tight source-log interval of the center; this deliberately fails
 * closed on tree/sky, branch/sky, hair/window and other one-sided high-contrast boundaries.  The
 * returned x is only the missing signed source residual (EV), y its magnitude, z the confidence.
 * No RGB channel is reconstructed and no neighbor can contribute across an admitted strong edge. */
vec3 iris26646SourceRadianceSurvival(ivec2 p){
    ivec2 sz=textureSize(SourceLinear,0);
    float srcCenter=log2(max(iris26626SourceGuide(texelFetch(SourceLinear,p,0).rgb),IRIS_26626_LOG_FLOOR));
    float toneCenter=texelFetch(CurrentToneLog,p,0).r;
    float highGate=smoothstep(log2(0.34),log2(0.62),srcCenter);
    if(highGate<=0.0) return vec3(0.0);
    vec3 best=vec3(0.0);
    for(int k=0;k<2;k++){
        int r=k==0?2:6;
        if(p.x-r<0||p.x+r>=sz.x||p.y-r<0||p.y+r>=sz.y) continue;
        ivec2 q[4]=ivec2[4](p-ivec2(r,0),p+ivec2(r,0),p-ivec2(0,r),p+ivec2(0,r));
        float srcSum=0.0,toneSum=0.0,weightSum=0.0;
        int admitted=0;
        for(int i=0;i<4;i++){
            float sl=log2(max(iris26626SourceGuide(texelFetch(SourceLinear,q[i],0).rgb),IRIS_26626_LOG_FLOOR));
            float d=abs(sl-srcCenter);
            float sameMaterial=1.0-smoothstep(0.24,0.34,d);
            if(sameMaterial>0.50) admitted++;
            srcSum+=sameMaterial*sl;
            toneSum+=sameMaterial*texelFetch(CurrentToneLog,q[i],0).r;
            weightSum+=sameMaterial;
        }
        if(admitted<3||weightSum<2.55) continue;
        float srcBase=srcSum/weightSum;
        float toneBase=toneSum/weightSum;
        float srcResidual=srcCenter-srcBase;
        float toneResidual=toneCenter-toneBase;
        float sourceMagnitude=abs(srcResidual);
        float toneMagnitude=abs(toneResidual);
        float signAgreement=(srcResidual*toneResidual>=0.0||toneMagnitude<0.003)?1.0:0.0;
        float missing=max(sourceMagnitude-toneMagnitude-0.004,0.0);
        float structure=smoothstep(0.012,0.075,sourceMagnitude);
        float missingGate=smoothstep(0.006,0.055,missing);
        float confidence=highGate*structure*missingGate*signAgreement;
        float boundedMissing=min(missing,0.18);
        vec3 candidate=vec3(sign(srcResidual)*boundedMissing,boundedMissing,confidence);
        if(candidate.z*candidate.y>best.z*best.y) best=candidate;
    }
    return best;
}

/* IRIS_26655_UNIVERSAL_SOURCE_FINE_STRUCTURE_EVIDENCE
 * Semantic-independent high-frequency evidence in source log-radiance. Small-radius curvature
 * responds to text/ribs/foliage/fabric/hair/mesh/edges but rejects smooth illumination gradients.
 * 26644/26645 remain supporting evidence only; no detector directly changes absolute brightness. */
float iris26655SourceFineStructure(ivec2 p){
    ivec2 sz=textureSize(SourceLinear,0);
    if(p.x<2||p.y<2||p.x+2>=sz.x||p.y+2>=sz.y) return 0.0;
    float c=log2(max(iris26626SourceGuide(texelFetch(SourceLinear,p,0).rgb),IRIS_26626_LOG_FLOOR));
    float evidence=0.0;
    for(int k=0;k<2;k++){
        int r=k==0?1:2;
        float l=log2(max(iris26626SourceGuide(texelFetch(SourceLinear,p-ivec2(r,0),0).rgb),IRIS_26626_LOG_FLOOR));
        float rr=log2(max(iris26626SourceGuide(texelFetch(SourceLinear,p+ivec2(r,0),0).rgb),IRIS_26626_LOG_FLOOR));
        float u=log2(max(iris26626SourceGuide(texelFetch(SourceLinear,p-ivec2(0,r),0).rgb),IRIS_26626_LOG_FLOOR));
        float d=log2(max(iris26626SourceGuide(texelFetch(SourceLinear,p+ivec2(0,r),0).rgb),IRIS_26626_LOG_FLOOR));
        float curvature=abs(c-0.25*(l+rr+u+d));
        evidence=max(evidence,k==0?curvature:0.70*curvature);
    }
    return smoothstep(0.004,0.028,evidence);
}

/* IRIS_26655_EDGE_AWARE_ILLUMINATION_BASE
 * Joint-bilateral reconstruction of the coarse source-domain log-radiance field. The pyramid
 * itself is range-aware, and this final reconstruction uses the full-resolution source only as
 * a radiometric guide. Smooth illumination gradients may differ substantially from their local
 * source pixel and remain smooth; strong material/exposure discontinuities reject coarse samples
 * from the opposite side. No semantic/object classification is used. */
float iris26655EdgeAwareBaseLog(ivec2 p){
    ivec2 fineSize=textureSize(SourceLinear,0);
    ivec2 baseSize=textureSize(SourceGuideLog,0);
    float sourceLog=log2(max(iris26626SourceGuide(texelFetch(SourceLinear,p,0).rgb),IRIS_26626_LOG_FLOOR));
    vec2 coarsePos=(vec2(p)+vec2(0.5))*vec2(baseSize)/vec2(fineSize)-vec2(0.5);
    ivec2 c0=ivec2(floor(coarsePos));
    float sum=0.0;
    float weightSum=0.0;
    for(int oy=-1;oy<=2;oy++){
        for(int ox=-1;ox<=2;ox++){
            ivec2 q=clamp(c0+ivec2(ox,oy),ivec2(0),baseSize-ivec2(1));
            float v=texelFetch(SourceGuideLog,q,0).r;
            vec2 d=coarsePos-vec2(q);
            float sx=max(1.5-abs(d.x),0.0);
            float sy=max(1.5-abs(d.y),0.0);
            float spatial=sx*sy;
            float ev=(v-sourceLog)/0.75;
            float rangeWeight=exp(-0.5*ev*ev);
            float w=spatial*rangeWeight;
            sum+=v*w;
            weightSum+=w;
        }
    }
    return weightSum>1.0e-8?sum/weightSum:sourceLog;
}

void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);

    if(iris26626Mode==1){
        float sourceGuide=iris26626SourceGuide(texelFetch(SourceLinear,p,0).rgb);
        Output=log2(max(sourceGuide,IRIS_26626_LOG_FLOOR));
        return;
    }
    if(iris26626Mode==2){
        float sourceGuide=iris26626SourceGuide(texelFetch(SourceLinear,p,0).rgb);
        float sourceLog=log2(max(sourceGuide,IRIS_26626_LOG_FLOOR));
        Output=mappedReferenceLog+irisRemapDelta(sourceLog,sourceReferenceLog);
        return;
    }
    if(iris26626Mode==3){
        Output=exp2(texelFetch(SourceGuideLog,p,0).r);
        return;
    }
    if(iris26626Mode==4){
        float sourceReconstruction=texelFetch(LocalBand,p,0).r+irisExpand(CoarseReconstruction,p);
        Output=sourceReconstruction-texelFetch(CurrentToneLog,p,0).r;
        return;
    }
    if(iris26626Mode==6){
        float currentLog=texelFetch(CurrentToneLog,p,0).r;
        ivec2 fineSize=textureSize(CurrentToneLog,0);
        ivec2 baseSize=textureSize(SourceGuideLog,0);
        vec2 uv=(vec2(p)+vec2(0.5))/vec2(fineSize);
        vec2 baseHalfTexel=vec2(0.5)/vec2(baseSize);
        float baseLog=texture(SourceGuideLog,clamp(uv,baseHalfTexel,vec2(1.0)-baseHalfTexel)).r;
        float currentLinear=exp2(clamp(currentLog,-12.0,0.0));
        float baseLinear=exp2(clamp(baseLog,-12.0,0.0));
        float residual=currentLinear-baseLinear;

        /* IRIS_26655_LEGACY_HC_OFF_LOCAL_PRESENTATION_ONLY
         * Mode 6 is retained exclusively for the proven HC-OFF/lower-body reference. The HC-ON
         * upper-range owner is mode 8 and never consumes the 26635/26645/26646 direct tone math.
         *
         * IRIS_26654_LOCAL_LAPLACIAN_NO_HIGHLIGHT_TOGGLE_AUTHORITY
         * Local Laplacian deliberately does not know whether Highlight Compression is enabled.
         * It always reconstructs the inherited legacy local candidate. When HC is ON the final
         * render/gainmap may consume only its bounded zero-DC source-structure residual; absolute
         * upper-range brightness is owned by the post-brightness global 26654 tone. */
        float upperGate=smoothstep(0.65,0.985,baseLinear);
        float shoulderGate=smoothstep(0.70,0.985,baseLinear);
        /* IRIS_26655_HC_ON_BODY_REFERENCE_NEUTRALIZES_OLD_HIGHLIGHT_OWNERS
         * When HC is ON this legacy reconstruction is needed only for the validated body below
         * the 0.65 entry. Fade all old 26635/26645/26646 highlight brightness operations out over
         * the same 0.65..0.72 ownership handoff used by mode 8; HC-OFF remains byte-semantic legacy. */
        float bodyReferenceFade=iris26655BodyReferenceOnly!=0?smoothstep(0.65,0.72,baseLinear):0.0;
        vec3 iris26646Radiance=iris26655BodyReferenceOnly!=0?vec3(0.0):iris26646SourceRadianceSurvival(p);
        float sourceStructureGate=max(max(iris26644SourceStructure(p),iris26645SourceTexture(p)),iris26646Radiance.z);
        float smoothShoulder=1.0-pow(max(1.0-baseLinear,0.0),1.12);
        float structureShoulderScale=1.0-0.72*sourceStructureGate;
        float legacyBaseOut=mix(baseLinear,smoothShoulder,
            0.55*shoulderGate*structureShoulderScale*(1.0-bodyReferenceFade));
        float baseOut=legacyBaseOut;

        /* IRIS_26639_SIGNAL_DRIVEN_SHADOW_BASE
         * Correct only the low-frequency base B. The 0.05 true-floor endpoint and the scene-derived
         * upper body endpoint are exact identity with zero derivative change. A quartic C1 bump
         * reaches at most 0.25 EV at its center; the structural residual R is added afterward and is
         * never multiplied by this correction. */
        const float shadowFloorEnd=0.050;
        float bodyEnd=clamp(iris26639ShadowBodyEnd,0.18,0.42);
        float bodyStrength=clamp(iris26639ShadowBodyStrength,0.0,1.0);
        float bodyT=clamp((baseOut-shadowFloorEnd)/max(bodyEnd-shadowFloorEnd,1.0e-6),0.0,1.0);
        float bodyBump=16.0*bodyT*bodyT*(1.0-bodyT)*(1.0-bodyT);
        float bodyScale=exp2(-0.25*bodyStrength*bodyBump);
        float shadowBase=baseOut*bodyScale;
        /* IRIS_26654_LOCAL_DETAIL_CANDIDATE_ONLY
         * Keep the inherited structural measurements, but they no longer own absolute highlight
         * brightness. 26635/26645/26646 may shape this local candidate only; the HC-ON consumer
         * removes its local DC component and admits a bounded residual only where the source proves
         * real structure. */
        float structureGate=smoothstep(0.012,0.045,abs(residual));
        float smallResidualWeight=mix(1.0,0.78,upperGate);
        float legacyResidualWeight=mix(
                smallResidualWeight,1.0,max(structureGate,sourceStructureGate));
        float residualWeight=legacyResidualWeight;
        float weightedResidual=residualWeight*residual;
        float candidateLinear=shadowBase+weightedResidual;
        /* IRIS_26645_LEGACY_LOCAL_CANDIDATE_HEADROOM
         * When real pre-tone structure would otherwise hit the display ceiling, lower only B by
         * exactly the proven positive overshoot. R remains unchanged, so the saved SDR retains its
         * local separation instead of becoming a clipped-looking sub-white plateau. */
        float positiveOvershoot=max(candidateLinear-0.997,0.0);
        float protectedBase=max(shadowBase-sourceStructureGate*positiveOvershoot*(1.0-bodyReferenceFade),
            IRIS_26626_LOG_FLOOR);
        float outLinear=clamp(protectedBase+weightedResidual,IRIS_26626_LOG_FLOOR,1.0);
        /* IRIS_26646_LEGACY_LOCAL_CANDIDATE_RADIANCE
         * 26645 only used SourceLinear as a texture gate.  Carry the measured missing source
         * residual itself into the scalar tone result, while reserving bounded headroom in the
         * same structured region.  This is luminance-only presentation: final RGB continues to use
         * one common scalar, so CFA/chroma/hue ownership is untouched. */
        float reserveEv=0.40*iris26646Radiance.y*iris26646Radiance.z*upperGate*(1.0-bodyReferenceFade);
        float outLog=log2(max(outLinear,IRIS_26626_LOG_FLOOR))-reserveEv
                +iris26646Radiance.x*iris26646Radiance.z*(1.0-bodyReferenceFade);
        Output=clamp(outLog,-12.0,0.0);
        return;
    }
    if(iris26626Mode==7){
        /* IRIS_26655_SOURCE_DOMAIN_ILLUMINATION_BASE_EXPAND
         * SourceGuideLog is the resolution-relative coarse B pyramid in source log-radiance.
         * Bilinear interpolation stays in log space; exp2 produces a positive extended-linear base. */
        float baseLog=iris26655EdgeAwareBaseLog(p);
        Output=exp2(max(baseLog,-12.0));
        return;
    }
    if(iris26626Mode==8){
        /* IRIS_26655_SOURCE_DOMAIN_B_PLUS_R_FINAL_COMPOSITE
         * CurrentToneLog = exact inherited legacy presentation used below 0.65.
         * DeltaLog       = T(B), the final pointwise tone applied to broad source-domain base B.
         * GlobalMappedLog= T(S), the same tone applied to original source S.
         * Only high-frequency source evidence may admit bounded R = T(S)-T(B). Broad gradients,
         * smooth ceilings, screens and walls therefore follow B instead of forming a bright island.
         * Ownership is driven by max(S,B): ordinary body pixels remain legacy-exact unless the broad
         * illumination field itself proves they belong to the highlight transition. */
        float sourceGuide=iris26626SourceGuide(texelFetch(SourceLinear,p,0).rgb);
        float baseLog=iris26655EdgeAwareBaseLog(p);
        float baseSource=exp2(max(baseLog,-12.0));
        float highlightGuide=max(sourceGuide,baseSource);
        float legacy=exp2(clamp(texelFetch(CurrentToneLog,p,0).r,-12.0,0.0));
        float pointMapped=exp2(clamp(texelFetch(GlobalMappedLog,p,0).r,-12.0,0.0));
        float baseMapped=exp2(clamp(texelFetch(DeltaLog,p,0).r,-12.0,0.0));
        float fine=iris26655SourceFineStructure(p);
        float texture=iris26645SourceTexture(p);
        float balanced=iris26644SourceStructure(p);
        float localEvidence=max(fine,0.85*texture);
        float structure=clamp(max(localEvidence,0.60*balanced*localEvidence),0.0,1.0);
        float upper=smoothstep(0.65,1.15,highlightGuide);
        float maxAbs=mix(0.035,0.100,upper);
        float detail=clamp(pointMapped-baseMapped,-maxAbs,maxAbs)*structure;
        float spatial=clamp(baseMapped+detail,IRIS_26626_LOG_FLOOR,1.0);
        float owner=smoothstep(0.65,0.72,highlightGuide);
        float finalLinear=mix(legacy,spatial,owner);
        Output=log2(max(finalLinear,IRIS_26626_LOG_FLOOR));
        return;
    }
    if(iris26626Mode==5){
        float sourceGuide=iris26626SourceGuide(texelFetch(SourceLinear,p,0).rgb);
        float sourceLog=log2(max(sourceGuide,IRIS_26626_LOG_FLOOR));
        float upperGate=smoothstep(0.65,0.72,sourceGuide)
                *(1.0-smoothstep(0.98,1.05,sourceGuide));
        float current=texelFetch(CurrentToneLog,p,0).r;
        float delta=texelFetch(DeltaLog,p,0).r;

        /* IRIS_26626_FAIL_CLOSED_SOURCE_STRUCTURE_GATE
         * The source-domain candidate may only preserve structure that is locally present in the
         * source itself.  A one-sided material step has zero balance; a flat bright plateau beside
         * a distant edge has zero curvature.  Symmetric ridges/valleys and smooth curved fields may
         * contribute, but the correction is capped by their measured source-log curvature so it
         * cannot invent or over-amplify contrast.  Radii are tied to existing Local-Laplacian scales. */
        float allowed=0.0;
        const int IRIS_26626_R0=4;
        const int IRIS_26626_R1=16;
        const int IRIS_26626_R2=32;
        for(int k=0;k<3;k++){
            int r=k==0?IRIS_26626_R0:(k==1?IRIS_26626_R1:IRIS_26626_R2);
            ivec2 dx=ivec2(r,0);
            ivec2 dy=ivec2(0,r);
            float lx=log2(max(iris26626SourceGuide(texelFetch(SourceLinear,clamp(p-dx,ivec2(0),textureSize(SourceLinear,0)-ivec2(1)),0).rgb),IRIS_26626_LOG_FLOOR));
            float rx=log2(max(iris26626SourceGuide(texelFetch(SourceLinear,clamp(p+dx,ivec2(0),textureSize(SourceLinear,0)-ivec2(1)),0).rgb),IRIS_26626_LOG_FLOOR));
            float uy=log2(max(iris26626SourceGuide(texelFetch(SourceLinear,clamp(p-dy,ivec2(0),textureSize(SourceLinear,0)-ivec2(1)),0).rgb),IRIS_26626_LOG_FLOOR));
            float dyv=log2(max(iris26626SourceGuide(texelFetch(SourceLinear,clamp(p+dy,ivec2(0),textureSize(SourceLinear,0)-ivec2(1)),0).rgb),IRIS_26626_LOG_FLOOR));

            float ax0=abs(sourceLog-lx), ax1=abs(sourceLog-rx);
            float ay0=abs(sourceLog-uy), ay1=abs(sourceLog-dyv);
            float axMax=max(ax0,ax1), ayMax=max(ay0,ay1);
            float bx=axMax>0.003 ? min(ax0,ax1)/axMax : 0.0;
            float by=ayMax>0.003 ? min(ay0,ay1)/ayMax : 0.0;
            float cx=sourceLog-0.5*(lx+rx);
            float cy=sourceLog-0.5*(uy+dyv);
            float sx=(cx*delta)>0.0 ? bx*abs(cx) : 0.0;
            float sy=(cy*delta)>0.0 ? by*abs(cy) : 0.0;
            allowed=max(allowed,max(sx,sy));
        }
        allowed=min(allowed,0.20); /* pre-strength EV cap; max final correction <=0.06 EV */
        float correction=sign(delta)*min(abs(delta),allowed);
        Output=current+upperGate*clamp(iris26626PreservationStrength,0.0,0.30)*correction;
        return;
    }

    /* Mode 0: byte-equivalent successful-26625 scalar equation. */
    float x=texelFetch(GlobalMappedLog,p,0).r;
    Output=referenceLog+irisRemapDelta(x,referenceLog);
}
