precision highp float;
precision highp sampler2D;
uniform sampler2D InputBuffer;
uniform sampler2D Watermark;
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

void main() {
    ivec2 xy = ivec2(gl_FragCoord.xy);
    ivec2 texSize = ivec2(textureSize(InputBuffer, 0));
    vec2 texS = vec2(textureSize(InputBuffer, 0));
    vec2 watersize = vec2(textureSize(Watermark, 0));
    vec2 noiseSize = vec2(textureSize(Noise, 0));
    vec4 water;
    xy+=ivec2(0,yOffset)+ivec2(OFFSET);
    switch(rotate){
        case 0:
        xy += ivec2(0,(rawSize.y-cropSize.y));
        if(mirror)
            xy.y = texSize.y - xy.y;
        Output = texelFetch(InputBuffer, xy, 0);
        break;
        case 1:

        xy += ivec2((rawSize.y-cropSize.y),0);
        if(mirror)
            xy.x = cropSize.y - xy.x;
        Output = texelFetch(InputBuffer, ivec2(texSize.x-xy.y,xy.x), 0);
        break;
        case 2:
        //xy += ivec2(0,-(texSize.y-rotatedSize.y)/4);
        if(mirror)
            xy.y = texSize.y - xy.y;
        Output = texelFetch(InputBuffer, ivec2(texSize.x-xy.x,texSize.y-xy.y), 0);
        break;
        case 3:
        //xy += ivec2(-(texSize.x-rotatedSize.x)/4,0);
        if(mirror)
            xy.x = cropSize.y - xy.x;
        Output = texelFetch(InputBuffer, ivec2(xy.y,texSize.y-xy.x),0);
        break;
    }
    #if WATERMARK == 1
    /* IRIS_26677_IRIS_WATERMARK_OUTPUT_OWNER
     * Final-raster normalized geometry only: 11.5% of final width, 2.5% safe inset, lower-right, using global tiled-raster coordinates.
     * This is independent of screen density/device and occurs after HDR/tone/color processing. */
    vec2 iris26676OutSize = (rotate == 1 || rotate == 3)
            ? vec2(float(cropSize.y), float(cropSize.x))
            : vec2(float(cropSize.x), float(cropSize.y));
    float iris26677WmWidth = iris26676OutSize.x * 0.115;
    float iris26677WmHeight = iris26677WmWidth * (watersize.y / watersize.x);
    float iris26677Margin = max(2.0, min(iris26676OutSize.x, iris26676OutSize.y) * 0.025);
    float iris26677Left = iris26676OutSize.x - iris26677Margin - iris26677WmWidth;
    float iris26677Bottom = iris26677Margin;
    vec2 iris26677Frag = vec2(gl_FragCoord.x, gl_FragCoord.y + float(yOffset));
    if (iris26677Frag.x >= iris26677Left
            && iris26677Frag.x <= iris26677Left + iris26677WmWidth
            && iris26677Frag.y >= iris26677Bottom
            && iris26677Frag.y <= iris26677Bottom + iris26677WmHeight) {
        vec2 iris26677Uv = vec2(
                (iris26677Frag.x - iris26677Left) / iris26677WmWidth,
                (iris26677Frag.y - iris26677Bottom) / iris26677WmHeight);
        water = texture(Watermark, iris26677Uv);
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
