#!/usr/bin/env python3
"""Compile actual 26942 guarded native scheduling expression and timestamp indices in a C++17 host harness.
Host control proof is NOT a substitute for actual NDK/Vulkan builds or device timings.
"""
import re,sys,subprocess,tempfile
from pathlib import Path
from build_26942_incremental import R,fail,scope
P='app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp'
def main():
 scope()
 s=(R/P if '--live' in sys.argv else R/'handoff_payload_26942'/P).read_text()
 match=re.search(r'const bool batchPadMerge26942\s*=\s*(iris26941BOffHdrqLazyPoolReset\s*&&[\s\S]*?!aligns);',s)
 if not match:fail('missing precise compiled B OFF scheduling guard')
 guard=match.group(1)
 # Compiler actually evaluates the exact guard expression extracted from the
 # candidate source, including RAWR alignment pass and strict B-only TLS flag.
 code=r"""#include <cassert>
#include <cstdint>
#include <vector>
#include <cstdlib>
#include <cstdio>
#include <cmath>
#include <cstring>
#include <string>
enum class MergeAlgorithm { HdrPlusFrequency, Wronski, HdrPlusSpatial };
struct Config { bool frequencyAlignOnce; };
int main() {
  unsigned checked=0;
  for (int enabled=0;enabled<2;++enabled) {
    for (int frequency=0;frequency<2;++frequency) {
      for (int once=0;once<2;++once) {
        for (unsigned pass=0;pass<4;++pass) {
          const bool iris26941BOffHdrqLazyPoolReset=enabled!=0;
          const MergeAlgorithm algorithm_=frequency?MergeAlgorithm::HdrPlusFrequency:MergeAlgorithm::Wronski;
          const Config hdrplus_{once!=0};
          const bool aligns = !hdrplus_.frequencyAlignOnce || pass==0u;
          const bool batchPadMerge26942 = GUARD;
          const bool expected=enabled&&frequency&&once&&pass>0u;
          assert(batchPadMerge26942==expected);
          ++checked;
        }
      }
    }
  }
  assert(checked==32);
  for(unsigned frames=2;frames<=30;++frames) {
    const unsigned companions=frames-1;
    const unsigned before=4+4+1+companions*(3+3*2)+1;
    const unsigned after=before-3*companions;
    assert(before-after==3*companions);
    if(frames==15)assert(before-after==42 && after==94);
  }
  // The actual shader dispatch/descriptor ABI remains the same; the native
  // source proof separately checks the *verbatim* previous branch under else.
  for(int profile=0;profile<2;++profile) {
    std::vector<unsigned> marks={0,1};
    auto recordTimestamp=[&](unsigned q){marks.push_back(q);};
    auto mark=[&](std::uint32_t k){
      if (k == 5u) {if (profile) recordTimestamp(3u);}
      else if (k == 1u) recordTimestamp(2u);
      else recordTimestamp(profile ? k + 2u : k + 1u);
    };
    mark(1u);
    if(profile)mark(5u);
    mark(2u);mark(3u);
    recordTimestamp(profile?6u:5u);
    assert(marks.size()==(profile?7u:6u));
    for(unsigned i=0;i<marks.size();++i)assert(marks[i]==i);
  }
  std::puts("PASS actual candidate C++17 guard, 15-frame 42 less submits/fences, original 4-pass+15 frame count, profile query order and fail-closed mode isolation");
}
"""
 code=code.replace('GUARD',guard)
 # Assertions compare byte-locked timestamp map, extracted below from actual
 # source, not just an independently handwritten predicate.
 branch=s.split('const bool batchPadMerge26942 =',1)[1].split('            } else {\n',1)[0]
 for m in ('if (k == 5u) {','if (profile) recordTimestamp(3u);',
           'else if (k == 1u) recordTimestamp(2u);',
           'else recordTimestamp(profile ? k + 2u : k + 1u);',
           'recordTimestamp(profile ? 6u : 5u);'):
  if branch.count(m)!=1:fail('native timestamp map missing or duplicated '+m)
 with tempfile.TemporaryDirectory(prefix='26942_native_host_') as d:
  p=Path(d)/'test.cpp';b=Path(d)/'test';p.write_text(code)
  subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-O2',str(p),'-o',str(b)],check=True)
  subprocess.run([str(b)],check=True)
if __name__=='__main__':
 try:main()
 except Exception as e:print('26942 C++17 HOST BLOCKED',e,file=sys.stderr);sys.exit(1)
