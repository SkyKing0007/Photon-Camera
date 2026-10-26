#!/usr/bin/env python3
"""Check binary forward and rollback on real full indexed previous candidate."""
from pathlib import Path
import hashlib,subprocess,tempfile,shutil,sys
P=Path(__file__).resolve().parent;B=Path(sys.argv[1]).resolve();C=Path(sys.argv[2]).resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(n):return {k:h for h,k in (line.split('  ',1) for line in (P/n).read_text().splitlines())}
prev=manifest('26881_BASE_26880_FULL_APP.sha256');cur=manifest('26881_EXPECTED_CANDIDATE_FULL_APP.sha256')
fwd=Path(sys.argv[3]).resolve() if len(sys.argv)>3 else P/'26881_FORWARD_FULL_INDEX.patch'
back=Path(sys.argv[4]).resolve() if len(sys.argv)>4 else P/'26881_ROLLBACK_FULL_INDEX.patch'
assert fwd.read_bytes().count(b'diff --git ')==18 and back.read_bytes().count(b'diff --git ')==18
for patch in (fwd,back):
 assert b'index ' in patch.read_bytes() and b'GIT binary patch' in patch.read_bytes()
 assert not any(x in patch.read_bytes() for x in (b'rename from ',b'rename to ',b'copy from ',b'copy to '))
for n in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'photon26881_fuzz0_abbrev{n}_') as td:
  root=Path(td);shutil.copytree(B/'app',root/'app')
  subprocess.run(['git','init','-q'],cwd=root,check=True)
  for patch,want in ((fwd,cur),(back,prev)):
   cmd=['git','-c',f'core.abbrev={n}','apply','--whitespace=nowarn']
   for suffix in (['--check',str(patch)],[str(patch)]):
    cp=subprocess.run(cmd+suffix,cwd=root,capture_output=True)
    assert cp.returncode==0,(n,patch,cp.stderr[-600:])
   universe={'app/'+f.relative_to(root/'app').as_posix() for f in (root/'app').rglob('*') if f.is_file()}
   assert universe==set(want),(n,'file universe diff',universe^set(want))
   for rel,h in want.items():assert sha(root/rel)==h,(n,rel)
print('PASS 26881 exact full-index binary forward and rollback core.abbrev 7/12/40, fuzz=0, original 2015/candidate 2009 universes')
