#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile,os
if len(sys.argv)!=4:raise SystemExit('usage: verify_26706_patches.py ROOT BASE26705 CANDIDATE')
base=Path(sys.argv[2]);cand=Path(sys.argv[3]);pkg=Path(__file__).resolve().parent;f=pkg/'26706_RUNTIME_DELTA_FROM_26705.patch';r=pkg/'26706_RUNTIME_ROLLBACK_TO_26705.patch'
def H(x):return {str(p.relative_to(x)):hashlib.sha256(p.read_bytes()).hexdigest() for p in x.rglob('*') if p.is_file() and '.git' not in p.parts}
def run(args,cwd,env=None,cap=False):return subprocess.check_output(args,cwd=cwd,env=env) if cap else subprocess.run(args,cwd=cwd,env=env,check=True,stdout=subprocess.DEVNULL)
BH=H(base);CH=H(cand)
with tempfile.TemporaryDirectory(prefix='i26706_') as td:
 d=Path(td);repo=d/'repo';shutil.copytree(base/'app',repo/'app');run(['git','init','-q'],repo);run(['git','config','user.email','proof@iris.local'],repo);run(['git','config','user.name','Iris Proof'],repo);run(['git','add','-f','app'],repo);env=os.environ.copy();env.update({'GIT_AUTHOR_DATE':'2000-01-01T00:00:00Z','GIT_COMMITTER_DATE':'2000-01-01T00:00:00Z'});run(['git','commit','-qm','base'],repo,env)
 shutil.rmtree(repo/'app');shutil.copytree(cand/'app',repo/'app');run(['git','add','-f','app'],repo)
 fw=[run(['git','-c',f'core.abbrev={ab}','diff','--cached','--binary','--full-index','--no-ext-diff','HEAD','--','app'],repo,cap=True) for ab in ('7','12','40')];assert fw[0]==fw[1]==fw[2]==f.read_bytes()
 run(['git','commit','-qm','candidate'],repo,env);rb=[run(['git','-c',f'core.abbrev={ab}','diff','HEAD','HEAD^','--binary','--full-index','--no-ext-diff','--','app'],repo,cap=True) for ab in ('7','12','40')];assert rb[0]==rb[1]==rb[2]==r.read_bytes()
 replay=d/'replay';shutil.copytree(base/'app',replay/'app');run(['git','init','-q'],replay);run(['git','config','user.email','proof@iris.local'],replay);run(['git','config','user.name','Iris Proof'],replay);run(['git','add','-f','app'],replay);run(['git','commit','-qm','base'],replay)
 run(['git','apply','--check',str(f)],replay);run(['git','apply',str(f)],replay);assert H(replay)==CH;run(['git','apply','--check',str(r)],replay);run(['git','apply',str(r)],replay);assert H(replay)==BH
print('PASS 26706 deterministic full-index forward/rollback patches at core.abbrev 7/12/40; fuzz=0 exact replay + rollback')
