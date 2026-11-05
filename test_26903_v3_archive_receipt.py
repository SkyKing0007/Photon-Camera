#!/usr/bin/env python3
"""Execute the COMPLETE ORIGINAL archival CLI (V2 failure reproduction) and
V3 narrow fix against an actual TAR/manifest/receipt and negative mutations.
Compiler/Actions evidence in THIS isolated test is simulated: NOT compile proof.
"""
import hashlib,os,pathlib,shutil,subprocess,sys,tarfile,tempfile
R=pathlib.Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
RUNSHA='a5e9b4923325a13d3ab54fbfe233f3fca0d79b3a6f43ae194fa5edcb1ab67b44'
RUNNER='build_26903_iris_rawr.sh'
withrunner=sys.argv[1:]==['--runner']
assert sys.argv[1:] in ([],['--runner'])
ENV={**os.environ,'GITHUB_JOB':'build','GITHUB_RUN_ID':'42034102654','GITHUB_SHA':'a8c121fc4ee9f72ee82f0c5dafc6c1652493ffc8','GITHUB_REF_NAME':'experimental-clean-photon-rebuild'}
with tempfile.TemporaryDirectory(prefix='p26903_v3_exact_archive_postbuild_') as td:
 T=pathlib.Path(td);O=T/'build_26903_iris_rawr_outputs';O.mkdir()
 if withrunner:
  assert (R/RUNNER).is_file() and H(R/RUNNER)==RUNSHA
  shutil.copyfile(R/RUNNER,T/RUNNER)
  expected=RUNSHA
 else:
  (T/RUNNER).write_text('#!/bin/bash\nset -euo pipefail\necho archival-fixture-runner\n')
  expected=H(T/RUNNER)
 (T/'26903_V3_GENERATED_BUILD_SHA256.txt').write_text(f'{expected}  {RUNNER}\n')
 shutil.copyfile(R/'26903_GENERATED_BUILD_SHA256.txt',T/'26903_GENERATED_BUILD_SHA256.txt')
 shutil.copyfile(R/'26903_V2_GENERATED_BUILD_SHA256.txt',T/'26903_V2_GENERATED_BUILD_SHA256.txt')
 with tarfile.open(O/'26903_candidate_app_source.tar.gz','w:gz') as tar:
  for name,data in [('app/version.properties',b'VERSION_BUILD=26903\n'),('app/src/main/AndroidManifest.xml',b'<manifest />\n')]:
   f=T/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data)
   tar.add(f,arcname=name)
 (O/'26903_candidate_full_app.sha256').write_text(''.join(f'{H(T/f)}  {f}\n' for f in ('app/version.properties','app/src/main/AndroidManifest.xml')))
 archive=O/'26903_candidate_app_source.tar.gz'; tarsha=H(archive)
 (O/'26903_candidate_app_source.tar.gz.sha256').write_text(f'{tarsha}  {archive}\n')
 comp='\n'.join(x+': PASS' for x in ('REAL GLSL COMPILE','REAL SPIR-V VALIDATION','REAL KOTLIN COMPILE','REAL JAVA COMPILE','NATIVE/NDK COMPILE','FULL ANDROID ASSEMBLE','POST-BUILD INVARIANCE'))+'\n'
 (O/'26903_COMPILER_STATUS.txt').write_text(comp)
 (O/'26903_APK.sha256').write_text('a'*64+'  IrisCamera-0.9726903-26903-iris-rawr-debug.apk\n')
 def run(helper='photon_preserve_26903_v3_runner.py',env=ENV,sha=expected):
  return subprocess.run([sys.executable,'-S',str(R/helper),'26903','--root',str(T),'--expected-sha256',sha],capture_output=True,text=True,env=env)
 original=run('photon_preserve_successful_runner.py')
 assert original.returncode and 'generated runner SHA receipt does not pin the exact executed runner' in original.stderr,('V2 original fails',original.stderr)
 p=run();assert p.returncode==0,(p.stdout,p.stderr)
 ex=O/'exact_generated_runner'
 assert (ex/RUNNER).read_bytes()==(T/RUNNER).read_bytes()
 assert (ex/'26903_V3_GENERATED_BUILD_SHA256.txt').read_bytes()==(T/'26903_V3_GENERATED_BUILD_SHA256.txt').read_bytes()
 assert (ex/'EXACT_EXECUTED_RUNNER.sha256').read_text()==f'{expected}  {RUNNER}\n'
 assert not (ex/'26903_GENERATED_BUILD_SHA256.txt').exists()
 assert not (ex/'26903_V2_GENERATED_BUILD_SHA256.txt').exists()
 print('PASS archival COMPLETE original V2 failure reproduced; COMPLETE corrected V3 archive/genuine extracted TAR/manifest/exact runner and V3 receipt positive', 'REAL_RUNNER' if withrunner else 'SMALL_FIXTURE')
 def mutate(label,path,value=None,missing=False,symlink=False):
  backup=path.with_name(path.name+'.mutate-backup')
  assert not backup.exists()
  path.rename(backup)
  try:
   if value is not None:path.write_bytes(value)
   if symlink:path.symlink_to(backup)
   p=run()
   assert p.returncode!=0,(label,p.stdout,p.stderr)
  finally:
   if path.exists() or path.is_symlink():path.unlink()
   backup.rename(path)
 mutate('V3 generated receipt missing',T/'26903_V3_GENERATED_BUILD_SHA256.txt',missing=True)
 mutate('V3 generated receipt SHA incorrect',T/'26903_V3_GENERATED_BUILD_SHA256.txt',value=('0'*64+'  '+RUNNER+'\n').encode())
 mutate('V3 runner tampered',T/RUNNER,value=b'#!/bin/bash\necho CORRUPTED\n')
 mutate('V3 runner symlinked',T/RUNNER,symlink=True)
 mutate('V3 compiled TAR missing',archive,missing=True)
 mutate('V3 compiled TAR corrupt',archive,value=b'CORRUPTED compressed source')
 mutate('V3 compiled TAR receipt digest corrupt',O/'26903_candidate_app_source.tar.gz.sha256',value=('0'*64+'  '+str(archive)+'\n').encode())
 mutate('V3 compiled manifest corrupt',O/'26903_candidate_full_app.sha256',value=('0'*64+'  app/version.properties\n').encode())
 mutate('V3 compiler status missing',O/'26903_COMPILER_STATUS.txt',missing=True)
 mutate('V3 no real compiler evidence',O/'26903_COMPILER_STATUS.txt',value=b'REAL GLSL COMPILE: NOT RUN\n')
 mutate('V3 empty APK receipt',O/'26903_APK.sha256',value=b'')
 assert run(env={**ENV,'GITHUB_REF_NAME':'dev'}).returncode!=0
 assert run(env={**ENV,'GITHUB_RUN_ID':'invalid'}).returncode!=0
 assert run(sha='0'*64).returncode!=0
 assert run().returncode==0
 print('PASS V3 exact original full archiver checks + 14 negative bad-receipt/tar/runner/compiler/metadata cases and recovery; simulated fixture not Android compile')
