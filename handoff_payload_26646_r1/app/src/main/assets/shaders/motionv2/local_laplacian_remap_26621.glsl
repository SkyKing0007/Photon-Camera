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

        /* IRIS_26635_SPATIALLY_COHERENT_HIGHLIGHT_ROLLOFF
         * B is the already-mapped low-frequency illumination owner.  Give B a small continuous
         * asymptotic lift toward white (no target-white plateau), then carry the structural
         * residual R with a bounded highlight weight. Small residuals are gently suppressed in
         * bright fields; strong slats/folds/specular geometry retain unit weight. */
        float upperGate=smoothstep(0.65,0.985,baseLinear);
        float shoulderGate=smoothstep(0.70,0.985,baseLinear);
        vec3 iris26646Radiance=iris26646SourceRadianceSurvival(p);
        float sourceStructureGate=max(max(iris26644SourceStructure(p),iris26645SourceTexture(p)),iris26646Radiance.z);
        float smoothShoulder=1.0-pow(max(1.0-baseLinear,0.0),1.12);
        /* IRIS_26645_STRUCTURE_AWARE_HIGHLIGHT_BASE
         * Smooth bright illumination keeps the successful 26635 shoulder. Real source texture
         * retains more base headroom so grass/pavement/fabric is not lifted into one pale plateau. */
        float structureShoulderScale=1.0-0.72*sourceStructureGate;
        float baseOut=mix(baseLinear,smoothShoulder,
            0.55*shoulderGate*structureShoulderScale);

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
        float structureGate=smoothstep(0.012,0.045,abs(residual));
        float smallResidualWeight=mix(1.0,0.78,upperGate);
        /* IRIS_26644_VISUAL_HIGHLIGHT_STRUCTURE_PRESERVATION
         * Keep 26635 suppression only for genuinely smooth bright-field residuals. If the
         * pre-tone source independently proves real local structure, preserve that residual. */
        float residualWeight=mix(
                smallResidualWeight,1.0,max(structureGate,sourceStructureGate));
        float weightedResidual=residualWeight*residual;
        float candidateLinear=shadowBase+weightedResidual;
        /* IRIS_26645_STRUCTURAL_HEADROOM_RESERVATION
         * When real pre-tone structure would otherwise hit the display ceiling, lower only B by
         * exactly the proven positive overshoot. R remains unchanged, so the saved SDR retains its
         * local separation instead of becoming a clipped-looking sub-white plateau. */
        float positiveOvershoot=max(candidateLinear-0.997,0.0);
        float protectedBase=max(shadowBase-sourceStructureGate*positiveOvershoot,
            IRIS_26626_LOG_FLOOR);
        float outLinear=clamp(protectedBase+weightedResidual,IRIS_26626_LOG_FLOOR,1.0);
        /* IRIS_26646_EXTENDED_LINEAR_RADIANCE_SURVIVAL_OWNER
         * 26645 only used SourceLinear as a texture gate.  Carry the measured missing source
         * residual itself into the scalar tone result, while reserving bounded headroom in the
         * same structured region.  This is luminance-only presentation: final RGB continues to use
         * one common scalar, so CFA/chroma/hue ownership is untouched. */
        float reserveEv=0.40*iris26646Radiance.y*iris26646Radiance.z*upperGate;
        float outLog=log2(max(outLinear,IRIS_26626_LOG_FLOOR))-reserveEv
                +iris26646Radiance.x*iris26646Radiance.z;
        Output=clamp(outLog,-12.0,0.0);
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
