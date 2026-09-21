precision highp float; precision highp usampler2D;
uniform highp usampler2D InputBuffer; uniform vec4 blackLevel; uniform float whiteLevel; out vec4 Output;
float n(ivec2 p,int q){float v=float(texelFetch(InputBuffer,p,0).r);float b=q==0?blackLevel.r:(q==1?blackLevel.g:(q==2?blackLevel.b:blackLevel.a));return max((v-b)/max(whiteLevel-b,1.0),0.0);}
void main(){ivec2 p=ivec2(gl_FragCoord.xy)*2;Output=vec4(n(p,0),n(p+ivec2(1,0),1),n(p+ivec2(0,1),2),n(p+ivec2(1,1),3));}
