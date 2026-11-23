package com.hinnka.mycamera.processor

/**
 * Original RAW SDR/UHDR residual equation from bjzhou GpuReferenceGainmapProducer.
 * Source: pinned 0a8a11defe7d932d8c8a729120a4d5f159e9d677, RAW_LUMA_RESIDUAL_FRAGMENT_SHADER.
 * Requires actual mutually aligned: post-LUT encoded SDR, extended linear HDR,
 * and the measured pre/post-LUT luminance sidecar. A made-up ratio=1 sidecar
 * is NOT an acceptable substitute for an active donor LUT stack.
 *
 * This isolated shader is not yet connected to an Android gainmap exporter.
 */
internal object Iris26975CDonorGpuLutResidualShader {
    val fragment = """
        #version 300 es
        precision highp float;
        in vec2 vTexCoord;
        out vec4 fragColor;
        uniform sampler2D uLutLuminanceGainTexture;
        uniform sampler2D uSdrTexture;
        uniform sampler2D uHdrTexture;
        uniform float uMinGainRatio;
        uniform float uMaxGainRatio;
        uniform float uOffset;
        uniform float uStrength;

        float srgbToLinear(float value) {
            float safeValue = max(value, 0.0);
            return safeValue <= 0.04045
                ? safeValue / 12.92
                : pow((safeValue + 0.055) / 1.055, 2.4);
        }
        vec3 srgbToLinear(vec3 value) {
            return vec3(srgbToLinear(value.r), srgbToLinear(value.g), srgbToLinear(value.b));
        }
        void main() {
            vec3 sdrLinear = srgbToLinear(texture(uSdrTexture, vTexCoord).rgb);
            vec3 hdrLinear = max(texture(uHdrTexture, vTexCoord).rgb, vec3(0.0));
            const vec3 LINEAR_SRGB_LUMA = vec3(0.2126, 0.7152, 0.0722);
            float sdrLuma = max(dot(sdrLinear, LINEAR_SRGB_LUMA), 0.0);
            float hdrLuma = max(dot(hdrLinear, LINEAR_SRGB_LUMA), 0.0);
            float lutLumaGain = max(texture(uLutLuminanceGainTexture, vTexCoord).r, 0.0);
            float targetHdrLuma = max((hdrLuma + uOffset) * lutLumaGain - uOffset, 0.0);
            float candidateRatio = clamp((targetHdrLuma + uOffset) / (sdrLuma + uOffset),
                uMinGainRatio, uMaxGainRatio);
            float normalizedStrength = clamp(uStrength, 0.25, 2.0);
            float strengthRatio = clamp(1.0 + (candidateRatio - 1.0) * normalizedStrength,
                uMinGainRatio, uMaxGainRatio);
            float gainEv = log2(strengthRatio);
            float minGainEv = log2(uMinGainRatio);
            float maxGainEv = log2(uMaxGainRatio);
            float normalized = (gainEv - minGainEv) / (maxGainEv - minGainEv);
            fragColor = vec4(vec3(clamp(normalized, 0.0, 1.0)), 1.0);
        }
    """.trimIndent()
}
