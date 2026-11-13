#!/usr/bin/env python3
"""26925 private shadow source bytes, two real Android ABI copies, no vendor edits."""
from pathlib import Path
import sys
R=Path(__file__).resolve().parent
P=R/'handoff_payload_26925' if '--payload' in sys.argv else R
B=P/'app/src/main/cpp/iris26864'; S=B/'bridge'
C=(B/'Iris26864VendorRawr.cmake').read_text();M=(S/'Iris26924MultiframeCMakeLists.txt').read_text()
FILES={
 'multiframe/pipeline/CMakeLists.txt':S/'Iris26924MultiframeCMakeLists.txt',
 'multiframe/pipeline/src/ScratchLayout.cpp':S/'Iris26925ScratchLayout.cpp',
 'multiframe/pipeline/src/MultiframeRecorder.cpp':S/'Iris26924MultiframeRecorder.cpp',
 'multiframe/pipeline/src/AndroidBurstCoordinator.cpp':S/'Iris26888BOffHdrqCoordinator.cpp',
 'multiframe/pipeline/src/VulkanExecutor.cpp':S/'Iris26888BOffVulkanExecutor.cpp',
 'multiframe/pipeline/include/rawr/raw_gpu_pipeline/MultiframeRecorder.h':S/'Iris26924MultiframeRecorder.h',
 'multiframe/pipeline/include/rawr/raw_gpu_pipeline/VulkanExecutor.h':S/'Iris26924VulkanExecutor.h',
}
for path in ('Iris26924_raw_residual.comp','Iris26924_raw_adjoint.comp',
             'Iris26925_raw_cfa_weight.comp','Iris26925_support_finish.comp'):
 n='iris'+path.split('Iris',1)[1]
 FILES['multiframe/merge_wronski/shaders/'+n]=S/path
for p in FILES.values():assert p.is_file(),('26925 missing compiled shadow '+str(p))
for k in ('Iris26925ScratchLayout.cpp','Iris26925_raw_cfa_weight.comp','Iris26925_support_finish.comp'):
 assert C.count(k)==1,(k,'incorrect CMake shadow count')
for k in ('iris26925_raw_cfa_weight.comp','iris26925_support_finish.comp'):
 assert M.count(k)==1,(k,'not selected in compiled shader list')
assert 'add_subdirectory("${IRIS26887_VENDOR_SHADOW}/multiframe/pipeline"' in C
assert 'Iris26923WronskiFinalize.comp' not in C
assert '"${IRIS26887_VENDOR_SHADOW}/multiframe/merge_wronski/shaders/a11_finalize.comp" COPYONLY' in C
E=(S/'Iris26888BOffVulkanExecutor.cpp').read_text();H=(S/'Iris26924VulkanExecutor.h').read_text()
for name,ident in [('iris26925_raw_cfa_weight','Iris26925RawCfaWeight'),
                   ('iris26925_support_finish','Iris26925SupportFinish')]:
 assert E.count('"'+name+'"')==2 and H.count(ident)==1,(name,'static eager descriptor mapping')
assert '{{0,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE},{1,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}' in E
assert 'static_assert(sizeof(kOrder) / sizeof(kOrder[0]) == static_cast<size_t>(ShaderId::Count)' in E
print('PASS 26925 private CMake source ownership, no stale 26923 shader, all new CMake shadow sources and Vulkan eager specs')
if '--cmake' in sys.argv:
 cxx=R/'app/.cxx';assert cxx.is_dir(),'real Android .cxx outputs missing (compile required)'
 for abi in ('arm64-v8a','armeabi-v7a'):
  for dest,source in FILES.items():
   matches=[p for p in cxx.rglob(dest) if abi in p.parts and 'iris26887_b_only_vendor' in p.parts]
   assert len(matches)==1,(abi,dest,'expected exactly one CMake shadow input',matches)
   assert matches[0].read_bytes()==source.read_bytes(),(abi,dest,'compiled CMake source bytes diverged')
 print('PASS 26925 actual CMake-generated source/shader copies, BOTH Android NDK ABIs; no original vendor changes')
