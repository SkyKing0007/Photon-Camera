#!/usr/bin/env python3
"""Actual full-index forward and reverse proof at 7/12/40 abbreviations; fuzz=0."""
from pathlib import Path
import argparse,re,tempfile,subprocess,hashlib,shutil
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');args=p.parse_args()
changed=(R/'26964_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
base={p:h for h,p in [line.split('  ',1) for line in (R/'26964_BASE_26963_FULL_APP.sha256').read_text().splitlines()]}
after={p:h for h,p in [line.split('  ',1) for line in (R/'26964_EXPECTED_FULL_APP.sha256').read_text().splitlines()]}
for fname in ('26964_FORWARD_FULLINDEX.patch','26964_ROLLBACK_FULLINDEX.patch'):
 text=(R/fname).read_text()
 headers=re.findall(r'^diff --git [ab]/(.+?) [ab]/(.+?)$',text,re.M)
 assert len(headers)==4 and {x for x,y in headers}==set(changed) and all(x==y for x,y in headers)
 assert len(re.findall(r'^index [0-9a-f]{40}\.\.[0-9a-f]{40}',text,re.M))==4
if args.live:
 root=R/'.photon_26964_work/authority_26963';cand=R/'.photon_26964_work/candidate_26964'
 assert root.is_dir() and cand.is_dir()
 for abbrev in (7,12,40):
  with tempfile.TemporaryDirectory(prefix=f'26964_git_{abbrev}_') as t:
   T=Path(t)
   def git(*cmd):
    run=subprocess.run(['git','-C',t,'-c',f'core.abbrev={abbrev}',*cmd],capture_output=True,text=True)
    if run.returncode:raise AssertionError(f'git {cmd}: {run.stderr}')
   git('init','-q');git('config','user.email','proof@example.invalid');git('config','user.name','Patch Proof')
   for rel in changed:
    dst=T/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/rel,dst)
   git('add','-f',*changed);git('commit','-qm','verified 26963')
   git('apply','--check',str(R/'26964_FORWARD_FULLINDEX.patch'))
   git('apply',str(R/'26964_FORWARD_FULLINDEX.patch'))
   assert all(hashlib.sha256((T/x).read_bytes()).hexdigest()==after[x] for x in changed)
   git('apply','--check',str(R/'26964_ROLLBACK_FULLINDEX.patch'))
   git('apply',str(R/'26964_ROLLBACK_FULLINDEX.patch'))
   assert all(hashlib.sha256((T/x).read_bytes()).hexdigest()==base[x] for x in changed)
   assert all(hashlib.sha256((cand/x).read_bytes()).hexdigest()==after[x] for x in changed)
 print('PASS exact 26964 reversible git patches and source hash proof core.abbrev=7/12/40')
else:print('PASS 26964 4-file full-index patch metadata; guarded live apply on actual source in Actions')
