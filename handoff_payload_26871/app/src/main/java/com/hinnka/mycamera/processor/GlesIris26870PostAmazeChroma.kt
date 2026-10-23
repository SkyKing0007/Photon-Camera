package com.hinnka.mycamera.processor

/** IRIS_26870_B_NATIVE_POST_AMAZE_CHROMA.
 * Sensor-neutral linear camera RGB; AFTER native physical LSC+AMaZE, BEFORE
 * temporary WB / highlight / Lab / FCC. Corrects chroma only, never luminance.
 * Small-texture, hue and edge confidence vetoes protect coherent material.
 * IRIS_26871_B_MULTISCALE_CHROMA: far-ring comparisons suppress broad
 * incoherent low-light color mottling; no second filter or added full-frame buffer.
 * This shader FUSES the already-present temporary WB pass and creates NO
 * extra full-frame RGBA16F intermediate (crucial for 2x output GPU memory).
 * The future-tone visibility budget is conservative and local-luminance aware;
 * it is NOT a fake replacement for RAWR's native RAW burst noise estimator.
 */
internal object GlesIris26870PostAmazeChroma {
    val shader="""#version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uSensorNeutralAmazeRgb;
        uniform ivec2 uSize;
        uniform float uReferenceProtectionEv;
        uniform vec3 uAmazeWb;
        layout(location=0) out vec4 oPostWbCameraRgb;
        const vec3 kY=vec3(0.25,0.50,0.25);
        float yy(vec3 x){return dot(max(x,vec3(0.0)),kY);}
        vec3 src(ivec2 p){
          return max(texelFetch(uSensorNeutralAmazeRgb,clamp(p,ivec2(0),uSize-1),0).rgb,vec3(0.0));
        }
        vec2 chr(vec3 rgb,float y){return vec2(rgb.r-rgb.g,rgb.b-rgb.g)/max(y,0.035);}
        void main(){
          ivec2 p=ivec2(gl_FragCoord.xy);
          vec4 raw=texelFetch(uSensorNeutralAmazeRgb,p,0);
          vec3 c=max(raw.rgb,vec3(0.0));
          float y=yy(c);
          if(y<0.003 || y>0.90){oPostWbCameraRgb=vec4(raw.rgb*uAmazeWb,raw.a);return;}
          float structure=0.0;
          for(int d=0;d<4;d++){
            ivec2 q=p+(d==0?ivec2(1,0):d==1?ivec2(-1,0):d==2?ivec2(0,1):ivec2(0,-1));
            vec3 n=src(q);
            structure=max(structure,abs(yy(n)-y)/max(y,0.035));
          }
          float protectedStructure=1.0-smoothstep(0.04,0.14,structure);
          if(protectedStructure<=0.0){oPostWbCameraRgb=vec4(raw.rgb*uAmazeWb,raw.a);return;}
          vec2 center=chr(c,y),acc=vec2(0.0);
          float sum=0.0;
          for(int ring=0;ring<4;ring++){
            int radius=ring==0?4:ring==1?11:ring==2?32:72;
            float ringWeight=ring<2?1.0:0.65;
            for(int d=0;d<8;d++){
              ivec2 off=ivec2((d==0||d==4||d==5)?radius:((d==1||d==6||d==7)?-radius:0),
                               (d==2||d==4||d==6)?radius:((d==3||d==5||d==7)?-radius:0));
              vec3 n=src(p+off);
              float ny=yy(n);
              vec2 nc=chr(n,ny);
              float material=(1.0-smoothstep(0.02,0.11,abs(ny-y)/max(y,0.07)))
                           *(1.0-smoothstep(0.12,0.44,length(nc-center)));
              acc+=nc*(material*ringWeight);sum+=material*ringWeight;
            }
          }
          float agree=smoothstep(7.0,15.0,sum);
          if(agree<=0.0){oPostWbCameraRgb=vec4(raw.rgb*uAmazeWb,raw.a);return;}
          vec2 consensus=acc/max(sum,1.0e-5);
          float unsupported=length(center-consensus);
          float outlier=smoothstep(0.025,0.16,unsupported);
          float genuineHueProtect=1.0-smoothstep(0.28,0.56,length(center));
          // Anticipate exposure/tone lifting in each local signal region.
          // This is a bounded presentation budget, not a second exposure owner.
          float expectedShadowGain=exp2(clamp(uReferenceProtectionEv,0.0,1.5))
                                  *(1.0+2.0*(1.0-smoothstep(0.025,0.22,y)));
          float visible=smoothstep(0.006,0.045,y*expectedShadowGain);
          float amount=0.46*agree*protectedStructure*outlier*genuineHueProtect*visible;
          vec2 filteredChroma=mix(center,consensus,clamp(amount,0.0,0.46));
          float span=max(y,0.035);
          float g=y-0.25*(filteredChroma.x+filteredChroma.y)*span;
          vec3 rgb=vec3(g+filteredChroma.x*span,g,g+filteredChroma.y*span);
          if(min(rgb.r,min(rgb.g,rgb.b))<0.0){oPostWbCameraRgb=vec4(raw.rgb*uAmazeWb,raw.a);return;}
          // Preserve the original sensor-linear luminance and HDR headroom.
          oPostWbCameraRgb=vec4(rgb*uAmazeWb,raw.a);
        }
    """.trimIndent()
}
