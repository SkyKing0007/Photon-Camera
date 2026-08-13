precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float effectiveSupport;
uniform float sensorClipLevel;
out vec3 Output;

float cameraStructure(vec3 c) {
    return max(c.g,0.0);
}

/*
 * IRIS_26446_TRUE_LOCAL_SUPPORT_DENOISE
 *
 * Local support is in frame-equivalent units:
 *   1.0 = reference only
 *   1.0 + accepted auxiliary confidences = locally supported burst estimate.
 *
 * Flat, weak-support regions receive modest residual cleanup.
 * Edges/text/fabric/highlights rapidly suppress it.
 */
void main() {
    ivec2 xy=ivec2(gl_FragCoord.xy);
    ivec2 sz=textureSize(InputBuffer,0);

    vec4 center4=texelFetch(InputBuffer,xy,0);
    vec3 center=max(center4.rgb,vec3(0.0));
    float localSupport=max(center4.a,1.0);
    float targetSupport=max(effectiveSupport,1.0);

    float supportRatio=
            clamp(localSupport/max(targetSupport,1.0),0.0,1.5);
    float supportDeficit=
            1.0-smoothstep(0.60,1.00,supportRatio);

    float y0=cameraStructure(center);
    float localMin=y0;
    float localMax=y0;
    float sumW=0.0;
    vec3 sum=vec3(0.0);

    float rangeScale=
            0.018+0.060*sqrt(max(y0,0.0))+0.010*y0;

    for(int oy=-1;oy<=1;oy++) {
        for(int ox=-1;ox<=1;ox++) {
            ivec2 p=clamp(
                    xy+ivec2(ox,oy),
                    ivec2(0),
                    sz-ivec2(1));
            vec3 v=max(texelFetch(InputBuffer,p,0).rgb,vec3(0.0));
            float y=cameraStructure(v);
            localMin=min(localMin,y);
            localMax=max(localMax,y);

            float spatial=(ox==0 && oy==0)?1.0:0.72;
            float range=exp(-abs(y-y0)/max(rangeScale,1.0e-4));
            float w=spatial*range;
            sum+=v*w;
            sumW+=w;
        }
    }

    vec3 filtered=sum/max(sumW,1.0e-5);

    float localContrast=
            (localMax-localMin)
            /max(0.045+0.38*y0,1.0e-4);
    float detailEvidence=smoothstep(0.10,0.52,localContrast);

    float peak=max(center.r,max(center.g,center.b));
    float highlightProtect=smoothstep(
            0.78,
            0.97,
            peak/max(sensorClipLevel,1.0e-4));

    float strength=
            mix(0.04,0.30,supportDeficit)
            *mix(1.0,0.18,detailEvidence)
            *mix(1.0,0.12,highlightProtect);

    Output=max(
            mix(center,filtered,clamp(strength,0.0,0.30)),
            vec3(0.0));
}