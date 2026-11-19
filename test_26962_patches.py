#!/usr/bin/env python3
"""Strict Git full-index forward and rollback at core.abbrev=7,12,40; fuzz=0."""
from pathlib import Path
import argparse,hashlib,re,subprocess,shutil,tempfile
R=Path(__file__).resolve().parent
want=(R/'26962_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
base={p:h for h,p in (x.split('  ',1) for x in (R/'26962_BASE_26961_FULL_APP.sha256').read_text().splitlines())}
after={p:h for h,p in (x.split('  ',1) for x in (R/'26962_EXPECTED_FULL_APP.sha256').read_text().splitlines())}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def validate(name):
 s=(R/name).read_text();lines=re.findall(r'^diff --git a/(.+?) b/(.+?)$',s,re.M)
 assert len(lines)==len(want)==2 and set(x for x,y in lines)==set(want) and all(x==y for x,y in lines)
 assert len(re.findall('^index [0-9a-f]{40}\\.\\.[0-9a-f]{40}',s,re.M))==2
 return s
def check(live=False):
 validate('26962_FORWARD_FULLINDEX.patch');validate('26962_ROLLBACK_FULLINDEX.patch')
 # Test on real extracted base source for both directions and three different Git abbrev configurations.
 if live:
  root=R/'.photon_26962_work/authority_26961';cand=R/'.photon_26962_work/candidate_26962'
  assert root.is_dir() and cand.is_dir()
  for ab in (7,12,40):
   with tempfile.TemporaryDirectory(prefix=f'26962_git{ab}_') as tmp:
    p=Path(tmp)
    def git(*args):
     o=subprocess.run(['git','-C',str(p),'-c',f'core.abbrev={ab}',*args],capture_output=True,text=True)
     if o.returncode:raise AssertionError(f'git {args} failed {o.stderr}')
     return o.stdout
    git('init','-q');git('config','user.email','proof@example.invalid');git('config','user.name','Photon proof')
    for x in want:
     dst=p/x;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/x,dst)
    git('add','-f','--',*want);git('commit','-qm','authority')
    git('apply','--check',str(R/'26962_FORWARD_FULLINDEX.patch'))
    git('apply',str(R/'26962_FORWARD_FULLINDEX.patch'))
    assert all(sha(p/x)==after[x]==sha(cand/x) for x in want)
    git('apply','--check',str(R/'26962_ROLLBACK_FULLINDEX.patch'))
    git('apply',str(R/'26962_ROLLBACK_FULLINDEX.patch'))
    assert all(sha(p/x)==base[x] for x in want)
 print('PASS 26962 full-index source patch headers'+(' and exact forward/rollback core.abbrev 7/12/40' if live else '; live replay requires exact 26961 Actions source'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');x=p.parse_args();check(x.live)
