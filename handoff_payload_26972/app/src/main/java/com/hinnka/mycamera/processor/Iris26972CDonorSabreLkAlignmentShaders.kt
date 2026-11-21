package com.hinnka.mycamera.processor

/**
 * C-only ports of the pinned bjzhou 1.29.0 GLSL LK stages:
 * GradientAndGradientProducts, BlockLucasKanade (GLES3 fragment fallback),
 * and UpsampleAlignmentI16Halide three-local-plus-global candidate selection.
 * Git blob: f51c5976adb368da7ee9d312731b36b393d7a8c4.
 * No source text is loaded from, or dynamically delegated to, Iris A/B.
 */
internal object Iris26972CDonorSabreLkAlignmentShaders {
    val gradientProducts = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
        precision highp int;
        precision highp isampler2D;
        uniform highp isampler2D uReference;
        uniform ivec2 uImageSize;
        uniform int uTileStride;
        uniform int uTileSize;
        layout(location = 0) out vec4 oProducts0;

        float valueAt(ivec2 p) {
            return float(texelFetch(
                uReference,
                clamp(p, ivec2(0), uImageSize - ivec2(1)),
                0
            ).r);
        }
        vec2 gradientAt(ivec2 p) {
            return clamp(
                vec2(
                    valueAt(p + ivec2(1, 0)) - valueAt(p - ivec2(1, 0)),
                    valueAt(p + ivec2(0, 1)) - valueAt(p - ivec2(0, 1))
                ),
                vec2(-32768.0),
                vec2(32767.0)
            );
        }
        void main() {
            ivec2 tile = ivec2(gl_FragCoord.xy);
            ivec2 origin = (tile + ivec2(1)) * uTileStride;
            int sampleStep = 1;
            float count = float((uTileSize / sampleStep) * (uTileSize / sampleStep));
            float xx = 0.0;
            float yy = 0.0;
            float xy = 0.0;
            for (int y = 0; y < 64; y += sampleStep) {
                if (y >= uTileSize) break;
                for (int x = 0; x < 64; x += sampleStep) {
                    if (x >= uTileSize) break;
                    ivec2 p = origin + ivec2(x, y);
                    vec2 gradient = gradientAt(p);
                    xx += gradient.x * gradient.x;
                    yy += gradient.y * gradient.y;
                    xy += gradient.x * gradient.y;
                }
            }
            float inverseCount = 1.0 / count;
            vec3 hessian = vec3(
                0.25 * xx * inverseCount,
                0.25 * yy * inverseCount,
                0.25 * xy * inverseCount
            );
            bool xMajor = hessian.x >= hessian.y;
            float major = xMajor ? hessian.x : hessian.y;
            float slope = major > 0.0 ? hessian.z / major : 0.0;
            float orthogonalEnergy = 0.0;
            for (int y = 0; y < 64; y += sampleStep) {
                if (y >= uTileSize) break;
                for (int x = 0; x < 64; x += sampleStep) {
                    if (x >= uTileSize) break;
                    vec2 gradient = gradientAt(origin + ivec2(x, y));
                    float residual = xMajor
                        ? gradient.y - slope * gradient.x
                        : gradient.x - slope * gradient.y;
                    orthogonalEnergy += residual * residual;
                }
            }
            oProducts0 = vec4(hessian, major * (0.25 * orthogonalEnergy * inverseCount));
        }
    """.trimIndent()

    private val lkCommon = """
        precision highp float;
        precision highp sampler2D;
        precision highp int;
        precision highp isampler2D;
        uniform highp isampler2D uReference;
        uniform highp isampler2D uCurrent;
        uniform sampler2D uProducts0;
        uniform sampler2D uInitialAlignment;
        uniform ivec2 uImageSize;
        uniform ivec2 uGridSize;
        uniform int uTileStride;
        uniform int uTileSize;
        uniform int uNormalize;
        uniform int uHasInitialAlignment;

        int referenceValueAt(ivec2 p) {
            return texelFetch(
                uReference,
                clamp(p, ivec2(0), uImageSize - ivec2(1)),
                0
            ).r;
        }
        float referenceAt(ivec2 p) {
            return float(referenceValueAt(p));
        }
        vec2 gradientAt(ivec2 p) {
            return clamp(
                vec2(
                    referenceAt(p + ivec2(1, 0)) -
                        referenceAt(p - ivec2(1, 0)),
                    referenceAt(p + ivec2(0, 1)) -
                        referenceAt(p - ivec2(0, 1))
                ),
                vec2(-32768.0),
                vec2(32767.0)
            );
        }
        int currentAt(ivec2 p) {
            return texelFetch(
                uCurrent,
                clamp(p, ivec2(0), uImageSize - ivec2(1)),
                0
            ).r;
        }
        int q15Weight(float value) {
            return clamp(int(floor(value * 32768.0)), 0, 32767);
        }
        int roundedShiftRight15(int value) {
            int biased = value + 16384;
            return biased >= 0
                ? biased / 32768
                : -((-biased + 32767) / 32768);
        }
        int warpedCurrentValueAt(vec2 p) {
            vec2 bounded = clamp(
                p,
                vec2(0.0),
                vec2(uImageSize - ivec2(1))
            );
            ivec2 p0 = ivec2(floor(bounded));
            vec2 fraction = fract(bounded);
            int w00 = q15Weight((1.0 - fraction.x) * (1.0 - fraction.y));
            int w10 = q15Weight(fraction.x * (1.0 - fraction.y));
            int w01 = q15Weight((1.0 - fraction.x) * fraction.y);
            int w11 = q15Weight(fraction.x * fraction.y);
            int weighted =
                currentAt(p0) * w00 +
                currentAt(p0 + ivec2(1, 0)) * w10 +
                currentAt(p0 + ivec2(0, 1)) * w01 +
                currentAt(p0 + ivec2(1, 1)) * w11;
            return clamp(roundedShiftRight15(weighted), -32768, 32767);
        }
        float warpedCurrentAt(vec2 p) {
            return float(warpedCurrentValueAt(p));
        }
        vec3 initialAlignmentAt(ivec2 tile) {
            return uHasInitialAlignment != 0
                ? texelFetch(
                    uInitialAlignment,
                    clamp(tile, ivec2(0), uGridSize - ivec2(1)),
                    0
                ).xyz
                : vec3(0.0);
        }
        vec4 solveAlignment(ivec2 tile, vec3 initialAlignment, vec2 target, float count) {
            vec4 products0 = texelFetch(uProducts0, tile, 0);
            float bx = 0.5 * target.x / count;
            float by = 0.5 * target.y / count;
            float inverseDeterminant = 1.0 / (1.0 + products0.w);
            vec2 delta = inverseDeterminant * vec2(
                products0.z * by - products0.y * bx,
                products0.z * bx - products0.x * by
            );
            return vec4(
                initialAlignment.xy + clamp(delta, vec2(-1.0), vec2(1.0)),
                initialAlignment.z,
                0.0
            );
        }
    """.trimIndent()

    val blockLucasKanade = "#version 300 es\n" + lkCommon + "\n" + """
        out vec4 oAlignment;
        void main() {
            ivec2 tile = ivec2(gl_FragCoord.xy);
            vec3 initialAlignment = initialAlignmentAt(tile);
            vec2 flow = initialAlignment.xy;
            ivec2 origin = (tile + ivec2(1)) * uTileStride;
            float count = float(uTileSize * uTileSize);
            float meanResidual = 0.0;
            if (uNormalize != 0) {
                for (int y = 0; y < 64; ++y) {
                    if (y >= uTileSize) break;
                    for (int x = 0; x < 64; ++x) {
                        if (x >= uTileSize) break;
                        meanResidual += warpedCurrentAt(
                            vec2(origin + ivec2(x, y)) + flow
                        ) - referenceAt(origin + ivec2(x, y));
                    }
                }
                meanResidual /= count;
            }
            vec2 target = vec2(0.0);
            for (int y = 0; y < 64; ++y) {
                if (y >= uTileSize) break;
                for (int x = 0; x < 64; ++x) {
                    if (x >= uTileSize) break;
                    ivec2 p = origin + ivec2(x, y);
                    float residual = warpedCurrentAt(vec2(p) + flow) -
                        referenceAt(p) - meanResidual;
                    target += residual * gradientAt(p);
                }
            }
            oAlignment = solveAlignment(tile, initialAlignment, target, count);
        }
    """.trimIndent()

    val upsampleAlignment = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
        precision highp int;
        precision highp isampler2D;
        uniform highp isampler2D uReference;
        uniform highp isampler2D uCurrent;
        uniform sampler2D uInitialAlignment;
        uniform ivec2 uImageSize;
        uniform ivec2 uInitialGridSize;
        uniform int uInitialGridMin;
        uniform int uTargetGridMin;
        uniform int uInitialTileStride;
        uniform int uTargetTileStride;
        uniform int uTargetTileSize;
        uniform ivec2 uTargetImageOffset;
        uniform float uInitialScale;
        uniform int uHasGlobalCandidate;
        uniform vec2 uGlobalCandidate;
        out vec4 oAlignment;
        int valueAt(highp isampler2D image, ivec2 p) {
            return texelFetch(
                image,
                clamp(p, ivec2(0), uImageSize - ivec2(1)),
                0
            ).r;
        }
        ivec2 boundedInitialTile(ivec2 p) {
            return clamp(p, ivec2(0), uInitialGridSize - ivec2(1));
        }
        vec2 candidateFlow(ivec2 p) {
            return texelFetch(
                uInitialAlignment,
                boundedInitialTile(p),
                0
            ).xy * uInitialScale;
        }
        float candidateCost(ivec2 origin, vec2 flow) {
            ivec2 displacement = ivec2(roundEven(flow));
            int cost = 0;
            for (int y = 0; y < 64; y += 1) {
                if (y >= uTargetTileSize) break;
                for (int x = 0; x < 64; x += 1) {
                    if (x >= uTargetTileSize) break;
                    ivec2 p = origin + ivec2(x, y);
                    cost += abs(
                        valueAt(uReference, p) -
                        valueAt(uCurrent, p + displacement)
                    );
                }
            }
            return float(cost) / float(uTargetTileSize * uTargetTileSize);
        }
        void main() {
            ivec2 targetTile = ivec2(gl_FragCoord.xy);
            ivec2 targetLogicalTile = targetTile + ivec2(uTargetGridMin);
            vec2 targetCenter =
                (vec2(targetLogicalTile) + vec2(0.5)) *
                float(uTargetTileStride);
            vec2 initialGrid =
                targetCenter /
                (uInitialScale * float(uInitialTileStride)) -
                vec2(float(uInitialGridMin) + 0.5);
            vec2 nearestPosition = roundEven(initialGrid);
            ivec2 nearest = ivec2(nearestPosition);
            ivec2 nextX = nearest + ivec2(
                initialGrid.x < nearestPosition.x ? -1 : 1, 0
            );
            ivec2 nextY = nearest + ivec2(
                0, initialGrid.y < nearestPosition.y ? -1 : 1
            );
            nearest = boundedInitialTile(nearest);
            nextX = boundedInitialTile(nextX);
            nextY = boundedInitialTile(nextY);
            ivec2 origin = targetLogicalTile * uTargetTileStride - uTargetImageOffset;
            vec2 bestFlow = candidateFlow(nearest);
            vec2 nearestFlow = bestFlow;
            float bestCost = candidateCost(origin, bestFlow);
            float nearestCost = bestCost;
            float candidateIndex = 0.0;
            vec2 flowX = candidateFlow(nextX);
            float costX = all(equal(roundEven(flowX), roundEven(nearestFlow))) ? nearestCost :
                candidateCost(origin, flowX);
            if (costX < bestCost) {
                bestFlow = flowX;
                bestCost = costX;
                candidateIndex = 1.0;
            }
            vec2 flowY = candidateFlow(nextY);
            float costY = all(equal(roundEven(flowY), roundEven(nearestFlow))) ? nearestCost :
                all(equal(roundEven(flowY), roundEven(flowX))) ? costX :
                candidateCost(origin, flowY);
            if (costY < bestCost) {
                bestFlow = flowY;
                bestCost = costY;
                candidateIndex = 2.0;
            }
            if (uHasGlobalCandidate != 0) {
                vec2 globalFlow = uGlobalCandidate * uInitialScale;
                float globalCost = all(equal(roundEven(globalFlow), roundEven(nearestFlow))) ? nearestCost :
                    all(equal(roundEven(globalFlow), roundEven(flowY))) ? costY :
                    all(equal(roundEven(globalFlow), roundEven(flowX))) ? costX :
                    candidateCost(origin, globalFlow);
                if (globalCost < bestCost) {
                    bestFlow = globalFlow;
                    bestCost = globalCost;
                    candidateIndex = 3.0;
                }
            }
            oAlignment = vec4(bestFlow, bestCost, candidateIndex);
        }
    """.trimIndent()
}
