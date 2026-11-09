#!/usr/bin/env python3
"""Actual V2 sealed-stage tamper negatives; original 26914 validators retained."""
import hashlib,tempfile,shutil,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent
import verify_26914_v2_handoff as v

def main():
 v.verify()
 rows=(R/'26914_V2_STAGE1_PATHS.txt').read_text().splitlines()
 targets=['handoff_payload_26914_v2/'+v.BRIDGE,'26914_V2_PRECOMPILE_EXPECTED_FULL_APP.sha256',
          'build_26914_v2_incremental.py','test_26914_kotlin_owner.py',
          'test_26914_v2_source.py','verify_26914_v2_handoff.py',
          '.github/workflows/build-26914-v2-change-aware.yml','TRIGGER_26914_V2.txt',
          'build_26914_incremental.py','26914_PRECOMPILE_EXPECTED_FULL_APP.sha256',
          '26914_V2_STAGE1_PATHS.txt','26914_V2_HANDOFF_HASHES.sha256']
 # Re-sealed hostile candidate must still be rejected (not only hash tamper).
 with tempfile.TemporaryDirectory(prefix='photon_26914v2_negative_') as d:
  t=Path(d)
  # Link-free byte copies; guard against symlink bypass.
  full=set(rows)|{'.github/workflows/build-26914-v2-change-aware.yml','TRIGGER_26914_V2.txt',
        '26914_BASE_26913_FULL_APP.sha256','26914_PRECOMPILE_EXPECTED_FULL_APP.sha256',
        '26914_CHANGED_RUNTIME_ALLOWLIST.txt','26914_DELETED_RUNTIME_PATHS.txt',
        '26914_ADDED_RUNTIME_PATHS.txt','26914_STAGE1_PATHS.txt','26914_HANDOFF_HASHES.sha256',
        'handoff_payload_26914/'+v.BRIDGE, 'build_26914_incremental.py',
        'test_26914_source.py','verify_26914_handoff.py',
        '.github/workflows/build-26914-change-aware.yml','TRIGGER_26914.txt'}
  # Actual original V1 seal contains every historical payload path.
  full|=set((R/'26914_STAGE1_PATHS.txt').read_text().splitlines())
  for p in full:
   dest=t/p;dest.parent.mkdir(parents=True,exist_ok=True)
   shutil.copy2(R/p,dest)
  # V1 verifier also imports nothing; V2 source no special dependencies.
  def verifies():
   r=subprocess.run([sys.executable,'-S',str(t/'verify_26914_v2_handoff.py')],cwd=t,capture_output=True,text=True)
   return r.returncode==0
  assert verifies(),'clean-copy original V1 + new V2 validation failed'
  rejects=0
  for p in targets:
   dest=t/p;original=dest.read_bytes()
   dest.write_bytes(original+b'\n# 26914 hostile mutation\n')
   assert not verifies(),f'hostile file unexpectedly accepted {p}'
   dest.write_bytes(original)
   assert verifies(),f'original bytes not restored {p}'
   rejects+=1
  # Tamper corrected Kotlin then re-seal all V2 hashes; semantic diff must reject.
  source=t/'handoff_payload_26914_v2'/v.BRIDGE
  orig=source.read_bytes();source.write_bytes(orig.replace(b'val customNoise26914 =',b'val customNoise26913 =',1))
  h=t/'26914_V2_HANDOFF_HASHES.sha256'
  h.write_text(h.read_text().replace(hashlib.sha256(orig).hexdigest(),hashlib.sha256(source.read_bytes()).hexdigest()))
  assert not verifies(),'re-sealed rogue Kotlin code accepted'
  rejects+=1
 print('PASS 26914 V2 actual complete V1/V2 independent sealed-stage mutations rejected:',rejects)
if __name__=='__main__':main()
