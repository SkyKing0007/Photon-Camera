#include "Iris26864RealRawrCoordinator.hpp"
#include <cassert>
#include <iostream>
using namespace iris26864;
static RealRawrRunRequest request() {
 RealRawrRunRequest q;
 for(int i=0;i<2;++i){RealRawrNormal n{};n.timestampNs=100+i;
 n.borrowedRaw.ref.timestampNs=n.timestampNs;n.borrowedRaw.ref.width=32;n.borrowedRaw.ref.height=32;
 n.borrowedRaw.image=100+i;n.borrowedRaw.view=200+i;
 q.normals.push_back(n);}
 q.prepareNormal=[](uint32_t){++test::preparedCalls;};return q;
}
int main(){
 auto q=request();int consumed=0;
 auto cb=[&](const auto&, const auto&){++consumed;};
 // Success: normal RAWR ownership is released, with no unnecessary idle wait.
 test::mode=0;test::idle=0;
 runRealPinnedRawrB(q,cb);
 assert(consumed==1 && test::destructorCalls==1 && test::idleCalls==0 && test::preparedCalls==2);
 // Failed RAWR fence: settled queue before upstream scratch is destroyed.
 test::mode=1;int prior=test::destructorCalls;int idles=test::idleCalls;
 try {runRealPinnedRawrB(q,cb); assert(false);} catch(const std::runtime_error&){}
 assert(test::idleCalls==idles+1 && test::destructorCalls==prior+1 && test::destructorBeforeIdle==0);
 // Unresolved queue: upstream scratch is quarantined and not destroyed.
 test::idle=-4;prior=test::destructorCalls;idles=test::idleCalls;
 try {runRealPinnedRawrB(q,cb); assert(false);} catch(const std::runtime_error&){}
 assert(test::idleCalls==idles+1 && test::destructorCalls==prior && test::destructorBeforeIdle==0);
 // Missing measured noise aborts and cannot call B's output consumer.
 test::idle=0;test::mode=2;prior=consumed;
 try {runRealPinnedRawrB(q,cb);assert(false);} catch(const std::runtime_error&){}
 assert(consumed==prior);
 // Wrong 2x geometry aborts before AMaZE publication.
 test::mode=3;prior=consumed;
 try {runRealPinnedRawrB(q,cb);assert(false);} catch(const std::runtime_error&){}
 assert(consumed==prior);
 // Consumer error remains fail-closed and settles queue.
 test::mode=0;prior=consumed;idles=test::idleCalls;
 try {runRealPinnedRawrB(q,[&](const auto&,const auto&){throw std::runtime_error("AMaZE failed");});assert(false);} catch(const std::runtime_error&){}
 assert(consumed==prior && test::idleCalls==idles+1);
 // HDR+ 1x still works and does not require Wronski noise receipt.
 q.algorithm=RealBEngine::HdrPlusFrequency;
 runRealPinnedRawrB(q,cb); assert(consumed==prior+1);
 std::cout<<"PASS: 7 real-wrapper host-compiled RAII paths, no Android/Vulkan compiler claim\n";
}
