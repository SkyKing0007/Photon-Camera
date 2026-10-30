#!/usr/bin/env python3
"""26889 candidate-FIRST exact successful 26888 source/manifest/allowlist verifier."""
import hashlib,pathlib,sys,re,shutil
from typing import Dict
ROOT=pathlib.Path(__file__).resolve().parent
assert len(sys.argv) in (3,4), 'USAGE base-root candidate-root [--transform]'
BASE=pathlib.Path(sys.argv[1]);CAND=pathlib.Path(sys.argv[2])
if len(sys.argv)==4:
 assert sys.argv[3]=='--transform'
 assert BASE.resolve()!=CAND.resolve()
 assert not CAND.exists(),'candidate must be new: refuse stale overlay'
 shutil.copytree(BASE,CAND)
 for src in (ROOT/'handoff_payload_26889').rglob('*'):
  if src.is_file():
   dest=CAND/'app'/src.relative_to(ROOT/'handoff_payload_26889')
   dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)

def scan(p):
 return {str(x.relative_to(p)):hashlib.sha256(x.read_bytes()).hexdigest() for x in p.rglob('*') if x.is_file()}
def load(p):
 d={}
 for l in p.read_text().splitlines():
  h,n=l.split('  ',1);assert re.fullmatch('[0-9a-f]{64}',h) and n not in d
  d[n]=h
 return d
A=scan(BASE);B=scan(CAND)
wantA=load(ROOT/'26889_BASE_FULL_APP.sha256');wantB=load(ROOT/'26889_EXPECTED_CANDIDATE_FULL_APP.sha256')
assert A==wantA and B==wantB,(len(A),len(B),'authority/candidate SHA mismatch')
add=set(B)-set(A);delete=set(A)-set(B);mod={n for n in A.keys()&B.keys() if A[n]!=B[n]}
allow=set((ROOT/'26889_CHANGED_ALLOWLIST.txt').read_text().splitlines())
assert add|mod|delete==allow and len(A)==2024 and len(B)==2025 and len(add)==1 and len(mod)==9 and not delete
protected=load(ROOT/'26889_UNCHANGED_PROTECTED.sha256')
assert len(protected)==2015 and all(A[n]==B[n]==h for n,h in protected.items())
assert (CAND/'app/version.properties').read_text().endswith('VERSION_BUILD=26889\n')
assert 'VERSION_NAME=0.9726889' in (CAND/'app/version.properties').read_text()
print('PASS 26889 2024 authority/2025 candidate nine modifications one B-OFF add protected=2015 exact')
