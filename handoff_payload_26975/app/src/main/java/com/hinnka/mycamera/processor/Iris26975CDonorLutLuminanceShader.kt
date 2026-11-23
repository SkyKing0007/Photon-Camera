package com.hinnka.mycamera.processor

/**
 * Original donor LutImageProcessor.LUT_LUMINANCE_GAIN_SHADER, pinned revision
 * 0a8a11defe7d932d8c8a729120a4d5f159e9d677.
 *
 * Encoded sRGB before and after the *actual* original LUT stack are mandatory.
 * A constant 1.0 sidecar is not a substitute for an active baseline/creative
 * LUT, and the resulting R16F gain must be pixel-aligned at the donor's 2x
 * downsampled grid before entering GpuReferenceGainmapProducer.
 *
 * This shader is detached until the complete donor LUT stack, HDR reference
 * and JPEG/R publication path are wired and tested together. Do not use
 * Iris's previous independent gainmap in its place.
 */
internal object Iris26975CDonorLutLuminanceShader {
    const val DOWNSAMPLE = 2
    const val OFFSET = 1e-4f
    val fragment = """
        #version 300 es
        precision highp float;

        in vec2 vTexCoord;
        out vec4 fragColor;
        uniform sampler2D uBeforeLutTexture;
        uniform sampler2D uAfterLutTexture;
        uniform float uOffset;

        float srgbToLinear(float value) {
            float magnitude = abs(value);
            float linearMagnitude = magnitude <= 0.04045
                ? magnitude / 12.92
                : pow((magnitude + 0.055) / 1.055, 2.4);
            return sign(value) * linearMagnitude;
        }

        vec3 srgbToLinear(vec3 value) {
            return vec3(
                srgbToLinear(value.r),
                srgbToLinear(value.g),
                srgbToLinear(value.b)
            );
        }

        void main() {
            const vec3 LINEAR_SRGB_LUMA = vec3(0.2126, 0.7152, 0.0722);
            vec3 beforeLinear = srgbToLinear(texture(uBeforeLutTexture, vTexCoord).rgb);
            vec3 afterLinear = srgbToLinear(texture(uAfterLutTexture, vTexCoord).rgb);
            float beforeLuma = max(dot(beforeLinear, LINEAR_SRGB_LUMA), 0.0);
            float afterLuma = max(dot(afterLinear, LINEAR_SRGB_LUMA), 0.0);
            float gain = (afterLuma + uOffset) / (beforeLuma + uOffset);
            fragColor = vec4(gain, 0.0, 0.0, 1.0);
        }
    """.trimIndent()
}
