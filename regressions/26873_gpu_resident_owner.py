#!/usr/bin/env python3
"""Real previous-runtime regression plus memory/fence/frame-count ownership assertions."""
from pathlib import Path
import sys,re
B=Path(sys.argv[1]);C=Path(sys.argv[2]);pr='app/src/main/cpp/iris26864/'
def b(f):return (B/pr/f).read_text()
def c(f):return (C/pr/f).read_text()
run=c('Iris26864FrozenDirectRawrRunner.cpp');coor=c('Iris26864RealRawrCoordinator.cpp');upload=c('Iris26864TwoSlotRaw16Uploader.cpp');header=c('Iris26864TwoSlotRaw16Uploader.hpp')
assert 'TwoSlotRaw16Uploader twoSlots(' in b('Iris26864FrozenDirectRawrRunner.cpp')
assert 'ONE fenced companion GPU slot' in b('Iris26864RealRawrCoordinator.cpp')
assert 'IRIS_26873_B_RESIDENT_INPUT_OWNER' in run
assert 'residentEligible=hdrq && request.normals.size()<=30u' in run
assert 'const uint64_t reserve=1536ull*1024ull*1024ull' in run
assert 'want<=largestDeviceHeap-reserve' in run
assert 'B_RESIDENT_ALLOC_FALLBACK' in run
assert 'inputs->uploadInto(i,i,raw);' in run
assert 'merge.prepareNormal=[](std::uint32_t){}' in run
assert 'merge.prepareNormal=[&](std::uint32_t index)' in run
assert 'inputs->upload(index,request.referenceIndex,raw)' in run
assert 'if(!inputs) inputs.reset(new TwoSlotRaw16Uploader' in run
assert 'vkQueueWaitIdle(request.inheritedQueue)' in run
assert run.count('quarantineUnresolved()')>=3
assert 'mode=%s normals=%zu uploads=%u expected=%zu upload_ms=%.2f' in run
assert 'B_RESIDENT_SCRATCH_FALLBACK' in run
assert 'if(!resident||enteredConsumer||!allocationFailure)' in run
assert 'inputs.reset(); // no unresolved GPU use' in run
assert 'runRealPinnedRawrB(merge,wrappedConsume); // exact math, all frames' in run
assert 'FrozenRawInputLayout::CaptureResident' in coor
assert 'r.algorithm!=RealBEngine::HdrPlusFrequency' in coor
assert 'residentImages.insert(f.borrowedRaw.image)' in coor
assert 'residentViews.insert(f.borrowedRaw.view)' in coor
assert 'ONE fenced companion GPU slot' in coor
assert 'uploadInto(index,index==referenceIndex?0u:1u,frames)' in upload
assert 'for(uint32_t i=0;i<slots_;++i)' in upload
assert 'if(quarantined_||index>=frames.size()||slot>=slots_' in upload
assert 'uint32_t slots=2u' in header
assert 'RawInputLayout' not in b('Iris26864RealRawrCoordinator.hpp')
for untouched in ['Iris26864JniGpuInteropImpl.inc','Iris26864BMergePlan.hpp']:
 assert b(untouched)==c(untouched)
for untouched in ['app/src/main/java/com/hinnka/mycamera/processor/GlesIris26864FrozenRawrIngress.kt',
                  'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
                  'app/src/main/assets/shaders/preview/main_fs.glsl']:
 assert (B/untouched).read_bytes()==(C/untouched).read_bytes()
# Exact observed prior failure: shared mutable companion image must remain explicitly rejected
assert 'f.borrowedRaw.image!=companion||f.borrowedRaw.view!=companionView' in coor
# No new JNI/Camera2 fallback, no Algorithm ownership substitution
assert 'runRealPinnedRawrB(merge,wrappedConsume)' in run
assert 'no silent alternate capture' in run
print('PASS 26873 actual 26872 source regression: unique resident views + strict old fallback + unchanged Java/JNI/GLSL/AE')
