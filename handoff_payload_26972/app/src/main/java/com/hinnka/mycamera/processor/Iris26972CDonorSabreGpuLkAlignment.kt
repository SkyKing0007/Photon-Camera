package com.hinnka.mycamera.processor

import android.opengl.EGL14
import android.opengl.EGLContext
import android.opengl.GLES30
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.ceil
import kotlin.math.floor

/**
 * C-owned multi-scale actual (nonzero-flow) Lucas–Kanade and AlignAlt.
 * Operates only on the real signed-S16 donor gray pyramids, with cached reference
 * Hessian and current-frame residual; it performs 3 coarse / 2 fine iterations,
 * a donor 3-neighbor + measured global candidate at each pyramid transition, and
 * a final shifted, 16-RAW-pixel merge-grid AlignAlt without median filtering.
 *
 * Source equations are from pinned bjzhou 1.29.0 GlesMgcRawSpatialStacker and
 * GlesMgcRawSpatialShaders. This stage is isolated from A/B; it still requires
 * actual Android driver/shader tests and C burst producer, and is not active.
 */
internal object Iris26972CDonorSabreGpuLkAlignment {
    private const val COMPONENT="26972 C donor multi-scale Lucas-Kanade"
    private const val MERGE_TILE_RAW = 16
    private const val MERGE_TILE_QUADS = MERGE_TILE_RAW / 2
    private val gl = Iris26972CDonorSabreGpuMerge

    internal data class Plan(
        val reference:Iris26972CDonorSabreGpuGrayPyramid.Result,
        val current:Iris26972CDonorSabreGpuGrayPyramid.Result,
        val frameIndex:Int,
        val frozenReferenceSnr:Float,
    )
    internal class Result private constructor(
        val sparseLkTexture:Int,
        val finalGridWidth:Int,
        val finalGridHeight:Int,
        val rawWidth:Int,
        val rawHeight:Int,
        val frameIndex:Int,
        private val context:EGLContext,
    ):AutoCloseable {
        private var closed=false
        internal fun requireOwner(){
            check(!closed && context!=EGL14.EGL_NO_CONTEXT &&
                EGL14.eglGetCurrentContext()==context){"$COMPONENT wrong owner/released"}
        }
        override fun close(){
            requireOwner()
            GLES30.glDeleteTextures(1,intArrayOf(sparseLkTexture),0)
            closed=true
        }
        internal companion object {
            fun owned(texture:Int,width:Int,height:Int,plan:Plan)=Result(
                texture,width,height,plan.reference.rawWidth,plan.reference.rawHeight,
                plan.frameIndex,EGL14.eglGetCurrentContext())
        }
    }

    private data class Flow(
        val texture:Int, val gridWidth:Int,val gridHeight:Int,
        val tileStride:Int,val scale:Int,val gridMin:Int,
    )

    internal fun validate(plan:Plan) {
        plan.reference.requireOwner()
        plan.current.requireOwner()
        require(plan.frameIndex in 1..49 &&
            plan.frozenReferenceSnr.isFinite() && plan.frozenReferenceSnr>=0f &&
            plan.reference.rawWidth==plan.current.rawWidth &&
            plan.reference.rawHeight==plan.current.rawHeight &&
            plan.reference.maximumTileSize==plan.current.maximumTileSize &&
            plan.reference.levels.size==plan.current.levels.size &&
            plan.reference.levels.isNotEmpty()){
            "$COMPONENT requires frozen matching NORMAL reference/current RAW pyramids"
        }
        plan.reference.levels.zip(plan.current.levels).forEach { (a,b) ->
            require(a.width==b.width && a.height==b.height &&
                a.tileSize==b.tileSize && a.gridWidth==b.gridWidth &&
                a.gridHeight==b.gridHeight && a.scale==b.scale &&
                a.texture>0 && b.texture>0 && a.texture!=b.texture){
                "$COMPONENT invalid or aliased signed-S16 level"
            }
        }
    }

    internal fun solve(plan:Plan):Result {
        validate(plan)
        gl.requireCurrentContext()
        require(gl.glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS)>=4 &&
            gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE)>=
                maxOf(plan.reference.rawWidth/2,plan.reference.rawHeight/2)){
            "$COMPONENT requires four shader samplers and complete RAW gray frame"
        }
        gl.checkGl("before donor C Lucas-Kanade")
        val saved=Iris26972CDonorSabreGpuMerge.GlState.capture()
        val scratch=ArrayList<Int>()
        val programs=IntArray(3)
        var frameBuffer=0;var vertex=0;var result=0;var success=false
        // Readback is a genuine reduction of measured LK, never a guessed zero/global flow.
        val savedPackBuffer=gl.glInt(GLES30.GL_PIXEL_PACK_BUFFER_BINDING)
        val savedPackAlignment=gl.glInt(GLES30.GL_PACK_ALIGNMENT)
        val savedPackRowLength=gl.glInt(GLES30.GL_PACK_ROW_LENGTH)
        try {
            programs[0]=gl.compileProgram(gl.VERTEX,Iris26972CDonorSabreLkAlignmentShaders.gradientProducts)
            programs[1]=gl.compileProgram(gl.VERTEX,Iris26972CDonorSabreLkAlignmentShaders.blockLucasKanade)
            programs[2]=gl.compileProgram(gl.VERTEX,Iris26972CDonorSabreLkAlignmentShaders.upsampleAlignment)
            val ids=IntArray(1)
            GLES30.glGenFramebuffers(1,ids,0);frameBuffer=ids[0]
            GLES30.glGenVertexArrays(1,ids,0);vertex=ids[0]
            check(frameBuffer>0 && vertex>0){"$COMPONENT GL framebuffer/VAO missing"}
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,frameBuffer)
            GLES30.glBindVertexArray(vertex)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glDisable(GLES30.GL_BLEND)
            GLES30.glColorMask(true,true,true,true)

            fun loc(program:Int,name:String):Int=GLES30.glGetUniformLocation(program,name).also{
                check(it>=0){"$COMPONENT donor program missing $name"}
            }
            fun bind(program:Int,name:String,unit:Int,texture:Int){
                check(texture>0){"$COMPONENT missing $name"}
                GLES30.glActiveTexture(GLES30.GL_TEXTURE0+unit)
                GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,texture)
                GLES30.glUniform1i(loc(program,name),unit)
            }
            fun alloc(w:Int,h:Int):Int {
                check(w in 1..gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE) &&
                    h in 1..gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE)){
                    "$COMPONENT invalid intermediate grid dimensions"
                }
                GLES30.glGenTextures(1,ids,0)
                val id=ids[0]
                check(id>0 && id !in scratch &&
                    plan.reference.levels.none{it.texture==id} &&
                    plan.current.levels.none{it.texture==id}){
                    "$COMPONENT allocation alias"
                }
                scratch+=id
                GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
                GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,id)
                for(p in intArrayOf(GLES30.GL_TEXTURE_MIN_FILTER,GLES30.GL_TEXTURE_MAG_FILTER))
                    GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,p,GLES30.GL_NEAREST)
                for(p in intArrayOf(GLES30.GL_TEXTURE_WRAP_S,GLES30.GL_TEXTURE_WRAP_T))
                    GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,p,GLES30.GL_CLAMP_TO_EDGE)
                GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,GLES30.GL_RGBA32F,
                    w,h,0,GLES30.GL_RGBA,GLES30.GL_FLOAT,null)
                gl.checkGl("C LK RGBA32F allocation")
                return id
            }
            fun render(texture:Int,w:Int,h:Int,label:String){
                GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,frameBuffer)
                GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT0,
                    GLES30.GL_TEXTURE_2D,texture,0)
                GLES30.glDrawBuffers(1,intArrayOf(GLES30.GL_COLOR_ATTACHMENT0),0)
                check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)==
                    GLES30.GL_FRAMEBUFFER_COMPLETE){"$COMPONENT $label RGBA32F render target unavailable"}
                GLES30.glViewport(0,0,w,h)
                GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3)
                gl.checkGl("C donor LK $label")
            }
            fun estimateGlobal(flow:Flow):FloatArray {
                val count=flow.gridWidth.toLong()*flow.gridHeight
                require(count in 1..1_000_000){"$COMPONENT unsupported histogram grid"}
                val data=ByteBuffer.allocateDirect((count*16).toInt()).order(ByteOrder.nativeOrder())
                GLES30.glBindFramebuffer(GLES30.GL_READ_FRAMEBUFFER,frameBuffer)
                GLES30.glFramebufferTexture2D(GLES30.GL_READ_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT0,
                    GLES30.GL_TEXTURE_2D,flow.texture,0)
                check(GLES30.glCheckFramebufferStatus(GLES30.GL_READ_FRAMEBUFFER)==
                    GLES30.GL_FRAMEBUFFER_COMPLETE){"$COMPONENT histogram source not readable"}
                GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER,0)
                GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,4)
                GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH,0)
                GLES30.glReadPixels(0,0,flow.gridWidth,flow.gridHeight,
                    GLES30.GL_RGBA,GLES30.GL_FLOAT,data)
                gl.checkGl("C donor global alignment readback")
                val values=data.asFloatBuffer()
                val histogram=IntArray(129*129)
                var sumX=0L;var sumY=0L
                for (i in 0 until count.toInt()){
                    val x=values.get(i*4);val y=values.get(i*4+1)
                    check(x.isFinite() && y.isFinite()){
                        "$COMPONENT nonfinite true LK field"
                    }
                    fun roundAway(value:Float):Int=if(value>=0f)
                        floor(value.toDouble()+.5).toInt() else ceil(value.toDouble()-.5).toInt()
                    val bx=roundAway(x).coerceIn(-64,64)
                    val by=roundAway(y).coerceIn(-64,64)
                    histogram[(by+64)*129+bx+64]++
                    sumX+=bx;sumY+=by
                }
                var peak=0;var peakX=-64;var peakY=-64
                for(by in -64..64)for(bx in -64..64){
                    val n=histogram[(by+64)*129+bx+64]
                    if(n>peak){peak=n;peakX=bx;peakY=by}
                }
                return if(peak>=10)floatArrayOf(peakX.toFloat(),peakY.toFloat()) else
                    floatArrayOf(sumX.toFloat()/count,sumY.toFloat()/count)
            }
            fun upsample(
                reference:Iris26972CDonorSabreGpuGrayPyramid.Level,
                current:Iris26972CDonorSabreGpuGrayPyramid.Level,
                input:Flow,targetWidth:Int,targetHeight:Int,targetStride:Int,
                targetTileSize:Int,targetMin:Int,offsetX:Int,offsetY:Int,
                global:Boolean,
            ):Flow {
                val scale=input.scale.toFloat()/reference.scale.toFloat()
                check(scale.isFinite() && scale>0f && targetTileSize in 1..64)
                val candidate=if(global)estimateGlobal(input) else floatArrayOf(0f,0f)
                val output=alloc(targetWidth,targetHeight)
                val program=programs[2]
                GLES30.glUseProgram(program)
                bind(program,"uReference",0,reference.texture)
                bind(program,"uCurrent",1,current.texture)
                bind(program,"uInitialAlignment",2,input.texture)
                GLES30.glUniform2i(loc(program,"uImageSize"),reference.width,reference.height)
                GLES30.glUniform2i(loc(program,"uInitialGridSize"),input.gridWidth,input.gridHeight)
                GLES30.glUniform1i(loc(program,"uInitialGridMin"),input.gridMin)
                GLES30.glUniform1i(loc(program,"uTargetGridMin"),targetMin)
                GLES30.glUniform1i(loc(program,"uInitialTileStride"),input.tileStride)
                GLES30.glUniform1i(loc(program,"uTargetTileStride"),targetStride)
                GLES30.glUniform1i(loc(program,"uTargetTileSize"),targetTileSize)
                GLES30.glUniform2i(loc(program,"uTargetImageOffset"),offsetX,offsetY)
                GLES30.glUniform1f(loc(program,"uInitialScale"),scale)
                GLES30.glUniform1i(loc(program,"uHasGlobalCandidate"),if(global)1 else 0)
                GLES30.glUniform2f(loc(program,"uGlobalCandidate"),candidate[0],candidate[1])
                render(output,targetWidth,targetHeight,"AlignAlt")
                return Flow(output,targetWidth,targetHeight,targetStride,reference.scale,targetMin)
            }
            fun lkLevel(
                reference:Iris26972CDonorSabreGpuGrayPyramid.Level,
                current:Iris26972CDonorSabreGpuGrayPyramid.Level,
                initial:Flow?,fine:Boolean,
            ):Flow {
                val product=alloc(reference.gridWidth,reference.gridHeight)
                val gradient=programs[0]
                GLES30.glUseProgram(gradient)
                bind(gradient,"uReference",0,reference.texture)
                GLES30.glUniform2i(loc(gradient,"uImageSize"),reference.width,reference.height)
                GLES30.glUniform1i(loc(gradient,"uTileStride"),reference.tileSize)
                GLES30.glUniform1i(loc(gradient,"uTileSize"),reference.tileSize)
                render(product,reference.gridWidth,reference.gridHeight,"gradient products")
                var flow=initial
                val lk=programs[1]
                repeat(if(fine)2 else 3){
                    val output=alloc(reference.gridWidth,reference.gridHeight)
                    GLES30.glUseProgram(lk)
                    bind(lk,"uReference",0,reference.texture)
                    bind(lk,"uCurrent",1,current.texture)
                    bind(lk,"uProducts0",2,product)
                    // The first iteration has no initial alignment; no fake initial motion.
                    bind(lk,"uInitialAlignment",3,flow?.texture?:product)
                    GLES30.glUniform2i(loc(lk,"uImageSize"),reference.width,reference.height)
                    GLES30.glUniform2i(loc(lk,"uGridSize"),reference.gridWidth,reference.gridHeight)
                    GLES30.glUniform1i(loc(lk,"uTileStride"),reference.tileSize)
                    GLES30.glUniform1i(loc(lk,"uTileSize"),reference.tileSize)
                    GLES30.glUniform1i(loc(lk,"uNormalize"),if(fine)0 else 1)
                    GLES30.glUniform1i(loc(lk,"uHasInitialAlignment"),if(flow==null)0 else 1)
                    render(output,reference.gridWidth,reference.gridHeight,"Lucas-Kanade")
                    flow=Flow(output,reference.gridWidth,reference.gridHeight,
                        reference.tileSize,reference.scale,1)
                }
                return checkNotNull(flow)
            }
            val references=plan.reference.levels
            val currents=plan.current.levels
            var flow:Flow?=null
            for (i in references.lastIndex downTo 0) {
                val reference=references[i]
                val current=currents[i]
                val initial=if(flow==null) null else upsample(
                    reference,current,checkNotNull(flow),reference.gridWidth,
                    reference.gridHeight,reference.tileSize,reference.tileSize,1,0,0,true)
                flow=lkLevel(reference,current,initial,i==0)
            }
            val support=Iris26972CDonorSabreAlignmentOffset.tileSupport(plan.frozenReferenceSnr)
            val finalSupport=minOf(MERGE_TILE_RAW,support)
            val inset=(support-finalSupport)/2
            val offset=Iris26972CDonorSabreAlignmentOffset.forFrame(
                plan.frameIndex,MERGE_TILE_QUADS)
            val gridW=(plan.reference.rawWidth+MERGE_TILE_RAW-1)/MERGE_TILE_RAW
            val gridH=(plan.reference.rawHeight+MERGE_TILE_RAW-1)/MERGE_TILE_RAW
            val final=upsample(references[0],currents[0],checkNotNull(flow),
                gridW,gridH,MERGE_TILE_QUADS,finalSupport,0,
                offset.x-inset,offset.y-inset,false)
            result=final.texture
            success=true
            return Result.owned(result,gridW,gridH,plan)
        }finally{
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER,savedPackBuffer)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,savedPackAlignment)
            GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH,savedPackRowLength)
            for(program in programs)if(program>0)GLES30.glDeleteProgram(program)
            if(vertex>0)GLES30.glDeleteVertexArrays(1,intArrayOf(vertex),0)
            if(frameBuffer>0)GLES30.glDeleteFramebuffers(1,intArrayOf(frameBuffer),0)
            val garbage=if(success)scratch.filter{it!=result} else scratch
            if(garbage.isNotEmpty())GLES30.glDeleteTextures(garbage.size,garbage.toIntArray(),0)
            saved.restore()
        }
    }

    /** Return only a measured C flow, never an identity-flow substitute or A/B adapter. */
    internal fun solveAndConvert(plan:Plan):Iris26972CDonorSabreGpuConvertedFlow.Result {
        val sparse=solve(plan)
        try {
            sparse.requireOwner()
            return Iris26972CDonorSabreGpuConvertedFlow.convert(
                Iris26972CDonorSabreGpuConvertedFlow.Plan(
                    rawWidth=sparse.rawWidth,rawHeight=sparse.rawHeight,
                    sparseLkTexture=sparse.sparseLkTexture,
                    finalGridWidth=sparse.finalGridWidth,
                    finalGridHeight=sparse.finalGridHeight,
                    frameIndex=sparse.frameIndex))
        }finally { sparse.close() }
    }
}
