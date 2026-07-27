
#define SCALE 4
#define SCALEMPY (1.0/float(SCALE))
precision highp float;
precision highp sampler2D;
uniform sampler2D LowresInput;
uniform sampler2D Guide;
uniform sampler2D GuideHigh;
uniform float noiseS;
uniform float noiseO;
out vec3 Output;
#import interpolation
#import median

/*
 * Guided Upsample v10 — 3x3 window + noise-adaptive regularization
 *
 * Original: 3x3 window, hardcoded varThreshold = 0.001
 * v2-v8: 5x5 window — too large, caused color desaturation on small features
 * v10: 3x3 window (matches original size) + noise-adaptive regularization
 *
 * The5x5 window spanned both teal text and white background even at text center,
 * causing the regression to fit mixed data and desaturate colors.
 * 3x3 is small enough to stay within color boundaries for most pixels.
 */

void computeAB(ivec2 center, out vec3 a, out vec3 b) {
    float momentX  = 0.0;
    vec3  momentY  = vec3(0.0);
    float momentX2 = 0.0;
    vec3  momentXY = vec3(0.0);
    float ws = 0.0;
    const float sigma     = 1.2;
    const float sigmaSq2  = 2.0 * sigma * sigma;
    for (int i = -1; i <= 1; i++) {
        for (int j = -1; j <= 1; j++) {
            ivec2 pos     = center + ivec2(i, j);
            vec3  lowresVal  = texelFetch(LowresInput, pos, 0).rgb;
            float lightness  = dot(texelFetch(Guide, pos, 0).rgb, vec3(1.0/3.0));
            float w          = exp(-float(i*i + j*j) / sigmaSq2);
            momentX  += lightness * w;
            momentY  += lowresVal * w;
            momentX2 += lightness * lightness * w;
            momentXY += lightness * lowresVal * w;
            ws       += w;
        }
    }
    float invWs = 1.0 / ws;
    float meanX = momentX * invWs;
    vec3  meanY = momentY * invWs;
    vec3  covXY = momentXY * invWs - meanX * meanY;
    float varX  = momentX2 * invWs - meanX * meanX;

    // Noise-adaptive regularization (replaces hardcoded 0.001)
    // Uses actual noise level: noiseS * avgLuma + noiseO
    float avgLuma = clamp(meanX, 0.0, 1.0);
    float noiseVar = noiseS * avgLuma + noiseO;
    float varThreshold = noiseVar * 0.1;

    // When variance is too low the guide provides no useful signal,
    // so blend linearly toward a=0 (output = meanY) to avoid instability.
    float varWeight    = varX / (varX + varThreshold);
    a = varWeight * covXY / (varX + varThreshold);
    b = meanY - a * meanX;
}

void main() {
    ivec2 xy   = ivec2(gl_FragCoord.xy);
    ivec2 size = textureSize(GuideHigh, 0);

    vec2  lowres_pos = vec2(xy) / float(SCALE);
    ivec2 c          = ivec2(floor(lowres_pos));
    vec2  f          = fract(lowres_pos);
    vec3 a00, b00, a10, b10, a01, b01, a11, b11;
    computeAB(c,                 a00, b00);
    computeAB(c + ivec2(1, 0),   a10, b10);
    computeAB(c + ivec2(0, 1),   a01, b01);
    computeAB(c + ivec2(1, 1),   a11, b11);

    vec3 a = mix(mix(a00, a10, f.x), mix(a01, a11, f.x), f.y);
    vec3 b = mix(mix(b00, b10, f.x), mix(b01, b11, f.x), f.y);

    vec3 guideCenter = texelFetch(GuideHigh, xy, 0).rgb;
    Output = a * dot(guideCenter, vec3(1.0/3.0)) + b;
    float diffs[9];
    for (int i = -1; i <= 1; i++) {
        for (int j = - 1; j <= 1; j++) {
            ivec2 pos = xy + ivec2(i, j);
            vec3  guideVal = texelFetch(GuideHigh, pos, 0).rgb;
            diffs[(i+1)*3 + (j+1)] = dot(guideVal - (a * dot(guideVal, vec3(1.0/3.0)) + b), vec3(1.0/3.0));
        }
    }
    float medianDiff = median9(diffs);
    float absDev[9];
    for(int i = 0; i < 9; i++) {
        absDev[i] = abs(diffs[i] - medianDiff);
    }
    float mad = median9(absDev);
    float centerDiff = diffs[4];
    float threshold = 4.5 * mad;
    float dev = abs(centerDiff - medianDiff);

    float br = dot(Output, vec3(1.0/3.0));
    float guideBr = dot(guideCenter, vec3(1.0/3.0));
    float shadowBlend = smoothstep(0.0, 0.001, guideBr);
    guideBr = mix(br, guideBr, shadowBlend);

    // In extremely dark areas only, reduce guide influence to prevent color noise
    // (original behavior preserved)
    if (br > 1e-6) {
        Output = (Output / br) * guideBr;
    }
    Output = clamp(Output, 0.0, 1.0);
}
