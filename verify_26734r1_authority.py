#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26734r1_authority.py ROOT BASE26733 CAND26734')
pkg=Path(sys.argv[1]); b=Path(sys.argv[2]); c=Path(sys.argv[3])
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,r=l.split(None,1); d[r.strip()]=h
 return d
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B,C=H(b),H(c); assert len(B)==len(C)==1823
bm=load('26734R1_BASE_26733_FULL_APP.sha256'); cm=load('26734R1_EXPECTED_CANDIDATE_FULL_APP.sha256'); fm=load('26734R1_FAILED_26734_CANDIDATE_FULL_APP.sha256'); am=load('26734R1_SUCCESSFUL_26733_CANDIDATE_AUTHORITY.sha256')
assert len(bm)==len(cm)==len(fm)==len(am)==1823 and B==bm==am and C==cm==fm
changed=set((pkg/'26734R1_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert len(changed)==8 and {k for k in B|C if B.get(k)!=C.get(k)}==changed
pb=load('26734R1_PROTECTED_UNCHANGED_BASE.sha256'); pc=load('26734R1_PROTECTED_UNCHANGED_CANDIDATE.sha256'); assert len(pb)==len(pc)==1815 and pb==pc
for stem,count in [('NATIVE_PROTECTED',819),('VENDOR_PROTECTED',1),('DNG',6)]:
 x=load(f'26734R1_{stem}_BASE.sha256'); y=load(f'26734R1_{stem}_CANDIDATE.sha256'); assert len(x)==len(y)==count,(stem,len(x),len(y)); assert x==y,stem
nb=load('26734R1_NATIVE_FULL_BASE.sha256'); nc=load('26734R1_NATIVE_FULL_CANDIDATE.sha256'); assert len(nb)==len(nc)==820 and sum(nb.get(k)!=nc.get(k) for k in nb)==1
sb=load('26734R1_ASSET_SHADER_UNIVERSE_BASE.sha256'); sc=load('26734R1_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256'); assert len(sb)==len(sc)==271 and sb==sc
print('PASS 26734 R1 authority: exact successful 26733 -> byte-identical failed-26734 runtime candidate; 8 runtime changes; 1815 protected / 819 native-protected / 1 vendor / 6 DNG invariant')
