package com.hinnka.mycamera.processor

import com.hinnka.mycamera.processor.Iris26972CDonorSabreGreenShaders.PLANE_PADDING
import com.hinnka.mycamera.processor.Iris26972CDonorSabreGreenShaders.chromaOps
import com.hinnka.mycamera.processor.Iris26972CDonorSabreGreenShaders.header
import com.hinnka.mycamera.processor.Iris26972CDonorSabreGreenShaders.integerOps

/**
 * C-only donor ResolveSabre GPU passes, bjzhou PhotonCamera v1.29.0.
 * Source blob a64486bf42b2379dac5a1cf3c208d310d10213ec.
 * No A/B source or shader objects are changed.
 */
internal object Iris26972CDonorSabreResolveShaders {
    val convertToInt = """
        ${header.prependIndent("        ").trimStart()}
        uniform highp sampler2D uAccumulated;
        uniform ivec2 uImageSize;
        uniform ivec2 uRedSite;
        uniform float uQuantizationScale;
        layout(location = 0) out highp ivec4 oConverted;

        void main() {
            ivec2 virtualSite = ivec2(gl_FragCoord.xy) - ivec2($PLANE_PADDING);
            ivec2 source = clamp(virtualSite + uRedSite, ivec2(0), uImageSize - ivec2(1));
            vec4 color = texelFetch(uAccumulated, source, 0);
            int cfaColor = (virtualSite.x & 1) + (virtualSite.y & 1);
            float sampleValue = cfaColor == 0 ? color.r : (cfaColor == 1 ? color.g : color.b);
            float scaled = sampleValue * uQuantizationScale;
            oConverted = ivec4(int(clamp(roundEven(scaled), -32768.0, 32767.0)), 0, 0, 0);
        }
    """.trimIndent()

    val resolveOutput = """
        ${header.prependIndent("        ").trimStart()}
        uniform highp sampler2D uAccumulated;
        uniform highp isampler2D uBalanced;
        uniform highp isampler2D uGreen;
        uniform ivec2 uImageSize;
        uniform ivec2 uPlaneSize;
        uniform ivec2 uRedSite;
        uniform float uBlendBias;
        uniform float uBlendScale;
        uniform float uInverseQuantizationScale;
        uniform vec3 uFinalGains;
        // RGGB gains of the lens shading map; a 1x1 map of ones when the capture has none.
        uniform highp sampler2D uLensShading;
        layout(location = 0) out highp uvec4 oResolved;

        ${integerOps.prependIndent("        ").trimStart()}

        // Converted value; only read at R/B sites, where pass 2 kept it.
        int converted(int u, int v) { return planeAt(uBalanced, uPlaneSize, u, v); }
        int green(int u, int v) { return planeAt(uGreen, uPlaneSize, u, v); }

        ${chromaOps.prependIndent("        ").trimStart()}

        void main() {
            ivec2 site = ivec2(gl_FragCoord.xy);
            int u = site.x;
            int v = site.y;
            int cfaColor = (u & 1) + (v & 1);
            int demosaicedRed = cfaColor == 0 ? converted(u, v) : chroma(u, v, false);
            int demosaicedGreen = green(u, v);
            int demosaicedBlue = cfaColor == 2 ? converted(u, v) : chroma(u, v, true);
            vec3 demosaiced = vec3(demosaicedRed, demosaicedGreen, demosaicedBlue) *
                uInverseQuantizationScale;

            ivec2 source = clamp(site + uRedSite, ivec2(0), uImageSize - ivec2(1));
            vec4 color = texelFetch(uAccumulated, source, 0);
            float weight = clamp(uBlendBias + color.a * uBlendScale, 0.0, 1.0);
            vec4 shading = texture(uLensShading, (vec2(site) + 0.5) / vec2(uImageSize));
            vec3 gains = uFinalGains * vec3(shading.r, 0.5 * (shading.g + shading.b), shading.a);
            vec3 resolved = clamp(mix(color.rgb, demosaiced, weight) * gains, 0.0, 1.0);
            oResolved = uvec4(uvec3(round(resolved * 65535.0)), 65535u);
        }
    """.trimIndent()

    /**
     * Explicit C-only deviation from pinned donor: replay the SAME ResolveSabre integer CFA
     * arithmetic before the donor's final SDR [0,1] clamp and U16 quantization.
     * This cannot recover already-saturated sensor photosites; it only preserves genuinely
     * available linear overrange through WB / lens shading. Never infer HDR from SDR bytes.
     * The donor's original resolveOutput above remains byte-for-byte unchanged.
     */
    val resolveExtendedLinearOutput: String by lazy {
        val original = resolveOutput
        val out = "layout(location = 0) out highp uvec4 oResolved;"
        val clipped = "vec3 resolved = clamp(mix(color.rgb, demosaiced, weight) * gains, 0.0, 1.0);"
        val packed = "oResolved = uvec4(uvec3(round(resolved * 65535.0)), 65535u);"
        check(original.contains(out) && original.contains(clipped) && original.contains(packed) &&
            original.split(out).size == 2 && original.split(clipped).size == 2 &&
            original.split(packed).size == 2) {
            "26972 C extended HDR requires exact pinned donor ResolveSabre shader anchors"
        }
        original.replace(out, "layout(location = 0) out highp vec4 oExtended;")
            .replace(clipped, "vec3 resolved = mix(color.rgb, demosaiced, weight) * gains;")
            .replace(packed, "oExtended = vec4(resolved, 1.0);")
    }
}
