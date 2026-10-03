#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit("usage: verify_26756_authority.py PACKAGE BASE CANDIDATE")
root,base,cand=map(Path,sys.argv[1:])
def parse(name):
 out={}
 for line in (root/name).read_text().splitlines():
  if line.strip(): h,p=line.split(None,1); out[p.strip()]=h
 return out
def actual(tree,p): return hashlib.sha256((tree/p).read_bytes()).hexdigest()
def prove(name,tree,count):
 m=parse(name); assert len(m)==count,(name,len(m),count)
 for p,h in m.items(): assert (tree/p).is_file() and actual(tree,p)==h,(name,p)
 return m
prove("26756_BASE_26755_FULL_APP.sha256",base,1823); prove("26756_EXACT_26755_CANDIDATE_AUTHORITY.sha256",base,1823); prove("26756_EXPECTED_CANDIDATE_FULL_APP.sha256",cand,1823)
a=prove("26756_PROTECTED_BASE.sha256",base,1821); b=prove("26756_PROTECTED_CANDIDATE.sha256",cand,1821); assert a==b
for stem,count in [("DNG",6),("VENDOR",778),("NATIVE_PROTECTED",818),("SHADER",271)]:
 a=prove(f"26756_{stem}_BASE.sha256",base,count); b=prove(f"26756_{stem}_CANDIDATE.sha256",cand,count); assert a==b,stem
print("PASS 26756 authority: 1823 base/candidate; 1821 protected; DNG 6; vendor 778; native-protected 818; shaders 271 invariant")
