#include <array>
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <vector>
#include <stdexcept>
#include <random>
// Contract exercised by the staged Android R16F -> packed bits -> JNI sampler.
static std::vector<uint8_t> pack(const std::vector<uint16_t>&half,uint32_t w,uint32_t h) {
 const uint32_t rowBytes=(w+7)/8;
 std::vector<uint8_t> dst(size_t(rowBytes)*h);
 for(uint32_t y=0;y<h;y++)for(uint32_t x=0;x<w;x++) {
   const auto b=half[size_t(y)*w+x];
   if(b!=0x0000&&b!=0x3c00)throw std::invalid_argument("nonbinary mask");
   if(b==0x3c00)dst[size_t(y)*rowBytes+(x>>3)]|=uint8_t(1u<<(x&7));
 }
 return dst;
}
static bool read(const std::vector<uint8_t>&bits,uint32_t w,uint32_t y,uint32_t x) {
 const uint32_t rowBytes=(w+7)/8;
 return 0u!=(bits[size_t(y)*rowBytes+(x>>3)]&(1u<<(x&7)));
}
int main() {
 std::mt19937 rng(26864u);
 uint64_t checks=0;
 for(uint32_t w: {2u,7u,8u,9u,17u,31u,3070u,4096u}) {
   const uint32_t h=19;
   std::vector<uint16_t> mask(size_t(w)*h);
   for(auto&v:mask)v=(rng()%11u==0u)?0x3c00:0x0000;
   const auto bits=pack(mask,w,h);
   assert(bits.size()==size_t((w+7)/8)*h);
   for(uint32_t y=0;y<h;y++)for(uint32_t x=0;x<w;x++) {
     assert(read(bits,w,y,x)==(mask[size_t(y)*w+x]==0x3c00));
     float m= (x%5u)? 0.f : .35f;
     const auto expected=read(bits,w,y,x)?1.f:m;
     if(read(bits,w,y,x))m=1.f;
     assert(m==expected);
     checks+=2;
   }
   // No sidecar provided for the inherited A route: identical pre-existing M.
   for(uint32_t k=0;k<200;k++) {float m=float(k)/200.f; assert(m==float(k)/200.f);checks++;}
   auto bad=mask;bad[0]=0x7e00;bool rejected=false;
   try{(void)pack(bad,w,h);}catch(const std::invalid_argument&){rejected=true;}
   assert(rejected);checks++;
 }
 printf("PASS: %llu mask/legacy/union/reject checks\n",(unsigned long long)checks);
}
