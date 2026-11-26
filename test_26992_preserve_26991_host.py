#!/usr/bin/env python3
"""Re-execute the exact 26991 processing host using a SHA-proven sparse predecessor rollback."""
import argparse,pathlib,subprocess,tempfile,shutil,hashlib,sys
R=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,required=True);p.add_argument('--base',type=pathlib.Path,required=True);a=p.parse_args();root=a.root.resolve();base=a.base.resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(n):return {p:h for h,p in (l.split('  ',1) for l in (R/n).read_text().splitlines())}
prior=read('26991_BASE_26990_FULL_APP.sha256');current=read('26991_EXPECTED_FULL_APP.sha256');changed=(R/'26991_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines();assert len(changed)==7 and set(changed)=={p for p in prior if prior[p]!=current[p]}
with tempfile.TemporaryDirectory(prefix='26992-preserved-26991-') as td:
 t=pathlib.Path(td);subprocess.run(['git','init','-q',str(t)],check=True)
 for rel in changed:
  assert sha(base/rel)==current[rel]==sha(root/rel),rel
  dest=t/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/rel,dest)
 patch=R/'26991_ROLLBACK_FULLINDEX.patch';cmd=['git','apply','--whitespace=nowarn'];subprocess.run(cmd+['--check',str(patch)],cwd=t,check=True);subprocess.run(cmd+[str(patch)],cwd=t,check=True)
 for rel in changed:assert sha(t/rel)==prior[rel],rel
 subprocess.run([sys.executable,'-S',str(R/'test_26991_processing_host.py'),'--root',str(root),'--base',str(t)],cwd=R,check=True)
print('PASS original 26991 processing regression replay with exact sparse 26990 preimage')
