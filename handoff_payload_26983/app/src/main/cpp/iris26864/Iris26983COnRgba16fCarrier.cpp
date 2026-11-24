// Independent C ON transport copied from the successful 26982 JNI carrier.
#include <jni.h>
#include <android/hardware_buffer.h>
#include <android/hardware_buffer_jni.h>
#include <android/log.h>
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl31.h>
#include <GLES2/gl2ext.h>
#include <algorithm>
#include <cstdint>
#include <cstring>
#include "Iris26983COnGuidePack.h"
#define TAG "Iris26983COnCarrier"
/* IRIS_26826_SHARED_RGBA16F_CARRIER_NATIVE
 * Shared HardwareBuffer is only transport/storage. Existing Sabre/VGN, CPU denoiser and post
 * math are unchanged. Producer/consumer use same-format RGBA16F framebuffer blits and glFinish
 * before ownership crosses CPU/context boundaries. */
namespace {
template <typename T>T iris26826EglProc(const char*name){return reinterpret_cast<T>(eglGetProcAddress(name));}

bool iris26826Describe(JNIEnv*env,jobject hardwareBuffer,AHardwareBuffer**out,AHardwareBuffer_Desc*desc,int width,int height){
    if(!hardwareBuffer||!out||!desc||width<=0||height<=0)return false;
    AHardwareBuffer*buffer=AHardwareBuffer_fromHardwareBuffer(env,hardwareBuffer);if(!buffer)return false;
    AHardwareBuffer_describe(buffer,desc);
    if((int)desc->width!=width||(int)desc->height!=height||desc->layers!=1||
       desc->format!=AHARDWAREBUFFER_FORMAT_R16G16B16A16_FLOAT)return false;
    *out=buffer;return true;
}

bool iris26826BindHardwareBufferTexture(JNIEnv*env,jobject hardwareBuffer,int width,int height,GLuint texture,EGLImageKHR*imageOut){
    if(!imageOut||texture==0)return false;*imageOut=EGL_NO_IMAGE_KHR;
    AHardwareBuffer*buffer=nullptr;AHardwareBuffer_Desc desc{};if(!iris26826Describe(env,hardwareBuffer,&buffer,&desc,width,height))return false;
    EGLDisplay display=eglGetCurrentDisplay();if(display==EGL_NO_DISPLAY)return false;
    auto getClient=iris26826EglProc<PFNEGLGETNATIVECLIENTBUFFERANDROIDPROC>("eglGetNativeClientBufferANDROID");
    auto createImage=iris26826EglProc<PFNEGLCREATEIMAGEKHRPROC>("eglCreateImageKHR");
    auto bindImage=iris26826EglProc<PFNGLEGLIMAGETARGETTEXTURE2DOESPROC>("glEGLImageTargetTexture2DOES");
    if(!getClient||!createImage||!bindImage)return false;
    EGLClientBuffer client=getClient(buffer);if(!client)return false;
    const EGLint attrs[]={EGL_IMAGE_PRESERVED_KHR,EGL_TRUE,EGL_NONE};
    EGLImageKHR image=createImage(display,EGL_NO_CONTEXT,EGL_NATIVE_BUFFER_ANDROID,client,attrs);if(image==EGL_NO_IMAGE_KHR)return false;
    glBindTexture(GL_TEXTURE_2D,texture);bindImage(GL_TEXTURE_2D,image);
    GLenum err=glGetError();if(err!=GL_NO_ERROR){
        auto destroyImage=iris26826EglProc<PFNEGLDESTROYIMAGEKHRPROC>("eglDestroyImageKHR");if(destroyImage)destroyImage(display,image);return false;
    }
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);
    *imageOut=image;return true;
}

bool iris26826CopyHardwareBuffer(JNIEnv*env,jobject hardwareBuffer,GLuint endpointTexture,int width,int height,bool intoHardwareBuffer){
    if(endpointTexture==0)return false;
    GLint oldTex=0,oldRead=0,oldDraw=0;glGetIntegerv(GL_TEXTURE_BINDING_2D,&oldTex);glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING,&oldRead);glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING,&oldDraw);
    GLuint sharedTex=0,fbos[2]={0,0},readTex=0,drawTex=0;EGLImageKHR image=EGL_NO_IMAGE_KHR;bool ok=false;
    glGenTextures(1,&sharedTex);if(sharedTex==0)goto done;
    if(!iris26826BindHardwareBufferTexture(env,hardwareBuffer,width,height,sharedTex,&image))goto done;
    glGenFramebuffers(2,fbos);if(fbos[0]==0||fbos[1]==0)goto done;
    readTex=intoHardwareBuffer?endpointTexture:sharedTex;drawTex=intoHardwareBuffer?sharedTex:endpointTexture;
    glBindFramebuffer(GL_READ_FRAMEBUFFER,fbos[0]);glFramebufferTexture2D(GL_READ_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,readTex,0);
    if(glCheckFramebufferStatus(GL_READ_FRAMEBUFFER)!=GL_FRAMEBUFFER_COMPLETE)goto done;
    glBindFramebuffer(GL_DRAW_FRAMEBUFFER,fbos[1]);glFramebufferTexture2D(GL_DRAW_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,drawTex,0);
    if(glCheckFramebufferStatus(GL_DRAW_FRAMEBUFFER)!=GL_FRAMEBUFFER_COMPLETE)goto done;
    while(glGetError()!=GL_NO_ERROR){}
    glBlitFramebuffer(0,0,width,height,0,0,width,height,GL_COLOR_BUFFER_BIT,GL_NEAREST);
    if(glGetError()!=GL_NO_ERROR)goto done;
    glFinish();if(glGetError()!=GL_NO_ERROR)goto done;ok=true;
 done:
    glBindFramebuffer(GL_READ_FRAMEBUFFER,(GLuint)oldRead);glBindFramebuffer(GL_DRAW_FRAMEBUFFER,(GLuint)oldDraw);
    glBindTexture(GL_TEXTURE_2D,(GLuint)oldTex);
    if(fbos[0]||fbos[1])glDeleteFramebuffers(2,fbos);
    if(sharedTex)glDeleteTextures(1,&sharedTex);
    if(image!=EGL_NO_IMAGE_KHR){auto destroyImage=iris26826EglProc<PFNEGLDESTROYIMAGEKHRPROC>("eglDestroyImageKHR");if(destroyImage)destroyImage(eglGetCurrentDisplay(),image);}
    return ok;
}
}

extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_processor_Iris26983COnRgba16fCarrier_copyFromCurrentGlTextureNative(
        JNIEnv*env,jclass,jobject hardwareBuffer,jint sourceTextureId,jint width,jint height){
    bool ok=iris26826CopyHardwareBuffer(env,hardwareBuffer,(GLuint)sourceTextureId,width,height,true);
    if(!ok)__android_log_print(ANDROID_LOG_WARN,TAG,"IRIS_26826_SHARED_RGBA16F_FAILURE stage=producer_copy");
    return ok?JNI_TRUE:JNI_FALSE;
}

extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_processor_Iris26983COnRgba16fCarrier_copyToCurrentGlTextureNative(
        JNIEnv*env,jclass,jobject hardwareBuffer,jint destinationTextureId,jint width,jint height){
    bool ok=iris26826CopyHardwareBuffer(env,hardwareBuffer,(GLuint)destinationTextureId,width,height,false);
    if(!ok)__android_log_print(ANDROID_LOG_WARN,TAG,"IRIS_26826_SHARED_RGBA16F_FAILURE stage=consumer_copy");
    return ok?JNI_TRUE:JNI_FALSE;
}

/* IRIS_26915_FINAL_1X_STRIDE_AWARE_CPU_PACK
 * Lock only after proving exact buffer capacities and clip validity.
 * The 1x producer is CPU-written / GPU-sampled; never assume physical
 * AHardwareBuffer stride == width. The original 2x GPU transport is untouched.
 */
extern "C" JNIEXPORT jboolean JNICALL
Java_com_particlesdevs_photoncamera_processing_processor_Iris26983COnRgba16fCarrier_writeFinal1xGuideNative(
    JNIEnv* env, jclass, jobject hardwareBuffer, jobject rgbaBuffer,
    jobject maskBuffer, jint width, jint height) {
    AHardwareBuffer* buffer=nullptr;
    AHardwareBuffer_Desc desc{};
    size_t rgbBytesPlaceholder=0,maskBytesPlaceholder=0,strideBytesPlaceholder=0;
    if (!iris26826Describe(env,hardwareBuffer,&buffer,&desc,width,height) ||
        !rgbaBuffer || !maskBuffer ||
        !iris26915guide::sizes(width,height,static_cast<size_t>(desc.stride),
                                &rgbBytesPlaceholder,&maskBytesPlaceholder,&strideBytesPlaceholder)) {
        __android_log_print(ANDROID_LOG_WARN,TAG,
              "IRIS_26915_GUIDE_FAILURE stage=describe_or_stride width=%d height=%d",width,height);
        return JNI_FALSE;
    }
    const jlong rgbaCap=env->GetDirectBufferCapacity(rgbaBuffer);
    const jlong maskCap=env->GetDirectBufferCapacity(maskBuffer);
    const auto* rgba=static_cast<const uint8_t*>(env->GetDirectBufferAddress(rgbaBuffer));
    const auto* mask=static_cast<const uint8_t*>(env->GetDirectBufferAddress(maskBuffer));
    if (!rgba || !mask || rgbaCap<0 || maskCap<0 ||
        static_cast<uint64_t>(rgbaCap)!=rgbBytesPlaceholder ||
        static_cast<uint64_t>(maskCap)!=maskBytesPlaceholder ||
        !iris26915guide::validMask(mask,
                 static_cast<size_t>(width)*static_cast<size_t>(height))) {
        __android_log_print(ANDROID_LOG_WARN,TAG,
              "IRIS_26915_GUIDE_FAILURE stage=direct_or_mask width=%d height=%d",width,height);
        return JNI_FALSE;
    }
    void* pixels=nullptr;
    const int lockRc=AHardwareBuffer_lock(buffer,AHARDWAREBUFFER_USAGE_CPU_WRITE_OFTEN,
                                          -1,nullptr,&pixels);
    if (lockRc!=0 || !pixels) {
        __android_log_print(ANDROID_LOG_WARN,TAG,
              "IRIS_26915_GUIDE_FAILURE stage=cpu_lock rc=%d stride=%u width=%d height=%d",
              lockRc,desc.stride,width,height);
        return JNI_FALSE;
    }
    const bool packed=iris26915guide::pack(static_cast<uint8_t*>(pixels),
                         static_cast<size_t>(desc.stride),width,height,
                         rgba,static_cast<size_t>(rgbaCap),
                         mask,static_cast<size_t>(maskCap));
    const int unlockRc=AHardwareBuffer_unlock(buffer,nullptr);
    if (!packed || unlockRc!=0) {
        __android_log_print(ANDROID_LOG_WARN,TAG,
              "IRIS_26915_GUIDE_FAILURE stage=cpu_pack_or_unlock packed=%d rc=%d stride=%u width=%d",
              packed?1:0,unlockRc,desc.stride,width);
        return JNI_FALSE;
    }
    __android_log_print(ANDROID_LOG_INFO,TAG,
              "IRIS_26915_GUIDE_STRIDE_PACK_PASS width=%d height=%d stride=%u rgbExact=true clipExact=true",
              width,height,desc.stride);
    return JNI_TRUE;
}

extern "C" JNIEXPORT jobject JNICALL Java_com_particlesdevs_photoncamera_processing_processor_Iris26983COnRgba16fCarrier_lockCpuNative(
        JNIEnv*env,jclass,jobject hardwareBuffer,jint width,jint height){
    AHardwareBuffer*buffer=nullptr;AHardwareBuffer_Desc desc{};if(!iris26826Describe(env,hardwareBuffer,&buffer,&desc,width,height))return nullptr;
    if(desc.stride!=(uint32_t)width){__android_log_print(ANDROID_LOG_WARN,TAG,"IRIS_26826_SHARED_RGBA16F_FAILURE stage=cpu_stride stride=%u width=%d",desc.stride,width);return nullptr;}
    void*ptr=nullptr;uint64_t usage=AHARDWAREBUFFER_USAGE_CPU_READ_OFTEN|AHARDWAREBUFFER_USAGE_CPU_WRITE_OFTEN;
    int rc=AHardwareBuffer_lock(buffer,usage,-1,nullptr,&ptr);if(rc!=0||!ptr){__android_log_print(ANDROID_LOG_WARN,TAG,"IRIS_26826_SHARED_RGBA16F_FAILURE stage=cpu_lock rc=%d",rc);return nullptr;}
    jlong bytes=(jlong)width*(jlong)height*8LL;return env->NewDirectByteBuffer(ptr,bytes);
}

extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_processor_Iris26983COnRgba16fCarrier_unlockCpuNative(
        JNIEnv*env,jclass,jobject hardwareBuffer){
    if(!hardwareBuffer)return JNI_FALSE;AHardwareBuffer*buffer=AHardwareBuffer_fromHardwareBuffer(env,hardwareBuffer);if(!buffer)return JNI_FALSE;
    int rc=AHardwareBuffer_unlock(buffer,nullptr);if(rc!=0)__android_log_print(ANDROID_LOG_WARN,TAG,"IRIS_26826_SHARED_RGBA16F_FAILURE stage=cpu_unlock rc=%d",rc);
    return rc==0?JNI_TRUE:JNI_FALSE;
}
/* IRIS_26876_B_WRONSKI_EXACT_2X_AHB_DIRECT_RENDER
 * Requires the existing real Vulkan->GLES signaled fence, post-AMaZE B-only
 * sensor-neutral RGB (LONG only luminance) and the independent ORIGINAL 2x
 * sensor clip R16F. No CPU/full-size RGB16F disk carrier is generated.
 * The EGLImage is the ONE output surface; avoid allocating an additional
 * 50MP intermediate for clipping transport. Never borrowed by A/NIGHT/DNG.
 */
namespace {
constexpr const char* kIris26876BPackVertex=R"IRIS26876(#version 310 es
precision highp float;
void main(){
 vec2 p=vec2(float((gl_VertexID<<1)&2),float(gl_VertexID&2));
 gl_Position=vec4(p*2.0-1.0,0.0,1.0);
}
)IRIS26876";
constexpr const char* kIris26876BPackFrag=R"IRIS26876(#version 310 es
precision highp float;
precision highp int;
uniform highp sampler2D uBLinearRgb;
uniform highp sampler2D uBExactSensorClip;
uniform ivec2 uSize;
uniform int uRequireOriginal2xBinary;
layout(std430,binding=4) buffer Iris26876B2xFault { uint invalidCount; };
layout(location=0) out vec4 oB2x;
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    if(any(greaterThanEqual(p,uSize))){oB2x=vec4(0.0);return;}
    vec3 rgb=texelFetch(uBLinearRgb,p,0).rgb;
    float clip=texelFetch(uBExactSensorClip,p,0).r;
    if(any(isnan(rgb))||any(isinf(rgb))||isnan(clip)||isinf(clip)||
        clip<0.0||clip>1.0||
        (uRequireOriginal2xBinary!=0 && !(clip==0.0||clip==1.0))){
        atomicAdd(invalidCount,1u);oB2x=vec4(0.0);return;
    }
    oB2x=vec4(rgb,clip);
}
)IRIS26876";

GLuint iris26876CompileSimple(GLenum kind,const char*src){
    GLuint sh=glCreateShader(kind);
    if(!sh)return 0;
    glShaderSource(sh,1,&src,nullptr);glCompileShader(sh);
    GLint compiled=0;glGetShaderiv(sh,GL_COMPILE_STATUS,&compiled);
    if(!compiled){
        char log[1024]{};glGetShaderInfoLog(sh,sizeof(log),nullptr,log);
        __android_log_print(ANDROID_LOG_ERROR,TAG,"IRIS_26876_B_AHB_SHADER_FAIL %s",log);
        glDeleteShader(sh);return 0;
    }
    return sh;
}

bool iris26876PackRgbClipIntoAhb(JNIEnv*env,jobject target,GLuint rgb,GLuint clip,
                                 int w,int h,bool strict2x){
    if(!target||!rgb||!clip||w<2||h<2||w>8192||h>8192||
        uint64_t(w)*h>uint64_t(8192)*8192||eglGetCurrentContext()==EGL_NO_CONTEXT)
        return false;
    GLenum pre=glGetError();
    if(pre!=GL_NO_ERROR)return false; // inherited GL error is a hard blocker
    GLint maxTexture=0,major=0,minor=0;
    glGetIntegerv(GL_MAX_TEXTURE_SIZE,&maxTexture);
    glGetIntegerv(GL_MAJOR_VERSION,&major);glGetIntegerv(GL_MINOR_VERSION,&minor);
    if(maxTexture<std::max(w,h)||major<3||(major==3&&minor<1))return false;
    GLint priorProgram=0,priorReadFbo=0,priorDrawFbo=0,priorVao=0;
    GLint priorActiveTexture=0,priorUnit0=0,priorUnit1=0,priorTex2D=0;
    GLint priorSsbo=0,priorSsbo4=0,priorViewport[4]{0,0,0,0};
    GLboolean priorMask[4]{GL_TRUE,GL_TRUE,GL_TRUE,GL_TRUE};
    glGetIntegerv(GL_CURRENT_PROGRAM,&priorProgram);
    glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING,&priorReadFbo);
    glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING,&priorDrawFbo);
    glGetIntegerv(GL_VERTEX_ARRAY_BINDING,&priorVao);
    glGetIntegerv(GL_ACTIVE_TEXTURE,&priorActiveTexture);
    glActiveTexture(GL_TEXTURE0);glGetIntegerv(GL_TEXTURE_BINDING_2D,&priorUnit0);
    glActiveTexture(GL_TEXTURE1);glGetIntegerv(GL_TEXTURE_BINDING_2D,&priorUnit1);
    glActiveTexture(GL_TEXTURE2);glGetIntegerv(GL_TEXTURE_BINDING_2D,&priorTex2D);
    glGetIntegerv(GL_SHADER_STORAGE_BUFFER_BINDING,&priorSsbo);
    glGetIntegeri_v(GL_SHADER_STORAGE_BUFFER_BINDING,4,&priorSsbo4);
    glGetIntegerv(GL_VIEWPORT,priorViewport);
    glGetBooleanv(GL_COLOR_WRITEMASK,priorMask);
    const GLboolean blend=glIsEnabled(GL_BLEND),depth=glIsEnabled(GL_DEPTH_TEST),
        stencil=glIsEnabled(GL_STENCIL_TEST),scissor=glIsEnabled(GL_SCISSOR_TEST),
        cull=glIsEnabled(GL_CULL_FACE),raster=glIsEnabled(GL_RASTERIZER_DISCARD);
    GLuint eglTexture=0,fb=0,vtx=0,frag=0,program=0,vao=0,errors=0;
    EGLImageKHR eglImage=EGL_NO_IMAGE_KHR;
    bool ok=false;
    do {
        glActiveTexture(GL_TEXTURE2);glGenTextures(1,&eglTexture);
        if(!eglTexture||!iris26826BindHardwareBufferTexture(env,target,w,h,eglTexture,&eglImage))break;
        glGenFramebuffers(1,&fb);if(!fb)break;
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER,fb);
        glFramebufferTexture2D(GL_DRAW_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,eglTexture,0);
        if(glCheckFramebufferStatus(GL_DRAW_FRAMEBUFFER)!=GL_FRAMEBUFFER_COMPLETE)break;
        vtx=iris26876CompileSimple(GL_VERTEX_SHADER,kIris26876BPackVertex);
        frag=iris26876CompileSimple(GL_FRAGMENT_SHADER,kIris26876BPackFrag);
        if(!vtx||!frag)break;
        program=glCreateProgram();if(!program)break;
        glAttachShader(program,vtx);glAttachShader(program,frag);glLinkProgram(program);
        GLint linked=0;glGetProgramiv(program,GL_LINK_STATUS,&linked);
        if(!linked)break;
        uint32_t zero=0;
        glGenBuffers(1,&errors);if(!errors)break;
        glBindBuffer(GL_SHADER_STORAGE_BUFFER,errors);
        glBufferData(GL_SHADER_STORAGE_BUFFER,sizeof(zero),&zero,GL_DYNAMIC_READ);
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER,4,errors);
        glGenVertexArrays(1,&vao);if(!vao)break;
        glBindVertexArray(vao);
        glDisable(GL_BLEND);glDisable(GL_DEPTH_TEST);glDisable(GL_STENCIL_TEST);
        glDisable(GL_SCISSOR_TEST);glDisable(GL_CULL_FACE);glDisable(GL_RASTERIZER_DISCARD);
        glColorMask(GL_TRUE,GL_TRUE,GL_TRUE,GL_TRUE);
        glViewport(0,0,w,h);
        glUseProgram(program);
        glUniform1i(glGetUniformLocation(program,"uBLinearRgb"),0);
        glUniform1i(glGetUniformLocation(program,"uBExactSensorClip"),1);
        glUniform2i(glGetUniformLocation(program,"uSize"),w,h);
        glUniform1i(glGetUniformLocation(program,"uRequireOriginal2xBinary"),strict2x?1:0);
        glActiveTexture(GL_TEXTURE0);glBindTexture(GL_TEXTURE_2D,rgb);
        glActiveTexture(GL_TEXTURE1);glBindTexture(GL_TEXTURE_2D,clip);
        glDrawArrays(GL_TRIANGLES,0,3);
        glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT|GL_BUFFER_UPDATE_BARRIER_BIT|
                        GL_FRAMEBUFFER_BARRIER_BIT);
        glFinish();
        if(glGetError()!=GL_NO_ERROR)break;
        glBindBuffer(GL_SHADER_STORAGE_BUFFER,errors);
        auto*mapped=static_cast<uint32_t*>(glMapBufferRange(GL_SHADER_STORAGE_BUFFER,0,4,GL_MAP_READ_BIT));
        if(!mapped)break;
        const uint32_t faults=*mapped;
        const GLboolean unmapped=glUnmapBuffer(GL_SHADER_STORAGE_BUFFER);
        if(faults||!unmapped||glGetError()!=GL_NO_ERROR){
            __android_log_print(ANDROID_LOG_ERROR,TAG,"IRIS_26876_B_AHB_INVALID_PIXELS count=%u",faults);
            break;
        }
        ok=true;
    } while(false);
    glBindFramebuffer(GL_READ_FRAMEBUFFER,(GLuint)priorReadFbo);
    glBindFramebuffer(GL_DRAW_FRAMEBUFFER,(GLuint)priorDrawFbo);
    glBindVertexArray((GLuint)priorVao);
    glUseProgram((GLuint)priorProgram);
    glActiveTexture(GL_TEXTURE0);glBindTexture(GL_TEXTURE_2D,(GLuint)priorUnit0);
    glActiveTexture(GL_TEXTURE1);glBindTexture(GL_TEXTURE_2D,(GLuint)priorUnit1);
    glActiveTexture(GL_TEXTURE2);glBindTexture(GL_TEXTURE_2D,(GLuint)priorTex2D);
    glActiveTexture((GLenum)priorActiveTexture);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER,4,(GLuint)priorSsbo4);
    glBindBuffer(GL_SHADER_STORAGE_BUFFER,(GLuint)priorSsbo);
    glViewport(priorViewport[0],priorViewport[1],priorViewport[2],priorViewport[3]);
    glColorMask(priorMask[0],priorMask[1],priorMask[2],priorMask[3]);
    auto restore=[](GLenum what,GLboolean enabled){if(enabled)glEnable(what);else glDisable(what);};
    restore(GL_BLEND,blend);restore(GL_DEPTH_TEST,depth);restore(GL_STENCIL_TEST,stencil);
    restore(GL_SCISSOR_TEST,scissor);restore(GL_CULL_FACE,cull);restore(GL_RASTERIZER_DISCARD,raster);
    if(vao)glDeleteVertexArrays(1,&vao);
    if(errors)glDeleteBuffers(1,&errors);
    if(program)glDeleteProgram(program);
    if(frag)glDeleteShader(frag);
    if(vtx)glDeleteShader(vtx);
    if(fb)glDeleteFramebuffers(1,&fb);
    if(eglTexture)glDeleteTextures(1,&eglTexture);
    if(eglImage!=EGL_NO_IMAGE_KHR){
        auto destroy=iris26826EglProc<PFNEGLDESTROYIMAGEKHRPROC>("eglDestroyImageKHR");
        if(!destroy||!destroy(eglGetCurrentDisplay(),eglImage))ok=false;
    }
    if(glGetError()!=GL_NO_ERROR)ok=false;
    __android_log_print(ok?ANDROID_LOG_INFO:ANDROID_LOG_ERROR,TAG,
        "IRIS_26876_B_AHB_EXACT_CLIP_GPU_RENDER ok=%d w=%d h=%d noDiskOrCpuFallback=1",
        (int)ok,w,h);
    return ok;
}
}
extern "C" JNIEXPORT jboolean JNICALL
Java_com_particlesdevs_photoncamera_processing_processor_Iris26983COnRgba16fCarrier_packWronskiRgbAndClipNative26876(
    JNIEnv*env,jclass,jobject buffer,jint rgbTexture,jint clipTexture,
    jint width,jint height,jboolean original2xBinary){
    return iris26876PackRgbClipIntoAhb(env,buffer,(GLuint)rgbTexture,(GLuint)clipTexture,
                                       width,height,original2xBinary==JNI_TRUE)?JNI_TRUE:JNI_FALSE;
}

