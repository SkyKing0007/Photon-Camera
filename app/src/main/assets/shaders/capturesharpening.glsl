precision mediump float;
precision mediump sampler2D;
uniform sampler2D InputBuffer;
uniform float size;
uniform float strength;
out vec3 Output;
//#define depthMin (0.012)
#define depthMin (0.006)
#define depthMax (0.890)
#define colour (0.2)
#define size1 (1.1)
#define SHARPSIZE 5
#define SHARPSIZEKER 3.0
#define SHARPSTR 1.0
#define INSIZE 0,0
#define MOTIONHALORESTRAINT 0
#define NOISES 0.0
#define NOISEO 0.0
#define MOTIONRESIDUALNOISESCALE 1.0
#import gaussian
void main() {
    ivec2 xy = ivec2(gl_FragCoord.xy);
    vec3 mask = vec3(0.0);
    vec3 cur = (texelFetch(InputBuffer, (xy), 0).rgb);
    float pdfsize = 0.0;
    ivec2 sizeImage = ivec2(INSIZE);
    for (int i=-SHARPSIZE; i <= SHARPSIZE; ++i){
        float pdf2 = pdf(float(i)/float(SHARPSIZEKER));
        if(i+xy.x >= sizeImage.x || i+xy.x <= 0) continue;
        for (int j=-SHARPSIZE; j <= SHARPSIZE; ++j){
            if(j+xy.y >= sizeImage.y || j+xy.y <= 0) continue;
            float pdfv = pdf(float(j)/float(SHARPSIZEKER))*pdf2;
            mask+=vec3(texelFetch(InputBuffer, (xy+ivec2(i, j)), 0).rgb)*pdfv;
            pdfsize+=pdfv;
        }
    }
    mask/=pdfsize;
    mask = cur-mask;

    float sharpenDelta =
            (mask.r + mask.g + mask.b)
                    * (float(SHARPSTR) / 3.0);
#if MOTIONHALORESTRAINT
    /*
     * Build 26289:
     * Do not convert near-noise-floor positive residuals into connected
     * carpet worms or hard clumps. Strong real edges remain authorized.
     */
    float centerLuma = dot(cur, vec3(0.299, 0.587, 0.114));
    float visibleNoiseAmplitude =
            sqrt(
                    max(
                            NOISES * max(centerLuma, 0.0) + NOISEO,
                            0.000001
                    )
            ) * MOTIONRESIDUALNOISESCALE;

    float residualMagnitude =
            abs(sharpenDelta);

    float residualDetailGate =
            smoothstep(
                    visibleNoiseAmplitude * 1.55,
                    visibleNoiseAmplitude * 3.80 + 0.000001,
                    residualMagnitude
            );

    float channelEdgeStrength =
            max(
                    abs(mask.r),
                    max(abs(mask.g), abs(mask.b))
            );

    float realEdgeGate =
            smoothstep(
                    visibleNoiseAmplitude * 2.80,
                    visibleNoiseAmplitude * 7.00 + 0.000001,
                    channelEdgeStrength
            );

    sharpenDelta *=
            max(
                    residualDetailGate,
                    realEdgeGate
            );

    /* Retain the successful 26288 dark-side halo restraint. */
    float negativeAllowance =
            mix(0.0015, 0.0050, smoothstep(0.06, 0.42, centerLuma));
    sharpenDelta = max(sharpenDelta, -negativeAllowance);
#endif
    cur += sharpenDelta;
    Output = clamp(cur,0.0,1.0);
}
