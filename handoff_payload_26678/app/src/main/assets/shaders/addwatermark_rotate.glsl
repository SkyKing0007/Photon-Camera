precision highp float;
precision highp sampler2D;
uniform sampler2D InputBuffer;
uniform sampler2D WatermarkDark;
uniform sampler2D WatermarkWhite;
uniform sampler2D Noise;
uniform int yOffset;
uniform int rotate;
uniform bool mirror;
uniform ivec2 cropSize;
uniform ivec2 rawSize;
out vec4 Output;
#define WATERMARK 1
#define OFFSET 0,0
#import interpolation

// Triangular remapping: maps [0,1] blue noise to [-0.5, 0.5] with triangular distribution.
// This eliminates the DC bias of simple centered remapping and produces
// a smoother error distribution across adjacent quantization levels.
float triRemap(float v) {
    float orig = v * 2.0 - 1.0;
    return sign(orig) * (1.0 - sqrt(1.0 - abs(orig))) * 0.5;
}
vec3 triRemap(vec3 v) {
    return vec3(triRemap(v.r), triRemap(v.g), triRemap(v.b));
}

/* IRIS_26678_ADAPTIVE_WATERMARK_BACKGROUND_OWNER
 * Fetch a pixel in the final oriented GL output coordinate system without changing AE/HDR.
 * Every watermark fragment evaluates the same five destination samples, so the entire logo uses
 * one coherent variant rather than changing color per-pixel on mixed backgrounds. */
vec4 iris26678FetchFinal(ivec2 finalXY) {
    ivec2 texSizeLocal = ivec2(textureSize(InputBuffer, 0));
    ivec2 q = finalXY + ivec2(OFFSET);
    ivec2 src = q;
    switch(rotate) {
        case 0:
            q += ivec2(0, (rawSize.y-cropSize.y));
            if(mirror) q.y = texSizeLocal.y - q.y;
            src = q;
            break;
        case 1:
            q += ivec2((rawSize.y-cropSize.y), 0);
            if(mirror) q.x = cropSize.y - q.x;
            src = ivec2(texSizeLocal.x-q.y, q.x);
            break;
        case 2:
            if(mirror) q.y = texSizeLocal.y - q.y;
            src = ivec2(texSizeLocal.x-q.x, texSizeLocal.y-q.y);
            break;
        case 3:
            if(mirror) q.x = cropSize.y - q.x;
            src = ivec2(q.y, texSizeLocal.y-q.x);
            break;
    }
    src = clamp(src, ivec2(0), texSizeLocal - ivec2(1));
    return texelFetch(InputBuffer, src, 0);
}

float iris26678BackgroundLuma(vec2 finalPoint) {
    vec3 c = clamp(iris26678FetchFinal(ivec2(finalPoint)).rgb, vec3(0.0), vec3(1.0));
    return dot(c, vec3(0.2126, 0.7152, 0.0722));
}

void main() {
    ivec2 xy = ivec2(gl_FragCoord.xy) + ivec2(0, yOffset);
    vec2 watersize = vec2(textureSize(WatermarkDark, 0));
    vec2 noiseSize = vec2(textureSize(Noise, 0));
    vec4 water;
    Output = iris26678FetchFinal(xy);
    #if WATERMARK == 1
    /* IRIS_26678_FINAL_RASTER_WATERMARK_OUTPUT_OWNER
     * Final-raster normalized geometry only: 11.5% of final width, 2.5% safe inset, lower-right, using global tiled-raster coordinates.
     * This is independent of screen density/device and occurs after HDR/tone/color processing. */
    vec2 iris26676OutSize = (rotate == 1 || rotate == 3)
            ? vec2(float(cropSize.y), float(cropSize.x))
            : vec2(float(cropSize.x), float(cropSize.y));
    float iris26677WmWidth = iris26676OutSize.x * 0.115;
    float iris26677WmHeight = iris26677WmWidth * (watersize.y / watersize.x);
    float iris26677Margin = max(2.0, min(iris26676OutSize.x, iris26676OutSize.y) * 0.025);
    float iris26677Left = iris26676OutSize.x - iris26677Margin - iris26677WmWidth;
    /* IRIS_26678_GL_READBACK_TOP_ORIGIN_CONTRACT
     * GLCoreBlockProcessing writes glReadPixels row zero directly as Android Bitmap row zero.
     * Therefore final-raster bottom-right is the high-GL-y interval, not y=margin. */
    float iris26678FinalTop = iris26676OutSize.y - iris26677Margin - iris26677WmHeight;
    vec2 iris26677Frag = vec2(gl_FragCoord.x, gl_FragCoord.y + float(yOffset));
    if (iris26677Frag.x >= iris26677Left
            && iris26677Frag.x <= iris26677Left + iris26677WmWidth
            && iris26677Frag.y >= iris26678FinalTop
            && iris26677Frag.y <= iris26678FinalTop + iris26677WmHeight) {
        vec2 iris26677Uv = vec2(
                (iris26677Frag.x - iris26677Left) / iris26677WmWidth,
                (iris26677Frag.y - iris26678FinalTop) / iris26677WmHeight);
        float iris26678Background = (
                iris26678BackgroundLuma(vec2(iris26677Left + iris26677WmWidth * 0.20, iris26678FinalTop + iris26677WmHeight * 0.20))
                + iris26678BackgroundLuma(vec2(iris26677Left + iris26677WmWidth * 0.80, iris26678FinalTop + iris26677WmHeight * 0.20))
                + iris26678BackgroundLuma(vec2(iris26677Left + iris26677WmWidth * 0.50, iris26678FinalTop + iris26677WmHeight * 0.50))
                + iris26678BackgroundLuma(vec2(iris26677Left + iris26677WmWidth * 0.20, iris26678FinalTop + iris26677WmHeight * 0.80))
                + iris26678BackgroundLuma(vec2(iris26677Left + iris26677WmWidth * 0.80, iris26678FinalTop + iris26677WmHeight * 0.80))) / 5.0;
        bool iris26678UseDark = iris26678Background >= 0.55;
        water = iris26678UseDark
                ? texture(WatermarkDark, iris26677Uv)
                : texture(WatermarkWhite, iris26677Uv);
        Output = mix(Output, water, water.a);
    }
    #endif
    //Output*=1.005;

    // Blue noise dithering: tile noise over the output at 1:1 pixel ratio.
    // Triangular remap gives a zero-mean [-0.5, 0.5] distribution, scaled
    // to one 8-bit quantization step so dither is invisible but breaks banding.
    vec2 noiseUV = vec2(gl_FragCoord.xy) / noiseSize;
    vec3 noiseVal = texture(Noise, noiseUV).rgb;
    //Output.rgb += triRemap(noiseVal) * (2.0 / 255.0);
    Output = clamp(Output, 0.0, 1.0);
    Output.a = 1.0;

}
