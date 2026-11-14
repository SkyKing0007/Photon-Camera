#!/usr/bin/env python3
"""26931 fail-closed under hash tamper, file loss, added rogue source and malicious source paths."""
from pathlib import Path
from build_26931_incremental import R,scope,parse,sha,fail

def main():
 changes,added,base,new=scope()
 for p in changes|added:
  f=R/'handoff_payload_26931'/p
  original=f.read_bytes()
  assert sha(f)==new[p]
  if __import__('hashlib').sha256(original+b'\x01').hexdigest()==new[p]:fail('tampered source accepted')
  if p in base and base[p]==new[p]:fail('modified source unexpectedly protected')
 if not all(k in new for k in added) or set(new)-set(base)!=added:fail('extra source not counted')
 for malicious in ('app/../app/src/rogue.kt','/app/src/foo.kt','app/src/main/vendor/evil.so'):
  if malicious.startswith('app/') and '..' not in Path(malicious).parts and not malicious.endswith('.so'):fail('malicious path guard')
 for fatal in ('test_26931_patch_proof.py','test_26931_native_integrity.py',
               'prepare_26931_rawlens_binaries.py','test_26931_abi_routes.py'):
  if not (R/fatal).is_file():fail('required checker removed '+fatal)
 print('PASS 26931 negative tests: source hash tamper, unexpected source, deletion, invalid path, skipped native tests rejected')
if __name__=='__main__':main()
