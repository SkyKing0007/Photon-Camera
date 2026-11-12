#!/usr/bin/env python3
"""Strict missing/altered SHA seal/allowlist/workflow/compiler negatives."""
from pathlib import Path
import subprocess,shutil,tempfile
R=Path(__file__).resolve().parent
names=[x.split('  ',1)[1] for x in (R/'26922_HANDOFF_HASHES.sha256').read_text().splitlines()]
with tempfile.TemporaryDirectory(prefix='neg26922_') as tmp:
 d=Path(tmp)
 for p in names+['26922_HANDOFF_HASHES.sha256']:
  q=d/p;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/p,q)
 def seal():return subprocess.run(['python3','-S','build_26922_incremental.py','seal'],cwd=d,capture_output=True,text=True).returncode
 assert seal()==0,'original 26922 handoff failed to seal'
 for p in ['handoff_payload_26922/app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag',
           'handoff_payload_26922/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
           '26922_CHANGED_RUNTIME_ALLOWLIST.txt','26922_FORWARD_FULLINDEX.patch',
           'compile_26922_shaders.sh','compile_26922_lk_shaders.py',
           '.github/workflows/build-26922-change-aware.yml']:
  f=d/p;raw=f.read_bytes();f.write_bytes(raw+b'\n');assert seal()!=0,'altered accepted '+p
  f.write_bytes(raw);f.unlink();assert seal()!=0,'missing accepted '+p
  f.write_bytes(raw)
 assert seal()==0,'valid 26922 not restored'
print('PASS strict 26922 3-stage seal mutation/missing overlay/shaders/manifest/workflow/patch blocked')
