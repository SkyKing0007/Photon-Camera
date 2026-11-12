#!/usr/bin/env python3
"""Compile ACTUAL 26923 burst-moment C++ helper and reject invalid evidence."""
from pathlib import Path
import subprocess,tempfile,textwrap,sys
R=Path(__file__).resolve().parent
root=R if '--live' in sys.argv else R/'handoff_payload_26923'
s=(root/'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp').read_text()
a=s.index('std::optional<BurstNoiseFit> iris26923MeasuredMoments(')
b=s.index('// Uniform HDR+ merges',a)
part=s[a:b]
assert 'RAW-pair' in part or 'RAW-pair' in s
source=r"""#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <optional>
#include <vector>
#include <stdexcept>
#include <iostream>
namespace rawr::raw_merge_wronski_gpu {
struct CfaNoiseProfile {std::array<float,4> slopeBySite{},offsetBySite{};};
bool valid(const CfaNoiseProfile& n){for(int i=0;i<4;i++)if(!(std::isfinite(n.slopeBySite[i]) && n.slopeBySite[i]>0 && std::isfinite(n.offsetBySite[i]) && n.offsetBySite[i]>=0))return false;return true;}
}
struct BurstNoiseFit {rawr::raw_merge_wronski_gpu::CfaNoiseProfile profile{};uint32_t usableBlocks=0,bins=0;};
constexpr uint32_t kNoiseBlockFloats=16;
""" + part + r"""
int main() {
  constexpr int B=320;
  std::vector<float> blocks(B*16,0.f);
  for(int i=0;i<B;i++) for(int site=0;site<4;site++){
    float* p=&blocks[i*16+site*4];
    const float mean=.02f+float(i%40)*.008f;
    p[0]=128.f;p[1]=p[0]*mean;p[2]=0.f;
    const float var=(.000002f+.00009f*mean)*(1.f+float(i%7)*.04f);
    p[3]=2.f*var*127.f;
  }
  auto fit=iris26923MeasuredMoments(blocks.data(),B);
  if(!fit || !rawr::raw_merge_wronski_gpu::valid(fit->profile) || fit->usableBlocks!=B) return 1;
  for(int i=0;i<4;i++)if(!(fit->profile.slopeBySite[i]>0.f && fit->profile.offsetBySite[i]>0.f))return 2;
  for(auto& s:blocks)s=0; // low-information completely flat RAW pair
  for(int i=0;i<B;i++)for(int j=0;j<4;j++){
    float* p=&blocks[i*16+j*4];p[0]=128;p[1]=128*.17f;p[2]=0;p[3]=2e-6f*127.f;
  }
  fit=iris26923MeasuredMoments(blocks.data(),B);
  if(!fit||!rawr::raw_merge_wronski_gpu::valid(fit->profile))return 3;
  blocks.assign(B*16,0);
  if(iris26923MeasuredMoments(blocks.data(),B))return 4; // no measurements must NOT use Camera2
  // One valid block per CFA site: the low-information estimator must never
  // dereference beyond the sole actual sensor moment (historical n=1 guard).
  for(int site=0;site<4;site++){
    float* p=&blocks[site*4];p[0]=2;p[1]=.2f;p[2]=0;p[3]=.000002f;
  }
  fit=iris26923MeasuredMoments(blocks.data(),B);
  if(!fit||!rawr::raw_merge_wronski_gpu::valid(fit->profile))return 5;

  std::cout<<"PASS actual 26923 C++ RAW-only low-information moments and hard missing-evidence rejection\n";
}
"""
with tempfile.TemporaryDirectory(prefix='p26923_nativehost_') as d:
 q=Path(d);(q/'fit.cpp').write_text(source)
 subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(q/'fit.cpp'),'-o',str(q/'fit')],check=True)
 subprocess.run([str(q/'fit')],check=True)
# Full-image loop simulated for no-new-color/luma-bound numeric regression;
# this is NOT device image-quality proof and does not replace actual Vulkan compile.
def refine(c,near,weight):
 y=.25*c[0]+.5*c[1]+.25*c[2]
 balance=min(weight)/max(max(weight),1e-8)
 if not(near is not None and balance>.04 and .006<y<.94 and min(c)>.003):return c
 detail=y-near
 floor=.0009+.001*max(y,0)**.5
 import math
 bounded=max(-.008,min(.008,math.copysign(max(abs(detail)-floor,0),detail)))
 def smooth(x):
  t=max(0,min(1,(x-.04)/(.30-.04)))
  return t*t*(3-2*t)
 support=smooth(balance)
 current=list(c)
 for t in range(3):
  for zs in range(3):
   cy=.25*current[0]+.5*current[1]+.25*current[2]
   resid=y-cy
   delta=support*(.20*resid+.045*bounded)
   current=[v*max(cy+delta,1e-6)/max(cy,1e-6) for v in current]
 return current
for c,near,weights in [([.2,.18,.17],.13,[.7,.7,.6]),([.01,.01,.01],.009,[.7,.7,.7]),([.2,.18,.17],.13,[.01,.7,.7])]:
 x=refine(c,near,weights)
 assert abs(x[0]/x[1]-c[0]/c[1])<1e-9
 assert abs(x[2]/x[1]-c[2]/c[1])<1e-9
 assert max(abs(x[i]-c[i]) for i in range(3))<=.004
print('PASS 26923 nine fused-HR pixel corrections remain bounded and chromaticity invariant')
