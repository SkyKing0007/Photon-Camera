#!/usr/bin/env python3
"""Candidate-first 26890 from ACTUAL successful 26889 compiled TAR bytes."""
import hashlib,pathlib,sys,re,shutil
R=pathlib.Path(__file__).resolve().parent
assert len(sys.argv) in (3,4),'BASE CAND [--transform]'
B=pathlib.Path(sys.argv[1]);C=pathlib.Path(sys.argv[2]);assert B.resolve()!=C.resolve()
def load(f):
 d={}
 for ln in (R/f).read_text().splitlines():
  h,n=ln.split('  ',1);assert re.fullmatch('[a-f0-9]{64}',h) and n not in d
  d[n]=h
 return d
def scan(p):return {k.relative_to(p).as_posix():hashlib.sha256(k.read_bytes()).hexdigest() for k in (p/'app').rglob('*') if k.is_file()}
A=load('26890_BASE_FULL_APP.sha256');Z=load('26890_EXPECTED_CANDIDATE_FULL_APP.sha256');P=load('26890_UNCHANGED_PROTECTED.sha256')
assert len(A)==len(Z)==2025 and len(P)==2017
changed={k for k in A if A[k]!=Z.get(k)}
assert len(changed)==8 and set(A)==set(Z) and set(P)==set(A)-changed
assert (R/'26890_CHANGED_ALLOWLIST.txt').read_text().splitlines()==sorted(changed)
assert not (R/'26890_DELETIONS.txt').read_bytes()
if len(sys.argv)==4:
 assert sys.argv[3]=='--transform' and not C.exists()
 shutil.copytree(B,C)
 payload=R/'handoff_payload_26890'
 for k in changed:
  path=C/k;path.parent.mkdir(parents=True,exist_ok=True)
  path.write_bytes((payload/k[4:]).read_bytes())
assert scan(B)==A,'actual successful 26889 compiled source not exact'
assert scan(C)==Z,'26890 candidate source SHA mismatch'
assert all(A[k]==Z[k]==v for k,v in P.items())
assert (C/'app/version.properties').read_text().endswith('VERSION_NAME=0.9726890\nVERSION_BUILD=26890\n')
print('PASS 26890 frozen 2025/2025, 8 modifications, 2017 byte-identical protected files, 0 added/deleted')
