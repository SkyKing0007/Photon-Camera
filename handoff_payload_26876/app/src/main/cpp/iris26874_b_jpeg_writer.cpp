/*
 * IRIS_26874_B_NATIVE_JPEG_OWNER
 * Experiment B only. No image-development math, color conversion or gain-map fitting.
 * RAWR v0.5.0 strip/worker architecture independently adapted from the GPL-3.0
 * implementation by adityawarmanfw (92bd2196d9cee337695d76e107520034248568f3).
 * Photon/Iris and RAWR both distribute under GPL-3.0; preserve source provenance.
 * Boundaries: caller-owned finalized P3 RGBA8; already-frozen Android gain-map codes;
 * byte-equivalent ICC and libultrahdr compressed-image container parameters.
 */
#include <jni.h>
#include <android/bitmap.h>
#include <android/hardware_buffer.h>
#include <android/hardware_buffer_jni.h>
#include <android/log.h>
#include <turbojpeg.h>
#include <ultrahdr_api.h>
#include <ultrahdr/icc.h>
#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <limits>
#include <memory>
#include <string>
#include <thread>
#include <vector>
#include <cerrno>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/resource.h>

namespace {
constexpr char TAG[] = "Iris26874BJpeg";
constexpr size_t kMaxOutput = static_cast<size_t>(std::numeric_limits<int>::max());
thread_local std::string gTelemetry = "state=NOT_RUN";
struct Utf { JNIEnv* e; jstring s; const char* p;
    Utf(JNIEnv* x,jstring y):e(x),s(y),p(y?x->GetStringUTFChars(y,nullptr):nullptr){}
    ~Utf(){if(p)e->ReleaseStringUTFChars(s,p);} };
struct LockedBitmap { JNIEnv* e; jobject object; AndroidBitmapInfo info{}; const uint8_t* pixels=nullptr;
    LockedBitmap(JNIEnv* env,jobject b):e(env),object(b){
        if(b && AndroidBitmap_getInfo(e,b,&info)==ANDROID_BITMAP_RESULT_SUCCESS){
            void* p=nullptr;
            if(AndroidBitmap_lockPixels(e,b,&p)==ANDROID_BITMAP_RESULT_SUCCESS) pixels=(const uint8_t*)p;
        }
    }
    ~LockedBitmap(){if(pixels)AndroidBitmap_unlockPixels(e,object);}
};
struct Turbo { tjhandle h=tj3Init(TJINIT_COMPRESS); ~Turbo(){if(h)tj3Destroy(h);} };
struct TurboBytes {unsigned char* p=nullptr; size_t n=0; ~TurboBytes(){if(p)tj3Free(p);} TurboBytes()=default;
    TurboBytes(const TurboBytes&)=delete; TurboBytes&operator=(const TurboBytes&)=delete;};
struct Encoder { uhdr_codec_private_t* p=uhdr_create_encoder(); ~Encoder(){if(p)uhdr_release_encoder(p);} };
struct Segment {int top=0,rows=0;TurboBytes bytes;std::string error;size_t sofHeight=0,sos=0,scan=0;};
inline unsigned be16(const uint8_t* p){return (unsigned(p[0])<<8)|p[1];}
inline void put16(std::vector<uint8_t>&o,unsigned v){o.push_back(uint8_t(v>>8));o.push_back(uint8_t(v));}
static bool setup(tjhandle h,int quality,int subsamp){
    return h && tj3Set(h,TJPARAM_QUALITY,quality)==0 && tj3Set(h,TJPARAM_SUBSAMP,subsamp)==0 &&
        tj3Set(h,TJPARAM_FASTDCT,0)==0 && tj3Set(h,TJPARAM_OPTIMIZE,0)==0 &&
        tj3Set(h,TJPARAM_PROGRESSIVE,0)==0 && tj3Set(h,TJPARAM_ARITHMETIC,0)==0 &&
        tj3Set(h,TJPARAM_RESTARTBLOCKS,0)==0 && tj3Set(h,TJPARAM_RESTARTROWS,0)==0;
}
static bool parseSegment(Segment& s){
    auto*d=s.bytes.p;size_t n=s.bytes.n;
    if(!d||n<8||d[0]!=0xff||d[1]!=0xd8||d[n-2]!=0xff||d[n-1]!=0xd9)return false;
    size_t i=2;bool sof=false;
    while(i+4<=n){
        if(d[i]!=0xff)return false;
        const uint8_t marker=d[i+1];const unsigned len=be16(d+i+2);
        if(len<2 || i+2+len>n)return false;
        if(marker==0xc0){if(len<7)return false;s.sofHeight=i+5;sof=true;}
        else if(marker==0xda){if(!sof)return false;s.sos=i;s.scan=i+2+len;return true;}
        else if(marker==0xdd || (marker>=0xc1&&marker<=0xcf&&marker!=0xc4&&marker!=0xc8&&marker!=0xcc))return false;
        i+=2+len;
    }
    return false;
}
static void encodeOne(const uint8_t* rgba,int width,int stride,int quality,int subsamp,Segment& s){
    Turbo t;if(!setup(t.h,quality,subsamp)){s.error="configure";return;}
    if(tj3Compress8(t.h,rgba+size_t(s.top)*stride,width,stride,s.rows,TJPF_RGBA,&s.bytes.p,&s.bytes.n)!=0)
        s.error="compress";
}
static bool parallelStrips(const uint8_t* rgba,int width,int height,int stride,int quality,int subsamp,
                           std::vector<uint8_t>&output,int&stripCount){
    stripCount=1;
    const unsigned threads=std::min(8u,std::max(1u,std::thread::hardware_concurrency()));
    if(threads<2||uint64_t(width)*height<1000000u)return false;
    const int mcuW=tjMCUWidth[subsamp],mcuH=tjMCUHeight[subsamp];
    if(mcuW<=0||mcuH<=0)return false;
    const int mcusPerRow=(width+mcuW-1)/mcuW, mcuRows=(height+mcuH-1)/mcuH;
    const int cap=65535/mcusPerRow;if(cap<1)return false;
    const int stripMcuRows=std::min(cap,(mcuRows+int(threads)-1)/int(threads));
    const int count=(mcuRows+stripMcuRows-1)/stripMcuRows;if(count<2)return false;
    std::vector<Segment> strips(static_cast<size_t>(count));
    for(int i=0;i<count;++i){strips[i].top=i*stripMcuRows*mcuH;strips[i].rows=std::min(stripMcuRows*mcuH,height-strips[i].top);}
    std::atomic<int> next{0};
    auto work=[&](){::setpriority(PRIO_PROCESS,0,10);for(int i=next.fetch_add(1);i<count;i=next.fetch_add(1))
        encodeOne(rgba,width,stride,quality,subsamp,strips[static_cast<size_t>(i)]);};
    std::vector<std::thread> workers;
    try {for(int i=1;i<std::min(count,int(threads));++i)workers.emplace_back(work);}catch(...){/* finish with available workers */}
    work();for(auto&thread:workers)thread.join();
    for(auto& s:strips){if(!s.error.empty()||!parseSegment(s))return false;}
    const auto& first=strips[0];
    for(int i=1;i<count;++i){const auto& s=strips[static_cast<size_t>(i)];
        if(s.sofHeight!=first.sofHeight||s.scan!=first.scan||
           memcmp(first.bytes.p,s.bytes.p,s.sofHeight)!=0||
           memcmp(first.bytes.p+first.sofHeight+2,s.bytes.p+s.sofHeight+2,
                  first.scan-first.sofHeight-2)!=0)return false;
    }
    // SOF height is full-height, and each independent entropy stream begins at a restart boundary.
    size_t size=first.scan+6+2;for(const auto&s:strips){size+=s.bytes.n-2-s.scan+2;}
    if(size>kMaxOutput)return false;
    output.clear();output.reserve(size);
    output.insert(output.end(),first.bytes.p,first.bytes.p+first.sos);
    // Restart interval is exactly the number of MCUs encoded by one full strip.
    output.push_back(0xff);output.push_back(0xdd);put16(output,4);put16(output,unsigned(mcusPerRow*stripMcuRows));
    output.insert(output.end(),first.bytes.p+first.sos,first.bytes.p+first.scan);
    output[first.sofHeight]=uint8_t(height>>8);output[first.sofHeight+1]=uint8_t(height);
    for(int i=0;i<count;++i){auto&s=strips[static_cast<size_t>(i)];
        if(i){output.push_back(0xff);output.push_back(uint8_t(0xd0+((i-1)&7)));}
        output.insert(output.end(),s.bytes.p+s.scan,s.bytes.p+s.bytes.n-2);
    }
    output.push_back(0xff);output.push_back(0xd9);stripCount=count;return true;
}
static bool compress(const uint8_t*rgba,int w,int h,int stride,int q,int subsamp,int pixelFormat,
                     std::vector<uint8_t>&result,int&strips){
    strips=1;
    if(!rgba||w<=0||h<=0||w>32767||h>32767||stride<=0||
       (pixelFormat==TJPF_RGBA&&stride<w*4)||
       (pixelFormat==TJPF_GRAY&&stride<w))return false;
    if(pixelFormat==TJPF_RGBA){
        try {if(parallelStrips(rgba,w,h,stride,q,subsamp,result,strips))return true;}
        catch(...){/* Allocation/thread failure: retry the proven one-thread TurboJPEG path. */}
        result.clear();strips=1;
    }
    Turbo t;TurboBytes bytes;
    if(!setup(t.h,q,subsamp)||tj3Compress8(t.h,rgba,w,stride,h,pixelFormat,&bytes.p,&bytes.n)!=0
       ||!bytes.p||!bytes.n)return false;
    result.assign(bytes.p,bytes.p+bytes.n);return true;
}
// Embed the same profile bytes as the established Iris motionv2jpeg writer, not RAWR's color profile.
static bool addDisplayP3Icc(std::vector<uint8_t>&base){
    auto profile=ultrahdr::IccHelper::writeIccProfile(UHDR_CT_SRGB,UHDR_CG_DISPLAY_P3);
    if(!profile||profile->getLength()<=ultrahdr::kICCIdentifierSize||base.size()<2||base[0]!=0xff||base[1]!=0xd8)return false;
    const size_t n=profile->getLength()-ultrahdr::kICCIdentifierSize;
    if(n+16>65535)return false;
    const uint8_t*data=static_cast<const uint8_t*>(profile->getData())+ultrahdr::kICCIdentifierSize;
    std::vector<uint8_t> tagged;tagged.reserve(base.size()+n+18);tagged.push_back(0xff);tagged.push_back(0xd8);
    tagged.push_back(0xff);tagged.push_back(0xe2);put16(tagged,unsigned(n+16));
    static constexpr char ident[]="ICC_PROFILE";
    tagged.insert(tagged.end(),ident,ident+sizeof(ident)); // includes NUL; 12 bytes
    tagged.push_back(1);tagged.push_back(1); // seq 1 of 1; APP2 header 14 bytes
    tagged.insert(tagged.end(),data,data+n);tagged.insert(tagged.end(),base.begin()+2,base.end());
    base.swap(tagged);return true;
}
static bool readFile(const char*path,std::vector<uint8_t>&out){
    if(!path)return false;FILE*f=fopen(path,"rb");if(!f)return false;
    if(fseek(f,0,SEEK_END)!=0){fclose(f);return false;}
    long n=ftell(f);if(n<=0||size_t(n)>kMaxOutput||fseek(f,0,SEEK_SET)!=0){fclose(f);return false;}
    out.resize(size_t(n));const size_t got=fread(out.data(),1,out.size(),f);const int rc=fclose(f);
    return got==out.size()&&rc==0;
}
/* IRIS_26875_B_PUBLICATION_SAME_OWNED_PATH
 * 26874 used <output>.26874-pending without a .jpg extension in public
 * DCIM; Android's scoped MediaStore can deny that second sidecar path.
 * Iris's proven 26873 Motion publisher writes to the already-reserved final
 * JPEG path, then ImageSaver adds EXIF and reports completion. Adopt exactly
 * that output ownership; on any write/fsync/close error remove the partial
 * file before returning false. Never allow A or a second writer to publish.
 */
static bool writeOwnedJpeg(const char*path,const uint8_t*data,size_t bytes,std::string&error){
    if(!path||!data||bytes==0){error="write_invalid_input";return false;}
    int fd=open(path,O_WRONLY|O_CREAT|O_TRUNC|O_CLOEXEC,0600);
    if(fd<0){error="write_open errno="+std::to_string(errno);return false;}
    bool ok=true;size_t done=0;
    while(done<bytes){ssize_t n=::write(fd,data+done,bytes-done);
        if(n<0&&errno==EINTR)continue;
        if(n<=0){error="write_bytes errno="+std::to_string(errno);ok=false;break;}
        done+=size_t(n);
    }
    if(ok&&fsync(fd)!=0){error="write_fsync errno="+std::to_string(errno);ok=false;}
    if(close(fd)!=0){if(ok)error="write_close errno="+std::to_string(errno);ok=false;}
    if(!ok)unlink(path);
    return ok;
}
struct Metadata {std::array<float,3> lo{},hi{},gamma{},epsS{},epsH{};float minHdr=1.f,maxHdr=2.f;bool useBase=true;};
static bool fetch(JNIEnv*env,jfloatArray src,std::array<float,3>&dst){
    if(!src||env->GetArrayLength(src)!=3)return false;
    env->GetFloatArrayRegion(src,0,3,dst.data());return !env->ExceptionCheck();
}
static bool buildMetadata(JNIEnv*e,jfloatArray min,jfloatArray max,jfloatArray gamma,jfloatArray es,jfloatArray eh,
                          float ds,float dh,bool use,Metadata& m){
    m.minHdr=ds;m.maxHdr=dh;m.useBase=use;
    return fetch(e,min,m.lo)&&fetch(e,max,m.hi)&&fetch(e,gamma,m.gamma)&&fetch(e,es,m.epsS)&&fetch(e,eh,m.epsH);
}
static bool publish(const char*path,const std::vector<uint8_t>&base,const std::vector<uint8_t>&gain,
                    const Metadata*meta,std::string&error){
    if(base.empty()||base.size()>kMaxOutput){error="base_empty_or_oversize";return false;}
    if(!meta) return writeOwnedJpeg(path,base.data(),base.size(),error);
    if(gain.empty()||gain.size()>kMaxOutput){error="gain_empty_or_oversize";return false;}
    Encoder owner;if(!owner.p){error="uhdr_create_encoder";return false;}
    uhdr_compressed_image_t b{};b.data=const_cast<uint8_t*>(base.data());b.data_sz=b.capacity=base.size();
    b.cg=UHDR_CG_DISPLAY_P3;b.ct=UHDR_CT_SRGB;b.range=UHDR_CR_FULL_RANGE;
    uhdr_compressed_image_t g{};g.data=const_cast<uint8_t*>(gain.data());g.data_sz=g.capacity=gain.size();
    g.cg=UHDR_CG_UNSPECIFIED;g.ct=UHDR_CT_UNSPECIFIED;g.range=UHDR_CR_UNSPECIFIED;
    uhdr_gainmap_metadata_t m{};for(int i=0;i<3;i++){
        m.min_content_boost[i]=meta->lo[i];m.max_content_boost[i]=meta->hi[i];m.gamma[i]=meta->gamma[i];
        m.offset_sdr[i]=meta->epsS[i];m.offset_hdr[i]=meta->epsH[i];}
    m.hdr_capacity_min=meta->minHdr;m.hdr_capacity_max=meta->maxHdr;m.use_base_cg=meta->useBase?1:0;
    // Preserve the original 26873 pinned libultrahdr contract verbatim. Do
    // not suppress status: 26874 reduced every distinct failure to false.
    auto check=[&](const char*stage,const uhdr_error_info_t&st)->bool{
        if(st.error_code==UHDR_CODEC_OK)return true;
        error=std::string(stage)+" code="+std::to_string(int(st.error_code));
        if(st.has_detail&&st.detail[0]){error+=" detail=";error+=st.detail;}
        return false;
    };
    if(!check("uhdr_set_base",uhdr_enc_set_compressed_image(owner.p,&b,UHDR_BASE_IMG))||
       !check("uhdr_set_gain",uhdr_enc_set_gainmap_image(owner.p,&g,&m))||
       !check("uhdr_set_output",uhdr_enc_set_output_format(owner.p,UHDR_CODEC_JPG))||
       !check("uhdr_encode",uhdr_encode(owner.p)))return false;
    auto*out=uhdr_get_encoded_stream(owner.p);
    if(!out||!out->data||out->data_sz==0||out->data_sz>kMaxOutput){
        error="uhdr_stream_invalid";return false;
    }
    if(!is_uhdr_image(out->data,int(out->data_sz))){error="uhdr_stream_validation";return false;}
    return writeOwnedJpeg(path,static_cast<const uint8_t*>(out->data),out->data_sz,error);
}
static long ms(const std::chrono::steady_clock::time_point&then){
    return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now()-then).count();
}
} // namespace

extern "C" JNIEXPORT jboolean JNICALL
Java_com_particlesdevs_photoncamera_processing_ultrahdr_Iris26874BJpegPublisher_publishBitmapNative(
        JNIEnv* e,jclass,jobject bitmap,jobject gainBitmap,jstring output,jint quality,
        jfloatArray min,jfloatArray max,jfloatArray gamma,jfloatArray es,jfloatArray eh,jfloat ds,jfloat dh,jboolean use){
    Utf dest(e,output);if(!dest.p||quality!=98)return JNI_FALSE;
    LockedBitmap base(e,bitmap);if(!base.pixels||base.info.format!=ANDROID_BITMAP_FORMAT_RGBA_8888)return JNI_FALSE;
    LockedBitmap gain(e,gainBitmap);
    if(gainBitmap&&(!gain.pixels||(gain.info.format!=ANDROID_BITMAP_FORMAT_A_8&&gain.info.format!=ANDROID_BITMAP_FORMAT_RGBA_8888)))return JNI_FALSE;
    const bool uhdr=gainBitmap!=nullptr;
    Metadata md{};if(uhdr&&!buildMetadata(e,min,max,gamma,es,eh,ds,dh,use==JNI_TRUE,md))return JNI_FALSE;
    std::vector<uint8_t> b,g;int strips=1,gainStrips=1;
    const auto start=std::chrono::steady_clock::now();
    // Two independent compressors consume locked and immutable Android Bitmap buffers.
    bool baseOk=false,gainOk=!uhdr;
    try {
        auto baseEncode=[&](){try {
            baseOk=compress(base.pixels,int(base.info.width),int(base.info.height),int(base.info.stride),
                            quality,TJSAMP_444,TJPF_RGBA,b,strips)&&addDisplayP3Icc(b);
        }catch(...){baseOk=false;}};
        std::thread baseWorker;
        try { baseWorker=std::thread([&](){::setpriority(PRIO_PROCESS,0,10);baseEncode();}); }
        catch (...) { /* No thread resources: preserve ordinary single-thread encoding. */ }
        struct JoinOnExit { std::thread& t; ~JoinOnExit(){if(t.joinable())t.join();} } join{baseWorker};
        if(uhdr) gainOk=compress(gain.pixels,int(gain.info.width),int(gain.info.height),int(gain.info.stride),
                                95,gain.info.format==ANDROID_BITMAP_FORMAT_A_8?TJSAMP_GRAY:TJSAMP_444,
                                gain.info.format==ANDROID_BITMAP_FORMAT_A_8?TJPF_GRAY:TJPF_RGBA,g,gainStrips);
        if(baseWorker.joinable())baseWorker.join();else baseEncode();
        const long encodedMs=ms(start);
        std::string error;
        if(!baseOk)error="base_compress_or_p3_icc";
        else if(!gainOk)error="gain_compress";
        bool ok=baseOk&&gainOk&&publish(dest.p,b,g,uhdr?&md:nullptr,error);
        bool stripCompatibilityRetry=false;
        // IRIS_26875_REAL_26874_STRIP_JPEGR_PARSER_REGRESSION:
        // The pinned libultrahdr JPEG scanner (unlike RAWR's own container
        // muxer) may reject DRI/RST structure. Retry ONLY that exact base
        // scanner failure with B's private optimized single-thread JPEG,
        // never A's encoder, never a single-frame processing fallback.
        if(!ok&&strips>1&&error.rfind("uhdr_set_base",0)==0){
            stripCompatibilityRetry=true;
            Turbo t;TurboBytes single;
            if(setup(t.h,quality,TJSAMP_444)&&
               tj3Compress8(t.h,base.pixels,int(base.info.width),int(base.info.stride),
                            int(base.info.height),TJPF_RGBA,&single.p,&single.n)==0&&single.p){
                std::vector<uint8_t> restored(single.p,single.p+single.n);
                if(addDisplayP3Icc(restored)){
                    error.clear();
                    ok=publish(dest.p,restored,g,uhdr?&md:nullptr,error);
                }else error="retry_p3_icc";
            }else error="retry_private_turbo_encode";
        }
        gTelemetry="mode=normal codec=optimized_isolated_26874 strips="+std::to_string(strips)
                +" gainStrips="+std::to_string(gainStrips)+" encodedWallMs="+std::to_string(encodedMs)
                +" totalMs="+std::to_string(ms(start))+" stripParserRetry="+(stripCompatibilityRetry?"true":"false")
                +" published="+(ok?"true":"false")
                +(ok?"":(" failedStage="+error));
        __android_log_print(ANDROID_LOG_INFO,TAG,"IRIS_26874_B_JPEG_OWNER %s",gTelemetry.c_str());
        return ok?JNI_TRUE:JNI_FALSE;
    }catch(const std::exception&ex){gTelemetry=std::string("mode=normal failure=")+ex.what();}
    catch(...){gTelemetry="mode=normal failure=native_exception";}
    __android_log_print(ANDROID_LOG_ERROR,TAG,"IRIS_26874_B_JPEG_OWNER %s",gTelemetry.c_str());
    return JNI_FALSE;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_particlesdevs_photoncamera_processing_ultrahdr_Iris26874BJpegPublisher_publishPrecompressedNative(
        JNIEnv*e,jclass,jstring bp,jstring gp,jstring op,
        jfloatArray min,jfloatArray max,jfloatArray gamma,jfloatArray es,jfloatArray eh,jfloat ds,jfloat dh,jboolean use){
    Utf base(e,bp),gain(e,gp),out(e,op);if(!base.p||!gain.p||!out.p)return JNI_FALSE;
    std::vector<uint8_t> b,g;Metadata md{};
    if(!buildMetadata(e,min,max,gamma,es,eh,ds,dh,use==JNI_TRUE,md)||!readFile(base.p,b)||!readFile(gain.p,g))return JNI_FALSE;
    try {
        const auto start=std::chrono::steady_clock::now();std::string error;
        bool ok=publish(out.p,b,g,&md,error);
        gTelemetry="mode=true2x_encoded_stream codec=original_stream_renderer packageMs="+std::to_string(ms(start))
                +" published="+(ok?"true":"false")+(ok?"":(" failedStage="+error));
        __android_log_print(ANDROID_LOG_INFO,TAG,"IRIS_26874_B_JPEG_OWNER %s",gTelemetry.c_str());
        return ok?JNI_TRUE:JNI_FALSE;
    }catch(const std::exception&ex){gTelemetry=std::string("mode=true2x failure=")+ex.what();}
    catch(...){gTelemetry="mode=true2x failure=native_exception";}
    __android_log_print(ANDROID_LOG_ERROR,TAG,"IRIS_26874_B_JPEG_OWNER %s",gTelemetry.c_str());
    return JNI_FALSE;
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_particlesdevs_photoncamera_processing_ultrahdr_Iris26874BJpegPublisher_getLastTelemetryNative(
        JNIEnv*env,jclass){return env->NewStringUTF(gTelemetry.c_str());}


/* IRIS_26876_B_TRUE50MP_GPU_RGBA8_GAIN_FINAL_PUBLICATION
 * A producer-completed, one-shot RGBA8 HardwareBuffer carries Display-P3
 * SDR RGB in channels 0..2 and the existing full-res gain-map code in A.
 * The B-private TurboJPEG writer ignores SDR alpha and extracts gain A8.
 * No 50MP RGB16F filename or 50MP CPU color/clipping work is permitted.
 * The caller MUST wait for its actual EGL/Vulkan producer completion fence,
 * validate the GPU error report, and keep this HB alive until this returns.
 * This JNI endpoint accepts only final display-domain pixels.
 */
namespace {
struct Iris26876LockedRgbaGain {
    AHardwareBuffer* handle=nullptr;
    AHardwareBuffer_Desc description{};
    const uint8_t* pixels=nullptr;
    bool locked=false;
    explicit Iris26876LockedRgbaGain(JNIEnv* env,jobject obj){
        if(!obj)return;
        handle=AHardwareBuffer_fromHardwareBuffer(env,obj);
        if(handle)AHardwareBuffer_describe(handle,&description);
    }
    bool lock(int expectWidth,int expectHeight){
        if(!handle||expectWidth<=0||expectHeight<=0||description.width!=uint32_t(expectWidth)||
           description.height!=uint32_t(expectHeight)||description.layers!=1u||
           description.format!=AHARDWAREBUFFER_FORMAT_R8G8B8A8_UNORM||
           description.stride<description.width||
           !(description.usage&AHARDWAREBUFFER_USAGE_CPU_READ_OFTEN)||
           uint64_t(description.stride)*4u>uint64_t(std::numeric_limits<int>::max())||
           uint64_t(description.width)*description.height>uint64_t(8192u)*8192u)
            return false;
        void* mapped=nullptr;
        // -1 is valid ONLY after caller has waited on the producer GPU fence.
        if(AHardwareBuffer_lock(handle,AHARDWAREBUFFER_USAGE_CPU_READ_OFTEN,-1,nullptr,&mapped)!=0 || !mapped)
            return false;
        pixels=static_cast<const uint8_t*>(mapped);locked=true;
        return true;
    }
    int strideBytes()const{return int(description.stride)*4;}
    ~Iris26876LockedRgbaGain(){
        if(locked)AHardwareBuffer_unlock(handle,nullptr);
    }
    Iris26876LockedRgbaGain(const Iris26876LockedRgbaGain&)=delete;
    Iris26876LockedRgbaGain& operator=(const Iris26876LockedRgbaGain&)=delete;
};
} // namespace

extern "C" JNIEXPORT jboolean JNICALL
Java_com_particlesdevs_photoncamera_processing_ultrahdr_Iris26874BJpegPublisher_publishGpuRgbaGainNative(
        JNIEnv* env,jclass,jobject buffer,jstring outPath,jint width,jint height,
        jint quality,jboolean hasGain,jfloatArray min,jfloatArray max,jfloatArray gamma,
        jfloatArray es,jfloatArray eh,jfloat ds,jfloat dh,jboolean use){
    gTelemetry="mode=sr50_gpu stage=start published=false";
    Utf path(env,outPath);
    if(!path.p||quality!=98||width<=0||height<=0||
       uint64_t(width)*height>uint64_t(8192u)*8192u){
        gTelemetry="mode=sr50_gpu failedStage=input_contract";return JNI_FALSE;
    }
    const bool uhdr=hasGain==JNI_TRUE;
    Metadata md{};
    if(uhdr&&!buildMetadata(env,min,max,gamma,es,eh,ds,dh,use==JNI_TRUE,md)){
        gTelemetry="mode=sr50_gpu failedStage=gain_metadata";return JNI_FALSE;
    }
    Iris26876LockedRgbaGain surface(env,buffer);
    if(!surface.lock(width,height)){
        gTelemetry="mode=sr50_gpu failedStage=hardware_buffer_lock_or_shape";return JNI_FALSE;
    }
    const auto begin=std::chrono::steady_clock::now();
    std::vector<uint8_t> baseJpeg,gainJpeg;
    int baseStrips=1,gainStrips=1;
    try {
        // CPU merely consumes final GPU-rendered RGBA8 pixels, never performs
        // color, clipping, demosaic, or gain fitting. The actual bitstream is
        // encoded with the SAME private TurboJPEG path as successful 26875 B.
        bool baseOk=false,gainOk=!uhdr;
        auto encodeBase=[&](){
            try {baseOk=compress(surface.pixels,width,height,surface.strideBytes(),
                         98,TJSAMP_444,TJPF_RGBA,baseJpeg,baseStrips)&&addDisplayP3Icc(baseJpeg);}
            catch(...){baseOk=false;}
        };
        std::thread worker;
        try {worker=std::thread([&](){::setpriority(PRIO_PROCESS,0,10);encodeBase();});}
        catch(...){/* the caller thread will execute the same encoder */}
        struct Join {std::thread& t;~Join(){if(t.joinable())t.join();}} join{worker};
        if(uhdr){
            // A8 is the exact alpha code written by the fused GPU renderer;
            // never derive gain anew from SDR RGB or modify its transfer curve.
            const size_t samples=static_cast<size_t>(width)*height;
            std::vector<uint8_t> gray(samples);
            for(int y=0;y<height;++y){
                const uint8_t*row=surface.pixels+static_cast<size_t>(y)*surface.strideBytes();
                uint8_t*dst=gray.data()+static_cast<size_t>(y)*width;
                for(int x=0;x<width;++x)dst[x]=row[static_cast<size_t>(x)*4u+3u];
            }
            gainOk=compress(gray.data(),width,height,width,95,TJSAMP_GRAY,TJPF_GRAY,gainJpeg,gainStrips);
        }
        if(worker.joinable())worker.join();else encodeBase();
        std::string error;
        if(!baseOk)error="base_compress_or_p3_icc";
        else if(!gainOk)error="gain_compress";
        bool ok=baseOk&&gainOk&&publish(path.p,baseJpeg,gainJpeg,uhdr?&md:nullptr,error);
        bool scannerRetry=false;
        if(!ok&&baseOk&&gainOk&&baseStrips>1&&error.rfind("uhdr_set_base",0)==0){
            scannerRetry=true;
            Turbo t;TurboBytes single;
            if(setup(t.h,98,TJSAMP_444)&&tj3Compress8(t.h,surface.pixels,width,
                      surface.strideBytes(),height,TJPF_RGBA,&single.p,&single.n)==0&&single.p){
                std::vector<uint8_t> legacyCompatible(single.p,single.p+single.n);
                if(addDisplayP3Icc(legacyCompatible)){
                    error.clear();ok=publish(path.p,legacyCompatible,gainJpeg,uhdr?&md:nullptr,error);
                }else error="retry_p3_icc";
            }else error="retry_private_turbo_encode";
        }
        gTelemetry="mode=sr50_gpu codec=optimized_isolated_26874 strips="+std::to_string(baseStrips)+
                " gainStrips="+std::to_string(gainStrips)+" paddedStride="+
                std::to_string(surface.strideBytes()!=width*4)+" scannerRetry="+
                (scannerRetry?"true":"false")+" elapsedMs="+std::to_string(ms(begin))+
                " published="+(ok?"true":"false")+(ok?"":(" failedStage="+error));
        __android_log_print(ok?ANDROID_LOG_INFO:ANDROID_LOG_ERROR,TAG,
                            "IRIS_26876_B_GPU_JPEGR %s",gTelemetry.c_str());
        return ok?JNI_TRUE:JNI_FALSE;
    }catch(const std::exception& e){gTelemetry=std::string("mode=sr50_gpu failedStage=exception detail=")+e.what();}
    catch(...){gTelemetry="mode=sr50_gpu failedStage=unknown_exception";}
    __android_log_print(ANDROID_LOG_ERROR,TAG,"IRIS_26876_B_GPU_JPEGR %s",gTelemetry.c_str());
    return JNI_FALSE;
}

/* IRIS_26876_B_GPU_TO_HEIC_COMPRESSED_STREAMS
 * HEIC grid requires two compressed JPEG inputs, not a 50MP RGB16F source.
 * Its B-only GPU producer is the SAME validated P3/gain raster used by JPEG/R.
 * Files are compressed and temporary; they are NOT RGB16F, clipbits or CPU
 * scene color. The Java shutter owner deletes BOTH on all failure paths.
 */
extern "C" JNIEXPORT jboolean JNICALL
Java_com_particlesdevs_photoncamera_processing_ultrahdr_Iris26874BJpegPublisher_encodeGpuHeicPairNative(
        JNIEnv*env,jclass,jobject hb,jstring basePath,jstring gainPath,
        jint w,jint h,jint quality){
    Utf base(env,basePath),gain(env,gainPath);
    if(!base.p||!gain.p||quality!=98||w<=0||h<=0||
       uint64_t(w)*h>uint64_t(8192)*8192||strcmp(base.p,gain.p)==0)return JNI_FALSE;
    Iris26876LockedRgbaGain mapped(env,hb);
    if(!mapped.lock(w,h))return JNI_FALSE;
    const auto begin=std::chrono::steady_clock::now();
    std::vector<uint8_t> b,g;
    int strips=1,gainStrips=1;
    try {
        bool ok=compress(mapped.pixels,w,h,mapped.strideBytes(),98,TJSAMP_444,TJPF_RGBA,b,strips)
                &&addDisplayP3Icc(b);
        if(!ok)return JNI_FALSE;
        std::vector<uint8_t> gray(static_cast<size_t>(w)*h);
        for(int y=0;y<h;y++){
            const uint8_t*src=mapped.pixels+size_t(y)*mapped.strideBytes();
            for(int x=0;x<w;x++)gray[size_t(y)*w+x]=src[size_t(x)*4u+3u];
        }
        ok=compress(gray.data(),w,h,w,95,TJSAMP_GRAY,TJPF_GRAY,g,gainStrips);
        if(!ok){unlink(base.p);unlink(gain.p);return JNI_FALSE;}
        std::string error;
        ok=writeOwnedJpeg(base.p,b.data(),b.size(),error)&&
           writeOwnedJpeg(gain.p,g.data(),g.size(),error);
        if(!ok){unlink(base.p);unlink(gain.p);}
        gTelemetry="mode=sr50_gpu_heic_pair strips="+std::to_string(strips)+
            " paddedStride="+std::to_string(mapped.strideBytes()!=w*4)+
            " elapsedMs="+std::to_string(ms(begin))+" success="+(ok?"true":"false");
        __android_log_print(ok?ANDROID_LOG_INFO:ANDROID_LOG_ERROR,TAG,
             "IRIS_26876_B_GPU_HEIC_COMPRESSED_INPUTS %s",gTelemetry.c_str());
        return ok?JNI_TRUE:JNI_FALSE;
    }catch(...){unlink(base.p);unlink(gain.p);return JNI_FALSE;}
}
