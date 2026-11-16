#!/usr/bin/env python3
"""Fail closed on actual tampering with staged 26944 source, seal, references and workflow."""
import tempfile,sys,shutil
from pathlib import Path
import build_26944_incremental as m

def main():
 paths,_,_=m.scope()
 sealed=[line.split('  ',1)[1] for line in (m.R/'26944_HANDOFF_HASHES.sha256').read_text().splitlines()]
 original=m.R
 with tempfile.TemporaryDirectory(prefix='photon_26944_negatives_') as td:
  t=Path(td)
  for p in sealed+['26944_HANDOFF_HASHES.sha256']:
   dst=t/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original/p,dst)
  oldR=m.R;oldPackage=getattr(m,'PACKAGE_ONLY',False)
  def reject(name,p,bad):
   before=p.read_bytes()
   try:
    p.write_bytes(bad)
    try:m.seal()
    except Exception:pass
    else:raise AssertionError('tamper accepted '+name)
   finally:p.write_bytes(before)
  try:
   m.R=t;m.PACKAGE_ONLY=True
   assert m.scope()[0]==paths
   m.seal()
   p=t/'handoff_payload_26944/app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMerge.comp'
   reject('changed Fourier merge',p,p.read_bytes()+b'\n// not sealed')
   p=t/'26944_CHANGED_RUNTIME_ALLOWLIST.txt'
   reject('unapproved source path',p,p.read_bytes()+b'app/src/main/cpp/iris26864/vendor/rawr/WRONG.cpp\n')
   p=t/'26944_ADDED_RUNTIME_PATHS.txt'
   reject('unapproved new source',p,b'app/src/main/cpp/vendor/OOPS.cpp\n')
   p=t/'test_26944_shader_contract.py';reject('missing shader check',p,b'')
   p=t/'26944_EXPECTED_ACTION_EXECUTABLES.txt'
   reject('stale old script',p,p.read_bytes().replace(b'compile_26944_shaders.sh',b'compile_26943_shaders.sh'))
   p=t/'.github/workflows/build-26944-change-aware.yml'
   reject('weakened compiler',p,p.read_bytes().replace(b':app:assembleDebug --stacktrace',b':app:compileDebugJavaWithJavac'))
   p=t/'26944_ROLLBACK_FULLINDEX.patch'
   reject('reverse patch prefix',p,p.read_bytes().replace(b'diff --git a/',b'diff --git b/',1))
   p=t/'26944_HANDOFF_HASHES.sha256'
   reject('missing receipt',p,p.read_bytes().replace(b'test_26944_source.py',b'OLD_BAD_SOURCE.py'))
   m.seal()
  finally:m.R=oldR;m.PACKAGE_ONLY=oldPackage
 print('PASS 26944 tamper/missing source, strict workflow, historical refs, patch, stage, seal fail-closed negatives')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
