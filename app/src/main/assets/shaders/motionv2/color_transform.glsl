precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform vec3 sensorGains;
uniform float sensorClipLevel;
uniform vec3 colorRow0;
uniform vec3 colorRow1;
uniform vec3 colorRow2;
out vec3 Output;

/*
 * IRIS_26430_SENSOR_CLIP_COLOR_SAFETY_ONLY
 *
 * 26429 repaired the dominant R/G/B edge-registration/robustness failure.
 * Therefore ordinary extended-linear highlights must pass through untouched.
 *
 * Only camera-space samples approaching the physical sensor ceiling are allowed
 * to lose chroma authority. There is no output-space "overflow" neutralization,
 * no neighboring hue donor and no normal highlight tone mapping here.
 */

float max3(vec3 v) { return max(v.r,max(v.g,v.b)); }
float min3(vec3 v) { return min(v.r,min(v.g,v.b)); }

vec3 transformBalanced(vec3 balanced) {
    return vec3(
            dot(colorRow0,balanced),
            dot(colorRow1,balanced),
            dot(colorRow2,balanced));
}

/*
 * IRIS_26437_SENSOR_WHITE_POINT_COLOR_OWNERSHIP
 *
 * Repair chroma before white balance / matrix conversion, while camera-space
 * samples can still be compared to the real sensor white point.
 */
vec3 sensorNeutralFromGreen(vec3 cameraRgb) {
    vec3 gains=max(sensorGains,vec3(1.0e-6));
    float g=max(cameraRgb.g,0.0);
    return vec3(
            g*gains.g/gains.r,
            g,
            g*gains.g/gains.b);
}

void main() {
    ivec2 xy=ivec2(gl_FragCoord.xy);
    vec3 cameraRgb=max(texelFetch(InputBuffer,xy,0).rgb,vec3(0.0));

    float sensorClip=max(sensorClipLevel,1.0e-6);
    vec3 sensorRelative=cameraRgb/sensorClip;
    float peakRelative=max3(sensorRelative);

    /*
     * IRIS_26445_PER_CHANNEL_SENSOR_VALIDITY
     *
     * A reflective/white pixel does not become "bad RGB" all at once. Track
     * reliability independently for R/G/B so one saturated photosite does not
     * force an abrupt green-derived neutral replacement for the whole pixel.
     */
    vec3 channelLoss=smoothstep(
            vec3(0.900),
            vec3(0.995),
            sensorRelative);
    float leastLoss=min3(channelLoss);
    float greatestLoss=max3(channelLoss);
    float partialChannelLoss=
            clamp(greatestLoss-leastLoss,0.0,1.0);

    /*
     * Build a small, smooth neighborhood risk mask. Only the confidence mask is
     * spatially averaged; image structure itself is never blurred. This removes
     * the Bayer-scale hard contours visible on white TV boxes, thin leaves and
     * reflective metal.
     */
    ivec2 size=textureSize(InputBuffer,0);
    float riskSum=0.0;
    float riskWeight=0.0;
    for(int oy=-1;oy<=1;oy++) {
        for(int ox=-1;ox<=1;ox++) {
            ivec2 p=clamp(xy+ivec2(ox,oy),ivec2(0),size-ivec2(1));
            vec3 n=max(texelFetch(InputBuffer,p,0).rgb,vec3(0.0));
            vec3 nr=n/sensorClip;
            vec3 nl=smoothstep(vec3(0.900),vec3(0.995),nr);
            float np=max3(nr);
            float nPartial=max3(nl)-min3(nl);
            float spatial=(ox==0 && oy==0)?2.0:1.0;
            float r=
                    smoothstep(0.82,1.00,np)
                    *mix(0.25,1.0,clamp(nPartial,0.0,1.0));
            riskSum+=r*spatial;
            riskWeight+=spatial;
        }
    }
    float neighborhoodRisk=
            riskSum/max(riskWeight,1.0e-6);

    /*
     * IRIS_26445_LUMA_OWNED_HIGHLIGHT_CHROMA
     *
     * Apply the Camera2 gains/matrix to the measured signal first. Then, only
     * where per-channel sensor validity is being lost, compress chroma around
     * the transformed luminance axis. Luma/edge geometry remains the exact
     * reference-owned value. This replaces 26437's green-derived whole-pixel
     * neutralization and its hard terminal switch.
     */
    vec3 balanced=cameraRgb*sensorGains;
    vec3 linearSrgb=max(transformBalanced(balanced),vec3(0.0));


    float y=max(
            dot(linearSrgb,vec3(0.2126,0.7152,0.0722)),
            0.0);
    vec3 neutralLinear=vec3(y);

    float localValidityRisk=
            smoothstep(0.04,0.55,partialChannelLoss)
            *smoothstep(0.82,1.00,peakRelative);
    float terminalWhiteRisk=
            smoothstep(0.970,1.020,peakRelative);

    float chromaCompression=clamp(
            max(
                    localValidityRisk,
                    0.72*terminalWhiteRisk)
            *mix(0.82,1.0,neighborhoodRisk),
            0.0,
            0.92);

    linearSrgb=mix(
            linearSrgb,
            neutralLinear,
            chromaCompression);

    Output=max(linearSrgb,vec3(0.0));
}
