#!/usr/bin/env python3
"""Physically mutate isolated handoff copies and require fail-closed seal."""
import hashlib,importlib.util,pathlib,tempfile,shutil,subprocess,sys
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder26977',R/'build_26977_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
b.seal();changed,base,want=b.scope()
entries={p:h for h,p in (x.split('  ',1) for x in (R/'26977_HANDOFF_HASHES.sha256').read_text().splitlines())}
assert len(entries)==len(changed)+len(b.FILES)+2
with tempfile.TemporaryDirectory(prefix='photon26977-neg-') as t:
 t=pathlib.Path(t)
 for p in [*entries,'26977_HANDOFF_HASHES.sha256']:
  dst=t/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/p,dst)
 cases=0
 for p in ['TRIGGER_26977.txt','.github/workflows/build-26977-change-aware.yml','26977_FORWARD_FULLINDEX.patch','26977_PROTECTED_SOURCE.sha256','handoff_payload_26977/'+sorted(changed)[0]]:
  f=t/p;original=f.read_bytes();f.write_bytes(original+b'\nNEGATIVE\n')
  ret=subprocess.run([sys.executable,'-S',str(t/'build_26977_incremental.py'),'seal'],capture_output=True,text=True)
  assert ret.returncode!=0,p;f.write_bytes(original);cases+=1
 extra=t/'handoff_payload_26977/app/unexpected.txt';extra.write_text('negative extra')
 ret=subprocess.run([sys.executable,'-S',str(t/'build_26977_incremental.py'),'seal'],capture_output=True,text=True);assert ret.returncode!=0 and 'payload missing/extra' in ret.stderr
 extra.unlink();cases+=1
 subprocess.run([sys.executable,'-S',str(t/'build_26977_incremental.py'),'seal'],check=True)
 print('PASS',cases,'actual isolated tamper/extra negative seals; clean seal restored')
