#!/usr/bin/env python3
"""Actual sealed handoff mutation replay; 12 cases must fail closed."""
from pathlib import Path
import shutil,subprocess,sys,tempfile
from build_26937_incremental import R,scope,fail

def copy_package(dst):
 paths=[line.split('  ',1)[1] for line in (R/'26937_HANDOFF_HASHES.sha256').read_text().splitlines()]
 paths.append('26937_HANDOFF_HASHES.sha256')
 for rel in paths:
  s=R/rel;t=dst/rel;t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s,t)

def reject(name,mutator):
 with tempfile.TemporaryDirectory(prefix='26937_neg_') as d:
  t=Path(d);copy_package(t);mutator(t)
  p=subprocess.run([sys.executable,'-S','build_26937_incremental.py','seal','--package-only'],cwd=t,text=True,capture_output=True,timeout=60)
  if p.returncode==0 or '26937 BLOCKED:' not in p.stderr:fail('negative was accepted '+name+' '+p.stderr[-500:])
  print('PASS fail-closed',name)

def main():
 changed,added,old,new=scope()
 if len(changed)!=4 or added:fail('scope changed from protected four sources')
 target='handoff_payload_26937/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt'
 def corrupt(root,filename):
  f=root/filename;f.write_bytes(f.read_bytes()+b'\n// silent wrong bytes')
 reject('modified actual median GLSL',lambda r:corrupt(r,target))
 reject('missing pinned glslang command',lambda r:(r/'compile_26937_shaders.sh').unlink())
 reject('missing authentic successful 26936 LKR restore',lambda r:(r/'prepare_26937_lkr_from_successful_26936.py').unlink())
 reject('missing owner regression',lambda r:(r/'test_26937_source.py').unlink())
 reject('missing highlight math regression',lambda r:(r/'test_26937_highlight_math.py').unlink())
 reject('modified protected source manifest',lambda r:(r/'26937_PROTECTED_SOURCE.sha256').write_text('0'*64+'  app/build.gradle\n'))
 reject('wrong source allowlist',lambda r:(r/'26937_CHANGED_RUNTIME_ALLOWLIST.txt').write_text('app/version.properties\n'))
 reject('truncated actual Actions workflow',lambda r:(r/'.github/workflows/build-26937-change-aware.yml').write_text('name: incomplete\n'))
 reject('mutated Stage3 trigger',lambda r:corrupt(r,'TRIGGER_26937.txt'))
 reject('lost executable reference',lambda r:(r/'26937_EXPECTED_ACTION_EXECUTABLES.txt').write_text('gradlew\n'))
 reject('tampered full-index rollback',lambda r:(r/'26937_ROLLBACK_FULLINDEX.patch').write_text('diff --git a/stale b/stale\n'))
 reject('tampered handoff digest',lambda r:(r/'26937_HANDOFF_HASHES.sha256').write_text('0'*64+'  '+target+'\n'))
 print('PASS 12 actual 26937 package mutation rejects')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
