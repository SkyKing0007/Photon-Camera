// RAWR ce767e80bfce2e1641abf7dad6b1bf504d844fd9 Lab defringe common.
// Port change: GLSL ES 3.10 std140 UBO substitutes original Vulkan 128-byte push constant.
layout(std140, binding = 0) uniform DefringeParameters {
    uint width;
    uint height;
    float strength;
    float threshold;
    float edgeMode;
    uint pad0;
    uint pad1;
    uint pad2;
    vec4 forwardRows[3];
    vec4 inverseRows[3];
} pc;
const vec3 white = vec3(.96422, 1., .82521);
mat3 cameraToXyzMatrix() {
    return transpose(mat3(pc.forwardRows[0].xyz, pc.forwardRows[1].xyz, pc.forwardRows[2].xyz));
}
mat3 xyzToCameraMatrix() {
    return transpose(mat3(pc.inverseRows[0].xyz, pc.inverseRows[1].xyz, pc.inverseRows[2].xyz));
}
#define cameraToXyz cameraToXyzMatrix()
#define xyzToCamera xyzToCameraMatrix()
float labf(float t) { return t > 216. / 24389. ? pow(t, 1. / 3.) : (24389. / 27. * t + 16.) / 116.; }
float labinv(float t) { return t > 6. / 29. ? t * t * t : 3. * (6. / 29.) * (6. / 29.) * (t - 4. / 29.); }
vec3 toLab(vec3 rgb) {
    vec3 v = cameraToXyz * rgb / white;
    vec3 f = vec3(labf(v.x), labf(v.y), labf(v.z));
    return vec3(116. * f.y - 16., 500. * (f.x - f.y), 200. * (f.y - f.z));
}
vec3 fromLab(vec3 v) {
    float fy = (v.x + 16.) / 116.;
    vec3 f = vec3(fy + v.y / 500., fy, fy - v.z / 200.);
    return xyzToCamera * (white * vec3(labinv(f.x), labinv(f.y), labinv(f.z)));
}
float labY(float L) { return labinv((L + 16.) / 116.); }
float huelabToHuehsv2(float h) {
    float hr = 0.;
    if (h >= 0. && h < .6) hr = .11666 * h + .93;
    else if (h >= .6 && h < 1.4) hr = .1125 * h - .0675;
    else if (h >= 1.4 && h < 2.) hr = .2666 * h - .2833;
    else if (h >= 2.) hr = .1489 * h - .04785;
    else if (h < -2.8) hr = .23419 * h + 1.1557;
    else if (h < -2.3) hr = .16 * h + .948;
    else if (h < -.9) hr = .12143 * h + .85928;
    else if (h < -.1) hr = .2125 * h + .94125;
    else hr = .1 * h + .93;
    return hr < 0. ? hr + 1. : (hr > 1. ? hr - 1. : hr);
}
float flatCurveHalf(float u) {
    float t = (.7 - sqrt(max(.49 - .8 * u, 0.))) / .4;
    return .5 * t * t;
}
float hueWeight(vec2 ab) {
    const float x0 = .668944571, xPeak = .8287775246, x1 = .9908883827, yPeak = .97835991;
    float hr = huelabToHuehsv2(any(notEqual(ab, vec2(0.))) ? atan(ab.y, ab.x) : 0.);
    float y = 0.;
    if (hr > x0 && hr < xPeak) {
        float u = (hr - x0) / (xPeak - x0);
        y = yPeak * (u <= .5 ? flatCurveHalf(u) : 1. - flatCurveHalf(1. - u));
    } else if (hr >= xPeak && hr < x1) {
        float u = (hr - xPeak) / (x1 - xPeak);
        y = yPeak * (u <= .5 ? 1. - flatCurveHalf(u) : flatCurveHalf(1. - u));
    }
    float c = y - .5;
    c = c < 0. ? 2. * c : c;
    return (1. + c) * (1. + c);
}
float purpleChroma(vec2 ab) { return min(hueWeight(ab), 1.) * length(ab); }
const float kPurpleObjectLo = .38, kPurpleObjectHi = .48;
