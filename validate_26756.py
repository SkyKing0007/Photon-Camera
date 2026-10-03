#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit("usage: validate_26756.py BASE26755 CANDIDATE26756")
base,cand=map(Path,sys.argv[1:]); root=Path(__file__).resolve().parent
allow=[x.strip() for x in (root/"26756_RUNTIME_CHANGED_PATHS.txt").read_text().splitlines() if x.strip()]
assert len(allow)==2 and len(set(allow))==2
def H(r): return {"app/"+p.relative_to(r/"app").as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/"app").rglob("*") if p.is_file()}
b,c=H(base),H(cand); assert len(b)==len(c)==1823,(len(b),len(c))
changed=sorted(p for p in set(b)|set(c) if b.get(p)!=c.get(p)); assert changed==sorted(allow),(changed,sorted(allow)); assert not(set(c)-set(b)) and not(set(b)-set(c))
v=(cand/"app/version.properties").read_text(); assert "VERSION_NAME=0.9726756" in v and "VERSION_BUILD=26756" in v
print("PASS 26756 exact runtime allowlist: 2 changed / 0 added / 1821 protected")
