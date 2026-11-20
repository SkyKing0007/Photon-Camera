#!/usr/bin/env python3
"""26969 strict full-index forward/rollback replay against the actual successful 26968 TAR."""
import pathlib,subprocess,tempfile,shutil,sys,hashlib,re
R=pathlib.Path(__file__).resolve().parent
parse=lambda p:dict((path,h) for h,path in (line.split('  ',1) for line in (R/p).read_text().splitlines()))
A=parse('26969_BASE_26968_FULL_APP.sha256');B=parse('26969_EXPECTED_FULL_APP.sha256')
changed=set((R/'26969_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines());added=set((R/'26969_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
assert changed=={p for p in A if A[p]!=B.get(p)};assert added==set(B)-set(A)
for name in ('26969_FORWARD_FULLINDEX.patch','26969_ROLLBACK_FULLINDEX.patch'):
 t=(R/name).read_text();assert len(t)>5000,name
 assert t.count('@@ ')>=14,name
 assert t.count('--- ')==14 and t.count('+++ ')==14,name
 for path in changed|added:assert path in t,(name,path)
if '--payload' in sys.argv:
 print('PASS 26969 sealed forward+rollback diffs syntax, 14 exact changed/added paths')
 sys.exit(0)
source=R/'.photon_26969_work/authority_26968';candidate=R/'.photon_26969_work/candidate_26969'
assert (source/'app/version.properties').is_file() and (candidate/'app/version.properties').is_file(),'actual 26968 compiled authority not yet extracted'
with tempfile.TemporaryDirectory(prefix='iris26969_patch_') as temp:
 q=pathlib.Path(temp)
 for path in changed:
  dest=q/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/path,dest)
 for action,file in [('forward','26969_FORWARD_FULLINDEX.patch'),('rollback','26969_ROLLBACK_FULLINDEX.patch')]:
  subprocess.run(['patch','--batch','--forward','--fuzz=0','--reject-file=-','-p1','-i',str(R/file)],cwd=q,check=True,capture_output=True)
  expected=B if action=='forward' else A
  for path in changed:
   assert hashlib.sha256((q/path).read_bytes()).hexdigest()==expected[path],(action,path)
  for path in added:
   if action=='forward':assert (q/path).is_file() and hashlib.sha256((q/path).read_bytes()).hexdigest()==B[path]
   else:assert not (q/path).exists(),('new file remains after rollback',path)
print('PASS exact 26968-success source forward and rollback patch replay, 14 paths, no fuzz')
