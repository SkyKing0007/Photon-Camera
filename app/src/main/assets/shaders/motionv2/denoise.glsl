precision highp float;
precision mediump sampler2D;
uniform sampler2D InputBuffer;
uniform float noiseS;
uniform float noiseO;
uniform float effectiveSupport;
out vec3 Output;

float gaussWeight(float x){ return exp(-0.5*x*x); }

/*
 * IRIS_26427_HIGHLIGHT_CHROMA_AUTHORITY_LOCK
 *
 * MotionV2ColorTransform owns coherent highlight clipping. This residual
 * denoiser may clean ordinary color noise, but must not borrow neighborhood
 * chroma back into bright highlights.
 */
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    ivec2 sz=textureSize(InputBuffer,0);
    vec3 c=max(texelFetch(InputBuffer,p,0).rgb,vec3(0.0));
    float g0=max(c.g,0.0);
    float sigma=sqrt(max(g0*noiseS+noiseO,1.0e-8))
            /sqrt(max(effectiveSupport,1.0));
    float edgeSigma=max(2.6*sigma,0.0045);

    float gMin=g0;
    float gMax=g0;
    for(int y=-1;y<=1;y++){
        for(int x=-1;x<=1;x++){
            ivec2 q=clamp(p+ivec2(x,y),ivec2(0),sz-ivec2(1));
            float g=texelFetch(InputBuffer,q,0).g;
            gMin=min(gMin,g);
            gMax=max(gMax,g);
        }
    }

    float localRange=max(gMax-gMin,0.0);
    float detailEvidence=
            smoothstep(1.8*sigma,5.0*sigma+0.003,localRange);

    float sumW=0.0;
    float sumG=0.0;
    float sumRG=0.0;
    float sumBG=0.0;
    for(int y=-2;y<=2;y++){
        for(int x=-2;x<=2;x++){
            ivec2 q=clamp(p+ivec2(x,y),ivec2(0),sz-ivec2(1));
            vec3 s=max(texelFetch(InputBuffer,q,0).rgb,vec3(0.0));

            float dg=abs(s.g-g0);
            float edgeW=gaussWeight(dg/max(edgeSigma,1.0e-6));
            float spatial=1.0/(1.0+0.42*float(x*x+y*y));
            float w=edgeW*spatial;

            sumW+=w;
            sumG+=w*s.g;
            sumRG+=w*(s.r-s.g);
            sumBG+=w*(s.b-s.g);
        }
    }

    float invW=1.0/max(sumW,1.0e-6);
    float filteredG=sumG*invW;
    float filteredRG=sumRG*invW;
    float filteredBG=sumBG*invW;

    float supportDeficit=
            1.0-clamp(
                    (effectiveSupport-1.0)/11.0,
                    0.0,
                    1.0);

    float flatLuma=mix(0.18,0.30,supportDeficit);
    float detailLuma=mix(0.02,0.06,supportDeficit);
    float lumaStrength=mix(flatLuma,detailLuma,detailEvidence);

    float flatChroma=mix(0.76,0.92,supportDeficit);
    float detailChroma=mix(0.30,0.42,supportDeficit);
    float baseChromaStrength=
            mix(flatChroma,detailChroma,detailEvidence);

    /*
     * Luminance—not max RGB—is the lock signal. This protects legitimately
     * saturated single-channel colors while stopping neighborhood chroma
     * borrowing across genuinely bright clipping boundaries.
     */
    float y=max(dot(c,vec3(0.2126,0.7152,0.0722)),0.0);
    float highlightLock=smoothstep(0.60,0.82,y);

    float outG=mix(g0,filteredG,lumaStrength*(1.0-highlightLock));

    float centerRG=c.r-c.g;
    float centerBG=c.b-c.g;
    float chromaStrength=baseChromaStrength*(1.0-highlightLock);

    float rg=mix(centerRG,filteredRG,chromaStrength);
    float bg=mix(centerBG,filteredBG,chromaStrength);

    /*
     * At full lock, preserve the coherent RGB delivered by the color stage
     * exactly.
     */
    outG=mix(outG,g0,highlightLock);
    rg=mix(rg,centerRG,highlightLock);
    bg=mix(bg,centerBG,highlightLock);

    Output=max(vec3(outG+rg,outG,outG+bg),vec3(0.0));
}
