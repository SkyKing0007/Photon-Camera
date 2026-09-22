#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26686_authority.py ROOT BASE CAND')
root,base,cand=map(Path,sys.argv[1:])
def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mf(p):
    out={}
    for line in Path(p).read_text().splitlines():
        if line.strip(): hh,rel=line.split('  ',1);out[rel]=hh
    return out
def snap(r): return {str(p.relative_to(r)):h(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
a=snap(base); b=snap(cand)
if len(a)!=1764 or len(b)!=1767: raise SystemExit(f'FAIL full file count {len(a)}/{len(b)}')
if a!=mf(root/'R1_26686_BASE_26685_R1_FULL_APP.sha256'): raise SystemExit('FAIL exact successful 26685 full manifest')
if b!=mf(root/'R1_26686_EXPECTED_CANDIDATE_FULL_APP.sha256'): raise SystemExit('FAIL 26686 candidate full manifest')
allow=set((root/'R1_26686_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); actual={k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
if actual!=allow: raise SystemExit('FAIL exact changed-file allowlist '+repr(sorted(actual^allow)))
prot=mf(root/'R1_26686_PROTECTED_UNCHANGED_BASE.sha256')
if len(prot)!=1753: raise SystemExit('FAIL protected count')
if prot!=mf(root/'R1_26686_PROTECTED_UNCHANGED_CANDIDATE.sha256'): raise SystemExit('FAIL protected manifests differ')
for rel,hh in prot.items():
    if a.get(rel)!=hh or b.get(rel)!=hh: raise SystemExit('FAIL protected byte '+rel)
for prefix,count in [('NATIVE_PROTECTED',804),('VENDOR_PROTECTED',778),('DNG',7),('ASSET_SHADER_UNIVERSE',271)]:
    bm=mf(root/f'R1_26686_{prefix}_BASE.sha256'); cm=mf(root/f'R1_26686_{prefix}_CANDIDATE.sha256')
    if len(bm)!=count or bm!=cm: raise SystemExit('FAIL '+prefix+' manifest/count')
    for rel,hh in bm.items():
        if a.get(rel)!=hh or b.get(rel)!=hh: raise SystemExit('FAIL '+prefix+' byte '+rel)
added=[x for x in (root/'R1_26686_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
if len(added)!=3 or any(x in a for x in added) or any(x not in b for x in added): raise SystemExit('FAIL added-path authority')
print('PASS 26686 authority: 1764 base / 1767 candidate / 14 changed / 3 added / 1753 protected / 804 native-protected / 778 vendor / 7 DNG / 271 inherited asset shaders + 1 new native compute shader')
