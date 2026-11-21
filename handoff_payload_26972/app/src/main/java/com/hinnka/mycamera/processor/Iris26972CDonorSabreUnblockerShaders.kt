package com.hinnka.mycamera.processor

/** Exact bjzhou 1.29.0 UnblockerRaw10Halide and UnblockerBlur fragment bodies, C-only.
 * From GlesMgcRawSpatialShaders.kt tagged source blob f51c5976adb368da7ee9d312731b36b393d7a8c4.
 */
internal object Iris26972CDonorSabreUnblockerShaders {
    val unblocker = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uRaw;
        uniform ivec2 uRawSize;
        uniform ivec2 uGridSize;
        uniform ivec2 uTileOffset;
        uniform int uCfaPattern;
        uniform float uBlackLevelGreen;
        uniform float uNoiseQuadratic;
        uniform float uNoiseScale;
        uniform float uNoiseOffset;
        uniform float uOutputScale;
        uniform float uOutputOffset;
        out float oUnblocker;

        uvec2 greensAt(ivec2 q) {
            // Raw16 Unblocker mirrors Bayer quads, repeating the boundary quad.
            ivec2 period = (uRawSize / 2) * 2;
            q = (q % period + period) % period;
            ivec2 p = min(q, period - ivec2(1) - q) * 2;
            uint p00 = texelFetch(uRaw, p, 0).r;
            uint p10 = texelFetch(uRaw, p + ivec2(1, 0), 0).r;
            uint p01 = texelFetch(uRaw, p + ivec2(0, 1), 0).r;
            uint p11 = texelFetch(uRaw, p + ivec2(1), 0).r;
            uvec4 v;
            if (uCfaPattern == 0) v = uvec4(p00, p10, p01, p11);
            else if (uCfaPattern == 1) v = uvec4(p10, p00, p11, p01);
            else if (uCfaPattern == 2) v = uvec4(p01, p11, p00, p10);
            else v = uvec4(p11, p01, p10, p00);
            return v.yz;
        }
        uint averageGreen(ivec2 q) {
            uvec2 g = greensAt(q);
            return (g.x + g.y + 1u) >> 1u;
        }
        uint verticalGreen(ivec2 q) {
            uint outer = (averageGreen(q - ivec2(0, 1)) +
                averageGreen(q + ivec2(0, 1))) >> 1u;
            return (outer + averageGreen(q) + 1u) >> 1u;
        }
        uint blurredGreen(ivec2 q) {
            uint outer = (verticalGreen(q - ivec2(1, 0)) +
                verticalGreen(q + ivec2(1, 0)) + 1u) >> 1u;
            return (outer + verticalGreen(q)) >> 1u;
        }
        // Low/high limbs preserve the original integer moments for RAW16 as well
        // as RAW10. A float sum loses low bits before the variance subtraction.
        uvec2 addWide(uvec2 a, uvec2 b) {
            uint low = a.x + b.x;
            return uvec2(low, a.y + b.y + (low < a.x ? 1u : 0u));
        }
        float roundedVariance(uint sum, uvec2 squareSum, uint countShift) {
            uvec2 numerator = uvec2(
                squareSum.x << countShift,
                (squareSum.y << countShift) | (squareSum.x >> (32u - countShift))
            );
            // sum <= 128 * 65535, so the doubled 16-bit cross product fits U32.
            // Keep this in ES 3.00 without extended-integer built-ins.
            uint lo16 = sum & 65535u;
            uint hi16 = sum >> 16u;
            uint cross = 2u * lo16 * hi16;
            uvec2 squared = addWide(uvec2(lo16 * lo16, hi16 * hi16),
                uvec2(cross << 16u, cross >> 16u));
            numerator = uvec2(
                numerator.x - squared.x,
                numerator.y - squared.y - (numerator.x < squared.x ? 1u : 0u)
            );
            uint divisorShift = countShift * 2u;
            numerator = addWide(numerator, uvec2(1u << (divisorShift - 1u), 0u));
            return float((numerator.x >> divisorShift) |
                (numerator.y << (32u - divisorShift)));
        }
        void main() {
            // The original AOT evaluates one extra cell on every side before its
            // UnblockerBlur pass. uTileOffset is (-1, -1) for that padded domain.
            ivec2 tile = ivec2(gl_FragCoord.xy) + uTileOffset;
            ivec2 origin = tile * 8;
            uint preSum = 0u;
            uvec2 preSquareSum = uvec2(0u);
            uint postSum = 0u;
            uvec2 postSquareSum = uvec2(0u);
            for (int y = 0; y < 8; ++y) {
                for (int x = 0; x < 8; ++x) {
                    ivec2 q = origin + ivec2(x, y);
                    uvec2 g = greensAt(q);
                    uint b = blurredGreen(q);
                    preSum += g.x + g.y;
                    preSquareSum = addWide(preSquareSum, uvec2(g.x * g.x, 0u));
                    preSquareSum = addWide(preSquareSum, uvec2(g.y * g.y, 0u));
                    postSum += b;
                    postSquareSum = addWide(postSquareSum, uvec2(b * b, 0u));
                }
            }
            float preMean = float((preSum + 64u) >> 7u);
            float preVariance = roundedVariance(preSum, preSquareSum, 7u);
            float postVariance = roundedVariance(postSum, postSquareSum, 6u);
            float signal = max(preMean - uBlackLevelGreen, 0.0);
            float predictedNoise =
                (uNoiseQuadratic * signal + uNoiseScale) * signal +
                uNoiseOffset;
            float correctedVariance = max(
                preVariance - 4.0 * predictedNoise,
                0.0
            );
            float denominator = postVariance * (128.0 / 9.0);
            float ratio = denominator > 0.0
                ? correctedVariance / denominator
                : 0.0;
            float mapped = denominator > 0.0
                ? uOutputScale * (sqrt(max(ratio, 0.0)) - uOutputOffset)
                : (correctedVariance > 0.0 ? uOutputScale : 0.0);
            // The AOT converts with fcvtzs before storing U8. Quantize explicitly so the
            // normalized GL_R8 conversion cannot round a boundary upward.
            oUnblocker = floor(clamp(mapped, 0.0, 1.0) * 255.0) / 255.0;
        }
    """.trimIndent()

    val unblockerBlur = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
        precision highp int;
        uniform sampler2D uPreBlur;
        out float oUnblocker;

        int valueAt(ivec2 p) {
            return int(floor(texelFetch(uPreBlur, p, 0).r * 255.0 + 0.5));
        }
        int halvingAdd(int a, int b) {
            return (a + b) >> 1;
        }
        int roundedHalvingAdd(int a, int b) {
            return (a + b + 1) >> 1;
        }
        void main() {
            // The output cell (x,y) is centered at (x+1,y+1) in the padded map.
            ivec2 p = ivec2(gl_FragCoord.xy);
            int topLeft = valueAt(p + ivec2(0, 0));
            int top = valueAt(p + ivec2(1, 0));
            int topRight = valueAt(p + ivec2(2, 0));
            int left = valueAt(p + ivec2(0, 1));
            int center = valueAt(p + ivec2(1, 1));
            int right = valueAt(p + ivec2(2, 1));
            int bottomLeft = valueAt(p + ivec2(0, 2));
            int bottom = valueAt(p + ivec2(1, 2));
            int bottomRight = valueAt(p + ivec2(2, 2));

            int leftPair = halvingAdd(topLeft, bottomLeft);
            int rightPair = halvingAdd(topRight, bottomRight);
            int leftColumn = roundedHalvingAdd(leftPair, left);
            int rightColumn = roundedHalvingAdd(rightPair, right);
            int outerColumns = roundedHalvingAdd(leftColumn, rightColumn);
            int middlePair = halvingAdd(top, bottom);
            int middleColumn = roundedHalvingAdd(middlePair, center);
            int filtered = halvingAdd(outerColumns, middleColumn);
            oUnblocker = float(filtered) / 255.0;
        }
    """.trimIndent()
}
