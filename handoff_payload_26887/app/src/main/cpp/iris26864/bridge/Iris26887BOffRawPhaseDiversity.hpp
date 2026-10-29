#pragma once
// IRIS_26887_B_OFF_INDEPENDENT_RAW_PHASE_COVERAGE
// A deliberately strict CAPTURE-LEVEL precondition for B's post-AMaZE guide.
// Two CFA arrays at the SAME Bayer phase are not independent material-color
// evidence. Require actual sub-CFA-cell sensor displacement measured from the
// separate ORIGINAL raw normals, never inferred from merged/post-AMaZE RGB.
// This does not alter RAW buffers, shutter, reference selection or frame count.
// In flat, repeated, occluded, low-correlation or ambiguous scenes it returns
// false; the B temporal chroma stage then passes all pixels through unchanged.
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <vector>

namespace iris26887 {
struct Raw16Frame {
    const std::uint8_t* bytes=nullptr;
    std::size_t byteCount=0;
    std::uint32_t stride=0,width=0,height=0;
    float black[4]{},white=0,exposure=0;
};
struct PhaseCoverage {
    bool verified=false;
    std::uint32_t reliableCompanions=0;
    float minReliableCfaShift=0.f;
};
namespace detail {
inline float green(const Raw16Frame& f,std::uint32_t pattern,int x,int y){
    if(!f.bytes||x<0||y<0||x*2+1>=int(f.width)||y*2+1>=int(f.height))return -1.f;
    const bool diagonal=pattern==1u||pattern==2u;
    const int off[4]={diagonal?0:1,diagonal?0:0,diagonal?1:0,diagonal?1:1};
    float value=0.f;
    for(int k=0;k<2;++k){
        const int xx=x*2+off[2*k], yy=y*2+off[2*k+1];
        const std::size_t index=std::size_t(yy)*f.stride+std::size_t(xx)*2u;
        if(index+1u>=f.byteCount)return -1.f;
        const float raw=float(std::uint16_t(f.bytes[index])|(std::uint16_t(f.bytes[index+1])<<8u));
        const int phase=(off[2*k+1]<<1)+off[2*k];
        const float range=f.white-f.black[phase];
        if(!(range>1.f))return -1.f;
        value+=std::clamp((raw-f.black[phase])/range,0.f,1.f);
    }
    return value*.5f;
}
struct Cost {
    float value=std::numeric_limits<float>::infinity();
    std::uint32_t n=0;
};
inline Cost cost(const Raw16Frame& a,const Raw16Frame& b,std::uint32_t pattern,
                 int dx,int dy,int width,int height,int quadrant){
    double e=0.;std::uint32_t n=0;
    const int nx=width/2,ny=height/2;
    const int startx=std::max(4,nx/5),endx=std::min(nx-5,4*nx/5);
    const int starty=std::max(4,ny/5),endy=std::min(ny-5,4*ny/5);
    if(endx<=startx||endy<=starty)return {};
    const int stepX=std::max(1,(endx-startx)/22),stepY=std::max(1,(endy-starty)/22);
    const float gain=a.exposure/b.exposure;
    for(int y=starty;y<endy;y+=stepY){
        for(int x=startx;x<endx;x+=stepX){
            const int q=(x>=(startx+endx)/2?1:0)+(y>=(starty+endy)/2?2:0);
            if(quadrant!=4&&q!=quadrant)continue;
            float va=green(a,pattern,x,y),vb=green(b,pattern,x+dx,y+dy);
            if(va<.002f||va>.90f||vb<.002f||vb>.90f)continue;
            float delta=va-vb*gain;
            e+=std::min(double(delta)*delta,0.04*0.04);
            ++n;
        }
    }
    if(n<40u/(quadrant==4?1u:4u))return {};
    return {float(e/double(n)),n};
}
struct Estimate {bool good=false;float dx=0.f,dy=0.f;};
inline Estimate estimate(const Raw16Frame& a,const Raw16Frame& b,std::uint32_t pattern,
                         int width,int height,int quadrant){
    float best=std::numeric_limits<float>::infinity();int bx=0,by=0;
    for(int yy=-3;yy<=3;++yy)for(int xx=-3;xx<=3;++xx){
        const auto c=cost(a,b,pattern,xx,yy,width,height,quadrant);
        if(c.value<best){best=c.value;bx=xx;by=yy;}
    }
    if(bx<=-3||bx>=3||by<=-3||by>=3||!std::isfinite(best))return {};
    const auto cxm=cost(a,b,pattern,bx-1,by,width,height,quadrant).value;
    const auto cxp=cost(a,b,pattern,bx+1,by,width,height,quadrant).value;
    const auto cym=cost(a,b,pattern,bx,by-1,width,height,quadrant).value;
    const auto cyp=cost(a,b,pattern,bx,by+1,width,height,quadrant).value;
    const float xcur=cxm+cxp-2.f*best,ycur=cym+cyp-2.f*best;
    // A nearly flat or repeating patch does NOT provide measured phase.
    if(!(xcur>0.000002f||ycur>0.000002f))return {};
    if(best>.0012f)return {}; // avoid unstable apparent shifts on moving patterns
    float fx=xcur>0.000002f?std::clamp(0.5f*(cxm-cxp)/xcur,-0.5f,0.5f):0.f;
    float fy=ycur>0.000002f?std::clamp(0.5f*(cym-cyp)/ycur,-0.5f,0.5f):0.f;
    return {true,float(bx)+fx,float(by)+fy};
}
} // detail
inline PhaseCoverage measurePhaseCoverage(const std::vector<Raw16Frame>& frames,
                                         std::size_t reference,std::uint32_t localCfa){
    PhaseCoverage proof{};
    if(frames.size()<3u||frames.size()>64u||reference>=frames.size()||localCfa>3u)return proof;
    const Raw16Frame& ref=frames[reference];
    if(ref.width<128u||ref.height<128u||(ref.width&1u)||(ref.height&1u)||
       !(std::isfinite(ref.white)&&ref.white>1.f)||
       !(std::isfinite(ref.exposure)&&ref.exposure>0.f))return proof;
    for(std::size_t k=0;k<frames.size();++k){
        if(k==reference)continue;
        const auto& f=frames[k];
        if(!f.bytes||f.width!=ref.width||f.height!=ref.height||
           f.stride<f.width*2u||!(std::isfinite(f.exposure)&&f.exposure>0.f)||
           std::abs(std::log(f.exposure/ref.exposure))>0.025f)continue;
        auto full=detail::estimate(ref,f,localCfa,int(ref.width),int(ref.height),4);
        if(!full.good)continue;
        std::uint32_t agreeing=0;
        for(int quad=0;quad<4;++quad){
            auto local=detail::estimate(ref,f,localCfa,int(ref.width),int(ref.height),quad);
            if(local.good&&std::hypot(local.dx-full.dx,local.dy-full.dy)<0.28f)++agreeing;
        }
        if(agreeing<3u)continue;
        // Fractional cell displacement is *independent Bayer sampling*.
        // Integer whole CFA-cell displacements keep the same CFA phase.
        const float fx=full.dx-std::round(full.dx),fy=full.dy-std::round(full.dy);
        const float fractional=std::hypot(fx,fy);
        if(fractional<0.15f)continue;
        ++proof.reliableCompanions;
        if(proof.minReliableCfaShift==0.f||fractional<proof.minReliableCfaShift)
            proof.minReliableCfaShift=fractional;
    }
    proof.verified=proof.reliableCompanions>=2u;
    return proof;
}
} // namespace iris26887
