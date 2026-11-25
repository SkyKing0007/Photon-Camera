package com.hinnka.mycamera.processor

import android.content.Context
import android.opengl.EGL14
import android.opengl.EGLContext
import android.opengl.GLES30
import android.opengl.GLES31
import com.hinnka.mycamera.utils.PLog
import com.particlesdevs.photoncamera.processing.processor.Iris26983COnRgba16fCarrier
import java.nio.ByteBuffer
import java.nio.ByteOrder

/** Independent C SR ON, exact 26982 all-NORMAL LKR 3x2 GPU processing stage.
 * Requires the dedicated serialized processing EGL context, not the preview context.
 * The returned 1x guide/clip are still pre-post-denoise and NOT publication authority.
 * Caller owns input RAWs and must preserve the EGL context through result close.
 * Not a route selector. Until capture and postprocessing are connected this is unused.
 */
internal class GlesIris26983COnGpuMerge(
    private val app: Context,
    private val width: Int,
    private val height: Int,
    private val cfaPattern: Int,
    lensMap: FloatArray?,
    private val lensShadingWidth: Int,
    private val lensShadingHeight: Int,
) {
    private val lensShading = lensMap?.copyOf()
    private val textures = ArrayList<Int>()
    private val textureSpecs = HashMap<Int, TextureSpec>()
    private val programs = ArrayList<Int>()
    private val framebuffers = ArrayList<Int>()
    private val uniformLocations = HashMap<Int, HashMap<String, Int>>()
    private val validatedRenderTargetSpecs = HashSet<List<TextureSpec>>()
    private var renderFbo = 0
    private var renderTargetAttachmentCount = 0
    private var iris26859BLensMapTexture = 0
    private var iris26859BLensShadeProgram = 0
    private var iris26856LabPrepareProgram = 0
    private var iris26856LabReduceProgram = 0
    private var iris26856LabReconstructProgram = 0
    private var iris26932RawLensMedianProgram = 0
    private var used = false
    private data class TextureSpec(val width: Int,val height: Int,val internalFormat: Int,val filter: Int)

    /** Owns both 1x textures and the packed 2x carrier until explicitly closed.
     * A future consumer may borrow but must not delete the GL texture IDs.
     */
    class Result internal constructor(
        true2x: Iris26983COnRgba16fCarrier,
        val oneXSensorRgb: Int,
        val oneXClip: Int,
        val bridgeRgb: Int,
        private val context: EGLContext,
        private val thread: Thread,
    ): AutoCloseable {
        private var closed=false
        private var packedOwner: Iris26983COnRgba16fCarrier? = true2x
        val true2x: Iris26983COnRgba16fCarrier
            get() = checkNotNull(packedOwner) { "26983 C ON 2x carrier already transferred" }
        /** Only after the 1x guide and sidecar have been copied; transfer AHB, not EGL textures. */
        fun takeTrue2x(): Iris26983COnRgba16fCarrier {
            assertUsable()
            val result = true2x
            packedOwner = null
            return result
        }
        fun assertUsable() {
            check(!closed && Thread.currentThread() === thread && EGL14.eglGetCurrentContext() == context) {
                "26983 C ON guide requires its original processing GL context"
            }
        }
        override fun close() {
            if(closed) return
            check(Thread.currentThread() === thread && EGL14.eglGetCurrentContext() == context) {
                "26983 C ON guide cleanup requires its original processing GL context"
            }
            closed=true
            try { GLES30.glDeleteTextures(3,intArrayOf(oneXSensorRgb,oneXClip,bridgeRgb),0) }
            finally {
                val owner = packedOwner
                packedOwner = null
                owner?.close()
            }
        }
    }

    /** Immutable selected-reference/physical RAW receipt is supplied by the future C capture owner.
     * Only the proven 26982 Motion all-NORMAL path is admitted here; do not silently discard LONG.
     */
    fun run(frames: List<RawStackFrame>, referenceFrameNumber: Long, referenceTimestamp: Long,
            referenceBlack: FloatArray, sensorWhite: Int,
            color: GlesIris26983COnColorContract.Snapshot,
            alternativeHighlight: Boolean, previewP995: Float, linearOutput: Iris26985CLinearOutput): Result {
        check(!used); used=true
        val context=EGL14.eglGetCurrentContext()
        check(context != EGL14.EGL_NO_CONTEXT) { "26983 C ON requires current GLES processing context" }
        require(width>=64 && height>=64 && width%2==0 && height%2==0 && cfaPattern in 0..3)
        require(frames.size in 2..24 && frames.count{it.role==RawBurstFrameRole.NORMAL}>=2 &&
            frames.all{it.role in listOf(RawBurstFrameRole.NORMAL,RawBurstFrameRole.HDR_SHORT,RawBurstFrameRole.HDR_LONG)})
        require(frames.first().physicalCameraId?.isNotEmpty()==true &&
                frames.all { it.physicalCameraId==frames.first().physicalCameraId })
        val refIndex=frames.indexOfFirst { it.frameNumber==referenceFrameNumber && it.sensorTimestampNs==referenceTimestamp }
        require(refIndex>=0 && frames.count { it.sensorTimestampNs==referenceTimestamp }==1)
        val snapshot=color.cloneForCapture()
        val outputW=Math.multiplyExact(width,2); val outputH=Math.multiplyExact(height,2)
        val limit=IntArray(1); GLES30.glGetIntegerv(GLES30.GL_MAX_TEXTURE_SIZE,limit,0)
        require(outputW<=limit[0] && outputH<=limit[0])
        var packedOwner: Iris26983COnRgba16fCarrier?=null
        var completed=false
        val oldPriority=GlesGpuScheduler.lowerCurrentThreadPriority("Iris26983COnGpu")
        try {
            renderFbo=createFramebuffer()
            applyRawRenderState()
            // Do not reserve ~500MB of 50MP GL textures while Vulkan is solving.
            var nativeRgb=0
            var nativeClip=0
            GlesIris26983COnFrozenRawIngress.borrowNormals(frames,width,height,referenceBlack.copyOf(),sensorWhite,linearOutput).use { frozen ->
                GlesIris26983COnLkrBridge.run(app,frozen,snapshot.amazeWhiteBalance,cfaPattern,refIndex,
                    GlesIris26983COnLkrBridge.JpegTransport { rgb,w,h,wb,hdrWhite ->
                        nativeRgb=createTexture(w,h,GLES30.GL_RGBA16F,GLES30.GL_NEAREST)
                        nativeClip=createTexture(w,h,GLES30.GL_R16F,GLES30.GL_NEAREST)
                        renderRawLens2420Cleanup(rgb,nativeRgb,w,h,wb,hdrWhite)
                        intArrayOf(nativeRgb,nativeClip)
                    },linearOutput)
            }
            GlesGpuScheduler.memoryBarrier()
            checkGlError("26983 C ON native LKR 50MP RGB + sensor clip")
            // 2.4.20 owns directional/chroma and highlight cleanup. Lens shading was applied
            // once in the shared float result; never repeat the historical Lab/median path.
            val sensorRgb=nativeRgb
            val guideRgb=createTexture(width,height,GLES30.GL_RGBA16F,GLES30.GL_NEAREST)
            val guideClip=createTexture(width,height,GLES30.GL_R16F,GLES30.GL_NEAREST)
            val p=linkProgram(iris26876DerivedGuideShader,"iris_26983_con_2x_derived_1x_guide")
            GLES30.glUseProgram(p)
            bindTexture(p,"uTwoXLinear",0,sensorRgb)
            bindTexture(p,"uTwoXOriginalClip",1,nativeClip)
            uniform2i(p,"uOneXExtent",width,height)
            draw(p,width,height,intArrayOf(guideRgb,guideClip))
            GlesGpuScheduler.memoryBarrier()
            checkGlError("26983 C ON 2x-derived 1x guide")
            val packed=Iris26983COnRgba16fCarrier.tryCreate(outputW,outputH)
                ?: error("26983 cannot allocate exact 50MP C ON carrier")
            packedOwner=packed
            check(packed.packWronskiRgbAndClip26876(sensorRgb,nativeClip)) { "26983 C ON exact 2x AHB export failed" }
            GlesGpuScheduler.memoryBarrier()
            checkGlError("26983 C ON carrier + live guide")
            // Release the 50MP transient allocation set before the extra 1x
            // copy, as in the original reconstruction -> stacker boundary.
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,0)
            textures.toList().filter { it!=guideRgb && it!=guideClip }.forEach {
                releaseOwnedTexture(it,"26983 consumed reconstruction transient")
            }
            // Exact 26982 separate primary 1x carrier and color sidecar. Keep
            // the guide and mask registered until both live textures are copied.
            val bridgeRgb=copyPersistentTexture(guideRgb,width,height)
            GlesGpuScheduler.memoryBarrier()
            checkGlError("26983 C ON independent bridge transport")
            check(bridgeRgb!=guideRgb && bridgeRgb in textures && guideRgb in textures && guideClip in textures)
            val result=Result(packed,guideRgb,guideClip,bridgeRgb,context,Thread.currentThread())
            for(id in intArrayOf(guideRgb,guideClip,bridgeRgb)) {
                textures.remove(id); textureSpecs.remove(id)
            }
            completed=true
            return result
        } finally {
            try {
                if(!completed) runCatching { packedOwner?.close() }
                GLES30.glUseProgram(0)
                GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,0)
                if(programs.isNotEmpty()) for(program in programs) GLES30.glDeleteProgram(program)
                if(framebuffers.isNotEmpty()) GLES30.glDeleteFramebuffers(framebuffers.size,framebuffers.toIntArray(),0)
                if(textures.isNotEmpty()) GLES30.glDeleteTextures(textures.size,textures.toIntArray(),0)
                textures.clear(); textureSpecs.clear(); programs.clear(); framebuffers.clear()
            } finally { GlesGpuScheduler.restoreCurrentThreadPriority(oldPriority,"Iris26983COnGpu") }
        }
    }

    /** Exact donor chroma_cleanup and HDR-scaled sensor-white tail, before Iris color matrix.
     * Two halo rows on each side; no extra full-frame RGB32F texture or Java heap copy.
     * DNG publication precedes this callback and never consumes the JPEG cleanup.
     */
    private fun renderRawLens2420Cleanup(rgb:ByteBuffer,target:Int,w:Int,h:Int,wb:FloatArray,hdrWhite:Float) {
        require(wb.size==3 && wb.all{it.isFinite()&&it>0f})
        require(rgb.isDirect && rgb.capacity().toLong()>=w.toLong()*h*12)
        val neutral=FloatArray(3){1f/wb[it]}
        val maxNeutral=neutral.maxOrNull()!!
        for(i in neutral.indices)neutral[i]/=maxNeutral
        val rows=128
        val upload=createTexture(w,minOf(h,rows+4),GLES30.GL_RGB32F,GLES30.GL_NEAREST)
        try {
            val source=app.assets.open("shaders/iris26983/con_26986_rawlens_cleanup.frag").bufferedReader().use{it.readText()}
            val program=linkProgram(source,"iris26986_rawlens2420_cleanup")
            GLES30.glUseProgram(program)
            bindTexture(program,"u_rgb",0,upload)
            uniform2i(program,"u_outsize",w,h)
            uniform1i(program,"u_fc_median",1)
            GLES30.glUniform1f(uniformLocation(program,"u_defringe"),1f)
            GLES30.glUniform1f(uniformLocation(program,"u_white_scale"),hdrWhite)
            GLES30.glUniform3f(uniformLocation(program,"u_camera_white_normalized"),neutral[0],neutral[1],neutral[2])
            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER,0)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT,4)
            bindRenderTargets(intArrayOf(target),"26986 donor chroma cleanup")
            for(y in 0 until h step rows) {
                val end=minOf(h,y+rows);val first=maxOf(0,y-2);val last=minOf(h,end+2)
                val band=rgb.duplicate().order(ByteOrder.nativeOrder())
                band.position(first*w*12);band.limit(last*w*12)
                GLES30.glTexSubImage2D(GLES30.GL_TEXTURE_2D,0,0,0,w,last-first,GLES30.GL_RGB,GLES30.GL_FLOAT,band.slice().order(ByteOrder.nativeOrder()))
                uniform1i(program,"u_row_start",first)
                GLES30.glViewport(0,y,w,end-y)
                GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3)
                checkGlError("26986 donor cleanup stripe $y")
            }
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,0)
            GlesGpuScheduler.memoryBarrier()
            checkGlError("26986 donor cleanup complete")
        } finally {
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,0)
            releaseOwnedTexture(upload,"26986 bounded donor RGB32F stripe")
        }
    }

    /** Active LKR-only branch of renderRawrBPostAmaze26856, no legacy FCC or second denoise. */
    private fun renderCOnPostLkr(input: Int, nativeClip: Int, snapshot: GlesIris26983COnColorContract.Snapshot,
                                 w: Int,h: Int): Int {
        check(input in textures && nativeClip in textures && w==width*2 && h==height*2)
        var temporary=0; var median=0; var lab=0; var neutral=0; var succeeded=false
        try {
            val applyProgram=linkProgram(GlesIris26983COnColorContract.applyAmazeWbForLabFcc,
                "iris_26983_con_temporary_wb_no_extra_noise")
            temporary=createTexture(w,h,GLES30.GL_RGBA16F,GLES30.GL_NEAREST)
            GLES30.glUseProgram(applyProgram)
            bindTexture(applyProgram,"uSensorNeutralAmazeRgb",0,input)
            uniform2i(applyProgram,"uSize",w,h)
            val gains=snapshot.amazeWhiteBalance
            GLES30.glUniform3f(GLES30.glGetUniformLocation(applyProgram,"uAmazeWb"),gains[0],gains[1],gains[2])
            draw(applyProgram,w,h,intArrayOf(temporary))
            GlesGpuScheduler.memoryBarrier()
            checkGlError("26983 C ON temporary WB for Lab")
            median=renderIris26932LkrMedian(temporary,w,h,nativeClip,gains)
            lab=renderRawrLabDefringe26856(median,snapshot.postWbCameraToSrgb,1f,w,h)
            val program=linkProgram(GlesIris26983COnSmoothWhite.shader,"iris_26983_con_post_lab_neutral_reconciliation")
            neutral=createTexture(w,h,GLES30.GL_RGBA16F,GLES30.GL_NEAREST)
            GLES30.glUseProgram(program)
            bindTexture(program,"uWbRgb",0,lab)
            bindTexture(program,"uPreLabWbRgb",1,median)
            uniform2i(program,"uSize",w,h)
            val inverse=snapshot.inverseWhiteBalance
            GLES30.glUniform3f(GLES30.glGetUniformLocation(program,"uInverseAmazeWb"),inverse[0],inverse[1],inverse[2])
            draw(program,w,h,intArrayOf(neutral))
            GlesGpuScheduler.memoryBarrier()
            checkGlError("26983 C ON Lab inverse-WB camera RGB")
            succeeded=true
            return neutral
        } finally {
            if(temporary!=0) releaseOwnedTexture(temporary,"26983 temporary WB")
            if(median!=0) releaseOwnedTexture(median,"26983 median")
            if(lab!=0) releaseOwnedTexture(lab,"26983 Lab")
            if(!succeeded && neutral!=0) releaseOwnedTexture(neutral,"26983 rejected neutral RGB")
        }
    }
    private fun ensureIris26859BLensMapTexture() {
        // Tile releaseTexturesFrom(...) may retire a prior B texture; stale GL
        // names MUST NOT be sampled on following true2x tiles or captures.
        if (iris26859BLensMapTexture != 0 && iris26859BLensMapTexture in textures) return
        iris26859BLensMapTexture = 0
        if (!hasLensShading() || checkNotNull(lensShading).any {
            !it.isFinite() || it <= 0f
        }) return
        iris26859BLensMapTexture = createLensShadingTexture()
        PLog.i("Iris26983COnGpu","IRIS_26859_B_LSC_MAP physicalMap=" +
            "${lensShadingWidth}x${lensShadingHeight} physicalPerLens=true valid=true")
    }

    private fun renderIris26859BLensShading(
        input: Int, outWidth: Int, outHeight: Int,
        originX: Int, originY: Int, expandedScale: Int,
    ): Int {
        val valid = hasLensShading() && checkNotNull(lensShading).all {
            it.isFinite() && it > 0f
        }
        if (!valid) return 0
        ensureIris26859BLensMapTexture()
        check(iris26859BLensMapTexture != 0 && iris26859BLensMapTexture in textures) {
            "26859 B LSC GPU map ownership lost before sampling"
        }
        if (iris26859BLensShadeProgram == 0) {
            iris26859BLensShadeProgram = linkProgram(
                lensShadeShader, "iris_26859_b_physical_lsc_once",
            )
        }
        val output = createTexture(outWidth, outHeight, GLES30.GL_RGBA16F, GLES30.GL_NEAREST)
        var complete = false
        try {
            val p=iris26859BLensShadeProgram
            GLES30.glUseProgram(p)
            bindTexture(p, "uSensorRgb", 0, input)
            bindTexture(p, "uLensShading", 1, iris26859BLensMapTexture)
            uniform2i(p, "uSize", outWidth, outHeight)
            uniform2i(p, "uOrigin", originX, originY)
            uniform2i(p, "uNativeSize", width, height)
            uniform1i(p, "uExpandedScale", expandedScale)
            draw(p, outWidth, outHeight, intArrayOf(output))
            GlesGpuScheduler.memoryBarrier()
            checkGlError("26859 B post-AMaZE sensor-linear optical LSC")
            complete = true
            return output
        } finally {
            if (!complete) releaseOwnedTexture(output,"26859 B failed lens shade output")
        }
    }

    private fun renderRawrLabDefringe26856(
        cameraLinearRgb: Int, cameraToSrgb: FloatArray, strength: Float,
        processingWidth: Int = width, processingHeight: Int = height,
    ): Int {
        check(cameraLinearRgb != 0 && cameraToSrgb.size == 9 && strength in 0f..1f)
        val limit = IntArray(1)
        GLES31.glGetIntegerv(GLES31.GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS, limit, 0)
        check(limit[0] >= 256) { "26856 RAWR Lab needs 256 compute invocations per workgroup" }
        val maxGroupX = IntArray(1)
        val maxGroupY = IntArray(1)
        GLES31.glGetIntegeri_v(GLES31.GL_MAX_COMPUTE_WORK_GROUP_SIZE, 0, maxGroupX, 0)
        GLES31.glGetIntegeri_v(GLES31.GL_MAX_COMPUTE_WORK_GROUP_SIZE, 1, maxGroupY, 0)
        check(maxGroupX[0] >= 256 && maxGroupY[0] >= 16) {
            "26856 RAWR Lab local workgroup exceeds device X/Y limits"
        }
        GLES31.glGetIntegerv(GLES31.GL_MAX_COMPUTE_SHARED_MEMORY_SIZE, limit, 0)
        check(limit[0] >= 16384) { "26856 RAWR Lab requires >=16KiB compute shared memory" }
        val assets = app.assets
        fun link(name: String): Int {
            val source = GlesIris26983COnLabDefringe.expandedShader(assets, name)
            // RAWR's unmodified 16x16 / 256-lane kernels exceed the GLES3.1
            // universal 128-lane baseline. They have been device-gated above.
            val shader = compileShader(GLES31.GL_COMPUTE_SHADER, source, "26856 RAWR $name")
            val program = GLES31.glCreateProgram()
            try {
                GLES31.glAttachShader(program, shader)
                GLES31.glLinkProgram(program)
            } finally {
                GLES31.glDeleteShader(shader)
            }
            val status = IntArray(1)
            GLES31.glGetProgramiv(program, GLES31.GL_LINK_STATUS, status, 0)
            if (status[0] == 0) {
                val log = GLES31.glGetProgramInfoLog(program)
                GLES31.glDeleteProgram(program)
                error("26856 RAWR Lab $name link failed: $log")
            }
            programs += program
            return program
        }
        if (iris26856LabPrepareProgram == 0) {
            iris26856LabPrepareProgram = link("lab_defringe_prepare.comp")
            iris26856LabReduceProgram = link("lab_defringe_reduce.comp")
            iris26856LabReconstructProgram = link("lab_defringe_reconstruct.comp")
        }
        val score = createTexture((processingWidth + 1) / 2, processingHeight, GLES30.GL_R32UI, GLES30.GL_NEAREST)
        val corrected = createTexture(processingWidth, processingHeight, GLES30.GL_RGBA16F, GLES30.GL_NEAREST)
        val bufferIds = IntArray(2)
        GLES31.glGenBuffers(2, bufferIds, 0)
        if (bufferIds[0] == 0 || bufferIds[1] == 0) {
            GLES31.glDeleteBuffers(2, bufferIds, 0)
            releaseOwnedTexture(score, "26856 RAWR Lab allocation failure score")
            releaseOwnedTexture(corrected, "26856 RAWR Lab allocation failure corrected")
            error("26856 RAWR Lab buffer allocation failed")
        }
        val groupsX = (processingWidth + 15) / 16
        val groupsY = (processingHeight + 15) / 16
        val statsBytes = (1L + groupsX.toLong() * groupsY.toLong()) * Float.SIZE_BYTES
        check(statsBytes in 4..Int.MAX_VALUE.toLong())
        val formerProgram = IntArray(1)
        GLES31.glGetIntegerv(GLES31.GL_CURRENT_PROGRAM, formerProgram, 0)
        var completed = false
        try {
            val params = GlesIris26983COnLabDefringe.parameters(processingWidth, processingHeight, strength, cameraToSrgb)
            GLES31.glBindBuffer(GLES31.GL_UNIFORM_BUFFER, bufferIds[0])
            GLES31.glBufferData(GLES31.GL_UNIFORM_BUFFER, params.capacity(), params, GLES31.GL_STREAM_DRAW)
            GLES31.glBindBufferBase(GLES31.GL_UNIFORM_BUFFER, 0, bufferIds[0])
            GLES31.glBindBuffer(GLES31.GL_SHADER_STORAGE_BUFFER, bufferIds[1])
            GLES31.glBufferData(GLES31.GL_SHADER_STORAGE_BUFFER, statsBytes.toInt(), null, GLES31.GL_DYNAMIC_DRAW)
            GLES31.glBindBufferBase(GLES31.GL_SHADER_STORAGE_BUFFER, 3, bufferIds[1])
            GLES31.glUseProgram(iris26856LabPrepareProgram)
            GLES31.glBindImageTexture(0, cameraLinearRgb, 0, false, 0,
                GLES31.GL_READ_ONLY, GLES30.GL_RGBA16F)
            GLES31.glBindImageTexture(1, score, 0, false, 0,
                GLES31.GL_WRITE_ONLY, GLES30.GL_R32UI)
            GLES31.glDispatchCompute(groupsX, groupsY, 1)
            GLES31.glMemoryBarrier(GLES31.GL_SHADER_IMAGE_ACCESS_BARRIER_BIT or
                GLES31.GL_SHADER_STORAGE_BARRIER_BIT)
            GLES31.glUseProgram(iris26856LabReduceProgram)
            GLES31.glDispatchCompute(1, 1, 1)
            GLES31.glMemoryBarrier(GLES31.GL_SHADER_STORAGE_BARRIER_BIT)
            GLES31.glUseProgram(iris26856LabReconstructProgram)
            GLES31.glBindImageTexture(0, score, 0, false, 0,
                GLES31.GL_READ_ONLY, GLES30.GL_R32UI)
            GLES31.glBindImageTexture(1, corrected, 0, false, 0,
                GLES31.GL_WRITE_ONLY, GLES30.GL_RGBA16F)
            GLES31.glBindImageTexture(2, cameraLinearRgb, 0, false, 0,
                GLES31.GL_READ_ONLY, GLES30.GL_RGBA16F)
            GLES31.glDispatchCompute(groupsX, groupsY, 1)
            GLES31.glMemoryBarrier(GLES31.GL_SHADER_IMAGE_ACCESS_BARRIER_BIT or
                GLES31.GL_TEXTURE_FETCH_BARRIER_BIT)
            checkGlError("26856 RAWR Lab prepare/reduce/reconstruct")
            completed = true
            return corrected
        } finally {
            GLES31.glBindImageTexture(0, 0, 0, false, 0, GLES31.GL_READ_ONLY, GLES30.GL_RGBA16F)
            GLES31.glBindImageTexture(1, 0, 0, false, 0, GLES31.GL_READ_ONLY, GLES30.GL_RGBA16F)
            GLES31.glBindImageTexture(2, 0, 0, false, 0, GLES31.GL_READ_ONLY, GLES30.GL_RGBA16F)
            GLES31.glBindBufferBase(GLES31.GL_UNIFORM_BUFFER, 0, 0)
            GLES31.glBindBufferBase(GLES31.GL_SHADER_STORAGE_BUFFER, 3, 0)
            GLES31.glBindBuffer(GLES31.GL_UNIFORM_BUFFER, 0)
            GLES31.glBindBuffer(GLES31.GL_SHADER_STORAGE_BUFFER, 0)
            GLES31.glDeleteBuffers(2, bufferIds, 0)
            GLES31.glUseProgram(formerProgram[0])
            releaseOwnedTexture(score, "26856 RAWR Lab R32UI packed outlier scores")
            if (!completed) releaseOwnedTexture(corrected, "26856 RAWR Lab aborted RGB output")
        }
    }

    private fun renderIris26932LkrMedian(input: Int, w: Int, h: Int, originalClip: Int, gains: FloatArray): Int {
        check(w == width*2 && h == height*2 && input != 0 &&
            originalClip!=0 && gains.size==3 && gains.all { it.isFinite() && it>0f } &&
            cfaPattern in 0..3) {
            "26937 RawLens median/physical sensor clipping escaped B SR ON 50MP route"
        }
        if (iris26932RawLensMedianProgram == 0) iris26932RawLensMedianProgram = linkProgram(
            GlesIris26983COnRawLensMedian.shader, "iris_26937_rawlens_median_plus_physical_clipped_white")
        val result=createTexture(w,h,GLES30.GL_RGBA16F,GLES30.GL_NEAREST)
        var success=false
        try {
            val program=iris26932RawLensMedianProgram
            GLES30.glUseProgram(program)
            bindTexture(program,"uLkrPostWbRgb",0,input)
            bindTexture(program,"uNativeSensorClip",1,originalClip)
            uniform2i(program,"uSize",w,h)
            uniform1i(program,"uBayerPattern",cfaPattern)
            GLES30.glUniform3f(GLES30.glGetUniformLocation(program,"uAmazeWb"),
                gains[0],gains[1],gains[2])
            draw(program,w,h,intArrayOf(result))
            GlesGpuScheduler.memoryBarrier()
            checkGlError("26932 RawLens LKR one-pass 3x3 chroma median")
            success=true
            return result
        } finally { if(!success)releaseOwnedTexture(result,"26932 rejected RawLens median") }
    }

    private fun createLensShadingTexture(): Int {
        val valid = hasLensShading()
        val textureWidth = if (valid) lensShadingWidth else 1
        val textureHeight = if (valid) lensShadingHeight else 1
        val values = FloatArray(textureWidth * textureHeight * 4) { 1f }
        if (valid) {
            val source = checkNotNull(lensShading)
            for (index in values.indices) {
                values[index] = source[index]
                    .takeIf { it.isFinite() && it > 0f } ?: 1f
            }
        }
        return createFloatTexture(
            width = textureWidth,
            height = textureHeight,
            internalFormat = GLES30.GL_RGBA16F,
            format = GLES30.GL_RGBA,
            values = values,
            filter = GLES30.GL_LINEAR,
        )
    }

    private fun hasLensShading(): Boolean = lensShading != null &&
        lensShadingWidth > 0 &&
        lensShadingHeight > 0 &&
        lensShading.size >= lensShadingWidth * lensShadingHeight * 4

    private fun allocateTexture(spec: TextureSpec): Int {
        val ids = IntArray(1)
        GLES30.glGenTextures(1, ids, 0)
        val texture = ids[0]
        check(texture != 0) { "glGenTextures returned 0" }
        textures += texture
        textureSpecs[texture] = spec
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, texture)
        GLES30.glTexParameteri(
            GLES30.GL_TEXTURE_2D,
            GLES30.GL_TEXTURE_MIN_FILTER,
            spec.filter,
        )
        GLES30.glTexParameteri(
            GLES30.GL_TEXTURE_2D,
            GLES30.GL_TEXTURE_MAG_FILTER,
            spec.filter,
        )
        GLES30.glTexParameteri(
            GLES30.GL_TEXTURE_2D,
            GLES30.GL_TEXTURE_WRAP_S,
            GLES30.GL_CLAMP_TO_EDGE,
        )
        GLES30.glTexParameteri(
            GLES30.GL_TEXTURE_2D,
            GLES30.GL_TEXTURE_WRAP_T,
            GLES30.GL_CLAMP_TO_EDGE,
        )
        GLES30.glTexStorage2D(
            GLES30.GL_TEXTURE_2D,
            1,
            spec.internalFormat,
            spec.width,
            spec.height,
        )
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, 0)
        checkGlError("create texture ${spec.width}x${spec.height}")
        return texture
    }

    private fun createFloatTexture(
        width: Int,
        height: Int,
        internalFormat: Int,
        format: Int,
        values: FloatArray,
        filter: Int,
    ): Int {
        val buffer = ByteBuffer.allocateDirect(values.size * Float.SIZE_BYTES)
            .order(ByteOrder.nativeOrder())
            .asFloatBuffer()
            .apply {
                put(values)
                rewind()
            }
        val texture = createTexture(
            textureWidth = width,
            textureHeight = height,
            internalFormat = internalFormat,
            filter = filter,
        )
        GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER, 0)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, texture)
        GLES30.glTexSubImage2D(
            GLES30.GL_TEXTURE_2D,
            0,
            0,
            0,
            width,
            height,
            format,
            GLES30.GL_FLOAT,
            buffer,
        )
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, 0)
        checkGlError("create float texture ${width}x$height")
        return texture
    }

    private fun createFramebuffer(): Int {
        val ids = IntArray(1)
        GLES30.glGenFramebuffers(1, ids, 0)
        check(ids[0] != 0) { "glGenFramebuffers returned 0" }
        framebuffers += ids[0]
        return ids[0]
    }

    private fun draw(
        program: Int,
        viewportWidth: Int,
        viewportHeight: Int,
        targets: IntArray,
        preserveBlend: Boolean = false,
    ) {
        bindRenderTargets(targets, "program $program")
        GLES30.glViewport(0, 0, viewportWidth, viewportHeight)
        if (!preserveBlend) GLES30.glDisable(GLES30.GL_BLEND)
        GLES30.glUseProgram(program)
        GLES30.glDrawArrays(GLES30.GL_TRIANGLES, 0, 3)
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
        checkGlError("draw program $program")
    }

    private fun releaseOwnedTexture(texture: Int, label: String) {
        if (texture == 0) return
        check(textures.remove(texture)) { "$label texture=$texture is not owned" }
        textureSpecs.remove(texture)
        GLES30.glDeleteTextures(1, intArrayOf(texture), 0)
        checkGlError("release $label")
    }

    private fun bindRenderTargets(targets: IntArray, label: String) {
        require(targets.isNotEmpty())
        val targetSpecs = targets.map { texture ->
            checkNotNull(textureSpecs[texture]) {
                "$label target texture $texture is not owned by the Spatial stacker"
            }
        }
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, renderFbo)
        val attachments = IntArray(targets.size)
        for (index in targets.indices) {
            val attachment = GLES30.GL_COLOR_ATTACHMENT0 + index
            attachments[index] = attachment
            GLES30.glFramebufferTexture2D(
                GLES30.GL_FRAMEBUFFER,
                attachment,
                GLES30.GL_TEXTURE_2D,
                targets[index],
                0,
            )
        }
        // A framebuffer retains attachments that are not explicitly replaced. Bento writes three
        // half-resolution masks, while the following SpatialMerge draw writes two full-resolution
        // accumulators. Leaving COLOR_ATTACHMENT2 attached makes the framebuffer dimensions the
        // intersection of both sizes on Adreno, clipping the merge to one quarter of the image.
        for (index in targets.size until renderTargetAttachmentCount) {
            GLES30.glFramebufferTexture2D(
                GLES30.GL_FRAMEBUFFER,
                GLES30.GL_COLOR_ATTACHMENT0 + index,
                GLES30.GL_TEXTURE_2D,
                0,
                0,
            )
        }
        renderTargetAttachmentCount = targets.size
        GLES30.glDrawBuffers(attachments.size, attachments, 0)
        // Completeness is a property of these immutable attachment specifications. Validate each
        // format/size combination once instead of forcing driver validation in every hot pass.
        if (validatedRenderTargetSpecs.add(targetSpecs)) {
            val status = GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)
            check(status == GLES30.GL_FRAMEBUFFER_COMPLETE) {
                "$label framebuffer incomplete: 0x${status.toString(16)}"
            }
        }
    }

    private fun bindTexture(program: Int, name: String, unit: Int, texture: Int) {
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + unit)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, texture)
        GLES30.glUniform1i(uniformLocation(program, name), unit)
    }

    private fun uniform1i(program: Int, name: String, value: Int) {
        GLES30.glUniform1i(uniformLocation(program, name), value)
    }

    private fun uniform2i(program: Int, name: String, x: Int, y: Int) {
        GLES30.glUniform2i(uniformLocation(program, name), x, y)
    }

    private fun uniformLocation(program: Int, name: String): Int {
        val locations = uniformLocations.getOrPut(program) { HashMap() }
        return locations.getOrPut(name) { GLES30.glGetUniformLocation(program, name) }
    }

    private fun linkProgram(fragmentSource: String, name: String): Int {
        val vertexSource=GlesGraphicsShaderSources.fullscreenVertexFor(fragmentSource)
        val vertex=compileShader(GLES30.GL_VERTEX_SHADER,vertexSource,"$name vertex")
        var fragment=0;var program=0;var handedOff=false
        try {
            fragment=compileShader(GLES30.GL_FRAGMENT_SHADER,fragmentSource,"$name fragment")
            program=GLES30.glCreateProgram()
            check(program!=0) { "$name program allocation failed" }
            GLES30.glAttachShader(program,vertex)
            GLES30.glAttachShader(program,fragment)
            GLES30.glLinkProgram(program)
            val status=IntArray(1)
            GLES30.glGetProgramiv(program,GLES30.GL_LINK_STATUS,status,0)
            check(status[0]!=0) { "$name link failed: ${GLES30.glGetProgramInfoLog(program)}" }
            programs += program; handedOff=true
            return program
        } finally {
            GLES30.glDeleteShader(vertex)
            if(fragment!=0) GLES30.glDeleteShader(fragment)
            if(!handedOff && program!=0) GLES30.glDeleteProgram(program)
        }
    }

    private fun compileShader(type: Int, source: String, name: String): Int {
        val shader=GLES30.glCreateShader(type)
        check(shader!=0) { "$name shader allocation failed" }
        var handedOff=false
        try {
            GLES30.glShaderSource(shader,source)
            GLES30.glCompileShader(shader)
            val status=IntArray(1)
            GLES30.glGetShaderiv(shader,GLES30.GL_COMPILE_STATUS,status,0)
            check(status[0]!=0) { "$name compile failed: ${GLES30.glGetShaderInfoLog(shader)}" }
            handedOff=true
            return shader
        } finally { if(!handedOff) GLES30.glDeleteShader(shader) }
    }

    private fun applyRawRenderState() {
        GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
        GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER, 0)
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
        GLES30.glDisable(GLES30.GL_BLEND)
        GLES30.glDisable(GLES30.GL_DITHER)
        GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
        GLES30.glDisable(GLES30.GL_DEPTH_TEST)
        GLES30.glDisable(GLES30.GL_STENCIL_TEST)
        GLES30.glDisable(GLES30.GL_CULL_FACE)
    }

    private fun checkGlError(label: String) {
        var error = GLES30.glGetError()
        if (error == GLES30.GL_NO_ERROR) return
        val first = error
        while (error != GLES30.GL_NO_ERROR) {
            error = GLES30.glGetError()
        }
        throw IllegalStateException("$label GL error: 0x${first.toString(16)}")
    }

    private fun copyPersistentTexture(source: Int, w: Int, h: Int): Int {
        val destination=allocateTexture(TextureSpec(w,h,GLES30.GL_RGBA16F,GLES30.GL_NEAREST))
        bindRenderTargets(intArrayOf(source),"26983 C ON independent bridge source")
        GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER,0)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,destination)
        GLES30.glCopyTexSubImage2D(GLES30.GL_TEXTURE_2D,0,0,0,0,0,w,h)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,0)
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,0)
        checkGlError("26983 C ON independent bridge copy")
        return destination
    }

    private fun createTexture(textureWidth: Int,textureHeight: Int,internalFormat: Int,filter: Int): Int =
        allocateTexture(TextureSpec(textureWidth,textureHeight,internalFormat,filter))

    private val lensShadeShader = """
        #version 300 es
        precision highp float;
        uniform sampler2D uSensorRgb;
        uniform sampler2D uLensShading;
        uniform ivec2 uSize;
        uniform ivec2 uOrigin;
        uniform ivec2 uNativeSize;
        uniform int uExpandedScale;
        layout(location=0) out vec4 oRgb;
        void main(){
            ivec2 p=clamp(ivec2(gl_FragCoord.xy),ivec2(0),uSize-ivec2(1));
            vec4 rgba=texelFetch(uSensorRgb,p,0);
            vec2 nativeUv=(vec2(uOrigin+p)+vec2(0.5))/
                (vec2(uNativeSize)*float(uExpandedScale));
            vec4 gains=texture(uLensShading,nativeUv);
            vec3 physical=vec3(gains.r,0.5*(gains.g+gains.b),gains.a);
            oRgb=vec4(rgba.rgb*physical,rgba.a);
        }
    """.trimIndent()
    private val iris26876DerivedGuideShader = """#version 300 es
        precision highp float;
        precision highp sampler2D;
        uniform sampler2D uTwoXLinear;
        uniform sampler2D uTwoXOriginalClip;
        uniform ivec2 uOneXExtent;
        layout(location=0) out vec4 oLinear;
        layout(location=1) out float oClipCoverage;
        void main() {
            ivec2 q=clamp(ivec2(gl_FragCoord.xy),ivec2(0),uOneXExtent-1)*2;
            vec4 a=texelFetch(uTwoXLinear,q,0);
            vec4 b=texelFetch(uTwoXLinear,q+ivec2(1,0),0);
            vec4 c=texelFetch(uTwoXLinear,q+ivec2(0,1),0);
            vec4 d=texelFetch(uTwoXLinear,q+ivec2(1,1),0);
            oLinear=vec4(0.25*(a.rgb+b.rgb+c.rgb+d.rgb),1.0);
            float ca=texelFetch(uTwoXOriginalClip,q,0).r;
            float cb=texelFetch(uTwoXOriginalClip,q+ivec2(1,0),0).r;
            float cc=texelFetch(uTwoXOriginalClip,q+ivec2(0,1),0).r;
            float cd=texelFetch(uTwoXOriginalClip,q+ivec2(1,1),0).r;
            oClipCoverage=clamp(0.25*(ca+cb+cc+cd),0.0,1.0);
        }
    """.trimIndent()
}
