package com.hinnka.mycamera.processor

import android.opengl.EGL14
import android.opengl.EGLContext
import android.opengl.GLES30
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.floor
import kotlin.math.ceil

/**
 * Experiment C-only VERTICAL-STRIP texture-address adapter for bjzhou's original RAW
 * LUT luminance and GpuReferenceGainmapProducer GLSL. Not the older Iris CPU
 * 2x2 gainmap approximation. The donor math and R16F/RGBA8 intermediates are
 * unchanged; the vertex domain simply maps each gainmap column strip onto the ORIGINAL
 * global image coordinates. We MUST retain the full image height for both passes:
 * the donor's separate readback and gainmap EGL contexts invert the sidecar row
 * address relative to the HDR source. Arbitrary vertical tiles therefore DO NOT
 * reproduce the donor, even if their GL_LINEAR source taps are available.
 * Test: odd 7x5, full-size and sub-width vertical strips vs untiled donor shaders.
 *
 * Before and after SDR must be actual independently rendered encoded sRGB
 * outputs of the selected donor LUT stack. This code cannot grant permission
 * to substitute an identity LUT for an active baseline or creative layer.
 * HDR must be the ORIGINAL linear-extended-sRGB donor HDR reference aligned
 * with the finalized output SDR, not sensor RGB or a post-SDR fabricated image.
 *
 * This owner is NOT connected to publication until those two invariants and
 * the original JPEG/R packaging are proven. It never allocates a 50MP Bitmap.
 */
internal class Iris26975CDonorTiledGainmapGpu : AutoCloseable {
    private val gpu = Iris26972CDonorSabreGpuMerge
    private val owner: EGLContext = EGL14.eglGetCurrentContext()
    private val programs = IntArray(2)
    private var vao = 0
    private var closed = false

    internal data class Tile(
        val sourceLeft: Int, val sourceTop: Int,
        val sourceWidth: Int, val sourceHeight: Int,
        val gainLeft: Int, val gainTop: Int,
        val gainWidth: Int, val gainHeight: Int,
        val fullImageWidth: Int, val fullImageHeight: Int,
    ) {
        val fullGainWidth: Int get() = (fullImageWidth + 1) / 2
        val fullGainHeight: Int get() = (fullImageHeight + 1) / 2
        internal fun verify() {
            require(fullImageWidth in 2..16384 && fullImageHeight in 2..16384 &&
                sourceLeft >= 0 && sourceTop >= 0 &&
                sourceWidth in 1..256 && sourceHeight == fullImageHeight && sourceTop == 0 &&
                sourceLeft + sourceWidth <= fullImageWidth &&
                sourceTop + sourceHeight <= fullImageHeight &&
                gainLeft >= 0 && gainTop >= 0 &&
                gainWidth in 1..128 && gainHeight == fullGainHeight && gainTop == 0 &&
                gainLeft + gainWidth <= fullGainWidth &&
                gainTop + gainHeight <= fullGainHeight) {
                "C donor GPU UHDR requires full-height column strips to preserve original sidecar coordinates"
            }
            fun covers(origin:Int,size:Int,gainOrigin:Int,gainSize:Int,full:Int,fullGain:Int):Boolean {
                fun center(g:Int) = (g + .5) * full / fullGain - .5
                val first = floor(center(gainOrigin)).toInt().coerceIn(0,full-1)
                val last = ceil(center(gainOrigin + gainSize - 1)).toInt().coerceIn(0,full-1)
                return origin <= first && last < origin + size
            }
            require(covers(sourceLeft,sourceWidth,gainLeft,gainWidth,fullImageWidth,fullGainWidth) &&
                covers(sourceTop,sourceHeight,gainTop,gainHeight,fullImageHeight,fullGainHeight)) {
                "C donor GPU UHDR source tile truncates GL_LINEAR support"
            }
        }
    }

    private fun requireOwner() {
        check(!closed && owner != EGL14.EGL_NO_CONTEXT && owner == EGL14.eglGetCurrentContext()) {
            "C donor GPU UHDR wrong EGL owner"
        }
        gpu.requireCurrentContext()
    }
    companion object {
        /** Shader coordinates use global gainmap centers, not local 2x2 averages. */
        internal val vertex = """
            #version 300 es
            precision highp float;
            uniform vec2 uGainOrigin;
            uniform vec2 uGainTileSize;
            uniform vec2 uFullGainSize;
            uniform vec2 uFullImageSize;
            uniform vec2 uSourceOrigin;
            uniform vec2 uSourceTileSize;
            out vec2 vTexCoord;
            out vec2 vSidecarCoord;
            void main() {
                vec2 p[3] = vec2[3](vec2(-1.0,-1.0),vec2(3.0,-1.0),vec2(-1.0,3.0));
                vec2 position = p[gl_VertexID];
                gl_Position = vec4(position,0.0,1.0);
                vec2 localUv = position*0.5 + 0.5;
                vSidecarCoord = vec2(localUv.x, 1.0-localUv.y);
                vec2 topOriginGain = uGainOrigin +
                    vec2(localUv.x,1.0-localUv.y)*uGainTileSize;
                vTexCoord = (topOriginGain/uFullGainSize*uFullImageSize -
                    uSourceOrigin)/uSourceTileSize;
            }
        """.trimIndent()

        // Preserve donor fragment math verbatim; only the sidecar sampler's
        // coordinate is switched from original whole-FBO UV to the local tile UV.
        internal val sidecarFragment = Iris26975CDonorLutLuminanceShader.fragment
        internal val residualFragment = Iris26975CDonorGpuLutResidualShader.fragment
            .replace("in vec2 vTexCoord;", "in vec2 vTexCoord;\n        in vec2 vSidecarCoord;")
            .replace("texture(uLutLuminanceGainTexture, vTexCoord)",
                "texture(uLutLuminanceGainTexture, vSidecarCoord)")
    }
    private fun location(p:Int,name:String)=GLES30.glGetUniformLocation(p,name)
    private fun bind(p:Int,name:String,unit:Int,tex:Int) {
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0+unit)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,tex)
        GLES30.glUniform1i(location(p,name),unit)
    }
    private fun tex(format:Int,w:Int,h:Int,bytes:ByteBuffer?=null):Int {
        val ids=IntArray(1);GLES30.glGenTextures(1,ids,0)
        check(ids[0]>0)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,ids[0])
        for(key in intArrayOf(GLES30.GL_TEXTURE_MIN_FILTER,GLES30.GL_TEXTURE_MAG_FILTER))
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,key,GLES30.GL_LINEAR)
        for(key in intArrayOf(GLES30.GL_TEXTURE_WRAP_S,GLES30.GL_TEXTURE_WRAP_T))
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,key,GLES30.GL_CLAMP_TO_EDGE)
        val pixel = if(format==GLES30.GL_RGBA16F) GLES30.GL_FLOAT else GLES30.GL_UNSIGNED_BYTE
        val source = bytes?.duplicate()?.order(ByteOrder.nativeOrder())?.apply{clear()}
        GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,format,w,h,0,GLES30.GL_RGBA,pixel,source)
        return ids[0]
    }
    private fun frame(target:Int):Int {
        val ids=IntArray(1);GLES30.glGenFramebuffers(1,ids,0)
        check(ids[0]>0)
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,ids[0])
        GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT0,
            GLES30.GL_TEXTURE_2D,target,0)
        GLES30.glDrawBuffers(1,intArrayOf(GLES30.GL_COLOR_ATTACHMENT0),0)
        check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)==GLES30.GL_FRAMEBUFFER_COMPLETE)
        return ids[0]
    }
    private fun uniforms(program:Int,tile:Tile) {
        GLES30.glUniform2f(location(program,"uGainOrigin"),tile.gainLeft.toFloat(),tile.gainTop.toFloat())
        GLES30.glUniform2f(location(program,"uGainTileSize"),tile.gainWidth.toFloat(),tile.gainHeight.toFloat())
        GLES30.glUniform2f(location(program,"uFullGainSize"),tile.fullGainWidth.toFloat(),tile.fullGainHeight.toFloat())
        GLES30.glUniform2f(location(program,"uFullImageSize"),tile.fullImageWidth.toFloat(),tile.fullImageHeight.toFloat())
        GLES30.glUniform2f(location(program,"uSourceOrigin"),tile.sourceLeft.toFloat(),tile.sourceTop.toFloat())
        GLES30.glUniform2f(location(program,"uSourceTileSize"),tile.sourceWidth.toFloat(),tile.sourceHeight.toFloat())
    }
    private fun draw(program:Int,fb:Int,tile:Tile,setup:()->Unit){
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,fb)
        GLES30.glViewport(0,0,tile.gainWidth,tile.gainHeight)
        GLES30.glUseProgram(program)
        GLES30.glBindVertexArray(vao)
        GLES30.glDisable(GLES30.GL_BLEND)
        GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
        GLES30.glDisable(GLES30.GL_DEPTH_TEST)
        GLES30.glColorMask(true,true,true,true)
        uniforms(program,tile)
        setup()
        GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3)
    }
    private fun prepare() {
        if(programs[0]!=0)return
        require(sidecarFragment.count{it=='#'}>0 && residualFragment.contains("vSidecarCoord"))
        programs[0]=gpu.compileProgram(vertex,sidecarFragment)
        programs[1]=gpu.compileProgram(vertex,residualFragment)
        val id=IntArray(1);GLES30.glGenVertexArrays(1,id,0);vao=id[0]
        check(programs.all{it>0} && vao>0)
    }

    /**
     * Returns top-left ALPHA_8 donor gainmap pixels on the global 2x grid.
     * Before and after SDR are original RGBA_F16 sources supplied as float32
     * for native GPU half conversion, never JPEG-rounded RGBA8. `hdrRgbaF32`
     * is an actual linear RGBA32F reference which is uploaded
     * into the original donor's RGBA16F format before bilinear sampling.
     */
    fun compute(tile:Tile,beforeLut:ByteBuffer,afterLut:ByteBuffer,
        hdrRgbaF32:ByteBuffer,strength:Float):ByteBuffer {
        requireOwner();tile.verify()
        require(strength.isFinite() && strength in .25f..2f &&
            beforeLut.isDirect && afterLut.isDirect && hdrRgbaF32.isDirect &&
            !beforeLut.isReadOnly && !afterLut.isReadOnly && !hdrRgbaF32.isReadOnly &&
            beforeLut.capacity().toLong()>=tile.sourceWidth.toLong()*tile.sourceHeight*16 &&
            afterLut.capacity().toLong()>=tile.sourceWidth.toLong()*tile.sourceHeight*16 &&
            beforeLut.order()==ByteOrder.nativeOrder() &&
            afterLut.order()==ByteOrder.nativeOrder() &&
            hdrRgbaF32.capacity().toLong()>=tile.sourceWidth.toLong()*tile.sourceHeight*16) {
            "C donor UHDR requires actual aligned before-LUT / after-LUT / linear HDR"
        }
        check(gpu.glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS)>=3)
        check(gpu.glInt(GLES30.GL_MAX_TEXTURE_SIZE)>=maxOf(tile.sourceHeight,tile.sourceWidth,
            tile.gainWidth,tile.gainHeight)) {
            "C donor GPU UHDR full-height strip exceeds GLES texture dimensions"
        }
        val state=Iris26972CDonorSabreGpuMerge.GlState.capture()
        val oldUnpackBuffer=gpu.glInt(GLES30.GL_PIXEL_UNPACK_BUFFER_BINDING)
        val oldUnpackAlign=gpu.glInt(GLES30.GL_UNPACK_ALIGNMENT)
        val oldUnpackRows=gpu.glInt(GLES30.GL_UNPACK_ROW_LENGTH)
        val oldPackBuffer=gpu.glInt(GLES30.GL_PIXEL_PACK_BUFFER_BINDING)
        val oldPackAlign=gpu.glInt(GLES30.GL_PACK_ALIGNMENT)
        val oldPackRows=gpu.glInt(GLES30.GL_PACK_ROW_LENGTH)
        val images=IntArray(5);val fb=IntArray(2)
        try {
            prepare()
            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER,0)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT,1)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH,0)
            images[0]=tex(GLES30.GL_RGBA16F,tile.sourceWidth,tile.sourceHeight,beforeLut)
            images[1]=tex(GLES30.GL_RGBA16F,tile.sourceWidth,tile.sourceHeight,afterLut)
            images[2]=tex(GLES30.GL_RGBA16F,tile.sourceWidth,tile.sourceHeight,hdrRgbaF32)
            images[3]=tex(GLES30.GL_RGBA16F,tile.gainWidth,tile.gainHeight)
            images[4]=tex(GLES30.GL_RGBA8,tile.gainWidth,tile.gainHeight)
            fb[0]=frame(images[3]);fb[1]=frame(images[4])
            val a=programs[0]
            draw(a,fb[0],tile){
                bind(a,"uBeforeLutTexture",0,images[0]);bind(a,"uAfterLutTexture",1,images[1])
                GLES30.glUniform1f(location(a,"uOffset"),1e-4f)
            }
            val b=programs[1]
            draw(b,fb[1],tile){
                bind(b,"uLutLuminanceGainTexture",0,images[3]);bind(b,"uSdrTexture",1,images[1])
                bind(b,"uHdrTexture",2,images[2])
                GLES30.glUniform1f(location(b,"uMinGainRatio"),.25f)
                GLES30.glUniform1f(location(b,"uMaxGainRatio"),4f)
                GLES30.glUniform1f(location(b,"uOffset"),1e-4f)
                GLES30.glUniform1f(location(b,"uStrength"),strength)
            }
            GLES30.glBindFramebuffer(GLES30.GL_READ_FRAMEBUFFER,fb[1])
            GLES30.glReadBuffer(GLES30.GL_COLOR_ATTACHMENT0)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER,0)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,1)
            GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH,0)
            val rgba=ByteBuffer.allocateDirect(tile.gainWidth*tile.gainHeight*4)
            GLES30.glReadPixels(0,0,tile.gainWidth,tile.gainHeight,
                GLES30.GL_RGBA,GLES30.GL_UNSIGNED_BYTE,rgba)
            gpu.checkGl("C donor tiled LUT sidecar / UHDR original GPU shader")
            val output=ByteBuffer.allocateDirect(tile.gainWidth*tile.gainHeight)
            for(y in 0 until tile.gainHeight)for(x in 0 until tile.gainWidth){
                val from=((tile.gainHeight-1-y)*tile.gainWidth+x)*4
                output.put(rgba.get(from))
            }
            output.position(0)
            return output
        } finally {
            if(fb.any{it>0})GLES30.glDeleteFramebuffers(fb.count{it>0},fb.filter{it>0}.toIntArray(),0)
            if(images.any{it>0})GLES30.glDeleteTextures(images.count{it>0},images.filter{it>0}.toIntArray(),0)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER,oldUnpackBuffer)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT,oldUnpackAlign)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH,oldUnpackRows)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER,oldPackBuffer)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,oldPackAlign)
            GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH,oldPackRows)
            state.restore()
        }
    }
    /**
     * Assemble one complete original-donor ALPHA_8 gainmap from full-height
     * vertical strips. This is only a GPU assembly API, NOT publication approval.
     * An actual after-LUT render and original linear HDR source must be supplied
     * for every strip; legacy Iris writeTile and provisional HDR are forbidden.
     */
    internal data class DonorInputs(
        val beforeLutEncodedSrgb: ByteBuffer,
        val afterLutEncodedSrgb: ByteBuffer,
        val independentHdrLinearSrgb: ByteBuffer,
        val physicalCameraId: String,
        val referenceTimestampNs: Long,
    )

    fun computeCompleteGainmap(
        imageWidth: Int,
        imageHeight: Int,
        physicalCameraId: String,
        referenceTimestampNs: Long,
        strength: Float,
        supplyOriginalDonorInputs: (Iris26975CDonorGainmapStripAssembly.Strip) -> DonorInputs,
    ): ByteBuffer {
        requireOwner()
        require(physicalCameraId.isNotBlank() && referenceTimestampNs > 0L) {
            "C donor UHDR requires physical RAW and genuine reference timestamp"
        }
        return Iris26975CDonorGainmapStripAssembly.assemble(imageWidth,imageHeight) { strip ->
            val inputs = supplyOriginalDonorInputs(strip)
            require(inputs.physicalCameraId == physicalCameraId &&
                inputs.referenceTimestampNs == referenceTimestampNs) {
                "C donor UHDR input belongs to another physical RAW exposure"
            }
            val tile = Tile(
                strip.sourceLeft, 0, strip.sourceWidth, imageHeight,
                strip.gainLeft, 0, strip.gainWidth, strip.gainImageHeight,
                imageWidth, imageHeight,
            )
            compute(tile,inputs.beforeLutEncodedSrgb,inputs.afterLutEncodedSrgb,
                inputs.independentHdrLinearSrgb,strength)
        }
    }

    /**
     * Connect real finalized GuidedUpsample+Lanczos SDR pixels to the original
     * bjzhou LUT-sidecar/residual GPU stages for the user's explicit No LUT
     * selection. Full-height vertical strips keep donor sampling phase.
     *
     * This is the tested source/GPU boundary, NOT proof that the preceding
     * camera-domain HDR ratio has achieved the donor's numerical parity. The
     * separate publish gate must stay closed until that comparison passes.
     */
    internal fun computeNoLutFromFinalizedGeometry(
        imageWidth: Int,
        imageHeight: Int,
        physicalCameraId: String,
        referenceTimestampNs: Long,
        strength: Float,
        selection: Iris26975CDonorLutSelection.Frozen,
        source: Iris26975CGeometryResampler,
    ): ByteBuffer {
        requireOwner()
        require(selection.isNoLut) { "26975 C original UHDR cannot silently apply Standard LUT" }
        return computeCompleteGainmap(
            imageWidth, imageHeight, physicalCameraId, referenceTimestampNs,
            strength,
        ) { strip ->
            val pixels = Iris26975CDonorGainmapStripAssembly.materializeNoLutSourceStrip(
                strip, selection, physicalCameraId, referenceTimestampNs,
                fits = source::fits,
                render = { x, y, w, h ->
                    val tile = source.render(x, y, w, h)
                    Iris26975CDonorGainmapStripAssembly.FinalizedTile(tile.sdr, tile.hdr, tile.encodedSdrF32)
                },
            )
            DonorInputs(
                pixels.beforeLutEncodedSrgb,
                pixels.afterLutEncodedSrgb,
                pixels.independentHdrLinearSrgb,
                pixels.physicalCameraId,
                pixels.referenceTimestampNs,
            )
        }
    }

    override fun close() {
        if(closed)return
        requireOwner()
        val state=Iris26972CDonorSabreGpuMerge.GlState.capture()
        try {
            programs.filter{it>0}.forEach{GLES30.glDeleteProgram(it)}
            if(vao>0)GLES30.glDeleteVertexArrays(1,intArrayOf(vao),0)
            vao=0;closed=true
        } finally {state.restore()}
    }
}
