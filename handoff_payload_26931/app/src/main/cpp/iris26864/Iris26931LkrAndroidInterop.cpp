// SPDX-License-Identifier: Apache-2.0
// IRIS_26931_B_SR_ON_LKR_EXACT_2_2_86_ADAPTER
// Only supplies a per-frame sensor-normalisation and zero-copy-compatible
// Android GLES texture handoff to the pinned upstream RawLens native LKR
// library. ALL burst noise, LK alignment, 3x2 solve, coverage, and finishing
// remain inside the release's verified liblkrpipeline.so; no imitated stages.
#include <jni.h>
#include <GLES3/gl3.h>
#include <android/log.h>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
void throwJava(JNIEnv* env, const char* message) {
    jclass exceptionClass=env->FindClass("java/lang/IllegalStateException");
    if(exceptionClass){env->ThrowNew(exceptionClass,message);env->DeleteLocalRef(exceptionClass);}
}
void need(bool ok, const char* message) { if(!ok)throw std::runtime_error(message); }

// These pixel-store settings may have been modified by the existing Iris
// Vulkan/AHB/GL path; restore all of them on every return and failure.
struct UnpackState {
    GLint texture=0,pbo=0,alignment=4,rowLength=0,skipRows=0,skipPixels=0;
    UnpackState() {
        glGetIntegerv(GL_TEXTURE_BINDING_2D,&texture);
        glGetIntegerv(GL_PIXEL_UNPACK_BUFFER_BINDING,&pbo);
        glGetIntegerv(GL_UNPACK_ALIGNMENT,&alignment);
        glGetIntegerv(GL_UNPACK_ROW_LENGTH,&rowLength);
        glGetIntegerv(GL_UNPACK_SKIP_ROWS,&skipRows);
        glGetIntegerv(GL_UNPACK_SKIP_PIXELS,&skipPixels);
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER,0);
        glPixelStorei(GL_UNPACK_ALIGNMENT,1);
        glPixelStorei(GL_UNPACK_ROW_LENGTH,0);
        glPixelStorei(GL_UNPACK_SKIP_ROWS,0);
        glPixelStorei(GL_UNPACK_SKIP_PIXELS,0);
    }
    ~UnpackState() {
        glBindTexture(GL_TEXTURE_2D,static_cast<GLuint>(texture));
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER,static_cast<GLuint>(pbo));
        glPixelStorei(GL_UNPACK_ALIGNMENT,alignment);
        glPixelStorei(GL_UNPACK_ROW_LENGTH,rowLength);
        glPixelStorei(GL_UNPACK_SKIP_ROWS,skipRows);
        glPixelStorei(GL_UNPACK_SKIP_PIXELS,skipPixels);
    }
};

struct FloatElements {
    JNIEnv* e; jfloatArray a; jfloat* d;
    FloatElements(JNIEnv* env,jfloatArray arr):e(env),a(arr),d(arr?env->GetFloatArrayElements(arr,nullptr):nullptr){}
    ~FloatElements(){if(d)e->ReleaseFloatArrayElements(a,d,JNI_ABORT);}
};
struct IntElements {
    JNIEnv* e; jintArray a; jint* d;
    IntElements(JNIEnv* env,jintArray arr):e(env),a(arr),d(arr?env->GetIntArrayElements(arr,nullptr):nullptr){}
    ~IntElements(){if(d)e->ReleaseIntArrayElements(a,d,JNI_ABORT);}
};
void checkedGl(const char* stage) {
    const GLenum err=glGetError();
    if(err!=GL_NO_ERROR){
      __android_log_print(ANDROID_LOG_ERROR,"Iris26931Lkr","%s: GL error 0x%x",stage,err);
      throw std::runtime_error(stage);
    }
}
}

extern "C" JNIEXPORT jobjectArray JNICALL
Java_com_hinnka_mycamera_processor_GlesIris26931LkrBridge_nativePrepare(
    JNIEnv* env,jclass,jobjectArray originals,jintArray strideBytes,
    jfloatArray phaseBlacks,jfloatArray whites,jint width,jint height) {
    std::vector<void*> allocated;
    try {
        const jsize k=originals?env->GetArrayLength(originals):0;
        need(k>=2 && k<=59 && width>=64 && height>=64 && (width%2)==0 && (height%2)==0,
             "26931 invalid frozen NORMAL RAW geometry/count");
        need(strideBytes && phaseBlacks && whites && env->GetArrayLength(strideBytes)==k &&
             env->GetArrayLength(phaseBlacks)==4*k && env->GetArrayLength(whites)==k,
             "26931 per-frame RAW provenance incomplete");
        const uint64_t n=uint64_t(width)*uint64_t(height);
        need(n<=static_cast<uint64_t>(std::numeric_limits<jlong>::max()/2) &&
             n*2 <= static_cast<uint64_t>(std::numeric_limits<jint>::max()),
             "26931 pre-normalized RAW exceeds direct buffer address range");
        IntElements st(env,strideBytes);
        FloatElements bl(env,phaseBlacks),wh(env,whites);
        need(st.d && bl.d && wh.d,"26931 RAW metadata array access failed");
        jclass bufferClass=env->FindClass("java/nio/ByteBuffer");
        need(bufferClass!=nullptr,"26931 ByteBuffer JNI class absent");
        jobjectArray result=env->NewObjectArray(k,bufferClass,nullptr);
        env->DeleteLocalRef(bufferClass);
        need(result!=nullptr,"26931 RAW buffer array allocation failed");
        for(jsize f=0;f<k;++f){
            jobject bb=env->GetObjectArrayElement(originals,f);
            const auto* src=bb?static_cast<const uint8_t*>(env->GetDirectBufferAddress(bb)):nullptr;
            const jlong capacity=bb?env->GetDirectBufferCapacity(bb):0;
            const jint rowBytes=st.d[f];
            const uint64_t last=uint64_t(height-1)*uint64_t(std::max(rowBytes,0))+uint64_t(width)*2;
            need(src && rowBytes>=width*2 && (rowBytes&1)==0 && last<=uint64_t(capacity),
                 "26931 missing/misaligned immutable RAW16 input");
            const float white=wh.d[f];
            need(std::isfinite(white) && white>1.0f && white<=65535.0f,"26931 invalid physical RAW white");
            for(int c=0;c<4;++c)need(std::isfinite(bl.d[4*f+c]) && bl.d[4*f+c]>=0.0f &&
                                     bl.d[4*f+c]<white,"26931 invalid RAW phase black");
            auto* out=static_cast<uint16_t*>(std::malloc(size_t(n*2)));
            need(out!=nullptr,"26931 fail closed: insufficient RAM for exact per-frame RAW adapter");
            allocated.push_back(out);
            for(jint y=0;y<height;++y){
                const auto* line=reinterpret_cast<const uint16_t*>(src+size_t(y)*rowBytes);
                uint16_t* dst=out+size_t(y)*width;
                const jint py=(y&1)*2;
                for(jint x=0;x<width;++x){
                    const float black=bl.d[f*4+py+(x&1)];
                    // Quantize only when the original per-frame black/white or stride
                    // cannot be passed losslessly through RawLens's shared-metadata JNI.
                    const float normal=(float(line[x])-black)/(white-black);
                    const float q=std::min(65535.0f,std::max(0.0f,normal*65535.0f));
                    dst[x]=static_cast<uint16_t>(std::lround(q));
                }
            }
            if(bb)env->DeleteLocalRef(bb);
            jobject dst=env->NewDirectByteBuffer(out,jlong(n*2));
            need(dst!=nullptr,"26931 native RAW staging ByteBuffer failed");
            env->SetObjectArrayElement(result,f,dst);
            env->DeleteLocalRef(dst);
            need(!env->ExceptionCheck(),"26931 staged RAW array insertion failed");
        }
        // Caller owns all native malloc blocks and ALWAYS frees through
        // the original RawLens SrpBridge.nativeFreeDirect, including on failure.
        allocated.clear();
        return result;
    }catch(const std::exception& e){
        for(void* p:allocated)std::free(p);
        if(!env->ExceptionCheck())throwJava(env,e.what());
        return nullptr;
    }
}

extern "C" JNIEXPORT void JNICALL
Java_com_hinnka_mycamera_processor_GlesIris26931LkrBridge_nativePublishRgba16f(
    JNIEnv* env,jclass,jobject srcBuffer,jint texture,jint width,jint height){
    try {
        need(texture>0 && width>=64 && height>=64,"26931 invalid LKR RGB destination");
        const auto* src=srcBuffer?static_cast<const float*>(env->GetDirectBufferAddress(srcBuffer)):nullptr;
        const jlong cap=srcBuffer?env->GetDirectBufferCapacity(srcBuffer):0;
        const uint64_t needBytes=uint64_t(width)*height*3*4;
        need(src && needBytes<=uint64_t(cap) && needBytes<=size_t(-1),
             "26931 LKR direct RGB buffer not full resolution");
        constexpr int rows=16;
        std::vector<float> stripe(size_t(width)*rows*4);
        checkedGl("26931 pre-RGB upload stale GL state");
        UnpackState state;
        glBindTexture(GL_TEXTURE_2D,static_cast<GLuint>(texture));
        for(jint y=0;y<height;y+=rows){
            const jint h=std::min(rows,height-y);
            const size_t n=size_t(width)*h;
            const auto* input=src+size_t(y)*width*3;
            for(size_t p=0;p<n;++p){
                const float r=input[p*3],g=input[p*3+1],b=input[p*3+2];
                need(std::isfinite(r)&&std::isfinite(g)&&std::isfinite(b)&&
                     std::fabs(r)<=65504.0f&&std::fabs(g)<=65504.0f&&std::fabs(b)<=65504.0f,
                     "26931 LKR nonfinite/half-float overflow: discard capture");
                stripe[p*4]=r;stripe[p*4+1]=g;stripe[p*4+2]=b;stripe[p*4+3]=1.0f;
            }
            glTexSubImage2D(GL_TEXTURE_2D,0,0,y,width,h,GL_RGBA,GL_FLOAT,stripe.data());
            checkedGl("26931 RGB32F to Iris RGBA16F full-extent texture upload failed");
        }
        glFlush();
        checkedGl("26931 RGB producer completion");
    }catch(const std::exception& e){if(!env->ExceptionCheck())throwJava(env,e.what());}
}

extern "C" JNIEXPORT void JNICALL
Java_com_hinnka_mycamera_processor_GlesIris26931LkrBridge_nativePublishClipR16f(
    JNIEnv* env,jclass,jobject rawBuffer,jint strideBytes,jfloatArray phaseBlacks,
    jfloat white,jint dstTexture,jint width,jint height){
    try {
        const uint64_t outW=uint64_t(width)*2,outH=uint64_t(height)*2;
        need(rawBuffer && dstTexture>0 && width>=64 && height>=64 && outW<=16384 && outH<=16384 &&
             strideBytes>=width*2 && (strideBytes&1)==0 && phaseBlacks &&
             env->GetArrayLength(phaseBlacks)==4 && std::isfinite(white) && white>1,
             "26931 invalid sensor clip provenance/extent");
        const auto* src=static_cast<const uint8_t*>(env->GetDirectBufferAddress(rawBuffer));
        const jlong cap=env->GetDirectBufferCapacity(rawBuffer);
        const uint64_t last=uint64_t(height-1)*strideBytes+uint64_t(width)*2;
        need(src && uint64_t(cap)>=last,"26931 clip reference RAW16 source truncated");
        FloatElements bl(env,phaseBlacks);
        need(bl.d!=nullptr,"26931 missing per-phase clip black levels");
        for(int i=0;i<4;++i)need(std::isfinite(bl.d[i]) && bl.d[i]>=0 && bl.d[i]<white,
                                  "26931 invalid per-phase clip level");
        constexpr jint band=32;
        std::vector<uint16_t> stripe(size_t(outW)*band);
        checkedGl("26931 pre-clip upload stale GL state");
        UnpackState state;
        glBindTexture(GL_TEXTURE_2D,static_cast<GLuint>(dstTexture));
        for(jint oy=0;oy<jint(outH);oy+=band){
            const jint nrows=std::min(band,jint(outH)-oy);
            for(jint dy=0;dy<nrows;++dy){
                const jint yy=(oy+dy)/2;
                const auto* line=reinterpret_cast<const uint16_t*>(src+size_t(yy)*strideBytes);
                const int phY=(yy&1)*2;
                uint16_t* dst=stripe.data()+size_t(dy)*outW;
                for(jint x=0;x<width;++x){
                    const float black=bl.d[phY+(x&1)];
                    const float normal=(float(line[x])-black)/(white-black);
                    const uint16_t clip=normal>=0.98f?uint16_t(0x3c00):uint16_t(0);
                    dst[2*x]=clip;dst[2*x+1]=clip;
                }
            }
            glTexSubImage2D(GL_TEXTURE_2D,0,0,oy,GLsizei(outW),nrows,GL_RED,GL_HALF_FLOAT,stripe.data());
            checkedGl("26931 original sensor clip R16F full-extent upload failed");
        }
        glFlush();
        checkedGl("26931 clip producer completion");
    }catch(const std::exception& e){if(!env->ExceptionCheck())throwJava(env,e.what());}
}
