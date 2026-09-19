#extension GL_OES_EGL_image_external_essl3 : require
precision mediump float;
uniform samplerExternalOES sTexture;
uniform vec2 resolution;
uniform bool enablePeak;
uniform bool mirror;
uniform float irisSoftwareZoom;
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
    /* IRIS_26669_STATELESS_PREVIEW_HIGHLIGHT_PRESENTATION
     * HAL/user AE remains the sole repeating sensor-exposure owner. This is a frame-local display
     * shoulder only: no history, histogram feedback, temporal slew, Camera2 request mutation, or
     * delayed exposure state. It compresses bright preview luminance immediately while preserving
     * chromaticity, so moving between scenes cannot trigger a second Iris-driven exposure step. */
    float irisY = max(dot(color.rgb, vec3(0.299, 0.587, 0.114)), 0.0);
    const float irisPivot = 0.38;
    if (irisY > irisPivot) {
        float irisT = clamp((irisY - irisPivot) / max(1.0 - irisPivot, 0.0001), 0.0, 1.0);
        float irisCompressedT = irisT / (1.0 + 1.10 * irisT);
        float irisOutY = irisPivot + (1.0 - irisPivot) * irisCompressedT;
        float irisScale = irisOutY / max(irisY, 0.0001);
        color.rgb *= irisScale;
    }
    Output = color;
}