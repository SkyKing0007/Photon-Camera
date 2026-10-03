#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26753_authority.py PACKAGE BASE CANDIDATE')
root,base,cand=map(Path,sys.argv[1:])

def parse(name):
    out={}
    for line in (root/name).read_text().splitlines():
        if not line.strip(): continue
        h,p=line.split(None,1); out[p.strip()]=h
    return out

def actual(tree,p): return hashlib.sha256((tree/p).read_bytes()).hexdigest()
def prove(name,tree,expected_count):
    m=parse(name); assert len(m)==expected_count,(name,len(m),expected_count)
    for p,h in m.items(): assert (tree/p).is_file() and actual(tree,p)==h,(name,p)
    return m
base_full=prove('26753_BASE_26752_FULL_APP.sha256',base,1823)
cand_full=prove('26753_EXPECTED_CANDIDATE_FULL_APP.sha256',cand,1823)
base_prot=prove('26753_PROTECTED_BASE.sha256',base,1818)
cand_prot=prove('26753_PROTECTED_CANDIDATE.sha256',cand,1818)
assert base_prot==cand_prot
for stem,count in [('DNG',6),('VENDOR',778),('NATIVE_PROTECTED',818),('SHADER',271)]:
    a=prove(f'26753_{stem}_BASE.sha256',base,count); b=prove(f'26753_{stem}_CANDIDATE.sha256',cand,count); assert a==b,stem
print('PASS 26753 authority: 1823 base/candidate; 1818 protected; DNG 6; vendor 778; native-protected 818; shaders 271 invariant')
