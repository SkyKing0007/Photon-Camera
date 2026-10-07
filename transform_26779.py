#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=4: raise SystemExit("usage: transform_26779.py BASE CAND PAYLOAD")
base=Path(sys.argv[1]); cand=Path(sys.argv[2]); payload=Path(sys.argv[3])
allowed=[
"app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java",
"app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java",
"app/src/main/res/values/default_prefs.xml",
"app/src/main/res/values/strings.xml",
"app/src/main/res/xml/preferences.xml",
"app/version.properties",
]
actual=sorted(str(p.relative_to(payload)) for p in payload.rglob("*") if p.is_file())
assert actual==allowed,(actual,allowed)
if cand.exists(): shutil.rmtree(cand)
shutil.copytree(base,cand)
for rel in allowed:
    src=payload/rel; dst=cand/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
def U(r):
    return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(r)/"app").rglob("*") if p.is_file()}
a,b=U(base),U(cand)
assert len(a)==1779 and len(b)==1779,(len(a),len(b))
changed=sorted(k for k in a if a[k]!=b[k])
assert changed==allowed,changed
assert set(a)==set(b),"file universe changed"
print("PASS 26779 deterministic candidate reconstruction: exactly 6 modified files, 0 additions, 0 deletions")
