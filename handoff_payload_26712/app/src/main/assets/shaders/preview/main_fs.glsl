#extension GL_OES_EGL_image_external_essl3 : require
precision mediump float;
uniform samplerExternalOES sTexture;
uniform vec2 resolution;
uniform bool enablePeak;
uniform bool mirror;
uniform float irisSoftwareZoom;
uniform float iris26662ReferencePreviewGain;
uniform vec4 iris26678FlickerParams;
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

    /* IRIS_26712_FULL_INVERSE_HAL_PREVIEW_PRESENTATION
     * 26708 remains the visible authority. Iris may physically move the shared sensor exposure
     * only while a composition is stationary, but that capture-domain offset must be invisible.
     * Apply the exact frame-owned inverse exposure as a true linear multiplier, then encode/clamp.
     * This intentionally allows the viewfinder highlights to clip exactly as the HAL-looking
     * baseline would; protected RAW headroom remains capture data and is not advertised visually.
     */
    float iris26662Gain = clamp(iris26662ReferencePreviewGain, 0.3535534, 2.8284271);
    if (abs(iris26662Gain - 1.0) > 0.0001) {
        vec3 encoded = clamp(color.rgb, vec3(0.0), vec3(1.0));
        vec3 lowLinear = encoded / 12.92;
        vec3 highLinear = pow((encoded + 0.055) / 1.055, vec3(2.4));
        vec3 linearRgb = mix(lowLinear, highLinear, step(vec3(0.04045), encoded));
        linearRgb = max(linearRgb, vec3(0.0)) * iris26662Gain;
        vec3 lowEncoded = 12.92 * linearRgb;
        vec3 highEncoded = 1.055 * pow(max(linearRgb, vec3(0.0)), vec3(1.0 / 2.4)) - 0.055;
        color.rgb = clamp(mix(lowEncoded, highEncoded, step(vec3(0.0031308), linearRgb)),
                          vec3(0.0), vec3(1.0));
    }

    /* IRIS_26678_POST_WYSIWYG_ROW_FLICKER_CORRECTION
     * This stage is downstream of the exact 26662/26667 white-anchored WYSIWYG owner. It never
     * changes exposure/HDR state. Only a timestamp-owned, temporally drifting row harmonic may
     * enable it; weak/absent evidence is mathematically neutral. The same white-anchored rational
     * map prevents the correction from turning protected white into clipped preview white. */
    float iris26678Strength = clamp(iris26678FlickerParams.w, 0.0, 1.0);
    float iris26678Harmonic = iris26678FlickerParams.x;
    if (iris26678Strength > 0.0001 && iris26678Harmonic >= 0.5) {
        float iris26678Phase = 6.28318530718 * iris26678Harmonic * clamp(uv.y, 0.0, 1.0);
        float iris26678LogMod = iris26678FlickerParams.y * cos(iris26678Phase)
                + iris26678FlickerParams.z * sin(iris26678Phase);
        iris26678LogMod = clamp(iris26678LogMod, -0.12, 0.12);
        float iris26678Gain = exp(-iris26678LogMod * iris26678Strength);
        if (abs(iris26678Gain - 1.0) > 0.0001) {
            vec3 iris26678Encoded = clamp(color.rgb, vec3(0.0), vec3(1.0));
            vec3 iris26678LowLinear = iris26678Encoded / 12.92;
            vec3 iris26678HighLinear = pow((iris26678Encoded + 0.055) / 1.055, vec3(2.4));
            vec3 iris26678Linear = mix(iris26678LowLinear, iris26678HighLinear,
                    step(vec3(0.04045), iris26678Encoded));
            float iris26678Y = dot(iris26678Linear, vec3(0.2126, 0.7152, 0.0722));
            float iris26678Guide = max(iris26678Y,
                    max(iris26678Linear.r, max(iris26678Linear.g, iris26678Linear.b)));
            if (iris26678Guide > 1.0e-6) {
                float iris26678Mapped = iris26678Gain * iris26678Guide
                        / (1.0 + (iris26678Gain - 1.0) * iris26678Guide);
                iris26678Linear *= iris26678Mapped / iris26678Guide;
            }
            vec3 iris26678LowEncoded = 12.92 * iris26678Linear;
            vec3 iris26678HighEncoded = 1.055 * pow(max(iris26678Linear, vec3(0.0)),
                    vec3(1.0 / 2.4)) - 0.055;
            color.rgb = clamp(mix(iris26678LowEncoded, iris26678HighEncoded,
                    step(vec3(0.0031308), iris26678Linear)), vec3(0.0), vec3(1.0));
        }
    }
    Output = color;
}