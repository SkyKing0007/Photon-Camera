#extension GL_OES_EGL_image_external_essl3 : require
precision mediump float;
uniform samplerExternalOES sTexture;
uniform vec2 resolution;
uniform bool enablePeak;
uniform bool mirror;
uniform float irisSoftwareZoom;
uniform float iris26661ReferencePreviewGain;
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

    /* IRIS_26661_GOOGLE_REFERENCE_LIVE_PREVIEW_COMPENSATION
     * Camera2 AE compensation deliberately protects the RAW reference exposure. Approximate the
     * inverse only for the displayed preview in linear-light sRGB so the user does not see a dark
     * viewfinder. The same protection magnitude is accounted for exactly once by final rendering.
     */
    vec3 encoded = clamp(color.rgb, vec3(0.0), vec3(1.0));
    vec3 lowLinear = encoded / 12.92;
    vec3 highLinear = pow((encoded + 0.055) / 1.055, vec3(2.4));
    vec3 linearRgb = mix(lowLinear, highLinear, step(vec3(0.04045), encoded));
    linearRgb *= max(iris26661ReferencePreviewGain, 1.0);
    vec3 lowEncoded = 12.92 * linearRgb;
    vec3 highEncoded = 1.055 * pow(max(linearRgb, vec3(0.0)), vec3(1.0 / 2.4)) - 0.055;
    color.rgb = clamp(mix(lowEncoded, highEncoded, step(vec3(0.0031308), linearRgb)),
                      vec3(0.0), vec3(1.0));
    Output = color;
}