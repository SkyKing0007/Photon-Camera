#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit("usage: validate_26758.py BASE CANDIDATE")
b,c=map(Path,sys.argv[1:])
allow=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties',
]
def H(r): return {"app/"+p.relative_to(r/"app").as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/"app").rglob("*") if p.is_file()}
hb,hc=H(b),H(c); assert len(hb)==len(hc)==1823 and set(hb)==set(hc)
changed=sorted(k for k in hb if hb[k]!=hc[k]); assert changed==sorted(allow),(changed,allow)
v=(c/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726758' in v and 'VERSION_BUILD=26758' in v
for p in allow: assert (b/p).is_file() and (c/p).is_file()
print('PASS 26758 validate: 1823-file universe; exact 4 existing runtime changes; version 0.9726758/26758')
