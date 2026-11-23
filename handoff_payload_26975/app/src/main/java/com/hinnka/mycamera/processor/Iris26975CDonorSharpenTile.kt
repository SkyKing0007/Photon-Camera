package com.hinnka.mycamera.processor

import android.opengl.EGL14
import android.opengl.GLES30
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract
import java.nio.ByteBuffer

/**
 * C-owned native-grid bounded implementation of bjzhou's ACTIVE MGC
 * SharpenTo16Bit, not the older RawSharpenPass adaptive USM.
 * Reference source at 0a8a11defe7d932d8c8a729120a4d5f159e9d677:
 * GlesMgcSharpenShaders + GlesMgcSharpen + MgcSharpenCurveBuilder.
 *
 * The four original encoded-domain stages (BT.709 luma, binomial L1@d1,
 * L2@d2, L3@d4 + band curves + 5x5 gamut/overshoot clamp) use EXACTLY
 * the donor's arithmetic. Only image-space texture addressing changes:
 * each stage retains the minimal full-image-clamped input halo, then
 * discards it after a <=256x256 output tile. No image-wide 50MP R32F pyramid.
 * This reproduces the donor algorithm subject to GPU float roundoff; device
 * comparison remains necessary before claiming pixel equivalence.
 */
internal class Iris26975CDonorSharpenTile(
    private val color: Iris26972CColorDeveloper.Result,
) : AutoCloseable {
    private val gpu = Iris26972CDonorSabreGpuMerge
    private val owner = EGL14.eglGetCurrentContext()
    private val textures = IntArray(4)
    private val fbos = IntArray(4)
    private val programs = IntArray(4)
    private val curves = Iris26975CDonorMgcSharpenCurves.build(color.referenceSnr)
    // Donor: UI 0.40 maps to 1.0; ResolveSabre attenuation multiplies it.
    private val attenuation = Iris26975CDonorMgcSharpenCurves.strength(
        Iris26972CContract.SHARPENING) * color.sharpenAttenuation
    private val knots = FloatArray(12)
    private val values = FloatArray(12)
    private val slopes = FloatArray(12)
    private var vao = 0
    private var closed = false

    init {
        color.requireOwner()
        gpu.requireCurrentContext()
        check(owner != EGL14.EGL_NO_CONTEXT &&
            gpu.glInt(GLES30.GL_MAX_TEXTURE_SIZE) >= CORE + 2 * LUMA_HALO &&
            gpu.glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS) >= 4) {
            "C donor MGC sharpen GLES capability unavailable"
        }
        // Match GlesMgcSharpen.KernelUniforms exactly.
        for (band in 0..2) for (k in 0..3) {
            val index = 4 * band + k
            val x0 = curves[5 * band + k]
            val x1 = curves[5 * band + k + 1]
            val y0 = curves[15 + 5 * band + k]
            val y1 = curves[15 + 5 * band + k + 1]
            require(x1 > x0) { "C donor MGC sharpen knot ordering" }
            knots[index] = x0
            values[index] = y0
            slopes[index] = (y1 - y0) / (x1 - x0)
        }
        val oldState = Iris26972CDonorSabreGpuMerge.GlState.capture()
        var initialized = false
        try {
            programs[0] = gpu.compileProgram(VERTEX, LUMA)
            programs[1] = gpu.compileProgram(VERTEX, LEVEL1)
            programs[2] = gpu.compileProgram(VERTEX, LEVEL2)
            programs[3] = gpu.compileProgram(VERTEX, OUTPUT)
            GLES30.glGenTextures(4, textures, 0)
            GLES30.glGenFramebuffers(4, fbos, 0)
            val id = IntArray(1)
            GLES30.glGenVertexArrays(1, id, 0)
            vao = id[0]
            check(textures.all { it > 0 } && fbos.all { it > 0 } &&
                textures.toSet().size == 4 && fbos.toSet().size == 4 && vao > 0) {
                "C donor MGC sharpen scratch allocation failed"
            }
            for (index in 0..3) {
                val isOutput = index == 3
                val halo = when (index) {
                    0 -> LUMA_HALO
                    1 -> LEVEL1_HALO
                    2 -> LEVEL2_HALO
                    else -> 0
                }
                val format = if (isOutput) GLES30.GL_RGBA16F else GLES30.GL_R32F
                val pixel = if (isOutput) GLES30.GL_RGBA else GLES30.GL_RED
                GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
                GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, textures[index])
                GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_MIN_FILTER,
                    GLES30.GL_NEAREST)
                GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_MAG_FILTER,
                    GLES30.GL_NEAREST)
                GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_WRAP_S,
                    GLES30.GL_CLAMP_TO_EDGE)
                GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_WRAP_T,
                    GLES30.GL_CLAMP_TO_EDGE)
                val size = CORE + halo * 2
                GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D, 0, format,
                    size, size, 0, pixel, if (isOutput) GLES30.GL_HALF_FLOAT else GLES30.GL_FLOAT, null)
                GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, fbos[index])
                GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,
                    GLES30.GL_COLOR_ATTACHMENT0, GLES30.GL_TEXTURE_2D, textures[index], 0)
                check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER) ==
                    GLES30.GL_FRAMEBUFFER_COMPLETE) {
                    "C donor MGC R32F/16F sharpen target[$index] unsupported"
                }
            }
            gpu.checkGl("C MGC donor sharpen pyramid initialization")
            initialized = true
        } finally {
            oldState.restore()
            if (!initialized) dispose()
        }
    }

    /** Reads exact native-grid sharpened encoded SDR; geometry and JPEG own their own transforms. */
    fun readEncodedTile(x: Int, y: Int, w: Int, h: Int, dst: ByteBuffer) {
        color.requireOwner()
        check(!closed && owner == EGL14.eglGetCurrentContext()) {
            "C donor MGC sharpen wrong EGL owner"
        }
        require(x >= 0 && y >= 0 && w in 1..CORE && h in 1..CORE &&
            x <= color.width - w && y <= color.height - h && dst.isDirect &&
            !dst.isReadOnly && dst.capacity().toLong() >= w.toLong() * h * 16L) {
            "C donor MGC sharpen invalid output tile"
        }
        val state = Iris26972CDonorSabreGpuMerge.GlState.capture()
        val oldPack = gpu.glInt(GLES30.GL_PIXEL_PACK_BUFFER_BINDING)
        val oldAlign = gpu.glInt(GLES30.GL_PACK_ALIGNMENT)
        val oldRows = gpu.glInt(GLES30.GL_PACK_ROW_LENGTH)
        try {
            GLES30.glBindVertexArray(vao)
            GLES30.glDisable(GLES30.GL_BLEND)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glColorMask(true, true, true, true)
            // Original pass 1: encoded RGB -> BT.709 luma. Off-image taps are
            // clamped to the ACTUAL physical image edge, not to the tile edge.
            begin(0, w + 2 * LUMA_HALO, h + 2 * LUMA_HALO)
            bind(0, "uSource", 0, color.encodedSrgbTexture)
            origin(0, "uGlobalOrigin", x - LUMA_HALO, y - LUMA_HALO)
            GLES30.glUniform2i(loc(0, "uImageMax"), color.width - 1, color.height - 1)
            GLES30.glDrawArrays(GLES30.GL_TRIANGLES, 0, 3)

            // Original pass 2: L1 binomial 3x3 at dilation 1. This plane has
            // six pixels of source geometry on each side, as in the donor.
            begin(1, w + 2 * LEVEL1_HALO, h + 2 * LEVEL1_HALO)
            bind(1, "uLuma", 0, textures[0])
            origin(1, "uGlobalOrigin", x - LEVEL1_HALO, y - LEVEL1_HALO)
            origin(1, "uLumaOrigin", x - LUMA_HALO, y - LUMA_HALO)
            GLES30.glDrawArrays(GLES30.GL_TRIANGLES, 0, 3)

            // Original pass 3: L2 binomial 3x3 at dilation 2.
            begin(2, w + 2 * LEVEL2_HALO, h + 2 * LEVEL2_HALO)
            bind(2, "uLevel1", 0, textures[1])
            origin(2, "uGlobalOrigin", x - LEVEL2_HALO, y - LEVEL2_HALO)
            origin(2, "uLevel1Origin", x - LEVEL1_HALO, y - LEVEL1_HALO)
            GLES30.glDrawArrays(GLES30.GL_TRIANGLES, 0, 3)

            // Original pass 4: L3 d4, three SNR curves, local extrema clamp,
            // and shared delta to R,G,B. No chroma sharpening.
            begin(3, w, h)
            bind(3, "uSource", 0, color.encodedSrgbTexture)
            bind(3, "uLuma", 1, textures[0])
            bind(3, "uLevel1", 2, textures[1])
            bind(3, "uLevel2", 3, textures[2])
            origin(3, "uGlobalOrigin", x, y)
            origin(3, "uLumaOrigin", x - LUMA_HALO, y - LUMA_HALO)
            origin(3, "uLevel1Origin", x - LEVEL1_HALO, y - LEVEL1_HALO)
            origin(3, "uLevel2Origin", x - LEVEL2_HALO, y - LEVEL2_HALO)
            GLES30.glUniform1fv(loc(3, "uKnots"), knots.size, knots, 0)
            GLES30.glUniform1fv(loc(3, "uValues"), values.size, values, 0)
            GLES30.glUniform1fv(loc(3, "uSlopes"), slopes.size, slopes, 0)
            GLES30.glUniform1f(loc(3, "uLowerScale"), 1f - attenuation)
            GLES30.glUniform1f(loc(3, "uUpperScale"), 1f + attenuation)
            GLES30.glDrawArrays(GLES30.GL_TRIANGLES, 0, 3)
            gpu.checkGl("C MGC donor sharpen four-pass draw")

            GLES30.glBindFramebuffer(GLES30.GL_READ_FRAMEBUFFER, fbos[3])
            GLES30.glReadBuffer(GLES30.GL_COLOR_ATTACHMENT0)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
            GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH, 0)
            dst.clear()
            dst.limit(w * h * 16)
            GLES30.glReadPixels(0, 0, w, h, GLES30.GL_RGBA, GLES30.GL_FLOAT, dst)
            gpu.checkGl("C MGC donor sharpen native F32 readback")
            dst.position(0)
        } finally {
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, oldPack)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, oldAlign)
            GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH, oldRows)
            state.restore()
        }
    }

    private fun begin(index: Int, width: Int, height: Int) {
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, fbos[index])
        GLES30.glViewport(0, 0, width, height)
        GLES30.glUseProgram(programs[index])
    }
    private fun bind(index: Int, name: String, unit: Int, id: Int) {
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + unit)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, id)
        GLES30.glUniform1i(loc(index, name), unit)
    }
    private fun origin(index: Int, name: String, x: Int, y: Int) {
        GLES30.glUniform2i(loc(index, name), x, y)
    }
    private fun loc(index: Int, name: String): Int =
        GLES30.glGetUniformLocation(programs[index], name).also {
            check(it >= 0) { "C donor MGC sharpen required uniform $name optimized away" }
        }
    override fun close() {
        check(!closed && owner == EGL14.eglGetCurrentContext()) {
            "C donor MGC sharpen cannot release from another EGL owner"
        }
        dispose()
        closed = true
    }
    private fun dispose() {
        programs.filter { it > 0 }.forEach { GLES30.glDeleteProgram(it) }
        if (fbos.any { it > 0 }) GLES30.glDeleteFramebuffers(fbos.size, fbos, 0)
        if (textures.any { it > 0 }) GLES30.glDeleteTextures(textures.size, textures, 0)
        if (vao > 0) GLES30.glDeleteVertexArrays(1, intArrayOf(vao), 0)
    }
    private companion object {
        const val CORE = 256
        const val LUMA_HALO = 7
        const val LEVEL1_HALO = 6
        const val LEVEL2_HALO = 4
        const val VERTEX = """
            #version 300 es
            precision highp float;
            void main() {
                vec2 p[3] = vec2[3](vec2(-1.0,-1.0),vec2(3.0,-1.0),vec2(-1.0,3.0));
                gl_Position = vec4(p[gl_VertexID],0.0,1.0);
            }
        """
        const val LUMA = """
            #version 300 es
            precision highp float;
            precision highp int;
            precision highp sampler2D;
            uniform highp sampler2D uSource;
            uniform ivec2 uGlobalOrigin;
            uniform ivec2 uImageMax;
            layout(location=0) out float oLuma;
            const vec3 ENCODED_LUMA = vec3(0.2126, 0.7152, 0.0722);
            void main() {
                ivec2 p = ivec2(gl_FragCoord.xy) + uGlobalOrigin;
                vec3 rgb = clamp(texelFetch(uSource, clamp(p,ivec2(0),uImageMax),0).rgb, 0.0, 1.0);
                oLuma = dot(rgb, ENCODED_LUMA);
            }
        """
        const val LEVEL1 = """
            #version 300 es
            precision highp float;
            precision highp int;
            precision highp sampler2D;
            uniform highp sampler2D uLuma;
            uniform ivec2 uGlobalOrigin;
            uniform ivec2 uLumaOrigin;
            layout(location=0) out float oLevel;
            float source(ivec2 p) {return texelFetch(uLuma,p-uLumaOrigin,0).r;}
            float column(ivec2 p) {
                return 0.25 * (source(p-ivec2(0,1))+source(p+ivec2(0,1)))+0.5*source(p);
            }
            void main() {
                ivec2 p = ivec2(gl_FragCoord.xy)+uGlobalOrigin;
                oLevel = 0.25*(column(p-ivec2(1,0))+column(p+ivec2(1,0)))+0.5*column(p);
            }
        """
        const val LEVEL2 = """
            #version 300 es
            precision highp float;
            precision highp int;
            precision highp sampler2D;
            uniform highp sampler2D uLevel1;
            uniform ivec2 uGlobalOrigin;
            uniform ivec2 uLevel1Origin;
            layout(location=0) out float oLevel;
            float source(ivec2 p) {return texelFetch(uLevel1,p-uLevel1Origin,0).r;}
            float column(ivec2 p) {
                return 0.25 * (source(p-ivec2(0,2))+source(p+ivec2(0,2)))+0.5*source(p);
            }
            void main() {
                ivec2 p = ivec2(gl_FragCoord.xy)+uGlobalOrigin;
                oLevel = 0.25*(column(p-ivec2(2,0))+column(p+ivec2(2,0)))+0.5*column(p);
            }
        """
        const val OUTPUT = """
            #version 300 es
            precision highp float;
            precision highp int;
            precision highp sampler2D;
            uniform highp sampler2D uSource;
            uniform highp sampler2D uLuma;
            uniform highp sampler2D uLevel1;
            uniform highp sampler2D uLevel2;
            uniform ivec2 uGlobalOrigin;
            uniform ivec2 uLumaOrigin;
            uniform ivec2 uLevel1Origin;
            uniform ivec2 uLevel2Origin;
            uniform float uKnots[12];
            uniform float uValues[12];
            uniform float uSlopes[12];
            uniform float uLowerScale;
            uniform float uUpperScale;
            layout(location=0) out vec4 oColor;
            float luma(ivec2 p) {return texelFetch(uLuma,p-uLumaOrigin,0).r;}
            float level1(ivec2 p) {return texelFetch(uLevel1,p-uLevel1Origin,0).r;}
            float level2(ivec2 p) {return texelFetch(uLevel2,p-uLevel2Origin,0).r;}
            float level2Column(ivec2 p) {
                return 0.25*(level2(p-ivec2(0,4))+level2(p+ivec2(0,4)))+0.5*level2(p);
            }
            float level3(ivec2 p) {
                return 0.25*(level2Column(p-ivec2(4,0))+level2Column(p+ivec2(4,0)))
                    +0.5*level2Column(p);
            }
            float bandResponse(int band,float d) {
                float magnitude=abs(d);
                int first=band*4;
                int segment=magnitude>=uKnots[first+3]?3:
                    magnitude>=uKnots[first+2]?2:
                    magnitude>=uKnots[first+1]?1:0;
                int index=first+segment;
                return sign(d)*(uValues[index]+uSlopes[index]*(magnitude-uKnots[index]));
            }
            float sharpenedLuma(ivec2 p) {
                float y0=luma(p);
                float y1=level1(p);
                float y2=level2(p);
                float y3=level3(p);
                float sharp=y3+bandResponse(0,y0-y1)+bandResponse(1,y1-y2)
                    +bandResponse(2,y2-y3);
                float lowest=y0;
                float highest=y0;
                for(int j=-2;j<=2;++j)for(int i=-2;i<=2;++i){
                    float neighbour=luma(p+ivec2(i,j));
                    lowest=min(lowest,neighbour);
                    highest=max(highest,neighbour);
                }
                sharp=max(lowest*uLowerScale,min(highest*uUpperScale,sharp));
                return clamp(sharp,0.0,1.0);
            }
            void main() {
                ivec2 p=ivec2(gl_FragCoord.xy)+uGlobalOrigin;
                vec3 rgb=clamp(texelFetch(uSource,p,0).rgb,0.0,1.0);
                oColor=vec4(clamp(rgb+(sharpenedLuma(p)-luma(p)),0.0,1.0),1.0);
            }
        """
    }
}
