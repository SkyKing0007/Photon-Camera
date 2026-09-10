precision highp float;
precision highp int;
precision mediump sampler2D;

uniform sampler2D Accumulator;
uniform sampler2D RemapFine;
uniform sampler2D RemapCoarse;
uniform sampler2D GuideLevel;
uniform float referenceLog;
uniform float referenceStep;
uniform float referenceMin;
uniform float referenceMax;
uniform int firstReference;
out float Output;

/* IRIS_26621_MATCHED_PYRAMID_EXPAND
 * Exact phase-matched EXPAND companion to the centered [1 4 6 4 1]/16 REDUCE filter.
 * Even fine coordinates use [1 6 1]/8 on coarse samples; odd coordinates use [1 1]/2.
 * The separable weights sum to one at every pixel, including clamped image boundaries. */
float irisCoarseAt(sampler2D tex,ivec2 p){
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
    sum+=irisCoarseAt(tex,ivec2(bx-1,by-1))*(wxm*wym);
    sum+=irisCoarseAt(tex,ivec2(bx  ,by-1))*(wxc*wym);
    sum+=irisCoarseAt(tex,ivec2(bx+1,by-1))*(wxp*wym);
    sum+=irisCoarseAt(tex,ivec2(bx-1,by  ))*(wxm*wyc);
    sum+=irisCoarseAt(tex,ivec2(bx  ,by  ))*(wxc*wyc);
    sum+=irisCoarseAt(tex,ivec2(bx+1,by  ))*(wxp*wyc);
    sum+=irisCoarseAt(tex,ivec2(bx-1,by+1))*(wxm*wyp);
    sum+=irisCoarseAt(tex,ivec2(bx  ,by+1))*(wxc*wyp);
    sum+=irisCoarseAt(tex,ivec2(bx+1,by+1))*(wxp*wyp);
    return sum;
}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    float fine=texelFetch(RemapFine,p,0).r;
    float coarse=irisExpand(RemapCoarse,p);
    float lap=fine-coarse;
    float localReference=clamp(texelFetch(GuideLevel,p,0).r,referenceMin,referenceMax);
    float weight=max(1.0-abs(localReference-referenceLog)/max(referenceStep,1.0e-6),0.0);
    float previous=firstReference!=0 ? 0.0 : texelFetch(Accumulator,p,0).r;
    Output=previous+weight*lap;
}
