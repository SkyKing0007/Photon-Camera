#!/usr/bin/env python3
"""Real host C++17 extracted from actual live 26921 native source; parity positive/negative regressions."""
from pathlib import Path
import subprocess,tempfile,shutil,sys
path=Path('app/src/main/cpp/iris26864/Iris26864FrozenDirectRawrRunner.cpp')
if '--payload' in sys.argv:path=Path('handoff_payload_26921')/path
s=path.read_text()
a=s.index('    if (iris26920Arm.armed) {',s.index('void runRealRawrFromFrozenDirectNormals('))
b=s.index('    iris26920Report =',a)
guard=s[a:b]
for needle in ('shutterMatches!=1u','wronskiReference.physicalLensIdentity','normal.physicalLensIdentity!=iris26920Arm.lens','iris26920Arm.armed=false'):
 assert needle in guard,needle
program=r'''#include <vector>
#include <stdexcept>
#include <cstdint>
#include <cstddef>
#include <cassert>
struct Normal { struct {uint64_t timestamp;} borrowed; uint64_t physicalLensIdentity;};
enum class RealBEngine {HdrPlusFrequency,WronskiTrue2x};
struct Req {std::vector<Normal> normals;std::size_t referenceIndex;RealBEngine algorithm;};
struct Arm {bool armed;bool enabled;uint64_t lens;uint64_t referenceTimestamp;};
Arm iris26920Arm;
void guard(const Req& request) {
''' + guard + '''}
bool accepts(Req r,uint64_t lens,uint64_t shutter,bool enabled){
 iris26920Arm={true,enabled,lens,shutter};
 try{guard(r);return !iris26920Arm.armed;}catch(...){return false;}
}
int main(){
 Req base{{{{100},55},{{101},55},{{102},55}},0,RealBEngine::WronskiTrue2x};
 assert(accepts(base,55,100,true));
 base.referenceIndex=2;assert(accepts(base,55,100,true));
 assert(accepts(base,55,100,false));
 assert(!accepts(base,55,999,true));
 assert(!accepts(base,66,100,true));
 base.normals[1].physicalLensIdentity=66;assert(!accepts(base,55,100,true));
 base.normals[1].physicalLensIdentity=55;
 base.normals[1].borrowed.timestamp=100;assert(!accepts(base,55,100,true));
 base.normals[1].borrowed.timestamp=101;
 base.algorithm=RealBEngine::HdrPlusFrequency;assert(!accepts(base,55,100,true));
 base.algorithm=RealBEngine::WronskiTrue2x;
 base.referenceIndex=1;assert(accepts(base,55,100,true));
}
'''
with tempfile.TemporaryDirectory() as t:
 p=Path(t)/'26921_guard.cpp';p.write_text(program)
 cc=shutil.which('clang++') or shutil.which('g++')
 if not cc:raise RuntimeError('real host C++ compiler missing')
 subprocess.run([cc,'-std=c++17','-Wall','-Wextra','-Werror','-O2',str(p),'-o',t+'/guard'],check=True)
 subprocess.run([t+'/guard'],check=True)
print('PASS 26921 real host C++17 native guard 9 active-path positive/negative cases')
