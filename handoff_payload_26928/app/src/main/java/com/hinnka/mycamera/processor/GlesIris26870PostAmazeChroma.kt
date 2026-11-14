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
        uniform float uIris26922ShotVariance;
        uniform float uIris26922ReadVariance;
        // IRIS_26926_B_ON_4_SITE_BURST_CONFIDENCE_TRANSFER. The true Wronski
        // temporal/phase support has been transported in source texture alpha,
        // including through the original RAWR native chroma wavelet copy.
        uniform float uIris26926BurstFrames;
        uniform vec3 uIris26926ShotByRgb;
        uniform vec3 uIris26926ReadByRgb;
        uniform sampler2D uIris26926LensShading;
        uniform int uIris26926LensShadingPresent;
        uniform ivec2 uIris26926RawSize;
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
        float originalRawSupport(ivec2 q){
          if(uIris26922SrOn==0)return 1.0;
          return clamp(texelFetch(uSensorNeutralAmazeRgb,
              clamp(q,ivec2(0),uSize-1),0).a,0.0,1.0);
        }
        // Original normalized sensor RAW variance: v=a*y+b. Native physical
        // LSC changes it by g^2: v_post=g*a*y_post + g*g*b, NOT a*y_post+b.
        // AMaZE introduces cross-channel covariance; use an intentionally
        // conservative pixelwise approximate scalar, NEVER advertise exact
        // demosaic variance or divide by the nominal 15 accepted frames.
        float burstFloor(ivec2 p,vec3 rgb,float y,float rawSupport){
          vec3 gain=vec3(1.0);
          if(uIris26926LensShadingPresent!=0){
            vec2 uv=(vec2(p)+vec2(0.5))/
                max(vec2(uIris26926RawSize)*2.0,vec2(1.0));
            vec4 perCfa=texture(uIris26926LensShading,clamp(uv,vec2(0.0),vec2(1.0)));
            gain=vec3(perCfa.r,0.5*(perCfa.g+perCfa.b),perCfa.a);
            gain=clamp(gain,vec3(0.25),vec3(32.0));
          }
          vec3 shot=max(uIris26926ShotByRgb,vec3(0.0));
          vec3 read=max(uIris26926ReadByRgb,vec3(0.0));
          vec3 varRgb=shot*max(rgb,vec3(0.0))*gain+read*gain*gain;
          // Support is the original Wronski confidence from measured Bayer
          // coverage+Neff, not Neff itself. Map conservatively between a
          // single noisy frame and the nominal burst as a noise lower bound.
          float validFrames=mix(1.0,max(uIris26926BurstFrames,1.0),
              clamp(rawSupport,0.0,1.0));
          float variance=max(dot(varRgb,vec3(0.25,0.50,0.25)),0.0)/validFrames;
          return sqrt(variance)/max(y,0.055);
        }
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
        // IRIS_26928_B_OFF_SOURCE_DOMAIN_MATERIAL_CHROMA.
        // The old 26927 edge repair only ran when local luminance structure
        // exceeded 0.14, required 4 of 8 donors at distance 3 with extremely
        // small variance, and vetoed moderately strong false chroma. The
        // ordinary 4/11-pixel rings meanwhile REQUIRED a donor to resemble
        // the *contaminated center hue*. Both conditions can preserve false
        // chroma that is already spatially connected in HDRq/AMaZE output.
        //
        // The correction below applies ONLY to the B OFF PRE-WB camera-linear
        // image. It gathers independent same-luminance, unclipped witnesses
        // on the 6-pixel same-side rays; each entire ray is checked, so a
        // bright/dark boundary cannot supply chroma from the other object.
        // Donor consensus is measured WITHOUT weighting it by the target
        // chroma: an artifact must not self-authorize its own hue. Two robust
        // agreement passes reject dispersed or two-material colors. Direct
        // near-neighbor support protects genuine tiny coherent color edges.
        // No neutral target, tone, global blur, new texture, or extra draw.
        vec3 bOffMaterialOutlier(ivec2 p,vec3 c,float y,float structure){
          if(uIris26924BOff==0 || rawClipped(p) || y<0.003 || y>0.82)
            return c;
          vec2 center=chr(c,y);
          float saturation=length(center);
          // Do not erase strong genuine red/blue/green tiny structure.
          if(saturation<0.055 || saturation>0.54)return c;
          float peers=0.0;
          for(int d=0;d<8;++d){
            ivec2 o=ivec2((d==0||d==4||d==5)?1:((d==1||d==6||d==7)?-1:0),
                          (d==2||d==4||d==6)?1:((d==3||d==5||d==7)?-1:0));
            ivec2 q=p+o;
            if(rawClipped(q))continue;
            vec3 v=src(q);float vy=yy(v);
            if(abs(vy-y)/max(max(y,vy),0.055)>0.12)continue;
            if(length(chr(v,vy)-center)<0.060)peers+=1.0;
          }
          // A real colored interface or coherent narrow color structure may
          // be the ONLY reliable source of its own hue. Preserve it even if
          // a distant same-brightness area has a different material color.
          if(saturation>0.14 && peers>=3.0)return c;
          if(saturation>0.20 && peers>=2.0)return c;
          if(structure>0.28 && peers>=2.0)return c;
          vec2 donor[8];bool valid[8];
          vec2 total=vec2(0.0);float n=0.0;
          for(int d=0;d<8;++d){
            ivec2 ray=ivec2((d==0||d==4||d==5)?1:((d==1||d==6||d==7)?-1:0),
                            (d==2||d==4||d==6)?1:((d==3||d==5||d==7)?-1:0));
            bool same=true;
            for(int k=1;k<=6;++k){
              ivec2 q=p+k*ray;
              if(rawClipped(q)){same=false;break;}
              vec3 v=src(q);float vy=yy(v);
              // The comparison is to the original center brightness, not an
              // average that could walk gradually across a real boundary.
              if(abs(vy-y)/max(max(y,vy),0.055)>0.095){same=false;break;}
            }
            vec2 candidate=vec2(0.0);
            if(same){
              vec3 far=src(p+6*ray);candidate=chr(far,yy(far));
              // A saturated endpoint is never treated as the correct color
              // of a different object simply because its luminance matches.
              if(length(candidate)>0.60)same=false;
            }
            valid[d]=same;donor[d]=candidate;
            if(same){total+=candidate;n+=1.0;}
          }
          if(n<4.0)return c;
          vec2 initial=total/n;
          // Reject a split across two genuine colors of similar luminance
          // BEFORE robust trimming. Otherwise one 3-vs-5 donor material
          // cluster could be discarded as outliers and the majority material
          // could repaint the other object's true color. Ordinary isolated
          // noisy witnesses can still be rejected by the later robust pass.
          float firstScatter=0.0;float displaced=0.0;
          for(int d=0;d<8;++d){
            if(valid[d]){
              float delta=length(donor[d]-initial);
              firstScatter+=delta*delta;
              if(delta>=0.13)displaced+=1.0;
            }
          }
          firstScatter=sqrt(max(firstScatter/n,0.0));
          if(displaced>=2.0 || firstScatter>0.092)return c;
          // Reject divided-material or scattered false-color donors rather
          // than pulling the pixel toward an average of conflicting colors.
          vec2 clean=vec2(0.0);float cleanN=0.0;
          for(int d=0;d<8;++d){
            if(valid[d] && length(donor[d]-initial)<0.13){
              clean+=donor[d];cleanN+=1.0;
            }
          }
          if(cleanN<4.0)return c;
          vec2 consensus=clean/cleanN;
          float scatter=0.0;
          for(int d=0;d<8;++d){
            if(valid[d] && length(donor[d]-initial)<0.13)
              scatter+=dot(donor[d]-consensus,donor[d]-consensus);
          }
          scatter=sqrt(max(scatter/cleanN,0.0));
          if(scatter>0.085)return c;
          float difference=length(center-consensus);
          if(difference<0.060)return c;
          // A same-luminance color boundary is not proof that a source hue
          // is wrong. Moderate agreement with immediate material survives.
          if(peers>=2.0 && saturation>0.22 && structure>0.09)return c;
          float gain=0.57*smoothstep(0.060,0.21,difference)*
                     (1.0-smoothstep(0.28,0.54,saturation))*
                     (1.0-smoothstep(0.045,0.085,scatter));
          gain*=1.0-0.48*smoothstep(0.0,3.0,peers);
          vec2 corrected=mix(center,consensus,clamp(gain,0.0,0.57));
          float span=max(y,0.035);
          float g=y-0.25*(corrected.x+corrected.y)*span;
          vec3 candidate=vec3(g+corrected.x*span,g,g+corrected.y*span);
          return min(candidate.r,min(candidate.g,candidate.b))>=0.0?candidate:c;
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
          float sourceSupport=originalRawSupport(p);
          if(y<0.003 || y>0.90 ||
             (uIris26924BOff!=0 && rawClipped(p))) {
            oPostWbCameraRgb=vec4(rawrHighlightOff(raw.rgb),raw.a);return;
          }
          float structure=0.0;
          for(int d=0;d<4;d++){
            ivec2 q=p+(d==0?ivec2(1,0):d==1?ivec2(-1,0):d==2?ivec2(0,1):ivec2(0,-1));
            vec3 n=src(q);
            structure=max(structure,abs(yy(n)-y)/max(y,0.035));
          }
          float protectedStructure=1.0-smoothstep(0.04,0.14,structure);
          // 26928: Evaluate robust same-material evidence before the old
          // edge veto. Otherwise its exit would preserve the contaminated
          // chroma without ever evaluating trustworthy same-side witnesses.
          // B ON and all non-native-B routes are exact no-ops here.
          if(uIris26924BOff!=0){
            vec3 repaired=bOffMaterialOutlier(p,c,y,structure);
            if(length(repaired-c)>0.000001){
              oPostWbCameraRgb=vec4(rawrHighlightOff(repaired),raw.a);return;
            }
          }
          if(protectedStructure<=0.0){
            oPostWbCameraRgb=vec4(rawrHighlightOff(raw.rgb),raw.a);return;
          }
          // The native sensor mask blocks borrowing *from* clipped pixels;
          // it must not blanket-veto correction of an otherwise valid dark
          // background pixel located next to a clipped lamp.
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
              // A nearby pixel's similar hue does not make it a trustworthy
              // donor if the same original RAW phase coverage was rejected.
              // Weak donors remain possible for flat material; do not erase
              // genuine color just because every part of a shadow is noisy.
              if(uIris26922SrOn!=0)
                material*=mix(0.35,1.0,originalRawSupport(p+off));
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
          if(agree<=0.0){oPostWbCameraRgb=vec4(rawrHighlightOff(raw.rgb),raw.a);return;}
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
          // The ORIGINAL burst must veto unnecessary chroma attenuation on
          // temporally well-supported genuine fine-color material.
          if(uIris26922SrOn!=0){
            float confident=smoothstep(0.36,0.88,sourceSupport);
            amount*=mix(1.0,0.16,confident);
          }
          // IRIS_26922_SR_ON_UNCERTAINTY_AWARE_CHROMA: estimate actual local
          // residual variance on the Wronski 2x result, backed by the frozen
          // NORMAL reference sensor shot/read floor. No false-detail masks,
          // per-channel sharpening, RAW fusion change, or new full-res buffer.
          // Spatial confidence is distinct from mere agreement with a nearby
          // noisy pixel: genuine textured/luma edges veto additional filtering.
          if(uIris26922SrOn!=0 && y<0.24 && protectedStructure>0.0){
            float localEnergy=0.0,localWeight=0.0;
            vec2 shortMean=vec2(0.0);
            float shortWeight=0.0;
            for(int d=0;d<8;d++){
              ivec2 o=ivec2((d==0||d==4||d==5)?3:((d==1||d==6||d==7)?-3:0),
                            (d==2||d==4||d==6)?3:((d==3||d==5||d==7)?-3:0));
              vec3 v=src(p+o);
              float vy=yy(v);
              float same=1.0-smoothstep(0.025,0.13,abs(vy-y)/max(y,0.055));
              vec2 vc=chr(v,vy);
              shortMean+=same*vc;shortWeight+=same;
              localEnergy+=same*dot(vc-center,vc-center);localWeight+=same;
            }
            float spread=localEnergy/max(localWeight,1.0);
            float localSigma=sqrt(max(spread,0.0));
            // The RAW floor is in normalized sensor signal units. Convert to
            // this shader's bounded relative chroma space without pretending
            // it is the native burst estimator's exact effective variance.
            float sigmaFloor=burstFloor(p,c,y,sourceSupport);
            float uncertainty=max(localSigma,sigmaFloor);
            float chromaStrength=length(center);
            float weakChroma=1.0-smoothstep(0.11,0.34,chromaStrength);
            float uncertain=smoothstep(0.030,0.18,uncertainty);
            float shadow=1.0-smoothstep(0.025,0.24,y);
            // Low absolute RAW confidence AND coarse hue inconsistency are
            // required together. Purely spatial smoothing cannot claim a
            // moving shadow is temporally supported. No luma modification.
            float unreliable=1.0-smoothstep(0.27,0.83,sourceSupport);
            float extra=0.40*uncertain*shadow*weakChroma*unreliable*
                        protectedStructure*agree*visible*outlier;
            // Pull residual color toward a supported material consensus,
            // never toward arbitrary grey. Preserve sensor luma exactly.
            amount=max(amount,clamp(extra,0.0,0.40));
          }
          vec2 filteredChroma=mix(center,consensus,clamp(amount,0.0,0.56));
          float span=max(y,0.035);
          float g=y-0.25*(filteredChroma.x+filteredChroma.y)*span;
          vec3 rgb=vec3(g+filteredChroma.x*span,g,g+filteredChroma.y*span);
          if(min(rgb.r,min(rgb.g,rgb.b))<0.0){oPostWbCameraRgb=vec4(rawrHighlightOff(raw.rgb),raw.a);return;}
          // Preserve the original sensor-linear luminance and HDR headroom.
          oPostWbCameraRgb=vec4(rawrHighlightOff(rgb),raw.a);
        }
    """.trimIndent()
}
