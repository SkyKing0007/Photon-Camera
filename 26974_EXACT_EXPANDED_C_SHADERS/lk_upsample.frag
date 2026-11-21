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
