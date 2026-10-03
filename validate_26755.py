#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit("usage: validate_26755.py BASE26754 CANDIDATE26755")
base,cand=map(Path,sys.argv[1:]); root=Path(__file__).resolve().parent
allow=[x.strip() for x in (root/"26755_RUNTIME_CHANGED_PATHS.txt").read_text().splitlines() if x.strip()]
assert len(allow)==3 and len(set(allow))==3
def H(r): return {"app/"+p.relative_to(r/"app").as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/"app").rglob("*") if p.is_file()}
b,c=H(base),H(cand); assert len(b)==len(c)==1823,(len(b),len(c))
changed=sorted(p for p in set(b)|set(c) if b.get(p)!=c.get(p)); assert changed==sorted(allow),(changed,sorted(allow)); assert not(set(c)-set(b)) and not(set(b)-set(c))
v=(cand/"app/version.properties").read_text(); assert "VERSION_NAME=0.9726755" in v and "VERSION_BUILD=26755" in v
print("PASS 26755 exact runtime allowlist: 3 changed / 0 added / 1820 protected")
