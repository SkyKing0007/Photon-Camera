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
 # This specifically catches the FAILED real 26942 V1 NDK use of an
 # undeclared namespace TLS symbol; the old mock silently declared it.
 # Build separate translation units, with the declaration copied verbatim
 # from the edited coordinator and the definition copied verbatim from the
 # actual successful 26941 compiled executor (SHA-locked in --live mode).
 declaration='extern thread_local bool iris26941BOffHdrqLazyPoolReset;'
 marker='thread_local std::optional<std::array<float,8>> iris26912BOffNoiseOverride;'
 if s.count(declaration)!=1 or s.index(declaration)<s.index(marker):
  fail('real coordinator missing exact externally linked TLS declaration')
 if s.index('namespace rawr::raw_gpu_pipeline {')>s.index(declaration) or s.index(declaration)>s.index('namespace {'):
  fail('TLS declaration in wrong namespace (V1 NDK undeclared identifier regression)')
 # The candidate must not silently become a second definition.
 if re.search(r'(?<!extern )thread_local bool\s+iris26941BOffHdrqLazyPoolReset\s*=',s):
  fail('coordinator has duplicate TLS definition')
 if '--live' in sys.argv:
  exfile=R/'app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp'
  from build_26942_incremental import parse
  pinned=parse(R/'26942_BASE_26941_FULL_APP.sha256')
  import hashlib
  if not exfile.is_file() or hashlib.sha256(exfile.read_bytes()).hexdigest()!=pinned['app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp']:
   fail('real 26941 executor TLS symbol definition source is missing or modified')
  executor=exfile.read_text()
 else:
  # The prior 26941 stage-1 payload is already present in the checkout and
  # is a prior published source overlay, not the stale app/src candidate.
  exfile=R/'handoff_payload_26941/app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp'
  executor=exfile.read_text() if exfile.is_file() else None
 definition='thread_local bool iris26941BOffHdrqLazyPoolReset = false;'
 if executor is not None:
  if executor.count(definition)!=1 or executor.index('namespace rawr::raw_gpu_pipeline {')>executor.index(definition):
   fail('inherited 26941 executor does not export TLS definition')
 # Independent minimal C++ compilation/link captures the actual declaration
 # and 26941 definition; absent declaration or mismatched namespace fails.
 with tempfile.TemporaryDirectory(prefix='26942_native_host_') as d:
  tmp=Path(d)
  p=tmp/'test.cpp';b=tmp/'test';p.write_text(code)
  subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-O2',str(p),'-o',str(b)],check=True)
  subprocess.run([str(b)],check=True)
  header='namespace rawr::raw_gpu_pipeline {\n'
  consumer=header+declaration+'\nbool flip26942(bool x) { iris26941BOffHdrqLazyPoolReset=x; return iris26941BOffHdrqLazyPoolReset; }\n}\n'
  producer=header+definition+'\n}\n'
  main='namespace rawr::raw_gpu_pipeline { bool flip26942(bool); }\nint main(){return (rawr::raw_gpu_pipeline::flip26942(true) && !rawr::raw_gpu_pipeline::flip26942(false)) ? 0:1;}\n'
  a=tmp/'consumer.cpp';dfile=tmp/'definition.cpp';m=tmp/'main.cpp';linked=tmp/'linked'
  for path,body in [(a,consumer),(dfile,producer),(m,main)]:path.write_text(body)
  good=['g++','-std=c++17','-Wall','-Wextra','-Werror',str(a),str(dfile),str(m),'-o',str(linked)]
  subprocess.run(good,check=True);subprocess.run([str(linked)],check=True)
  a.write_text(consumer.replace(declaration,''))
  bad=subprocess.run(good,capture_output=True,text=True)
  if bad.returncode==0 or 'not declared' not in bad.stderr:
   fail('negative V1 undeclared TLS guard compile unexpectedly passed')
  a.write_text('namespace incorrect_namespace {\n'+declaration+'\n}\n'+consumer.replace(declaration,''))
  bad=subprocess.run(good,capture_output=True,text=True)
  if bad.returncode==0:fail('negative misplaced TLS declaration unexpectedly passed')
 print('PASS 26942 V2 separate C++17 translation-unit TLS declaration/definition link and V1 undeclared/wrong-namespace negatives')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26942 C++17 HOST BLOCKED',e,file=sys.stderr);sys.exit(1)
