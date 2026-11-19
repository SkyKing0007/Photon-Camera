#!/usr/bin/env python3
"""Mutation tests against the actual source-seal executable (not merely a loose manifest parser)."""
import pathlib,tempfile,shutil,subprocess,sys
from build_26966_incremental import scope,sha
R=pathlib.Path(__file__).resolve().parent

def main():
 files=[x for x in R.iterdir() if x.is_file()]+list((R/'.github/workflows').glob('build-26966-*'))
 files+=list((R/'handoff_payload_26966').rglob('*'))
 files=[p for p in files if p.is_file()]
 tests=[('payload',pathlib.Path('handoff_payload_26966/app/version.properties'),b'INVALID_VERSION'),('workflow',pathlib.Path('.github/workflows/build-26966-change-aware.yml'),b'MUTATED_WORKFLOW'),('trigger',pathlib.Path('TRIGGER_26966.txt'),b'WRONG_TRIGGER'),('manifest',pathlib.Path('26966_EXPECTED_FULL_APP.sha256'),b'CORRUPT_MANIFEST')]
 for label,target,b in tests:
  with tempfile.TemporaryDirectory(prefix='photon_26966_negative_') as td:
   root=pathlib.Path(td)
   for item in files:
    rel=item.relative_to(R);dst=root/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(item,dst)
   (root/target).write_bytes(b)
   p=subprocess.run([sys.executable,'-S','build_26966_incremental.py','seal'],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   if p.returncode==0:raise AssertionError('mutated '+label+' incorrectly passed real seal')
 print('PASS four sealed-package negative mutations rejected by real 26966 seal')
if __name__=='__main__':main()
