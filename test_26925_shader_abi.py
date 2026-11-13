#!/usr/bin/env python3
"""Fail-closed current 26925 eager descriptor layout + compiled SPIR-V reflection."""
from pathlib import Path
import sys,re,struct
R=Path(__file__).resolve().parent
P=R/'handoff_payload_26925' if '--payload' in sys.argv else R
B=P/'app/src/main/cpp/iris26864/bridge'; exec=(B/'Iris26888BOffVulkanExecutor.cpp').read_text();head=(B/'Iris26924VulkanExecutor.h').read_text()
shaders={
 'iris26924_raw_residual':('Iris26924_raw_residual.comp',6),
 'iris26924_raw_adjoint':('Iris26924_raw_adjoint.comp',7),
 'iris26925_raw_cfa_weight':('Iris26925_raw_cfa_weight.comp',4),
 'iris26925_support_finish':('Iris26925_support_finish.comp',3),
 'iris26924_raw_update':('Iris26924_raw_update.comp',3),
 'iris26924_reference_model':('Iris26924_reference_model.comp',2),
}
for key,(file,n) in shaders.items():
 p=B/file
 if not p.is_file() and '--payload' in sys.argv:continue
 src=p.read_text()
 ids=[int(i) for i in re.findall(r'layout\(set=0,binding=(\d+),',src)]
 assert ids==list(range(n)),(key,'source binding divergence',ids)
 a='{"'+key+'",';assert exec.count(a)==1,(key,'missing/duplicate eager pipeline spec')
 chunk=exec.split(a,1)[1].split('}},',1)[0]
 got=[int(i) for i in re.findall(r'\{(\d+),VK_DESCRIPTOR_TYPE_STORAGE_IMAGE\}',chunk)]
 assert got==list(range(n)),(key,'actual eager C++ Vulkan ABI mismatch',got,n)
for k in ('Iris26925RawCfaWeight','Iris26925SupportFinish'):
 assert head.count(k)==1
h=head.split('enum class ShaderId')[1].split('};')[0]
ids=[x.strip().split('=')[0].strip() for x in h.split(',') if x.strip() and 'Count' not in x]
o=exec.split('static constexpr const char* kOrder[] = {',1)[1].split('};',1)[0]
order=re.findall(r'"([^"\n]+)"',o)
assert len(ids)==len(order)==61,(len(ids),len(order),'missing/duplicate eager pipeline index')
assert order.index('iris26925_raw_cfa_weight')==ids.index('Iris26925RawCfaWeight')
assert order.index('iris26925_support_finish')==ids.index('Iris26925SupportFinish')
assert 'static_assert(sizeof(kOrder) / sizeof(kOrder[0]) == static_cast<size_t>(ShaderId::Count)' in exec
print('PASS 26925 exact six native current shaders, per-binding eager Vulkan descriptor type/order 61, source push layout')
if '--compiled' in sys.argv:
 from importlib.util import spec_from_file_location,module_from_spec
 sp=spec_from_file_location('historical26920abi',R/'test_26920_vulkan_abi.py')
 m=module_from_spec(sp);sp.loader.exec_module(m)
 root=R/'.photon_26904_incremental_work/real_shader_tools/26925_raw_projection'
 assert 'DIR="$TOOLS/26925_raw_projection"' in (R/'compile_26925_hr_spirv.sh').read_text(), 'actual pinned compiler output path differs from SPIR-V reflector'
 assert root.is_dir(),('missing actual pinned compiled SPIRV',root)
 for key,(file,n) in shaders.items():
  src=Path(file).stem
  for variant in ('prod','trace'):
   for suffix in ('.spv','.opt.spv'):
    p=root/(src+'_'+variant+suffix)
    assert p.is_file(),('missing actual compiled+optimized Vulkan shader',p)
    mapp=m.parse_spv(p)
    assert mapp=={i:'image' for i in range(n)},(p,mapp,n)
 print('PASS current 26925 prod+trace raw SPIR-V and optimizer descriptor REFLECTION matches actual eager VkDescriptorSetLayout; not source-only')
