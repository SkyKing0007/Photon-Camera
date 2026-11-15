#!/usr/bin/env python3
"""Mutation-test exact 26935 source, 3-stage seal, tool chain and original historical jobs."""
import sys,subprocess,tempfile,shutil,pathlib
from build_26935_incremental import R,scope,fail

def negative(name,change):
 with tempfile.TemporaryDirectory(prefix='26935_scope_negative_') as d:
  t=pathlib.Path(d)
  entries=[row.split('  ',1)[1] for row in (R/'26935_HANDOFF_HASHES.sha256').read_text().splitlines()]
  for rel in entries+['26935_HANDOFF_HASHES.sha256']:
   src=R/rel;dst=t/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
  change(t)
  x=subprocess.run([sys.executable,'-S','build_26935_incremental.py','seal','--package-only'],cwd=t,capture_output=True,text=True,timeout=130)
  if x.returncode==0 or '26935 BLOCKED' not in x.stderr:
   fail('negative mutation did not fail closed '+name+' '+x.stderr[-700:])
  print('PASS rejected',name)

def main():
 scope()
 overlay='handoff_payload_26935/app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26935BOnSession.java'
 negative('changed guard source hash',lambda t:(t/overlay).write_bytes((t/overlay).read_bytes()+b'\n//tampered\n'))
 negative('missing processing relay',lambda t:(t/'handoff_payload_26935/app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26935BOnProcessingRelay.java').unlink())
 negative('missing actual pinned shader compilation',lambda t:(t/'compile_26935_shaders.sh').unlink())
 negative('missing authenticated original dual-ABI native restore',lambda t:(t/'prepare_26935_lkr_from_successful_26934.py').unlink())
 negative('workflow missing NDK/Java/GLSL',lambda t:(t/'.github/workflows/build-26935-change-aware.yml').write_text('name: fake short workflow\n'))
 negative('short changed-file allowlist',lambda t:(t/'26935_CHANGED_RUNTIME_ALLOWLIST.txt').write_text('app/version.properties\n'))
 negative('tampered protected 26934 index',lambda t:(t/'26935_PROTECTED_SOURCE.sha256').write_text('0'*64+'  app/version.properties\n'))
 negative('unexpected protected new path',lambda t:(t/'handoff_payload_26935/app/src/main/java/com/particlesdevs/photoncamera/capture/UnexpectedProtected.java').write_text('class UnexpectedProtected{}\n'))
 print('PASS eight fail-closed mutated 26935 staged source/compilers/workflow/protected scope')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
