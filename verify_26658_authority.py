#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26658_authority.py ROOT BASE CANDIDATE')
root,base,cand=map(lambda x:Path(x).resolve(),sys.argv[1:4])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def readm(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1);d[r]=h
 return d
def H(r): return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
bh,ch=H(base),H(cand); assert len(bh)==len(ch)==1721
bm=readm(root/'R1_26658_BASE_26653_FULL_APP.sha256'); cm=readm(root/'R1_26658_EXPECTED_CANDIDATE_FULL_APP.sha256')
assert bh==bm and ch==cm
allow=set((root/'R1_26658_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines());allow.discard('')
assert len(allow)==6 and {r for r in bh if bh[r]!=ch[r]}==allow
pb=readm(root/'R1_26658_PROTECTED_UNCHANGED_BASE.sha256'); pc=readm(root/'R1_26658_PROTECTED_UNCHANGED_CANDIDATE.sha256')
assert len(pb)==len(pc)==1715 and pb==pc and set(pb)==set(bh)-allow
for kind,n in [('NATIVE_PROTECTED',807),('VENDOR_PROTECTED',778),('DNG',7)]:
 x=readm(root/f'R1_26658_{kind}_BASE.sha256');y=readm(root/f'R1_26658_{kind}_CANDIDATE.sha256');assert len(x)==len(y)==n and x==y
sb=readm(root/'R1_26658_SHADER_UNIVERSE_BASE.sha256');sc=readm(root/'R1_26658_SHADER_UNIVERSE_CANDIDATE.sha256');assert len(sb)==len(sc)==257 and sb==sc
print('PASS 26658 authority: 1721 base/candidate, exact 6 changed / 0 added, 1715 protected, 807 native, 778 vendor, 7 DNG, 257 shaders byte-invariant')
