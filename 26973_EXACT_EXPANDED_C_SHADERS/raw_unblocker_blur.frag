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
