precision highp float; precision highp sampler2D;
uniform sampler2D InputRgb; uniform sampler2D ClipMask; uniform ivec2 rawSize; out vec4 Output;
ivec2 clp(ivec2 p){return clamp(p,ivec2(0),rawSize-ivec2(1));}
/* Saved-only single-frame highlight reconstruction. It changes a pixel only when the
 * exact physical Bayer observation at that coordinate was at sensor clip. Neighbor
 * chroma ratios come only from nearby unclipped pixels; otherwise original RCD wins. */
void main(){ivec2 p=ivec2(gl_FragCoord.xy);vec3 c=texelFetch(InputRgb,p,0).rgb;if(texelFetch(ClipMask,p,0).r<0.5){Output=vec4(c,1.0);return;}float y=max(dot(c,vec3(0.2126,0.7152,0.0722)),1e-6);vec3 sum=vec3(0.0);float wsum=0.0;for(int j=-2;j<=2;j++){for(int i=-2;i<=2;i++){if(i==0&&j==0)continue;ivec2 q=clp(p+ivec2(i,j));if(texelFetch(ClipMask,q,0).r>=0.5)continue;vec3 n=max(texelFetch(InputRgb,q,0).rgb,vec3(0.0));float ny=max(dot(n,vec3(0.2126,0.7152,0.0722)),1e-6);float d=float(i*i+j*j);float w=1.0/(1.0+d);sum+=w*(n/ny);wsum+=w;}}if(wsum>1e-5){vec3 ratio=sum/wsum;vec3 est=max(ratio*y,vec3(0.0));float m=max(max(c.r,c.g),c.b);float t=smoothstep(0.985,1.02,m);c=mix(c,max(c,est),t);}Output=vec4(c,1.0);}
