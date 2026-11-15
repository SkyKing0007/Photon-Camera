#!/usr/bin/env python3
"""Mandatory fail-closed negative cases: tamper, missing file, scope, stage, bad manifest."""
from pathlib import Path
import tempfile,shutil,sys
import build_26940_incremental as m

def main():
 changed,_,_=m.scope()
 sealed=[line.split('  ',1)[1] for line in (m.R/'26940_HANDOFF_HASHES.sha256').read_text().splitlines()]
 src=m.R
 with tempfile.TemporaryDirectory(prefix='26940_sealed_negative_') as td:
  t=Path(td)
  for p in sealed+['26940_HANDOFF_HASHES.sha256']:
   dst=t/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src/p,dst)
  def blocked(label,write,restore):
   write()
   try:
    try:m.seal()
    except Exception:pass
    else:raise AssertionError('FAIL CLOSED test failed '+label)
   finally:restore()
  previous=m.R;previous_package=getattr(m,'PACKAGE_ONLY',False)
  try:
   m.R=t;m.PACKAGE_ONLY=True
   assert m.scope()[0]==changed
   m.seal()
   p=t/'handoff_payload_26940/app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp'
   data=p.read_bytes()
   blocked('runtime source SHA mutation',lambda:p.write_bytes(data+b'\n// CORRUPTED'),lambda:p.write_bytes(data))
   p=t/'test_26940_cache_host.py';data=p.read_bytes()
   blocked('missing mandatory host validator',lambda:p.unlink(),lambda:p.write_bytes(data))
   p=t/'26940_CHANGED_RUNTIME_ALLOWLIST.txt';data=p.read_bytes()
   blocked('unexpected source allowlist',lambda:p.write_bytes(data+b'app/src/main/NOPE\n'),lambda:p.write_bytes(data))
   p=t/'26940_V1_STAGE_2_UPLOAD_PATHS.txt';data=p.read_bytes()
   blocked('invalid stage workflow',lambda:p.write_bytes(b'.github/workflows/STAGED_WRONG.yml\n'),lambda:p.write_bytes(data))
   p=t/'26940_HANDOFF_HASHES.sha256';data=p.read_bytes()
   blocked('missing sealed path',lambda:p.write_bytes(data.replace(b'test_26940_source.py',b'missing_referenced_source.py')),lambda:p.write_bytes(data))
   m.seal()
  finally:
   m.R=previous;m.PACKAGE_ONLY=previous_package
 print('PASS 26940 sealed negative mutation/missing-file/allowlist/stage/manifest rejection; clean seal restored')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
