#!/usr/bin/env python3
"""Full blob IDs, zero-fuzz exact successful compiled 26917 forward/reverse at 7/12/40."""
from pathlib import Path
import re,hashlib,subprocess,sys,shutil,tempfile
R=Path(__file__).resolve().parent
changed=(R/'26920_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
added=set((R/'26920_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
before={p:h for h,p in (s.split('  ',1) for s in (R/'26920_BASE_26917_FULL_APP.sha256').read_text().splitlines())}
after={p:h for h,p in (s.split('  ',1) for s in (R/'26920_PRECOMPILE_EXPECTED_FULL_APP.sha256').read_text().splitlines())}
patch=R/'26920_FULL_INDEX_FORWARD.patch';s=patch.read_text()
assert len(changed)==19 and len(added)==2 and s.count('diff --git ')==19
indices=re.findall(r'^diff --git a/([^\n]+) b/([^\n]+)\n(?:new file mode 100644\n)?index ([0-9a-f]{40})\.\.([0-9a-f]{40})(?: 100644)?$',s,re.M)
assert len(indices)==19,len(indices)
for a,b,old,new in indices:
 assert a==b and a in changed
 f=R/'handoff_payload_26920'/a
 assert f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest()==after[a]
 blob=subprocess.run(['git','hash-object',str(f)],capture_output=True,text=True,check=True).stdout.strip()
 assert blob==new,(a,blob,new)
 assert (a in added and old=='0'*40) or (a not in added and old!='0'*40)
base=R/'.photon_26920_work/authority_26917'
if '--live' in sys.argv:assert base.is_dir(),'26917 successful compiled authority not prepared'
for n in (7,12,40):
 if '--live' not in sys.argv:break
 with tempfile.TemporaryDirectory(prefix='26920_fuzz0_') as td:
  root=Path(td)
  for p in changed:
   if p in added:continue
   f=base/p;assert f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest()==before[p]
   o=root/p;o.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,o)
  for flags in (['--check'],[],['--reverse','--check'],['--reverse']):
   q=subprocess.run(['git','-c',f'core.abbrev={n}','apply','--whitespace=error','-p1',*flags,str(patch)],cwd=root,capture_output=True,text=True)
   assert q.returncode==0,(n,flags,q.stderr)
   if flags==[]:assert all(hashlib.sha256((root/p).read_bytes()).hexdigest()==after[p] for p in changed)
   if flags==['--reverse']:assert all(not (root/p).exists() if p in added else hashlib.sha256((root/p).read_bytes()).hexdigest()==before[p] for p in changed)
print('PASS exact 26920 full-index 19-path patch '+('real compiled 26917 forward/reverse 7/12/40' if '--live' in sys.argv else 'SHA/provenance, authority replay pending'))
