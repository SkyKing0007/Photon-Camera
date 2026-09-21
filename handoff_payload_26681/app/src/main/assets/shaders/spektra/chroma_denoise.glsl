precision highp float; precision highp sampler2D;
uniform sampler2D InputRgb; uniform ivec2 imageSize; uniform float strength; out vec4 Output;
ivec2 clp(ivec2 p){return clamp(p,ivec2(0),imageSize-ivec2(1));}
float lum(vec3 v){return dot(v,vec3(0.2126,0.7152,0.0722));}
/* Single-frame luma-guided chroma-only denoise. Luma is exactly restored from the
 * center pixel; strength=0.75 is the audited saved-photo factory setting. */
void main(){ivec2 p=ivec2(gl_FragCoord.xy);vec3 c=max(texelFetch(InputRgb,p,0).rgb,vec3(0.0));float y=lum(c);vec3 chroma=c-vec3(y);vec3 sum=vec3(0.0);float wsum=0.0;for(int j=-2;j<=2;j++){for(int i=-2;i<=2;i++){ivec2 q=clp(p+ivec2(i,j));vec3 n=max(texelFetch(InputRgb,q,0).rgb,vec3(0.0));float ny=lum(n);float dl=abs(ny-y)/max(max(y,ny),0.03);float spatial=exp(-0.45*float(i*i+j*j));float edge=exp(-10.0*dl*dl);float w=spatial*edge;sum+=w*(n-vec3(ny));wsum+=w;}}vec3 filtered=wsum>1e-6?sum/wsum:chroma;vec3 outRgb=vec3(y)+mix(chroma,filtered,clamp(strength,0.0,1.0));float outY=lum(outRgb);outRgb+=vec3(y-outY);Output=vec4(max(outRgb,vec3(0.0)),1.0);}
