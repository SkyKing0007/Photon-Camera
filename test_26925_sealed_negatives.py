#!/usr/bin/env python3
"""Actual fail-closed stage-1 builder negative tests, isolated temporary copy.
Proves missing/edited/stale handoff items fail sealed builder, not mock flags.
"""
from pathlib import Path
import hashlib,subprocess,tempfile,shutil
R=Path(__file__).resolve().parent
entries={}
for line in (R/'26925_HANDOFF_HASHES.sha256').read_text().splitlines():
 h,p=line.split('  ',1)
 assert p not in entries and len(h)==64,('duplicate/invalid staged hash',p)
 entries[p]=h
for x in ('build_26925_incremental.py','test_26925_source.py','26925_FORWARD_FULLINDEX.patch',
          '26925_ROLLBACK_FULLINDEX.patch','TRIGGER_26925.txt',
          'handoff_payload_26925/app/version.properties'):
 assert x in entries,x
with tempfile.TemporaryDirectory(prefix='p26925_real_sealed_negatives_') as d:
 t=Path(d)
 for p in entries:
  q=t/p;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/p,q)
 shutil.copy2(R/'26925_HANDOFF_HASHES.sha256',t/'26925_HANDOFF_HASHES.sha256')
 def run():return subprocess.run(['python3','-S','build_26925_incremental.py','seal'],cwd=t,capture_output=True,text=True)
 ok=run();assert ok.returncode==0,ok.stdout+' '+ok.stderr
 def negative(p,change):
  x=t/p;original=x.read_bytes();change(x)
  bad=run();assert bad.returncode!=0 and '26925 BLOCKED' in bad.stderr,(p,bad.stdout,bad.stderr)
  x.write_bytes(original)
  good=run();assert good.returncode==0,(p,'after negative reset',good.stdout,good.stderr)
 negative('handoff_payload_26925/app/version.properties',lambda x:x.write_bytes(x.read_bytes()+b'\nINJECTED_CHANGED_SOURCE=1'))
 negative('test_26925_shader_contract.py',lambda x:x.unlink())
 negative('TRIGGER_26925.txt',lambda x:x.write_bytes(x.read_bytes()+b'\nSTALE_26924_TRIGGER'))
 bad_lines=(t/'26925_HANDOFF_HASHES.sha256').read_text()
 (t/'26925_HANDOFF_HASHES.sha256').write_text(bad_lines+list(bad_lines.splitlines())[0]+'\n')
 bad=run();assert bad.returncode!=0 and '26925 BLOCKED' in bad.stderr
print('PASS real 26925 stage1 executable seals: missing file, mutated runtime shader, altered unique trigger, duplicate SHA receipt; full sealed builder rejects all')
