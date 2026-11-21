#version 300 es
precision highp float;
precision highp sampler2D;
precision highp int;
precision highp isampler2D;
uniform highp isampler2D uReference;
uniform ivec2 uImageSize;
uniform int uTileStride;
uniform int uTileSize;
layout(location = 0) out vec4 oProducts0;

float valueAt(ivec2 p) {
    return float(texelFetch(
        uReference,
        clamp(p, ivec2(0), uImageSize - ivec2(1)),
        0
    ).r);
}
vec2 gradientAt(ivec2 p) {
    return clamp(
        vec2(
            valueAt(p + ivec2(1, 0)) - valueAt(p - ivec2(1, 0)),
            valueAt(p + ivec2(0, 1)) - valueAt(p - ivec2(0, 1))
        ),
        vec2(-32768.0),
        vec2(32767.0)
    );
}
void main() {
    ivec2 tile = ivec2(gl_FragCoord.xy);
    ivec2 origin = (tile + ivec2(1)) * uTileStride;
    int sampleStep = 1;
    float count = float((uTileSize / sampleStep) * (uTileSize / sampleStep));
    float xx = 0.0;
    float yy = 0.0;
    float xy = 0.0;
    for (int y = 0; y < 64; y += sampleStep) {
        if (y >= uTileSize) break;
        for (int x = 0; x < 64; x += sampleStep) {
            if (x >= uTileSize) break;
            ivec2 p = origin + ivec2(x, y);
            vec2 gradient = gradientAt(p);
            xx += gradient.x * gradient.x;
            yy += gradient.y * gradient.y;
            xy += gradient.x * gradient.y;
        }
    }
    float inverseCount = 1.0 / count;
    vec3 hessian = vec3(
        0.25 * xx * inverseCount,
        0.25 * yy * inverseCount,
        0.25 * xy * inverseCount
    );
    bool xMajor = hessian.x >= hessian.y;
    float major = xMajor ? hessian.x : hessian.y;
    float slope = major > 0.0 ? hessian.z / major : 0.0;
    float orthogonalEnergy = 0.0;
    for (int y = 0; y < 64; y += sampleStep) {
        if (y >= uTileSize) break;
        for (int x = 0; x < 64; x += sampleStep) {
            if (x >= uTileSize) break;
            vec2 gradient = gradientAt(origin + ivec2(x, y));
            float residual = xMajor
                ? gradient.y - slope * gradient.x
                : gradient.x - slope * gradient.y;
            orthogonalEnergy += residual * residual;
        }
    }
    oProducts0 = vec4(hessian, major * (0.25 * orthogonalEnergy * inverseCount));
}
