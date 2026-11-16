#!/usr/bin/env python3
"""Tampering with staged candidate, historical refs, three-stage seal must abort."""
import tempfile,sys,shutil
from pathlib import Path
import build_26943_incremental as m

def main():
 paths,_,_=m.scope()
 sealed=[line.split('  ',1)[1] for line in (m.R/'26943_HANDOFF_HASHES.sha256').read_text().splitlines()]
 original=m.R
 with tempfile.TemporaryDirectory(prefix='photon_26943_negatives_') as td:
  t=Path(td)
  for p in sealed+['26943_HANDOFF_HASHES.sha256']:
   dst=t/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original/p,dst)
  oldR=m.R;oldPackage=getattr(m,'PACKAGE_ONLY',False)
  def reject(name,p,bad):
   original_bytes=p.read_bytes()
   try:
    p.write_bytes(bad)
    try:m.seal()
    except Exception:pass
    else:raise AssertionError('tamper accepted '+name)
   finally:p.write_bytes(original_bytes)
  try:
   m.R=t;m.PACKAGE_ONLY=True
   assert m.scope()[0]==paths
   m.seal()
   p=t/'handoff_payload_26943/app/src/main/cpp/iris26864/Iris26943RawAhbIngress.cpp'
   reject('modified import',p,p.read_bytes()+b'\n//tampered')
   p=t/'handoff_payload_26943/app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp'
   reject('removed descriptor-layout correction',p,p.read_bytes().replace(b'{5, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}',b'{5, VK_DESCRIPTOR_TYPE_STORAGE_BUFFER}',1))
   p=t/'26943_CHANGED_RUNTIME_ALLOWLIST.txt'
   reject('changed unapproved',p,p.read_bytes()+b'app/src/main/cpp/vendor/OOPS.cpp\n')
   p=t/'26943_ADDED_RUNTIME_PATHS.txt'
   reject('missing new runtime',p,b'')
   p=t/'test_26943_shader_contract.py'
   reject('missing shader gate',p,b'')
   p=t/'test_26943_source.py'
   reject('remove runtime descriptor ABI check',p,p.read_bytes().replace(b'verify_hdrq_descriptor_abi(',b'disabled_hdrq_descriptor_abi(',1))
   p=t/'26943_V1_STAGE_2_UPLOAD_PATHS.txt'
   reject('incorrect workflow path',p,b'.github/workflows/WRONG.yml\n')
   p=t/'26943_EXPECTED_ACTION_EXECUTABLES.txt'
   reject('stale executable',p,p.read_bytes().replace(b'compile_26943_shaders.sh',b'compile_26942_shaders.sh'))
   p=t/'26943_HANDOFF_HASHES.sha256'
   reject('missing receipt',p,p.read_bytes().replace(b'test_26943_source.py',b'BADABSENT_source.py'))
   m.seal()
  finally:m.R=oldR;m.PACKAGE_ONLY=oldPackage
 print('PASS 26943 negative rejection: 18 changes+4 added, 2032 protected, descriptor ABIs, shaders, allowlists, stages, executable refs and package seals')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
