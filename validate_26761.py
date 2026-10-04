#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26761.py BASE CANDIDATE')
b,c=map(Path,sys.argv[1:])
allow=[x for x in (Path(__file__).resolve().parent/'26761_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
def H(r): return {'app/'+p.relative_to(r/'app').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
hb,hc=H(b),H(c); assert len(hb)==len(hc)==1823 and set(hb)==set(hc)
changed=sorted(k for k in hb if hb[k]!=hc[k]); assert changed==sorted(allow),(changed,allow)
assert len(changed)==5 and not (set(hc)-set(hb)) and not (set(hb)-set(hc))
for p in allow: assert (b/p).is_file() and (c/p).is_file()
v=(c/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726761' in v and 'VERSION_BUILD=26761' in v
print('PASS 26761 validate: authority-seeded 1823-file universe; exact 5 existing runtime changes; 0 additions/deletions; version 0.9726761/26761')
