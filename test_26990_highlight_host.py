#!/usr/bin/env python3
"""Actual C++ finishing function + extracted exact white-owner block. GPU source audit is separate; real Vulkan compilation is mandatory in Actions."""
from pathlib import Path
import argparse,hashlib,subprocess,tempfile,resource
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=R);p.add_argument('--base',type=Path,default=R/'.photon_26990_work/authority_26989');o=p.parse_args()
N=Path('app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp');D=o.root/N;B=o.base/N
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
manifest={p:h for h,p in (x.split('  ',1) for x in (R/'26990_LEGACY_NATIVE.sha256').read_text().splitlines())}
base={p:h for h,p in (x.split('  ',1) for x in (R/'26990_BASE_26989_FULL_APP.sha256').read_text().splitlines())}
for rel,h in manifest.items():assert sha(o.root/rel)==h and sha(o.base/rel)==base[rel],rel
full=(D/'lkrl_full.cpp').read_text();start=full.index('  // HDR bracket: exposure of each frame relative to the reference (frame 0).');end=full.index('  int ox = -1, oy = -1;',start);white=full[start:end];assert full.count('S.hdr_white =')==1
src=r'''
#include "lkrl_api.h"
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <random>
#include <vector>
#include <cstdlib>
#include <string>
struct Prm { std::vector<float> exposure; struct {float clip=1.f;} solve; };
struct Stats { float hdr_white=0.f; };
bool calc_white(Prm prm,int K,bool holdout,Stats& S,std::string* err){
'''+white+r'''
 return true;
}
int main(){
 std::mt19937 rng(26988);std::uniform_real_distribution<float> u(0,1);int count=0;
 Stats S;std::string err;Prm p;
 for(int k=2;k<=30;k++){p.exposure.clear();assert(calc_white(p,k,false,S,&err)&&S.hdr_white==1.f);p.exposure.assign(k,50.f);assert(calc_white(p,k,false,S,&err)&&S.hdr_white==1.f);count+=2;}
 p.exposure={1.f,.25f};assert(calc_white(p,2,false,S,&err)&&S.hdr_white==4.f);p.exposure={1.f,0.f};assert(!calc_white(p,2,false,S,&err));p.exposure={1.f};assert(!calc_white(p,2,false,S,&err));count+=3;
 for(float clip:{1.0f,2.0f,4.0f})for(bool enable:{false,true})for(int scale:{1,2}){
  constexpr int W=16,H=16,HW=W*H;lkrl::SolveParams p;p.s=scale;p.clip=clip;p.notch=false;p.grain=0;p.fallback_chroma=0;p.shadow_chroma=0;p.highlight_desat=enable;p.wb={2.f,1.f,1.5f};p.hl_ratio[0]=3;p.hl_ratio[1]=1;p.hl_ratio[2]=.3f;
  std::vector<float> a(3*HW),z(3*HW);
  for(int i=0;i<HW;i++)for(int c=0;c<3;c++)a[c*HW+i]=clip*(i%3==0?(.90f+.2f*u(rng)):(i%3==1?(.0f+.8f*u(rng)):(c==0?1.1f:.6f)));
  a[0]=a[HW]=a[2*HW]=clip;a[1]=clip;a[HW+1]=.4f*clip;a[2*HW+1]=.5f*clip;auto out=a;
  setenv("IRIS26985C_LKRL_HL_REC","1",1);unsetenv("IRIS26985C_LKRL_HL_OLD");
  lkrl::FinishLook(z.data(),out.data(),H,W,p,nullptr,nullptr);
  for(int i=0;i<HW;i++){
   const float mn=std::min(a[i],std::min(a[HW+i],a[2*HW+i]));const float m=enable?std::clamp((mn-.92f*clip)/std::max(clip-.92f*clip,1e-6f),0.f,1.f):0.f;
   const float L=.25f*p.wb[0]*a[i]+.5f*p.wb[1]*a[HW+i]+.25f*p.wb[2]*a[2*HW+i];
   for(int c=0;c<3;c++){const float want=a[c*HW+i]+m*(L/p.wb[c]-a[c*HW+i]);assert(std::fabs(out[c*HW+i]-want)<1e-5f);if(m==0)assert(out[c*HW+i]==a[c*HW+i]);++count;}
   float after=.25f*p.wb[0]*out[i]+.5f*p.wb[1]*out[HW+i]+.25f*p.wb[2]*out[2*HW+i];assert(std::fabs(after-L)<1e-5f);
  }
  assert(out[1]==a[1]&&out[HW+1]==a[HW+1]&&out[2*HW+1]==a[2*HW+1]);
  if(enable)assert(std::fabs(out[0]*p.wb[0]-out[HW]*p.wb[1])<1e-5f&&std::fabs(out[HW]*p.wb[1]-out[2*HW]*p.wb[2])<1e-5f);
 }
 printf("PASS %d actual native highlight/white assertions: zero-bracket white=1, exact 2.3.94 CPU behavior, preserved partial-channel color and WB luma\n",count);
}
'''
with tempfile.TemporaryDirectory() as td:
 t=Path(td);f=t/'test.cpp';f.write_text(src);vk=t/'vulkan/vulkan.h';vk.parent.mkdir();names="VkBuffer VkDeviceMemory VkShaderModule VkDescriptorSetLayout VkPipelineLayout VkPipeline VkDescriptorSet VkCommandBuffer VkDevice VkPhysicalDevice VkQueue VkCommandPool VkFence VkDescriptorPool VkPipelineCache VkQueryPool".split()
 vk.write_text('#pragma once\n#define VK_NULL_HANDLE nullptr\n'+''.join('using '+n+' = void*;\n' for n in names)+'struct VkPhysicalDeviceMemoryProperties {};\n')
 def compile_cpu(root,out):subprocess.run(['g++','-std=c++17','-O2','-ffp-contract=off','-ffunction-sections','-fdata-sections','-pthread','-I'+str(t),'-I'+str(root),str(f),str(root/'lkrl_finish.cpp'),str(root/'lkrl_image.cpp'),str(root/'lkrl_mhc.cpp'),'-Wl,--gc-sections','-o',str(out)],check=True)
 compile_cpu(D,t/'positive');subprocess.run([str(t/'positive')],check=True)
 compile_cpu(B,t/'negative');neg=subprocess.run([str(t/'negative')],capture_output=True,text=True,preexec_fn=lambda:resource.setrlimit(resource.RLIMIT_CORE,(0,0)))
 assert neg.returncode!=0 and 'Assertion' in neg.stderr,neg.stdout+neg.stderr
 print('PASS actual 26989 opposed-highlight negative rejected legacy color contract')
