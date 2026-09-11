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
