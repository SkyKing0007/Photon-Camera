#!/usr/bin/env python3
"""Full-index, deterministic forward+rollback proof, source SHA at 7/12/40."""
from pathlib import Path
import argparse,subprocess,tempfile,hashlib,shutil,re
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');args=p.parse_args()
paths=(R/'26963_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
assert len(paths)==4
base={p:h for h,p in (l.split('  ',1) for l in (R/'26963_BASE_26962_FULL_APP.sha256').read_text().splitlines())}
after={p:h for h,p in (l.split('  ',1) for l in (R/'26963_EXPECTED_FULL_APP.sha256').read_text().splitlines())}
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
for name in ('26963_FORWARD_FULLINDEX.patch','26963_ROLLBACK_FULLINDEX.patch'):
 s=(R/name).read_text();heads=re.findall(r'^diff --git a/(.+?) b/(.+?)$',s,re.M)
 assert len(heads)==4 and {x for x,y in heads}==set(paths) and all(x==y for x,y in heads)
 assert len(re.findall(r'^index [a-f0-9]{40}\.\.[a-f0-9]{40}',s,re.M))==4
for abbrev in (7,12,40):
 with tempfile.TemporaryDirectory(prefix='26963_patch_') as d:
  temp=Path(d)
  def git(*commands):
   a=subprocess.run(['git','-C',str(temp),'-c',f'core.abbrev={abbrev}',*commands],capture_output=True,text=True)
   assert a.returncode==0,(commands,a.stdout,a.stderr)
  git('init','-q');git('config','user.email','proof@invalid.example');git('config','user.name','Patch Proof')
  src=R/'.photon_26963_work/authority_26962' if args.live else None
  if src is None:
   # Static metadata and staged hashes only; actual compiled prior source is required for live replay.
   for path in paths:assert sha(R/'handoff_payload_26963'/path)==after[path]
   break
  assert src.is_dir()
  for path in paths:
   f=temp/path;f.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src/path,f)
  git('add','-f','--',*paths);git('commit','-qm','26962 exact authority source')
  git('apply','--check',str(R/'26963_FORWARD_FULLINDEX.patch'))
  git('apply',str(R/'26963_FORWARD_FULLINDEX.patch'))
  assert all(sha(temp/path)==after[path] for path in paths)
  git('apply','--check',str(R/'26963_ROLLBACK_FULLINDEX.patch'))
  git('apply',str(R/'26963_ROLLBACK_FULLINDEX.patch'))
  assert all(sha(temp/path)==base[path] for path in paths)
  cand=R/'.photon_26963_work/candidate_26963'
  assert all(sha(cand/path)==after[path] for path in paths)
print('PASS full-index exact forward+rollback SHA at core.abbrev 7,12,40' if args.live else 'PASS four full-index patch metadata and payload hashes; live replay gated on recovered 26962 source')
