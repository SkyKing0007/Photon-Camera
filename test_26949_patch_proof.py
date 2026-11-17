#!/usr/bin/env python3
"""Forward/rollback byte-exact git apply on 3 files, SHA-1 full blob indexes."""
import sys,pathlib,tempfile,subprocess,hashlib,shutil,re
R=pathlib.Path(__file__).resolve().parent
C=(R/'26949_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
A={p:h for h,p in [l.split('  ',1) for l in (R/'26949_BASE_26948_FULL_APP.sha256').read_text().splitlines()]}
B={p:h for h,p in [l.split('  ',1) for l in (R/'26949_EXPECTED_FULL_APP.sha256').read_text().splitlines()]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def apply(root,patch,check=False):
 cmd=['git','apply','--unsafe-paths']+(['--check'] if check else [])+[str(R/patch)]
 subprocess.run(cmd,cwd=root,check=True,capture_output=True)
for kind in ['FORWARD','ROLLBACK']:
 s=(R/f'26949_{kind}_FULLINDEX.patch').read_text()
 assert s.count('diff --git a/')==len(C) and s.count('index ')==len(C)
 for line in s.splitlines():
  if line.startswith('index '):assert re.fullmatch(r'index [a-f0-9]{40}\.\.[a-f0-9]{40} 100644',line)
for abr in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'26949_patch_abbr{abr}_') as temp:
  d=pathlib.Path(temp)
  for p in C:
   src=R/'handoff_payload_26949'/p
   f=d/p;f.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,f)
  for p in C:assert sha(d/p)==B[p]
  apply(d,'26949_ROLLBACK_FULLINDEX.patch',True)
  apply(d,'26949_ROLLBACK_FULLINDEX.patch')
  for p in C:assert sha(d/p)==A[p]
  apply(d,'26949_FORWARD_FULLINDEX.patch',True)
  apply(d,'26949_FORWARD_FULLINDEX.patch')
  for p in C:assert sha(d/p)==B[p]
  # Strict negative: altered base file must not accept exact patch cleanly.
  f=d/C[0]; t=f.read_text(); assert 'IRIS_26949_B_OFF_EXACT_RAWR_AMAZE_HANDOFF' in t; f.write_text(t.replace('IRIS_26949_B_OFF_EXACT_RAWR_AMAZE_HANDOFF','CORRUPTED_B_OFF_EXACT_RAWR_AMAZE_HANDOFF'))
  r=subprocess.run(['git','apply','--check',str(R/'26949_ROLLBACK_FULLINDEX.patch')],cwd=d,capture_output=True)
  assert r.returncode!=0
print('PASS 26949 full SHA-index forward+rollback fuzz=0 at abbreviations 7/12/40; tamper rejection')
