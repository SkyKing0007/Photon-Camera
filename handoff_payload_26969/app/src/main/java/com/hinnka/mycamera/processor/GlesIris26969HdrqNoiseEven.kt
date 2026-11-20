package com.hinnka.mycamera.processor

/**
 * IRIS_26969_HDRQ_B_OFF_NEIGHBOUR_GRAIN_EVENING.
 * The Rexture merge's effective-frame map is NOT an HDR+ Quality map. We do not
 * borrow it or invent per-pixel HDRQ frame counts. Instead this source-domain
 * 1/8-resolution texture measures actual output grain by neighbouring camera-
 * linear green and R-G/B-G variance after the four-pass HDRQ merge + AMaZE.
 * The temporary texture is only ~1/64 of a full RGBA image. The consumer is
 * B Super Res OFF only, prior to WB/Lab/SDR/UHDR; A, B ON, Night and Spektra
 * never use it. Adapts the noise-equalisation PRINCIPLE of RAWR Rexture #132,
 * not Rexture's confidence semantics or shader implementation.
 */
internal object GlesIris26969HdrqNoiseEven {
    val measure = """#version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uIris26969CameraLinear;
        uniform ivec2 uIris26969Size;
        layout(location=0) out vec4 oVariance;
        vec3 lc(ivec2 p) {
            vec3 v=max(texelFetch(uIris26969CameraLinear,
                clamp(p,ivec2(0),uIris26969Size-1),0).rgb,vec3(0.0));
            return vec3(v.g,v.r-v.g,v.b-v.g);
        }
        void main() {
            ivec2 base=ivec2(gl_FragCoord.xy)*8;
            vec3 mean=vec3(0.0);
            for(int y=0;y<4;y++) for(int x=0;x<4;x++)
                mean+=lc(base+ivec2(x*2+1,y*2+1));
            mean*=0.0625;
            vec3 v=vec3(0.0);
            for(int y=0;y<4;y++) for(int x=0;x<4;x++) {
                vec3 d=lc(base+ivec2(x*2+1,y*2+1))-mean;
                v+=d*d;
            }
            // Alpha is the actual local green mean, used for a brightness-
            // compatible reference. No zero-noise claim about flat textures.
            oVariance=vec4(max(v*0.0625,vec3(0.0)),mean.x);
        }
    """.trimIndent()
}
