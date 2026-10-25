#!/usr/bin/env python3
"""Deterministic 7/12/40 full-index exact full-universe forward/rollback, zero fuzz."""
from pathlib import Path
import tempfile,subprocess,hashlib,shutil,sys
P=Path(__file__).resolve().parent;B=Path(sys.argv[1]);C=Path(sys.argv[2]);forward=P/'26879_FORWARD_FULL_INDEX.patch';rollback=P/'26879_ROLLBACK_FULL_INDEX.patch'
if len(sys.argv)>=5:forward=Path(sys.argv[3]);rollback=Path(sys.argv[4])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def entries(name):return {x:d for d,x in [l.split('  ',1) for l in (P/name).read_text().splitlines()]}
prior=entries('26879_BASE_26878_FULL_APP.sha256');latest=entries('26879_EXPECTED_CANDIDATE_FULL_APP.sha256')
assert len(prior)==len(latest)==2001
for p in (forward,rollback):
 assert p.is_file() and b'index ' in p.read_bytes(),('missing full-index patch',p)
 assert not any(x in p.read_text(errors='replace') for x in ('rename from ','rename to ','copy from ','copy to '))
for n in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'26879_real_full_index_{n}_') as tmp:
  root=Path(tmp);shutil.copytree(B/'app',root/'app');subprocess.run(['git','init','-q'],cwd=root,check=True)
  for p,expect in [(forward,latest),(rollback,prior)]:
   for check in (True,False):
    cmd=['git','-c',f'core.abbrev={n}','apply','--whitespace=nowarn']
    if check:cmd.append('--check')
    cmd.append(str(p.resolve()))
    result=subprocess.run(cmd,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    assert result.returncode==0,('git patch fuzz=0 failed',n,p,result.stderr.decode()[-1000:])
   found={'app/'+f.relative_to(root/'app').as_posix() for f in (root/'app').rglob('*') if f.is_file()}
   assert found==set(expect),(n,p,'extra/missing source')
   for name,d in expect.items():assert sha(root/name)==d,(n,p,name)
print('PASS 26879 full-index deterministic forward/rollback at core.abbrev 7/12/40 with zero fuzz and 2001 exact byte hashes')
