precision highp float; precision highp sampler2D;
uniform sampler2D InputRgb; uniform mat3 sensorToLinearSrgb; out vec4 Output;
void main(){ivec2 p=ivec2(gl_FragCoord.xy);vec3 v=texelFetch(InputRgb,p,0).rgb;Output=vec4(max(sensorToLinearSrgb*v,vec3(0.0)),1.0);}
