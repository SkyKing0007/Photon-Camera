#!/usr/bin/env python3
"""C++17 actually compile isolated 26940 cache source/lifetime under a minimal Vulkan owner test."""
import pathlib,subprocess,tempfile,sys
from build_26940_incremental import R,fail
SRC='app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc'
PREFIX=r'''
#include <memory>
#include <mutex>
#include <exception>
#include <stdexcept>
#include <cstdint>
#include <cassert>
#include <iostream>
constexpr int VK_SUCCESS=0;
int waitStatus=0,created=0,deleted=0,coordinatorCreated=0,coordinatorDeleted=0;
int vkQueueWaitIdle(int){return waitStatus;}
namespace amaze {
struct VulkanDeviceOwner { VulkanDeviceOwner(){++created;} ~VulkanDeviceOwner(){++deleted;} int queue() const {return 123;} };
}
namespace rawr::raw_gpu_pipeline {
struct AndroidBurstCoordinator {AndroidBurstCoordinator(){++coordinatorCreated;}~AndroidBurstCoordinator(){++coordinatorDeleted;}};
}
'''
END=r'''
int main(){
 auto& c=iris26940BOffCache();
 {std::lock_guard<std::mutex> lock(c.mutex);
 c.select(100,4000,3000,1);
 auto* device=c.device.get(); auto* coord=c.coordinator.get();
 assert(created==1 && coordinatorCreated==1);
 c.select(100,4000,3000,1);
 assert(c.device.get()==device && c.coordinator.get()==coord && created==1);
 c.select(101,4000,3000,1);
 assert(created==2 && deleted==1 && coordinatorCreated==2 && coordinatorDeleted==1);
 c.select(101,4000,3002,1);
 assert(created==3 && deleted==2 && coordinatorCreated==3 && coordinatorDeleted==2);
 c.select(101,4000,3002,2);
 assert(created==4 && deleted==3 && coordinatorCreated==4 && coordinatorDeleted==3);
 try { Iris26940CacheFailureGuard failure(&c); throw std::runtime_error("failure"); }
 catch(const std::runtime_error&) {}
 assert(!c.device && !c.coordinator && deleted==4 && coordinatorDeleted==4);
 c.select(102,4000,3000,0);
 waitStatus=-1;
 c.clear();
 assert(!c.device && !c.coordinator && deleted==4 && coordinatorDeleted==4);
 waitStatus=0;
 }
 std::cout<<"PASS native C++17 B OFF cache host reuse, geometry/lens/CFA invalidation, exception cleanup, device-lost quarantine\n";
}
'''
def main():
 live='--live' in sys.argv
 p=R/SRC if live else R/'handoff_payload_26940'/SRC
 if not p.is_file():fail('B OFF isolated C++ source missing')
 s=p.read_text();begin='struct Iris26940BOffGpuCache final {';end='std::vector<float> iris26864ReadFloats('
 if s.count(begin)!=1 or s.count(end)!=1:fail('unable to extract C++ cache ownership without mutation')
 body=s[s.index(begin):s.index(end)]
 with tempfile.TemporaryDirectory(prefix='26940_cache_cpp_') as td:
  source=pathlib.Path(td)/'test.cpp';output=pathlib.Path(td)/'test'
  source.write_text(PREFIX+body+END)
  for args in (['g++','-std=c++17','-Wall','-Wextra','-Werror','-pthread',str(source),'-o',str(output)],[str(output)]):
   subprocess.run(args,check=True)
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
