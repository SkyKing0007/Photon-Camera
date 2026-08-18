#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D ReferenceGuide;
uniform highp sampler2D MovingGuide;
uniform highp sampler2D CoarseFlow;
layout(rgba16f,binding=0) uniform highp writeonly image2D OutputFlow;
uniform ivec2 levelSize;
uniform ivec2 coarseGridSize;
uniform int coarseTileSize;
uniform int targetTileSize;
uniform float coarseToTargetScale;
float atRef(ivec2 p){return texelFetch(ReferenceGuide,clamp(p,ivec2(0),levelSize-ivec2(1)),0).r;}
float atMov(ivec2 p){return texelFetch(MovingGuide,clamp(p,ivec2(0),levelSize-ivec2(1)),0).r;}
ivec2 clampTile(ivec2 p){return clamp(p,ivec2(0),coarseGridSize-ivec2(1));}
vec2 flowAt(ivec2 p){return texelFetch(CoarseFlow,clampTile(p),0).xy*coarseToTargetScale;}
float costAt(ivec2 origin,vec2 f){ivec2 d=ivec2(round(f));float c=0.0;float n=0.0;for(int y=0;y<32;y+=2){if(y>=targetTileSize)continue;for(int x=0;x<32;x+=2){if(x>=targetTileSize)continue;ivec2 p=origin+ivec2(x,y);if(any(greaterThanEqual(p,levelSize)))continue;c+=abs(atRef(p)-atMov(p+d));n+=1.0;}}return c/max(n,1.0);}
/* IRIS_26484_BJZHOU_THREE_CANDIDATE_L1_UPSAMPLE
 * Preserve whole coarse vectors at motion boundaries. For each finer tile, test the nearest
 * coarse flow plus the next-nearest candidate on X and Y in the target-level image, then pass
 * the best whole vector into LK. This avoids synthesizing a motion vector between objects.
 */
void main(){
 ivec2 t=ivec2(gl_GlobalInvocationID.xy);ivec2 tg=imageSize(OutputFlow);if(any(greaterThanEqual(t,tg)))return;
 vec2 center=(vec2(t)+0.5)*float(targetTileSize);
 vec2 cg=center/(max(coarseToTargetScale,1e-6)*float(coarseTileSize))-vec2(0.5);
 vec2 nr=round(cg);ivec2 near=clampTile(ivec2(nr));ivec2 nx=clampTile(ivec2(nr)+ivec2(cg.x<nr.x?-1:1,0));ivec2 ny=clampTile(ivec2(nr)+ivec2(0,cg.y<nr.y?-1:1));
 ivec2 origin=t*targetTileSize;vec2 best=flowAt(near);float bestCost=costAt(origin,best);float idx=0.0;
 vec2 fx=flowAt(nx);float cx=costAt(origin,fx);if(cx<bestCost){best=fx;bestCost=cx;idx=1.0;}
 vec2 fy=flowAt(ny);float cy=costAt(origin,fy);if(cy<bestCost){best=fy;bestCost=cy;idx=2.0;}
 imageStore(OutputFlow,t,vec4(best,bestCost,idx));
}
