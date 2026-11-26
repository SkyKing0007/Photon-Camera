#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,subprocess,tempfile
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');a=p.parse_args();assert a.payload!=a.live
N=Path('app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp');D=(R if a.live else R/'handoff_payload_26989')/N
prior={p:h for h,p in (x.split('  ',1) for x in (R/'26988_BASE_26987_FULL_APP.sha256').read_text().splitlines())}
for f in ('lkrl_adapter.cpp','lkrl_finish.cpp','lkrl_full.cpp','lkrl_jni.cpp','lkrl_solver.cpp'):
 assert hashlib.sha256((D/f).read_bytes()).hexdigest()==prior[(N/f).as_posix()]
print('PASS exact restored successful 2.4.20 CPU/GPU highlight source bytes')
if a.live:
 src=r'''
#include "lkrl_api.h"
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <vector>
int main(){
 int checks=0;
 for(int scale:{1,2})for(bool enable:{false,true}){
  constexpr int W=16,H=16,HW=W*H;lkrl::SolveParams p;p.s=scale;p.clip=1.f;p.notch=false;p.grain=0;p.fallback_chroma=0;p.shadow_chroma=0;p.highlight_desat=enable;p.wb={2.f,1.f,1.5f};p.hl_ratio[0]=1.1f;p.hl_ratio[1]=1.f;p.hl_ratio[2]=.8f;
  std::vector<float> a(3*HW),z(3*HW);
  for(int i=0;i<HW;i++)for(int c=0;c<3;c++)a[c*HW+i]=.12f+.01f*c;
  a[0]=a[HW]=a[2*HW]=1.f;a[1]=1.f;a[HW+1]=.4f;a[2*HW+1]=.5f;
  auto out=a;lkrl::FinishLook(z.data(),out.data(),H,W,p,nullptr,nullptr);
  for(int i=0;i<3*HW;i++){assert(std::isfinite(out[i]));if(!enable || (i%HW>=2))assert(out[i]==a[i]);++checks;}
  if(enable){assert(out[0]!=a[0]||out[HW]!=a[HW]||out[2*HW]!=a[2*HW]);assert(out[1]!=a[1]||out[HW+1]!=a[HW+1]||out[2*HW+1]!=a[2*HW+1]);}
 }
 printf("PASS %d real latest CPU finish assertions: finite output, subclip identity, active opposed highlights, disabled identity\n",checks);
}
'''
 with tempfile.TemporaryDirectory() as td:
  t=Path(td);f=t/'test.cpp';f.write_text(src);exe=t/'host';vk=t/'vulkan/vulkan.h';vk.parent.mkdir();names="VkBuffer VkDeviceMemory VkShaderModule VkDescriptorSetLayout VkPipelineLayout VkPipeline VkDescriptorSet VkDevice VkPhysicalDevice VkQueue VkCommandPool VkCommandBuffer VkFence VkDescriptorPool VkPipelineCache VkQueryPool".split()
  vk.write_text('#pragma once\n#define VK_NULL_HANDLE nullptr\n'+''.join('using '+n+' = void*;\n' for n in names)+'struct VkPhysicalDeviceMemoryProperties {};\n')
  subprocess.run(['g++','-std=c++17','-O2','-ffp-contract=off','-ffunction-sections','-fdata-sections','-pthread','-I'+str(t),'-I'+str(D),str(f),str(D/'lkrl_finish.cpp'),str(D/'lkrl_image.cpp'),str(D/'lkrl_mhc.cpp'),'-Wl,--gc-sections','-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
