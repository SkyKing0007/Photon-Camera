#!/usr/bin/env python3
"""Exact three-stage fail-closed active 26920 V5 source, CMake shadow ABI, compiler CLI and runner seal."""
from pathlib import Path
import hashlib,re
R=Path(__file__).resolve().parent
WF='.github/workflows/build-26920-change-aware.yml'
STAGE='26920_STAGE1_PATHS.txt'
HASHES='26920_HANDOFF_HASHES.sha256'
PREV_EXEC='31eebc26fa69a71da1c82bd7a304bd7d8c4e8158d598df12a92a5b8e21a535bf'
TRIGGER='RUN_26920_V5_ACTUAL_CMAKE_SHADOW_ABI_REPAIR_FROM_SUCCESSFUL_26917\n'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
 paths=(R/STAGE).read_text().splitlines()
 assert paths and len(paths)==len(set(paths)) and HASHES in paths
 assert all(not Path(p).is_absolute() and '..' not in Path(p).parts for p in paths)
 allowed=set(paths+[WF,'TRIGGER_26920.txt'])
 provided={}
 for ln in (R/HASHES).read_text().splitlines():
  h,p=ln.split('  ',1)
  assert p not in provided and re.fullmatch('[a-f0-9]{64}',h)
  provided[p]=h
 assert set(provided)==allowed-{HASHES},(set(provided)-allowed,allowed-set(provided))
 for p,h in provided.items():assert (R/p).is_file() and sha(R/p)==h,p
 changed=(R/'26920_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 added=(R/'26920_ADDED_RUNTIME_PATHS.txt').read_text().splitlines()
 assert len(changed)==19 and len(set(changed))==19 and len(added)==2
 assert (R/'26920_DELETED_RUNTIME_PATHS.txt').read_text()==''
 assert all('handoff_payload_26920/'+p in paths for p in changed)
 assert (R/'build_26917_incremental.py').is_file() and sha(R/'build_26917_incremental.py')==PREV_EXEC
 assert (R/'TRIGGER_26920.txt').read_text()==TRIGGER
 w=(R/WF).read_text()
 assert 'photon-26920-v5-shadow-abi-b-on-lk-per-lens-clean-26917' in w
 for text in ['test_26920_source.py --live','test_26920_math_host.py',
  'test_26920_patch_proof.py --live','test_26917_border.py --live',
  'build_26920_incremental.py fetch','build_26920_incremental.py prepare',
  'build_26920_incremental.py verify-compiled','build_26920_incremental.py finalize',
  ':app:assembleDebug','compile_26917_amaze_import.sh','compile_26920_lk_shaders.sh',
  'verify_26906_native_cache.py postflight','verify_26904_v3_cmake_handoff.py --handoff',
  'test_26920_sealed_negatives.py', 'test_26920_vulkan_abi.py --live',
  'test_26920_vulkan_abi.py --live --cmake']:
  assert text in w,'missing inherited build gate '+text
 assert w.count('build_26920_incremental.py fetch')==1
 assert w.count('build_26920_incremental.py prepare')==1
 assert w.count('build_26920_incremental.py finalize')==1
 assert not any(t in w for t in ['--skip','--offline','continue-on-error: true','SKIP_COMPILER'])
 # Historical 26904 V1 regression: spirv-opt does NOT accept a separate
 # target-env token. It requires --target-env=vulkan1.1, unlike spirv-val.
 # This gate is semantic, not just a SHA seal: a new, consistently-resealed
 # package with the old malformed optimizer command must still be rejected.
 compiler=(R/'compile_26920_lk_shaders.sh').read_text()
 assert compiler.count('spirv-opt --target-env=vulkan1.1 -O ')==1, 'wrong SPIR-V optimizer CLI'
 assert not re.search(r'\bspirv-opt\s+--target-env\s+vulkan',compiler), '26904 V1 optimizer CLI regression'
 for exact in ['for variant in prod trace;', 'for shader in lk_refine robust_photometric;',
  'spirv-val --target-env vulkan1.1', 'spirv-opt --target-env=vulkan1.1 -O',
  'spirv-val --target-env vulkan1.1 "$OUT/${shader}_${variant}.opt.spv"']:
  assert exact in compiler, 'missing production/trace Vulkan compiler gate '+exact

 for t in ['26918','26919','26917','26916','26915','26914','26904']:
  assert 'test_'+t in w or 'verify_'+t in w
 # Semantic safety gate against the successful 26920 V3 phone crash:
 # Both SSBOs are always declared in the shader even when the lens toggle is OFF.
 ex=(R/'handoff_payload_26920/app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/pipeline/src/VulkanExecutor.cpp').read_text()
 for shader,nxt,binding in [('lk_refine','flow_dense_smooth',4),('robust_photometric','robust_erode5',9)]:
  part=ex.split('{"'+shader+'",',1)[1].split('{"'+nxt+'",',1)[0]
  descriptors=dict((int(n),typ) for n,typ in re.findall(r'\{(\d+), VK_DESCRIPTOR_TYPE_(STORAGE_BUFFER|STORAGE_IMAGE)\}',part))
  assert descriptors.get(binding)=='STORAGE_BUFFER', '26920 V3 Vulkan pipeline crash: '+shader+' SSBO binding='+str(binding)
 assert 'mf compute pipeline shader=' in ex and ' variant=' in ex
 # ACTUAL compiled CMake shadow: successful 26917 replaces the upstream
 # VulkanExecutor.cpp AND AndroidBurstCoordinator.cpp from Iris26888 bridge.
 # V4 mistakenly fixed the upstream file only. Both shadows are required,
 # regardless of the user switch state and even if every SHA receipt passes.
 shadow_ex=(R/'handoff_payload_26920/app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp').read_text()
 for shader,nxt,binding in [('lk_refine','flow_dense_smooth',4),('robust_photometric','robust_erode5',9)]:
  part=shadow_ex.split('{"'+shader+'",',1)[1].split('{"'+nxt+'",',1)[0]
  descriptors=dict((int(n),typ) for n,typ in re.findall(r'\{(\d+), VK_DESCRIPTOR_TYPE_(STORAGE_BUFFER|STORAGE_IMAGE)\}',part))
  assert descriptors.get(binding)=='STORAGE_BUFFER', '26920 V4 CMake shadow ABI failure: '+shader+' SSBO binding='+str(binding)
 assert 'mf compute pipeline shader=' in shadow_ex and ' variant=' in shadow_ex
 assert 'shadow=iris26887_b_only_vendor' in shadow_ex
 shadow_co=(R/'handoff_payload_26920/app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp').read_text()
 for piece in ('VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT',
               'destroyHostBuffer(iris26920Counts_)',
               'if (merge_.iris26920Active) ensureHostBuffer(iris26920Counts_, 16u);',
               'vkCmdCopyBuffer(command_',
               'arena_.buffer("iris26920_stats").buffer',
               'result.iris26920Enabled = true',
               'result.iris26920Counts[0] != tileMax'):
  assert piece in shadow_co, '26920 V4 CMake shadow Wronski path missing '+piece
 assert 'test_26920_vulkan_abi.py' in paths
 new=(R/'handoff_payload_26920/app/src/main/java/com/hinnka/mycamera/processor/Iris26920NativeProbe.java').read_text()
 assert 'nativeArm(' in new and 'nativeTakeLastReport()' in new and 'nativeClear()' in new
 assert 'no image change' not in (R/'build_26920_incremental.py').read_text().lower()
 print('PASS 26920 V5 sealed stages='+str(len(paths))+' +1 workflow +1 trigger, SHA-bound ACTUAL CMake shadow, active source, 26917 executed runner, real Vulkan and all inherited compiler gates')
if __name__=='__main__':verify()
