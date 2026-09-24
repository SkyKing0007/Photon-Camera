#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
if len(sys.argv)!=4:raise SystemExit('usage: repair_26698_patches.py ROOT BASE26697 CANDIDATE')
base=Path(sys.argv[2]);cand=Path(sys.argv[3]);pkg=Path(__file__).resolve().parent;f=pkg/'26698_RUNTIME_DELTA_FROM_26697.patch';r=pkg/'26698_RUNTIME_ROLLBACK_TO_26697.patch'
def H(x):return {str(p.relative_to(x)):hashlib.sha256(p.read_bytes()).hexdigest() for p in x.rglob('*') if p.is_file() and '.git' not in p.parts}
BH=H(base);CH=H(cand)
with tempfile.TemporaryDirectory(prefix='i26698_') as td:
 d=Path(td);repo=d/'repo';shutil.copytree(base/'app',repo/'app');subprocess.run(['git','init','-q'],cwd=repo,check=True);subprocess.run(['git','config','user.email','proof@iris.local'],cwd=repo,check=True);subprocess.run(['git','config','user.name','Iris Proof'],cwd=repo,check=True);subprocess.run(['git','add','-f','app'],cwd=repo,check=True);subprocess.run(['git','commit','-qm','base'],cwd=repo,check=True)
 # canonical patches generated at multiple abbrev settings must be byte-identical
 generated=[]
 shutil.rmtree(repo/'app');shutil.copytree(cand/'app',repo/'app');subprocess.run(['git','add','-f','app'],cwd=repo,check=True)
 for ab in ('7','12','40'):
  data=subprocess.check_output(['git','-c',f'core.abbrev={ab}','diff','--cached','--binary','--full-index','--no-ext-diff','HEAD','--','app'],cwd=repo);generated.append(data)
 assert generated[0]==generated[1]==generated[2] and generated[0]==f.read_bytes()
 subprocess.run(['git','commit','-qm','candidate'],cwd=repo,check=True)
 backs=[]
 for ab in ('7','12','40'):
  data=subprocess.check_output(['git','-c',f'core.abbrev={ab}','diff','HEAD','HEAD^','--binary','--full-index','--no-ext-diff','--','app'],cwd=repo);backs.append(data)
 assert backs[0]==backs[1]==backs[2] and backs[0]==r.read_bytes()
 # fresh replay + exact rollback, git apply has no fuzz mode
 replay=d/'replay';shutil.copytree(base/'app',replay/'app');subprocess.run(['git','init','-q'],cwd=replay,check=True);subprocess.run(['git','config','user.email','proof@iris.local'],cwd=replay,check=True);subprocess.run(['git','config','user.name','Iris Proof'],cwd=replay,check=True);subprocess.run(['git','add','-f','app'],cwd=replay,check=True);subprocess.run(['git','commit','-qm','base'],cwd=replay,check=True)
 subprocess.run(['git','apply','--check',str(f)],cwd=replay,check=True);subprocess.run(['git','apply',str(f)],cwd=replay,check=True);assert H(replay)==CH
 subprocess.run(['git','apply','--check',str(r)],cwd=replay,check=True);subprocess.run(['git','apply',str(r)],cwd=replay,check=True);assert H(replay)==BH
print('PASS 26698 deterministic full-index forward/rollback patches at core.abbrev 7/12/40; exact replay + rollback')
