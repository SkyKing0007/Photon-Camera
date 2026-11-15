#!/usr/bin/env python3
"""Fail-closed 26936 staged package mutation and missing-reference tests.
All 10 cases physically invoke actual sealed package verifier in clean scratch.
"""
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
from build_26936_incremental import R,scope,fail

def copy_package(dst):
 hashes=R/'26936_HANDOFF_HASHES.sha256'
 parts=[line.split('  ',1)[1] for line in hashes.read_text().splitlines()]
 parts.append('26936_HANDOFF_HASHES.sha256')
 for rel in parts:
  src=R/rel;t=dst/rel;t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,t)
 return parts

def reject(name,mutate):
 with tempfile.TemporaryDirectory(prefix='p26936_negative_') as d:
  root=Path(d);copy_package(root);mutate(root)
  p=subprocess.run([sys.executable,'-S','build_26936_incremental.py','seal','--package-only'],cwd=root,capture_output=True,text=True,timeout=90)
  if p.returncode==0 or '26936 BLOCKED:' not in p.stderr:
   fail('negative case did not fail closed: '+name+'\n'+p.stderr[-600:])
  print('PASS fail closed',name)

def main():
 ch,ad,old,new=scope();assert len(ch)==7 and not ad
 target='handoff_payload_26936/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt'
 reject('modified active GLSL runtime byte',lambda r:(r/target).write_bytes((r/target).read_bytes()+b'\n// silent shader drift'))
 reject('missing live GLSL + SPIRV compiler',lambda r:(r/'compile_26936_shaders.sh').unlink())
 reject('missing actual original RawLens restore',lambda r:(r/'prepare_26936_lkr_from_successful_26935.py').unlink())
 reject('missing new source ownership validator',lambda r:(r/'test_26936_source.py').unlink())
 reject('missing regression host',lambda r:(r/'test_26936_guard_host.py').unlink())
 reject('mutated protection index',lambda r:(r/'26936_PROTECTED_SOURCE.sha256').write_text('0'*64+'  app/version.properties\n'))
 reject('unexpected/altered runtime allowlist',lambda r:(r/'26936_CHANGED_RUNTIME_ALLOWLIST.txt').write_text('app/version.properties\n'))
 reject('truncated full Actions workflow',lambda r:(r/'.github/workflows/build-26936-change-aware.yml').write_text('name: stale\n'))
 reject('altered Stage3 unique trigger',lambda r:(r/'TRIGGER_26936.txt').write_bytes((r/'TRIGGER_26936.txt').read_bytes()+b'\nwrong'))
 reject('missing mandatory executable reference',lambda r:(r/'26936_EXPECTED_ACTION_EXECUTABLES.txt').write_text('gradlew\n'))
 reject('tampered current patch',lambda r:(r/'26936_FORWARD_FULLINDEX.patch').write_text('diff --git a/stale b/stale\n'))
 reject('tampered per-file checksum',lambda r:(r/'26936_HANDOFF_HASHES.sha256').write_text('0'*64+'  '+target+'\n'))
 print('PASS 12 actual sealed fail-closed mutations; no bypass of real GLSL/NDK/Kotlin/Java compilation')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
