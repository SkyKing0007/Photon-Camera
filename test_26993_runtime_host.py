#!/usr/bin/env python3
import sys,subprocess,tempfile,pathlib
import build_26993_incremental as b
R=b.R
if __name__=='__main__':
 b.exact(b.BASE,'26993_BASE_26992_FULL_APP.sha256','host baseline');b.exact(R,'26993_EXPECTED_FULL_APP.sha256','host current')
 for n in ('test_26993_owner_host.py','test_26993_spektra_host.py'):
  subprocess.run([sys.executable,'-S',str(R/n),'--base',str(b.BASE),'--candidate',str(R)],cwd=R,check=True)
 subprocess.run([sys.executable,'-S',str(R/'test_26993_shadow_math.py')],cwd=R,check=True)
 with tempfile.TemporaryDirectory() as d:
  subprocess.run(['javac','-d',d,str(R/'Parse26993.java')],check=True)
  subprocess.run(['java','-cp',d,'Parse26993',*[str(R/p) for p in b.ALLOWED_MODIFIED if p.endswith('.java')]],check=True)
 b.exact(R,'26993_EXPECTED_FULL_APP.sha256','host current unchanged')
 print('PASS 26993 physical owner, Spektra planner, exact shader curve and Java source syntax host gates')
