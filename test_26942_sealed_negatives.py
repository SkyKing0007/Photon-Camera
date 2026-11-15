#!/usr/bin/env python3
"""Fail closed on altered source/validator/allowlist/stage/handoff source references."""
import sys,tempfile,shutil
from pathlib import Path
import build_26942_incremental as m

def main():
 changed,_,_=m.scope()
 sealed=[line.split('  ',1)[1] for line in (m.R/'26942_HANDOFF_HASHES.sha256').read_text().splitlines()]
 original=m.R
 with tempfile.TemporaryDirectory(prefix='26942_negatives_') as tmp:
  t=Path(tmp)
  for p in sealed+['26942_HANDOFF_HASHES.sha256']:
   dst=t/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original/p,dst)
  def mutate(label,p,bad):
   source=p.read_bytes()
   try:
    p.write_bytes(bad)
    try:m.seal()
    except Exception:pass
    else:raise AssertionError('negative test escaped: '+label)
   finally:p.write_bytes(source)
  prev=m.R;prevflag=getattr(m,'PACKAGE_ONLY',False)
  try:
   m.R=t;m.PACKAGE_ONLY=True
   assert m.scope()[0]==changed
   m.seal()
   p=t/'handoff_payload_26942/app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp'
   mutate('mutated Vulkan frequency chunk scheduler',p,p.read_bytes()+b'\n// MODIFIED')
   p=t/'test_26942_shader_contract.py';mutate('missing shader validator',p,b'')
   p=t/'26942_CHANGED_RUNTIME_ALLOWLIST.txt';mutate('unexpected source changed',p,p.read_bytes()+b'app/src/main/cpp/native/INVALID.cpp\n')
   p=t/'26942_V2_STAGE_2_UPLOAD_PATHS.txt';mutate('missing actual workflow',p,b'.github/workflows/WRONG.yml\n')
   p=t/'26942_EXPECTED_ACTION_EXECUTABLES.txt';mutate('missing actual script reference',p,p.read_bytes().replace(b'compile_26942_shaders.sh',b'compile_26942_fake.sh'))
   p=t/'26942_HANDOFF_HASHES.sha256';mutate('missing hash manifest entry',p,p.read_bytes().replace(b'test_26942_source.py',b'unreferenced_absent.py'))
   m.seal()
  finally:m.R=prev;m.PACKAGE_ONLY=prevflag
 print('PASS 26942 sealed negative source/GLSL/validator/allowlist/stage/references/hash-manifest tests')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
