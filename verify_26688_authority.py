#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26688_authority.py ROOT BASE CAND')
root,base,cand=map(Path,sys.argv[1:])
def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mf(p):
    out={}
    for line in Path(p).read_text().splitlines():
        if line.strip(): hh,rel=line.split('  ',1); out[rel]=hh
    return out
def snap(r): return {str(p.relative_to(r)):h(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
a=snap(base); b=snap(cand)
if len(a)!=1768 or len(b)!=1770: raise SystemExit(f'FAIL full file count {len(a)}/{len(b)}')
if a!=mf(root/'R1_26688_BASE_26687_R1_1_FULL_APP.sha256'): raise SystemExit('FAIL exact successful 26687 R1.1 full manifest')
if b!=mf(root/'R1_26688_EXPECTED_CANDIDATE_FULL_APP.sha256'): raise SystemExit('FAIL 26688 candidate full manifest')
allow=set((root/'R1_26688_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); actual={k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
if actual!=allow: raise SystemExit('FAIL exact changed-file allowlist '+repr(sorted(actual^allow)))
prot=mf(root/'R1_26688_PROTECTED_UNCHANGED_BASE.sha256')
if len(prot)!=1760: raise SystemExit('FAIL protected count')
if prot!=mf(root/'R1_26688_PROTECTED_UNCHANGED_CANDIDATE.sha256'): raise SystemExit('FAIL protected manifests differ')
for rel,hh in prot.items():
    if a.get(rel)!=hh or b.get(rel)!=hh: raise SystemExit('FAIL protected byte '+rel)
for prefix,count in [('NATIVE_PROTECTED',804),('VENDOR_PROTECTED',778),('DNG',7),('ASSET_SHADER_UNIVERSE',271)]:
    bm=mf(root/f'R1_26688_{prefix}_BASE.sha256'); cm=mf(root/f'R1_26688_{prefix}_CANDIDATE.sha256')
    if len(bm)!=count or bm!=cm: raise SystemExit('FAIL '+prefix+' manifest/count')
    for rel,hh in bm.items():
        if a.get(rel)!=hh or b.get(rel)!=hh: raise SystemExit('FAIL '+prefix+' byte '+rel)
nb=mf(root/'R1_26688_NATIVE_FULL_BASE.sha256'); nc=mf(root/'R1_26688_NATIVE_FULL_CANDIDATE.sha256')
if len(nb)!=817 or len(nc)!=819: raise SystemExit('FAIL native full count')
for rel,hh in nb.items():
    if not rel.startswith('app/src/main/cpp/') or a.get(rel)!=hh: raise SystemExit('FAIL native base completeness '+rel)
for rel,hh in nc.items():
    if not rel.startswith('app/src/main/cpp/') or b.get(rel)!=hh: raise SystemExit('FAIL native candidate completeness '+rel)
native_actual={k for k in set(nb)|set(nc) if nb.get(k)!=nc.get(k)}
native_expected={'app/src/main/cpp/CMakeLists.txt','app/src/main/cpp/spektra/SpektraNativeJni.cpp','app/src/main/cpp/spektra/SpektraRawCpuOwner.cpp','app/src/main/cpp/spektra/SpektraRawCpuOwner.h'}
if native_actual!=native_expected: raise SystemExit('FAIL native exact changed set '+repr(sorted(native_actual^native_expected)))
added=[x for x in (root/'R1_26688_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
expected_added=['app/src/main/cpp/spektra/SpektraRawCpuOwner.cpp','app/src/main/cpp/spektra/SpektraRawCpuOwner.h']
if added!=expected_added or any(x in a for x in added) or any(x not in b for x in added): raise SystemExit('FAIL added-path authority')
if (root/'R1_26688_DELETED_PATHS_MUST_EXIST.txt').read_text().strip(): raise SystemExit('FAIL unexpected deletion manifest')
print('PASS 26688 authority: 1768 base / 1770 candidate / 10 changed / 2 added / 0 deleted / 1760 protected / 817->819 complete native / 804 native-protected / 778 vendor / 7 DNG / 271 asset shaders')
