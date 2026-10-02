#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26747.py BASE26746 CAND26747')
b,c=map(Path,sys.argv[1:])
assert (c/'app/version.properties').read_text().count('VERSION_BUILD=26747')==1
assert 'VERSION_NAME=0.9726747' in (c/'app/version.properties').read_text()
print('PASS 26747 semantic validation')
