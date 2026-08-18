precision highp float;
precision highp int;
precision highp usampler2D;

uniform highp usampler2D rawTexture;
uniform highp sampler2D chromaGuide;
uniform highp sampler2D flowTexture;
uniform highp sampler2D robustnessTexture;
uniform highp sampler2D covarianceTexture;
uniform highp sampler2D semanticPhaseWeightTexture;
uniform ivec2 rawSize;
uniform ivec2 packedSize;
uniform int cfaPattern;
uniform vec4 blackLevel;
uniform float whiteLevel;
uniform float exposureScale;
uniform float wbR;
uniform float wbB;
uniform vec2 greenNoise;
uniform float chromaEdgeNoiseSigmas;
uniform float chromaEdgeSigmaFloor;
uniform int referenceFrame;
uniform int useFrameWeight;
uniform int useSemanticPhaseWeight;
uniform float physicalClipThreshold;

layout(location=0) out vec4 SemanticAndGreenWeight;
layout(location=1) out vec4 OpponentWeights;

/* IRIS_26501_WRONSKI_PER_FRAME_SPATIAL_RGB_OWNER
 * Each accepted RAW frame contributes semantic G / (R-G) / (B-G) evidence before
 * any Bayer collapse. Wronski flow, covariance and final rejection weight remain
 * authoritative. Two persistent RGBA16F render targets accumulate additively;
 * there is no read/write RGB ping-pong image.
 */
int phaseAt(ivec2 p){return ((p.y&1)<<1)|(p.x&1);}
int colorAt(ivec2 p){
    int q=phaseAt(p);
    if(cfaPattern==0)return q==0?0:(q==3?2:1);
    if(cfaPattern==1)return q==1?0:(q==2?2:1);
    if(cfaPattern==2)return q==2?0:(q==1?2:1);
    return q==3?0:(q==0?2:1);
}
float wbForColor(int c){return c==0?wbR:(c==2?wbB:1.0);}
bool inBounds(ivec2 p){return all(greaterThanEqual(p,ivec2(0)))&&all(lessThan(p,rawSize));}
int clampPhaseCoordinate(int v,int extent){
    int phase=v&1;
    if(phase>=extent)return extent-1;
    int last=phase+2*((extent-1-phase)/2);
    return clamp(v,phase,last);
}
ivec2 phaseClamp(ivec2 p){
    return ivec2(clampPhaseCoordinate(p.x,rawSize.x),clampPhaseCoordinate(p.y,rawSize.y));
}
bool ownedSample(ivec2 requested,out ivec2 ownedPixel){
    if(inBounds(requested)){ownedPixel=requested;return true;}
    if(referenceFrame!=0){ownedPixel=phaseClamp(requested);return true;}
    ownedPixel=ivec2(0);return false;
}
float physicalSensor(ivec2 p){
    int phase=phaseAt(p);
    float rawValue=float(texelFetch(rawTexture,p,0).r);
    float black=blackLevel[phase];
    return max(rawValue-black,0.0)/max(whiteLevel-black,1.0);
}
float gainedRaw(ivec2 p){return physicalSensor(p)*exposureScale*wbForColor(colorAt(p));}
float greenAt(ivec2 p){return texelFetch(chromaGuide,p,0).r;}
mat2 precisionAt(vec2 sourceRaw){
    vec2 uv=clamp((sourceRaw+vec2(0.5))/vec2(rawSize),vec2(0.0),vec2(1.0));
    vec4 v=texture(covarianceTexture,uv);
    return mat2(v.x,v.y,v.z,v.w);
}
float spatialWeight(vec2 offset,mat2 precisionMatrix){
    float d=max(dot(offset,precisionMatrix*offset),0.0);
    return exp2(-0.5*d)+0.00005;
}
float phaseComponent(vec4 v,int q){return q==0?v.r:(q==1?v.g:(q==2?v.b:v.a));}
vec3 semanticAxisPhaseWeight(ivec2 outputPixel){
    if(useSemanticPhaseWeight==0)return vec3(1.0);
    ivec2 packedCoord=clamp(outputPixel>>1,ivec2(0),packedSize-ivec2(1));
    vec4 phaseWeight=max(texelFetch(semanticPhaseWeightTexture,packedCoord,0),vec4(0.0));
    float rWeight=0.0,bWeight=0.0,gWeight=0.0;
    int greenCount=0;
    for(int q=0;q<4;++q){
        ivec2 phasePixel=ivec2(q&1,q>>1);
        int c=colorAt(phasePixel);
        float w=phaseComponent(phaseWeight,q);
        if(c==0)rWeight=w;
        else if(c==2)bWeight=w;
        else{gWeight+=w;greenCount++;}
    }
    gWeight/=float(max(greenCount,1));
    /* Axis order is G, R-G, B-G. */
    return clamp(vec3(gWeight,rWeight,bWeight),vec3(0.0),vec3(1.0));
}
float frameWeightAt(ivec2 outputPixel){
    if(useFrameWeight==0)return 1.0;
    ivec2 packedCoord=outputPixel>>1;
    vec2 uv=(vec2(packedCoord)+vec2(0.5))/vec2(packedSize);
    return clamp(texture(robustnessTexture,uv).r,0.0,1.0);
}
vec2 sourceRawAt(ivec2 outputPixel){
    if(referenceFrame!=0)return vec2(outputPixel);
    ivec2 packedCoord=outputPixel>>1;
    vec2 uv=(vec2(packedCoord)+vec2(0.5))/vec2(packedSize);
    vec2 packedFlow=texture(flowTexture,uv).xy;
    return vec2(outputPixel)+2.0*packedFlow;
}
float chromaGuideWeight(float localGreen,float targetGreen){
    float signal=max(max(localGreen,targetGreen),0.0);
    float variance=max(greenNoise.x*signal+greenNoise.y,1.0e-10);
    float sigma=max(chromaEdgeSigmaFloor,chromaEdgeNoiseSigmas*sqrt(variance));
    float normalized=(localGreen-targetGreen)/max(sigma,1.0e-7);
    return exp(-0.5*normalized*normalized);
}
void main(){
    ivec2 outP=ivec2(gl_FragCoord.xy);
    SemanticAndGreenWeight=vec4(0.0);
    OpponentWeights=vec4(0.0);
    if(any(greaterThanEqual(outP,rawSize)))return;
    float fw=frameWeightAt(outP);
    if(fw<=0.0)return;
    vec2 sourceRaw=sourceRawAt(outP);
    if(sourceRaw.x<0.0||sourceRaw.y<0.0||sourceRaw.x>float(rawSize.x-1)||sourceRaw.y>float(rawSize.y-1))return;

    vec2 samplePosition=sourceRaw+vec2(0.5);
    ivec2 anchor=ivec2(floor(samplePosition));
    vec2 subpixelOffset=vec2(anchor)+vec2(0.5)-samplePosition;
    mat2 precisionMatrix=precisionAt(sourceRaw);
    vec3 semantic=vec3(0.0);
    vec3 weights=vec3(0.0);

    /* Native green owns structure. Missing auxiliary edge samples are skipped rather
     * than mirrored; therefore their authority naturally falls relative to frame 0. */
    for(int dy=-1;dy<=1;++dy){
        for(int dx=-1;dx<=1;++dx){
            ivec2 requested=anchor+ivec2(dx,dy);
            ivec2 q;
            if(!ownedSample(requested,q)||colorAt(q)!=1)continue;
            if(physicalSensor(q)>=physicalClipThreshold)continue;
            float w=spatialWeight(vec2(dx,dy)+subpixelOffset,precisionMatrix);
            semantic.x+=gainedRaw(q)*w;
            weights.x+=w;
        }
    }
    if(weights.x<=1.0e-8)return;
    float targetGreen=semantic.x/weights.x;

    for(int dy=-1;dy<=1;++dy){
        for(int dx=-1;dx<=1;++dx){
            ivec2 requested=anchor+ivec2(dx,dy);
            ivec2 q;
            if(!ownedSample(requested,q))continue;
            int c=colorAt(q);
            if(c==1)continue;
            if(physicalSensor(q)>=physicalClipThreshold)continue;
            float spatial=spatialWeight(vec2(dx,dy)+subpixelOffset,precisionMatrix);
            float localGreen=greenAt(q);
            float w=spatial*chromaGuideWeight(localGreen,targetGreen);
            float opponent=gainedRaw(q)-localGreen;
            if(c==0){semantic.y+=opponent*w;weights.y+=w;}
            else{semantic.z+=opponent*w;weights.z+=w;}
        }
    }

    vec3 axisWeight=semanticAxisPhaseWeight(outP)*fw;
    SemanticAndGreenWeight=vec4(
            semantic.x*axisWeight.x,
            semantic.y*axisWeight.y,
            semantic.z*axisWeight.z,
            weights.x*axisWeight.x);
    OpponentWeights=vec4(
            weights.y*axisWeight.y,
            weights.z*axisWeight.z,
            0.0,0.0);
}
