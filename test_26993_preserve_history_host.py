#!/usr/bin/env python3
"""Replay exact 26992 V2 and 26991 historical host checks using pinned sparse source preimages.
Version changes are checked against their own manifests, never required to match older versions.
"""
import pathlib,subprocess,sys,tempfile,shutil
import build_26993_incremental as b
R=b.R
if __name__=='__main__':
 base=b.exact(b.BASE,'26993_BASE_26992_FULL_APP.sha256','actual 26992 historical host authority');live=b.exact(R,'26993_EXPECTED_FULL_APP.sha256','current 26993 historical host successor');prev=b.parse(R/'26992_BASE_26991_FULL_APP.sha256');prev2=b.parse(R/'26991_BASE_26990_FULL_APP.sha256')
 assert b.parse(R/'26992_EXPECTED_FULL_APP.sha256')==base and b.parse(R/'26991_EXPECTED_FULL_APP.sha256')==prev
 delta92=set((R/'26992_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines());delta91=set((R/'26991_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines());version='app/version.properties';assert len(delta92)==3 and len(delta91)==7 and delta91&delta92=={version}
 assert delta92=={p for p in base if base[p]!=prev[p]} and delta91=={p for p in prev if prev[p]!=prev2[p]}
 assert all(live[p]==base[p] for p in (delta91|delta92)-{version}) and live[version]!=base[version]!=prev[version]
 with tempfile.TemporaryDirectory(prefix='26993-history-host-') as td:
  t=pathlib.Path(td);subprocess.run(['git','init','-q',str(t)],check=True)
  # Sparse exact 26991 inputs, including both old gainmap files and the six historical 26991 processing/settings changes.
  for p in sorted(delta91|delta92):
   f=t/p;f.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(b.BASE/p,f);assert b.sha(f)==base[p]
  strength='app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/hdr/HdrGainmapStrength.kt';f=t/strength;f.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(b.BASE/strength,f);assert b.sha(f)==base[strength]==prev[strength]==live[strength]
  cmd=['git','apply','--whitespace=nowarn'];patch=R/'26992_ROLLBACK_FULLINDEX.patch';subprocess.run(cmd+['--check',str(patch)],cwd=t,check=True);subprocess.run(cmd+[str(patch)],cwd=t,check=True)
  for p in delta91|delta92:assert b.sha(t/p)==prev[p],p
  # Original V2 version-aware gate against the real 26992 root, unmodified.
  subprocess.run([sys.executable,'-S',str(R/'test_26992_preserve_26991_host.py'),'--root',str(b.BASE),'--base',str(t)],cwd=R,check=True)
  # The original 26992 gain-map host runs against live 26993 and exact 26991 preimage.
  subprocess.run([sys.executable,'-S',str(R/'test_26992_processing_host.py'),'--root',str(R),'--base',str(t)],cwd=R,check=True)
  # Direct execution of the original 26991 processing host against the actual live 26993 tree.
  patch=R/'26991_ROLLBACK_FULLINDEX.patch';subprocess.run(cmd+['--check',str(patch)],cwd=t,check=True);subprocess.run(cmd+[str(patch)],cwd=t,check=True)
  for p in delta91:assert b.sha(t/p)==prev2[p],p
  subprocess.run([sys.executable,'-S',str(R/'test_26991_processing_host.py'),'--root',str(R),'--base',str(t)],cwd=R,check=True)
 b.exact(b.BASE,'26993_BASE_26992_FULL_APP.sha256','actual 26992 untouched');b.exact(R,'26993_EXPECTED_FULL_APP.sha256','26993 live untouched')
 print('PASS original 26992 V2 and 26991 host replay including live 26993; historical versions separately pinned')
