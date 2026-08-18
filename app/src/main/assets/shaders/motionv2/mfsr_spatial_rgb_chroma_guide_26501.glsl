precision highp float;
precision highp int;
precision highp usampler2D;

uniform highp usampler2D rawTexture;
uniform ivec2 rawSize;
uniform int cfaPattern;
uniform vec4 blackLevel;
uniform float whiteLevel;
uniform float exposureScale;
uniform float wbR;
uniform float wbB;
out float Output;

/* IRIS_26501_PER_FRAME_NATIVE_GREEN_GUIDE
 * 1.27.1-style edge-directed green is built independently for every RAW frame.
 * Native green sites are preserved. R/B sites are reconstructed only from native
 * green neighbours plus the same-colour second-neighbour correction. R/B values
 * are never allowed to become a generic green lower bound.
 */
int phaseAt(ivec2 p){return ((p.y&1)<<1)|(p.x&1);}
int colorAt(ivec2 p){
    int q=phaseAt(p);
    if(cfaPattern==0)return q==0?0:(q==3?2:1);
    if(cfaPattern==1)return q==1?0:(q==2?2:1);
    if(cfaPattern==2)return q==2?0:(q==1?2:1);
    return q==3?0:(q==0?2:1);
}
int clampPhaseCoordinate(int v,int extent){
    int phase=v&1;
    if(phase>=extent)return extent-1;
    int last=phase+2*((extent-1-phase)/2);
    return clamp(v,phase,last);
}
ivec2 phaseClamp(ivec2 p){
    return ivec2(clampPhaseCoordinate(p.x,rawSize.x),clampPhaseCoordinate(p.y,rawSize.y));
}
float wbForColor(int c){return c==0?wbR:(c==2?wbB:1.0);}
float gainedRaw(ivec2 p){
    p=phaseClamp(p);
    int phase=phaseAt(p);
    float rawValue=float(texelFetch(rawTexture,p,0).r);
    float black=blackLevel[phase];
    float sensor=max(rawValue-black,0.0)/max(whiteLevel-black,1.0);
    return sensor*exposureScale*wbForColor(colorAt(p));
}
float greenAtNonGreen(ivec2 p,float center){
    float gL=gainedRaw(p+ivec2(-1,0));
    float gR=gainedRaw(p+ivec2( 1,0));
    float gU=gainedRaw(p+ivec2(0,-1));
    float gD=gainedRaw(p+ivec2(0, 1));
    float cL2=gainedRaw(p+ivec2(-2,0));
    float cR2=gainedRaw(p+ivec2( 2,0));
    float cU2=gainedRaw(p+ivec2(0,-2));
    float cD2=gainedRaw(p+ivec2(0, 2));
    float horizontalLinear=0.5*(gL+gR);
    float verticalLinear=0.5*(gU+gD);
    float horizontalCorrection=clamp(
            0.25*(2.0*center-cL2-cR2),
            -0.5*abs(gL-gR),0.5*abs(gL-gR));
    float verticalCorrection=clamp(
            0.25*(2.0*center-cU2-cD2),
            -0.5*abs(gU-gD),0.5*abs(gU-gD));
    float horizontal=horizontalLinear+horizontalCorrection;
    float vertical=verticalLinear+verticalCorrection;
    float gradientH=abs(gL-gR)+abs(2.0*center-cL2-cR2);
    float gradientV=abs(gU-gD)+abs(2.0*center-cU2-cD2);
    float blendH=gradientV/max(gradientH+gradientV,1.0e-7);
    float green=mix(vertical,horizontal,blendH);
    float nativeMin=min(min(gL,gR),min(gU,gD));
    float nativeMax=max(max(gL,gR),max(gU,gD));
    return clamp(green,nativeMin,nativeMax);
}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    if(any(greaterThanEqual(p,rawSize))){Output=0.0;return;}
    float center=gainedRaw(p);
    int c=colorAt(p);
    Output=c==1?center:greenAtNonGreen(p,center);
}
