#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys

def fail(m): raise SystemExit('FAIL: '+m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read_manifest(p):
    d={}
    for line in p.read_text().splitlines():
        if not line.strip():continue
        h,rel=line.split('  ',1);d[rel]=h
    return d
def verify(root,manifest):
    m=read_manifest(manifest)
    for rel,h in m.items():
        p=root/rel
        if not p.is_file():fail(f'missing {rel}')
        if sha(p)!=h:fail(f'hash {rel}')
    return len(m)
def main():
    if len(sys.argv)!=4:fail('usage package_root base candidate')
    pkg,base,cand=map(Path,sys.argv[1:])
    bf=pkg/'V1_26570_BASE_26569_FULL_APP.sha256'; cf=pkg/'V1_26570_EXPECTED_CANDIDATE_FULL_APP.sha256'
    pb=pkg/'V1_26570_PROTECTED_UNCHANGED_BASE.sha256'; pc=pkg/'V1_26570_PROTECTED_UNCHANGED_CANDIDATE.sha256'
    nb=pkg/'V1_26570_NATIVE_PROTECTED_BASE.sha256'; nc=pkg/'V1_26570_EXPECTED_NATIVE_PROTECTED.sha256'
    db=pkg/'V1_26570_DNG_PROTECTED_BASE.sha256'; dc=pkg/'V1_26570_DNG_PROTECTED_CANDIDATE.sha256'
    ab=pkg/'V1_26570_PROTECTED_ARCHITECTURE_BASE.sha256'; ac=pkg/'V1_26570_PROTECTED_ARCHITECTURE_CANDIDATE.sha256'
    pre=pkg/'V1_26570_PREWRITE_SOURCE_HASHES.sha256'; expchg=pkg/'V1_26570_EXPECTED_CHANGED_SOURCE_HASHES.sha256'
    counts=[verify(base,bf),verify(cand,cf),verify(base,pb),verify(cand,pc),verify(base,nb),verify(cand,nc),verify(base,db),verify(cand,dc),verify(base,ab),verify(cand,ac),verify(base,pre),verify(cand,expchg)]
    if counts[:2]!=[1708,1708]:fail('full manifest completeness')
    if counts[2:4]!=[1705,1705]:fail('protected completeness')
    if counts[4:6]!=[803,803]:fail('native protected completeness')
    if counts[6:8]!=[7,7]:fail('DNG completeness')
    # Protection manifests must be byte-identical because protected universes are invariant.
    for a,b,label in [(pb,pc,'protected'),(nb,nc,'native'),(db,dc,'DNG'),(ab,ac,'architecture')]:
        if a.read_bytes()!=b.read_bytes():fail(label+' manifest drift')
    changed=(pkg/'V1_26570_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()
    if len(changed)!=3 or len(set(changed))!=3:fail('changed allowlist cardinality')
    for rel in changed:
        if rel not in read_manifest(pre) or rel not in read_manifest(expchg):fail('changed hash manifest omission '+rel)
    print(f'PASS exact 26569 compiled-candidate authority full={counts[0]} protected={counts[2]} nativeProtected={counts[4]} DNG={counts[6]} architecture={counts[8]}')
    print('PASS exact prewrite and expected changed-source hashes')
if __name__=='__main__':main()
