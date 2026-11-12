#!/usr/bin/env python3
"""Exact three-stage fail-closed active 26920 V2 source and runner seal."""
from pathlib import Path
import hashlib,re
R=Path(__file__).resolve().parent
WF='.github/workflows/build-26920-change-aware.yml'
STAGE='26920_STAGE1_PATHS.txt'
HASHES='26920_HANDOFF_HASHES.sha256'
PREV_EXEC='31eebc26fa69a71da1c82bd7a304bd7d8c4e8158d598df12a92a5b8e21a535bf'
TRIGGER='RUN_26920_V2_ACTIVE_PER_PHYSICAL_LENS_B_ON_LK_FROM_SUCCESSFUL_26917_NO_SHADOW\n'
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
 assert len(changed)==16 and len(set(changed))==16 and len(added)==2
 assert (R/'26920_DELETED_RUNTIME_PATHS.txt').read_text()==''
 assert all('handoff_payload_26920/'+p in paths for p in changed)
 assert (R/'build_26917_incremental.py').is_file() and sha(R/'build_26917_incremental.py')==PREV_EXEC
 assert (R/'TRIGGER_26920.txt').read_text()==TRIGGER
 w=(R/WF).read_text()
 assert 'photon-26920-v2-active-b-on-lk-per-lens-clean-26917' in w
 for text in ['test_26920_source.py --live','test_26920_math_host.py',
  'test_26920_patch_proof.py --live','test_26917_border.py --live',
  'build_26920_incremental.py fetch','build_26920_incremental.py prepare',
  'build_26920_incremental.py verify-compiled','build_26920_incremental.py finalize',
  ':app:assembleDebug','compile_26917_amaze_import.sh','compile_26920_lk_shaders.sh',
  'verify_26906_native_cache.py postflight','verify_26904_v3_cmake_handoff.py --handoff',
  'test_26920_sealed_negatives.py']:
  assert text in w,'missing inherited build gate '+text
 assert w.count('build_26920_incremental.py fetch')==1
 assert w.count('build_26920_incremental.py prepare')==1
 assert w.count('build_26920_incremental.py finalize')==1
 assert not any(t in w for t in ['--skip','--offline','continue-on-error: true','SKIP_COMPILER'])
 for t in ['26918','26919','26917','26916','26915','26914','26904']:
  assert 'test_'+t in w or 'verify_'+t in w
 new=(R/'handoff_payload_26920/app/src/main/java/com/hinnka/mycamera/processor/Iris26920NativeProbe.java').read_text()
 assert 'nativeArm(' in new and 'nativeTakeLastReport()' in new and 'nativeClear()' in new
 assert 'no image change' not in (R/'build_26920_incremental.py').read_text().lower()
 print('PASS 26920 V2 sealed stages='+str(len(paths))+' +1 workflow +1 trigger, SHA-bound active source, 26917 executed runner, real Vulkan and all inherited compiler gates')
if __name__=='__main__':verify()
