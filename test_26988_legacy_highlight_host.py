#!/usr/bin/env python3
"""C-private LK-R 2.3.94 highlight rule: exact CPU execution and live GPU dispatch/source audit."""
from pathlib import Path
import argparse,hashlib,json,subprocess,tempfile,os
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');o=p.parse_args();assert o.payload!=o.live
N=Path('app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp');D=(R if o.live else R/'handoff_payload_26988')/N
read=lambda n:(D/n).read_text()
# Exact donor block, recovered from RawLens 2.3.94 lkrl_finish.cpp blob 0d25122a164dbde286c8dac17be79f7c605f5c6f.
old='''  // Neutralise only pixels with no remaining unsaturated colour channel.
  // One-channel clipping is common in sunsets: the other channels still
  // contain valid colour. Do not expand this mask into coloured neighbours.
  if (prm.highlight_desat) {
    const float lo = 0.92f * prm.clip, hi = prm.clip;
    for (size_t i = 0; i < HW; ++i) {
      const float mn = std::min(x[i], std::min(x[HW + i], x[2 * HW + i]));
      const float m = std::clamp((mn - lo) / std::max(hi - lo, 1e-6f), 0.0f, 1.0f);
      if (m <= 0.0f) continue;
      const float L = q[0] * x[i] + q[1] * x[HW + i] + q[2] * x[2 * HW + i];   // wb-space luma
      for (int c = 0; c < 3; ++c) {
        const float neutral = L / prm.wb[c];
        x[c * HW + i] += m * (neutral - x[c * HW + i]);
      }
    }
  }'''
finish=read('lkrl_finish.cpp');assert finish.count(old)==1 and 'hl_ratio' not in finish and 'LKRL_HL_REC' not in finish and 'LKRL_HL_OLD' not in finish
adapter=read('lkrl_adapter.cpp');assert 'false, 0 /* C: 2.3.94 highlight rule; no rim reconstruction */' in adapter and 'if (!fin_done) FinishLook(' in adapter
solver=read('lkrl_solver.cpp');assert 'fa.desat ? 2 : 0 /* donor legacy all-channels rule */' in solver and '0.0f /* no opposed inpaint */' in solver and 'run(7)' not in solver[solver.index('bool LiteSolver::finish('):] and 'static_assert(sizeof(FinPush) == 80' in solver
full=read('lkrl_full.cpp');assert 'S.hdr_white = hdr ? hdr_clip : 1.0f;' in full and 'if (hdr) { sp.clip = hdr_clip; sp.exposure = erel; }' in full and 'const float hdr_clip = prm.solve.clip / emin' in full and 'hl_ratio' not in full and 'hl_cells' not in full and full.count('S.hdr_white =')==1
jni=read('lkrl_jni.cpp');assert 'highlight: 2.3.94 all-channels rule; opposed inpaint off; bracket HDR preserved' in jni and 'IRIS26985C_LKRL_HL_OLD' not in jni and 'IRIS26985C_LKRL_HL_REC' not in jni
print('PASS exact donor CPU block, fixed private GPU legacy mode, no rim extension, genuine bracket headroom unchanged')
if o.live:
 shader=read('shaders/fin.comp');assert 'bool rec = pc.desat == 1 && pc.hrec != 0.0;' in shader and 'bool old = pc.desat == 2;' in shader and 'float lo = (old ? 0.92 : 0.85) * pc.clip' in shader and 'float v = (old || rec) ? min(xd.x, min(xd.y, xd.z))' in shader and 'if (!old) m = m * m * (3.0 - 2.0 * m);' in shader and 'if (!old && !rec) L = min' in shader and 'm * (L / wb[c] - x[c * HW + i])' in shader
 # Verify unchanged shader from successful source; exact GPU compilation still mandatory on Actions.
 manifest={p:h for h,p in (x.split('  ',1) for x in (R/'26988_BASE_26987_FULL_APP.sha256').read_text().splitlines())};assert hashlib.sha256((D/'shaders/fin.comp').read_bytes()).hexdigest()==manifest[str(N/'shaders/fin.comp')]
 src=r'''
#include "lkrl_api.h"
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <random>
#include <vector>
#include <cstdlib>
// Isolate the actual native finishing function from optional prior/notch steps.
int main(){
 std::mt19937 rng(26988);std::uniform_real_distribution<float> u(0,1);int count=0;
 for(float clip:{1.0f,2.0f,4.0f})for(bool enable:{false,true})for(int scale:{1,2}){
  constexpr int W=16,H=16,HW=W*H;lkrl::SolveParams p;p.s=scale;p.clip=clip;p.notch=false;p.grain=0;p.fallback_chroma=0;p.shadow_chroma=0;p.highlight_desat=enable;p.wb={2.f,1.f,1.5f};p.hl_ratio[0]=3;p.hl_ratio[1]=1;p.hl_ratio[2]=.3f;
  std::vector<float> a(3*HW),z(3*HW);
  for(int i=0;i<HW;i++)for(int c=0;c<3;c++)a[c*HW+i]=clip*(i%3==0?(.90f+.2f*u(rng)):(i%3==1?(.0f+.8f*u(rng)):(c==0?1.1f:.6f)));
  // Fully clipped and partial highlights beside each other; real color in an unclipped channel must survive.
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
 printf("PASS %d actual FinishLook channel assertions; neutral clipping, partial-channel preservation, no rim tint or neighborhood spread, HDR scaling and WB luma\n",count);
}
'''
 with tempfile.TemporaryDirectory() as td:
  t=Path(td);f=t/'test.cpp';f.write_text(src);exe=t/'host'
  # Only declarations for the unused Vulkan API types in lkrl_api.h. Actual CPU
  # algorithm/params/headers remain untouched; no Vulkan functions are supplied.
  # This host CPU test deliberately does not substitute for the real NDK gate.
  vk=t/'vulkan/vulkan.h';vk.parent.mkdir();names="VkBuffer VkDeviceMemory VkShaderModule VkDescriptorSetLayout VkPipelineLayout VkPipeline VkDescriptorSet VkDevice VkPhysicalDevice VkQueue VkCommandPool VkCommandBuffer VkFence VkDescriptorPool VkPipelineCache VkQueryPool".split()
  vk.write_text("#pragma once\n#define VK_NULL_HANDLE nullptr\n"+"".join("using "+n+" = void*;\n" for n in names)+"struct VkPhysicalDeviceMemoryProperties {};\n")
  def compile_cpu(root,out):
   subprocess.run(['g++','-std=c++17','-O2','-ffp-contract=off','-ffunction-sections','-fdata-sections','-pthread','-I'+str(t),'-I'+str(root),str(f),str(root/'lkrl_finish.cpp'),str(root/'lkrl_image.cpp'),str(root/'lkrl_mhc.cpp'),'-Wl,--gc-sections','-o',str(out)],check=True)
  compile_cpu(D,exe);subprocess.run([str(exe)],check=True)
  # Negative control: the actual successful 26987 opposed-inpaint implementation,
  # not a reconstructed historical runtime tree or a hand-written approximation.
  prior=R/'.photon_26988_work/authority_26987'/N
  assert hashlib.sha256((prior/'lkrl_finish.cpp').read_bytes()).hexdigest()==manifest[str(N/'lkrl_finish.cpp')]
  original=t/'original';compile_cpu(prior,original)
  import resource
  def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
  neg=subprocess.run([str(original)],capture_output=True,text=True,preexec_fn=no_core)
  assert neg.returncode!=0 and 'Assertion' in neg.stderr,neg.stdout+neg.stderr
  print('PASS actual 26987 opposed-inpaint native CPU negative control rejected the legacy color contract')
 print('PASS unchanged Vulkan shader legacy mode and push layout source audit (device GPU execution not tested)')
