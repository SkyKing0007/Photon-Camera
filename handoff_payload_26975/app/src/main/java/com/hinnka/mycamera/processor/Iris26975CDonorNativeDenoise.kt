package com.hinnka.mycamera.processor

import android.content.Context
import android.opengl.EGL14
import android.opengl.GLES30
import com.hinnka.mycamera.raw.Iris26975CIndependentDenoise
import com.hinnka.mycamera.processor.experimentc.Iris26975CSabreDenoiseMetadata
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract
import java.io.File
import java.io.RandomAccessFile
import java.nio.ByteOrder
import java.nio.channels.FileChannel
import java.util.UUID

/**
 * Experiment C-only connection to the REAL, already compiled bjzhou/MGC
 * FullResolutionDenoise native AOT. No approximate bilateral filter, invented
 * noise profile or user-facing fallback. Full 1x camera RGB uses a bounded
 * GPU stripe read/write path into an exclusive file-backed direct mmap: never
 * a 50MP Kotlin Bitmap or extra full-image RGBA32F copy.
 *
 * packHalf2x16 returns the literal IEEE-754 half bits expected by the existing
 * native RGBA16F ABI. The output stays in the native same-physical RAW grid.
 */
internal object Iris26975CDonorNativeDenoise {
    private const val COMPONENT = "26975 C original donor full-res Sabre native denoise"
    private const val STRIPE = 64
    private val gpu = Iris26972CDonorSabreGpuMerge

    fun apply(
        context: Context,
        scratch: File,
        physical: Iris26972CPhysicalRawMetadata.Frozen,
        fused: Iris26972CDonorSabreGpuResolve.Result,
        referenceSignal: Float,
        shading: Iris26972CPhysicalLensShading.Frozen,
        mergedNoise: com.hinnka.mycamera.processor.experimentc.bjzhou.processor.MgcSabreMergedNoiseModel.Output,
    ) {
        fused.requireOwner()
        gpu.requireCurrentContext()
        // Donor Sabre's per-frame merged S/O/correlation is already authoritative.
        // A rejection/coverage-map readback is NOT an input to this denoiser.
        require(referenceSignal.isFinite() && referenceSignal >= 0f &&
            scratch.isDirectory && scratch.canWrite() &&
            physical.physicalCameraId.isNotBlank() &&
            mergedNoise.read.size == 3 && mergedNoise.shot.size == 3 &&
            mergedNoise.correlation.size == 128 &&
            mergedNoise.read.all { it.isFinite() && it >= 0f } &&
            mergedNoise.shot.all { it.isFinite() && it >= 0f } &&
            mergedNoise.correlation.all { it.isFinite() && it >= 0f }) {
            "$COMPONENT missing authentic merged RAW noise or private storage"
        }
        val bytes = fused.width.toLong()*fused.height*8L
        require(bytes in 8L..Int.MAX_VALUE.toLong() &&
            scratch.usableSpace > bytes + 128L*1024*1024) {
            "$COMPONENT cannot bound full-resolution native RGBA16F storage"
        }
        check(Iris26975CIndependentDenoise.ensureInitialized(context)) {
            "$COMPONENT authentic MGC Sabre AOT assets are missing"
        }
        shading.requireMatches(physical.physicalCameraId,physical.sensorTimestampNs)
        val physicalShading = shading.copyValuesForHostAudit()
        require(if (shading.hasMeasuredMap) {
            physicalShading.size.toLong() ==
                shading.mapWidth.toLong()*shading.mapHeight*4L &&
                physicalShading.all { it.isFinite() && it > 0f }
        } else physicalShading.isEmpty()) {
            "$COMPONENT invalid optional physical-lens noise-strength shading"
        }
        // MGC V25 NoiseModel::EstimateSnr for normalized Sabre output:
        // merged green read/shot are the ONLY denoising SNR authority.
        // The pre-merge reference SNR is deliberately reserved for sharpening.
        val outputSnr = checkNotNull(
            Iris26975CDonorSabreMergedNoiseModel.outputNoiseModelSnr(
                referenceSignal,mergedNoise.read[1],mergedNoise.shot[1])) {
            "$COMPONENT cannot derive donor merged green denoise SNR"
        }
        val metadata = Iris26975CSabreDenoiseMetadata(
            cfaPattern=physical.cfaPattern,
            whiteBalanceGains=physical.copyCanonicalWbForAudit(),
            // Donor Sabre AOT uses the same exact physical Camera2 lens
            // shading both at Resolve and while selecting Y/CrCb denoise.
            lensShadingMap=physicalShading.takeIf { shading.hasMeasuredMap },
            lensShadingMapWidth=if (shading.hasMeasuredMap) shading.mapWidth else 0,
            lensShadingMapHeight=if (shading.hasMeasuredMap) shading.mapHeight else 0,
            // Consume the donor V25 merged read/shot/correlation directly.
            // Sabre is not Spatial: it MUST NOT manufacture a Q8 support map
            // or re-apply the historical Iris residual-noise factor.
            mgcDenoiseReadNoise=mergedNoise.read,
            mgcDenoiseShotNoise=mergedNoise.shot,
            mgcDenoiseCorrelation=mergedNoise.correlation,
        )
        val tmp = File(scratch,".iris26975c_donor_${UUID.randomUUID()}.rgba16f")
        check(!tmp.exists()) { "$COMPONENT private mapped source collision" }
        val oldState=Iris26972CDonorSabreGpuMerge.GlState.capture()
        val oldPack=gpu.glInt(GLES30.GL_PIXEL_PACK_BUFFER_BINDING)
        val oldUnpack=gpu.glInt(GLES30.GL_PIXEL_UNPACK_BUFFER_BINDING)
        val oldPackAlign=gpu.glInt(GLES30.GL_PACK_ALIGNMENT)
        val oldUnpackAlign=gpu.glInt(GLES30.GL_UNPACK_ALIGNMENT)
        val oldPackRows=gpu.glInt(GLES30.GL_PACK_ROW_LENGTH)
        val oldUnpackRows=gpu.glInt(GLES30.GL_UNPACK_ROW_LENGTH)
        var program=0;var fbo=0;var vao=0;var packedTexture=0
        try {
            RandomAccessFile(tmp,"rw").use { file ->
                file.setLength(bytes)
                file.channel.use { channel ->
                    val mapped=channel.map(FileChannel.MapMode.READ_WRITE,0L,bytes)
                        .order(ByteOrder.nativeOrder())
                    program=gpu.compileProgram(gpu.VERTEX,PACK_HALF)
                    val ids=IntArray(1)
                    GLES30.glGenTextures(1,ids,0);packedTexture=ids[0]
                    GLES30.glGenFramebuffers(1,ids,0);fbo=ids[0]
                    GLES30.glGenVertexArrays(1,ids,0);vao=ids[0]
                    check(program>0 && packedTexture>0 && fbo>0 && vao>0) {
                        "$COMPONENT no lossless HALF transfer scratch"
                    }
                    GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
                    GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,packedTexture)
                    GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,
                        GLES30.GL_TEXTURE_MIN_FILTER,GLES30.GL_NEAREST)
                    GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,
                        GLES30.GL_TEXTURE_MAG_FILTER,GLES30.GL_NEAREST)
                    GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,
                        GLES30.GL_TEXTURE_WRAP_S,GLES30.GL_CLAMP_TO_EDGE)
                    GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,
                        GLES30.GL_TEXTURE_WRAP_T,GLES30.GL_CLAMP_TO_EDGE)
                    GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,GLES30.GL_RG32UI,
                        fused.width,STRIPE,0,GLES30.GL_RG_INTEGER,
                        GLES30.GL_UNSIGNED_INT,null)
                    GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,fbo)
                    GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,
                        GLES30.GL_COLOR_ATTACHMENT0,GLES30.GL_TEXTURE_2D,packedTexture,0)
                    check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)==
                        GLES30.GL_FRAMEBUFFER_COMPLETE) {
                        "$COMPONENT exact half-pack FBO unsupported by GPU"
                    }
                    GLES30.glBindVertexArray(vao)
                    GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
                    GLES30.glDisable(GLES30.GL_BLEND)
                    GLES30.glDisable(GLES30.GL_DEPTH_TEST)
                    GLES30.glColorMask(true,true,true,true)
                    GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER,0)
                    GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,1)
                    GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH,0)
                    GLES30.glUseProgram(program)
                    GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
                    GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,fused.extendedCameraRgbTexture)
                    GLES30.glUniform1i(uniform(program,"uSource"),0)
                    for (y in 0 until fused.height step STRIPE) {
                        val h=minOf(STRIPE,fused.height-y)
                        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,fbo)
                        GLES30.glViewport(0,0,fused.width,h)
                        GLES30.glUniform1i(uniform(program,"uOriginY"),y)
                        GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3)
                        GLES30.glBindFramebuffer(GLES30.GL_READ_FRAMEBUFFER,fbo)
                        GLES30.glReadBuffer(GLES30.GL_COLOR_ATTACHMENT0)
                        val start=y.toLong()*fused.width*8L
                        val len=h.toLong()*fused.width*8L
                        mapped.position(start.toInt())
                        mapped.limit((start+len).toInt())
                        GLES30.glReadPixels(0,0,fused.width,h,GLES30.GL_RG_INTEGER,
                            GLES30.GL_UNSIGNED_INT,mapped)
                        gpu.checkGl("C original donor native denoise exact HALF capture y=$y")
                    }
                    mapped.clear()
                    // C-owned JNI dispatches the original static MGC AOT; the
                    // input S/O/correlation derives from the donor Sabre merge.
                    // There is no Spatial Q8 residual support-map dependency.
                    check(Iris26975CIndependentDenoise.denoise(
                        rgba16f=mapped,width=fused.width,height=fused.height,
                        globalOriginX=0,globalOriginY=0,
                        fullWidth=fused.width,fullHeight=fused.height,
                        metadata=metadata,tuningSnr=outputSnr,
                        lumaStrengthScale=Iris26972CContract.LUMA_DENOISE,
                        chromaStrengthScale=Iris26972CContract.CHROMA_DENOISE,
                    )) { "$COMPONENT genuine donor native kernel returned failure" }
                    mapped.clear()
                    GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER,0)
                    GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT,1)
                    GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH,0)
                    GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,fused.extendedCameraRgbTexture)
                    for (y in 0 until fused.height step STRIPE) {
                        val h=minOf(STRIPE,fused.height-y)
                        val start=y.toLong()*fused.width*8L
                        val len=h.toLong()*fused.width*8L
                        mapped.position(start.toInt())
                        mapped.limit((start+len).toInt())
                        GLES30.glTexSubImage2D(GLES30.GL_TEXTURE_2D,0,0,y,
                            fused.width,h,GLES30.GL_RGBA,GLES30.GL_HALF_FLOAT,mapped)
                        gpu.checkGl("C original donor native denoise HALF upload y=$y")
                    }
                    mapped.clear()
                }
            }
        } finally {
            if(program>0)GLES30.glDeleteProgram(program)
            if(fbo>0)GLES30.glDeleteFramebuffers(1,intArrayOf(fbo),0)
            if(vao>0)GLES30.glDeleteVertexArrays(1,intArrayOf(vao),0)
            if(packedTexture>0)GLES30.glDeleteTextures(1,intArrayOf(packedTexture),0)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER,oldPack)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER,oldUnpack)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,oldPackAlign)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT,oldUnpackAlign)
            GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH,oldPackRows)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH,oldUnpackRows)
            oldState.restore()
            check(!tmp.exists() || tmp.delete()) {
                "$COMPONENT unable to remove private full-size native transfer"
            }
        }
    }

    private fun uniform(program:Int,name:String):Int =
        GLES30.glGetUniformLocation(program,name).also {
            check(it>=0) { "$COMPONENT required shader uniform optimized away: $name" }
        }

    private const val PACK_HALF = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp sampler2D;
        uniform highp sampler2D uSource;
        uniform int uOriginY;
        layout(location=0) out highp uvec2 oHalfPairs;
        void main() {
            ivec2 p=ivec2(gl_FragCoord.xy)+ivec2(0,uOriginY);
            vec4 color=texelFetch(uSource,p,0);
            // Rejected nonfinite input must not silently become a real photo.
            oHalfPairs=uvec2(packHalf2x16(color.rg),packHalf2x16(color.ba));
        }
    """
}
