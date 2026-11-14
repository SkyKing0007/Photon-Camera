#!/usr/bin/env python3
"""Real fail-closed corruption/absence/extra/invalid executable regression on isolated sealed package copies.
No Android build, no repository mutation, no hidden dynamic mocks.
"""
from pathlib import Path
import hashlib,sys,subprocess,tempfile,shutil
from build_26932_incremental import R,scope,sha,fail

def attempt(mutator,label):
 with tempfile.TemporaryDirectory(prefix='26932_negative_') as td:
  root=Path(td)
  paths=[line.split('  ',1)[1] for line in (R/'26932_HANDOFF_HASHES.sha256').read_text().splitlines()]
  paths+=['26932_HANDOFF_HASHES.sha256']
  for rel in paths:
   src=R/rel;dst=root/rel
   dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
  mutator(root)
  r=subprocess.run([sys.executable,'-S','build_26932_incremental.py','seal','--package-only'],cwd=root,capture_output=True,text=True,timeout=120)
  if r.returncode==0:fail('NEGATIVE TEST ACCEPTED '+label)
  if '26932 BLOCKED:' not in r.stderr:fail('NEGATIVE TEST DID NOT FAIL CLOSED '+label+' '+r.stderr[-500:])
  print('PASS fail closed '+label)

def main():
 changed,added,base,new=scope()
 if len(base)!=2046 or len(new)!=2048 or len(changed)!=7 or len(added)!=2:fail('unexpected scope in negative tests')
 for p in changed|added:
  source=R/'handoff_payload_26932'/p;body=source.read_bytes()
  if sha(source)!=new[p] or hashlib.sha256(body+b'\0').hexdigest()==new[p]:fail('tamper hash acceptance '+p)
 for req in ('test_26932_source.py','compile_26932_shaders.sh','test_26932_shader_contract.py',
   'test_26932_workflow_refs.py','test_26932_math.py','test_26932_patch_proof.py'):
  if not (R/req).is_file():fail('mandatory verifier missing '+req)
 sample='handoff_payload_26932/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt'
 attempt(lambda d:(d/sample).write_bytes((d/sample).read_bytes()+b'\n// corrupt'), 'corrupted live shader source')
 attempt(lambda d:(d/'compile_26932_shaders.sh').unlink(), 'missing real GLSL compiler')
 attempt(lambda d:(d/'26932_EXPECTED_ACTION_EXECUTABLES.txt').write_text('gradlew\n'), 'missing/unused executable graph')
 attempt(lambda d:(d/'.github/workflows/build-26932-change-aware.yml').write_text('name: fake\n'), 'missing workflow compilers')
 def extra(d):
  p=d/'handoff_payload_26932/app/src/main/java/com/hinnka/mycamera/processor/UnexpectedNative.java'
  p.parent.mkdir(parents=True,exist_ok=True);p.write_text('UNLISTED')
 attempt(extra,'unlisted source addition')
 attempt(lambda d:(d/'26932_EXPECTED_FULL_APP.sha256').write_text('0'*64+'  app/version.properties\n'), 'malformed or short source manifest')
 print('PASS 26932 six executable negative tests, historical source scope and current all-file hash protection')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
