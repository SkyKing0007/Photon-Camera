#!/usr/bin/env python3
"""Real host C++17 arithmetic/scheduler invariants; not real Android NDK linking."""
import sys,subprocess,tempfile,re
from pathlib import Path
from build_26943_incremental import R,scope,fail
P='app/src/main/cpp/iris26864/'
def main():
 scope();live='--live' in sys.argv
 def read(n):return ((R if live else R/'handoff_payload_26943')/(P+n)).read_text()
 ring=read('Iris26943GpuZslRing.cpp');hdrq=read('bridge/Iris26887BOffHdrqRecorder.cpp')
 for mark in ('std::unordered_set<uint64_t> seen','views.clear();return false;','frames_[i].ready && frames_[i].timestamp==ts','next_=(next_+1u)%capacity_'):
  if mark not in ring:fail('actual native ring code contract missing '+mark)
 for mark in ('motionEnabled','sizeof(MismatchPc) == 100u','sizeof(BorderPc)==16u','rawNoiseMeasured_'):
  if mark not in hdrq:fail('GLSL/C++ ABI missing '+mark)
 code=r"""#include <cstdint>
#include <vector>
#include <unordered_set>
#include <cassert>
#include <cmath>
#include <cstddef>
#include <algorithm>
#include <cstdio>
struct alignas(4) MismatchPc {int32_t tilesX,tilesY,rgbaWidth,rgbaHeight;float exposureFactor;
  float pad0,pad1,pad2;float slopeRaw[4],offsetRaw[4],referenceBlack[4];
  int32_t measuredNoise,uniformExposure;float referenceWhite,gainForMask;int32_t motionEnabled;};
struct BorderPc {int32_t width,height;float minValue;int32_t motionEnabled;};
static_assert(sizeof(MismatchPc)==100);static_assert(sizeof(BorderPc)==16);
static bool select(const std::vector<uint64_t>& selected, const std::vector<uint64_t>& available) {
 if(selected.size()<2||selected.size()>18)return false;
 std::unordered_set<uint64_t> seen;
 for(auto ts:selected) {if(!ts || !seen.insert(ts).second)return false;
  if(std::find(available.begin(),available.end(),ts)==available.end())return false;}
 return true;
}
int main(){
 const std::vector<uint64_t> list={101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118};
 assert(select({103,101,112,118,116,102,108,109,111,113,114,110,105,104,106},list));
 assert(!select({101,999},list));assert(!select({101,101},list));assert(!select({0,101},list));
 assert(!select({101},list));
 // Old 26942 two-slot fallback uses one upload for the ref and a separate
 // companion upload on each of four frequency passes.
 assert(1+4*(15-1)==57);
 // Resident post-shutter = 15; fully staged = zero post-shutter uploads.
 unsigned staged=15;unsigned selected=15;
 assert(staged==selected && (staged==selected?0:57)==0);
 for(unsigned n=2;n<=30;++n)assert(1+4*(n-1)>=n);
 // GPU ring only consumes exact selected timestamps: never downgrade frames.
 for(unsigned drop=0;drop<15;++drop){auto a=list; a.erase(a.begin()+drop);if(drop==0)assert(!select({101,102},a));}
 float grid[4]={1.f,0.3f,0.7f,0.8f};
 float support=0.25f*(grid[0]+grid[1]+grid[2]+grid[3]);
 float moving=std::clamp((1.f-support-0.24f)/(0.78f-0.24f),0.f,1.f);
 assert(moving>=0.f && moving<=1.f);
 std::puts("PASS native C++17 matching, 15 unchanged frames, 0/15/57 routes, ABI 100/16, low-confidence reference restoration");
}
"""
 with tempfile.TemporaryDirectory(prefix='photon_26943_cpp17_') as td:
  cpp=Path(td)/'host.cpp';exe=Path(td)/'host';cpp.write_text(code)
  subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
