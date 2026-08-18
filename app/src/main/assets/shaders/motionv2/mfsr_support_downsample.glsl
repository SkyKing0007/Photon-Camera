#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
layout(rgba32f,binding=0) uniform highp readonly image2D frameSupport;
layout(r32f,binding=1) uniform highp writeonly image2D outSupport;

/* IRIS_26483_DIRECT_SUPPORT_TELEMETRY_DOWNSAMPLE
 * Diagnostic-only: replace the legacy per-frame CFA merge/support path with one
 * end-of-burst 2x2 reduction of the authoritative direct-Wronski frame support.
 */
void main(){
    ivec2 q=ivec2(gl_GlobalInvocationID.xy);ivec2 sz=imageSize(outSupport);if(any(greaterThanEqual(q,sz)))return;
    ivec2 b=q*2;ivec2 src=imageSize(frameSupport)-ivec2(1);float s=0.0;
    for(int y=0;y<2;y++)for(int x=0;x<2;x++)s+=max(imageLoad(frameSupport,min(b+ivec2(x,y),src)).r,0.0);
    imageStore(outSupport,q,vec4(1.0+0.25*s));
}
