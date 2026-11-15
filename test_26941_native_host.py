#!/usr/bin/env python3
"""Host C++17 descriptor lifetime simulation and source isolation invariants."""
import sys,re,subprocess,tempfile
from pathlib import Path
from build_26941_incremental import R,fail,scope
CPP='app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp'
COORD='app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp'
HOST=r'''
#include <array>
#include <cassert>
#include <stdexcept>
#include <cstddef>
struct MockPool {
  unsigned resets=0,allocations=0;
  void reset(){++resets;allocations=0;}
  void alloc(){assert(allocations<256);++allocations;}
};
struct MockExecutor {
  std::array<MockPool,55> pools{};
  std::array<bool,55> pending{};
  bool lazy=false;
  void begin(){
    if(lazy){pending.fill(true);return;}
    pending.fill(false);
    for(auto &p:pools)p.reset();
  }
  void record(size_t i){
    if(lazy&&pending[i]){pools[i].reset();pending[i]=false;}
    pools[i].alloc();
  }
};
int main(){
  MockExecutor original;
  for(unsigned chunk=0;chunk<136;++chunk){original.begin();original.record(25);}
  unsigned eager=0;for(auto &p:original.pools)eager+=p.resets;
  assert(eager==136*55);
  MockExecutor optimized;optimized.lazy=true;
  for(unsigned chunk=0;chunk<136;++chunk){
    optimized.begin();
    optimized.record(25);optimized.record(25);optimized.record(41);
  }
  unsigned used=0;for(auto &p:optimized.pools)used+=p.resets;
  assert(used==136*2 && used<eager);
  // An unused pool is reset before the first use, not left with stale sets.
  optimized.begin();optimized.record(41);optimized.record(25);
  assert(optimized.pools[41].resets==137 && optimized.pools[25].resets==137);
  optimized.lazy=false;optimized.begin();
  unsigned all=0;for(auto &p:optimized.pools)all+=p.resets;
  assert(all==used+2+55);
  // Failed record after reset cannot silently make stale descriptors usable.
  optimized.lazy=true;optimized.begin();optimized.record(41);
  optimized.begin();optimized.record(41);
  assert(optimized.pools[41].resets==140);
}
'''
def main():
 scope();live='--live' in sys.argv;root=R if live else R/'handoff_payload_26941'
 s=(root/CPP).read_text();c=(root/COORD).read_text()
 for word in ('if (iris26941BOffHdrqLazyPoolReset && iris26941PoolNeedsReset[i])',
              'iris26941PoolNeedsReset[i] = false;',
              'iris26941PoolNeedsReset.fill(true);',
              'iris26941PoolNeedsReset.fill(false);',
              'vkResetDescriptorPool(device_, p.pool, 0)',
              'thread_local bool iris26941BOffHdrqLazyPoolReset = false;',
              'if (iris26940BOffHdrqPipelineInit &&'):
  if word not in s:fail('B-only shadow Vulkan pool correctness invariant missing '+word)
 for word in ('ScopedBOffLazyPoolReset',
              'rawr::raw_gpu_pipeline::iris26941BOffHdrqLazyPoolReset = active;',
              'rawr::raw_gpu_pipeline::iris26941BOffHdrqLazyPoolReset = previous;',
              'bOffReusable != nullptr && !sr'):
  if word not in c:fail('B-only coordinator per-run fence/isolation invariant missing '+word)
 if not(s.index('if (iris26941BOffHdrqLazyPoolReset && iris26941PoolNeedsReset[i])')<
        s.index('ck(vkAllocateDescriptorSets(device_, &ai, &set)')):
  fail('descriptor pool reset must happen BEFORE allocation')
 if not(s.index('if (iris26941BOffHdrqLazyPoolReset) {',s.index('void VulkanExecutor::beginBatch()'))<
        s.index('for (auto& p : programs_)',s.index('void VulkanExecutor::beginBatch()'))):
  fail('lazy path not branched ahead of original default eager reset')
 # Actual previous successful vendor math must be byte-identical (source allowlist).
 cxx=subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-O2','-x','c++','-','-o','/tmp/iris26941_host_descriptor_test'],input=HOST,text=True,capture_output=True)
 if cxx.returncode:fail('real C++17 host test compile failed '+cxx.stderr[-1000:])
 test=subprocess.run(['/tmp/iris26941_host_descriptor_test'],capture_output=True,text=True)
 if test.returncode:fail('host descriptor test failed '+test.stderr[-1000:])
 print('PASS actual C++17 host descriptor simulation 136×55 -> 136×2 example, reset-before-first-allocation, old modes eager, run RAII scoped')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
