#include <algorithm>
#include <android/bitmap.h>
#include <android/log.h>
#include <array>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstdarg>
#include <deque>
#include <mutex>
#include <thread>
#include <jni.h>
#include <EGL/egl.h>
#include <GLES3/gl31.h>
#include <cstdio>
#include <cerrno>
#include <string>
#include <turbojpeg.h>
#include <jpeglib.h>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <vector>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <limits>
#include <ultrahdr/icc.h>
#include <ultrahdr_api.h>
#include "motionv2_jpeg_r_encoder.h"
#define TAG "MotionV2Jpeg444"
/* IRIS_26513_FAST_HUFFMAN: entropy-table optimization disabled; quantization, 4:4:4 sampling and pixels unchanged. */
namespace { struct U{JNIEnv*e;jstring s;const char*c;U(JNIEnv*e,jstring s):e(e),s(s),c(s?e->GetStringUTFChars(s,nullptr):nullptr){}~U(){if(c)e->ReleaseStringUTFChars(s,c);}};
/* IRIS_26576_NATIVE_PUBLICATION_TELEMETRY_ONLY
 * Single active Motion processing is already enforced. Keep one per-native-thread summary of the
 * just-completed 26571 GPU-first / 26570 CPU-fallback publication call for Java to persist.
 */
thread_local std::string gIris26576PublicationTelemetry;
void iris26576SetPublicationTelemetry(const char*fmt,...){
    char buffer[2048];va_list args;va_start(args,fmt);vsnprintf(buffer,sizeof(buffer),fmt,args);va_end(args);
    gIris26576PublicationTelemetry=buffer;
}
bool write(const char*p,const unsigned char*d,size_t n){FILE*f=fopen(p,"wb");if(!f)return false;size_t w=fwrite(d,1,n,f);int a=fflush(f),b=fclose(f);return w==n&&a==0&&b==0;}
bool f3(JNIEnv*e,jfloatArray a,std::array<float,3>*o){if(!a||e->GetArrayLength(a)!=3)return false;e->GetFloatArrayRegion(a,0,3,o->data());return !e->ExceptionCheck();}}

namespace {
/* IRIS_26565_JPEG_BOUNDARY_DISPLAY_P3
 * Internal Photon/Iris image processing, Night Jin, UHDR ratio construction and all existing
 * appearance math remain in their proven sRGB-referred domains. Only final publication converts
 * encoded sRGB samples through linear light to Display-P3, then emits the standards-defined P3 ICC.
 */
struct DisplayP3Lut {
    std::array<float,256> decode{};
    std::array<float,16385> encode{};
    DisplayP3Lut(){
        for(size_t i=0;i<decode.size();i++){float x=(float)i/255.f;decode[i]=x<=0.04045f?x/12.92f:std::pow((x+0.055f)/1.055f,2.4f);}
        for(size_t i=0;i<encode.size();i++){float x=(float)i/(float)(encode.size()-1);encode[i]=x<=0.0031308f?12.92f*x:1.055f*std::pow(x,1.f/2.4f)-0.055f;}
    }
    float enc(float x)const{
        x=std::max(0.f,std::min(1.f,x));float q=x*(float)(encode.size()-1);int a=(int)q,b=std::min(a+1,(int)encode.size()-1);return encode[(size_t)a]+(encode[(size_t)b]-encode[(size_t)a])*(q-a);
    }
    void convert(uint8_t r8,uint8_t g8,uint8_t b8,uint8_t*out)const{
        float r=decode[r8],g=decode[g8],b=decode[b8];
        // IEC sRGB D65 -> Display-P3 D65, derived from the published primary chromaticities.
        float pr=0.8224619687f*r+0.1775380313f*g;
        float pg=0.0331941989f*r+0.9668058011f*g;
        float pb=0.0170826307f*r+0.0723974407f*g+0.9105199286f*b;
        out[0]=(uint8_t)std::lround(enc(pr)*255.f);out[1]=(uint8_t)std::lround(enc(pg)*255.f);out[2]=(uint8_t)std::lround(enc(pb)*255.f);
    }
    void convertInPlace(uint8_t*rgb)const{uint8_t o[3];convert(rgb[0],rgb[1],rgb[2],o);rgb[0]=o[0];rgb[1]=o[1];rgb[2]=o[2];}
    std::array<float,3> convertEncoded(float r,float g,float b)const{
        auto dec=[](float x){x=std::max(0.f,std::min(1.f,x));return x<=0.04045f?x/12.92f:std::pow((x+0.055f)/1.055f,2.4f);};
        float lr=dec(r),lg=dec(g),lb=dec(b);return {enc(0.8224619687f*lr+0.1775380313f*lg),enc(0.0331941989f*lr+0.9668058011f*lg),enc(0.0170826307f*lr+0.0723974407f*lg+0.9105199286f*lb)};
    }
};
const DisplayP3Lut& displayP3Lut(){static const DisplayP3Lut lut;return lut;}

bool writeDisplayP3Icc(j_compress_ptr c){
    auto icc=ultrahdr::IccHelper::writeIccProfile(UHDR_CT_SRGB,UHDR_CG_DISPLAY_P3);
    if(!icc||icc->getLength()<=ultrahdr::kICCIdentifierSize)return false;
    const size_t n=icc->getLength()-ultrahdr::kICCIdentifierSize;
    if(n>(size_t)std::numeric_limits<unsigned int>::max())return false;
    const auto*d=(const JOCTET*)icc->getData()+ultrahdr::kICCIdentifierSize;
    jpeg_write_icc_profile(c,d,(unsigned int)n);return true;
}

bool encodeRgbaBitmapP3(const char*path,const AndroidBitmapInfo&i,const uint8_t*p,int quality,bool sourceDisplayP3){
    if(!path||!p||i.width==0||i.height==0)return false;FILE*f=fopen(path,"wb");if(!f)return false;
    jpeg_compress_struct c{};jpeg_error_mgr jerr{};c.err=jpeg_std_error(&jerr);jpeg_create_compress(&c);jpeg_stdio_dest(&c,f);
    c.image_width=i.width;c.image_height=i.height;c.input_components=3;c.in_color_space=JCS_RGB;jpeg_set_defaults(&c);jpeg_set_quality(&c,std::clamp(quality,1,100),TRUE);
    for(int k=0;k<c.num_components;k++){c.comp_info[k].h_samp_factor=1;c.comp_info[k].v_samp_factor=1;}
    jpeg_start_compress(&c,TRUE);bool ok=writeDisplayP3Icc(&c);std::vector<uint8_t>row((size_t)i.width*3);const auto&lut=displayP3Lut();
    while(ok&&c.next_scanline<c.image_height){const uint8_t*src=p+(size_t)c.next_scanline*i.stride;for(size_t x=0;x<i.width;x++){if(sourceDisplayP3){row[x*3]=src[x*4];row[x*3+1]=src[x*4+1];row[x*3+2]=src[x*4+2];}else lut.convert(src[x*4],src[x*4+1],src[x*4+2],&row[x*3]);}JSAMPROW rp=row.data();ok=jpeg_write_scanlines(&c,&rp,1)==1;}
    if(ok)jpeg_finish_compress(&c);else jpeg_abort_compress(&c);jpeg_destroy_compress(&c);int a=fflush(f),b=fclose(f);return ok&&a==0&&b==0;
}
}

extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_writeNative(JNIEnv*e,jclass,jobject bitmap,jstring path,jint quality,jboolean sourceDisplayP3){AndroidBitmapInfo i{};if(!bitmap||!path||AndroidBitmap_getInfo(e,bitmap,&i)!=ANDROID_BITMAP_RESULT_SUCCESS||i.format!=ANDROID_BITMAP_FORMAT_RGBA_8888)return JNI_FALSE;void*p=nullptr;if(AndroidBitmap_lockPixels(e,bitmap,&p)!=ANDROID_BITMAP_RESULT_SUCCESS||!p)return JNI_FALSE;U u(e,path);bool ok=u.c&&encodeRgbaBitmapP3(u.c,i,(const uint8_t*)p,(int)quality,sourceDisplayP3==JNI_TRUE);AndroidBitmap_unlockPixels(e,bitmap);return ok?JNI_TRUE:JNI_FALSE;}

extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_convertSrgbToDisplayP3Native(JNIEnv*e,jclass,jobject bitmap){AndroidBitmapInfo i{};if(!bitmap||AndroidBitmap_getInfo(e,bitmap,&i)!=ANDROID_BITMAP_RESULT_SUCCESS||i.format!=ANDROID_BITMAP_FORMAT_RGBA_8888)return JNI_FALSE;void*p=nullptr;if(AndroidBitmap_lockPixels(e,bitmap,&p)!=ANDROID_BITMAP_RESULT_SUCCESS||!p)return JNI_FALSE;const auto&lut=displayP3Lut();auto*base=(uint8_t*)p;unsigned hc=std::thread::hardware_concurrency();int workers=std::max(1,std::min(4,(int)(hc?hc:2)));std::atomic<uint32_t>next{0};auto work=[&](){for(;;){uint32_t y=next.fetch_add(1);if(y>=i.height)break;uint8_t*row=base+(size_t)y*i.stride;for(uint32_t x=0;x<i.width;x++)lut.convertInPlace(row+x*4);}};std::vector<std::thread>threads;for(int n=0;n<workers;n++)threads.emplace_back(work);for(auto&t:threads)t.join();AndroidBitmap_unlockPixels(e,bitmap);return JNI_TRUE;}

namespace {
constexpr float kIris26532DetailLog2Range = 0.75f;
inline float clampf(float v,float lo,float hi){return std::max(lo,std::min(hi,v));}
inline float srgbToLinear(float x){x=clampf(x,0.f,1.f);return x<=0.04045f?x/12.92f:std::pow((x+0.055f)/1.055f,2.4f);}
inline float linearToSrgb(float x){x=std::max(x,0.f);return x<=0.0031308f?12.92f*x:1.055f*std::pow(x,1.f/2.4f)-0.055f;}
inline float detailLog2Q8(const uint8_t*detail,int w,int h,float x,float y){
    x=clampf(x,0.f,(float)std::max(0,w-1));y=clampf(y,0.f,(float)std::max(0,h-1));
    int x0=(int)std::floor(x),y0=(int)std::floor(y),x1=std::min(x0+1,w-1),y1=std::min(y0+1,h-1);
    float fx=x-x0,fy=y-y0;
    auto d=[&](int px,int py){float n=(float)detail[(size_t)py*w+px]/255.f;return (n*2.f-1.f)*kIris26532DetailLog2Range;};
    float a=d(x0,y0)+(d(x1,y0)-d(x0,y0))*fx,b=d(x0,y1)+(d(x1,y1)-d(x0,y1))*fx;
    return a+(b-a)*fy;
}
inline void bilinearBitmap(const uint8_t*base,int bw,int bh,int stride,float x,float y,float*rgb){
    x=clampf(x,0.f,(float)std::max(0,bw-1)); y=clampf(y,0.f,(float)std::max(0,bh-1));
    int x0=(int)std::floor(x),y0=(int)std::floor(y),x1=std::min(x0+1,bw-1),y1=std::min(y0+1,bh-1);float fx=x-x0,fy=y-y0;
    const uint8_t*p00=base+(size_t)y0*stride+x0*4,*p10=base+(size_t)y0*stride+x1*4,*p01=base+(size_t)y1*stride+x0*4,*p11=base+(size_t)y1*stride+x1*4;
    for(int c=0;c<3;c++){float a=p00[c]+(p10[c]-p00[c])*fx,b=p01[c]+(p11[c]-p01[c])*fx;rgb[c]=(a+(b-a)*fy)/255.f;}
}
/* Map a final-oriented native pixel back to the unrotated MotionV2Render output. This mirrors
 * addwatermark_rotate.glsl's crop/rotation geometry without materializing a 50 MP bitmap. */
inline void finalToUnrotated(float bx,float by,int rawW,int rawH,int cropW,int cropH,int rotation,bool mirror,float*outX,float*outY){
    float x=bx,y=by;
    switch(rotation){
        case 90: { // shader rotate=3
            float sx=y; float sy=(float)rawH-x;
            x=sx; y=sy; break;
        }
        case 180: { x=(float)rawW-x; y=(float)rawH-y; break; }
        case 270: { // shader rotate=1
            float xx=x+(float)(rawH-cropH); if(mirror) xx=(float)cropH-xx;
            float sx=(float)rawW-y; float sy=xx; x=sx; y=sy; return;
        }
        default: { y+=(float)(rawH-cropH); if(mirror)y=(float)rawH-y; break; }
    }
    if(rotation==90){ if(mirror){/* horizontal output mirror maps to vertical source flip */ y=(float)rawH-y;} }
    else if(rotation==180){ if(mirror)y=(float)rawH-y; }
    *outX=x;*outY=y;
}
}

/* IRIS_26564_TRUE_2X_CPU_REFERENCE_BACKEND
 * Canonical CPU implementation of the same direct-CFA Sabre RBF estimator used by the GLES
 * accelerator. The input evidence is already frozen by the proven Sabre owner: sparse flow,
 * packed covariance and rejection. No alignment, sharpening, native-RGB interpolation or device
 * model policy exists here. Accumulation is tile-local and therefore memory bounded.
 */
namespace iris26564 {
inline float halfToFloat(uint16_t h){
    uint32_t sign=(uint32_t)(h&0x8000u)<<16,exp=(h>>10)&0x1fu,mant=h&0x03ffu,bits;
    if(exp==0){
        if(mant==0)bits=sign;
        else{
            int e=-14;while((mant&0x0400u)==0){mant<<=1;--e;}mant&=0x03ffu;
            bits=sign|(uint32_t)(e+127)<<23|(mant<<13);
        }
    }else if(exp==31)bits=sign|0x7f800000u|(mant<<13);
    else bits=sign|((exp+112u)<<23)|(mant<<13);
    float f;std::memcpy(&f,&bits,sizeof(f));return f;
}
inline uint16_t floatToHalf(float f){
    uint32_t x;std::memcpy(&x,&f,sizeof(x));uint32_t sign=(x>>16)&0x8000u;
    int exp=(int)((x>>23)&0xffu)-127+15;uint32_t mant=x&0x7fffffu;
    if(((x>>23)&0xffu)==0xffu)return (uint16_t)(sign|(mant?0x7e00u:0x7c00u));
    if(exp<=0){
        if(exp<-10)return (uint16_t)sign;
        mant=(mant|0x800000u)>>(1-exp);if(mant&0x1000u)mant+=0x2000u;
        return (uint16_t)(sign|(mant>>13));
    }
    if(exp>=31)return (uint16_t)(sign|0x7c00u);
    if(mant&0x1000u){mant+=0x2000u;if(mant&0x800000u){mant=0;++exp;if(exp>=31)return (uint16_t)(sign|0x7c00u);}}
    return (uint16_t)(sign|((uint32_t)exp<<10)|(mant>>13));
}
inline float smooth01(float t){t=clampf(t,0.f,1.f);return t*t*(3.f-2.f*t);}
inline int clampi(int v,int lo,int hi){return std::max(lo,std::min(hi,v));}
inline float mirrorCoord(float u,float border){
    if(u<=border)u=2.f*border-u;
    if(u>1.f-border)u=2.f*(1.f-border)-u;
    return clampf(u,0.f,1.f);
}
struct Flow4{float x,y,z,w;};
inline Flow4 flowFetch(const uint16_t*data,int w,int h,int x,int y){
    x=clampi(x,0,w-1);y=clampi(y,0,h-1);const uint16_t*p=data+((size_t)y*w+x)*4;
    return {halfToFloat(p[0]),halfToFloat(p[1]),halfToFloat(p[2]),halfToFloat(p[3])};
}
inline Flow4 flowSample(const uint16_t*data,int w,int h,float u,float v){
    float x=clampf(u*(float)w-0.5f,0.f,(float)(w-1)),y=clampf(v*(float)h-0.5f,0.f,(float)(h-1));
    int x0=(int)floorf(x),y0=(int)floorf(y),x1=std::min(x0+1,w-1),y1=std::min(y0+1,h-1);float fx=x-x0,fy=y-y0;
    Flow4 a=flowFetch(data,w,h,x0,y0),b=flowFetch(data,w,h,x1,y0),c=flowFetch(data,w,h,x0,y1),d=flowFetch(data,w,h,x1,y1),o{};
    const float av[4]={a.x,a.y,a.z,a.w},bv[4]={b.x,b.y,b.z,b.w},cv[4]={c.x,c.y,c.z,c.w},dv[4]={d.x,d.y,d.z,d.w};float*ov=&o.x;
    for(int k=0;k<4;k++){float r0=av[k]+(bv[k]-av[k])*fx,r1=cv[k]+(dv[k]-cv[k])*fx;ov[k]=r0+(r1-r0)*fy;}return o;
}
inline void unpackRgb10a2(uint32_t word,float out[3]){out[0]=(float)(word&1023u)/1023.f;out[1]=(float)((word>>10)&1023u)/1023.f;out[2]=(float)((word>>20)&1023u)/1023.f;}
inline void covFetch(const uint32_t*data,int w,int h,int x,int y,float out[3]){x=clampi(x,0,w-1);y=clampi(y,0,h-1);unpackRgb10a2(data[(size_t)y*w+x],out);}
inline void covSample(const uint32_t*data,int regionW,int regionH,int originX,int originY,int fullW,int fullH,float u,float v,float out[3]){
    float gx=clampf(u*(float)fullW-0.5f,0.f,(float)(fullW-1))-(float)originX;
    float gy=clampf(v*(float)fullH-0.5f,0.f,(float)(fullH-1))-(float)originY;
    gx=clampf(gx,0.f,(float)(regionW-1));gy=clampf(gy,0.f,(float)(regionH-1));int x0=(int)floorf(gx),y0=(int)floorf(gy),x1=std::min(x0+1,regionW-1),y1=std::min(y0+1,regionH-1);float fx=gx-x0,fy=gy-y0;
    float a[3],b[3],c[3],d[3];covFetch(data,regionW,regionH,x0,y0,a);covFetch(data,regionW,regionH,x1,y0,b);covFetch(data,regionW,regionH,x0,y1,c);covFetch(data,regionW,regionH,x1,y1,d);
    for(int k=0;k<3;k++){float r0=a[k]+(b[k]-a[k])*fx,r1=c[k]+(d[k]-c[k])*fx;out[k]=r0+(r1-r0)*fy;}
}
inline float rejectionSample(const uint8_t*data,int regionW,int regionH,int originX,int originY,int fullW,int fullH,float u,float v){
    if(!data)return 1.f;float gx=clampf(u*(float)fullW-0.5f,0.f,(float)(fullW-1))-(float)originX,gy=clampf(v*(float)fullH-0.5f,0.f,(float)(fullH-1))-(float)originY;
    gx=clampf(gx,0.f,(float)(regionW-1));gy=clampf(gy,0.f,(float)(regionH-1));int x0=(int)floorf(gx),y0=(int)floorf(gy),x1=std::min(x0+1,regionW-1),y1=std::min(y0+1,regionH-1);float fx=gx-x0,fy=gy-y0;
    auto at=[&](int x,int y){return (float)data[(size_t)y*regionW+x]/255.f;};float r0=at(x0,y0)+(at(x1,y0)-at(x0,y0))*fx,r1=at(x0,y1)+(at(x1,y1)-at(x0,y1))*fx;return r0+(r1-r0)*fy;
}
inline uint16_t rawFetch(const uint16_t*data,int regionW,int regionH,int rowStrideSamples,int originX,int originY,int fullW,int fullH,int x,int y){
    x=clampi(x,0,fullW-1)-originX;y=clampi(y,0,fullH-1)-originY;x=clampi(x,0,regionW-1);y=clampi(y,0,regionH-1);return data[(size_t)y*rowStrideSamples+x];
}
inline void swizzle4(const float in[4],int type,float out[4]){static const int map[4][4]={{0,1,2,3},{1,0,3,2},{2,3,0,1},{3,2,1,0}};for(int i=0;i<4;i++)out[i]=in[map[type&3][i]];}
inline float kernelWeight(float dx,float dy,const float c[3]){float d=dx*dx*c[0]+dy*dy*c[1]+dx*dy*c[2]*2.f;return std::exp2(-0.5f*d)+0.00005f;}
inline void sampleRbf(const uint16_t*raw,int regionW,int regionH,int rowStrideSamples,int originX,int originY,int fullW,int fullH,float sx,float sy,int cfa,const float gains[4],const float black[4],const float cov[3],float color[3],float weightOut[3]){
    int px=(int)floorf(sx),py=(int)floorf(sy);float bayer[3][3],weights[3][3];
    for(int ix=0;ix<3;ix++)for(int iy=0;iy<3;iy++)bayer[ix][iy]=(float)rawFetch(raw,regionW,regionH,rowStrideSamples,originX,originY,fullW,fullH,px+ix-1,py+iy-1);
    float subx=floorf(sx)+0.5f-sx,suby=floorf(sy)+0.5f-sy;for(int i=-1;i<=1;i++)for(int j=-1;j<=1;j++)weights[i+1][j+1]=kernelWeight(subx+(float)i,suby+(float)j,cov);
    int offx=0,offy=0;if(cfa==0){offx=1;offy=1;}else if(cfa==1){offx=0;offy=1;}else if(cfa==2){offx=1;offy=0;}
    int type=(((py+offy)&1)<<1)+((px+offx)&1);float rg[4],rb[4];swizzle4(gains,type,rg);swizzle4(black,type,rb);
    float cornerW[4]={weights[0][0],weights[0][2],weights[2][0],weights[2][2]},cornerV[4]={bayer[0][0],bayer[0][2],bayer[2][0],bayer[2][2]};
    float udW[2]={weights[1][0],weights[1][2]},udV[2]={bayer[1][0],bayer[1][2]},lrW[2]={weights[0][1],weights[2][1]},lrV[2]={bayer[0][1],bayer[2][1]};
    float tmpI[4]={0,0,0,0},tmpW[4]={0,0,0,0};
    for(int i=0;i<4;i++){tmpI[0]+=(cornerV[i]*rg[0]+rb[0])*cornerW[i];tmpW[0]+=cornerW[i];}
    for(int i=0;i<2;i++){tmpI[1]+=(udV[i]*rg[1]+rb[1])*udW[i];tmpW[1]+=udW[i];tmpI[2]+=(lrV[i]*rg[2]+rb[2])*lrW[i];tmpW[2]+=lrW[i];}
    tmpI[3]=(bayer[1][1]*rg[3]+rb[3])*weights[1][1];tmpW[3]=weights[1][1];float I[4],W[4];swizzle4(tmpI,type,I);swizzle4(tmpW,type,W);
    color[0]=I[0];color[1]=I[1]+I[2];color[2]=I[3];weightOut[0]=W[0];weightOut[1]=W[1]+W[2];weightOut[2]=W[3];
}
inline void lensSample(const float*map,int w,int h,float u,float v,float out[4]){
    if(!map||w<=0||h<=0){for(int k=0;k<4;k++)out[k]=1.f;return;}float x=clampf(u*(float)w-0.5f,0.f,(float)(w-1)),y=clampf(v*(float)h-0.5f,0.f,(float)(h-1));int x0=(int)floorf(x),y0=(int)floorf(y),x1=std::min(x0+1,w-1),y1=std::min(y0+1,h-1);float fx=x-x0,fy=y-y0;
    for(int k=0;k<4;k++){auto at=[&](int xx,int yy){float z=map[((size_t)yy*w+xx)*4+k];return std::isfinite(z)&&z>0.f?z:1.f;};float a=at(x0,y0)+(at(x1,y0)-at(x0,y0))*fx,b=at(x0,y1)+(at(x1,y1)-at(x0,y1))*fx;out[k]=a+(b-a)*fy;}
}
}

extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_IrisTrue2xSrNative_accumulateCpuTileFrame(
        JNIEnv*e,jclass,jobject accumBuffer,jobject phaseBuffer,jint tileW,jint tileH,jint outX,jint outY,jint fullOutW,jint fullOutH,
        jobject rawBuffer,jint rawX,jint rawY,jint rawW,jint rawH,jint rawRowStrideSamples,jobject flowBuffer,jint flowW,jint flowH,jfloat flowScaleX,jfloat flowScaleY,jfloat flowOffsetX,jfloat flowOffsetY,
        jobject covBuffer,jint covX,jint covY,jint covW,jint covH,jint covFullW,jint covFullH,jobject rejectionBuffer,jint rejX,jint rejY,jint rejW,jint rejH,jint rejFullW,jint rejFullH,
        jint fullRawW,jint fullRawH,jint cfa,jfloatArray gainsArray,jfloatArray blackArray,jfloatArray covRgArray,jfloatArray covBArray,jboolean useWeight,jfloat rawClipThreshold){
    if(!accumBuffer||!phaseBuffer||!rawBuffer||!flowBuffer||!covBuffer||
       tileW<=0||tileH<=0||fullOutW<=0||fullOutH<=0||fullRawW<=0||fullRawH<=0||
       outX<0||outY<0||outX>fullOutW-tileW||outY>fullOutH-tileH||
       rawX<0||rawY<0||rawW<=0||rawH<=0||rawX>fullRawW-rawW||rawY>fullRawH-rawH||
       rawRowStrideSamples<rawW||flowW<=0||flowH<=0||covW<=0||covH<=0||
       covFullW<=0||covFullH<=0||covX<0||covY<0||covX>covFullW-covW||covY>covFullH-covH||
       cfa<0||cfa>3)return JNI_FALSE;
    if(useWeight==JNI_TRUE&&(!rejectionBuffer||rejW<=0||rejH<=0||rejFullW<=0||rejFullH<=0||
       rejX<0||rejY<0||rejX>rejFullW-rejW||rejY>rejFullH-rejH))return JNI_FALSE;
    auto*acc=(float*)e->GetDirectBufferAddress(accumBuffer);auto*phase=(uint8_t*)e->GetDirectBufferAddress(phaseBuffer);auto*raw=(const uint16_t*)e->GetDirectBufferAddress(rawBuffer);auto*flow=(const uint16_t*)e->GetDirectBufferAddress(flowBuffer);auto*cov=(const uint32_t*)e->GetDirectBufferAddress(covBuffer);auto*rej=rejectionBuffer?(const uint8_t*)e->GetDirectBufferAddress(rejectionBuffer):nullptr;
    if(!acc||!phase||!raw||!flow||!cov||(useWeight==JNI_TRUE&&!rej))return JNI_FALSE;
    const jlong accumulatorBytes=(jlong)tileW*tileH*10*(jlong)sizeof(float);
    const jlong rawBytes=((jlong)(rawH-1)*rawRowStrideSamples+rawW)*(jlong)sizeof(uint16_t);
    const jlong flowBytes=(jlong)flowW*flowH*4*(jlong)sizeof(uint16_t);
    const jlong covarianceBytes=(jlong)covW*covH*(jlong)sizeof(uint32_t);
    if(e->GetDirectBufferCapacity(accumBuffer)<accumulatorBytes||
       e->GetDirectBufferCapacity(phaseBuffer)<(jlong)tileW*tileH||
       e->GetDirectBufferCapacity(rawBuffer)<rawBytes||
       e->GetDirectBufferCapacity(flowBuffer)<flowBytes||
       e->GetDirectBufferCapacity(covBuffer)<covarianceBytes||
       (useWeight==JNI_TRUE&&e->GetDirectBufferCapacity(rejectionBuffer)<(jlong)rejW*rejH))return JNI_FALSE;
    float gains[4],black[4],crg[4],cb[2];if(!gainsArray||!blackArray||!covRgArray||!covBArray||e->GetArrayLength(gainsArray)!=4||e->GetArrayLength(blackArray)!=4||e->GetArrayLength(covRgArray)!=4||e->GetArrayLength(covBArray)!=2)return JNI_FALSE;
    e->GetFloatArrayRegion(gainsArray,0,4,gains);e->GetFloatArrayRegion(blackArray,0,4,black);e->GetFloatArrayRegion(covRgArray,0,4,crg);e->GetFloatArrayRegion(covBArray,0,2,cb);if(e->ExceptionCheck())return JNI_FALSE;
    const float borderX=1.5f/(float)fullRawW,borderY=1.5f/(float)fullRawH;
    for(int ly=0;ly<tileH;ly++)for(int lx=0;lx<tileW;lx++){
        int gx=outX+lx,gy=outY+ly;float refU=((float)gx+0.5f)/(float)fullOutW,refV=((float)gy+0.5f)/(float)fullOutH;
        iris26564::Flow4 fv=iris26564::flowSample(flow,flowW,flowH,refU*flowScaleX+flowOffsetX,refV*flowScaleY+flowOffsetY);
        float su=iris26564::mirrorCoord(refU+fv.x,borderX),sv=iris26564::mirrorCoord(refV+fv.y,borderY);float packed[3],c[3];iris26564::covSample(cov,covW,covH,covX,covY,covFullW,covFullH,su,sv,packed);c[0]=packed[0]*crg[1]+crg[0];c[1]=packed[1]*crg[3]+crg[2];c[2]=packed[2]*cb[1]+cb[0];
        float color[3],weights[3];iris26564::sampleRbf(raw,rawW,rawH,rawRowStrideSamples,rawX,rawY,fullRawW,fullRawH,su*(float)fullRawW,sv*(float)fullRawH,cfa,gains,black,c,color,weights);float fw=useWeight==JNI_TRUE?iris26564::rejectionSample(rej,rejW,rejH,rejX,rejY,rejFullW,rejFullH,refU,refV):1.f;
        int centerX=iris26564::clampi((int)floorf(su*(float)fullRawW),0,fullRawW-1),centerY=iris26564::clampi((int)floorf(sv*(float)fullRawH),0,fullRawH-1);float sourceRawPeak=0.f;for(int ry=-1;ry<=1;ry++)for(int rx=-1;rx<=1;rx++){int xx=iris26564::clampi(centerX+rx,0,fullRawW-1),yy=iris26564::clampi(centerY+ry,0,fullRawH-1);int localX=iris26564::clampi(xx-rawX,0,rawW-1),localY=iris26564::clampi(yy-rawY,0,rawH-1);sourceRawPeak=std::max(sourceRawPeak,(float)raw[(size_t)localY*rawRowStrideSamples+localX]);}
        size_t q=((size_t)ly*tileW+lx)*10;for(int k=0;k<3;k++){acc[q+k]+=color[k]*fw;acc[q+3+k]+=weights[k]*fw;}
        const bool temporalReliable=fw>0.08f&&std::isfinite(rawClipThreshold)&&sourceRawPeak<rawClipThreshold;
        if(temporalReliable){
            float frameRgb[3];for(int k=0;k<3;k++)frameRgb[k]=color[k]/std::max(weights[k],1.0e-7f);
            float frameY=clampf(0.25f*frameRgb[0]+0.50f*frameRgb[1]+0.25f*frameRgb[2],0.f,4.f);
            acc[q+6]+=frameY*fw;acc[q+7]+=frameY*frameY*fw;acc[q+8]+=fw;acc[q+9]+=fw*fw;
            float fx=fv.x*(float)fullRawW,fy=fv.y*(float)fullRawH;float px=fx-floorf(fx),py=fy-floorf(fy);int bin=(px>=0.5f?1:0)+(py>=0.5f?2:0);phase[(size_t)ly*tileW+lx]|=(uint8_t)(1u<<bin);
        }
    }
    return JNI_TRUE;
}

extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_IrisTrue2xSrNative_resolveCpuTile(
        JNIEnv*e,jclass,jobject accumBuffer,jobject outputBuffer,jint tileW,jint tileH,jint outX,jint outY,jint fullOutW,jint fullOutH,jfloatArray cameraScaleArray,jfloatArray lensArray,jint lensW,jint lensH){
    auto*acc=(const float*)e->GetDirectBufferAddress(accumBuffer);auto*out=(uint16_t*)e->GetDirectBufferAddress(outputBuffer);
    if(!acc||!out||tileW<=0||tileH<=0||fullOutW<=0||fullOutH<=0||
       outX<0||outY<0||outX>fullOutW-tileW||outY>fullOutH-tileH)return JNI_FALSE;
    if(e->GetDirectBufferCapacity(accumBuffer)<(jlong)tileW*tileH*10*(jlong)sizeof(float)||
       e->GetDirectBufferCapacity(outputBuffer)<(jlong)tileW*tileH*3*(jlong)sizeof(uint16_t))return JNI_FALSE;float scale[3];if(!cameraScaleArray||e->GetArrayLength(cameraScaleArray)!=3)return JNI_FALSE;e->GetFloatArrayRegion(cameraScaleArray,0,3,scale);if(e->ExceptionCheck())return JNI_FALSE;
    std::vector<float> lens;if(lensArray&&lensW>0&&lensH>0){jsize n=e->GetArrayLength(lensArray);if(n<lensW*lensH*4)return JNI_FALSE;lens.resize((size_t)lensW*lensH*4);e->GetFloatArrayRegion(lensArray,0,(jsize)lens.size(),lens.data());if(e->ExceptionCheck())return JNI_FALSE;}
    for(int ly=0;ly<tileH;ly++)for(int lx=0;lx<tileW;lx++){size_t i=(size_t)ly*tileW+lx,q=i*10,o=i*3;float rgb[3];for(int k=0;k<3;k++)rgb[k]=std::max(0.f,acc[q+k]/std::max(acc[q+3+k],1.0e-7f))*scale[k];float u=((float)(outX+lx)+0.5f)/(float)fullOutW,v=((float)(outY+ly)+0.5f)/(float)fullOutH,ls[4];iris26564::lensSample(lens.empty()?nullptr:lens.data(),lensW,lensH,u,v,ls);rgb[0]*=ls[0];rgb[1]*=0.5f*(ls[1]+ls[2]);rgb[2]*=ls[3];for(int k=0;k<3;k++)out[o+k]=iris26564::floatToHalf(std::max(rgb[k],0.f));}
    return JNI_TRUE;
}


/* IRIS_26564_TRUE2X_NATIVE_VGN_CHROMA_TRANSFER
 * Preserve the proven native Sabre/VGN + 26561 camera-chroma decision without allocating a
 * 50 MP recursive VGN surface. The native guide and true-2x carrier are both RGB16F camera RGB.
 * A bounded two-row native correction field is derived from the guide minus the 2x2 average of
 * the direct reconstruction, after removing 0.25/0.50/0.25 camera luma from both. Bilinear
 * interpolation of that zero-luma correction retains true-2x luma and high-frequency residuals.
 */
extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_IrisTrue2xSrNative_applyNativeVgnChromaGuide(
        JNIEnv*e,jclass,jstring truePath,jint trueW,jint trueH,jstring guidePath,jint guideW,jint guideH){
    if(!truePath||!guidePath||trueW<=0||trueH<=0||guideW<=0||guideH<=0||
       trueW!=guideW*2||trueH!=guideH*2)return JNI_FALSE;
    U tp(e,truePath),gp(e,guidePath);if(!tp.c||!gp.c)return JNI_FALSE;
    int tfd=open(tp.c,O_RDWR),gfd=open(gp.c,O_RDONLY);if(tfd<0||gfd<0){if(tfd>=0)close(tfd);if(gfd>=0)close(gfd);return JNI_FALSE;}
    struct stat ts{},gs{};const uint64_t tBytes=(uint64_t)trueW*(uint64_t)trueH*6ull;
    const uint64_t gBytes=(uint64_t)guideW*(uint64_t)guideH*6ull;
    if(fstat(tfd,&ts)!=0||fstat(gfd,&gs)!=0||(uint64_t)ts.st_size!=tBytes||(uint64_t)gs.st_size!=gBytes){close(tfd);close(gfd);return JNI_FALSE;}
    auto readExact=[](int fd,void*dst,size_t bytes,off_t offset)->bool{
        auto*p=(uint8_t*)dst;size_t done=0;while(done<bytes){ssize_t n=pread(fd,p+done,bytes-done,offset+(off_t)done);if(n<=0)return false;done+=(size_t)n;}return true;
    };
    auto writeExact=[](int fd,const void*src,size_t bytes,off_t offset)->bool{
        const auto*p=(const uint8_t*)src;size_t done=0;while(done<bytes){ssize_t n=pwrite(fd,p+done,bytes-done,offset+(off_t)done);if(n<=0)return false;done+=(size_t)n;}return true;
    };
    using Corr=std::array<float,3>;
    std::vector<uint16_t> guideRow((size_t)guideW*3),srcA((size_t)trueW*3),srcB((size_t)trueW*3),outRow((size_t)trueW*3);
    auto loadCorrectionRow=[&](int gy,std::vector<Corr>&corr)->bool{
        gy=iris26564::clampi(gy,0,guideH-1);corr.resize((size_t)guideW);
        const size_t gb=(size_t)guideW*3*sizeof(uint16_t),tb=(size_t)trueW*3*sizeof(uint16_t);
        if(!readExact(gfd,guideRow.data(),gb,(off_t)gy*(off_t)gb))return false;
        int y0=std::min(gy*2,trueH-1),y1=std::min(y0+1,trueH-1);
        if(!readExact(tfd,srcA.data(),tb,(off_t)y0*(off_t)tb)||!readExact(tfd,srcB.data(),tb,(off_t)y1*(off_t)tb))return false;
        for(int gx=0;gx<guideW;gx++){
            float g[3],a[3]={0.f,0.f,0.f};
            for(int k=0;k<3;k++){
                g[k]=iris26564::halfToFloat(guideRow[(size_t)gx*3+k]);
                int x0=std::min(gx*2,trueW-1),x1=std::min(x0+1,trueW-1);
                a[k]=0.25f*(iris26564::halfToFloat(srcA[(size_t)x0*3+k])+
                            iris26564::halfToFloat(srcA[(size_t)x1*3+k])+
                            iris26564::halfToFloat(srcB[(size_t)x0*3+k])+
                            iris26564::halfToFloat(srcB[(size_t)x1*3+k]));
                if(!std::isfinite(g[k])||!std::isfinite(a[k]))return false;
            }
            float gyv=0.25f*g[0]+0.50f*g[1]+0.25f*g[2],ay=0.25f*a[0]+0.50f*a[1]+0.25f*a[2];
            for(int k=0;k<3;k++)corr[(size_t)gx][k]=(g[k]-gyv)-(a[k]-ay);
        }
        return true;
    };
    auto applyOutputRow=[&](int oy,const std::vector<Corr>&cy0,const std::vector<Corr>&cy1,float fy)->bool{
        const size_t rowBytes=(size_t)trueW*3*sizeof(uint16_t);if(!readExact(tfd,outRow.data(),rowBytes,(off_t)oy*(off_t)rowBytes))return false;
        for(int ox=0;ox<trueW;ox++){
            float sx=((float)ox+0.5f)*0.5f-0.5f;sx=clampf(sx,0.f,(float)(guideW-1));int x0=(int)floorf(sx),x1=std::min(x0+1,guideW-1);float fx=sx-(float)x0;
            for(int k=0;k<3;k++){
                float c0=cy0[(size_t)x0][k]+(cy0[(size_t)x1][k]-cy0[(size_t)x0][k])*fx;
                float c1=cy1[(size_t)x0][k]+(cy1[(size_t)x1][k]-cy1[(size_t)x0][k])*fx;
                float delta=c0+(c1-c0)*fy;size_t q=(size_t)ox*3+k;float v=iris26564::halfToFloat(outRow[q]);if(!std::isfinite(v)||!std::isfinite(delta))return false;
                outRow[q]=iris26564::floatToHalf(std::max(v+delta,0.f));
            }
        }
        return writeExact(tfd,outRow.data(),rowBytes,(off_t)oy*(off_t)rowBytes);
    };
    std::vector<Corr> prev,curr,next;
    bool ok=loadCorrectionRow(0,curr);if(ok)prev=curr;
    if(ok)ok=loadCorrectionRow(std::min(1,guideH-1),next);
    for(int gy=0;ok&&gy<guideH;gy++){
        const int even=gy*2,odd=even+1;
        ok=applyOutputRow(even,prev,curr,gy==0?0.f:0.75f);
        if(ok)ok=applyOutputRow(odd,curr,next,gy+1<guideH?0.25f:0.f);
        if(gy+1<guideH){prev=std::move(curr);curr=std::move(next);if(gy+2<guideH)ok=loadCorrectionRow(gy+2,next);else next=curr;}
    }
    int syncRc=ok?fsync(tfd):-1;close(tfd);close(gfd);return (ok&&syncRc==0)?JNI_TRUE:JNI_FALSE;
}


/* IRIS_26573_CROSS_FRAME_TRUE_DETAIL_LUMA_OWNER
 * Native Sabre Resolve + VGN remains the sole RGB/chroma/highlight and low-frequency identity owner.
 * Direct-CFA true2x contributes only bounded temporally-proven zero-mean 2x2 luminance microstructure. The CPU
 * fallback mirrors the GPU contract exactly; unsafe block evidence yields factor 1.0 exactly.
 */
extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_IrisTrue2xSrNative_prepareVgnGuidedRenderTile(
        JNIEnv*e,jclass,jstring truePath,jint trueW,jint trueH,jstring guidePath,jint guideW,jint guideH,
        jstring phasePath,jint regionX,jint regionY,jint regionW,jint regionH,jobject outputBuffer,jlongArray detailStats){
    if(!truePath||!guidePath||!phasePath||!outputBuffer||!detailStats||e->GetArrayLength(detailStats)<9||
       trueW<=1||trueH<=1||guideW<=0||guideH<=0||trueW!=guideW*2||trueH!=guideH*2||
       regionX<0||regionY<0||regionW<=0||regionH<=0||regionX>trueW-regionW||regionY>trueH-regionH)return JNI_FALSE;
    auto*out=(uint16_t*)e->GetDirectBufferAddress(outputBuffer);jlong cap=e->GetDirectBufferCapacity(outputBuffer);
    const jlong required=(jlong)regionW*regionH*4*(jlong)sizeof(uint16_t);if(!out||cap<required)return JNI_FALSE;
    U tp(e,truePath),gp(e,guidePath),pp(e,phasePath);if(!tp.c||!gp.c||!pp.c)return JNI_FALSE;
    int tfd=open(tp.c,O_RDONLY),gfd=open(gp.c,O_RDONLY),pfd=open(pp.c,O_RDONLY);
    if(tfd<0||gfd<0||pfd<0){if(tfd>=0)close(tfd);if(gfd>=0)close(gfd);if(pfd>=0)close(pfd);return JNI_FALSE;}
    struct stat ts{},gs{},ps{};const uint64_t tBytes=(uint64_t)trueW*(uint64_t)trueH*6ull,
        gBytes=(uint64_t)guideW*(uint64_t)guideH*6ull,pBytes=(uint64_t)trueW*(uint64_t)trueH;
    if(fstat(tfd,&ts)!=0||fstat(gfd,&gs)!=0||fstat(pfd,&ps)!=0||(uint64_t)ts.st_size!=tBytes||
       (uint64_t)gs.st_size!=gBytes||(uint64_t)ps.st_size!=pBytes){close(tfd);close(gfd);close(pfd);return JNI_FALSE;}
    auto readExact=[](int fd,void*dst,size_t bytes,off_t offset)->bool{auto*p=(uint8_t*)dst;size_t done=0;while(done<bytes){ssize_t n=pread(fd,p+done,bytes-done,offset+(off_t)done);if(n<=0)return false;done+=(size_t)n;}return true;};
    const int ex0=std::max(0,regionX-2),ey0=std::max(0,regionY-2),ex1=std::min((int)trueW,regionX+regionW+2),ey1=std::min((int)trueH,regionY+regionH+2);
    const int ew=ex1-ex0,eh=ey1-ey0;std::vector<uint16_t>direct((size_t)ew*eh*3);std::vector<uint8_t>support((size_t)regionW*regionH);
    for(int y=0;y<eh;y++)if(!readExact(tfd,direct.data()+(size_t)y*ew*3,(size_t)ew*6,((off_t)(ey0+y)*trueW+ex0)*6)){close(tfd);close(gfd);close(pfd);return JNI_FALSE;}
    for(int y=0;y<regionH;y++)if(!readExact(pfd,support.data()+(size_t)y*regionW,(size_t)regionW,(off_t)(regionY+y)*trueW+regionX)){close(tfd);close(gfd);close(pfd);return JNI_FALSE;}
    const int gx0=std::max(0,(regionX/2)-2),gy0=std::max(0,(regionY/2)-2),gx1=std::min((int)guideW,(regionX+regionW+1)/2+2),gy1=std::min((int)guideH,(regionY+regionH+1)/2+2);
    const int gw=gx1-gx0,gh=gy1-gy0;std::vector<uint16_t>guide((size_t)gw*gh*3);
    for(int y=0;y<gh;y++)if(!readExact(gfd,guide.data()+(size_t)y*gw*3,(size_t)gw*6,((off_t)(gy0+y)*guideW+gx0)*6)){close(tfd);close(gfd);close(pfd);return JNI_FALSE;}
    auto dAt=[&](int x,int y)->std::array<float,3>{x=iris26564::clampi(x,0,trueW-1);y=iris26564::clampi(y,0,trueH-1);size_t q=((size_t)(y-ey0)*ew+(x-ex0))*3;return {iris26564::halfToFloat(direct[q]),iris26564::halfToFloat(direct[q+1]),iris26564::halfToFloat(direct[q+2])};};
    auto gAt=[&](int x,int y)->std::array<float,3>{x=iris26564::clampi(x,0,guideW-1);y=iris26564::clampi(y,0,guideH-1);size_t q=((size_t)(y-gy0)*gw+(x-gx0))*3;return {iris26564::halfToFloat(guide[q]),iris26564::halfToFloat(guide[q+1]),iris26564::halfToFloat(guide[q+2])};};
    auto packedSupportAt=[&](int x,int y)->uint8_t{x=iris26564::clampi(x,regionX,regionX+regionW-1);y=iris26564::clampi(y,regionY,regionY+regionH-1);return support[(size_t)(y-regionY)*regionW+(x-regionX)];};
    auto supportAt=[&](int x,int y)->int{return std::min(4,(int)(packedSupportAt(x,y)&0x07u));};
    auto temporalAt=[&](int x,int y)->float{return (float)((packedSupportAt(x,y)>>3)&0x1fu)/31.f;};
    auto lum=[](const std::array<float,3>&v){return 0.25f*v[0]+0.50f*v[1]+0.25f*v[2];};
    auto peak3=[](const std::array<float,3>&v){return std::max(v[0],std::max(v[1],v[2]));};
    auto chroma=[&](const std::array<float,3>&v){float sum=std::max(v[0]+v[1]+v[2],1.0e-5f);return std::array<float,3>{v[0]/sum,v[1]/sum,v[2]/sum};};
    auto bilGuide=[&](int ox,int oy){float sx=clampf(((float)ox+0.5f)*0.5f-0.5f,0.f,(float)(guideW-1)),sy=clampf(((float)oy+0.5f)*0.5f-0.5f,0.f,(float)(guideH-1));int x0=(int)floorf(sx),y0=(int)floorf(sy),x1=std::min(x0+1,guideW-1),y1=std::min(y0+1,guideH-1);float fx=sx-x0,fy=sy-y0;auto a=gAt(x0,y0),b=gAt(x1,y0),c=gAt(x0,y1),d=gAt(x1,y1);std::array<float,3>o{};for(int k=0;k<3;k++)o[k]=(a[k]+(b[k]-a[k])*fx)*(1.f-fy)+(c[k]+(d[k]-c[k])*fx)*fy;return o;};
    const jsize statsLength=e->GetArrayLength(detailStats);
    constexpr int proofGridWidth=32,proofGridHeight=24,proofGridOffset=9;
    const bool hasProofGrid=statsLength>=proofGridOffset+proofGridWidth*proofGridHeight*3;
    std::vector<jlong> stats((size_t)statsLength,0);bool ok=true;
    for(int ly=0;ok&&ly<regionH;ly++)for(int lx=0;lx<regionW;lx++){
        int ox=regionX+lx,oy=regionY+ly;int bx=(ox/2)*2,by=(oy/2)*2;
        auto b00=dAt(bx,by),b10=dAt(std::min(bx+1,(int)trueW-1),by),b01=dAt(bx,std::min(by+1,(int)trueH-1)),b11=dAt(std::min(bx+1,(int)trueW-1),std::min(by+1,(int)trueH-1));
        auto directRgb=((oy-by)==0)?(((ox-bx)==0)?b00:b10):(((ox-bx)==0)?b01:b11);auto guideRgb=bilGuide(ox,oy);auto guideBlock=gAt(bx/2,by/2);
        for(int k=0;k<3;k++)if(!std::isfinite(directRgb[k])||!std::isfinite(guideRgb[k])||!std::isfinite(guideBlock[k])){ok=false;break;}if(!ok)break;
        float y00=std::max(lum(b00),0.f),y10=std::max(lum(b10),0.f),y01=std::max(lum(b01),0.f),y11=std::max(lum(b11),0.f);
        float directY=std::max(lum(directRgb),0.f),lowY=std::max(0.25f*(y00+y10+y01+y11),0.f),guideY=std::max(lum(guideRgb),0.f),guideBlockY=std::max(lum(guideBlock),0.f);
        int p00=supportAt(bx,by),p10=supportAt(bx+1,by),p01=supportAt(bx,by+1),p11=supportAt(bx+1,by+1);int phaseCount=((oy-by)==0)?(((ox-bx)==0)?p00:p10):(((ox-bx)==0)?p01:p11);int blockPhaseCount=std::min(std::min(p00,p10),std::min(p01,p11));
        float phaseGate=blockPhaseCount>=4?1.f:(blockPhaseCount==3?0.85f:(blockPhaseCount==2?0.50f:0.f));
        float temporalGate=std::min(std::min(temporalAt(bx,by),temporalAt(bx+1,by)),std::min(temporalAt(bx,by+1),temporalAt(bx+1,by+1)));
        float signalGate=iris26564::smooth01((guideBlockY-0.015f)/0.055f);float blockPeak=std::max(std::max(std::max(peak3(b00),peak3(b10)),std::max(peak3(b01),peak3(b11))),peak3(guideBlock));
        float highlightGate=1.f-iris26564::smooth01((blockPeak-0.72f)/0.20f);std::array<float,3>directBlock{};for(int k=0;k<3;k++)directBlock[k]=0.25f*(b00[k]+b10[k]+b01[k]+b11[k]);
        auto dc=chroma(directBlock),gc=chroma(guideBlock);float cd=std::sqrt((dc[0]-gc[0])*(dc[0]-gc[0])+(dc[1]-gc[1])*(dc[1]-gc[1])+(dc[2]-gc[2])*(dc[2]-gc[2]));float chromaGate=1.f-iris26564::smooth01((cd-0.015f)/0.055f);
        float agreement=std::fabs(std::log2((lowY+0.01f)/(guideBlockY+0.01f)));float agreementGate=1.f-iris26564::smooth01((agreement-0.08f)/0.27f);float safetyGate=std::min(signalGate,std::min(highlightGate,std::min(chromaGate,agreementGate)));float confidence=clampf(phaseGate*temporalGate*safetyGate,0.f,1.f);
        float denom=std::max(lowY,0.015f);float d00=(y00-lowY)/denom,d10=(y10-lowY)/denom,d01=(y01-lowY)/denom,d11=(y11-lowY)/denom;float maxAbsDetail=std::max(std::max(std::fabs(d00),std::fabs(d10)),std::max(std::fabs(d01),std::fabs(d11)));float shapeScale=maxAbsDetail>1.0e-6f?std::min(1.f,0.42f/maxAbsDetail):0.f;float directDetail=((directY-lowY)/denom)*shapeScale;
        float targetY=std::max(guideY+guideBlockY*directDetail*confidence,0.f);float factor=guideY>1.0e-5f?clampf(targetY/guideY,0.68f,1.47f):1.f;
        int reasonClass=0;if(blockPhaseCount<2)reasonClass=6;else if(temporalGate<=0.02f)reasonClass=3;else if(highlightGate<=0.001f)reasonClass=4;else if(chromaGate<=0.001f||agreementGate<=0.001f)reasonClass=5;else if(signalGate<=0.001f)reasonClass=7;else if(confidence>=0.50f)reasonClass=2;else if(confidence>0.02f)reasonClass=1;
        size_t dst=((size_t)ly*regionW+lx)*4;for(int k=0;k<3;k++)out[dst+k]=iris26564::floatToHalf(std::max(guideRgb[k]*factor,0.f));out[dst+3]=iris26564::floatToHalf((float)(phaseCount*8+reasonClass));
        stats[0]++;if(reasonClass==1)stats[1]++;else if(reasonClass==2)stats[2]++;else if(reasonClass==3)stats[3]++;else if(reasonClass==4)stats[4]++;else if(reasonClass==5)stats[5]++;else if(reasonClass==6)stats[6]++;else if(reasonClass==7)stats[7]++;else stats[8]++;
        if(hasProofGrid){int cellX=iris26564::clampi((int)(((int64_t)ox*proofGridWidth)/trueW),0,proofGridWidth-1),cellY=iris26564::clampi((int)(((int64_t)oy*proofGridHeight)/trueH),0,proofGridHeight-1);size_t g=(size_t)proofGridOffset+((size_t)cellY*proofGridWidth+cellX)*3;stats[g]++;if(reasonClass==1||reasonClass==2)stats[g+1]++;if(reasonClass==2)stats[g+2]++;}
    }
    close(tfd);close(gfd);close(pfd);if(ok){std::vector<jlong> previous((size_t)statsLength);e->GetLongArrayRegion(detailStats,0,statsLength,previous.data());if(e->ExceptionCheck())return JNI_FALSE;for(jsize k=0;k<statsLength;k++)previous[(size_t)k]+=stats[(size_t)k];e->SetLongArrayRegion(detailStats,0,statsLength,previous.data());if(e->ExceptionCheck())return JNI_FALSE;}return ok?JNI_TRUE:JNI_FALSE;
}

extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_IrisTrue2xSrNative_writeRenderTileInterior(
        JNIEnv*e,jclass,jstring outputPath,jint fullW,jint fullH,jobject regionBuffer,jint regionX,jint regionY,jint regionW,jint regionH,
        jint interiorX,jint interiorY,jint interiorW,jint interiorH){
    if(!outputPath||!regionBuffer||fullW<=0||fullH<=0||regionX<0||regionY<0||regionW<=0||regionH<=0||
       regionX>fullW-regionW||regionY>fullH-regionH||interiorX<regionX||interiorY<regionY||interiorW<=0||interiorH<=0||
       interiorX>regionX+regionW-interiorW||interiorY>regionY+regionH-interiorH||interiorX>fullW-interiorW||interiorY>fullH-interiorH)return JNI_FALSE;
    auto*rgba=(const uint16_t*)e->GetDirectBufferAddress(regionBuffer);jlong cap=e->GetDirectBufferCapacity(regionBuffer);
    if(!rgba||cap<(jlong)regionW*regionH*4*(jlong)sizeof(uint16_t))return JNI_FALSE;U op(e,outputPath);if(!op.c)return JNI_FALSE;
    int fd=open(op.c,O_RDWR);if(fd<0)return JNI_FALSE;struct stat st{};const uint64_t expected=(uint64_t)fullW*(uint64_t)fullH*6ull;
    if(fstat(fd,&st)!=0||(uint64_t)st.st_size!=expected){close(fd);return JNI_FALSE;}std::vector<uint16_t>row((size_t)interiorW*3);bool ok=true;
    const int localX=interiorX-regionX,localY=interiorY-regionY;
    for(int y=0;ok&&y<interiorH;y++){
        const uint16_t*src=rgba+((size_t)(localY+y)*regionW+localX)*4;for(int x=0;x<interiorW;x++)for(int k=0;k<3;k++)row[(size_t)x*3+k]=src[(size_t)x*4+k];
        const off_t off=((off_t)(interiorY+y)*(off_t)fullW+(off_t)interiorX)*6;const uint8_t*p=(const uint8_t*)row.data();size_t bytes=row.size()*sizeof(uint16_t),done=0;
        while(done<bytes){ssize_t n=pwrite(fd,p+done,bytes-done,off+(off_t)done);if(n<=0){ok=false;break;}done+=(size_t)n;}
    }
    close(fd);return ok?JNI_TRUE:JNI_FALSE;
}


/* IRIS_26564_TRUE2X_FINAL_RENDER_OWNER
 * Bounded true-2x final renderer. Scene pixels come only from the direct-CFA RGB16F render
 * derivative. A small source region is read per output tile, then the exact proven 26563 profile
 * color -> adaptive appearance -> display exposure -> optional Iris tone -> 26559 render math is
 * evaluated at 2x. Final crop/rotation/mirror follows the already-proven streaming-SR geometry.
 *
 * The 1x Android bitmap is never sampled for scene color. It provides only the exact final native
 * output dimensions; Java separately retains it as UHDR/JPEG-R metadata authority. Optional Jin
 * receives the exact retained 512 residual/reference arrays from the one already-proven inference.
 */
namespace iris26564render {
struct Vec3 { float r,g,b; };
inline Vec3 add(Vec3 a,Vec3 b){return {a.r+b.r,a.g+b.g,a.b+b.b};}
inline Vec3 sub(Vec3 a,Vec3 b){return {a.r-b.r,a.g-b.g,a.b-b.b};}
inline Vec3 mul(Vec3 a,float s){return {a.r*s,a.g*s,a.b*s};}
inline Vec3 mix3(Vec3 a,Vec3 b,float t){return add(a,mul(sub(b,a),t));}
inline float luma(Vec3 c){return 0.22897456f*c.r+0.69173852f*c.g+0.07928691f*c.b;}
inline float peak(Vec3 c){return std::max(c.r,std::max(c.g,c.b));}
inline float length3(Vec3 c){return std::sqrt(c.r*c.r+c.g*c.g+c.b*c.b);}
inline float smoothstep(float a,float b,float x){float t=clampf((x-a)/std::max(b-a,1.0e-12f),0.f,1.f);return t*t*(3.f-2.f*t);}
inline Vec3 clampNonnegative(Vec3 c){return {std::max(c.r,0.f),std::max(c.g,0.f),std::max(c.b,0.f)};}
inline float componentGainLimit(float y,float c){
    if(c>1.0e-7f)return std::max(1.f,(1.f-y)/c);
    if(c<-1.0e-7f)return std::max(1.f,(0.f-y)/c);
    return 4.f;
}
struct SourceRegion {
    int x0=0,y0=0,w=0,h=0,fullW=0,fullH=0;
    std::vector<uint16_t> rgb;
    bool contains(int x,int y)const{return x>=x0&&x<x0+w&&y>=y0&&y<y0+h;}
    bool cameraAt(int x,int y,Vec3*out)const{
        x=std::max(0,std::min(fullW-1,x));y=std::max(0,std::min(fullH-1,y));
        if(!contains(x,y)||!out)return false;
        size_t q=((size_t)(y-y0)*w+(x-x0))*3;
        float r=iris26564::halfToFloat(rgb[q]),g=iris26564::halfToFloat(rgb[q+1]),b=iris26564::halfToFloat(rgb[q+2]);
        if(!std::isfinite(r)||!std::isfinite(g)||!std::isfinite(b))return false;
        *out={std::max(r,0.f),std::max(g,0.f),std::max(b,0.f)};return true;
    }
};
struct Watermark {
    int w=0,h=0;
    std::vector<uint8_t> rgba;
    bool enabled()const{return w>0&&h>0&&rgba.size()==(size_t)w*h*4;}
};
struct Jin {
    int w=0,h=0;
    std::vector<float> residual;
    std::vector<jint> guide;
    std::vector<float> guideP3;
    bool enabled()const{return w>1&&h>1&&residual.size()==(size_t)w*h*3&&guide.size()==(size_t)w*h&&guideP3.size()==(size_t)w*h*3;}
};
struct Params {
    int trueW=0,trueH=0,rawW=0,rawH=0,cropW=0,cropH=0,rotation=0;
    bool mirror=false;
    float residualZoom=1.f,displayGain=1.f,exposureEv=0.f,shadows=0.f,contrast=0.f,sceneWhite=1.f;
    float sensorToProfile[9]{};
    float profileToDisplay[9]{};
};
inline Vec3 mat(const float*m,Vec3 v){
    return {m[0]*v.r+m[1]*v.g+m[2]*v.b,
            m[3]*v.r+m[4]*v.g+m[5]*v.b,
            m[6]*v.r+m[7]*v.g+m[8]*v.b};
}
inline bool profileColor(const SourceRegion&s,const Params&p,int x,int y,Vec3*out){
    Vec3 camera;if(!s.cameraAt(x,y,&camera))return false;
    Vec3 profile=mat(p.sensorToProfile,camera);Vec3 linear=mat(p.profileToDisplay,profile);
    float floor=std::min(linear.r,std::min(linear.g,linear.b));if(floor<0.f){linear.r-=floor;linear.g-=floor;linear.b-=floor;}
    *out=clampNonnegative(linear);return std::isfinite(out->r)&&std::isfinite(out->g)&&std::isfinite(out->b);
}
inline bool adaptiveAppearance(const SourceRegion&s,const Params&p,int x,int y,Vec3*out){
    Vec3 center;if(!profileColor(s,p,x,y,&center))return false;
    float cy=luma(center);Vec3 cc={center.r-cy,center.g-cy,center.b-cy};float cm=length3(cc);float relative=cm/std::max(cy,0.08f);
    const int dx[4]={-1,1,0,0},dy[4]={0,0,-1,1};Vec3 sum=cc;float magSum=cm,maxYDelta=0.f;
    for(int i=0;i<4;i++){Vec3 n;if(!profileColor(s,p,x+dx[i],y+dy[i],&n))return false;float ny=luma(n);Vec3 nc={n.r-ny,n.g-ny,n.b-ny};sum=add(sum,nc);magSum+=length3(nc);maxYDelta=std::max(maxYDelta,std::fabs(ny-cy));}
    Vec3 mean=mul(sum,0.2f);float meanMag=magSum*0.2f;float coherence=length3(mean)/std::max(meanMag,1.0e-6f);float disagreement=length3(sub(cc,mean));
    float neutral=smoothstep(0.0035f,0.018f,cm);float rolloff=1.f-smoothstep(0.08f,0.45f,relative);float dg=std::max(p.displayGain,1.0e-6f);
    float projectedY=cy*dg,projectedPeak=peak(center)*dg;float shadow=smoothstep(0.015f,0.075f,projectedY);float high=1.f-smoothstep(0.72f,0.98f,projectedPeak);
    float coh=smoothstep(0.45f,0.82f,coherence);float agree=1.f-smoothstep(0.018f,0.085f,disagreement);float edge=1.f-smoothstep(0.025f,0.11f,maxYDelta*dg);
    float requested=1.f+0.22f*neutral*rolloff*shadow*high*coh*agree*edge;float limit=4.f;float inPeak=peak(center);
    if(inPeak>=1.f||projectedPeak>=1.f)limit=1.f;else{limit=std::min(limit,componentGainLimit(cy,cc.r));limit=std::min(limit,componentGainLimit(cy,cc.g));limit=std::min(limit,componentGainLimit(cy,cc.b));}
    float g=clampf(std::min(requested,limit),1.f,1.22f);*out=g<=1.000001f?center:add(Vec3{cy,cy,cy},mul(cc,g));return true;
}
inline Vec3 tone(Vec3 rgb,const Params&p){
    rgb=mul(clampNonnegative(rgb),std::exp2(p.exposureEv));
    if(std::fabs(p.shadows)>=0.0001f){float y=luma(rgb),mask=1.f-smoothstep(0.08f,0.55f,y),target=y;if(p.shadows<0.f)target=y+(-p.shadows)*0.08f*mask*(1.f-clampf(y,0.f,1.f));else target=y*(1.f-0.75f*p.shadows*mask);rgb=y<=1.0e-7f?Vec3{std::max(target,0.f),std::max(target,0.f),std::max(target,0.f)}:mul(clampNonnegative(rgb),std::max(target,0.f)/y);}
    if(std::fabs(p.contrast)>=0.0001f){float y=luma(rgb);if(y>1.0e-7f){const float pivot=0.18f;float slope=1.f+0.25f*p.contrast;float target=pivot*std::exp2(std::log2(std::max(y/pivot,1.0e-6f))*slope);rgb=mul(clampNonnegative(rgb),std::max(target,0.f)/y);}}
    return clampNonnegative(rgb);
}
inline bool preRenderAt(const SourceRegion&s,const Params&p,int x,int y,Vec3*out){Vec3 c;if(!adaptiveAppearance(s,p,x,y,&c))return false;c=mul(c,std::max(p.displayGain,1.0e-6f));*out=tone(c,p);return true;}
inline bool samplePreRender(const SourceRegion&s,const Params&p,float x,float y,Vec3*out){
    x=clampf(x,0.f,(float)(p.trueW-1));y=clampf(y,0.f,(float)(p.trueH-1));
    if(p.residualZoom<=1.00001f){int ix=(int)std::lround(x),iy=(int)std::lround(y);return preRenderAt(s,p,ix,iy,out);}
    int x0=(int)std::floor(x),y0=(int)std::floor(y),x1=std::min(x0+1,p.trueW-1),y1=std::min(y0+1,p.trueH-1);float fx=x-x0,fy=y-y0;Vec3 a,b,c,d;
    if(!preRenderAt(s,p,x0,y0,&a)||!preRenderAt(s,p,x1,y0,&b)||!preRenderAt(s,p,x0,y1,&c)||!preRenderAt(s,p,x1,y1,&d))return false;
    *out=mix3(mix3(a,b,fx),mix3(c,d,fx),fy);return true;
}
/* IRIS_26569_TRUE2X_PROFILE_CACHE
 * Motion true2x repeatedly queried center + four neighbors through identical sensor->profile->P3
 * matrices. Cache that deterministic profile-color result once per bounded source band. The
 * original profileColor/adaptiveAppearance/samplePreRender functions above remain untouched and
 * authoritative for Jin-enabled fallback; this cache changes evaluation count, not equations.
 */
struct ProfileRegion {
    int x0=0,y0=0,w=0,h=0,fullW=0,fullH=0;
    std::vector<Vec3> rgb;
    bool contains(int x,int y)const{return x>=x0&&x<x0+w&&y>=y0&&y<y0+h;}
    bool at(int x,int y,Vec3*out)const{
        x=std::max(0,std::min(fullW-1,x));y=std::max(0,std::min(fullH-1,y));
        if(!contains(x,y)||!out)return false;
        *out=rgb[(size_t)(y-y0)*w+(x-x0)];
        return std::isfinite(out->r)&&std::isfinite(out->g)&&std::isfinite(out->b);
    }
};
inline bool buildProfileRegion(const SourceRegion&s,const Params&p,int workers,ProfileRegion*out){
    if(!out||s.w<=0||s.h<=0)return false;
    out->x0=s.x0;out->y0=s.y0;out->w=s.w;out->h=s.h;out->fullW=s.fullW;out->fullH=s.fullH;out->rgb.resize((size_t)s.w*s.h);
    std::atomic<int> nextRow{0};std::atomic<bool> ok{true};
    auto work=[&](){while(ok.load(std::memory_order_relaxed)){int ly=nextRow.fetch_add(1);if(ly>=s.h)break;for(int lx=0;lx<s.w;lx++){Vec3 v;if(!profileColor(s,p,s.x0+lx,s.y0+ly,&v)){ok.store(false,std::memory_order_relaxed);break;}out->rgb[(size_t)ly*s.w+lx]=v;}}};
    std::vector<std::thread> threads;threads.reserve((size_t)workers);for(int i=0;i<workers;i++)threads.emplace_back(work);for(auto&t:threads)t.join();return ok.load(std::memory_order_relaxed);
}
inline bool adaptiveAppearanceCached(const ProfileRegion&s,const Params&p,int x,int y,Vec3*out){
    Vec3 center;if(!s.at(x,y,&center))return false;
    float cy=luma(center);Vec3 cc={center.r-cy,center.g-cy,center.b-cy};float cm=length3(cc);float relative=cm/std::max(cy,0.08f);
    const int dx[4]={-1,1,0,0},dy[4]={0,0,-1,1};Vec3 sum=cc;float magSum=cm,maxYDelta=0.f;
    for(int i=0;i<4;i++){Vec3 n;if(!s.at(x+dx[i],y+dy[i],&n))return false;float ny=luma(n);Vec3 nc={n.r-ny,n.g-ny,n.b-ny};sum=add(sum,nc);magSum+=length3(nc);maxYDelta=std::max(maxYDelta,std::fabs(ny-cy));}
    Vec3 mean=mul(sum,0.2f);float meanMag=magSum*0.2f;float coherence=length3(mean)/std::max(meanMag,1.0e-6f);float disagreement=length3(sub(cc,mean));
    float neutral=smoothstep(0.0035f,0.018f,cm);float rolloff=1.f-smoothstep(0.08f,0.45f,relative);float dg=std::max(p.displayGain,1.0e-6f);
    float projectedY=cy*dg,projectedPeak=peak(center)*dg;float shadow=smoothstep(0.015f,0.075f,projectedY);float high=1.f-smoothstep(0.72f,0.98f,projectedPeak);
    float coh=smoothstep(0.45f,0.82f,coherence);float agree=1.f-smoothstep(0.018f,0.085f,disagreement);float edge=1.f-smoothstep(0.025f,0.11f,maxYDelta*dg);
    float requested=1.f+0.22f*neutral*rolloff*shadow*high*coh*agree*edge;float limit=4.f;float inPeak=peak(center);
    if(inPeak>=1.f||projectedPeak>=1.f)limit=1.f;else{limit=std::min(limit,componentGainLimit(cy,cc.r));limit=std::min(limit,componentGainLimit(cy,cc.g));limit=std::min(limit,componentGainLimit(cy,cc.b));}
    float g=clampf(std::min(requested,limit),1.f,1.22f);*out=g<=1.000001f?center:add(Vec3{cy,cy,cy},mul(cc,g));return true;
}
inline bool preRenderAtCached(const ProfileRegion&s,const Params&p,int x,int y,Vec3*out){Vec3 c;if(!adaptiveAppearanceCached(s,p,x,y,&c))return false;c=mul(c,std::max(p.displayGain,1.0e-6f));*out=tone(c,p);return true;}
inline bool samplePreRenderCached(const ProfileRegion&s,const Params&p,float x,float y,Vec3*out){
    x=clampf(x,0.f,(float)(p.trueW-1));y=clampf(y,0.f,(float)(p.trueH-1));
    if(p.residualZoom<=1.00001f){int ix=(int)std::lround(x),iy=(int)std::lround(y);return preRenderAtCached(s,p,ix,iy,out);}
    int x0=(int)std::floor(x),y0=(int)std::floor(y),x1=std::min(x0+1,p.trueW-1),y1=std::min(y0+1,p.trueH-1);float fx=x-x0,fy=y-y0;Vec3 a,b,c,d;
    if(!preRenderAtCached(s,p,x0,y0,&a)||!preRenderAtCached(s,p,x1,y0,&b)||!preRenderAtCached(s,p,x0,y1,&c)||!preRenderAtCached(s,p,x1,y1,&d))return false;
    *out=mix3(mix3(a,b,fx),mix3(c,d,fx),fy);return true;
}

inline Vec3 renderHeadroom(Vec3 rgb,const Params&p){
    rgb=clampNonnegative(rgb);float y=std::max(luma(rgb),0.f),pk=peak(rgb),guide=std::max(y,pk);if(guide>1.0e-7f&&guide>0.50f){float white=std::max(p.sceneWhite,0.55f);float x=clampf((guide-0.50f)/std::max(white-0.50f,1.0e-6f),0.f,1.f);float shaped=std::log(1.f+6.f*x)/std::log(7.f);float mapped=0.50f+(1.25f-0.50f)*shaped;rgb=mul(rgb,mapped/guide);}rgb=mul(rgb,0.80f);float pk2=peak(rgb);if(pk2>1.f)rgb=mul(rgb,1.f/std::max(pk2,1.0e-6f));return clampNonnegative(rgb);
}
struct SrgbLut {std::array<float,16385>v{};SrgbLut(){for(size_t i=0;i<v.size();i++){float x=(float)i/(float)(v.size()-1);v[i]=x<=0.0031308f?12.92f*x:1.055f*std::pow(x,1.f/2.4f)-0.055f;}}float at(float x)const{x=clampf(x,0.f,1.f);float q=x*(float)(v.size()-1);int i=(int)q;int j=std::min(i+1,(int)v.size()-1);return v[(size_t)i]+(v[(size_t)j]-v[(size_t)i])*(q-i);}};
inline void true2xFinalToUnrotated(float x,float y,const Params&p,float*outX,float*outY){
    switch(p.rotation){
        case 90: {
            float xx=x;if(p.mirror)xx=(float)p.cropH-xx;
            *outX=y;*outY=(float)p.rawH-xx;return;
        }
        case 180: {
            float yy=y;if(p.mirror)yy=(float)p.rawH-yy;
            *outX=(float)p.rawW-x;*outY=(float)p.rawH-yy;return;
        }
        case 270: {
            float xx=x+(float)(p.rawH-p.cropH);if(p.mirror)xx=(float)p.cropH-xx;
            *outX=(float)p.rawW-y;*outY=xx;return;
        }
        default: {
            float yy=y+(float)(p.rawH-p.cropH);if(p.mirror)yy=(float)p.rawH-yy;
            *outX=x;*outY=yy;return;
        }
    }
}
inline void outputToSource(const Params&p,int ox,int oy,float*outX,float*outY){
    float bx=((float)ox+0.5f)*0.5f-0.5f,by=((float)oy+0.5f)*0.5f-0.5f,ux=0.f,uy=0.f;
    true2xFinalToUnrotated(bx,by,p,&ux,&uy);
    float cx=((float)p.rawW-1.f)*0.5f,cy=((float)p.rawH-1.f)*0.5f;
    float sx=cx+(ux-cx)/p.residualZoom,sy=cy+(uy-cy)/p.residualZoom;
    *outX=clampf(2.f*(sx+0.5f)-0.5f,0.f,(float)(p.trueW-1));
    *outY=clampf(2.f*(sy+0.5f)-0.5f,0.f,(float)(p.trueH-1));
}
inline bool readRegion(int fd,const Params&p,int ox0,int oy0,int ox1,int oy1,SourceRegion*out){
    float minx=1.0e30f,miny=1.0e30f,maxx=-1.0e30f,maxy=-1.0e30f;const int xs[2]={ox0,ox1},ys[2]={oy0,oy1};for(int yy:ys)for(int xx:xs){float x,y;outputToSource(p,xx,yy,&x,&y);minx=std::min(minx,x);maxx=std::max(maxx,x);miny=std::min(miny,y);maxy=std::max(maxy,y);}
    int x0=std::max(0,(int)std::floor(minx)-3),x1=std::min(p.trueW-1,(int)std::ceil(maxx)+3),y0=std::max(0,(int)std::floor(miny)-3),y1=std::min(p.trueH-1,(int)std::ceil(maxy)+3);if(x1<x0||y1<y0)return false;
    out->x0=x0;out->y0=y0;out->w=x1-x0+1;out->h=y1-y0+1;out->fullW=p.trueW;out->fullH=p.trueH;out->rgb.resize((size_t)out->w*out->h*3);size_t rowBytes=(size_t)out->w*6;
    for(int y=0;y<out->h;y++){off_t off=((off_t)(out->y0+y)*(off_t)p.trueW+(off_t)out->x0)*6;uint8_t*dst=(uint8_t*)out->rgb.data()+(size_t)y*rowBytes;size_t done=0;while(done<rowBytes){ssize_t n=pread(fd,dst+done,rowBytes-done,off+(off_t)done);if(n<=0)return false;done+=(size_t)n;}}
    return true;
}
inline Vec3 sampleWatermark(const Watermark&w,float u,float v){
    if(!w.enabled())return {0.f,0.f,0.f};u=clampf(u,0.f,1.f);v=clampf(v,0.f,1.f);float x=u*(float)w.w-0.5f,y=v*(float)w.h-0.5f;x=clampf(x,0.f,(float)(w.w-1));y=clampf(y,0.f,(float)(w.h-1));int x0=(int)floorf(x),y0=(int)floorf(y),x1=std::min(x0+1,w.w-1),y1=std::min(y0+1,w.h-1);float fx=x-x0,fy=y-y0;auto p=[&](int xx,int yy,int c){return (float)w.rgba[((size_t)yy*w.w+xx)*4+c]/255.f;};Vec3 a{},b{};for(int c=0;c<3;c++){float r0=p(x0,y0,c)+(p(x1,y0,c)-p(x0,y0,c))*fx,r1=p(x0,y1,c)+(p(x1,y1,c)-p(x0,y1,c))*fx;float z=r0+(r1-r0)*fy;if(c==0)a.r=z;else if(c==1)a.g=z;else a.b=z;}auto p3=displayP3Lut().convertEncoded(a.r,a.g,a.b);return {p3[0],p3[1],p3[2]};
}
inline float sampleWatermarkAlpha(const Watermark&w,float u,float v){
    if(!w.enabled())return 0.f;u=clampf(u,0.f,1.f);v=clampf(v,0.f,1.f);float x=clampf(u*(float)w.w-0.5f,0.f,(float)(w.w-1)),y=clampf(v*(float)w.h-0.5f,0.f,(float)(w.h-1));int x0=(int)floorf(x),y0=(int)floorf(y),x1=std::min(x0+1,w.w-1),y1=std::min(y0+1,w.h-1);float fx=x-x0,fy=y-y0;auto a=[&](int xx,int yy){return (float)w.rgba[((size_t)yy*w.w+xx)*4+3]/255.f;};float r0=a(x0,y0)+(a(x1,y0)-a(x0,y0))*fx,r1=a(x0,y1)+(a(x1,y1)-a(x0,y1))*fx;return r0+(r1-r0)*fy;
}
inline bool watermarkUv(const Params&p,const Watermark&w,int ox,int oy,float*u,float*v){
    if(!w.enabled())return false;float x=(float)ox,y=(float)oy,tw=(float)p.trueW,th=(float)p.trueH,cw=(float)p.cropW*2.f,ch=(float)p.cropH*2.f,crx=0.f,cry=0.f;
    switch(p.rotation){case 270:x+=(th-ch);crx=(x-(th-ch))/tw;cry=(y-cw)/th;break;case 180:crx=x/tw;cry=(y-ch)/th;break;case 90:crx=x/tw;cry=(y-tw)/th;break;default:y+=(th-ch);crx=x/tw;cry=(y-th)/th;break;}
    crx*=tw/th;crx/=((float)w.w/(float)w.h);crx*=1.025f;crx*=15.f;cry=(cry+1.f/15.f)*15.f;if(crx<0.f||cry<0.f)return false;*u=crx;*v=cry;return true;
}
inline bool renderBase(const SourceRegion&s,const Params&p,const Watermark&w,const SrgbLut&lut,int ox,int oy,float gainMax,uint8_t*out,uint8_t*gainOut){
    float sx,sy;outputToSource(p,ox,oy,&sx,&sy);Vec3 hdr;if(!samplePreRender(s,p,sx,sy,&hdr))return false;Vec3 sdr=renderHeadroom(hdr,p);
    if(gainOut){const float off=0.015625f,safeMax=std::max(gainMax,1.001f);float hdrY=std::max(luma(clampNonnegative(hdr)),0.f),sdrY=std::max(luma(clampNonnegative(sdr)),0.f);float ratio=clampf((hdrY+off)/(sdrY+off),1.f,safeMax);float code=clampf(std::log2(ratio)/std::max(std::log2(safeMax),1.0e-6f),0.f,1.f);*gainOut=(uint8_t)std::lround(code*255.f);}
    float rr=lut.at(sdr.r),gg=lut.at(sdr.g),bb=lut.at(sdr.b);float wu,wv;if(watermarkUv(p,w,ox,oy,&wu,&wv)){float a=sampleWatermarkAlpha(w,wu,wv);if(a>0.f){Vec3 wc=sampleWatermark(w,wu,wv);rr=rr+(wc.r-rr)*a;gg=gg+(wc.g-gg)*a;bb=bb+(wc.b-bb)*a;}}
    out[0]=(uint8_t)std::lround(clampf(rr,0.f,1.f)*255.f);out[1]=(uint8_t)std::lround(clampf(gg,0.f,1.f)*255.f);out[2]=(uint8_t)std::lround(clampf(bb,0.f,1.f)*255.f);return true;
}
inline bool renderBaseCached(const ProfileRegion&s,const Params&p,const Watermark&w,const SrgbLut&lut,int ox,int oy,float gainMax,uint8_t*out,uint8_t*gainOut){
    float sx,sy;outputToSource(p,ox,oy,&sx,&sy);Vec3 hdr;if(!samplePreRenderCached(s,p,sx,sy,&hdr))return false;Vec3 sdr=renderHeadroom(hdr,p);
    if(gainOut){const float off=0.015625f,safeMax=std::max(gainMax,1.001f);float hdrY=std::max(luma(clampNonnegative(hdr)),0.f),sdrY=std::max(luma(clampNonnegative(sdr)),0.f);float ratio=clampf((hdrY+off)/(sdrY+off),1.f,safeMax);float code=clampf(std::log2(ratio)/std::max(std::log2(safeMax),1.0e-6f),0.f,1.f);*gainOut=(uint8_t)std::lround(code*255.f);}
    float rr=lut.at(sdr.r),gg=lut.at(sdr.g),bb=lut.at(sdr.b);float wu,wv;if(watermarkUv(p,w,ox,oy,&wu,&wv)){float a=sampleWatermarkAlpha(w,wu,wv);if(a>0.f){Vec3 wc=sampleWatermark(w,wu,wv);rr=rr+(wc.r-rr)*a;gg=gg+(wc.g-gg)*a;bb=bb+(wc.b-bb)*a;}}
    out[0]=(uint8_t)std::lround(clampf(rr,0.f,1.f)*255.f);out[1]=(uint8_t)std::lround(clampf(gg,0.f,1.f)*255.f);out[2]=(uint8_t)std::lround(clampf(bb,0.f,1.f)*255.f);return true;
}
inline float guideRgb(const Jin&j,int x,int y,int c){return j.guideP3[((size_t)y*j.w+x)*3+c];}
inline float guideDistance2ToNative(const Jin&j,int x,int y,const float native[3]){float d0=native[0]-guideRgb(j,x,y,0),d1=native[1]-guideRgb(j,x,y,1),d2=native[2]-guideRgb(j,x,y,2);return (d0*d0+d1*d1+d2*d2)/3.f;}
inline float guidePairDistance(const Jin&j,int ax,int ay,int bx,int by){float d0=guideRgb(j,ax,ay,0)-guideRgb(j,bx,by,0),d1=guideRgb(j,ax,ay,1)-guideRgb(j,bx,by,1),d2=guideRgb(j,ax,ay,2)-guideRgb(j,bx,by,2);return std::sqrt((d0*d0+d1*d1+d2*d2)/3.f);}
inline void applyJinPixel(const Jin&j,const uint8_t*center,const uint8_t*right,const uint8_t*down,int ox,int oy,int outW,int outH,uint8_t*out){
    if(!j.enabled()){out[0]=center[0];out[1]=center[1];out[2]=center[2];return;}float fy=((float)oy+0.5f)*(float)j.h/(float)outH-0.5f;int y0=std::max(0,std::min(j.h-1,(int)floorf(fy))),y1=std::min(y0+1,j.h-1);float ty=clampf(fy-y0,0.f,1.f);float fx=((float)ox+0.5f)*(float)j.w/(float)outW-0.5f;int x0=std::max(0,std::min(j.w-1,(int)floorf(fx))),x1=std::min(x0+1,j.w-1);float tx=clampf(fx-x0,0.f,1.f);float native[3]={center[0]/255.f,center[1]/255.f,center[2]/255.f};const float sw[4]={(1.f-tx)*(1.f-ty),tx*(1.f-ty),(1.f-tx)*ty,tx*ty};const int gx[4]={x0,x1,x0,x1},gy[4]={y0,y0,y1,y1};float bil[3]={0,0,0};for(int k=0;k<4;k++){size_t b=((size_t)gy[k]*j.w+gx[k])*3;for(int c=0;c<3;c++)bil[c]+=j.residual[b+c]*sw[k];}
    auto yl=[](const uint8_t*q){return (0.22897456f*q[0]+0.69173852f*q[1]+0.07928691f*q[2])/255.f;};float centerL=yl(center),nativeEdge=0.f;if(right)nativeEdge=std::max(nativeEdge,std::fabs(centerL-yl(right)));if(down)nativeEdge=std::max(nativeEdge,std::fabs(centerL-yl(down)));float guideSpan=0.f;for(int a=0;a<4;a++)for(int b=a+1;b<4;b++)guideSpan=std::max(guideSpan,guidePairDistance(j,gx[a],gy[a],gx[b],gy[b]));float nativeGate=smoothstep(0.025f,0.120f,nativeEdge),guideGate=smoothstep(0.060f,0.200f,guideSpan),edgeGate=std::max(nativeGate,guideGate);float reduced[3]={bil[0],bil[1],bil[2]};if(edgeGate>0.0001f){int cx=std::max(0,std::min(j.w-1,(int)lroundf(fx))),cy=std::max(0,std::min(j.h-1,(int)lroundf(fy)));float sum[3]={0,0,0},ws=0.f;for(int yy=std::max(0,cy-1);yy<=std::min(j.h-1,cy+1);yy++)for(int xx=std::max(0,cx-1);xx<=std::min(j.w-1,cx+1);xx++){float dx=(float)xx-fx,dy=(float)yy-fy,sp=1.f/(1.f+dx*dx+dy*dy),compat=1.f/(1.f+80.f*guideDistance2ToNative(j,xx,yy,native)),ww=sp*compat;size_t b=((size_t)yy*j.w+xx)*3;for(int c=0;c<3;c++)sum[c]+=j.residual[b+c]*ww;ws+=ww;}if(ws>1.0e-8f)for(int c=0;c<3;c++){float mean=sum[c]/ws,before=bil[c],after=before;if(before!=0.f){if(before*mean<=0.f&&std::fabs(mean)<std::fabs(before))after=0.f;else if(before*mean>0.f&&std::fabs(mean)<std::fabs(before))after=mean;}reduced[c]=after;}}
    for(int c=0;c<3;c++){float rr=bil[c]+(reduced[c]-bil[c])*edgeGate;if(std::fabs(rr)>std::fabs(bil[c])+1.0e-6f)rr=bil[c];out[c]=(uint8_t)lroundf(clampf(native[c]+rr,0.f,1.f)*255.f);}
}
/* IRIS_26568_TRUE2X_STREAMING_JPEG
 * 26567 rendered independent 256x256 tiles to full-frame RGB8/gain scratch files, fsynced
 * them, then reread every byte into libjpeg. Pixel math has no cross-pixel accumulation; Jin
 * only needs the already-rendered right/down neighbors. Keep exact renderBase/applyJinPixel math
 * and replace only storage order with full-width bands plus one down-row halo.
 */

inline uint64_t iris26569Ns(std::chrono::steady_clock::time_point a,std::chrono::steady_clock::time_point b);
inline bool writeJpegBand(jpeg_compress_struct*c,std::vector<uint8_t>&bytes,int width,int components,int rows,uint64_t*timingNs);

/* IRIS_26571_TRUE2X_GPU_PUBLICATION
 * Accelerate only the late 50 MP publication renderer. Sabre/VGN reconstruction, the true2x
 * carrier, capture/frame policy, DNG, JPEG quality, 4:4:4 sampling, 1:1 gain-map geometry and
 * JPEG-R ownership are unchanged. The exact 26570 CPU renderer remains the authoritative fallback.
 *
 * The GPU producer owns its EGL context on one thread, renders bounded full-width bands into an
 * RGBA8UI publication surface (RGB=SDR base, A=1:1 gain code), and uses two PBOs/fences for
 * asynchronous readback. CPU libjpeg consumes prior bands concurrently. No full-frame GPU output
 * allocation is introduced.
 */
#ifndef EGL_OPENGL_ES3_BIT_KHR
#define EGL_OPENGL_ES3_BIT_KHR 0x0040
#endif

struct Iris26571GpuTiming {
    uint64_t sourceReadNs=0, uploadDispatchNs=0, readbackWaitNs=0, deinterleaveNs=0, producerNs=0;
};

struct Iris26571ReadyBand {
    int top=0,h=0;
    std::vector<uint8_t> rgb;
    std::vector<uint8_t> gain;
};

struct Iris26571BandQueue {
    std::mutex mutex;
    std::condition_variable notEmpty,notFull;
    std::deque<Iris26571ReadyBand> bands;
    bool done=false;
    bool ok=true;
    std::string reason;
    static constexpr size_t kCapacity=2;
    bool push(Iris26571ReadyBand&&b){
        std::unique_lock<std::mutex>lock(mutex);
        notFull.wait(lock,[&](){return bands.size()<kCapacity||!ok;});
        if(!ok)return false;
        bands.emplace_back(std::move(b));
        notEmpty.notify_one();return true;
    }
    bool pop(Iris26571ReadyBand*out){
        std::unique_lock<std::mutex>lock(mutex);
        notEmpty.wait(lock,[&](){return !bands.empty()||done||!ok;});
        if(bands.empty())return false;
        *out=std::move(bands.front());bands.pop_front();notFull.notify_one();return true;
    }
    void finish(bool success,const char*why){
        std::lock_guard<std::mutex>lock(mutex);if(!success)ok=false;done=true;if(why&&!success)reason=why;
        notEmpty.notify_all();notFull.notify_all();
    }
};

static const char*kIris26571PublicationCompute=R"GLSL(
#version 310 es
precision highp float;
precision highp int;
precision highp usampler2D;
/* IRIS_26571_TRUE2X_PUBLICATION_COMPUTE */
layout(local_size_x=16,local_size_y=8,local_size_z=1) in;
layout(binding=0) uniform highp sampler2D uSource;
layout(rgba8ui,binding=0) writeonly uniform highp uimage2D uOutput;
layout(std430,binding=1) readonly buffer IrisGammaLut { float gammaLut[]; };

uniform ivec2 uSrcOrigin;
uniform ivec2 uSrcSize;
uniform ivec2 uTrueSize;
uniform ivec2 uOutputSize;
uniform ivec2 uRawSize;
uniform ivec2 uCropSize;
uniform int uRotation;
uniform int uMirror;
uniform int uBandTop;
uniform int uBandH;
uniform int uGenerateGain;
uniform float uResidualZoom;
uniform float uDisplayGain;
uniform float uExposureEv;
uniform float uShadows;
uniform float uContrast;
uniform float uSceneWhite;
uniform float uGainMax;
uniform vec3 uSensorRow0;
uniform vec3 uSensorRow1;
uniform vec3 uSensorRow2;
uniform vec3 uDisplayRow0;
uniform vec3 uDisplayRow1;
uniform vec3 uDisplayRow2;

float irisLuma(vec3 c){return dot(c,vec3(0.22897456,0.69173852,0.07928691));}
float irisPeak(vec3 c){return max(c.r,max(c.g,c.b));}
vec3 irisClampNonnegative(vec3 c){return max(c,vec3(0.0));}
float irisComponentGainLimit(float y,float c){
    if(c>1.0e-7)return max(1.0,(1.0-y)/c);
    if(c<(-1.0e-7))return max(1.0,(0.0-y)/c);
    return 4.0;
}
vec3 irisMatRows(vec3 r0,vec3 r1,vec3 r2,vec3 v){return vec3(dot(r0,v),dot(r1,v),dot(r2,v));}
vec3 irisCameraAt(ivec2 fullP){
    fullP=clamp(fullP,ivec2(0),uTrueSize-ivec2(1));
    ivec2 local=fullP-uSrcOrigin;
    local=clamp(local,ivec2(0),uSrcSize-ivec2(1));
    return max(texelFetch(uSource,local,0).rgb,vec3(0.0));
}
vec3 irisProfileColor(ivec2 p){
    vec3 camera=irisCameraAt(p);
    vec3 profile=irisMatRows(uSensorRow0,uSensorRow1,uSensorRow2,camera);
    vec3 linear=irisMatRows(uDisplayRow0,uDisplayRow1,uDisplayRow2,profile);
    float floorV=min(linear.r,min(linear.g,linear.b));
    if(floorV<0.0)linear-=vec3(floorV);
    return irisClampNonnegative(linear);
}
vec3 irisAdaptive(ivec2 p){
    vec3 center=irisProfileColor(p);
    float cy=irisLuma(center);
    vec3 cc=center-vec3(cy);
    float cm=length(cc);
    float relative=cm/max(cy,0.08);
    const ivec2 d0=ivec2(-1,0),d1=ivec2(1,0),d2=ivec2(0,-1),d3=ivec2(0,1);
    vec3 n0=irisProfileColor(p+d0),n1=irisProfileColor(p+d1),n2=irisProfileColor(p+d2),n3=irisProfileColor(p+d3);
    float y0=irisLuma(n0),y1=irisLuma(n1),y2=irisLuma(n2),y3=irisLuma(n3);
    vec3 c0=n0-vec3(y0),c1=n1-vec3(y1),c2=n2-vec3(y2),c3=n3-vec3(y3);
    vec3 mean=(cc+c0+c1+c2+c3)*0.2;
    float meanMag=(cm+length(c0)+length(c1)+length(c2)+length(c3))*0.2;
    float maxYDelta=max(max(abs(y0-cy),abs(y1-cy)),max(abs(y2-cy),abs(y3-cy)));
    float coherence=length(mean)/max(meanMag,1.0e-6);
    float disagreement=length(cc-mean);
    float neutral=smoothstep(0.0035,0.018,cm);
    float rolloff=1.0-smoothstep(0.08,0.45,relative);
    float dg=max(uDisplayGain,1.0e-6);
    float projectedY=cy*dg,projectedPeak=irisPeak(center)*dg;
    float shadow=smoothstep(0.015,0.075,projectedY);
    float high=1.0-smoothstep(0.72,0.98,projectedPeak);
    float coh=smoothstep(0.45,0.82,coherence);
    float agree=1.0-smoothstep(0.018,0.085,disagreement);
    float edge=1.0-smoothstep(0.025,0.11,maxYDelta*dg);
    float requested=1.0+0.22*neutral*rolloff*shadow*high*coh*agree*edge;
    float limitV=4.0;
    if(irisPeak(center)>=1.0||projectedPeak>=1.0)limitV=1.0;
    else{
        limitV=min(limitV,irisComponentGainLimit(cy,cc.r));
        limitV=min(limitV,irisComponentGainLimit(cy,cc.g));
        limitV=min(limitV,irisComponentGainLimit(cy,cc.b));
    }
    float g=clamp(min(requested,limitV),1.0,1.22);
    return g<=1.000001?center:vec3(cy)+cc*g;
}
vec3 irisTone(vec3 rgb){
    rgb=irisClampNonnegative(rgb)*exp2(uExposureEv);
    if(abs(uShadows)>=0.0001){
        float y=irisLuma(rgb),mask=1.0-smoothstep(0.08,0.55,y),target=y;
        if(uShadows<0.0)target=y+(-uShadows)*0.08*mask*(1.0-clamp(y,0.0,1.0));
        else target=y*(1.0-0.75*uShadows*mask);
        rgb=y<=1.0e-7?vec3(max(target,0.0)):irisClampNonnegative(rgb)*(max(target,0.0)/y);
    }
    if(abs(uContrast)>=0.0001){
        float y=irisLuma(rgb);
        if(y>1.0e-7){
            const float pivot=0.18;
            float slope=1.0+0.25*uContrast;
            float target=pivot*exp2(log2(max(y/pivot,1.0e-6))*slope);
            rgb=irisClampNonnegative(rgb)*(max(target,0.0)/y);
        }
    }
    return irisClampNonnegative(rgb);
}
vec3 irisPreRenderAt(ivec2 p){return irisTone(irisAdaptive(p)*max(uDisplayGain,1.0e-6));}
vec3 irisSamplePreRender(vec2 p){
    p=clamp(p,vec2(0.0),vec2(uTrueSize-ivec2(1)));
    if(uResidualZoom<=1.00001)return irisPreRenderAt(ivec2(floor(p+vec2(0.5))));
    ivec2 p0=ivec2(floor(p)),p1=min(p0+ivec2(1),uTrueSize-ivec2(1));
    vec2 f=p-vec2(p0);
    vec3 a=irisPreRenderAt(p0),b=irisPreRenderAt(ivec2(p1.x,p0.y));
    vec3 c=irisPreRenderAt(ivec2(p0.x,p1.y)),d=irisPreRenderAt(p1);
    return mix(mix(a,b,f.x),mix(c,d,f.x),f.y);
}
vec2 irisOutputToSource(ivec2 op){
    float bx=(float(op.x)+0.5)*0.5-0.5,by=(float(op.y)+0.5)*0.5-0.5;
    float ux=0.0,uy=0.0;
    if(uRotation==90){
        float xx=bx;if(uMirror!=0)xx=float(uCropSize.y)-xx;ux=by;uy=float(uRawSize.y)-xx;
    }else if(uRotation==180){
        float yy=by;if(uMirror!=0)yy=float(uRawSize.y)-yy;ux=float(uRawSize.x)-bx;uy=float(uRawSize.y)-yy;
    }else if(uRotation==270){
        float xx=bx+float(uRawSize.y-uCropSize.y);if(uMirror!=0)xx=float(uCropSize.y)-xx;ux=float(uRawSize.x)-by;uy=xx;
    }else{
        float yy=by+float(uRawSize.y-uCropSize.y);if(uMirror!=0)yy=float(uRawSize.y)-yy;ux=bx;uy=yy;
    }
    float cx=(float(uRawSize.x)-1.0)*0.5,cy=(float(uRawSize.y)-1.0)*0.5;
    float sx=cx+(ux-cx)/uResidualZoom,sy=cy+(uy-cy)/uResidualZoom;
    return clamp(2.0*(vec2(sx,sy)+vec2(0.5))-vec2(0.5),vec2(0.0),vec2(uTrueSize-ivec2(1)));
}
vec3 irisHeadroom(vec3 rgb){
    rgb=irisClampNonnegative(rgb);
    float y=max(irisLuma(rgb),0.0),pk=irisPeak(rgb),guide=max(y,pk);
    if(guide>1.0e-7&&guide>0.50){
        float white=max(uSceneWhite,0.55);
        float x=clamp((guide-0.50)/max(white-0.50,1.0e-6),0.0,1.0);
        float shaped=log(1.0+6.0*x)/log(7.0);
        float mapped=0.50+(1.25-0.50)*shaped;
        rgb*=mapped/guide;
    }
    rgb*=0.80;
    float pk2=irisPeak(rgb);if(pk2>1.0)rgb*=1.0/max(pk2,1.0e-6);
    return irisClampNonnegative(rgb);
}
float irisGamma(float x){
    x=clamp(x,0.0,1.0);float q=x*16384.0;int a=int(q),b=min(a+1,16384);
    return mix(gammaLut[a],gammaLut[b],q-float(a));
}
uint irisByte(float x){return uint(clamp(floor(clamp(x,0.0,1.0)*255.0+0.5),0.0,255.0));}
void main(){
    ivec2 local=ivec2(gl_GlobalInvocationID.xy);
    if(local.x>=uOutputSize.x||local.y>=uBandH)return;
    ivec2 op=ivec2(local.x,uBandTop+local.y);
    vec3 hdr=irisSamplePreRender(irisOutputToSource(op));
    vec3 sdr=irisHeadroom(hdr);
    uint gainCode=0u;
    if(uGenerateGain!=0){
        const float off=0.015625;float safeMax=max(uGainMax,1.001);
        float hdrY=max(irisLuma(irisClampNonnegative(hdr)),0.0);
        float sdrY=max(irisLuma(irisClampNonnegative(sdr)),0.0);
        float ratio=clamp((hdrY+off)/(sdrY+off),1.0,safeMax);
        float code=clamp(log2(ratio)/max(log2(safeMax),1.0e-6),0.0,1.0);
        gainCode=irisByte(code);
    }
    uvec4 outv=uvec4(irisByte(irisGamma(sdr.r)),irisByte(irisGamma(sdr.g)),irisByte(irisGamma(sdr.b)),gainCode);
    imageStore(uOutput,local,outv);
}
)GLSL";

inline GLuint iris26571Compile(GLenum type,const char*src,std::string*error){
    GLuint s=glCreateShader(type);if(!s)return 0;glShaderSource(s,1,&src,nullptr);glCompileShader(s);GLint ok=0;glGetShaderiv(s,GL_COMPILE_STATUS,&ok);
    if(!ok){GLint n=0;glGetShaderiv(s,GL_INFO_LOG_LENGTH,&n);std::vector<char>log((size_t)std::max(n,1));glGetShaderInfoLog(s,n,nullptr,log.data());if(error)*error=log.data();glDeleteShader(s);return 0;}return s;
}
inline GLuint iris26571Program(std::string*error){
    GLuint sh=iris26571Compile(GL_COMPUTE_SHADER,kIris26571PublicationCompute,error);if(!sh)return 0;GLuint p=glCreateProgram();if(!p){glDeleteShader(sh);return 0;}glAttachShader(p,sh);glLinkProgram(p);glDeleteShader(sh);GLint ok=0;glGetProgramiv(p,GL_LINK_STATUS,&ok);
    if(!ok){GLint n=0;glGetProgramiv(p,GL_INFO_LOG_LENGTH,&n);std::vector<char>log((size_t)std::max(n,1));glGetProgramInfoLog(p,n,nullptr,log.data());if(error)*error=log.data();glDeleteProgram(p);return 0;}return p;
}

class Iris26571GpuPublisher {
public:
    ~Iris26571GpuPublisher(){destroy();}
    bool init(const Params&p,const SrgbLut&lut,int outW,int outH,int bandRows,bool useExplicitFenceSync,std::string*reason){
        params=&p;outWidth=outW;outHeight=outH;maxBandRows=bandRows;explicitFenceSync=useExplicitFenceSync;
        display=eglGetDisplay(EGL_DEFAULT_DISPLAY);if(display==EGL_NO_DISPLAY){set(reason,"eglGetDisplay");return false;}
        EGLint maj=0,min=0;if(!eglInitialize(display,&maj,&min)){set(reason,"eglInitialize");return false;}
        if(!eglBindAPI(EGL_OPENGL_ES_API)){set(reason,"eglBindAPI");return false;}
        const EGLint cfgAttr[]={EGL_SURFACE_TYPE,EGL_PBUFFER_BIT,EGL_RENDERABLE_TYPE,EGL_OPENGL_ES3_BIT_KHR,EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_NONE};
        EGLint count=0;if(!eglChooseConfig(display,cfgAttr,&config,1,&count)||count<1){set(reason,"eglChooseConfig");return false;}
        const EGLint pbAttr[]={EGL_WIDTH,1,EGL_HEIGHT,1,EGL_NONE};surface=eglCreatePbufferSurface(display,config,pbAttr);if(surface==EGL_NO_SURFACE){set(reason,"eglCreatePbufferSurface");return false;}
        const EGLint ctxAttr[]={EGL_CONTEXT_CLIENT_VERSION,3,EGL_NONE};context=eglCreateContext(display,config,EGL_NO_CONTEXT,ctxAttr);if(context==EGL_NO_CONTEXT){set(reason,"eglCreateContext");return false;}
        if(!eglMakeCurrent(display,surface,surface,context)){set(reason,"eglMakeCurrent");return false;}
        GLint major=0,minor=0,maxTex=0;glGetIntegerv(GL_MAJOR_VERSION,&major);glGetIntegerv(GL_MINOR_VERSION,&minor);glGetIntegerv(GL_MAX_TEXTURE_SIZE,&maxTex);
        if(major<3||(major==3&&minor<1)){set(reason,"OpenGL ES < 3.1");return false;}
        if(maxTex<std::max(outWidth,std::max(p.trueW,p.trueH))){set(reason,"GL_MAX_TEXTURE_SIZE");return false;}
        std::string compileError;program=iris26571Program(&compileError);if(!program){set(reason,("compute:"+compileError).c_str());return false;}
        glGenTextures(1,&sourceTex);glBindTexture(GL_TEXTURE_2D,sourceTex);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);
        glGenTextures(1,&outputTex);glBindTexture(GL_TEXTURE_2D,outputTex);glTexStorage2D(GL_TEXTURE_2D,1,GL_RGBA8UI,outWidth,maxBandRows);
        glGenFramebuffers(1,&fbo);glBindFramebuffer(GL_FRAMEBUFFER,fbo);glFramebufferTexture2D(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,outputTex,0);if(glCheckFramebufferStatus(GL_FRAMEBUFFER)!=GL_FRAMEBUFFER_COMPLETE){set(reason,"RGBA8UI framebuffer");return false;}
        glGenBuffers(1,&lutSsbo);glBindBuffer(GL_SHADER_STORAGE_BUFFER,lutSsbo);glBufferData(GL_SHADER_STORAGE_BUFFER,(GLsizeiptr)(lut.v.size()*sizeof(float)),lut.v.data(),GL_STATIC_DRAW);
        const size_t maxBytes=(size_t)outWidth*maxBandRows*4;glGenBuffers(2,pbo);for(int i=0;i<2;i++){glBindBuffer(GL_PIXEL_PACK_BUFFER,pbo[i]);glBufferData(GL_PIXEL_PACK_BUFFER,(GLsizeiptr)maxBytes,nullptr,GL_STREAM_READ);}
        glBindBuffer(GL_PIXEL_PACK_BUFFER,0);GLenum err=glGetError();if(err!=GL_NO_ERROR){set(reason,"GL allocation");return false;}
        glUseProgram(program);glUniform1i(loc("uSource"),0);setParams();return true;
    }
    bool renderReadback(int fd,float gainMax,bool generateGain,int top,int h,int slot,Iris26571ReadyBand*out,Iris26571GpuTiming*timing,std::string*reason){
        if(!params||slot<0||slot>1)return false;
        SourceRegion src;auto rs=std::chrono::steady_clock::now();if(!readRegion(fd,*params,0,top,outWidth-1,top+h-1,&src)){set(reason,"readRegion");return false;}auto re=std::chrono::steady_clock::now();if(timing)timing->sourceReadNs+=iris26569Ns(rs,re);
        auto us=std::chrono::steady_clock::now();glPixelStorei(GL_UNPACK_ALIGNMENT,1);glActiveTexture(GL_TEXTURE0);glBindTexture(GL_TEXTURE_2D,sourceTex);
        if(src.w>sourceAllocW||src.h>sourceAllocH){sourceAllocW=std::max(sourceAllocW,src.w);sourceAllocH=std::max(sourceAllocH,src.h);glTexImage2D(GL_TEXTURE_2D,0,GL_RGB16F,sourceAllocW,sourceAllocH,0,GL_RGB,GL_HALF_FLOAT,nullptr);}
        glTexSubImage2D(GL_TEXTURE_2D,0,0,0,src.w,src.h,GL_RGB,GL_HALF_FLOAT,src.rgb.data());
        glUseProgram(program);glUniform2i(loc("uSrcOrigin"),src.x0,src.y0);glUniform2i(loc("uSrcSize"),src.w,src.h);glUniform1i(loc("uBandTop"),top);glUniform1i(loc("uBandH"),h);glUniform1i(loc("uGenerateGain"),generateGain?1:0);glUniform1f(loc("uGainMax"),gainMax);
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER,1,lutSsbo);glBindImageTexture(0,outputTex,0,GL_FALSE,0,GL_WRITE_ONLY,GL_RGBA8UI);
        glDispatchCompute((GLuint)((outWidth+15)/16),(GLuint)((h+7)/8),1);glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT|GL_FRAMEBUFFER_BARRIER_BIT);
        glBindFramebuffer(GL_FRAMEBUFFER,fbo);glReadBuffer(GL_COLOR_ATTACHMENT0);glPixelStorei(GL_PACK_ALIGNMENT,1);glBindBuffer(GL_PIXEL_PACK_BUFFER,pbo[slot]);glReadPixels(0,0,outWidth,h,GL_RGBA_INTEGER,GL_UNSIGNED_BYTE,(void*)0);
        if(fence[slot]){glDeleteSync(fence[slot]);fence[slot]=0;}if(explicitFenceSync)fence[slot]=glFenceSync(GL_SYNC_GPU_COMMANDS_COMPLETE,0);glFlush();auto ue=std::chrono::steady_clock::now();if(timing)timing->uploadDispatchNs+=iris26569Ns(us,ue);
        GLenum submitErr=glGetError();if(submitErr!=GL_NO_ERROR){setGl(reason,explicitFenceSync?"dispatch/readback_async":"dispatch/readback_map_sync",submitErr);return false;}if(explicitFenceSync&&!fence[slot]){set(reason,"glFenceSync_null");return false;}
        pendingTop[slot]=top;pendingH[slot]=h;return true;
    }
    bool resolve(int slot,bool generateGain,Iris26571ReadyBand*out,Iris26571GpuTiming*timing,std::string*reason){
        if(!out||slot<0||slot>1||pendingH[slot]<=0){set(reason,"resolve_invalid_state");return false;}if(explicitFenceSync&&!fence[slot]){set(reason,"resolve_missing_fence");return false;}
        if(explicitFenceSync){auto ws=std::chrono::steady_clock::now();GLenum wait=GL_TIMEOUT_EXPIRED;while(wait==GL_TIMEOUT_EXPIRED)wait=glClientWaitSync(fence[slot],GL_SYNC_FLUSH_COMMANDS_BIT,1000000000ull);auto we=std::chrono::steady_clock::now();if(timing)timing->readbackWaitNs+=iris26569Ns(ws,we);if(wait==GL_WAIT_FAILED){set(reason,"glClientWaitSync");return false;}}
        glBindBuffer(GL_PIXEL_PACK_BUFFER,pbo[slot]);GLenum bindErr=glGetError();if(bindErr!=GL_NO_ERROR){setGl(reason,"resolve_bind_pbo",bindErr);return false;}size_t px=(size_t)outWidth*pendingH[slot],bytes=px*4;auto mapStart=std::chrono::steady_clock::now();const uint8_t*mapped=(const uint8_t*)glMapBufferRange(GL_PIXEL_PACK_BUFFER,0,(GLsizeiptr)bytes,GL_MAP_READ_BIT);auto mapEnd=std::chrono::steady_clock::now();if(!explicitFenceSync&&timing)timing->readbackWaitNs+=iris26569Ns(mapStart,mapEnd);if(!mapped){GLenum mapErr=glGetError();setGl(reason,"glMapBufferRange",mapErr);glBindBuffer(GL_PIXEL_PACK_BUFFER,0);return false;}
        auto ds=std::chrono::steady_clock::now();out->top=pendingTop[slot];out->h=pendingH[slot];out->rgb.resize(px*3);if(generateGain)out->gain.resize(px);else out->gain.clear();
        for(size_t i=0;i<px;i++){out->rgb[i*3]=mapped[i*4];out->rgb[i*3+1]=mapped[i*4+1];out->rgb[i*3+2]=mapped[i*4+2];if(generateGain)out->gain[i]=mapped[i*4+3];}
        GLboolean unmapOk=glUnmapBuffer(GL_PIXEL_PACK_BUFFER);GLenum unmapErr=glGetError();glBindBuffer(GL_PIXEL_PACK_BUFFER,0);GLenum unbindErr=glGetError();auto de=std::chrono::steady_clock::now();if(timing)timing->deinterleaveNs+=iris26569Ns(ds,de);if(fence[slot]){glDeleteSync(fence[slot]);fence[slot]=0;}pendingH[slot]=0;if(unmapOk!=GL_TRUE){set(reason,"glUnmapBuffer_invalidated");return false;}if(unmapErr!=GL_NO_ERROR){setGl(reason,"glUnmapBuffer",unmapErr);return false;}if(unbindErr!=GL_NO_ERROR){setGl(reason,"resolve_unbind_pbo",unbindErr);return false;}return true;
    }
private:
    EGLDisplay display=EGL_NO_DISPLAY;EGLConfig config=nullptr;EGLSurface surface=EGL_NO_SURFACE;EGLContext context=EGL_NO_CONTEXT;
    GLuint program=0,sourceTex=0,outputTex=0,fbo=0,lutSsbo=0,pbo[2]{0,0};GLsync fence[2]{0,0};int pendingTop[2]{0,0},pendingH[2]{0,0};int sourceAllocW=0,sourceAllocH=0,outWidth=0,outHeight=0,maxBandRows=0;bool explicitFenceSync=true;const Params*params=nullptr;
    GLint loc(const char*n){return glGetUniformLocation(program,n);}
    static void set(std::string*r,const char*m){if(r)*r=m?m:"unknown";}
    static void setGl(std::string*r,const char*stage,GLenum err){if(!r)return;char b[96];std::snprintf(b,sizeof(b),"%s_gl_error_0x%04x",stage?stage:"gl",(unsigned int)err);*r=b;}
    void setParams(){
        glUseProgram(program);glUniform2i(loc("uTrueSize"),params->trueW,params->trueH);glUniform2i(loc("uOutputSize"),outWidth,outHeight);glUniform2i(loc("uRawSize"),params->rawW,params->rawH);glUniform2i(loc("uCropSize"),params->cropW,params->cropH);glUniform1i(loc("uRotation"),params->rotation);glUniform1i(loc("uMirror"),params->mirror?1:0);glUniform1f(loc("uResidualZoom"),params->residualZoom);glUniform1f(loc("uDisplayGain"),params->displayGain);glUniform1f(loc("uExposureEv"),params->exposureEv);glUniform1f(loc("uShadows"),params->shadows);glUniform1f(loc("uContrast"),params->contrast);glUniform1f(loc("uSceneWhite"),params->sceneWhite);
        glUniform3f(loc("uSensorRow0"),params->sensorToProfile[0],params->sensorToProfile[1],params->sensorToProfile[2]);glUniform3f(loc("uSensorRow1"),params->sensorToProfile[3],params->sensorToProfile[4],params->sensorToProfile[5]);glUniform3f(loc("uSensorRow2"),params->sensorToProfile[6],params->sensorToProfile[7],params->sensorToProfile[8]);
        glUniform3f(loc("uDisplayRow0"),params->profileToDisplay[0],params->profileToDisplay[1],params->profileToDisplay[2]);glUniform3f(loc("uDisplayRow1"),params->profileToDisplay[3],params->profileToDisplay[4],params->profileToDisplay[5]);glUniform3f(loc("uDisplayRow2"),params->profileToDisplay[6],params->profileToDisplay[7],params->profileToDisplay[8]);
    }
    void destroy(){
        if(display!=EGL_NO_DISPLAY&&context!=EGL_NO_CONTEXT&&surface!=EGL_NO_SURFACE)eglMakeCurrent(display,surface,surface,context);
        for(int i=0;i<2;i++)if(fence[i]){glDeleteSync(fence[i]);fence[i]=0;}if(pbo[0]||pbo[1])glDeleteBuffers(2,pbo);if(lutSsbo)glDeleteBuffers(1,&lutSsbo);if(fbo)glDeleteFramebuffers(1,&fbo);if(outputTex)glDeleteTextures(1,&outputTex);if(sourceTex)glDeleteTextures(1,&sourceTex);if(program)glDeleteProgram(program);
        if(display!=EGL_NO_DISPLAY){eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);if(context!=EGL_NO_CONTEXT)eglDestroyContext(display,context);if(surface!=EGL_NO_SURFACE)eglDestroySurface(display,surface);eglTerminate(display);}
        display=EGL_NO_DISPLAY;surface=EGL_NO_SURFACE;context=EGL_NO_CONTEXT;program=sourceTex=outputTex=fbo=lutSsbo=0;pbo[0]=pbo[1]=0;
    }
};

inline bool iris26571EncodeGpuPublication(int sourceFd,float gainMax,const Params&p,const SrgbLut&lut,int outW,int outH,int bandRows,bool generateGain,const char*basePath,const char*gainPath,int quality,bool useExplicitFenceSync,Iris26571GpuTiming*gpuTiming,uint64_t*baseJpegNs,uint64_t*gainJpegNs,std::string*reason){
    if(!basePath||outW<=0||outH<=0||bandRows<=0)return false;
    Iris26571BandQueue queue;auto producerStart=std::chrono::steady_clock::now();
    std::thread producer([&](){
        Iris26571GpuPublisher gpu;std::string why;if(!gpu.init(p,lut,outW,outH,bandRows,useExplicitFenceSync,&why)){queue.finish(false,why.c_str());return;}
        int bandIndex=0;bool ok=true;for(int top=0;top<outH&&ok;top+=bandRows,bandIndex++){
            int h=std::min(bandRows,outH-top),slot=bandIndex&1;if(bandIndex>=2){Iris26571ReadyBand ready;if(!gpu.resolve(slot,generateGain,&ready,gpuTiming,&why)){ok=false;break;}if(!queue.push(std::move(ready))){ok=false;why="queue_cancelled";break;}}
            if(!gpu.renderReadback(sourceFd,gainMax,generateGain,top,h,slot,nullptr,gpuTiming,&why)){ok=false;break;}
        }
        if(ok){int totalBands=(outH+bandRows-1)/bandRows;for(int k=std::max(0,totalBands-2);k<totalBands;k++){int slot=k&1;Iris26571ReadyBand ready;if(!gpu.resolve(slot,generateGain,&ready,gpuTiming,&why)){ok=false;break;}if(!queue.push(std::move(ready))){ok=false;why="queue_cancelled";break;}}}
        queue.finish(ok,ok?nullptr:why.c_str());
    });

    FILE*baseOut=fopen(basePath,"wb");if(!baseOut){queue.finish(false,"open base");producer.join();return false;}FILE*gainOut=nullptr;if(generateGain){gainOut=fopen(gainPath,"wb");if(!gainOut){fclose(baseOut);queue.finish(false,"open gain");producer.join();return false;}}
    jpeg_compress_struct baseC{};jpeg_error_mgr baseErr{};baseC.err=jpeg_std_error(&baseErr);jpeg_create_compress(&baseC);jpeg_stdio_dest(&baseC,baseOut);baseC.image_width=outW;baseC.image_height=outH;baseC.input_components=3;baseC.in_color_space=JCS_RGB;jpeg_set_defaults(&baseC);jpeg_set_quality(&baseC,std::clamp(quality,1,100),TRUE);for(int k=0;k<baseC.num_components;k++){baseC.comp_info[k].h_samp_factor=1;baseC.comp_info[k].v_samp_factor=1;}jpeg_start_compress(&baseC,TRUE);bool streamed=writeDisplayP3Icc(&baseC);
    jpeg_compress_struct gainC{};jpeg_error_mgr gainErr{};bool gainCreated=false;if(generateGain){gainC.err=jpeg_std_error(&gainErr);jpeg_create_compress(&gainC);gainCreated=true;jpeg_stdio_dest(&gainC,gainOut);gainC.image_width=outW;gainC.image_height=outH;gainC.input_components=1;gainC.in_color_space=JCS_GRAYSCALE;jpeg_set_defaults(&gainC);jpeg_set_quality(&gainC,95,TRUE);jpeg_start_compress(&gainC,TRUE);}
    int expectedTop=0,bands=0;while(streamed&&expectedTop<outH){Iris26571ReadyBand band;if(!queue.pop(&band)){streamed=false;break;}if(band.top!=expectedTop||band.h<=0){streamed=false;break;}
        std::atomic<bool>gainOk{true};std::thread gainThread;if(generateGain)gainThread=std::thread([&](){gainOk.store(writeJpegBand(&gainC,band.gain,outW,1,band.h,gainJpegNs),std::memory_order_relaxed);});
        bool baseOk=writeJpegBand(&baseC,band.rgb,outW,3,band.h,baseJpegNs);if(generateGain)gainThread.join();if(!baseOk||(generateGain&&!gainOk.load(std::memory_order_relaxed))){streamed=false;break;}expectedTop+=band.h;bands++;
    }
    if(!streamed)queue.finish(false,"jpeg_band_encode");
    producer.join();{std::lock_guard<std::mutex>lock(queue.mutex);if(!queue.ok){streamed=false;if(reason)*reason=queue.reason;}}
    auto producerEnd=std::chrono::steady_clock::now();if(gpuTiming)gpuTiming->producerNs=iris26569Ns(producerStart,producerEnd);
    if(streamed&&baseC.next_scanline==baseC.image_height&&(!generateGain||gainC.next_scanline==gainC.image_height)){jpeg_finish_compress(&baseC);if(generateGain)jpeg_finish_compress(&gainC);}else{jpeg_abort_compress(&baseC);if(gainCreated)jpeg_abort_compress(&gainC);}
    jpeg_destroy_compress(&baseC);if(gainCreated)jpeg_destroy_compress(&gainC);int bf=fflush(baseOut),bc=fclose(baseOut),gf=0,gc=0;if(gainOut){gf=fflush(gainOut);gc=fclose(gainOut);}
    bool ok=streamed&&bf==0&&bc==0&&(!generateGain||(gf==0&&gc==0));if(!ok){unlink(basePath);if(generateGain)unlink(gainPath);}return ok;
}

struct StreamingBandTiming { uint64_t profileNs=0,renderNs=0,jinNs=0; };
inline uint64_t iris26569Ns(std::chrono::steady_clock::time_point a,std::chrono::steady_clock::time_point b){return (uint64_t)std::chrono::duration_cast<std::chrono::nanoseconds>(b-a).count();}
inline void addBandTiming(StreamingBandTiming*total,const StreamingBandTiming&band){if(!total)return;total->profileNs+=band.profileNs;total->renderNs+=band.renderNs;total->jinNs+=band.jinNs;}
struct StreamingBandBuffer{int top=0,h=0;bool ok=false;std::vector<uint8_t>rgb,gain;StreamingBandTiming timing{};};
inline bool writeJpegBand(jpeg_compress_struct*c,std::vector<uint8_t>&bytes,int width,int components,int rows,uint64_t*timingNs){
    if(!c||width<=0||components<=0||rows<=0||bytes.size()<(size_t)width*components*rows)return false;
    const int maxBatch=32;std::array<JSAMPROW,maxBatch>rowPointers{};int y=0;
    while(y<rows){int batch=std::min(maxBatch,rows-y);for(int i=0;i<batch;i++)rowPointers[(size_t)i]=&bytes[((size_t)(y+i)*width)*components];auto start=std::chrono::steady_clock::now();JDIMENSION written=jpeg_write_scanlines(c,rowPointers.data(),(JDIMENSION)batch);auto end=std::chrono::steady_clock::now();if(timingNs)*timingNs+=iris26569Ns(start,end);if(written==0)return false;y+=(int)written;}
    return true;
}
inline bool renderStreamingBand(int sourceFd,float gainMax,const Params&p,const Watermark&w,const Jin&j,const SrgbLut&lut,int outW,int outH,int top,int coreH,int workers,bool generateGain,std::vector<uint8_t>*rgbRows,std::vector<uint8_t>*gainRows,StreamingBandTiming*timing){
    if(!rgbRows||coreH<=0||outW<=0)return false;
    const bool useJin=j.enabled();
    const int extH=coreH+(useJin&&top+coreH<outH?1:0);
    SourceRegion src;if(!readRegion(sourceFd,p,0,top,outW-1,top+extH-1,&src))return false;
    if(!useJin){
        ProfileRegion profile;auto profileStart=std::chrono::steady_clock::now();if(!buildProfileRegion(src,p,workers,&profile))return false;auto profileEnd=std::chrono::steady_clock::now();if(timing)timing->profileNs+=iris26569Ns(profileStart,profileEnd);
        rgbRows->resize((size_t)outW*coreH*3);if(generateGain){if(!gainRows)return false;gainRows->resize((size_t)outW*coreH);}
        std::atomic<int> nextRow{0};std::atomic<bool> ok{true};auto renderStart=std::chrono::steady_clock::now();
        auto work=[&](){while(ok.load(std::memory_order_relaxed)){int y=nextRow.fetch_add(1);if(y>=coreH)break;for(int x=0;x<outW;x++){uint8_t*g=generateGain?&(*gainRows)[(size_t)y*outW+x]:nullptr;if(!renderBaseCached(profile,p,w,lut,x,top+y,gainMax,&(*rgbRows)[((size_t)y*outW+x)*3],g)){ok.store(false,std::memory_order_relaxed);break;}}}};
        std::vector<std::thread> threads;threads.reserve((size_t)workers);for(int i=0;i<workers;i++)threads.emplace_back(work);for(auto&t:threads)t.join();auto renderEnd=std::chrono::steady_clock::now();if(timing)timing->renderNs+=iris26569Ns(renderStart,renderEnd);return ok.load(std::memory_order_relaxed);
    }
    std::vector<uint8_t>base((size_t)outW*extH*3),gainBase;if(generateGain)gainBase.resize((size_t)outW*extH);std::atomic<int>nextBaseRow{0};std::atomic<bool>ok{true};auto renderStart=std::chrono::steady_clock::now();
    auto baseWork=[&](){while(ok.load(std::memory_order_relaxed)){int y=nextBaseRow.fetch_add(1);if(y>=extH)break;for(int x=0;x<outW;x++){uint8_t*g=generateGain?&gainBase[(size_t)y*outW+x]:nullptr;if(!renderBase(src,p,w,lut,x,top+y,gainMax,&base[((size_t)y*outW+x)*3],g)){ok.store(false,std::memory_order_relaxed);break;}}}};std::vector<std::thread>threads;threads.reserve((size_t)workers);for(int i=0;i<workers;i++)threads.emplace_back(baseWork);for(auto&t:threads)t.join();auto renderEnd=std::chrono::steady_clock::now();if(timing)timing->renderNs+=iris26569Ns(renderStart,renderEnd);if(!ok.load(std::memory_order_relaxed))return false;
    rgbRows->resize((size_t)outW*coreH*3);if(generateGain){if(!gainRows)return false;gainRows->resize((size_t)outW*coreH);}std::atomic<int>nextOutputRow{0};threads.clear();auto jinStart=std::chrono::steady_clock::now();auto outputWork=[&](){while(ok.load(std::memory_order_relaxed)){int y=nextOutputRow.fetch_add(1);if(y>=coreH)break;for(int x=0;x<outW;x++){const uint8_t*c=&base[((size_t)y*outW+x)*3];const uint8_t*r=(x+1<outW)?&base[((size_t)y*outW+x+1)*3]:nullptr;const uint8_t*d=(top+y+1<outH)?&base[((size_t)(y+1)*outW+x)*3]:nullptr;applyJinPixel(j,c,r,d,x,top+y,outW,outH,&(*rgbRows)[((size_t)y*outW+x)*3]);if(generateGain)(*gainRows)[(size_t)y*outW+x]=gainBase[(size_t)y*outW+x];}}};for(int i=0;i<workers;i++)threads.emplace_back(outputWork);for(auto&t:threads)t.join();auto jinEnd=std::chrono::steady_clock::now();if(timing)timing->jinNs+=iris26569Ns(jinStart,jinEnd);return ok.load(std::memory_order_relaxed);
}

}

extern "C" JNIEXPORT jstring JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_getLastTrue2xPublicationTelemetryNative(JNIEnv*e,jclass){
    return e->NewStringUTF(gIris26576PublicationTelemetry.c_str());
}

extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_writeTrue2xNative(
        JNIEnv*e,jclass,jobject bitmap,jstring renderPath,jint trueW,jint trueH,jint rawW,jint rawH,jint cropW,jint cropH,jint rotation,jboolean mirror,jfloat residualZoom,
        jfloatArray sensorToProfile,jfloatArray profileToDisplay,jfloat displayGain,jfloat exposureEv,jfloat shadows,jfloat contrast,jobject watermarkBitmap,
        jfloatArray jinResidual,jintArray jinReference,jint jinW,jint jinH,jstring gainPath,jfloat gainMaxRatio,jstring path,jint quality){
    using namespace iris26564render;gIris26576PublicationTelemetry="backend=UNSET callStarted=true";AndroidBitmapInfo info{};if(!bitmap||!renderPath||!path||trueW<=0||trueH<=0||rawW<=0||rawH<=0||cropW<=0||cropH<=0||trueW!=rawW*2||trueH!=rawH*2||cropW>rawW||cropH>rawH||AndroidBitmap_getInfo(e,bitmap,&info)!=ANDROID_BITMAP_RESULT_SUCCESS||info.format!=ANDROID_BITMAP_FORMAT_RGBA_8888){iris26576SetPublicationTelemetry("backend=NONE validationFailed=true");return JNI_FALSE;}
    int expectedNativeW=(rotation==90||rotation==270)?cropH:rawW,expectedNativeH=(rotation==90||rotation==270)?rawW:cropH;if((int)info.width!=expectedNativeW||(int)info.height!=expectedNativeH)return JNI_FALSE;
    Params p{};p.trueW=trueW;p.trueH=trueH;p.rawW=rawW;p.rawH=rawH;p.cropW=cropW;p.cropH=cropH;p.rotation=rotation;p.mirror=mirror==JNI_TRUE;p.residualZoom=std::max(1.f,(float)residualZoom);p.displayGain=displayGain;p.exposureEv=exposureEv;p.shadows=shadows;p.contrast=contrast;p.sceneWhite=std::max(1.f,std::min(6.f,0.90f*std::max(1.f,p.displayGain)));
    if(!sensorToProfile||!profileToDisplay||e->GetArrayLength(sensorToProfile)!=9||e->GetArrayLength(profileToDisplay)!=9)return JNI_FALSE;e->GetFloatArrayRegion(sensorToProfile,0,9,p.sensorToProfile);e->GetFloatArrayRegion(profileToDisplay,0,9,p.profileToDisplay);if(e->ExceptionCheck())return JNI_FALSE;for(float v:p.sensorToProfile)if(!std::isfinite(v))return JNI_FALSE;for(float v:p.profileToDisplay)if(!std::isfinite(v))return JNI_FALSE;if(!std::isfinite(p.displayGain)||p.displayGain<=0.f||!std::isfinite(p.exposureEv)||!std::isfinite(p.shadows)||!std::isfinite(p.contrast)||!std::isfinite(p.residualZoom))return JNI_FALSE;
    U rp(e,renderPath),gp(e,gainPath),op(e,path);if(!rp.c||!op.c)return JNI_FALSE;const bool generateGain=gp.c!=nullptr;if(generateGain&&(!std::isfinite((float)gainMaxRatio)||gainMaxRatio<=1.f))return JNI_FALSE;int sourceFd=open(rp.c,O_RDONLY);if(sourceFd<0)return JNI_FALSE;struct stat st{};uint64_t expected=(uint64_t)trueW*(uint64_t)trueH*6ull;if(fstat(sourceFd,&st)!=0||(uint64_t)st.st_size!=expected){close(sourceFd);return JNI_FALSE;}
    Watermark water{};if(watermarkBitmap){AndroidBitmapInfo wi{};if(AndroidBitmap_getInfo(e,watermarkBitmap,&wi)!=ANDROID_BITMAP_RESULT_SUCCESS||wi.format!=ANDROID_BITMAP_FORMAT_RGBA_8888||wi.width==0||wi.height==0){close(sourceFd);return JNI_FALSE;}void*wp=nullptr;if(AndroidBitmap_lockPixels(e,watermarkBitmap,&wp)!=ANDROID_BITMAP_RESULT_SUCCESS||!wp){close(sourceFd);return JNI_FALSE;}water.w=(int)wi.width;water.h=(int)wi.height;water.rgba.resize((size_t)water.w*water.h*4);for(int y=0;y<water.h;y++)std::memcpy(water.rgba.data()+(size_t)y*water.w*4,(const uint8_t*)wp+(size_t)y*wi.stride,(size_t)water.w*4);AndroidBitmap_unlockPixels(e,watermarkBitmap);}
    Jin jin{};if(jinResidual||jinReference||jinW||jinH){if(!jinResidual||!jinReference||jinW<=1||jinH<=1||e->GetArrayLength(jinResidual)!=(jsize)((jlong)jinW*jinH*3)||e->GetArrayLength(jinReference)!=(jsize)((jlong)jinW*jinH)){close(sourceFd);return JNI_FALSE;}jin.w=jinW;jin.h=jinH;jin.residual.resize((size_t)jinW*jinH*3);jin.guide.resize((size_t)jinW*jinH);e->GetFloatArrayRegion(jinResidual,0,(jsize)jin.residual.size(),jin.residual.data());e->GetIntArrayRegion(jinReference,0,(jsize)jin.guide.size(),jin.guide.data());if(e->ExceptionCheck()){close(sourceFd);return JNI_FALSE;}for(float v:jin.residual)if(!std::isfinite(v)){close(sourceFd);return JNI_FALSE;}const auto&p3=displayP3Lut();jin.guideP3.resize((size_t)jinW*jinH*3);for(int i=0;i<jinW*jinH;i++){jint argb=jin.guide[(size_t)i];float sr=(float)((argb>>16)&255)/255.f,sg=(float)((argb>>8)&255)/255.f,sb=(float)(argb&255)/255.f;auto baseP3=p3.convertEncoded(sr,sg,sb);auto outP3=p3.convertEncoded(clampf(sr+jin.residual[(size_t)i*3],0.f,1.f),clampf(sg+jin.residual[(size_t)i*3+1],0.f,1.f),clampf(sb+jin.residual[(size_t)i*3+2],0.f,1.f));for(int c=0;c<3;c++){jin.guideP3[(size_t)i*3+c]=baseP3[(size_t)c];jin.residual[(size_t)i*3+c]=outP3[(size_t)c]-baseP3[(size_t)c];}}}
    int outW=(int)info.width*2,outH=(int)info.height*2;
    /* IRIS_26568_TRUE2X_DIRECT_JPEG_SCANLINES
     * Preserve exact 26567 final-render math, 4:4:4 JPEG parameters, Display-P3 ICC and 1:1
     * gain samples, but stream full-width bands directly. Ephemeral RGB8/gain scratch disappears.
     */
    SrgbLut lut;const bool motionFast=!jin.enabled();const int bandRows=motionFast?256:128;unsigned hc=std::thread::hardware_concurrency();int workers=std::max(1,std::min(motionFast?6:4,(int)(hc?hc:2)));
    /* IRIS_26571_TRUE2X_GPU_PUBLICATION_ROUTE
     * Only the Jin-free / watermark-free true2x publication fast path is GPU-eligible. Any EGL,
     * GLES 3.1, allocation, shader, dispatch, readback or encode failure deletes the GPU temp
     * outputs and replays the exact 26570 CPU publication path from the unchanged true2x carrier.
     */
    /* IRIS_26577_TRUE2X_GPU_READBACK_COMPAT_TIER
     * Preserve the successful 26571 two-PBO/fence path as the first choice. If only its explicit
     * fence/resolve transport fails, replay the identical GPU publication math with the same two
     * bounded PBOs while allowing glMapBufferRange itself to synchronize, matching the proven Sabre
     * PBO behavior on-device. CPU remains the final exact 26570 fallback.
     */
    bool gpuEligible=motionFast&&!water.enabled();bool gpuEncoded=false;bool gpuCompatUsed=false;Iris26571GpuTiming gpuTiming{},gpuCompatTiming{};uint64_t gpuBaseJpegNs=0,gpuGainJpegNs=0,gpuCompatBaseJpegNs=0,gpuCompatGainJpegNs=0,gpuCompatTotalNs=0;std::string gpuReason,gpuCompatReason;
    std::string gpuBasePath=std::string(op.c)+".iris26571_gpu",gpuGainPath=generateGain?std::string(gp.c)+".iris26571_gpu":std::string();
    unlink(gpuBasePath.c_str());if(generateGain)unlink(gpuGainPath.c_str());auto gpuStart=std::chrono::steady_clock::now();
    if(gpuEligible)gpuEncoded=iris26571EncodeGpuPublication(sourceFd,(float)gainMaxRatio,p,lut,outW,outH,bandRows,generateGain,gpuBasePath.c_str(),generateGain?gpuGainPath.c_str():nullptr,(int)quality,true,&gpuTiming,&gpuBaseJpegNs,&gpuGainJpegNs,&gpuReason);
    auto gpuEnd=std::chrono::steady_clock::now();uint64_t gpuTotalNs=iris26569Ns(gpuStart,gpuEnd);
    if(gpuEligible&&!gpuEncoded){unlink(gpuBasePath.c_str());if(generateGain)unlink(gpuGainPath.c_str());auto compatStart=std::chrono::steady_clock::now();gpuEncoded=iris26571EncodeGpuPublication(sourceFd,(float)gainMaxRatio,p,lut,outW,outH,bandRows,generateGain,gpuBasePath.c_str(),generateGain?gpuGainPath.c_str():nullptr,(int)quality,false,&gpuCompatTiming,&gpuCompatBaseJpegNs,&gpuCompatGainJpegNs,&gpuCompatReason);auto compatEnd=std::chrono::steady_clock::now();gpuCompatTotalNs=iris26569Ns(compatStart,compatEnd);gpuCompatUsed=gpuEncoded;__android_log_print(ANDROID_LOG_INFO,TAG,"IRIS_26577_TRUE2X_GPU_COMPAT_RESULT asyncReason=%s asyncMs=%.3f compatUsed=%d compatReason=%s compatMs=%.3f",gpuReason.empty()?"missing_reason":gpuReason.c_str(),(double)gpuTotalNs/1000000.0,gpuCompatUsed?1:0,gpuCompatReason.empty()?(gpuCompatUsed?"none":"missing_reason"):gpuCompatReason.c_str(),(double)gpuCompatTotalNs/1000000.0);}
    if(gpuEncoded){
        unlink(op.c);if(rename(gpuBasePath.c_str(),op.c)!=0){gpuEncoded=false;if(gpuCompatUsed)gpuCompatReason="rename_base";else gpuReason="rename_base";}
        if(gpuEncoded&&generateGain){unlink(gp.c);if(rename(gpuGainPath.c_str(),gp.c)!=0){gpuEncoded=false;if(gpuCompatUsed)gpuCompatReason="rename_gain";else gpuReason="rename_gain";}}
        if(!gpuEncoded){unlink(op.c);if(generateGain)unlink(gp.c);}
    }
    if(gpuEncoded){
        close(sourceFd);const Iris26571GpuTiming&usedTiming=gpuCompatUsed?gpuCompatTiming:gpuTiming;uint64_t usedBaseJpegNs=gpuCompatUsed?gpuCompatBaseJpegNs:gpuBaseJpegNs,usedGainJpegNs=gpuCompatUsed?gpuCompatGainJpegNs:gpuGainJpegNs,usedTotalNs=gpuCompatUsed?gpuCompatTotalNs:gpuTotalNs;
        iris26576SetPublicationTelemetry("backend=GPU gpuEligible=1 gpuUsed=1 gpuMode=%s asyncAttemptMs=%.3f asyncFailureReason=%s sourceReadMs=%.3f uploadDispatchMs=%.3f readbackWaitMs=%.3f deinterleaveMs=%.3f producerMs=%.3f baseJpegMs=%.3f gainJpegMs=%.3f totalMs=%.3f bandRows=%d pboSlots=2 gain1to1=%d",gpuCompatUsed?"MAP_SYNC_COMPAT":"ASYNC_FENCE",(double)gpuTotalNs/1000000.0,gpuCompatUsed?(gpuReason.empty()?"missing_reason":gpuReason.c_str()):"none",(double)usedTiming.sourceReadNs/1000000.0,(double)usedTiming.uploadDispatchNs/1000000.0,(double)usedTiming.readbackWaitNs/1000000.0,(double)usedTiming.deinterleaveNs/1000000.0,(double)usedTiming.producerNs/1000000.0,(double)usedBaseJpegNs/1000000.0,(double)usedGainJpegNs/1000000.0,(double)usedTotalNs/1000000.0,bandRows,generateGain?1:0);
        __android_log_print(ANDROID_LOG_INFO,TAG,"IRIS_26577_TRUE2X_GPU_PUBLICATION gpuMode=%s asyncAttemptMs=%.3f asyncFailureReason=%s sourceReadMs=%.3f uploadDispatchMs=%.3f readbackWaitMs=%.3f deinterleaveMs=%.3f producerMs=%.3f baseJpegMs=%.3f gainJpegMs=%.3f totalMs=%.3f bandRows=%d pboSlots=2 gain1to1=%d",gpuCompatUsed?"MAP_SYNC_COMPAT":"ASYNC_FENCE",(double)gpuTotalNs/1000000.0,gpuCompatUsed?(gpuReason.empty()?"missing_reason":gpuReason.c_str()):"none",(double)usedTiming.sourceReadNs/1000000.0,(double)usedTiming.uploadDispatchNs/1000000.0,(double)usedTiming.readbackWaitNs/1000000.0,(double)usedTiming.deinterleaveNs/1000000.0,(double)usedTiming.producerNs/1000000.0,(double)usedBaseJpegNs/1000000.0,(double)usedGainJpegNs/1000000.0,(double)usedTotalNs/1000000.0,bandRows,generateGain?1:0);
        return JNI_TRUE;
    }
    unlink(gpuBasePath.c_str());if(generateGain)unlink(gpuGainPath.c_str());const char*primaryReason=gpuReason.empty()?(gpuEligible?"missing_async_reason":"jin_or_watermark"):gpuReason.c_str();const char*compatReason=gpuCompatReason.empty()?(gpuEligible?"missing_compat_reason":"not_attempted"):gpuCompatReason.c_str();
    __android_log_print(ANDROID_LOG_INFO,TAG,"IRIS_26577_TRUE2X_GPU_TO_CPU_FALLBACK eligible=%d asyncReason=%s asyncMs=%.3f compatReason=%s compatMs=%.3f",(int)gpuEligible,primaryReason,(double)gpuTotalNs/1000000.0,compatReason,(double)gpuCompatTotalNs/1000000.0);

    /* Exact successful 26570 CPU fallback begins here. */
    unlink(op.c);if(generateGain)unlink(gp.c);FILE*baseOut=fopen(op.c,"wb");if(!baseOut){__android_log_print(ANDROID_LOG_ERROR,TAG,"IRIS_26568_TRUE2X_FAIL stage=open_base_jpeg errno=%d",errno);close(sourceFd);return JNI_FALSE;}FILE*gainOut=nullptr;if(generateGain){gainOut=fopen(gp.c,"wb");if(!gainOut){__android_log_print(ANDROID_LOG_ERROR,TAG,"IRIS_26568_TRUE2X_FAIL stage=open_gain_jpeg errno=%d",errno);fclose(baseOut);unlink(op.c);close(sourceFd);return JNI_FALSE;}}
    jpeg_compress_struct baseC{};jpeg_error_mgr baseErr{};baseC.err=jpeg_std_error(&baseErr);jpeg_create_compress(&baseC);jpeg_stdio_dest(&baseC,baseOut);baseC.image_width=outW;baseC.image_height=outH;baseC.input_components=3;baseC.in_color_space=JCS_RGB;jpeg_set_defaults(&baseC);jpeg_set_quality(&baseC,std::clamp((int)quality,1,100),TRUE);for(int k=0;k<baseC.num_components;k++){baseC.comp_info[k].h_samp_factor=1;baseC.comp_info[k].v_samp_factor=1;}jpeg_start_compress(&baseC,TRUE);bool streamed=writeDisplayP3Icc(&baseC);
    jpeg_compress_struct gainC{};jpeg_error_mgr gainErr{};bool gainCreated=false;if(generateGain){gainC.err=jpeg_std_error(&gainErr);jpeg_create_compress(&gainC);gainCreated=true;jpeg_stdio_dest(&gainC,gainOut);gainC.image_width=outW;gainC.image_height=outH;gainC.input_components=1;gainC.in_color_space=JCS_GRAYSCALE;jpeg_set_defaults(&gainC);jpeg_set_quality(&gainC,95,TRUE);jpeg_start_compress(&gainC,TRUE);}
    StreamingBandTiming timing{};uint64_t baseJpegNs=0,gainJpegNs=0,overlapNs=0;int bands=0;auto streamStart=std::chrono::steady_clock::now();
    /* IRIS_26570_TRUE2X_RENDER_ENCODE_PIPELINE
     * Keep the exact 26569 pixel equations, 4:4:4 base JPEG, 1:1 gain map and 256-row memory
     * bound. While libjpeg consumes band N, render band N+1; base and gain compressors run on
     * separate threads/instances. Two bounded bands are the only added storage.
     */
    auto renderBand=[&](int top,StreamingBandBuffer*slot){slot->top=top;slot->h=std::min(bandRows,outH-top);slot->timing={};slot->ok=renderStreamingBand(sourceFd,(float)gainMaxRatio,p,water,jin,lut,outW,outH,slot->top,slot->h,workers,generateGain,&slot->rgb,&slot->gain,&slot->timing);};
    StreamingBandBuffer current,next;if(outH>0)renderBand(0,&current);else streamed=false;if(!current.ok)streamed=false;
    while(streamed){
        addBandTiming(&timing,current.timing);const int nextTop=current.top+current.h;std::thread nextRender;bool hasNext=nextTop<outH;auto overlapStart=std::chrono::steady_clock::now();if(hasNext)nextRender=std::thread([&](){renderBand(nextTop,&next);});
        std::atomic<bool>gainBandOk{true};std::thread gainEncode;if(generateGain){gainEncode=std::thread([&](){gainBandOk.store(writeJpegBand(&gainC,current.gain,outW,1,current.h,&gainJpegNs),std::memory_order_relaxed);});}
        bool baseBandOk=writeJpegBand(&baseC,current.rgb,outW,3,current.h,&baseJpegNs);if(generateGain)gainEncode.join();if(hasNext)nextRender.join();auto overlapEnd=std::chrono::steady_clock::now();overlapNs+=iris26569Ns(overlapStart,overlapEnd);bands++;
        if(!baseBandOk||(generateGain&&!gainBandOk.load(std::memory_order_relaxed))){streamed=false;break;}if(!hasNext)break;if(!next.ok){streamed=false;break;}std::swap(current,next);
    }
    auto streamEnd=std::chrono::steady_clock::now();
    if(streamed&&baseC.next_scanline==baseC.image_height&&(!generateGain||gainC.next_scanline==gainC.image_height)){jpeg_finish_compress(&baseC);if(generateGain)jpeg_finish_compress(&gainC);}else{streamed=false;jpeg_abort_compress(&baseC);if(gainCreated)jpeg_abort_compress(&gainC);}jpeg_destroy_compress(&baseC);if(gainCreated)jpeg_destroy_compress(&gainC);int baseFlush=fflush(baseOut),baseClose=fclose(baseOut),gainFlush=0,gainClose=0;if(gainOut){gainFlush=fflush(gainOut);gainClose=fclose(gainOut);}close(sourceFd);
    bool baseEncoded=streamed&&baseFlush==0&&baseClose==0;bool gainEncoded=!generateGain||(streamed&&gainFlush==0&&gainClose==0);if(!baseEncoded)unlink(op.c);if(generateGain&&!gainEncoded)unlink(gp.c);iris26576SetPublicationTelemetry("backend=CPU gpuEligible=%d gpuUsed=0 asyncAttemptMs=%.3f asyncFailureReason=%s compatAttemptMs=%.3f compatFailureReason=%s profileMs=%.3f renderMs=%.3f jinMs=%.3f baseJpegMs=%.3f gainJpegMs=%.3f streamMs=%.3f workers=%d bandRows=%d baseEncoded=%d gainEncoded=%d",(int)gpuEligible,(double)gpuTotalNs/1000000.0,primaryReason,(double)gpuCompatTotalNs/1000000.0,compatReason,(double)timing.profileNs/1000000.0,(double)timing.renderNs/1000000.0,(double)timing.jinNs/1000000.0,(double)baseJpegNs/1000000.0,(double)gainJpegNs/1000000.0,(double)iris26569Ns(streamStart,streamEnd)/1000000.0,workers,bandRows,baseEncoded?1:0,gainEncoded?1:0);__android_log_print(ANDROID_LOG_INFO,TAG,"IRIS_26570_TRUE2X_ENCODER_TIMING profileMs=%.3f renderMs=%.3f jinMs=%.3f baseJpegMs=%.3f gainJpegMs=%.3f overlapPipelineMs=%.3f streamMs=%.3f workers=%d bandRows=%d profileCache=%d jpegBatchRows=%d doubleBuffered=%d concurrentGain=%d",timing.profileNs/1000000.0,timing.renderNs/1000000.0,timing.jinNs/1000000.0,baseJpegNs/1000000.0,gainJpegNs/1000000.0,overlapNs/1000000.0,iris26569Ns(streamStart,streamEnd)/1000000.0,workers,bandRows,motionFast?1:0,32,1,generateGain?1:0);__android_log_print(ANDROID_LOG_INFO,TAG,"IRIS_26568_TRUE2X_FINAL_STREAM rendered=%d baseEncoded=%d gainEncoded=%d gain1to1=%d source=%dx%d output=%dx%d workers=%d bands=%d jin=%d watermark=%d scratch=BOUNDED_DOUBLE_BAND",streamed?1:0,baseEncoded?1:0,gainEncoded?1:0,generateGain?1:0,(int)trueW,(int)trueH,outW,outH,workers,bands,jin.enabled()?1:0,water.enabled()?1:0);
    __android_log_print(ANDROID_LOG_INFO,"MotionTrace","PIPELINE_STATE stage=IRIS_26571_TRUE2X_CPU_FALLBACK details=profileMs=%.3f renderMs=%.3f jinMs=%.3f baseJpegMs=%.3f gainJpegMs=%.3f streamMs=%.3f workers=%d bandRows=%d",(double)timing.profileNs/1000000.0,(double)timing.renderNs/1000000.0,(double)timing.jinNs/1000000.0,(double)baseJpegNs/1000000.0,(double)gainJpegNs/1000000.0,(double)iris26569Ns(streamStart,streamEnd)/1000000.0,workers,bandRows);
    /* A valid 50MP base is authoritative. Gain/JPEG-R auxiliary failure is handled by Java by
     * promoting that exact P3 base to SDR; it must never report base failure and trigger 12MP. */
    return baseEncoded?JNI_TRUE:JNI_FALSE;
}

extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_writeSuperResNative(
        JNIEnv*e,jclass,jobject bitmap,jstring detailPath,jint detailW,jint detailH,jint rawW,jint rawH,jint cropW,jint cropH,jint rotation,jboolean mirror,jfloat residualZoom,jstring path,jint quality){
    AndroidBitmapInfo info{};if(!bitmap||!detailPath||!path||detailW<=0||detailH<=0||AndroidBitmap_getInfo(e,bitmap,&info)!=ANDROID_BITMAP_RESULT_SUCCESS||info.format!=ANDROID_BITMAP_FORMAT_RGBA_8888)return JNI_FALSE;
    U ud(e,detailPath);if(!ud.c)return JNI_FALSE;int fd=open(ud.c,O_RDONLY);if(fd<0)return JNI_FALSE;struct stat st{};size_t expected=(size_t)detailW*(size_t)detailH;
    if(fstat(fd,&st)!=0||(size_t)st.st_size!=expected){close(fd);return JNI_FALSE;}void*m=mmap(nullptr,expected,PROT_READ,MAP_PRIVATE,fd,0);close(fd);if(m==MAP_FAILED)return JNI_FALSE;const uint8_t*detail=(const uint8_t*)m;
    void*pixels=nullptr;if(AndroidBitmap_lockPixels(e,bitmap,&pixels)!=ANDROID_BITMAP_RESULT_SUCCESS||!pixels){munmap(m,expected);return JNI_FALSE;}U u(e,path);if(!u.c){AndroidBitmap_unlockPixels(e,bitmap);munmap(m,expected);return JNI_FALSE;}
    FILE*f=fopen(u.c,"wb");if(!f){AndroidBitmap_unlockPixels(e,bitmap);munmap(m,expected);return JNI_FALSE;}
    jpeg_compress_struct c{};jpeg_error_mgr jerr{};c.err=jpeg_std_error(&jerr);jpeg_create_compress(&c);jpeg_stdio_dest(&c,f);
    int outW=(int)info.width*2,outH=(int)info.height*2;c.image_width=outW;c.image_height=outH;c.input_components=3;c.in_color_space=JCS_RGB;jpeg_set_defaults(&c);jpeg_set_quality(&c,std::clamp((int)quality,1,100),TRUE);
    for(int k=0;k<c.num_components;k++){c.comp_info[k].h_samp_factor=1;c.comp_info[k].v_samp_factor=1;}
    jpeg_start_compress(&c,TRUE);std::vector<uint8_t>row((size_t)outW*3);const uint8_t*base=(const uint8_t*)pixels;float z=std::max(1.f,(float)residualZoom);
    while(c.next_scanline<c.image_height){int oy=(int)c.next_scanline;float by=((float)oy+0.5f)*0.5f-0.5f;for(int ox=0;ox<outW;ox++){float bx=((float)ox+0.5f)*0.5f-0.5f;float rgb[3];bilinearBitmap(base,(int)info.width,(int)info.height,(int)info.stride,bx,by,rgb);
            float ux=0.f,uy=0.f;finalToUnrotated(bx,by,rawW,rawH,cropW,cropH,rotation,mirror==JNI_TRUE,&ux,&uy);float cx=((float)rawW-1.f)*0.5f,cy=((float)rawH-1.f)*0.5f;float sx=cx+(ux-cx)/z,sy=cy+(uy-cy)/z;float dx=2.f*(sx+0.5f)-0.5f,dy=2.f*(sy+0.5f)-0.5f;float ld=detailLog2Q8(detail,detailW,detailH,dx,dy);
            float lin[3]={srgbToLinear(rgb[0]),srgbToLinear(rgb[1]),srgbToLinear(rgb[2])};float y=0.2126f*lin[0]+0.7152f*lin[1]+0.0722f*lin[2];float shadow=clampf((y-0.015f)/0.085f,0.f,1.f),high=1.f-clampf((y-0.75f)/0.23f,0.f,1.f);float factor=std::exp2(ld*shadow*high);
            for(int k=0;k<3;k++)row[(size_t)ox*3+k]=(uint8_t)std::lround(clampf(linearToSrgb(lin[k]*factor),0.f,1.f)*255.f);
        }JSAMPROW rp=row.data();jpeg_write_scanlines(&c,&rp,1);}
    jpeg_finish_compress(&c);jpeg_destroy_compress(&c);int flush=fflush(f),closeRc=fclose(f);AndroidBitmap_unlockPixels(e,bitmap);munmap(m,expected);return (flush==0&&closeRc==0)?JNI_TRUE:JNI_FALSE;
}

extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_encodeGainmapNative(JNIEnv*e,jclass,jobject bitmap,jstring path,jint quality){AndroidBitmapInfo i{};if(!bitmap||!path||AndroidBitmap_getInfo(e,bitmap,&i)!=ANDROID_BITMAP_RESULT_SUCCESS||(i.format!=ANDROID_BITMAP_FORMAT_A_8&&i.format!=ANDROID_BITMAP_FORMAT_RGBA_8888))return JNI_FALSE;void*p=nullptr;if(AndroidBitmap_lockPixels(e,bitmap,&p)!=ANDROID_BITMAP_RESULT_SUCCESS||!p)return JNI_FALSE;tjhandle h=tj3Init(TJINIT_COMPRESS);int pf=i.format==ANDROID_BITMAP_FORMAT_A_8?TJPF_GRAY:TJPF_RGBA;int ss=i.format==ANDROID_BITMAP_FORMAT_A_8?TJSAMP_GRAY:TJSAMP_444;int q=std::clamp((int)quality,1,100);bool cfg=h&&tj3Set(h,TJPARAM_QUALITY,q)>=0&&tj3Set(h,TJPARAM_SUBSAMP,ss)>=0&&tj3Set(h,TJPARAM_OPTIMIZE,0)>=0;unsigned char*out=nullptr;size_t n=0;int rc=cfg?tj3Compress8(h,(const unsigned char*)p,(int)i.width,(int)i.stride,(int)i.height,pf,&out,&n):-1;AndroidBitmap_unlockPixels(e,bitmap);U u(e,path);bool ok=rc>=0&&out&&n&&u.c&&write(u.c,out,n);if(out)tj3Free(out);if(h)tj3Destroy(h);return ok?JNI_TRUE:JNI_FALSE;}
extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_packageJpegRNative(JNIEnv*e,jclass,jstring b,jstring g,jstring o,jint gamut,jfloatArray rmin,jfloatArray rmax,jfloatArray gamma,jfloatArray es,jfloatArray eh,jfloat ds,jfloat dh,jboolean use){U ub(e,b),ug(e,g),uo(e,o);if(!ub.c||!ug.c||!uo.c)return JNI_FALSE;iris26507::GainmapMetadata m;if(!f3(e,rmin,&m.ratioMin)||!f3(e,rmax,&m.ratioMax)||!f3(e,gamma,&m.gamma)||!f3(e,es,&m.epsilonSdr)||!f3(e,eh,&m.epsilonHdr))return JNI_FALSE;m.displaySdr=ds;m.displayHdr=dh;m.useBaseColorSpace=use==JNI_TRUE;std::string err;return iris26507::packageJpegR(ub.c,ug.c,uo.c,gamut,m,&err)?JNI_TRUE:JNI_FALSE;}

extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_processor_IrisNightNeuralEnhancer_applyReferenceResidualNative(
        JNIEnv*e,jclass,jobject bitmap,jfloatArray residual,jintArray referenceRgb,jint rw,jint rh,jboolean baseDisplayP3){
    /* IRIS_26556_JIN_NATIVE_SABRE_GUIDED_RESIDUAL
     * Jin itself is unchanged: Java supplies the complete dense 512x512 RGB residual
     * denorm(output)-denorm(input), plus the exact 512 RGB reference pixels fed to Jin.
     *
     * Smooth native regions retain the exact 26555 bilinear residual. Near a real edge, native
     * Sabre RGB and Jin's exact 512 input identify same-side residual support. A local compatible
     * Jin-residual baseline may only REDUCE a high-frequency residual peak; it is never allowed to
     * increase any residual component beyond the 26555 bilinear magnitude. This prevents the
     * coarse 512 transfer from inventing bright/dark segmented structures beside a native edge
     * without globally disabling Jin there. No gain ratio, 32x32 grid, luma-only reinterpretation,
     * tiled inference, or neural-model change is introduced here.
     */
    if(!bitmap||!residual||!referenceRgb||rw<2||rh<2||
       e->GetArrayLength(residual)!=(jsize)(rw*rh*3)||
       e->GetArrayLength(referenceRgb)!=(jsize)(rw*rh))return JNI_FALSE;
    AndroidBitmapInfo info{};
    if(AndroidBitmap_getInfo(e,bitmap,&info)!=ANDROID_BITMAP_RESULT_SUCCESS||
       info.format!=ANDROID_BITMAP_FORMAT_RGBA_8888)return JNI_FALSE;

    std::vector<float> r((size_t)rw*rh*3);
    std::vector<jint> guide((size_t)rw*rh);
    e->GetFloatArrayRegion(residual,0,(jsize)r.size(),r.data());
    e->GetIntArrayRegion(referenceRgb,0,(jsize)guide.size(),guide.data());
    if(e->ExceptionCheck())return JNI_FALSE;
    for(float v:r)if(!std::isfinite(v))return JNI_FALSE;
    std::vector<float> guideP3;
    if(baseDisplayP3==JNI_TRUE){const auto&p3=displayP3Lut();guideP3.resize((size_t)rw*rh*3);for(int i=0;i<rw*rh;i++){jint argb=guide[(size_t)i];float sr=(float)((argb>>16)&255)/255.f,sg=(float)((argb>>8)&255)/255.f,sb=(float)(argb&255)/255.f;auto bp=p3.convertEncoded(sr,sg,sb);auto op=p3.convertEncoded(clampf(sr+r[(size_t)i*3],0.f,1.f),clampf(sg+r[(size_t)i*3+1],0.f,1.f),clampf(sb+r[(size_t)i*3+2],0.f,1.f));for(int c=0;c<3;c++){guideP3[(size_t)i*3+c]=bp[(size_t)c];r[(size_t)i*3+c]=op[(size_t)c]-bp[(size_t)c];}}}

    auto guideRgb=[&](int x,int y,int c)->float{
        if(baseDisplayP3==JNI_TRUE)return guideP3[((size_t)y*rw+x)*3+c];
        jint argb=guide[(size_t)y*rw+x];
        int shift=c==0?16:(c==1?8:0);
        return (float)((argb>>shift)&255)/255.f;
    };
    auto guideDistance2ToNative=[&](int x,int y,const float nativeRgb[3])->float{
        float d0=nativeRgb[0]-guideRgb(x,y,0);
        float d1=nativeRgb[1]-guideRgb(x,y,1);
        float d2=nativeRgb[2]-guideRgb(x,y,2);
        return (d0*d0+d1*d1+d2*d2)/3.f;
    };
    auto guidePairDistance=[&](int ax,int ay,int bx,int by)->float{
        float d0=guideRgb(ax,ay,0)-guideRgb(bx,by,0);
        float d1=guideRgb(ax,ay,1)-guideRgb(bx,by,1);
        float d2=guideRgb(ax,ay,2)-guideRgb(bx,by,2);
        return std::sqrt((d0*d0+d1*d1+d2*d2)/3.f);
    };

    void*p=nullptr;
    if(AndroidBitmap_lockPixels(e,bitmap,&p)!=ANDROID_BITMAP_RESULT_SUCCESS||!p)return JNI_FALSE;
    const auto*base=(const uint8_t*)p;
    uint64_t guidedPixels=0;
    uint64_t suppressedComponents=0;
    const uint64_t totalPixels=(uint64_t)info.width*(uint64_t)info.height;
    auto luma=[&](const uint8_t*q)->float{
        if(baseDisplayP3==JNI_TRUE)return (0.22897456f*(float)q[0]+0.69173852f*(float)q[1]+0.07928691f*(float)q[2])/255.f;
        return (0.2126f*(float)q[0]+0.7152f*(float)q[1]+0.0722f*(float)q[2])/255.f;
    };
    auto smooth01=[](float t)->float{
        t=clampf(t,0.f,1.f);
        return t*t*(3.f-2.f*t);
    };

    for(uint32_t y=0;y<info.height;y++){
        auto*row=(uint8_t*)p+(size_t)y*info.stride;
        float fy=((float)y+0.5f)*(float)rh/(float)info.height-0.5f;
        int y0=std::max(0,std::min(rh-1,(int)floorf(fy)));
        int y1=std::min(y0+1,rh-1);
        float ty=clampf(fy-(float)y0,0.f,1.f);
        for(uint32_t x=0;x<info.width;x++){
            float fx=((float)x+0.5f)*(float)rw/(float)info.width-0.5f;
            int x0=std::max(0,std::min(rw-1,(int)floorf(fx)));
            int x1=std::min(x0+1,rw-1);
            float tx=clampf(fx-(float)x0,0.f,1.f);
            uint8_t*q=row+x*4;
            float nativeRgb[3]={q[0]/255.f,q[1]/255.f,q[2]/255.f};

            const float sw[4]={
                    (1.f-tx)*(1.f-ty), tx*(1.f-ty), (1.f-tx)*ty, tx*ty};
            const int gx[4]={x0,x1,x0,x1};
            const int gy[4]={y0,y0,y1,y1};
            float bilinear[3]={0.f,0.f,0.f};
            for(int k=0;k<4;k++){
                size_t b=((size_t)gy[k]*rw+gx[k])*3;
                for(int c=0;c<3;c++)bilinear[c]+=r[b+c]*sw[k];
            }

            // High-resolution native edge evidence. Right/down samples are unmodified in scan
            // order, so this does not use residual-altered pixels as the structural guide.
            float centerL=luma(q),nativeEdge=0.f;
            if(x+1<info.width){
                const uint8_t*qr=row+(size_t)(x+1)*4;
                nativeEdge=std::max(nativeEdge,std::fabs(centerL-luma(qr)));
            }
            if(y+1<info.height){
                const uint8_t*qd=base+(size_t)(y+1)*info.stride+(size_t)x*4;
                nativeEdge=std::max(nativeEdge,std::fabs(centerL-luma(qd)));
            }

            // The 512 guide footprint extends edge awareness across the whole interpolation cell,
            // not just the single native boundary pixel. Smooth 512 neighborhoods keep this zero.
            float guideSpan=0.f;
            for(int a=0;a<4;a++)for(int b=a+1;b<4;b++)
                guideSpan=std::max(guideSpan,guidePairDistance(gx[a],gy[a],gx[b],gy[b]));
            float nativeGate=smooth01((nativeEdge-0.025f)/(0.120f-0.025f));
            float guideGate=smooth01((guideSpan-0.060f)/(0.200f-0.060f));
            float edgeGate=std::max(nativeGate,guideGate);

            float reduced[3]={bilinear[0],bilinear[1],bilinear[2]};
            if(edgeGate>0.0001f){
                // Local compatible Jin-residual baseline. Native RGB selects samples from the same
                // structural side of the edge while the spatial term keeps the baseline local.
                int cx=std::max(0,std::min(rw-1,(int)lroundf(fx)));
                int cy=std::max(0,std::min(rh-1,(int)lroundf(fy)));
                float sum[3]={0.f,0.f,0.f};
                float wsum=0.f;
                for(int yy=std::max(0,cy-1);yy<=std::min(rh-1,cy+1);yy++){
                    for(int xx=std::max(0,cx-1);xx<=std::min(rw-1,cx+1);xx++){
                        float dx=(float)xx-fx,dy=(float)yy-fy;
                        float spatial=1.f/(1.f+dx*dx+dy*dy);
                        float compat=1.f/(1.f+80.f*guideDistance2ToNative(xx,yy,nativeRgb));
                        float w=spatial*compat;
                        size_t b=((size_t)yy*rw+xx)*3;
                        for(int c=0;c<3;c++)sum[c]+=r[b+c]*w;
                        wsum+=w;
                    }
                }
                if(wsum>1.0e-8f){
                    for(int c=0;c<3;c++){
                        float mean=sum[c]/wsum;
                        float before=bilinear[c];
                        float after=before;
                        // Permanent edge-artifact invariant: guidance may suppress a local residual
                        // peak but may never create a larger correction than 26555 bilinear.
                        if(before!=0.f){
                            if(before*mean<=0.f && std::fabs(mean)<std::fabs(before))after=0.f;
                            else if(before*mean>0.f && std::fabs(mean)<std::fabs(before))after=mean;
                        }
                        reduced[c]=after;
                        if(std::fabs(after)+1.0e-8f<std::fabs(before))suppressedComponents++;
                    }
                }
                if(edgeGate>=0.5f)guidedPixels++;
            }

            for(int c=0;c<3;c++){
                float rr=bilinear[c]+(reduced[c]-bilinear[c])*edgeGate;
                // The inequality is intentional and regression-tested: edge guidance cannot
                // increase the absolute Jin correction versus the original 26555 bilinear value.
                if(std::fabs(rr)>std::fabs(bilinear[c])+1.0e-6f)rr=bilinear[c];
                float v=nativeRgb[c]+rr;
                q[c]=(uint8_t)lrintf(clampf(v,0.f,1.f)*255.f);
            }
        }
    }
    AndroidBitmap_unlockPixels(e,bitmap);
    __android_log_print(ANDROID_LOG_INFO,TAG,
            "IRIS_26556_JIN_NATIVE_GUIDED_TRANSFER native=%ux%u guide=%dx%d guidedPixels=%llu totalPixels=%llu suppressedComponents=%llu",
            info.width,info.height,(int)rw,(int)rh,
            (unsigned long long)guidedPixels,(unsigned long long)totalPixels,
            (unsigned long long)suppressedComponents);
    return JNI_TRUE;
}

extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_isJpegRNative(JNIEnv*e,jclass,jstring p){U u(e,p);return u.c&&iris26507::isJpegR(u.c)?JNI_TRUE:JNI_FALSE;}
