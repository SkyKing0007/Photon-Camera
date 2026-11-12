// Supplemental deterministic host check of the exact bounded confidence/LK math.
// NOT a replacement for mandatory production glslang/SPIR-V or Android NDK.
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <random>
struct Refinement {bool accepted;double dx,dy;};
static Refinement accept(double dx,double dy,int train,double det,double stable,
                         int held,double errBefore,double errAfter){
    bool finite=std::isfinite(dx)&&std::isfinite(dy);
    bool candidate=finite&&train>=32&&det>1.e-8&&stable>0.2&&
        std::max(std::abs(dx),std::abs(dy))>0.001&&
        std::max(std::abs(dx),std::abs(dy))<=0.125;
    return {candidate&&held>=32&&errBefore>1.e-4&&errAfter<errBefore*0.85,
            candidate?dx:0.0,candidate?dy:0.0};
}
static double confidence(double old,double normalizedError){
    double extra=std::clamp((normalizedError-1.5)/5.,0.,1.);
    double c=std::clamp(old,0.,1.);
    if(c>0.&&extra>0.)c*=1.-0.10*extra;
    return c;
}
int main(){
 assert(accept(.05,-.05,45,.1,.50,48,25,12).accepted);
 assert(!accept(.126,0,45,.1,.50,48,25,12).accepted);
 assert(!accept(.05,0,45,.1,.50,48,25,24).accepted);
 assert(!accept(.05,0,45,.1,.50,10,25,12).accepted);
 assert(!accept(.05,0,10,.1,.50,48,25,12).accepted);
 assert(!accept(.05,0,45,.1,.10,48,25,12).accepted);
 assert(!accept(NAN,0,45,.1,.50,48,25,12).accepted);
 std::mt19937 rng(26920);
 std::uniform_real_distribution<double> d(0.,10.), c(-.2,1.2);
 for(int i=0;i<100000;++i){
  double old=c(rng),norm=d(rng),r=confidence(old,norm),bounded=std::clamp(old,0.,1.);
  assert(r>=0.&&r<=bounded&&r>=0.9*bounded-1e-12);
  if(norm<=1.5)assert(std::abs(r-bounded)<1e-12);
 }
 std::cout<<"PASS 26920 bounded subpixel LK heldout and conservative original-motion-gated confidence, 100000 cases; real Vulkan compilation separately required\n";
}
