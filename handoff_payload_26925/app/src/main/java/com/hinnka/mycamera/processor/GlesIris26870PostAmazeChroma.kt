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
        // Only true native Wronski 2x, never B OFF or A/Sabre.
        uniform int uIris26922SrOn;
        // IRIS_26925: per-pixel conservative effective original RAW support
        // is carried by the native Wronski/AMaZE RGB alpha. This is not a
        // total-frame-count or spatially guessed uncertainty map.
        uniform int uIris26925SupportPresent;
        uniform float uIris26925OriginalFrames;
        uniform vec3 uIris26925ShotByRgb;
        uniform vec3 uIris26925ReadByRgb;
        uniform vec3 uAmazeWb;
        // 26924: original sensor-CFA clip provenance. Native B only;
        // the 1x clip map must match this RGB domain exactly.
        uniform sampler2D uIris26924SensorClip;
        uniform int uIris26924ClipPresent;
        uniform int uIris26924BOff;
        layout(location=0) out vec4 oPostWbCameraRgb;
        const vec3 kY=vec3(0.25,0.50,0.25);
        float yy(vec3 x){return dot(max(x,vec3(0.0)),kY);}
        vec3 src(ivec2 p){
          return max(texelFetch(uSensorNeutralAmazeRgb,clamp(p,ivec2(0),uSize-1),0).rgb,vec3(0.0));
        }
        vec2 chr(vec3 rgb,float y){return vec2(rgb.r-rgb.g,rgb.b-rgb.g)/max(y,0.035);}
        bool rawClipped(ivec2 p) {
          if (uIris26924ClipPresent==0) return false;
          return texelFetch(uIris26924SensorClip,clamp(p,ivec2(0),uSize-1),0).r>0.5;
        }
        // A Bayer clip bit belongs to a physical CFA site, not a guessed RGB
        // hue. Disallow hue borrowing in the contaminated 3x3 neighborhood.
        bool untrustedClipNeighborhood(ivec2 p) {
          if (uIris26924ClipPresent==0) return false;
          for(int j=-1;j<=1;++j) for(int i=-1;i<=1;++i)
            if(rawClipped(p+ivec2(i,j))) return true;
          return false;
        }
        // A matching endpoint does not establish same material. Sample the
        // whole donor path, stopping at any luminance discontinuity, clipping,
        // or chromaticity jump. This is local B-only correction, not a global
        // color-matrix, tone, or Wronski change.
        bool connectedMaterial(ivec2 p, ivec2 off, float centerY, vec2 centerC) {
          int n=max(1,(max(abs(off.x),abs(off.y))+3)/4);
          for(int k=1;k<=18;++k) {
            if(k>n) break;
            ivec2 q=p+ivec2(round(vec2(off)*(float(k)/float(n))));
            // Origin already checked in a 3x3 clipped neighborhood.
            // Test each bridge site's original clipping bit directly rather
            // than reading 9 neighbors at every 4-pixel bridge point.
            if(rawClipped(q)) return false;
            vec3 rgb=src(q);float y=yy(rgb);
            if(abs(y-centerY)/max(centerY,0.075)>0.09) return false;
            if(length(chr(rgb,y)-centerC)>0.21) return false;
          }
          return true;
        }
        // Original RAWR Highlight Reconstruction OFF, not its ON guide/repair:
        // the camera-linear RGB is already normalized to sensor-white. Apply
        // temporary WB once, then cap ALL three post-WB channels by the SAME
        // minimum WB-channel ceiling before Lab defringe and FCC. No masks,
        // hue guessing, neighbor propagation, painted-white target or late pass.
        vec3 rawrHighlightOff(vec3 sensorNeutralRgb){
          vec3 postWb=max(sensorNeutralRgb*uAmazeWb,vec3(0.0));
          float commonCeiling=min(uAmazeWb.r,min(uAmazeWb.g,uAmazeWb.b));
          return min(postWb,vec3(commonCeiling));
        }
        void main(){
          ivec2 p=ivec2(gl_FragCoord.xy);
          vec4 raw=texelFetch(uSensorNeutralAmazeRgb,p,0);
          vec3 c=max(raw.rgb,vec3(0.0));
          float y=yy(c);
          if(y<0.003 || y>0.90 ||
             (uIris26924BOff!=0 && untrustedClipNeighborhood(p))) {
            oPostWbCameraRgb=vec4(rawrHighlightOff(raw.rgb),raw.a);return;
          }
          float structure=0.0;
          for(int d=0;d<4;d++){
            ivec2 q=p+(d==0?ivec2(1,0):d==1?ivec2(-1,0):d==2?ivec2(0,1):ivec2(0,-1));
            vec3 n=src(q);
            structure=max(structure,abs(yy(n)-y)/max(y,0.035));
          }
          float protectedStructure=1.0-smoothstep(0.04,0.14,structure);
          if(protectedStructure<=0.0){oPostWbCameraRgb=vec4(rawrHighlightOff(raw.rgb),raw.a);return;}
          vec2 center=chr(c,y),acc=vec2(0.0);
          float sum=0.0;
          for(int ring=0;ring<4;ring++){
            // Wide-ring endpoint matches are not proof of connected material.
            // B OFF restricts donors to 4/11px, with intermediate checks.
            if(uIris26924BOff!=0 && ring>=2) continue;
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
              // IRIS_26881_B_TOPOLOGY_PATH_GUARD:
              // 26871's 32/72 px rings could cross an unrelated edge even
              // when both endpoints had similar luminance/chroma. Demand a
              // same-material midpoint for wide-ring consensus, without
              // weakening 26871's long-range flat-region blotch suppression.
              if(uIris26924BOff!=0 && material>0.005 &&
                 !connectedMaterial(p,off,y,center)) material=0.0;
              if(ring>=2 && material>0.005){
                ivec2 mid=p+off/2;
                vec3 bridge=src(mid);
                float bridgeY=yy(bridge);
                vec2 bridgeChroma=chr(bridge,bridgeY);
                float bridgeLum=1.0-smoothstep(0.018,0.080,
                                    abs(bridgeY-y)/max(y,0.07));
                float bridgeHue=1.0-smoothstep(0.09,0.28,
                                    length(bridgeChroma-center));
                material*=bridgeLum*bridgeHue;
              }
              acc+=nc*(material*ringWeight);sum+=material*ringWeight;
            }
          }
          float agree=smoothstep(7.0,15.0,sum);
          bool srOn26925=(uIris26922SrOn!=0 && uIris26925SupportPresent!=0);
          if(agree<=0.0 && !srOn26925){
            oPostWbCameraRgb=vec4(rawrHighlightOff(raw.rgb),raw.a);return;
          }
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
          // IRIS_26925_B_ON_PHYSICAL_NOISE_AND_TEMPORAL_SUPPORT.
          // The native 2x Wronski result carries effective ORIGINAL RAW
          // per-channel support min as FP16 alpha, computed once after the
          // ninth U(z)-y update, from per-color sumW^2/sumW2.  No /15 guess.
          vec2 filteredChroma=mix(center,consensus,clamp(amount,0.0,0.56));
          if(srOn26925 && y<0.40 && protectedStructure>0.0){
            float neff=clamp(raw.a,0.0,uIris26925OriginalFrames);
            float denom=max(neff,1.0);
            vec3 physicalVariance=(uIris26925ShotByRgb*max(y,0.0)+
                                   uIris26925ReadByRgb)/denom;
            float sigmaFloor=sqrt(max(max(physicalVariance.r,
                               physicalVariance.g),physicalVariance.b));
            // RAW variance is in sensor-linear codes. Our chroma is
            // normalized by source signal, with a conservative green-site
            // floor and no white-balance-dependent magic constants.
            float sigmaRelative=sigmaFloor/max(y,0.055);
            // Neighbor consent is INDEPENDENT of the candidate's suspicious
            // hue. A center-color gate would preserve an isolated purple or
            // cyan speckle by rejecting all perfectly neutral neighbors.
            vec2 localSum=vec2(0.0);
            float localSum2=0.0,localWeight=0.0;
            for(int d=0;d<8;++d){
              ivec2 o=ivec2((d==0||d==4||d==5)?1:((d==1||d==6||d==7)?-1:0),
                            (d==2||d==4||d==6)?1:((d==3||d==5||d==7)?-1:0));
              ivec2 qq=clamp(p+o,ivec2(0),uSize-1);
              vec4 v=texelFetch(uSensorNeutralAmazeRgb,qq,0);
              float vy=yy(v.rgb);
              float lumGap=abs(vy-y)/max(y,0.055);
              float same=1.0-smoothstep(0.045,0.14,lumGap);
              // An unreliable low-support donor has bounded influence.
              float donorSupport=clamp(v.a,0.0,uIris26925OriginalFrames);
              float reliable=0.20+0.80*sqrt(donorSupport/
                                      max(uIris26925OriginalFrames,1.0));
              float w=same*reliable;
              vec2 cc=chr(max(v.rgb,vec3(0.0)),vy);
              localSum+=w*cc;
              localSum2+=w*dot(cc,cc);
              localWeight+=w;
            }
            if(localWeight>=1.0){
              vec2 localMean=localSum/localWeight;
              float dispersion=sqrt(max(localSum2/localWeight-
                                   dot(localMean,localMean),0.0));
              float outlier=length(center-localMean);
              // Require a coherent neighborhood and an outlier larger than
              // the locally calibrated burst uncertainty. This is a bounded
              // CHROMA-only update; luminance is reconstructed unchanged.
              float coherent=1.0-smoothstep(0.08,0.24,dispersion);
              float outlierConfidence=smoothstep(0.70,2.5,
                            outlier/max(0.70*sigmaRelative,0.008));
              float supportPenalty=1.0-smoothstep(3.0,
                                 max(7.0,uIris26925OriginalFrames*0.85),neff);
              float strength=clamp((0.20+0.46*supportPenalty)*
                  coherent*outlierConfidence*protectedStructure*
                  (1.0-smoothstep(0.24,0.40,y)),0.0,0.66);
              filteredChroma=mix(filteredChroma,localMean,strength);
            }
          }
          float span=max(y,0.035);
          float g=y-0.25*(filteredChroma.x+filteredChroma.y)*span;
          vec3 rgb=vec3(g+filteredChroma.x*span,g,g+filteredChroma.y*span);
          if(min(rgb.r,min(rgb.g,rgb.b))<0.0){oPostWbCameraRgb=vec4(rawrHighlightOff(raw.rgb),raw.a);return;}
          // Preserve the original sensor-linear luminance and HDR headroom.
          oPostWbCameraRgb=vec4(rawrHighlightOff(rgb),raw.a);
        }
    """.trimIndent()
}
