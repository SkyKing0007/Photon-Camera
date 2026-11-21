#!/usr/bin/env python3
"""Full-index forward and rollback patch physical proof at 7/12/40, fuzz=0.
Does not commit any source or modify the repository, only temporary copies.
"""
from pathlib import Path
import hashlib,re,shutil,subprocess,tempfile,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_26973_incremental as build
R=build.R
forward=R/'26973_FORWARD_FULLINDEX.patch';rollback=R/'26973_ROLLBACK_FULLINDEX.patch'
for patch in (forward,rollback):
 s=patch.read_text()
 if s.count('diff --git ')!=11 or s.count('index ')<7:build.fail('expected full-index 11-path patch differs')
 for line in s.splitlines():
  if line.startswith('index ') and not re.fullmatch(r'index [0-9a-f]{40}\.\.[0-9a-f]{40}(?: [0-7]{6})?',line):build.fail('patch abbreviated or invalid index '+line)
 if re.search(r'(^|\n)(?:---|\+\+\+)\s+(?![ab]/app/|/dev/null)',s):build.fail('patch paths escape app')
if '--live' not in sys.argv:
 print('PASS 26973 patch payload 11 full-index changes, no abbreviated hashes or path escape')
 sys.exit(0)
base=build.BASE;candidate=build.CAND
build.exact(base,'26973_BASE_26972_FULL_APP.sha256','patch starting baseline')
build.exact(candidate,'26973_EXPECTED_FULL_APP.sha256','patch target frozen candidate')
for abbrev in (7,12,40):
 with tempfile.TemporaryDirectory(prefix='photon26973_patch_') as tmp:
  root=Path(tmp);shutil.copytree(base/'app',root/'app')
  def git_apply(p):
   for arguments in (['--check'],[]):
    r=subprocess.run(['git','-c',f'core.abbrev={abbrev}','apply','--binary','--whitespace=error',*arguments,str(p)],cwd=root,capture_output=True,text=True)
    if r.returncode:build.fail('fuzz=0 patch '+p.name+' core.abbrev='+str(abbrev)+' '+r.stderr[:700])
  git_apply(forward)
  build.exact(root,'26973_EXPECTED_FULL_APP.sha256','forward full-index proof')
  git_apply(rollback)
  build.exact(root,'26973_BASE_26972_FULL_APP.sha256','rollback full-index proof')
 print('PASS 26973 forward/rollback full-index byte-exact fuzz=0 at git core.abbrev 7/12/40')
