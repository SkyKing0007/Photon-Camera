#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D TileFlow;
layout(rgba16f,binding=0) uniform highp writeonly image2D OutputFlow;
uniform ivec2 outputSize;
uniform int tileSize;
uniform float interpolationTolerance;
vec2 fAt(ivec2 p){ivec2 s=textureSize(TileFlow,0);return texelFetch(TileFlow,clamp(p,ivec2(0),s-ivec2(1)),0).xy;}
/* IRIS_26484_BJZHOU_SAFE_SPATIAL_FLOW_RECONSTRUCTION
 * Interpolate only when all four neighboring tile vectors agree with the base vector inside the
 * MGC tolerance. Otherwise preserve the whole base vector. Z carries local 3x3 flow variation for
 * rejection; W remains reserved.
 */
void main(){
 ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,outputSize)))return;int ts=max(tileSize,1);ivec2 gs=textureSize(TileFlow,0);
 ivec2 tile=clamp(p/ts,ivec2(0),gs-ivec2(1));ivec2 off=p-tile*ts;vec2 base=fAt(tile);vec2 outF=base;
 bool left=off.x<=ts/2,top=off.y<=ts/2;ivec2 t00=ivec2(left?tile.x-1:tile.x,top?tile.y-1:tile.y);vec2 f00=fAt(t00),f10=fAt(t00+ivec2(1,0)),f01=fAt(t00+ivec2(0,1)),f11=fAt(t00+ivec2(1,1));float th=float(ts)*interpolationTolerance;
 bool cancel=any(greaterThanEqual(abs(f00-base),vec2(th)))||any(greaterThanEqual(abs(f10-base),vec2(th)))||any(greaterThanEqual(abs(f01-base),vec2(th)))||any(greaterThanEqual(abs(f11-base),vec2(th)));
 if(!cancel){float ux=float(p.x)/float(ts)-(float(t00.x)+0.5);float uy=float(p.y)/float(ts)-(float(t00.y)+0.5);outF=mix(mix(f00,f10,ux),mix(f01,f11,ux),uy);}
 vec2 mn=vec2(3.4e38),mx=vec2(-3.4e38);for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){vec2 v=fAt(tile+ivec2(x,y));mn=min(mn,v);mx=max(mx,v);}float variation=length((mx-mn)/max(vec2(outputSize),vec2(1.0)));
 imageStore(OutputFlow,p,vec4(outF,variation,cancel?1.0:0.0));
}
