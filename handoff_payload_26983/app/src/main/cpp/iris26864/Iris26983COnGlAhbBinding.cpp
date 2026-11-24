// C ON copy of the 26982 AHB import owner. Independent JNI symbols and handles.
#include <jni.h>
#include <android/hardware_buffer.h>
#include <android/hardware_buffer_jni.h>
#include <android/log.h>
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl3.h>
#include <GLES2/gl2ext.h>
#include <cstdint>
#include <new>
namespace {
constexpr char TAG[]="Iris26983COnAhb";
template <typename T>T iris26826EglProc(const char*name){return reinterpret_cast<T>(eglGetProcAddress(name));}
}
/* IRIS_26876_B_GL_AHB_CROSS_CONTEXT_IMPORT
 * Native EGLImage handles are deliberately opaque and short-lived. The Java
 * caller holds each HardwareBuffer across its binding; handles cannot outlive
 * the current EGL context/display or migrate to another GL thread.
 */
namespace {
struct Iris26983COnImportedAhb {
    EGLDisplay display=EGL_NO_DISPLAY;
    EGLImageKHR image=EGL_NO_IMAGE_KHR;
    GLuint texture=0;
};
void iris26983COnReleaseImportedAhb(Iris26983COnImportedAhb *entry){
    if(!entry)return;
    if(entry->display==eglGetCurrentDisplay()&&
       eglGetCurrentContext()!=EGL_NO_CONTEXT){
        if(entry->texture)glDeleteTextures(1,&entry->texture);
        if(entry->image!=EGL_NO_IMAGE_KHR){
            auto destroy=iris26826EglProc<PFNEGLDESTROYIMAGEKHRPROC>("eglDestroyImageKHR");
            if(destroy)destroy(entry->display,entry->image);
        }
    } else {
        __android_log_print(ANDROID_LOG_ERROR,TAG,
          "IRIS_26876_B_EGL_OWNER_CONTEXT_LOST resource_release_unverified=1");
    }
    delete entry;
}
}
extern "C" JNIEXPORT jlong JNICALL
Java_com_particlesdevs_photoncamera_processing_ultrahdr_Iris26983COnGlAhbBinding_bindNative(
    JNIEnv *env,jclass,jobject hb,jint w,jint h,jboolean finalRgba8){
    if(!hb||w<=0||h<=0||w>8192||h>8192||
       eglGetCurrentDisplay()==EGL_NO_DISPLAY||eglGetCurrentContext()==EGL_NO_CONTEXT)
       return 0;
    AHardwareBuffer *native=AHardwareBuffer_fromHardwareBuffer(env,hb);
    if(!native)return 0;
    AHardwareBuffer_Desc desc{};AHardwareBuffer_describe(native,&desc);
    const uint32_t format=finalRgba8==JNI_TRUE?
        AHARDWAREBUFFER_FORMAT_R8G8B8A8_UNORM:AHARDWAREBUFFER_FORMAT_R16G16B16A16_FLOAT;
    if(desc.width!=(uint32_t)w||desc.height!=(uint32_t)h||
       desc.layers!=1||desc.format!=format||
       !(desc.usage&AHARDWAREBUFFER_USAGE_GPU_SAMPLED_IMAGE)||
       (finalRgba8==JNI_TRUE&&!(desc.usage&AHARDWAREBUFFER_USAGE_GPU_FRAMEBUFFER)))
       return 0;
    if(glGetError()!=GL_NO_ERROR)return 0;
    auto getClient=iris26826EglProc<PFNEGLGETNATIVECLIENTBUFFERANDROIDPROC>(
        "eglGetNativeClientBufferANDROID");
    auto create=iris26826EglProc<PFNEGLCREATEIMAGEKHRPROC>("eglCreateImageKHR");
    auto bind=iris26826EglProc<PFNGLEGLIMAGETARGETTEXTURE2DOESPROC>(
        "glEGLImageTargetTexture2DOES");
    if(!getClient||!create||!bind)return 0;
    EGLClientBuffer client=getClient(native);if(!client)return 0;
    const EGLint attrs[]={EGL_IMAGE_PRESERVED_KHR,EGL_TRUE,EGL_NONE};
    auto *entry=new(std::nothrow) Iris26983COnImportedAhb();
    if(!entry)return 0;
    entry->display=eglGetCurrentDisplay();
    entry->image=create(entry->display,EGL_NO_CONTEXT,EGL_NATIVE_BUFFER_ANDROID,client,attrs);
    GLint old=0,unit=0;
    glGetIntegerv(GL_ACTIVE_TEXTURE,&unit);
    glActiveTexture(GL_TEXTURE0);
    glGetIntegerv(GL_TEXTURE_BINDING_2D,&old);
    bool ok=entry->image!=EGL_NO_IMAGE_KHR;
    if(ok){
        glGenTextures(1,&entry->texture);
        ok=entry->texture!=0;
        if(ok){
            glBindTexture(GL_TEXTURE_2D,entry->texture);
            bind(GL_TEXTURE_2D,entry->image);
            glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);
            glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);
            glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);
            glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);
            ok=glGetError()==GL_NO_ERROR;
        }
    }
    glBindTexture(GL_TEXTURE_2D,(GLuint)old);
    glActiveTexture((GLenum)unit);
    if(!ok){iris26983COnReleaseImportedAhb(entry);return 0;}
    return reinterpret_cast<jlong>(entry);
}
extern "C" JNIEXPORT jint JNICALL
Java_com_particlesdevs_photoncamera_processing_ultrahdr_Iris26983COnGlAhbBinding_textureNative(
    JNIEnv*,jclass,jlong ptr){
    if(!ptr||eglGetCurrentContext()==EGL_NO_CONTEXT)return 0;
    auto *entry=reinterpret_cast<Iris26983COnImportedAhb*>(ptr);
    if(entry->display!=eglGetCurrentDisplay())return 0;
    return (jint)entry->texture;
}
extern "C" JNIEXPORT void JNICALL
Java_com_particlesdevs_photoncamera_processing_ultrahdr_Iris26983COnGlAhbBinding_releaseNative(
    JNIEnv*,jclass,jlong ptr){
    if(ptr)iris26983COnReleaseImportedAhb(reinterpret_cast<Iris26983COnImportedAhb*>(ptr));
}
