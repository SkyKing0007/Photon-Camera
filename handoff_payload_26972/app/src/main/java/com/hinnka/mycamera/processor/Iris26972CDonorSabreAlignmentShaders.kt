package com.hinnka.mycamera.processor

/**
 * Experiment C-only, verbatim algorithm from the tagged bjzhou/PhotonCamera 1.29.0
 * GlesMgcRawSpatialShaders.convertAlignment (blob f51c5976adb368da7ee9d312731b36b393d7a8c4).
 * This converts a *real* signed sparse LK flow grid; it does not estimate optical flow.
 */
internal object Iris26972CDonorSabreAlignmentShaders {
    val convertAlignment = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
        precision highp int;
        uniform sampler2D uAlignment;
        uniform ivec2 uGridSize;
        uniform int uAlignmentTileSize;
        uniform int uAlignmentGridMin;
        uniform float uAlignmentScale;
        uniform vec2 uFlowNormalizationSize;
        out vec4 oFlow;
        vec2 flowAtTile(ivec2 tile) {
            return texelFetch(
                uAlignment,
                clamp(tile, ivec2(0), uGridSize - ivec2(1)),
                0
            ).xy * uAlignmentScale;
        }
        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy);
            ivec2 tile = clamp(
                p / uAlignmentTileSize - ivec2(uAlignmentGridMin),
                ivec2(0), uGridSize - ivec2(1)
            );
            vec2 flowPixels = flowAtTile(tile);
            vec2 minimumFlow = vec2(1.0e20);
            vec2 maximumFlow = vec2(-1.0e20);
            for (int y = -1; y <= 1; ++y) {
                for (int x = -1; x <= 1; ++x) {
                    vec2 v = flowAtTile(tile + ivec2(x, y));
                    minimumFlow = min(minimumFlow, v);
                    maximumFlow = max(maximumFlow, v);
                }
            }
            vec2 uvFlow = flowPixels / uFlowNormalizationSize;
            vec2 normalizedRange =
                (maximumFlow - minimumFlow) /
                max(uFlowNormalizationSize, vec2(1.0));
            // ConvertAlignmentHalide stores the Euclidean length of the normalized
            // min/max flow extent. X and Y use their own output dimensions.
            float localFlowVariation = length(normalizedRange);
            oFlow = vec4(uvFlow, localFlowVariation, 0.0);
        }
    """.trimIndent()
}
