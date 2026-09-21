#define LAYOUT //
LAYOUT
precision highp float;precision highp int;precision highp image2D;
layout(std430,binding=1)readonly buffer RedBuf{
float red[];
};
layout(std430,binding=2)readonly buffer GreenBuf{
float green[];
};
layout(std430,binding=3)readonly buffer BlueBuf{
float blue[];
};
layout(rgba16f,binding=9)writeonly uniform highp image2D OutputRgb;
uniform ivec2 rawSize;uniform ivec2 bandSize;uniform ivec2 bandOrigin;uniform int coreLocalX;uniform int coreLocalY;uniform int coreRows;uniform vec3 calculationWb;
int idxAt(ivec2 p){return p.y*bandSize.x+p.x;}
/* IRIS_26498_RCD_TRUE_MIRRORED_HALO_BORDER
 * Every physical output pixel is at least 12 samples inside the virtual mirrored
 * RCD band, so the same directional reconstruction owns center and photo border.
 * No clamped edge kernel and no PPG algorithm switch remain.
 */
void main(){ivec2 gid=ivec2(gl_GlobalInvocationID.xy);if(gid.x>=rawSize.x||gid.y>=coreRows)return;ivec2 lp=ivec2(coreLocalX+gid.x,coreLocalY+gid.y);ivec2 gp=ivec2(gid.x,bandOrigin.y+lp.y);int i=idxAt(lp);vec3 rgb=max(vec3(red[i],green[i],blue[i]),vec3(0.0));rgb/=max(calculationWb,vec3(1.0e-6));imageStore(OutputRgb,gp,vec4(rgb,1.0));}
