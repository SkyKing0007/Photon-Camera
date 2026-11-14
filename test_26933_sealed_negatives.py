#!/usr/bin/env python3
"""Tamper, missing-reference, reserved keyword and negative scope: fail CLOSED."""
import shutil,subprocess,sys,tempfile
from pathlib import Path
from build_26933_incremental import R,scope,sha,fail

def negative(mutator,name):
 with tempfile.TemporaryDirectory(prefix='photon26933_neg_') as td:
  root=Path(td)
  paths=[s.split('  ',1)[1] for s in (R/'26933_HANDOFF_HASHES.sha256').read_text().splitlines()]
  paths+=['26933_HANDOFF_HASHES.sha256']
  for rel in paths:
   src=R/rel;dst=root/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
  mutator(root)
  x=subprocess.run([sys.executable,'-S','build_26933_incremental.py','seal','--package-only'],cwd=root,capture_output=True,text=True,timeout=120)
  if x.returncode==0 or '26933 BLOCKED:' not in x.stderr:
   fail('negative test accepted unexpectedly '+name+'\n'+x.stderr[-700:])
  print('PASS fail closed',name)

def main():
 ch,ad,b,n=scope()
 if (len(b),len(n),len(ch),len(ad))!=(2048,2048,2,0):fail('negative baseline source universe unexpected')
 sample='handoff_payload_26933/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt'
 negative(lambda p:(p/sample).write_bytes((p/sample).read_bytes()+b'\n// stale corrupt'), 'corrupted current GLSL')
 negative(lambda p:(p/'compile_26933_shaders.sh').unlink(), 'missing real GLSL/SPIR-V compiler')
 negative(lambda p:(p/'26933_EXPECTED_ACTION_EXECUTABLES.txt').write_text('gradlew\n'), 'unlisted/unused Actions executable references')
 negative(lambda p:(p/'.github/workflows/build-26933-change-aware.yml').write_text('name: stale\n'), 'truncated workflow / absent Android compilation')
 def extra(p):
  f=p/'handoff_payload_26933/app/src/main/java/com/hinnka/mycamera/processor/UnexpectedBOffTouch.java'
  f.parent.mkdir(parents=True,exist_ok=True);f.write_text('NO')
 negative(extra,'unexpected protected source addition')
 negative(lambda p:(p/'26933_EXPECTED_FULL_APP.sha256').write_text('0'*64+'  app/version.properties\n'), 'malformed/short full-source manifest')
 # Independently prove reserved GLSL parser would fail even with a re-sealed
 # manifest: test the actual shader, not only the package source hash checker.
 with tempfile.TemporaryDirectory(prefix='26933_glsl_coherent_') as td:
  t=Path(td);q=t/sample;q.parent.mkdir(parents=True,exist_ok=True)
  q.write_text((R/sample).read_text().replace('float sensorApproach=', 'float coherent = 0.0;\n            float sensorApproach=',1))
  for name in ('test_26933_shader_contract.py','build_26933_incremental.py'):
   shutil.copy2(R/name,t/name)
  # The checker depends only on shader source; build import does not invoke seal.
  x=subprocess.run([sys.executable,'-S','test_26933_shader_contract.py'],cwd=t,capture_output=True,text=True)
  if x.returncode==0 or 'coherent' not in x.stderr:fail('GLSL coherent keyword erroneously allowed')
 print('PASS six sealed fail-closed tests + explicit reserved GLSL keyword executable parser rejection')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
