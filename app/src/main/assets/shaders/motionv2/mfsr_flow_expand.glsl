#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D TileFlow;
layout(rgba16f,binding=0) uniform highp writeonly image2D OutputFlow;
uniform ivec2 outputSize;
uniform int tileSize;

/* IRIS_26462_WRONSKI_NEAREST_TILE_FLOW_EXPAND
 * Public/IPOL configuration uses nearest flow upscaling. Subpixel precision
 * remains in each tile flow because ICA refines it in float coordinates.
 */
void main() {
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(p,outputSize))) return;
    ivec2 gs=textureSize(TileFlow,0);
    ivec2 tile=clamp(p/max(tileSize,1),ivec2(0),gs-ivec2(1));
    vec4 f=texelFetch(TileFlow,tile,0);
    imageStore(OutputFlow,p,f);
}