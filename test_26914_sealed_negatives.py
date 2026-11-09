#!/usr/bin/env python3
"""Exercise exact 26914 real stage inventory and fail-closed mutations, without stubs.
Uses the production handoff verifier and real builder seal from an isolated copy.
"""
from pathlib import Path
import tempfile,shutil,subprocess,sys,hashlib
R=Path(__file__).resolve().parent
EXCLUDED={'.photon_26914_work','photon_26914_outputs','__pycache__','app'}
def run():
 stage=(R/'26914_STAGE1_PATHS.txt').read_text().splitlines()+['.github/workflows/build-26914-change-aware.yml','TRIGGER_26914.txt']
 assert all((R/p).is_file() for p in stage)
 with tempfile.TemporaryDirectory(prefix='26914_negative_') as d:
  base=Path(d)/'stage';base.mkdir()
  for p in stage:
   target=base/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/p,target)
  def verify(root,expected,only_verifier=False):
   commands=[['python3','-S','verify_26914_handoff.py'],['python3','-S','build_26914_incremental.py','seal']]
   for command in (commands[:1] if only_verifier else commands):
    result=subprocess.run(command,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if expected:
     assert result.returncode==0,(command,result.stderr.decode()[:500])
    else:
     assert result.returncode!=0,('unsafe mutation accepted',command)
  verify(base,True)
  mutations=[
   ('alter APK and builder compiler controls','build_26914_incremental.py',b':app:assembleDebug',b':app:assembleRelease'),
   ('alter actual builder prior artifact','build_26914_incremental.py',b'ART_ID=13642374414',b'ART_ID=13642374415'),
   ('alter actual runner snapshot SHA','build_26914_incremental.py',b'8ebd0be6412264bca09cacd530dca2b5f31e382252a73ee5af2b2ef3dbfc7c78',b'0'*64),
   ('alter workflow independent trigger','.github/workflows/build-26914-change-aware.yml',b'TRIGGER_26914.txt',b'TRIGGER_26913.txt'),
   ('alter workflow native real compiler','.github/workflows/build-26914-change-aware.yml',b'compile_26904_shaders_v2.sh',b'compile_26904_shaders_no.sh'),
   ('alter release trigger','TRIGGER_26914.txt',b'RUN_26914_',b'RUN_26915_'),
   ('alter runtime scope','26914_CHANGED_RUNTIME_ALLOWLIST.txt',b'app/version.properties',b'app/something.properties'),
   ('alter successor compiled manifest','26914_PRECOMPILE_EXPECTED_FULL_APP.sha256',b'app/version.properties',b'app/version-corrupt.properties'),
   ('alter predecessor compiled manifest','26914_BASE_26913_FULL_APP.sha256',b'app/version.properties',b'app/version-corrupt.properties'),
   ('alter deletion list','26914_DELETED_RUNTIME_PATHS.txt',b'Iris26912PerLensHighlightSwitch.java',b'Iris26913PerLensHighlightSwitch.java'),
   ('alter source payload','handoff_payload_26914/app/version.properties',b'VERSION_BUILD=26914',b'VERSION_BUILD=26913'),
   ('alter stage1 inventory','26914_STAGE1_PATHS.txt',b'26914_BASE_26913_FULL_APP.sha256',b'26914_BASE_26912_FULL_APP.sha256'),
   ('alter sealed receipt','26914_HANDOFF_HASHES.sha256',b'26914_BASE_26913_FULL_APP.sha256',b'26914_BASE_26912_FULL_APP.sha256'),
   ('alter Java grammar test','tests_26914/SourceGrammar26914.java',b'SourceGrammar26914',b'SourceGrammar26913'),
  ]
  for label,path,old,new in mutations:
   target=base/path;clean=target.read_bytes();assert old in clean,label
   target.write_bytes(clean.replace(old,new,1));verify(base,False);target.write_bytes(clean)
  # Re-sealed malicious workflow (hostile actor also updates seal) must fail semantic checks.
  wf=base/'.github/workflows/build-26914-change-aware.yml';clean=wf.read_bytes()
  assert b'  workflow_dispatch:' in clean
  wf.write_bytes(clean.replace(b'  workflow_dispatch:',b'  pull_request:\n  workflow_dispatch:',1))
  seal=base/'26914_HANDOFF_HASHES.sha256';h=seal.read_text().splitlines()
  newsha=hashlib.sha256(wf.read_bytes()).hexdigest()
  seal.write_text('\n'.join(newsha+'  .github/workflows/build-26914-change-aware.yml' if line.endswith('  .github/workflows/build-26914-change-aware.yml') else line for line in h)+'\n')
  verify(base,False,only_verifier=True)
  # Fully re-sealed source tamper still fails explicit expected manifest equality.
  seal.write_text((R/'26914_HANDOFF_HASHES.sha256').read_text());wf.write_bytes(clean)
  payload=base/'handoff_payload_26914/app/version.properties';old=payload.read_bytes();payload.write_bytes(old.replace(b'VERSION_BUILD=26914',b'VERSION_BUILD=26999'))
  lines=seal.read_text().splitlines();newsha=hashlib.sha256(payload.read_bytes()).hexdigest()
  seal.write_text('\n'.join(newsha+'  handoff_payload_26914/app/version.properties' if line.endswith('  handoff_payload_26914/app/version.properties') else line for line in lines)+'\n')
  verify(base,False,only_verifier=True)
  print('PASS 26914 16 actual sealed-file hostile negative mutations (including re-sealed workflow and runtime source), production verifier (and runner seal for non-resealed mutations) fail closed')
if __name__=='__main__':
 try:run()
 except Exception as e:print('FAIL 26914 mutation suite',e,file=sys.stderr);sys.exit(1)
