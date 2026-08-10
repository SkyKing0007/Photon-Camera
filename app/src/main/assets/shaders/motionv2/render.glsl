precision highp float;
precision mediump sampler2D;
uniform sampler2D InputBuffer;
out vec3 Output;

float srgbEncode(float x) {
    x=max(x,0.0);
    return x<=0.0031308 ? 12.92*x : 1.055*pow(x,1.0/2.4)-0.055;
}
vec3 srgbEncode(vec3 x) {
    return vec3(srgbEncode(x.r),srgbEncode(x.g),srgbEncode(x.b));
}

/* IRIS_26420_MOTION_V2_CANONICAL_TONE_ONLY */
vec3 compressDisplayHighlights(vec3 rgb) {
    rgb=max(rgb,vec3(0.0));
    float y=max(dot(rgb,vec3(0.2126,0.7152,0.0722)),0.0);
    const float start=0.70;
    if(y<=start) return rgb;
    float span=1.0-start;
    float excess=y-start;
    float yc=start+excess/(1.0+excess/span);
    return rgb*(yc/max(y,1.0e-6));
}

void main() {
    ivec2 xy=ivec2(gl_FragCoord.xy);
    vec3 linearSrgb=texelFetch(InputBuffer,xy,0).rgb;
    linearSrgb=compressDisplayHighlights(linearSrgb);
    Output=clamp(srgbEncode(linearSrgb),vec3(0.0),vec3(1.0));
}