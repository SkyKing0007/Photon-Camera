precision highp float;
precision highp sampler2D;
uniform sampler2D InputBuffer;
uniform sampler2D ExposureMip;
uniform sampler2D FusedMip;
uniform float exposure;
out vec4 Output;

vec3 RRTAndODTFit(vec3 v){vec3 a=v*(v+0.0245786)-0.000090537;vec3 b=v*(0.983729*v+0.4329510)+0.238081;return a/b;}
vec3 ACESFilmicToneMapping(vec3 color){
    const mat3 ACESInputMat=mat3(vec3(0.59719,0.07600,0.02840),vec3(0.35458,0.90834,0.13383),vec3(0.04823,0.01566,0.83777));
    const mat3 ACESOutputMat=mat3(vec3(1.60475,-0.10208,-0.00327),vec3(-0.53108,1.10813,-0.07276),vec3(-0.07367,-0.00605,1.07602));
    color*=1.0/0.6;color=ACESInputMat*color;color=RRTAndODTFit(color);color=ACESOutputMat*color;return clamp(color,vec3(0.0),vec3(1.0));
}
vec3 p3ToSrgbLinear(vec3 c){return vec3(1.22494018*c.r-0.22494018*c.g,-0.04205695*c.r+1.04205695*c.g,-0.01963755*c.r-0.07863605*c.g+1.09827360*c.b);}
vec3 srgbToP3Linear(vec3 c){return vec3(0.8224619687*c.r+0.1775380313*c.g,0.0331941989*c.r+0.9668058011*c.g,0.0170826307*c.r+0.0723974407*c.g+0.9105199286*c.b);}
float srgbDecode(float x){x=clamp(x,0.0,1.0);return x<=0.04045?x/12.92:pow((x+0.055)/1.055,2.4);}
vec3 srgbDecode(vec3 c){return vec3(srgbDecode(c.r),srgbDecode(c.g),srgbDecode(c.b));}
float srgbEncode(float x){x=max(x,0.0);return x<=0.0031308?12.92*x:1.055*pow(x,1.0/2.4)-0.055;}
vec3 srgbEncode(vec3 c){return vec3(srgbEncode(c.r),srgbEncode(c.g),srgbEncode(c.b));}
float physicalLuma(vec3 c){return dot(max(c,vec3(0.0)),vec3(0.22897456,0.69173852,0.07928691));}
float peak3(vec3 c){return max(c.r,max(c.g,c.b));}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);ivec2 sourceSize=textureSize(InputBuffer,0);vec2 uv=gl_FragCoord.xy/vec2(sourceSize);
    ivec2 mipSize=textureSize(ExposureMip,0);vec2 px=1.0/vec2(mipSize);
    float momentX=0.0,momentY=0.0,momentX2=0.0,momentXY=0.0,ws=0.0;
    for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){
        vec2 q=uv+vec2(float(dx),float(dy))*px;float x=texture(ExposureMip,q).y;float y=texture(FusedMip,q).x;
        float w=exp(-0.5*float(dx*dx+dy*dy)/(0.7*0.7));momentX+=x*w;momentY+=y*w;momentX2+=x*x*w;momentXY+=x*y*w;ws+=w;
    }
    momentX/=ws;momentY/=ws;momentX2/=ws;momentXY/=ws;float A=(momentXY-momentX*momentY)/(max(momentX2-momentX*momentX,0.0)+0.00001);float B=momentY-A*momentX;
    vec4 src=texelFetch(InputBuffer,p,0);vec3 sourceP3=max(src.rgb,vec3(0.0));vec3 sourceSrgb=p3ToSrgbLinear(sourceP3);
    vec3 texelOriginal=sqrt(max(ACESFilmicToneMapping(sourceSrgb*exposure),vec3(0.0)));float luminance=dot(texelOriginal,vec3(0.1,0.7,0.2))+0.00001;
    float finalMultiplier=max(A*luminance+B,0.0)/luminance;const float threshold=0.007;
    if(luminance<=threshold){float t=luminance/threshold;finalMultiplier=mix(1.0,finalMultiplier,t*t);}
    /* Exact linked-demo output code value. Convert its colorimetrically interpreted sRGB display
     * result to standard encoded Display-P3; this is a gamut/encoding adapter only. */
    vec3 demoCode=sqrt(max(ACESFilmicToneMapping(sourceSrgb*exposure*finalMultiplier),vec3(0.0)));
    vec3 displayLinearSrgb=srgbDecode(demoCode);vec3 displayLinearP3=max(srgbToP3Linear(displayLinearSrgb),vec3(0.0));vec3 encodedP3=clamp(srgbEncode(displayLinearP3),vec3(0.0),vec3(1.0));
    /* Physical guide was frozen before adaptive color appearance.  Wronski owns SDR appearance
     * only; it must not manufacture UHDR headroom from post-appearance RGB. */
    float physicalGuide=max(src.a,0.0);Output=vec4(encodedP3,physicalGuide);
}
