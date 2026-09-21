precision highp float; precision highp sampler2D;
uniform sampler2D InputBayer; uniform ivec2 rawSize; uniform float clipThreshold; out float Output;
float phaseComponent(vec4 v,int q){return q==0?v.r:(q==1?v.g:(q==2?v.b:v.a));}
void main(){ivec2 p=ivec2(gl_FragCoord.xy);if(any(greaterThanEqual(p,rawSize))){Output=0.0;return;}int q=(p.x&1)|((p.y&1)<<1);float v=phaseComponent(texelFetch(InputBayer,p>>1,0),q);Output=v>=clipThreshold?1.0:0.0;}
