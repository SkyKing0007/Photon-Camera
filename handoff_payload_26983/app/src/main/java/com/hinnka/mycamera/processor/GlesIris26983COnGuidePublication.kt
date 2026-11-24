package com.hinnka.mycamera.processor

import android.opengl.GLES30
import com.hinnka.mycamera.utils.LargeDirectBuffer
import com.particlesdevs.photoncamera.processing.processor.Iris26983COnRgba16fCarrier
import java.nio.ByteBuffer
import java.nio.ByteOrder

/** C SR ON exact Motion primary + sidecar + selected 1x guide transport.
 * No C OFF MGC tuning, secondary residual MGC denoise, CPU 50MP readback,
 * A/B carrier types or image files. Caller retains GpuMerge.Result, including
 * 2x carrier, until final renderer is done. All readbacks are native 1x only.
 */
internal object GlesIris26983COnGuidePublication {
    class LinearTransport internal constructor(
        shared: Iris26983COnRgba16fCarrier?,
        fallback: ByteBuffer?,
    ): AutoCloseable {
        private var sharedOwner = shared
        private var fallbackOwner = fallback
        private var closed=false
        init { require((shared!=null) xor (fallback!=null)) }
        /** The receiving operation MUST take ownership on invocation, including rejection. */
        fun <T> consume(block: (ByteBuffer?, Iris26983COnRgba16fCarrier?) -> T): T {
            check(!closed)
            val shared = sharedOwner
            val fallback = fallbackOwner
            check((shared!=null) xor (fallback!=null))
            closed=true
            sharedOwner=null; fallbackOwner=null
            return block(fallback,shared)
        }
        override fun close() {
            if(closed) return
            closed=true
            val shared=sharedOwner; val fallback=fallbackOwner
            sharedOwner=null; fallbackOwner=null
            try { shared?.close() } finally { LargeDirectBuffer.free(fallback) }
        }
    }
    class Prepared internal constructor(
        val primary: LinearTransport,
        val sidecar: LinearTransport,
        val final1x: Iris26983COnRgba16fCarrier,
    ): AutoCloseable {
        private var closed=false
        override fun close() {
            if(closed) return
            closed=true
            try { final1x.close() } finally {
                try { primary.close() } finally { sidecar.close() }
            }
        }
    }
    fun prepare(merge: GlesIris26983COnGpuMerge.Result, w: Int, h: Int): Prepared {
        merge.assertUsable()
        require(w>1 && h>1 && merge.true2x.width==Math.multiplyExact(w,2) &&
                merge.true2x.height==Math.multiplyExact(h,2))
        require(w.toLong()*h*8L<=Int.MAX_VALUE)
        GLES30.glFinish()
        var sidecar: LinearTransport?=null
        var primary: LinearTransport?=null
        var pendingShared: Iris26983COnRgba16fCarrier?=null
        var pendingFallback: ByteBuffer?=null
        var final1x: Iris26983COnRgba16fCarrier?=null
        var done=false
        try {
            // Original B sidecar copies color unchanged; separate primary
            // gets the original forceOpaqueHalfAlpha before final guide pack.
            sidecar=copySidecar(merge.oneXSensorRgb,w,h)
            var shared=Iris26983COnRgba16fCarrier.tryCreate(w,h)
            pendingShared=shared
            val mapped=if(shared!=null && shared.copyFromCurrentGlTexture(merge.bridgeRgb)) shared.lockCpu() else null
            val rgba: ByteBuffer
            if(shared!=null && mapped!=null && mapped.capacity().toLong()==shared.expectedBytes()) {
                rgba=mapped
            } else {
                shared?.close(); pendingShared=null; shared=null
                rgba=readHalf(merge.bridgeRgb,w,h,false)
                pendingFallback=rgba
            }
            forceOpaqueHalfAlpha(rgba,w,h)
            final1x=packFinalGuide(rgba,merge.oneXClip,w,h)
            if(shared!=null) check(shared.unlockCpu()) { "26983 C ON primary CPU unlock failed" }
            primary=LinearTransport(shared,pendingFallback)
            pendingShared=null; pendingFallback=null
            val out=Prepared(primary,sidecar,final1x)
            done=true
            return out
        } finally {
            if(!done) {
                try { final1x?.close() } finally {
                    try { primary?.close() } finally {
                        try { sidecar?.close() } finally {
                            try { pendingShared?.close() } finally { LargeDirectBuffer.free(pendingFallback) }
                        }
                    }
                }
            }
        }
    }
    private fun copySidecar(texture: Int,w: Int,h: Int): LinearTransport {
        val shared=Iris26983COnRgba16fCarrier.tryCreate(w,h)
        var handedOff=false
        try {
            if(shared!=null && shared.copyFromCurrentGlTexture(texture)) {
                val out=LinearTransport(shared,null); handedOff=true; return out
            }
            return LinearTransport(null,readHalf(texture,w,h,false))
        } finally { if(!handedOff) shared?.close() }
    }
    private fun packFinalGuide(rgba: ByteBuffer, maskTexture: Int,w: Int,h: Int): Iris26983COnRgba16fCarrier {
        val pixels=w.toLong()*h
        require(maskTexture>0 && rgba.isDirect && rgba.capacity().toLong()==pixels*8L)
        val sensorMask=readHalf(maskTexture,w,h,true)
        var owner: Iris26983COnRgba16fCarrier?=null
        var handedOff=false
        try {
            check(sensorMask.isDirect && sensorMask.capacity().toLong()==pixels*2L)
            val next=Iris26983COnRgba16fCarrier.tryCreateFinal1xGuide(w,h)
                ?: error("26983 C ON 1x final guide hardware buffer unavailable")
            owner=next
            check(next.writeFinal1xGuideCpu(rgba,sensorMask)) { "26983 C ON 1x stride-aware guide pack failed" }
            handedOff=true
            return next
        } finally {
            LargeDirectBuffer.free(sensorMask)
            if(!handedOff) owner?.close()
        }
    }
    // Same half-alpha word and RGB-preserving loop as the successful B bridge.
    internal fun forceOpaqueHalfAlpha(buffer: ByteBuffer,width: Int,height: Int) {
        val shorts=buffer.duplicate().order(ByteOrder.nativeOrder()).apply { position(0) }.asShortBuffer()
        val pixels=width*height
        require(shorts.capacity()>=pixels*4)
        for(pixel in 0 until pixels) shorts.put(pixel*4+3,0x3c00.toShort())
        buffer.position(0)
    }
    private fun readHalf(texture: Int,w: Int,h: Int,mask: Boolean): ByteBuffer {
        require(texture>0 && w>1 && h>1)
        val bytes=w.toLong()*h*(if(mask) 2L else 8L)
        val output=LargeDirectBuffer.allocate(bytes,"26983 C ON exact 1x transport")
            ?: error("26983 C ON unable to allocate 1x transport")
        val fbo=IntArray(1)
        try {
            GLES30.glGenFramebuffers(1,fbo,0)
            check(fbo[0]!=0)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER,0)
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,fbo[0])
            GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT0,GLES30.GL_TEXTURE_2D,texture,0)
            check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)==GLES30.GL_FRAMEBUFFER_COMPLETE)
            GLES30.glReadBuffer(GLES30.GL_COLOR_ATTACHMENT0)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,if(mask) 2 else 8)
            output.position(0)
            GLES30.glReadPixels(0,0,w,h,if(mask) GLES30.GL_RED else GLES30.GL_RGBA,GLES30.GL_HALF_FLOAT,output)
            check(GLES30.glGetError()==GLES30.GL_NO_ERROR) { "26983 C ON 1x readback failed" }
            output.position(0)
            return output
        } catch(t: Throwable) {
            LargeDirectBuffer.free(output); throw t
        } finally {
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,1)
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,0)
            if(fbo[0]!=0) GLES30.glDeleteFramebuffers(1,fbo,0)
        }
    }
}
