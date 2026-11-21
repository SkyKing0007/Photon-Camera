package com.hinnka.mycamera.processor

/**
 * Independent Experiment C GL shader port of bjzhou 1.29.0
 * GlesMgcRawSpatialShaders.kt, pinned Git blob f51c5976adb368da7ee9d312731b36b393d7a8c4.
 * These are donor RAW_SENSOR -> signed-S16 gray pyramid operators, not existing Iris A/B.
 */
internal object Iris26972CDonorSabreLkGrayShaders {
    val rawToGray = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uRaw;
        uniform ivec2 uRawSize;
        uniform ivec2 uGraySize;
        uniform int uCfaPattern;
        uniform vec4 uBlackLevels;
        uniform float uGain;
        layout(location = 0) out highp int oGray;
        uint quadSum(ivec2 q) {
            q = clamp(q, ivec2(0), uGraySize - ivec2(1));
            ivec2 p = clamp(q * 2, ivec2(0), uRawSize - ivec2(2));
            return texelFetch(uRaw, p, 0).r +
                texelFetch(uRaw, p + ivec2(1, 0), 0).r +
                texelFetch(uRaw, p + ivec2(0, 1), 0).r +
                texelFetch(uRaw, p + ivec2(1, 1), 0).r;
        }
        uint hadd(uint a, uint b) { return (a + b) >> 1; }
        uint rhadd(uint a, uint b) { return (a + b + 1u) >> 1; }
        uint verticalAt(ivec2 q) {
            return rhadd(
                hadd(quadSum(q + ivec2(0, -1)), quadSum(q + ivec2(0, 1))),
                quadSum(q)
            );
        }
        void main() {
            ivec2 q = ivec2(gl_FragCoord.xy);
            uint filtered = hadd(
                rhadd(verticalAt(q + ivec2(-1, 0)), verticalAt(q + ivec2(1, 0))),
                verticalAt(q)
            );
            float scale = uGain * 0.25;
            float blackSum = ((uBlackLevels.x + uBlackLevels.y) +
                uBlackLevels.z) + uBlackLevels.w;
            float offset = 0.5 - scale * blackSum;
            float value = offset + scale * float(filtered);
            oGray = int(clamp(value, -16383.0, 16383.0));
        }
    """.trimIndent()

    val grayDownsample = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
        precision highp int;
        precision highp isampler2D;
        uniform highp isampler2D uInput;
        uniform ivec2 uInputSize;
        layout(location = 0) out highp int oGray;
        float valueAt(ivec2 p) {
            return float(texelFetch(
                uInput, clamp(p, ivec2(0), uInputSize - ivec2(1)), 0
            ).r);
        }
        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy) * 2;
            float value = 0.0;
            for (int y = -1; y <= 1; ++y) {
                float wy = y == 0 ? 0.5 : 0.25;
                for (int x = -1; x <= 1; ++x) {
                    float wx = x == 0 ? 0.5 : 0.25;
                    value += valueAt(p + ivec2(x, y)) * wx * wy;
                }
            }
            oGray = int(clamp(floor(value + 0.5), -32768.0, 32767.0));
        }
    """.trimIndent()

    val grayDownsample4 = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
        precision highp int;
        precision highp isampler2D;
        uniform highp isampler2D uInput;
        uniform ivec2 uInputSize;
        layout(location = 0) out highp int oGray;
        int valueAt(ivec2 p) {
            return texelFetch(
                uInput, clamp(p, ivec2(0), uInputSize - ivec2(1)), 0
            ).r;
        }
        int firstStageAt(ivec2 p) {
            int sum = 0;
            for (int y = -1; y <= 1; ++y) {
                for (int x = -1; x <= 1; ++x) {
                    sum += valueAt(p + ivec2(x, y)) *
                        (2 - abs(x)) * (2 - abs(y));
                }
            }
            return (sum + 8) >> 4;
        }
        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy) * 4;
            int sum = 0;
            for (int y = -1; y <= 1; ++y) {
                for (int x = -1; x <= 1; ++x) {
                    sum += firstStageAt(p + 2 * ivec2(x, y)) *
                        (2 - abs(x)) * (2 - abs(y));
                }
            }
            oGray = (sum + 8) >> 4;
        }
    """.trimIndent()
}
