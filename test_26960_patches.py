#!/usr/bin/env python3
"""Full-index deterministic bidirectional Git apply proof, core.abbrev 7/12/40, no fuzzy source."""
import argparse,pathlib,re,hashlib,subprocess,tempfile,shutil
R=pathlib.Path(__file__).resolve().parent
changed=(R/'26960_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
base={p:h for h,p in (line.split('  ',1) for line in (R/'26960_BASE_26959_FULL_APP.sha256').read_text().splitlines())}
after={p:h for h,p in (line.split('  ',1) for line in (R/'26960_EXPECTED_FULL_APP.sha256').read_text().splitlines())}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p):
 text=(R/p).read_text();
 headers=re.findall(r'^diff --git [ab]/(.+?) [ab]/(.+?)$',text,re.M)
 assert len(headers)==7 and {p for p,q in headers}==set(changed) and all(p==q for p,q in headers)
 assert len(re.findall(r'^index ',text,re.M))==7 and all(re.search(r'index [0-9a-f]{40}\.\.[0-9a-f]{40}',part) for part in text.split('diff --git ')[1:])
 return text
f=lines('26960_FORWARD_FULLINDEX.patch');b=lines('26960_ROLLBACK_FULLINDEX.patch')
def prove():
 root=R/'.photon_26960_work/authority_26959';candidate=R/'.photon_26960_work/candidate_26960'
 assert root.is_dir() and candidate.is_dir()
 for abbrev in (7,12,40):
  with tempfile.TemporaryDirectory(prefix=f'26960_git{abbrev}_') as temp:
   temp=pathlib.Path(temp)
   def git(*cmd,success=True):
    c=subprocess.run(['git','-C',str(temp),'-c',f'core.abbrev={abbrev}',*cmd],capture_output=True,text=True)
    if success and c.returncode:raise RuntimeError(f'git {cmd} failed: {c.stderr}')
    return c
   git('init','-q');git('config','user.email','proof@example.invalid');git('config','user.name','Patch Proof')
   for rel in changed:
    dst=temp/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/rel,dst)
   git('add','-A');git('commit','-qm','26959 exact compiled changed files')
   git('apply','--check',str(R/'26960_FORWARD_FULLINDEX.patch'))
   git('apply',str(R/'26960_FORWARD_FULLINDEX.patch'))
   assert all(sha(temp/rel)==after[rel] for rel in changed)
   git('apply','--check',str(R/'26960_ROLLBACK_FULLINDEX.patch'))
   git('apply',str(R/'26960_ROLLBACK_FULLINDEX.patch'))
   assert all(sha(temp/rel)==base[rel] for rel in changed)
   for rel in changed:
    assert sha(candidate/rel)==after[rel]
 print('PASS full-index patches exact forward/rollback SHA core.abbrev=7,12,40')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');args=p.parse_args()
 if args.live:prove()
 else:print('PASS full-index exact 7-file patch metadata; live apply follows reconstructed actual 26959 TAR')
