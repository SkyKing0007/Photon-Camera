#version 300 es
precision highp float;
precision highp sampler2D;
precision highp int;
precision highp isampler2D;
uniform highp isampler2D uReference;
uniform highp isampler2D uCurrent;
uniform sampler2D uProducts0;
uniform sampler2D uInitialAlignment;
uniform ivec2 uImageSize;
uniform ivec2 uGridSize;
uniform int uTileStride;
uniform int uTileSize;
uniform int uNormalize;
uniform int uHasInitialAlignment;

int referenceValueAt(ivec2 p) {
    return texelFetch(
        uReference,
        clamp(p, ivec2(0), uImageSize - ivec2(1)),
        0
    ).r;
}
float referenceAt(ivec2 p) {
    return float(referenceValueAt(p));
}
vec2 gradientAt(ivec2 p) {
    return clamp(
        vec2(
            referenceAt(p + ivec2(1, 0)) -
                referenceAt(p - ivec2(1, 0)),
            referenceAt(p + ivec2(0, 1)) -
                referenceAt(p - ivec2(0, 1))
        ),
        vec2(-32768.0),
        vec2(32767.0)
    );
}
int currentAt(ivec2 p) {
    return texelFetch(
        uCurrent,
        clamp(p, ivec2(0), uImageSize - ivec2(1)),
        0
    ).r;
}
int q15Weight(float value) {
    return clamp(int(floor(value * 32768.0)), 0, 32767);
}
int roundedShiftRight15(int value) {
    int biased = value + 16384;
    return biased >= 0
        ? biased / 32768
        : -((-biased + 32767) / 32768);
}
int warpedCurrentValueAt(vec2 p) {
    vec2 bounded = clamp(
        p,
        vec2(0.0),
        vec2(uImageSize - ivec2(1))
    );
    ivec2 p0 = ivec2(floor(bounded));
    vec2 fraction = fract(bounded);
    int w00 = q15Weight((1.0 - fraction.x) * (1.0 - fraction.y));
    int w10 = q15Weight(fraction.x * (1.0 - fraction.y));
    int w01 = q15Weight((1.0 - fraction.x) * fraction.y);
    int w11 = q15Weight(fraction.x * fraction.y);
    int weighted =
        currentAt(p0) * w00 +
        currentAt(p0 + ivec2(1, 0)) * w10 +
        currentAt(p0 + ivec2(0, 1)) * w01 +
        currentAt(p0 + ivec2(1, 1)) * w11;
    return clamp(roundedShiftRight15(weighted), -32768, 32767);
}
float warpedCurrentAt(vec2 p) {
    return float(warpedCurrentValueAt(p));
}
vec3 initialAlignmentAt(ivec2 tile) {
    return uHasInitialAlignment != 0
        ? texelFetch(
            uInitialAlignment,
            clamp(tile, ivec2(0), uGridSize - ivec2(1)),
            0
        ).xyz
        : vec3(0.0);
}
vec4 solveAlignment(ivec2 tile, vec3 initialAlignment, vec2 target, float count) {
    vec4 products0 = texelFetch(uProducts0, tile, 0);
    float bx = 0.5 * target.x / count;
    float by = 0.5 * target.y / count;
    float inverseDeterminant = 1.0 / (1.0 + products0.w);
    vec2 delta = inverseDeterminant * vec2(
        products0.z * by - products0.y * bx,
        products0.z * bx - products0.x * by
    );
    return vec4(
        initialAlignment.xy + clamp(delta, vec2(-1.0), vec2(1.0)),
        initialAlignment.z,
        0.0
    );
}
out vec4 oAlignment;
void main() {
    ivec2 tile = ivec2(gl_FragCoord.xy);
    vec3 initialAlignment = initialAlignmentAt(tile);
    vec2 flow = initialAlignment.xy;
    ivec2 origin = (tile + ivec2(1)) * uTileStride;
    float count = float(uTileSize * uTileSize);
    float meanResidual = 0.0;
    if (uNormalize != 0) {
        for (int y = 0; y < 64; ++y) {
            if (y >= uTileSize) break;
            for (int x = 0; x < 64; ++x) {
                if (x >= uTileSize) break;
                meanResidual += warpedCurrentAt(
                    vec2(origin + ivec2(x, y)) + flow
                ) - referenceAt(origin + ivec2(x, y));
            }
        }
        meanResidual /= count;
    }
    vec2 target = vec2(0.0);
    for (int y = 0; y < 64; ++y) {
        if (y >= uTileSize) break;
        for (int x = 0; x < 64; ++x) {
            if (x >= uTileSize) break;
            ivec2 p = origin + ivec2(x, y);
            float residual = warpedCurrentAt(vec2(p) + flow) -
                referenceAt(p) - meanResidual;
            target += residual * gradientAt(p);
        }
    }
    oAlignment = solveAlignment(tile, initialAlignment, target, count);
}
