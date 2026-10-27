#!/usr/bin/env python3
"""Original successful 26883 full-index forward/rollback at 7,12,40 fuzz=0."""
from pathlib import Path
import hashlib,subprocess,tempfile,shutil,sys
R=Path(__file__).resolve().parent;B=Path(sys.argv[1]).resolve();C=Path(sys.argv[2]).resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(n):return {k:h for h,k in (s.split('  ',1) for s in (R/n).read_text().splitlines())}
old=manifest('26884_BASE_26883_FULL_APP.sha256');new=manifest('26884_EXPECTED_CANDIDATE_FULL_APP.sha256')
fwd=R/'26884_FORWARD_FULL_INDEX.patch';back=R/'26884_ROLLBACK_FULL_INDEX.patch'
for p in (fwd,back):
 data=p.read_bytes()
 assert data.count(b'diff --git ')==3 and data.count(b'index ')==3
 assert not any(t in data for t in (b'rename from ',b'rename to ',b'copy from ',b'copy to '))
for n in [7,12,40]:
 with tempfile.TemporaryDirectory(prefix=f'26884_real_compiled_abbrev{n}_') as td:
  d=Path(td);shutil.copytree(B/'app',d/'app');subprocess.run(['git','init','-q'],cwd=d,check=True)
  for patch,want in [(fwd,new),(back,old)]:
   for flags in [['--check'],[]]:
    x=subprocess.run(['git','-c',f'core.abbrev={n}','apply','--whitespace=nowarn',*flags,str(patch)],cwd=d,capture_output=True)
    assert x.returncode==0,(n,str(patch),flags,x.stderr[-500:])
   files={'app/'+p.relative_to(d/'app').as_posix() for p in (d/'app').rglob('*') if p.is_file()}
   assert files==set(want),(n,'unexpected file universe')
   assert all(sha(d/k)==v for k,v in want.items()),('byte mismatch',n)
print('PASS 26884 deterministic full-index forward/rollback core.abbrev 7/12/40, fuzz=0, exact original 2009 files')
