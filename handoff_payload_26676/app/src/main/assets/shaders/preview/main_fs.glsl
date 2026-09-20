#extension GL_OES_EGL_image_external_essl3 : require
precision mediump float;
uniform samplerExternalOES sTexture;
uniform vec2 resolution;
uniform bool enablePeak;
uniform bool mirror;
uniform float irisSoftwareZoom;
uniform float iris26662ReferencePreviewGain;
/* IRIS_26524_PREVIEW_RESIDUAL_ZOOM */
out vec4 Output;
in vec2 texCoord;
void main() {
    vec2 uv = texCoord.xy;
    float zoom = max(irisSoftwareZoom, 1.0);
    uv = vec2(0.5) + (uv - vec2(0.5)) / zoom;
    if(mirror)
        uv.y = 1.0 - uv.y;
    vec4 color = texture(sTexture, uv);
    vec2 size = resolution;
    // focus peaking
    vec4 avg = vec4(0.0);
    for (int i = -1; i <= 1; i++) {
        for (int j = -1; j <= 1; j++) {
            avg += texture(sTexture, uv + vec2(i*2, j*2) / (size * zoom));
        }
    }
    avg /= 9.0;
    float diff = dot(abs(color - avg), vec4(0.299, 0.587, 0.114, 0.0));
    float denoiseK = 0.05;
    // denoise
    float w = (diff * diff) /(denoiseK + (diff * diff));
    vec4 dc = vec4(1.0,0.0,1.0,0.0);
    if(enablePeak)
        color = color + dc*32.0*diff*w;

    /* IRIS_26662_FRAME_MATCHED_PREVIEW_PRESENTATION
     * Preserve exact 26660 preview bytes when no RAW protection is active. When protection is
     * active, restore body brightness with a white-anchored rational exposure map instead of the
     * 26661 full linear multiplier. The map is monotone, maps display white to display white, and
     * rescales RGB uniformly, so it cannot create the blown preview highlights seen in 26661.
     */
    float iris26662Gain = max(iris26662ReferencePreviewGain, 1.0);
    if (iris26662Gain > 1.0001) {
        vec3 encoded = clamp(color.rgb, vec3(0.0), vec3(1.0));
        vec3 lowLinear = encoded / 12.92;
        vec3 highLinear = pow((encoded + 0.055) / 1.055, vec3(2.4));
        vec3 linearRgb = mix(lowLinear, highLinear, step(vec3(0.04045), encoded));
        float y = dot(linearRgb, vec3(0.2126, 0.7152, 0.0722));
        float guide = max(y, max(linearRgb.r, max(linearRgb.g, linearRgb.b)));
        if (guide > 1.0e-6) {
            float mappedGuide = iris26662Gain * guide
                    / (1.0 + (iris26662Gain - 1.0) * guide);
            linearRgb *= mappedGuide / guide;
        }
        vec3 lowEncoded = 12.92 * linearRgb;
        vec3 highEncoded = 1.055 * pow(max(linearRgb, vec3(0.0)), vec3(1.0 / 2.4)) - 0.055;
        color.rgb = clamp(mix(lowEncoded, highEncoded, step(vec3(0.0031308), linearRgb)),
                          vec3(0.0), vec3(1.0));
    }
    Output = color;
}