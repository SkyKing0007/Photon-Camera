#include "SpektraRawCpuOwner.h"

#include <android/log.h>
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstring>
#include <mutex>
#include <thread>
#include <vector>

namespace iris_spektra {
namespace {

#define SPEKTRA_RAW_LOGI(...) __android_log_print(ANDROID_LOG_INFO, "SpektraRawCpu", __VA_ARGS__)
#define SPEKTRA_RAW_LOGW(...) __android_log_print(ANDROID_LOG_WARN, "SpektraRawCpu", __VA_ARGS__)

struct Vec3 { float r, g, b; };

inline Vec3 add(Vec3 a, Vec3 b) { return {a.r+b.r,a.g+b.g,a.b+b.b}; }
inline Vec3 mul(Vec3 a, float s) { return {a.r*s,a.g*s,a.b*s}; }
inline Vec3 max0(Vec3 a) { return {std::max(0.0f,a.r),std::max(0.0f,a.g),std::max(0.0f,a.b)}; }
inline float luminance(Vec3 a) { return 0.2126f*a.r + 0.7152f*a.g + 0.0722f*a.b; }

uint16_t floatToHalf(float f) {
    uint32_t x = 0;
    std::memcpy(&x, &f, sizeof(x));
    const uint32_t sign = (x >> 16u) & 0x8000u;
    uint32_t mantissa = x & 0x007fffffu;
    int32_t exponent = static_cast<int32_t>((x >> 23u) & 0xffu) - 127 + 15;
    if (((x >> 23u) & 0xffu) == 0xffu) {
        if (mantissa == 0u) return static_cast<uint16_t>(sign | 0x7c00u);
        return static_cast<uint16_t>(sign | 0x7e00u);
    }
    if (exponent <= 0) {
        if (exponent < -10) return static_cast<uint16_t>(sign);
        mantissa = (mantissa | 0x00800000u) >> static_cast<uint32_t>(1 - exponent);
        if (mantissa & 0x00001000u) mantissa += 0x00002000u;
        return static_cast<uint16_t>(sign | (mantissa >> 13u));
    }
    if (exponent >= 31) return static_cast<uint16_t>(sign | 0x7c00u);
    if (mantissa & 0x00001000u) {
        mantissa += 0x00002000u;
        if (mantissa & 0x00800000u) {
            mantissa = 0;
            ++exponent;
            if (exponent >= 31) return static_cast<uint16_t>(sign | 0x7c00u);
        }
    }
    return static_cast<uint16_t>(sign | (static_cast<uint32_t>(exponent) << 10u) | (mantissa >> 13u));
}

float halfToFloat(uint16_t h) {
    const uint32_t sign = static_cast<uint32_t>(h & 0x8000u) << 16u;
    const uint32_t exponent = (h >> 10u) & 0x1fu;
    uint32_t mantissa = h & 0x03ffu;
    uint32_t bits = 0;
    if (exponent == 0u) {
        if (mantissa == 0u) bits = sign;
        else {
            int e = -14;
            while ((mantissa & 0x0400u) == 0u) { mantissa <<= 1u; --e; }
            mantissa &= 0x03ffu;
            bits = sign | (static_cast<uint32_t>(e + 127) << 23u) | (mantissa << 13u);
        }
    } else if (exponent == 31u) {
        bits = sign | 0x7f800000u | (mantissa << 13u);
    } else {
        bits = sign | ((exponent + (127u - 15u)) << 23u) | (mantissa << 13u);
    }
    float f = 0.0f;
    std::memcpy(&f, &bits, sizeof(f));
    return f;
}

int clampParity(int value, int lo, int hi, int parity) {
    int v = std::max(lo, std::min(hi, value));
    if ((v & 1) == parity) return v;
    if (v + 1 <= hi) return v + 1;
    if (v - 1 >= lo) return v - 1;
    return v;
}

struct CpuDevelop {
    const RawDevelopRequest& q;

    uint8_t readByte(size_t index) const {
        return index < q.sourceBytes ? q.source[index] : 0u;
    }

    void clampActivePreservePhase(int* x, int* y) const {
        *x = clampParity(*x, q.activeRawDomain[0], q.activeRawDomain[2]-1, *x & 1);
        *y = clampParity(*y, q.activeRawDomain[1], q.activeRawDomain[3]-1, *y & 1);
    }

    uint16_t rawSample(int x, int y) const {
        clampActivePreservePhase(&x,&y);
        const size_t row = static_cast<size_t>(y) * static_cast<size_t>(q.rowStride);
        if (q.format == 37) { // RAW10
            const size_t group = row + static_cast<size_t>(x >> 2) * 5u;
            const int lane = x & 3;
            return static_cast<uint16_t>((static_cast<uint16_t>(readByte(group + lane)) << 2u)
                    | ((readByte(group + 4u) >> (lane * 2)) & 3u));
        }
        if (q.format == 38) { // RAW12
            const size_t group = row + static_cast<size_t>(x >> 1) * 3u;
            const int lane = x & 1;
            const uint8_t lo = readByte(group + 2u);
            return static_cast<uint16_t>((static_cast<uint16_t>(readByte(group + lane)) << 4u)
                    | (lane == 0 ? (lo & 15u) : ((lo >> 4u) & 15u)));
        }
        const int stride = std::max(2, q.pixelStride);
        const size_t p = row + static_cast<size_t>(x) * static_cast<size_t>(stride);
        return static_cast<uint16_t>(readByte(p) | (static_cast<uint16_t>(readByte(p+1u)) << 8u));
    }

    int phaseAt(int x, int y) const { return (x & 1) | ((y & 1) << 1); }
    int colorAt(int x, int y) const {
        const int phase = phaseAt(x,y);
        if (phase == q.cfaArrangement) return 0;      // red
        if (phase == (q.cfaArrangement ^ 3)) return 2; // blue
        return 1;
    }

    float lscGainChannel(int x, int y, int ch) const {
        if (!q.lensShading || q.lensShadingRows <= 0 || q.lensShadingCols <= 0) return 1.0f;
        const float minX = static_cast<float>(q.activeRawDomain[0]);
        const float minY = static_cast<float>(q.activeRawDomain[1]);
        const float maxX = static_cast<float>(std::max(q.activeRawDomain[0]+1, q.activeRawDomain[2]-1));
        const float maxY = static_cast<float>(std::max(q.activeRawDomain[1]+1, q.activeRawDomain[3]-1));
        const float u = std::max(0.0f, std::min(1.0f, (static_cast<float>(x)-minX) / std::max(1.0f,maxX-minX)));
        const float v = std::max(0.0f, std::min(1.0f, (static_cast<float>(y)-minY) / std::max(1.0f,maxY-minY)));
        const float fx = u * static_cast<float>(std::max(1,q.lensShadingCols-1));
        const float fy = v * static_cast<float>(std::max(1,q.lensShadingRows-1));
        const int x0 = std::max(0,std::min(q.lensShadingCols-1,static_cast<int>(std::floor(fx))));
        const int y0 = std::max(0,std::min(q.lensShadingRows-1,static_cast<int>(std::floor(fy))));
        const int x1 = std::min(q.lensShadingCols-1,x0+1);
        const int y1 = std::min(q.lensShadingRows-1,y0+1);
        const float tx = fx-static_cast<float>(x0), ty = fy-static_cast<float>(y0);
        auto at=[&](int xx,int yy){return q.lensShading[(yy*q.lensShadingCols+xx)*4+ch];};
        const float a = at(x0,y0)*(1.0f-tx)+at(x1,y0)*tx;
        const float b = at(x0,y1)*(1.0f-tx)+at(x1,y1)*tx;
        const float g = a*(1.0f-ty)+b*ty;
        return std::isfinite(g) && g > 0.0f ? g : 1.0f;
    }

    int semanticLscChannel(int x, int y) const {
        const int c=colorAt(x,y);
        if (c==0) return 0;
        if (c==2) return 3;
        const int sensorRowParity=(y&1)^((q.bayerOffset>>1)&1);
        return sensorRowParity==0 ? 1 : 2;
    }

    float sampleNorm(int x, int y) const {
        const int phase = phaseAt(x,y);
        const int black = q.blackLevel4[phase];
        const float denom = std::max(1.0f, static_cast<float>(q.whiteLevel-black));
        const float normalized=std::max(0.0f,(static_cast<float>(rawSample(x,y))-static_cast<float>(black))/denom);
        return normalized*lscGainChannel(x,y,semanticLscChannel(x,y));
    }

    float averageColor(int x, int y, int target, bool diagonal) const {
        const int offsets[4][2] = {
            {diagonal?-1:-1, diagonal?-1:0},
            {diagonal? 1: 1, diagonal?-1:0},
            {diagonal?-1: 0, diagonal? 1:-1},
            {diagonal? 1: 0, diagonal? 1: 1}
        };
        float sum=0.0f; int n=0;
        for (const auto& d: offsets) {
            const int xx=x+d[0], yy=y+d[1];
            if (colorAt(xx,yy)==target) { sum += sampleNorm(xx,yy); ++n; }
        }
        if (n == 0) {
            const int farOffsets[8][2]={{-2,0},{2,0},{0,-2},{0,2},{-2,-2},{2,-2},{-2,2},{2,2}};
            for (const auto& d: farOffsets) {
                const int xx=x+d[0], yy=y+d[1];
                if (colorAt(xx,yy)==target) { sum += sampleNorm(xx,yy); ++n; }
            }
        }
        return n > 0 ? sum/static_cast<float>(n) : sampleNorm(x,y);
    }

    Vec3 demosaicRaw(int x, int y) const {
        const int c=colorAt(x,y);
        Vec3 rgb{};
        if (c==0) { rgb.r=sampleNorm(x,y); rgb.g=averageColor(x,y,1,false); rgb.b=averageColor(x,y,2,true); }
        else if (c==2) { rgb.b=sampleNorm(x,y); rgb.g=averageColor(x,y,1,false); rgb.r=averageColor(x,y,0,true); }
        else { rgb.g=sampleNorm(x,y); rgb.r=averageColor(x,y,0,false); rgb.b=averageColor(x,y,2,false); }
        return max0(rgb);
    }

    Vec3 highlightRecover(int x, int y, Vec3 center) const {
        if (!q.savedPhoto) return center;
        const float clip = std::max(0.5f,std::min(1.2f,q.sensorClipThreshold));
        const bool cr=center.r>=clip, cg=center.g>=clip, cb=center.b>=clip;
        if ((!cr&&!cg&&!cb) || (cr&&cg&&cb)) return center;
        Vec3 n = mul(add(add(demosaicRaw(x-2,y),demosaicRaw(x+2,y)),
                         add(demosaicRaw(x,y-2),demosaicRaw(x,y+2))),0.25f);
        const float centerG=std::max(center.g,1e-5f), neighborG=std::max(n.g,1e-5f);
        const float rr=n.r/neighborG, br=n.b/neighborG;
        if (cr) center.r=std::max(center.r,rr*centerG);
        if (cb) center.b=std::max(center.b,br*centerG);
        if (cg) {
            const float fromR=center.r/std::max(rr,1e-4f);
            const float fromB=center.b/std::max(br,1e-4f);
            center.g=std::max(center.g,0.5f*(fromR+fromB));
        }
        return center;
    }

    Vec3 sensorToLinear(Vec3 s) const {
        Vec3 out{
            q.sensorToLinearSrgb[0]*s.r + q.sensorToLinearSrgb[1]*s.g + q.sensorToLinearSrgb[2]*s.b,
            q.sensorToLinearSrgb[3]*s.r + q.sensorToLinearSrgb[4]*s.g + q.sensorToLinearSrgb[5]*s.b,
            q.sensorToLinearSrgb[6]*s.r + q.sensorToLinearSrgb[7]*s.g + q.sensorToLinearSrgb[8]*s.b};
        if (!std::isfinite(out.r)) out.r=0.0f;
        if (!std::isfinite(out.g)) out.g=0.0f;
        if (!std::isfinite(out.b)) out.b=0.0f;
        return max0(out);
    }

    Vec3 linearAt(int x,int y) const { return sensorToLinear(highlightRecover(x,y,demosaicRaw(x,y))); }

    Vec3 reconstructForOutput(int ox,int oy) const {
        const int cropL=q.sourceCrop[0], cropT=q.sourceCrop[1];
        const int cropW=q.sourceCrop[2]-q.sourceCrop[0], cropH=q.sourceCrop[3]-q.sourceCrop[1];
        if (q.savedPhoto && q.outputWidth==cropW && q.outputHeight==cropH) return linearAt(cropL+ox,cropT+oy);
        // VF-S is a preview path, not a full-resolution reconstruction pass. Reconstruct one
        // source-lattice RGB sample at the center of each reduced footprint; this keeps CFA/color
        // semantics identical to the saved path while avoiding four redundant demosaic evaluations.
        const float sx=static_cast<float>(cropL)+(static_cast<float>(ox)+0.5f)*cropW/q.outputWidth;
        const float sy=static_cast<float>(cropT)+(static_cast<float>(oy)+0.5f)*cropH/q.outputHeight;
        return linearAt(static_cast<int>(std::floor(sx)),static_cast<int>(std::floor(sy)));
    }
};

bool validate(const RawDevelopRequest& q, std::string* error) {
    auto fail=[&](const char* m){if(error)*error=m;return false;};
    if (!q.source || q.sourceBytes==0 || q.sourceWidth<=1 || q.sourceHeight<=1 || q.rowStride<=0) return fail("Invalid packed RAW input");
    if (q.format!=32 && q.format!=37 && q.format!=38) return fail("Unsupported packed RAW format");
    const int minRow=q.format==37?((q.sourceWidth+3)/4)*5:q.format==38?((q.sourceWidth+1)/2)*3:q.sourceWidth*std::max(2,q.pixelStride);
    const uint64_t required=static_cast<uint64_t>(q.sourceHeight-1)*q.rowStride+static_cast<uint64_t>(minRow);
    if (q.rowStride<minRow || required>q.sourceBytes) return fail("Packed RAW row-stride/buffer contract mismatch");
    if (q.cfaArrangement<0 || q.cfaArrangement>3 || q.bayerOffset<0 || q.bayerOffset>3) return fail("Unresolved CFA/Bayer origin");
    if (q.whiteLevel<=0 || q.outputWidth<=0 || q.outputHeight<=0) return fail("Invalid RAW/output levels");
    if (q.rawBounds[0]<0 || q.rawBounds[1]<0 || q.rawBounds[2]>q.sourceWidth || q.rawBounds[3]>q.sourceHeight || q.rawBounds[2]<=q.rawBounds[0] || q.rawBounds[3]<=q.rawBounds[1]) return fail("Invalid RAW bounds");
    const int* domains[2]={q.sourceCrop,q.activeRawDomain};
    for (const int* r:domains) if (r[0]<q.rawBounds[0] || r[1]<q.rawBounds[1] || r[2]>q.rawBounds[2] || r[3]>q.rawBounds[3] || r[2]<=r[0] || r[3]<=r[1]) return fail("RAW domains disagree");
    if (q.activeRawDomain[2]-q.activeRawDomain[0]<2 || q.activeRawDomain[3]-q.activeRawDomain[1]<2) return fail("Active RAW domain cannot preserve CFA phase");
    if (q.lensShading && (q.lensShadingRows<=0 || q.lensShadingCols<=0)) return fail("Invalid lens shading dimensions");
    const uint64_t outputBytes=static_cast<uint64_t>(q.outputWidth)*q.outputHeight*8ull;
    if (outputBytes==0 || outputBytes>static_cast<uint64_t>(0x7fffffff)) return fail("RAW output is too large");
    return true;
}

void storePixel(std::vector<uint8_t>& out, int width, int x, int y, Vec3 rgb) {
    uint16_t h[4]={floatToHalf(std::max(0.0f,rgb.r)),floatToHalf(std::max(0.0f,rgb.g)),
                   floatToHalf(std::max(0.0f,rgb.b)),floatToHalf(1.0f)};
    const size_t p=(static_cast<size_t>(y)*width+static_cast<size_t>(x))*8u;
    std::memcpy(out.data()+p,h,sizeof(h));
}

Vec3 loadPixel(const std::vector<uint8_t>& out, int width, int x, int y) {
    const size_t p=(static_cast<size_t>(y)*width+static_cast<size_t>(x))*8u;
    uint16_t h[4]{}; std::memcpy(h,out.data()+p,sizeof(h));
    return {halfToFloat(h[0]),halfToFloat(h[1]),halfToFloat(h[2])};
}

void applySavedChromaDenoise(std::vector<uint8_t>& out, int width, int height, float strength) {
    strength=std::max(0.0f,std::min(1.0f,strength));
    if (strength<=0.0f || width<5 || height<5) return;
    // Preserve original rows that will be needed after earlier rows are overwritten. Future rows are
    // still original in `out`; horizontal neighbors come from a current-row snapshot.
    std::vector<uint8_t> prior2(static_cast<size_t>(width)*8u), prior1(static_cast<size_t>(width)*8u), current(static_cast<size_t>(width)*8u);
    bool have1=false,have2=false;
    for (int y=0;y<height;++y) {
        const size_t rowBytes=static_cast<size_t>(width)*8u;
        std::memcpy(current.data(),out.data()+static_cast<size_t>(y)*rowBytes,rowBytes);
        for (int x=0;x<width;++x) {
            auto rowPixel=[&](const std::vector<uint8_t>& row,int xx){
                xx=std::max(0,std::min(width-1,xx)); uint16_t h[4]{}; std::memcpy(h,row.data()+static_cast<size_t>(xx)*8u,sizeof(h));
                return Vec3{halfToFloat(h[0]),halfToFloat(h[1]),halfToFloat(h[2])};};
            Vec3 center=rowPixel(current,x);
            Vec3 left=rowPixel(current,x-2), right=rowPixel(current,x+2);
            Vec3 up=center,down=center;
            if (y>=2 && have2) up=rowPixel(prior2,x);
            if (y+2<height) down=loadPixel(out,width,x,y+2);
            Vec3 avg=mul(add(add(left,right),add(up,down)),0.25f);
            const float yc=luminance(center), ya=luminance(avg);
            Vec3 cc{center.r-yc,center.g-yc,center.b-yc};
            Vec3 ca{avg.r-ya,avg.g-ya,avg.b-ya};
            Vec3 result{yc + cc.r*(1.0f-strength)+ca.r*strength,
                        yc + cc.g*(1.0f-strength)+ca.g*strength,
                        yc + cc.b*(1.0f-strength)+ca.b*strength};
            storePixel(out,width,x,y,max0(result));
        }
        prior2.swap(prior1);
        prior1.swap(current);
        if (have1) have2=true;
        have1=true;
    }
}

} // namespace

struct SpektraRawCpuOwner::Impl {
    mutable std::mutex workMutex;
    std::atomic<bool> savedWaiting{false};
    std::atomic<uint64_t> previewProcessed{0};
    std::atomic<uint64_t> previewDropped{0};
    std::atomic<uint64_t> previewMicrosTotal{0};
    std::atomic<uint64_t> lastStillMicros{0};

    bool run(const RawDevelopRequest& q,std::vector<uint8_t>* out,std::string* error) {
        if (!validate(q,error)) return false;
        const uint64_t bytes=static_cast<uint64_t>(q.outputWidth)*q.outputHeight*8ull;
        out->assign(static_cast<size_t>(bytes),0u);
        CpuDevelop d{q};
        SPEKTRA_RAW_LOGI("IRIS_26688_RAW_CPU_STAGE stage=%s_begin src=%dx%d out=%dx%d format=%d",
                q.savedPhoto?"saved":"preview",q.sourceWidth,q.sourceHeight,q.outputWidth,q.outputHeight,q.format);
        auto renderRows=[&](int y0,int y1){
            for(int y=y0;y<y1;++y) for(int x=0;x<q.outputWidth;++x) storePixel(*out,q.outputWidth,x,y,d.reconstructForOutput(x,y));
        };
        if (q.savedPhoto && q.outputHeight>=256) {
            const unsigned hc=std::thread::hardware_concurrency();
            const int workers=std::max(1,std::min(4,static_cast<int>(hc==0?4:hc)));
            std::atomic<int> next{0};
            std::vector<std::thread> threads; threads.reserve(static_cast<size_t>(workers));
            for(int i=0;i<workers;++i) threads.emplace_back([&]{for(;;){int y=next.fetch_add(1);if(y>=q.outputHeight)break;renderRows(y,y+1);}});
            for(auto& t:threads)t.join();
            applySavedChromaDenoise(*out,q.outputWidth,q.outputHeight,q.chromaDenoiseStrength);
        } else renderRows(0,q.outputHeight);
        SPEKTRA_RAW_LOGI("IRIS_26688_RAW_CPU_STAGE stage=%s_complete bytes=%zu",
                q.savedPhoto?"saved":"preview",out->size());
        return true;
    }
};

SpektraRawCpuOwner& SpektraRawCpuOwner::instance(){static SpektraRawCpuOwner o;return o;}
SpektraRawCpuOwner::SpektraRawCpuOwner():impl_(new Impl()){}
SpektraRawCpuOwner::~SpektraRawCpuOwner(){delete impl_;}

bool SpektraRawCpuOwner::process(const RawDevelopRequest& q,std::vector<uint8_t>* out,
        bool* previewDropped,double* elapsedMicros,std::string* error){
    if(previewDropped)*previewDropped=false;
    const auto start=std::chrono::steady_clock::now();
    std::unique_lock<std::mutex> lock(impl_->workMutex,std::defer_lock);
    if(q.savedPhoto){impl_->savedWaiting.store(true,std::memory_order_release);lock.lock();impl_->savedWaiting.store(false,std::memory_order_release);}
    else if(impl_->savedWaiting.load(std::memory_order_acquire)||!lock.try_lock()){
        impl_->previewDropped.fetch_add(1,std::memory_order_relaxed);if(previewDropped)*previewDropped=true;return true;
    }
    const bool ok=impl_->run(q,out,error);
    const auto stop=std::chrono::steady_clock::now();
    const uint64_t micros=static_cast<uint64_t>(std::chrono::duration_cast<std::chrono::microseconds>(stop-start).count());
    if(elapsedMicros)*elapsedMicros=static_cast<double>(micros);
    if(q.savedPhoto)impl_->lastStillMicros.store(micros,std::memory_order_relaxed);
    else if(ok){impl_->previewProcessed.fetch_add(1,std::memory_order_relaxed);impl_->previewMicrosTotal.fetch_add(micros,std::memory_order_relaxed);}
    return ok;
}

void SpektraRawCpuOwner::release(){
    // No device/queue/fence lifetime exists. The owner is process-stable and owns only atomics/mutex.
}

void SpektraRawCpuOwner::stats(uint64_t out[6]) const{
    const uint64_t p=impl_->previewProcessed.load(std::memory_order_relaxed);
    const uint64_t total=impl_->previewMicrosTotal.load(std::memory_order_relaxed);
    out[0]=p;out[1]=impl_->previewDropped.load(std::memory_order_relaxed);out[2]=p?total/p:0;
    out[3]=impl_->lastStillMicros.load(std::memory_order_relaxed);out[4]=1u;out[5]=0u;
}

} // namespace iris_spektra
