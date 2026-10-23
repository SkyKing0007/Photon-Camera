precision highp float;
precision highp sampler2D;
uniform sampler2D InputBuffer;
uniform float cleanupStrength;
uniform float presentationGain;
out vec3 Output;

const vec3 YW=vec3(0.22897456,0.69173852,0.07928691);
float lum(vec3 a){return dot(max(a,vec3(0.0)),YW);}
vec2 chroma(vec3 a,float y){
    return vec2(a.r-y,a.b-y)/max(0.045,y);
}
vec3 at(ivec2 p,ivec2 wh){
    return max(texelFetch(InputBuffer,clamp(p,ivec2(0),wh-1),0).rgb,vec3(0.0));
}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    ivec2 wh=textureSize(InputBuffer,0);
    vec3 original=at(p,wh);
    float y=lum(original);
    float visibleY=y*max(presentationGain,1.0e-4);
    if(cleanupStrength<=0.0001||y<0.006){Output=original;return;}
    vec2 c=chroma(original,y);
    // Protect coherent weak structure in BOTH luminance and chroma.
    float structure=0.0;
    for(int dy=-1;dy<=1;dy++) for(int dx=-1;dx<=1;dx++) {
        if(dx==0&&dy==0)continue;
        vec3 n=at(p+ivec2(dx,dy),wh);
        float yn=lum(n);
        vec2 cn=chroma(n,yn);
        structure=max(structure,abs(y-yn)/max(0.035,y));
        structure=max(structure,length(c-cn)*0.28);
    }
    float protect=1.0-smoothstep(0.055,0.16,structure);
    // Same-material, bounded chroma-only consensus on separated taps.
    // 16 outer samples target broad mottling rather than weave-frequency
    // variations, while rejecting both luminance and chroma boundaries.
    const ivec2 dirs[8]=ivec2[8](ivec2(1,0),ivec2(-1,0),
        ivec2(0,1),ivec2(0,-1),ivec2(1,1),ivec2(-1,1),
        ivec2(1,-1),ivec2(-1,-1));
    vec2 acc=vec2(0.0);
    float weight=0.0;
    for(int ring=0;ring<2;ring++) {
        int stepSize=ring==0?4:12;
        for(int j=0;j<8;j++){
            vec3 n=at(p+dirs[j]*stepSize,wh);
            float yn=lum(n);
            vec2 cn=chroma(n,yn);
            float lightAgreement=1.0-smoothstep(0.02,0.12,
                abs(y-yn)/max(0.065,y));
            float hueAgreement=1.0-smoothstep(0.10,0.45,length(c-cn));
            float w=lightAgreement*hueAgreement;
            acc+=cn*w;weight+=w;
        }
    }
    // Flatness and cross-material guard; never 'black implies flat'.
    float support=smoothstep(5.0,10.0,weight);
    // Estimate eventual shadow visibility using the same final display-gain
    // authority as MotionV2Render; never infer texturelessness from darkness.
    float visible=smoothstep(0.004,0.025,visibleY);
    float fraction=0.24*clamp(cleanupStrength,0.0,1.0)*protect*support*visible;
    vec2 updated=mix(c,acc/max(weight,1.0e-5),fraction);
    float rr=y+updated.x*max(0.045,y);
    float bb=y+updated.y*max(0.045,y);
    float gg=(y-YW.r*rr-YW.b*bb)/YW.g;
    vec3 corrected=max(vec3(rr,gg,bb),vec3(0.0));
    // Preserve luminance despite numerical bounds, avoid white clipping.
    corrected*=y/max(lum(corrected),1.0e-5);
    Output=max(corrected,vec3(0.0));
}
