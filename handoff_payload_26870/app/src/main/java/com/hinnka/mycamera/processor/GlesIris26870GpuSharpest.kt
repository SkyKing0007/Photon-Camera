package com.hinnka.mycamera.processor

import android.opengl.GLES30
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.abs

/**
 * IRIS_26870_B_NORMAL_GPU_SHARPNESS_OWNER.
 * GL ES 3 integer RAW16 GPU-sampled Bayer-green structural score. Operates
 * synchronously on the existing B capture EGL thread BEFORE native HDRq /
 * Wronski submission.  Never changes the frozen NORMAL batch or its metadata.
 * No Camera2 noise profile, CPU RAW-image sharpness estimate, or LONG/SHORT.
 */
internal object GlesIris26870GpuSharpest {
    private const val GRID = 96
    private val vertex = """#version 300 es
        void main() {
          vec2 p=vec2((gl_VertexID==1)?3.0:-1.0,(gl_VertexID==2)?3.0:-1.0);
          gl_Position=vec4(p,0.0,1.0);
        }
    """.trimIndent()
    private val fragment = """#version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uRaw;
        uniform int uCfa;
        uniform ivec2 uSourceSize;
        uniform vec4 uBlack;
        uniform float uWhite;
        layout(location=0) out vec4 outScore;
        float readNormalized(ivec2 p,float black) {
          float raw=float(texelFetch(uRaw,p,0).r);
          return clamp((raw-black)/max(uWhite-black,1.0),0.0,1.0);
        }
        void main(){
          ivec2 cell=ivec2(gl_FragCoord.xy);
          int phase=cell.y & 1;
          int gx=((uCfa==0||uCfa==3)?1-phase:phase);
          ivec2 p=ivec2(4+(cell.x*(uSourceSize.x-8))/96,4+(cell.y*(uSourceSize.y-8))/96);
          p=ivec2((p.x & ~1)+gx,(p.y & ~1)+phase);
          p=clamp(p,ivec2(2),uSourceSize-ivec2(3));
          int site=(p.y & 1)*2+(p.x & 1);
          float b=uBlack[site];
          float c=readNormalized(p,b);
          float l=readNormalized(p+ivec2(-2,0),b);
          float r=readNormalized(p+ivec2(2,0),b);
          float t=readNormalized(p+ivec2(0,2),b);
          float d=readNormalized(p+ivec2(0,-2),b);
          float lo=min(c,min(min(l,r),min(t,d)));
          float hi=max(c,max(max(l,r),max(t,d)));
          if(lo<0.035||hi>0.94){outScore=vec4(0.0);return;}
          float xx=abs(r-l),yy=abs(t-d),gradient=xx+yy;
          float residual=abs(4.0*c-l-r-t-d);
          // Reject shot/read noise, isolated hot pixels and incoherent sparkle.
          float structuralSupport=smoothstep(0.012,0.035,gradient)
               *(1.0-smoothstep(0.60,1.6,residual/max(gradient,0.001)));
          if(structuralSupport<0.12){outScore=vec4(0.0);return;}
          outScore=vec4(clamp(gradient*4.0,0.0,1.0)*structuralSupport,
                        1.0,clamp(residual*4.0,0.0,1.0)*structuralSupport,1.0);
        }
    """.trimIndent()

    private fun shader(type: Int, source: String): Int {
        val id=GLES30.glCreateShader(type)
        check(id!=0) { "26870 GPU sharpness shader allocation failed" }
        GLES30.glShaderSource(id,source)
        GLES30.glCompileShader(id)
        val ok=IntArray(1)
        GLES30.glGetShaderiv(id,GLES30.GL_COMPILE_STATUS,ok,0)
        if(ok[0]!=GLES30.GL_TRUE){
            val log=GLES30.glGetShaderInfoLog(id)
            GLES30.glDeleteShader(id)
            throw IllegalStateException("26870 GPU sharpness shader: $log")
        }
        return id
    }
    private fun program(): Int {
        val vs=shader(GLES30.GL_VERTEX_SHADER,vertex)
        val fs=try { shader(GLES30.GL_FRAGMENT_SHADER,fragment) }
               catch(t:Throwable){ GLES30.glDeleteShader(vs);throw t }
        try {
            val p=GLES30.glCreateProgram()
            check(p!=0)
            GLES30.glAttachShader(p,vs)
            GLES30.glAttachShader(p,fs)
            GLES30.glLinkProgram(p)
            val ok=IntArray(1)
            GLES30.glGetProgramiv(p,GLES30.GL_LINK_STATUS,ok,0)
            if(ok[0]!=GLES30.GL_TRUE) {
                val log=GLES30.glGetProgramInfoLog(p)
                GLES30.glDeleteProgram(p)
                throw IllegalStateException("26870 GPU sharpness link: $log")
            }
            return p
        } finally { GLES30.glDeleteShader(vs);GLES30.glDeleteShader(fs) }
    }
    private fun state(id:Int):Int{
        val v=IntArray(1);GLES30.glGetIntegerv(id,v,0);return v[0]
    }
    fun select(frozen:GlesIris26864FrozenRawrIngress,cfa:Int,shutterIndex:Int):Int {
        frozen.assertUsable()
        require(cfa in 0..3 && shutterIndex in frozen.buffers.indices)
        val w=frozen.width;val h=frozen.height
        val maxTex=state(GLES30.GL_MAX_TEXTURE_SIZE)
        if(w<128||h<128||w>maxTex||h>maxTex)return shutterIndex
        val oldProgram=state(GLES30.GL_CURRENT_PROGRAM)
        val oldVao=state(GLES30.GL_VERTEX_ARRAY_BINDING)
        val oldRead=state(GLES30.GL_READ_FRAMEBUFFER_BINDING)
        val oldDraw=state(GLES30.GL_DRAW_FRAMEBUFFER_BINDING)
        val oldActive=state(GLES30.GL_ACTIVE_TEXTURE)
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
        val oldTex=state(GLES30.GL_TEXTURE_BINDING_2D)
        val oldUnpack=state(GLES30.GL_PIXEL_UNPACK_BUFFER_BINDING)
        val oldPack=state(GLES30.GL_PIXEL_PACK_BUFFER_BINDING)
        val oldRow=state(GLES30.GL_UNPACK_ROW_LENGTH)
        val oldUnpackSkipRows=state(GLES30.GL_UNPACK_SKIP_ROWS)
        val oldUnpackSkipPixels=state(GLES30.GL_UNPACK_SKIP_PIXELS)
        val oldPackRow=state(GLES30.GL_PACK_ROW_LENGTH)
        val oldPackSkipRows=state(GLES30.GL_PACK_SKIP_ROWS)
        val oldPackSkipPixels=state(GLES30.GL_PACK_SKIP_PIXELS)
        val oldUnpackAlign=state(GLES30.GL_UNPACK_ALIGNMENT)
        val oldPackAlign=state(GLES30.GL_PACK_ALIGNMENT)
        val viewport=IntArray(4)
        GLES30.glGetIntegerv(GLES30.GL_VIEWPORT,viewport,0)
        val oldScissor=GLES30.glIsEnabled(GLES30.GL_SCISSOR_TEST)
        val oldBlend=GLES30.glIsEnabled(GLES30.GL_BLEND)
        val oldDepth=GLES30.glIsEnabled(GLES30.GL_DEPTH_TEST)
        val oldStencil=GLES30.glIsEnabled(GLES30.GL_STENCIL_TEST)
        val oldCull=GLES30.glIsEnabled(GLES30.GL_CULL_FACE)
        val ids=IntArray(2)
        val fb=IntArray(1)
        val vao=IntArray(1)
        var prog=0
        try {
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glDisable(GLES30.GL_BLEND)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glDisable(GLES30.GL_STENCIL_TEST)
            GLES30.glDisable(GLES30.GL_CULL_FACE)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER,0)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER,0)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT,1)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_SKIP_ROWS,0)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_SKIP_PIXELS,0)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,1)
            GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH,0)
            GLES30.glPixelStorei(GLES30.GL_PACK_SKIP_ROWS,0)
            GLES30.glPixelStorei(GLES30.GL_PACK_SKIP_PIXELS,0)
            GLES30.glGenTextures(2,ids,0)
            check(ids[0]>0 && ids[1]>0)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,ids[0])
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MIN_FILTER,GLES30.GL_NEAREST)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MAG_FILTER,GLES30.GL_NEAREST)
            GLES30.glTexStorage2D(GLES30.GL_TEXTURE_2D,1,GLES30.GL_R16UI,w,h)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,ids[1])
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MIN_FILTER,GLES30.GL_NEAREST)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MAG_FILTER,GLES30.GL_NEAREST)
            GLES30.glTexStorage2D(GLES30.GL_TEXTURE_2D,1,GLES30.GL_RGBA8,GRID,GRID)
            GLES30.glGenFramebuffers(1,fb,0)
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,fb[0])
            GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT0,
                GLES30.GL_TEXTURE_2D,ids[1],0)
            check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)==GLES30.GL_FRAMEBUFFER_COMPLETE)
            GLES30.glGenVertexArrays(1,vao,0)
            GLES30.glBindVertexArray(vao[0])
            prog=program()
            GLES30.glUseProgram(prog)
            GLES30.glUniform1i(GLES30.glGetUniformLocation(prog,"uRaw"),0)
            GLES30.glUniform1i(GLES30.glGetUniformLocation(prog,"uCfa"),cfa)
            GLES30.glUniform2i(GLES30.glGetUniformLocation(prog,"uSourceSize"),w,h)
            GLES30.glViewport(0,0,GRID,GRID)
            val scores=DoubleArray(frozen.buffers.size)
            val supports=IntArray(frozen.buffers.size)
            val baseline=frozen.exposures[shutterIndex].toDouble()
            check(baseline.isFinite() && baseline>0)
            val host=ByteBuffer.allocateDirect(GRID*GRID*4).order(ByteOrder.nativeOrder())
            for(i in frozen.buffers.indices){
                val exp=frozen.exposures[i].toDouble()
                // Reference-dependent exposure/black/clip metadata MUST be
                // comparable to shutter when downstream capture metadata stays frozen.
                if(!exp.isFinite() || abs(exp/baseline-1.0)>0.005)continue
                GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,ids[0])
                GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH,frozen.stridesBytes[i]/2)
                val raw=frozen.buffers[i].duplicate().order(ByteOrder.nativeOrder())
                raw.position(0)
                GLES30.glTexSubImage2D(GLES30.GL_TEXTURE_2D,0,0,0,w,h,
                    GLES30.GL_RED_INTEGER,GLES30.GL_UNSIGNED_SHORT,raw)
                val blacks=frozen.blackByFrameByPhase
                GLES30.glUniform4f(GLES30.glGetUniformLocation(prog,"uBlack"),
                    blacks[i*4],blacks[i*4+1],blacks[i*4+2],blacks[i*4+3])
                GLES30.glUniform1f(GLES30.glGetUniformLocation(prog,"uWhite"),frozen.sensorWhiteByFrame[i])
                GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3)
                host.clear()
                GLES30.glReadPixels(0,0,GRID,GRID,GLES30.GL_RGBA,GLES30.GL_UNSIGNED_BYTE,host)
                check(GLES30.glGetError()==GLES30.GL_NO_ERROR) { "26870 GPU sharpness RAW16 readback failed" }
                var sum=0.0;var count=0
                for(j in 0 until GRID*GRID){
                    if((host.get(j*4+1).toInt() and 255)>200){
                        sum+=(host.get(j*4).toInt() and 255)/255.0+
                             0.15*(host.get(j*4+2).toInt() and 255)/255.0
                        count++
                    }
                }
                if(count>=500){scores[i]=sum/count;supports[i]=count}
            }
            val best=scores.indices.maxByOrNull{scores[it]} ?: shutterIndex
            if(supports[best]<500 || scores[best]<0.04 ||
               (scores[shutterIndex]>0.0 && scores[best]<scores[shutterIndex]*1.10))return shutterIndex
            val peak=scores[best]
            val near=scores.indices.filter { supports[it]>=500 && scores[it]>=peak*0.985 }
            val t=frozen.timestampsNs[shutterIndex]
            return near.minByOrNull{ abs(frozen.timestampsNs[it]-t) } ?: shutterIndex
        } catch(ignored: Throwable) {
            // A shader/device/sparse-scene failure cannot change the reference
            // to an unverified frame. Preserve the proven 26868 shutter owner.
            return shutterIndex
        } finally {
            if(prog!=0)GLES30.glDeleteProgram(prog)
            if(vao[0]!=0)GLES30.glDeleteVertexArrays(1,vao,0)
            if(fb[0]!=0)GLES30.glDeleteFramebuffers(1,fb,0)
            GLES30.glDeleteTextures(2,ids,0)
            GLES30.glBindFramebuffer(GLES30.GL_READ_FRAMEBUFFER,oldRead)
            GLES30.glBindFramebuffer(GLES30.GL_DRAW_FRAMEBUFFER,oldDraw)
            GLES30.glBindVertexArray(oldVao)
            GLES30.glUseProgram(oldProgram)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER,oldUnpack)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER,oldPack)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH,oldRow)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_SKIP_ROWS,oldUnpackSkipRows)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_SKIP_PIXELS,oldUnpackSkipPixels)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT,oldUnpackAlign)
            GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH,oldPackRow)
            GLES30.glPixelStorei(GLES30.GL_PACK_SKIP_ROWS,oldPackSkipRows)
            GLES30.glPixelStorei(GLES30.GL_PACK_SKIP_PIXELS,oldPackSkipPixels)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,oldPackAlign)
            GLES30.glViewport(viewport[0],viewport[1],viewport[2],viewport[3])
            if(oldScissor)GLES30.glEnable(GLES30.GL_SCISSOR_TEST)else GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            if(oldBlend)GLES30.glEnable(GLES30.GL_BLEND)else GLES30.glDisable(GLES30.GL_BLEND)
            if(oldDepth)GLES30.glEnable(GLES30.GL_DEPTH_TEST)else GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            if(oldStencil)GLES30.glEnable(GLES30.GL_STENCIL_TEST)else GLES30.glDisable(GLES30.GL_STENCIL_TEST)
            if(oldCull)GLES30.glEnable(GLES30.GL_CULL_FACE)else GLES30.glDisable(GLES30.GL_CULL_FACE)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,oldTex)
            GLES30.glActiveTexture(oldActive)
        }
    }
}
