#!/usr/bin/env python3
"""Verify exact deterministic full-index forward and rollback, 7/12/40 abbreviated index."""
from pathlib import Path
import argparse,hashlib,re,subprocess,tempfile
R=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--payload',action='store_true');ap.add_argument('--live',action='store_true');args=ap.parse_args()
def parse(name):
 return {p:h for h,p in (line.split('  ',1) for line in (R/name).read_text().splitlines())}
a=parse('26965_BASE_26964_FULL_APP.sha256');b=parse('26965_EXPECTED_FULL_APP.sha256')
changed=set((R/'26965_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
assert len(changed)==4
forward=(R/'26965_FORWARD_FULLINDEX.patch').read_text()
reverse=(R/'26965_ROLLBACK_FULLINDEX.patch').read_text()
assert len(re.findall(r'(?m)^diff --git ',forward))==len(changed)
assert len(re.findall(r'(?m)^diff --git ',reverse))==len(changed)
assert len(re.findall(r'(?m)^index [0-9a-f]{40}\.\.[0-9a-f]{40} 100644$',forward))==len(changed)
def shortened(s,n):
 return re.sub(r'(?m)^(index )([0-9a-f]{40})\.\.([0-9a-f]{40})( 100644)$',lambda m:m[1]+m[2][:n]+'..'+m[3][:n]+m[4],s)
def cmd(args,cwd,patch):
 return subprocess.run(['git','apply',*args,'-'],input=patch,text=True,cwd=cwd,capture_output=True)
for n in (7,12,40):
 with tempfile.TemporaryDirectory(prefix='photon26965_patch_') as td:
  root=Path(td)
  for rel in changed:
   p=root/rel;p.parent.mkdir(parents=True,exist_ok=True)
   data=(R/'handoff_payload_26965'/rel).read_bytes()
   assert hashlib.sha256(data).hexdigest()==b[rel]
   p.write_bytes(data)
  pR=shortened(reverse,n);pF=shortened(forward,n)
  assert cmd(['--check'],root,pR).returncode==0
  z=cmd([],root,pR);assert z.returncode==0,z.stderr
  for rel in changed:assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==a[rel],(n,rel)
  assert cmd(['--check'],root,pF).returncode==0
  z=cmd([],root,pF);assert z.returncode==0,z.stderr
  for rel in changed:assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==b[rel],(n,rel)
  assert cmd(['--check'],root,pF).returncode!=0 # must reject double application
print('PASS 26965 7/12/40 full-index forward/rollback, exact source hashes, duplicate rejection')
