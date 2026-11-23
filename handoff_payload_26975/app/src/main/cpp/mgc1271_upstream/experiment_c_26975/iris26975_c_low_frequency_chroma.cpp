// Port of pinned bjzhou/PhotonCamera @0a8a11de, donor V25
// mgc_full_resolution_denoise.cpp low-frequency ProcessRaw branch and
// mgc_denoise_static.cpp BoxDownsampleNoiseModel.  C-only ownership; A/B untouched.
#include "iris26975_c_low_frequency_chroma.h"
#include "iris26975_c_donor_chroma_noise.h"
#include "mgc_denoise_static.h"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <new>
#include <vector>

namespace {
struct HalideType { uint8_t code, bits; uint16_t lanes; };
struct HalideDimension { int32_t min, extent, stride; uint32_t flags; };
struct HalideBuffer {
    uint64_t device;
    const void* device_interface;
    uint8_t* host;
    uint64_t flags;
    HalideType type;
    int32_t dimensions;
    const HalideDimension* dim;
    void* padding;
};
static_assert(sizeof(HalideBuffer) == 56);
static_assert(sizeof(HalideDimension) == 16);
static_assert(offsetof(HalideBuffer, type) == 32);
static_assert(offsetof(HalideBuffer, dim) == 40);
HalideBuffer Buffer(void* ptr, HalideType type, int dimensions,
    const HalideDimension* layout) {
    return HalideBuffer{0,nullptr,static_cast<uint8_t*>(ptr),0,type,dimensions,layout,nullptr};
}
extern "C" int photon_mgc_chroma_denoise_pyramid_complete_s16(
    void*, HalideBuffer*, HalideBuffer*, int, int, HalideBuffer*, HalideBuffer*,
    HalideBuffer*, HalideBuffer*, HalideBuffer*);

// C-specific dispatch: donor low-frequency decimation is 2-L, downsample L.
// The 26974 A/B wrapper is hardwired to (2,0), so cannot be reused here.
int RunChromaAtLevel(const int16_t* input, int width, int height,
    const uint16_t* strength, int sw, int sh,
    const photon::mgc_denoise::ChromaDenoiseNoiseBuffers& noise,
    int log2_downsample, int16_t* output) {
    if (!input || !strength || !output || log2_downsample < 1 ||
        log2_downsample > 2 || width <= 0 || height <= 0 ||
        sw != (width << log2_downsample) / 4 ||
        sh != (height << log2_downsample) / 4 ||
        width % 128 || height % 16) return -1;
    const HalideDimension image[] = {{0,width,1,0}, {0,height,width,0},
        {0,3,width*height,0}};
    const HalideDimension map[] = {{0,sw,1,0},{0,sh,sw,0},{0,3,sw*sh,0}};
    const HalideDimension scalar[] = {{0,4,1,0},{0,2,12,0}};
    const HalideDimension read[] = {{0,4,1,0},{0,3,4,0},{0,2,12,0}};
    const HalideDimension outliers[] = {{0,4,1,0},{0,2,4,0}};
    auto bInput = Buffer(const_cast<int16_t*>(input),{0,16,1},3,image);
    auto bStrength = Buffer(const_cast<uint16_t*>(strength),{1,16,1},3,map);
    auto bQuadratic = Buffer(const_cast<float*>(noise.quadratic),{2,32,1},2,scalar);
    auto bShot = Buffer(const_cast<float*>(noise.shot),{2,32,1},2,scalar);
    auto bRead = Buffer(const_cast<float*>(noise.read),{2,32,1},3,read);
    auto bOutliers = Buffer(const_cast<uint8_t*>(noise.outlier_threshold),{1,8,1},2,outliers);
    auto bOutput = Buffer(output,{0,16,1},3,image);
    return photon_mgc_chroma_denoise_pyramid_complete_s16(nullptr,&bInput,&bStrength,
        2-log2_downsample,log2_downsample,&bQuadratic,&bShot,&bRead,
        &bOutliers,&bOutput);
}

// Donor BoxDownsampleS16Halide: rounded arithmetic shift of each 4x4 block.
void BoxDownsamplePlanes(const int16_t* input, int width, int height,
                        int log2_factor, int16_t* output) {
    const int factor = 1 << log2_factor;
    const int ow = width >> log2_factor, oh = height >> log2_factor;
    const int shift = 2 * log2_factor;
    const int64_t rounding = int64_t{1} << (shift-1);
    const size_t in_plane = static_cast<size_t>(width)*height;
    const size_t out_plane = static_cast<size_t>(ow)*oh;
    #pragma omp parallel for collapse(2) schedule(static)
    for (int channel=0;channel<3;++channel) {
        for (int y=0;y<oh;++y) {
            const int16_t* src = input+channel*in_plane;
            int16_t* dst = output+channel*out_plane+static_cast<size_t>(y)*ow;
            for (int x=0;x<ow;++x) {
                int64_t sum=0;
                for (int dy=0;dy<factor;++dy) {
                    const int16_t* row = src+static_cast<size_t>(y*factor+dy)*width+x*factor;
                    for (int dx=0;dx<factor;++dx) sum+=row[dx];
                }
                dst[x]=static_cast<int16_t>((sum+rounding)>>shift);
            }
        }
    }
}

// Donor normalized spectrum half-bin filter/decimation with alias folding.
bool FilterAndDecimateSpectrum(float spectrum[128], const float* filter,
                              int filter_size, float* scale) {
    if (std::all_of(spectrum,spectrum+128,[](float v){return v==0.f;})) {
        std::fill_n(spectrum,128,1.f);*scale=0.f;return true;
    }
    float filtered[128]={};
    float energy=0.f;
    constexpr double pi = 3.1415926535897932384626433832795;
    for (int i=0;i<128;++i) {
        double real=0.,imag=0.;
        const double omega=(static_cast<double>(i)+0.5)*2.*pi/128.-pi;
        for (int tap=0;tap<filter_size;++tap) {
            real+=static_cast<double>(filter[tap])*std::cos(omega*tap);
            imag-=static_cast<double>(filter[tap])*std::sin(omega*tap);
        }
        filtered[i]=spectrum[i]*static_cast<float>(real*real+imag*imag);
        energy+=filtered[i];
    }
    energy*=1.f/128.f;
    if (!(energy>0.f)||!std::isfinite(energy)) return false;
    const float inv=1.f/energy;
    for(int i=0;i<128;++i) spectrum[i]=filtered[i]*inv;
    const float convolution_scale=energy*energy;
    float expanded[256]={};
    for (int i=64;i<128;++i) {
        const float left=.25f*spectrum[i-1]+.75f*spectrum[i];
        const float right=.75f*spectrum[i]+.25f*spectrum[std::min(i+1,127)];
        expanded[2*i]=left;expanded[2*i+1]=right;
        expanded[255-2*i]=left;expanded[254-2*i]=right;
    }
    for(int i=64;i<128;++i) {
        const float value=.5f*expanded[(i+192)&255]+.5f*expanded[i+64];
        spectrum[i]=value;spectrum[127-i]=value;
    }
    float ds_energy=0.f;
    for(int i=0;i<128;++i) ds_energy+=spectrum[i];
    ds_energy*=1.f/128.f;
    if (!(ds_energy>0.f)||!std::isfinite(ds_energy)) return false;
    for(int i=0;i<128;++i) spectrum[i]/=ds_energy;
    *scale=convolution_scale*(ds_energy*ds_energy);
    return true;
}
bool BoxDownsampleNoiseModel(int log2_factor,float read[3],float* shot,
                            float* quadratic,float spectrum[128]) {
    constexpr float box[2]={.5f,.5f};
    for(int step=0;step<log2_factor;++step) {
        float scale=0.f;
        if(!FilterAndDecimateSpectrum(spectrum,box,2,&scale)) return false;
        for(int channel=0;channel<3;++channel) read[channel]*=scale;
        *shot*=scale;*quadratic*=scale;
    }
    return true;
}

inline int16_t Wrap16(int n) {return static_cast<int16_t>(static_cast<uint16_t>(n));}
inline int16_t Abs16(int16_t v){return Wrap16(v<0?-static_cast<int>(v):v);}
inline int16_t AbsDiff16(int16_t a,int16_t m){return Wrap16(Abs16(a)-Abs16(m));}
inline int16_t Median3(int16_t a,int16_t b,int16_t c) {
    return std::max(std::min(a,b),std::min(std::max(a,b),c));
}
inline int16_t Median5(int16_t a,int16_t b,int16_t c,int16_t d,int16_t e) {
    int16_t v[5]={a,b,c,d,e};std::sort(v,v+5);return v[2];
}
// GCam low-frequency ChromaMedianFilter, dual-five-point or dual-three-point.
void ChromaMedianFilter(int type,const int16_t* input,int width,int height,int16_t* output) {
    const size_t plane=static_cast<size_t>(width)*height;
    std::copy_n(input,plane,output);
    const int16_t* u=input+plane;const int16_t* v=input+2*plane;
    #pragma omp parallel for schedule(static)
    for(int y=0;y<height;++y) {
        const int ym=std::max(y-1,0), yp=std::min(y+1,height-1);
        for(int x=0;x<width;++x) {
            const int xm=std::max(x-1,0), xp=std::min(x+1,width-1);
            const auto at=[&](const int16_t* p,int yy,int xx) {
                return p[static_cast<size_t>(yy)*width+xx];
            };
            int16_t median_a[2],median_b[2],centre[2];
            const int16_t* planes[2]={u,v};
            for(int c=0;c<2;++c) {
                const int16_t* p=planes[c];centre[c]=at(p,y,x);
                if(type==1) {
                    median_a[c]=Median5(centre[c],at(p,ym,x),at(p,yp,x),at(p,y,xm),at(p,y,xp));
                    median_b[c]=Median5(centre[c],at(p,ym,xm),at(p,ym,xp),at(p,yp,xm),at(p,yp,xp));
                } else {
                    median_a[c]=Median3(at(p,y,xm),centre[c],at(p,y,xp));
                    median_b[c]=Median3(at(p,ym,x),centre[c],at(p,yp,x));
                }
            }
            int16_t avg[2];for(int c=0;c<2;++c)avg[c]=static_cast<int16_t>(
                (static_cast<int>(median_a[c])+median_b[c])>>1);
            int16_t excess;
            if(type==1) excess=std::max(AbsDiff16(centre[0],avg[0]),AbsDiff16(centre[1],avg[1]));
            else excess=std::min(
                std::max(AbsDiff16(centre[0],median_a[0]),AbsDiff16(centre[1],median_a[1])),
                std::max(AbsDiff16(centre[0],median_b[0]),AbsDiff16(centre[1],median_b[1])));
            const int weight=std::clamp(std::clamp(static_cast<int>(excess)+1024,-32768,32767),0,2047);
            const size_t index=static_cast<size_t>(y)*width+x;
            for(int c=0;c<2;++c) {
                const int16_t d=Wrap16(avg[c]-centre[c]);
                const int delta=(static_cast<int>(d)*weight+1024)>>11;
                output[(c+1)*plane+index]=Wrap16(centre[c]+delta);
            }
        }
    }
}
void AddUpsampledChromaCorrection(const int16_t* before,const int16_t* after,
    int low_w,int low_h,int level,int16_t* full,int width,int height) {
    const float factor=static_cast<float>(1<<level);
    const size_t full_plane=static_cast<size_t>(width)*height;
    const size_t low_plane=static_cast<size_t>(low_w)*low_h;
    #pragma omp parallel for collapse(2) schedule(static)
    for(int c=1;c<3;++c) {
        for(int y=0;y<height;++y) {
            const float ly=std::clamp((y+.5f)/factor-.5f,0.f,static_cast<float>(low_h-1));
            const int y0=static_cast<int>(ly),y1=std::min(y0+1,low_h-1);
            const float fy=ly-y0;
            int16_t* row=full+c*full_plane+static_cast<size_t>(y)*width;
            for(int x=0;x<width;++x) {
                const float lx=std::clamp((x+.5f)/factor-.5f,0.f,static_cast<float>(low_w-1));
                const int x0=static_cast<int>(lx),x1=std::min(x0+1,low_w-1);
                const float fx=lx-x0;
                const auto delta=[&](int xx,int yy) {
                    const size_t i=c*low_plane+static_cast<size_t>(yy)*low_w+xx;
                    return static_cast<float>(after[i])-static_cast<float>(before[i]);
                };
                const float correction=(1.f-fy)*((1.f-fx)*delta(x0,y0)+fx*delta(x1,y0))+
                    fy*((1.f-fx)*delta(x0,y1)+fx*delta(x1,y1));
                row[x]=static_cast<int16_t>(std::lrint(std::clamp(
                    static_cast<float>(row[x])+correction,-32768.f,32767.f)));
            }
        }
    }
}
} // namespace

namespace photon::experiment_c_26975 {
int ApplyLowFrequencyChroma(int16_t* full,int width,int height,
    const uint16_t* strength,int sw,int sh,const float read[3],
    float shot,float quadratic,const float spectrum[128],
    const float tuning[5],const float outlier[5],int level,int median_type) {
    // Donor native 1x MgcFinishResolution resolves to L=2. Never silently omit this stage.
    if(!full||!strength||!read||!spectrum||!tuning||!outlier||
        level!=2||median_type!=2||width<=0||height<=0||width%512||height%64||
        sw!=width/4||sh!=height/4||
        static_cast<int64_t>(width)*height>std::numeric_limits<int>::max()/3||
        !std::all_of(read,read+3,[](float v){return std::isfinite(v)&&v>=0.f;})||
        !std::isfinite(shot)||shot<0.f||!std::isfinite(quadratic)||quadratic<0.f||
        !std::all_of(spectrum,spectrum+128,[](float v){return std::isfinite(v)&&v>=0.f;}))
        return -1;
    try {
        const int low_w=width>>level, low_h=height>>level;
        const size_t count=static_cast<size_t>(low_w)*low_h*3;
        std::vector<int16_t> low_before(count),low_after(count),low_median(count);
        BoxDownsamplePlanes(full,width,height,level,low_before.data());
        ChromaMedianFilter(median_type,low_before.data(),low_w,low_h,low_median.data());
        float low_read[3]={read[0],read[1],read[2]};
        float low_shot=shot,low_quadratic=quadratic;
        float low_spectrum[128];std::copy_n(spectrum,128,low_spectrum);
        if(!BoxDownsampleNoiseModel(level,low_read,&low_shot,&low_quadratic,low_spectrum))return -2;
        mgc_denoise::ChromaDenoiseNoiseBuffers noise;
        if(!BuildDonorChromaNoiseBuffers(low_read,low_shot,low_quadratic,
               low_spectrum,tuning,outlier,&noise)) return -3;
        const int rc=RunChromaAtLevel(low_median.data(),low_w,low_h,strength,sw,sh,
                   noise,level,low_after.data());
        if(rc!=0)return rc;
        AddUpsampledChromaCorrection(low_before.data(),low_after.data(),low_w,low_h,
                                     level,full,width,height);
        return 0;
    }catch(const std::bad_alloc&){return -4;}
}
} // namespace photon::experiment_c_26975
