#!/usr/bin/env python3
"""26880 deterministic real complete binary patch fwd+rollback at core.abbrev 7/12/40, fuzz=0."""
from pathlib import Path
import tempfile,hashlib,subprocess,shutil,sys
P=Path(__file__).resolve().parent;B=Path(sys.argv[1]).resolve();C=Path(sys.argv[2]).resolve()
forward=Path(sys.argv[3]).resolve() if len(sys.argv)>3 else P/'26880_FORWARD_FULL_INDEX.patch'
rollback=Path(sys.argv[4]).resolve() if len(sys.argv)>4 else P/'26880_ROLLBACK_FULL_INDEX.patch'
def manifest(name):return {q:d for d,q in (line.split('  ',1) for line in (P/name).read_text().splitlines())}
prior=manifest('26880_BASE_26879_FULL_APP.sha256');latest=manifest('26880_EXPECTED_CANDIDATE_FULL_APP.sha256')
assert len(prior)==2001 and len(latest)==2015
for p in (forward,rollback):
 assert p.is_file() and b'index ' in p.read_bytes() and b'GIT binary patch' in p.read_bytes()
 assert not any(x in p.read_bytes() for x in (b'rename from ',b'rename to ',b'copy from ',b'copy to '))
for n in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'26880_real_patch_abbrev{n}_') as td:
  root=Path(td);shutil.copytree(B/'app',root/'app')
  subprocess.run(['git','init','-q'],cwd=root,check=True)
  for patch,want in ((forward,latest),(rollback,prior)):
   cmd=['git','-c',f'core.abbrev={n}','apply','--whitespace=nowarn','--unsafe-paths']
   for c in (cmd+['--check',str(patch)],cmd+[str(patch)]):
    proc=subprocess.run(c,cwd=root,capture_output=True)
    assert proc.returncode==0,(n,str(patch),proc.stderr.decode()[-2000:])
   found={'app/'+p.relative_to(root/'app').as_posix() for p in (root/'app').rglob('*') if p.is_file()}
   assert found==set(want),(n,'runtime changed-file allowlist mismatch',len(found^set(want)))
   for rel,d in want.items():assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==d,(n,rel)
print('PASS 26880 real full-index binary forward/rollback 7/12/40, fuzz=0, exact 2001/2015 source universes')
